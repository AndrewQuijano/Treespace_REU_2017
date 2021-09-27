from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root
from networkx import DiGraph, get_node_attributes
from networkx.algorithms.simple_paths import all_simple_edge_paths
from networkx.classes import is_empty
from drawing import draw_tree
import uuid
from networkx.algorithms.flow import min_cost_flow
from collections import Counter


# Create the rooted spanning tree (see Francis et al. 2018 paper)
# args: g - original phylogenetic network
def create_rooted_tree(g):
    _, paths = vertex_disjoint_paths(g)
    s = rooted_spanning_tree(g, paths)
    return s


# Starts with a Rooted Spanning Tree (RST) from Francis et al. 2018 paper
# If there are omnian vertices that are leaves, extend the path to a leaf in N.
# args:
# g: Original Phylogenetic Network N
# Spanning_tree: Spanning Tree with T_0 removed
def extend_omnian_to_leaves(g, spanning_tree):
    network_leaves = get_leaves(g)
    # Map uuid -> node name
    uuid_to_node_name = get_node_attributes(spanning_tree, "labels")
    node_to_uuid = {node_label: uuid_id for uuid_id, node_label in uuid_to_node_name.items()}

    omnian_to_leaf_paths = list()

    # Used in the case if there are multiple leaf paths for 1 omnian...
    leaf_usage = dict()
    for leaf in network_leaves:
        leaf_usage[leaf] = 0
    omnian_all_leaf_paths = dict()

    # i = 0
    # Path from omnian in S to leaf in G
    for omnian in get_leaves(spanning_tree):
        # T_0 is NOT removed at first... if the "omnian" is a leaf in N, SKIP!
        node_name = uuid_to_node_name[omnian]
        if node_name in network_leaves:
            # print("Leaf " + str(node_name) + " is NOT an unmatched omnian node!")
            continue

        # Find the paths from Omnian Node to each leaf in N
        for leaf in network_leaves:
            omnian_to_leaf = list(all_simple_edge_paths(g, uuid_to_node_name[omnian], leaf))
            if len(omnian_to_leaf) == 0:
                continue
            # If there are is multiple paths to same leaf, just picking any is OK!
            elif len(omnian_to_leaf) >= 1:
                omnian_to_leaf_paths.append(omnian_to_leaf[0])
        # print("Searching Paths for Omnian: " + labels[omnian])

        # If the omnian only has 1 path to a leaf, just extend the path.
        if len(omnian_to_leaf_paths) == 1:
            path = omnian_to_leaf_paths[0]
            # Update the value that the leaf is getting "one" omnian going to it
            leaf = path[len(path) - 1][1]
            value = leaf_usage[leaf]
            value += 1
            leaf_usage[leaf] = value

            # If the omnian has a path to only 1 leaf, just extend it...
            start = None
            previous = None
            for source_label, target_label in path:
                # print(source_label, target_label)
                if start is None:
                    start = node_to_uuid[source_label]
                    target_uuid = str(uuid.uuid4())
                    spanning_tree.add_node(target_uuid, labels=target_label)
                    spanning_tree.add_edge(start, target_uuid)
                    previous = target_uuid
                else:
                    target_uuid = str(uuid.uuid4())
                    spanning_tree.add_node(target_uuid, labels=target_label)
                    spanning_tree.add_edge(previous, target_uuid)
                    previous = target_uuid
        else:
            # Handle this in a later time if an omnian goes to multiple leaves...
            omnian_all_leaf_paths[omnian] = omnian_to_leaf_paths
            continue

        # Clear paths for next omnian...
        omnian_to_leaf_paths.clear()

    # Sort by value, I want to prioritize paths that needs more "incoming paths"
    leaf_usage = dict(sorted(leaf_usage.items(), key=lambda item: item[1]))

    for leaf, value in leaf_usage.items():
        print("Leaf: " + leaf, " Demand: " + str(value))

    # Handle the situation of omnian to multiple leaves
    # Because it is sorted, the leaves that require paths come first...
    for omnian, path_to_leaves in omnian_all_leaf_paths.items():
        print("For Omnian: " + uuid_to_node_name[omnian])
        print("The following paths are available: " + str(path_to_leaves))

        # Select which leaf the omnian should go to...
        for target_leaf in leaf_usage.keys():
            # Does the leaf exist in any of the paths?
            path_to_leaf = None
            leaf = None
            for path in path_to_leaves:
                leaf = path[len(path) - 1][1]
                print("Path: " + str(path))
                print("The path has leaf: " + str(leaf))
                if target_leaf == leaf:
                    path_to_leaf = path
                    break

            if path_to_leaf is None:
                print("The target leaf: " + target_leaf + " has no path...")
                continue
            else:
                print("Path Selected: " + str(path_to_leaf))

            # Get Value
            incoming_paths_count = leaf_usage[target_leaf]
            # Update value for next iteration...
            value = incoming_paths_count + 1
            leaf_usage[leaf] = value

            # Repeat code to extend the path from omnian to leaf node.
            start = None
            previous = None
            for source_label, target_label in path_to_leaf:
                # print(source_label, target_label)
                if start is None:
                    start = node_to_uuid[source_label]
                    target_uuid = str(uuid.uuid4())
                    spanning_tree.add_node(target_uuid, labels=target_label)
                    spanning_tree.add_edge(start, target_uuid)
                    previous = target_uuid
                else:
                    target_uuid = str(uuid.uuid4())
                    spanning_tree.add_node(target_uuid, labels=target_label)
                    spanning_tree.add_edge(previous, target_uuid)
                    previous = target_uuid
            # Break out when you found that one path
            break
        # To be safe, ensure that the dictionary is sorted by leaf for next paths
        # so the remaining omnians know which path to a leaf should be prioritized
        leaf_usage = dict(sorted(leaf_usage.items(), key=lambda item: item[1]))
        for leaf, value in leaf_usage.items():
            print("Leaf: " + leaf, " Demand: " + str(value))


