from networkx import DiGraph, all_simple_paths, add_path
from typing import List, Tuple
from treespace.utils import get_leaves, get_root, get_all_roots
from treespace.drawing import draw_tree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree
from collections import OrderedDict
import copy


# To make life easier, I can use this to add a new path to an existing leaf path
def combine_paths_based_on_edge(graph: DiGraph, new_path: List, current_leaf_path: List, edge_to_add: List) -> DiGraph:
    # Identify the nodes in the first path up to the start of the edge to add
    path1_nodes = new_path[:new_path.index(edge_to_add[0])+1]

    # Identify the nodes in the second path from the end of the edge to add
    path2_nodes = current_leaf_path[current_leaf_path.index(edge_to_add[1]):]

    # Combine these nodes to create the new path
    new_path = path1_nodes + path2_nodes

    # Remove the old paths from the graph
    graph.remove_nodes_from(new_path)
    graph.remove_nodes_from(current_leaf_path)

    # Add the new path to the graph
    add_path(graph, new_path)
    return graph


# Find all disjoint paths between all pairs of nodes in the graph
# Each graph I generate will be just disjoint paths, on the final step I will join these
# disjoint paths to create a tree with root rho and same leaf set
def find_disjoint_paths(graph: DiGraph) -> list:
    disjoint_paths = []
    for target in graph.nodes:
        if graph.out_degree(target) == 0:  # target is a leaf node
            for source in graph.nodes:
                if source != target:
                    paths = list(all_simple_paths(graph, source, target))
                    for path in paths:
                        # Check if path is not a subset of any path in disjoint_paths
                        if not any(set(path).issubset(set(p)) for p in disjoint_paths):
                            disjoint_paths.append(path)
    return disjoint_paths


# Check if all nodes were covered at least once
def all_nodes_covered(nodes_used: dict) -> bool:
    for node_usage in nodes_used.values():
        if node_usage == 0:
            return False
    return True


# Used within exchange argument to prioritize which path with unmatched omnian to pick
# There is an option to have a start and end parameter, say you have
# [1, 2, 3, 4, 5], and start = 2 end = 4, you will only get the number of 0s for 2, 3, 4.
# This is to make the call whether to cut or not.
def count_untouched_score_in_path(omnian_path: list, nodes_used: dict, start='', end='') -> int:
    count = 0

    # Determine the slice of the path to consider
    if start == '' and end == '':
        path_slice = omnian_path
    else:
        try:
            start_index = omnian_path.index(start)
            end_index = omnian_path.index(end) + 1  # +1 to include the end node in the slice
            path_slice = omnian_path[start_index:end_index]
        except ValueError:
            raise ValueError("Start or end node not found in the given path")

    # Count the number of untouched nodes in the specified path slice
    for node in path_slice:
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


# This is a helper function to iter_tree
# This takes care of
# 1- making sure you only have one root, rho.
# It does this by connecting loose ends up to any node
# 2- you only have the same leaves from the original network N. It does this by removing any loose ends.
# So when I occasionally change paths, just leaving a hanging omnian will be cleaned up here
def prune_tree(tree: DiGraph, graph: DiGraph):
    root = get_root(graph)
    leaves = get_leaves(graph)

    # Make sure there is only one root in the tree you are making
    current_roots = get_all_roots(tree)
    while len(current_roots) != 1:
        roots_to_delete = set()
        for temp_root in current_roots:
            if temp_root == root:
                continue
            else:
                print("An extra root was found", temp_root)

            parents = list(graph.predecessors(temp_root))
            found_root_path = False
            for parent in parents:
                # Try to pick node already with a root path when moving up...
                # This will make it easier to not lose track of the initial disjoint paths
                if parent in tree.nodes():
                    tree.add_edge(parent, temp_root)
                    found_root_path = True
                    print("[Root Path Found] Will remove by adding edge: ", parent, '->', temp_root)
                    break

            # If nothing found, just pick any predecessor
            if not found_root_path:
                tree.add_edge(parents[0], temp_root)
                print("[Root Path Not Found] Will remove by adding edge: ", parents[0], '->', temp_root)

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


# Iterate Tree:
# Using the input disjoint paths, create a tree with 1 root and all leaves
# Then update the metrics to count which nodes have been covered from this one tree
# I need the original network g to inform my decision which leaves/paths are valid
def iter_tree(tree: DiGraph, omnian_tuple: List[Tuple], nodes_used: dict, g: DiGraph) -> DiGraph:
    # Note the tree is a deep copy of a base tree already, so I need to add the remaining edges

    # Dictionary to store the scores
    path_scores = {}
    path_mapping = {}

    # Sort by the score for omnian disjoint paths
    for omnian_disjoint_path, full_omnian_path in omnian_tuple:
        num_unused_nodes_in_path = count_untouched_score_in_path(omnian_disjoint_path, nodes_used)
        # Store the score in the dictionary
        path_scores[tuple(omnian_disjoint_path)] = num_unused_nodes_in_path
        path_mapping[tuple(omnian_disjoint_path)] = full_omnian_path

    # Sort the items in the dictionary by score in descending order
    path_scores = OrderedDict(sorted(path_scores.items(), key=lambda item: item[1], reverse=True))

    # Iterate through path_scores
    for omnian_disjoint_path, num_unused_nodes_in_path in path_scores.items():
        # Get the corresponding full_omnian_path from path_mapping
        full_omnian_path = path_mapping[omnian_disjoint_path]

        # Find the correct full_omnian_path to leaf_path
        # REMEMBER: The generated tree should only have paths ending in a leaf ONLY
        for leaf_path in find_disjoint_paths(tree):
            leaf = leaf_path[-1]
            if leaf == full_omnian_path[-1]:
                # 1- for the omnian path, check the bottom
                # a- check the children of leaf of unmatched omnnian in G
                # b- does this omnian match a node in the tree being generated?
                # If yes, compare if you get more nodes switching path
                # You, should ONLY cut an edge and add one
                # the pruning will take care of the rest
                # otherwise, nothing to do
                for child in g.successors(omnian_disjoint_path[-1]):
                    if child in tree.nodes():
                        pass

                # 1- for the omnian path, check the top
                # a- check the parents of unmatched omnnian in G
                # b- does this omnian match a node in the tree being generated?
                # If yes, compare if you get more nodes switching path
                # You, should ONLY cut an edge and add one
                # the pruning will take care of the rest
                # otherwise, nothing to do
                for parents in g.predecessors(omnian_disjoint_path[0]):
                    if parents in tree.nodes():
                        pass

                # Finally add the rest of the disjoint path
                add_path(tree, omnian_disjoint_path) 

    prune_tree(tree, g)

    # Update Metrics of which nodes have been used in a tree
    for node in tree.nodes():
        counter = nodes_used[node]
        counter += 1
        nodes_used[node] = counter
    return tree


