from networkx import DiGraph
from networkx.algorithms.flow import min_cost_flow
from treespace_metrics.utils import get_leaves
from treespace_metrics.francis import build_path, rooted_spanning_tree
from treespace_metrics.drawing import draw_tree
import platform
from typing import Tuple

plt = platform.system()


def maximum_covering_subtree(network: DiGraph, name=None, draw=False) -> Tuple[DiGraph, int]:
    """
    Implements the algorithm described in 'Maximum Covering Subtrees for Phylogenetic Networks' by Davidov et al.
    Finds the minimum number of nodes to cut to make a network tree-based.

    Args:
        network (DiGraph): The phylogenetic network as a directed graph.
        name (str, optional): The name of the file to save the output image. Defaults to None.
        draw (bool, optional): Whether to generate and save an image of the network. Defaults to False.

    Returns:
        tuple[DiGraph, int]: A tuple containing the tree-based network and the number of nodes removed.
    """
    leaves = get_leaves(network)
    # Build min-cost flow network
    # Create V_in and V_out node for each
    f = create_flow_network(network, leaves)
    flows = min_cost_flow(f)
    start = []
    matches = []
    for src, flow in flows.items():
        if src == "s":
            for destination_node, value in flow.items():
                if value == 1:
                    dst_node_id = destination_node[2:]
                    start.append(dst_node_id)
        elif src.startswith('o-'):
            for destination_node, value in flow.items():
                if destination_node == "t":
                    continue
                if value == 1:
                    src_node_id = src[2:]
                    dst_node_id = destination_node[2:]
                    matches.append((src_node_id, dst_node_id))
                    # print(str(src_node_id) + "," + str(dst_node_id))
    paths = []
    for u in start:
        # You do delete matches, so you need to pass a copy
        p = build_path(u, matches.copy())
        paths.append(p)

    # Build rooted Spanning Tree
    tree_based_network = rooted_spanning_tree(network, paths)
    diff = set(network.nodes()) - set(tree_based_network.nodes())
    n = len(diff)

    if draw:
        if name is None:
            draw_tree(network, "original network")
            draw_tree(tree_based_network, "tree-based network")
        else:
            draw_tree(network, name)
            draw_tree(tree_based_network, name + "-MAX-CST")
    return tree_based_network, n


def create_flow_network(network: DiGraph, leaves: set) -> DiGraph:
    """
    Generates the flow network required to compute the minimum number of nodes to cut.

    Args:
        network (DiGraph): The phylogenetic network as a directed graph.
        leaves (list): A list of leaf nodes in the network.

    Returns:
        DiGraph: A directed graph representing the flow network.
    """
    f = DiGraph()
    f.add_node('s', demand=-len(leaves))
    f.add_node('t', demand=len(leaves))
    # Set-up all the nodes
    for node in network.nodes():
        f.add_node("i-" + str(node))
        f.add_node("o-" + str(node))
        f.add_edge("i-" + str(node), "o-" + str(node), capacity=1, weight=-1)
        f.add_edge('s', "i-" + str(node), capacity=1, weight=0)
        if node in leaves:
            f.add_edge("o-" + str(node), 't', capacity=1, weight=0)

    # Set-up all the edges
    for edge in network.edges():
        f.add_edge("o-" + str(edge[0]), "i-" + str(edge[1]), capacity=1, weight=0)
    return f
