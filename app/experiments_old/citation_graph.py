import time
import matplotlib.pyplot as plt
import networkx as nx
from pandas import read_csv
from pyalex import Works

from utils.config import PUBLICATIONS_PATH


BATCH_SIZE = 50
REQUEST_DELAY = 0.5
MAX_RETRY = 3
BACKOFF_FACTOR = 2.0
SPRING_LAYOUT_K = 0.35


def fetch_root_work(title):
    if not isinstance(title, str) or not title.strip():
        print("The first publication title is missing or invalid.")
        return None
    try:
        search_results = Works().search_filter(title=title).get()
    except Exception as exc:
        print(f"Failed to fetch OpenAlex record for '{title}': {exc}")
        return None
    if not search_results:
        print(f"No OpenAlex record found for '{title}'.")
        return None
    return search_results[0]


def _chunked(iterable, size):
    for idx in range(0, len(iterable), size):
        yield iterable[idx : idx + size]


def fetch_reference_details(reference_ids):
    cleaned_ids = [rid for rid in reference_ids if isinstance(rid, str) and rid]
    details = {}
    if not cleaned_ids:
        return details

    for chunk in _chunked(cleaned_ids, BATCH_SIZE):
        attempt = 0
        delay = REQUEST_DELAY
        works = []
        while attempt < MAX_RETRY:
            try:
                works = Works()[chunk]
                break
            except Exception as exc:
                attempt += 1
                if attempt >= MAX_RETRY:
                    print(f"Skipping chunk of {len(chunk)} references: {exc}")
                    works = []
                    break
                print(f"Retrying chunk fetch due to error: {exc}")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR
        for work in works:
            openalex_id = work.get("id")
            if not openalex_id:
                continue
            label = work.get("display_name") or work.get("title") or openalex_id
            references = set(work.get("referenced_works") or [])
            details[openalex_id] = {
                "label": label,
                "references": references,
            }
        time.sleep(REQUEST_DELAY)
    return details


def build_graph(root_work, reference_details):
    graph = nx.DiGraph()

    root_id = root_work.get("id")
    root_label = root_work.get("display_name") or root_work.get("title") or "Root Publication"
    graph.add_node(root_id, label=root_label)

    referenced_nodes = set(reference_details.keys())
    for ref_id, info in reference_details.items():
        graph.add_node(ref_id, label=info["label"])
        graph.add_edge(root_id, ref_id)

    for ref_id, info in reference_details.items():
        for target in info["references"]:
            if target in referenced_nodes:
                graph.add_edge(ref_id, target)

    return graph


def draw_graph(graph):
    if graph.number_of_nodes() == 0:
        print("Nothing to visualize; the graph is empty.")
        return

    pagerank_scores = {}
    if graph.number_of_edges() > 0:
        pagerank_scores = nx.pagerank(graph, alpha=0.85)

    node_index = {node: idx for idx, node in enumerate(graph.nodes(), start=1)}
    print("Node legend:")
    for node, idx in node_index.items():
        print(f"[{idx}] {graph.nodes[node].get('label')}")

    plt.figure(figsize=(12, 9), dpi=100)
    pos = nx.spring_layout(graph, seed=42, k=SPRING_LAYOUT_K)

    node_sizes = []
    for node in graph.nodes():
        base_size = 300
        score = pagerank_scores.get(node, 0)
        node_sizes.append(base_size + score * 4000)

    node_colors = []
    for node in graph.nodes():
        if graph.in_degree(node) == 0:
            node_colors.append("#FC7303")
        elif graph.out_degree(node) == 0:
            node_colors.append("#009688")
        else:
            node_colors.append("#0066FF")

    display_labels = {node: f"[{node_index[node]}]" for node in graph.nodes()}

    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(graph, pos, arrowstyle="-|>", arrowsize=12, edge_color="#444444")
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=display_labels,
        font_size=8,
        verticalalignment="center",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
    )

    plt.title("Citation Neighborhood of Root Publication", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def main():
    publications = read_csv(PUBLICATIONS_PATH)
    if publications.empty:
        print("The publications file is empty.")
        return

    first_title = publications.iloc[0].get("Title")
    root_work = fetch_root_work(first_title)
    if root_work is None:
        return

    referenced_ids = root_work.get("referenced_works") or []
    if not referenced_ids:
        print("The root publication does not reference any works.")
        return

    reference_details = fetch_reference_details(referenced_ids)
    graph = build_graph(root_work, reference_details)

    print(
        "Graph includes 1 root publication,"
        f" {len(reference_details)} referenced works, and {graph.number_of_edges()} edges."
    )
    draw_graph(graph)


if __name__ == "__main__":
    main()
