import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

import utils.resource_manager as R


def setup_paper_view(resource_id: int, resource: R.PaperResource):
    st.header(f"📘 {resource.title}")
    tabs = st.tabs(["Overview", "Citation Graph", "Experiments", "Referenced Work"])

    with tabs[0]:
        authors = resource.authors
        year = resource.year
        infos = [str(year)]
        if authors is not None:
            infos.append(", ".join(authors))

        st.write(" • ".join(infos))

        url = resource.url
        if url:
            url_label, primary_link = url
            st.markdown(f"[View on {url_label}]({primary_link})")

        abstract = resource.abstract
        with st.container(border=True):
            st.markdown("#### Abstract")
            if abstract:
                st.write(abstract)
            else:
                st.info("No abstract available for this work.")

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

    with tabs[3]:
        referenced_work = resource.referenced_work
        if referenced_work is not None:
            for ref in resource.referenced_work:
                st.markdown(ref)
