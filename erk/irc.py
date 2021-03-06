#
#  Erk IRC Client
#  Copyright (C) 2019  Daniel Hetrick
#               _   _       _                         
#              | | (_)     | |                        
#   _ __  _   _| |_ _  ___ | |__                      
#  | '_ \| | | | __| |/ _ \| '_ \                     
#  | | | | |_| | |_| | (_) | |_) |                    
#  |_| |_|\__,_|\__| |\___/|_.__/ _                   
#  | |     | |    _/ |           | |                  
#  | | __ _| |__ |__/_  _ __ __ _| |_ ___  _ __ _   _ 
#  | |/ _` | '_ \ / _ \| '__/ _` | __/ _ \| '__| | | |
#  | | (_| | |_) | (_) | | | (_| | || (_) | |  | |_| |
#  |_|\__,_|_.__/ \___/|_|  \__,_|\__\___/|_|   \__, |
#                                                __/ |
#                                               |___/ 
#  https://github.com/nutjob-laboratories
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

SSL_AVAILABLE = True

import sys
import random
import string
from collections import defaultdict
import time
import fnmatch
import re

from .resources import *
from .files import *
from .strings import *
from .objects import *
from . import config
from . import events
from . import userinput

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore

from .dialogs import(
	NeterrorDialog
	)

from twisted.internet import reactor, protocol

try:
	from twisted.internet import ssl
except ImportError as error:
	SSL_AVAILABLE = False
except Exception as exception:
	pass

from twisted.words.protocols import irc
from twisted.words.protocols.irc import ctcpStringify

SCRIPT_WINDOW = None

def connect(**kwargs):
	bot = IRC_Connection_Factory(**kwargs)
	reactor.connectTCP(kwargs["server"],kwargs["port"],bot)

def connectSSL(**kwargs):
	bot = IRC_Connection_Factory(**kwargs)
	reactor.connectSSL(kwargs["server"],kwargs["port"],bot,ssl.ClientContextFactory())

def reconnect(**kwargs):
	bot = IRC_ReConnection_Factory(**kwargs)
	reactor.connectTCP(kwargs["server"],kwargs["port"],bot)

def reconnectSSL(**kwargs):
	bot = IRC_ReConnection_Factory(**kwargs)
	reactor.connectSSL(kwargs["server"],kwargs["port"],bot,ssl.ClientContextFactory())

client = None

def generateID(tlength=16):
	letters = string.ascii_letters
	return ''.join(random.choice(letters) for i in range(tlength))

# =====================================
# | TWISTED IRC CONNECTION MANAGEMENT |
# =====================================

