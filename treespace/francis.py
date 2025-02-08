from networkx import DiGraph, Graph, all_simple_paths
from networkx import get_node_attributes
import platform

from treespace.drawing import draw_bipartite
from treespace.utils import get_root, maximum_matching_all, get_leaves

plt = platform.system()


def build_francis_bipartite(network: DiGraph) -> Graph:
    """
    Read the paper "New Characterisations of Tree-Based Networks and Proximity Measures"
    Complete bipartite matching of all vertices in the network
    :param network: the input phylogenetic network B
    :return: a bipartite graph which will be used for the next step of the algorithm
    """
    # Build V1 and V2
    francis = Graph()
    for node in network.nodes():
        francis.add_node(node, biparite=0)
        francis.add_node('V-' + node, biparite=1)

    data = get_node_attributes(francis, 'biparite')
    for s, t in network.edges():
        # s is in V_1
        if data[s] == 0:
            francis.add_edge(s, 'V-' + t)
    return francis


def vertex_disjoint_paths(network: DiGraph, name=None, draw=False) -> [int, list]:
    """
    Taken from "New Characterisations of Tree-Based Networks and Proximity Measures"
    Once the bipartite matching is complete,
    get the vertex disjoint paths from the matching as described in the paper.
    :param network: The phylogenetic network N
    :param name: the name of the graph, this is used to save output images of the network
    :param draw: if True, the bipartite graph will be drawn
    :return:
        - The unmatched omnian nodes in the network from maximum matching
        - The list of vertex disjoint paths in generated Bipartite Graph used to make the spanning tree
    """
    francis = build_francis_bipartite(network)
    max_matchings = maximum_matching_all(francis)

    # Step 1: Compute disjoint paths
    u2 = set()
    matches = []
    nodes = set(network.nodes())
    missing_v1 = set()

    data = get_node_attributes(francis, 'biparite')
    for s, t in max_matchings.items():
        if data[s] == 0:
            matches.append((s, t[2:]))
            u2.add(t[2:])
            missing_v1.add(s)

    u2 = nodes - u2
    missing_v1 = nodes - missing_v1

    # Build all Vertex Disjoint paths
    paths = []
    for u in u2:
        # You do delete matches, so you need to pass a copy
        p = build_path(u, matches.copy())
        paths.append(p)

    # Step 2: Exclude leaves to know number of new leaves
    leaves = get_leaves(network)
    missing_v1 = len(missing_v1 - set(leaves))

    if draw:
        if name is None:
            draw_bipartite(francis, max_matchings, "francis-bipartite")
        else:
            draw_bipartite(francis, max_matchings, name + "-francis-bipartite")

    return missing_v1, paths


def get_next_node(u: str, matches):
    """
    Helper function for rooted_spanning_tree and starting_match
    :param u: a node in the network
    :param matches: maximum matching, used to generate the vertex disjoint path
    :return: Next element in path
    """
    for match in matches:
        if match[0] == u:
            matches.remove(match)
            return match[1]
    return None


def build_path(u: str, matches):
    """
    Helper function for rooted_spanning_tree
    :param u: node u, described in the paper
    :param matches: complete maximum matching
    :return: Output a maximum path from maximum matching starting at vertex u
    """
    max_path = list()
    new_vertex = u
    max_path.append(u)
    while True:
        new_vertex = get_next_node(new_vertex, matches)
        if new_vertex is None:
            return max_path
        else:
            max_path.append(new_vertex)


def rooted_spanning_tree(network: DiGraph, paths: list) -> DiGraph:
    """
    Taken from "New Characterisations of Tree-Based Networks and Proximity Measures"
    Using the vertex disjoint paths, build the rooted spanning tree
    :param network: A Phylogenetic Network N
    :param paths:
    :return: A rooted spanning tree based on the vertex disjoint paths, see the paper
    """
    spanning_tree = DiGraph()
    root = get_root(network)

    # Build the Spanning Tree from each path
    for path in paths:
        parents = list(network.predecessors(path[0]))

        if root not in path:
            spanning_tree.add_edge(parents[0], path[0])

        # Add the disjoint path
        for i in range(len(path) - 1):
            spanning_tree.add_edge(path[i], path[i + 1])

    return spanning_tree


def tree_based_network(network: DiGraph, spanning_tree: DiGraph) -> DiGraph:
    """
    Taken from "New Characterisations of Tree-Based Networks and Proximity Measures"
    Using the rooted spanning tree, build the tree-based network by appending a leaf to unmatched omnian nodes
    :param network: A Phylogenetic Network N
    :param spanning_tree: A rooted spanning tree based on the vertex disjoint paths, built earlier
    :return: A tree-based network based on the rooted spanning tree
    """
    leaves = get_leaves(network)
    paths = get_paths(spanning_tree)
    leaf_count = 0
    for path in paths:
        if not path[len(path) - 1] in leaves:
            node = 'new-leaf-' + str(leaf_count)
            spanning_tree.add_node(node)
            spanning_tree.add_edge(path[len(path) - 1], node)
            leaf_count += 1
    return spanning_tree


def get_paths(spanning_tree: DiGraph) -> list:
    """
    Helper function for tree_based_network function.
    This gets the paths from the rooted spanning tree, which we use to append the leaf
    :param spanning_tree: A rooted spanning tree based on the vertex disjoint paths, built earlier
    :return: The list of disjoint paths in the spanning tree
    """
    paths = []
    roots = []
    leaves = []
    for node in spanning_tree.nodes():
        if spanning_tree.in_degree(node) == 0:  # it's a root
            roots.append(node)
        elif spanning_tree.out_degree(node) == 0:  # it's a leaf
            leaves.append(node)

    for root in roots:
        for leaf in leaves:
            for path in all_simple_paths(spanning_tree, root, leaf):
                paths.append(path)
    return paths
