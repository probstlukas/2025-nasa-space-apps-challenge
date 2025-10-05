import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt


def setup_paper_view(resource_id: int, resource: dict):
    tabs = st.tabs(["Overview", "Citation Graph", "Experiments"])

    with tabs[0]:
        st.subheader("Abstract")
        # st.write(resource.get("abstract", "No abstract available."))

    with tabs[1]:
        st.subheader("Citation Graph")
        G = nx.DiGraph()
        # G.add_edges_from(resource.get("citations", []))
        fig, ax = plt.subplots()
        nx.draw(G, with_labels=True, ax=ax)
        st.pyplot(fig)

    with tabs[2]:
        st.subheader("Experiments")
        # st.write(", ".join(resource.get("experiments", [])))