class IRC_Connection(irc.IRCClient):
	nickname = 'bot'
	realname = 'bot'
	username = 'bot'

	versionName = APPLICATION_NAME
	versionNum = APPLICATION_VERSION
	sourceURL = OFFICIAL_REPOSITORY

	heartbeatInterval = 120

	def ctcpUnknownQuery(self, user, channel, tag, data):

		events.received_unknown_ctcp_message(self.gui,self,user,channel,tag,data)

		return irc.IRCClient.ctcpUnknownQuery(self, user, channel, tag, data)

	def irc_RPL_AWAY(self,prefix,params):
		user = params[1]
		msg = params[2]

		# Make sure to not display the away message
		# if the reason why we're receiving it is
		# because of an automatic "whois" request
		for nick in self.request_whois:
			if nick==user: return

		
		events.user_away(self.gui,self,user,msg)

	def irc_RPL_UNAWAY(self,prefix,params):
		msg = params[1]

		self.is_away = False
		events.build_connection_display(self.gui)

	def irc_RPL_NOWAWAY(self,prefix,params):

		msg = params[1]

		self.is_away = True
		events.build_connection_display(self.gui)

	def irc_RPL_BANLIST(self,prefix,params):
		channel = params[1]
		ban = params[2]
		banner = params[3]

		e = [ban,banner]
		self.banlists[channel].append(e)

	def irc_RPL_ENDOFBANLIST(self,prefix,params):
		channel = params[1]

		banlist = []
		if channel in self.banlists:
			banlist = self.banlists[channel]
			self.banlists[channel] = []

		events.banlist(self.gui,self,channel,banlist)

	def isupport(self,options):
		self.options = options

		for o in options:
			p = o.split('=')
			if len(p)==2:
				if p[0].lower()=='network':
					self.network = p[1]

		self.server_options(options)

		events.server_options(self.gui,self,options)

	def __init__(self,**kwargs):

		self.kwargs = kwargs

		objectconfig(self,**kwargs)

		self.script = None

		self.oldnick = self.nickname

		self.id = generateID()
		self.network = 'Unknown'

		self.userlists = defaultdict(list)
		self.banlists = defaultdict(list)

		self.whois = {}

		self.whowas = {}

		self.who = {}

		self.is_away = False

		self.uptime = 0

		self.joined_channels = []
		self.do_whois = []
		self.request_whois = []

		self.registered = False

		self.flat_motd = ''

		self.last_tried_nickname = ''

		# BEGIN SERVER INFO

		self.maxnicklen = 0
		self.maxchannels = 0
		self.channellen = 0
		self.topiclen = 0
		self.kicklen = 0
		self.awaylen = 0
		self.maxtargets = 0
		self.casemapping = ""
		self.cmds = []
		self.prefix = []
		self.chanmodes = []
		self.supports = []
		self.modes = 0
		self.maxmodes = []

		self.safelist = False

		self.channels = []
		self.channellist = []

		self.last_fetch = 0

		self.list_requested = False
		self.list_window = None
		self.list_search = None

		# END SERVER INFO

		entry = [self.server,self.port]
		self.gui.connecting.append(entry)
		self.gui.start_spinner()

		events.startup(self.gui,self)

	def uptime_beat(self):

		self.uptime = self.uptime + 1

		events.uptime(self.gui,self,self.uptime)

		if config.GET_HOSTMASKS_ON_CHANNEL_JOIN:
			if len(self.do_whois)>0:
				nick = self.do_whois.pop(0)
				if len(nick.strip())>0:
					self.request_whois.append(nick)
					self.sendLine("WHOIS "+nick)

		# Refresh internal userlist
		if config.AUTOMATICALLY_FETCH_CHANNEL_LIST:
			if self.uptime % config.CHANNEL_LIST_REFRESH_FREQUENCY==0:
				self.sendLine("LIST")
				self.last_fetch = self.uptime

	def connectionMade(self):

		# PROTOCTL UHNAMES
		self.sendLine("PROTOCTL UHNAMES")

		try:
			self.gui._erk_net_connection_lost.close()
		except:
			pass

		events.connection(self.gui,self)

		irc.IRCClient.connectionMade(self)

	def connectionLost(self, reason):

		if hasattr(self,"uptimeTimer"):
			self.uptimeTimer.stop()
			self.uptime = 0
		# else:
		# 	print("Error connecting to server")

		self.last_tried_nickname = ''

		self.registered = False

		try:
			self.gui._erk_net_connection_lost.close()
		except:
			pass

		events.disconnection(self.gui,self)

		irc.IRCClient.connectionLost(self, reason)

	def signedOn(self):

		events.registered(self.gui,self)

		self.uptimeTimer = UptimeHeartbeat()
		self.uptimeTimer.beat.connect(self.uptime_beat)
		self.uptimeTimer.start()

		self.registered = True

		if len(self.autojoin)>0:
			for channel in self.autojoin:
				chan = channel[0]
				key = channel[1]
				if len(key)>0:
					self.sendLine(f"JOIN {chan} {key}")
				else:
					self.sendLine(f"JOIN {chan}")

		# Execute auto-script
		if self.kwargs['script']!=None:

			if not self.gui.block_scripts:

				global SCRIPT_WINDOW
				SCRIPT_WINDOW = events.fetch_console_window(self)
				self.scriptThread = ScriptThread(self.kwargs['script'],dict(userinput.VARIABLE_TABLE))
				self.scriptThread.execLine.connect(self.execute_script_line)
				self.scriptThread.scriptEnd.connect(self.execute_script_end)
				self.scriptThread.start()

	def execute_script_line(self,line):
		userinput.handle_input(SCRIPT_WINDOW,self,line)

	def execute_script_end(self,vtable):
		global SCRIPT_WINDOW
		SCRIPT_WINDOW = None

		if config.GLOBALIZE_ALL_SCRIPT_ALIASES:
			userinput.VARIABLE_TABLE.update(vtable)

	def joined(self, channel):
		self.sendLine(f"MODE {channel}")
		self.sendLine(f"MODE {channel} +b")

		self.joined_channels.append(channel)

		events.erk_joined_channel(self.gui,self,channel)

		self.autojoin.append( [channel,''] )

	def left(self, channel):

		events.erk_left_channel(self.gui,self,channel)

		clean = []
		for c in self.joined_channels:
			if c==channel: continue
			clean.append(c)
		self.joined_channels = clean

		clean = []
		for c in self.autojoin:
			if c[0]==channel: continue
			clean.append(c)
		self.autojoin = clean

	def privmsg(self, user, target, msg):
		pnick = user.split('!')[0]
		phostmask = user.split('!')[1]

		if target==self.nickname:
			events.private_message(self.gui,self,user,msg)
		else:
			events.public_message(self.gui,self,target,user,msg)

	def noticed(self, user, channel, msg):
		tok = user.split('!')
		if len(tok) >= 2:
			pnick = tok[0]
			phostmask = tok[1]
		else:
			pnick = user
			phostmask = user

		events.notice_message(self.gui,self,channel,user,msg)

	def receivedMOTD(self, motd):
		events.motd(self.gui,self,motd)

	def modeChanged(self, user, channel, mset, modes, args):
		if "b" in modes: self.sendLine(f"MODE {channel} +b")
		if "o" in modes: self.sendLine("NAMES "+channel)
		if "v" in modes: self.sendLine("NAMES "+channel)

		events.mode(self.gui,self,channel,user,mset,modes,args)

		for m in modes:
			if m=='k':
				if mset:
					# Update autojoins
					if len(self.autojoin)>0:
						chans = []
						changed = False
						key=args[0]
						for c in self.autojoin:
							chan = c[0]
							ckey = c[1]
							if chan==channel:
								changed = True
								e = [channel,key]
								chans.append(e)
								continue
							chans.append(c)
						if changed: self.autojoin = chans
				else:
					if len(self.autojoin)>0:
						chans = []
						changed = False
						for c in self.autojoin:
							chan = c[0]
							ckey = c[1]
							if chan==channel:
								changed = True
								e = [channel,'']
								chans.append(e)
								continue
							chans.append(c)
						if changed: self.autojoin = chans

		
		
	def nickChanged(self,nick):
		self.nickname = nick

		events.erk_changed_nick(self.gui,self,nick)

		for c in events.fetch_channel_list(self):
			self.sendLine("NAMES "+c)

	def userJoined(self, user, channel):
		if user.split('!')[0] == self.nickname:
			return

		p = user.split('!')
		if len(p)==2:
			if p[0] == self.nickname: return
		else:
			if config.GET_HOSTMASKS_ON_CHANNEL_JOIN:
				self.do_whois.append(user)

		events.join(self.gui,self,user,channel)

		self.sendLine("NAMES "+channel)

	def userLeft(self, user, channel):

		events.part(self.gui,self,user,channel)

		self.sendLine("NAMES "+channel)

	def left(self,channel):
		events.close_channel_window(self,channel,None)

	def irc_ERR_NICKNAMEINUSE(self, prefix, params):

		if self.registered:
			# Since we're already registered, just
			# let the user know that the desired nickname
			# is already in use
			events.erk_nickname_in_use(self.gui,self,params[1])
			return

		oldnick = params[1]

		if self.last_tried_nickname=='':
			self.last_tried_nickname = self.alternate
			self.setNick(self.alternate)
			events.erk_changed_nick(self.gui,self,self.alternate)
			return

		rannum = random.randrange(1,99)

		self.last_tried_nickname = self.last_tried_nickname + str(rannum)
		self.setNick(self.last_tried_nickname)
		events.erk_changed_nick(self.gui,self,self.last_tried_nickname)

	def userRenamed(self, oldname, newname):

		for c in events.where_is_user(self,oldname):
			self.sendLine("NAMES "+c)

		events.nick(self.gui,self,oldname,newname)
					
	def topicUpdated(self, user, channel, newTopic):
		
		events.topic(self.gui,self,user,channel,newTopic)

	def action(self, user, channel, data):
		pnick = user.split('!')[0]
		phostmask = user.split('!')[1]
		
		events.action_message(self.gui,self,channel,user,data)

	def userKicked(self, kickee, channel, kicker, message):
		self.sendLine("NAMES "+channel)

		msg = Message(SYSTEM_MESSAGE,'',kickee+" was kicked from "+channel+" by "+kicker+" ("+message+")")

		win = events.fetch_console_window(self)
		if win:
			win.writeText( msg )

		win = events.fetch_channel_window(self,channel)
		if win:
			win.writeText( msg )

	def kickedFrom(self, channel, kicker, message):

		events.kicked_channel_window(self,channel)

		win = events.fetch_console_window(self)
		if win:
			win.writeText( Message(SYSTEM_MESSAGE,'',"You were kicked from "+channel+" by "+kicker+" ("+message+")") )

	def irc_QUIT(self,prefix,params):
		x = prefix.split('!')
		if len(x) >= 2:
			nick = x[0]
		else:
			nick = prefix
		if len(params) >=1:
			m = params[0].split(':')
			if len(m)>=2:
				msg = m[1].strip()
			else:
				msg = ""
		else:
			msg = ""

		for c in events.where_is_user(self,nick):
			self.sendLine("NAMES "+c)

		events.quit(self.gui,self,nick,msg)

	def irc_RPL_NAMREPLY(self, prefix, params):
		channel = params[2].lower()
		nicklist = params[3].split(' ')

		if channel in self.joined_channels:
			if config.GET_HOSTMASKS_ON_CHANNEL_JOIN:
				for u in nicklist:
					p = u.split('!')
					if len(p)!=2:
						u = u.replace('@','')
						u = u.replace('+','')
						if not events.channel_has_hostmask(self.gui,self,channel,u):
							self.do_whois.append(u)

		if channel in self.userlists:
			# Add to user list
			self.userlists[channel] = self.userlists[channel] + nicklist
			# Remove duplicates
			self.userlists[channel] = list(dict.fromkeys(self.userlists[channel]))
		else:
			self.userlists[channel] = nicklist

	def irc_RPL_ENDOFNAMES(self, prefix, params):

		channel = params[1].lower()

		try:
			self.joined_channels.remove(channel)
		except:
			pass

		if channel in self.userlists:
			events.userlist(self.gui,self,channel,self.userlists[channel])
			del self.userlists[channel]

	def irc_RPL_TOPIC(self, prefix, params):
		if not params[2].isspace():
			TOPIC = params[2]
		else:
			TOPIC = ""

		channel = params[1]

		events.topic(self.gui,self,'',channel,TOPIC)

	def irc_RPL_WHOISCHANNELS(self, prefix, params):
		params.pop(0)
		nick = params.pop(0)
		channels = ", ".join(params)

		if nick in self.request_whois: return

		if nick in self.whois:
			self.whois[nick].channels = channels
		else:
			self.whois[nick] = WhoisData()
			self.whois[nick].nickname = nick
			self.whois[nick].channels = channels

	def irc_RPL_WHOISUSER(self, prefix, params):
		nick = params[1]
		username = params[2]
		host = params[3]
		realname = params[5]

		if nick in self.request_whois:
			events.received_hostmask_for_channel_user(self.gui,self,nick,username+"@"+host)
			return

		if nick in self.whois:
			self.whois[nick].username = username
			self.whois[nick].host = host
			self.whois[nick].realname = realname
		else:
			self.whois[nick] = WhoisData()
			self.whois[nick].nickname = nick
			self.whois[nick].username = username
			self.whois[nick].host = host
			self.whois[nick].realname = realname

	def irc_RPL_WHOISIDLE(self, prefix, params):
		params.pop(0)
		nick = params.pop(0)
		idle_time = params.pop(0)
		signed_on = params.pop(0)

		if nick in self.request_whois: return

		if nick in self.whois:
			self.whois[nick].idle = idle_time
			self.whois[nick].signon = signed_on
		else:
			self.whois[nick] = WhoisData()
			self.whois[nick].nickname = nick
			self.whois[nick].idle = idle_time
			self.whois[nick].signon = signed_on

	def irc_RPL_WHOISSERVER(self, prefix, params):
		nick = params[1]
		server = params[2]

		if nick in self.request_whois: return

		if nick in self.whois:
			self.whois[nick].server = server
		else:
			self.whois[nick] = WhoisData()
			self.whois[nick].nickname = nick
			self.whois[nick].server = server

	def irc_RPL_WHOISOPERATOR(self,prefix,params):
		nick = params[1]
		privs = params[2]

		if nick in self.request_whois: return

		if nick in self.whois:
			self.whois[nick].privs = privs
		else:
			self.whois[nick] = WhoisData()
			self.whois[nick].nickname = nick
			self.whois[nick].privs = privs

	def irc_RPL_ENDOFWHOIS(self, prefix, params):
		nick = params[1]

		if nick in self.request_whois:
			try:
				self.request_whois.remove(nick)
			except:
				pass
			return

		if nick in self.whois:
			events.received_whois(self.gui,self,self.whois[nick])
			del self.whois[nick]

	def irc_RPL_WHOWASUSER(self, prefix, params):
		nick = params[1]
		username = params[2]
		host = params[3]
		realname = params[5]

		if nick in self.whowas:
			entry = [username,host,realname]
			self.whowas[nick].append(entry)
		else:
			self.whowas[nick] = []
			entry = [username,host,realname]
			self.whowas[nick].append(entry)

	def irc_RPL_ENDOFWHOWAS(self, prefix, params):
		nick = params[1]

		if nick in self.whowas:
			replies = self.whowas[nick]
			del self.whowas[nick]
			events.received_whowas(self.gui,self,nick,replies)

	def irc_RPL_WHOREPLY(self, prefix, params):
		channel = params[1]
		username = params[2]
		host = params[3]
		server = params[4]
		nick = params[5]
		hr = params[7].split(' ')

		if nick in self.who:
			self.who[nick].append([channel,username,host,server])
		else:
			self.who[nick] = []
			self.who[nick].append([channel,username,host,server])


	def irc_RPL_ENDOFWHO(self, prefix, params):
		nick = params[1]

		if nick in self.who:
			replies = self.who[nick]
			del self.who[nick]
			events.received_who(self.gui,self,nick,replies)

	def irc_RPL_VERSION(self, prefix, params):
		sversion = params[1]
		server = params[2]

		events.received_version(self.gui,self,server,sversion)

	def irc_RPL_CHANNELMODEIS(self, prefix, params):
		params.pop(0)
		channel = params.pop(0)

		for m in params:
			if len(m)>0:
				if m[0] == "+":
					m = m[1:]

					if m=="k":
						params.pop(0)
						chankey = params.pop(0)
						events.mode(self.gui,self,channel,self.hostname,True,m,[chankey])

						# Update autojoins
						if len(self.autojoin)>0:
							chans = []
							changed = False
							for c in self.autojoin:
								chan = c[0]
								key = c[1]
								if chan==channel:
									changed = True
									e = [channel,chankey]
									chans.append(e)
									continue
								chans.append(c)
							if changed: self.autojoin = chans
						continue
					# mode added
					events.mode(self.gui,self,channel,self.hostname,True,m,[])
				else:
					m = m[1:]
					# mode removed
					events.mode(self.gui,self,channel,self.hostname,False,m,[])

					# Update autojoins
					if m=="k":
						if len(self.autojoin)>0:
							chans = []
							changed = False
							for c in self.autojoin:
								chan = c[0]
								key = c[1]
								if chan==channel:
									changed = True
									e = [channel,'']
									chans.append(e)
									continue
								chans.append(c)
							if changed: self.autojoin = chans

	def irc_RPL_YOUREOPER(self, prefix, params):
		
		events.erk_youre_oper(self.gui,self)

	def irc_INVITE(self,prefix,params):
		p = prefix.split("!")
		if len(p)==2:
			nick = p[0]
			hostmask = p[1]
		else:
			nick = prefix
			hostmask = None

		target = params[0]
		channel = params[1]

		events.erk_invited(self.gui,self,prefix,channel)
		
	def irc_RPL_INVITING(self,prefix,params):
		user = params[1]
		channel = params[2]

		events.erk_inviting(self.gui,self,user,channel)

	def irc_RPL_LIST(self,prefix,params):

		server = prefix
		channel = params[1]
		usercount = params[2]
		topic = params[3]

		self.channels.append(channel)
		e = ChannelInfo(channel,usercount,topic)
		self.channellist.append(e)

		if self.list_requested:
			
			found = False
			if self.list_search!=None:
				if fnmatch.fnmatch(e.name,self.list_search): found = True
				if fnmatch.fnmatch(e.topic,self.list_search): found = True

			if self.list_search!=None:
				if not found: return

			if len(e.topic.strip())>0:
				msg = Message(PLUGIN_MESSAGE,'',"<a href=\""+e.name+"\">"+e.name+"</a> ("+str(e.count)+" users) - "+e.topic)
			else:
				msg = Message(PLUGIN_MESSAGE,'',"<a href=\""+e.name+"\">"+e.name+"</a> ("+str(e.count)+" users)")
			self.list_window.writeText(msg,True)


	def irc_RPL_LISTSTART(self,prefix,params):
		server = prefix

		self.channels = []
		self.channellist= []

		self.last_fetch = self.uptime

		if self.list_requested:

			msg = Message(HORIZONTAL_RULE_MESSAGE,'','')
			self.list_window.writeText(msg,True)

			if self.list_search!=None:
				msg = Message(PLUGIN_MESSAGE,'',"Channels with <b><i>"+self.list_search+"</i></b> in the name or topic")
				self.list_window.writeText(msg,True)

	def irc_RPL_LISTEND(self,prefix,params):
		server = prefix

		self.list_requested = False
		self.list_window = None
		self.list_search = None

	def irc_RPL_TIME(self,prefix,params):

		server = params[1]
		time = params[2]

		events.received_time(self.gui,self,params[1],params[2])

	def irc_RPL_USERHOST(self,prefix,params):
		data = params[1]

	def sendLine(self,line):

		events.line_output(self.gui,self,line)

		return irc.IRCClient.sendLine(self, line)

	def irc_ERR_NOSUCHNICK(self,prefix,params):
		events.received_error(self.gui,self,params[1]+": "+params[2])

	def irc_ERR_NOSUCHSERVER(self,prefix,params):
		events.received_error(self.gui,self,params[1]+": "+params[2])

	def irc_ERR_NOSUCHCHANNEL(self,prefix,params):
		events.received_error(self.gui,self,params[1]+": "+params[2])

	def irc_ERR_CANNOTSENDTOCHAN(self,prefix,params):
		events.received_error(self.gui,self,params[1]+": "+params[2])


	def msg(self,target,msg,write=True):

		if write:
			found = False
			for window in events.fetch_window_list(self):
				if window.name==target:
					out = Message(SELF_MESSAGE,self.nickname,msg)
					window.writeText(out)
					found = True

			if not found:
				if target[:1]!='#' and target[:1]!='&' and target[:1]!='!' and target[:1]!='+':
					# target is not a channel
					if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
						w = events.open_private_window(self,target)
						if w:
							out = Message(SELF_MESSAGE,self.nickname,msg)
							w.writeText(out)

		return irc.IRCClient.msg(self, target, msg)

	def describe(self,target,msg,write=True):

		if write:
			found = False
			for window in events.fetch_window_list(self):
				if window.name==target:
					out = Message(ACTION_MESSAGE,self.nickname,msg)
					window.writeText(out)
					found = True

			if not found:
				if target[:1]!='#' and target[:1]!='&' and target[:1]!='!' and target[:1]!='+':
					# target is not a channel
					if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
						w = events.open_private_window(self,target)
						if w:
							out = Message(ACTION_MESSAGE,self.nickname,msg)
							w.writeText(out)

		return irc.IRCClient.describe(self, target, msg)

	def notice(self,target,msg,write=True):

		if write:
			found = False
			for window in events.fetch_window_list(self):
				if window.name==target:
					out = Message(NOTICE_MESSAGE,self.nickname,msg)
					window.writeText(out)
					found = True

			if not found:
				if target[:1]!='#' and target[:1]!='&' and target[:1]!='!' and target[:1]!='+':
					# target is not a channel
					if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
						w = events.open_private_window(self,target)
						if w:
							out = Message(NOTICE_MESSAGE,self.nickname,msg)
							w.writeText(out)

		return irc.IRCClient.notice(self, target, msg)

	def ctcpMakeReply(self, user, messages):
		"""
		Send one or more C{extended messages} as a CTCP reply.
		@type messages: a list of extended messages.  An extended
		message is a (tag, data) tuple, where 'data' may be C{None}.
		"""
		self.notice(user, ctcpStringify(messages),False)

	def ctcpMakeQuery(self, user, messages):
		"""
		Send one or more C{extended messages} as a CTCP query.
		@type messages: a list of extended messages.  An extended
		message is a (tag, data) tuple, where 'data' may be C{None}.
		"""
		self.msg(user, ctcpStringify(messages), False)

	def lineReceived(self, line):

		# Decode the incoming text line
		try:
			line2 = line.decode('utf-8')
		except UnicodeDecodeError:
			try:
				line2 = line.decode('iso-8859-1')
			except UnicodeDecodeError:
				line2 = line.decode("CP1252", 'replace')

		# Re-encode the text line to utf-8 for all other
		# IRC events (this fixes an error raised when attempting
		# to get a channel list from a server)
		line = line2.encode('utf-8')

		events.line_input(self.gui,self,line2)

		d = line2.split(" ")
		if len(d) >= 2:
			if d[1].isalpha(): return irc.IRCClient.lineReceived(self, line)

		if "Cannot join channel (+k)" in line2:
			events.received_error(self.gui,self,f"Cannot join channel (wrong or missing password)")
			pass
		if "Cannot join channel (+l)" in line2:
			events.received_error(self.gui,self,f"Cannot join channel (channel is full)")
			pass
		if "Cannot join channel (+b)" in line2:
			events.received_error(self.gui,self,f"Cannot join channel (banned)")
			pass
		if "Cannot join channel (+i)" in line2:
			events.received_error(self.gui,self,f"Cannot join channel (channel is invite only)")
			pass
		if "not an IRC operator" in line2:
			events.received_error(self.gui,self,"Permission denied (you're not an IRC operator")
			pass
		if "not channel operator" in line2:
			events.received_error(self.gui,self,"Permission denied (you're not channel operator)")
			pass
		if "is already on channel" in line2:
			events.received_error(self.gui,self,"Invite failed (user is already in channel)")
			pass
		if "not on that channel" in line2:
			events.received_error(self.gui,self,"Permission denied (you're not in channel)")
			pass
		if "aren't on that channel" in line2:
			events.received_error(self.gui,self,"Permission denied (target user is not in channel)")
			pass
		if "have not registered" in line2:
			events.received_error(self.gui,self,"You're not registered")
			pass
		if "may not reregister" in line2:
			events.received_error(self.gui,self,"You can't reregister")
			pass
		if "enough parameters" in line2:
			events.received_error(self.gui,self,"Error: not enough parameters supplied to command")
			pass
		if "isn't among the privileged" in line2:
			events.received_error(self.gui,self,"Registration refused (server isn't setup to allow connections from your host)")
			pass
		if "Password incorrect" in line2:
			events.received_error(self.gui,self,"Permission denied (incorrect password)")
			pass
		if "banned from this server" in line2:
			events.received_error(self.gui,self,"You are banned from this server")
			pass
		if "kill a server" in line2:
			events.received_error(self.gui,self,"Permission denied (you can't kill a server)")
			pass
		if "O-lines for your host" in line2:
			events.received_error(self.gui,self,"Error: no O-lines for your host")
			pass
		if "Unknown MODE flag" in line2:
			events.received_error(self.gui,self,"Error: unknown MODE flag")
			pass
		if "change mode for other users" in line2:
			events.received_error(self.gui,self,"Permission denied (can't change mode for other users)")
			pass

		return irc.IRCClient.lineReceived(self, line)

	# BEGIN SERVER OPTIONS

	def server_options(self,options):

		# Options are sent in chunks: not every option
		# will be set in each chunk

		supports = []
		maxchannels = 0
		maxnicklen = 0
		nicklen = 0
		channellen = 0
		topiclen = 0
		kicklen = 0
		awaylen = 0
		maxtargets = 0
		modes = 0
		maxmodes = []
		chanmodes = []
		prefix = []
		cmds = []
		casemapping = "none"

		for o in options:
			if "=" in o:
				p = o.split("=")
				if len(p)>1:
					if p[0].lower() == "maxchannels": maxchannels = int(p[1])
					if p[0].lower() == "maxnicklen": maxnicklen = int(p[1])
					if p[0].lower() == "nicklen": nicklen = int(p[1])
					if p[0].lower() == "channellen": channellen = int(p[1])
					if p[0].lower() == "topiclen": topiclen = int(p[1])
					if p[0].lower() == "kicklen": kicklen = int(p[1])
					if p[0].lower() == "awaylen": awaylen = int(p[1])
					if p[0].lower() == "maxtargets": maxtargets = int(p[1])
					if p[0].lower() == "modes": modes = int(p[1])
					if p[0].lower() == "casemapping": casemapping = p[1]

					if p[0].lower() == "cmds":
						for c in p[1].split(","):
							cmds.append(c)

					if p[0].lower() == "prefix":
						pl = p[1].split(")")
						if len(pl)>=2:
							pl[0] = pl[0][1:]	# get rid of prefixed (

							for i in range(len(pl[0])):
								entry = [ pl[0][i], pl[1][i] ]
								prefix.append(entry)

					if p[0].lower() == "chanmodes":
						for e in p[1].split(","):
							chanmodes.append(e)

					if p[0].lower() == "maxlist":
						for e in p[1].split(","):
							ml = e.split(':')
							if len(ml)==2:
								entry = [ml[0],int(ml[1])]
								maxmodes.append(entry)
			else:
				supports.append(o)

		if len(maxmodes)>0: self.maxmodes = maxmodes
		if maxnicklen>0: self.maxnicklen = maxnicklen
		if maxchannels > 0: self.maxchannels = maxchannels
		if channellen > 0: self.channellen = channellen
		if topiclen > 0: self.topiclen = topiclen
		if kicklen > 0: self.kicklen = kicklen
		if awaylen > 0: self.awaylen = awaylen
		if maxtargets > 0: self.maxtargets = maxtargets
		if modes > 0: self.modes = modes
		if casemapping != "": self.casemapping = casemapping

		if len(cmds)>0:
			for c in cmds:
				self.cmds.append(c)

		if len(prefix)>0: self.prefix = prefix
		if len(chanmodes)>0: self.chanmodes = chanmodes
		if len(supports)>0:
			for s in supports:
				self.supports.append(s)

		if config.AUTOMATICALLY_FETCH_CHANNEL_LIST:
			if 'SAFELIST' in self.supports:
				if not self.safelist:
					self.safelist = True
					self.sendLine("LIST")

	# BEGIN SERVER OPTIONS


