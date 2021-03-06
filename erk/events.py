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

from datetime import datetime
import fnmatch

from .resources import *
from .files import *
from .widgets import *
from .objects import *
from .strings import *
from .common import *
from . import config

from . import textformat

CHANNELS = []
CONNECTIONS = []
CONSOLES = []
PRIVATES = []

UNSEEN = []

TRIGGERED = []

AUTOCOMPLETE = []

def fetch_autocompletes():
	return AUTOCOMPLETE

def add_to_autocomplete(item,replacement):
	for e in AUTOCOMPLETE:
		if e[0]==item:
			e[1] = replacement
			return

	entry = [item,replacement]
	AUTOCOMPLETE.append(entry)

def received_unknown_ctcp_message(gui,client,user,channel,tag,message):
	pass
	# if not client.gui.block_plugins:
	# 	if client.gui.plugins.ctcp(client,user,channel,tag,message): return

def toggle_userlist():
	for c in CHANNELS:
		c.widget.toggleUserlist()

def received_who(gui,client,nickname,replies):
	
	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):

			for e in replies:
				username = e[1]
				host = e[2]
				server = e[3]
				channel = e[0]

				gui.current_page.writeText( Message(WHOIS_MESSAGE,nickname, "WHO: "+username+"@"+host+": \x02"+server+", "+channel+"\x0F"), True )

def received_version(gui,client,server,version):
	
	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',server+" version: "+version  ) )

def received_whowas(gui,client,nickname,replies):
	
	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):

			for e in replies:
				username = e[0]
				host = e[1]
				realname = e[2]

				gui.current_page.writeText( Message(WHOIS_MESSAGE,nickname, "WHOWAS: "+username+"@"+host+": \x02"+realname+"\x0F"), True )

def received_time(gui,client,server,time):
	
	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',server+" time: "+time  ) )

def toggle_name_topic_display():
	for c in CHANNELS:
		c.widget.refresh_name_topic_display()

def fetch_connections():
	return CONNECTIONS

def quit_all():
	for c in CONNECTIONS:
		c.quit(config.DEFAULT_QUIT_PART_MESSAGE)

def clear_unseen(window):
	try:
		global UNSEEN
		global TRIGGERED
		clean = []
		for w in UNSEEN:
			if w.client.id==window.client.id:
				if w.name==window.name:
					continue
			clean.append(w)
		UNSEEN = clean

		clean = []
		for w in TRIGGERED:
			if w.client.id==window.client.id:
				if w.name==window.name:
					continue
			clean.append(w)
		TRIGGERED = clean
	except:
		pass

def window_has_unseen(window,gui):

	# Never mark the current window as having unseen messages
	if gui.current_page:
		if gui.current_page.client.id==window.client.id:
			if gui.current_page.name==window.name:
				return False

	for w in UNSEEN:
		if w.client.id==window.client.id:
			if w.name==window.name: return True
	return False

class PulseQTreeWidgetItem(QTreeWidgetItem):
	@property
	def animation(self):
		if not hasattr(self, "_animation"):
			self._animation = QVariantAnimation()
			self._animation.valueChanged.connect(self._on_value_changed)
			#self._animation.setLoopCount(-1)	# Loop forever
		return self._animation

	def loop_this_animation(self):
		self._animation.setLoopCount(-1)

	def _on_value_changed(self, color):
		for i in range(self.columnCount()):
			# self.setBackground(i, color)
			self.setForeground(i, color)

def animation_triggered(window):
	for w in TRIGGERED:
		if w.client.id==window.client.id:
			if w.name==window.name: return True
	return False

