#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys

from .tkutil import (
	ColorMap, fgtag, bgtag,
	Stretch, MyReadOnlyText, GridStyle)

vi = sys.version_info
if vi[0] == 2:
	import Tkinter as tk
elif vi[0] == 3:
	import tkinter as tk

from .termcolor import TermColor
from .tkutil import centerwindow

class AskGui(tk.Toplevel):
	def __init__(self, master = None,
			message = "",
			title = "Question"):
		tk.Toplevel.__init__(self, master)

		self.message = message
		self.input = ''

		self.transient(master)
		self.master = master
		if title:
			self.title(title)

		self.CreateWidgets()
		self.grab_set()

	def End(self, event):
		self.input = self.wInput.get()
		self.master.focus_set()
		self.destroy()

	def CreateWidgets(self):
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(0, weight = 1)
		self.wMessage = MyReadOnlyText(self, height = 8, bg = 'wheat')
		self.wMessage.insert(tk.END, self.message + '\n')
		self.wMessage.insert(tk.END, 'Press [OK] when you are done\n')
		self.wMessage.grid(sticky = Stretch, **GridStyle)
		self.wInput = tk.Entry(self, width = 100)
		self.wInput.grid(row = 1, column = 0, sticky = tk.E + tk.W, **GridStyle)
		self.wInput.bind('<Return>', self.End)
		self.wOK = tk.Button(self, text = 'OK', default = tk.ACTIVE)
		self.wOK.grid(row = 2, column = 0, sticky = Stretch, **GridStyle)
		self.wOK.bind('<Button-1>', self.End)

		self.wInput.focus_set()

		self.protocol("WM_DELETE_WINDOW", lambda: ())

def prcolor(self, msg, fg, bg):
	if self.bLog.get() != 0:
		self.wLog.insert(tk.END, msg + '\n',
			(fgtag(ColorMap[fg]) if fg in ColorMap else fgtag(''),
				bgtag(ColorMap[bg]) if bg in ColorMap else bgtag('')))

def pr(self, msg):
	#return self.prcolor(msg, TermColor.Nil, TermColor.Nil)
	return prcolor(self, msg, TermColor.Nil, TermColor.Nil)

def ask(self, message = "Please input", enter = True, title = "Question"):
	asker = AskGui(self, message, title)
	centerwindow(asker)
	asker.wait_window(asker)
	return asker.input

def pprgr(self, finish, total, start_time= None, existing = 0,
		prefix = '', suffix = '', seg = 1000):
	self.progress.set(self.maxProgress * (finish - existing) // total)

