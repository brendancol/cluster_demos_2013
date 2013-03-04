#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2011 Ulf Großekathöfer
#
# Email: ugrossek@techfak.uni-bielefeld.de
#
# Last modified: Tue Feb 01, 2011  10:19PM
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>


"""
This module provides some handy functions for use with K-Trees.
"""

import numpy
import cPickle as pickle

def save_ktree(k, filename):
    f = open(filename, "wb")
    pickle.dump(k, f, -1)
    f.close()

def load_ktree(filename):
    f = open(filename, "rb")
    k = pickle.load(f)
    f.close()
    return k

