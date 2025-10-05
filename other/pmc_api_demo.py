import requests
import xml.etree.ElementTree as ET
import re
import pandas as pd


def get_pmc_abstract(url):
    """
    Fetch the abstract of a PMC article using the PMC OAI-PMH API.
    Returns the abstract as a string, or None if not found.
    Handles both correct and typo versions of the abstract element.
    """
    # Extract numeric PMC ID from URL
    match = re.search(r"PMC(\d+)", url)
    if not match:
        raise ValueError("Invalid PMC URL")

    pmc_numeric_id = match.group(1)
    oai_id = f"oai:pubmedcentral.nih.gov:{pmc_numeric_id}"

    # Construct API URL
    api_url = (
        f"https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
        f"?verb=GetRecord&metadataPrefix=oai_dc&identifier={oai_id}"
    )

    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")

    root = ET.fromstring(response.text)
    namespaces = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    }

    # Look for both the correct and typo versions
    abstract_elements = root.findall(".//dc:description", namespaces)
    if not abstract_elements:
        abstract_elements = root.findall(
            ".//dc:descripton", namespaces
        )  # typo fallback

    if abstract_elements:
        abstract = " ".join([elem.text for elem in abstract_elements if elem.text])
        return abstract.strip()
    else:
        return None


# Assuming you already have the get_pmc_abstract function defined
# from the previous code snippet

# Load the CSV
df = pd.read_csv(
    "data/SB_publication_PMC.csv"
)  # replace with your actual CSV file path

# Create a new column to store abstracts
df["Abstract"] = None

# Iterate over the URLs and fetch abstracts
for idx, row in df.iterrows():
    url = row["Link"]
    try:
        abstract = get_pmc_abstract(url)
        df.at[idx, "Abstract"] = abstract
        print(f"Processed {url}")
        print(f"Abstract: {abstract[:100]}")
    except Exception as e:
        print(f"Failed to process {url}: {e}")

# Save the updated CSV with abstracts
df.to_csv("your_file_with_abstracts.csv", index=False)
