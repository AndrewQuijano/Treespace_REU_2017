from networkx import DiGraph, Graph, all_simple_paths
from networkx import get_node_attributes
import platform

from treespace.drawing import draw_bipartite
from treespace.utils import get_root, maximum_matching_all, get_leaves

plt = platform.system()


# input is a DAG - Phylogenetic Network
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: G_N
def build_francis_bipartite(graph: DiGraph) -> Graph:
    # Build V1 and V2
    francis = Graph()
    for node in graph.nodes():
        francis.add_node(node, biparite=0)
        francis.add_node('V-' + node, biparite=1)

    data = get_node_attributes(francis, 'biparite')
    for s, t in graph.edges():
        # s is in V_1
        if data[s] == 0:
            francis.add_edge(s, 'V-' + t)
    return francis


# Input: DAG - Phylogenetic Network
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# If used for unmatched omnians, should be starting from UNMATCHED Omnians...
# output: vertex disjoint paths of Bipartite Graph used to make spanning tree
def vertex_disjoint_paths(graph: DiGraph, name=None, draw=False) -> [int, list]:
    francis = build_francis_bipartite(graph)
    max_matchings = maximum_matching_all(francis)

    # Step 1: Compute disjoint paths
    u2 = set()
    matches = []
    nodes = set(graph.nodes())
    missing_v1 = set()

    data = get_node_attributes(francis, 'biparite')
    for s, t in max_matchings.items():
        if data[s] == 0:
            matches.append((s, t[2:]))
            u2.add(t[2:])
            missing_v1.add(s)

    u2 = nodes - u2
    missing_v1 = nodes - missing_v1

    # Build all Vertex Disjoint paths
    paths = []
    for u in u2:
        # You do delete matches, so you need to pass a copy
        p = build_path(u, matches.copy())
        paths.append(p)

    # Step 2: Exclude leaves to know number of new leaves
    leaves = get_leaves(graph)
    missing_v1 = len(missing_v1 - set(leaves))

    if draw:
        if name is None:
            draw_bipartite(francis, max_matchings, "francis-bipartite")
        else:
            draw_bipartite(francis, max_matchings, name + "-francis-bipartite")

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
def rooted_spanning_tree(graph: DiGraph, paths: list) -> DiGraph:
    spanning_tree = DiGraph()
    root = get_root(graph)

    # Build the Spanning Tree from each path
    for path in paths:
        parents = list(graph.predecessors(path[0]))

        if root not in path:
            spanning_tree.add_edge(parents[0], path[0])

        # Add the disjoint path
        for i in range(len(path) - 1):
            spanning_tree.add_edge(path[i], path[i + 1])

    return spanning_tree


# Input: Spanning Tree S and the original Network N
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: tree-based network N
def tree_based_network(graph: DiGraph, spanning_tree: DiGraph) -> DiGraph:
    leaves = get_leaves(graph)
    paths = get_paths(spanning_tree)
    leaf_count = 0
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
def get_paths(spanning_tree) -> list:
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