def build_connection_display(gui,new_server=None):

	if gui.seditors!=None:
		gui.seditors.clientsRefreshed(fetch_connections())

	global TRIGGERED

	# get system color from the text formatting
	# use orange if one is not found
	unseen_color = "#FF8C00"
	unseen_back = "#000000"
	connect_color = "#006400"
	for key in textformat.STYLES:
		if key==config.UNSEEN_ANIMATION_COLOR:
			for e in textformat.STYLES[key].split(';'):
				l = e.strip()
				l2 = l.split(':')
				if len(l2)==2:
					if l2[0].lower()=='color':
						unseen_color = l2[1].strip()
		if key=='all':
			for e in textformat.STYLES[key].split(';'):
				l = e.strip()
				l2 = l.split(':')
				if len(l2)==2:
					if l2[0].lower()=='color':
						unseen_back = l2[1].strip()

		if key==config.CONNECTION_ANIMATION_COLOR:
			for e in textformat.STYLES[key].split(';'):
				l = e.strip()
				l2 = l.split(':')
				if len(l2)==2:
					if l2[0].lower()=='color':
						connect_color = l2[1].strip()

	# Make a list of expanded server nodes, and make sure they
	# are still expanded when we rewrite the display
	expanded = []

	if config.EXPAND_SERVER_ON_CONNECT:
		if new_server: expanded.append(new_server.id)

	iterator = QTreeWidgetItemIterator(gui.connection_display)
	while True:
		item = iterator.value()
		if item is not None:
			if hasattr(item,"isExpanded"):
				if item.isExpanded():
					if hasattr(item,"erk_client"):
						expanded.append(item.erk_client.id)
			iterator += 1
		else:
			break

	clearQTreeWidget(gui.connection_display)

	servers = []

	for c in CONNECTIONS:
		channels = []
		for window in CHANNELS:
			if window.widget.client.id == c.id:
				channels.append(window.widget)

		for window in PRIVATES:
			if window.widget.client.id == c.id:
				channels.append(window.widget)

		if c.hostname:
			servers.append( [c.hostname,c,channels] )
		else:
			servers.append( ["Connecting...",c,channels] )

	root = gui.connection_display.invisibleRootItem()

	# # Set main status bar
	# slist = []
	# for e in servers:
	# 	if e[0]=="Connecting...": continue
	# 	slist.append(e[0]+" ("+e[1].nickname+")")
	# if len(slist)>0:
	# 	gui.set_status(f"{', '.join(slist)}")

	# BEGIN STARTER DISPLAY

	if len(CONSOLES)>0 or len(CHANNELS)>0 or len(PRIVATES)>0:

		gui.connection_dock.show()

	else:
		gui.connection_dock.hide()
		#gui.set_status("&nbsp;")

	# END STARTER DISPLAY

	for s in servers:

		if s[0] == "Connecting...":
			if config.CONNECTION_MESSAGE_ANIMATION:
				parent = PulseQTreeWidgetItem(root)
				parent.animation.setStartValue(QColor(unseen_back))
				parent.animation.setEndValue(QColor(connect_color))
				parent.animation.setDuration(config.CONNECTION_ANIMATION_LENGTH)
				parent.loop_this_animation()
				parent.animation.start()
			else:
				parent = QTreeWidgetItem(root)
		else:
			parent = QTreeWidgetItem(root)

		# parent.setText(0,s[0])
		parent.setText(0,s[1].server)

		if not config.CONNECTION_MESSAGE_ANIMATION:
			if s[0] == "Connecting...":
				parent.setForeground(0,QBrush(QColor(connect_color))) 

		parent.setIcon(0,QIcon(CONNECTING_ICON))
		parent.erk_client = s[1]
		parent.erk_channel = False
		parent.erk_widget = None
		parent.erk_name = None
		parent.erk_server = True
		parent.erk_console = False

		if s[0]!="Connecting...":
			if config.DISPLAY_CONNECTION_UPTIME:
				child = QTreeWidgetItem(parent)
				if s[1].id in gui.uptimers:
					child.setText(0,prettyUptime(gui.uptimers[s[1].id]))
				else:
					child.setText(0,"00:00:00")
				child.setIcon(0,QIcon(CLOCK_ICON))
				child.erk_uptime = True
				child.erk_client = s[1]
				child.erk_console = False

		if s[1].id in expanded:
			parent.setExpanded(True)

		# Add console "window"
		for c in CONSOLES:
			if c.widget.client.id == s[1].id:
				if s[0]!="Connecting...":

					parent.erk_widget = c.widget

					if c.widget.client.network:
						parent.erk_name = c.widget.client.network
						if c.widget.client.is_away:
							parent.setText(0,c.widget.client.network+" (away)")
						else:
							parent.setText(0,c.widget.client.network)
						parent.setIcon(0,QIcon(NETWORK_ICON))
					else:
						# parent.erk_name = s[0]
						parent.erk_name = s[1].server

					parent.erk_console = True

					if window_has_unseen(c.widget,gui):
						f = parent.font(0)
						f.setItalic(True)
						parent.setFont(0,f)
					
					if gui.current_page:
						if hasattr(gui.current_page,"name"):
							if gui.current_page.name==SERVER_CONSOLE_NAME:
								if gui.current_page.client.id==s[1].id:
									f = parent.font(0)
									f.setItalic(False)
									f.setBold(True)
									parent.setFont(0,f)

		for channel in s[2]:
			if config.UNSEEN_MESSAGE_ANIMATION:
				# PulseQTreeWidgetItem
				if window_has_unseen(channel,gui):
					child = PulseQTreeWidgetItem(parent)
					if not animation_triggered(channel):
						child.animation.setStartValue(QColor(unseen_back))
						child.animation.setEndValue(QColor(unseen_color))
						child.animation.setDuration(config.UNSEEN_ANIMATION_LENGTH)
						child.animation.start()
						TRIGGERED.append(channel)
					else:
						child.setForeground(0,QBrush(QColor(unseen_color))) 
				else:
					child = QTreeWidgetItem(parent)
			else:
				child = QTreeWidgetItem(parent)

			child.setText(0,channel.name)
			if channel.type==config.CHANNEL_WINDOW:
				child.erk_channel = True
				child.setIcon(0,QIcon(CHANNEL_ICON))
			elif channel.type==config.PRIVATE_WINDOW:
				child.setIcon(0,QIcon(NICK_ICON))
				child.erk_channel = False
			child.erk_client = s[1]
			child.erk_widget = channel
			child.erk_name = channel.name
			child.erk_console = False

			if not config.UNSEEN_MESSAGE_ANIMATION:
				if window_has_unseen(channel,gui):
					child.setForeground(0,QBrush(QColor(unseen_color))) 

			if gui.current_page:
				if hasattr(gui.current_page,"name"):
					if gui.current_page.name==channel.name:
						if gui.current_page.client.id==s[1].id:
							f = child.font(0)
							f.setBold(True)
							child.setFont(0,f)

							continue

def apply_style(style):
	for c in CHANNELS:
		if not c.widget.custom_style:
			c.widget.chat.setStyleSheet(style)
			c.widget.userlist.setStyleSheet(style)
			c.widget.input.setStyleSheet(style)
	for c in PRIVATES:
		if not c.widget.custom_style:
			c.widget.chat.setStyleSheet(style)
			c.widget.input.setStyleSheet(style)
	for c in CONSOLES:
		if not c.widget.custom_style:
			c.widget.chat.setStyleSheet(style)
			c.widget.input.setStyleSheet(style)

def resize_font_fix():
	for c in CHANNELS:
		c.widget.chat.zoomIn()
		c.widget.chat.zoomOut()
		c.widget.chat.moveCursor(QTextCursor.End)
	for c in PRIVATES:
		c.widget.chat.zoomIn()
		c.widget.chat.zoomOut()
		c.widget.chat.moveCursor(QTextCursor.End)
	for c in CONSOLES:
		c.widget.chat.zoomIn()
		c.widget.chat.zoomOut()
		c.widget.chat.moveCursor(QTextCursor.End)

