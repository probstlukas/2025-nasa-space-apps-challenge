# Toolchains
Set of toolchains to generate graph data from a set of papers, experiements etc. 

## Structure of a toolchain
Each toolchain is a method which returns a networkx graph.
The minimal requirement for a graph are the following:
- Each edge is undirected
- Each edge has a `similarity` score of type `float` in [0,1]


```python
def create_citation_graph() -> nx.Graph:
    # Create citation graph with network x
    return graph
```


# NetworkX Graph
```python
import networkx as nx
import matplotlib.pyplot as plt

# Create an undirected graph
G = nx.Graph()

# Add nodes with attributes
G.add_nodes_from([
    ("A", {"label": "Person A", "age": 30}),
    ("B", {"label": "Person B", "age": 25}),
    ("C", {"label": "Person C", "age": 40}),
])

# Add edges with attributes (including similarity)
G.add_edges_from([
    ("A", "B", {"similarity": 0.8, "relation": "friends"}),
    ("A", "C", {"similarity": 0.6, "relation": "colleagues"}),
    ("B", "C", {"similarity": 0.9, "relation": "siblings"}),
])

# Print nodes and edges with attributes
print("Nodes:", G.nodes(data=True))
print("Edges:", G.edges(data=True))
```

## Retrieve edges for a node
```python
# G.edges("A", data=True)
edges = list(G.edges("A", data=True))
# Output
# [('A', 'B', {'similarity': 0.8, 'relation': 'friends'}),
# ('A', 'C', {'similarity': 0.6, 'relation': 'colleagues'})]
```