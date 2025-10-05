"""Utility for building and caching a similarity graph between resources."""

from __future__ import annotations

import json
import pickle
from functools import lru_cache
from typing import Dict, Tuple

import networkx as nx
import numpy as np
import tqdm
from networkx.readwrite import json_graph

from utils.config import RESOURCE_PATH, SIM_GRAPH

TOP_K_NEIGHBOURS = 10


def _load_resource_embeddings() -> Tuple[Dict[int, np.ndarray], Dict[int, Dict[str, object]]]:
    """Load embeddings and metadata from the exported snapshot."""
    if not RESOURCE_PATH.exists():
        raise RuntimeError(
            "Resource snapshot missing. Run the application once to generate resources and embeddings before building the graph."
        )

    with RESOURCE_PATH.open("rb") as fh:
        repository: Dict[str, Dict[str, object]] = pickle.load(fh)

    snapshot = repository.get("embeddings", {})

    embeddings: Dict[int, np.ndarray] = {}
    metadata: Dict[int, Dict[str, object]] = {}

    for resource_id_str, payload in snapshot.items():
        embedding = payload.get("embedding")
        if not embedding:
            continue
        vector = np.asarray(embedding, dtype=np.float32)
        norm = np.linalg.norm(vector)
        if not np.isfinite(norm) or norm == 0.0:
            continue
        vector /= norm

        resource_id = int(resource_id_str)
        embeddings[resource_id] = vector
        metadata[resource_id] = {
            "title": payload.get("title", "Untitled"),
            "type": payload.get("type", "Unknown"),
            "year": payload.get("year"),
        }

    return embeddings, metadata


def load_or_create_similarity_graph() -> nx.Graph:
    """Create a similarity graph using cached embeddings."""
    embeddings, metadata = _load_resource_embeddings()
    if not embeddings:
        raise RuntimeError(
            "No embeddings available. Run the application once to cache resource embeddings before building the graph."  # noqa: EM102
        )

    ordered_ids = list(embeddings.keys())
    matrix = np.stack([embeddings[rid] for rid in ordered_ids])
    similarity_matrix = matrix @ matrix.T
    np.fill_diagonal(similarity_matrix, -np.inf)

    graph = nx.Graph()
    for node_id in ordered_ids:
        graph.add_node(node_id, **metadata[node_id])

    for row_index, node_id in enumerate(tqdm.tqdm(ordered_ids, desc="Building similarity graph")):
        similarities = similarity_matrix[row_index]
        if np.all(~np.isfinite(similarities)):
            continue

        top_indices = np.argpartition(similarities, -TOP_K_NEIGHBOURS)[-TOP_K_NEIGHBOURS:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        for col_index in top_indices:
            neighbour_id = ordered_ids[col_index]
            weight = float(similarities[col_index])
            if not np.isfinite(weight) or neighbour_id == node_id:
                continue
            graph.add_edge(node_id, neighbour_id, similarity=weight)

    return graph


def save_similarity_graph(graph: nx.Graph, path=SIM_GRAPH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json_graph.node_link_data(graph)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def load_similarity_graph(path=SIM_GRAPH) -> nx.Graph:
    if not path.exists():
        raise FileNotFoundError(f"Similarity graph file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return json_graph.node_link_graph(data)


@lru_cache(maxsize=1)
def get_similarity_graph() -> nx.Graph:
    try:
        return load_similarity_graph()
    except FileNotFoundError:
        graph = load_or_create_similarity_graph()
        save_similarity_graph(graph)
        return graph


if __name__ == "__main__":
    graph = get_similarity_graph()
    save_similarity_graph(graph)
    print(
        f"Similarity graph built with {graph.number_of_nodes()} nodes and "
        f"{graph.number_of_edges()} edges. Saved to {SIM_GRAPH}."
    )
