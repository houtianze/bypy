#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys

vi = sys.version_info
if vi[0] == 2:
	import ScrolledText as scrt
	import Tkinter as tk
elif vi[0] == 3:
	from tkinter import scrolledtext as scrt
	import tkinter as tk

from .termcolor import TermColor

MyReadOnlyText = tk.Text
MyLogText = scrt.ScrolledText
try:
# https://stackoverflow.com/questions/3842155/is-there-a-way-to-make-the-tkinter-text-widget-read-only
	from idlelib.WidgetRedirector import WidgetRedirector

	class ReadOnlyText(tk.Text):
		def __init__(self, *args, **kwargs):
			tk.Text.__init__(self, *args, **kwargs)
			self.redirector = WidgetRedirector(self)
			self.insert = self.redirector.register("insert", lambda *args, **kw: "break")
			self.delete = self.redirector.register("delete", lambda *args, **kw: "break")

	class ReadOnlyScrolledText(scrt.ScrolledText):
		def __init__(self, *args, **kwargs):
			scrt.ScrolledText.__init__(self, *args, **kwargs)
			self.redirector = WidgetRedirector(self)
			self.insert = self.redirector.register("insert", lambda *args, **kw: "break")
			self.delete = self.redirector.register("delete", lambda *args, **kw: "break")

	MyReadOnlyText = ReadOnlyText
	MyLogText = ReadOnlyScrolledText
except:
	# it's OK, we just ignore it
	pass

Stretch = tk.N+tk.E+tk.S+tk.W
GridStyle = { 'padx' : 0, 'pady' : 0 }

ColorMap = {
	TermColor.Black: "black",
	TermColor.Red: "red",
	TermColor.Green: "green",
	TermColor.Yellow: "yellow",
	TermColor.Blue: "blue",
	TermColor.Magenta: "magenta",
	TermColor.Cyan: "cyan",
	TermColor.White: "white" }

def fgtag(text):
	return 'FG' + text

def bgtag(text):
	return 'BG' + text

def centerwindow(w):
	w.update() # fucking bit me
	sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
	width, height = w.winfo_width(), w.winfo_height()
	x = (sw - width) // 2
	y = (sh - height) // 2
	w.geometry('{}x{}+{}+{}'.format(width, height, x, y))

