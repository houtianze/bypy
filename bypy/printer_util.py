#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# this file exists to avoid circular dependencies
# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import os
import math
import re

from . import const

def iswindows():
	return os.name == 'nt'

def human_time(seconds):
	''' DocTests:
	>>> human_time(0) == ''
	True
	>>> human_time(122.1) == '2m2s'
	True
	>>> human_time(133) == '2m13s'
	True
	>>> human_time(12345678) == '20W2D21h21m18s'
	True
	'''
	isec = int(seconds)
	s = isec % 60
	m = isec // 60 % 60
	h = isec // 60 // 60 % 24
	d = isec // 60 // 60 // 24 % 7
	w = isec // 60 // 60 // 24 // 7

	result = ''
	for t in [ ('W', w), ('D', d), ('h', h), ('m', m), ('s', s) ]:
		if t[1]:
			result += str(t[1]) + t[0]

	return result

def limit_unit(timestr, num = 2):
	''' DocTests:
	>>> limit_unit('1m2s', 1) == '1m'
	True
	>>> limit_unit('1m2s') == '1m2s'
	True
	>>> limit_unit('1m2s', 4) == '1m2s'
	True
	>>> limit_unit('1d2h3m2s') == '1d2h'
	True
	>>> limit_unit('1d2h3m2s', 1) == '1d'
	True
	'''
	l = len(timestr)
	i = 0
	p = 0
	while i < num and p <= l:
		at = 0
		while p < l:
			c = timestr[p]
			if at == 0:
				if c.isdigit():
					p += 1
				else:
					at += 1
			elif at == 1:
				if not c.isdigit():
					p += 1
				else:
					at += 1
			else:
				break

		i += 1

	return timestr[:p]

def human_time_short(seconds):
	return limit_unit(human_time(seconds))

def interpret_size(si):
	'''
	>>> interpret_size(10)
	10
	>>> interpret_size('10')
	10
	>>> interpret_size('10b')
	10
	>>> interpret_size('10k')
	10240
	>>> interpret_size('10K')
	10240
	>>> interpret_size('10kb')
	10240
	>>> interpret_size('10kB')
	10240
	>>> interpret_size('a10')
	Traceback (most recent call last):
	ValueError
	>>> interpret_size('10a')
	Traceback (most recent call last):
	KeyError: 'A'
	'''
	m = re.match(r"\s*(\d+)\s*([ac-z]?)(b?)\s*$", str(si), re.I)
	if m:
		if not m.group(2) and m.group(3):
			times = 1
		else:
			times = const.SIPrefixTimes[m.group(2).upper()] if m.group(2) else 1
		return int(m.group(1)) * times
	else:
		raise ValueError

def human_num(num, precision = 0, filler = ''):
	# https://stackoverflow.com/questions/15263597/python-convert-floating-point-number-to-certain-precision-then-copy-to-string/15263885#15263885
	numfmt = '{{:.{}f}}'.format(precision)
	exp = math.log(num, const.OneK) if num > 0 else 0
	expint = int(math.floor(exp))
	maxsize = len(const.SIPrefixNames) - 1
	if expint > maxsize:
		print("Ridiculously large number '{}' passed to 'human_num()'".format(num))
		expint = maxsize
	unit = const.SIPrefixNames[expint]
	return numfmt.format(num / float(const.OneK ** expint)) + filler + unit

def human_size(num, precision = 3):
	''' DocTests:
	>>> human_size(1000, 0) == '1000B'
	True
	>>> human_size(1025) == '1.001kB'
	True
	'''
	return human_num(num, precision) + 'B'

def human_speed(speed, precision = 0):
	return human_num(speed, precision) + 'B/s'

