from networkx import DiGraph, Graph
from networkx import all_simple_paths
from networkx import get_node_attributes
from misc import get_root, maximum_matching_all, get_leaves
from drawing import draw_bipartite
import platform
plt = platform.system()


# input is a DAG - Phylogenetic Network
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: G_N
def build_francis_bipartite(graph):
    # Build V1 and V2
    francis = Graph()
    for node in graph.nodes():
        francis.add_node(node, biparite=0)
        francis.add_node('V2-' + node, biparite=1)

    data = get_node_attributes(francis, 'biparite')
    for s, t in graph.edges():
        try:
            # s is in V_1
            if data[s] == 0:
                francis.add_edge(s, 'V2-' + t)
        except KeyError:
            continue
    return francis


# Input: DAG - Phylogenetic Network
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# output: vertex disjoint paths used to make spanning tree
def vertex_disjoint_paths(graph, name=None):
    matches = []
    missing_v1 = []
    u2 = []
    francis = build_francis_bipartite(graph)
    max_matchings = maximum_matching_all(francis)
    if plt == "Linux":
        if name is None:
            draw_bipartite(francis, max_matchings, "francis-bipartite")
        else:
            draw_bipartite(francis, max_matchings, name + "francis-bipartite")
    data = get_node_attributes(francis, 'biparite')
    for s, t in max_matchings.items():
        # s is in V_2
        if data[s] == 1:
            matches.append((s[3:], t))
            u2.append(s[3:])
            missing_v1.append(t)
        # t is in V_2
        if data[t] == 1:
            matches.append((s, t[3:]))
            u2.append(t[3:])
            missing_v1.append(s)

    # Build set of Vertex-disjoint-paths
    nodes = list(graph.nodes())
    paths = []
    # Build all Vertex Disjoint paths
    # First ensure that U2 contains all values not matched in V_2
    u2 = list(set(nodes) - set(u2))
    missing_v1 = list(set(nodes) - set(missing_v1))
    # print("Unmatched V_1 (including leaves): " + str(missing_v1))
    # print("Unmatched V_2: " + str(u2))
    # Now start making paths!
    for u in u2:
        # You do delete matches, so you need to pass a copy
        paths.append(build_path(u, matches.copy()))
    # Exclude leaves to know number of new leaves
    leaves = get_leaves(graph)
    missing_v1 = list(set(missing_v1) - set(leaves))
    # print("Unmatched V_1 (without leaves): " + str(missing_v1))
    return missing_v1, paths


# Input: Maximum matching of G_N
# Helper function for rooted_spanning_tree and starting_match
# Output: Next element in path
def get_next_node(u, matches):
    for match in matches:
        if match[0] == u:
            matches.remove(match)
            return match[1]
    return None


# Input: Maximum matching of G_N
# Helper function for rooted_spanning_tree
# Output: Output maximum path from maximum matching starting at vertex u
def build_path(u, matches):
    max_path = list()
    new_vertex = u
    max_path.append(u)
    while True:
        new_vertex = get_next_node(new_vertex, matches)
        if new_vertex is None:
            return max_path
        else:
            max_path.append(new_vertex)


# Input: disjoint paths from vertex_disjoint_paths
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: rooted spanning tree
def rooted_spanning_tree(graph, paths):
    root = get_root(graph)
    for path in paths:
        if root in path:
            continue
        else:
            parents = list(graph.predecessors(path[0]))
            path.insert(0, parents[0])

    # Build Spanning Tree
    spanning_tree = DiGraph()
    for path in paths:
        spanning_tree.add_nodes_from(path)
        edges = []
        for i in range(len(path) - 1):
            edges.append((path[i], path[i + 1]))
        spanning_tree.add_edges_from(edges)
    return spanning_tree


# Input: Spanning Tree S
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: tree-based network N'
def tree_based_network(spanning_tree, leaves=None):
    if leaves is None:
        leaves = get_root(spanning_tree)
    leaf_count = 0
    paths = get_paths(spanning_tree)
    for path in paths:
        if not path[len(path) - 1] in leaves:
            node = 'new-leaf-' + str(leaf_count)
            spanning_tree.add_node(node)
            spanning_tree.add_edge(path[len(path) - 1], node)
            leaf_count += 1
    return spanning_tree


# Input: Spanning Tree S
# Helper function for tree_based_network
# Output: All paths in tree S
def get_paths(spanning_tree):
    paths = []
    roots = []
    leaves = []
    for node in spanning_tree.nodes():
        if spanning_tree.in_degree(node) == 0:  # it's a root
            roots.append(node)
        elif spanning_tree.out_degree(node) == 0:  # it's a leaf
            leaves.append(node)

    for root in roots:
        for leaf in leaves:
            for path in all_simple_paths(spanning_tree, root, leaf):
                paths.append(path)
    return paths
