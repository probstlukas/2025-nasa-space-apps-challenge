from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union
from pandas import DataFrame, read_csv

# from pyalex import config as pyalex_config, invert_abstract
from pyalex.api import invert_abstract

from utils.config import PUBLICATIONS_PATH
from utils.openalex_utils import (
    fetch_work_by_title,
    fetch_referenced_works,
    summarise_reference,
    resolve_best_link,
)


class PaperResource:
    def __init__(self, title: str):
        self.title = title
        self.type = "Publication"
        self.icon = "📄"
        self._data = None

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
                print(summaries)
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
    def url(self) -> Optional[Tuple[str, str]]:
        if self.data is None:
            return None
        link_info = resolve_best_link(self.data)
        primary_link = link_info.get("url")
        if primary_link:
            label = link_info.get("label") or "Source"
            return label, primary_link
        return None

    def get_property(self, key: str, default=None):
        if self.data is not None:
            return self.data.get(key, default)
        return default

    title: str
    data: Optional[Dict[str, Any]]


@dataclass
class ExperimentResource:
    title: str
    description: str
    type: str = "Experiment"
    icon: str = "🔬"

    @property
    def abstract(self):
        return self.description


ResourceType = Union[PaperResource, ExperimentResource]


RESOURCES: Dict[int, ResourceType] = {}


_next_id = 0


def gen_id():
    global _next_id
    id = _next_id
    _next_id += 1
    return id


def _load_resources() -> DataFrame:
    df = read_csv(PUBLICATIONS_PATH)
    data = df.dropna(subset=["Title"]).drop_duplicates(subset=["Title"])

    for _, row in data.iterrows():
        RESOURCES[gen_id()] = PaperResource(title=row["Title"])


# Load resources statically once on server startup
_load_resources()
