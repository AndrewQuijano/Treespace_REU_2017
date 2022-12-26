import unittest
from run_treespace import analyze_generated_graphs, create_local_random_dag


class TestTreespace(unittest.TestCase):

    def test_using_networks(self):
        analyze_generated_graphs("Graph", is_newick=False, draw_image=True)

    def test_using_newick_networks(self):
        analyze_generated_graphs("Phylo", is_newick=True, draw_image=False)

    def test_using_random_networks(self):
        new_dir = create_local_random_dag(3, 15, 10)
        analyze_generated_graphs(new_dir, is_newick=False, draw_image=True)


if __name__ == '__main__':
    unittest.main()
