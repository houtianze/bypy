#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

import sys
from functools import partial

from . import printer_console
from . import bypy
from . import printer
from . import cached
from . import util

try:
	vi = sys.version_info
	if vi[0] == 2:
		import Tkinter
		Tkinter
	elif vi[0] == 3:
		import tkinter
		tkinter
except ImportError:
	printer_gui = None
else:
	from . import printer_gui

def setconsole():
	bypy.pr = cached.pr = util.pr = printer_console.pr
	bypy.prcolor = util.prcolor = printer.prcolor = printer_console.prcolor
	bypy.ask = util.ask = printer_console.ask
	bypy.pprgr = util.pprgr = printer_console.pprgr

def setgui(*arg):
	inst = arg[0]
	bypy.pr = cached.pr = util.pr = partial(printer_gui.pr, inst)
	bypy.prcolor = util.prcolor = printer.prcolor = partial(printer_gui.prcolor, inst)
	bypy.ask = util.ask = partial(printer_gui.ask, inst)
	bypy.pprgr = util.pprgr = partial(printer_gui.pprgr, inst)

def patchpr(func):
	bypy.pr = cached.pr = util.pr = func

def patchprcolor(func):
	bypy.prcolor = util.prcolor = printer.prcolor = func

def patchask(func):
	bypy.ask = util.ask = func

def patchpprgr(func):
	bypy.pprgr = util.pprgr = func

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
