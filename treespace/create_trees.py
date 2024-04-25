from networkx import DiGraph

from treespace.utils import get_leaves, get_root, get_all_roots
from treespace.drawing import draw_tree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree


# Check if all nodes were covered at least once
def all_nodes_covered(nodes_used: dict) -> bool:
    for node_usage in nodes_used.values():
        if node_usage == 0:
            return False
    return True


# Used within exchange argument to prioritize which path with unmatched omnian to pick
def count_untouched_nodes_in_path(omnian_path: list, nodes_used: dict) -> int:
    count = 0
    for node in omnian_path:
        if nodes_used[node] == 0:
            count += 1
    return count


# Convert a list of nodes to a list of paths
# e, g. [ 1, 2, 3, 4 ] becomes [ (1, 2), (2, 3), (3, 4) ]
# This is only used in drawing, this helps me track which edges have NOT been picked yet
def path_to_edges(paths: list) -> list:
    edge_list = []
    for path in paths:
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            edge_list.append(edge)
    return edge_list


# Iterate Tree:
# Using the input disjoint paths, create a tree with 1 root and all leaves
# Then update the metrics to count which nodes have been covered from this one tree
# I need the original network g to inform my decision which leaves/paths are valid
def iterate_tree(disjoint_paths: list, nodes_used: dict, g) -> DiGraph:
    tree = DiGraph()
    # Build tree from disjoint paths
    leaves = get_leaves(g)
    root = get_root(g)

    # Essentially similar to spanning tree, only add the following paths
    # 1- Path with the root
    # 2- All paths ending in a leaf
    for path in disjoint_paths:
        if path[len(path) - 1] in leaves:
            print("This path is OK because it ends in a leaf", path)
            # Add the path to the tree, if the path is just leaf node,
            # this fail-safe ensures it is added
            if len(path) == 1:
                tree.add_node(path[0])
            else:
                for i in range(len(path) - 1):
                    tree.add_edge(path[i], path[i + 1])
            continue

        # Check if the path has the root or not...
        if root in path:
            for i in range(len(path) - 1):
                tree.add_edge(path[i], path[i + 1])
            print("This path is OK because it has a root", path)
        else:
            print("This disjoint path should not be used to build a tree", path)
            continue

    # Make sure there is only one root in the tree you are making
    current_roots = get_all_roots(tree)
    while len(current_roots) != 1:
        roots_to_delete = set()
        for temp_root in current_roots:
            if temp_root == root:
                continue
            parents = list(g.predecessors(temp_root))
            # TODO: Should I be concerned about node count? might want to pick lowest level too
            tree.add_edge(parents[0], temp_root)
            print("Found extra root", temp_root, "Will remove by adding edge", parents[0], temp_root)
            roots_to_delete.add(temp_root)
        # Delete temp_roots and check if you need to keep adding more paths up...
        for remove_node in roots_to_delete:
            current_roots.remove(remove_node)
        current_roots = current_roots.union(get_all_roots(tree))

    # Make sure there are only the specified leaves allowed in the tree you are making
    current_leaves = get_leaves(tree)
    while leaves != current_leaves:
        leaves_to_delete = set()
        for leaf in current_leaves:
            if leaf not in leaves:
                print("Found invalid leaf", leaf, " deleting from generated tree")
                tree.remove_node(leaf)
                leaves_to_delete.add(leaf)
        for leaf in leaves_to_delete:
            current_leaves.remove(leaf)
        current_leaves = current_leaves.union(get_leaves(tree))

    # Update Metrics of which nodes have been used in a tree
    for node in tree.nodes():
        counter = nodes_used[node]
        counter += 1
        nodes_used[node] = counter
    return tree


# Exchange algorithm
# Essentially, starting from one set of disjoint paths,
# change the node the omnian should be matched with
# You should have the same number of disjoint paths both as input and output (Francis et al.)
# but the new tree should be different from new paths and will prioritize untouched nodes on iterate_tree
def exchange_disjoint_paths(disjoint_paths: list, count_nodes: dict, graph: DiGraph):
    leaves = get_leaves(graph)
    omnian_paths = []
    leaf_paths = []
    # Split which paths are ending in an unmatched omnian node and which are ending in leaf
    for path in disjoint_paths:
        if path[len(path) - 1] not in leaves:
            omnian_paths.append(path)
        else:
            leaf_paths.append(path)

    # Compute which omnian paths has the most untouched nodes
    for omnian_path in omnian_paths:
        count_untouched_nodes_in_path(omnian_path, count_nodes)

    # The omnian path I have to check the top node and bottom node, and exchange with a leaf path
    # Remember, leaf path we can already assume by definition has count >= 1 for each node already

    # Check what path the omnian node could be matched to now
    # Goal: Create different disjoint paths to leaves, using nodes with minimal coverage as possible.


# Main Function to get minimum number of rooted trees
def enum_trees(g: DiGraph, graph_name: str, draw=False) -> list:
    trees = []
    # Start with getting disjoint paths and drawing it on the graph for visualization
    _, paths = vertex_disjoint_paths(g)
    spanning_tree = rooted_spanning_tree(g, paths)


    if draw:
        draw_tree(g, graph_name + '-spanning-tree', highlight_edges=spanning_tree.edges())
        draw_tree(g, graph_name + '-initial-disjoint-paths', highlight_edges=path_to_edges(paths))

    node_used_count = {}
    for node in g.nodes():
        node_used_count[node] = 0

    tree_num = 1
    # Compute a metric for each disjoint part...
    while not all_nodes_covered(node_used_count):
        # 1- Use disjoint paths to create a tree with only leaves L
        # Be sure to update the metrics too
        tree = iterate_tree(paths, node_used_count, g)
        trees.append(tree)
        if draw:
            draw_tree(tree, graph_name + '-tree-number-' + str(tree_num))
            current_disjoint_paths = path_to_edges(paths)
            draw_tree(g, graph_name + '-disjoint-paths-' + str(tree_num), highlight_edges=current_disjoint_paths)
        # 2- Use exchange algorithm to compute new disjoint paths for next round
        # Also, enforce there should be NO new paths made
        number_of_disjoint_paths = len(paths)
        exchange_disjoint_paths(paths, node_used_count, g)
        assert number_of_disjoint_paths == len(paths)
        if tree_num == 1:
            break

    return trees