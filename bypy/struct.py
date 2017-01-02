#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from .util import iswindows

# tree represented using dictionary, (Obsolete: OrderedDict no longer required)
# NOTE: No own-name is kept, so the caller needs to keep track of that
# NOTE: Case-sensitive, as I don't want to waste time wrapping up a case-insensitive one
# single-linked-list, no backwards travelling capability
class PathDictTree(dict):
	def __init__(self, type = 'D', **kwargs):
		super(PathDictTree, self).__init__()
		self.type = type
		self.extra = {}
		for k, v in kwargs.items():
			self.extra[k] = v

	def __str__(self):
		return self.__str('')

	def __str(self, prefix):
		result = ''
		for k, v in self.items():
			result += "{} - {}/{} - size: {} - md5: {} \n".format(
				v.type, prefix, k,
				v.extra['size'] if 'size' in v.extra else '',
				v.extra['md5'] if 'md5' in v.extra else '')

		for k, v in self.items():
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
			if iswindows():
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

