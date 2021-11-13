import networkx as nx
from utils import maximum_matching_all
from networkx import get_node_attributes, DiGraph, Graph


def is_tree_based(graph: DiGraph):
    if is_binary(graph):
        # print("Graph is not binary! Zhang's won't work!")
        return None
    unmatched_reticulation = zhang_graph(graph)
    if len(unmatched_reticulation) == 0:
        return True
    else:
        return False


def is_binary(graph):
    for node in graph.nodes():
        if graph.out_degree(node) > 2 or graph.in_degree(node) > 2:
            return False
    return True


# Use this for non-binary graph
def zhang_graph(graph) -> list:

    try:
        zhang = zhang_bipartite(graph)
        max_match = maximum_matching_all(zhang)
        reticulations = [n for n, d in zhang.nodes(data=True) if d['biparite'] == 0]
        data = get_node_attributes(zhang, 'biparite')

        matched_reticulations = set()
        for s, t in max_match.items():
            try:
                if data[s] == 1:
                    matched_reticulations.add(s)
                if data[t] == 1:
                    matched_reticulations.add(t)
            except KeyError:
                continue
    except nx.exception.NetworkXPointlessConcept:
        return list()
    set_minus = set(reticulations) - matched_reticulations
    return list(set_minus)


def zhang_bipartite(graph) -> Graph:
    zhang = nx.Graph()

    for node in graph.nodes():
        # This is a reticulation vertex
        if graph.in_degree(node) == 2 and graph.out_degree(node) == 1:
            zhang.add_node(node, bipartite=0)
            # BE CAREFUL NOT TO ADD RETICULATIONS AGAIN ON OTHER SIDE!
            for parent in graph.predecessors(node):
                if graph.in_degree(parent) == 1 and graph.out_degree(parent) == 2:
                    zhang.add_node(parent, bipartite=1)
                    for e in graph.edges(parent):
                        # Add the edge only if we know the child is a reticulation
                        if graph.in_degree(e[1]) == 2 and graph.out_degree(e[1]) == 1:
                            zhang.add_edge(node, parent)
    return zhang