def rerender_all():
	for c in CHANNELS:
		c.widget.rerender()
	for c in PRIVATES:
		c.widget.rerender()
	for c in CONSOLES:
		c.widget.rerender()

def rerender_userlists():
	for c in CHANNELS:
		c.widget.rerender_userlist()

def rerender_channel_nickname():
	for c in CHANNELS:
		c.widget.channelNickVisibility()

def reset_history():
	for c in CHANNELS:
		c.widget.history_buffer = ['']
		c.widget.history_buffer_pointer = 0

def toggle_nickspell():
	for c in CHANNELS:
		c.widget.input.addNicks(c.widget.nicks)
	for c in PRIVATES:
		c.widget.input.addNicks(c.widget.nicks)
	for c in CONSOLES:
		c.widget.input.addNicks(c.widget.nicks)

def newspell_all(lang):
	for c in CHANNELS:
		c.widget.changeSpellcheckLanguage(lang)
	for c in PRIVATES:
		c.widget.changeSpellcheckLanguage(lang)
	for c in CONSOLES:
		c.widget.changeSpellcheckLanguage(lang)

def resetinput_all():
	for c in CHANNELS:
		c.widget.reset_input()
	for c in PRIVATES:
		c.widget.reset_input()
	for c in CONSOLES:
		c.widget.reset_input()

def set_fonts_all(font):
	for c in CHANNELS:
		c.widget.chat.setFont(font)
		c.widget.topic.setFont(font)
		c.widget.userlist.setFont(font)
		c.widget.input.setFont(font)
		c.widget.name_display.setFont(font)
		c.widget.nick_display.setFont(font)
	for c in PRIVATES:
		c.widget.chat.setFont(font)
		c.widget.input.setFont(font)
		c.widget.name_display.setFont(font)
	for c in CONSOLES:
		c.widget.chat.setFont(font)
		c.widget.input.setFont(font)
		c.widget.name_display.setFont(font)

def kicked_channel_window(client,name):
	global CHANNELS

	clean = []
	windex = 0
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				windex = client.gui.stack.indexOf(c.widget)
				c.widget.close()
				continue
		clean.append(c)
	CHANNELS = clean

	if len(CHANNELS)>0:
		w = None
		for c in CHANNELS:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(PRIVATES)>0:
		w = None
		for c in PRIVATES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(CONSOLES)>0:
		w = None
		for c in CONSOLES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	client.gui.stack.setCurrentWidget(client.gui.starter)
	build_connection_display(client.gui)

def using_custom_style(client,name):
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				return c.widget.custom_style

def using_custom_style_server(client):
	for c in CONSOLES:
		if c.widget.client.id == client.id:
			return c.widget.custom_style

def restore_chat_style(client,name):
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				c.widget.restoreStyle()

def restore_chat_style_server(client):
	for c in CONSOLES:
		if c.widget.client.id == client.id:
			c.widget.restoreStyle()

def load_chat_style(client,name,file,nosave=False):
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				c.widget.loadNewStyle(file,nosave)

def load_chat_style_server(client,file,nosave=False):
	for c in CONSOLES:
		if c.widget.client.id == client.id:
			c.widget.loadNewStyle(file,nosave)

def close_channel_window(client,name,msg=None):
	global CHANNELS

	clean = []
	windex = 0
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				windex = client.gui.stack.indexOf(c.widget)
				# c.widget.client.part(name,msg)
				c.widget.close()
				continue
		clean.append(c)
	CHANNELS = clean

	if len(CHANNELS)>0:
		w = None
		for c in CHANNELS:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(PRIVATES)>0:
		w = None
		for c in PRIVATES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(CONSOLES)>0:
		w = None
		for c in CONSOLES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	client.gui.stack.setCurrentWidget(client.gui.starter)
	build_connection_display(client.gui)

def close_private_window(client,name):
	global PRIVATES

	clean = []
	windex = 0
	for c in PRIVATES:
		if c.widget.client.id == client.id:
			if c.widget.name==name:
				windex = client.gui.stack.indexOf(c.widget)
				c.widget.close()
				continue
		clean.append(c)
	PRIVATES = clean

	if len(CHANNELS)>0:
		w = None
		for c in CHANNELS:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(PRIVATES)>0:
		w = None
		for c in PRIVATES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	if len(CONSOLES)>0:
		w = None
		for c in CONSOLES:
			if c.widget.client.id==client.id:
				w = c.widget
		if w:
			client.gui.stack.setCurrentWidget(w)
			build_connection_display(client.gui)
			return

	client.gui.stack.setCurrentWidget(client.gui.starter)
	build_connection_display(client.gui)

def full_nick_list(client):
	nicks = []
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			nicks = nicks + window.widget.nicks
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			if not window.widget.name in nicks:
				nicks.append(window.widget.name)
	return nicks

def fetch_window_list(client):
	wl = []
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			wl.append(window.widget)
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			wl.append(window.widget)
	return wl

def fetch_channel_window(client,channel):
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			if window.widget.name==channel:
				return window.widget
	return None

def fetch_private_window(client,channel):
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			if window.widget.name==channel:
				return window.widget
	return None

def fetch_console_window(client):
	for window in CONSOLES:
		if window.widget.client.id==client.id:
			return window.widget
	return None

def fetch_channel_list(client):
	channels = []
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			channels.append(window.widget.name)
	return channels

def fetch_private_list(client):
	channels = []
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			channels.append(window.widget.name)
	return channels

def name_to_channel(client,channel):
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			if window.widget.name==channel:
				return window.widget
	return None

def name_to_private(client,channel):
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			if window.widget.name==channel:
				return window.widget
	return None

def disable_all_runscript():
	for window in CONSOLES:
		window.widget.runScript.setEnabled(False)
		#window.widget.runScript.setVisible(False)

