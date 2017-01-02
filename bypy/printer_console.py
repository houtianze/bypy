#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys
import time

# unify Python 2 and 3
if sys.version_info[0] == 3:
	raw_input = input

from . import const
from . import gvar
from .printer_util import (
	iswindows, human_speed, human_size, human_time_short)

def colorstr(msg, fg, bg):
	CSI = '\x1b['
	fgs = ''
	bgs = ''
	if fg >=0 and fg <= 7:
		fgs = str(fg + 30)

	if bg >= 0 and bg <=7:
		bgs = str(bg + 40)

	cs = ';'.join([fgs, bgs]).strip(';')
	if cs:
		return CSI + cs + 'm' + msg + CSI + '0m'
	else:
		return msg

def pr(msg):
	print(msg)
	# we need to flush the output periodically to see the latest status
	now = time.time()
	if now - gvar.last_stdout_flush >= const.PrintFlushPeriodInSec:
		sys.stdout.flush()
		gvar.last_stdout_flush = now

def prcolor(msg, fg, bg):
	if sys.stdout.isatty() and not iswindows():
		pr(colorstr(msg, fg, bg))
	else:
		pr(msg)

def ask(msg, enter = True):
	pr(msg)
	if enter:
		pr('Press [Enter] when you are done')
	return raw_input()

# print progress
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def pprgr(finish, total, start_time = None, existing = 0,
		prefix = '', suffix = '', seg = 20):
	# we don't want this goes to the log, so we use stderr
	if total > 0:
		segth = seg * finish // total
		percent = 100 * finish // total
		current_batch_percent = 100 * (finish - existing) // total
	else:
		segth = seg
		percent = 100
	eta = ''
	now = time.time()
	if start_time is not None and current_batch_percent > 5 and finish > 0:
		finishf = float(finish) - float(existing)
		totalf = float(total)
		remainf = totalf - float(finish)
		elapsed = now - start_time
		speed = human_speed(finishf / elapsed)
		eta = 'ETA: ' + human_time_short(elapsed * remainf / finishf) + \
				' (' + speed + ', ' + \
				human_time_short(elapsed) + ' gone)'
	msg = '\r' + prefix + '[' + segth * '=' + (seg - segth) * '_' + ']' + \
		" {}% ({}/{})".format(percent, human_size(finish, 1), human_size(total, 1)) + \
		' ' + eta + suffix
	#msg = '\r' + prefix + '[' + segth * '=' + (seg - segth) * '_' + ']' + \
	#	" {}% ({}/{})".format(percent, human_size(finish), human_size(total)) + \
	#	' ' + eta + suffix
	sys.stderr.write(msg + ' ') # space is used as a clearer
	sys.stderr.flush()

