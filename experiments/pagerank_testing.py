import networkx as nx
from random import seed, randrange, random
seed(1)
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 10), dpi=80)


N = 20

G = nx.Graph()
G.add_nodes_from(range(N))
edges = set()
edge_similarity = {}
while len(edges) < 40:
    u = randrange(0, N)
    v = randrange(0, N - 1)
    if v >= u: v += 1
    if u > v: u, v = v, u
    edges.add((u, v))
    edge_similarity[(u, v)] = random()
G.add_edges_from(edges)
# nx.set_edge_attributes(G, edge_similarity, "similarity")

def get_similarity(u, v):
    if u > v: u, v = v, u
    if (u, v) not in edge_similarity: return 0
    return edge_similarity[(u, v)]

c = randrange(0, N)
importance = [0] * N
importance[c] = 1.0

damping = 0.85

for _ in range(100):
    new_importance = [0] * N
    for u in range(N):
        similarity_sum = 0
        for v in G.neighbors(u):
            if v == c: continue
            similarity_sum += get_similarity(u, v)
        for v in G.neighbors(u):
            if v == c: continue
            new_importance[v] += importance[u] * damping * get_similarity(u, v) / similarity_sum
        new_importance[c] += importance[u] * (1 - damping)
    importance = new_importance


pos = nx.kamada_kawai_layout(G)
nx.draw(
    G, pos,
    node_color=["purple" if v == c else "blue" for v in range(N)],
    node_size=list(map(lambda t: 1000 * t, importance)),
    labels={ i: f"{val:.02f}" for i, val in enumerate(importance) }
)
edge_similarity_formatted = { k: f"{v:.02f}" for k, v in edge_similarity.items() }
nx.draw_networkx_edge_labels(G, pos, edge_similarity_formatted)

plt.show()