# This function has two important things to do
# 1- Create a Tree, with just the paths for root and leaves
# 2- For all other disjoint paths, extend these such that they start at root and end in leaf
def initialize_enum(g: DiGraph, disjoint_paths: list) -> Tuple[DiGraph, List[Tuple], List]:
    omnian_paths = []
    leaf_paths = []

    base_tree = DiGraph()
    leaves = get_leaves(g)
    root = get_root(g)

    # Essentially similar to the spanning tree:
    # - Only add all paths ending in a leaf
    for path in disjoint_paths:
        if path[len(path) - 1] in leaves:
            leaf_paths.append(path)
            print("This path is OK because it ends in a leaf", path)
            # Add the path to the tree, if the path is just leaf node,
            # this fail-safe ensures it is added
            if len(path) == 1:
                base_tree.add_node(path[0])
            else:
                add_path(base_tree, path)
        else:
            omnian_paths.append(path)
            print("This path is an Omnian path", path)
    
    omnian_tuple = []

    # For the Omnian paths, you want to extend to root and to a leaf,
    # use the other disjoint paths to help you.
    for omnian_path in omnian_paths:
        print("Found Omnian path", omnian_path)
        full_omnian_path = copy.deepcopy(omnian_path)

        # 1- Make sure you find the path that goes up to the root
        omnian_path_root = omnian_path[0]
        while omnian_path_root != root:
            current_length = len(full_omnian_path)
            for parent in g.predecessors(omnian_path_root):
                # It is in my interest that the omnian disjoint path matches a leaf disjoint path in the base tree
                if parent in base_tree.nodes():
                    full_omnian_path.insert(0, parent)
                    break

            # If the size is same, add child, path not found in the leaf disjoint paths
            if current_length == len(full_omnian_path):
                should_break = False
                for other_omnian_paths in omnian_paths:
                    # I want to check if the child others in another disjoint omnian path
                    for parent in g.predecessors(omnian_path_root):
                        # Join it, and terminate both loops
                        if parent in other_omnian_paths:
                            should_break = True
                            full_omnian_path.insert(0, parent)
                            break

                    if should_break:
                        break

            print("The Extended Omnian Path is", full_omnian_path)
            omnian_path_root = full_omnian_path[0]

        print("Completed Extending the Omnian Path to a Root")

        # 2- Pick a path that goes to a leaf you can reach
        omnian_path_leaf = omnian_path[len(omnian_path) - 1]
        while omnian_path_leaf not in leaves:
            current_length = len(full_omnian_path)
            for child in g.successors(omnian_path_leaf):
                # It is in my interest that the omnian disjoint path matches a leaf disjoint path 
                # in the base tree first
                if child in base_tree.nodes():
                    full_omnian_path.append(child)
                    break

            # If the size is same, add child, path not found in the leaf disjoint paths
            if current_length == len(full_omnian_path):
                should_break = False
                for other_omnian_paths in omnian_paths:
                    # I want to check if the child others in another disjoint omnian path
                    for child in g.successors(omnian_path_leaf):
                        # Join it, and terminate both loops
                        if child in other_omnian_paths:
                            should_break = True
                            full_omnian_path.append(child)
                            break
                    if should_break:
                        break

            omnian_path_leaf = full_omnian_path[len(full_omnian_path) - 1]

        print("Extended Omnian path", full_omnian_path)
        omnian_tuple.append((omnian_path, full_omnian_path))

    return base_tree, omnian_tuple


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

    base_tree, omnian_tuple = initialize_enum(g, paths)

    # TODO: 
    # I should test the following now
    # 1- does the getting disjoint path work from base tree?
    for path in find_disjoint_paths(base_tree):
        print("Disjoint Path from Base Tree", path)
    
    # 2- what does the full omnian path look like?
    for omnian_disjoint_path, full_omnian_path in omnian_tuple:
        print("Omnian Disjoint Path", omnian_disjoint_path)
        print("Full Omnian Path", full_omnian_path)

    tree_num = 1
    # Compute a metric for each disjoint part...
    while not all_nodes_covered(node_used_count):
        # 1- Use disjoint paths to create a tree with only leaves L
        # Be sure to update the metrics too
        tree = iter_tree(base_tree.copy(as_view=False), omnian_tuple, node_used_count, g)
        trees.append(tree)
        if draw:
            draw_tree(tree, graph_name + '-tree-number-' + str(tree_num))

        if tree_num == 1:
            break

    return trees