def objectconfig(obj,**kwargs):

	for key, value in kwargs.items():

		if key=="nickname":
			obj.nickname = value
		
		if key=="alternate":
			obj.alternate = value

		if key=="username":
			obj.username = value

		if key=="realname":
			obj.realname = value

		if key=="server":
			obj.server = value

		if key=="port":
			obj.port = value

		if key=="ssl":
			obj.usessl = value

		if key=="password":
			obj.password = value

		if key=="gui":
			obj.gui = value

		if key=="reconnect":
			obj.reconnect = value

		if key=="autojoin":
			obj.autojoin = value

		if key=="failreconnect":
			obj.failreconnect = value

		if key=="script":
			obj.script = value

class IRC_Connection_Factory(protocol.ClientFactory):
	def __init__(self,**kwargs):
		self.kwargs = kwargs

	def buildProtocol(self, addr):
		bot = IRC_Connection(**self.kwargs)
		bot.factory = self
		return bot

	def clientConnectionLost(self, connector, reason):

		show_dialog = True

		if self.kwargs["gui"].erk_is_quitting: show_dialog = False

		cid = self.kwargs["server"]+str(self.kwargs["port"])
		if cid in self.kwargs["gui"].quitting:
			show_dialog = False
			try:
				self.kwargs["gui"].quitting.remove(cid)
			except:
				pass
			return

		if config.SHOW_CONNECTION_LOST_ERROR:
			if show_dialog:
				self.kwargs["gui"]._erk_net_connection_lost = NeterrorDialog("Connection lost",f'Connection to {self.kwargs["server"]}:{str(self.kwargs["port"])} was lost.')
				self.kwargs["gui"]._erk_net_connection_lost.server = self.kwargs["server"]
				self.kwargs["gui"]._erk_net_connection_lost.port = self.kwargs["port"]

	def clientConnectionFailed(self, connector, reason):

		show_dialog = True

		if self.kwargs["gui"].erk_is_quitting: show_dialog = False

		cid = self.kwargs["server"]+str(self.kwargs["port"])
		if cid in self.kwargs["gui"].quitting:
			show_dialog = False
			try:
				self.kwargs["gui"].quitting.remove(cid)
			except:
				pass
			return

		if config.SHOW_CONNECTION_FAIL_ERROR:
			if show_dialog:
				self.kwargs["gui"]._erk_net_connection_lost = NeterrorDialog("Connection failed",f'Connection to {self.kwargs["server"]}:{str(self.kwargs["port"])} could not be established.')
				self.kwargs["gui"]._erk_net_connection_lost.server = self.kwargs["server"]
				self.kwargs["gui"]._erk_net_connection_lost.port = self.kwargs["port"]


