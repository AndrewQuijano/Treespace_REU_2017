import matplotlib.colors as mcolors
import networkx as nx
from networkx import DiGraph, MultiDiGraph
from networkx.algorithms.simple_paths import all_simple_edge_paths
from networkx.algorithms.flow import min_cost_flow
from networkx.drawing.nx_pydot import write_dot
from drawing import draw_tree
from copy import deepcopy
import os
from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root


# Input: Rooted Spanning Tree S
# Output: Flow Network used to compute Enum Min Num of Trees
def create_flow_network(s: DiGraph, leaves: set, demand: int, omnian_to_leaves: dict, leaf_weights: dict):
    f = deepcopy(s)
    f.add_node('s', demand=-demand)
    f.add_node('t', demand=demand)

    # Attach root to source
    root = get_root(s)
    f.add_edge('s', root, capacity=demand, weight=0)

    # Attach all leaves to t, capacity should allow for "infinity"
    for leaf in leaves:
        f.add_edge(leaf, 't', capacity=demand, weight=0)

    # Attach all omnians to leaves in t, Note here the cost is NOT 0
    # it now depends on in-degree
    for omnian, leaf_set in omnian_to_leaves.items():
        for leaf in leaf_set:
            f.add_edge(omnian, leaf, capacity=1, weight=leaf_weights[leaf])
    return f


# For all omnian vertices, determine to which leaves they can get to in G
def get_all_leaf_destinations(g: DiGraph, omnians, leaves):
    omnian_map = {}

    # omnian map = {omnian node : L1, L2 (all leaves it can go to)}
    for omnian in omnians:
        omnian_map[omnian] = []

    # Find the paths from Omnian Node to each leaf in N
    for omnian in omnians:
        for leaf in leaves:
            omnian_to_leaf = list(all_simple_edge_paths(g, omnian, leaf))
            if len(omnian_to_leaf) == 0:
                continue
            # If there are is multiple paths to same leaf, just picking any is OK!
            elif len(omnian_to_leaf) >= 1:
                omnian_map[omnian].append(leaf)

    # Compute the expected weight for each incoming leaf...
    # leaf_map = {leaf1 : # of incoming omnians to leaf1, leaf2: # of omnian to incoming leaf2}
    leaf_map = {}
    for leaf in leaves:
        leaf_weight = 0
        for omnian, leaf_destinations in omnian_map.items():
            if leaf in leaf_destinations:
                leaf_weight += 1
        leaf_map[leaf] = leaf_weight
    return omnian_map, leaf_map


# Create the Tree t_0 from the Spanning Tree
# Return Spanning Tree with t_0 removed
# args:
# - Spanning Tree of Network N
# - leaves: leaves of Network N
# - name: Name of Phylogenetic network to assign name to .png files
def first_tree(spanning_tree, leaves: set):
    first = DiGraph()
    root = get_root(spanning_tree)
    nodes = set()

    # Flip edges for leaf to root?
    for leaf in leaves:
        edges = list(all_simple_edge_paths(spanning_tree, root, leaf))[0]
        # print(edges)
        # So path is from leaf to root
        edges.reverse()
        # print(edges)
        for src, tgt in edges:
            first.add_node(src)
            first.add_node(tgt)

            if spanning_tree.out_degree(tgt) <= 1:
                nodes.add(tgt)
            else:
                break

            if spanning_tree.out_degree(src) <= 1:
                nodes.add(src)
            else:
                break
        first.add_edges_from(edges)
        # print("Remove: " + str(nodes))
        for node in nodes:
            spanning_tree.remove_node(node)
        nodes.clear()
    return first


def next_tree(tree_zero: DiGraph, graph: DiGraph, spanning_tree: DiGraph, omnian_to_leaf_mapping: dict):
    selected_leaf_set = set()
    delete_omnians = set()
    root = get_root(graph)
    network_leaves = get_leaves(tree_zero)
    tree = DiGraph()

    for omnian, leaf in omnian_to_leaf_mapping.items():
        if leaf in selected_leaf_set:
            continue
        selected_leaf_set.add(leaf)

        # create full path root -> omnian -> leaf
        first_part = list(all_simple_edge_paths(spanning_tree, root, omnian))[0]
        second_part = list(all_simple_edge_paths(graph, omnian, leaf))[0]
        tree.add_edges_from(first_part)
        tree.add_edges_from(second_part)
        delete_omnians.add(omnian)

    # Update current list so you don't recreate trees on accident.
    for omnian in delete_omnians:
        del omnian_to_leaf_mapping[omnian]

    # Check the tree has the full leaf set, if not. add it.
    for leaf in network_leaves - selected_leaf_set:
        extra_path = list(all_simple_edge_paths(tree_zero, root, leaf))[0]
        tree.add_edges_from(extra_path)
    return tree


def enum_trees(g: DiGraph, graph_name: str, draw=False):
    # Start with creating the spanning tree
    _, paths = vertex_disjoint_paths(g)
    spanning_tree = rooted_spanning_tree(g, paths)

    # draw graph and highlight RST
    draw_tree(g, graph_name + '-spanning-tree', highlight_edges=spanning_tree.edges())

    network_leaves = get_leaves(g)
    omnian_leaves = get_leaves(spanning_tree).symmetric_difference(network_leaves)
    demand = len(network_leaves) + len(omnian_leaves)
    remaining_path, leaf_weights = get_all_leaf_destinations(g, omnian_leaves, network_leaves)

    f = create_flow_network(spanning_tree, network_leaves, demand, remaining_path, leaf_weights)
    flows = min_cost_flow(f)
    all_incoming_flow = []
    omnian_to_leaf = dict()
    for src, flow in flows.items():
        if src in network_leaves:
            for sink_node, incoming_flow in flow.items():
                # print(src, '->', sink_node, ' has ', value, ' units coming in')
                all_incoming_flow.append(incoming_flow)
        if src in omnian_leaves:
            for leaf_node, value in flow.items():
                if value == 1:
                    # print("omnian", src, "goes to leaf", leaf_node)
                    omnian_to_leaf[src] = leaf_node

    tree_zero = first_tree(spanning_tree, network_leaves)
    tree_list = [tree_zero]

    # Create directory of each tree and place tree 0 dot
    tree_directory = graph_name + '_trees/'
    os.makedirs(tree_directory, exist_ok=True)

    while len(omnian_to_leaf) != 0:
        tree = next_tree(tree_zero, g, spanning_tree, omnian_to_leaf)
        tree_list.append(tree)
        # print("Tree made: " + str(list(spanning_tree.nodes())))

    combine_trees(tree_list, tree_directory, draw)
    return tree_list, max(all_incoming_flow)


# https://stackoverflow.com/questions/62512760/how-to-label-edges-of-a-multigraph-in-networkx-and-matplotlib
def combine_trees(trees, tree_dir, draw=False):
    combined_tree = MultiDiGraph()
    colors = mcolors.TABLEAU_COLORS.keys()
    i = 0
    for tree, color in zip(trees, colors):
        write_dot(tree, tree_dir + 'tree_' + str(i) + '.dot')
        color = color.replace('tab:', '')
        # print("Drawing edges with color", color)
        for source, target in tree.edges():
            combined_tree.add_edge(source, target, color=color)
        if draw:
            draw_tree(tree, tree_dir + 'tree_' + str(i))
            draw_tree(combined_tree, tree_dir + 'combined_graph_' + str(i) + '.png')
        i += 1
    write_dot(combined_tree, tree_dir + 'combined_tree.dot')
    if draw:
        p = nx.drawing.nx_pydot.to_pydot(combined_tree)
        p.write_png(tree_dir + 'combined_tree.png')
