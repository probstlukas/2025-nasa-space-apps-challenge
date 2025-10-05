from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
PUBLICATIONS_PATH = DATA_DIR / "SB_publication_PMC.csv"
EXPERIMENTS_PATH = DATA_DIR / "osd_experiment_data.pkl"
RESOURCE_PATH = DATA_DIR / "resources.pkl"
SIM_GRAPH = DATA_DIR / "similarity_graph.json"

LOGO_PATH = BASE_DIR / "images" / "logo.png"
