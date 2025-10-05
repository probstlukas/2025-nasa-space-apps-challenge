import requests
import json
import pandas as pd
from io import StringIO


_CACHED_PUBMED_TO_OSD_MAP = None


def fetch_metadata():
    # url = f"https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/{osd_id}/assay/*/sample/*/?format=json"
    # url = f"https://visualization.osdr.nasa.gov/biodata/api/v2/query/metadata/?investigation.study%20publications.study%20publication%20status=Published"
    url = "https://visualization.osdr.nasa.gov/biodata/api/v2/query/metadata/?investigation.study%20publications.study%20pubmed%20id"
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def _ensure_pubmed_to_osd_map():
    global _CACHED_PUBMED_TO_OSD_MAP
    if _CACHED_PUBMED_TO_OSD_MAP is not None:
        return

    data = fetch_metadata()

    # Read into a pandas DataFrame
    df = pd.read_csv(
        StringIO(data), dtype={"investigation.study publications.study pubmed id": str}
    )

    # print(df)

    # Group by PubMed ID and get unique OSD IDs per group
    grouped = (
        df.groupby("investigation.study publications.study pubmed id")["id.accession"]
        .unique()
        .to_dict()
    )
    grouped = {pubmed_id: list(osd_ids) for pubmed_id, osd_ids in grouped.items()}

    _CACHED_PUBMED_TO_OSD_MAP = grouped


def get_pubmed_to_osd(pubmed_id: str):
    """
    Returns the list of dataset ids (OSD ids) given the publication id (pubmed id) or None if no data is available.

    The url for datasets has the following format:
    `https://osdr.nasa.gov/bio/repo/data/studies/<OSD-ID>`
    """
    _ensure_pubmed_to_osd_map()
    print(_CACHED_PUBMED_TO_OSD_MAP)
    return _CACHED_PUBMED_TO_OSD_MAP.get(pubmed_id, None)


if __name__ == "__main__":
    osd_ids = get_pubmed_to_osd("37686374")
    print(osd_ids)