class IRC_ReConnection_Factory(protocol.ReconnectingClientFactory):
	def __init__(self,**kwargs):
		self.kwargs = kwargs

	def buildProtocol(self, addr):
		bot = IRC_Connection(**self.kwargs)
		bot.factory = self
		return bot

	def clientConnectionLost(self, connector, reason):

		show_dialog = True

		if self.kwargs["gui"].erk_is_quitting: show_dialog = False

		cid = self.kwargs["server"]+str(self.kwargs["port"])
		if cid in self.kwargs["gui"].quitting:
			show_dialog = False
			try:
				self.kwargs["gui"].quitting.remove(cid)
			except:
				pass
			return

		if config.SHOW_CONNECTION_LOST_ERROR:
			if show_dialog:
				self.kwargs["gui"]._erk_net_connection_lost = NeterrorDialog("Connection lost",f'Connection to {self.kwargs["server"]}:{str(self.kwargs["port"])} was lost.')
				self.kwargs["gui"]._erk_net_connection_lost.server = self.kwargs["server"]
				self.kwargs["gui"]._erk_net_connection_lost.port = self.kwargs["port"]

		protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def clientConnectionFailed(self, connector, reason):

		show_dialog = True

		if self.kwargs["gui"].erk_is_quitting: show_dialog = False

		cid = self.kwargs["server"]+str(self.kwargs["port"])
		if cid in self.kwargs["gui"].quitting:
			show_dialog = False
			try:
				self.kwargs["gui"].quitting.remove(cid)
			except:
				pass
			return

		if config.SHOW_CONNECTION_FAIL_ERROR:
			if show_dialog:
				self.kwargs["gui"]._erk_net_connection_lost = NeterrorDialog("Connection failed",f'Connection to {self.kwargs["server"]}:{str(self.kwargs["port"])} could not be established.')
				self.kwargs["gui"]._erk_net_connection_lost.server = self.kwargs["server"]
				self.kwargs["gui"]._erk_net_connection_lost.port = self.kwargs["port"]

		if self.kwargs["failreconnect"]:
			protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

