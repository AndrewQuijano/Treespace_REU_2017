#!/usr/bin/env python3
from max_cst import maximum_covering_subtree, count_trees
from jetten import is_tree_based
from francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from os import listdir
from os.path import isfile, join
from Bio import Phylo
from networkx import is_directed
from drawing import draw_tree
from networkx import DiGraph
import platform
from misc import read_matrix
import argparse

plt = platform.system()


def test():
    for fname, g in read_matrix(directory="./Graph/"):
        m, eta = maximum_covering_subtree(g, fname)
        missing_v1, paths = vertex_disjoint_paths(g, fname)
        t = is_tree_based(g, fname)
        c = count_trees(g, fname)
        if fname == 'justin_list.txt':
            assert (eta == 4)
            assert (missing_v1 == 2)
            assert (not t)
            assert (c == 4)


def main(directory="./Phylo/"):
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    for network in files:
        g = Phylo.read(directory + network, 'newick')
        g = Phylo.to_networkx(g)
        if not is_directed(g):
            g = create_dag(g)

        # Max-CST, returns MAX-CST and number of vertices removed
        name = network.split('.')[0]
        print('----' + name + '----')
        t, n = maximum_covering_subtree(g, name)
        print('1- This requires a minimum of ' + str(n) + ' vertices to be removed to become tree-based')
        # Francis et. al. algorithm, returns number of leaves needed and disjoint paths for spanning tree.
        missing_v1, paths = vertex_disjoint_paths(g, name)
        if plt == "Linux":
            s = rooted_spanning_tree(g, paths)
            st = tree_based_network(s)
            draw_tree(st, name + '-spanning-tree')
        print('2- This requires a minimum of ' + str(missing_v1) + ' leaves to be added to become tree-based')
        # Jettan and van Iersel Tree-based
        if is_tree_based(g, name):
            print('3- This is a tree-based phylogenetic network')
        else:
            print('3- This is NOT a tree-based phylogenetic network')
        tree_count = count_trees(g, name)
        print('4- There are ' + str(tree_count) + ' minimum trees that span the entire network')


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


parser = argparse.ArgumentParser(prog='A python program that can run algorithms used to analyze Phylogenetic networks.')
group = parser.add_mutually_exclusive_group()
group.add_argument('--test', action='store_true')
args = parser.parse_args()
if args.test:
    test()
else:
    main()
