#!/usr/bin/env python

import pypandoc

for md in ['HISTORY']:
	pypandoc.convert_file(md + '.md', 'rst', outputfile=md + '.rst')
