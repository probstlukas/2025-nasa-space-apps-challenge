from functools import partial
from typing import List, Tuple
import streamlit as st
import pandas as pd
import utils.resource_manager as R
from utils.resource_manager import ResourceType


# TODO: Instead implement this utility in the backend and import it here
def search_resources(query) -> List[Tuple[int, ResourceType]]:
    results = []
    for idx, (id, resource) in enumerate(R.RESOUCES.items()):
        results.append((id, resource))
        if idx >= 10:
            break
    return results


def setup_search_page(on_resource_clicked):
    query = st.text_input("Search for papers:")
    if query:
        results = search_resources(query)

        for id, resource in results:
            # st.button(
            #    f"📄 {resource.title} (Year: {resource.year}, Authors: {resource.authors})",
            #    on_click=lambda id=id: on_resource_clicked(id),
            # )

            st.markdown(
                f"""
                **📄 {resource.title}**

                *Authors:* {', '.join(resource.authors)}  
                *Year:* {resource.year}  
                *Type:* {resource.type}
                """
            )
            st.button(
                "Select",
                key=id,
                on_click=lambda id=id: on_resource_clicked(id),
            )
            st.divider()
        else:
            st.info("No results found.")