def enable_all_runscript():
	for window in CONSOLES:
		window.widget.runScript.setEnabled(True)
		#window.widget.runScript.setVisible(True)

def hide_all_console_buttons():
	for window in CONSOLES:
		window.widget.runScript.setVisible(False)
		window.widget.disconnectButton.setVisible(False)

def show_all_console_buttons():
	for window in CONSOLES:
		window.widget.runScript.setVisible(True)
		window.widget.disconnectButton.setVisible(True)

def open_private_window(client,target):

	window = fetch_private_window(client,target)
	if window:
		client.gui.stack.setCurrentWidget(window)
		window.input.setFocus()
		return
	else:

		newchan = Chat(
			target,
			client,
			config.PRIVATE_WINDOW,
			client.gui.app,
			client.gui
			)

		index = client.gui.stack.addWidget(newchan)
		if config.SWITCH_TO_NEW_WINDOWS:
			client.gui.stack.setCurrentWidget(newchan)
			newchan.input.setFocus()

		PRIVATES.append( Window(index,newchan) )

		# Update connection display
		build_connection_display(client.gui)

		if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
			newchan.input.setFocus()

		return newchan

def where_is_user(client,nick):
	channels = []
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			if nick in window.widget.nicks:
				channels.append(window.widget.name)
			
	return channels

def channel_has_hostmask(gui,client,channel,user):

	window = fetch_channel_window(client,channel)
	if window:
		if user in window.hostmasks: return True
		return False

	# Window not found, so return true
	return True

def line_output(gui,client,line):
	pass
	
	# if not client.gui.block_plugins:
	# 	client.gui.plugins.line_out(client,line)

def line_input(gui,client,line):
	pass
	
	# if not client.gui.block_plugins:
	# 	client.gui.plugins.line_in(client,line)

