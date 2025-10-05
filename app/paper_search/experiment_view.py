import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

import utils.resource_manager as R


def setup_experiment_view(resource_id: int, resource: R.ExperimentResource):
    st.header(f"📘 {resource.title}")
    tabs = st.tabs(["Overview", "Publications"])

    with tabs[0]:
        authors = resource.authors
        year = resource.year
        infos = [str(year)]
        if authors is not None:
            infos.append(", ".join(authors))

        st.write(" • ".join(infos))

        paper_url = resource.paper_url
        pdf_url = resource.pdf_url
        if paper_url and pdf_url:
            url_label, primary_link = paper_url
            st.markdown(
                f"[View on {url_label}]({primary_link}) &emsp; [View PDF]({pdf_url})"
            )

        description = resource.description
        with st.container(border=True):
            st.markdown("#### Description")
            if description:
                st.write(description)
            else:
                st.info("No abstract available for this work.")

    with tabs[1]:
        st.subheader("Publications")
        publications = resource.publications
        print(publications)

        if len(publications) > 0:
            for pub in publications:
                st.markdown(
                    f"""
                    **{pub.icon} {pub.title}**

                    *Authors:* {', '.join(pub.authors)}  
                    *Year:* {pub.year}  
                    *Type:* {pub.type}
                    """
                )
                st.divider()
        else:
            st.write("No publications on this dataset available")
