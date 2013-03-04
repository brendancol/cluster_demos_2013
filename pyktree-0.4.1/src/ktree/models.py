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

import numpy
import scipy.spatial.distance
import scipy.stats

import sys
import random

import trees

DISTANCES = [
            'eculidean',
            'cityblock',
            'sqeuclidean'
            ]

def model(options):
    """Convenient function that returns the right model for given options.

    """
    if options.distance == "sqeuclidean" and options.weighted:
        return WeightedSqeuclideanModel()
    if options.distance == "sqeuclidean" and not options.weighted:
        return SqeuclideanModel()
    elif options.distance == "euclidean" and options.weighted:
        return WeightedEuclideanModel()
    elif options.distance == "euclidean" and not options.weighted:
        return EuclideanModel()
    elif options.distance == "cityblock":
        return CityblockModel()
    else:
        raise ValueError("Options %s unknown." % str(options))

class Model(object):
    """A Model is the base class for all distance and centroid related functions.
    In oder to operate a model has to provide four functions:

    distance_functions(self, x, y): a function that returns the distance between
                                    x (an example) and y (a centroid).
    distance_matrix(self, X, Y): a function that returns a distance matrix between
                                 a list of examples X and a list of centroids Y.
    centroid_function(self, node): a function that computes a representation for
                                   a node.
    clustering_function(self, node): a function that generates two clusters, 
                                     i.e. two new centroids and related assignments.

    A "centroid" means in this context a prototypic representation for a node.
    For example, if you choose the experimental "GaussianModel", a representation
    would be the mean parameter mu and the variance parameter sigma.
    However, the data type of "examples" and the representation of centroids 
    only depends on the chosen model.
    """
    
    def distance_function(self, x, y):
        """Returns the distance between x and y."""
        pass

    def distance_matrix(self, X, Y):
        """Returns a distance matrix for elements of list X and list Y."""
        N1 = len(X)
        N2 = len(Y)
        dm = numpy.empty((N1, N2))
        for ix, x in enumerate(X):
            for iy, y in enumerate(Y):
                dm[ix, iy] = self.distance_function(x.data,y.data)
        return dm    

    def centroid_function(self, node):
        """Computes the centroid for the elements of "node"."""
        pass

    def clustering_function(self, node):
        """Performce clustering on the elements of "node"."""
        pass


class EuclideanModel(Model):
    """An EuclideanModel uses euclidean distance as distance measure
    and the average function to compute the centroid.
    
    Please note that this model does not use weighted averages. 
    """

    def _toarray(self, node):
        """Generates an numpy array from a nodes keys."""
        keys = None
        for item in node:
            if keys is None:
                keys = item[0]
            else: 
                keys = numpy.vstack((keys, item[0]))
        return numpy.atleast_2d(keys)

    def distance_function(self, x, y):
        """Returns euclidean distance between "x" and "y"."""
        # return numpy.linalg.norm(x-y)
        return numpy.sqrt(numpy.sum((x-y)**2))
        
    def distance_matrix(self, X, Y):
        """Returns a distance matrix for elements of lists "X" and "Y"
        in terms of euclidean distance.
        """
        return scipy.spatial.distance.cdist(X, Y, metric="euclidean")

    def centroid_function(self, node):
        """Computes and returns the average of the node's "node" keys."""
        node = self._toarray(node)
        return numpy.mean(node,0) 

    def clustering_function(self, node):
        """Simple implementation of k-means algorithm.
        Arguments:
            * node:     ktree.node that should be processed.
        Returns:
            * centroids
            * assignments    
        """    
        # some consts:
        max_iter = 10
        K = 2
        # lets start from here:
        X = self._toarray(node)
        N, d = X.shape
        # random initalization:
        centroids = X[random.sample(xrange(N), 2),:] 
        for iter in xrange(max_iter): # well, ...
            # assign:
            dm = self.distance_matrix(X, centroids)
            assignments = numpy.argmin(dm,1)
            # this shouldn't happen:
            if len(set(assignments)) == 1:
                 i = numpy.random.randint(len(assignments)) 
                 assignments[i] = abs(assignments[i]-1)    
            #update centroids:
            for k in xrange(K):
                centroids[k,:] = self.centroid_function(X[numpy.nonzero(assignments==k)])
        return centroids, assignments


