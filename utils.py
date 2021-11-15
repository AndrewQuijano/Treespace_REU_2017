from networkx import DiGraph, Graph
from os import listdir
from os.path import isfile, join
from networkx import topological_sort
from operator import itemgetter
from networkx import is_directed
from networkx.algorithms.components.weakly_connected import weakly_connected_components
from networkx.algorithms.components import connected_components
from networkx.algorithms.bipartite import hopcroft_karp_matching
from typing import Union


# ---------------------------Used by Jettan and Drawing--------------------------------
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


# ---------------------------Random useful general graph stuff-------------------------
def maximum_matching_all(graph: Union[DiGraph: Graph]):
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
        return roots[0]
        # print("Found Multiple Roots...Un-rooted Metrics not implemented: " + str(roots))
        # raise NotImplementedError


def get_max_distances(graph: DiGraph, source=None):
    keys = list(graph.nodes())
    values = len(keys) * [float("-inf")]
    distances = dict(zip(keys, values))
    max_paths = dict()
    for node in keys:
        max_paths[node] = []
    vertices = topological_sort(graph)
    # Always is longest path from the root
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


# The smaller the number, the closer to the root you are!
# The node count variable exists because in treespace.py
# I do delete nodes, which can screw with the distance computation as some nodes are deleted/index fails.
# So, to compensate, I put the number of nodes in original graph as a potential argument.
def closest_to_root(graph: DiGraph, target_nodes: list, distances=None, source=None):
    if len(target_nodes) == 1:
        return target_nodes[0]
    if distances is None:
        distances = get_max_distances(graph, source)

    target_node_distances = itemgetter(*target_nodes)(distances)
    min_dist = min(target_node_distances)

    if target_node_distances.count(min_dist) == 1:
        for target in target_nodes:
            # print("node: " + str(target) + " w/ distance: " + str(distances[target]))
            if distances[target] == min_dist:
                return target
    else:
        # Break the tie by checking if any of its children are farther than expected
        node_child_map = dict()
        for node in target_nodes:
            children = list(graph.successors(node))
            if len(children) == 1:
                node_child_map[node] = distances[children[0]]
            else:
                node_child_map[node] = max(itemgetter(*children)(distances))
        # the node corresponding to higher value gets returned...
        node_child_map = sorted(node_child_map.items(), key=lambda x: x[1], reverse=False)
        for node in node_child_map:
            return node[0]


# The smaller the number, the closer to the root you are!
# treat -1000 as negative infinity
# The node count variable exists because in treespace.py
# I do delete nodes, which can screw with the distance computation as some nodes are deleted/index fails.
# So, to compensate, I put the number of nodes in original graph as a potential argument.
def farthest_from_root(graph: DiGraph, target_nodes: list, distances=None, source=None):
    if len(target_nodes) == 1:
        return target_nodes[0]
    if distances is None:
        distances = get_max_distances(graph, source)
    target_node_distances = itemgetter(*target_nodes)(distances)
    max_dist = max(target_node_distances)

    if target_node_distances.count(max_dist) == 1:
        for target in target_nodes:
            # print("node: " + str(target) + " w/ distance: " + str(distances[target]))
            if distances[target] == max_dist:
                return target
    else:
        # Break the tie by checking if any of its children are farther than expected
        node_child_map = dict()
        for node in target_nodes:
            children = list(graph.successors(node))
            if len(children) == 1:
                node_child_map[node] = distances[children[0]]
            else:
                node_child_map[node] = max(itemgetter(*children)(distances))
        # the node corresponding to higher value gets returned...
        node_child_map = sorted(node_child_map.items(), key=lambda x: x[1], reverse=True)
        for node in node_child_map:
            return node[0]


# -------------------------------Read all Matrix from input------------------------------------
def read_adjacency_list(graph: str) -> DiGraph:
    g = DiGraph()
    with open(graph, 'r') as fd:
        for line in fd:
            source, targets = line.rstrip().split(':')
            if targets == '':
                g.add_node(source.strip())
                continue

            for target in targets.split(','):
                g.add_edge(source.strip(), target.strip())
    return g


# Input: list of files in ./Graphs Folder
# Output: list of numpy arrays representing a graph
def read_matrix(directory="./Graph/") -> list:
    graphs = []
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    for graph in files:
        try:
            # If it is a README, skip this...
            if 'README' in graph:
                continue
            else:
                g = read_adjacency_list(directory + graph)
                graphs.append((graph, g))
        except UnicodeError:
            # Likely because a picture or something was here...?
            continue
    return graphs
