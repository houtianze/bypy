#!/usr/bin/env python
# coding=utf-8

from setuptools import setup,find_packages

import bypy
doclist = bypy.__doc__.split("---")
long_desc = doclist[1].strip() + '\n\n'
try:
	import pypandoc
	long_desc += pypandoc.convert('HISTORY.md', 'rst')
except Exception as ex:
	print("Error: PanDoc not found\n{}".format(ex))
	with open('HISTORY.md') as f:
		long_desc += f.read()

print(long_desc)

setup(
	name='bypy',
	version=bypy.__version__,
	description='Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘 Python 客户端',
	long_description=long_desc,
	author='Hou Tianze',
	license='MIT',
	url='https://github.com/houtianze/bypy',
	download_url='https://github.com/houtianze/bypy/tarball/' + bypy.__version__,
	packages=find_packages(),
	scripts=['bypy', 'bypy.bat', 'bypy.py', 'bypygui.pyw'],
	package_data = {
		'' : ['*.md']
	},
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
	include_package_data=True)

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
