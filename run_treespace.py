#!/usr/bin/env python3

import argparse
import os
from os import listdir
from os.path import isfile, join

from Bio import Phylo
from treespace.create_trees import enum_trees
from treespace.drawing import draw_tree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from treespace.jetten import is_tree_based
from treespace.max_cst import maximum_covering_subtree
from treespace.utils import read_adjacency_list, create_dag

import subprocess


# Used by both offline and online method to analyze metrics of graphs, and store output
def analyze_generated_graphs(dataset_size: int, output_directory: str):
    # Create Headers of CSV results like answers.csv
    with open("metrics.csv", 'w+') as fd:
        fd.write('graph,is_tree_based,max_cst,spanning_tree,rooted_tree\n')

    # Create directory to store pictures for analysis...
    os.makedirs(output_directory, exist_ok=True)

    for random_network in range(0, dataset_size):
        random_network = "0%d" % random_network
        print("Opening the random_network: " + random_network)
        tree_directory = random_network + '_trees'
        os.makedirs(os.path.join(output_directory, tree_directory), exist_ok=True)

        graph = read_adjacency_list(random_network)
        row = ''
        draw_tree(graph, random_network)
        if is_tree_based(graph):
            row += random_network + ",1"
        else:
            row += random_network + ",0"
        # Obtain Metrics and Print
        _, eta = maximum_covering_subtree(graph, random_network)
        missing_v1, paths = vertex_disjoint_paths(graph, random_network)
        tree_list, count = enum_trees(graph, os.path.join(output_directory, random_network), True)
        row += ',' + str(eta) + ',' + str(missing_v1) + ',' + str(count) + '\n'
        with open("metrics.csv", 'a+') as metric:
            metric.write(row)
        subprocess.call(['mv', random_network, output_directory])

    subprocess.Popen("mv *.png " + output_directory, shell=True, executable='/bin/bash')
    subprocess.call(['mv', 'metrics.csv', output_directory])


# Creates random Phylogenetic Networks
# These networks are usually tree-based or almost tree-based. I need to make it more random somehow...
# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_local_random_dag(arg_vector: argparse):
    subprocess.call(['./phylo_generator/binary_ntk_generator',
                     str(arg_vector.num_leaves), str(arg_vector.num_reticulation),
                     str(arg_vector.num_dataset)])
    output_dir = 'output_ret=' + str(arg_vector.num_reticulation) + '_leaves=' + str(arg_vector.num_leaves)
    analyze_generated_graphs(arg_vector.num_dataset, output_dir)


def main(argv: argparse):
    list_of_network_files = [f for f in listdir(args.dir) if isfile(join(args.dir, f))]
    for network_file in list_of_network_files:
        if args.newick:
            g = Phylo.read(join(args.dir, network_file), 'newick')
            g = Phylo.to_networkx(g)
            g = create_dag(g)
        else:
            g = read_adjacency_list(join(args.dir, network_file))

        # Max-CST, returns MAX-CST and number of vertices removed
        name = network_file.split('.')[0]
        print('----' + name + '----')
        if argv.max:
            t, n = maximum_covering_subtree(g, name, argv.draw)
            print('1- This requires a minimum of ' + str(n) + ' vertices to be removed to become tree-based')

        # Francis et. al. algorithm, returns number of leaves needed and disjoint paths for spanning tree.
        if argv.francis:
            missing_v1, paths = vertex_disjoint_paths(g, name, argv.draw)
            if argv.draw:
                s = rooted_spanning_tree(g, paths)
                st = tree_based_network(s, g)
                draw_tree(st, name + '-spanning-tree')
            print('2- This requires a minimum of ' + str(missing_v1) + ' leaves to be added to become tree-based')
        # Jettan and van Iersel Tree-based
        if argv.tree:
            if is_tree_based(g, name, argv.draw):
                print('3- This is a tree-based phylogenetic network')
            else:
                print('3- This is NOT a tree-based phylogenetic network')
        if argv.count:
            trees = enum_trees(g, name, argv.draw)
            print("4- The minimum number of trees required to span Network N is: " + str(len(trees)) + " trees")


parser = argparse.ArgumentParser(prog='A python program that can run algorithms used to '
                                      'compute Phylogenetic network metrics')
group = parser.add_mutually_exclusive_group()
parser.add_argument('--draw', '-d', dest='draw', action='store_true',
                    help="Draw all Bipartite Graphs, Trees, etc.")
parser.add_argument('--jettan', '-j', dest='tree', action='store_true',
                    help="Check if all Networks N (including non-binary) is tree-based")
parser.add_argument('--max', '-m', dest='max', action='store_true',
                    help="Run Maximum Covering Subtree on all Networks N")
parser.add_argument('--francis', '-f', dest='francis', action='store_true',
                    help="Run Francis et al. Spanning Tree Algorithm on all input Networks N")
parser.add_argument('--count', '-c', dest='count', action='store_true',
                    help="Count the minimum number of trees required to span the Network N")

# Collect for arguments on generating random graphs
# num_leaves=10, num_reticulation=5, num_dataset=10
parser.add_argument('--leaves', '-l', nargs='?', dest='num_leaves', action='store',
                    help="number of leaves in each graph", const=1, default=10, type=int)
parser.add_argument('--reticulation', '-r', nargs='?', dest='num_reticulation', action='store',
                    help="number of reticulation vertices for each graph", const=1, default=10,
                    type=int)
parser.add_argument('--graphs', '-g', nargs='?', dest='num_dataset', action='store',
                    help="num of random graphs to generate", const=1, default=10, type=int)
parser.add_argument('--dir', nargs='?', dest='dir', action='store',
                    help="Directory containing either NetworkX Adjacency List or Newick formatted graphs", type=str)
parser.add_argument('--newick', '-n', dest='newick', action='store_true',
                    help='Identify the input is Newick data')

# What mode
group.add_argument('--test', '-t', dest='test', action='store_true',
                   help="Run Testing on Networks in the Graph Folder")

args = parser.parse_args()

if args.test:
    create_local_random_dag(args)
else:
    main(args)
