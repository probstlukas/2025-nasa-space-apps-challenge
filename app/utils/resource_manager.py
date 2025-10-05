import datetime
import os
import pickle
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
from pandas import read_csv

try:  # Streamlit is optional in non-app contexts
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - used when running outside Streamlit
    st = None

from openai import OpenAI

# from pyalex import config as pyalex_config, invert_abstract
from pyalex.api import invert_abstract

from utils.config import PUBLICATIONS_PATH, EXPERIMENTS_PATH, RESOURCE_PATH
from utils.openalex_utils import (
    fetch_work_by_title,
    fetch_referenced_works,
    summarise_reference,
    resolve_best_link,
)

EMBED_MODEL = "text-embedding-3-small"
EMBED_BATCH_SIZE = 64
EMBED_MAX_CHARS = 6000


class PaperResource:
    def __init__(self, title: str):
        self.title = title
        self.type = "Publication"
        self.icon = "📘"
        self._data = None
        self._experiments = []

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        if self._data is None:
            self._data = fetch_work_by_title(self.title)
        return self._data

    @property
    def year(self):
        if self.data is not None:
            return self._data.get("publication_year", "-")
        else:
            return "-"

    @property
    def authors(self):
        if self.data is None:
            return []
        authors = [
            entry.get("author", {}).get("display_name")
            for entry in self.data.get("authorships", [])
            if isinstance(entry, dict)
        ]
        return authors

    @property
    def abstract(self):
        if self.data is None:
            return None

        abstract = self.data.get("abstract")
        if not abstract:
            abstract = invert_abstract(self.data.get("abstract_inverted_index"))

        return abstract

    @property
    def referenced_work(self):
        if self.data is None:
            return None
        referenced_ids = self.data.get("referenced_works") or []

        if referenced_ids:
            referenced_works = fetch_referenced_works(tuple(referenced_ids))

            if referenced_works:
                reference_label_list = []
                summaries = [summarise_reference(work) for work in referenced_works]

                for idx, reference in enumerate(
                    sorted(
                        summaries,
                        key=lambda item: item.get("publication_year") or 0,
                        reverse=True,
                    ),
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
                        reference_label = f"{idx}. [{descriptor}]({link}){suffix}"
                    else:
                        reference_label = f"{idx}. {descriptor}"

                    reference_label_list.append(reference_label)
            return reference_label_list
        return None

    @property
    def paper_url(self) -> Optional[Tuple[str, str]]:
        if self.data is None:
            return None
        link_info = resolve_best_link(self.data)
        primary_link = link_info.get("url")
        if primary_link:
            label = link_info.get("label") or "Source"
            return label, primary_link
        return None

    @property
    def pdf_url(self):
        if self.data is None:
            return None
        best_location = (
            self.data.get("best_oa_location") or self.data.get("primary_location") or {}
        )
        if best_location is not None:
            return best_location.get("pdf_url", None)
        return None

    def get_property(self, key: str, default=None):
        if self.data is not None:
            return self.data.get(key, default)
        return default

    @property
    def experiments(self) -> List["ExperimentResource"]:
        return self._experiments


class ExperimentResource:
    def __init__(self, osd_key: str, metadata: Dict[str, Any]):
        self.osd_key = osd_key
        self.type = "Experiment"
        self.icon = "🔬"
        self._metadata = metadata

    @property
    def title(self):
        return self._metadata.get("study title", None)

    @property
    def description(self):
        return self._metadata.get("study description")

    @property
    def abstract(self):
        return self.description

    @property
    def authors(self):
        return self._metadata.get("study publication author list")

    @property
    def year(self):
        timestamp = self._metadata.get("study public release date", None)
        if timestamp is None:
            return timestamp
        else:
            year = datetime.datetime.utcfromtimestamp(timestamp).year
            return str(year)

    @property
    def publications(self) -> List[PaperResource]:
        titles = self._metadata.get("study publication title", None)
        if isinstance(titles, str):
            titles = [titles]

        publications = []
        if titles is None:
            return publications
        for title in titles:
            publication_id = PAPER_TITLE_INDEX.get(title, None)
            if publication_id is None:
                # print(f"Could not find publication with title '{title}'")
                continue

            publication = RESOURCES[publication_id]
            publications.append(publication)
        return publications

    def get_property(self, key: str):
        return self._metadata.get(key, None)

    @property
    def paper_url(self) -> Optional[Tuple[str, str]]:
        return None

    @property
    def pdf_url(self):
        return None


ResourceType = Union[PaperResource, ExperimentResource]


RESOURCES: Dict[int, ResourceType] = {}
PAPER_TITLE_INDEX: Dict[str, int] = {}


_next_id = 0


def gen_id():
    global _next_id
    id = _next_id
    _next_id += 1
    return id


def _load_publications():
    df = read_csv(PUBLICATIONS_PATH)
    data = df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])

    for _, row in data.iterrows():
        resource = PaperResource(title=row["Title"])
        id = gen_id()
        RESOURCES[id] = resource

        PAPER_TITLE_INDEX[resource.title] = id


