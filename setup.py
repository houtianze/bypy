#!/usr/bin/env python
# coding=utf-8

from setuptools import setup

from bypy import const

long_desc = ''
with open('README.rst') as f:
	long_desc = f.read()

long_desc += '\n\n'

with open('HISTORY.rst') as f:
	long_desc += f.read()

setup(
	name=const.__title__,
	version=const.__version__,
	description=const.__desc__,
	long_description=long_desc,
	author=const.__author__,
	author_email='houtianze@users.noreply.github.com',
	license=const.__license__,
	url=const.__url__,
	download_url='https://github.com/houtianze/bypy/tarball/' + const.__version__,
	#packages=find_packages(),
	packages=['bypy', 'bypy.test'],
	package_data = {
		'bypy' : ['*.rst', '*.pem']
	},
	entry_points = {
		'console_scripts': [
			'bypy = bypy.bypy:main'
		],
		'gui_scripts': [
			'bypygui = bypy.gui:main'
		]
	},
	test_suite='bypy.test',
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
	install_requires = [
		'requests',
	],
	include_package_data=True
)

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
