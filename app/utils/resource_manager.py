from dataclasses import dataclass
from typing import Any, Dict, Optional
from pandas import DataFrame, read_csv
from pathlib import Path

from .config import PUBLICATIONS_PATH
from .openalex_utils import fetch_work_by_title


class PaperResource:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        self._data = None

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        fetch_work_by_title(self.title)

    title: str
    url: str
    data: Optional[Dict[str, Any]]


@dataclass
class ExperimentResource:
    title: str
    description: str


RESOURCES = {
    1: {
        "type": "paper",
        "title": "Some paper title",
        "abstract": "A comprehensive study on deep learning for NLP tasks.",
        "experiments": ["GLUE", "SQuAD"],
        "citations": [(1, 2), (2, 3)],
    },
    2: {
        "type": "experiment",
        "description": "Explores the use of GNNs in various domains.",
        "papers": ["Cora", "PubMed"],
        "authors": [(1, 3), (3, 2)],
    },
    3: {
        "type": "experiment",
        "description": "Second demo experiment.",
        "papers": ["Cora", "PubMed"],
        "authors": [(1, 3), (3, 2)],
    },
}


_next_id = 0


def gen_id():
    global _next_id
    id = _next_id
    _next_id += 1
    return id


def _ensure_resources() -> DataFrame:
    df = read_csv(PUBLICATIONS_PATH)
    data = df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])

    for _, row in data.iterrows():
        print(row["Title"])
        RESOURCES[gen_id()] = PaperResource(title=row["Title"], url=row["Link"])

    print(RESOURCES[0])


def get_resource(resource_id: int):
    return RESOURCES.get(resource_id, {})


if __name__ == "__main__":
    _ensure_resources()
