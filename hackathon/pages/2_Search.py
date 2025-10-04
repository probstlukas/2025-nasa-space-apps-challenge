import streamlit as st
import networkx as nx
from random import seed, randrange, random
seed(1)
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 10), dpi=80)

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

c = randrange(0, N)


importance = [0] * G.order()
importance[c] = 1.0

damping = 0.85

for _ in range(100):
    new_importance = [0] * G.order()
    for u in range(G.order()):
        similarity_sum = 0
        for v in G.neighbors(u):
            if v == c: continue
            similarity_sum += G.get_edge_data(u, v)["similarity"]
        for v in G.neighbors(u):
            if v == c: continue
            new_importance[v] += importance[u] * damping * G.get_edge_data(u, v)["similarity"] / similarity_sum
        new_importance[c] += importance[u] * (1 - damping)
    importance = new_importance

for i in range(G.order()):
    importance[i] /= 1 - damping

number_of_results = 8
relevant = [i for i in range(N) if importance[i] >= sorted(importance)[G.order() - number_of_results]]
R = nx.induced_subgraph(G, relevant)


pos = nx.kamada_kawai_layout(R)
nx.draw_networkx_nodes(
    R, pos,
    node_color=["#AAAAAA" for _ in R.nodes],
    node_size=[2000 - 10 for _ in R.nodes]
)
nx.draw_networkx_nodes(
    R, pos,
    node_color=["#FC7303" if v == c else "#0066FF" for v in R.nodes],
    node_size=[2000 * importance[v] for v in R.nodes]
)
nx.draw_networkx_labels(
    R, pos,
    labels={ v: f"[{v}]" for v in R.nodes }
)
nx.draw_networkx_edges(R, pos)

st.markdown("ok")
