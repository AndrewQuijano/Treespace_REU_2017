from networkx import DiGraph, all_simple_paths, add_path
from typing import List, Tuple
from treespace.utils import get_leaves, get_root, get_all_roots
from treespace.drawing import draw_tree
from treespace.francis import vertex_disjoint_paths, rooted_spanning_tree


# I check the current tree being made and see if I should continue trying to check the existing omnian paths to build higher
def continue_building_tree(tree: DiGraph, g: DiGraph) -> bool:
    root = get_root(g)

    root_path = None
    non_root_paths = []
    for path in find_disjoint_paths(tree):
        if path[0] != root:
            non_root_paths.append(path)
        else:
            root_path = path

    print("[Checking Building Tree] Root Path", root_path)
    print("[Checking Building Tree] Non-Root Paths", non_root_paths)

    # There has to be a path to the root already...
    # if not keep searching then damn it!
    if root_path is None:
        return True
    else:
        # Check that all non-root paths are connected to the root path
        for path in non_root_paths:
            path_root = path[0]
            parents_in_network = set(g.predecessors(path_root))
            if not any(node in tree for node in parents_in_network):
                return True
    
    # Otherwise, no need to continue building!
    return False

# To make life easier, I can use this to add a new path to an existing leaf path
# For example, if I have a path
# edge: 16 -> 17
# (Omnian, to be added to the graph) 10 -> 12 -> 15 -> 16
# (Leaf, currently on the graph) 9 -> 14 -> 17 -> 18 -> 19 -> L2
# My output will be the tree will only have path
# 10 -> 12 -> 15 -> 16 -> 17 -> 18 -> 19 -> L2 (drops 9 and 14 to keep the path disjoint)
# The function is assuming current_leaf_path ends in a leaf node
def combine_paths_based_on_edge(graph: DiGraph, updating_path: List, current_leaf_path: List, edge_to_add: List) -> DiGraph:
    # Identify the nodes in the first path up to the start of the edge to add
    path1_nodes = updating_path[:updating_path.index(edge_to_add[0])+1]

    # Identify the nodes in the second path from the end of the edge to add
    path2_nodes = current_leaf_path[current_leaf_path.index(edge_to_add[1]):]

    # Combine these nodes to create the new path
    new_path = path1_nodes + path2_nodes
    print("[ITER] New Path based on omnians", updating_path)
    print("[ITER] Current Leaf Path", current_leaf_path)
    print("[ITER] New Path", new_path)

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
            raise ValueError("[ITER] Start or end node not found in the given path")

    # Count the number of untouched nodes in the specified path slice
    for node in path_slice:
        if nodes_used[node] == 0:
            count += 1
    print("[ITER] Path ", path_slice, "has", count, " untouched nodes")
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
                print("[Prune Tree] An extra root was found", temp_root)

            parents = list(graph.predecessors(temp_root))
            found_root_path = False
            for parent in parents:
                # Try to pick node already with a root path when moving up...
                # This will make it easier to not lose track of the initial disjoint paths
                if parent in tree.nodes():
                    tree.add_edge(parent, temp_root)
                    found_root_path = True
                    print("[Prune Tree] Will remove by adding edge: ", parent, '->', temp_root)
                    break

            # If nothing found, just pick any predecessor
            if not found_root_path:
                tree.add_edge(parents[0], temp_root)
                print("[Prune Tree] Will remove by adding edge: ", parents[0], '->', temp_root)

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
                print("[Prune Tree] Found invalid leaf", leaf, " deleting from generated tree")
                tree.remove_node(leaf)
                leaves_to_delete.add(leaf)
        for leaf in leaves_to_delete:
            current_leaves.remove(leaf)
        current_leaves = current_leaves.union(get_leaves(tree))


