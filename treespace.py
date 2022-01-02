#!/usr/bin/env python3

import argparse
import os
import zipfile
from os import listdir
from os.path import isfile, join, basename

from Bio import Phylo
from networkx import DiGraph, Graph
from networkx import is_directed

from create_trees import enum_trees
from drawing import draw_tree
from francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from jetten import is_tree_based
from max_cst import maximum_covering_subtree
from utils import read_matrix, read_adjacency_list

import subprocess
import requests


# Creates random Phylogenetic Networks
# These networks are usually tree-based or almost tree-based. I need to make it more random somehow...
# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_random_dag(arg_vector: argparse):
    # Get graphs, query the site and download ZIP random_network...
    url = 'http://phylnet.univ-mlv.fr/tools/randomNtkGenerator-results.php?num_leaves=' \
          + str(arg_vector.num_leaves) + \
          "&num_ret=" + str(arg_vector.num_reticulation) + \
          "&num_datasets=" + str(arg_vector.num_dataset)
    r = requests.get(url)
    # To download, the URL is in a function...
    link = None
    for line in r.text.split('\n'):
        if "#link" in line:
            link = line.strip()
    new_url = link.split('<')[1].split('>')[0].split('=')[1]
    new_url = new_url[2:len(new_url) - 1]
    zip_random_network = basename(new_url)
    get_zip = "http://phylnet.univ-mlv.fr/tools/bin/userdata/" + zip_random_network
    print("Writing Contents to:", zip_random_network)
    r = requests.get(get_zip)
    with open(zip_random_network, 'wb') as fd:
        fd.write(r.content)

    # Unzip and build graph, automatically creates random_network...
    try:
        with zipfile.ZipFile(zip_random_network, "r") as zip_ref:
            zip_ref.extractall(".")
    except zipfile.BadZipFile:
        print("As of 11/9/2021 the website now just doesn't return ZIP random_networks")
        return

    output_dir = 'output_ret=' + str(arg_vector.num_reticulation) + '_leaves=' + str(arg_vector.num_leaves)
    analyze_generated_graphs(arg_vector.num_dataset, output_dir)
    subprocess.call(['rm', zip_random_network])


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


# Read answers.csv file which contains graph names and expected value for various metrics
def read_test_answers() -> dict:
    answer_key = dict()
    with open('answers.csv', 'r') as fd:
        next(fd)
        for line in fd:
            line = line.strip().split(',')
            random_network = line[0]
            # Tree-Based, Max-CST Metric, Spanning Tree
            answer_key[random_network] = (int(line[1]), int(line[2]), int(line[3]), int(line[4]))
    return answer_key


def test_maximum_distance():
    pass


# Used for Experiments for Treespace REU Working Group
def test(test_directory="Graph"):
    answer = read_test_answers()
    # Should read in answer.txt for each test graph?
    for fname, g in read_matrix(test_directory):
        fname = fname.split('.')[0]
        values = answer[fname]
        print("Testing on Network: " + fname)

        t = is_tree_based(g, os.path.join(test_directory, fname))
        # 1) Tree-Based, 2) Max-CST Metric, 3) Spanning Tree
        if t:
            assert values[0] == 1
        else:
            assert values[0] == 0
        _, eta = maximum_covering_subtree(g)
        assert values[1] == eta

        missing_v1, paths = vertex_disjoint_paths(g, os.path.join(test_directory, fname), draw=True)
        assert values[2] == missing_v1

        draw_tree(g, os.path.join(test_directory, fname))

        trees, count = enum_trees(g, os.path.join(test_directory, fname), draw=True)
        assert values[3] == count


def main(argv: argparse, directory="Phylo"):
    random_networks = [f for f in listdir(directory) if isfile(join(directory, f))]
    for network in random_networks:
        g = Phylo.read(join(directory, network), 'newick')
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
def create_dag(g: Graph):
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
parser.add_argument('--num', '-n', nargs='?', dest='num_leaves', action='store',
                    help="number of leaves in each graph", const=1, default=10, type=int)
parser.add_argument('--reticulation', '-r', nargs='?', dest='num_reticulation', action='store',
                    help="number of reticulation vertices for each graph", const=1, default=10,
                    type=int)
parser.add_argument('--graphs', '-g', nargs='?', dest='num_dataset', action='store',
                    help="num of random graphs to generate", const=1, default=10, type=int)

# What mode
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
