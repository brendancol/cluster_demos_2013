Pyktree provides a K-Tree implementation in the Python programming
language.  K-trees are a scalable approach to clustering by combining
the B+-tree and k-means algorithms. Clustering can be used to solve
problems in signal processing, machine learning, and other contexts. 

For further information see:

    Geva, S.: K-tree: a height balanced tree structured vector
    quantizer.  Proceedings of the 2000 IEEE Signal Processing Society
    Workshop Neural Networks for Signal Processing X, 2000. 1 (2000)
    271-280 vol.1, http://eprints.qut.edu.au/16970/1/c169708.pdf

Please send bug reports, questions, or any other inquiries to:
ugrossek@techfak.uni-bielefeld.de!

Copyright 2011: Ulf Großekathöfer <ugrossek@techfak.uni-bielefeld.de>
License:        GNU General Public License 3.0

=========================
Installation Instructions
=========================

The pyktree package requires scipy. If you do not have scipy installed
on your system, please go to http://www.scipy.org/, download, and
install it.  Additionally, you will need Python version 2.5 or higher.
Please note that this K-Tree implementation does not work with Python
3.0 yet.

For installation unpack pyktree-<version>.tar.gz, change to the archive
directory, and call the installation script.  For example, if you are
using Linux the commands would be:

> tar xvfz pyktree-<version>.tar.gz
> cd pyktree-<version>
> python setup.py install

To obtain a complete list of installation options, call:

> python setup.py help

==================
How to use K-Trees
==================

There are two ways of using pyktree: First, as a Python library, or,
second, as command line tools.

1. Library use: 
===============

    Import the module "ktree" in your python program and use the
    provided functions and classes.  The module provides a function
    "ktree.ktree(order=5, data_set)" that generates a K-Tree from a
    data_set of order "order". 
    
    Please see "example/ktree_example.py" for example code.
    
2. Command line use:   
===================

    pyktree comes with three command line scripts: ktmk, ktnn, ktpr.  A
    typical use case would look like this:

    EXAMPLE
    -------

    > # Build a K-Tree for a data set:
    > ktmk --data-set data.txt --order 6 --k-tree ktree.ktf -m -r

    > # Print the K-Tree:
    > ktpr ktree.ktf

    > # Find nearest neighbors in K-Tree for unseen examples:
    > ktnn --k-tree ktree.ktf --data-set unseen.txt --outfile nn.txt


    DETAILED DESCRIPTIONS
    ---------------------

    NAME 
   
        ktmk -- builds K-Trees 
   
    SYNOPSIS 
        
        ktmk {-d|--data-set} FILE {-o|--order} ORDER {-k|--k-tree} OUTFILE {-q|--quite} {-m|--unweighted-mean} {-r|-reinsert} {-f|--distance} DIST

   DESCRIPTION

        ktmk builds a K-Tree for a data set and saves it to a file.

    OPTIONS

        -h, --help
            Print a help message and exit.

        -d, --data-set FILE
            FILE that contains the data set. Each line of FILE should
            contain one example.

        -o, --order ORDER
            Order of K-Tree, default value is 5. 
        
        -k, --outfile FILE
            FILE to save K-Tree.

        -q, --quite 
            Do not print anything to stdout. Be quite. 

        -m, --unweighted-mean
            Use unwighted mean for computation of k-means.

        -r, --reinsert        
            Re-insert all examples when tree is build.

        -f DIST, --distance=DIST
            Distance measure for k-tree. Distance can be one of:
            eculidean cityblock sqeuclidean. 
            Default distance measure is 'sqeuclidean'.
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    NAME
    
        ktnn -- find nearest neighbor(s) in given K-Tree.       

    SYNOPSIS 
    
        ktnn {-k|--k-tree} FILE  {-d|--data-set} FILE  {-v|--verbose} LEVEL
    
    DESCRIPTION

        ktnn searches the nearest neighbors in a K-Tree for a set of
        unseen examples.

    OPTIONS

        -h, --help
            Print a help message and exit.

        -k  --k-tree FILE
            FILE that contains the K-Tree. This file can be generated
            with ktmk.

        -d  --data-set FILE
            FILE that contains the data set. Each line of FILE should
            contain one example. ktnn will search for the nearest
            neighbor for each example in FILE.

        -o, -outfile FILE
            FILE to save nearest neighbors.

        -q, --quite 
            Do not print anything to stdout. Be quite.  

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    NAME

        ktpr -- prints K-Tree as an ASCII representation

    SYNOPSIS 
    
        ktpr FILE
    
    DESCRIPTION
        
        ktpr prints an ASCII representation of a K-tree to stdout.
        Please note, this representation can get very large, even for
        (relatively) small K-Trees. It is not recommended to use ktshow
        for K-Trees with more than 1000 examples.

    OPTIONS

        FILE The file that contains the K-Tree.


