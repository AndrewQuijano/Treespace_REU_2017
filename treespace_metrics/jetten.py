import networkx as nx
from networkx import get_node_attributes, DiGraph, Graph
import platform

from treespace_metrics.utils import maximum_matching_all, is_omnian, is_reticulation
from treespace_metrics.drawing import draw_bipartite

plt = platform.system()


def is_tree_based(network: DiGraph, name=None, draw=False) -> bool:
    """
    Read the paper "Nonbinary tree-based phylogenetic networks' by Laura Jetten and Leo van Iersel".
    The complete algorithm that checks if a network is tree-based.

    Args:
        network (DiGraph): Input phylogenetic network N.
        name (str, optional): The name of the graph, used to save output images of the network. Defaults to None.
        draw (bool, optional): Whether to draw the bipartite graph. Defaults to False.

    Returns:
        bool: True if the network is tree-based, False otherwise.
    """
    jetten_bipartite_network = jetten_bipartite(network)
    unmatched_omnian = jetten_network(jetten_bipartite_network, name, draw)
    return len(unmatched_omnian) == 0


def jetten_bipartite(network: DiGraph) -> Graph:
    """
    Read the paper "Nonbinary tree-based phylogenetic networks' by Laura Jetten and Leo van Iersel".
    Take an input phylogenetic network N and build the bipartite graph used by Jetten et al.

    Args:
        network (DiGraph): The input phylogenetic network.

    Returns:
        Graph: A bipartite graph which will be used for the next step of the algorithm.
    """
    jetten = Graph()
    omnians = []
    reticulation = []

    # Fill the nodes up
    for node in network.nodes():
        # set Reticulations
        if is_reticulation(network, node):
            reticulation.append(node)
            jetten.add_node('R-' + node, biparite=1)

        # set Omnians
        if is_omnian(network, node):
            omnians.append(node)
            jetten.add_node(node, biparite=0)

    data = get_node_attributes(jetten, 'biparite')
    for source_node, target_node in network.edges():
        try:
            # source_node is an omnian vertex
            if data[source_node] == 0:
                jetten.add_edge(source_node, 'R-' + target_node)
        except KeyError:
            continue
    return jetten


def jetten_network(bipartite_network: Graph, name=None, draw=False) -> set:
    """
    Use this function to check if the network is tree-based by completing the maximum matching.
    This function will return the unmatched omnian nodes in the network from maximum matching, and also draw the bipartite graph.

    Args:
        bipartite_network (Graph): The bipartite graph generated from the input phylogenetic network.
        name (str, optional): The name of the output file with the bipartite graph. Defaults to None.
        draw (bool, optional): Whether to draw the bipartite graph. Defaults to False.

    Returns:
        set: The unmatched omnian nodes in the network from maximum matching.
    """
    matched_omnians = set()

    try:
        max_match = maximum_matching_all(bipartite_network)

        if draw:
            if name is None:
                draw_bipartite(bipartite_network, max_match, graph_name="jetten-bipartite")
            else:
                draw_bipartite(bipartite_network, max_match, graph_name=name + "-jetten-bipartite")
        omnians = set(n for n, d in bipartite_network.nodes(data=True) if d['biparite'] == 0)
        is_omnian_node = get_node_attributes(bipartite_network, 'biparite')
        for source_node, target_node in max_match.items():
            if is_omnian_node[source_node] == 1:
                matched_omnians.add(target_node)
            if is_omnian_node[target_node] == 1:
                matched_omnians.add(source_node)
        set_minus = omnians - matched_omnians

    except nx.exception.NetworkXPointlessConcept:
        return set()

    return set_minus