# In anticipation you will have multiple node labels,
# have all nodes be uuid keys to support multiple same labels!
def convert_to_uuid_keys(network):
    new_graph = DiGraph()
    node_list = dict()
    for source, target in network.edges():
        if source not in node_list:
            src_key = str(uuid.uuid4())
            new_graph.add_node(src_key, labels=source)
            node_list[source] = src_key
        if target not in node_list:
            tgt_key = str(uuid.uuid4())
            new_graph.add_node(tgt_key, labels=target)
            node_list[target] = tgt_key
        new_graph.add_edge(node_list[source], node_list[target])
    # draw_tree(new_graph, "Graph/conversion")
    # print(get_node_attributes(new_graph, "labels"))
    return new_graph


# Get the next Tree_i created from the Rooted Spanning Tree with Extended Omnian vertex
# g - complete network N
# leaves - all leaves in N
# tree_zero, spanning tree which only has omnian leaves. Used to generate new trees
# s- spanning tree only containing 1 path to each leaf in N
def next_tree(tree_zero, spanning_tree, network_leaves):
    nodes = set()
    selected_leaf_set = set()
    tree = DiGraph()
    root = get_root(spanning_tree)
    uuid_to_node_name = get_node_attributes(spanning_tree, 'labels')

    # if Tree_0 has no edges (just created). Record first tree crated from this function
    if is_empty(tree_zero):
        create_tree_zero = True
    else:
        create_tree_zero = False

    # Path from omnian in S to leaf in G
    for leaf in get_leaves(spanning_tree):
        # print("[NEXT TREE] Select Path: " + uuid_to_node_name[root] + " -> " + uuid_to_node_name[leaf])
        full_path = list(all_simple_edge_paths(spanning_tree, root, leaf))[0]
        full_path.reverse()
        leaf = uuid_to_node_name[full_path[0][1]]
        # print("[NEXT TREE] Leaf selected is: " + leaf)

        # for s, t in full_path:
        #    print(uuid_to_node_name[s], uuid_to_node_name[t])

        # Can't have more than 1 path to same leaf of Network N!
        if leaf in selected_leaf_set:
            # print("[NEXT TREE] Skipped, Can't Select Same Leaf Twice! " + str(selected_leaf_set))
            continue

        selected_leaf_set.add(leaf)

        # Append all paths first...
        for src, tgt in full_path:
            if create_tree_zero:
                tree_zero.add_edge(uuid_to_node_name[src], uuid_to_node_name[tgt])
            tree.add_edge(uuid_to_node_name[src], uuid_to_node_name[tgt])

        # print("Path is: " + str(full_path))
        # Repeat the same process from earlier
        for src, tgt in full_path:
            # print(label_attribute[src] + '->' + label_attribute[tgt])
            if spanning_tree.out_degree(tgt) <= 1:
                nodes.add(tgt)
            else:
                break

            if spanning_tree.out_degree(src) <= 1:
                nodes.add(src)
            else:
                break

        # print("Delete: " + str(nodes))
        for node in nodes:
            spanning_tree.remove_node(node)
        nodes.clear()

    # print("Leaves picked: " + str(selected_leaf_set) + ", First Step of T_i is completed")

    # To make it a correct "tree" append all remaining leaves for full leaf set
    # Base this on the first tree generated
    root = get_root(tree_zero)
    for leaf in network_leaves - selected_leaf_set:
        # print("Create Path from: " + root + " -> " + leaf)
        extra_path = list(all_simple_edge_paths(tree_zero, root, leaf))[0]
        tree.add_edges_from(extra_path)
    return tree


