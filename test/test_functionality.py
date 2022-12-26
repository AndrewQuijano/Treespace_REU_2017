import unittest
import subprocess


class TestTreespace(unittest.TestCase):

    def test_using_networks(self):
        subprocess.call(['python', 'run_treespace.py', '--dir', 'Graph', '-d'])

    def test_using_newick_networks(self):
        subprocess.call(['python', 'run_treespace.py', '--dir', 'Phylo', '-n'])

    def test_using_random_networks(self):
        subprocess.call(['python', 'run_treespace.py', '--generate', '-l', '3', '-r', '15', '-g', '10'])


if __name__ == '__main__':
    unittest.main()
