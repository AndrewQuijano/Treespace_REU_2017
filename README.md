# Treespace_REU_2017
[![Build Status](https://travis-ci.com/AndrewQuijano/Treespace_REU_2017.svg?branch=main)](https://travis-ci.com/AndrewQuijano/Treespace_REU_2017)

[![codecov](https://codecov.io/gh/AndrewQuijano/Treespace_REU_2017/branch/main/graph/badge.svg?token=DG1IUGC12E)](https://codecov.io/gh/AndrewQuijano/Treespace_REU_2017)

## Installation
This code has been tested on Ubuntu 20 LTS. Upon downloading the repository, run the installation script to obtain all the required packages. This code is written using Python 3.7.

When you download the repository, you need to add the executable flag to install.sh. Also, you will need to convert the file into UNIX format by using:  
*dos2unix* install.sh

## Usage
The script will read Phylogenetic networks from the Phylo directory. Each file would correspond to a phylogenetic network to analyze.  
Please use the Newick format for all phylogenetic networks and that all the internal nodes are labelled!

Run the test cases to ensure the metrics work on pre-defined graphs, run:  
python3 treespace.py --test

If you want to run on Phylogenetic Networks in Newick format, put then in Phylo/ directory. Some example networks are provided in the repository.

Add the following arguments as needed:  
* -d, if you are running on Linux, it will draw bipartite graphs/Networks/Trees
* -j, Run the Jettan and van Iersal Algorithm to determine if Network is tree-based
* -m, Run the Maximum Covering Sub-Tree algorithm, to determine minimum number of nodes to remove to make network N tree-based
* -f, Run the Francis et al. Algorithm to compute the spanning tree of network N, and number of additional leaves required to make the Network tree-based.
* -c, Count the minimum number of trees requires to span a phylohenetic network N **NOTE: STILL IN PROGRESS**


NOTE: This code will work on rooted binary and non-binary phylogeneitc networks! However, it does NOT support unrooted phylogenetic networks.  

## Authors and Acknowledgment
Code Author: Andrew Quijano  

Please cite the papers from which the algorithms are derived from if you use this library.  

Zhang's algorithm (zhang.py):  
Louxin Zhang. On tree-based phylogenetic networks. Journal of Computational Biology, 23(7):553–565, 2016.  

Jettan and van Iersal's Algorithm (jettan.py):  
Laura Jetten and Leo van Iersel. Nonbinary tree-based phylogenetic networks. IEEE/ACM Transactions on Computational Biology and Bioinformatics, 1:205–217, 2018. On-line publication: October 2016.

Francis et. al's Spanning Tree Algorithm (francis.py):  
Andrew Francis, Charles Semple, and Mike Steel. New characterisations of tree-based networks and proximity measures. Advances in Applied Mathematics, 93:93–107, 2018.  

Maximum Covering Subtree (max-cst.py):  
Davidov, N., Hernandez, A., Mckenna, P., Medlin, K., Jian, J., Mojumder, R., Owen, M., Quijano, A., Rodriguez, A., John, K.S. and Thai, K., 2020. Maximum Covering Subtrees for Phylogenetic Networks. IEEE/ACM Transactions on Computational Biology and Bioinformatics.

https://arxiv.org/abs/2009.12413

This work was funded by a Research Experiencefor Undergraduates (REU) grant from the U.S. National Science Foundation (#1461094 to St. John and Owen).  

I would like to thank Professor van Iersel for this link containing phylogenetic networks we used to test the code in the Phylo diretory:  
http://phylnet.univ-mlv.fr/recophync/networkDraw.php

The name of the text file will identify the paper it came from to cite if you use these as well.  
Please note, I had to use the newick format *with internal node names*, so I can easily convert this into a DAG in networkx to be compatible with the algorithms.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Project status
The project is currently fully tested and functional. I am interested in implementing algorithms for unrooted phylogenetic networks, but they are NP-Complete, so im unsure if the time investment is worth it to implement it. If there is interest, please email me.
