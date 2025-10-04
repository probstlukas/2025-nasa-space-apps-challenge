import streamlit as st

from utils.navigation import render_sidebar

st.set_page_config(
    page_title="Hello World",
    page_icon="📈",
)

render_sidebar("app.py")

st.markdown("# Homepage")
st.write(
    """TODO"""
)
