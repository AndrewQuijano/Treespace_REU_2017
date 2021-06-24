#!/usr/bin/env python3

from max_cst import maximum_covering_subtree
from jetten import is_tree_based
from francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from create_trees import enum_trees

from os import listdir
from os.path import isfile, join
from Bio import Phylo
from networkx import is_directed
from drawing import draw_tree
from networkx import DiGraph
from misc import read_matrix
import argparse

import zipfile


# Query this site: http://phylnet.univ-mlv.fr/tools/randomNtkGenerator.php
def create_random_dag(num_leaves=10, num_reticulation=5, num_dataset=10):
    # Get graphs, query the site and download ZIP file...

    # Unzip and build graph, automatically creates file...
    with zipfile.ZipFile("20210624-174025681.zip", "r") as zip_ref:
        zip_ref.extractall("test-trees/")

    graphs = []
    for file in listdir("test-trees/"):
        graph = DiGraph()
        with open("test-trees/" + file, 'r') as fd:
            for line in fd:
                line = line.strip()
                source, target = line.split(' ')
                graph.add_edge(source, target)
            # draw_tree(graph, file)
            # Apply Metrics
            # t, n = maximum_covering_subtree(graph, file, True)
            # missing_v1, paths = vertex_disjoint_paths(graph, file, True)
            # s = rooted_spanning_tree(graph, paths)
            # draw_tree(s, file + '-spanning-tree')
            # if is_tree_based(graph):
            #     print("Tree-Based")
            # else:
            #    print("Not Tree-Based")
        graphs.append(graph)
        write_graph(graph, file)


# Write graph to text file following adjacency list structure shown in read_graph
def write_graph(graph, file_name):
    with open(file_name + '.txt', 'w+') as fd:
        for node in graph.nodes():
            fd.write(str(node) + ':')
            line = ''
            for neighbor in graph.successors(node):
                line += str(neighbor) + ','
            if line.endswith(','):
                line = line[:-1]
            fd.write(line + '\n')


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
        _, eta = maximum_covering_subtree(g)
        assert values[1] == eta

        # Draw original and spanning tree of what is tested...
        # Idea is to see, can Spanning Tree give hints on min number of trees?
        # Also, check if you successfully altered the Jettan et al. Bipartite Graph
        missing_v1, paths = vertex_disjoint_paths(g, "Graph/" + fname)

        assert values[2] == missing_v1

        s = rooted_spanning_tree(g, paths)
        draw_tree(s, "Graph/" + fname + '-spanning-tree')
        draw_tree(g, "Graph/" + fname)

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

group = parser.add_mutually_exclusive_group()
group.add_argument('--test', '-t', dest='test', action='store_true',
                   help="Run Testing on Networks in the Graph Folder")
args = parser.parse_args()
if args.test:
    create_random_dag()
    # test()
else:
    main(args)
