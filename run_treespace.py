#!/usr/bin/env python3

import argparse
import os
import shutil
from os import listdir
from os.path import isfile, join

from Bio import Phylo
from treespace.create_trees import enum_trees
from treespace.drawing import draw_tree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from treespace.jetten import is_tree_based
from treespace.max_cst import maximum_covering_subtree
from treespace.utils import read_adjacency_list, create_dag, path_to_edges

import subprocess


# Used by both offline and online method to analyze metrics of graphs, and store output
def analyze_generated_graphs(input_dir: str, is_newick: bool, draw_image: bool):
    list_of_network_files = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
    output_image_dir = os.path.join(input_dir, 'images')
    if os.path.exists(output_image_dir):
        shutil.rmtree(output_image_dir)
    os.makedirs(output_image_dir, exist_ok=True)

    # Create Headers of CSV results like answers.csv
    metric_path = os.path.join(output_image_dir, "metrics.csv")
    with open(metric_path, 'w+') as fd:
        fd.write('graph,is_tree_based,max_cst,spanning_tree,rooted_tree\n')

    for network_file in list_of_network_files:
        if is_newick:
            graph = Phylo.read(join(input_dir, network_file), 'newick')
            graph = Phylo.to_networkx(graph)
            graph = create_dag(graph)
        else:
            graph = read_adjacency_list(join(input_dir, network_file))

        network_name = network_file.split('.')[0]
        print("Opening the phylogenetic network: " + network_name)
        graph_drawing_location = os.path.join(output_image_dir, network_name)

        # Get Metrics and Print, these parts are already known
        tree_based = is_tree_based(graph)
        _, eta = maximum_covering_subtree(graph, graph_drawing_location, draw_image)
        missing_v1, paths = vertex_disjoint_paths(graph, graph_drawing_location, draw_image)

        # Print Spanning Tree and New Leaf network
        spanning_tree = rooted_spanning_tree(graph, paths)

        # draw_tree(spanning_tree, graph_drawing_location + '-spanning-tree')
        # draw_tree(graph, graph_drawing_location, highlight_edges=spanning_tree.edges())
        draw_tree(graph, graph_drawing_location + '-initial-disjoint-paths', highlight_edges=path_to_edges(paths))

        new_tree_based_network = tree_based_network(graph, spanning_tree)
        draw_tree(new_tree_based_network, graph_drawing_location + '-spanning-tree-with-leaves')

        # TODO: Keep working on this research question, I think you are getting close
        tree_list = []
        # tree_list = enum_trees(graph, graph_drawing_location, draw_image)

        with open(metric_path, 'a+') as metric:
            if tree_based:
                metric.write(network_name + ',1,' + str(eta) + ',' + str(missing_v1) + ',' + str(len(tree_list)) + '\n')
            else:
                metric.write(network_name + ',0,' + str(eta) + ',' + str(missing_v1) + ',' + str(len(tree_list)) + '\n')


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
        subprocess.call(['mv', random_network + '.txt', input_dir])
    return input_dir


def main():
    parser = argparse.ArgumentParser(prog='A python program that can run algorithms used to '
                                          'compute Phylogenetic network metrics')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('--draw', '-d', dest='draw', action='store_true',
                        help="Draw all Bipartite Graphs, Trees, etc.")

    # Collect for arguments on generating random graphs
    # num_leaves=10, num_reticulation=5, num_dataset=10
    parser.add_argument('--leaves', '-l', nargs='?', dest='leaves', action='store',
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
    group.add_argument('--generate', dest='generate', action='store_true',
                       help="Generate a new folder with random binary phylogenetic networks and collect metrics")

    args = parser.parse_args()

    if args.generate:
        new_dir = create_local_random_dag(args.leaves, args.num_reticulation, args.num_dataset)
        analyze_generated_graphs(new_dir, False, args.draw)
    else:
        analyze_generated_graphs(args.dir, args.newick, args.draw)


if __name__ == '__main__':
    main()
