import os
from typing import Dict, List, Sequence

import numpy as np
import streamlit as st
from pandas import DataFrame, read_csv
from pyalex import config as pyalex_config

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled at runtime
    SentenceTransformer = None

from utils.config import PUBLICATIONS_PATH
from utils.embedding_store import (
    get_embeddings_for_texts,
    load_embedding_store,
    save_embedding_store,
)
from utils.openalex_utils import (
    compose_work_text,
    fetch_work_by_title,
    get_abstract_text,
    get_cache,
    iterate_cached_works,
    resolve_best_link,
    summarise_reference,
)
from utils.ui import render_app_sidebar


st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")
pyalex_config.email = "lukas.probst@student.kit.edu"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

render_app_sidebar()


@st.cache_data(show_spinner=False)
def load_publications() -> DataFrame:
    print(PUBLICATIONS_PATH)
    
    df = read_csv(PUBLICATIONS_PATH)
    return df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])


def ensure_metadata_availability(titles: Sequence[str]) -> None:
    cache = get_cache()
    missing = [title for title in titles if title not in cache["works_by_title"]]
    if not missing:
        st.sidebar.success("All publications already have cached OpenAlex metadata.")
        return

    progress = st.sidebar.progress(0.0)
    status = st.sidebar.empty()
    for idx, title in enumerate(missing, start=1):
        status.write(f"Fetching metadata: {title}")
        fetch_work_by_title(title, show_status=False)
        progress.progress(idx / len(missing))
    status.empty()
    progress.empty()
    st.sidebar.success(f"Fetched {len(missing)} additional OpenAlex records.")


def build_corpus(titles: Sequence[str]) -> List[Dict[str, str]]:
    works = iterate_cached_works(titles)
    corpus: List[Dict[str, str]] = []
    for work in works:
        text_blob = compose_work_text(work)
        if not text_blob.strip():
            continue
        link_info = resolve_best_link(work)
        metadata = summarise_reference(work)
        identifier = metadata.get("id") or metadata.get("title")
        corpus.append(
            {
                "id": identifier or work.get("id") or work.get("display_name") or "",
                "title": work.get("display_name") or work.get("title") or "Untitled",
                "year": work.get("publication_year"),
                "text": text_blob,
                "abstract": get_abstract_text(work),
                "link": link_info.get("url"),
                "link_label": link_info.get("label"),
                "metadata": metadata,
            }
        )
    return corpus


@st.cache_resource(show_spinner=False)
def load_embedder(model_name: str) -> SentenceTransformer:
    if SentenceTransformer is None:
        raise ModuleNotFoundError(
            "sentence-transformers is required. Install it with `pip install sentence-transformers`."
        )
    return SentenceTransformer(model_name)


@st.cache_resource(show_spinner=False)
def load_embedding_cache(model_name: str) -> Dict[str, np.ndarray]:
    return load_embedding_store(model_name)


st.title("Semantic Paper Finder")
st.caption(
    "Compare your query against rich OpenAlex metadata (title, abstract, topics) "
    "to surface the most relevant publications in the NASA bioscience corpus."
)

publications = load_publications()
all_titles = publications["Title"].tolist()
cache = get_cache()
coverage = len(cache["works_by_title"]) / len(all_titles) if all_titles else 0
st.info(
    f"OpenAlex metadata cached for {len(cache['works_by_title'])} of {len(all_titles)} papers "
    f"({coverage:.0%} coverage)."
)

with st.sidebar.expander("Fetch or refresh metadata", expanded=False):
    st.write(
        "The search uses cached OpenAlex records gathered from the Publication Explorer. "
        "Refresh to ensure all papers are available before building the index."
    )
    if st.button("Fetch missing records", width='stretch'):
        ensure_metadata_availability(all_titles)

if SentenceTransformer is None:
    st.error(
        "The semantic search requires the `sentence-transformers` package. "
        "Install it in your environment and reload the page."
    )
    st.stop()

corpus = build_corpus(all_titles)
if not corpus:
    st.warning(
        "No cached OpenAlex records found yet. Fetch metadata first via the "
        "Publication Explorer or the refresh button above."
    )
    st.stop()

model = load_embedder(MODEL_NAME)
store = load_embedding_cache(MODEL_NAME)

