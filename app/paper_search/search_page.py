from functools import partial
import streamlit as st
import pandas as pd


# TODO: Instead implement this utility in the backend and import it here
def search_papers(query):
    """Mock search results."""
    data = [
        {
            "id": 1,
            "title": "Deep Learning for NLP",
            "authors": "Smith et al.",
            "year": 2021,
        },
        {
            "id": 2,
            "title": "Graph Neural Networks",
            "authors": "Johnson et al.",
            "year": 2020,
        },
        {
            "id": 3,
            "title": "Transformers in Vision",
            "authors": "Lee et al.",
            "year": 2022,
        },
    ]
    df = pd.DataFrame(data)
    return df[df["title"].str.contains(query, case=False, na=False)]


def setup_search_page(on_resource_clicked):
    query = st.text_input("Search for papers:")
    if query:
        results = search_papers(query)
        if not results.empty:
            for _, row in results.iterrows():
                st.button(
                    f"📄 {row['title']} ({row['year']}) - {row['authors']}",
                    on_click=lambda row=row: on_resource_clicked(row["id"]),
                )
        else:
            st.info("No results found.")
