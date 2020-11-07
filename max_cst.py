from misc import get_leaves
from networkx import DiGraph
from networkx.algorithms.flow import min_cost_flow
from francis import build_path, rooted_spanning_tree
from drawing import draw_tree
import platform
plt = platform.system()


def maximum_covering_subtree(network, name=None, max_cst=None):
    leaves = get_leaves(network)
    # Build min-cost flow network
    # Create V_in and V_out node for each
    if max_cst is None:
        f = create_flow_network(network, leaves)
    else:
        f = create_flow_network(network, leaves, max_cst)
    flows = min_cost_flow(f)
    start = []
    matches = []
    for src, flow in flows.items():
        if "s" == src:
            for dst, v in flow.items():
                if v == 1:
                    dst_node_id = dst[2:]
                    start.append(dst_node_id)
        if src.startswith('o-'):
            for dst, v in flow.items():
                if dst == "t":
                    continue
                if v == 1:
                    src_node_id = src[2:]
                    dst_node_id = dst[2:]
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
    # print("Verticies not used in MAX-CST: " + str(diff))
    n = len(diff)
    if plt == "Linux":
        if name is None:
            draw_tree(network, "original network")
            draw_tree(tree_based_network, "tree-based network")
        else:
            draw_tree(network, name)
            draw_tree(tree_based_network, name + "-MAX-CST")
    return tree_based_network, n


def create_flow_network(g, leaves, filtered_nodes=set()):
    f = DiGraph()
    f.add_node('s', demand=-len(leaves))
    f.add_node('t', demand=len(leaves))
    # Set-up all the nodes
    for node in g.nodes():
        f.add_node("i-" + str(node))
        f.add_node("o-" + str(node))
        if node in filtered_nodes:
            f.add_edge("i-" + str(node), "o-" + str(node), capacity=1, weight=-1)
        else:
            f.add_edge("i-" + str(node), "o-" + str(node), capacity=1, weight=-2)
        f.add_edge('s', "i-" + str(node), capacity=1, weight=0)
        if node in leaves:
            f.add_edge("o-" + str(node), 't', capacity=1, weight=0)
    # Set-up all the edges
    for edge in g.edges():
        f.add_edge("o-" + str(edge[0]), "i-" + str(edge[1]), capacity=1, weight=0)
    return f


# An attempt to solve the second open question by Francis et al.
def count_trees(graph, name=None):
    current = set()
    all_nodes = set(graph.nodes())
    trees = 0
    while current != all_nodes:
        tree, n = maximum_covering_subtree(graph, max_cst=current)
        diff = all_nodes - set(tree.nodes())
        print("Nodes not used in MAX-CST: " + str(diff))
        current = current.union(set(tree.nodes()))
        print("collected: " + str(current))
        trees += 1
        if plt == "Linux":
            if name is not None:
                draw_tree(tree, name + '-' + str(trees))
            else:
                draw_tree(tree, 'subtree-' + str(trees))
    return trees
