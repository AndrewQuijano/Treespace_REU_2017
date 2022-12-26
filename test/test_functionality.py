import unittest
from run_treespace import analyze_generated_graphs, create_local_random_dag


class TestTreespace(unittest.TestCase):

    def test_using_networks(self):
        analyze_generated_graphs("Graph", False, True)

    def test_using_newick_networks(self):
        analyze_generated_graphs("Phylo", True, True)

    #def test_using_random_networks(self):
    #    new_dir = create_local_random_dag(3, 15, 10)
    #    analyze_generated_graphs(new_dir, False, True)


if __name__ == '__main__':
    unittest.main()
