import streamlit as st
from semanticscholar import SemanticScholar
from pandas import read_csv

from utils.config import PUBLICATIONS_PATH
from utils.navigation import render_sidebar


st.set_page_config(
    page_title="CSV Publications",
    page_icon="📊",
)

# render_sidebar("pages/2_Publications.py")
# Title
st.markdown("# CSV Publications Test")



# Get CSV publications
publications = read_csv(PUBLICATIONS_PATH)
publications

first_title = publications['Title'][0]

first_title

# Create an instance of the client to request data from the API
sch = SemanticScholar()

# Get a paper by its ID
paper = sch.get_paper('10.1093/mind/lix.236.433')

# Print the paper title
st.write(paper.title)
