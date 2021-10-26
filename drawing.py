from networkx.drawing.nx_agraph import graphviz_layout
from networkx.drawing.nx_pylab import draw_networkx_labels, draw_networkx_edge_labels
from networkx import draw_networkx_nodes, draw_networkx_edges, get_edge_attributes
from networkx import draw, get_node_attributes
from networkx.exception import AmbiguousSolution, NetworkXPointlessConcept
import matplotlib.pyplot as plt
from textwrap import wrap
from misc import get_root
import platform
import matplotlib as mlt

plat = platform.system()


# https://stackoverflow.com/questions/11479624/is-there-a-way-to-guarantee-hierarchical-output-from-networkx
def draw_tree(graph, tree_name=None, highlight_edges=None, draw_edge_labels=False):
    if plat != "Linux":
        return
    r = get_root(graph)
    pos = graphviz_layout(graph, prog='dot', root=r)

    mlt.rcParams['figure.dpi'] = 200
    # For printing...
    fig = plt.figure(figsize=(8.5, 11))
    # fig = plt.figure(figsize=(20, 10))
    ax = fig.add_subplot(111)

    capacities = get_edge_attributes(graph, "capacity")

    if draw_edge_labels:
        draw_networkx_edge_labels(graph, pos, capacities)

    if highlight_edges is not None:
        draw_networkx_edges(graph, pos, edgelist=highlight_edges, edge_color='r', width=5)

    label_attribute = get_node_attributes(graph, 'labels')
    if len(label_attribute) != 0:
        draw_networkx_nodes(graph, pos, nodelist=graph.nodes())
        draw_networkx_edges(graph, pos, edgelist=graph.edges())
        draw_networkx_labels(graph, pos, label_attribute)
    else:
        draw(graph, pos, with_labels=True, arrows=True)

    # plt.show()
    if tree_name is None:
        plt.title('Phylogenetic network')
        plt.savefig('network.png')
    else:
        ax.set_title('\n'.join(wrap(tree_name)))
        plt.savefig(tree_name + '.png')
    plt.close()


# https://stackoverflow.com/questions/35472402/how-do-display-bipartite-graphs-with-python-networkx-package
def draw_bipartite(graph, matches=None, graph_name="bipartite"):
    if plat != "Linux":
        return
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
            matched_edges, unmatched_edges = get_edges(graph.edges(), matches)
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


def get_edges(all_edges, matches):
    matched_edges = set()
    unmatched_edges = set(all_edges)
    for s, t in matches.items():
        e = (s, t)
        if e in unmatched_edges:
            matched_edges.add((s, t))
    unmatched_edges = unmatched_edges - matched_edges
    return matched_edges, unmatched_edges
