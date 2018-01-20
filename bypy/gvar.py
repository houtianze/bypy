#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import locale
import time
from . import const

## global variables
try:
	SystemLanguageCode, SystemEncoding = locale.getdefaultlocale()
except ValueError as e:
	# https://coderwall.com/p/-k_93g/mac-os-x-valueerror-unknown-locale-utf-8-in-python
	# Mac OS X: ValueError: unknown locale: UTF-8 in Python
	# Proper fix:
	# export LC_ALL=en_US.UTF-8
	# export LANG=en_US.UTF-8
	if e.args and e.args[0] and e.args[0] == "unknown locale: UTF-8":
		SystemLanguageCode, SystemEncoding = '', 'UTF-8'
	else:
		raise
# the previous time stdout was flushed, maybe we just flush every time, or maybe this way performs better
# http://stackoverflow.com/questions/230751/how-to-flush-output-of-python-print
last_stdout_flush = time.time()
#last_stdout_flush = 0
# save cache if more than 10 minutes passed
last_cache_save = time.time()

# mutable, the actual ones used, capital ones are supposed to be immutable
# this is introduced to support mirrors
pcsurl  = const.PcsUrl
cpcsurl = const.CPcsUrl
dpcsurl = const.DPcsUrl

