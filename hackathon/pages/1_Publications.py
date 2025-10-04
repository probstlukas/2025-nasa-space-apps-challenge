import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import streamlit as st
from pandas import DataFrame, read_csv
from pyalex import Works, config as pyalex_config, invert_abstract

from utils.config import PUBLICATIONS_PATH


st.set_page_config(page_title="Publications", page_icon="📊")
pyalex_config.email = "lukas.probst@student.kit.edu"

BATCH_SIZE = 50
CACHE_FILE = PUBLICATIONS_PATH.resolve().parent / "openalex_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)



def _normalize_pmc_url(url: Any) -> str:
    if not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    if not cleaned.startswith("http"):
        token = cleaned.replace("PMC", "").replace("pmc", "").strip("/")
        if token:
            cleaned = f"PMC{token}" if not token.upper().startswith("PMC") else token
        else:
            cleaned = ""
        if cleaned:
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{cleaned}/"
        return ""
    if "articles/" in cleaned:
        base, suffix = cleaned.rsplit("articles/", 1)
        suffix = suffix.strip("/")
        if suffix and not suffix.upper().startswith("PMC"):
            suffix = "PMC" + suffix
        return f"{base}articles/{suffix}/"
    return cleaned


def resolve_best_link(work: Dict[str, Any]) -> Dict[str, Optional[str]]:
    ids = work.get("ids") or {}

    pmcid_url = _normalize_pmc_url(ids.get("pmcid"))
    if pmcid_url:
        return {"url": pmcid_url, "label": "PubMed Central"}

    doi = ids.get("doi") or work.get("doi")
    if isinstance(doi, str) and doi.strip():
        doi_clean = doi.strip()
        if not doi_clean.lower().startswith("http"):
            doi_clean = f"https://doi.org/{doi_clean}"
        return {"url": doi_clean, "label": "DOI"}

    best_location = work.get("best_oa_location") or work.get("primary_location") or {}
    if isinstance(best_location, dict):
        landing = best_location.get("landing_page_url") or best_location.get("pdf_url")
        if landing:
            return {"url": landing, "label": "Publisher"}

    openalex_url = ids.get("openalex") or work.get("id")
    if isinstance(openalex_url, str) and openalex_url.strip():
        return {"url": openalex_url.strip(), "label": "OpenAlex"}

    return {"url": None, "label": None}


def _empty_cache() -> Dict[str, Dict[str, Any]]:
    return {"works_by_title": {}, "works_by_id": {}}


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, set):
        return [_serialize(v) for v in value]
    return value


def _load_cache_from_disk() -> Dict[str, Dict[str, Any]]:
    if not CACHE_FILE.exists():
        return _empty_cache()
    try:
        with CACHE_FILE.open("r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except (OSError, json.JSONDecodeError):
        return _empty_cache()
    if not isinstance(data, dict):
        return _empty_cache()
    for key in ("works_by_title", "works_by_id"):
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
    return data  # type: ignore[return-value]


def _persist_cache_to_disk(cache: Dict[str, Dict[str, Any]]) -> None:
    try:
        with CACHE_FILE.open("w", encoding="utf-8") as cache_file:
            json.dump(_serialize(cache), cache_file, ensure_ascii=False, indent=2)
    except OSError as exc:
        st.warning(f"Unable to persist OpenAlex cache: {exc}")


def _get_cache() -> Dict[str, Dict[str, Any]]:
    cache = st.session_state.get("openalex_cache_store")
    if cache is None:
        cache = _load_cache_from_disk()
        st.session_state["openalex_cache_store"] = cache
    return cache


@st.cache_data(show_spinner=False)
def load_publications() -> DataFrame:
    df = read_csv(PUBLICATIONS_PATH)
    return df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])


