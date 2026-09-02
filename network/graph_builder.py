"""
graph_builder.py

Builds a small, made-up road network so we can test our
failure-simulation logic before touching real NER road data.

Concepts used here:
- Graph: a set of "nodes" (locations) connected by "edges" (roads).
- Node: a single location, e.g. a warehouse, village, or hospital.
- Edge: a road connecting two locations. We store extra info
  (road_id, distance) on each edge.
- Weighted edge: an edge that has a "cost" attached to it (here,
  distance). Shortest-path algorithms use this weight to decide
  the "best" route.

We use the NetworkX library because it already implements graphs
and shortest-path algorithms correctly, so we don't have to write
that from scratch.
"""

import networkx as nx


def build_network() -> nx.Graph:
    """
    Builds the tiny artificial network described in the project doc:

            B
           / \\
          /   \\
         A     C
          \\   /
           \\ /
            D

    Roads (edges):
        R1: A - B, distance 10
        R2: B - C, distance 10
        R3: A - D, distance 8
        R4: D - C, distance 8

    Returns:
        networkx.Graph: an undirected graph where each edge has
        'road_id' and 'distance' attributes.
    """
    graph = nx.Graph()

    # Add locations as nodes. Real coordinates / names come later.
    graph.add_nodes_from(["A", "B", "C", "D"])

    # Add roads as weighted edges.
    # Each road gets a unique road_id so we can select it later.
    roads = [
        ("A", "B", "R1", 10),
        ("B", "C", "R2", 10),
        ("A", "D", "R3", 8),
        ("D", "C", "R4", 8),
    ]

    for start, end, road_id, distance in roads:
        graph.add_edge(start, end, road_id=road_id, distance=distance)

    return graph


if __name__ == "__main__":
    # Quick manual check: run this file directly to see the network.
    g = build_network()
    print("Nodes:", list(g.nodes))
    print("Edges:")
    for u, v, data in g.edges(data=True):
        print(f"  {u} - {v}  road_id={data['road_id']}  distance={data['distance']}")