def received_error(gui,client,error):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(ERROR_MESSAGE,'',error), True )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(ERROR_MESSAGE,'',error) )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def user_away(gui,client,user,msg):
	# print(user +" "+ msg)

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',user+" is away ("+msg+")") )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',user+" is away ("+msg+")") )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def mode(gui,client,channel,user,mset,modes,args):
	
	if len(modes)<1: return

	# if not client.gui.block_plugins:
	# 	client.gui.plugins.mode(client,channel,user,mset,modes,args)

	args = list(args)
	cleaned = []
	for a in args:
		if a == None: continue
		cleaned.append(a)
	args = cleaned

	p = user.split('!')
	if len(p)==2:
		user = p[0]

	if channel==client.nickname:
		if mset:
			msg = Message(SYSTEM_MESSAGE,'',"Mode +"+modes+" set on "+channel,None,TYPE_MODE)
		else:
			msg = Message(SYSTEM_MESSAGE,'',"Mode -"+modes+" set on "+channel,None,TYPE_MODE)
		window = fetch_console_window(client)
		if window:
			window.writeText( msg )
		return

	reportadd = []
	reportremove = []
	window = fetch_channel_window(client,channel)
	if not window: return

	for m in modes:

		if m=="k":
			if len(args)>0:
				n = args.pop(0)
			else:
				n = None
			if mset:
				if n:
					window.setKey(n)
					if 'k' in window.modesoff:
						window.modesoff = window.modesoff.replace('k','')
					if not 'k' in window.modeson:
						window.modeson = window.modeson +'k'
					msg = Message(SYSTEM_MESSAGE,'',user+" set "+channel+"'s key to \""+n+"\"",None,TYPE_MODE)
				else:
					msg = None
			else:
				window.setKey('')
				if 'k' in window.modeson:
					window.modeson = window.modeson.replace('k','')
				if not 'k' in window.modesoff:
					window.modesoff = window.modesoff +'k'
				msg = Message(SYSTEM_MESSAGE,'',user+" unset "+channel+"'s key",None,TYPE_MODE)

			if msg:
				window.writeText( msg )

			# Update connection display
			build_connection_display(gui)

			continue

		if m=="o":
			if len(args)>0:
				n = args.pop(0)
			else:
				n = None
			if mset:
				if n:
					msg = Message(SYSTEM_MESSAGE,'',f"{user} granted {channel} operator status to {n}",None,TYPE_MODE)
				else:
					msg = None
			else:
				if n:
					#msg = f"{user} took {channel} operator status from {n}"
					msg = Message(SYSTEM_MESSAGE,'',f"{user} took {channel} operator status from {n}",None,TYPE_MODE)
				else:
					msg = None
			if msg:
				window.writeText( msg )
			continue

		if m=="v":
			if len(args)>0:
				n = args.pop(0)
			else:
				n = None
			if mset:
				if n:
					msg = Message(SYSTEM_MESSAGE,'',f"{user} granted {channel} voiced status to {n}",None,TYPE_MODE)
				else:
					msg = None
			else:
				if n:
					#msg = f"{user} took {channel} operator status from {n}"
					msg = Message(SYSTEM_MESSAGE,'',f"{user} took {channel} voiced status from {n}",None,TYPE_MODE)
				else:
					msg = None
			if msg:
				window.writeText( msg )
			continue

		if m=="c":
			if mset:
				if 'c' in window.modesoff:
					window.modesoff = window.modesoff.replace('c','')
				if not 'c' in window.modeson:
					window.modeson = window.modeson +'c'
				reportadd.append("c")
			else:
				if 'c' in window.modeson:
					window.modeson = window.modeson.replace('c','')
				if not 'c' in window.modesoff:
					window.modesoff = window.modesoff +'c'
				reportremove.append("c")
			continue

		if m=="C":
			if mset:
				if "C" in window.modesoff:
					window.modesoff = window.modesoff.replace("C",'')
				if not "C" in window.modeson:
					window.modeson = window.modeson +"C"
				reportadd.append("C")
			else:
				if "C" in window.modeson:
					window.modeson = window.modeson.replace("C",'')
				if not "C" in window.modesoff:
					window.modesoff = window.modesoff +"C"
				reportremove.append("C")
			continue

		if m=="m":
			if mset:
				if "m" in window.modesoff:
					window.modesoff = window.modesoff.replace("m",'')
				if not "m" in window.modeson:
					window.modeson = window.modeson +"m"
				reportadd.append("m")
			else:
				if "m" in window.modeson:
					window.modeson = window.modeson.replace("m",'')
				if not "m" in window.modesoff:
					window.modesoff = window.modesoff +"m"
				reportremove.append("m")
			continue

		if m=="n":
			if mset:
				if "n" in window.modesoff:
					window.modesoff = window.modesoff.replace("n",'')
				if not "n" in window.modeson:
					window.modeson = window.modeson +"n"
				reportadd.append("n")
			else:
				if "n" in window.modeson:
					window.modeson = window.modeson.replace("n",'')
				if not "n" in window.modesoff:
					window.modesoff = window.modesoff +"n"
				reportremove.append("n")
			continue

		if m=="p":
			if mset:
				if "p" in window.modesoff:
					window.modesoff = window.modesoff.replace("p",'')
				if not "p" in window.modeson:
					window.modeson = window.modeson +"p"
				reportadd.append("p")
			else:
				if "p" in window.modeson:
					window.modeson = window.modeson.replace("p",'')
				if not "p" in window.modesoff:
					window.modesoff = window.modesoff +"p"
				reportremove.append("p")
			continue

		if m=="s":
			if mset:
				if "s" in window.modesoff:
					window.modesoff = window.modesoff.replace("s",'')
				if not "s" in window.modeson:
					window.modeson = window.modeson +"s"
				reportadd.append("s")
			else:
				if "s" in window.modeson:
					window.modeson = window.modeson.replace("s",'')
				if not "s" in window.modesoff:
					window.modesoff = window.modesoff +"s"
				reportremove.append("s")
			continue

		if m=="t":
			if mset:
				if "t" in window.modesoff:
					window.modesoff = window.modesoff.replace("t",'')
				if not "t" in window.modeson:
					window.modeson = window.modeson +"t"
				reportadd.append("t")
			else:
				if "t" in window.modeson:
					window.modeson = window.modeson.replace("t",'')
				if not "t" in window.modesoff:
					window.modesoff = window.modesoff +"t"
				reportremove.append("t")
			continue

		if m=="i":
			if mset:
				if "i" in window.modesoff:
					window.modesoff = window.modesoff.replace("i",'')
				if not "i" in window.modeson:
					window.modeson = window.modeson +"i"
				reportadd.append("i")
			else:
				if "i" in window.modeson:
					window.modeson = window.modeson.replace("i",'')
				if not "i" in window.modesoff:
					window.modesoff = window.modesoff +"i"
				reportremove.append("i")
			continue

		if mset:
			reportadd.append(m)
		else:
			reportremove.append(m)

		if gui.current_page:
			if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

	if len(reportadd)>0 or len(reportremove)>0:
		if mset:

			for m in reportadd:
				if not m in window.modeson: window.modeson = window.modeson + m
				if m in window.modesoff: window.modesoff.replace(m,'')

			msg = Message(SYSTEM_MESSAGE,'',f"{user} set +{''.join(reportadd)} in {channel}",None,TYPE_MODE)
			window.writeText( msg )

			if not window_has_unseen(window,gui):
				UNSEEN.append(window)
		else:

			for m in reportremove:
				if not m in window.modesoff: window.modesoff = window.modesoff + m
				if m in window.modeson: window.modeson.replace(m,'')

			msg = Message(SYSTEM_MESSAGE,'',f"{user} set -{''.join(reportremove)} in {channel}",None,TYPE_MODE)
			window.writeText( msg )

			if not window_has_unseen(window,gui):
				UNSEEN.append(window)

	if config.DISPLAY_CHANNEL_MODES:
		# Change the channel's name display
		if len(window.modeson)>0:
			window.name_display.setText("<b>"+window.name+"</b> <i>+"+window.modeson+"</i>")
		else:
			window.name_display.setText("<b>"+window.name+"</b>")

def toggle_channel_mode_display():
	for window in CHANNELS:
		if config.DISPLAY_CHANNEL_MODES:
			if len(window.widget.modeson)>0:
				window.widget.name_display.setText("<b>"+window.widget.name+"</b> <i>+"+window.widget.modeson+"</i>")
			else:
				window.widget.name_display.setText("<b>"+window.widget.name+"</b>")
		else:
			window.widget.name_display.setText("<b>"+window.widget.name+"</b>")

def received_hostmask_for_channel_user(gui,client,nick,hostmask):
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			if nick in window.widget.nicks:
				window.widget.hostmasks[nick] = hostmask

def received_whois(gui,client,whoisdata):
	
	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, whoisdata.username+"@"+whoisdata.host+": \x02"+whoisdata.realname+"\x0F"), True )
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, "\x02"+whoisdata.server+"\x0F"), True )
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, "\x02"+whoisdata.channels+"\x0F"), True )
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, "\x02Signed on:\x0F "+datetime.fromtimestamp(int(whoisdata.signon)).strftime('%m/%d/%Y, %H:%M:%S')), True )
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, "\x02Idle:\x0F "+whoisdata.idle+" seconds"), True )
			gui.current_page.writeText( Message(WHOIS_MESSAGE,whoisdata.nickname, "\x02"+whoisdata.privs+"\x0F"), True )

