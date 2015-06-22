#!/usr/bin/env python
# coding=utf-8

from setuptools import setup,find_packages

import bypy

setup(
	name='bypy',
	version=bypy.__version__,
	description='Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘 Python 客户端',
	author='Hou Tianze',
	url='https://github.com/houtianze/bypy',
	download_url='https://github.com/houtianze/bypy/tarball/1.0.20',
	packages=find_packages(),
	scripts=['bypy.py', 'bypygui.pyw'],
	keywords = ['bypy', 'baidu', 'baidu pcs', 'client']
	)

# vim: set fileencoding=utf-8
