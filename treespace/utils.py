from networkx import DiGraph
from os import listdir
from os.path import isfile, join
from networkx import topological_sort
from operator import itemgetter
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


# Gets the Longest Path in a DAG, I am setting all as weight 1.
# https://www.geeksforgeeks.org/find-longest-path-directed-acyclic-graph/
def get_max_distances(graph: DiGraph, source=None):
    keys = list(graph.nodes())
    values = len(keys) * [float("-inf")]
    distances = dict(zip(keys, values))
    max_paths = dict()
    for node in keys:
        max_paths[node] = []
    vertices = topological_sort(graph)
    # Always is the longest path from the root
    if source is None:
        source = get_root(graph)
    distances[source] = 0
    for u in vertices:
        for v in graph.successors(u):
            if distances[v] < distances[u] + 1:
                distances[v] = distances[u] + 1
                max_paths[v].append(u)
                max_paths[v].extend(max_paths[u])
                # print(max_paths[v])
                # Select longer path, delete the other...
                if max_paths[v].count(source) != 1:
                    start = 0
                    end = 0
                    index = []
                    size = []
                    for node in max_paths[v]:
                        if node == source:
                            if start == 0:
                                index.append((start, end))
                                size.append(end - start + 1)
                            else:
                                index.append(end - start + 1)
                                size.append(end - start)
                            start = end
                        end += 1
                    # Delete shorter path
                    max_size = max(size)
                    index.remove(index[size.index(max_size)])
                    path = max_paths[v]
                    for idx in index:
                        del path[idx[0]:idx[1] + 1]

    # Set -Inf to Inf
    for node in keys:
        if distances[node] < 0:
            distances[node] = float("inf")

    # Check longest paths
    # for node, max_path in max_paths.items():
    #    max_path.reverse()
    #    print("Maximum path to node: " + node + " is: " + str(max_path))
    return distances


# Arguments
# graph - the DAG being analyzed
# target nodes - Provide a list of nodes in the graph
# Return - out of all the nodes listed in 'target nodes' which one is closest to the root?
# If there is a tie-breaker, just pick one randomly.
# The node count variable exists because in treespace.py
def root_path(graph: DiGraph, target_nodes: list, distances=None, source=None, longest_path=True):
    if len(target_nodes) == 1:
        return target_nodes[0]
    if distances is None:
        distances = get_max_distances(graph, source)

    # Break the tie by checking if any of its children are farther than expected
    node_child_map = dict()
    for node in target_nodes:
        children = list(graph.successors(node))
        if len(children) == 1:
            node_child_map[node] = distances[children[0]]
        else:
            node_child_map[node] = max(itemgetter(*children)(distances))

    if longest_path:
        node_child_map = sorted(node_child_map.items(), key=lambda x: x[1], reverse=True)
    else:
        node_child_map = sorted(node_child_map.items(), key=lambda x: x[1], reverse=False)

    for node in node_child_map:
        return node[0]


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


# -------------------------------Read all Matrix from input------------------------------------
# Read adjacency list, use the same structure as what is randomly generated.
def read_adjacency_list(adjacency_list_file: str) -> DiGraph:
    g = DiGraph()
    with open(adjacency_list_file, 'r') as fd:
        for line in fd:
            source, target = line.strip().split(' ')
            g.add_edge(source, target)
    return g
