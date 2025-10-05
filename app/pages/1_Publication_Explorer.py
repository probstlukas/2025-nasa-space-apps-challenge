import streamlit as st
from pandas import DataFrame, read_csv
from pyalex import config as pyalex_config, invert_abstract

from utils.config import PUBLICATIONS_PATH
from utils.openalex_utils import (
    fetch_referenced_works,
    fetch_work_by_title,
    resolve_best_link,
    summarise_reference,
)
from utils.ui import render_app_sidebar


st.set_page_config(page_title="Publication Explorer", page_icon="📊", layout="wide")
pyalex_config.email = "lukas.probst@student.kit.edu"

render_app_sidebar()


@st.cache_data(show_spinner=False)
def load_publications() -> DataFrame:
    df = read_csv(PUBLICATIONS_PATH)
    return df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])


st.title("Publication Explorer")
st.caption("Browse the NASA bioscience corpus and inspect individual citation contexts.")

publications = load_publications()
if publications.empty:
    st.error("No publications found in the CSV. Please check the data folder.")
    st.stop()

with st.sidebar:
    st.subheader("Choose a paper")
    selected_title = st.selectbox(
        "Select publication",
        publications["Title"].tolist(),
        index=0,
    )

if not selected_title:
    st.info("Select a paper to see its details, abstract, and references.")
    st.stop()

with st.spinner("Fetching publication details from OpenAlex..."):
    work_data = fetch_work_by_title(selected_title)

if work_data is None:
    st.warning("No OpenAlex record found for the selected publication.")
    st.stop()

authors = [
    entry.get("author", {}).get("display_name")
    for entry in work_data.get("authorships", [])
    if isinstance(entry, dict)
]
publication_year = work_data.get("publication_year")

st.subheader(selected_title)
meta_line = ""
if publication_year:
    meta_line += str(publication_year)
if authors:
    meta_line += (" • " if meta_line else "") + ", ".join(authors)
if meta_line:
    st.write(meta_line)
link_info = resolve_best_link(work_data)
primary_link = link_info.get("url")
if primary_link:
    label = link_info.get("label") or "Source"
    st.markdown(f"[View on {label}]({primary_link})")

abstract = work_data.get("abstract")
if not abstract:
    abstract = invert_abstract(work_data.get("abstract_inverted_index"))

with st.container(border=True):
    st.markdown("#### Abstract")
    if abstract:
        st.write(abstract)
    else:
        st.info("No abstract available for this work.")

referenced_ids = work_data.get("referenced_works") or []
st.markdown("#### Referenced Works")
if not referenced_ids:
    st.info("This publication does not list any referenced works in OpenAlex.")
else:
    with st.spinner("Fetching referenced work summaries..."):
        referenced_works = fetch_referenced_works(tuple(referenced_ids))

    if not referenced_works:
        st.warning("Referenced works could not be retrieved.")
    else:
        summaries = [summarise_reference(work) for work in referenced_works]
        st.session_state["knowledge_graph_seed"] = {
            "root": summarise_reference(work_data),
            "references": summaries,
        }
        for idx, reference in enumerate(
            sorted(summaries, key=lambda item: item.get("publication_year") or 0, reverse=True),
            start=1,
        ):
            title = reference.get("title") or reference.get("id") or "Untitled"
            link = reference.get("link") or reference.get("id")
            year = reference.get("publication_year")
            descriptor = f"{title}"
            if year:
                descriptor += f" ({year})"
            if link:
                label = reference.get("link_label")
                suffix = f" _(via {label})_" if label else ""
                st.markdown(f"{idx}. [{descriptor}]({link}){suffix}")
            else:
                st.markdown(f"{idx}. {descriptor}")

st.divider()
st.write(
    "Tip: OpenAlex responses are cached locally on disk. Start the citation graph page "
    "to visualise the latest selection or feed it to the chatbot."
)