# Iterate Tree:
# Using the input disjoint paths, create a tree with 1 root and all leaves
# Then update the metrics to count which nodes have been covered from this one tree
# I need the original network g to inform my decision which leaves/paths are valid
def iter_tree(tree: DiGraph, omnian_paths: List, nodes_used: dict, g: DiGraph) -> DiGraph:

    # TODO: A note to PIs, you may want to do ONE more loop of omnian paths, because you may terminate too early
    # and no discover paths that only become 'visible' once you reach the root.
    while continue_building_tree(tree, g):
        for leaf_ending_path in find_disjoint_paths(tree):
            print("[ITER] Checking Leaf Ending Path", leaf_ending_path)
            # First, check the parent of the disjoint path, if it goes to another leaf path, 
            # no need to check this further
            path_root = leaf_ending_path[0]
            parents_in_network = set(g.predecessors(path_root))
            if any(node in tree for node in parents_in_network):
                print("[ITER] This path has a parent going to another leaf ending path", leaf_ending_path)
                continue
            else:
                # I need to poke around the omnian paths to see which nodes to go up to the root
                print("[ITER] This path has no parent going to another leaf ending path", leaf_ending_path)
                # Iterate through all the omnian ending paths, check g.predecessors to get the viable edges
                # and respective disjoint path
                candidate_edges_and_paths = []
                for omnian_path in omnian_paths:
                    print("[ITER] Checking Omnian Path", omnian_path)
                    for omnian_node in omnian_path:
                        # I want to check which omnian paths would be connected to current disjoint paths on the tree
                        for leaf_path_node in g.successors(omnian_node):
                            print("[ITER] Checking if edge exists", omnian_node, leaf_path_node)
                            if leaf_path_node in leaf_ending_path:
                                edge = [omnian_node, leaf_path_node]
                                print("[ITER] Found edge to exchange", edge)
                                candidate_edges_and_paths.append((edge, omnian_path))

                # If no candidate edges, continue to the next leaf ending path that should be changed up
                if len(candidate_edges_and_paths) == 0:
                    print("[ITER] no valid edge found")
                    continue

                # Compute which edge to pick based on the number of untouched nodes
                scores = {}
                edge_to_path = {}
                for edge, omnian_path in candidate_edges_and_paths:
                    omnian_node, tree_path_node = edge
                    omnian_score = count_untouched_score_in_path(omnian_path, nodes_used, start=omnian_path[0], end=omnian_node)
                    # The minus is necessary, because the last node in tree_path technically is not getting cut
                    # I also want to be careful to avoid any negatives, hence the max()
                    tree_score = max(count_untouched_score_in_path(leaf_ending_path, nodes_used, start=leaf_ending_path[0], end=tree_path_node) - 1, 0)
                    # You subtract, because you gain the nodes in omnian path, 
                    # but might lose nodes in existing leaf ending path
                    total_score = omnian_score - tree_score
                    scores[tuple(edge)] = total_score
                    edge_to_path[tuple(edge)] = omnian_path
                    print("[ITER] edge", edge, " has a score of ", total_score)

                best_edge = max(scores, key=scores.get)
                omnian_path = edge_to_path[tuple(best_edge)]
                best_edge = list(best_edge)
                print("[ITER] Best Edge to pick", best_edge)
                combine_paths_based_on_edge(tree, omnian_path[:omnian_path.index(best_edge[0]) + 1], leaf_ending_path, best_edge)

        print("[ITER] Completed Path Update")

    print("[ITER] Completed Disjoint path creation, now pruning tree...")

    # I should not need this function tbh...
    prune_tree(tree, g)

    # Update Metrics of which nodes have been used in a tree
    for node in tree.nodes():
        counter = nodes_used[node]
        counter += 1
        nodes_used[node] = counter
    return tree


# This function has two important things to do
# 1- Create a Tree, with just the paths to leaves
# 2- Return Omnian paths
def initialize_enum(g: DiGraph, disjoint_paths: list) -> Tuple[DiGraph, List]:
    omnian_paths = []
    leaf_paths = []

    base_tree = DiGraph()
    leaves = get_leaves(g)

    # Essentially similar to the spanning tree:
    # - Only add all paths ending in a leaf
    for path in disjoint_paths:
        if path[len(path) - 1] in leaves:
            leaf_paths.append(path)
            # Add the path to the tree, if the path is just leaf node,
            # this fail-safe ensures it is added
            if len(path) == 1:
                base_tree.add_node(path[0])
            else:
                add_path(base_tree, path)
        else:
            omnian_paths.append(path)

    for path in leaf_paths:
        print("[INIT] This path is OK because it ends in a leaf", path)
    
    for path in omnian_paths:
        print("[INIT] This path ends in an unmatched omnian node", path)
    
    return base_tree, omnian_paths


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

    # Compute a metric for each disjoint part...
    while not all_nodes_covered(node_used_count):
        # 1- Use disjoint paths to create a tree with only leaves L
        # Be sure to update the metrics too
        tree = iter_tree(base_tree.copy(as_view=False), omnian_tuple, node_used_count, g)
        trees.append(tree)

        if draw:
            draw_tree(tree, graph_name + '-tree-number-' + str(len(trees)))

        # Have a quick and easy way to break, after making 1 tree, there are bugs
        # but it is the proof of concept that matters most.
        if len(trees) >= 1:
            break

    return trees