class SqeuclideanModel(EuclideanModel):
    """A SqeuclideanModel uses euclidean squared distances as distance measure
    and the average function to compute the centroid.
    
    Please note that this model does not uses weighted averages. 
    """

    def distance_function(self, x, y):
        """Euclidean squared distance between vectors x and y."""
        # return numpy.linalg.norm(x-y)**2
        return numpy.sum((x-y)**2)
        
    def distance_matrix(self, X, Y):
        """Returns a distance matrix for elements of lists "X" and "Y"
        in terms of euclidean squared distance.
        """
        return scipy.spatial.distance.cdist(X, Y, metric="sqeuclidean")


class CityblockModel(EuclideanModel):
    """A CityblockModel uses cityblock distance as distance measure
    and the median function as centroid funtion.
    """

    def distance_function(self, x, y):
        """cityblock distance between vectors "x" and "y"."""
        return numpy.sum(abs(x-y))
        
    def distance_matrix(self, X, Y):
        """Returns a distance matrix for elements of lists "X" and "Y"
        in terms of cityblock distances.
        """
        return scipy.spatial.distance.cdist(X, Y, metric="cityblock")

    def centroid_function(self, node):
        """Returns the median of "node"'s keys."""
        node = self._toarray(node)
        try:
            centroid = numpy.median(node,0)
        except IndexError:
            centroid = numpy.median(node)
        return centroid


class WeightedEuclideanModel(EuclideanModel):
    """A WeightedEuclideanModel uses euclidean distance as distance measure
    and the average function to compute the centroid.
    
    Please note that this model uses weighted averages. 
    """

    def centroid_function(self, node, Ns=None):
        if Ns is None:
            Ns = node.Ns
        X = self._toarray(node) 
        try:
            centroid = numpy.average(numpy.atleast_2d(X), weights=Ns, axis=0)
        except (ZeroDivisionError, IndexError):
            centroid = numpy.average(numpy.atleast_2d(X))
        return centroid

    def clustering_function(self, node):
        """Simple implementation of k-means algorithm.
        Arguments:
            * node:     ktree.node that should be processed.
        Returns:
            * centroids
            * assignments    
        This function uses weighted means.
        """    
        # some consts:
        max_iter = 10
        K = 2
        # lets start from here:
        X = self._toarray(node)
        N, d = X.shape
        Ns = numpy.array(node.Ns)
        # random initalization:
        centroids = X[random.sample(xrange(N), 2),:] 
        for iter in xrange(max_iter): # well, ...
            # assign:
            dm = self.distance_matrix(X, centroids)
            assignments = numpy.argmin(dm,1)
            # this shouldn't happen:
            if len(set(assignments)) == 1:
                 i = numpy.random.randint(len(assignments)) 
                 assignments[i] = abs(assignments[i]-1)    
            #update centroids:
            for k in xrange(K):
                centroids[k,:] = self.centroid_function(X[numpy.nonzero(assignments==k)], 
                                                        Ns[assignments==k])
        return centroids, assignments


class WeightedSqeuclideanModel(WeightedEuclideanModel):
    """A WeightedSqeuclideanModel uses euclidean squared distance
    as distance measure and the weighted average function 
    to compute the centroid.
    """

    def distance_function(self, x, y):
        """Euclidean squared distance between vectors x and y."""
        # return numpy.linalg.norm(x-y)**2
        return numpy.sum((x-y)**2)
        
    def distance_matrix(self, X, Y):
        """Returns a distance matrix for elements of lists "X" and "Y"
        in terms of euclidean squared distance.
        """
        return scipy.spatial.distance.cdist(X, Y, metric="sqeuclidean")


