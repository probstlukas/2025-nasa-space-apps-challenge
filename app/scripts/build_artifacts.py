"""Command-line helper to build resource and similarity graph artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import RESOURCE_PATH, SIM_GRAPH  # noqa: E402
from utils.resource_manager import (  # noqa: E402
    RESOURCES,
    _load_resources,
    save_repository_snapshot,
)
from utils.similarity_graph import (  # noqa: E402
    load_or_create_similarity_graph,
    save_similarity_graph,
)


def build_resources(verbose: bool = True) -> None:
    if verbose:
        print("Loading resources and ensuring embeddings…")
    _load_resources()
    save_repository_snapshot(RESOURCE_PATH)
    if verbose:
        print(f"Resource snapshot stored at {RESOURCE_PATH} ({len(RESOURCES)} records).")


def build_similarity_graph(verbose: bool = True) -> None:
    if verbose:
        print("Building similarity graph from cached embeddings…")
    graph = load_or_create_similarity_graph()
    save_similarity_graph(graph, SIM_GRAPH)
    if verbose:
        print(
            f"Similarity graph saved to {SIM_GRAPH} "
            f"with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cached artifacts for BioScholar.")
    parser.add_argument(
        "--graph-only",
        action="store_true",
        help="Skip resource snapshot rebuild and only refresh the similarity graph.",
    )
    parser.add_argument(
        "--resources-only",
        action="store_true",
        help="Refresh the resource snapshot but skip similarity graph generation.",
    )
    args = parser.parse_args()

    if args.graph_only and args.resources_only:
        parser.error("Choose either --graph-only or --resources-only, not both.")

    if not args.graph_only:
        build_resources()

    if not args.resources_only:
        build_similarity_graph()


if __name__ == "__main__":
    main()