# Input: Rooted Spanning Tree G
# Output: Flow Network used to compute Enum Min Num of Trees
def create_flow_network(g, leaves, demand, omnian_to_leaves, leaf_weights, edge_weights):
    f = DiGraph()

    f.add_node('s', demand=-demand)
    f.add_node('t', demand=demand)

    # Attach root to source
    root = get_root(g)
    f.add_edge('s', root, capacity=demand, weight=0)

    # Copy the graph and add capacity and no weight
    # TODO: Should probably pre-computed the needed capacities for edges to be forced...
    for source, target in g.edges():
        f.add_edge(source, target, capacity=1, weight=0)

    # Attach all leaves to t, capacity should allow for "infinity"
    for leaf in leaves:
        f.add_edge(leaf, 't', capacity=demand, weight=0)

    # Attach all omnians to leaves in t, Note here the cost is NOT 0
    # it now depends on in-degree
    for omnian, leaf_set in omnian_to_leaves.items():
        for leaf in leaf_set:
            f.add_edge(omnian, leaf, capacity=1, weight=1000)

    return f


# For all omnian vertices, determine to which leaves they can get to in G
def get_all_leaf_destinations(g, omnians, leaves):
    omnian_map = {}

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
    leaf_map = {}
    for leaf in leaves:
        print(leaf)
        leaf_weight = 0
        for omnian, leaf_destinations in omnian_map.items():
            if leaf in leaf_destinations:
                leaf_weight += 1
        leaf_map[leaf] = leaf_weight
    return omnian_map, leaf_map


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

    print("Get Path 1")
    for root in roots:
        print("root", root)
        for leaf in leaves:
            print("leaf", leaf)
            for path in all_simple_edge_paths(spanning_tree, root, leaf):
                paths.append(path)
                print("path", path)

    capacities = {}
    for path in paths:
        capacities.update(dict(Counter(path)))
    print("cap", capacities)
    return paths


def enum_trees(g, graph_name, draw=False):
    # Start with creating the spanning tree
    spanning_tree = create_rooted_tree(g)
    edge_weights = get_paths(spanning_tree)
    network_leaves = get_leaves(g)
    omnian_leaves = get_leaves(spanning_tree).symmetric_difference(network_leaves)
    demand = len(network_leaves) + len(omnian_leaves)
    remaining_path, leaf_weights = get_all_leaf_destinations(g, omnian_leaves, network_leaves)
    f = create_flow_network(spanning_tree, network_leaves, demand, remaining_path, leaf_weights, edge_weights)
    draw_tree(f, graph_name + '-flow-network')
    flows = min_cost_flow(f)

    for src, flow in flows.items():
        if src in network_leaves:
            for sink_node, value in flow.items():
                print(sink_node, value)

    return None, 5


# create trees, GRAVEYARD
def enum_trees_old(g, graph_name, draw=False):
    # Start with creating the spanning tree
    spanning_tree = create_rooted_tree(g)
    network_leaves = get_leaves(g)

    # Draw Figure 2(a), of network with edges of Rooted Spanning Tree...
    draw_tree(g, graph_name + "_RST_Highlighted", highlight_edges=spanning_tree.edges())

    # Relabel nodes to UUID keys and labels to allow for multiple instances of label!
    # Be sure to also extend the path of omnian nodes to a leaf as well
    spanning_tree = convert_to_uuid_keys(spanning_tree)
    extend_omnian_to_leaves(g, spanning_tree)

    # Draw Figure 2(b), of Spanning Tree with the extended network...
    draw_tree(spanning_tree, graph_name + "_Extended_Spanning_Tree")

    # Confirm all nodes all covered at least once
    all_nodes = set()
    tree_zero = DiGraph()
    i = 0
    tree_list = []

    # Keep cutting paths from spanning tree S to generate T_i
    while True:
        tree = next_tree(tree_zero, spanning_tree, network_leaves)
        tree_list.append(tree)
        if draw:
            draw_tree(tree, graph_name + "_Tree_" + str(i))
        i = i + 1
        all_nodes.update(tree.nodes())

        # If there are no edges in Spanning Tree, there are no paths, terminate loop!
        if is_empty(spanning_tree):
            break

    # Confirm that every node was covered in all the trees...
    assert all_nodes == set(g.nodes())
    return tree_list, len(tree_list)
