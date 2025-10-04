import streamlit as st
import networkx as nx
from random import seed, randrange, random
seed(1)
import matplotlib.pyplot as plt

st.set_page_config(page_title="Search", page_icon="🔍")



N = 20

G = nx.Graph()
G.add_nodes_from(range(N))
edges = set()
edges_with_similarity = []
while len(edges) < 40:
    u = randrange(0, N)
    v = randrange(0, N - 1)
    if v >= u: v += 1
    if u > v: u, v = v, u
    if (u, v) in edges: continue
    edges.add((u, v))
    edges_with_similarity.append((u, v, random()))

for u, v, sim in edges_with_similarity:
    G.add_edge(u, v, similarity=sim)


def create_relevance_graph(c, lim):
    relevance = [0] * G.order()
    relevance[c] = 1.0

    damping = 0.85

    for _ in range(100):
        new_relevance = [0] * G.order()
        for u in range(G.order()):
            similarity_sum = 0
            for v in G.neighbors(u):
                if v == c: continue
                similarity_sum += G.get_edge_data(u, v)["similarity"]
            for v in G.neighbors(u):
                if v == c: continue
                new_relevance[v] += relevance[u] * damping * G.get_edge_data(u, v)["similarity"] / similarity_sum
            new_relevance[c] += relevance[u] * (1 - damping)
        relevance = new_relevance

    for i in range(G.order()):
        relevance[i] /= 1.0 - damping
        relevance[i] = min(relevance[i], 1.0)

    relevant = [i for i in range(N) if relevance[i] >= sorted(relevance)[G.order() - min(G.order(), lim)]]
    R = nx.induced_subgraph(G, relevant)

    fig, ax = plt.subplots()
    fig.set_size_inches(5, 10)
    ax.axis("off")

    pos = nx.spring_layout(R, k=0.35, seed=0)
    nx.draw_networkx_nodes(
        R, pos,
        node_color=["white" for _ in R.nodes],
        node_size=[2000 - 10 for _ in R.nodes],
        ax=ax
    )
    nx.draw_networkx_nodes(
        R, pos,
        node_color=["#FC7303" if v == c else "#0066FF" for v in R.nodes],
        node_size=[2000 * relevance[v] for v in R.nodes],
        ax=ax
    )
    nx.draw_networkx_labels(
        R, pos,
        labels={ v: f"[{v}]" for v in R.nodes },
        ax=ax
    )
    nx.draw_networkx_edges(R, pos, edge_color="white", ax=ax)

    return relevant, fig



search_query = st.text_input("Search here")
description_column, connection_column = st.columns([0.50, 0.50])
if search_query:
    if not search_query.isdigit():
        description_column.write(f"The search query \"{search_query}\" is not a number")
    else:
        c = int(search_query)
        if c >= N:
            description_column.write(f"The search query {c} is too large")
        else:
            relevant, fig = create_relevance_graph(c, 8)
            for entry in relevant:
                description_column.write(f"Found relevant entry {entry}")
                description_column.divider()
            connection_column.pyplot(fig, transparent=True)
