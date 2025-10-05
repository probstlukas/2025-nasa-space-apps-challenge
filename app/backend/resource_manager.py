RESOURCES = {
    1: {
        "type": "paper",
        "title": "Some paper title",
        "abstract": "A comprehensive study on deep learning for NLP tasks.",
        "experiments": ["GLUE", "SQuAD"],
        "citations": [(1, 2), (2, 3)],
    },
    2: {
        "type": "experiment",
        "description": "Explores the use of GNNs in various domains.",
        "papers": ["Cora", "PubMed"],
        "authors": [(1, 3), (3, 2)],
    },
    3: {
        "type": "experiment",
        "description": "Second demo experiment.",
        "papers": ["Cora", "PubMed"],
        "authors": [(1, 3), (3, 2)],
    },
}


def get_resource(resource_id: int):
    return RESOURCES.get(resource_id, {})
