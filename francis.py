from collections import OrderedDict
from networkx import DiGraph, Graph, all_simple_paths
from networkx import all_simple_edge_paths, get_node_attributes, get_edge_attributes, set_edge_attributes
from misc import get_root, maximum_matching_all, get_leaves
from drawing import draw_bipartite
from networkx import shortest_path_length
from networkx.algorithms.components.weakly_connected import weakly_connected_components
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
def vertex_disjoint_paths(graph, name=None, draw=False):
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
    # print("missing u2: " + str(u2))
    # print("missing v1: " + str(missing_v1))
    # Build all Vertex Disjoint paths
    paths = []
    for u in u2:
        # You do delete matches, so you need to pass a copy
        p = build_path(u, matches.copy())
        paths.append(p)

    # Step 2: Exclude leaves to know number of new leaves
    leaves = get_leaves(graph)
    missing_v1 = len(missing_v1 - set(leaves))
    # print("Unmatched V_1 (without leaves): " + str(missing_v1))

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


def compute_capacity_of_all_children(spanning_tree, node):
    capacity = get_edge_attributes(spanning_tree, "capacity")
    total_capacity = 0
    for child in spanning_tree.successors(node):
        total_capacity += capacity[(node, child)]
    return max(total_capacity, 1)


# Source: https://stackoverflow.com/questions/19849303/does-networkx-keep-track-of-node-depths
def sort_by_depth(graph, root, nodes):
    nodes_map = dict()
    depth_map = shortest_path_length(graph, root)
    for node in nodes:
        nodes_map[node] = depth_map[node]
    sorted_dict = OrderedDict(sorted(nodes_map.items(), key=lambda x: x[1], reverse=False))
    return sorted_dict


def get_other_root(spanning_tree, node):
    parts = list(weakly_connected_components(spanning_tree))
    for part in parts:
        if node in part:
            for root_candidate in part:
                if spanning_tree.in_degree(root_candidate) == 0:
                    return root_candidate


# Input: disjoint paths from vertex_disjoint_paths
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: rooted spanning tree
def rooted_spanning_tree(graph, paths):
    spanning_tree = DiGraph()
    root = get_root(graph)

    # Build Spanning Tree, Disjoint Paths only...
    for path in paths:
        spanning_tree.add_nodes_from(path)
        # Add only the disjoint paths...
        for i in range(len(path) - 1):
            spanning_tree.add_edge(path[i], path[i + 1], capacity=1, weight=0)

    # Pick first thing to connect in paths
    starting_disjoint_paths = []
    for path in paths:
        starting_disjoint_paths.append(path[0])
    depth_and_node_map = sort_by_depth(graph, root, starting_disjoint_paths)

    # Find all edges required to join the paths...
    # Think best you join paths that are deepest in g and work your way up...
    connecting_edges = []

    for target_node, depth in depth_and_node_map.items():
        # Ensure connection path has 1 root path...
        if target_node == root:
            continue
        source_node = None
        for parent in graph.predecessors(target_node):
            source_node = parent
            break
        connecting_edges.append((source_node, target_node))

    # Connect disjoint paths and update flow network as needed...
    for connecting_source, disjoint_target in connecting_edges:
        new_capacity = compute_capacity_of_all_children(spanning_tree, disjoint_target)
        # print("Connecting", connecting_source, disjoint_target, "with capacity", new_capacity)
        spanning_tree.add_edge(connecting_source, disjoint_target, capacity=new_capacity, weight=0)

        # Need to update all predecessors using sum of capacities...
        update_path = list(all_simple_edge_paths(spanning_tree, root, connecting_source))
        if len(update_path) == 0 and connecting_source != root:
            temp_root = get_other_root(spanning_tree, connecting_source)
            update_path = list(all_simple_edge_paths(spanning_tree, temp_root, connecting_source))

        # check all predecessors including connecting_source, increase capacity by 1
        # e.g. (connecting_source, parent), (parent, grandparent), ..., (BLAH, root) or root of sub-tree.
        for path in update_path:
            path.reverse()
            for source, target in path:
                updated_capacity = compute_capacity_of_all_children(spanning_tree, target)
                attrs = {(source, target): {"capacity": updated_capacity}}
                # print("Update attribute", attrs)
                set_edge_attributes(spanning_tree, attrs)
    return spanning_tree


# Input: Spanning Tree S and the original Network N
# Taken from "New Characterisations of Tree-Based Networks and
# Proximity Measures"
# Output: tree-based network N'
def tree_based_network(spanning_tree, graph):
    leaves = get_leaves(graph)
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
