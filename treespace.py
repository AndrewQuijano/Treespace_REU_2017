#!/usr/bin/env python3

import argparse
import os
import zipfile
from os import listdir
from os.path import isfile, join, basename

from Bio import Phylo
from networkx import DiGraph
from networkx import is_directed

from create_trees import enum_trees
from drawing import draw_tree
from francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from jetten import is_tree_based
from max_cst import maximum_covering_subtree
from misc import read_matrix

import subprocess
import requests


# Creates random Phylogenetic Networks
# These networks are usually tree-based or almost tree-based. I need to make it more random somehow...
# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_random_dag(arg_vector):
    if arg_vector.num_leaves is None:
        num_leaves = 10
    else:
        num_leaves = arg_vector.num_leaves

    if arg_vector.num_reticulation is None:
        num_reticulation = 5
    else:
        num_reticulation = arg_vector.num_reticulation

    if arg_vector.num_dataset is None:
        num_dataset = 10
    else:
        num_dataset = arg_vector.num_dataset

    # Get graphs, query the site and download ZIP file...
    url = "http://phylnet.univ-mlv.fr/tools/randomNtkGenerator-results.php?num_leaves=" + str(num_leaves) + \
          "&num_ret=" + str(num_reticulation) + "&num_datasets=" + str(num_dataset)
    r = requests.get(url)
    # To download, the URL is in a function...
    link = None
    for line in r.text.split('\n'):
        if "#link" in line:
            link = line.strip()
    new_url = link.split('<')[1].split('>')[0].split('=')[1]
    new_url = new_url[2:len(new_url) - 1]
    zip_file = basename(new_url)
    get_zip = "http://phylnet.univ-mlv.fr/tools/bin/userdata/" + zip_file
    print("Writing Contents to:", zip_file)
    r = requests.get(get_zip)
    with open(zip_file, 'wb') as fd:
        fd.write(r.content)

    # Unzip and build graph, automatically creates file...
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(".")

    output_dir = 'output_ret=' + str(num_reticulation) + '_leaves=' + str(num_leaves)
    analyze_generated_graphs(num_dataset, output_dir)
    subprocess.call(['rm', zip_file])


# Used by both offline and online method to analyze metrics of graphs, and store output
def analyze_generated_graphs(dataset_size, output_directory):
    # Create Headers of CSV results like answers.csv
    with open("metrics.csv", 'w+') as fd:
        fd.write('graph,is_tree_based,max_cst,spanning_tree,rooted_tree\n')

    # Create directory to store pictures for analysis...
    os.makedirs(output_directory)

    for file in range(0, dataset_size):
        file = "0%d" % file
        print("Opening the file: " + file)

        graph = DiGraph()
        with open(file, 'r') as fd:
            row = ''
            for line in fd:
                line = line.strip()
                source, target = line.split(' ')
                graph.add_edge(source, target)
            draw_tree(graph, file)
            if is_tree_based(graph):
                row += file + ",1"
            else:
                row += file + ",0"
            # Obtain Metrics and Print
            _, eta = maximum_covering_subtree(graph, file)
            missing_v1, paths = vertex_disjoint_paths(graph, file)
            tree_list, count = enum_trees(graph, file, True)
            row += ',' + str(eta) + ',' + str(missing_v1) + ',' + str(count) + '\n'
            with open("metrics.csv", 'a+') as metric:
                metric.write(row)
            subprocess.call(['mv', file, output_directory])

    subprocess.Popen("mv *.png " + output_directory, shell=True, executable='/bin/bash')
    subprocess.call(['mv', 'metrics.csv', output_directory])


# Creates random Phylogenetic Networks
# These networks are usually tree-based or almost tree-based. I need to make it more random somehow...
# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_local_random_dag(arg_vector):
    if arg_vector.num_leaves is None:
        num_leaves = 10
    else:
        num_leaves = arg_vector.num_leaves

    if arg_vector.num_reticulation is None:
        num_reticulation = 5
    else:
        num_reticulation = arg_vector.num_reticulation

    if arg_vector.num_dataset is None:
        num_dataset = 10
    else:
        num_dataset = arg_vector.num_dataset

    subprocess.call(['./phylo_generator/binary_ntk_generator',
                     str(num_leaves), str(num_reticulation), str(num_dataset)])
    output_dir = 'output_ret=' + str(num_reticulation) + '_leaves=' + str(num_leaves)
    analyze_generated_graphs(num_dataset, output_dir)


