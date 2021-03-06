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

import sys
import os
#from itertools import combinations_with_replacement
from zipfile import ZipFile
import shutil
import platform

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore

from .resources import *
from .widgets import *
from .files import *
from .common import *
from .plugins import PluginCollection,PLUGIN_DIRECTORY
from . import config
from . import events
from . import textformat
from . import userinput

from .dialogs import(
	ComboDialog,
	JoinDialog,
	NickDialog,
	WindowSizeDialog,
	HistorySizeDialog,
	LogSizeDialog,
	FormatTextDialog,
	AboutDialog,
	EditorDialog,
	ErrorDialog,
	ExportLogDialog,
	PrefixDialog,
	ListTimeDialog,
	InstallDialog,
	SettingsDialog,
	AutosaveDialog,
	ComboDialogCmd,
	FormatEditDialog,
	ScriptEditor,
	)

from .dialogs.export_package import Dialog as ExportPackageDialog

from .dialogs.blank import Dialog as Blank

from .irc import(
	connect,
	connectSSL,
	reconnect,
	reconnectSSL
	)

USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR = False

DO_NOT_DISPLAY_MENUS_OR_TOOLBAR = False

class Erk(QMainWindow):

	# Occasionally, when restoring the main window, chat windows' text display
	# gets "zoomed in" on new text, for some reason. This prevents this from
	# being displayed to the user
	def changeEvent(self,event):
		if event.type() == QEvent.WindowStateChange:
			if event.oldState() and Qt.WindowMinimized:
				events.resize_font_fix()
			elif event.oldState() == Qt.WindowNoState:
				events.resize_font_fix()
			elif self.windowState() == Qt.WindowMaximized:
				events.resize_font_fix()

		if event.type() == QEvent.ActivationChange and self.isActiveWindow():
			if self.current_page:
				if hasattr(self.current_page,"input"):
					if hasattr(self.current_page.input,"setFocus"):
						self.current_page.input.setFocus()

				events.clear_unseen(self.current_page)
				events.build_connection_display(self)

		
		return QMainWindow.changeEvent(self, event)

	def newStyle(self,style):
		events.apply_style(style)

	def closeEvent(self, event):

		do_quit = True

		if config.ASK_BEFORE_QUIT:

			num_servers = len(events.fetch_connections())

			if num_servers>0:

				msgBox = QMessageBox()
				msgBox.setIconPixmap(QPixmap(ERK_ICON))
				msgBox.setWindowIcon(QIcon(ERK_ICON))
				if num_servers==1:
					msgBox.setText("Are you sure you want to quit?")
				else:
					msgBox.setText("You are currently connected to "+str(num_servers)+" servers. Are you sure you want to quit?")
				msgBox.setWindowTitle("Quit "+APPLICATION_NAME)
				msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

				rval = msgBox.exec()

				if rval == QMessageBox.Cancel:
					do_quit = False

		if do_quit:

			if config.SAVE_MACROS:
				if len(userinput.MACROS)>0:
					save_macros(userinput.MACROS,self.macrofile)

			self.erk_is_quitting = True
			# if not self.block_plugins:
			# 	self.plugins.unload()
			if self.fullscreen==False:
				config.DEFAULT_APP_WIDTH = self.width()
				config.DEFAULT_APP_HEIGHT = self.height()
				config.save_settings(self.configfile)
			self.app.quit()
		else:
			event.ignore()

	def disconnect_current(self,msg=None):
		if self.current_client:
			events.disconnect_from_server(self.current_client,msg)
			self.current_client = None

	def refresh_application_title(self,item=None):

		# Fix for no connection
		if hasattr(self.current_page,"nothing_is_connected"):
			self.setWindowTitle(APPLICATION_NAME)

		if item!=None:

			topic = ''
			if hasattr(item.erk_widget,"channel_topic"):
				if len(item.erk_widget.channel_topic)>0:
					topic = item.erk_widget.channel_topic
			if not config.APP_TITLE_SHOW_TOPIC: topic = ''

			hasname = False
			if hasattr(item,"erk_name"):
				if config.APP_TITLE_TO_CURRENT_CHAT:
					if item.erk_name:
						hasname = True
						if len(topic)>0:
							self.setWindowTitle(item.erk_name+" - "+topic)
						else:
							self.setWindowTitle(item.erk_name)
				elif config.APP_TITLE_SHOW_TOPIC:
					self.setWindowTitle(topic)
				else:
					self.setWindowTitle(APPLICATION_NAME)

			if not config.APP_TITLE_TO_CURRENT_CHAT:
				if not hasname and topic=='':
					self.setWindowTitle(APPLICATION_NAME)

			return

		window = self.current_page

		topic = ''
		if hasattr(window,"channel_topic"):
			if len(window.channel_topic)>0:
				topic = window.channel_topic
		if not config.APP_TITLE_SHOW_TOPIC: topic = ''

		if hasattr(window,"name"):
			if window.name==MASTER_LOG_NAME:
				pass
			elif window.name==SERVER_CONSOLE_NAME:
				self.setWindowTitle(APPLICATION_NAME)
			else:
				if config.APP_TITLE_TO_CURRENT_CHAT:
					if len(topic)>0:
						self.setWindowTitle(window.name+" - "+topic)
					else:
						self.setWindowTitle(window.name)
				elif config.APP_TITLE_SHOW_TOPIC:
					self.setWindowTitle(topic)
				else:
					self.setWindowTitle(APPLICATION_NAME)

	def pageChange(self,index):

		window = self.stack.widget(index)

		self.current_page = window

		if hasattr(window,"client"):
			self.current_client = window.client
			if not DO_NOT_DISPLAY_MENUS_OR_TOOLBAR:
				self.disconnect.setVisible(True)
		else:
			self.current_client = None
			if not DO_NOT_DISPLAY_MENUS_OR_TOOLBAR:
				self.disconnect.setVisible(False)

		if hasattr(window,"name"):
			if window.name==MASTER_LOG_NAME:
				self.current_client = None
				if not DO_NOT_DISPLAY_MENUS_OR_TOOLBAR:
					self.disconnect.setVisible(False)

		if hasattr(window,"input"):
			# Set focus to the input widget
			window.input.setFocus()

		if hasattr(window,"client"): events.clear_unseen(window)
		events.build_connection_display(self)

		self.refresh_application_title()

	def connectionNodeSingleClicked(self,item,column):
		if config.DOUBLECLICK_SWITCH: return
		if hasattr(item,"erk_widget"):
			if item.erk_widget:
				self.stack.setCurrentWidget(item.erk_widget)
				self.refresh_application_title(item)

		self.connection_display.clearSelection()
		events.build_connection_display(self)

	def connectionNodeDoubleClicked(self,item):
		if not config.DOUBLECLICK_SWITCH: return
		if hasattr(item,"erk_widget"):
			if item.erk_widget:
				self.stack.setCurrentWidget(item.erk_widget)
				self.refresh_application_title(item)

		self.connection_display.clearSelection()
		events.build_connection_display(self)

	def start_spinner(self):
		if not config.SCHWA_ANIMATION: return
		if DO_NOT_DISPLAY_MENUS_OR_TOOLBAR: return
		if not USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR: self.spinner.start()

	def stop_spinner(self):
		if not config.SCHWA_ANIMATION: return
		if DO_NOT_DISPLAY_MENUS_OR_TOOLBAR: return
		if not USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
			self.spinner.stop()
			self.corner_widget.setIcon(QIcon(self.toolbar_icon))

	def registered(self,client):
		clean = []
		for c in self.connecting:
			host = c[0]
			port = c[1]
			if client.server==host and client.port == port:
				continue
			clean.append(c)

		self.connecting = clean

		if len(self.connecting)==0: self.stop_spinner()

	def display_load_errors(self):
		if len(self.plugins.errors())>0:
			errs = self.plugins.errors()
			if config.SHOW_LOAD_ERRORS:
				total_errors = {}
				for e in errs:
					if e.package in total_errors:
						total_errors[e.package].append([e.classname,e.reason])
					else:
						total_errors[e.package] = []
						total_errors[e.package].append([e.classname,e.reason])
				
				ErrorDialog(self,total_errors)
			else:
				for e in errs:
					s = "Error loading package "+e.package+"!\n"
					s = s + e.classname+": "+e.reason
					print(s)

	def resizeEvent(self, event):
		pass

	def connectionDisplayResized(self):
		events.build_connection_display(self)

		self.do_connection_display_width_save = self.total_uptime + 5

	def menuDocked(self,is_floating):
		if not is_floating:
			# menu bar has been docked
			p = self.toolBarArea(self.toolbar)
			if p == Qt.TopToolBarArea:
				config.MENU_BAR_ORIENT="top"
			else:
				config.MENU_BAR_ORIENT="bottom"
			config.save_settings(self.configfile)

	def set_menubar_moveable(self,is_moveable):
		if hasattr(self,'toolbar'):
			if is_moveable:
				self.toolbar.setMovable(True)
			else:
				self.toolbar.setMovable(False)
				if config.MENU_BAR_ORIENT.lower()=='top':
					self.addToolBar(Qt.TopToolBarArea,self.toolbar)
				else:
					self.addToolBar(Qt.BottomToolBarArea,self.toolbar)

	def showSettingsDialog(self):
		self._erk_this_is_the_settings_dialog_space = SettingsDialog(self.configfile,self)

	def __init__(
			self,
			app,
			info=None,
			#block_plugins=False,
			block_settings=False,
			block_toolbar=False,
			configfile=None,
			stylefile=STYLE_FILE,
			userfile=USER_FILE,
			fullscreen=False,
			width=None,
			height=None,
			logdir=LOG_DIRECTORY,
			block_scripts=False,
			scriptdir=SCRIPTS_DIRECTORY,
			block_connectiondisplay=False,
			do_ontop=False,
			force_qmenu=False,
			style_dir=STYLES_DIRECTORY,
			no_styles=False,
			block_editor=False,
			macrofile=MACRO_SAVE_FILE,
			block_install=False,
			parent=None
		):
		
		super(Erk, self).__init__(parent)

		self.app = app
		self.parent = parent

		self.editor = None

		self.erk_is_quitting = False

		self.quitting = []
		self.connecting = []

		self.seditors = None

		self.uptimers = {}

		self.total_uptime = 0
		self.do_connection_display_width_save = 0

		self.current_client = None

		self.block_install = block_install

		#self.block_plugins = block_plugins

		self.block_settings = block_settings

		self.block_toolbar = block_toolbar

		self.block_editor = block_editor

		self.fullscreen = fullscreen

		self.configfile = configfile

		self.stylefile = stylefile

		self.userfile = userfile

		self.logdir = logdir

		self.block_scripts = block_scripts

		self.scriptsdir = scriptdir

		self.styledir = style_dir

		self.do_ontop = do_ontop

		self.block_styles = no_styles

		self.macrofile = macrofile

		#self.cmdline_plugin = False
		self.cmdline_script = False
		self.cmdline_editor = False
		self.cmdline_install = False

		#if self.block_plugins: self.cmdline_plugin = True
		if self.block_scripts: self.cmdline_script = True
		if self.block_editor: self.cmdline_editor = True
		if self.block_install: self.cmdline_install = True

		self.force_qmenu = force_qmenu

		self.block_connectiondisplay = block_connectiondisplay

		global USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR

		if force_qmenu:
			USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR = True

		if config.USE_QMENUBAR_MENUS:
			USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR = True

		# Determine if window color is dark or light
		mbcolor = self.palette().color(QPalette.Window).name()
		c = tuple(int(mbcolor[i:i + 2], 16) / 255. for i in (1, 3, 5))
		luma = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
		luma = luma*100

		if luma>=40:
			self.is_light_colored = True
		else:
			self.is_light_colored = False

		self.style = textformat.get_text_format_settings(self.stylefile)

		# Load application settings
		config.load_settings(configfile)

		# Rebuild the command help, if a user has a different symbol
		# for executing commands
		userinput.buildHelp()

		if not config.ENABLE_SCRIPT_EDITOR: self.block_editor = True

		# Load in script engine
		if not self.block_scripts:
			if config.SAVE_MACROS:
				macro_table = get_macros(self.macrofile)
				userinput.MACROS = list(macro_table)

				
		if config.BLOCK_PLUGIN_INSTALL: self.block_install = True

		if width!=None:
			appwidth = width
		else:
			appwidth = int(config.DEFAULT_APP_WIDTH)

		if height!=None:
			appheight = height
		else:
			appheight = int(config.DEFAULT_APP_HEIGHT)

		u = get_user(self.userfile)
		self.ignore = u["ignore"]

		self.setWindowTitle(APPLICATION_NAME)
		self.setWindowIcon(QIcon(ERK_ICON))

		if config.DISPLAY_FONT=='':
			id = QFontDatabase.addApplicationFont(DEFAULT_FONT)
			_fontstr = QFontDatabase.applicationFontFamilies(id)[0]
			self.font = QFont(_fontstr,9)
		else:
			f = QFont()
			f.fromString(config.DISPLAY_FONT)
			self.font = f

		self.app.setFont(self.font)

		if self.do_ontop:
			self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

		self.stack = QStackedWidget(self)
		self.stack.currentChanged.connect(self.pageChange)
		self.setCentralWidget(self.stack)

		self.current_page = None

		if self.block_toolbar:
			global DO_NOT_DISPLAY_MENUS_OR_TOOLBAR
			DO_NOT_DISPLAY_MENUS_OR_TOOLBAR = True

		if not DO_NOT_DISPLAY_MENUS_OR_TOOLBAR:
			if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
				self.menubar = self.menuBar()
			else:
				self.toolbar = generate_menu_toolbar(self)

				if config.MENU_BAR_ORIENT.lower()=='top':
					self.addToolBar(Qt.TopToolBarArea,self.toolbar)
				else:
					self.addToolBar(Qt.BottomToolBarArea,self.toolbar)

				self.toolbar.topLevelChanged.connect(self.menuDocked)

				if config.MENU_BAR_MOVABLE:
					self.toolbar.setMovable(True)
				else:
					self.toolbar.setMovable(False)

				if self.is_light_colored:
					self.toolbar_icon = TOOLBAR_ICON
				else:
					self.toolbar_icon = LIGHT_TOOLBAR_ICON

				# MENU TOOLBAR
				self.mainMenu = QMenu()
				self.settingsMenu = QMenu()
				self.helpMenu = QMenu()
				self.pluginMenu = QMenu()
				self.toolsMenu = QMenu()

		# Plugins
		# if not self.block_plugins:
		# 	self.plugins = PluginCollection("plugins")

		# 	self.display_load_errors()

		if not DO_NOT_DISPLAY_MENUS_OR_TOOLBAR:
			self.buildMenuInterface()
		
		self.connection_display, self.connection_dock = buildConnectionDisplayWidget(self)

		if config.CONNECTION_DISPLAY_LOCATION=="left":
			self.addDockWidget(Qt.LeftDockWidgetArea,self.connection_dock)
		elif config.CONNECTION_DISPLAY_LOCATION=="right":
			self.addDockWidget(Qt.RightDockWidgetArea,self.connection_dock)

		if config.CONNECTION_DISPLAY_MOVE:
			self.connection_dock.setFeatures(
				QDockWidget.DockWidgetMovable |
				QDockWidget.DockWidgetFloatable
				)
			self.connection_dock.setTitleBarWidget(None)
		else:
			self.connection_dock.setFeatures( QDockWidget.NoDockWidgetFeatures )
			self.connection_dock.setTitleBarWidget(QWidget())

		self.connection_display.installEventFilter(self)

		if config.CONNECTION_DISPLAY_VISIBLE:
			self.connection_dock.show()
		else:
			self.connection_dock.hide()

		if self.block_connectiondisplay:
			self.connection_dock.hide()
			self.connection_display.hide()

		self.resize(appwidth,appheight)

		if info:
			self.connectToIRCServer(info)

		self.starter = QTextBrowser(self)
		self.starter.name = MASTER_LOG_NAME
		self.stack.addWidget(self.starter)
		self.starter.anchorClicked.connect(self.linkClicked)

		if self.is_light_colored:
			css =  "QTextBrowser { background-image: url(" + LOGO_IMAGE + "); background-attachment: fixed; background-repeat: no-repeat; background-position: center middle; }"
		else:
			css =  "QTextBrowser { background-image: url(" + LIGHT_LOGO_IMAGE + "); background-attachment: fixed; background-repeat: no-repeat; background-position: center middle; }"

		self.starter.setStyleSheet(css)

		self.starter.append("<p style=\"text-align: right;\"><small><b>Version "+APPLICATION_VERSION+ "&nbsp;&nbsp;</b><br><a href=\""+OFFICIAL_REPOSITORY+"\">"+OFFICIAL_REPOSITORY+"</a>&nbsp;&nbsp;</small></p>")

		self.starter.nothing_is_connected = True

		self.starter.anchorClicked.connect(self.linkClicked)

		if self.fullscreen:
			self.showFullScreen()

		# System Tray
		# self.tray = QSystemTrayIcon() 
		# self.tray.setIcon(QIcon(ERK_ICON)) 
		# self.tray.setVisible(True)

		# self.trayMenu = QMenu()

		# entry = QAction(QIcon(CONNECT_MENU_ICON),"Connect to a server",self)
		# entry.triggered.connect(self.menuCombo)
		# self.trayMenu.addAction(entry)

		# entry = QAction(QIcon(SETTINGS_ICON),"Preferences",self)
		# entry.triggered.connect(self.showSettingsDialog)
		# self.trayMenu.addAction(entry)

		# insertNoTextSeparator(self,self.trayMenu)

		# entry = QAction(QIcon(QUIT_ICON),"Exit",self)
		# entry.triggered.connect(self.close)
		# self.trayMenu.addAction(entry)

		# self.tray.setContextMenu(self.trayMenu)

		

	def spellcheck_language(self,setting):

		if config.SPELLCHECK_LANGUAGE=="en": self.spell_en.setIcon(QIcon(RUNCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="fr": self.spell_fr.setIcon(QIcon(RUNCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="es": self.spell_es.setIcon(QIcon(RUNCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="de": self.spell_de.setIcon(QIcon(RUNCHECKED_ICON))

		config.SPELLCHECK_LANGUAGE = setting
		config.save_settings(self.configfile)
		events.newspell_all(setting)

		if config.SPELLCHECK_LANGUAGE=="en": self.spell_en.setIcon(QIcon(RCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="fr": self.spell_fr.setIcon(QIcon(RCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="es": self.spell_es.setIcon(QIcon(RCHECKED_ICON))
		if config.SPELLCHECK_LANGUAGE=="de": self.spell_de.setIcon(QIcon(RCHECKED_ICON))

	
	def startScriptEditor(self):
		if self.seditors!= None:
			self.seditors.activateWindow()
			return

		self.seditors = ScriptEditor(None,self,self.configfile,self.scriptsdir,None)
		self.seditors.resize(640,480)

		self.seditors.clientsRefreshed(events.fetch_connections())

	def buildMenuInterface(self):

		if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:

			self.menubar.clear()
			self.mainMenu = self.menubar.addMenu("IRC")

		else:

			self.toolbar.clear()
			add_toolbar_spacer(self.toolbar)
			self.mainMenu.clear()
			add_toolbar_menu(self.toolbar,"IRC",self.mainMenu)

		entry = MenuAction(self,CONNECT_MENU_ICON,"Connect","Connect to an IRC server",25,self.menuCombo)
		self.mainMenu.addAction(entry)

		self.mainMenu.addSeparator()

		self.disconnect = QAction(QIcon(DISCONNECT_ICON),"Disconnect",self)
		self.disconnect.triggered.connect(self.disconnect_current)
		self.mainMenu.addAction(self.disconnect)

		c = events.fetch_connections()
		if len(c)==0:
			self.disconnect.setVisible(False)
		
		entry = QAction(QIcon(RESTART_ICON),"Restart",self)
		entry.triggered.connect(lambda state: restart_program())
		self.mainMenu.addAction(entry)

		entry = QAction(QIcon(QUIT_ICON),"Exit",self)
		entry.triggered.connect(self.close)
		self.mainMenu.addAction(entry)

		if not self.block_settings:

			if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
				self.settingsMenu = self.menubar.addMenu("Settings")
			else:
				self.settingsMenu.clear()
				add_toolbar_menu(self.toolbar,"Settings",self.settingsMenu)

			entry = MenuAction(self,SETTINGS_MENU_ICON,"Preferences","Change "+APPLICATION_NAME+" settings",25,self.showSettingsDialog)
			self.settingsMenu.addAction(entry)

			entry = MenuAction(self,EXPORT_MENU_ICON,"Export Logs","Export chat logs to various formats",25,self.menuExportLog)
			self.settingsMenu.addAction(entry)

			self.settingsMenu.addSeparator()


			# Hide menu

			hideMenu = self.settingsMenu.addMenu(QIcon(HIDE_ICON),"Hide notifications")

			self.hide_invite = QAction(QIcon(UNCHECKED_ICON),"Invite",self)
			self.hide_invite.triggered.connect(lambda state,s="hide_invite": self.toggleSetting(s))
			hideMenu.addAction(self.hide_invite)

			if config.HIDE_INVITE_MESSAGE: self.hide_invite.setIcon(QIcon(CHECKED_ICON))

			self.hide_join = QAction(QIcon(UNCHECKED_ICON),"Join",self)
			self.hide_join.triggered.connect(lambda state,s="hide_join": self.toggleSetting(s))
			hideMenu.addAction(self.hide_join)

			if config.HIDE_JOIN_MESSAGE: self.hide_join.setIcon(QIcon(CHECKED_ICON))

			self.hide_mode = QAction(QIcon(UNCHECKED_ICON),"Mode",self)
			self.hide_mode.triggered.connect(lambda state,s="hide_mode": self.toggleSetting(s))
			hideMenu.addAction(self.hide_mode)

			if config.HIDE_MODE_DISPLAY: self.hide_mode.setIcon(QIcon(CHECKED_ICON))

			self.hide_nick = QAction(QIcon(UNCHECKED_ICON),"Nick",self)
			self.hide_nick.triggered.connect(lambda state,s="hide_nick": self.toggleSetting(s))
			hideMenu.addAction(self.hide_nick)

			if config.HIDE_NICK_MESSAGE: self.hide_nick.setIcon(QIcon(CHECKED_ICON))

			self.hide_part = QAction(QIcon(UNCHECKED_ICON),"Part",self)
			self.hide_part.triggered.connect(lambda state,s="hide_part": self.toggleSetting(s))
			hideMenu.addAction(self.hide_part)

			if config.HIDE_PART_MESSAGE: self.hide_part.setIcon(QIcon(CHECKED_ICON))

			self.hide_topic = QAction(QIcon(UNCHECKED_ICON),"Topic",self)
			self.hide_topic.triggered.connect(lambda state,s="hide_topic": self.toggleSetting(s))
			hideMenu.addAction(self.hide_topic)

			if config.HIDE_TOPIC_MESSAGE: self.hide_topic.setIcon(QIcon(CHECKED_ICON))

			self.hide_quit = QAction(QIcon(UNCHECKED_ICON),"Quit",self)
			self.hide_quit.triggered.connect(lambda state,s="hide_quit": self.toggleSetting(s))
			hideMenu.addAction(self.hide_quit)

			if config.HIDE_QUIT_MESSAGE: self.hide_quit.setIcon(QIcon(CHECKED_ICON))

			self.settingsMenu.addSeparator()

			self.winsizeMenuEntry = QAction(QIcon(RESIZE_ICON),"Set initial window size",self)
			self.winsizeMenuEntry.triggered.connect(self.menuResize)
			self.settingsMenu.addAction(self.winsizeMenuEntry)

			w = config.DEFAULT_APP_WIDTH
			h =  config.DEFAULT_APP_HEIGHT

			if self.fullscreen: self.winsizeMenuEntry.setEnabled(False)

			self.set_full = QAction(QIcon(WINDOW_ICON),"Enter full screen mode",self)
			self.set_full.triggered.connect(lambda state,s="fullscreen": self.toggleSetting(s))
			self.settingsMenu.addAction(self.set_full)

			if self.fullscreen: self.set_full.setText("Exit full screen more")

		# Tools menu

		show_tool_menu = True
		if self.block_styles:
			if self.block_scripts:
				show_tool_menu = False

				# if not self.block_plugins:
				# 	if config.PLUGINS_ENABLED:
				# 		if config.DEVELOPER_MODE:
				# 			show_tool_menu = True

		if show_tool_menu:

			if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
				self.toolsMenu = self.menubar.addMenu("Tools")
			else:
				self.toolsMenu.clear()
				add_toolbar_menu(self.toolbar,"Tools",self.toolsMenu)

			showEditor = True
			if self.block_editor: showEditor = False
			if self.block_scripts: showEditor = False

			if showEditor:
				entry = MenuAction(self,SCRIPT_EDITOR_MENU_ICON,SCRIPT_EDITOR_NAME,"Create, edit, and run scripts",25,self.showScriptEditor)
				self.toolsMenu.addAction(entry)

			if not self.block_styles:
				entry = MenuAction(self,STYLE_MENU_ICON,STYLE_EDITOR_NAME,"Create and edit styles",25,self.showStyleDialog)
				self.toolsMenu.addAction(entry)

			# if config.DEVELOPER_MODE:

			# 	if config.PLUGINS_ENABLED and not self.block_plugins:

			# 		s = textSeparator(self,"Plugin Development")
			# 		self.toolsMenu.addAction(s)

			# 		entry = MenuAction(self,MENU_EDITOR_ICON,EDITOR_NAME,"Create and edit plugins",25,self.menuEditor)
			# 		self.toolsMenu.addAction(entry)

			# 		self.expPackMenu = MenuAction(self,MENU_ARCHIVE_ICON,"Export plugin","Export an installed plugin",25,self.exportPackage)
			# 		self.toolsMenu.addAction(self.expPackMenu)

			# 		entry = MenuAction(self,MENU_DIRECTORY_ICON,"Open directory","Open the plugin directory",25,self.openPlugDir)
			# 		self.toolsMenu.addAction(entry)

			# 		entry = MenuAction(self,MENU_RELOAD_ICON,"Reload plugins","Load any new plugins",25,self.menuReloadPlugins)
			# 		self.toolsMenu.addAction(entry)

		# Plugin menu

		# if not self.block_plugins:
		# 	if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
		# 		self.pluginMenu = self.menubar.addMenu("Plugins")
		# 	else:
		# 		self.pluginMenu.clear()
		# 		add_toolbar_menu(self.toolbar,"Plugins",self.pluginMenu)

		# 	self.rebuildPluginMenu()

		# Help menu

		if USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:
			self.helpMenu = self.menubar.addMenu("Help")
		else:
			self.helpMenu.clear()
			add_toolbar_menu(self.toolbar,"Help",self.helpMenu)

		entry = MenuAction(self,ERK_MENU_ICON,"About","About the "+APPLICATION_NAME+" IRC client",25,self.menuAbout)
		self.helpMenu.addAction(entry)

		idir = sys.path[0]
		DOCUMENTATION_DIRECTORY = os.path.join(idir, "documentation")

		entry = MenuAction(self,PDF_MENU_ICON,"Scripting & Commands","How to do stuff directly from chat",25,self.openCommandDocumentation)
		self.helpMenu.addAction(entry)

		entry = MenuAction(self,PDF_MENU_ICON,"Plugin Guide","How to write and use "+APPLICATION_NAME+" plugins",25,self.openPluginDocumentation)
		self.helpMenu.addAction(entry)

		self.helpMenu.addSeparator()

		helpLink = QAction(QIcon(LINK_ICON),"Official Ərk repository",self)
		helpLink.triggered.connect(lambda state,u="https://github.com/nutjob-laboratories/erk": self.open_link_in_browser(u))
		self.helpMenu.addAction(helpLink)

		helpLink = QAction(QIcon(LINK_ICON),"Official Ərk plugin repository",self)
		helpLink.triggered.connect(lambda state,u="https://github.com/nutjob-laboratories/erk-plugins": self.open_link_in_browser(u))
		self.helpMenu.addAction(helpLink)

		helpLink = QAction(QIcon(LINK_ICON),"GNU General Public License 3",self)
		helpLink.triggered.connect(lambda state,u="https://www.gnu.org/licenses/gpl-3.0.en.html": self.open_link_in_browser(u))
		self.helpMenu.addAction(helpLink)

		self.helpMenu.addSeparator()

		RFC_1459 = os.path.join(DOCUMENTATION_DIRECTORY, "rfc1459.pdf")
		RFC_2812 = os.path.join(DOCUMENTATION_DIRECTORY, "rfc2812.pdf")

		helpLink = QAction(QIcon(PDF_ICON),"RFC 1459",self)
		helpLink.triggered.connect(lambda state,s=RFC_1459: QDesktopServices.openUrl(QUrl("file:"+s)))
		self.helpMenu.addAction(helpLink)

		helpLink = QAction(QIcon(PDF_ICON),"RFC 2812",self)
		helpLink.triggered.connect(lambda state,s=RFC_2812: QDesktopServices.openUrl(QUrl("file:"+s)))
		self.helpMenu.addAction(helpLink)

		self.helpMenu.addSeparator()

		helpLink = QAction(QIcon(LINK_ICON),"List of emoji shortcodes",self)
		helpLink.triggered.connect(lambda state,u="https://www.webfx.com/tools/emoji-cheat-sheet/": self.open_link_in_browser(u))
		self.helpMenu.addAction(helpLink)

		if not USE_QT5_QMENUBAR_INSTEAD_OF_TOOLBAR:

			if config.SCHWA_ANIMATION:
				add_toolbar_stretch(self.toolbar)
				self.corner_widget = add_toolbar_image(self.toolbar,self.toolbar_icon)

				if self.is_light_colored:
					ANIM = SPINNER_ANIMATION
				else:
					ANIM = LIGHT_SPINNER_ANIMATION

				self.spinner = QMovie(ANIM)

				self.spinner.frameChanged.connect(lambda state,b=self.corner_widget: self.corner_widget.setIcon( QIcon(self.spinner.currentPixmap()) ) )

	def openPlugDir(self):
		QDesktopServices.openUrl(QUrl("file:"+PLUGIN_DIRECTORY))

		x = Blank()
		x.show()
		x.close()

	def openCommandDocumentation(self):
		idir = sys.path[0]
		DOCUMENTATION_DIRECTORY = os.path.join(idir, "documentation")
		DOCUMENTATION = os.path.join(DOCUMENTATION_DIRECTORY, "Erk_Scripting_and_Commands.pdf")

		QDesktopServices.openUrl(QUrl("file:"+DOCUMENTATION))

		x = Blank()
		x.show()
		x.close()

	def openPluginDocumentation(self):
		idir = sys.path[0]
		DOCUMENTATION_DIRECTORY = os.path.join(idir, "documentation")
		DOCUMENTATION = os.path.join(DOCUMENTATION_DIRECTORY, "Erk_Plugin_Guide.pdf")

		QDesktopServices.openUrl(QUrl("file:"+DOCUMENTATION))

		x = Blank()
		x.show()
		x.close()

	def showStyleDialog(self):
		FormatTextDialog(self)

	def showScriptEditor(self):
		self.seditors = ScriptEditor(None,self,self.configfile,self.scriptsdir,None)
		self.seditors.resize(640,480)

		self.seditors.clientsRefreshed(events.fetch_connections())

	def menuExportLog(self):
		d = ExportLogDialog(self)
		if d:
			elog = d[0]
			dlog = d[1]
			llog = d[2]
			do_json = d[3]
			do_epoch = d[4]
			if not do_json:
				options = QFileDialog.Options()
				options |= QFileDialog.DontUseNativeDialog
				fileName, _ = QFileDialog.getSaveFileName(self,"Save export As...",INSTALL_DIRECTORY,"Text File (*.txt);;All Files (*)", options=options)
				if fileName:
					# extension = os.path.splitext(fileName)[1]
					# if extension.lower()!='txt': fileName = fileName + ".txt"
					efl = len("txt")+1
					if fileName[-efl:].lower()!=f".txt": fileName = fileName+f".txt"
					dump = dumpLog(elog,dlog,llog,do_epoch)
					code = open(fileName,mode="w",encoding="utf-8")
					code.write(dump)
					code.close()
			else:
				options = QFileDialog.Options()
				options |= QFileDialog.DontUseNativeDialog
				fileName, _ = QFileDialog.getSaveFileName(self,"Save export As...",INSTALL_DIRECTORY,"JSON File (*.json);;All Files (*)", options=options)
				if fileName:
					# extension = os.path.splitext(fileName)[1]
					# if extension.lower()!='json': fileName = fileName + ".json"
					efl = len("json")+1
					if fileName[-efl:].lower()!=f".json": fileName = fileName+f".json"
					dump = dumpLogJson(elog,do_epoch)
					code = open(fileName,mode="w",encoding="utf-8")
					code.write(dump)
					code.close()

	def exportPackage(self):
		x = ExportPackageDialog(self)
		info = x.get_name_information(self)

		if info:

			default_outfile = os.path.basename(info)

			if os.path.isfile(info):
				options = QFileDialog.Options()
				options |= QFileDialog.DontUseNativeDialog
				fileName, _ = QFileDialog.getSaveFileName(self,"Save Package As...",default_outfile,f"{APPLICATION_NAME} Package File (*.{PACKAGE_FILE_EXTENSION})", options=options)
				if fileName:
					efl = len(PACKAGE_FILE_EXTENSION)+1
					if fileName[-efl:].lower()!=f".{PACKAGE_FILE_EXTENSION}": fileName = fileName+f".{PACKAGE_FILE_EXTENSION}"
					zf = zipfile.ZipFile(fileName, "w")
					zf.write(info,os.path.basename(info))
					zf.close()
				return

		if info:

			default_outfile = os.path.basename(info)+f".{PACKAGE_FILE_EXTENSION}"

			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			fileName, _ = QFileDialog.getSaveFileName(self,"Save Package As...",default_outfile,f"{APPLICATION_NAME} Package File (*.{PACKAGE_FILE_EXTENSION})", options=options)
			if fileName:
				efl = len(PACKAGE_FILE_EXTENSION)+1
				if fileName[-efl:].lower()!=f".{PACKAGE_FILE_EXTENSION}": fileName = fileName+f".{PACKAGE_FILE_EXTENSION}"
				zf = zipfile.ZipFile(fileName, "w")
				for dirname, subdirs, files in os.walk(info):
					pname = os.path.basename(info)
					for fname in files:
						if "__pycache__" in fname: continue
						filename, file_extension = os.path.splitext(fname)
						if file_extension.lower()==".pyc": continue
						sfile = os.path.join(dirname,fname)
						bname = os.path.basename(sfile)

						#zf.write(sfile,pname+"\\"+bname)
						# The ^^above unsurprisingly caused a mangled zip to be exported
						# The following fixes that
						zf.write(os.path.join(dirname, fname), os.path.relpath(os.path.join(dirname, fname), os.path.join(info, '..')))

				zf.close()

	# def rebuildPluginMenu(self):

	# 	self.pluginMenu.clear()

	# 	if not self.block_install:

	# 		entry = MenuAction(self,MENU_INSTALL_ICON,"Install","Install a plugin",25,self.menuInstall)
	# 		self.pluginMenu.addAction(entry)

	# 		if not config.PLUGINS_ENABLED:
	# 			entry.setEnabled(False)

	# 	if not hasattr(self,"plugins"):
	# 		self.plugins = PluginCollection("plugins")
	# 		self.display_load_errors()

	# 	if len(self.plugins.plugins)==0:

	# 		self.pluginMenu.addSeparator()

	# 		l1 = QLabel("<br>&nbsp;<b>No plugins installed</b>&nbsp;<br>")
	# 		l1.setAlignment(Qt.AlignCenter)
	# 		entry = QWidgetAction(self)
	# 		entry.setDefaultWidget(l1)
	# 		self.pluginMenu.addAction(entry)

	# 		self.expPackMenu.setVisible(False)
			
	# 	else:
	# 		s = textSeparator(self,"Installed plugins")
	# 		self.pluginMenu.addAction(s)

	# 	plist = {}

	# 	for p in self.plugins.plugins:

	# 		if p._package in plist:
	# 			plist[p._package].append(p)
	# 		else:
	# 			plist[p._package] = []
	# 			plist[p._package].append(p)

	# 	for pack in plist:

	# 		m = self.pluginMenu.addMenu(QIcon(PACKAGE_ICON),pack)

	# 		for p in plist[pack]: plugdir = p._packdir
	# 		plugtype = "package"

	# 		if plugdir==PLUGIN_DIRECTORY:
	# 			plugdir = p.__file__
	# 			plugtype = "plugin"
	# 			m.setIcon(QIcon(PLUGIN_ICON))

	# 		if not config.PLUGINS_ENABLED:
	# 			m.setEnabled(False)

	# 		for p in plist[pack]:

	# 			if os.path.isfile(p._packicon): m.setIcon(QIcon(p._packicon))

	# 			if os.path.isfile(p._icon):
	# 				icon = p._icon
	# 			else:
	# 				icon = PLUGIN_ICON

	# 			args = []
	# 			if p.version:
	# 				PLUGIN_VERSION = p.version + " "
	# 			else:
	# 				PLUGIN_VERSION = ''

	# 			if p.author and p.author!="Unknown":
	# 				args.append(p.author)

	# 			if p.website:
	# 				args.append(f"<a href=\"{p.website}\">Website</a>")

	# 			if p.source:
	# 				args.append(f"<a href=\"{p.source}\">Source Code</a>")

	# 			max_length = 40
	# 			if len(p.description)>max_length:
	# 				if len(p.description)>=max_length+3:
	# 					offset = max_length-3
	# 				elif len(p.description)==max_length+2:
	# 					offset = max_length-2
	# 				elif len(p.description)==max_length+1:
	# 					offset = max_length-1
	# 				else:
	# 					offset = max_length
	# 				display_description = p.description[0:offset]+"..."
	# 			else:
	# 				display_description = p.description


	# 			if len(args)==3:
	# 				entry = Menu5Action(self,icon,p.name+" "+PLUGIN_VERSION,display_description,*args,25)
	# 			elif len(args)==2:
	# 				entry = Menu4Action(self,icon,p.name+" "+PLUGIN_VERSION,display_description,*args,25)
	# 			elif len(args)==1:
	# 				entry = Menu3Action(self,icon,p.name+" "+PLUGIN_VERSION,display_description,*args,25)
	# 			else:
	# 				entry = MenuNoAction(self,icon,p.name+" "+PLUGIN_VERSION,display_description,25)

	# 			m.addAction(entry)

	# 			if config.DEVELOPER_MODE:

	# 				entry = QAction(QIcon(EDITOR_ICON),"Edit "+os.path.basename(p.__file__),self)
	# 				entry.triggered.connect(lambda state,f=p.__file__: self.editPlugin(f))
	# 				m.addAction(entry)

	# 				if hasattr(p,"load"):

	# 					entry = QAction(QIcon(LAMBDA_ICON),"Execute load()",self)
	# 					entry.triggered.connect(lambda state,f=p.name: self.plugins.forceload(f))
	# 					m.addAction(entry)

	# 				if hasattr(p,"unload"):

	# 					entry = QAction(QIcon(LAMBDA_ICON),"Execute unload()",self)
	# 					entry.triggered.connect(lambda state,f=p.name: self.plugins.forceunload(f))
	# 					m.addAction(entry)

	# 			if p.name in config.DISABLED_PLUGINS:
	# 				enabled = False
	# 				entry = QAction(QIcon(UNCHECKED_ICON),"Enabled",self)
	# 			else:
	# 				enabled = True
	# 				entry = QAction(QIcon(CHECKED_ICON),"Enabled",self)

	# 			entry.triggered.connect(lambda state,n=p.name: self.toggle_plugin(n))
	# 			m.addAction(entry)

	# 			m.addSeparator()
	# 			#insertNoTextSeparator(self,m)

	# 		entry = QAction(QIcon(UNINSTALL_ICON),"Uninstall \""+pack+"\"",self)
	# 		entry.triggered.connect(lambda state,f=plugdir,p=pack: self.uninstall_plugin(f,p))
	# 		m.addAction(entry)

	# def uninstall_plugin(self,directory,upack):

	# 	msgBox = QMessageBox()
	# 	msgBox.setIconPixmap(QPixmap(ERK_ICON))
	# 	msgBox.setWindowIcon(QIcon(ERK_ICON))
	# 	msgBox.setText("Are you sure you want to uninstall \""+upack+"\"?")
	# 	msgBox.setWindowTitle("Uninstall "+upack)
	# 	msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

	# 	rval = msgBox.exec()

	# 	if rval == QMessageBox.Cancel:
	# 		return

	# 	# Find the pack we're uninstalling
	# 	plist = {}

	# 	for p in self.plugins.plugins:

	# 		if p._package in plist:
	# 			plist[p._package].append(p)
	# 		else:
	# 			plist[p._package] = []
	# 			plist[p._package].append(p)

	# 	for pack in plist:
	# 		if pack==upack:
	# 			# Found it!
	# 			for p in plist[pack]:
	# 				# Execute unload()
	# 				self.plugins.uninstall_forceunload(p.name)

	# 	if os.path.isdir(directory):
	# 		shutil.rmtree(directory)
	# 	elif os.path.isfile(directory):
	# 		os.remove(directory)

	# 	self.plugins.reload_plugins(True)
	# 	self.rebuildPluginMenu()

	# def menuInstall(self):
	# 	# PLUGIN_DIRECTORY
	# 	options = QFileDialog.Options()
	# 	options |= QFileDialog.DontUseNativeDialog
	# 	fileName, _ = QFileDialog.getOpenFileName(self,"Select Plugin Package", INSTALL_DIRECTORY,f"{APPLICATION_NAME} Package File (*.{PACKAGE_FILE_EXTENSION});;Python File (*.py)", options=options)
	# 	if fileName:

	# 		x = InstallDialog(fileName)
	# 		if x:
	# 			file_name, file_extension = os.path.splitext(fileName)
	# 			if file_extension.lower()==f".{PACKAGE_FILE_EXTENSION}":
	# 				with ZipFile(fileName,'r') as zipObj:
	# 					zipObj.extractall(PLUGIN_DIRECTORY)
	# 			else:
	# 				bname = os.path.basename(fileName)
	# 				shutil.copy(fileName, os.path.join(PLUGIN_DIRECTORY, bname))

	# 			self.plugins.reload_plugins(True)
	# 			self.display_load_errors()
	# 			self.rebuildPluginMenu()

	# def menuEditor(self):
	# 	x = EditorDialog(self,None,None,self.configfile,self.stylefile)
	# 	w = config.DEFAULT_APP_WIDTH
	# 	h = config.DEFAULT_APP_HEIGHT
	# 	x.resize(w,h)
	# 	x.show()

	# def editPlugin(self,filename):
	# 	x = EditorDialog(self,filename,None,self.configfile,self.stylefile)
	# 	w = config.DEFAULT_APP_WIDTH
	# 	h = config.DEFAULT_APP_HEIGHT
	# 	x.resize(w,h)
	# 	x.show()

	# def toggle_plugin(self,name):
	# 	if name in config.DISABLED_PLUGINS:
	# 		config.DISABLED_PLUGINS.remove(name)
	# 	else:
	# 		config.DISABLED_PLUGINS.append(name)
	# 	config.save_settings(self.configfile)
	# 	self.plugins.load()
	# 	self.rebuildPluginMenu()

	# def menuReloadPlugins(self):
	# 	self.plugins.reset_errors()
	# 	self.plugins.reload_plugins(True)
	# 	self.display_load_errors()
	# 	self.rebuildPluginMenu()

	# 	x = Blank()
	# 	x.show()
	# 	x.close()

	def toggleSetting(self,setting):

		if setting=="hide_join":
			if config.HIDE_JOIN_MESSAGE:
				config.HIDE_JOIN_MESSAGE = False
				self.hide_join.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_JOIN_MESSAGE = True
				self.hide_join.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_part":
			if config.HIDE_PART_MESSAGE:
				config.HIDE_PART_MESSAGE = False
				self.hide_part.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_PART_MESSAGE = True
				self.hide_part.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_invite":
			if config.HIDE_INVITE_MESSAGE:
				config.HIDE_INVITE_MESSAGE = False
				self.hide_invite.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_INVITE_MESSAGE = True
				self.hide_invite.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_nick":
			if config.HIDE_NICK_MESSAGE:
				config.HIDE_NICK_MESSAGE = False
				self.hide_nick.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_NICK_MESSAGE = True
				self.hide_nick.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_quit":
			if config.HIDE_QUIT_MESSAGE:
				config.HIDE_QUIT_MESSAGE = False
				self.hide_quit.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_QUIT_MESSAGE = True
				self.hide_quit.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_topic":
			if config.HIDE_TOPIC_MESSAGE:
				config.HIDE_TOPIC_MESSAGE = False
				self.hide_topic.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_TOPIC_MESSAGE = True
				self.hide_topic.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="hide_mode":
			if config.HIDE_MODE_DISPLAY:
				config.HIDE_MODE_DISPLAY = False
				self.hide_mode.setIcon(QIcon(UNCHECKED_ICON))
			else:
				config.HIDE_MODE_DISPLAY = True
				self.hide_mode.setIcon(QIcon(CHECKED_ICON))
			config.save_settings(self.configfile)
			events.rerender_all()
			return

		if setting=="fullscreen":
			if self.fullscreen:
				self.fullscreen = False
				self.showNormal()
				self.set_full.setText("Enter full screen more")
				self.winsizeMenuEntry.setEnabled(True)
			else:
				self.fullscreen = True
				self.showFullScreen()
				self.set_full.setText("Exit full screen more")
				self.winsizeMenuEntry.setEnabled(False)
			return

	def linkClicked(self,url):
		if url.host():
			QDesktopServices.openUrl(url)
			self.starter.setSource(QUrl())
			self.starter.moveCursor(QTextCursor.End)

	def open_link_in_browser(self,url):
		u = QUrl()
		u.setUrl(url)
		QDesktopServices.openUrl(u)

	def menuAbout(self):
		self.about_dialog = AboutDialog()

	def reload_all_text(self):
		events.rerender_all()

	def menuCombo(self):
		info = ComboDialog(self.userfile,self.block_scripts,self.scriptsdir,self.configfile)
		if info!=None:
			self.connectToIRCServer(info)

	def menuComboCmd(self,do_ssl=None,do_reconnect=None):
		info = ComboDialogCmd(self.userfile,do_ssl,do_reconnect,self.block_scripts,self.scriptsdir,self.configfile)
		if info!=None:
			self.connectToIRCServer(info)

	def menuJoin(self,client):
		info = JoinDialog()
		if info!=None:
			channel = info[0]
			key = info[1]
			client.join(channel,key)

	def menuNick(self,client):
		info = NickDialog(client.nickname,self)
		if info!=None:
			client.setNick(info)

	def menuResize(self):
		info = WindowSizeDialog(self)
		if info!=None:
			config.DEFAULT_APP_WIDTH = info[0]
			config.DEFAULT_APP_HEIGHT = info[1]
			config.save_settings(self.configfile)
			self.resize(info[0],info[1])

	def eventFilter(self, source, event):

		# User List Menu
		if (event.type() == QtCore.QEvent.ContextMenu and source is self.connection_display):

			item = source.itemAt(event.pos())
			if item is None: return True

			if hasattr(item,"erk_widget"):
				if item.erk_widget:
					if hasattr(item,"erk_channel"):
						menu = QMenu(self)

						if item.erk_console:

							if item.erk_client.hostname:
								entry = MenuNoActionRaw(self,CONNECT_MENU_ICON,item.erk_client.server+":"+str(item.erk_client.port),item.erk_client.hostname,25)
								menu.addAction(entry)
							else:
								entry = MenuNoActionRaw(self,CONNECT_MENU_ICON,item.erk_client.server+":"+str(item.erk_client.port),'',25)
								menu.addAction(entry)

							menu.addSeparator()

							if item.erk_client.network:
								link = get_network_url(item.erk_client.network)
								if link:
									entry = QAction(QIcon(LINK_ICON),item.erk_client.network+" website",self)
									entry.triggered.connect(lambda state,u=link: self.open_link_in_browser(u))
									menu.addAction(entry)

							settingsMenu = buildServerSettingsMenu(self,item.erk_client)
							settingsMenu.setIcon(QIcon(SETTINGS_ICON))

							menu.addMenu(settingsMenu)

							if not self.block_styles:

								menu.addSeparator()

								entry = QAction(QIcon(FORMAT_ICON),"Load style",self)
								entry.triggered.connect(lambda state,client=item.erk_client: self.load_style_file_in_window_server(client))
								menu.addAction(entry)

								entry = QAction(QIcon(EDIT_ICON),"Edit style",self)
								entry.triggered.connect(lambda state,client=item.erk_client: self.edit_style_file_in_window(client,None))
								menu.addAction(entry)

								if events.using_custom_style_server(item.erk_client):
									entry = QAction(QIcon(UNDO_ICON),"Revert style to default",self)
									entry.triggered.connect(lambda state,client=item.erk_client: self.restore_style_file_in_window_server(client))
									menu.addAction(entry)

							menu.addSeparator()

							entry = QAction(QIcon(NICK_ICON),"Change nickname",self)
							entry.triggered.connect(lambda state,client=item.erk_client: self.menuNick(client))
							menu.addAction(entry)

							entry = QAction(QIcon(CHANNEL_ICON),"Join channel",self)
							entry.triggered.connect(lambda state,client=item.erk_client: self.menuJoin(client))
							menu.addAction(entry)

							menu.addSeparator()

							entry = QAction(QIcon(DISCONNECT_ICON),"Disconnect",self)
							entry.triggered.connect(lambda state,client=item.erk_client: events.disconnect_from_server(client))
							menu.addAction(entry)
						else:
							if not self.block_styles:
								entry = QAction(QIcon(FORMAT_ICON),"Load style",self)
								entry.triggered.connect(lambda state,client=item.erk_client,name=item.text(0): self.load_style_file_in_window(client,name))
								menu.addAction(entry)

								entry = QAction(QIcon(EDIT_ICON),"Edit style",self)
								entry.triggered.connect(lambda state,client=item.erk_client,name=item.text(0): self.edit_style_file_in_window(client,name))
								menu.addAction(entry)

								if events.using_custom_style(item.erk_client,item.text(0)):
									entry = QAction(QIcon(UNDO_ICON),"Revert style to default",self)
									entry.triggered.connect(lambda state,client=item.erk_client,name=item.text(0): self.restore_style_file_in_window(client,name))
									menu.addAction(entry)

								menu.addSeparator()

							if item.erk_channel:

								channel = item.text(0)

								if len(item.erk_widget.banlist)>0:

									bannedmenu = QMenu("Banned users",self)
									bannedmenu.setIcon(QIcon(BAN_ICON))
									for c in item.erk_widget.banlist:
										e = QAction(F"{c[0]}", self) 
										bannedmenu.addAction(e)
									menu.addMenu(bannedmenu)

								entry = QAction(QIcon(EXIT_ICON),"Leave channel",self)
								entry.triggered.connect(lambda state,client=item.erk_client,name=channel: client.part(name))
								menu.addAction(entry)
							else:

								channel = item.text(0)

								entry = QAction(QIcon(EXIT_ICON),"Close private chat",self)
								entry.triggered.connect(lambda state,client=item.erk_client,name=channel: events.close_private_window(client,name))
								menu.addAction(entry)

				else:
					return True
			else:
				return True

			action = menu.exec_(self.connection_display.mapToGlobal(event.pos()))

			self.connection_display.clearSelection()

			return True

		return super(Erk, self).eventFilter(source, event)

	def edit_style_file_in_window(self,client,name):
		FormatEditDialog(self,client,name)

	def restore_style_file_in_window(self,client,name):
		events.restore_chat_style(client,name)

	def restore_style_file_in_window_server(self,client):
		events.restore_chat_style_server(client)

	def load_style_file_in_window(self,client,name):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self,"Load Style File",self.styledir,f"{APPLICATION_NAME} Style File (*.{STYLE_FILE_EXTENSION});;All Files (*)", options=options)
		if fileName:
			events.load_chat_style(client,name,fileName)

	def load_style_file_in_window_server(self,client):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self,"Load Style File",self.styledir,f"{APPLICATION_NAME} Style File (*.{STYLE_FILE_EXTENSION});;All Files (*)", options=options)
		if fileName:
			events.load_chat_style_server(client,fileName)

	def open_private_window(self,client,nickname):
		events.open_private_window(client,nickname)

	def connectToIRCServer(self,info):
		actual_connect_attempt = False
		using_ssl = False
		if info.ssl:
			if info.reconnect:
				reconnectSSL(
					nickname=info.nickname,
					server=info.server,
					port=info.port,
					alternate=info.alternate,
					password=info.password,
					username=info.username,
					realname=info.realname,
					ssl=info.ssl,
					gui=self,
					reconnect=True,
					autojoin=info.autojoin,
					failreconnect=info.failreconnect,
					script=info.do_script,
				)
				actual_connect_attempt = True
				using_ssl = True
			else:
				connectSSL(
					nickname=info.nickname,
					server=info.server,
					port=info.port,
					alternate=info.alternate,
					password=info.password,
					username=info.username,
					realname=info.realname,
					ssl=info.ssl,
					gui=self,
					reconnect=False,
					autojoin=info.autojoin,
					failreconnect=info.failreconnect,
					script=info.do_script,
				)
				actual_connect_attempt = True
				using_ssl = True
		else:
			if info.reconnect:
				reconnect(
					nickname=info.nickname,
					server=info.server,
					port=info.port,
					alternate=info.alternate,
					password=info.password,
					username=info.username,
					realname=info.realname,
					ssl=info.ssl,
					gui=self,
					reconnect=True,
					autojoin=info.autojoin,
					failreconnect=info.failreconnect,
					script=info.do_script,
				)
				actual_connect_attempt = True
			else:
				connect(
					nickname=info.nickname,
					server=info.server,
					port=info.port,
					alternate=info.alternate,
					password=info.password,
					username=info.username,
					realname=info.realname,
					ssl=info.ssl,
					gui=self,
					reconnect=False,
					autojoin=info.autojoin,
					failreconnect=info.failreconnect,
					script=info.do_script,
				)
				actual_connect_attempt = True

		# Save connect attempts to the user history
		if actual_connect_attempt:
			user_info = get_user(self.userfile)
			if info.password:
				cpass = info.password
			else:
				cpass = ""
				
			if user_info["save_history"]:

				# Only make a save attemp if we're not using
				# the combo dialog to connect
				if not info.dialog:
					user_history = user_info["history"]

					# make sure server isn't in history
					inhistory = False
					for s in user_history:
						if s[0]==info.server:
							if s[1]==str(info.port):
								inhistory = True

					if inhistory==False:

						if using_ssl:
							ussl = "ssl"
						else:
							ussl = "normal"

						entry = [ info.server,str(info.port),UNKNOWN_NETWORK,ussl,cpass ]
						user_history.append(entry)

						user_info["history"] = user_history

			user_info["last_server"] = info.server
			user_info["last_port"] = str(info.port)
			user_info["last_password"] = cpass
			if using_ssl:
				user_info["ssl"] = True
			else:
				user_info["ssl"] = False

			save_user(user_info,self.userfile)

# SERVER SETTINGS MENU

def buildServerSettingsMenu(self,client):

	supports = client.supports # list
	maxchannels = client.maxchannels
	maxnicklen = client.maxnicklen
	channellen = client.channellen
	topiclen = client.topiclen
	kicklen = client.kicklen
	awaylen = client.awaylen
	maxtargets = client.maxtargets
	modes = client.modes
	chanmodes = client.chanmodes #list
	prefix = client.prefix # list
	cmds = client.cmds # list
	casemapping = client.casemapping
	maxmodes = client.maxmodes

	optionsMenu = QMenu("Server settings")

	e = textSeparator(self,"Limits")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum channels"+f":</b> {maxchannels}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum nickname length"+f":</b> {maxnicklen}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum channel length"+f":</b> {channellen}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum topic length"+f":</b> {topiclen}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum kick length"+f":</b> {kicklen}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum away length"+f":</b> {awaylen}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum message targets"+f":</b> {maxtargets}")
	optionsMenu.addAction(e)

	e = plainTextAction(self,"<b>Maximum modes per user"+f":</b> {modes}")
	optionsMenu.addAction(e)

	e = textSeparator(self,"Miscellaneous")
	optionsMenu.addAction(e)

	if len(maxmodes)>0:
		maxmodesmenu = QMenu("Maximum modes",self)
		for c in maxmodes:
			e = QAction(F"{c[0]}: {c[1]}", self) 
			maxmodesmenu.addAction(e)
		optionsMenu.addMenu(maxmodesmenu)

	if len(cmds)>0:
		cmdmenu = QMenu("Commands",self)
		for c in cmds:
			e = QAction(F"{c}", self) 
			cmdmenu.addAction(e)
		optionsMenu.addMenu(cmdmenu)

	if len(supports)>0:
		supportsmenu = QMenu("Supports",self)
		for c in supports:
			e = QAction(F"{c}", self) 
			supportsmenu.addAction(e)
		optionsMenu.addMenu(supportsmenu)

	if len(chanmodes)>0:
		chanmodemenu = QMenu("Channel modes",self)
		ct = 0
		for c in chanmodes:
			if ct==0:
				ctype = "A"
			elif ct==1:
				ctype = "B"
			elif ct==2:
				ctype = "C"
			elif ct==3:
				ctype = "D"
			e = QAction(F"{ctype}: {c}", self) 
			chanmodemenu.addAction(e)
			ct = ct + 1
		optionsMenu.addMenu(chanmodemenu)

	if len(prefix)>0:
		prefixmenu = QMenu("Status prefixes",self)
		for c in prefix:
			m = c[0]
			s = c[1]
			if s=="&": s="&&"
			e = QAction(F"{m}: {s}", self)
			if m=="o": e.setIcon(QIcon(USERLIST_OPERATOR_ICON))
			if m=="v": e.setIcon(QIcon(USERLIST_VOICED_ICON))
			if m=="a": e.setIcon(QIcon(USERLIST_ADMIN_ICON))
			if m=="q": e.setIcon(QIcon(USERLIST_OWNER_ICON))
			if m=="h": e.setIcon(QIcon(USERLIST_HALFOP_ICON))
			prefixmenu.addAction(e)
		optionsMenu.addMenu(prefixmenu)

	return optionsMenu
