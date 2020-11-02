import numpy as np
from os import listdir
from os.path import isfile, join
from networkx import topological_sort
from operator import itemgetter
from networkx import is_directed
from networkx.algorithms.components.weakly_connected import weakly_connected_components
from networkx.algorithms.components import connected_components
from networkx.algorithms.bipartite import hopcroft_karp_matching


# ---------------------------Random useful general graph stuff-------------------------
def maximum_matching_all(graph):
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
    leaves = []
    for v in graph.nodes():
        if graph.out_degree(v) == 0:
            leaves.append(v)
    return leaves


def get_root(graph):
    for v in graph.nodes():
        if graph.in_degree(v) == 0:
            return v
    return None


def get_max_distances(graph, source=-1):
    node_count = len(list(graph.nodes()))

    # First delete by type.
    # Delete by priority: type-0, type-1, type-2.
    # If matched, break tie by closest to root
    distances = [float("-inf")] * node_count
    max_paths = []
    for _ in range(node_count):
        max_paths.append([])
    vertices = topological_sort(graph)
    # Always is longest path from the root
    if source < 0:
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
                        if node == 0:
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
    for i in range(len(distances)):
        if distances[i] < 0:
            distances[i] = float("inf")
    # Check longest paths
    # ctr = 0
    # for node in max_paths:
    #    # if multiple 0's you need to fix and pick longest path...
    #    print("Maximum path for node: " + str(ctr) + " is: " + str(node))
    #    ctr += 1
    return distances


# The smaller the number, the closer to the root you are!
# The node count variable exists because in treespace.py
# I do delete nodes, which can screw with the distance computation as some nodes are deleted/index fails.
# So, to compensate, I put the number of nodes in original graph as a potential argument.
def closest_to_root(graph, target_nodes, distances=None, source=-1):
    if distances is None:
        distances = get_max_distances(graph, source)
    if len(target_nodes) == 1:
        return target_nodes[0]
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
def farthest_from_root(graph, target_nodes, distances=None, source=-1):
    if distances is None:
        distances = get_max_distances(graph, source)
    if len(target_nodes) == 1:
        return target_nodes[0]

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
def read_adjacency_list(graph):
    matrix = []
    with open(graph, 'r') as fd:
        # First line tells me number of nodes!
        # nodes: 15 -> 15 nodes in graph!
        n = next(fd)
        n = n.rstrip().split(':')[1]
        n = int(n)
        # Be careful if there are leaves as well!
        for line in fd:
            row = [0] * n
            adj = line.rstrip().split(':')[1]
            if adj:
                if ',' not in adj:
                    row[int(adj)] = 1
                else:
                    for idx in adj.split(','):
                        row[int(idx)] = 1
            matrix.append(row)
    return np.array(matrix, dtype=int)


# Input: list of files in ./Graphs Folder
# Output: list of numpy arrays representing a graph
def read_matrix(directory="./Graphs/"):
    matrices = []
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    for graph in files:
        print("----------------Reading file: " + graph + "--------------")
        # Check the file name if it is an adjacency_list
        if 'list' in graph:
            matrix = read_adjacency_list(directory + graph)
        else:
            matrix = np.loadtxt(directory + graph, dtype=int, delimiter=',')
        matrices.append(matrix)
    return matrices