def _load_experiments():
    with open(EXPERIMENTS_PATH, "rb") as f:
        experiment_data: Dict[str, dict] = pickle.load(f)

    for osd_key, experiment in experiment_data.items():
        metadata: dict = experiment["metadata"]
        id = gen_id()
        resource = ExperimentResource(osd_key, metadata)
        RESOURCES[id] = resource

        for pub in resource.publications:
            pub._experiments.append(resource)

    """
    dict_keys(['authoritative source url', 'flight program', 'mission', 'material type', 'project identifier', 'accession', 'identifiers', 'study identifier', 'study protocol name', 'study assay technology type', 'acknowledgments', 'study assay technology platform', 'study person', 'study protocol type', 'space program', 'study title', 'study factor type', 'study public release date', 'parameter value', 'thumbnail', 'study factor name', 'study assay measurement type', 'project type', 'factor value', 'data source accession', 'project title', 'study funding agency', 'study protocol description', 'experiment platform', 'characteristics', 'study grant number', 'study publication author list', 'project link', 'study publication title', 'managing nasa center', 'study description', 'organism', 'data source type'])
    """


def _get_openai_client() -> Optional[OpenAI]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and st is not None:
        api_key = (
            st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else None
        )
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _normalize_vector(values: List[float]) -> Optional[List[float]]:
    array = np.asarray(values, dtype=np.float32)
    norm = np.linalg.norm(array)
    if not np.isfinite(norm) or norm == 0.0:
        return None
    return (array / norm).astype(np.float32).tolist()


