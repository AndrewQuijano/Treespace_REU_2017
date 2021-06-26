from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root
from networkx import DiGraph, get_node_attributes
from networkx.algorithms.simple_paths import all_simple_edge_paths
from drawing import draw_tree
import uuid


# Create the rooted spanning tree
# args: g - original phylogenetic network
def create_rooted_tree(g):
    _, paths = vertex_disjoint_paths(g)
    s = rooted_spanning_tree(g, paths)
    return s


# Create the Tree t_0 from the Spanning Tree
# Return Spanning Tree with t_0 removed
# args:
# - Spanning Tree of Network N
# - leaves: leaves of Network N
# - name: Name of Phylogenetic network to assign name to .png files
def first_tree(spanning_tree, leaves, name):
    spanning_tree_copy = spanning_tree.copy()
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

    # For illustration
    draw_tree(spanning_tree_copy, name + '-Spanning-Tree', highlight_edges=first.edges())
    draw_tree(first, name + "_Tree_0")
    draw_tree(spanning_tree, name + "_Tree_0_Removed")
    return first


# Starts with Spanning Tree with T_0 removed. All its leaves are unmatched omnian vertices
# So now I must extend the paths to leaves in Network N.
# args:
# Spanning_tree: Spanning Tree with T_0 removed
# g: Original Phylogenetic Network N
def extend_omnian_to_leaves(g, spanning_tree):
    # Since I may have repeat nodes I need to be careful here as I need the paths to be independent...
    network_leaves = get_leaves(g)
    unmatched_omnians = get_leaves(spanning_tree)
    labels = get_node_attributes(spanning_tree, "labels")
    node_to_uuid = {node_label: uuid_id for uuid_id, node_label in labels.items()}

    omnian_to_leaf_paths = list()

    # Used in the case if there are multiple leaf paths for 1 omnian...
    leaf_usage = dict()
    for leaf in network_leaves:
        leaf_usage[leaf] = 0
    omnian_all_leaf_paths = dict()

    # i = 0
    # Path from omnian in S to leaf in G
    for omnian in unmatched_omnians:
        # Find the paths from Omnian Node to each leaf in N
        for leaf in network_leaves:
            omnian_to_leaf = list(all_simple_edge_paths(g, labels[omnian], leaf))
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

    # Handle the situation of omnian to multiple leaves
    # Because it is sorted, the leaves that require paths come first...
    for omnian, path_to_leaf in omnian_all_leaf_paths.items():
        # Select which leaf the omnian should go to...
        for target_leaf in leaf_usage.keys():
            # Does the leaf exist in any of the paths?
            leaf = path_to_leaf[len(path_to_leaf) - 1][1]
            if target_leaf != leaf:
                continue
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


# next tree:
# g - complete network N
# leaves - all leaves in N
# tree_zero, spanning tree which only has omnian leaves. Used to generate new trees
# s- spanning tree only containing 1 path to each leaf in N
def next_tree(tree_zero, spanning_tree):
    nodes = set()
    selected_leaf_set = set()
    tree = DiGraph()
    root = get_root(spanning_tree)
    network_leaves = get_leaves(tree_zero)
    unused_leaves = get_leaves(spanning_tree)
    label_attribute = get_node_attributes(spanning_tree, 'labels')

    # Path from omnian in S to leaf in G
    for leaf in unused_leaves:
        full_path = list(all_simple_edge_paths(spanning_tree, root, leaf))[0]
        full_path.reverse()

        leaf = label_attribute[full_path[0][1]]
        # Can't have more than 1 path to same leaf of Network N!
        if leaf in selected_leaf_set:
            # print("Skipped, Can't Select Same Leaf Twice!")
            continue

        selected_leaf_set.add(leaf)

        # print("Nodes in S prime: " + str(list(spanning_tree.nodes())))
        # Repeat the same process from earlier
        for src, tgt in full_path:
            tree.add_edge(label_attribute[src], label_attribute[tgt])
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

    # print("Leaves picked: " + str(selected_leaf_set))

    # To make it a correct "tree" append all remaining leaves for full leaf set
    # Base this on the first tree generated
    root = get_root(tree_zero)
    for leaf in network_leaves - selected_leaf_set:
        extra_path = list(all_simple_edge_paths(tree_zero, root, leaf))[0]
        tree.add_edges_from(extra_path)
    return tree


# create trees
def enum_trees(g, graph_name, draw=False):
    # Start with creating the spanning tree
    spanning_tree = create_rooted_tree(g)
    leaves = get_leaves(g)
    # From Spanning tree, the first tree will just be consist of
    # spanning tree with all paths to omnians gone
    # S_prime is the spanning-tree remaining after all first leaves filtered
    tree_zero = first_tree(spanning_tree, leaves, graph_name)
    tree_list = [tree_zero]
    # Relabel nodes to UUID keys and labels to allow for multiple instances of label!
    spanning_tree = convert_to_uuid_keys(spanning_tree)

    extend_omnian_to_leaves(g, spanning_tree)
    draw_tree(spanning_tree, "Graph/Extended-Spanning-Tree-final")

    i = 1
    # Confirm all nodes all covered at least once
    all_nodes = set(tree_zero.nodes())
    # Keep cutting paths from spanning tree S
    while len(list(spanning_tree.nodes())) != 0:
        tree = next_tree(tree_zero, spanning_tree)
        tree_list.append(tree)
        if draw:
            draw_tree(tree, graph_name + "_Tree_" + str(i))
        i = i + 1
        all_nodes.update(tree.nodes())
        # print("Tree made: " + str(list(spanning_tree.nodes())))
    # Confirm that every node was covered in all the trees...
    assert all_nodes == set(g.nodes())
    return tree_list, len(tree_list)
