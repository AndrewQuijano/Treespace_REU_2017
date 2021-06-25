from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root
from networkx import DiGraph, set_node_attributes, get_node_attributes
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
    labels = dict(zip(spanning_tree.nodes(), spanning_tree.nodes()))
    set_node_attributes(spanning_tree, labels, 'labels')
    label_attribute = get_node_attributes(spanning_tree, 'labels')

    i = 0
    # Path from omnian in S to leaf in G
    for omnian in unmatched_omnians:
        for leaf in network_leaves:
            # Find the path from Omnian Node to a Leaf in N
            omnian_to_leaf = list(all_simple_edge_paths(g, omnian, leaf))
            if len(omnian_to_leaf) == 0:
                continue
            elif len(omnian_to_leaf) == 1:
                omnian_to_leaf = omnian_to_leaf[0]
                for source, target in omnian_to_leaf:
                    print(source, target)

                    if source in label_attribute.keys() and target in label_attribute.keys():
                        continue

                    if target in label_attribute.keys():
                        print("Option 1: " + str(label_attribute))
                        target_name = str(uuid.uuid4())
                        label_attribute[target_name] = target
                        spanning_tree.add_node(target_name, labels=target)
                        spanning_tree.add_edge(source, target_name)
                    else:
                        print("Option 2: " + str(label_attribute))
                        label_attribute[target] = target
                        spanning_tree.add_node(target, labels=target)
                        spanning_tree.add_edge(source, target)

                    draw_tree(spanning_tree, "Graph/Extended-Spanning-Tree-" + str(i))
                    i = i + 1
            else:
                raise NotImplemented


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

        leaf = full_path[0][1]
        print("Leaf in N is picked: " + leaf)
        selected_leaf_set.add(label_attribute[leaf])
        # Can't have more than 1 path to same leaf of Network N!
        if leaf in selected_leaf_set:
            continue

        # print("Full path" + str(full_path))

        # print("Nodes in S prime: " + str(list(prime_tree.nodes())))
        # Repeat the same process from earlier
        for src, tgt in full_path:
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

        tree.add_edges_from(full_path)

    # print("Leaves picked: " + str(selected_leaf_set))

    # To make it a correct "tree" append all remaining leaves for full leaf set
    # Base this on the first tree generated
    for leaf in network_leaves - selected_leaf_set:
        extra_path = list(all_simple_edge_paths(tree_zero, root, leaf))[0]
        tree.add_edges_from(extra_path)
    return tree


# create trees
def enum_trees(g, graph_name, draw=False):
    # Start with creating the spanning tree
    spanning_tree = create_rooted_tree(g)
    leaves = set(get_leaves(g))
    # From Spanning tree, the first tree will just be consist of
    # spanning tree with all paths to omnians gone
    # S_prime is the spanning-tree remaining after all first leaves filtered
    tree_zero = first_tree(spanning_tree, leaves, graph_name)
    tree_list = [tree_zero]
    extend_omnian_to_leaves(g, spanning_tree)
    draw_tree(spanning_tree, "Graph/Extended-Spanning-Tree-final")

    i = 0
    # Keep cutting paths from spanning tree S
    while len(list(spanning_tree.nodes())) != 0:
        tree = next_tree(tree_zero, spanning_tree)
        tree_list.append(tree)
        if draw:
            draw_tree(tree, graph_name + "-Tree-" + str(i))
        i = i + 1
        print("Tree made: " + str(list(spanning_tree.nodes())))
    return tree_list, len(tree_list)
