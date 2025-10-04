from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup, FeatureNotFound
from pandas import read_csv

from utils.config import PUBLICATIONS_PATH


st.set_page_config(page_title="Publications", page_icon="📊")


