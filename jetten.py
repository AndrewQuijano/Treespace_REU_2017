import networkx as nx
from misc import maximum_matching_all
from networkx import get_node_attributes
from drawing import draw_bipartite
import platform

plt = platform.system()


def is_tree_based(graph, name=None, draw=False):
    unmatched_omnian = jetten_graph(graph, name, draw)
    if len(unmatched_omnian) == 0:
        return True
    else:
        # print("unmatched omnian nodes: " + str(unmatched_omnian))
        return False


def get_omnians(graph):
    omnians = []
    for node in graph.nodes():
        if is_omnian(graph, node):
            omnians.append(node)
    return omnians


def is_reticulation(graph, node):
    if graph.in_degree(node) >= 2 and graph.out_degree(node) == 1:
        return True
    else:
        return False


def is_omnian(graph, node):
    for child in graph.successors(node):
        if not is_reticulation(graph, child):
            return False
    if graph.out_degree(node) != 0:
        return True
    else:
        return False


def jetten_bipartite(graph):
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
    for s, t in graph.edges():
        try:
            # s is an omnian vertex
            if data[s] == 0:
                jetten.add_edge(s, 'R-' + t)
        except KeyError:
            # If you have a Leaf or Tree Vertex, it might not be Omnian or Reticulation...
            # print("Key Error: " + s + " OR " + t)
            continue
    # print("Omnians: " + str(omnians))
    # print("Reticulation: " + str(reticulation))
    return jetten


# Use this for non-binary graph
def jetten_graph(graph, name=None, draw=False):
    matched_omnians = set()

    try:
        jetten = jetten_bipartite(graph)
        max_match = maximum_matching_all(jetten)

        if draw:
            if name is None:
                draw_bipartite(jetten, max_match, graph_name="-jetten-bipartite")
            else:
                draw_bipartite(jetten, max_match, graph_name=name + "-jetten-bipartite")
        omnians = set(n for n, d in jetten.nodes(data=True) if d['biparite'] == 0)
        data = get_node_attributes(jetten, 'biparite')
        for s, t in max_match.items():
            if data[s] == 1:
                matched_omnians.add(t)
            if data[t] == 1:
                matched_omnians.add(s)
        # print("matched omnians: " + str(matched_omnians))
        set_minus = omnians - matched_omnians

    except nx.exception.NetworkXPointlessConcept:
        return list()

    return list(set_minus)
