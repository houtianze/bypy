#!/usr/bin/env python

import pypandoc

for md in ['README', 'HISTORY', 'CONTRIBUTING']:
	pypandoc.convert_file(md + '.md', 'rst', outputfile=md + '.rst')
