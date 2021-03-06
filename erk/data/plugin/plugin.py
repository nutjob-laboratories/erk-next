from erk import *

class !_PLUGIN_NAME!(Plugin):

	def __init__(self):
		self.name = "!PLUGIN_FULL_NAME!"
		self.description = None
		
		self.author = None
		self.version = None
		self.website = None
		self.source = None

	def received(self,client,line):
		"""Executed when the client receives data from the server.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		line -- The received data
		"""
		pass

	def sent(self,client,line):
		"""Executed when the client sends data to the server.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		line -- The sent data
		"""
		pass

	def load(self):
		"""Executed when the plugin is loaded.

		Arguments:
		self -- The plugin's instance
		"""
		pass

	def unload(self):
		"""Executed when the plugin is unloaded.

		Arguments:
		self -- The plugin's instance
		"""
		pass

	def input(self,client,name,text):
		"""Executed when the user inputs text.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		name -- The channel/username of the input that triggered the plugin
		text -- The user input
		"""
		pass

	def connect(self,client):
		"""Executes when the client registers with a server.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		"""
		pass

	def public(self,client,channel,user,message):
		"""Executed when the client receives a public message.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		channel -- The name of the channel that sent the message
		user -- The user who sent the message (in nickname!username@host format)
		message -- The message contents
		"""
		pass

	def private(self,client,user,message):
		"""Executed when the client receives a private message.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		user -- The user who sent the message (in nickname!username@host format)
		message -- The message contents
		"""
		pass

	def notice(self,client,target,user,message):
		"""Executed when the client receives a notice message.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		target -- The user or channel the notice was sent to
		user -- The user who sent the message (in nickname!username@host format)
		message -- The message contents
		"""
		pass

	def tick(self,client):
		"""Executes once per second.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		"""
		pass

	def join(self,client,channel,user):
		"""Executed when the client receives a join notification.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		channel -- The channel the user joined
		user -- The user who joined the channel
		"""
		pass

	def part(self,client,channel,user):
		"""Executed when the client receives a part notification.

		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		channel -- The channel the user left
		user -- The user who left the channel
		"""
		pass

	def ctcp(self,client,user,channel,tag,message):
		"""Executed when the client receives an unrecognized CTCP message.
		
		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		user -- The user who sent the message
		channel -- The channel the user sent it from
		tag -- The message's tag
		message -- The message contents
		"""
		pass

	def mode(self,channel,user,mset,modes,arguments):
		"""Executed when a mode is set on the client or a channel the client is in.
		
		Arguments:
		self -- The plugin's instance
		client -- The Twisted IRC client object
		channel -- The target (user or channel) the mode was set on
		user -- The user who set the mode
		mset -- True if a mode is set, False if a mode is unset
		modes -- The mode(s) set
		args -- A tuple of any arguments to the mode
		"""
		pass
