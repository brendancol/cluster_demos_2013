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
This module provides a K-Tree implementation in python.

See: 
Geva, S.: K-tree: a height balanced tree structured vector quantizer.
Proceedings of the 2000 IEEE Signal Processing Society Workshop
Neural Networks for Signal Processing X, 2000. 1 (2000) 271-280 vol.1
"""

# TODO:
#   - clean up

import sys
import datetime
import time

import numpy
import scipy

import models

# global variable, really?
ID = 0

def ktree(data, options=None):
    """This function creates a KTree and inserts the examples from "data" in the KTree.
    Arguments:
        * data:                 a data set for which a KTree will be build. 
                                Make sure "data" is an iterator.
        * options.order:        order of KTree, i.e. the maximum number of 
                                a node's children.  Default order is 5.
        * options.distance:     Distance measure that will be used for K-Tree, 
                                please use one of:
                                "cityblock", "euclidean", "sqeuclidean".
                                Default distance measure is "sqeuclidean".
        * options.weight_mean:  Use weight mean in k-means computation or not 
                                (only valid for "euclidean", "sqeuclidean").
                                Default is True.
    Returns:
        * a KTree

    Please note that "euclidean" and "sqeuclidean" should result in similar results.
    """
    if options is None:
        options = KTreeOptions()
    k = KTree(options=options)
    # build K-Tree:
    for i, d in enumerate(data):
        k.insert(d)
    if options.reinsert:
        # remove all leafs from tree
        k.remove_leafs()
        # re-insert vectors 
        for i, d in enumerate(data):
            k.insert(d, split=False)
    return k    


class KTreeOptions(object):
    """This class holds the options for K-Trees
    Currently, this options are:
        .order:    integer value indicating the order 
                   of the K-Tree, default 5.
        .weighted: a boolean weather to use a weighted
                   mean or not, default True.
        .distance: One of 
                       - "sqeuclidean" (default),
                       - "euclidean",
                       - "cityblock".
        .reinsert: 
    """

    def __init__(self):
        self.order = 5
        self.weighted = True
        self.distance = "sqeuclidean"
        self.reinsert = True

    def __str__(self):
        s =  "KTreeOptions: order: %i, " % self.order
        s += "weighted: %s, " % str(self.weighted)
        s += "distance: %s" % self.distance
        return s


class KNode(list):

    def __init__(self, options=None, model=None, parent=None):
        global ID
        ID += 1
        self.ID = ID
        # TODO: look up options in parent node?
        self.options = options
        if self.options is None:
            self.options = KTreeOptions()
        self.model = model
        if self.model is None:
                self.model = models.model(self.options)
        self.parent = parent

    def str(self, level=0):
        """A string representation of the current node and its (sub)trees."""
        s = "KN" + str(self.ID) + " " #"(parent.ID:"+ str(self.parent.ID) + " "
        for item in self:
            if item[1] is None:
                child_str = ""
            else:
                try:
                    child_str = ": " + item[1].str(level+1) 
                except AttributeError, exc:
                    child_str = ": " + str(item[1])
            s += "\n" + "\t"*level + "    " + str(item[0]) + child_str 
        return s+")"

    def __str__(self):
        return "KN" + str(self.ID)

    def __eq__(self, other):
        return self.ID == other.ID

    @property 
    def N(self):
        """A property that represents the accumulated number 
        of leafs in this node's (sub)tree.
        """
        try:
            return numpy.sum([item[1].N for item in self])
        except AttributeError:
            return len(self)

    @property
    def distortion(self):
        try:
            dist =  numpy.sum([ item[1].distortion for item in self ])
        except AttributeError:
            centroid = self.model.centroid_function(self)
            dist = numpy.sum([ self.model.distance_function(item[0], centroid) for item in self ])
        return dist

    @property
    def N_code_book(self):
        try:
            ncb = numpy.sum([ item[1].N_code_book for item in self ])
        except AttributeError:
            ncb = 1
        return ncb 
         
    @property
    def Ns(self):
        """The number of leafs in each sub-tree."""
        Ns = []
        for value in self.values():
            try:
                Ns.append(value.N)
            except AttributeError:
                Ns.append(1)
        return Ns

    @property
    def depth(self):
        """A property that represents the depth of this node's (sub)tree."""
        try:
            d = self[0][1].depth  
        except (IndexError, AttributeError):
            d = -1
        return d+1 

    def nearest_neighbor(self, value):
        """Find the nearest neighbor of "value" in this KTree."""
        try:
            nearest = self.nearestitem(value)[1].nearest_neighbor(value)
        except AttributeError, exc:
            nearest = self.nearestitem(value)[0]
        return nearest

    def level(self, n=1):
        """Return the prototypes of level 'n' in this KTree. 
        'n' is counted bottom-up, i.e. the level just above leaf level can be accessed with n=1.
        """
        if self.depth == n:
            return zip(self.keys(), self.Ns)
        else:
            keys = []
            for value in self.values():
                keys.append(value.level(n))
            return  [k for key in keys for k in key]

    def remove(self, key):
        """Delete the item that is associated with "key" from this node."""
        #print "remove:", self.ID, key, "*", map(lambda x: str(x[0])+" "+str(x[1]), self)
        for i, item in enumerate(self):
            if item[1] is key:
                del self[i]

    def remove_leafs(self):
        if self.hold_leafs:
            for i in range(len(self)-1,-1,-1):
                del self[i]
        else:
            for subnode in self:
                subnode[1].remove_leafs()

    @property
    def hold_leafs(self):
        """Returns True if this node holds leafs and
        False if is holds sub-nodes.
        """
        try:
            # ok, if this node has sub-nodes, these nodes
            # would definitely have an insert method, right?
            f = self[0][1].insert
            return False
        except (IndexError, AttributeError), exc:
            return True

    def keys(self):
        """A property that returns a list of all keys in this node."""
        return [ k[0] for k in self ]

    def values(self):
        return [ k[1] for k in self ]

    def items(self):
        return [ (k[0],k[1]) for k in self ]

    def append(self, key, value, split=True):
        """Append a (key, value) pair to this KNode and split it 
        if the number of elements exceed the KTree's order.
        """
        try:
            value.parent = self
        except AttributeError, exc:
            pass
        super(KNode, self).append([key, value])
        if (len(self) > self.options.order) and split:
            self.split()

    def split(self):
        """Split this node and replace it with its successors in the parent node."""
        centroids, labels = self.model.clustering_function(self)
        if isinstance(self.parent, KTree):
            self.parent = self.parent.new_root()
        else:
            self.parent.remove(self)
        nodes = [ KNode(options=self.options, model=self.model) for i in range(2) ]
        for label, item in zip(labels, self.items()):
            nodes[label].append(item[0], item[1])
        for i, node in enumerate(nodes):
            self.parent.append(centroids[i], node)

    def nearestitem(self, key):
        """Find this KNode's nearest item 
        in terms of distance to "key".
        """
        dm = [ self.model.distance_function(key, sk) for sk in self.keys() ]
        return self[numpy.argmin(dm)]

    def insert(self, value, split=True):
        """ Insert "value" to this KNode. If this KNode has leafs, append
        "value" to the leafs, otherwise insert "value" to its nearest child
        node.
        """
        if not self.hold_leafs:
            nearest_element = self.nearestitem(value)
            nearest_element[1].insert(value)
            # TODO: this can be solved more efficiently:
            nearest_element[0] = self.model.centroid_function(nearest_element[1])
        else:
            self.append(value, None, split)

    
