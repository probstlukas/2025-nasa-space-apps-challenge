import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt


def setup_experiment_view(resource_id: int, resource: dict):
    tabs = st.tabs(["Overview", "Papers"])

    with tabs[0]:
        st.subheader("Description")
        st.write(resource.get("description", "No description available."))

    with tabs[1]:
        st.subheader("Datasets Used")
        st.write(", ".join(resource.get("experiments", [])))
