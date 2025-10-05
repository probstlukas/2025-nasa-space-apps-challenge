import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

from utils.ui import render_app_sidebar


st.set_page_config(page_title="Citation Graph", page_icon="🕸️", layout="wide")

render_app_sidebar()


seed_data = st.session_state.get("knowledge_graph_seed")

st.title("Citation Graph")
st.caption("Visualise the citation neighbourhood for the publication selected on the Publications page.")

if not seed_data:
    st.info(
        "Pick a publication on the Publications page first. The graph will appear "
        "here once the reference metadata has been loaded."
    )
    st.stop()

root = seed_data.get("root") or {}
references = seed_data.get("references") or []

if not root.get("id"):
    st.warning("The selected work does not provide a resolvable OpenAlex identifier.")
    st.stop()


def build_graph(root_node, reference_nodes):
    graph = nx.DiGraph()
    root_id = root_node.get("id")
    graph.add_node(root_id, title=root_node.get("title") or "Selected Publication")

    mapped = {}
    for reference in reference_nodes:
        ref_id = reference.get("id")
        if not ref_id:
            continue
        mapped[ref_id] = reference
        graph.add_node(ref_id, title=reference.get("title") or "Untitled")
        graph.add_edge(root_id, ref_id)

    for ref_id, reference in mapped.items():
        for target in reference.get("referenced_works", []) or []:
            if target in mapped:
                graph.add_edge(ref_id, target)

    return graph


def render_graph(graph):
    pagerank_scores = {}
    if graph.number_of_edges() > 0:
        pagerank_scores = nx.pagerank(graph, alpha=0.85)

    node_index = {node: idx for idx, node in enumerate(graph.nodes(), start=1)}
    st.write("Node legend:")
    for node, idx in node_index.items():
        title = graph.nodes[node].get("title") or node
        st.markdown(f"[{idx}] {title}")

    pos = nx.spring_layout(graph, seed=42, k=0.35)
    node_sizes = [300 + pagerank_scores.get(node, 0) * 4000 for node in graph.nodes()]

    node_colors = []
    for node in graph.nodes():
        if graph.in_degree(node) == 0:
            node_colors.append("#FC7303")
        elif graph.out_degree(node) == 0:
            node_colors.append("#009688")
        else:
            node_colors.append("#0066FF")

    display_labels = {node: f"[{node_index[node]}]" for node in graph.nodes()}

    fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
    ax.axis("off")
    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(graph, pos, arrowstyle="-|>", arrowsize=12, edge_color="#444444", ax=ax)
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=display_labels,
        font_size=8,
        verticalalignment="center",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
        ax=ax,
    )
    st.pyplot(fig, transparent=True)


citation_graph = build_graph(root, references)

if citation_graph.number_of_nodes() <= 1:
    st.warning("No referenced works share identifiers with the selected paper yet.")
    st.stop()

render_graph(citation_graph)

st.write(
    "Use the Publications page to select another paper and refresh this view, "
    "or extend the neighbourhood by loading more referenced works."
)
