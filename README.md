# Treespace_REU_2017
[![treespace-test](https://github.com/AndrewQuijano/Treespace_REU_2017/actions/workflows/treespace-test.yml/badge.svg)](https://github.com/AndrewQuijano/Treespace_REU_2017/actions/workflows/treespace-test.yml)

[![codecov](https://codecov.io/gh/AndrewQuijano/Treespace_REU_2017/branch/main/graph/badge.svg?token=DG1IUGC12E)](https://codecov.io/gh/AndrewQuijano/Treespace_REU_2017)

## Installation
This code has been tested on Ubuntu 22 LTS.
Upon downloading the repository, run the installation script to obtain all the required packages.
When you download the repository, run the following command `bash install.sh`

## Documentation
You can run commands to create python documentation as follows:
```bash
pip install pdoc
# will create an html folder with all generated documentation in .html format
pdoc3 --html treespace_metrics

# If you want it to run on local-host
pdoc --http localhost:8080 treespace_metrics
```
To access documentation, you can find it [here](https://andrewquijano.github.io/files/treespace_metrics/). 
You can also [download the package via pip](https://pypi.org/project/treespace-metrics/).

## Usage — Metrics on Adjacency Lists/Newick Graphs
I would like to thank Professor van Iersel for this [link](http://phylnet.univ-mlv.fr/recophync/networkDraw.php) containing phylogenetic networks we used to test the code in the [Phylo](https://github.com/AndrewQuijano/Treespace_REU_2017/tree/main/Phylo) directory. The name of the text file will identify the paper it came from to cite if you use these as well. Please note, I had to use the newick format *with internal node names*, so I can easily convert this into a DAG in networkx to be compatible with the algorithms.

Run the test cases to ensure the metrics work [on pre-defined graphs](https://github.com/AndrewQuijano/Treespace_REU_2017/tree/main/Graph), run:  
`pytest test`

Add the following arguments as needed:
* --dir, the input directory that has text files containing newick graphs or adjacency lists of phylogenetic networks
* -n, the input directory has text files that has newick formatted phylogenetic trees
* -d, draw the trees, bipartite graphs, etc.

After filling out the networks you want to get metrics for, here is how to execute the code:  
`python3 run_treespace.py --dir <directory> -d`

## Usage — Testing on Generated Networks
Louxin Zhang has provided me the source code to generate random binary phylogenetic networks, located in the [phylo_generator](https://github.com/AndrewQuijano/Treespace_REU_2017/tree/main/phylo_generator). Feel free to see his original code [here](https://github.com/LX-Zhang/Phylogenetic-Networks)  

After compiling the C code, run the following example to run generating 12 graphs with 3 leaves and 15 
reticulation nodes. After generating the graphs, compute the metrics and store it with images into a directory for further analysis.  
`python3 run_treespace.py --generate -l 3 -r 15 -g 12 -d`

## Authors and Acknowledgment
Code Author: Andrew Quijano  
This work was funded by a Research Experience for Undergraduates (REU) grant from the U.S. National Science Foundation (#1461094 to St. John and Owen).  

Please cite the papers from which the algorithms are derived from if you use this library.  

[Jettan and van Iersal's Algorithm](https://arxiv.org/abs/1601.04974) (jettan.py):  
Laura Jetten and Leo van Iersel.
Nonbinary tree-based phylogenetic networks.
IEEE/ACM Transactions on Computational Biology and Bioinformatics, 1:205–217, 2018. On-line publication: October 2016.

[Francis et al.'s Spanning Tree Algorithm](https://arxiv.org/abs/1611.04225) (francis.py):  
Andrew Francis, Charles Semple, and Mike Steel. 
New characterisations of tree-based networks and proximity measures. 
Advances in Applied Mathematics, 93:93–107, 2018.  

[Maximum Covering Subtrees for Phylogenetic Networks](https://arxiv.org/abs/2009.12413) (max-cst.py):  
Davidov, N., Hernandez, A., Mckenna, P., Medlin, K., Jian, J., Mojumder, R., Owen, M., Quijano, A., Rodriguez, A., John, K.S. and Thai, K., 2020. 
Maximum Covering Subtrees for Phylogenetic Networks. 
IEEE/ACM Transactions on Computational Biology and Bioinformatics.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Project status
The project is currently fully tested and functional for rooted phylogenetic networks. 
If you want to extend this for unrooted networks and have funding, please feel free to reach out.

Currently, I am working on the following:
* Solve the other problem about minimum number of trees spanning a network N, see `create_trees.py`
* Use OOP to create a PyPi package for this library
