#!/usr/bin/env python
# coding=utf-8

from setuptools import setup,find_packages

setup(
	name='bypy',
	version='1.2.7',
	description='Python client for Baidu Yun',
	long_description='Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘 Python 客户端',
	author='Hou Tianze',
	license='MIT',
	url='https://github.com/houtianze/bypy',
	packages=find_packages(),
	scripts=['bypy', 'bypy.py', 'bypygui.pyw'],
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
		'Programming Language :: Python',
		'Topic :: Utilities',
		'Topic :: Internet :: WWW/HTTP'],
	install_requires = [
		'requests',
	])

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
