from typing import Any

from networkx import DiGraph, Graph
from networkx.algorithms.components import connected_components
from networkx.algorithms.bipartite import hopcroft_karp_matching


def is_reticulation(network: DiGraph, node: str) -> bool:
    """
    Check if a node is a reticulation node.

    Args:
        network (DiGraph): The directed graph where the node is located.
        node (str): The node to check.

    Returns:
        bool: True if the node is a reticulation node, False otherwise.
    """
    if network.in_degree(node) >= 2 and network.out_degree(node) == 1:
        return True
    else:
        return False


def is_omnian(network: DiGraph, node: str) -> bool:
    """
    Check if a node is an omnian node.

    Args:
        network (DiGraph): The directed graph where the node is located.
        node (str): The node to check.

    Returns:
        bool: True if the node is an omnian node, False otherwise.
    """
    for child in network.successors(node):
        if not is_reticulation(network, child):
            return False
    if network.out_degree(node) != 0:
        return True
    else:
        return False

def maximum_matching_all(network: Graph) -> dict:
    """
    Compute the maximum matching for all connected components of a graph.

    Args:
        network (Graph): The input graph.

    Returns:
        dict: A dictionary representing the maximum matching of the graph.
    """
    matches = {}
    for conn in connected_components(network):
        sub = network.subgraph(conn)
        matches.update(hopcroft_karp_matching(sub))
    return matches


def get_leaves(network: DiGraph) -> set:
    """
    Get all leaf nodes of a phylogenetic network.

    Args:
        network (DiGraph): The input directed graph.

    Returns:
        set: A set of all leaf nodes in the network.
    """
    leaves = set()
    for v in network.nodes():
        if network.out_degree(v) == 0:
            leaves.add(v)
    return leaves


def get_root(network: DiGraph) -> Any | None:
    """
    Get the root of a phylogenetic network.

    Args:
        network (DiGraph): The input directed graph.

    Returns:
        str: The root node if there is exactly one root, None otherwise.

    Raises:
        NotImplementedError: If multiple roots are found.
    """
    roots = []
    for v in network.nodes():
        if network.in_degree(v) == 0:
            roots.append(v)
    if len(roots) == 0:
        return None
    if len(roots) == 1:
        return roots[0]
    raise NotImplementedError(f"Found multiple roots: {roots}")


def get_all_roots(graph: DiGraph) -> set:
    """
    Get all root nodes of a graph.

    Args:
        graph (DiGraph): The input directed graph.

    Returns:
        set: A set of all nodes with in-degree 0.
    """
    roots = set()
    for v in graph.nodes():
        if graph.in_degree(v) == 0:
            roots.add(v)
    return roots


def path_to_edges(paths: list[list]) -> list[tuple]:
    """
    Convert a list of paths to a list of edges.
    a List of paths [[1,2,3],[4,5,6]] to a List of edges [(1,2),(2,3),(4,5),(5,6)]

    Args:
        paths (list[list]): A list of paths, where each path is a list of nodes.

    Returns:
        list[tuple]: A list of edges represented as tuples.
    """
    edge_list = []
    for path in paths:
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            edge_list.append(edge)
    return edge_list


def create_dag(g: Graph) -> DiGraph:
    """
    Convert an undirected phylogenetic tree to a directed acyclic graph (DAG).
    This only works for rooted networks generated from BioPhylo and from Newick Format

    Args:
        g (Graph): A newick - networkx undirected phylogenetic tree.

    Returns:
        DiGraph: A directed acyclic graph (DAG) representation of the input tree.
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
    Read an adjacency list from a text file and create a directed graph.

    Args:
        adjacency_list_file (str): Path to the adjacency list file.

    Returns:
        DiGraph: A directed graph based on the adjacency list.
    """
    g = DiGraph()
    with open(adjacency_list_file, 'r') as fd:
        for line in fd:
            source, target = line.strip().split(' ')
            g.add_edge(source, target)
    return g