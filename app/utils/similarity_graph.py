import pickle
from utils.embedding_store import (
    get_embeddings_for_texts,
    load_embedding_store,
)
from utils.config import SIM_GRAPH, RESOURCE_PATH


from sentence_transformers import SentenceTransformer

import networkx as nx
import json
import tqdm


def load_embedder(model_name: str) -> SentenceTransformer:
    if SentenceTransformer is None:
        raise ModuleNotFoundError(
            "sentence-transformers is required. Install it with `pip install sentence-transformers`."
        )
    return SentenceTransformer(model_name)


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_or_create_similarity_graph():
    with open(RESOURCE_PATH, "rb") as f:
        RESOURCES = pickle.load(f)
    print("Create similarity graph from scratch")
    all_descriptions = {
        id: f"{resource.title}\n{resource.abstract}"
        for id, resource in list(RESOURCES.items())
    }

    print("a")
    model = load_embedder(MODEL_NAME)
    print("b")
    store = load_embedding_store(f"{MODEL_NAME}_keywords")
    print("c")
    embeddings, store = get_embeddings_for_texts(
        MODEL_NAME,
        *zip(*all_descriptions.items()),
        lambda batch: model.encode(
            batch, normalize_embeddings=True, show_progress_bar=False
        ),
        store=store,
    )

    G = nx.Graph()
    for v, desc in all_descriptions.items():
        G.add_node(v, {"description": desc})
    for u in tqdm.tqdm(all_descriptions.keys()):
        u_edges = []

        for v in all_descriptions.keys():
            if u == v:
                continue
            u_edges.append((embeddings[u] @ embeddings[v], v))
        u_edges.sort()
        u_edges = u_edges[::-1]
        u_edges = u_edges[:10]
        for w, v in u_edges:
            G.add_edge(u, v, similarity=float(w))

    return G


SIMILARITY_GRAPH = None


def _load_similarity_graph():
    global SIMILARITY_GRAPH

    if SIM_GRAPH.exists():
        with open(SIM_GRAPH, "rb") as f:
            SIMILARITY_GRAPH = pickle.load(f)

    if SIMILARITY_GRAPH is None:
        SIMILARITY_GRAPH = load_or_create_similarity_graph()

    if not SIM_GRAPH.exists():
        with open(SIM_GRAPH, "wb") as file:
            pickle.dump(SIMILARITY_GRAPH, file)


# _load_similarity_graph()


if __name__ == "__main__":
    _load_similarity_graph()
