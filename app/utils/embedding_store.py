from pathlib import Path
import pickle
from typing import Dict, Iterable, Tuple

import numpy as np

from utils.config import PUBLICATIONS_PATH
import tqdm


def _model_slug(model_name: str) -> str:
    return model_name.replace("/", "_").replace("-", "_")


def _store_path(model_name: str) -> Path:
    return (
        PUBLICATIONS_PATH.resolve().parent / f"embeddings_{_model_slug(model_name)}.npz"
    )


def load_embedding_store(model_name: str) -> Dict[str, np.ndarray]:
    from .resource_manager import RESOURCES

    print(len(RESOURCES))
    exit()

    path = _store_path(model_name)
    if not path.exists():
        return {}
    try:
        data = np.load(path, allow_pickle=True)
    except (OSError, ValueError):
        return {}
    ids = data.get("ids")
    embeddings = data.get("embeddings")
    if ids is None or embeddings is None:
        return {}
    id_list = ids.tolist()
    return {str(id_list[i]): embeddings[i] for i in range(len(id_list))}


def save_embedding_store(model_name: str, store: Dict[str, np.ndarray]) -> None:
    if not store:
        return
    ids = np.array(list(store.keys()), dtype=object)
    embeddings = np.stack([store[key] for key in ids], axis=0)
    path = _store_path(model_name)
    np.savez_compressed(path, ids=ids, embeddings=embeddings)


def get_embeddings_for_texts(
    model_name: str,
    ids: Iterable[str],
    texts: Iterable[str],
    encode_fn,
    store: Dict[str, np.ndarray] | None = None,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    print("Load embedding store")
    if store is None:
        store = load_embedding_store(model_name)
    ids_list = list(ids)
    texts_list = list(texts)

    missing_indices = [
        idx for idx, identifier in enumerate(ids_list) if identifier not in store
    ]
    if missing_indices:
        to_encode = [texts_list[idx] for idx in missing_indices]
        new_embeddings = encode_fn(to_encode)
        for index, embedding in tqdm.tqdm(zip(missing_indices, new_embeddings)):
            key = ids_list[index]
            store[key] = embedding.astype(np.float32)
        save_embedding_store(model_name, store)

    embeddings = np.stack([store[identifier] for identifier in ids_list], axis=0)
    return embeddings, store
