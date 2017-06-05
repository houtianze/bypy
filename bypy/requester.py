#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys
import logging
import json

from functools import partial

import requests

# unify Python 2 and 3
if sys.version_info[0] == 2:
	import urllib2 as ulr
	import httplib
	import cPickle as pickle
	pickleload = pickle.load
elif sys.version_info[0] == 3:
	import urllib.request as ulr
	import http.client as httplib
	import pickle
	unicode = str
	basestring = str
	long = int
	raw_input = input
	pickleload = partial(pickle.load, encoding="bytes")

from . import const
from .printer import (pdbg, perr)
from .util import (formatex)

# the object returned from your Requester should have the following members
# may be used for mocking / testing in the future
class RequesterResponse(object):
	def __init__(self, url, text, status_code):
		super(RequesterResponse, self).__init__()
		self.text = text
		self.url = url
		self.status_code = status_code
		self.headers = {}

	def json(self):
		json.loads(self.text)

# NOT in use, replacing the requests library is not trivial
class UrllibRequester(object):
	def __init__(self):
		super(UrllibRequester, self).__init__()

	@classmethod
	def setoptions(cls, options):
		pass

	@classmethod
	def request(cls, method, url, **kwargs):
		"""
		:type method: str
		"""
		methodupper = method.upper()
		hasdata = 'data' in kwargs
		if methodupper == 'GET':
			if hasdata:
				print("ERROR: Can't do HTTP GET when the 'data' parameter presents")
				assert False
			resp = ulr.urlopen(url, **kwargs)
		elif methodupper == 'POST':
			if hasdata:
				resp = ulr.urlopen(url, **kwargs)
			else:
				resp = ulr.urlopen(url, data = '', **kwargs)
		else:
			raise NotImplementedError()

		return resp

	@classmethod
	def set_logging_level(cls, level):
		pass

	@classmethod
	def disable_warnings(cls, debug):
		pass

# extracting this class out would make it easier to test / mock
class RequestsRequester(object):
	options = {}

	def __init__(self):
		super(RequestsRequester, self).__init__()

	@classmethod
	def setoptions(cls, options):
		cls.options = options

	@classmethod
	def request(cls, method, url, **kwargs):
		for k,v in cls.options.items():
			kwargs.setdefault(k, v)
		return requests.request(method, url, **kwargs)

	@classmethod
	def disable_warnings(cls, debug):
		failures = 0
		exmsg = ''
		try:
			import requests.packages.urllib3 as ul3
			if debug:
				pdbg("Using requests.packages.urllib3 to disable warnings")
			#ul3.disable_warnings(ul3.exceptions.InsecureRequestWarning)
			#ul3.disable_warnings(ul3.exceptions.InsecurePlatformWarning)
			ul3.disable_warnings()
		except Exception as ex:
			failures += 1
			exmsg += formatex(ex) + '-' * 64 + '\n'

		# i don't know why under Ubuntu, 'pip install requests'
		# doesn't install the requests.packages.* packages
		try:
			import urllib3 as ul3
			if debug:
				pdbg("Using urllib3 to disable warnings")
			ul3.disable_warnings()
		except Exception as ex:
			failures += 1
			exmsg += formatex(ex)

		if failures >= 2:
			perr("Failed to disable warnings for Urllib3.\n"
				"Possibly the requests library is out of date?\n"
				"You can upgrade it by running '{}'.\nExceptions:\n{}".format(
					const.PipUpgradeCommand, exmsg))

	# only if user specifies '-ddd' or more 'd's, the following
	# debugging information will be shown, as it's very talkative.
	# it enables debugging at httplib level (requests->urllib3->httplib)
	# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
	# the only thing missing will be the response.body which is not logged.
	@classmethod
	def set_logging_level(cls, level):
		if level >= 3:
			httplib.HTTPConnection.debuglevel = 1
			logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
			logging.getLogger().setLevel(logging.DEBUG)
			requests_log = logging.getLogger("requests.packages.urllib3")
			requests_log.setLevel(logging.DEBUG)
			requests_log.propagate = True


