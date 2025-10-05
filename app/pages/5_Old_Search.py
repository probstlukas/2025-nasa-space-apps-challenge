import streamlit as st
import networkx as nx
from random import seed, randrange, random

seed(1)
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")

G: nx.Graph = nx.node_link_graph(json.load(open("./data/keyword_graph.json", "r")))


def create_relevance_graph(c, lim):
    relevance = [0] * G.order()
    relevance[c] = 1.0

    damping = 0.85
    to_index = {v: i for i, v in enumerate(G.nodes)}

    for _ in range(100):
        new_relevance = [0] * G.order()
        for u in G.nodes:
            similarity_sum = 0
            for v in G.neighbors(u):
                if to_index[v] == c:
                    continue
                similarity_sum += G.get_edge_data(u, v)["similarity"]
            for v in G.neighbors(u):
                if to_index[v] == c:
                    continue
                new_relevance[to_index[v]] += (
                    relevance[to_index[u]]
                    * damping
                    * G.get_edge_data(u, v)["similarity"]
                    / similarity_sum
                )
            new_relevance[c] += relevance[to_index[u]] * (1 - damping)
        relevance = new_relevance

    norm = relevance[c]
    for i in range(G.order()):
        relevance[i] = min(relevance[i] / norm, 1.0)

    relevant = [
        i
        for i in range(G.order())
        if relevance[i] >= sorted(relevance)[G.order() - min(G.order(), lim)]
    ]
    node_list = list(G.nodes)
    R = nx.induced_subgraph(G, map(lambda i: node_list[i], relevant))

    fig, ax = plt.subplots()
    fig.set_size_inches(5, 5)
    ax.axis("off")

    pos = nx.spring_layout(G, seed=0)
    nx.draw_networkx_nodes(
        R,
        pos,
        node_color=["#888888" for _ in R.nodes],
        node_size=[2000 - 10 for _ in R.nodes],
        ax=ax,
    )
    nx.draw_networkx_nodes(
        R,
        pos,
        node_color=["#FC7303" if to_index[v] == c else "#0066FF" for v in R.nodes],
        node_size=[2000 * relevance[to_index[v]] for v in R.nodes],
        ax=ax,
    )
    nx.draw_networkx_labels(
        R, pos, labels={v: f"[{to_index[v]}]" for v in R.nodes}, ax=ax
    )
    nx.draw_networkx_edges(R, pos, edge_color="#888888", ax=ax)
    # xlim = ax.get_xlim()
    # ylim = ax.get_ylim()
    # nx.draw_networkx_edges(G, pos, edgelist=secondary_edges, edge_color="#888888", alpha=0.4, ax=ax)
    # ax.set_xlim(xlim)
    # ax.set_ylim(ylim)

    relevance[c] += 1e-9
    relevant.sort(key=lambda i: -relevance[i])
    relevant = list(map(lambda i: (i, node_list[i]), relevant))

    return relevant, fig


c = 0
description_column, connection_column = st.columns([0.5, 0.5])
relevant, fig = create_relevance_graph(c, 7)
for entry in relevant:
    entry_id, entry_name = entry
    entry_data = f"Christopher do title here for {entry_id}"
    description_column.write(f"[{entry_id}] {entry_data}")
    description_column.divider()
connection_column.pyplot(fig, transparent=True)
