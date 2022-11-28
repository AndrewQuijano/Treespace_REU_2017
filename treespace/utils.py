from networkx import DiGraph
from networkx import is_directed
from networkx.algorithms.components.weakly_connected import weakly_connected_components
from networkx.algorithms.components import connected_components
from networkx.algorithms.bipartite import hopcroft_karp_matching


# ---------------------------Used by Jettan and Drawing--------------------------------
def is_reticulation(graph, node) -> bool:
    if graph.in_degree(node) >= 2 and graph.out_degree(node) == 1:
        return True
    else:
        return False


def is_omnian(graph, node) -> bool:
    for child in graph.successors(node):
        if not is_reticulation(graph, child):
            return False
    if graph.out_degree(node) != 0:
        return True
    else:
        return False


# ---------------------------Random useful general graph stuff-------------------------
def maximum_matching_all(graph) -> dict:
    matches = dict()
    if is_directed(graph):
        parts = weakly_connected_components(graph)
    else:
        parts = connected_components(graph)
    for conn in parts:
        sub = graph.subgraph(conn)
        max_match = hopcroft_karp_matching(sub)
        matches.update(max_match)
    return matches


def get_leaves(graph):
    leaves = set()
    for v in graph.nodes():
        if graph.out_degree(v) == 0:
            leaves.add(v)
    return leaves


def get_root(graph):
    roots = []
    for v in graph.nodes():
        if graph.in_degree(v) == 0:
            roots.append(v)
    if len(roots) == 0:
        return None
    if len(roots) == 1:
        return roots[0]
    else:
        print("Found Multiple Roots...Un-rooted Metrics not implemented: " + str(roots))
        raise NotImplementedError


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


# Read adjacency list, use the same structure as what is randomly generated.
def read_adjacency_list(adjacency_list_file: str) -> DiGraph:
    g = DiGraph()
    with open(adjacency_list_file, 'r') as fd:
        for line in fd:
            source, target = line.strip().split(' ')
            g.add_edge(source, target)
    return g
