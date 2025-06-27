from networkx import DiGraph, all_simple_paths, add_path
from typing import List, Tuple
from treespace_metrics.utils import get_leaves, get_root, get_all_roots, path_to_edges
from treespace_metrics.drawing import draw_tree
from treespace_metrics.francis import vertex_disjoint_paths, rooted_spanning_tree


def is_connected_to_other_leaf_path(network: DiGraph, all_current_leaf_ending_path: list, leaf_path_analyzed: list) -> bool:
    """"
    This functions checks if leaf_
    Args:
        network: the original phylogenetic network N
        all_current_leaf_ending_path: List of all current leaf ending paths in the tree being generated
        leaf_path_analyzed: The current leaf ending path being analyzed.
    Returns:
        Bool: If leaf_path_analyzed has an edge in N that connects to any OTHER leaf ending path in the generated tree.
    """
    parents_in_network = set(network.predecessors(leaf_path_analyzed[0]))
    for leaf_path in all_current_leaf_ending_path:
        # You need to check if your leaf path connects to another leaf path, not yourself
        if leaf_path[-1] == leaf_path_analyzed[-1]:
            continue
        # Check if the leaf path has a parent that is in the other leaf ending path
        else:
            if any(node in leaf_path for node in parents_in_network):
                print("[CONNECTED] Leaf Path", leaf_path_analyzed, "is connected to another leaf path", leaf_path)
                return True
    return False


def least_common_ancestor(network: DiGraph, leaf_ending_path: list,
                          omnian_nodes: list) -> Tuple[str, str] | None:
    """
    This function helps find the least common ancestor, if one exists
    Args:
        network: the original phylogenetic network N
        leaf_ending_path: This is a path that ends in a leaf node in tree being generated
        omnian_nodes: This is the omnian ending path
    Returns:
        Tuple: The base tree with only leaf paths, and the list of omnian paths
    """
    print("[LCA] Finding LCA for Omnian Nodes", omnian_nodes)
    for omnian_path_node in omnian_nodes:
        print("[LCA] finding LCA for Omnian Node", omnian_path_node)
        for parent in network.predecessors(omnian_path_node):
            print("[LCA] Checking if edge", parent, omnian_path_node, "exists in N")
            if parent in leaf_ending_path:
                print("[LCA] Found LCA on leaf ending path, verified with Network N", parent)
                return parent, omnian_path_node
    return None


def continue_building_tree(generated_tree: DiGraph, network: DiGraph) -> bool:
    """
    This is a helper function to iter_tree
    I check the current tree being made and see if I should continue trying to check the existing omnian paths to build higher
    Args:
        generated_tree: the tree currently being built to solve the minimum enum problem
        network: the original network N
    Returns:
        Boolean: True - keep working on building the tree, False - stop building the tree
    """
    root = get_root(network)

    root_path = None
    non_root_paths = []
    for path in find_disjoint_paths(generated_tree, network):
        if path[0] != root:
            non_root_paths.append(path)
        else:
            root_path = path

    # Print the adjacency list of the tree
    print("[Checking Building Tree] Adjacency List of Tree")
    for node, neighbors in generated_tree.adj.items():
        print(f"{node}: {list(neighbors)}")

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
            parents_in_network = set(network.predecessors(path_root))
            if not any(node in generated_tree for node in parents_in_network):
                return True
    
    # Otherwise, no need to continue building!
    return False


def combine_paths_based_on_edge(generated_tree: DiGraph,
                                omnian_path: List[str],
                                current_leaf_path: List[str],
                                opl_to_ler_edge: List[str],
                                lca_to_opr_edge: List[str]) -> DiGraph:
    """
    This is a helper function to iter_tree
    To make life easier, I can use this to add a new path to an existing leaf path
    For example, if I have a path
    edge: 16 -> 17
    (Omnian, to be added to the graph) 10 -> 12 -> 15 -> 16
    (Leaf, currently on the graph) 9 -> 14 -> 17 -> 18 -> 19 -> L2
    My output will be the tree will only have path
    10 -> 12 -> 15 -> 16 -> 17 -> 18 -> 19 -> L2 (drops 9 and 14 to keep the path disjoint)
    The function is assuming current_leaf_path ends in a leaf node

    Args:
        generated_tree (DiGraph): The tree being generated in `iter_tree`.
        omnian_path (list): The omnian path selected that will be added to the tree as this will give most unused nodes.
        current_leaf_path (list): The path that is currently in the tree, ending in a leaf at the moment.
        opl_to_ler_edge (tuple): The edge to add that will connect the updating path to the current leaf path.
        lca_to_opr_edge (tuple): If the omnian path has a common ancestor with the leaf-ending path, this is how to factor that in.

    Returns:
        DiGraph: The updated tree with the new path added.

    """

    omnian_path_leaf, leaf_ending_root = opl_to_ler_edge
    if lca_to_opr_edge is None:
        lca, omnian_path_root = current_leaf_path[0], omnian_path[0]
    else:
        # If there is a LCA
        lca, omnian_path_root = lca_to_opr_edge

    # Identify the nodes in the first path up to the start of the edge to add
    omnian_nodes = omnian_path[omnian_path.index(omnian_path_root):omnian_path.index(omnian_path_leaf) + 1]

    # Identify the nodes in the second path from the end of the edge to add
    leaf_nodes = current_leaf_path[current_leaf_path.index(leaf_ending_root):omnian_path.index(lca)]

    # Combine these nodes to create the new path
    new_path = omnian_nodes + leaf_nodes
    print("[UPDATE_PATH] New Path based on omnians", omnian_path)
    print("[UPDATE_PATH] Current Leaf Path", current_leaf_path)
    print("[UPDATE_PATH] New Path", new_path)

    # Remove the old paths from the graph
    generated_tree.remove_nodes_from(new_path)
    generated_tree.remove_nodes_from(current_leaf_path)

    # Add the new path to the graph
    add_path(generated_tree, new_path)
    return generated_tree


