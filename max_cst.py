from misc import get_leaves
from networkx import DiGraph
from networkx.algorithms.flow import min_cost_flow
from francis import build_path, rooted_spanning_tree
from drawing import draw_tree
import platform
plt = platform.system()


def maximum_covering_subtree(network, name=None, draw=False):
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
    # print("Vertices not used in MAX-CST: " + str(diff))
    n = len(diff)
    if draw:
        if name is None:
            draw_tree(network, "original network")
            draw_tree(tree_based_network, "tree-based network")
        else:
            draw_tree(network, name)
            draw_tree(tree_based_network, name + "-MAX-CST")
    return tree_based_network, n


# Input: Phylogenetic Network N and the leaves of Network N
# Output: Flow Network as described in Figure 2 of Daviddov et al. paper
def create_flow_network(g, leaves):
    f = DiGraph()
    f.add_node('s', demand=-len(leaves))
    f.add_node('t', demand=len(leaves))
    # Set-up all the nodes
    for node in g.nodes():
        f.add_node("i-" + str(node))
        f.add_node("o-" + str(node))
        f.add_edge("i-" + str(node), "o-" + str(node), capacity=1, weight=-1)
        f.add_edge('s', "i-" + str(node), capacity=1, weight=0)
        if node in leaves:
            f.add_edge("o-" + str(node), 't', capacity=1, weight=0)

    # Set-up all the edges
    for edge in g.edges():
        f.add_edge("o-" + str(edge[0]), "i-" + str(edge[1]), capacity=1, weight=0)
    return f
