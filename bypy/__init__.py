#!/usr/bin/env python
# coding=utf-8

# A simple GUI for bypy, using Tkinter
# Copyright 2013 Hou Tianze (GitHub: houtianze, Twitter: @ibic, G+: +TianzeHou)
# Licensed under the GPLv3
# https://www.gnu.org/licenses/gpl-3.0.txt

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from . import const

# expose package names
from .bypy import ByPy
ByPy

__title__ =  const.__title__
__version__ = const.__version__
__author__ = const.__author__
__license__ = const.__license__

