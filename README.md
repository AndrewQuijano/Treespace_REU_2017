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

To use the script just run:  
python3 treespace.py  

It will return the following for each phylogenetic network:  
* Number of nodes needing to be removed to make it tree-based
* Number of leaves that are needed to be added to make the network tree-based.
* If it is tree-based using Jettan van Iersal's algorithm

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

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Project status
The project is currently fully tested and functional. I am interested in implementing algorithms for unrooted phylogenetic networks, but they are NP-Complete, so im unsure if the time investment is worth it to implement it. If there is interest, please email me.