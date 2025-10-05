import streamlit as st


from paper_search.search_page import setup_search_page
from paper_search.paper_view import setup_paper_view
from paper_search.experiment_view import setup_experiment_view
import utils.resource_manager as R


# ---- Mock Data & Functions ----
def on_resource_clicked(resource_id: int):
    print("on resource clicked", resource_id)

    st.session_state.selected_resource = resource_id


# ---- Streamlit Layout ----
st.set_page_config(page_title="BioScholar", layout="wide")
st.title("🔍 BioScholar")

# State to track selected paper
if "selected_resource" not in st.session_state:
    st.session_state.selected_resource = None


# ---- Main View Logic ----
if st.session_state.selected_resource is None:
    setup_search_page(on_resource_clicked)
else:
    # ---- Paper Details View ----
    resource_id = st.session_state.selected_resource
    resource = R.RESOURCES.get(resource_id)

    def on_click():
        st.session_state.update(selected_resource=None)
        print("paper clicked")

    st.button(
        "⬅️ Back to search",
        on_click=on_click,
    )

    if isinstance(resource, R.PaperResource):
        resource_type = "paper"
    elif isinstance(resource, R.ExperimentResource):
        resource_type = "experiment"
    else:
        raise ValueError(f"Unknown resource type '{type(resource).__name__}'")

    if resource_type == "paper":
        setup_paper_view(resource_id, resource)
    elif resource_type == "experiment":
        setup_experiment_view(resource_id, resource)
    else:
        raise ValueError(
            f"Unknown resource-type '{resource_type}' with id '{resource_id}'"
        )
