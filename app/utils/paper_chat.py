"""Utilities for paper-centric chat, including PDF ingestion and retrieval."""

from __future__ import annotations

from io import BytesIO
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
import streamlit as st
from openai import OpenAI

CHAT_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MAX_CHUNKS = 120
RETRIEVAL_TOP_K = 4

PDF_TEXT_MAX_BYTES = 15 * 1024 * 1024  # 15 MB limit for text extraction


@st.cache_resource(show_spinner=False)
def get_openai_client() -> Optional[OpenAI]:
    """Return a cached OpenAI client if an API key is configured."""
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def truncate_for_context(text: Optional[str], limit: int = 2500) -> str:
    """Trim long strings for display or prompt construction."""
    if not text:
        return "Not available."
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


@st.cache_data(show_spinner=False)
def fetch_pdf_bytes(pdf_url: Optional[str]) -> Optional[bytes]:
    """Download and cache the raw PDF bytes from a URL."""
    if not pdf_url:
        return None

    try:
        response = requests.get(pdf_url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        st.warning(f"Unable to download PDF: {exc}")
        return None

    return response.content


@st.cache_data(show_spinner=False)
def load_pdf_text(pdf_url: Optional[str]) -> Optional[str]:
    """Extract text from a PDF URL using cached bytes."""
    raw_bytes = fetch_pdf_bytes(pdf_url)
    if raw_bytes is None:
        return None

    if len(raw_bytes) > PDF_TEXT_MAX_BYTES:
        st.warning(
            "PDF is larger than 15 MB – skipping automatic ingestion to keep the app responsive."
        )
        return None

    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        raw_text = "\n".join(pages)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Unable to extract text from PDF: {exc}")
        return None

    cleaned = re.sub(r"\s+", " ", raw_text).strip()
    return cleaned or None


def chunk_text(
    text: str,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    max_chunks: int = MAX_CHUNKS,
) -> Tuple[List[str], bool]:
    """Split text into overlapping windows and report if truncation occurred."""
    sanitized = re.sub(r"\s+", " ", text).strip()
    if not sanitized:
        return [], False

    chunks: List[str] = []
    start = 0
    length = len(sanitized)
    truncated = False

    while start < length and len(chunks) < max_chunks:
        end = min(start + chunk_size, length)
        if end < length:
            soft_end = sanitized.rfind(" ", start + chunk_size // 2, end)
            if soft_end != -1 and soft_end > start:
                end = soft_end

        chunk = sanitized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break

        next_start = end - overlap if overlap and overlap < chunk_size else end
        if next_start <= start:
            next_start = end
        start = next_start

    if start < length and len(chunks) >= max_chunks:
        truncated = True

    return chunks, truncated


def build_pdf_index(
    pdf_text: str,
    client: OpenAI,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    max_chunks: int = MAX_CHUNKS,
) -> Optional[Dict[str, Any]]:
    """Create embeddings over PDF chunks for semantic retrieval."""
    chunks, truncated = chunk_text(
        pdf_text,
        chunk_size=chunk_size,
        overlap=overlap,
        max_chunks=max_chunks,
    )
    if not chunks:
        return None

    try:
        embedding_response = client.embeddings.create(
            model=EMBED_MODEL,
            input=chunks,
        )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Unable to embed PDF chunks: {exc}")
        return None

    embeddings = [datum.embedding for datum in embedding_response.data]
    return {"chunks": chunks, "embeddings": embeddings, "truncated": truncated}


def retrieve_passages(
    query: str,
    index: Dict[str, Any],
    client: OpenAI,
    *,
    top_k: int = RETRIEVAL_TOP_K,
) -> List[Dict[str, Any]]:
    """Return the top semantic matches for a query from the PDF index."""
    chunks: List[str] = index.get("chunks") or []
    embeddings: List[List[float]] = index.get("embeddings") or []
    if not chunks or not embeddings:
        return []

    try:
        query_embedding = client.embeddings.create(
            model=EMBED_MODEL,
            input=[query],
        ).data[0].embedding
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Unable to embed question for retrieval: {exc}")
        return []

    chunk_matrix = np.array(embeddings)
    query_vector = np.array(query_embedding)

    chunk_norms = np.linalg.norm(chunk_matrix, axis=1)
    query_norm = np.linalg.norm(query_vector)
    denom = np.maximum(chunk_norms * query_norm, 1e-12)
    similarities = (chunk_matrix @ query_vector) / denom

    if similarities.size == 0:
        return []

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    results: List[Dict[str, Any]] = []
    for rank, idx in enumerate(top_indices, start=1):
        score = float(similarities[idx])
        if score <= 0:
            continue
        results.append({"rank": rank, "score": score, "text": chunks[idx]})

    return results


def generate_chat_response(messages: List[Dict[str, str]]) -> Optional[str]:
    """Send a chat completion request using the default model."""
    client = get_openai_client()
    if client is None:
        st.error("OpenAI API key missing. Add `OPENAI_API_KEY` to Streamlit secrets to enable Q&A.")
        return None

    try:
        completion = client.chat.completions.create(
            model=CHAT_MODEL,
            temperature=0.2,
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Chatbot error: {exc}")
        return None

    return completion.choices[0].message.content if completion.choices else None


def stream_chat_response(messages: List[Dict[str, str]]):
    """Yield partial assistant responses as they stream from OpenAI."""
    client = get_openai_client()
    if client is None:
        st.error("OpenAI API key missing. Add `OPENAI_API_KEY` to Streamlit secrets to enable Q&A.")
        return

    try:
        stream = client.chat.completions.create(
            model=CHAT_MODEL,
            temperature=0.2,
            messages=messages,
            stream=True,
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Chatbot error: {exc}")
        return

    for part in stream:
        chunk = part.choices[0].delta.content
        if chunk:
            yield chunk


def approx_indexed_character_count(
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    max_chunks: int = MAX_CHUNKS,
) -> int:
    """Estimate the number of characters retained in the retrieval index."""
    effective = chunk_size - overlap if overlap and overlap < chunk_size else chunk_size
    if effective <= 0:
        effective = chunk_size
    return max_chunks * effective