def find_disjoint_paths(generated_tree: DiGraph, network: DiGraph) -> list:
    """
    This is a helper function to iter_tree.
    Find all disjoint paths between all pairs of nodes in the network N.
    Each graph I generate will be just disjoint paths, on the final step I will join these
    disjoint paths to create a tree with root rho and the same leaf set

    Args:
        generated_tree: the tree that is currently being built to solve the minimum enum problem
        network: the original network N
    Returns:
        List: The list of all paths found on the tree being generated
    """
    leaves = get_leaves(network)
    disjoint_paths = []
    for target in generated_tree.nodes():
        # target is a leaf node
        if generated_tree.out_degree(target) == 0:
            for source in generated_tree.nodes():
                if source != target:
                    paths = list(all_simple_paths(generated_tree, source, target))
                    for path in paths:
                        # Check if a path is not a subset of any path in disjoint_paths
                        if not any(set(path).issubset(set(p)) for p in disjoint_paths):
                            disjoint_paths.append(path)

    # Check JUST IN CASE the generated tree has a path of just a stray leaf node
    current_leaves_found = set()
    for path in disjoint_paths:
        disjoint_path_leaf = path[len(path) - 1]
        current_leaves_found.add(disjoint_path_leaf)
    for leaf in leaves - current_leaves_found:
        disjoint_paths.append([leaf])

    return disjoint_paths


def all_nodes_covered(nodes_used: dict) -> bool:
    """
    Check if all nodes were covered at least once
    Args:
        nodes_used: a dictionary with the number of times each node was used in a tree
    Returns:
        Boolean: True - all nodes were covered, False - some nodes were not covered
    """
    for node_usage in nodes_used.values():
        if node_usage == 0:
            return False
    return True


def count_untouched_score_in_path(omnian_path: list, nodes_used: dict,
                                  start='', end='', inclusive=False) -> int:
    """
    This is a helper function to iter_tree.
    Used within exchange argument to prioritize which path with unmatched omnian to pick
    There is an option to have a start and end parameter.
    Say you have [1, 2, 3, 4, 5], and start = 2 end = 5,
    you will only get the number of 0's for 3, 4; this is for inclusive=False.
    However, if inclusive was true, then you would get the number of 0's for 2, 3, 4, 5.
    This is to make the call whether to cut or not.

    Args:
        omnian_path: a list of a path that does end in an omnian node
        nodes_used: a dictionary with the number of times each node was used in a tree
        start: the start node to consider in the path
        end: the end node to consider in the path
        inclusive: a boolean to determine if the start and end nodes should be included in the count
    Returns:
        Int: the number of untouched nodes in the specified path slice
    """
    count = 0

    # Determine the slice of the path to consider
    if start == '' and end == '':
        path_slice = omnian_path
    else:
        try:
            if inclusive:
                start_index = omnian_path.index(start)
                end_index = omnian_path.index(end) + 1
            else:
                start_index = omnian_path.index(start) + 1
                end_index = omnian_path.index(end)
            path_slice = omnian_path[start_index:end_index]
        except ValueError:
            raise ValueError("[COUNT_UNTOUCHED] Start or end node not found in the given path")

    # Count the number of untouched nodes in the specified path slice
    for node in path_slice:
        if nodes_used[node] == 0:
            count += 1
    print("[COUNT_UNTOUCHED] Path ", path_slice, "has", count, "untouched nodes, inclusive", inclusive)
    return count


