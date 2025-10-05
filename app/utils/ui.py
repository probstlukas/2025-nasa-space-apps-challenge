from pathlib import Path
import streamlit as st


LOGO_PATH = Path(__file__).resolve().parent.parent / "images" / "logo.png"


def render_app_sidebar() -> None:
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width='stretch')
    st.sidebar.markdown("### Space Biology Knowledge Engine")
    st.sidebar.caption(
        "Navigate the NASA bioscience corpus, explore citation graphs, and query the knowledge base."
    )


__all__ = ["render_app_sidebar"]
