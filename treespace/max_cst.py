from networkx import DiGraph
from networkx.algorithms.flow import min_cost_flow
import platform

from treespace.utils import get_leaves
from treespace.francis import build_path, rooted_spanning_tree
from treespace.drawing import draw_tree

plt = platform.system()


def maximum_covering_subtree(network: DiGraph, name=None, draw=False) -> [DiGraph, int]:
    """
    Read 'Maximum Covering Subtrees for Phylogenetic Networks' by Davidov et al.
    This function implements the whole algorithm described in the paper that finds
    the minimum number of nodes to cut to make a network N tree-based
    :param network: phylogenetic network
    :param name: the name of the file to save the output image
    :param draw: confirm if there will be an image generated
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


def create_flow_network(network: DiGraph, leaves: list) -> DiGraph:
    """
    Read 'Maximum Covering Subtrees for Phylogenetic Networks' by Davidov et al.
    This is a helper function to generate the flow network required to compute the minimum number of nodes to cut
    :param network: Phylogenetic network N
    :param leaves: leaves in the network N
    :return:
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
