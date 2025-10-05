import datetime
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union
from pandas import DataFrame, read_csv

# from pyalex import config as pyalex_config, invert_abstract
from pyalex.api import invert_abstract

from utils.config import PUBLICATIONS_PATH, EXPERIMENTS_PATH, RESOURCE_PATH
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


def _load_resources() -> DataFrame:
    global RESOURCES

    if RESOURCE_PATH.exists():
        with open(RESOURCE_PATH, "rb") as file:
            RESOURCES = pickle.load(file)
            print("Loaded resources from file")

    if len(RESOURCES) > 0:
        return

    # Important to load publications before experiments
    _load_publications()

    _load_experiments()

    if not RESOURCE_PATH.exists():
        with open(RESOURCE_PATH, "wb") as file:
            pickle.dump(RESOURCES, file)


# Load resources statically once on server startup
_load_resources()
