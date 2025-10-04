"""Navigation helpers for the Streamlit application."""
from __future__ import annotations

import streamlit as st

_NAV_ITEMS = (
    {"path": "app.py", "label": "Homepage", "icon": "🏠"},
    {"path": "pages/2_Publications.py", "label": "Publications", "icon": "📚"},
)


def render_sidebar(active_path: str) -> None:
    """Render consistent sidebar navigation across pages."""
    st.sidebar.title("Navigation")
    for item in _NAV_ITEMS:
        st.sidebar.page_link(
            item["path"],
            label=item["label"],
            icon=item["icon"],
            disabled=item["path"] == active_path,
        )
