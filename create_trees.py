from francis import vertex_disjoint_paths, rooted_spanning_tree
from misc import get_leaves, get_root
from networkx import DiGraph
from networkx.algorithms.simple_paths import all_simple_edge_paths
from networkx import is_empty
from drawing import draw_tree
from networkx.exception import NodeNotFound


# Create the rooted spanning tree
def create_rooted_tree(g):
    _, paths = vertex_disjoint_paths(g)
    s = rooted_spanning_tree(g, paths)
    return s


def first_tree(s, leaves, name):
    first = DiGraph()
    root = get_root(s)
    nodes = set()

    # Flip edges for leaf to root?
    for leaf in leaves:
        edges = list(all_simple_edge_paths(s, root, leaf))[0]
        # print(edges)
        # So path is from leaf to root
        edges.reverse()
        # print(edges)
        for src, tgt in edges:
            first.add_node(src)
            first.add_node(tgt)

            if s.out_degree(tgt) <= 1:
                nodes.add(tgt)
            else:
                break

            if s.out_degree(src) <= 1:
                nodes.add(src)
            else:
                break
        first.add_edges_from(edges)
        # print("Remove: " + str(nodes))
        for node in nodes:
            s.remove_node(node)
        nodes.clear()
    draw_tree(first, name + "-First-Tree")
    draw_tree(s, name + "-First-Leftover")
    return first


# next tree:
# g - complete network N
# leaves - all leaves in N
# prime, spanning tree which only has omnian leaves. Used to generate new trees
# s- spanning tree only containing 1 path to each leaf in N
def next_tree(g, leaves, prime_tree, s):
    nodes = set()
    selected_leaf_set = set()
    tree = DiGraph()
    root = get_root(g)
    unmatched_omnians = get_leaves(prime_tree)

    # Path from omnian in S to leaf in G
    for omnian in unmatched_omnians:
        for leaf in leaves:
            omnian_to_leaf = list(all_simple_edge_paths(g, omnian, leaf))
            if len(omnian_to_leaf) == 0:
                continue

            # If you have two omnians head to 1 leaf
            # You can only pick 1 Path for that tree...
            if leaf in selected_leaf_set:
                continue

            try:
                full_path = list(all_simple_edge_paths(prime_tree, root, omnian))
            except NodeNotFound:
                continue

            if len(full_path) == 0:
                continue
            full_path = full_path[0]

            # First Question, will this only be 1 Leaf always?
            # Could I prove this is always the case...?
            # omnian_to_leaf.reverse()
            omnian_to_leaf = omnian_to_leaf[0]
            # print("omnian to leaf: " + str(omnian_to_leaf))

            selected_leaf_set.add(leaf)

            full_path.reverse()
            # print("Full path" + str(full_path))

            # print("Nodes in S prime: " + str(list(prime_tree.nodes())))
            # Repeat the same process from earlier
            for src, tgt in full_path:
                if prime_tree.out_degree(tgt) <= 1:
                    nodes.add(tgt)
                else:
                    break
                                    
                if prime_tree.out_degree(src) <= 1:
                    nodes.add(src)
                else:
                    break

            # print("Delete: " + str(nodes))
            for node in nodes:
                prime_tree.remove_node(node)
            nodes.clear()

            full_path.extend(omnian_to_leaf)
            # print("Full path" + str(full_path))
            tree.add_edges_from(full_path)

    # print("Leaves picked: " + str(selected_leaf_set))

    # To make it a correct "tree" append all remaining leaves for full leaf set
    # Base this on the first tree generated
    for leaf in leaves - selected_leaf_set:
        extra_path = list(all_simple_edge_paths(s, root, leaf))[0]
        tree.add_edges_from(extra_path)
    return tree


# create trees
def enum_trees(g, graph_name, draw=False):
    # Start with creating the spanning tree
    s = create_rooted_tree(g)
    leaves = set(get_leaves(g))
    # From Spanning tree, the first tree will just be consist of
    # spanning tree with all paths to omnians gone
    # S_prime is the spanning-tree remaining after all first leaves filtered
    first = first_tree(s, leaves, graph_name)
    tree_list = [first]
    i = 0

    # Keep cutting paths from spanning tree S
    while len(list(s.nodes())) != 0:
        print("Tree made: " + str(list(s.nodes())))
        tree = next_tree(g, leaves, s, first)
        tree_list.append(tree)
        if draw:
            draw_tree(tree, graph_name + "-Tree-" + str(i))
        i = i + 1
        print("Tree made: " + str(list(s.nodes())))
    return tree_list, len(tree_list)