def topic(gui,client,setter,channel,topic):
	p = setter.split('!')
	if len(p)==2:
		nick = p[0]
	else:
		nick = setter

	if nick=='': nick = "The server"

	window = fetch_channel_window(client,channel)
	if window:
		window.setTopic(topic)
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" set the topic to \""+topic+"\"",None,TYPE_TOPIC) )

		if not window_has_unseen(window,gui):
			UNSEEN.append(window)

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" set the topic in "+channel+" to \""+topic+"\"") )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def userlist(gui,client,channel,userlist):

	# Update connection display
	build_connection_display(gui)

	window = fetch_channel_window(client,channel)
	if window: window.writeUserlist(userlist)

def quit(gui,client,nick,message):

	for channel in where_is_user(client,nick):
		window = fetch_channel_window(client,channel)
		if window:
			if len(message)>0:
				window.writeText( Message(SYSTEM_MESSAGE,'',nick+" quit IRC ("+message+")",None,TYPE_QUIT) )
			else:
				window.writeText( Message(SYSTEM_MESSAGE,'',nick+" quit IRC",None,TYPE_QUIT) )

		if not window_has_unseen(window,gui):
			UNSEEN.append(window)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def action_message(gui,client,target,user,message):
	global UNSEEN
	p = user.split('!')
	if len(p)==2:
		nick = p[0]
		hostmask = p[1]
	else:
		nick = user
		hostmask = None

	ignore = False
	for i in gui.ignore:
		if i==nick: ignore = True
		if i==user: ignore = True
		if hostmask:
			if hostmask in i: ignore = True

	if ignore: return

	window = fetch_channel_window(client,target)
	if window:
		window.writeText( Message(ACTION_MESSAGE,user,message) )
	else:
		window = fetch_private_window(client,nick)
		if window:
			window.writeText( Message(ACTION_MESSAGE,user,message) )
		else:
			if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
				newchan = Chat(
					nick,
					client,
					config.PRIVATE_WINDOW,
					gui.app,
					gui
					)

				index = gui.stack.addWidget(newchan)
				if config.SWITCH_TO_NEW_WINDOWS:
					gui.stack.setCurrentWidget(newchan)

				#gui.setWindowTitle(nick)

				PRIVATES.append( Window(index,newchan) )

				newchan.writeText( Message(ACTION_MESSAGE,user,message) )

				window = newchan

				newchan.input.setFocus()

				# Update connection display
				build_connection_display(gui)
			else:
				# Write the private messages to the console window
				window = fetch_console_window(client)
				if window:
					window.writeText( Message(ACTION_MESSAGE,user,message) )

					posted_to_current = False
					if gui.current_page:
						if gui.current_page.name==SERVER_CONSOLE_NAME:
							if gui.current_page.client.id==client.id:
								posted_to_current = True

					if not posted_to_current:
						UNSEEN.append(window)

						# Update connection display
						build_connection_display(gui)
			return

	posted_to_current = False
	if gui.current_page:
		if gui.current_page.name==target:
			if gui.current_page.client.id==client.id:
				posted_to_current = True

	if not posted_to_current:
		if not window_has_unseen(window,gui):
			UNSEEN.append(window)

		# Update connection display
		build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def nick(gui,client,oldnick,newnick):

	channels = where_is_user(client,oldnick)
	msg = Message(SYSTEM_MESSAGE,'',oldnick+" is now known as "+newnick,None,TYPE_NICK)
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			if window.widget.name in channels:
				window.widget.writeText(msg)
	
	for window in PRIVATES:
		if window.widget.client.id==client.id:
			if window.widget.name==oldnick:
				window.widget.name = newnick
				window.widget.name_display.setText("<b>"+newnick+"</b>")

	window = fetch_console_window(client)
	if window:
		window.writeText(msg)

	# Update connection display
	build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()


def erk_invited(gui,client,sender,channel):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',sender+" invited you to "+channel,None,TYPE_INVITE) )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',sender+" invited you to "+channel) )

	if config.JOIN_ON_INVITE:
		client.join(channel)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()


def erk_inviting(gui,client,target,channel):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',"You've invited "+target+" to "+channel,None,TYPE_INVITE) )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',"You've invited "+target+" to "+channel) )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def erk_nickname_in_use(gui,client,badnick):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',"Nickname \""+badnick+"\" is already in use") )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',"Nickname \""+badnick+"\" is already in use") )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def erk_youre_oper(gui,client):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',"You are now an operator") )

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',"You are now an operator") )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def erk_changed_nick(gui,client,newnick):

	if gui.current_page:
		if hasattr(gui.current_page,"writeText"):
			gui.current_page.writeText( Message(SYSTEM_MESSAGE,'',"You are now known as "+newnick) )

	window = fetch_console_window(client)
	if window:
		if window != gui.current_page:
			window.writeText( Message(SYSTEM_MESSAGE,'',"You are now known as "+newnick) )

	# Update channel window nick displays
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			window.widget.nickDisplay(newnick)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def erk_channel_list(client):
	result = []
	for window in CHANNELS:
		if window.widget.client.id==client.id:
			result.append(window.widget.name)
	return result

