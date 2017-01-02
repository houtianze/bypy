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
SystemLanguageCode, SystemEncoding = locale.getdefaultlocale()
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

