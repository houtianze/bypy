#!/usr/bin/env python
# encoding: utf-8
# ===  IMPORTANT  ====
# NOTE: In order to support non-ASCII file names,
#       your system's locale MUST be set to 'utf-8'
# CAVEAT: DOESN'T work with proxy, the underlying reason being
#         the 'requests' package used for http communication doesn't seem
#         to work properly with proxies, reason unclear.
# NOTE: It seems Baidu doesn't handle MD5 quite right after combining files,
#       so it may return erroneous MD5s. Perform a rapidupload again may fix the problem.
#        That's why I changed default behavior to no-verification.
# NOTE: syncup / upload, syncdown / downdir are partially duplicates
#       the difference: syncup/down compare and perform actions
#       while down/up just proceed to download / upload (but still compare during actions)
#       so roughly the same, except that sync can delete extra files
#
# TODO: Dry run?
# TODO: Use batch functions for better performance

'''
bypy -- Python client for Baidu Yun
---

https://github.com/houtianze/bypy
---

bypy is a Baidu Yun client written in Python (2.7).
(NOTE: You need to install the 'requests' library by running 'pip install requests')

It offers some file operations like: list, download, upload, syncup, syncdown, etc.
The main purpose is to utilize Baidu Yun in Linux environment (e.g. Raspberry Pi)

It uses a server for OAuth authorization, to conceal the Application's Secret Key.
Alternatively, you can create your own App at Baidu and replace the 'ApiKey' and 'SecretKey' with your copies,
and then, change 'ServerAuth' to 'False'
---
@author:     Hou Tianze

@license:    MIT

@contact:    GitHub: houtianze, Twitter: @ibic, G+: +TianzeHou
'''

# it takes days just to fix you, unicode ...
# some references
# https://stackoverflow.com/questions/4374455/how-to-set-sys-stdout-encoding-in-python-3
# https://stackoverflow.com/questions/492483/setting-the-correct-encoding-when-piping-stdout-in-python
# http://drj11.wordpress.com/2007/05/14/python-how-is-sysstdoutencoding-chosen/
# https://stackoverflow.com/questions/11741574/how-to-set-the-default-encoding-to-utf-8-in-python
# https://stackoverflow.com/questions/2276200/changing-default-encoding-of-python
from __future__ import unicode_literals

EIncorrectPythonVersion = 1
import sys
vi = sys.version_info
if not hasattr(sys.version_info, 'major') or vi.major != 2 or vi.minor < 7:
	print("Error: Incorrect Python version. " + \
		"You need 2.7 or above (but not 3)")
	sys.exit(EIncorrectPythonVersion)

#reload(sys)
#sys.setdefaultencoding(SystemEncoding)

import os

import locale
SystemLanguageCode, SystemEncoding = locale.getdefaultlocale()
if SystemEncoding and not sys.platform.startswith('win32'):
	sysenc = SystemEncoding.upper()
	if sysenc != 'UTF-8' and sysenc != 'UTF8':
		err = "You MUST set system locale to 'UTF-8' to support unicode file names.\n" + \
			"Current locale is '{}'".format(SystemEncoding)
		ex = Exception(err)
		print(err)
		raise ex

if not SystemEncoding:
	# ASSUME UTF-8 encoding, if for whatever reason,
	# we can't get the default system encoding
	print("*WARNING*: Cannot detect the system encoding, assume it's 'UTF-8'")
	SystemEncoding = 'utf-8'

import codecs
# no idea who is the asshole that screws the sys.stdout.encoding
# the locale is 'UTF-8', sys.stdin.encoding is 'UTF-8',
# BUT, sys.stdout.encoding is None ...
if not (sys.stdout.encoding and sys.stdout.encoding.lower() == 'utf-8'):
	encoding_to_use = sys.stdout.encoding
	try:
		codecs.lookup(encoding_to_use)
		u'汉字'.encode(encoding_to_use)
	except: # (LookupError, TypeError, UnicodeEncodeError):
		encoding_to_use = 'utf-8'
		sys.exc_clear()
	sys.stdout = codecs.getwriter(encoding_to_use)(sys.stdout)
	sys.stderr = codecs.getwriter(encoding_to_use)(sys.stderr)
import signal
import time
import shutil
import posixpath
#import types
import traceback
import inspect
import logging
import httplib
import urllib
import json
import hashlib
import binascii
import re
import cPickle as pickle
import pprint
import socket
import math
#from collections import OrderedDict
from os.path import expanduser
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