identifiers = [entry["id"] or entry["title"] for entry in corpus]
texts = [entry["text"] for entry in corpus]

embeddings, store = get_embeddings_for_texts(
    MODEL_NAME,
    identifiers,
    texts,
    lambda batch: model.encode(batch, normalize_embeddings=True, show_progress_bar=False),
    store=store,
)
save_embedding_store(MODEL_NAME, store)

st.sidebar.header("Search Options")
results_count = st.sidebar.slider("Number of results", min_value=3, max_value=20, value=6)
score_threshold = st.sidebar.slider(
    "Minimum similarity", min_value=0.0, max_value=1.0, value=0.25, step=0.05
)

query = st.text_input("Describe the papers you are looking for", "microgravity stem cell differentiation")
if not query.strip():
    st.stop()

query_embedding = model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]

scores = embeddings @ query_embedding
ranked_indices = np.argsort(scores)[::-1]

st.markdown("### Top Matches")
num_displayed = 0
results_payload: List[Dict[str, str]] = []

for idx in ranked_indices:
    score = float(scores[idx])
    if score < score_threshold:
        continue
    entry = corpus[idx]
    year = entry.get("year")
    header = entry["title"]
    if year:
        header += f" ({year})"
    link = entry.get("link")
    label = entry.get("link_label")
    badge = f" via {label}" if label else ""

    st.markdown(f"#### {header}")
    st.write(f"Similarity score: {score:.2f}{badge}")
    if link:
        st.markdown(f"[Open {label or 'link'}]({link})")

    abstract = entry.get("abstract")
    if abstract:
        snippet = abstract[:600] + ("…" if len(abstract) > 600 else "")
        st.write(snippet)

    details = entry["metadata"]
    if details.get("referenced_works"):
        st.caption(
            f"References tracked: {len(details['referenced_works'])}. "
            "Open the citation graph page after selecting this publication in the explorer "
            "to visualise its neighbourhood."
        )
    st.divider()
    num_displayed += 1

    results_payload.append(
        {
            "id": entry["id"],
            "title": entry["title"],
            "year": year,
            "similarity": score,
            "link": link,
            "link_label": label,
            "abstract": entry.get("abstract"),
            "text": entry.get("text"),
        }
    )

    if num_displayed >= results_count:
        break

if num_displayed == 0:
    st.warning(
        "No papers met the similarity threshold. Lower the minimum similarity or fetch more metadata."
    )
else:
    st.success("Results grounded in OpenAlex metadata. Continue refining or inspect a match in detail above.")
    st.session_state["chat_context"] = {
        "query": query,
        "model_name": MODEL_NAME,
        "results": results_payload,
    }

    if st.button("Summarise top results with LLM", width='stretch'):
        try:
            from openai import OpenAI
        except ImportError:  # pragma: no cover - optional dependency
            st.error("Install the `openai` package to enable LLM summarisation.")
        else:
            api_key = st.secrets.get("openai_api_key")
            if not api_key:
                st.warning("`openai_api_key` not found in Streamlit secrets. Summarisation disabled.")
            else:
                client = OpenAI(api_key=api_key)
                context_blocks = []
                for result in results_payload[:results_count]:
                    context_blocks.append(
                        f"Title: {result['title']}\n"
                        f"Year: {result.get('year', 'n/a')}\n"
                        f"Similarity: {result['similarity']:.2f}\n"
                        f"Abstract: {result.get('abstract', 'No abstract available.')}"
                    )
                prompt = (
                    "You are assisting with the NASA Space Apps bioscience challenge. "
                    "Summarise the following candidate papers and explain why they are relevant "
                    "to the user query. Provide 3 concise bullet points."
                )
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": prompt},
                            {
                                "role": "user",
                                "content": (
                                    f"User query: {query}\n\n" + "\n\n".join(context_blocks)
                                ),
                            },
                        ],
                    )
                    summary = completion.choices[0].message.content
                    st.markdown("### Why this matters")
                    st.write(summary)
                    st.session_state["chat_context"]["summary"] = summary
                except Exception as exc:  # pragma: no cover - runtime errors only
                    st.error(f"LLM summarisation failed: {exc}")

st.caption(
    "Next step: head to the Chatbot page to interrogate these results or refine your search here."
)
