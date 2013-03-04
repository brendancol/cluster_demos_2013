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

import ktree
import numpy.random

# N: number of examples
# d: dimension of examples
# order: order of K-tree
N = 100
d = 1
order = 6

print "generating data set with", N, "examples:"
ds = numpy.random.normal(size=[N,d])
print
print "building KTree of order", order, ":"
t0 = time.time()
options = KTreeOptions()
options.order = order
options.weighted = True
options.distance = "sqeuclidean"
options.reinsert = True
k = ktree(data=ds, options=options)
t = time.time() - t0
if N < 500:
    print
    print k
print
print "generated KTree in", t, "seconds"
print
print "order:", k.order 
print "N:", N
print "depth:", k.depth
print
for i in [-1,0,1]:
    vec = numpy.ones((1,d))*i
    print "Looking for nearest neighbor of", str(vec), ",",
    print "found: ", k.nearest_neighbor(vec)