# Defines that should never be changed
OneK = 1024
OneM = OneK * OneK
OneG = OneM * OneK
OneT = OneG * OneK
OneP = OneT * OneK
OneE = OneP * OneK
OneZ = OneE * OneK
OneY = OneZ * OneK
SIPrefixNames = [ '', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y' ]

SIPrefixTimes = {
	'K' : OneK,
	'M' : OneM,
	'G' : OneG,
	'T' : OneT,
	'E' : OneE,
	'Z' : OneZ,
	'Y' : OneY }


# special variables
__all__ = []
__version__ = '1.0.20'

# ByPy default values
DefaultSliceInMB = 20
DefaultSliceSize = 20 * OneM
DefaultDlChunkSize = 20 * OneM
RetryDelayInSec = 10

# Baidu PCS constants
MinRapidUploadFileSize = 256 * OneK
MaxSliceSize = 2 * OneG
MaxSlicePieces = 1024

# return (error) codes
ENoError = 0 # plain old OK, fine, no error.
#EIncorrectPythonVersion = 1
EApiNotConfigured = 10 # ApiKey, SecretKey and AppPcsPath not properly configured
EArgument = 10 # invalid program command argument
EAbort = 20 # aborted
EException = 30 # unhandled exception occured
EParameter = 40 # invalid parameter passed to ByPy
EInvalidJson = 50
EHashMismatch = 60 # MD5 hashes of the local file and remote file don't match each other
EFileWrite = 70
EFileTooBig = 80 # file too big to upload
EFailToCreateLocalDir = 90
EFailToCreateLocalFile = 100
EFailToDeleteDir = 110
EFailToDeleteFile = 120
EFileNotFound = 130
EMaxRetry = 140
ERequestFailed = 150 # request failed
ECacheNotLoaded = 160
EMigrationFailed = 170
EDownloadCerts = 180
EFatal = -1 # No way to continue

# internal errors
IEMD5NotFound = 31079 # File md5 not found, you should use upload API to upload the whole file.
IEBDUSSExpired = -6

# PCS configuration constants
# ==== NOTE ====
# I use server auth, because it's the only possible method to protect the SecretKey.
# If you don't like that and want to perform local authorization using 'Device' method, you need to:
# - Change to: ServerAuth = False
# - Paste your own ApiKey and SecretKey.
# - Change the AppPcsPath to your own App's directory at Baidu PCS
# Then you are good to go
ServerAuth = True # change it to 'False' if you use your own appid
GaeUrl = 'https://bypyoauth.appspot.com'
OpenShiftUrl = 'https://bypy-tianze.rhcloud.com'
HerokuUrl = 'https://bypyoauth.herokuapp.com'
GaeRedirectUrl = GaeUrl + '/auth'
GaeRefreshUrl = GaeUrl + '/refresh'
OpenShiftRedirectUrl = OpenShiftUrl + '/auth'
OpenShiftRefreshUrl = OpenShiftUrl + '/refresh'
HerokuRedirectUrl = HerokuUrl + '/auth'
HerokuRefreshUrl = HerokuUrl + '/refresh'

AuthServerList = [
	# url, rety?, message
	(GaeRedirectUrl, False, "Authorizing with the GAE server ..."),
	(OpenShiftRedirectUrl, True, "I think you are WALLed, so let's authorize with the OpenShift server ..."),
	(HerokuRedirectUrl, True, "OpenShift also failed. Last resort: authorizing with the Heroku server ..."),
]

RefreshServerList = [
	# url, rety?, message
	(GaeRefreshUrl, False, "Refreshing with the GAE server ..."),
	(OpenShiftRefreshUrl, True, "I think you are WALLed, so let's refresh with the OpenShift server ..."),
	(HerokuRefreshUrl, True, "OpenShift also failed. Last resort: refreshing with the Heroku server ..."),
]

ApiKey = 'q8WE4EpCsau1oS0MplgMKNBn' # replace with your own ApiKey if you use your own appid
SecretKey = '' # replace with your own SecretKey if you use your own appid
if not SecretKey:
	ServerAuth = True
# NOTE: no trailing '/'
AppPcsPath = '/apps/bypy' # change this to the App's direcotry you specified when creating the app
AppPcsPathLen = len(AppPcsPath)

# Program setting constants
HomeDir = expanduser('~')
# os.path.join() may not handle unicode well
ConfigDir = HomeDir + os.sep + '.bypy'
TokenFilePath = ConfigDir + os.sep + 'bypy.json'
HashCachePath = ConfigDir + os.sep + 'bypy.pickle'
BDUSSPath = ConfigDir + os.sep + 'bypy.bduss'
ByPyCertsFile = 'bypy.cacerts.pem'
ByPyCertsPath = ConfigDir + os.sep + ByPyCertsFile
#UserAgent = 'Mozilla/5.0'
#UserAgent = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)"
# According to seanlis@github, this User-Agent string affects the download.
UserAgent = None
CleanOptionShort= '-c'
CleanOptionLong= '--clean'
DisableSslCheckOption = '--disable-ssl-check'
CaCertsOption = '--cacerts'

# Baidu PCS URLs etc.
OpenApiUrl = "https://openapi.baidu.com"
OpenApiVersion = "2.0"
OAuthUrl = OpenApiUrl + "/oauth/" + OpenApiVersion
ServerAuthUrl = OAuthUrl + "/authorize"
DeviceAuthUrl = OAuthUrl + "/device/code"
TokenUrl = OAuthUrl + "/token"
PcsUrl = 'https://pcs.baidu.com/rest/2.0/pcs/'
CPcsUrl = 'https://c.pcs.baidu.com/rest/2.0/pcs/'
DPcsUrl = 'https://d.pcs.baidu.com/rest/2.0/pcs/'
PanAPIUrl = 'http://pan.baidu.com/api/'

# mutable, actual ones used, capital ones are supposed to be immutable
# this is introduced to support mirrors
pcsurl  = PcsUrl
cpcsurl = CPcsUrl
dpcsurl = DPcsUrl

try:
	# non-standard python library, needs 'pip install requests'
	import requests
except:
	print("Fail to import the 'requests' library\n" + \
		"You need to install the 'requests' python library\n" + \
		"You can install it by running 'pip install requests'")
	raise

requests_version = requests.__version__.split('.')
if int(requests_version[0]) < 1:
	print("You Python Requests Library version is to lower than 1.\n" + \
		"You can run 'pip install requests' to upgrade it.")
	raise
# non-standard python library, needs 'pip install requesocks'
#import requesocks as requests # if you need socks proxy

# when was your last time flushing a toilet?
__last_flush = time.time()
#__last_flush = 0
PrintFlushPeriodInSec = 5.0
# save cache if more than 10 minutes passed
last_cache_save = time.time()
CacheSavePeriodInSec = 10 * 60.0

# https://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
# 0 - black, 1 - red, 2 - green, 3 - yellow
# 4 - blue, 5 - magenta, 6 - cyan 7 - white
class TermColor:
	NumOfColors = 8
	Black, Red, Green, Yellow, Blue, Magenta, Cyan, White = range(NumOfColors)
	Nil = -1

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

def prc(msg):
	print(msg)
	# we need to flush the output periodically to see the latest status
	global __last_flush
	now = time.time()
	if now - __last_flush >= PrintFlushPeriodInSec:
		sys.stdout.flush()
		__last_flush = now

pr = prc

def prcolorc(msg, fg, bg):
	if sys.stdout.isatty() and not sys.platform.startswith('win32'):
		pr(colorstr(msg, fg, bg))
	else:
		pr(msg)

prcolor = prcolorc

def plog(tag, msg, showtime = True, showdate = False,
		prefix = '', suffix = '', fg = TermColor.Nil, bg = TermColor.Nil):
	if showtime or showdate:
		now = time.localtime()
		if showtime:
			tag += time.strftime("[%H:%M:%S] ", now)
		if showdate:
			tag += time.strftime("[%Y-%m-%d] ", now)

	if prefix:
		prcolor("{}{}".format(tag, prefix), fg, bg)

	prcolor("{}{}".format(tag, msg), fg, bg)

	if suffix:
		prcolor("{}{}".format(tag, suffix), fg, bg)

def perr(msg, showtime = True, showdate = False, prefix = '', suffix = ''):
	return plog('<E> ', msg, showtime, showdate, prefix, suffix, TermColor.Red)

def pwarn(msg, showtime = True, showdate = False, prefix = '', suffix = ''):
	return plog('<W> ', msg, showtime, showdate, prefix, suffix, TermColor.Yellow)

def pinfo(msg, showtime = True, showdate = False, prefix = '', suffix = ''):
	return plog('<I> ', msg, showtime, showdate, prefix, suffix, TermColor.Green)

def pdbg(msg, showtime = True, showdate = False, prefix = '', suffix = ''):
	return plog('<D> ', msg, showtime, showdate, prefix, suffix, TermColor.Cyan)

def askc(msg, enter = True):
	pr(msg)
	if enter:
		pr('Press [Enter] when you are done')
	return raw_input()

ask = askc

# print progress
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def pprgrc(finish, total, start_time = None, existing = 0,
		prefix = '', suffix = '', seg = 20):
	# we don't want this goes to the log, so we use stderr
	if total > 0:
		segth = seg * finish // total
		percent = 100 * finish // total
	else:
		segth = seg
		percent = 100
	eta = ''
	now = time.time()
	if start_time is not None and percent > 5 and finish > 0:
		finishf = float(finish) - float(existing)
		totalf = float(total)
		remainf = totalf - float(finish)
		elapsed = now - start_time
		speed = human_speed(finishf / elapsed)
		eta = 'ETA: ' + human_time_short(elapsed * remainf / finishf) + \
				' (' + speed + ', ' + \
				human_time_short(elapsed) + ' gone)'
	msg = '\r' + prefix + '[' + segth * '=' + (seg - segth) * '_' + ']' + \
		" {}% ({}/{})".format(percent, human_size(finish), human_size(total)) + \
		' ' + eta + suffix
	sys.stderr.write(msg + ' ') # space is used as a clearer
	sys.stderr.flush()

pprgr = pprgrc

def remove_backslash(s):
	return s.replace(r'\/', r'/')

def rb(s):
	return s.replace(r'\/', r'/')

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

def human_time(seconds):
	''' DocTests:
	>>> human_time(0)
	u''
	>>> human_time(122.1)
	u'2m2s'
	>>> human_time(133)
	u'2m13s'
	>>> human_time(12345678)
	u'20W2D21h21m18s'
	'''
	isec = int(seconds)
	s = isec % 60
	m = isec / 60 % 60
	h = isec / 60 / 60 % 24
	d = isec / 60 / 60 / 24 % 7
	w = isec / 60 / 60 / 24 / 7

	result = ''
	for t in [ ('W', w), ('D', d), ('h', h), ('m', m), ('s', s) ]:
		if t[1]:
			result += str(t[1]) + t[0]

	return result

def limit_unit(timestr, num = 2):
	''' DocTests:
	>>> limit_unit('1m2s', 1)
	u'1m'
	>>> limit_unit('1m2s')
	u'1m2s'
	>>> limit_unit('1m2s', 4)
	u'1m2s'
	>>> limit_unit('1d2h3m2s')
	u'1d2h'
	>>> limit_unit('1d2h3m2s', 1)
	u'1d'
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
			times = SIPrefixTimes[m.group(2).upper()] if m.group(2) else 1
		return int(m.group(1)) * times
	else:
		raise ValueError

def human_num(num, precision = 0, filler = ''):
	# https://stackoverflow.com/questions/15263597/python-convert-floating-point-number-to-certain-precision-then-copy-to-string/15263885#15263885
	numfmt = '{{:.{}f}}'.format(precision)
	exp = math.log(num, OneK) if num > 0 else 0
	expint = int(math.floor(exp))
	maxsize = len(SIPrefixNames) - 1
	if expint > maxsize:
		pwarn("Ridiculously large number '{}' pased to 'human_num()'".format(num))
		expint = maxsize
	unit = SIPrefixNames[expint]
	return numfmt.format(num / float(OneK ** expint)) + filler + unit

def human_size(num, precision = 3):
	''' DocTests:
	>>> human_size(1000, 0)
	u'1000B'
	>>> human_size(1025)
	u'1.001kB'
	'''
	return human_num(num, precision) + 'B'

def human_speed(speed, precision = 0):
	return human_num(speed, precision) + 'B/s'

# no leading, trailing '/'
# remote path rule:
#  - all public methods of ByPy shall accept remote path as "partial path"
#    (before calling get_pcs_path())
#  - all private methods of ByPy shall accept remote path as "full path"
#    (after calling get_pcs_path())
def get_pcs_path(path):
	if not path or path == '/' or path == '\\':
		return AppPcsPath

	return (AppPcsPath + '/' + path.strip('/')).rstrip('/')

# guarantee no-exception
def copyfile(src, dst):
	result = ENoError
	try:
		shutil.copyfile(src, dst)
	except (shutil.Error, IOError) as ex:
		perr("Fail to copy '{}' to '{}'.\nException:\n{}\nStack:{}\n".format(
			src, dst, ex, traceback.format_exc()))
		result = EFailToCreateLocalFile

	return result

def movefile(src, dst):
	result = ENoError
	try:
		shutil.move(src, dst)
	except (shutil.Error, OSError) as ex:
		perr("Fail to move '{}' to '{}'.\nException:\n{}\nStack:\n{}\n".format(
			src, dst, ex, traceback.format_exc()))
		result = EFailToCreateLocalFile

	return result

def removefile(path, verbose = False):
	result = ENoError
	try:
		if verbose:
			pr("Removing local file '{}'".format(path))
		if path:
			os.remove(path)
	except Exception as ex:
		perr("Fail to remove local fle '{}'.\nException:\n{}\nStack:{}\n".format(
			path, ex, traceback.format_exc()))
		result = EFailToDeleteFile

	return result

def removedir(path, verbose = False):
	result = ENoError
	try:
		if verbose:
			pr("Removing local directory '{}'".format(path))
		if path:
			shutil.rmtree(path)
	except Exception as ex:
		perr("Fail to remove local directory '{}'.\nException:\n{}\nStack:{}\n".format(
			path, ex, traceback.format_exc()))
		result = EFailToDeleteDir

	return result

def makedir(path, mode = 0o777, verbose = False):
	result = ENoError

	if verbose:
		pr("Creating local directory '{}'".format(path))

	if path and not os.path.exists(path):
		try:
			os.makedirs(path, mode)
		except os.error as ex:
			perr("Failed at creating local dir '{}'.\nException:\n{}\nStack:{}\n".format(
				path, ex, traceback.format_exc()))
			result = EFailToCreateLocalDir

	return result

# guarantee no-exception
def getfilesize(path):
	size = -1
	try:
		size = os.path.getsize(path)
	except os.error:
		perr("Exception occured while getting size of '{}'. Exception:\n{}".format(path, traceback.format_exc()))

	return size

# guarantee no-exception
def getfilemtime(path):
	mtime = -1
	try:
		mtime = os.path.getmtime(path)
	except os.error:
		perr("Exception occured while getting modification time of '{}'. Exception:\n{}".format(path, traceback.format_exc()))

	return mtime

# seems os.path.join() doesn't handle Unicode well
def joinpath(first, second, sep = os.sep):
	head = ''
	if first:
		head = first.rstrip(sep) + sep

	tail = ''
	if second:
		tail = second.lstrip(sep)

	return head + tail

def donothing():
	pass

# https://urllib3.readthedocs.org/en/latest/security.html#insecurerequestwarning
def disable_urllib3_warning():
	try:
		import requests.packages.urllib3
		requests.packages.urllib3.disable_warnings()
	except:
		pass

# https://stackoverflow.com/questions/10883399/unable-to-encode-decode-pprint-output
class MyPrettyPrinter(pprint.PrettyPrinter):
	def format(self, obj, context, maxlevels, level):
		if isinstance(obj, unicode):
			#return (obj.encode('utf8'), True, False)
			return (obj, True, False)
		if isinstance(obj, str):
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
				return ("0x{}".format(binascii.hexlify(obj)), True, False)
		return pprint.PrettyPrinter.format(self, obj, context, maxlevels, level)

# there is room for more space optimization (like using the tree structure),
# but it's not added at the moment. for now, it's just simple pickle.
# SQLite might be better for portability
# NOTE: file names are case-sensitive
class cached(object):
	''' simple decorator for hash caching (using pickle) '''
	usecache = True
	verbose = False
	debug = False
	cache = {}
	cacheloaded = False
	dirty = False
	# we don't do cache loading / unloading here because it's an decorator,
	# and probably multiple instances are created for md5, crc32, etc
	# it's a bit complex, and i thus don't have the confidence to do it in ctor/dtor
	def __init__(self, f):
		self.f = f

	def __call__(self, *args):
		assert len(args) > 0
		result = None
		path = args[0]
		dir, file = os.path.split(path) # the 'filename' parameter
		absdir = os.path.abspath(dir)
		if absdir in cached.cache:
			entry = cached.cache[absdir]
			if file in entry:
				info = entry[file]
				if self.f.__name__ in info \
					and info['size'] == getfilesize(path) \
					and info['mtime'] == getfilemtime(path) \
					and self.f.__name__ in info \
					and cached.usecache:
					result = info[self.f.__name__]
					if cached.debug:
						pdbg("Cache hit for file '{}',\n{}: {}\nsize: {}\nmtime: {}".format(
							path, self.f.__name__,
							result if isinstance(result, (int, long, float, complex)) else binascii.hexlify(result),
							info['size'], info['mtime']))
				else:
					result = self.f(*args)
					self.__store(info, path, result)
			else:
				result = self.f(*args)
				entry[file] = {}
				info = entry[file]
				self.__store(info, path, result)
		else:
			result = self.f(*args)
			cached.cache[absdir] = {}
			entry = cached.cache[absdir]
			entry[file] = {}
			info = entry[file]
			self.__store(info, path, result)

		return result

	def __store(self, info, path, value):
		cached.dirty = True
		info['size'] = getfilesize(path)
		info['mtime'] = getfilemtime(path)
		info[self.f.__name__] = value
		if cached.debug:
			situation = "Storing cache"
			if cached.usecache:
				situation = "Cache miss"
			pdbg((situation + " for file '{}',\n{}: {}\nsize: {}\nmtime: {}").format(
				path, self.f.__name__,
				value if isinstance(value, (int, long, float, complex)) else binascii.hexlify(value),
				info['size'], info['mtime']))

		# periodically save to prevent loss in case of system crash
		global last_cache_save
		now = time.time()
		if now - last_cache_save >= CacheSavePeriodInSec:
			cached.savecache()
			last_cache_save = now
		if cached.debug:
			pdbg("Periodically saving Hash Cash")

	@staticmethod
	def loadcache():
		# load cache even we don't use cached hash values,
		# because we will save (possibly updated) and hash values
		if not cached.cacheloaded: # no double-loading
			if cached.verbose:
				pr("Loading Hash Cache File '{}'...".format(HashCachePath))

			if os.path.exists(HashCachePath):
				try:
					with open(HashCachePath, 'rb') as f:
						cached.cache = pickle.load(f)
					cached.cacheloaded = True
					if cached.verbose:
						pr("Hash Cache File loaded.")
				except (
					pickle.PickleError,
					# the following is for dealing with corrupted cache file
					EOFError, TypeError, ValueError):
					perr("Fail to load the Hash Cache, no caching. Exception:\n{}".format(traceback.format_exc()))
					cached.cache = {}
			else:
				if cached.verbose:
					pr("Hash Cache File not found, no caching")
		else:
			if cached.verbose:
				pr("Not loading Hash Cache since 'cacheloaded' is '{}'".format( cached.cacheloaded))

		return cached.cacheloaded

	@staticmethod
	def savecache(force_saving = False):
		saved = False
		# even if we were unable to load the cache, we still save it.
		if cached.dirty or force_saving:
			if cached.verbose:
				pr("Saving Hash Cache...")

			try:
				with open(HashCachePath, 'wb') as f:
					pickle.dump(cached.cache, f)
					f.close()
				if cached.verbose:
					pr("Hash Cache saved.")
				saved = True
				cached.dirty = False
			except Exception:
				perr("Failed to save Hash Cache. Exception:\n{}".format(traceback.format_exc()))

		else:
			if cached.verbose:
				pr("Not saving Hash Cache since 'dirty' is '{}' and 'force_saving' is '{}'".format(
					cached.dirty, force_saving))

		return saved

	@staticmethod
	def cleancache():
		if cached.loadcache():
			for absdir in cached.cache.keys():
				if not os.path.exists(absdir):
					if cached.verbose:
						pr("Directory: '{}' no longer exists, removing the cache entries".format(absdir))
					cached.dirty = True
					del cached.cache[absdir]
				else:
					oldfiles = cached.cache[absdir]
					files = {}
					needclean = False
					for f in oldfiles.keys():
						#p = os.path.join(absdir, f)
						p = joinpath(absdir, f)
						if os.path.exists(p):
							files[f] = oldfiles[f]
						else:
							if cached.verbose:
								needclean = True
								pr("File '{}' no longer exists, removing the cache entry".format(p))

					if needclean:
						cached.dirty = True
						cached.cache[absdir] = files
		cached.savecache()

@cached
def md5(filename, slice = OneM):
	m = hashlib.md5()
	with open(filename, "rb") as f:
		while True:
			buf = f.read(slice)
			if buf:
				m.update(buf)
			else:
				break

	return m.digest()

# slice md5 for baidu rapidupload
@cached
def slice_md5(filename):
	m = hashlib.md5()
	with open(filename, "rb") as f:
		buf = f.read(256 * OneK)
		m.update(buf)

	return m.digest()

@cached
def crc32(filename, slice = OneM):
	with open(filename, "rb") as f:
		buf = f.read(slice)
		crc = binascii.crc32(buf)
		while True:
			buf = f.read(slice)
			if buf:
				crc = binascii.crc32(buf, crc)
			else:
				break

	return crc & 0xffffffff

def enable_http_logging():
	httplib.HTTPConnection.debuglevel = 1

	logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

def ls_type(isdir):
	return 'D' if isdir else 'F'

def ls_time(itime):
	return time.strftime('%Y-%m-%d, %H:%M:%S', time.localtime(itime))

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

# tree represented using dictionary, (Obsolete: OrderedDict no longer required)
# NOTE: No own-name is kept, so the caller needs to keep track of that
# NOTE: Case-sensitive, as I don't want to waste time wrapping up a case-insensitive one
# single-linked-list, no backwards travelling capability
class PathDictTree(dict):
	def __init__(self, type = 'D', **kwargs):
		self.type = type
		self.extra = {}
		for k, v in kwargs.items():
			self.extra[k] = v
		super(PathDictTree, self).__init__()

	def __str__(self):
		return self.__str('')

	def __str(self, prefix):
		result = ''
		for k, v in self.iteritems():
			result += "{} - {}/{} - size: {} - md5: {} \n".format(
				v.type, prefix, k,
				v.extra['size'] if 'size' in v.extra else '',
				binascii.hexlify(v.extra['md5']) if 'md5' in v.extra else '')

		for k, v in self.iteritems():
			if v.type == 'D':
				result += v.__str(prefix + '/' + k)

		return result

	def add(self, name, child):
		self[name] = child
		return child

	# returns the child tree at the given path
	# assume that path is only separated by '/', instead of '\\'
	def get(self, path):
		place = self
		if path:
			# Linux can have file / folder names with '\\'?
			if sys.platform.startswith('win32'):
				assert '\\' not in path
			route = filter(None, path.split('/'))
			for part in route:
				if part in place:
					sub = place[part]
					assert place.type == 'D' # sanity check
					place = sub
				else:
					return None

		return place

	# return a string list of all 'path's in the tree
	def allpath(self):
		result = []

		for k, v in self.items():
			result.append(k)
			if v.type == 'D':
				for p in self.get(k).allpath():
					result.append(k + '/' + p)

		return result

class ByPy(object):
	'''The main class of the bypy program'''

	# public static properties
	HelpMarker = "Usage:"

	ListFormatDict = {
		'$t' : (lambda json: ls_type(json['isdir'])),
		'$f' : (lambda json: json['path'].split('/')[-1]),
		'$c' : (lambda json: ls_time(json['ctime'])),
		'$m' : (lambda json: ls_time(json['mtime'])),
		'$d' : (lambda json: str(json['md5'] if 'md5' in json else '')),
		'$s' : (lambda json: str(json['size'])),
		'$i' : (lambda json: str(json['fs_id'])),
		'$b' : (lambda json: str(json['block_list'] if 'block_list' in json else '')),
		'$u' : (lambda json: 'HasSubDir' if 'ifhassubdir' in json and json['ifhassubdir'] else 'NoSubDir'),
		'$$' : (lambda json: '$')
	}

	# Old setting locations, should be moved to ~/.bypy to be clean
	OldTokenFilePath = HomeDir + os.sep + '.bypy.json'
	OldHashCachePath = HomeDir + os.sep + '.bypy.pickle'

	@staticmethod
	def migratesettings():
		result = ENoError

		filesToMove = [
			[ByPy.OldTokenFilePath, TokenFilePath],
			[ByPy.OldHashCachePath, HashCachePath]
		]

		result = makedir(ConfigDir, 0o700) and result # make it secretive
		# this directory must exist
		if result != ENoError:
			perr("Fail to create config directory '{}'".format(ConfigDir))
			return result

		for tomove in filesToMove:
			oldfile = tomove[0]
			newfile = tomove[1]
			if os.path.exists(oldfile):
				dst = newfile
				if os.path.exists(newfile):
					dst = TokenFilePath + '.old'
				result = movefile(oldfile, dst) and result

		return result

	@staticmethod
	def getcertfile():
		result = ENoError
		if not os.path.exists(ByPyCertsPath):
			if os.path.exists(ByPyCertsFile):
				result = copyfile(ByPyCertsFile, ByPyCertsPath)
			else:
				try:
					# perform a simple download from github
					urllib.urlretrieve(
					'https://raw.githubusercontent.com/houtianze/bypy/master/bypy.cacerts.pem', ByPyCertsPath)
				except IOError as ex:
					perr("Fail download CA Certs to '{}'.\n" + \
						"Exception:\n{}\nStack:{}\n".format(
						ByPyCertsPath, ex, traceback.format_exc()))

					result = EDownloadCerts	

		return result

	def __init__(self,
		slice_size = DefaultSliceSize,
		dl_chunk_size = DefaultDlChunkSize,
		verify = True,
		retry = 5, timeout = None,
		quit_when_fail = False,
		listfile = None,
		resumedownload = True,
		extraupdate = lambda: (),
		incregex = '',
		ondup = '',
		followlink = True,
		checkssl = True,
		cacerts = None,
		rapiduploadonly = False,
		verbose = 0, debug = False):

		# handle backward compatibility
		sr = ByPy.migratesettings()
		if sr != ENoError:
			# bail out
			perr("Failed to migrate old settings.")
			onexit(EMigrationFailed)
		# it doesn't matter if it failed, we can disable SSL verification anyway
		ByPy.getcertfile()

		self.__slice_size = slice_size
		self.__dl_chunk_size = dl_chunk_size
		self.__verify = verify
		self.__retry = retry
		self.__quit_when_fail = quit_when_fail
		self.__timeout = timeout
		self.__listfile = listfile
		self.__resumedownload = resumedownload
		self.__extraupdate = extraupdate
		self.__incregex = incregex
		self.__incregmo = re.compile(incregex)
		if ondup and len(ondup) > 0:
			self.__ondup = ondup[0].upper()
		else:
			self.__ondup = 'O' # O - Overwrite* S - Skip P - Prompt
		# TODO: whether this works is still to be tried out
		self.__isrev = False
		self.__followlink = followlink;

		# TODO: properly fix this InsecurePlatformWarning
		checkssl = False
		# using a mirror, which has name mismatch SSL error,
		# so need to disable SSL check
		if pcsurl != PcsUrl:
			# TODO: print a warning
			checkssl = False

		self.__checkssl = checkssl
		self.__rapiduploadonly = rapiduploadonly

		self.Verbose = verbose
		self.Debug = debug

		if self.__checkssl:
			# sort of undocumented by requests
			# http://stackoverflow.com/questions/10667960/python-requests-throwing-up-sslerror
			if cacerts is not None:
				if os.path.isfile(cacerts):
					self.__checkssl = cacerts
				else:
					perr("Invalid CA Bundle '{}' specified")

			# falling through here means no customized CA Certs specified
			if self.__checkssl is True:
				# use our own CA Bundle if possible
				if os.path.isfile(ByPyCertsPath):
					self.__checkssl = ByPyCertsPath
				else:
					# Well, disable cert verification
					pwarn(
"** SSL Certificate Verification has been disabled **\n\n" + \
"If you are confident that your CA Bundle can verify " + \
"Baidu PCS's certs, you can run the prog with the '" + CaCertsOption + \
" <your ca cert path>' argument to enable SSL cert verification.\n\n" + \
"However, most of the time, you can ignore this warning, " + \
"you are going to send sensitive data to the cloud plainly right?")
					self.__checkssl = False

		if not checkssl:
			disable_urllib3_warning()

		# the prophet said: thou shalt initialize
		self.__existing_size = 0
		self.__json = {}
		self.__access_token = ''
		self.__bduss = ''
		self.__pancookies = {}
		self.__remote_json = {}
		self.__slice_md5s = []

		if self.__listfile and os.path.exists(self.__listfile):
			with open(self.__listfile, 'r') as f:
				self.__list_file_contents = f.read()
		else:
			self.__list_file_contents = None

		# only if user specifies '-ddd' or more 'd's, the following
		# debugging information will be shown, as it's very talkative.
		if self.Debug >= 3:
			# these two lines enable debugging at httplib level (requests->urllib3->httplib)
			# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
			# the only thing missing will be the response.body which is not logged.
			enable_http_logging()

		if not self.__load_local_json():
			# no need to call __load_local_json() again as __auth() will load the json & acess token.
			result = self.__auth()
			if result != ENoError:
				perr("Program authorization FAILED.\n" + \
					"You need to authorize this program before using any PCS functions.\n" + \
					"Quitting...\n")
				onexit(result)

		if not self.__load_local_bduss():
			self.pv("BDUSS not found at '{}'.".format(BDUSSPath))

	def pv(self, msg, **kwargs):
		if self.Verbose:
			pr(msg)

	def pd(self, msg, level = 1, **kwargs):
		if self.Debug >= level:
			pdbg(msg, kwargs)

	def shalloverwrite(self, prompt):
		if self.__ondup == 'S':
			return False
		elif self.__ondup == 'P':
			ans = ask(prompt, False).upper()
			if not ans.startswith('Y'):
				return False

		return True

	def __print_error_json(self, r):
		try:
			dj = r.json()
			if 'error_code' in dj and 'error_msg' in dj:
				ec = dj['error_code']
				et = dj['error_msg']
				msg = ''
				if ec == IEMD5NotFound:
					pf = pinfo
					msg = et
				else:
					pf = perr
					msg = "Error code: {}\nError Description: {}".format(ec, et)
				pf(msg)
		except Exception:
			perr('Error parsing JSON Error Code from:\n{}'.format(rb(r.text)))
			perr('Exception:\n{}'.format(traceback.format_exc()))

	def __dump_exception(self, ex, url, pars, r, act):
		if self.Debug or self.Verbose:
			perr("Error accessing '{}'".format(url))
			if ex and isinstance(ex, Exception) and self.Debug:
				perr("Exception:\n{}".format(ex))
			tb = traceback.format_exc()
			if tb:
				pr(tb)
			perr("Function: {}".format(act.__name__))
			perr("Website parameters: {}".format(pars))
			if hasattr(r, 'status_code'):
				perr("HTTP Response Status Code: {}".format(r.status_code))
				if (r.status_code != 200 and r.status_code != 206) or (not (pars.has_key('method') and pars['method'] == 'download') and url.find('method=download') == -1 and url.find('baidupcs.com/file/') == -1):
					self.__print_error_json(r)
					perr("Website returned: {}".format(rb(r.text)))

	# always append / replace the 'access_token' parameter in the https request
	def __request_work(self, url, pars, act, method, actargs = None, addtoken = True, dumpex = True, **kwargs):
		result = ENoError
		r = None

		self.__extraupdate()
		parsnew = pars.copy()
		if addtoken:
			parsnew['access_token'] = self.__access_token

		try:
			self.pd(method + ' ' + url)
			self.pd("actargs: {}".format(actargs))
			self.pd("Params: {}".format(pars))

			if method.upper() == 'GET':
				r = requests.get(url,
					params = parsnew, timeout = self.__timeout, verify = self.__checkssl, **kwargs)
			elif method.upper() == 'POST':
				r = requests.post(url,
					params = parsnew, timeout = self.__timeout, verify = self.__checkssl, **kwargs)

			# BUGFIX: DON'T do this, if we are downloading a big file, the program sticks and dies
			#self.pd("Request Headers: {}".format(
			#	pprint.pformat(r.request.headers)), 2)
			sc = r.status_code
			self.pd("HTTP Status Code: {}".format(sc))
			# BUGFIX: DON'T do this, if we are downloading a big file, the program sticks and dies
			#self.pd("Header returned: {}".format(pprint.pformat(r.headers)), 2)
			#self.pd("Website returned: {}".format(rb(r.text)), 3)
			if sc == requests.codes.ok or sc == 206: # 206 Partial Content
				if sc == requests.codes.ok:
					if not (hasattr(pars, 'method') and pars['method'] == 'download'):
						try:
							j = r.json()
							if hasattr(j, 'error_code') and j['error_code'] == 0 and hasattr(j, 'error_msg') and j['error_msg'] == 'no error': # __walk_remote_dir_act() KeyError: u'list'
								self.pd("Unexpected response: {}".format(j))
								return ERequestFailed
						except Exception:
							sys.exc_clear()
					self.pd("Request OK, processing action")
				else:
					self.pd("206 Partial Content")
				result = act(r, actargs)
				if result == ENoError:
					self.pd("Request all goes fine")
			elif sc == 404 and r.url.find('http://bcscdn.baidu.com/bcs-cdn/wenxintishi') == 0: # = "error_code":31390,"error_msg":"Illegal File"
				self.pd("File is blacklisted ('wenxintishi'). Skipping.")
				result = EFileNotFound
			else:
				ec = 0
				try:
					j = r.json()
					ec = j['error_code']
					# error print is done in __dump_exception()
					# self.__print_error_json(r)
				except ValueError:
					perr("Not valid error JSON")

				#   6 (sc: 403): No permission to access user data
				# 110 (sc: 401): Access token invalid or no longer valid
				# 111 (sc: 401): Access token expired
				if ec == 111 or ec == 110 or ec == 6: # and sc == 401:
					self.pd("Need to refresh token, refreshing")
					if ENoError == self.__refresh_token(): # refresh the token and re-request
						# TODO: avoid dead recursive loops
						# TODO: properly pass retry
						result = self.__request(url, pars, act, method, actargs, True, addtoken, dumpex, **kwargs)
					else:
						result = EFatal
						perr("FATAL: Token refreshing failed, can't continue.\nQuitting...\n")
						onexit(result)
				# File md5 not found, you should use upload API to upload the whole file.
				elif ec == IEMD5NotFound: # and sc == 404:
					self.pd("MD5 not found, rapidupload failed")
					result = ec
				# user not exists
				elif ec == 31045: # and sc == 403:
					self.pd("BDUSS has expired")
					result = IEBDUSSExpired
				# superfile create failed
				elif ec == 31081: # and sc == 404:
					self.pd("Failed to combine files from MD5 slices (superfile create failed)")
					result = ec
				# topath already exists
				elif ec == 31196: # and sc == 403:
					self.pd("UnzipCopy destination already exists.")
					result = act(r, actargs)
				# file copy failed
				elif ec == 31197: # and sc == 503:
					result = act(r, actargs)
				# file size exceeds limit
				elif ec == 31199: # and sc == 403:
					result = act(r, actargs)
				# errors that make retrying meaningless
				elif (
					ec == 31061 or # sc == 400 file already exists
					ec == 31062 or # sc == 400 file name is invalid
					ec == 31063 or # sc == 400 file parent path does not exist
					ec == 31064 or # sc == 403 file is not authorized
					ec == 31065 or # sc == 400 directory is full
					ec == 31066): # sc == 403 (indeed 404) file does not exist
					result = ec
					if dumpex:
						self.__dump_exception(None, url, pars, r, act)
				else:
					result = ERequestFailed
					if dumpex:
						self.__dump_exception(None, url, pars, r, act)
		except (requests.exceptions.RequestException,
				socket.error) as ex:
			# If certificate check failed, no need to continue
			# but prompt the user for work-around and quit
			# why so kludge? because requests' SSLError doesn't set
			# the errno and strerror due to using **kwargs,
			# so we are forced to use string matching
			if isinstance(ex, requests.exceptions.SSLError) \
				and re.match(r'^\[Errno 1\].*error:14090086.*:certificate verify failed$', str(ex), re.I):
				# [Errno 1] _ssl.c:504: error:14090086:SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed
				result = EFatal
				self.__dump_exception(ex, url, pars, r, act)
				perr("\n\n== Baidu's Certificate Verification Failure ==\n" + \
				"We couldn't verify Baidu's SSL Certificate.\n" + \
				"It's most likely that the system doesn't have " + \
				"the corresponding CA certificate installed.\n" + \
				"There are two ways of solving this:\n" + \
				"Either) Run this prog with the '" + CaCertsOption + \
				" <path to " + ByPyCertsPath + "> argument " + \
				"(" + ByPyCertsPath + " comes along with this prog). " + \
				"This is the secure way. " + \
				"However, it won't work after 2020-02-08 when " + \
				"the certificat expires.\n" + \
				"Or) Run this prog with the '" + DisableSslCheckOption + \
				"' argument. This supresses the CA cert check " + \
				"and always works.\n")
				onexit(result)

			# why so kludge? because requests' SSLError doesn't set
			# the errno and strerror due to using **kwargs,
			# so we are forced to use string matching
			if isinstance(ex, requests.exceptions.SSLError) \
				and re.match(r'^\[Errno 1\].*error:14090086.*:certificate verify failed$', str(ex), re.I):
				# [Errno 1] _ssl.c:504: error:14090086:SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed
				perr("\n*** We probably don't have Baidu's CA Certificate ***\n" + \
				"This in fact doesn't matter most of the time.\n\n" + \
				"However, if you are _really_ concern about it, you can:\n" + \
				"Either) Run this prog with the '" + CaCertsOption + \
				" <path to bypy.cacerts.pem>' " + \
				"argument. This is the secure way.\n" + \
				"Or) Run this prog with the '" + DisableSslCheckOption + \
				"' argument. This suppresses the CA cert check.\n")

			result = ERequestFailed
			if dumpex:
				self.__dump_exception(ex, url, pars, r, act)

		except Exception as ex:
			result = EFatal
			self.__dump_exception(ex, url, pars, r, act)
			perr("Fatal Exception, no way to continue.\nQuitting...\n")
			perr("If the error is reproducible, run the program with `-dv` arguments again to get more info.\n")
			onexit(result)
			# we eat the exception, and use return code as the only
			# error notification method, we don't want to mix them two
			#raise # must notify the caller about the failure

		return result

	def __request(self, url, pars, act, method, actargs = None, retry = True, addtoken = True, dumpex = True, **kwargs):
		tries = 1
		if retry:
			tries = self.__retry

		i = 0
		result = ERequestFailed

		# Change the User-Agent to avoid server fuss
		kwnew = kwargs.copy()
		if 'headers' not in kwnew:
			kwnew['headers'] = { 'User-Agent': UserAgent }
		else:
			kwnew['headers']['User-Agent'] = UserAgent

		while True:
			result = self.__request_work(url, pars, act, method, actargs, addtoken, dumpex, **kwnew)
			i += 1
			# only ERequestFailed needs retry, other error still directly return
			if result == ERequestFailed:
				if i < tries:
					# algo changed: delay more after each failure
					delay = RetryDelayInSec * i
					perr("Waiting {} seconds before retrying...".format(delay))
					time.sleep(delay)
					perr("Request Try #{} / {}".format(i + 1, tries))
				else:
					perr("Maximum number ({}) of tries failed.".format(tries))
					if self.__quit_when_fail:
						onexit(EMaxRetry)
					break
			else:
				break

		return result

	def __get(self, url, pars, act, actargs = None, retry = True, addtoken = True, dumpex = True, **kwargs):
		return self.__request(url, pars, act, 'GET', actargs, retry, addtoken, dumpex, **kwargs)

	def __post(self, url, pars, act, actargs = None, retry = True, addtoken = True, dumpex = True, **kwargs):
		return self.__request(url, pars, act, 'POST', actargs, retry, addtoken, dumpex, **kwargs)

	# direction: True - upload, False - download
	def __shallinclude(self, lpath, rpath, direction):
		arrow = '==>' if direction else '<=='
		checkpath = lpath if direction else rpath
		# TODO: bad practice, see os.access() document for more info
		if direction: # upload
			if not os.path.exists(lpath):
				perr("'{}' {} '{}' skipped since local path no longer exists".format(
					lpath, arrow, rpath));
				return False
		else: # download
			if os.path.exists(lpath) and (not os.access(lpath, os.R_OK)):
				perr("'{}' {} '{}' skipped due to permission".format(
					lpath, arrow, rpath));
				return False

		if '\\' in os.path.basename(checkpath):
			perr("'{}' {} '{}' skipped due to problemic '\\' in the path".format(
				lpath, arrow, rpath));
			return False

		include = (not self.__incregex) or self.__incregmo.match(checkpath)
		if not include:
			self.pv("'{}' {} '{}' skipped as it's not included in the regex pattern".format(
				lpath, arrow, rpath));

		return include

	def __replace_list_format(self, fmt, j):
		output = fmt
		for k, v in ByPy.ListFormatDict.iteritems():
			output = output.replace(k, v(j))
		return output

	def __load_local_json(self):
		try:
			with open(TokenFilePath, 'rb') as infile:
				self.__json = json.load(infile)
				self.__access_token = self.__json['access_token']
				self.pd("Token loaded:")
				self.pd(self.__json)
				return True
		except IOError:
			perr('Error while loading baidu pcs token:')
			perr(traceback.format_exc())
			return False

	def __store_json_only(self, j):
		self.__json = j
		self.__access_token = self.__json['access_token']
		self.pd("access token: " + self.__access_token)
		self.pd("Authorize JSON:")
		self.pd(self.__json)
		tokenmode = 0o600
		try:
			with open(TokenFilePath, 'wb') as outfile:
				json.dump(self.__json, outfile)

			os.chmod(TokenFilePath, tokenmode)
			return ENoError
		except Exception:
			perr("Exception occured while trying to store access token:\n" \
				"Exception:\n{}".format(traceback.format_exc()))
			return EFileWrite

	def __store_json(self, r):
		j = {}
		try:
			j = r.json()
		except Exception:
			perr("Failed to decode JSON:\n" \
				"Exception:\n{}".format(traceback.format_exc()))
			perr("Error response:\n{}".format(r.text));
			pinfo('-' * 64)
			pinfo("""This is most likely caused by authorization errors.
Possible causes:
 - You didn't run this program for a long time (more than a month).
 - You changed your Baidu password after authorizing this program.
 - You didn't give this program the 'netdisk' access while authorizing.
 - ...
Possible fixes:
 1. Remove the authorization token by running with the parameter '{}', and then re-run this program.
 2. If (1) still doesn't solve the problem, you may have to go to:
    https://passport.baidu.com/accountbind
    and remove the authorization of this program, and then re-run this program.""".format(CleanOptionShort))
			return EInvalidJson
		return self.__store_json_only(j)

	def __load_local_bduss(self):
		try:
			with open(BDUSSPath, 'rb') as infile:
				self.__bduss = infile.readline().strip()
				self.pd("BDUSS loaded: {}".format(self.__bduss))
				self.__pancookies = {'BDUSS': self.__bduss}
				return True
		except IOError:
			self.pd('Error loading BDUSS:')
			self.pd(traceback.format_exc())
			return False

	def __server_auth_act(self, r, args):
		return self.__store_json(r)

	def __server_auth(self):
		params = {
			'client_id' : ApiKey,
			'response_type' : 'code',
			'redirect_uri' : 'oob',
			'scope' : 'basic netdisk' }
		pars = urllib.urlencode(params)
		msg = 'Please visit:\n{}\nAnd authorize this app'.format(ServerAuthUrl + '?' + pars) + \
			'\nPaste the Authorization Code here within 10 minutes.'
		auth_code = ask(msg).strip()
		self.pd("auth_code: {}".format(auth_code))
		pr('Authorizing, please be patient, it may take upto {} seconds...'.format(self.__timeout))

		pars = {
			'code' : auth_code,
			'redirect_uri' : 'oob' }

		result = None
		for auth in AuthServerList:
			(url, retry, msg) = auth
			pr(msg)
			result = self.__get(url, pars, self.__server_auth_act, retry = retry, addtoken = False)
			if result == ENoError:
				break

		if result == ENoError:
			pr("Successfully authorized")
		else:
			perr("Fatal: All server authorizations failed.")

		return result

	def __device_auth_act(self, r, args):
		dj = r.json()
		return self.__get_token(dj)

	def __device_auth(self):
		pars = {
			'client_id' : ApiKey,
			'response_type' : 'device_code',
			'scope' : 'basic netdisk'}
		return self.__get(DeviceAuthUrl, pars, self.__device_auth_act, addtoken = False)

	def __auth(self):
		if ServerAuth:
			return self.__server_auth()
		else:
			return self.__device_auth()

	def __get_token_act(self, r, args):
		return self.__store_json(r)

	def __get_token(self, deviceJson):
		msg = 'Please visit:\n' + deviceJson['verification_url'] + \
			'\nwithin ' + str(deviceJson['expires_in']) + ' seconds\n' + \
			'Input the CODE: {}\n'.format(deviceJson['user_code']) + \
			'and Authorize this little app.\n' + \
			"Press [Enter] when you've finished\n"
		ask(msg)

		pars = {
			'grant_type' : 'device_token',
			'code' :  deviceJson['device_code'],
			'client_id' : ApiKey,
			'client_secret' : SecretKey}

		return self.__get(TokenUrl, pars, self.__get_token_act, addtoken = False)

	def __refresh_token_act(self, r, args):
		return self.__store_json(r)

	def __refresh_token(self):
		if ServerAuth:
			pr('Refreshing, please be patient, it may take upto {} seconds...'.format(self.__timeout))

			pars = {
				'grant_type' : 'refresh_token',
				'refresh_token' : self.__json['refresh_token'] }

			result = None
			for refresh in RefreshServerList:
				(url, retry, msg) = refresh
				pr(msg)
				result = self.__get(url, pars, self.__refresh_token_act, retry = retry, addtoken = False)
				if result == ENoError:
					break

			if result == ENoError:
				pr("Token successfully refreshed")
			else:
				perr("Token-refreshing on all the servers failed")

			return result
		else:
			pars = {
				'grant_type' : 'refresh_token',
				'refresh_token' : self.__json['refresh_token'],
				'client_secret' : SecretKey,
				'client_id' : ApiKey }
			return self.__post(TokenUrl, pars, self.__refresh_token_act)

	def __quota_act(self, r, args):
		j = r.json()
		pr('Quota: ' + human_size(j['quota']))
		pr('Used: ' + human_size(j['used']))
		return ENoError

	def help(self, command): # this comes first to make it easy to spot
		''' Usage: help command - provide some information for the command '''
		for i, v in ByPy.__dict__.iteritems():
			if callable(v) and v.__doc__ and v.__name__ == command :
				help = v.__doc__.strip()
				pos = help.find(ByPy.HelpMarker)
				if pos != -1:
					pr("Usage: " + help[pos + len(ByPy.HelpMarker):].strip())

	def refreshtoken(self):
		''' Usage: refreshtoken - refresh the access token '''
		return self.__refresh_token()

	def info(self):
		return self.quota()

	def quota(self):
		''' Usage: quota/info - displays the quota information '''
		pars = {
			'method' : 'info' }
		return self.__get(pcsurl + 'quota', pars, self.__quota_act)

	# return:
	#   0: local and remote files are of same size
	#   1: local file is larger
	#   2: remote file is larger
	#  -1: inconclusive (probably invalid remote json)
	def __compare_size(self, lsize, rjson):
		if 'size' in rjson:
			rsize = rjson['size']
			if lsize == rsize:
				return 0;
			elif lsize > rsize:
				return 1;
			else:
				return 2
		else:
			return -1

	def __verify_current_file(self, j, gotlmd5):
		# if we really don't want to verify
		if self.__current_file == '/dev/null' and not self.__verify:
			return ENoError

		rsize = 0
		rmd5 = 0

		# always perform size check even __verify is False
		if 'size' in j:
			rsize = j['size']
		else:
			perr("Unable to verify JSON: '{}', as no 'size' entry found".format(j))
			return EHashMismatch

		if 'md5' in j:
			rmd5 = binascii.unhexlify(j['md5'])
		#elif 'block_list' in j and len(j['block_list']) > 0:
		#	rmd5 = j['block_list'][0]
		#else:
		#	# quick hack for meta's 'block_list' field
		#	pwarn("No 'md5' nor 'block_list' found in json:\n{}".format(j))
		#	pwarn("Assuming MD5s match, checking size ONLY.")
		#	rmd5 = self.__current_file_md5
		else:
			perr("Unable to verify JSON: '{}', as no 'md5' entry found".format(j))
			return EHashMismatch

		self.pd("Comparing local file '{}' and remote file '{}'".format(
			self.__current_file, j['path']))
		self.pd("Local file size : {}".format(self.__current_file_size))
		self.pd("Remote file size: {}".format(rsize))

		if self.__current_file_size == rsize:
			self.pd("Local file and remote file sizes match")
			if self.__verify:
				if not gotlmd5:
					self.__current_file_md5 = md5(self.__current_file)
				self.pd("Local file MD5 : {}".format(binascii.hexlify(self.__current_file_md5)))
				self.pd("Remote file MD5: {}".format(binascii.hexlify(rmd5)))

				if self.__current_file_md5 == rmd5:
					self.pd("Local file and remote file hashes match")
					return ENoError
				else:
					pinfo("Local file and remote file hashes DON'T match")
					return EHashMismatch
			else:
				return ENoError
		else:
			pinfo("Local file and remote file sizes DON'T match")
			return EHashMismatch

	def __get_file_info_act(self, r, args):
		remotefile = args
		j = r.json()
		self.pd("List json: {}".format(j))
		l = j['list']
		for f in l:
			if f['path'] == remotefile: # case-sensitive
				self.__remote_json = f
				self.pd("File info json: {}".format(self.__remote_json))
				return ENoError;

		return EFileNotFound

	# the 'meta' command sucks, since it doesn't supply MD5 ...
	# now the JSON is written to self.__remote_json, due to Python call-by-reference chaos
	# https://stackoverflow.com/questions/986006/python-how-do-i-pass-a-variable-by-reference
	# as if not enough confusion in Python call-by-reference
	def __get_file_info(self, remotefile, **kwargs):
		rdir, rfile = posixpath.split(remotefile)
		self.pd("__get_file_info(): rdir : {} | rfile: {}".format(rdir, rfile))
		if rdir and rfile:
			pars = {
				'method' : 'list',
				'path' : rdir,
				'by' : 'name', # sort in case we can use binary-search, etc in the futrue.
				'order' : 'asc' }

			return self.__get(pcsurl + 'file', pars, self.__get_file_info_act, remotefile, **kwargs)
		else:
			perr("Invalid remotefile '{}' specified.".format(remotefile))
			return EArgument

	def __list_act(self, r, args):
		(remotedir, fmt) = args
		j = r.json()
		pr("{} ({}):".format(remotedir, fmt))
		for f in j['list']:
			pr(self.__replace_list_format(fmt, f))

		return ENoError

	def ls(self, remotepath = '',
		fmt = '$t $f $s $m $d',
		sort = 'name', order = 'asc'):
		return self.list(remotepath, fmt, sort, order)

	def list(self, remotepath = '',
		fmt = '$t $f $s $m $d',
		sort = 'name', order = 'asc'):
		''' Usage: list/ls [remotepath] [format] [sort] [order] - list the 'remotepath' directory at Baidu PCS
    remotepath - the remote path at Baidu PCS. default: root directory '/'
	format - specifies how the list are displayed
	  $t - Type: Directory ('D') or File ('F')
	  $f - File name
	  $c - Creation time
	  $m - Modification time
	  $d - MD5 hash
	  $s - Size
	  $$ - The '$' sign
	  So '$t - $f - $s - $$' will display "Type - File - Size - $'
	  Default format: '$t $f $s $m $d'
    sort - sorting by [name, time, size]. default: 'name'
    order - sorting order [asc, desc]. default: 'asc'
		'''
		rpath = get_pcs_path(remotepath)

		pars = {
			'method' : 'list',
			'path' : rpath,
			'by' : sort,
			'order' : order }

		return self.__get(pcsurl + 'file', pars, self.__list_act, (rpath, fmt))

	def __meta_act(self, r, args):
		return self.__list_act(r, args)

	# multi-file meta is not implemented for it's low usage
	def meta(self, remotepath, fmt = '$t $u $f $s $c $m $i $b'):
		''' Usage: meta <remotepath> [format] - \
get information of the given path (dir / file) at Baidu Yun.
  remotepath - the remote path
  format - specifies how the list are displayed
    it supports all the format variables in the 'list' command, and additionally the followings:
	$i - fs_id
	$b - MD5 block_list
	$u - Has sub directory or not
'''
		rpath = get_pcs_path(remotepath)
		pars = {
			'method' : 'meta',
			'path' : rpath }
		return self.__get(pcsurl + 'file', pars,
			self.__meta_act, (rpath, fmt))

	def __combine_file_act(self, r, args):
		result = self.__verify_current_file(r.json(), False)
		if result == ENoError:
			self.pv("'{}' =C=> '{}' OK.".format(self.__current_file, args))
		else:
			perr("'{}' =C=> '{}' FAILED.".format(self.__current_file, args))
		# save the md5 list, in case we add in resume function later to this program
		self.__last_slice_md5s = self.__slice_md5s
		self.__slice_md5s = []

		return result

	def __combine_file(self, remotepath, ondup = 'overwrite'):
		pars = {
			'method' : 'createsuperfile',
			'path' : remotepath,
			'ondup' : ondup }
		if self.__isrev and ondup != 'newcopy':
			pars['is_revision'] = 1

		# always print this, so that we can use these data to combine file later
		pr("Combining the following MD5 slices:")
		for m in self.__slice_md5s:
			pr(m)

		param = { 'block_list' : self.__slice_md5s }
		return self.__post(pcsurl + 'file',
				pars, self.__combine_file_act,
				remotepath,
				data = { 'param' : json.dumps(param) } )

	def unzip(self, remotepath, subpath = '/', start = 0, limit = 1000):
		''' Usage: unzip <remotepath> [<subpath> [<start> [<limit>]]]'''
		rpath = get_pcs_path(remotepath)
		return self.__panapi_unzip_file(rpath, subpath, start, limit);

	def __panapi_unzip_file_act(self, r, args):
		j = r.json()
		self.pd("Unzip response: {}".format(j))
		if j['errno'] == 0:
			if 'time' in j:
				perr("Extraction not completed yet: '{}'...".format(args['path']))
				return ERequestFailed
			elif 'list' in j:
				for e in j['list']:
					pr("{}\t{}\t{}".format(ls_type(e['isdir'] == 1), e['file_name'], e['size']))
		return ENoError

	def __panapi_unzip_file(self, rpath, subpath, start, limit):
		pars = {
			'path' : rpath,
			'start' : start,
			'limit' : limit,
			'subpath' : '/' + subpath.strip('/') }

		self.pd("Unzip request: {}".format(pars))
		return self.__get(PanAPIUrl + 'unzip?app_id=250528',
				pars, self.__panapi_unzip_file_act, cookies = self.__pancookies, actargs = pars )

	def extract(self, remotepath, subpath, saveaspath = None):
		''' Usage: extract <remotepath> <subpath> [<saveaspath>]'''
		rpath = get_pcs_path(remotepath)
		topath = get_pcs_path(saveaspath)
		if not saveaspath:
			topath = os.path.dirname(rpath) + '/' + subpath
		return self.__panapi_unzipcopy_file(rpath, subpath, topath)

	def __panapi_unzipcopy_file_act(self, r, args):
		j = r.json()
		self.pd("UnzipCopy response: {}".format(j))
		if 'path' in j:
			self.pv("Remote extract: '{}#{}' =xx=> '{}' OK.".format(args['path'], args['subpath'], j[u'path']))
			return ENoError
		elif 'error_code' in j:
			if j['error_code'] == 31196:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. File already exists.".format(args['path'], args['subpath'], args['topath']))
				subresult = self.__delete(args['topath'])
				if subresult == ENoError:
					return self.__panapi_unzipcopy_file(args['path'], args['subpath'], args['topath'])
				else:
					return ERequestFailed
			elif j['error_code'] == 31199:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. File too large.".format(args['path'], args['subpath'], args['topath']))
				return EMaxRetry
			else:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. Unknown error {}: {}.".format(args['path'], args['subpath'], args['topath'], j['error_code'], j['error_msg']))
		return EMaxRetry

	def __panapi_unzipcopy_file(self, rpath, subpath, topath):
		pars = {
			'app_id' : 250528,
			'method' : 'unzipcopy',
			'path' : rpath,
			'subpath' : '/' + subpath.strip('/'),
			'topath' : topath }

		self.pd("UnzipCopy request: {}".format(pars))
		return self.__get(pcsurl + 'file',
				pars, self.__panapi_unzipcopy_file_act, addtoken = False, cookies = self.__pancookies, actargs = pars )

	def revision(self, remotepath):
		''' Usage: revision <remotepath> '''
		rpath = get_pcs_path(remotepath)
		return self.__panapi_revision_list(rpath)

	def history(self, remotepath):
		''' Usage: history <remotepath> '''
		return self.revision(remotepath)

	def __panapi_revision_list_act(self, r, args):
		j = r.json()
		self.pd("RevisionList response: {}".format(j))
		if j['errno'] == 0:
			if 'list' in j:
				for e in j['list']:
					pr("{}\t{}\t{}".format(e['revision'], e['size'], ls_time(e['revision'] / 1e6)))
			return ENoError
		if j['errno'] == -6: # invalid BDUSS
			pr("BDUSS has expired.")
			return IEBDUSSExpired
		if j['errno'] == -9:
			pr("File '{}' not exists.".format(args['path']))
			return EFileNotFound
		return ENoError

	def __panapi_revision_list(self, rpath):
		pars = {
			'path' : rpath,
			'desc' : 1 }

		self.pd("RevisionList request: {}".format(pars))
		return self.__post(PanAPIUrl + 'revision/list?app_id=250528',
				{}, self.__panapi_revision_list_act, pars, data = pars, cookies = self.__pancookies )

	def revert(self, remotepath, revision, dir = None):
		''' Usage: revert <remotepath> revisionid [dir]'''
		rpath = get_pcs_path(remotepath)
		dir = get_pcs_path(dir)
		if not dir:
			dir = os.path.dirname(rpath)
		return self.__panapi_revision_revert(rpath, revision, dir)

	def __panapi_revision_revert_act(self, r, args):
		j = r.json()
		self.pd("RevisionRevert response: {}".format(j))
		if j['errno'] == 0:
			self.pv("Remote revert: '{}#{}' =rr=> '{}' OK.".format(args['path'], args['revision'], j['path']))
			return ENoError
		if j['errno'] == -6: # invalid BDUSS
			pr("BDUSS has expired.")
			return IEBDUSSExpired
		if j['errno'] == -9:
			pr("File '{}' not exists.".format(args['path']))
			return EFileNotFound
		if j['errno'] == 10:
			pr("Reverting '{}' in process...".format(args['path']))
			return ERequestFailed
		return ENoError

	def __panapi_revision_revert(self, rpath, revision, dir = None):
		if not dir:
			dir = os.path.dirname(rpath)
		pars = {
			'revision' : revision,
			'path' : rpath,
			'type' : 2,
			'dir' : dir }

		self.pd("RevisionRevert request: {}".format(pars))
		return self.__post(PanAPIUrl + 'revision/revert?app_id=250528',
				{}, self.__panapi_revision_revert_act, pars, data = pars, cookies = self.__pancookies )

	def __upload_slice_act(self, r, args):
		j = r.json()
		# slices must be verified and re-upload if MD5s don't match,
		# otherwise, it makes the uploading slower at the end
		rsmd5 = j['md5']
		self.pd("Uploaded MD5 slice: " + rsmd5)
		if self.__current_slice_md5 == binascii.unhexlify(rsmd5):
			self.__slice_md5s.append(rsmd5)
			self.pv("'{}' >>==> '{}' OK.".format(self.__current_file, args))
			return ENoError
		else:
			perr("'{}' >>==> '{}' FAILED.".format(self.__current_file, args))
			return EHashMismatch

	def __upload_slice(self, remotepath):
		pars = {
			'method' : 'upload',
			'type' : 'tmpfile'}

		return self.__post(cpcsurl + 'file',
				pars, self.__upload_slice_act, remotepath,
				# wants to be proper? properness doesn't work (search this sentence for more occurence)
				#files = { 'file' : (os.path.basename(self.__current_file), self.__current_slice) } )
				files = { 'file' : ('file', self.__current_slice) } )

	def __upload_file_slices(self, localpath, remotepath, ondup = 'overwrite'):
		pieces = MaxSlicePieces
		slice = self.__slice_size
		if self.__current_file_size <= self.__slice_size * MaxSlicePieces:
			# slice them using slice size
			pieces = (self.__current_file_size + self.__slice_size - 1 ) / self.__slice_size
		else:
			# the following comparision is done in the caller:
			# elif self.__current_file_size <= MaxSliceSize * MaxSlicePieces:

			# no choice, but need to slice them to 'MaxSlicePieces' pieces
			slice = (self.__current_file_size + MaxSlicePieces - 1) / MaxSlicePieces

		self.pd("Slice size: {}, Pieces: {}".format(slice, pieces))

		i = 0
		ec = ENoError
		with open(self.__current_file, 'rb') as f:
			start_time = time.time()
			while i < pieces:
				self.__current_slice = f.read(slice)
				m = hashlib.md5()
				m.update(self.__current_slice)
				self.__current_slice_md5 = m.digest()
				self.pd("Uploading MD5 slice: {}, #{} / {}".format(
					binascii.hexlify(self.__current_slice_md5),
					i + 1, pieces))
				j = 0
				while True:
					ec = self.__upload_slice(remotepath)
					if ec == ENoError:
						self.pd("Slice MD5 match, continuing next slice")
						pprgr(f.tell(), self.__current_file_size, start_time)
						break
					elif j < self.__retry:
						j += 1
						# TODO: Improve or make it TRY with the __requet retry logic
						perr("Slice MD5 mismatch, waiting {} seconds before retrying...".format(RetryDelayInSec))
						time.sleep(RetryDelayInSec)
						perr("Retrying #{} / {}".format(j + 1, self.__retry))
					else:
						self.__slice_md5s = []
						break
				i += 1

		if ec != ENoError:
			return ec
		else:
			#self.pd("Sleep 2 seconds before combining, just to be safer.")
			#time.sleep(2)
			return self.__combine_file(remotepath, ondup = 'overwrite')

	def __rapidupload_file_act(self, r, args):
		if self.__verify:
			self.pd("Not strong-consistent, sleep 1 second before verification")
			time.sleep(1)
			return self.__verify_current_file(r.json(), True)
		else:
			return ENoError

	def __rapidupload_file(self, localpath, remotepath, ondup = 'overwrite'):
		self.__current_file_md5 = md5(self.__current_file)
		self.__current_file_slice_md5 = slice_md5(self.__current_file)
		self.__current_file_crc32 = crc32(self.__current_file)

		md5str = binascii.hexlify(self.__current_file_md5)
		slicemd5str =  binascii.hexlify(self.__current_file_slice_md5)
		crcstr = hex(self.__current_file_crc32)
		pars = {
			'method' : 'rapidupload',
			'path' : remotepath,
			'content-length' : self.__current_file_size,
			'content-md5' : md5str,
			'slice-md5' : slicemd5str,
			'content-crc32' : crcstr,
			'ondup' : ondup }
		if self.__isrev and ondup != 'newcopy':
			pars['is_revision'] = 1

		self.pd("RapidUploading Length: {} MD5: {}, Slice-MD5: {}, CRC: {}".format(
			self.__current_file_size, md5str, slicemd5str, crcstr))
		return self.__post(pcsurl + 'file', pars, self.__rapidupload_file_act)

	def __upload_one_file_act(self, r, args):
		result = self.__verify_current_file(r.json(), False)
		if result == ENoError:
			self.pv("'{}' ==> '{}' OK.".format(self.__current_file, args))
		else:
			perr("'{}' ==> '{}' FAILED.".format(self.__current_file, args))

		return result

	def __upload_one_file(self, localpath, remotepath, ondup = 'overwrite'):
		pars = {
			'method' : 'upload',
			'path' : remotepath,
			'ondup' : ondup }
		if self.__isrev and ondup != 'newcopy':
			pars['is_revision'] = 1

		with open(localpath, "rb") as f:
			return self.__post(cpcsurl + 'file',
				pars, self.__upload_one_file_act, remotepath,
				# wants to be proper? properness doesn't work
				# there seems to be a bug at Baidu's handling of http text:
				# Content-Disposition: ...  filename=utf-8''yourfile.ext
				# (pass '-ddd' to this program to verify this)
				# when you specify a unicode file name, which will be encoded
				# using the utf-8'' syntax
				# so, we put a work-around here: we always call our file 'file'
				# NOTE: an empty file name '' doesn't seem to work, so we
				# need to give it a name at will, but empty one.
				# apperantly, Baidu PCS doesn't use this file name for
				# checking / verification, so we are probably safe here.
				#files = { 'file' : (os.path.basename(localpath), f) })
				files = { 'file' : ('file', f) })

	#TODO: upload empty directories as well?
	def __walk_upload(self, localpath, remotepath, ondup, walk):
		(dirpath, dirnames, filenames) = walk

		rdir = os.path.relpath(dirpath, localpath)
		if rdir == '.':
			rdir = ''
		else:
			rdir = rdir.replace('\\', '/')

		rdir = (remotepath + '/' + rdir).rstrip('/') # '/' bites

		result = ENoError
		for name in filenames:
			#lfile = os.path.join(dirpath, name)
			lfile = joinpath(dirpath, name)
			self.__current_file = lfile
			self.__current_file_size = getfilesize(lfile)
			rfile = rdir + '/' + name.replace('\\', '/')
			# if the corresponding file matches at Baidu Yun, then don't upload
			upload = True
			self.__isrev = False
			self.__remote_json = {}
			subresult = self.__get_file_info(rfile, dumpex = False)
			if subresult == ENoError: # same-name remote file exists
				self.__isrev = True
				if ENoError == self.__verify_current_file(self.__remote_json, False):
					# the two files are the same
					upload = False
					self.pv("Remote file '{}' already exists, skip uploading".format(rfile))
				else: # the two files are different
					if not self.shalloverwrite("Remote file '{}' exists but is different, ".format(rfile) + \
							"do you want to overwrite it? [y/N]"):
						upload = False

			if upload:
				fileresult = self.__upload_file(lfile, rfile, ondup)
				if fileresult != ENoError:
					result = fileresult # we still continue
			else:
				pinfo("Remote file '{}' exists and is the same, skip uploading".format(rfile))
				# next / continue

		return result

	def __upload_dir(self, localpath, remotepath, ondup = 'overwrite'):
		self.pd("Uploading directory '{}' to '{}'".format(localpath, remotepath))
		# it's so minor that we don't care about the return value
		self.__mkdir(remotepath, dumpex = False)
		for walk in os.walk(localpath, followlinks=self.__followlink):
			self.__walk_upload(localpath, remotepath, ondup, walk)

	def __upload_file(self, localpath, remotepath, ondup = 'overwrite'):
		# TODO: this is a quick patch
		if not self.__shallinclude(localpath, remotepath, True):
			# since we are not going to upload it, there is no error
			return ENoError

		self.__current_file = localpath
		self.__current_file_size = getfilesize(localpath)

		result = ENoError
		if self.__current_file_size > MinRapidUploadFileSize:
			self.pd("'{}' is being RapidUploaded.".format(self.__current_file))
			result = self.__rapidupload_file(localpath, remotepath, ondup)
			if result == ENoError:
				self.pv("RapidUpload: '{}' =R=> '{}' OK.".format(localpath, remotepath))
			else:
				if not self.__rapiduploadonly:
					self.pd("'{}' can't be RapidUploaded, now trying normal uploading.".format(
						self.__current_file))
					# rapid upload failed, we have to upload manually
					if self.__current_file_size <= self.__slice_size:
						self.pd("'{}' is being non-slicing uploaded.".format(self.__current_file))
						# no-slicing upload
						result = self.__upload_one_file(localpath, remotepath, ondup)
					elif self.__current_file_size <= MaxSliceSize * MaxSlicePieces:
						# slice them using slice size
						self.pd("'{}' is being slicing uploaded.".format(self.__current_file))
						result = self.__upload_file_slices(localpath, remotepath, ondup)
					else:
						result = EFileTooBig
						perr("Error: size of file '{}' - {} is too big".format(
							self.__current_file,
							self.__current_file_size))
				else:
					self.pv("'{}' can't be rapidly uploaded, so it's skipped since we are in the rapid-upload-only mode.".format(localpath))

			return result
		elif not self.__rapiduploadonly:
			# very small file, must be uploaded manually and no slicing is needed
			self.pd("'{}' is small and being non-slicing uploaded.".format(self.__current_file))
			return self.__upload_one_file(localpath, remotepath, ondup)

	def upload(self, localpath = u'', remotepath = '', ondup = "overwrite"):
		''' Usage: upload [localpath] [remotepath] [ondup] - \
upload a file or directory (recursively)
    localpath - local path, is the current directory '.' if not specified
    remotepath - remote path at Baidu Yun (after app root directory at Baidu Yun)
    ondup - what to do upon duplication ('overwrite' or 'newcopy'), default: 'overwrite'
		'''
		# copying since Python is call-by-reference by default,
		# so we shall not modify the passed-in parameters
		lpath = localpath.rstrip('\\/ ') # no trailing slashes
		lpathbase = os.path.basename(lpath)
		rpath = remotepath
		if not lpath:
			# so, if you don't specify the local path, it will always be the current direcotry
			# and thus isdir(localpath) is always true
			lpath = os.path.abspath(".")
			self.pd("localpath not set, set it to current directory '{}'".format(localpath))

		if os.path.isfile(lpath):
			self.pd("Uploading file '{}'".format(lpath))
			if not rpath or rpath == '/': # to root we go
				rpath = lpathbase
			if rpath[-1] == '/': # user intends to upload to this DIR
				rpath = get_pcs_path(rpath + lpathbase)
			else:
				rpath = get_pcs_path(rpath)
				# avoid uploading a file and destroy a directory by accident
				subresult = self.__get_file_info(rpath)
				if subresult == ENoError: # remove path exists, check is dir or file
					if self.__remote_json['isdir']: # do this only for dir
						rpath += '/' + lpathbase # rpath is guaranteed no '/' ended
					else: # rpath is a file
						self.__isrev = True
			self.pd("remote path is '{}'".format(rpath))
			return self.__upload_file(lpath, rpath, ondup)
		elif os.path.isdir(lpath):
			self.pd("Uploading directory '{}' recursively".format(lpath))
			rpath = get_pcs_path(rpath)
			return self.__upload_dir(lpath, rpath, ondup)
		else:
			perr("Error: invalid local path '{}' for uploading specified.".format(localpath))
			return EParameter

	def combine(self, remotefile, localfile = '', *args):
		''' Usage: combine <remotefile> [md5s] [localfile] - \
try to create a file at PCS by combining slices, having MD5s specified
  remotefile - remote file at Baidu Yun (after app root directory at Baidu Yun)
  md5s - MD5 digests of the slices, separated by spaces
    if not specified, you must specify the 'listfile' using the '-l' or '--list-file' switch in command line. the MD5 digests will be read from the (text) file, which can store the MD5 digest seperate by new-line or spaces
  localfile - local file for verification, if not specified, no verification is done
		'''
		self.__slice_md5s = []
		if args:
			for arg in args:
				self.__slice_md5s.append(arg)
		elif self.__list_file_contents:
			digests = filter(None, self.__list_file_contents.split())
			for d in digests:
				self.__slice_md5s.append(d)
		else:
			perr("You MUST either provide the MD5s through the command line, "
				"or using the '-l' ('--list-file') switch to specify "
				"the 'listfile' to read MD5s from")
			return EArgument

		verify = self.__verify
		if localfile:
			self.__current_file = localfile
			self.__current_file_size = getfilesize(localfile)
		else:
			self.__current_file = '/dev/null' # Force no verify
			self.__verify = False

		result = self.__combine_file(get_pcs_path(remotefile))
		self.__verify = verify
		return result

	# no longer used
	def __get_meta_act(self, r, args):
		parse_ok = False
		j = r.json()
		if 'list' in j:
			lj = j['list']
			if len(lj) > 0:
				self.__remote_json = lj[0] # TODO: ugly patch
				# patch for inconsistency between 'list' and 'meta' json
				#self.__remote_json['md5'] = self.__remote_json['block_list'].strip('[]"')
				self.pd("self.__remote_json: {}".format(self.__remote_json))
				parse_ok = True
				return ENoError

		if not parse_ok:
			self.__remote_json = {}
			perr("Invalid JSON: {}\n{}".format(j, traceback.format_exc()))
			return EInvalidJson

	# no longer used
	def __get_meta(self, remotefile):
		pars = {
			'method' : 'meta',
			'path' : remotefile }
		return self.__get(
			pcsurl + 'file', pars,
			self.__get_meta_act)

	# NO LONGER IN USE
	def __downfile_act(self, r, args):
		rfile, offset = args
		with open(self.__current_file, 'r+b' if offset > 0 else 'wb') as f:
			if offset > 0:
				f.seek(offset)

			rsize = self.__remote_json['size']
			start_time = time.time()
			for chunk in r.iter_content(chunk_size = self.__dl_chunk_size):
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
					f.flush()
					pprgr(f.tell(), rsize, start_time)
					# https://stackoverflow.com/questions/7127075/what-exactly-the-pythons-file-flush-is-doing
					#os.fsync(f.fileno())

		# No exception above, then everything goes fine
		result = ENoError
		if self.__verify:
			self.__current_file_size = getfilesize(self.__current_file)
			result = self.__verify_current_file(self.__remote_json, False)

		if result == ENoError:
			self.pv("'{}' <== '{}' OK".format(self.__current_file, rfile))
		else:
			perr("'{}' <== '{}' FAILED".format(self.__current_file, rfile))

		return result

	def __downchunks_act(self, r, args):
		rfile, offset, rsize, start_time = args

		expectedBytes = self.__dl_chunk_size
		if rsize - offset < self.__dl_chunk_size:
			expectedBytes = rsize - offset

		if len(r.content) != expectedBytes:
			return ERequestFailed
		else:
			with open(self.__current_file, 'r+b' if offset > 0 else 'wb') as f:
				if offset > 0:
					f.seek(offset)

				f.write(r.content)
				pos = f.tell()
				pprgr(pos, rsize, start_time, existing = self.__existing_size)
				if pos - offset == expectedBytes:
					return ENoError
				else:
					return EFileWrite

	# requirment: self.__remote_json is already gotten
	def __downchunks(self, rfile, start):
		rsize = self.__remote_json['size']

		pars = {
			'method' : 'download',
			'path' : rfile }

		offset = start
		self.__existing_size = offset
		start_time = time.time()
		while True:
			nextoffset = offset + self.__dl_chunk_size
			if nextoffset < rsize:
				headers = { "Range" : "bytes={}-{}".format(
					offset, nextoffset - 1) }
			elif offset > 0:
				headers = { "Range" : "bytes={}-".format(offset) }
			elif rsize >= 1: # offset == 0
				# Fix chunked + gzip response,
				# seems we need to specify the Range for the first chunk as well:
				# https://github.com/houtianze/bypy/pull/161
				#headers = { "Range" : "bytes=0-".format(rsize - 1) }
				headers = { "Range" : "bytes=0-{}".format(rsize - 1) }
			else:
				headers = {}

			subresult = self.__get(dpcsurl + 'file', pars,
				self.__downchunks_act, (rfile, offset, rsize, start_time), headers = headers)
			if subresult != ENoError:
				return subresult

			if nextoffset < rsize:
				offset += self.__dl_chunk_size
			else:
				break

		# No exception above, then everything goes fine
		result = ENoError
		if self.__verify:
			self.__current_file_size = getfilesize(self.__current_file)
			result = self.__verify_current_file(self.__remote_json, False)

		if result == ENoError:
			self.pv("'{}' <== '{}' OK".format(self.__current_file, rfile))
		else:
			perr("'{}' <== '{}' FAILED".format(self.__current_file, rfile))

		return result

	def __downfile(self, remotefile, localfile):
		# TODO: this is a quick patch
		if not self.__shallinclude(localfile, remotefile, False):
			# since we are not going to download it, there is no error
			return ENoError

		result = ENoError
		rfile = remotefile

		self.__remote_json = {}
		self.pd("Downloading '{}' as '{}'".format(rfile, localfile))
		self.__current_file = localfile
		#if self.__verify or self.__resumedownload:
		self.pd("Getting info of remote file '{}' for later verification".format(rfile))
		result = self.__get_file_info(rfile)
		if result != ENoError:
			return result

		offset = 0
		self.pd("Checking if we already have the copy locally")
		if os.path.isfile(localfile):
			self.pd("Same-name local file '{}' exists, checking if contents match".format(localfile))
			self.__current_file_size = getfilesize(self.__current_file)
			if ENoError == self.__verify_current_file(self.__remote_json, False):
				self.pd("Same local file '{}' already exists, skip downloading".format(localfile))
				return ENoError
			else:
				if not self.shalloverwrite("Same-name locale file '{}' exists but is different, ".format(localfile) + \
						"do you want to overwrite it? [y/N]"):
					pinfo("Same-name local file '{}' exists but is different, skip downloading".format(localfile))
					return ENoError

			if self.__resumedownload and \
				self.__compare_size(self.__current_file_size, self.__remote_json) == 2:
				# revert back at least one download chunk
				pieces = self.__current_file_size // self.__dl_chunk_size
				if pieces > 1:
					offset = (pieces - 1) * self.__dl_chunk_size
		elif os.path.isdir(localfile):
			if not self.shalloverwrite("Same-name direcotry '{}' exists, ".format(localfile) + \
				"do you want to remove it? [y/N]"):
				pinfo("Same-name directory '{}' exists, skip downloading".format(localfile))
				return ENoError

			self.pv("Directory with the same name '{}' exists, removing ...".format(localfile))
			result = removedir(localfile, self.Verbose)
			if result == ENoError:
				self.pv("Removed")
			else:
				perr("Error removing the directory '{}'".format(localfile))
				return result

		ldir, file = os.path.split(localfile)
		if ldir and not os.path.exists(ldir):
			result = makedir(ldir, verbose = self.Verbose)
			if result != ENoError:
				perr("Fail to make directory '{}'".format(ldir))
				return result

		return self.__downchunks(rfile, offset)

	def downfile(self, remotefile, localpath = ''):
		''' Usage: downfile <remotefile> [localpath] - \
download a remote file.
  remotefile - remote file at Baidu Yun (after app root directory at Baidu Yun)
  localpath - local path.
    if it ends with '/' or '\\', it specifies the local direcotry
    if it specifies an existing directory, it is the local direcotry
    if not specified, the local direcotry is the current directory '.'
    otherwise, it specifies the local file name
To stream a file using downfile, you can use the 'mkfifo' trick with omxplayer etc.:
  mkfifo /tmp/omx
  bypy.py downfile <remotepath> /tmp/omx &
  omxplayer /tmp/omx
		'''
		localfile = localpath
		if not localpath:
			localfile = os.path.basename(remotefile)
		elif localpath[-1] == '\\' or \
			localpath[-1] == '/' or \
			os.path.isdir(localpath):
			#localfile = os.path.join(localpath, os.path.basename(remotefile))
			localfile = joinpath(localpath, os.path.basename(remotefile))
		else:
			localfile = localpath

		pcsrpath = get_pcs_path(remotefile)
		return self.__downfile(pcsrpath, localfile)

	def __stream_act_actual(self, r, args):
		pipe, csize = args
		with open(pipe, 'wb') as f:
			for chunk in r.iter_content(chunk_size = csize):
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
					f.flush()
					# https://stackoverflow.com/questions/7127075/what-exactly-the-pythons-file-flush-is-doing
					#os.fsync(f.fileno())

	def __streaming_act(self, r, args):
		return self.__stream_act_actual(r, args)

	# NOT WORKING YET
	def streaming(self, remotefile, localpipe, fmt = 'M3U8_480_360', chunk = 4 * OneM):
		''' Usage: stream <remotefile> <localpipe> [format] [chunk] - \
stream a video / audio file converted to M3U format at cloud side, to a pipe.
  remotefile - remote file at Baidu Yun (after app root directory at Baidu Yun)
  localpipe - the local pipe file to write to
  format - output video format (M3U8_320_240 | M3U8_480_224 | \
M3U8_480_360 | M3U8_640_480 | M3U8_854_480). Default: M3U8_480_360
  chunk - chunk (initial buffering) size for streaming (default: 4M)
To stream a file, you can use the 'mkfifo' trick with omxplayer etc.:
  mkfifo /tmp/omx
  bypy.py downfile <remotepath> /tmp/omx &
  omxplayer /tmp/omx
  *** NOT WORKING YET ****
		'''
		pars = {
			'method' : 'streaming',
			'path' : get_pcs_path(remotefile),
			'type' : fmt }

		return self.__get(pcsurl + 'file', pars,
			self.__streaming_act, (localpipe, chunk), stream = True)

	def __walk_remote_dir_act(self, r, args):
		dirjs, filejs = args
		j = r.json()
		#self.pd("Remote path content JSON: {}".format(j))
		paths = j['list']
		for path in paths:
			if path['isdir']:
				dirjs.append(path)
			else:
				filejs.append(path)

		return ENoError

	def __walk_remote_dir(self, remotepath, proceed, args = None):
		pars = {
			'method' : 'list',
			'path' : remotepath,
			'by' : 'name',
			'order' : 'asc' }

		# Python parameters are by-reference and mutable, so they are 'out' by default
		dirjs = []
		filejs = []
		result = self.__get(pcsurl + 'file', pars, self.__walk_remote_dir_act, (dirjs, filejs))
		self.pd("Remote dirs: {}".format(dirjs))
		self.pd("Remote files: {}".format(filejs))
		if result == ENoError:
			subresult = proceed(remotepath, dirjs, filejs, args)
			if subresult != ENoError:
				self.pd("Error: {} while proceeding remote path'{}'".format(
					subresult, remotepath))
				result = subresult # we continue
			for dirj in dirjs:
				subresult = self.__walk_remote_dir(dirj['path'], proceed, args)
				if subresult != ENoError:
					self.pd("Error: {} while sub-walking remote dirs'{}'".format(
						subresult, dirjs))
					result = subresult

		return result

	def __prepare_local_dir(self, localdir):
		result = ENoError
		if os.path.isfile(localdir):
			result = removefile(localdir, self.Verbose)

		if result == ENoError:
			if localdir and not os.path.exists(localdir):
				result = makedir(localdir, verbose = self.Verbose)

		return result

	def __proceed_downdir(self, remotepath, dirjs, filejs, args):
		result = ENoError
		rootrpath, localpath = args
		rlen = len(remotepath) + 1 # '+ 1' for the trailing '/', it bites.
		rootlen = len(rootrpath) + 1 # ditto

		result = self.__prepare_local_dir(localpath)
		if result != ENoError:
			perr("Fail to create prepare local directory '{}' for downloading, ABORT".format(localpath))
			return result

		for dirj in dirjs:
			reldir = dirj['path'][rlen:]
			#ldir = os.path.join(localpath, reldir)
			ldir = joinpath(localpath, reldir)
			result = self.__prepare_local_dir(ldir)
			if result != ENoError:
				perr("Fail to create prepare local directory '{}' for downloading, ABORT".format(ldir))
				return result

		for filej in filejs:
			rfile = filej['path']
			relfile = rfile[rootlen:]
			#lfile = os.path.join(localpath, relfile)
			lfile = joinpath(localpath, relfile)
			self.__downfile(rfile, lfile)

		return result

	def downdir(self, remotepath = None, localpath = None):
		''' Usage: downdir <remotedir> [localdir] - \
download a remote directory (recursively)
  remotedir - remote directory at Baidu Yun (after app root directory at Baidu Yun)
  localdir - local directory. if not specified, it is set to the current direcotry
		'''
		rpath = get_pcs_path(remotepath)
		lpath = localpath

		if not lpath:
			lpath = '' # empty string does it, no need '.'

		lpath = lpath.rstrip('/\\ ')

		return self.__walk_remote_dir(rpath, self.__proceed_downdir, (rpath, lpath))

	def __mkdir_act(self, r, args):
		if self.Verbose:
			j = r.json()
			pr("path, ctime, mtime, fs_id")
			pr("{path}, {ctime}, {mtime}, {fs_id}".format(**j))

		return ENoError

	def __mkdir(self, rpath, **kwargs):
		# TODO: this is a quick patch
		# the code still works because Baidu Yun doesn't require
		# parent directory to exist remotely to upload / create a file
		if not self.__shallinclude('.', rpath, True):
			return ENoError

		self.pd("Making remote directory '{}'".format(rpath))

		pars = {
			'method' : 'mkdir',
			'path' : rpath }
		return self.__post(pcsurl + 'file', pars, self.__mkdir_act, **kwargs)


	def mkdir(self, remotepath):
		''' Usage: mkdir <remotedir> - \
create a directory at Baidu Yun
  remotedir - the remote directory
'''
		rpath = get_pcs_path(remotepath)
		return self.__mkdir(rpath)

	def __move_act(self, r, args):
		j = r.json()
		list = j['extra']['list']
		fromp = list[0]['from']
		to = list[0]['to']
		self.pd("Remote move: '{}' =mm-> '{}' OK".format(fromp, to))

	# aliases
	def mv(self, fromp, to):
		return self.move(fromp, to)

	def rename(self, fromp, to):
		return self.move(fromp, to)

	def ren(self, fromp, to):
		return self.move(fromp, to)

	def move(self, fromp, to):
		''' Usage: move/mv/rename/ren <from> <to> - \
move a file / dir remotely at Baidu Yun
  from - source path (file / dir)
  to - destination path (file / dir)
		'''
		frompp = get_pcs_path(fromp)
		top = get_pcs_path(to)
		pars = {
			'method' : 'move',
			'from' : frompp,
			'to' : top }

		self.pd("Remote moving: '{}' =mm=> '{}'".format(fromp, to))
		return self.__post(pcsurl + 'file', pars, self.__move_act)

	def __copy_act(self, r, args):
		j = r.json()
		for list in j['extra']['list']:
			fromp = list['from']
			to = list['to']
			self.pd("Remote copy: '{}' =cc=> '{}' OK".format(fromp, to))

		return ENoError

	# alias
	def cp(self, fromp, to):
		return self.copy(fromp, to)

	def copy(self, fromp, to):
		''' Usage: copy/cp <from> <to> - \
copy a file / dir remotely at Baidu Yun
  from - source path (file / dir)
  to - destination path (file / dir)
		'''
		frompp = get_pcs_path(fromp)
		top = get_pcs_path(to)
		pars = {
			'method' : 'copy',
			'from' : frompp,
			'to' : top }

		self.pd("Remote copying '{}' =cc=> '{}'".format(frompp, top))
		return self.__post(pcsurl + 'file', pars, self.__copy_act)

	def __delete_act(self, r, args):
		rid = r.json()['request_id']
		if rid:
			pr("Deletion request '{}' OK".format(rid))
			pr("Usage 'list' command to confirm")

			return ENoError
		else:
			perr("Deletion failed")
			return EFailToDeleteFile

	def __delete(self, rpath):
		pars = {
			'method' : 'delete',
			'path' : rpath }

		self.pd("Remote deleting: '{}'".format(rpath))
		return self.__post(pcsurl + 'file', pars, self.__delete_act)

	# aliases
	def remove(self, remotepath):
		return self.delete(remotepath)

	def rm(self, remotepath):
		return self.delete(remotepath)

	def delete(self, remotepath):
		''' Usage: delete/remove/rm <remotepath> - \
delete a file / dir remotely at Baidu Yun
  remotepath - destination path (file / dir)
		'''
		rpath = get_pcs_path(remotepath)
		return self.__delete(rpath)

	def __search_act(self, r, args):
		print_pcs_list(r.json())
		return ENoError

	def search(self, keyword, remotepath = None, recursive = True):
		''' Usage: search <keyword> [remotepath] [recursive] - \
search for a file using keyword at Baidu Yun
  keyword - the keyword to search
  remotepath - remote path at Baidu Yun, if not specified, it's app's root directory
  resursive - search recursively or not. default is true
		'''
		rpath = get_pcs_path(remotepath)

		pars = {
			'method' : 'search',
			'path' : rpath,
			'wd' : keyword,
			're' : '1' if str2bool(recursive) else '0'}

		self.pd("Searching: '{}'".format(rpath))
		return self.__get(pcsurl + 'file', pars, self.__search_act)

	def __listrecycle_act(self, r, args):
		print_pcs_list(r.json())
		return ENoError

	def listrecycle(self, start = 0, limit = 1000):
		''' Usage: listrecycle [start] [limit] - \
list the recycle contents
  start - starting point, default: 0
  limit - maximum number of items to display. default: 1000
		'''
		pars = {
			'method' : 'listrecycle',
			'start' : str2int(start),
			'limit' : str2int(limit) }

		self.pd("Listing recycle '{}'")
		return self.__get(pcsurl + 'file', pars, self.__listrecycle_act)

	def __restore_act(self, r, args):
		path = args
		pr("'{}' found and restored".format(path))
		return ENoError

	def __restore_search_act(self, r, args):
		path = args
		flist = r.json()['list']
		fsid = None
		for f in flist:
			if os.path.normpath(f['path'].lower()) == os.path.normpath(path.lower()):
				fsid = f['fs_id']
				self.pd("fs_id for restoring '{}' found".format(fsid))
				break
		if fsid:
			pars = {
				'method' : 'restore',
				'fs_id' : fsid }
			return self.__post(pcsurl + 'file', pars, self.__restore_act, path)
		else:
			perr("'{}' not found in the recycle bin".format(path))

	def restore(self, remotepath):
		''' Usage: restore <remotepath> - \
restore a file from the recycle bin
  remotepath - the remote path to restore
		'''
		rpath = get_pcs_path(remotepath)
		# by default, only 1000 items, more than that sounds a bit crazy
		pars = {
			'method' : 'listrecycle' }

		self.pd("Searching for fs_id to restore")
		return self.__get(pcsurl + 'file', pars, self.__restore_search_act, rpath)

	def __proceed_local_gather(self, dirlen, walk):
		#names.sort()
		(dirpath, dirnames, filenames) = walk

		files = []
		for name in filenames:
			#fullname = os.path.join(dirpath, name)
			fullname = joinpath(dirpath, name)
			files.append((name, getfilesize(fullname), md5(fullname)))

		reldir = dirpath[dirlen:].replace('\\', '/')
		place = self.__local_dir_contents.get(reldir)
		for dir in dirnames:
			place.add(dir, PathDictTree('D'))
		for file in files:
			place.add(file[0], PathDictTree('F', size = file[1], md5 = file[2]))

		return ENoError

	def __gather_local_dir(self, dir):
		self.__local_dir_contents = PathDictTree()
		for walk in os.walk(dir, followlinks=self.__followlink):
			self.__proceed_local_gather(len(dir), walk)
		self.pd(self.__local_dir_contents)

	def __proceed_remote_gather(self, remotepath, dirjs, filejs, args = None):
		# NOTE: the '+ 1' is due to the trailing slash '/'
		# be careful about the trailing '/', it bit me once, bitterly
		rootrdir = args
		rootlen = len(rootrdir)
		dlen = len(remotepath) + 1
		for d in dirjs:
			self.__remote_dir_contents.get(remotepath[rootlen:]).add(
				d['path'][dlen:], PathDictTree('D', size = d['size'], md5 = binascii.unhexlify(d['md5'])))

		for f in filejs:
			self.__remote_dir_contents.get(remotepath[rootlen:]).add(
				f['path'][dlen:], PathDictTree('F', size = f['size'], md5 = binascii.unhexlify(f['md5'])))

		return ENoError

	def __gather_remote_dir(self, rdir):
		self.__remote_dir_contents = PathDictTree()
		self.__walk_remote_dir(rdir, self.__proceed_remote_gather, rdir)
		self.pd("---- Remote Dir Contents ---")
		self.pd(self.__remote_dir_contents)

	def __compare(self, remotedir = None, localdir = None):
		if not localdir:
			localdir = '.'

		self.pv("Gathering local directory ...")
		self.__gather_local_dir(localdir)
		self.pv("Done")
		self.pv("Gathering remote directory ...")
		self.__gather_remote_dir(remotedir)
		self.pv("Done")
		self.pv("Comparing ...")
		# list merge, where Python shines
		commonsame = []
		commondiff = []
		localonly = []
		remoteonly = []
		# http://stackoverflow.com/questions/1319338/combining-two-lists-and-removing-duplicates-without-removing-duplicates-in-orig
		lps = self.__local_dir_contents.allpath()
		rps = self.__remote_dir_contents.allpath()
		dps = set(rps) - set(lps)
		allpath = lps + list(dps)
		for p in allpath:
			local = self.__local_dir_contents.get(p)
			remote = self.__remote_dir_contents.get(p)
			if local is None: # must be in the remote dir, since p is from allpath
				remoteonly.append((remote.type, p))
			elif remote is None:
				localonly.append((local.type, p))
			else: # all here
				same = False
				if local.type == 'D' and remote.type == 'D':
					type = 'D'
					same = True
				elif local.type == 'F' and remote.type == 'F':
					type = 'F'
					if local.extra['size'] == remote.extra['size'] and \
						local.extra['md5'] == remote.extra['md5']:
						same = True
					else:
						same = False
				else:
					type = local.type + remote.type
					same = False

				if same:
					commonsame.append((type, p))
				else:
					commondiff.append((type, p))

		self.pv("Done")
		return commonsame, commondiff, localonly, remoteonly

	def compare(self, remotedir = None, localdir = None):
		''' Usage: compare [remotedir] [localdir] - \
compare the remote direcotry with the local directory
  remotedir - the remote directory at Baidu Yun (after app's direcotry). \
if not specified, it defaults to the root directory.
  localdir - the local directory, if not specified, it defaults to the current directory.
		'''
		same, diff, local, remote = self.__compare(get_pcs_path(remotedir), localdir)

		pr("==== Same files ===")
		for c in same:
			pr("{} - {}".format(c[0], c[1]))

		pr("==== Different files ===")
		for d in diff:
			pr("{} - {}".format(d[0], d[1]))

		pr("==== Local only ====")
		for l in local:
			pr("{} - {}".format(l[0], l[1]))

		pr("==== Remote only ====")
		for r in remote:
			pr("{} - {}".format(r[0], r[1]))

		pr("\nStatistics:")
		pr("--------------------------------")
		pr("Same: {}".format(len(same)));
		pr("Different: {}".format(len(diff)));
		pr("Local only: {}".format(len(local)));
		pr("Remote only: {}".format(len(remote)));

	def syncdown(self, remotedir = '', localdir = u'', deletelocal = False):
		''' Usage: syncdown [remotedir] [localdir] [deletelocal] - \
sync down from the remote direcotry to the local directory
  remotedir - the remote directory at Baidu Yun (after app's direcotry) to sync from. \
if not specified, it defaults to the root directory
  localdir - the local directory to sync to if not specified, it defaults to the current directory.
  deletelocal - delete local files that are not inside Baidu Yun direcotry, default is False
		'''
		result = ENoError
		rpath = get_pcs_path(remotedir)
		same, diff, local, remote = self.__compare(rpath, localdir)
		# clear the way
		for d in diff:
			t = d[0]
			p = d[1]
			#lcpath = os.path.join(localdir, p) # local complete path
			lcpath = joinpath(localdir, p) # local complete path
			rcpath = rpath + '/' + p # remote complete path
			if t == 'DF':
				result = removedir(lcpath, self.Verbose)
				subresult = self.__downfile(rcpath, lcpath)
				if subresult != ENoError:
					result = subresult
			elif t == 'FD':
				result = removefile(lcpath, self.Verbose)
				subresult = makedir(lcpath, verbose = self.Verbose)
				if subresult != ENoError:
					result = subresult
			else: # " t == 'F' " must be true
				result = self.__downfile(rcpath, lcpath)

		for r in remote:
			t = r[0]
			p = r[1]
			#lcpath = os.path.join(localdir, p) # local complete path
			lcpath = joinpath(localdir, p) # local complete path
			rcpath = rpath + '/' + p # remote complete path
			if t == 'F':
				subresult = self.__downfile(rcpath, lcpath)
				if subresult != ENoError:
					result = subresult
			else: # " t == 'D' " must be true
				subresult = makedir(lcpath, verbose = self.Verbose)
				if subresult != ENoError:
					result = subresult

		if str2bool(deletelocal):
			for l in local:
				# use os.path.isfile()/isdir() instead of l[0], because we need to check file/dir existence.
				# as we may have removed the parent dir previously during the iteration
				#p = os.path.join(localdir, l[1])
				p = joinpath(localdir, l[1])
				if os.path.isfile(p):
					subresult = removefile(p, self.Verbose)
					if subresult != ENoError:
						result = subresult
				elif os.path.isdir(p):
					subresult = removedir(p, self.Verbose)
					if subresult != ENoError:
						result = subresult

		return result

	def syncup(self, localdir = u'', remotedir = '', deleteremote = False):
		''' Usage: syncup [localdir] [remotedir] [deleteremote] - \
sync up from the local direcotry to the remote directory
  localdir - the local directory to sync from if not specified, it defaults to the current directory.
  remotedir - the remote directory at Baidu Yun (after app's direcotry) to sync to. \
if not specified, it defaults to the root directory
  deleteremote - delete remote files that are not inside the local direcotry, default is False
		'''
		result = ENoError
		rpath = get_pcs_path(remotedir)
		#rpartialdir = remotedir.rstrip('/ ')
		same, diff, local, remote = self.__compare(rpath, localdir)
		# clear the way
		for d in diff:
			t = d[0] # type
			p = d[1] # path
			#lcpath = os.path.join(localdir, p) # local complete path
			lcpath = joinpath(localdir, p) # local complete path
			rcpath = rpath + '/' + p # remote complete path
			if self.shalloverwrite("Do you want to overwrite '{}' at Baidu Yun? [y/N]".format(p)):
				# this path is before get_pcs_path() since delete() expects so.
				#result = self.delete(rpartialdir + '/' + p)
				#result = self.__delete(rcpath)
				self.pd("diff type: {}".format(t))
				self.__isrev = True
				if t != 'F':
					result = self.move(remotedir + '/' + p, remotedir + '/' + p + '.moved_by_bypy.' + time.strftime("%Y%m%d%H%M%S"))
					self.__isrev = False
				if t == 'F' or t == 'FD':
					subresult = self.__upload_file(lcpath, rcpath)
					if subresult != ENoError:
						result = subresult
				else: # " t == 'DF' " must be true
					subresult = self.__mkdir(rcpath)
					if subresult != ENoError:
						result = subresult
			else:
				pinfo("Uploading '{}' skipped".format(lcpath))

		for l in local:
			t = l[0]
			p = l[1]
			#lcpath = os.path.join(localdir, p) # local complete path
			lcpath = joinpath(localdir, p) # local complete path
			rcpath = rpath + '/' + p # remote complete path
			self.pd("local type: {}".format(t))
			self.__isrev = False
			if t == 'F':
				subresult = self.__upload_file(lcpath, rcpath)
				if subresult != ENoError:
					result = subresult
			else: # " t == 'D' " must be true
				subresult = self.__mkdir(rcpath)
				if subresult != ENoError:
					result = subresult

		if str2bool(deleteremote):
			# i think the list is built top-down, so directories appearing later are either
			# children or another set of directories
			pp = '\\' # previous path, setting to '\\' make sure it won't be found in the first step
			for r in remote:
				#p = rpartialdir + '/' + r[1]
				p = rpath + '/' + r[1]
				if 0 != p.find(pp): # another path
					#subresult = self.delete(p)
					subresult = self.__delete(p)
					if subresult != ENoError:
						result = subresult
				pp = p

		return result

	def dumpcache(self):
		''' Usage: dumpcache - display file hash cache'''
		if cached.cacheloaded:
			#pprint.pprint(cached.cache)
			MyPrettyPrinter().pprint(cached.cache)
			return ENoError
		else:
			perr("Cache not loaded.")
			return ECacheNotLoaded

	def cleancache(self):
		''' Usage: cleancache - remove invalid entries from hash cache file'''
		if os.path.exists(HashCachePath):
			try:
				# backup first
				backup = HashCachePath + '.lastclean'
				shutil.copy(HashCachePath, backup)
				self.pd("Hash Cache file '{}' backed up as '{}".format(
					HashCachePath, backup))
				cached.cleancache()
				return ENoError
			except:
				perr("Exception:\n{}".format(traceback.format_exc()))
				return EException
		else:
			return EFileNotFound

OriginalFloatTime = True

def onexit(retcode = ENoError):
	# saving is the most important
	# we save, but don't clean, why?
	# think about unmount path, moved files,
	# once we discard the information, they are gone.
	# so unless the user specifically request a clean,
	# we don't act too smart.
	#cached.cleancache()
	cached.savecache()
	os.stat_float_times(OriginalFloatTime)
	# if we flush() on Ctrl-C, we get
	# IOError: [Errno 32] Broken pipe
	sys.stdout.flush()
	sys.exit(retcode)

def sighandler(signum, frame):
	pr("Signal {} received, Abort".format(signum))
	pr("Stack:\n")
	traceback.print_stack(frame)
	onexit(EAbort)

def main(argv=None): # IGNORE:C0111
	''' Main Entry '''

	# *** IMPORTANT ***
	# We must set this in order for cache to work,
	# as we need to get integer file mtime, which is used as the key of Hash Cache
	global OriginalFloatTime
	OriginalFloatTime = os.stat_float_times()
	os.stat_float_times(False)
	# --- IMPORTANT ---

	result = ENoError
	if argv is None:
		argv = sys.argv
	else:
		sys.argv.extend(argv)

	if sys.platform == 'win32':
		#signal.signal(signal.CTRL_C_EVENT, sighandler)
		#signal.signal(signal.CTRL_BREAK_EVENT, sighandler)
		# bug, see: http://bugs.python.org/issue9524
		pass
	else:
		signal.signal(signal.SIGBUS, sighandler)
		signal.signal(signal.SIGHUP, sighandler)
		# https://stackoverflow.com/questions/108183/how-to-prevent-sigpipes-or-handle-them-properly
		signal.signal(signal.SIGPIPE, signal.SIG_IGN)
		signal.signal(signal.SIGQUIT, sighandler)
		signal.signal(signal.SIGSYS, sighandler)

	signal.signal(signal.SIGABRT, sighandler)
	signal.signal(signal.SIGFPE, sighandler)
	signal.signal(signal.SIGILL, sighandler)
	signal.signal(signal.SIGINT, sighandler)
	signal.signal(signal.SIGSEGV, sighandler)
	signal.signal(signal.SIGTERM, sighandler)

	#program_name = os.path.basename(sys.argv[0])
	program_version = "v%s" % __version__
	program_version_message = '%%(prog)s %s' % (program_version )
	shortdesc = __import__('__main__').__doc__.split("\n")[1]
	shortdesc = program_version_message + ' -- ' + shortdesc.split('--')[1]
	program_shortdesc = shortdesc
	program_longdesc = __import__('__main__').__doc__.split("---\n")[1]

	try:
		# +++ DEPRECATED +++
		# check if ApiKey, SecretKey and AppPcsPath are correctly specified.
		#if not ApiKey or not SecretKey or not AppPcsPath:
		if False:
			ApiNotConfigured = '''
*** ABORT *** Baidu API not properly configured

- Please go to 'http://developer.baidu.com/' and create an application.
- Get the ApiKey, SecretKey and configure the App Path (default: '/apps/bypy/')
- Update the corresponding variables at the beginning of this file, \
right after the '# PCS configuration constants' comment.
- Try to run this program again

*** ABORT ***
'''
			pr(ApiNotConfigured)
			return EApiNotConfigured
		# --- DEPRECATED ---

		# setup argument parser
		epilog = "Commands:\n"
		summary = []
		for k, v in ByPy.__dict__.items():
			if callable(v) and v.__doc__:
				help = v.__doc__.strip()
				pos = help.find(ByPy.HelpMarker)
				if pos != -1:
					pos_body = pos + len(ByPy.HelpMarker)
					helpbody = help[pos_body:]
					helpline = helpbody.split('\n')[0].strip() + '\n'
					if helpline.find('help') == 0:
						summary.insert(0, helpline)
					else:
						summary.append(helpline)

		remaining = summary[1:]
		remaining.sort()
		summary = [summary[0]] + remaining
		epilog += ''.join(summary)

		parser = ArgumentParser(
			description=program_shortdesc + '\n\n' + program_longdesc,
			formatter_class=RawDescriptionHelpFormatter, epilog=epilog)

		# special
		parser.add_argument("--TESTRUN", dest="TESTRUN", action="store_true", help="Perform python doctest")
		parser.add_argument("--PROFILE", dest="PROFILE", action="store_true", help="Profile the code")

		# help, version, program information etc
		parser.add_argument('-V', '--version', action='version', version=program_version_message)
		#parser.add_argument(dest="paths", help="paths to folder(s) with source file(s) [default: %(default)s]", metavar="path", nargs='+')

		# debug, logging
		parser.add_argument("-d", "--debug", dest="debug", action="count", default=0, help="enable debugging & logging [default: %(default)s]")
		parser.add_argument("-v", "--verbose", dest="verbose", default=0, action="count", help="set verbosity level [default: %(default)s]")

		# program tunning, configration (those will be passed to class ByPy)
		parser.add_argument("-r", "--retry", dest="retry", default=5, help="number of retry attempts on network error [default: %(default)i times]")
		parser.add_argument("-q", "--quit-when-fail", dest="quit", default=False, help="quit when maximum number of retry failed [default: %(default)s]")
		parser.add_argument("-t", "--timeout", dest="timeout", default=60, help="network timeout in seconds [default: %(default)s]")
		parser.add_argument("-s", "--slice", dest="slice", default=DefaultSliceSize, help="size of file upload slice (can use '1024', '2k', '3MB', etc) [default: {} MB]".format(DefaultSliceInMB))
		parser.add_argument("--chunk", dest="chunk", default=DefaultDlChunkSize, help="size of file download chunk (can use '1024', '2k', '3MB', etc) [default: {} MB]".format(DefaultDlChunkSize / OneM))
		parser.add_argument("-e", "--verify", dest="verify", action="store_true", default=False, help="Verify upload / download [default : %(default)s]")
		parser.add_argument("-f", "--force-hash", dest="forcehash", action="store_true", help="force file MD5 / CRC32 calculation instead of using cached value")
		parser.add_argument("-l", "--list-file", dest="listfile", default=None, help="input list file (used by some of the commands only [default: %(default)s]")
		parser.add_argument("--resume-download", dest="resumedl", default=True, help="resume instead of restarting when downloading if local file already exists [default: %(default)s]")
		parser.add_argument("--include-regex", dest="incregex", default='', help="regular expression of files to include. if not specified (default), everything is included. for download, the regex applies to the remote files; for upload, the regex applies to the local files. to exclude files, think about your regex, some tips here: https://stackoverflow.com/questions/406230/regular-expression-to-match-string-not-containing-a-word [default: %(default)s]")
		parser.add_argument("--on-dup", dest="ondup", default='overwrite', help="what to do when the same file / folder exists in the destination: 'overwrite', 'skip', 'prompt' [default: %(default)s]")
		parser.add_argument("--no-symlink", dest="followlink", action="store_false", help="DON'T follow symbol links when uploading / syncing up")
		parser.add_argument(DisableSslCheckOption, dest="checkssl", action="store_false", help="DON'T verify host SSL cerificate")
		parser.add_argument(CaCertsOption, dest="cacerts", help="Specify the path for CA Bundle [default: %(default)s]")
		parser.add_argument("--mirror", dest="mirror", default=None, help="Specify the PCS mirror (e.g. bj.baidupcs.com. Open 'https://pcs.baidu.com/rest/2.0/pcs/manage?method=listhost' to get the list) to use.")
		parser.add_argument("--rapid-upload-only", dest="rapiduploadonly", action="store_true", help="Only upload large files that can be rapidly uploaded")

		# action
		parser.add_argument(CleanOptionShort, CleanOptionLong, dest="clean", action="count", default=0, help="1: clean settings (remove the token file) 2: clean settings and hash cache [default: %(default)s]")

		# the MAIN parameter - what command to perform
		parser.add_argument("command", nargs='*', help = "operations (quota / list)")

		# Process arguments
		args = parser.parse_args()

		if args.mirror:
			global pcsurl
			global cpcsurl
			global dpcsurl
			pcsurl = re.sub(r'//.*?/', '//' + args.mirror + '/', pcsurl)
			cpcsurl = pcsurl
			dpcsurl = pcsurl

		try:
			slice_size = interpret_size(args.slice)
		except (ValueError, KeyError):
			pr("Error: Invalid slice size specified '{}'".format(args.slice))
			return EArgument
		try:
			chunk_size = interpret_size(args.chunk)
		except (ValueError, KeyError):
			pr("Error: Invalid slice size specified '{}'".format(args.slice))
			return EArgument

		if args.TESTRUN:
			return TestRun()

		if args.PROFILE:
			return Profile()

		pr("Token file: '{}'".format(TokenFilePath))
		pr("Hash Cache file: '{}'".format(HashCachePath))
		pr("App root path at Baidu Yun '{}'".format(AppPcsPath))
		pr("sys.stdin.encoding = {}".format(sys.stdin.encoding))
		pr("sys.stdout.encoding = {}".format(sys.stdout.encoding))
		pr("sys.stderr.encoding = {}".format(sys.stderr.encoding))

		if args.verbose > 0:
			pr("Verbose level = {}".format(args.verbose))
			pr("Debug = {}".format(args.debug))

		pr("----\n")

		if os.path.exists(HashCachePath):
			cachesize = getfilesize(HashCachePath)
			if cachesize > 10 * OneM or cachesize == -1:
				pr((
"*** WARNING ***\n"
"Hash Cache file '{0}' is very large ({1}).\n"
"This may affect program's performance (high memory consumption).\n"
"You can first try to run 'bypy.py cleancache' to slim the file.\n"
"But if the file size won't reduce (this warning persists),"
" you may consider deleting / moving the Hash Cache file '{0}'\n"
"*** WARNING ***\n\n\n").format(HashCachePath, human_size(cachesize)))

		if args.clean >= 1:
			result = removefile(TokenFilePath, args.verbose)
			if result == ENoError:
				pr("Token file '{}' removed. You need to re-authorize "
					"the application upon next run".format(TokenFilePath))
			else:
				perr("Failed to remove the token file '{}'".format(TokenFilePath))
				perr("You need to remove it manually")

			if args.clean >= 2:
				subresult = os.remove(HashCachePath)
				if subresult == ENoError:
					pr("Hash Cache File '{}' removed.".format(HashCachePath))
				else:
					perr("Failed to remove the Hash Cache File '{}'".format(HashCachePath))
					perr("You need to remove it manually")
					result = subresult

			return result

		if len(args.command) <= 0 or \
			(len(args.command) == 1 and args.command[0].lower() == 'help'):
			parser.print_help()
			return EArgument
		elif args.command[0] in ByPy.__dict__: # dir(ByPy), dir(by)
			timeout = None
			if args.timeout:
				timeout = float(args.timeout)

			cached.usecache = not args.forcehash
			cached.verbose = args.verbose
			cached.debug = args.debug
			cached.loadcache()

			by = ByPy(slice_size = slice_size, dl_chunk_size = chunk_size,
					verify = args.verify,
					retry = int(args.retry), timeout = timeout,
					quit_when_fail = args.quit,
					listfile = args.listfile,
					resumedownload = args.resumedl,
					incregex = args.incregex,
					ondup = args.ondup,
					followlink = args.followlink,
					checkssl = args.checkssl,
					cacerts = args.cacerts,
					rapiduploadonly = args.rapiduploadonly,
					verbose = args.verbose, debug = args.debug)
			uargs = []
			for arg in args.command[1:]:
				uargs.append(unicode(arg, SystemEncoding))
			result = getattr(by, args.command[0])(*uargs)
		else:
			pr("Error: Command '{}' not available.".format(args.command[0]))
			parser.print_help()
			return EParameter

	except KeyboardInterrupt:
		### handle keyboard interrupt ###
		pr("KeyboardInterrupt")
		pr("Abort")
	except Exception:
		perr("Exception occurred:")
		pr(traceback.format_exc())
		pr("Abort")
		# raise

	onexit(result)

def TestRun():
	import doctest
	doctest.testmod()
	return ENoError

def Profile():
	import cProfile
	import pstats
	profile_filename = 'bypy_profile.txt'
	cProfile.run('main()', profile_filename)
	statsfile = open("profile_stats.txt", "wb")
	p = pstats.Stats(profile_filename, stream=statsfile)
	stats = p.strip_dirs().sort_stats('cumulative')
	stats.print_stats()
	statsfile.close()
	sys.exit(ENoError)

def unused():
	''' just prevent unused warnings '''
	inspect.stack()

if __name__ == "__main__":
	main()

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
