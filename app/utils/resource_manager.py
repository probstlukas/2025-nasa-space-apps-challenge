from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from pandas import DataFrame, read_csv

from utils.config import PUBLICATIONS_PATH
from utils.openalex_utils import fetch_work_by_title


class PaperResource:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        self._data = None

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        if self._data is None:
            self._data = fetch_work_by_title(self.title)
        return self._data

    @property
    def year(self):
        if self.data is not None:
            return self._data.get("year", "-")
        else:
            return "-"

    def get_property(self, key: str, default=None):
        if self.data is not None:
            return self.data.get(key, default)
        return default

    title: str
    url: str
    data: Optional[Dict[str, Any]]


@dataclass
class ExperimentResource:
    title: str
    description: str


ResourceType = Union[PaperResource, ExperimentResource]


RESOUCES: Dict[int, ResourceType] = {}


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
        RESOUCES[gen_id()] = PaperResource(title=row["Title"], url=row["Link"])


# Load resources statically once on server startup
_load_resources()
