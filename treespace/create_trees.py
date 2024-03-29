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


# Iterate Tree, build a tree from disjoint paths, update metrics
def iterate_tree(disjoint_paths: list, nodes_used: dict, g) -> DiGraph:
    tree = DiGraph()
    # Build tree from disjoint paths
    leaves = get_leaves(g)
    root = get_root(g)

    # Essentially similar to spanning tree, but NO omnians though
    for path in disjoint_paths:
        # Check if the path ends in a leaf or not...
        if not path[len(path) - 1] in leaves and root not in path:
            continue

        # Repeat from Spanning Tree building...
        parents = list(g.predecessors(path[0]))

        if root not in path:
            tree.add_edge(parents[0], path[0])

        # Add the path to the tree
        for i in range(len(path) - 1):
            tree.add_edge(path[i], path[i + 1])

    # Make sure to add any other paths if needed to connect leaf paths
    all_roots = get_all_roots(tree)
    while len(all_roots) != 1:
        to_delete = set()
        for temp_root in all_roots:
            if temp_root == root:
                continue
            parents = list(g.predecessors(temp_root))
            tree.add_edge(parents[0], temp_root)
            to_delete.add(temp_root)
        # Delete temp_roots and check if you need to keep adding more paths up...
        for remove_node in to_delete:
            all_roots.remove(remove_node)
        all_roots = all_roots.union(get_all_roots(tree))

    # Make sure you stick to leaf condition too...
    current_leaves = get_leaves(tree)
    while leaves != current_leaves:
        del_leaf = set()
        for leaf in current_leaves:
            if leaf not in leaves:
                tree.remove_node(leaf)
                del_leaf.add(leaf)
        for leaf in del_leaf:
            current_leaves.remove(leaf)
        current_leaves = current_leaves.union(get_leaves(tree))

    # Update Metrics
    for node in tree.nodes():
        counter = nodes_used[node]
        counter += 1
        nodes_used[node] = counter
    return tree


# Exchange algorithm
# Essentially, starting from one set of disjoint paths, change the node the omnian should be matched with
# You should have the same number of disjoint paths, but the new tree should be different and optimize picking
# more new nodes
def exchange_disjoint_paths(disjoint_paths: list, count_nodes: dict, graph: DiGraph) -> list:
    new_path = []
    leaves = get_leaves(graph)
    omnian_paths = []
    leaf_paths = []
    # Break paths ending in omnian and ending in leaf
    for path in disjoint_paths:
        if path[len(path) - 1] not in leaves:
            omnian_paths.append(path)
        else:
            leaf_paths.append(path)
    # Check what path the omnian node could be matched to now
    # Could use node counting to determine priority if necessary? IT IS NEEDED!
    # Goal: Create disjoint paths to leaves, using nodes with minimal coverage as possible.
    return new_path


def enum_trees(g: DiGraph, graph_name: str, draw=False) -> list:
    trees = []
    # Start with getting disjoint paths and drawing it on the graph for visualization
    _, paths = vertex_disjoint_paths(g)
    spanning_tree = rooted_spanning_tree(g, paths)

    if draw:
        draw_tree(g, graph_name + '-spanning-tree', highlight_edges=spanning_tree.edges())

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
        paths = exchange_disjoint_paths(paths, node_used_count, g)
        break

    return trees


def path_to_edges(paths: list) -> list:
    edge_list = []
    for path in paths:
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            edge_list.append(edge)
    return edge_list
