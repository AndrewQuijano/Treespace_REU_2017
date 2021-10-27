from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root
from networkx.algorithms.simple_paths import all_simple_edge_paths
from drawing import draw_tree
from networkx.algorithms.flow import min_cost_flow
from copy import deepcopy


# Input: Rooted Spanning Tree S
# Output: Flow Network used to compute Enum Min Num of Trees
def create_flow_network(s, leaves, demand, omnian_to_leaves, leaf_weights):
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
def get_all_leaf_destinations(g, omnians, leaves):
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


def enum_trees(g, graph_name, draw=False):
    # Start with creating the spanning tree
    _, paths = vertex_disjoint_paths(g)
    spanning_tree = rooted_spanning_tree(g, paths)

    if draw:
        draw_tree(spanning_tree, graph_name + '-spanning-tree')

    network_leaves = get_leaves(g)
    omnian_leaves = get_leaves(spanning_tree).symmetric_difference(network_leaves)
    demand = len(network_leaves) + len(omnian_leaves)
    remaining_path, leaf_weights = get_all_leaf_destinations(g, omnian_leaves, network_leaves)

    f = create_flow_network(spanning_tree, network_leaves, demand, remaining_path, leaf_weights)
    flows = min_cost_flow(f)
    all_incoming_flow = []
    for src, flow in flows.items():
        if src in network_leaves:
            for sink_node, value in flow.items():
                # print(src, '->', sink_node, ' has ', value, ' units coming in')
                all_incoming_flow.append(value)
    return [f], max(all_incoming_flow)
