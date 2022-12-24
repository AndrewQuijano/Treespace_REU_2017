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
def analyze_generated_graphs(input_dir: str, is_newick: bool, draw_image: bool):
    list_of_network_files = [f for f in listdir(args.dir) if isfile(join(args.dir, f))]
    output_image_dir = os.path.join(input_dir, 'images')
    os.makedirs(output_image_dir, exist_ok=True)

    # Create Headers of CSV results like answers.csv
    metric_path = os.path.join(output_image_dir, "metrics.csv")
    with open(metric_path, 'w+') as fd:
        fd.write('graph,is_tree_based,max_cst,spanning_tree,rooted_tree\n')

    for network_file in list_of_network_files:
        if is_newick:
            graph = Phylo.read(join(args.dir, network_file), 'newick')
            graph = Phylo.to_networkx(graph)
            graph = create_dag(graph)
        else:
            graph = read_adjacency_list(join(args.dir, network_file))

        network_name = network_file.split('.')[0]
        print("Opening the phylogenetic network: " + network_name)
        graph_drawing_location = os.path.join(output_image_dir, network_name)
        draw_tree(graph, graph_drawing_location)

        # Obtain Metrics and Print
        tree_based = is_tree_based(graph)
        _, eta = maximum_covering_subtree(graph, graph_drawing_location, draw_image)
        missing_v1, paths = vertex_disjoint_paths(graph, graph_drawing_location, draw_image)
        tree_list = enum_trees(graph, graph_drawing_location, draw_image)

        with open(metric_path, 'a+') as metric:
            if tree_based:
                metric.write(network_name + '1,' + str(eta) + ',' + str(missing_v1) + ',' + str(len(tree_list)) + '\n')
            else:
                metric.write(network_name + '0,' + str(eta) + ',' + str(missing_v1) + ',' + str(len(tree_list)) + '\n')


# Creates random Phylogenetic Networks
# These networks are usually tree-based or almost tree-based. I need to make it more random somehow...
# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_local_random_dag(num_leaves: int, num_reticulation: int, num_dataset: int) -> str:
    # Create new phylogenetic networks
    subprocess.call(['./phylo_generator/binary_ntk_generator',
                     str(num_leaves), str(num_reticulation),
                     str(num_dataset)])

    # move all the graphs into a directory
    input_dir = 'output_ret=' + str(num_reticulation) + '_leaves=' + str(num_leaves)
    os.makedirs(input_dir, exist_ok=True)

    for random_network in range(0, num_dataset):
        random_network = "0%d" % random_network
        subprocess.call(['mv', random_network, random_network + '.txt'])
        subprocess.call(['mv', random_network, input_dir])
    return input_dir


parser = argparse.ArgumentParser(prog='A python program that can run algorithms used to '
                                      'compute Phylogenetic network metrics')
group = parser.add_mutually_exclusive_group()
parser.add_argument('--draw', '-d', dest='draw', action='store_true',
                    help="Draw all Bipartite Graphs, Trees, etc.")

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
    new_dir = create_local_random_dag(args.leaves, args.num_reticulation, args.num_dataset)
    analyze_generated_graphs(new_dir, False, args.draw)
else:
    analyze_generated_graphs(args.dir, args.newick, args.draw)
