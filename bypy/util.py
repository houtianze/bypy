#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

### imports
import os
import sys
import time
import io
import json
import pprint
import codecs
import threading
import traceback
import shutil
# unify Python 2 and 3
if sys.version_info[0] == 2:
	from Queue import Queue
elif sys.version_info[0] == 3:
	unicode = str
	basestring = str
	long = int
	raw_input = input
	from queue import Queue

from . import const
from . import printer_console
from .printer_util import (iswindows, human_size, interpret_size)
from .printer import (
	bannerwarn, plog, pdbg, pinfo, pwarn, perr)

pr = printer_console.pr
prcolor = printer_console.prcolor
ask = printer_console.ask
pprgr = printer_console.pprgr

human_size
interpret_size
plog
pdbg
pinfo
pwarn

def remove_backslash(s):
	return s.replace(r'\/', r'/')

rb = remove_backslash

# no idea who screws the sys.stdout.encoding
# the locale is 'UTF-8', sys.stdin.encoding is 'UTF-8',
# BUT, sys.stdout.encoding is None ...
def fixenc(stdenc):
	if iswindows():
		bannerwarn("WARNING: StdOut encoding '{}' is unable to encode CJK strings.\n" \
			"Files with non-ASCII names may not be handled correctly.".format(stdenc))
	else:
		# fix by @xslidian
		if not stdenc:
			stdenc = 'utf-8'
		sys.stdout = codecs.getwriter(stdenc)(sys.stdout)
		sys.stderr = codecs.getwriter(stdenc)(sys.stderr)

# http://stackoverflow.com/questions/9403986/python-3-traceback-fails-when-no-exception-is-active
def formatex(ex):
	s = ''
	if ex and isinstance(ex, Exception):
		s = "Exception:\n{} - {}\nStack:\n{}".format(
			type(ex), ex, ''.join(traceback.format_stack()))

	return s

# marshaling
def str2bool(s):
	if isinstance(s, basestring):
		if s:
			sc = s.lower()[0]
			if sc == 't' or sc == 'y' or (sc >= '1' and sc <= '9'):
				return True
			else:
				return False
		else:
			return False
	else:
		# don't change
		return s

def str2int(s):
	if isinstance(s, basestring):
		return int(s)
	else:
		# don't change
		return s

def str2float(s):
	if isinstance(s, basestring):
		return float(s)
	else:
		# don't change
		return s

# guarantee no-exception
def copyfile(src, dst):
	result = const.ENoError
	try:
		shutil.copyfile(src, dst)
	except (shutil.Error, IOError) as ex:
		perr("Fail to copy '{}' to '{}'.\n{}".format(
			src, dst, formatex(ex)))
		result = const.EFailToCreateLocalFile

	return result

def movefile(src, dst):
	result = const.ENoError
	try:
		shutil.move(src, dst)
	except (shutil.Error, OSError) as ex:
		perr("Fail to move '{}' to '{}'.\n{}".format(
			src, dst, formatex(ex)))
		result = const.EFailToCreateLocalFile

	return result

def removefile(path, verbose = False):
	result = const.ENoError
	try:
		if verbose:
			pr("Removing local file '{}'".format(path))
		if path:
			os.remove(path)
	except Exception as ex:
		perr("Fail to remove local fle '{}'.\n{}".format(
			path, formatex(ex)))
		result = const.EFailToDeleteFile

	return result

def removedir(path, verbose = False):
	result = const.ENoError
	try:
		if verbose:
			pr("Removing local directory '{}'".format(path))
		if path:
			shutil.rmtree(path)
	except Exception as ex:
		perr("Fail to remove local directory '{}'.\n{}".format(
			path, formatex(ex)))
		result = const.EFailToDeleteDir

	return result

def removepath(path):
	if os.path.isdir(path):
		return removedir(path)
	elif os.path.isfile(path):
		return removefile(path)
	else:
		perr("Can't remove '{}', it's non-file and none-dir.".format(path))
		return const.EArgument

def makedir(path, mode = 0o777, verbose = False):
	result = const.ENoError

	if verbose:
		pr("Creating local directory '{}'".format(path))

	if path and not os.path.exists(path):
		try:
			os.makedirs(path, mode)
		except os.error as ex:
			perr("Failed at creating local dir '{}'.\n{}".format(
				path, formatex(ex)))
			result = const.EFailToCreateLocalDir

	return result

# guarantee no-exception
def getfilesize(path):
	size = -1
	try:
		size = os.path.getsize(path)
	except os.error as ex:
		perr("Exception occured while getting size of '{}'.\n{}".format(
			path, formatex(ex)))

	return size