def erk_left_channel(gui,client,channel):
	
	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',"You left "+channel) )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def erk_joined_channel(gui,client,channel):
	global CHANNELS
	
	newchan = Chat(
		channel,
		client,
		config.CHANNEL_WINDOW,
		gui.app,
		gui
		)

	index = gui.stack.addWidget(newchan)
	if config.SWITCH_TO_NEW_WINDOWS:
		gui.stack.setCurrentWidget(newchan)
		newchan.input.setFocus()

	#gui.setWindowTitle(channel)

	CHANNELS.append( Window(index,newchan) )

	newchan.writeText( Message(SYSTEM_MESSAGE,'',"Joined "+channel) )
	newchan.chat.moveCursor(QTextCursor.End)

	# Set focus to the input widget
	newchan.input.setFocus()

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',"Joined "+channel) )

	# Update connection display
	build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def uptime(gui,client,uptime):

	# if not client.gui.block_plugins:
	# 	client.gui.plugins.tick(client)
	
	gui.uptimers[client.id] = uptime
	gui.total_uptime = gui.total_uptime + 1

	if gui.do_connection_display_width_save<=gui.total_uptime and gui.do_connection_display_width_save!=0:
		config.save_settings(gui.configfile)
		gui.do_connection_display_width_save = 0

	if config.DISPLAY_CONNECTION_UPTIME:
		iterator = QTreeWidgetItemIterator(gui.connection_display)
		while True:
			item = iterator.value()
			if item is not None:
				if hasattr(item,"erk_uptime"):
					if item.erk_uptime:
						if item.erk_client.id==client.id:
							item.setText(0,prettyUptime(uptime))
				iterator += 1
			else:
				break

	# Update chat window log_timers
	if len(CHANNELS)>0:
		w = None
		for c in CHANNELS:
			w = c.widget
			w.log_counter = w.log_counter + 1
			if w.log_counter >= config.AUTOSAVE_LOG_TIME:
				w.do_log_save()
				w.log_counter = 0
			

	if len(PRIVATES)>0:
		w = None
		for c in PRIVATES:
			w = c.widget
			w.log_counter = w.log_counter + 1
			if w.log_counter >= config.AUTOSAVE_LOG_TIME:
				w.do_log_save()
				w.log_counter = 0
			

def part(gui,client,user,channel):

	# if not client.gui.block_plugins:
	# 	client.gui.plugins.part(client,channel,user)

	p = user.split('!')
	if len(p)==2:
		nick = p[0]
	else:
		nick = user

	window = fetch_channel_window(client,channel)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" left the channel",None,TYPE_PART) )

	if not window_has_unseen(window,gui):
		UNSEEN.append(window)

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" left "+channel) )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def join(gui,client,user,channel):

	# if not client.gui.block_plugins:
	# 	client.gui.plugins.join(client,channel,user)

	p = user.split('!')
	if len(p)==2:
		nick = p[0]
	else:
		nick = user

	window = fetch_channel_window(client,channel)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" joined the channel",None,TYPE_JOIN) )

	if not window_has_unseen(window,gui):
		UNSEEN.append(window)

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(SYSTEM_MESSAGE,'',nick+" joined "+channel) )

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def motd(gui,client,motd):
	
	window = fetch_console_window(client)

	if window:
		for line in motd:
			# window.writeText( Message(SYSTEM_MESSAGE,'',line) )
			window.writeText( Message(MOTD_MESSAGE,'',line) )


	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def notice_message(gui,client,target,user,message):

	# if not client.gui.block_plugins:
	# 	if client.gui.plugins.notice(client,target,user,message): return

	if len(user.strip())==0:
		if client.hostname:
			user = client.hostname
		else:
			user = client.server+":"+str(client.port)

	p = user.split('!')
	if len(p)==2:
		nick = p[0]
		hostmask = p[1]
	else:
		nick = user
		hostmask = None

	ignore = False
	for i in gui.ignore:
		if i==nick: ignore = True
		if i==user: ignore = True
		if hostmask:
			if hostmask in i: ignore = True

	if ignore: return

	window = fetch_channel_window(client,target)
	if window:
		window.writeText( Message(NOTICE_MESSAGE,user,message) )

		posted_to_current = False
		if gui.current_page:
			if gui.current_page.name==target:
				if gui.current_page.client.id==client.id:
					posted_to_current = True

		if not posted_to_current:
			if not window_has_unseen(window,gui):
				UNSEEN.append(window)

			# Update connection display
			build_connection_display(gui)
		return


	window = fetch_private_window(client,nick)
	if window:
		window.writeText( Message(NOTICE_MESSAGE,user,message) )

		posted_to_current = False
		if gui.current_page:
			if gui.current_page.name==nick:
				if gui.current_page.client.id==client.id:
					posted_to_current = True

		if not posted_to_current:
			if not window_has_unseen(window,gui):
				UNSEEN.append(window)

			# Update connection display
			build_connection_display(gui)

		return

	window = fetch_console_window(client)
	if window:
		window.writeText( Message(NOTICE_MESSAGE,user,message) )

		posted_to_current = False
		if gui.current_page:
			if gui.current_page.name==SERVER_CONSOLE_NAME:
				if gui.current_page.client.id==client.id:
					posted_to_current = True

		if not posted_to_current:
			if not window_has_unseen(window,gui):
				UNSEEN.append(window)

			# Update connection display
			build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def private_message(gui,client,user,message):

	# if not client.gui.block_plugins:
	# 	if client.gui.plugins.private(client,user,message): return

	global UNSEEN

	p = user.split('!')
	if len(p)==2:
		nick = p[0]
		hostmask = p[1]
	else:
		nick = user
		hostmask = None

	ignore = False
	for i in gui.ignore:
		if i==nick: ignore = True
		if i==user: ignore = True
		if hostmask:
			if hostmask in i: ignore = True

	if ignore: return
	
	msg = Message(CHAT_MESSAGE,user,message,TYPE_PRIVATE)

	window = fetch_private_window(client,nick)
	if window:
		window.writeText(msg)
	else:
		if config.OPEN_NEW_PRIVATE_MESSAGE_WINDOWS:
			newchan = Chat(
				nick,
				client,
				config.PRIVATE_WINDOW,
				gui.app,
				gui
				)

			index = gui.stack.addWidget(newchan)
			if config.SWITCH_TO_NEW_WINDOWS:
				gui.stack.setCurrentWidget(newchan)
				newchan.input.setFocus()

			#gui.setWindowTitle(nick)

			PRIVATES.append( Window(index,newchan) )

			newchan.writeText(msg)

			window = newchan

			# Update connection display
			build_connection_display(gui)
		else:
			# Write the private messages to the console window
			window = fetch_console_window(client)
			if window:
				window.writeText(msg)

				posted_to_current = False
				if gui.current_page:
					if gui.current_page.name==SERVER_CONSOLE_NAME:
						if gui.current_page.client.id==client.id:
							posted_to_current = True

				if not posted_to_current:

					found = False
					for w in UNSEEN:
						if w.client.id==window.client.id:
							if w.name==window.name:
								found = True

					if not found: UNSEEN.append(window)

					# Update connection display
					build_connection_display(gui)
		return

	posted_to_current = False
	if gui.current_page:
		if gui.current_page.name==nick:
			if gui.current_page.client.id==client.id:
				posted_to_current = True

	if not posted_to_current:
		
		found = False
		for w in UNSEEN:
			if w.client.id==window.client.id:
				if w.name==window.name:
					found = True

		if not found: UNSEEN.append(window)

		# Update connection display
		build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def public_message(gui,client,channel,user,message):

	# if not client.gui.block_plugins:
	# 	if client.gui.plugins.public(client,channel,user,message): return

	p = user.split('!')
	if len(p)==2:
		nick = p[0]
		hostmask = p[1]
	else:
		nick = user
		hostmask = None

	ignore = False
	for i in gui.ignore:
		if i==nick: ignore = True
		if i==user: ignore = True
		if hostmask:
			if hostmask in i: ignore = True

	if ignore: return

	msg = Message(CHAT_MESSAGE,user,message)

	window = fetch_channel_window(client,channel)
	if window:
		window.writeText(msg)

	posted_to_current = False
	if gui.current_page:
		if gui.current_page.name==channel:
			if gui.current_page.client.id==client.id:
				posted_to_current = True

	if not posted_to_current:
		if window:
			global UNSEEN
			found = False
			for w in UNSEEN:
				if w.client.id==window.client.id:
					if w.name==window.name:
						found = True

			if not found: UNSEEN.append(window)

			# Update connection display
			build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def registered(gui,client):

	# if not client.gui.block_plugins:
	# 	client.gui.plugins.connect(client)

	gui.registered(client)

	window = fetch_console_window(client)
	window.writeText( Message(SYSTEM_MESSAGE,'',"Registered with "+client.server+":"+str(client.port)+"!") )
	
	# Update connection display
	build_connection_display(gui)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def disconnect_from_server(client,msg=None):

	client.gui.quitting.append(client.server+str(client.port))

	client.quit(msg)