class UptimeHeartbeat(QThread):

	beat = pyqtSignal()

	def __init__(self,parent=None):
		super(UptimeHeartbeat, self).__init__(parent)
		self.threadactive = True

	def run(self):
		while self.threadactive:
			time.sleep(1)
			self.beat.emit()

	def stop(self):
		self.threadactive = False
		self.wait()

class ScriptThread(QThread):

	execLine = pyqtSignal(str)
	scriptEnd = pyqtSignal(dict)

	def __init__(self,script,variable_table,parent=None):
		super(ScriptThread, self).__init__(parent)
		self.script = script
		self.vtable = variable_table
		self.private_vtable = {}

		# Strip comments from script
		self.script = re.sub(re.compile("/\*.*?\*/",re.DOTALL ) ,"" ,self.script)

	def run(self):
		for line in self.script.split("\n"):
			line = line.strip()
			if len(line)==0: continue

			for key in self.vtable:
				line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+key,self.vtable[key])

			for key in self.private_vtable:
				line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+key,self.private_vtable[key])

			tokens = line.split()

			if len(tokens)>=3:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'alias':
					tokens.pop(0)
					var = tokens.pop(0)

					# If the interpolation symbol has been included, strip it
					interplen = len(config.SCRIPT_INTERPOLATE_SYMBOL)
					if len(var)>interplen:
						if var[0:interplen] == config.SCRIPT_INTERPOLATE_SYMBOL:
							var = var[interplen:]

					value = ' '.join(tokens)
					self.vtable[var] = value

			if len(tokens)>=3:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'_alias':
					tokens.pop(0)
					var = tokens.pop(0)

					# If the interpolation symbol has been included, strip it
					interplen = len(config.SCRIPT_INTERPOLATE_SYMBOL)
					if len(var)>interplen:
						if var[0:interplen] == config.SCRIPT_INTERPOLATE_SYMBOL:
							var = var[interplen:]

					value = ' '.join(tokens)
					self.private_vtable[var] = value

			if len(tokens)==2:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'wait' or tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'sleep':
					count = tokens[1]
					try:
						count = int(count)
					except:
						pass
					else:
						time.sleep(count)

			self.execLine.emit(line)

		self.scriptEnd.emit(self.vtable)

