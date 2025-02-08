from networkx import DiGraph, Graph
from networkx.algorithms.components import connected_components
from networkx.algorithms.bipartite import hopcroft_karp_matching


# ---------------------------Used by Jettan and Drawing--------------------------------
def is_reticulation(network, node) -> bool:
    """
    Check if a node is a reticulation node
    :param network: the graph where the node is in
    :param node: the node to check
    :return: boolean if the node is a reticulation node
    """
    if network.in_degree(node) >= 2 and network.out_degree(node) == 1:
        return True
    else:
        return False


def is_omnian(network, node) -> bool:
    """
    Check if a node is an omnian node
    :param network: the graph where the node is in
    :param node: the node to check
    :return: boolean is the node is an omnian node
    """
    for child in network.successors(node):
        if not is_reticulation(network, child):
            return False
    if network.out_degree(node) != 0:
        return True
    else:
        return False


# ---------------------------Random useful general graph stuff-------------------------
def maximum_matching_all(network: Graph) -> dict:
    """
    Complete maximum matching on all connected components of a graph.
    This is needed if a graph is disconnected.
    :param network: The input graph
    :return: the maximum matching of the graph
    """
    matches = dict()
    parts = connected_components(network)
    for conn in parts:
        sub = network.subgraph(conn)
        max_match = hopcroft_karp_matching(sub)
        matches.update(max_match)
    return matches


def get_leaves(network):
    """
    Get all leaf nodes of a phylogenetic network
    :param network: input network
    :return: the set of all leaves in the network
    """
    leaves = set()
    for v in network.nodes():
        if network.out_degree(v) == 0:
            leaves.add(v)
    return leaves


def get_root(network):
    """
    Get the root of a phylogenetic network.
    Throws an error if there are multiple roots.
    :param network:
    :return:
    """
    roots = []
    for v in network.nodes():
        if network.in_degree(v) == 0:
            roots.append(v)
    if len(roots) == 0:
        return None
    if len(roots) == 1:
        return roots[0]
    else:
        print("Found Multiple Roots...Un-rooted Metrics not implemented: " + str(roots))
        raise NotImplementedError


def get_all_roots(graph) -> set:
    """
    Get all the roots of a graph
    :param graph:
    :return: set of all nodes with in-degree 0
    """
    roots = set()
    for v in graph.nodes():
        if graph.in_degree(v) == 0:
            roots.add(v)
    return roots


def path_to_edges(paths: list) -> list:
    """
    Convert a list of paths to a list of edges
    :param paths: a List of paths [[1,2,3],[4,5,6]]
    :return: a List of edges [(1,2),(2,3),(4,5),(5,6)]
    """
    edge_list = []
    for path in paths:
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            edge_list.append(edge)
    return edge_list


def create_dag(g: Graph) -> DiGraph:
    """
    This only works for rooted networks generated from BioPhylo and from Newick Format
    :param g: a newick - networkx undirected phylogenetic tree.
    :return: The same networkx graph, but directed so the algorithms work as expected...
    """
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


def read_adjacency_list(adjacency_list_file: str) -> DiGraph:
    """
    Read the adjacency list text file, use the same structure as what is randomly generated.
    :param adjacency_list_file:
    :return: A graph based on the adjacency list
    """
    g = DiGraph()
    with open(adjacency_list_file, 'r') as fd:
        for line in fd:
            source, target = line.strip().split(' ')
            g.add_edge(source, target)
    return g
