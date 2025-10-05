import streamlit as st

from utils.ui import render_app_sidebar

st.set_page_config(
    page_title="Space Biology Knowledge Engine",
    page_icon="🧬",
    layout="wide",
)

render_app_sidebar()

st.title("Space Biology Knowledge Engine")
st.write(
    """
    Welcome to the 2025 NASA Space Apps Challenge project. Use the pages in the sidebar to:

    - Inspect individual publications and their citation neighbourhoods.
    - Search the corpus semantically using OpenAlex metadata.
        - Ask grounded questions about the retrieved papers in the chatbot.

    Suggested workflow:

    1. Open *Publication Explorer* to cache metadata for the papers you're interested in.
    2. Jump to *Semantic Search* to discover related work with embedding similarity.
    3. Explore relationships in *Citation Graph* or ask questions in *Chatbot*.
"""
)

st.info(
    "Need inspiration? Start with the Publication Explorer, pick a paper, and follow the links to build your knowledge graph."
)
