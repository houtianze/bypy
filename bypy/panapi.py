#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division


import os
import io

from . import const
from . import gvar
from .util import (
	pr, perr, formatex,
	ls_type, ls_time, get_pcs_path)
from .bypy import ByPy

# put all xslidian's bduss extensions here, i never tried out them though
class PanAPI(ByPy):
	IEBDUSSExpired = -6
	# Does https work? if so, we should always use https
	#PanAPIUrl = 'http://pan.baidu.com/api/'
	PanAPIUrl = 'https://pan.baidu.com/api/'

	def __init__(self, **kwargs):
		super(PanAPI, self).__init__(**kwargs)
		self.__bdusspath= self.__configdir + os.sep + 'bypy.bduss'
		self.__bduss = ''
		if not self.__load_local_bduss():
			self.pv("BDUSS not found at '{}'.".format(self.__bdusspath))

	def __load_local_bduss(self):
		try:
			with io.open(self.__bdusspath, 'rb') as infile:
				self.__bduss = infile.readline().strip()
				self.pd("BDUSS loaded: {}".format(self.__bduss))
				self.__cookies = {'BDUSS': self.__bduss}
				return True
		except IOError as ex:
			self.pd("Error loading BDUSS:")
			self.pd(formatex(ex))
			return False

	# overriding
	def __handle_more_response_error(self, r, sc, ec, act, actargs):
		result = const.ERequestFailed

		# user not exists
		if ec == 31045: # and sc == 403:
			self.pd("BDUSS has expired")
			result = PanAPI.IEBDUSSExpired
		# topath already exists
		elif ec == 31196: # and sc == 403:
			self.pd("UnzipCopy destination already exists.")
			result = act(r, actargs)
		# file copy failed
		elif ec == 31197: # and sc == 503:
			self.pd("File copy failed")
			result = act(r, actargs)
		# file size exceeds limit
		elif ec == 31199: # and sc == 403:
			result = act(r, actargs)

		return result

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
				return const.ERequestFailed
			elif 'list' in j:
				for e in j['list']:
					pr("{}\t{}\t{}".format(ls_type(e['isdir'] == 1), e['file_name'], e['size']))
		return const.ENoError

	def __panapi_unzip_file(self, rpath, subpath, start, limit):
		pars = {
			'path' : rpath,
			'start' : start,
			'limit' : limit,
			'subpath' : '/' + subpath.strip('/') }

		self.pd("Unzip request: {}".format(pars))
		return self.__get(PanAPI.PanAPIUrl + 'unzip?app_id=250528',
						  pars, self.__panapi_unzip_file_act, cookies = self.__cookies, actargs = pars )

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
			self.pv("Remote extract: '{}#{}' =xx=> '{}' OK.".format(args['path'], args['subpath'], j['path']))
			return const.ENoError
		elif 'error_code' in j:
			if j['error_code'] == 31196:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. File already exists.".format(args['path'], args['subpath'], args['topath']))
				subresult = self.__delete(args['topath'])
				if subresult == const.ENoError:
					return self.__panapi_unzipcopy_file(args['path'], args['subpath'], args['topath'])
				else:
					return const.ERequestFailed
			elif j['error_code'] == 31199:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. File too large.".format(args['path'], args['subpath'], args['topath']))
				return const.EMaxRetry
			else:
				perr("Remote extract: '{}#{}' =xx=> '{}' FAILED. Unknown error {}: {}.".format(args['path'], args['subpath'], args['topath'], j['error_code'], j['error_msg']))
		return const.EMaxRetry

	def __panapi_unzipcopy_file(self, rpath, subpath, topath):
		pars = {
			'app_id' : 250528,
			'method' : 'unzipcopy',
			'path' : rpath,
			'subpath' : '/' + subpath.strip('/'),
			'topath' : topath }

		self.pd("UnzipCopy request: {}".format(pars))
		return self.__get(gvar.pcsurl + 'file',
						  pars, self.__panapi_unzipcopy_file_act, addtoken = False, cookies = self.__cookies, actargs = pars )

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
					pr("{}\t{}\t{}".format(e['revision'], e['size'], ls_time(e['revision'] // 1e6)))
			return const.ENoError
		if j['errno'] == -6: # invalid BDUSS
			pr("BDUSS has expired.")
			return PanAPI.IEBDUSSExpired
		if j['errno'] == -9:
			pr("File '{}' not exists.".format(args['path']))
			return const.EFileNotFound
		return const.ENoError

	def __panapi_revision_list(self, rpath):
		pars = {
			'path' : rpath,
			'desc' : 1 }

		self.pd("RevisionList request: {}".format(pars))
		return self.__post(PanAPI.PanAPIUrl + 'revision/list?app_id=250528',
						   {}, self.__panapi_revision_list_act, pars, data = pars, cookies = self.__cookies )

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
			return const.ENoError
		if j['errno'] == -6: # invalid BDUSS
			pr("BDUSS has expired.")
			return PanAPI.IEBDUSSExpired
		if j['errno'] == -9:
			pr("File '{}' not exists.".format(args['path']))
			return const.EFileNotFound
		if j['errno'] == 10:
			pr("Reverting '{}' in process...".format(args['path']))
			return const.ERequestFailed
		return const.ENoError

	def __panapi_revision_revert(self, rpath, revision, dir = None):
		if not dir:
			dir = os.path.dirname(rpath)
		pars = {
			'revision' : revision,
			'path' : rpath,
			'type' : 2,
			'dir' : dir }

		self.pd("RevisionRevert request: {}".format(pars))
		return self.__post(PanAPI.PanAPIUrl + 'revision/revert?app_id=250528',
						   {}, self.__panapi_revision_revert_act, pars, data = pars, cookies = self.__cookies )

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
