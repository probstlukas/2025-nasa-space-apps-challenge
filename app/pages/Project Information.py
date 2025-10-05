import streamlit as st

# ------------------------------------------------------------
# 🎨 Page Configuration
# ------------------------------------------------------------
st.set_page_config(page_title="Project Information", page_icon="📊", layout="wide")

# ------------------------------------------------------------
# 🏷️ Page Header
# ------------------------------------------------------------
st.title("📊 Project Information")
st.markdown("#### Project overview and documentation.")

st.divider()

# ------------------------------------------------------------
# 📁 Project Metadata Section
# ------------------------------------------------------------
st.subheader("🗂️ Project Details")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Project Name", value="BioScholar")
with col2:
    st.metric(label="Status", value="Prototype")
with col3:
    st.metric(label="Last Updated", value="Oct 5, 2025")

st.markdown(
    """
    **Description:**  
    This project explores the intersection of biology and artificial intelligence to develop tools that assist researchers in analyzing scientific literature, extracting key insights, and accelerating discovery. BioScholar leverages advanced data processing, natural language understanding, and interactive dashboards to make research workflows more efficient and transparent.
    
    `BioScholar` is our project for the **NASA Space Apps Challenge hackathon**, addressing the **Space Biology Knowledge Engine** challenge.
    """
)

st.divider()


# ------------------------------------------------------------
# ⚡ Project Features
# ------------------------------------------------------------
st.subheader("✨ Key Features")
st.markdown(
    """
    - **Intelligent Q&A:** Ask questions about publications and get answers with precise passage citations.  
    - **Semantic Graph View:** Visualize the most relevant papers related to a selected resource, using AI-generated similarity scores to link related content.  
    - **Advanced Search:** Find publications and experimental resources quickly and efficiently.  
    - **Cross-Referencing:** Explore which publications reference specific experiments, and vice versa.  
    - **Integrated PDF Viewer:** Preview and interact with PDFs directly within the app whenever available.  
    """
)
st.divider()


# ------------------------------------------------------------
# 🧠 Related Resources / Documentation
# ------------------------------------------------------------
st.subheader("📚 NASA Space Apps Challenge")
st.markdown(
    """
    - [Project Information](https://www.spaceappschallenge.org/2025/challenges/build-a-space-biology-knowledge-engine/)  
    - [Data Sources](https://www.spaceappschallenge.org/2025/challenges/build-a-space-biology-knowledge-engine/?tab=resources)  
    """
)

st.divider()