# guarantee no-exception
def getfilemtime(path):
	mtime = -1
	try:
		mtime = os.path.getmtime(path)
	except os.error as ex:
		perr("Exception occured while getting modification time of '{}'.\n{}".format(
			path, formatex(ex)))

	return mtime

def getfilemtime_int(path):
	# just int it, this is reliable no matter how stat_float_times() is changed
	return int(getfilemtime(path))

	# mtime = getfilemtime(path)
	# if (mtime == -1):
	# 	return mtime
    #
	# if os.stat_float_times():
	# 	mtime = int(mtime)
    #
	# return mtime

# seems os.path.join() doesn't handle Unicode well
def joinpath(first, second, sep = os.sep):
	head = ''
	if first:
		head = first.rstrip(sep) + sep

	tail = ''
	if second:
		tail = second.lstrip(sep)

	return head + tail

# CAN Python make Unicode right?
# http://houtianze.github.io/python/unicode/json/2016/01/03/another-python-unicode-fisaco-on-json.html
def py2_jsondump(data, filename):
	with io.open(filename, 'w', encoding = 'utf-8') as f:
		f.write(unicode(json.dumps(data, ensure_ascii = False, sort_keys = True, indent = 2)))

def py3_jsondump(data, filename):
	with io.open(filename, 'w', encoding = 'utf-8') as f:
		return json.dump(data, f, ensure_ascii = False, sort_keys = True, indent = 2)

def jsonload(filename):
	with io.open(filename, 'r', encoding = 'utf-8') as f:
		return json.load(f)

if sys.version_info[0] == 2:
	jsondump = py2_jsondump
elif sys.version_info[0] == 3:
	jsondump = py3_jsondump

def ls_type(isdir):
	return 'D' if isdir else 'F'

def ls_time(itime):
	return time.strftime('%Y-%m-%d, %H:%M:%S', time.localtime(itime))

# no leading, trailing '/'
# remote path rule:
#  - all public methods of ByPy shall accept remote path as "partial path"
#    (before calling get_pcs_path())
#  - all private methods of ByPy shall accept remote path as "full path"
#    (after calling get_pcs_path())
def get_pcs_path(path):
	if not path or path == '/' or path == '\\':
		return const.AppPcsPath

	return (const.AppPcsPath + '/' + path.strip('/')).rstrip('/')

def is_pcs_root_path(path):
	return path == const.AppPcsPath or path == const.AppPcsPath + '/'

def print_pcs_list(json, foundmsg = "Found:", notfoundmsg = "Nothing found."):
	list = json['list']
	if list:
		pr(foundmsg)
		for f in list:
			pr("{} {} {} {} {} {}".format(
				ls_type(f['isdir']),
				f['path'],
				f['size'],
				ls_time(f['ctime']),
				ls_time(f['mtime']),
				f['md5']))
	else:
		pr(notfoundmsg)

# https://stackoverflow.com/questions/10883399/unable-to-encode-decode-pprint-output
class MyPrettyPrinter(pprint.PrettyPrinter):
	def format(self, obj, context, maxlevels, level):
		if isinstance(obj, unicode):
			#return (obj.encode('utf8'), True, False)
			return (obj, True, False)
		if isinstance(obj, bytes):
			convert = False
			#for c in obj:
			#	if ord(c) >= 128:
			#		convert = True
			#		break
			try:
				codecs.decode(obj)
			except:
				convert = True
			if convert:
				return ("0x{}".format(obj), True, False)
		return pprint.PrettyPrinter.format(self, obj, context, maxlevels, level)

class NewThread(threading.Thread):
	def __init__(self, func):
		threading.Thread.__init__(self)
		self.func = func

	def run(self):
		self.func()

def startthread(func):
	NewThread(func).start()

def inc_list_size(li, size = 3, filler = 0):
	i = len(li)
	while (i < size):
		li.append(filler)
		i += 1

def comp_semver(v1, v2):
	v1a = v1.split('.')
	v2a = v2.split('.')
	v1ia = [int(i) for i in v1a]
	v2ia = [int(i) for i in v2a]
	inc_list_size(v1ia, 3)
	inc_list_size(v2ia, 3)
	i = 0
	while (i < 3):
		if v1ia[i] != v2ia[i]:
			return v1ia[i] - v2ia[i]
		i += 1
	return 0

# NOT in use, see deque
class FixedSizeQueue(object):
	def __init__(self, size = 1024):
		self.size = size
		self.q = Queue()

	def put(self, item):
		if self.q.qsize() >= self.size:
			self.q.get()
		self.q.put(item)

	def get(self):
		return self.q.get()

def nop(*args):
	pass

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
