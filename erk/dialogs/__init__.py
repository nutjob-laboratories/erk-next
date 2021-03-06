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
try:
	import ssl
except ImportError:
	SSL_AVAILABLE = False

from .add_channel import Dialog as AddChannelDialog
from .combo import Dialog as Combo
from .join_channel import Dialog as JoinChannel
from .new_nick import Dialog as Nick
from .window_size import Dialog as WindowSize
from .history_size import Dialog as HistorySize
from .log_size import Dialog as LogSize
from .format import Dialog as FormatText
from .about import Dialog as About
from .editor import Window as Editor
from .export_log import Dialog as ExportLog
from .key import Dialog as Key
from .error import Dialog as Error
from .prefix import Dialog as Prefix
from .list_time import Dialog as ListTime
from .plugin_input import Dialog as PluginInput
from .neterror import Dialog as Neterror
from .install import Dialog as Installer
from .settings import Dialog as Settings
from .autosave_freq import Dialog as Autosave

from .scriptedit import Window as ErkScriptEditor
#from .alias import Dialog as InsertAlias

def AutosaveDialog():
	x = Autosave()
	info = x.get_entry_information()
	del x

	if not info: return None
	return info

def SettingsDialog(configfile,obj):
	x = Settings(configfile,obj)
	x.show()
	return x

def InstallDialog(file):
	x = Installer(file)
	info = x.get_install_information(file)
	del x

	if not info: return None
	return info

def NeterrorDialog(title,text):
	x = Neterror(title,text)
	x.show()
	return x

def PluginInputDialog(title,text,icon,obj=None):
	x = PluginInput(title,text,icon,obj)
	info = x.get_input_information(title,text,icon,obj)
	del x

	if not info: return None
	return info

def ListTimeDialog():
	x = ListTime()
	info = x.get_entry_information()
	del x

	if not info: return None
	return info

def PrefixDialog():
	x = Prefix()
	info = x.get_system_information()
	del x

	if not info: return None
	return info

def KeyDialog():
	x = Key()
	info = x.get_channel_information()
	del x

	if not info: return None
	return info

def ExportLogDialog(obj):
	x = ExportLog(obj)
	info = x.get_name_information(obj)
	del x

	if not info: return None
	return info

def ErrorDialog(obj,errlist=None):
	x = Error(errlist,obj)
	x.resize(400,250)
	x.show()

def EditorDialog(obj=None,filename=None,app=None,config=None,stylefile=None):
	x = Editor(filename,obj,app,config,stylefile)
	return x

def ScriptEditor(filename,parent,configfile,scriptsdir,app):
	x = ErkScriptEditor(filename,parent,configfile,scriptsdir,app)
	x.show()

	return x

def AboutDialog():
	x = About()
	x.show()
	return x

def FormatTextDialog(obj):
	x = FormatText(obj)
	x.show()

def FormatEditDialog(obj,client,name):
	x = FormatText(obj,client,name)
	x.show()

def LogSizeDialog():
	x = LogSize()
	info = x.get_entry_information()
	del x

	if not info: return None
	return info

def HistorySizeDialog():
	x = HistorySize()
	info = x.get_entry_information()
	del x

	if not info: return None
	return info

def WindowSizeDialog(obj):
	x = WindowSize(obj)
	info = x.get_window_information(obj)
	del x

	if not info: return None
	return info

def NickDialog(nick,obj):
	x = Nick(nick,obj)
	info = x.get_nick_information(nick,obj)
	del x

	if not info: return None
	return info

def JoinDialog():
	x = JoinChannel()
	info = x.get_channel_information()
	del x

	if not info: return None
	return info

def ComboDialog(userfile,block_scripts,scriptsdir,configfile):
	x = Combo(SSL_AVAILABLE,userfile,None,None,block_scripts,scriptsdir,configfile)
	info = x.get_connect_information(SSL_AVAILABLE,userfile,None,None,block_scripts,scriptsdir,configfile)
	del x

	if not info: return None
	return info

def ComboDialogCmd(userfile,do_ssl=None,do_reconnect=None,block_scripts=False,scriptsdir='',configfile=''):
	x = Combo(SSL_AVAILABLE,userfile,do_ssl,do_reconnect,block_scripts,scriptsdir)
	info = x.get_connect_information(SSL_AVAILABLE,userfile,do_ssl,do_reconnect,block_scripts,scriptsdir,configfile)
	del x

	if not info: return None
	return info

def ComboDialogBanner(userfile,block_scripts,scriptsdir,configfile):
	x = Combo(SSL_AVAILABLE,userfile,None,None,block_scripts,scriptsdir,configfile,True)
	info = x.get_connect_information(SSL_AVAILABLE,userfile,None,None,block_scripts,scriptsdir,configfile,True)
	del x

	if not info: return None
	return info