class ScriptThreadWindow(QThread):

	execLine = pyqtSignal(list)
	scriptEnd = pyqtSignal(list)
	scriptErr = pyqtSignal(list)
	msgBox = pyqtSignal(list)

	unalias = pyqtSignal(list)

	def __init__(self,window,client,script,mid,scriptname,variable_table,arguments,parent=None):
		super(ScriptThreadWindow, self).__init__(parent)
		self.script = script
		self.window = window
		self.client = client
		self.id = mid
		self.scriptname = scriptname

		self.vtable = variable_table
		self.arguments = arguments

		self.had_error = False

		self.private_vtable = {}

		# Strip comments from script
		self.script = re.sub(re.compile("/\*.*?\*/",re.DOTALL ) ,"" ,self.script)

	def run(self):
		for line in self.script.split("\n"):
			line = line.strip()
			if len(line)==0: continue

			# Interpolate arguments
			counter = 0
			for a in self.arguments:
				counter = counter + 1
				line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+str(counter),a)

			# Interpolate all arguments as a single string
			line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+'0',' '.join(self.arguments))

			# Interpolate alias variables
			for key in self.vtable:
				line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+key,self.vtable[key])

			# Interpolate private alias variables
			for key in self.private_vtable:
				line = line.replace(config.SCRIPT_INTERPOLATE_SYMBOL+key,self.private_vtable[key])

			tokens = line.split()

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'argcount':
					if len(tokens)<3:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}argcount in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}argcount requires at least 3 arguments"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'alias':
					if len(tokens)<3:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}alias in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}alias requires at least 3 arguments"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'_alias':
					if len(tokens)<3:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}palias in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}_alias requires at least 3 arguments"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'wait':
					if len(tokens)<2:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}wait in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}wait requires at least 1 argument"])
						self.had_error = True
						break
					if len(tokens)>2:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}wait in {self.scriptname}: Too many arguments passed to {config.INPUT_COMMAND_SYMBOL}wait"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'argcount':
					if len(tokens)<2:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}argcount in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}argcount requires at least 1 argument"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'unalias':
					if len(tokens)!=2:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}unalias in {self.scriptname}: {config.INPUT_COMMAND_SYMBOL}unalias requires only 1 argument"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'unalias' and len(tokens)==2:
					tokens.pop(0)
					ualias = tokens.pop(0)

					# If the interpolation symbol has been included, strip it
					interplen = len(config.SCRIPT_INTERPOLATE_SYMBOL)
					if len(ualias)>interplen:
						if ualias[0:interplen] == config.SCRIPT_INTERPOLATE_SYMBOL:
							ualias = ualias[interplen:]

					if ualias in self.vtable:
						self.vtable.pop(ualias)
						self.unalias.emit([self.scriptname,ualias])
					else:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}unalias in {self.scriptname}: alias \"{ualias}\" not found"])
						self.had_error = True
						break

			if len(tokens)>0:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'msgbox' and len(tokens)>=2:
					tokens.pop(0)
					text = ' '.join(tokens)
					self.msgBox.emit([self.scriptname,text])

			if len(tokens)>=3:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'argcount':
					tokens.pop(0)
					cnt = tokens.pop(0)
					try:
						cnt = int(cnt)
					except:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}argcount in {self.scriptname}: \"{str(cnt)}\" is not a number"])
						self.had_error = True
						break
					else:
						if len(self.arguments)!=cnt:
							self.scriptErr.emit([self.window,f"{' '.join(tokens)}"])
							self.had_error = True
							break

			if len(tokens)>=3:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'alias':
					tokens.pop(0)
					var = tokens.pop(0)

					# If the interpolation symbol has been included, strip it
					interplen = len(config.SCRIPT_INTERPOLATE_SYMBOL)
					if len(var)>interplen:
						if var[0:interplen] == config.SCRIPT_INTERPOLATE_SYMBOL:
							var = var[interplen:]

					value = ' '.join(tokens)
					self.vtable[var] = value

			if len(tokens)>=3:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'_alias':
					tokens.pop(0)
					var = tokens.pop(0)

					# If the interpolation symbol has been included, strip it
					interplen = len(config.SCRIPT_INTERPOLATE_SYMBOL)
					if len(var)>interplen:
						if var[0:interplen] == config.SCRIPT_INTERPOLATE_SYMBOL:
							var = var[interplen:]

					value = ' '.join(tokens)
					self.private_vtable[var] = value

			if len(tokens)==2:
				if tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'wait' or tokens[0].lower()==config.INPUT_COMMAND_SYMBOL+'sleep':
					count = tokens[1]
					try:
						count = int(count)
					except:
						self.scriptErr.emit([self.window,f"Error using {config.INPUT_COMMAND_SYMBOL}wait in {self.scriptname}: \"{count}\" is not a number"])
						self.had_error = True
						break
					else:
						time.sleep(count)

			self.execLine.emit([self.window,self.client,line])

		if not self.had_error:
			self.scriptEnd.emit([self.id,self.vtable])