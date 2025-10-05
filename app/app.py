import streamlit as st

import networkx as nx
import matplotlib.pyplot as plt
from frontend.search_page import setup_search_page
from frontend.paper_view import setup_paper_view
from frontend.experiment_view import setup_experiment_view
from backend.resource_manager import get_resource


# ---- Mock Data & Functions ----
def on_resource_clicked(resource_id: int):
    print("on resource clicked", resource_id)

    st.session_state.selected_resource = resource_id


# ---- Streamlit Layout ----
st.set_page_config(page_title="BioScholar", layout="wide")
st.title("🔍 BioScholar")

# State to track selected paper
if "selected_resource" not in st.session_state:
    st.session_state.selected_resource = None


# ---- Main View Logic ----
if st.session_state.selected_resource is None:
    setup_search_page(on_resource_clicked)
else:
    # ---- Paper Details View ----
    resource_id = st.session_state.selected_resource
    resource = get_resource(resource_id)

    def on_click():
        st.session_state.update(selected_resource=None)
        print("paper clicked")

    st.button(
        "⬅️ Back to search",
        on_click=on_click,
    )

    st.header(f"📘 Paper ID: {resource.get('title', resource_id)}")
    resource_type = resource.get("type")

    if resource_type == "paper":
        print("resource")
        setup_paper_view(resource_id, resource)
    elif resource_type == "experiment":
        setup_experiment_view(resource_id, resource)
    else:
        raise ValueError(
            f"Unknown resource-type '{resource_type}' with id '{resource_id}'"
        )