def prune_tree(tree: DiGraph, network: DiGraph):
    """
    This is a helper function to iter_tree
    This takes care of
    1- making sure you only have one root, rho. It does this by connecting loose ends up to any node
    2- you only have the same leaves from the original network N. It does this by removing any loose ends.
    So when I occasionally change paths, just leaving a hanging omnian will be cleaned up here

    Args:
        tree: the result of iter_tree, but we want to comply with the same leaf and root as N
        network: the original network N
    """
    root = get_root(network)
    leaves = get_leaves(network)

    # Make sure there is only one root in the tree you are making
    current_roots = get_all_roots(tree)
    while len(current_roots) != 1:
        roots_to_delete = set()
        for temp_root in current_roots:
            if temp_root == root:
                continue
            else:
                print("[Prune Tree] An extra root was found", temp_root)

            parents = list(network.predecessors(temp_root))
            found_root_path = False
            for parent in parents:
                # Try to pick node already existing in the generated tree
                # This will make it easier to not lose track of the initial disjoint paths
                if parent in tree.nodes():
                    tree.add_edge(parent, temp_root)
                    found_root_path = True
                    print("[Prune Tree] Will remove by adding edge: ", parent, '->', temp_root)
                    break

            # If nothing found, just pick any predecessor from N
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


def iter_tree(new_tree: DiGraph, omnian_paths: List,
              nodes_used: dict, network: DiGraph) -> DiGraph:
    """
    Iterate Tree:
    Using the input disjoint paths, create a tree with 1 root and all leaves in N.
    The general gist, the new_tree should start with disjoint paths ending with leaves in N.
    I want to extend the disjoint paths using the omnian paths, to reach the root.

    So taking the 'root' of these leaf ending disjoint paths, there are two cases
    1- There is no least common ancestor, effectively I am appending these nodes to path to reach the root
    2- There is a least common ancestor, I need update the disjoint path as follows:

    For Case 1, there are a few terms I should define to make this easier to understand
    - Leaf Ending Path (LEP): A disjoint path that ends in a leaf node
    - Omnian Path (OP): A disjoint path that ends in an omnian node
    There are two nodes to focus on the LEP, the Leaf Ending Root (LER) and a Least Common Ancestor (LCA) on the LEP.
    There is a possibility that the path of omnians could lead back to the LEP when checking edges on Network N,
    so to preserve the disjointness, I need to find the LCA on the LEP.

    A visualisation of the problem:
    LCA ->        [LEP Nodes]    -> LER -> [LEP Nodes] -> Leaf
    LCA -> OPR -> [OP Nodes] OPL -> LER

    To find the LCA, I check nodes in OP if they have an edge to LEP, if so, I can find the LCA.
    From this process I will define two other others:
    1. Omnian Path Leaf (OPL), the leaf of the OP, there is an edge (OPL, LER) in network N
    2. Omnian Path Root (OPR), the root of the OP, there is an edge (LCA, OPR) in network N

    I check if LCA -> [LEP Nodes] -> LER or LCA -> OPR -> [OP Nodes] OPL -> LER gives me more unused nodes or not.
    Once the decision is made, I update the generating tree to update the LEP.

    Main things I need to worry about to do this correctly are:
    1- Cut [LCA, ..., LER]
    2- Add [LCA, OPR, ..., OPL, LER]
    Main edges to worry about are (LCA, OPR) (OPL, LER) if you decide to swap!

    TODO: A note to PIs, you may want to do ONE more loop of omnian paths, because you may terminate too early
     and no discover paths that only become 'visible' once you reach the root.
    Args:
        new_tree: the base tree based from network N with only paths ending in a leaf.
        omnian_paths: a list of disjoint paths in the network N where the last node is an omnian node
        nodes_used: a dictionary with the number of times each node was used in a tree
        network: the original network N
    Returns:
        Tuple: a new tree that is the output of the iteration, with updated metrics
    """
    tripwire = 0

    while continue_building_tree(new_tree, network):
        all_leaf_ending_paths_in_generated_tree = find_disjoint_paths(new_tree, network)
        for leaf_ending_path in all_leaf_ending_paths_in_generated_tree:
            print("[ITER] Checking Leaf Ending Path", leaf_ending_path)
            if is_connected_to_other_leaf_path(network, all_leaf_ending_paths_in_generated_tree, leaf_ending_path):
                print("[ITER] This path has a parent going to another leaf ending path in Network N", leaf_ending_path)
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
                        # I want to check which omnian paths would be connected
                        # to current disjoint paths on the tree
                        for potential_leaf_path_node in network.successors(omnian_node):
                            # Exists in N, but not in your generating tree...
                            print("[ITER] Checking if edge exists in N, [Omnian]", omnian_node, "[Leaf]", potential_leaf_path_node)
                            if potential_leaf_path_node in leaf_ending_path:
                                opl_to_ler_edge = [omnian_node, potential_leaf_path_node]
                                print("[ITER] Found edge to exchange in N", opl_to_ler_edge)
                                candidate_edges_and_paths.append((opl_to_ler_edge, omnian_path))

                # If no candidate edges, continue to the next leaf ending path that should be changed up
                if len(candidate_edges_and_paths) == 0:
                    print("[ITER] no valid edge found")
                    continue

                # Compute which edge to pick based on the number of untouched nodes
                scores = {}
                edge_to_path = {}
                edge_to_lca_opl_edge = {}
                for opl_to_ler_edge, omnian_path in candidate_edges_and_paths:
                    omnian_path_leaf, leaf_ending_root = opl_to_ler_edge
                    lca_omnian_root_edge = least_common_ancestor(network, leaf_ending_path, omnian_path)
                    # Case 1- Omnian path helps extend a leaf path up, so no least common ancestor within the path
                    # Case 2- Omnian path has the least common ancestor within the path
                    if lca_omnian_root_edge is None:
                        omnian_score = count_untouched_score_in_path(omnian_path, nodes_used,
                                                                     inclusive=True)
                        tree_score = 0
                    else:
                        lca, omnian_path_root = lca_omnian_root_edge
                        # Remember, LCA is technically ONLY part of leaf ending path, NOT omnian path!
                        omnian_score = count_untouched_score_in_path(omnian_path, nodes_used,
                                                                     start=omnian_path_root,
                                                                     end=omnian_path_leaf,
                                                                     inclusive=True)
                        tree_score = count_untouched_score_in_path(leaf_ending_path, nodes_used,
                                                                   start=lca,
                                                                   end=leaf_ending_root)

                    # You subtract, because you gain the nodes in omnian path, 
                    # but might lose nodes in an existing leaf ending path
                    total_score = omnian_score - tree_score
                    scores[tuple(opl_to_ler_edge)] = total_score
                    edge_to_path[tuple(opl_to_ler_edge)] = omnian_path
                    if lca_omnian_root_edge is None:
                        edge_to_lca_opl_edge[tuple(opl_to_ler_edge)] = []
                    else:
                        edge_to_lca_opl_edge[tuple(opl_to_ler_edge)] = lca_omnian_root_edge

                    print("[ITER] edge", opl_to_ler_edge, " has a score of ", total_score)

                best_opl_to_ler_edge = max(scores, key=scores.get)
                best_score = scores[best_opl_to_ler_edge]

                if best_score <= 0:
                    print("[ITER] Best score is negative or zero, skipping update since you will NOT gain new nodes!")
                else:
                    omnian_path = edge_to_path[tuple(best_opl_to_ler_edge)]
                    best_edge_opl_to_ler = list(best_opl_to_ler_edge)
                    best_edge_lca_to_opr = edge_to_lca_opl_edge[tuple(best_opl_to_ler_edge)]
                    print("[ITER] Best Edge to pick", best_edge_opl_to_ler, "Updating Path now!")
                    combine_paths_based_on_edge(new_tree,
                                                omnian_path,
                                                leaf_ending_path,
                                                best_edge_opl_to_ler,
                                                best_edge_lca_to_opr)

        print("[ITER] Completed Path Update", tripwire)
        tripwire += 1
        if tripwire > 3:
            print("[ITER] Breaking out of loop! POST MORTEM NOW!")
            break

    print("[ITER] Completed Disjoint path creation, now pruning tree...")

    # I should not need this function tbh...
    # This should only be joining the disjoint paths
    prune_tree(new_tree, network)

    # Update Metrics of which nodes have been used in a tree
    for node in new_tree.nodes():
        counter = nodes_used[node]
        counter += 1
        nodes_used[node] = counter
    return new_tree


def initialize_enum(g: DiGraph, disjoint_paths: list) -> Tuple[DiGraph, List]:
    """
    This function has two important things to do
    1- Create a Tree, with just the paths to leaves
    2- Return Omnian paths
    Args:
        g: the original phylogenetic network N
        disjoint_paths: a list of disjoint paths in the network N, each path is generated from spanning tree algorithm
    Returns:
        Tuple: The base tree with only leaf paths, and the list of omnian paths
    """
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


def enum_trees(g: DiGraph, graph_name: str, draw=False) -> list:
    """
    The main function to compute minimum number of rooted trees spanning the network N
    Args:
        g: the original phylogenetic network N
        graph_name: the name of the graph to be drawn, based on input file name
        draw: a boolean to determine if the tree should be drawn in the images/ directory
    Returns:
        List: a list of DiGraphs, each representing a rooted tree
    """
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

        # Have a quick and easy way to break, after making 1 tree, there are bugs,
        # but it is the proof of concept that matters most.
        if len(trees) >= 1:
            break

    return trees
