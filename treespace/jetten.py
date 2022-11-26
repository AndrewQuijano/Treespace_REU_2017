import networkx as nx
from networkx import get_node_attributes, DiGraph, Graph
import platform

from treespace.utils import maximum_matching_all, is_omnian, is_reticulation
from treespace.drawing import draw_bipartite

plt = platform.system()


def is_tree_based(graph: DiGraph, name=None, draw=False) -> bool:
    jetten_bipartite_graph = jetten_bipartite(graph)
    unmatched_omnian = jetten_graph(jetten_bipartite_graph, name, draw)
    return len(unmatched_omnian) == 0


def jetten_bipartite(graph: DiGraph) -> Graph:
    jetten = nx.Graph()
    omnians = []
    reticulation = []

    # Fill the nodes up
    for node in graph.nodes():
        # set Reticulations
        if is_reticulation(graph, node):
            reticulation.append(node)
            jetten.add_node('R-' + node, biparite=1)

        # set Omnians
        if is_omnian(graph, node):
            omnians.append(node)
            jetten.add_node(node, biparite=0)

    data = get_node_attributes(jetten, 'biparite')
    for source_node, target_node in graph.edges():
        try:
            # source_node is an omnian vertex
            if data[source_node] == 0:
                jetten.add_edge(source_node, 'R-' + target_node)
        except KeyError:
            continue
    return jetten


# Use this for non-binary graph
def jetten_graph(bipartite_graph: Graph, name=None, draw=False) -> set:
    matched_omnians = set()

    try:
        max_match = maximum_matching_all(bipartite_graph)

        if draw:
            if name is None:
                draw_bipartite(bipartite_graph, max_match, graph_name="jetten-bipartite")
            else:
                draw_bipartite(bipartite_graph, max_match, graph_name=name + "-jetten-bipartite")
        omnians = set(n for n, d in bipartite_graph.nodes(data=True) if d['biparite'] == 0)
        is_omnian_node = get_node_attributes(bipartite_graph, 'biparite')
        for source_node, target_node in max_match.items():
            if is_omnian_node[source_node] == 1:
                matched_omnians.add(target_node)
            if is_omnian_node[target_node] == 1:
                matched_omnians.add(source_node)
        # print("matched omnians: " + str(matched_omnians))
        set_minus = omnians - matched_omnians

    except nx.exception.NetworkXPointlessConcept:
        return set()

    return set_minus