def _chunked(items: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _normalize_work(raw_work: Dict[str, Any]) -> Dict[str, Any]:
    return _serialize(dict(raw_work))




def _title_variants(original: str) -> List[str]:
    variants: List[str] = []

    def add_variant(value: str) -> None:
        cleaned = value.strip()
        if cleaned and cleaned not in variants:
            variants.append(cleaned)

    add_variant(original)
    sanitized = re.sub(r'[^\w\s]', ' ', original)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    add_variant(sanitized)
    return variants


def fetch_work_by_title(title: str) -> Optional[Dict[str, Any]]:
    cache = _get_cache()
    cached = cache["works_by_title"].get(title)
    if cached:
        return cached

    exception_messages: List[str] = []
    selected_variant: Optional[str] = None
    results = None

    for variant in _title_variants(title):
        try:
            candidate = Works().search_filter(title=variant).get()
        except Exception as exc:  # noqa: BLE001
            exception_messages.append(str(exc))
            continue
        if candidate:
            results = candidate
            selected_variant = variant
            break

    if results is None:
        try:
            results = Works().search(f'"{title}"').get()
        except Exception as exc:  # noqa: BLE001
            exception_messages.append(str(exc))

    if results:
        if selected_variant and selected_variant != title:
            st.info("Resolved the title via a sanitised query to handle special characters.")
        work = _normalize_work(results[0])
        cache["works_by_title"][title] = work
        work_id = work.get("id")
        if isinstance(work_id, str):
            cache["works_by_id"][work_id] = work
        _persist_cache_to_disk(cache)
        return work

    if exception_messages:
        unique_messages = list(dict.fromkeys(exception_messages))
        st.error(
            "OpenAlex request failed for this title due to: "
            + "; ".join(unique_messages)
        )
    return None


def fetch_referenced_works(reference_ids: Sequence[str]) -> List[Dict[str, Any]]:
    cache = _get_cache()
    cleaned_ids = [rid for rid in reference_ids if isinstance(rid, str) and rid]
    if not cleaned_ids:
        return []

    missing_ids = [rid for rid in cleaned_ids if rid not in cache["works_by_id"]]
    for chunk in _chunked(missing_ids, BATCH_SIZE):
        try:
            works = Works()[list(chunk)]
        except Exception as exc:  # noqa: BLE001
            st.warning(
                f"Skipping {len(chunk)} referenced works due to an API error: {exc}"
            )
            continue
        for work in works:
            normalized = _normalize_work(work)
            work_id = normalized.get("id")
            if isinstance(work_id, str):
                cache["works_by_id"][work_id] = normalized
    if missing_ids:
        _persist_cache_to_disk(cache)

    ordered = []
    for rid in cleaned_ids:
        cached = cache["works_by_id"].get(rid)
        if cached:
            ordered.append(cached)
    return ordered


def summarise_reference(work: Dict[str, Any]) -> Dict[str, Any]:
    link_info = resolve_best_link(work)
    return {
        "id": work.get("id"),
        "title": work.get("display_name") or work.get("title"),
        "publication_year": work.get("publication_year"),
        "referenced_works": work.get("referenced_works") or [],
        "link": link_info.get("url"),
        "link_label": link_info.get("label"),
    }


st.title("Publication Explorer")
st.caption("Browse the NASA bioscience corpus and inspect individual citation contexts.")

publications = load_publications()
if publications.empty:
    st.error("No publications found in the CSV. Please check the data folder.")
    st.stop()

selected_title = st.selectbox(
    "Select a publication",
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
primary_link = link_info.get('url')
if primary_link:
    label = link_info.get('label') or 'Source'
    st.markdown(f"[View on {label}]({primary_link})")
abstract = work_data.get("abstract")
if not abstract:
    abstract = invert_abstract(work_data.get("abstract_inverted_index"))

st.subheader("Abstract")
if abstract:
    st.write(abstract)
else:
    st.info("No abstract available for this work.")

referenced_ids = work_data.get("referenced_works") or []
st.subheader("Referenced Works")
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
    "Tip: OpenAlex responses are cached locally on disk. Start the citation "
    "graph page to visualise the latest selection or feed it to the chatbot."
)
