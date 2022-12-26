import os
import unittest

from treespace.jetten import is_tree_based
from treespace.max_cst import maximum_covering_subtree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree, tree_based_network
from treespace.utils import read_adjacency_list
from treespace.drawing import draw_tree
from treespace.create_trees import enum_trees


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
    test_directory = "Graph"

    @classmethod
    def setUpClass(cls):
        cls.answer = read_test_answers()
        cls.graph_files = [f for f in os.listdir(cls.test_directory)
                           if os.path.isfile(os.path.join(cls.test_directory, f))]
    
    def test_tree_based(self):
        for file_name in self.graph_files:
            graph = read_adjacency_list(os.path.join(self.test_directory, file_name))
            file_name = file_name.split('.')[0]
            values = self.answer[file_name]
            t = is_tree_based(graph, os.path.join(self.test_directory, file_name))
            if t:
                assert values[0] == 1
            else:
                assert values[0] == 0

    def test_max_cst(self):
        for file_name in self.graph_files:
            graph = read_adjacency_list(os.path.join(self.test_directory, file_name))
            fname = file_name.split('.')[0]
            values = self.answer[fname]
            _, eta = maximum_covering_subtree(graph, draw=True)
            assert values[1] == eta

    def test_spanning_tree(self):
        for file_name in self.graph_files:
            graph = read_adjacency_list(os.path.join(self.test_directory, file_name))
            fname = file_name.split('.')[0]
            values = self.answer[fname]
            missing_v1, paths = vertex_disjoint_paths(graph, os.path.join(self.test_directory, fname), draw=True)
            assert values[2] == missing_v1
            spanning_tree = rooted_spanning_tree(graph, paths)
            rooted_tree = tree_based_network(graph, spanning_tree)
            draw_tree(rooted_tree)

    def test_enum_tree(self):
        for file_name in self.graph_files:
            graph = read_adjacency_list(os.path.join(self.test_directory, file_name))
            fname = file_name.split('.')[0]
            values = self.answer[fname]
            trees, count = enum_trees(graph, os.path.join(self.test_directory, fname), draw=True)
    #        assert values[3] == count


if __name__ == '__main__':
    unittest.main()
