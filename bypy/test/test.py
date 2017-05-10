#!/usr/bin/env python
# encoding: utf-8
# PYTHON_ARGCOMPLETE_OK

# primitive sanity tests
# TODO: refactor and improve
# To Add:
# - Special file names (single quote)

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys
import os
import shutil
import re
import pprint
import copy
import time
if sys.version_info[0] == 3:
	basestring = str

from .. import bypy
from .. import monkey
from ..cached import cached
from .. import const

TestGarbledPathNames = False

MyDir = os.path.relpath(os.path.dirname(__file__))
ConfigDir = os.path.join(MyDir, 'configdir')
DownloadDir = os.path.join(MyDir, 'downdir')
TestDir = os.path.join(MyDir, 'testdir')
ShareDir = os.path.join(MyDir, 'sharedir')
# monkey patch all the way
# create some dummy files
zerofilename = os.path.join(TestDir, 'allzero.1m.bin')

# == Util fuctions ==
# store the output, for further analysis
class StorePrinter(object):
	def __init__(self, opr):
		self.opr = opr
		self.q = []

	def pr(self, msg):
		self.q.append(msg)
		self.opr(msg)

	def empty(self):
		del self.q[:]

	def getq(self):
		return self.q

def assertif(cond, assertion):
	if cond:
		assert assertion

def assertsingle(by, assertion):
	assertif(by.processes == 1, assertion)

def chkok(by, result):
	if by.processes == 1:
		if result != const.ENoError:
			print("Failed, result: {}".format(result))
			assert False
	else:
		if result != const.ENoError and result != const.IEFileAlreadyExists:
			print("Failed, result: {}".format(result))
			assert False

def makesuredir(dirname):
	if not os.path.exists(dirname):
		os.mkdir(dirname)

def banner(msg):
	title = "{0} {1} {0}".format('=' * 8, msg)
	line = '=' * len(title)
	print(line)
	print(title)
	print(line)

def ifany(list, require):
	for element in list:
		if require(element):
			return True

	return False

def filterregex(list, regex):
	rec = re.compile(regex)
	return filter(lambda x: rec and isinstance(x, basestring) and rec.search(x), list)

def createdummyfile(filename, size, value = 0):
	with open(filename, 'wb') as f:
		ba = bytearray([value] * size)
		f.write(ba)

mpr = StorePrinter(bypy.pr)
#bypy.pr = mpr.pr
monkey.patchpr(mpr.pr)
#shutil.copy('bypy.json', ConfigDir)
#shutil.copy('bypy.setting.json', ConfigDir)

def testmergeinto():
	fromc = {
		'a': {
			'a1': 1,
			'a2': 2
		},
		'b': {
			'b1': 10,
			'b2': 20
		}
	}

	to = {
		'a': {
			'a1': 9,
			'a3': 3
		},
		'b': {
			'b2': 90,
			'b3': 30,
		},
		'c': {
			'c1': 100
		}
	}
	toorig = copy.deepcopy(to)

	pprint.pprint(fromc)
	pprint.pprint(to)
	cached.mergeinto(fromc, to)
	pprint.pprint(to)
	print(repr(to))
	assert to == {u'a': {u'a1': 9, u'a3': 3, u'a2': 2}, u'c': {u'c1': 100}, u'b': {u'b1': 10, u'b2': 90, u'b3': 30}}

	to = toorig
	pprint.pprint(fromc)
	pprint.pprint(to)
	cached.mergeinto(fromc, to, False)
	pprint.pprint(to)
	print(repr(to))
	assert to == {u'a': {u'a1': 1, u'a3': 3, u'a2': 2}, u'c': {u'c1': 100}, u'b': {u'b1': 10, u'b2': 20, u'b3': 30}}

def prepare(by):
	# preparation
	makesuredir(ConfigDir)
	# we must upload something first, otherwise, listing / deleting the root directory will fail
	banner("Uploading a file")
	chkok(by, by.upload(TestDir + '/a.txt'))
	print("Response: {}".format(by.response.json()))
	banner("Listing the root directory")
	assert by.list('/') == const.ENoError
	print("Response: {}".format(by.response.json()))
	mpr.empty()
	createdummyfile(zerofilename, 1024 * 1024)

	makesuredir(ShareDir)
	sharesubdir = ShareDir + '/subdir'
	makesuredir(sharesubdir)
	createdummyfile(ShareDir + '/1M0.bin', 1024 * 1024)
	createdummyfile(ShareDir + '/1M1.bin', 1024 * 1024, 1)
	createdummyfile(sharesubdir + '/1M2.bin', 1024 * 1024, 2)

	if TestGarbledPathNames:
		jd = TestDir.encode() + os.sep.encode() + b'garble\xec\xeddir'
		jf = TestDir.encode() + os.sep.encode() + b'garble\xea\xebfile'
		makesuredir(jd)
		with open(jf, 'w') as f:
			f.write("garbled")

def emptyremote(by):
	banner("Deleting all the files at PCS")
	assert by.delete('/') == const.ENoError
	assert 'request_id' in by.response.json()
	mpr.empty()

def getquota(by):
	# quota
	banner("Getting quota")
	assert by.info() == const.ENoError
	resp = by.response.json()
	print("Response: {}".format(resp))
	#assert resp['used'] == 1048626
	assert resp['quota'] >= 2206539448320
	mpr.empty()

