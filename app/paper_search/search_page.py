import streamlit as st

from utils.resource_manager import (
    sample_resources,
    search_resources,
)


def _format_authors(resource) -> str:
    authors = getattr(resource, "authors", None)
    if not authors:
        return "Unknown"
    if isinstance(authors, str):
        return authors
    return ", ".join(authors)


def _render_resource_card(resource, *, score: float | None = None) -> str:
    lines = [
        f"**{resource.icon} {resource.title or 'Untitled'}**",
        "",
        f"*Type:* {resource.type}  ",
        f"*Authors:* {_format_authors(resource)}  ",
        f"*Year:* {resource.year or '-'}",
    ]
    if score is not None:
        lines.append(f"*Relevance score:* {score:.3f}")
    return "\n".join(lines)


def setup_search_page(on_resource_clicked):
    type_options = ("Publication", "Experiment")

    with st.container():
        cols = st.columns([2, 1])
        with cols[0]:
            query = st.text_input(
                "Search for papers:",
                key="paper_search_query",
            )
        with cols[1]:
            selected_types = st.multiselect(
                "Type filter",
                options=type_options,
                default=list(type_options),
                key="paper_search_types",
            )

    if not query:
        st.info("Start typing to search across publications and experiments.")
        suggestions = sample_resources(6, resource_types=selected_types)
        if suggestions:
            st.subheader("Explore suggested resources")
            for resource_id, resource in suggestions:
                st.markdown(_render_resource_card(resource))
                st.button(
                    "Select",
                    key=f"suggest-select-{resource_id}",
                    on_click=lambda rid=resource_id: on_resource_clicked(rid),
                )
                st.divider()
        return

    if not selected_types:
        st.info("Select at least one resource type to show results.")
        return

    results = search_resources(query, resource_types=selected_types)

    if not results:
        st.info("No results found.")
        return

    for resource_id, resource, score in results:
        st.markdown(_render_resource_card(resource, score=score))
        st.button(
            "Select",
            key=f"select-{resource_id}",
            on_click=lambda rid=resource_id: on_resource_clicked(rid),
        )
        st.divider()

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
