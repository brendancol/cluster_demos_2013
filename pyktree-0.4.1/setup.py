#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2011 Ulf Großekathöfer
#
# Email: ugrossek@techfak.uni-bielefeld.de
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


from distutils.core import setup

setup(  name='pyktree',
        version='0.4.1',
        description='K-Tree Implementation',
        author='Ulf Großekathöfer',
        author_email='ugrossek@techfak.uni-bielefeld.de',
        url = "http://ktree.sourceforge.net/",
        package_dir={'ktree': 'src/ktree'},
        py_modules = ['ktree.trees', 'ktree.models', 'ktree.utils'],
        scripts=['scripts/ktmk', 
                 'scripts/ktpr', 
                 'scripts/ktnn'],
        data_files=[('examples', ['examples/ktree_example.py'])]
     )