def assertsame(by):
	bypy.pr(by.result)
	assert len(by.result['diff']) == 0
	assert len(by.result['local']) == 0
	assert len(by.result['remote']) == 0
	assert len(by.result['same']) >= 5

def compare(by):
	# comparison
	banner("Comparing")
	assert by.compare(TestDir, TestDir) == const.ENoError
	assertsame(by)
	mpr.empty()

def uploaddir(by):
	# upload
	banner("Uploading the local directory")
	chkok(by, by.upload(TestDir, TestDir))
	assertsingle(by, filterregex(mpr.getq(),
					   r"RapidUpload:.*testdir[\\/]allzero.1m.bin' =R=\> '.*/testdir/allzero.1m.bin' OK"))
	assertsingle(by, filterregex(mpr.getq(), r".*testdir[\\/]a.txt' ==> '.*/testdir/a.txt' OK."))
	assertsingle(by, filterregex(mpr.getq(), r".*testdir[\\/]b.txt' ==> '.*/testdir/b.txt' OK."))
	print("Response: {}".format(by.response.json()))
	mpr.empty()

def downdir(by):
	# download
	banner("Downloading dir")
	shutil.rmtree(DownloadDir, ignore_errors=True)
	chkok(by, by.downdir(TestDir, DownloadDir))
	chkok(by, by.download(TestDir, DownloadDir))
	assert by.compare(TestDir, DownloadDir) == const.ENoError
	assertsame(by)
	mpr.empty()

def syncup(by):
	banner("Syncing up")
	emptyremote(by)
	chkok(by, by.syncup(TestDir, TestDir))
	assert by.compare(TestDir, TestDir) == const.ENoError
	assertsame(by)
	mpr.empty()

def syncdown(by):
	banner("Syncing down")
	shutil.rmtree(DownloadDir, ignore_errors=True)
	chkok(by, by.syncdown(TestDir, DownloadDir))
	chkok(by, by.compare(TestDir, DownloadDir))
	shutil.rmtree(DownloadDir, ignore_errors=True)
	assertsame(by)
	mpr.empty()

def cdl(by):
	banner("Offline (cloud) download")
	result = by.cdl_cancel(123)
	assert int(result) == const.IETaskNotFound
	mpr.empty()
	assert by.cdl_list() == const.ENoError
	# {u'request_id': 353951550, u'task_info': [], u'total': 0}
	assertsingle(by, filterregex(mpr.getq(), r"'total'\s*:\s*0"))
	mpr.empty()
	assert by.cdl_query(123) == const.ENoError
	assertsingle(by, filterregex(mpr.getq(), r"'result'\s*:\s*1"))
	mpr.empty()
	assert by.cdl_add("http://dl.client.baidu.com/BaiduKuaijie/BaiduKuaijie_Setup.exe", TestDir) == const.ENoError
	assertsingle(by, filterregex(mpr.getq(), r"'task_id'\s*:\s*\d+"))
	assert by.cdl_addmon("http://dl.client.baidu.com/BaiduKuaijie/BaiduKuaijie_Setup.exe", TestDir) == const.ENoError
	mpr.empty()

def testshare(by):
	banner("Share")
	#assert const.ENoError == by.share(ShareDir, '/', True, True)
	chkok(by, by.share(ShareDir, ShareDir))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/1M0.bin".format(ShareDir)))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/1M1.bin".format(ShareDir)))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/subdir/1M2.bin".format(ShareDir)))
	mpr.empty()
	chkok(by, by.upload(ShareDir, ShareDir))
	chkok(by, by.share(ShareDir, ShareDir, False))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/1M0.bin".format(ShareDir)))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/1M1.bin".format(ShareDir)))
	assertsingle(by, filterregex(mpr.getq(), r"bypy accept /{}/subdir/1M2.bin".format(ShareDir)))
	mpr.empty()

def cleanup():
	os.remove(zerofilename)
	#shutil.rmtree(ConfigDir, ignore_errors=True)
	shutil.rmtree(ShareDir, ignore_errors=True)
	shutil.rmtree(DownloadDir, ignore_errors=True)

def runTests(by):
	prepare(by)

	getquota(by)
	# sleep sometime helps preventing hanging requests <scorn>
	#cdl() # seems this is broken
	time.sleep(2)
	emptyremote(by)
	time.sleep(2)
	uploaddir(by)
	time.sleep(2)
	compare(by)
	time.sleep(2)
	downdir(by)
	time.sleep(2)
	syncup(by)
	time.sleep(2)
	syncdown(by)
	time.sleep(2)
	testshare(by)
	time.sleep(2)

def main():
	testmergeinto()

	try:
		by = bypy.ByPy(configdir=ConfigDir, debug=1, verbose=1)
		if 'refresh' in sys.argv:
			by.refreshtoken()
		runTests(by)
		if '1' in sys.argv:
			return

		time.sleep(10)
		by = bypy.ByPy(configdir=ConfigDir, processes=2, debug=1, verbose=1)
		runTests(by)
		if '2' in sys.argv:
			return

		# test aria2 downloading
		by = bypy.ByPy(configdir=ConfigDir, downloader='aria2', debug=1, verbose=1)
		downdir(by)
		by = bypy.ByPy(configdir=ConfigDir, downloader='aria2', processes=2, debug=1, verbose=1)
		downdir(by)
	except KeyboardInterrupt:
		print("User cancelled, cleaning up ...")
	finally:
		cleanup()
		print("Clean up done.")

# this is barely a sanity test, more to be added
if __name__ == "__main__":
	main()

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
