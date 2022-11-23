import os
import unittest

from treespace import enum_trees
from treespace import draw_tree
from treespace import vertex_disjoint_paths
from treespace import is_tree_based
from treespace import maximum_covering_subtree
from treespace import read_matrix


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


class TestTreespace(unittest.TestCase):

    def setUp(self):
        self.answer = read_test_answers()
        self.test_directory = "Graph"
        self.graphs = read_matrix(self.test_directory)
        for fname, graph in self.graphs:
            draw_tree(graph, os.path.join(self.test_directory, fname))

    def test_tree_based(self):
        for fname, graph in self.graphs:
            fname = fname.split('.')[0]
            values = self.answer[fname]
            print("Testing Tree-Based Check on Network: " + fname)
            t = is_tree_based(graph, os.path.join(self.test_directory, fname))
            if t:
                assert values[0] == 1
            else:
                assert values[0] == 0

    def test_max_cst(self):
        for fname, graph in self.graphs:
            fname = fname.split('.')[0]
            values = self.answer[fname]
            print("Testing MAX-CST on Network: " + fname)
            _, eta = maximum_covering_subtree(graph)
            assert values[1] == eta

    def test_spanning_tree(self):
        for fname, graph in self.graphs:
            fname = fname.split('.')[0]
            values = self.answer[fname]
            print("Testing Spanning Tree Algorithm on Network: " + fname)
            missing_v1, paths = vertex_disjoint_paths(graph, os.path.join(self.test_directory, fname), draw=True)
            assert values[2] == missing_v1

    def test_enum_tree(self):
        for fname, graph in self.graphs:
            fname = fname.split('.')[0]
            values = self.answer[fname]
            print("Testing Enum Minimal Trees Algorithm on Network: " + fname)
            trees, count = enum_trees(graph, os.path.join(self.test_directory, fname), draw=True)
            assert values[3] == count

    def test_maximum_distance(self):
        pass


if __name__ == '__main__':
    unittest.main()