def _prepare_text_for_embedding(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    trimmed = str(text).strip()
    if not trimmed:
        return None
    if len(trimmed) > EMBED_MAX_CHARS:
        trimmed = trimmed[:EMBED_MAX_CHARS]
    return trimmed


def _embedding_text(resource: ResourceType) -> Optional[str]:
    if isinstance(resource, PaperResource):
        title = resource.title
        if isinstance(title, str):
            return title
        return None
    if isinstance(resource, ExperimentResource):
        description = resource.description
        if description:
            if isinstance(description, list):
                description = " ".join(str(part) for part in description if part)
            return str(description)
        title = resource.title
        if title:
            return str(title)
        return str(resource.osd_key)
    return None


def _ensure_embeddings() -> bool:
    client = _get_openai_client()
    updated = False

    for resource in RESOURCES.values():
        if not hasattr(resource, "embedding"):
            resource.embedding = None  # type: ignore[attr-defined]
            updated = True
        if not hasattr(resource, "embedding_model"):
            resource.embedding_model = None  # type: ignore[attr-defined]
            updated = True

    if client is None:
        if st is not None:
            st.warning(
                "OpenAI API key missing. Skipping embedding generation; search results will be basic."
            )
        return updated

    pending_texts: List[str] = []
    pending_items: List[ResourceType] = []

    def flush_batch() -> None:
        nonlocal pending_texts, pending_items, updated
        if not pending_texts:
            return
        try:
            response = client.embeddings.create(model=EMBED_MODEL, input=pending_texts)
        except Exception as exc:  # noqa: BLE001
            if st is not None:
                st.error(f"Failed to create embeddings: {exc}")
            else:
                print(f"Failed to create embeddings: {exc}")
            pending_texts = []
            pending_items = []
            return

        for datum, resource in zip(response.data, pending_items):
            normalized = _normalize_vector(datum.embedding)
            resource.embedding = normalized  # type: ignore[attr-defined]
            resource.embedding_model = EMBED_MODEL  # type: ignore[attr-defined]
            updated = True

        pending_texts = []
        pending_items = []

    for resource in RESOURCES.values():
        existing_model = getattr(resource, "embedding_model", None)
        existing_embedding = getattr(resource, "embedding", None)
        if existing_model == EMBED_MODEL and existing_embedding is not None:
            continue

        text = _prepare_text_for_embedding(_embedding_text(resource))
        if not text:
            resource.embedding = None  # type: ignore[attr-defined]
            resource.embedding_model = EMBED_MODEL  # type: ignore[attr-defined]
            updated = True
            continue

        pending_texts.append(text)
        pending_items.append(resource)
        if len(pending_texts) >= EMBED_BATCH_SIZE:
            flush_batch()

    flush_batch()

    return updated


def _search_fallback(
    query: str,
    limit: int,
    *,
    allowed_types: Optional[Iterable[str]] = None,
) -> List[Tuple[int, ResourceType, float]]:
    needle = query.lower().strip()
    hits: List[Tuple[int, ResourceType, float]] = []
    seen: set[int] = set()

    if not needle:
        return []

    allowed_normalized: Optional[set[str]] = None
    if allowed_types is not None:
        allowed_normalized = {typ.lower() for typ in allowed_types if typ}
        if not allowed_normalized:
            return []

    for id, resource in RESOURCES.items():
        if allowed_normalized is not None and resource.type.lower() not in allowed_normalized:
            continue
        haystacks = [getattr(resource, "title", "") or ""]
        abstract = getattr(resource, "abstract", None) or ""
        if abstract:
            haystacks.append(abstract)
        if any(needle in value.lower() for value in haystacks if value):
            hits.append((id, resource, 0.0))
            seen.add(id)
            if len(hits) >= limit:
                break

    if len(hits) < limit:
        for id, resource in RESOURCES.items():
            if id in seen:
                continue
            if allowed_normalized is not None and resource.type.lower() not in allowed_normalized:
                continue
            hits.append((id, resource, 0.0))
            if len(hits) >= limit:
                break

    return hits


def search_resources(
    query: str,
    limit: int = 10,
    *,
    resource_types: Optional[Iterable[str]] = None,
) -> List[Tuple[int, ResourceType, float]]:
    if not query or not query.strip():
        return []

    allowed_normalized: Optional[set[str]] = None
    if resource_types is not None:
        allowed_normalized = {typ.lower() for typ in resource_types if typ}
        if not allowed_normalized:
            return []

    client = _get_openai_client()
    if client is None:
        return _search_fallback(query, limit, allowed_types=allowed_normalized)

    try:
        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=[query.strip()[:EMBED_MAX_CHARS]],
        )
    except Exception as exc:  # noqa: BLE001
        if st is not None:
            st.warning(f"Falling back to basic search: {exc}")
        else:
            print(f"Falling back to basic search: {exc}")
        return _search_fallback(query, limit, allowed_types=allowed_normalized)

    query_vector = _normalize_vector(response.data[0].embedding)
    if query_vector is None:
        return _search_fallback(query, limit, allowed_types=allowed_normalized)

    query_array = np.asarray(query_vector, dtype=np.float32)

    scored: List[Tuple[float, int, ResourceType]] = []
    for id, resource in RESOURCES.items():
        if allowed_normalized is not None and resource.type.lower() not in allowed_normalized:
            continue
        embedding = getattr(resource, "embedding", None)
        if not embedding:
            continue
        resource_array = np.asarray(embedding, dtype=np.float32)
        score = float(np.dot(resource_array, query_array))
        scored.append((score, id, resource))

    if not scored:
        return _search_fallback(query, limit, allowed_types=allowed_normalized)

    scored.sort(reverse=True)

    results: List[Tuple[int, ResourceType, float]] = []
    for score, id, resource in scored:
        results.append((id, resource, score))
        if len(results) >= limit:
            break

    return results


def sample_resources(
    count: int = 5,
    *,
    resource_types: Optional[Iterable[str]] = None,
) -> List[Tuple[int, ResourceType]]:
    allowed: Optional[set[str]] = None
    if resource_types is not None:
        allowed = {typ.lower() for typ in resource_types if typ}
        if not allowed:
            return []

    pool: List[Tuple[int, ResourceType]] = []
    for id, resource in RESOURCES.items():
        if allowed is not None and resource.type.lower() not in allowed:
            continue
        pool.append((id, resource))

    if not pool:
        return []

    if count >= len(pool):
        random.shuffle(pool)
        return pool

    return random.sample(pool, count)


def _load_resources() -> None:
    global RESOURCES

    loaded_from_disk = False
    if RESOURCE_PATH.exists():
        with open(RESOURCE_PATH, "rb") as file:
            RESOURCES = pickle.load(file)
            loaded_from_disk = True

    if len(RESOURCES) == 0:
        # Important to load publications before experiments
        _load_publications()
        _load_experiments()

    updated = _ensure_embeddings()

    if not RESOURCE_PATH.exists() or (loaded_from_disk and updated):
        with open(RESOURCE_PATH, "wb") as file:
            pickle.dump(RESOURCES, file)


# Load resources statically once on server startup
_load_resources()
