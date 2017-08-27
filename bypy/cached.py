#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import os
import time
import io
import hashlib
import binascii

from . import const
from . import gvar
from . import util
from .util import (
	pdbg, pinfo, perr,
	getfilesize, getfilemtime_int,
	joinpath, formatex,
	jsonload, jsondump,
	removepath)

pr = util.pr

def convertbincache(info, key):
	if key in info:
		binhash = info[key]
		strhash = binascii.hexlify(binhash)
		info[key] = strhash

# in Pickle, i saved the hash (MD5, CRC32) in binary format (bytes)
# now i need to pay the price to save them using string format ...
# TODO: Rename
def stringifypickle(picklecache):
	for absdir in picklecache:
		entry = picklecache[absdir]
		for file in entry:
			info = entry[file]
			# 'crc32' is still stored as int (long),
			# as it's supported by JSON, and can't be hexlified
			#for key in ['md5', 'slice_md5', 'crc32']:
			for key in ['md5', 'slice_md5']:
				convertbincache(info, key)

# there is room for more space optimization (like using the tree structure),
# but it's not added at the moment. for now, it's just simple pickle.
# SQLite might be better for portability
# NOTE: file names are case-sensitive
class cached(object):
	''' simple decorator for hash caching (using pickle) '''
	usecache = True
	verbose = False
	debug = False
	hashcachepath = const.HashCachePath
	cache = {}
	cacheloaded = False
	dirty = False
	# we don't do cache loading / unloading here because it's an decorator,
	# and probably multiple instances are created for md5, crc32, etc
	# it's a bit complex, and i thus don't have the confidence to do it in ctor/dtor
	def __init__(self, f):
		super(cached, self).__init__()
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
					and info['mtime'] == getfilemtime_int(path) \
					and self.f.__name__ in info \
					and cached.usecache:
					result = info[self.f.__name__]
					if cached.debug:
						pdbg("Cache hit for file '{}',\n{}: {}\nsize: {}\nmtime: {}".format(
							path, self.f.__name__,
							result,
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
		info['mtime'] = getfilemtime_int(path)
		info[self.f.__name__] = value
		if cached.debug:
			situation = "Storing cache"
			if cached.usecache:
				situation = "Cache miss"
			pdbg((situation + " for file '{}',\n{}: {}\nsize: {}\nmtime: {}").format(
				path, self.f.__name__,
				value,
				info['size'], info['mtime']))

		# periodically save to prevent loss in case of system crash
		now = time.time()
		if now - gvar.last_cache_save >= const.CacheSavePeriodInSec:
			cached.savecache()
			gvar.last_cache_save = now
		if cached.debug:
			pdbg("Periodically saving Hash Cash")

	# merge the from 'fromc' cache into the 'to' cache.
	# 'keepto':
	#  - True to keep the entry in 'to' cache when conflicting
	#  - False to keep the entry from 'fromc' cache
	# return number of conflict entries found
	@staticmethod
	def mergeinto(fromc, to, keepto = True):
		conflicts = 0
		for absdir in fromc:
			entry = fromc[absdir]
			if not absdir in to:
				to[absdir] = {}
			toentry = to[absdir]
			for file in entry:
				if file in toentry:
					if cached.debug:
						msg = "Cache merge conflict for: '{}/{}', {}: {}.".format(absdir, file,
							"Keeping the destination value" if keepto else
							"Using the source value",
							toentry[file] if keepto else entry[file])
						pdbg(msg)
					if not keepto:
						toentry[file] = entry[file]
					conflicts += 1
				else:
					toentry[file] = entry[file]

		return conflicts

	@staticmethod
	def ishexchar(c):
		return (c >= '0' and c <= '9') or (c >= 'a' and c <= 'f') or (c >= 'A' and c <= 'F')

	# pay the history debt ..., hashes were in binary format (bytes) in pickle
	@staticmethod
	def isbincache(cache):
		for absdir in cache:
			entry = cache[absdir]
			for file in entry:
				info = entry[file]
				if 'md5' in info:
					md5 = info['md5']
					for c in md5:
						if not cached.ishexchar(c):
							return True
		return False

	@staticmethod
	def loadcache(existingcache = {}):
		# load cache even we don't use cached hash values,
		# because we will save (possibly updated) and hash values
		if not cached.cacheloaded: # no double-loading
			if cached.verbose:
				pr("Loading Hash Cache File '{}'...".format(cached.hashcachepath))

			if os.path.exists(cached.hashcachepath):
				try:
					cached.cache = jsonload(cached.hashcachepath)
					# pay the history debt ...
					# TODO: Remove some time later when no-body uses the old bin format cache
					if cached.isbincache(cached.cache):
						pinfo("ONE TIME conversion for binary format Hash Cache ...")
						stringifypickle(cached.cache)
						pinfo("ONE TIME conversion finished")
					if existingcache: # not empty
						if cached.verbose:
							pinfo("Merging with existing Hash Cache")
						cached.mergeinto(existingcache, cached.cache)
					cached.cacheloaded = True
					if cached.verbose:
						pr("Hash Cache File loaded.")
				except (EOFError, TypeError, ValueError) as ex:
					perr("Fail to load the Hash Cache, no caching.\n{}".format(formatex(ex)))
					cached.cache = existingcache
			else:
				if cached.verbose:
					pr("Hash Cache File '{}' not found, no caching".format(cached.hashcachepath))
		else:
			if cached.verbose:
				pr("Not loading Hash Cache since 'cacheloaded' is '{}'".format(cached.cacheloaded))

		return cached.cacheloaded

	@staticmethod
	def savecache(force_saving = False):
		saved = False
		# even if we were unable to load the cache, we still save it.
		if cached.dirty or force_saving:
			if cached.verbose:
				pr("Saving Hash Cache...")
			try:
				jsondump(cached.cache, cached.hashcachepath)
				if cached.verbose:
					pr("Hash Cache saved.")
				saved = True
				cached.dirty = False
			except Exception as ex:
				perr("Failed to save Hash Cache.\n{}".format(formatex(ex)))
		else:
			if cached.verbose:
				pr("Skip saving Hash Cache since it has not been updated.")

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

	@staticmethod
	def remove(path):
		def notfound():
			pdbg("Failed to delete cache: Path '{}' not found in cache.".format(path))

		dir, file = os.path.split(path)
		absdir = os.path.abspath(dir)
		if absdir in cached.cache:
			entry = cached.cache[absdir]
			if file in entry:
				del entry[file]
				pdbg("Cache for '{}' removed.".format(path))
				if not entry:
					del cached.cache[absdir]
					pdbg("Empty directory '{}' in cache also removed.".format(absdir))
			else:
				notfound()
		else:
			notfound()

	@staticmethod
	def remove_path_and_cache(path):
		result = removepath(path)
		if result == const.ENoError and os.path.isfile(path):
			cached.remove(path)
		return result

@cached
def md5(filename, slice = const.OneM):
	m = hashlib.md5()
	with io.open(filename, 'rb') as f:
		while True:
			buf = f.read(slice)
			if buf:
				m.update(buf)
			else:
				break

	return m.hexdigest()

# slice md5 for baidu rapidupload
@cached
def slice_md5(filename):
	m = hashlib.md5()
	with io.open(filename, 'rb') as f:
		buf = f.read(256 * const.OneK)
		m.update(buf)

	return m.hexdigest()

@cached
def crc32(filename, slice = const.OneM):
	with io.open(filename, 'rb') as f:
		buf = f.read(slice)
		crc = binascii.crc32(buf)
		while True:
			buf = f.read(slice)
			if buf:
				crc = binascii.crc32(buf, crc)
			else:
				break

	return crc & 0xffffffff

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
