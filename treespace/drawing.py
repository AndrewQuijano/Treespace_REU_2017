from networkx.drawing.nx_agraph import graphviz_layout
from networkx.drawing.nx_pylab import draw_networkx_labels
from networkx import draw_networkx_nodes, draw_networkx_edges, DiGraph
from networkx import draw
from networkx.exception import AmbiguousSolution, NetworkXPointlessConcept
import matplotlib.pyplot as plt
from textwrap import wrap
import platform
import matplotlib as mlt
from treespace.utils import get_root, get_leaves, is_omnian

plat = platform.system()


def draw_tree(graph: DiGraph, tree_name=None, highlight_edges=None, color_node_type=False):
    """
    Draw the phylogenetic network
    https://stackoverflow.com/questions/11479624/is-there-a-way-to-guarantee-hierarchical-output-from-networkx

    Args:
        graph (DiGraph): Input phylogenetic network.
        tree_name (str, optional): The output file name of the drawn tree. Defaults to None.
        highlight_edges (list, optional): The edges to be highlighted in the output drawing of the tree. Defaults to None.
        color_node_type (bool, optional): If True, colors omnian nodes red, leaves green, and the rest blue. Defaults to False.

    Returns:
        None: Saves an output file with the drawn tree.
    """
    r = get_root(graph)
    leaves = get_leaves(graph)
    try:
        pos = graphviz_layout(graph, prog='dot', root=r)
    except ImportError:
        print("Please install graphviz to draw the tree")
        return

    mlt.rcParams['figure.dpi'] = 200
    # For printing...
    fig = plt.figure(figsize=(8.5, 11))
    # fig = plt.figure(figsize=(20, 10))
    ax = fig.add_subplot(111)

    for node, data in graph.nodes(data=True):
        try:
            if color_node_type:
                if is_omnian(graph, node):
                    draw_networkx_nodes(graph, pos, node_color='red', nodelist=[node])
                elif node in leaves:
                    draw_networkx_nodes(graph, pos, node_color='green', nodelist=[node])
                else:
                    draw_networkx_nodes(graph, pos, nodelist=[node])
            else:
                draw_networkx_nodes(graph, pos, node_color=data['color'], nodelist=[node])
        except KeyError:
            draw_networkx_nodes(graph, pos, nodelist=[node])

    for source, target, data in graph.edges(data=True):
        try:
            if highlight_edges is not None:
                if (source, target) in highlight_edges:
                    draw_networkx_edges(graph, pos, edgelist=[(source, target)], edge_color='r', width=3)
                else:
                    draw_networkx_edges(graph, pos, edgelist=[(source, target)], edge_color=data['color'], width=3)
            else:
                draw_networkx_edges(graph, pos, edgelist=[(source, target)], edge_color=data['color'], width=3)
        except KeyError:
            draw_networkx_edges(graph, pos, edgelist=[(source, target)], width=1)

    all_nodes = set(graph.nodes())
    labels = dict(zip(all_nodes, all_nodes))
    draw_networkx_labels(graph, pos, labels=labels)

    # plt.show()
    # Use this site to edit: https://edotor.net/
    if tree_name is None:
        plt.title('Phylogenetic network')
        plt.savefig('network.png')
    else:
        ax.set_title('\n'.join(wrap(tree_name)))
        plt.savefig(tree_name + '.png')
    plt.close()


def draw_bipartite(graph, matches=None, graph_name="bipartite"):
    """
    Draw a bipartite graph
    https://stackoverflow.com/questions/35472402/how-do-display-bipartite-graphs-with-python-networkx-package
    Args:
        graph (Graph): The input bipartite graph.
        matches (dict, optional): The list of edges that are matched, they will be colored red. Defaults to None.
        graph_name (str, optional): The file name where the drawing is stored. Defaults to "bipartite".

    Returns:
        None: Saves an output file with the drawn bipartite graph.
    """
    try:
        x = {n for n, d in graph.nodes(data=True) if d['biparite'] == 0}
        y = set(graph) - x
        pos = dict()
        pos.update((n, (1, i)) for i, n in enumerate(x))  # put nodes from X at x=1
        pos.update((n, (2, i)) for i, n in enumerate(y))  # put nodes from Y at x=2
        plt.title('Bipartite Graph - Red means edge is matched, Blue otherwise')
        # draw(graph, pos=pos, with_labels=True, arrows=True)
        # draw matchings
        if matches is None:
            draw(graph, with_labels=True, arrows=True)
        else:
            nodes = list(graph.nodes())
            draw_networkx_nodes(graph, pos, nodelist=nodes)
            matched_edges, unmatched_edges = get_edges(set(graph.edges()), matches)
            draw_networkx_edges(graph, pos, edgelist=matched_edges, width=8, alpha=0.5, edge_color='r')
            draw_networkx_edges(graph, pos, edgelist=unmatched_edges, width=8, alpha=0.5, edge_color='b')
            draw_networkx_labels(graph, pos, dict(zip(nodes, nodes)))
    except AmbiguousSolution:
        draw(graph, with_labels=True, arrows=True)
    except NetworkXPointlessConcept:
        draw(graph, with_labels=True, arrows=True)
    except KeyError:
        draw(graph, with_labels=True, arrows=True)
    # plt.show()
    plt.savefig(graph_name + '.png')
    plt.close()


def get_edges(all_edges: set, matches: dict) -> [set, set]:
    """
    Helper function for draw_bipartite. Separates the edges that are to be highlighted (matched)
    and not highlighted (unmatched).

    Args:
        all_edges (set): Set of all edges in the bipartite graph.
        matches (dict): A dictionary of matched edges.

    Returns:
        tuple: A tuple containing two sets:
            - matched_edges (set): The edges that are matched.
            - unmatched_edges (set): The edges that are not matched.
    """
    matched_edges = set()
    unmatched_edges = all_edges
    for s, t in matches.items():
        e = (s, t)
        if e in unmatched_edges:
            matched_edges.add((s, t))
    unmatched_edges = unmatched_edges - matched_edges
    return matched_edges, unmatched_edges
