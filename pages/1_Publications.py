from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup, FeatureNotFound
from pandas import read_csv

from utils.config import PUBLICATIONS_PATH


st.set_page_config(page_title="Publications", page_icon="📊")


EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def extract_pmcid(link: str) -> str:
    segments = [segment for segment in urlparse(link).path.split("/") if segment]
    for segment in reversed(segments):
        if segment.upper().startswith("PMC"):
            return segment.upper()
    return ""


def _parse_xml(content: str) -> BeautifulSoup:
    for parser in ("lxml-xml", "xml", "html.parser"):
        try:
            return BeautifulSoup(content, parser)
        except FeatureNotFound:
            continue
    raise RuntimeError("A suitable XML parser for BeautifulSoup is not installed.")


@st.cache_data(show_spinner=False)
def fetch_pmc_metadata(pmc_id: str) -> dict[str, object]:
    if not pmc_id:
        return {"abstract": "", "references": []}

    params = {"db": "pmc", "id": pmc_id, "retmode": "xml"}
    response = requests.get(EUTILS_URL, params=params, timeout=15)
    response.raise_for_status()

    soup = _parse_xml(response.text)
    article = soup.find("article")
    if not article:
        return {"abstract": "", "references": []}

    abstract_block = article.find("abstract")
    abstract = abstract_block.get_text(" ", strip=True) if abstract_block else ""

    references: list[str] = []
    back = article.find("back")
    if back:
        for ref in back.find_all("ref"):
            citation = (
                ref.find("mixed-citation")
                or ref.find("element-citation")
                or ref.find("citation")
                or ref
            )
            text = citation.get_text(" ", strip=True)
            if text:
                references.append(text)

    # Preserve order and remove duplicates while iterating
    seen = set()
    unique_references = []
    for ref in references:
        if ref not in seen:
            seen.add(ref)
            unique_references.append(ref)

    return {"abstract": abstract, "references": unique_references}


def render_publication_details(title: str, link: str) -> None:
    pmc_id = extract_pmcid(link)
    if not pmc_id:
        st.warning("Unable to determine a PMCID from the provided link.")
        return

    with st.spinner(f"Fetching PMC metadata for {pmc_id}..."):
        try:
            metadata = fetch_pmc_metadata(pmc_id)
        except requests.RequestException as exc:
            st.error(f"Failed to retrieve PMC content: {exc}")
            return
        except RuntimeError as exc:
            st.error(str(exc))
            return

    st.subheader(title)
    st.markdown(f"[View on PMC]({link})")
    st.subheader("Abstract")
    if metadata["abstract"]:
        st.write(metadata["abstract"])
    else:
        st.info("No abstract available in the PMC record.")

    st.subheader("References")
    if metadata["references"]:
        for reference in metadata["references"]:
            st.markdown(f"- {reference}")
    else:
        st.info("No references were found in the PMC record.")


def validate_publications(publications_df) -> dict[str, list[str]]:
    results = {
        "missing_abstract": [],
        "missing_references": [],
        "errors": [],
    }

    for idx, publication in publications_df.iterrows():
        title = publication.get("Title", f"Row {idx}")
        link = publication.get("Link", "")
        pmc_id = extract_pmcid(link)

        if not pmc_id:
            results["errors"].append(f"{title}: Unable to determine PMCID from link")
            continue

        try:
            metadata = fetch_pmc_metadata(pmc_id)
        except requests.RequestException as exc:
            results["errors"].append(f"{title}: Request failed ({exc})")
            continue
        except RuntimeError as exc:
            results["errors"].append(f"{title}: {exc}")
            continue

        if not metadata["abstract"]:
            results["missing_abstract"].append(title)
        if not metadata["references"]:
            results["missing_references"].append(title)

    return results


st.title("Space Biology Publications")

publications = read_csv(PUBLICATIONS_PATH)

if publications.empty:
    st.info("No publications found in the CSV file.")
else:
    st.dataframe(publications, hide_index=True)

    selection = st.selectbox(
        "Select a publication to view details",
        publications.index,
        format_func=lambda idx: publications.loc[idx, "Title"],
    )

    selected_publication = publications.loc[selection]
    render_publication_details(
        title=selected_publication.get("Title", "Untitled"),
        link=selected_publication.get("Link", ""),
    )

    with st.expander("Validate metadata for all publications"):
        if st.button("Run metadata check"):
            with st.spinner("Validating abstracts and references..."):
                validation = validate_publications(publications)

            if not any(validation.values()):
                st.success("All publications include an abstract and references.")
            else:
                if validation["missing_abstract"]:
                    st.warning(
                        "Publications without abstracts: "
                        + "; ".join(validation["missing_abstract"])
                    )
                if validation["missing_references"]:
                    st.warning(
                        "Publications without references: "
                        + "; ".join(validation["missing_references"])
                    )
                if validation["errors"]:
                    st.error("Issues detected:\n" + "\n".join(validation["errors"]))
