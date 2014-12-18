#!/usr/bin/env python
# coding=utf-8

from setuptools import setup,find_packages

setup(
	name='bypy',
	version='1.0.2',
	description='Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘 Python 客户端',
	author='Hou Tianze',
	author_email='houtianze@gmail.com',
	url='https://github.com/houtianze/bypy',
	packages=find_packages(),
	scripts=["bypy.py","bypygui.pyw"],
	)

# vim: set fileencoding=utf-8
