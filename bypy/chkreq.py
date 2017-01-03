#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys

from . import gvar
from .util import (iswindows, fixenc, bannerwarn)

class CheckResult:
	NumOfCheckResults= 3
	Pass, Warning, Error = range(NumOfCheckResults)

def check_requirements():
	result = CheckResult.Pass
	if iswindows():
		bannerwarn("You are running Python on Windows, which doesn't support Unicode so well.\n"
			"Files with non-ASCII names may not be handled correctly.")
		result = max(result, CheckResult.Warning)
	
	if sys.version_info[0] < 2 \
	or (sys.version_info[0] == 2 and sys.version_info[1] < 7) \
	or (sys.version_info[0] == 3 and sys.version_info[1] < 3):
		bannerwarn("Error: Incorrect Python version. You need 2.7 / 3.3 or above")
		result = max(result, CheckResult.Error)

	# we have warned Windows users, so the following is for *nix users only
	if gvar.SystemEncoding:
		sysencu = gvar.SystemEncoding.upper()
		if sysencu != 'UTF-8' and sysencu != 'UTF8':
			msg = "WARNING: System locale is not 'UTF-8'.\n" \
				  "Files with non-ASCII names may not be handled correctly.\n" \
				  "You should set your System Locale to 'UTF-8'.\n" \
				  "Current locale is '{}'".format(gvar.SystemEncoding)
			bannerwarn(msg)
			result = max(result, CheckResult.Warning)
	else:
		# ASSUME UTF-8 encoding, if for whatever reason,
		# we can't get the default system encoding
		gvar.SystemEncoding = 'utf-8'
		bannerwarn("WARNING: Can't detect the system encoding, assume it's 'UTF-8'.\n"
			  "Files with non-ASCII names may not be handled correctly." )
		result = max(result, CheckResult.Warning)
	
	stdenc = sys.stdout.encoding
	if stdenc:
		stdencu = stdenc.upper()
		if not (stdencu == 'UTF8' or stdencu == 'UTF-8'):
			bannerwarn("Encoding for StdOut: {}".format(stdenc))
			try:
				'\u6c49\u5b57'.encode(stdenc) # '汉字'
			except: # (LookupError, TypeError, UnicodeEncodeError):
				fixenc(stdenc)
	else:
		fixenc(stdenc)
	
	return result

if __name__ == "__main__":
	check_requirements()

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