def read_test_answers():
    answer_key = dict()
    with open('answers.csv', 'r') as fd:
        next(fd)
        for line in fd:
            line = line.strip().split(',')
            file = line[0]
            # Tree-Based, Max-CST Metric, Spanning Tree
            answer_key[file] = (int(line[1]), int(line[2]), int(line[3]), int(line[4]))
    return answer_key


# Used for Experiments for Treespace REU Working Group
def test():
    answer = read_test_answers()
    # Should read in answer.txt for each test graph?
    for fname, g in read_matrix(directory="./Graph/"):
        fname = fname.split('.')[0]
        values = answer[fname]
        print("Testing on Network: " + fname)

        t = is_tree_based(g, 'Graph/' + fname)
        # 1) Tree-Based, 2) Max-CST Metric, 3) Spanning Tree
        if t:
            assert values[0] == 1
        else:
            assert values[0] == 0
        # _, eta = maximum_covering_subtree(g)
        # assert values[1] == eta

        # Draw original and spanning tree of what is tested...
        # Idea is to see, can Spanning Tree give hints on min number of trees?
        # Also, check if you successfully altered the Jettan et al. Bipartite Graph
        # missing_v1, paths = vertex_disjoint_paths(g, "Graph/" + fname, draw=True)
        # assert values[2] == missing_v1

        # draw_tree(g, "Graph/" + fname)

        trees, count = enum_trees(g, "Graph/" + fname, draw=True)
        assert values[3] == count


def main(argv, directory="./Phylo/"):
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    for network in files:
        g = Phylo.read(directory + network, 'newick')
        g = Phylo.to_networkx(g)
        if not is_directed(g):
            g = create_dag(g)

        # Max-CST, returns MAX-CST and number of vertices removed
        name = network.split('.')[0]
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
            trees, count = enum_trees(g, name, argv.draw)
            print("4- The minimum number of trees required to span Network N is: " + str(count) + " trees")


# Input: g, a newick - networkx undirected phylogenetic tree.
# Output: g-prime, the same networkx graph, but directed so the algorithms work as expected...
# Note this only works for rooted networks generated from BioPhylo and from Newick Format
def create_dag(g):
    g_prime = DiGraph()
    for node in g.nodes(data=False):
        n = getattr(node, 'name')
        c = getattr(node, 'confidence')

        if n is not None:
            g_prime.add_node(str(n))
        else:
            g_prime.add_node(str(c))

    for s, t in g.edges():
        n_1 = getattr(s, 'name')
        c_1 = getattr(s, 'confidence')
        n_2 = getattr(t, 'name')
        c_2 = getattr(t, 'confidence')
        if n_1 is not None:
            if n_2 is not None:
                g_prime.add_edge(str(n_1), str(n_2))
            else:
                g_prime.add_edge(str(n_1), str(c_2))
        else:
            if n_2 is not None:
                g_prime.add_edge(str(c_1), str(n_2))
            else:
                g_prime.add_edge(str(c_1), str(c_2))
    return g_prime


parser = argparse.ArgumentParser(prog='A python program that can run algorithms used to '
                                      'compute Phylogenetic network metrics')
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
parser.add_argument('--num', '-n', dest='num_leaves', action='store',
                    help="number of leaves in each graph", type=int)
parser.add_argument('--reticulation', '-r', dest='num_reticulation', action='store',
                    help="number of reticulation vertices for each graph", type=int)
parser.add_argument('--graphs', '-g', dest='num_dataset', action='store',
                    help="num of random graphs to generate", type=int)

# What mode
group = parser.add_mutually_exclusive_group()
group.add_argument('--test', '-t', dest='test', action='store_true',
                   help="Run Testing on Networks in the Graph Folder")
group.add_argument('--online', '-o', dest='online', action='store_true',
                   help="Online Testing of algorithm on random generated networks")
group.add_argument('--offline', '-off', dest='offline', action='store_true',
                   help="Offline Testing of algorithm on random generated networks")
args = parser.parse_args()

if args.test:
    print("Running Test cases")
    test()
elif args.online:
    print("Running Online Random Graph Generator to run metrics on")
    create_random_dag(args)
elif args.offline:
    print("Running Offline Random Graph Generator to run metrics on")
    create_local_random_dag(args)
else:
    main(args)