def disconnection(gui,client):

	global CONNECTIONS
	clean = []
	for c in CONNECTIONS:
		if c.id == client.id: continue
		clean.append(c)
	CONNECTIONS = clean

	global PRIVATES
	clean = []
	for c in PRIVATES:
		if c.widget.client.id == client.id:
			c.widget.close()
			continue
		clean.append(c)
	PRIVATES = clean

	global CHANNELS
	clean = []
	for c in CHANNELS:
		if c.widget.client.id == client.id:
			c.widget.close()
			continue
		clean.append(c)
	CHANNELS = clean

	global CONSOLES
	clean = []
	for window in CONSOLES:
		if window.widget.client.id==client.id:
			window.widget.close()
			continue
		clean.append(window)
	CONSOLES = clean

	if len(CHANNELS)>0:
		w = None
		for c in CHANNELS:
			w = c.widget
		client.gui.stack.setCurrentWidget(w)
	elif len(PRIVATES)>0:
		w = None
		for c in PRIVATES:
			w = c.widget
		client.gui.stack.setCurrentWidget(w)
	elif len(CONSOLES)>0:
		w = None
		for c in CONSOLES:
			w = c.widget
		client.gui.stack.setCurrentWidget(w)
	else:
		client.gui.stack.setCurrentWidget(client.gui.starter)
		client.gui.total_uptime = 0

	# Update connection display
	build_connection_display(gui)

def connection(gui,client):
	global CONNECTIONS
	CONNECTIONS.append(client)

	window = fetch_console_window(client)
	window.writeText( Message(SYSTEM_MESSAGE,'',"Connected to "+client.server+":"+str(client.port)+"!") )

	# Update connection display
	build_connection_display(gui,client)

	if gui.current_page:
		if hasattr(gui.current_page,"input"): gui.current_page.input.setFocus()

def server_options(gui,client,options):
	
	window = fetch_console_window(client)

	window.writeText( Message(SYSTEM_MESSAGE,'', ", ".join(options)    ) )

	if client.network:
		user_info = get_user(gui.userfile)
		newhistory = []
		change = False
		for s in user_info["history"]:
			if s[0]==client.server:
				if s[1]==str(client.port):
					if s[2]==UNKNOWN_NETWORK:
						s[2] = client.network
						change = True
			newhistory.append(s)

		if change:
			user_info["history"] = newhistory
			save_user(user_info,gui.userfile)

	window.update_server_name()

	# Update connection display
	build_connection_display(gui)

def banlist(gui,client,channel,banlist):
	
	window = fetch_channel_window(client,channel)
	if window:
		window.banlist = banlist

def startup(gui,client):
	global CONSOLES

	newconsole = Chat(
		SERVER_CONSOLE_NAME,
		client,
		config.SERVER_WINDOW,
		gui.app,
		gui
		)

	index = gui.stack.addWidget(newconsole)

	if config.SWITCH_TO_NEW_WINDOWS:
		gui.stack.setCurrentWidget(newconsole)

	if client.hostname:
		gui.setWindowTitle(client.hostname)
	else:
		gui.setWindowTitle(client.server+":"+str(client.port))

	CONSOLES.append( Window(index,newconsole) )

	newconsole.writeText( Message(SYSTEM_MESSAGE,'',"Connecting to "+client.server+":"+str(client.port)+"...") )

	# Set focus to the input widget
	newconsole.input.setFocus()
	
	# Update connection display
	build_connection_display(gui)