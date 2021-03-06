
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore

from . import config

def format(color, style=''):
	"""Return a QTextCharFormat with the given attributes.
	"""
	_color = QColor()
	_color.setNamedColor(color)

	_format = QTextCharFormat()
	_format.setForeground(_color)
	if 'bold' in style:
		_format.setFontWeight(QFont.Bold)
	if 'italic' in style:
		_format.setFontItalic(True)
	if 'bi' in style:
		_format.setFontWeight(QFont.Bold)
		_format.setFontItalic(True)

	return _format

class ErkScriptHighlighter (QSyntaxHighlighter):

	def __init__(self, document,configfile):
		QSyntaxHighlighter.__init__(self, document)

		config.load_settings(configfile)

		# Make sure to escape any special characters in the
		# command symbol; this also allows for command
		# symbols that are more than one character
		special = ['\\','^','$','.','|','?','*','+','(',')','{']
		cmdsymbol = ''
		for c in config.INPUT_COMMAND_SYMBOL:
			if c in special:
				c = '\\'+c
			cmdsymbol = cmdsymbol + c

		erk = [
			cmdsymbol+'away',
			cmdsymbol+'back',
			cmdsymbol+'invite',
			cmdsymbol+'join',
			cmdsymbol+'list',
			cmdsymbol+'me',
			cmdsymbol+'msg',
			cmdsymbol+'nick',
			cmdsymbol+'notice',
			cmdsymbol+'oper',
			cmdsymbol+'part',
			cmdsymbol+'quit',
			cmdsymbol+'send',
			cmdsymbol+'time',
			cmdsymbol+'topic',
			cmdsymbol+'version',
			cmdsymbol+'who',
			cmdsymbol+'whois',
			cmdsymbol+'whowas',
			cmdsymbol+'alias',
			cmdsymbol+'argcount',
			cmdsymbol+'connect',
			cmdsymbol+'connectscript',
			cmdsymbol+'exit',
			cmdsymbol+'help',
			cmdsymbol+'print',
			cmdsymbol+'reconnect',
			cmdsymbol+'refresh',
			cmdsymbol+'ressl',
			cmdsymbol+'script',
			cmdsymbol+'settings',
			cmdsymbol+'ssl',
			cmdsymbol+'style',
			cmdsymbol+'switch',
			cmdsymbol+'wait',
			cmdsymbol+'_alias',
			cmdsymbol+'macro',
			cmdsymbol+'macrohelp',
			cmdsymbol+'unmacro',
			cmdsymbol+'edit',
			cmdsymbol+'msgbox',
			cmdsymbol+'macrousage',
			cmdsymbol+'unalias',
			cmdsymbol+'dictionary',
			cmdsymbol+'undictionary',
			cmdsymbol+'write',
			cmdsymbol+'cat',
		]

		STYLES = {
			'comments': format(config.SCRIPT_SYNTAX_COMMENTS,'bold'),
			'erk': format(config.SCRIPT_SYNTAX_COMMANDS,'bold'),
			'channel': format(config.SCRIPT_SYNTAX_TARGETS,'bold'),
			'alias': format(config.SCRIPT_SYNTAX_ALIAS,'bold'),
		}

		# Comments
		self.script_comments = (QRegExp("(\\/\\*|\\*\\/|\n)"), 1, STYLES['comments'])

		rules = []

		# Commands
		rules += [(r'%s' % o, 0, STYLES['erk'])
			for o in erk]

		# Make sure to escape any special characters in the
		# interpolation symbol; this also allows for interpolation
		# symbols that are more than one character
		special = ['\\','^','$','.','|','?','*','+','(',')','{']
		interp = ''
		for c in config.SCRIPT_INTERPOLATE_SYMBOL:
			if c in special:
				c = '\\'+c
			interp = interp + c

		# Channel names
		rules += [
			(r'(#\w+)', 0, STYLES['channel']),
			(r'(\&\w+)', 0, STYLES['channel']),
			(r'(\!\w+)', 0, STYLES['channel']),
			(r'(\+\w+)', 0, STYLES['channel']),
			(rf'({interp}\w+)', 0, STYLES['alias']),
		]

		# Build a QRegExp for each pattern
		self.rules = [(QRegExp(pat), index, fmt)
			for (pat, index, fmt) in rules]

	def highlightBlock(self, text):

		"""Apply syntax highlighting to the given block of text.
		"""
		# Do other syntax formatting
		for expression, nth, format in self.rules:
			index = expression.indexIn(text, 0)

			while index >= 0:
				index = expression.pos(nth)
				length = len(expression.cap(nth))
				self.setFormat(index, length, format)
				index = expression.indexIn(text, index + length)

		self.setCurrentBlockState(0)

		# Do multi-line comments
		in_multiline = self.match_multiline(text, *self.script_comments)

	def match_multiline(self, text, delimiter, in_state, style):
		if self.previousBlockState() == in_state:
			start = 0
			add = 0
		else:
			start = delimiter.indexIn(text)
			add = delimiter.matchedLength()

		while start >= 0:
			end = delimiter.indexIn(text, start + add)
			if end >= add:
				length = end - start + add + delimiter.matchedLength()
				self.setCurrentBlockState(0)
			else:
				self.setCurrentBlockState(in_state)
				length = len(text) - start + add
			self.setFormat(start, length, style)
			start = delimiter.indexIn(text, start + length)

		if self.currentBlockState() == in_state:
			return True
		else:
			return False
