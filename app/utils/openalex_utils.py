import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import streamlit as st
from pyalex import Works, invert_abstract

from utils.config import PUBLICATIONS_PATH


CACHE_FILE = PUBLICATIONS_PATH.resolve().parent / "openalex_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
BATCH_SIZE = 50
FETCH_DELAY_SECONDS = 0.25


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


def get_cache() -> Dict[str, Dict[str, Any]]:
    cache = st.session_state.get("openalex_cache_store")
    if cache is None:
        cache = _load_cache_from_disk()
        st.session_state["openalex_cache_store"] = cache
    return cache


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
    sanitized = re.sub(r"[^\w\s]", " ", original)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    add_variant(sanitized)
    return variants


def fetch_work_by_title(
    title: str, *, show_status: bool = True
) -> Optional[Dict[str, Any]]:
    cache = get_cache()
    cached = cache["works_by_title"].get(title)
    if cached:
        return cached

    exception_messages: List[str] = []
    selected_variant: Optional[str] = None
    results = None

    for variant in _title_variants(title):
        query = f'"{variant}"'
        try:
            candidate = Works().search(query).get()
        except Exception as exc:  # noqa: BLE001
            exception_messages.append(str(exc))
            continue
        if candidate:
            results = candidate
            selected_variant = variant
            break
        time.sleep(FETCH_DELAY_SECONDS)

    if results:
        work = _normalize_work(results[0])
        cache["works_by_title"][title] = work
        work_id = work.get("id")
        if isinstance(work_id, str):
            cache["works_by_id"][work_id] = work
        _persist_cache_to_disk(cache)
        return work

    if show_status and exception_messages:
        unique_messages = list(dict.fromkeys(exception_messages))
        message = "; ".join(unique_messages)
        if st is not None:
            st.warning(
                "OpenAlex lookup could not resolve this title automatically. "
                "Falling back to search without metadata.\n"
                f"Details: {message}"
            )
        else:
            print(f"OpenAlex lookup failed for '{title}': {message}")
    return None


def fetch_referenced_works(reference_ids: Sequence[str]) -> List[Dict[str, Any]]:
    cache = get_cache()
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
        time.sleep(FETCH_DELAY_SECONDS)
    if missing_ids:
        _persist_cache_to_disk(cache)

    ordered = []
    for rid in cleaned_ids:
        cached = cache["works_by_id"].get(rid)
        if cached:
            ordered.append(cached)
    return ordered


def _normalize_pmc_url(url: Any) -> str:
    if not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    if not cleaned.startswith("http"):
        token = cleaned.replace("PMC", "").replace("pmc", "").strip("/")
        if token:
            cleaned = token if token.upper().startswith("PMC") else f"PMC{token}"
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


def compose_work_text(work: Dict[str, Any]) -> str:
    parts: List[str] = []
    title = work.get("display_name") or work.get("title")
    if title:
        parts.append(title)
    abstract = get_abstract_text(work)
    if abstract:
        parts.append(abstract)

    def _collect_strings(items: Any, keys: Tuple[str, ...] = ("display_name",)) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in keys:
                    value = item.get(key)
                    if isinstance(value, str) and value:
                        parts.append(value)
                        break

    _collect_strings(work.get("topics"), ("display_name", "id"))
    _collect_strings(work.get("concepts"), ("display_name", "id"))
    _collect_strings(work.get("keywords"), ("display_name",))

    return ". ".join(segment for segment in parts if segment)


def iterate_cached_works(titles: Sequence[str]) -> List[Dict[str, Any]]:
    cache = get_cache()
    works: List[Dict[str, Any]] = []
    for title in titles:
        work = cache["works_by_title"].get(title)
        if work:
            works.append(work)
    return works


def get_abstract_text(work: Dict[str, Any]) -> str:
    abstract = work.get("abstract")
    if abstract:
        return str(abstract)
    inverted = work.get("abstract_inverted_index")
    if inverted:
        reconstructed = invert_abstract(inverted)
        if reconstructed:
            return str(reconstructed)
    return ""
