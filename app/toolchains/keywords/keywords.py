from utils.embedding_store import (
    get_embeddings_for_texts,
    load_embedding_store,
)
from utils.resource_manager import RESOURCES

from sentence_transformers import SentenceTransformer

import networkx as nx
import json


def load_embedder(model_name: str) -> SentenceTransformer:
    if SentenceTransformer is None:
        raise ModuleNotFoundError(
            "sentence-transformers is required. Install it with `pip install sentence-transformers`."
        )
    return SentenceTransformer(model_name)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


all_descriptions = { id: f"{resource.title}\n{resource.abstract}" for id, resource in list(RESOURCES.items()) }


model = load_embedder(MODEL_NAME)
store = load_embedding_store(f"{MODEL_NAME}_keywords")
embeddings, store = get_embeddings_for_texts(
    MODEL_NAME,
    *zip(*all_descriptions.items()),
    lambda batch: model.encode(batch, normalize_embeddings=True, show_progress_bar=False),
    store=store,
)



G = nx.Graph()
G.add_nodes_from(all_descriptions.keys())
for u in all_descriptions.keys():
    u_edges = []
    for v in all_descriptions.keys():
        if u == v: continue
        u_edges.append((embeddings[u] @ embeddings[v], v))
    u_edges.sort()
    u_edges = u_edges[::-1]
    u_edges = u_edges[:10]
    for w, v in u_edges:
        G.add_edge(u, v, similarity=float(w))

json.dump(nx.node_link_data(G), open("keyword_graph.json", "w"))
