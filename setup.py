#!/usr/bin/env python
# coding=utf-8

import io
import re

from setuptools import setup

# https://packaging.python.org/single_source_version/
# CAN'T believe there is no single *clean* way of retrieving the version.
def getmeta(path, encoding = 'utf8'):
	with io.open(path, encoding = encoding) as fp:
		content = fp.read()
	metakeys = ['title', 'version', 'desc', 'author', 'license', 'url']
	metatrans = { 'title' : 'name', 'desc' : 'description' }
	meta = {}
	for mk in metakeys:
		match = re.search(
			r"^__" + mk + r"__\s*=\s*['\"]([^'\"]*)['\"]",
            content, re.M)
		if match:
			if mk in metatrans:
				key = metatrans[mk]
			else:
				key = mk
			meta[key] = match.group(1)
		else:
			raise RuntimeError("Unable to find meta key: {}".format(mk))
	return meta

meta = getmeta('bypy/const.py')

long_desc = '''\
Documents:
~~~~~~~~~~
See: https://github.com/houtianze/bypy


'''

with open('HISTORY.rst') as f:
	long_desc += f.read()

setup(
	long_description=long_desc,
	author_email = 'houtianze@users.noreply.github.com',
	download_url = 'https://github.com/houtianze/bypy/tarball/' + meta['version'],
	#packages=find_packages(),
	packages = ['bypy', 'bypy.test'],
	package_data = {
		'bypy' : ['*.rst', 'bypy/*.pem']
	},
	entry_points = {
		'console_scripts': [
			'bypy = bypy.bypy:main'
		],
		'gui_scripts': [
			'bypygui = bypy.gui:main'
		]
	},
	test_suite = 'bypy.test',
	keywords = ['bypy', 'bypy.py', 'baidu pcs', 'baidu yun', 'baidu pan', 'baidu netdisk',
				'baidu cloud storage', 'baidu personal cloud storage',
				'百度云', '百度云盘', '百度网盘', '百度个人云存储'],
	classifiers = [
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: End Users/Desktop',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: English',
		'Operating System :: MacOS :: MacOS X',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: POSIX',
		'Operating System :: Unix',
		'Programming Language :: Python',
		'Topic :: Utilities',
		'Topic :: Internet :: WWW/HTTP'],
	install_requires = ['requests>=2.10.0'],
	include_package_data = True,
	**meta
)

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
