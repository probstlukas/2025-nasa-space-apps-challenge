import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

import utils.resource_manager as R


def setup_paper_view(resource_id: int, resource: R.PaperResource):
    tabs = st.tabs(["Overview", "Citation Graph", "Experiments", "Referenced Work"])

    with tabs[0]:
        authors = resource.authors
        year = resource.year
        infos = [year]
        if authors is not None:
            infos.append(authors)

        st.write(" • ".join(infos))

        abstract = resource.abstract
        with st.container(border=True):
            st.markdown("#### Abstract")
            if abstract:
                st.write(abstract)
            else:
                st.info("No abstract available for this work.")

        # Add metadata below the abstract as rows
        with st.container():
            authors = resource.authors
            year = resource.year
            infos = [year]
            if authors is not None:
                infos.append(authors)

            st.write(" • ".join(infos))

            # URL / Link
            st.markdown("**Link**")
            url = resource.url
            if url:
                st.markdown(f"[Open resource]({url})", unsafe_allow_html=True)
            else:
                st.write("N/A")

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
