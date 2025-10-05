import streamlit as st

from utils.resource_manager import search_resources


def _format_authors(resource) -> str:
    authors = getattr(resource, "authors", None)
    if not authors:
        return "Unknown"
    if isinstance(authors, str):
        return authors
    return ", ".join(authors)


def setup_search_page(on_resource_clicked):
    query = st.text_input("Search for papers:")

    if not query:
        st.info("Start typing to search across publications and experiments.")
        return

    results = search_resources(query)

    if not results:
        st.info("No results found.")
        return

    for resource_id, resource, score in results:
        st.markdown(
            f"""
            **{resource.icon} {resource.title or 'Untitled'}**

            *Type:* {resource.type}  
            *Authors:* {_format_authors(resource)}  
            *Year:* {resource.year or '-'}  
            *Relevance score:* {score:.3f}
            """
        )
        st.button(
            "Select",
            key=f"select-{resource_id}",
            on_click=lambda rid=resource_id: on_resource_clicked(rid),
        )
        st.divider()