class KTree(object):
    """The complete KTree object."""

    def __init__(self, options=None):
        self.ID = -1
        self.options = options
        if self.options is None:
            self.options = KTreeOptions()
        # self.model provides all metric related functions:
        self.model = models.model(self.options)
        # root node of tree:
        self.root = self.new_root()

    def __str__(self):
        s = "KTree("
        s += str(self.options)
        s += " "
        s += self.root.str()
        s += "\n)"
        return s

    def __iter__(self):
        return self.root

    @property
    def order(self):
        """Convenient property that returns this K-Tree's order.""" 
        return self.options.order

    def insert(self, value, split=True):
        """Insert value in KTree."""
        self.root.insert(value, split)

    def nearest_neighbor(self, value):
        """Find the nearest neighbor of "value" in this KTree."""
        return self.root.nearest_neighbor(value)
    
    def new_root(self):
        """Create and return a new root node."""
        self.root = KNode(parent=self, options=self.options, model=self.model)
        return self.root         

    def remove_leafs(self):
        """Remove all leafs from tree."""
        return self.root.remove_leafs()

    @property
    def depth(self):
        """Depth of KTree."""
        return self.root.depth

    @property
    def N(self):
        """Number of leafs."""
        return self.root.N

    @property
    def distrortion(self):
        return self.root.distortion

    @property
    def N_code_book(self):
        return self.root.N_code_book 
 

# very little test:
if __name__ == "__main__":
    N = 100
    d = 1
    order = 6
    import numpy.random
    print "generating data set with", N, "examples:"
    ds = numpy.random.normal(size=[N,d])
    #ds = numpy.arange(10)
    #ds.shape = (10,1)
    print
    print "building KTree of order", order, ":"
    t0 = time.time()
    options = KTreeOptions()
    options.order = order
    print options
    #options.distance = "sceuclidean"
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
