"""
simulator.py

The core logic for our "what-if a road fails" simulation.

Three functions:

1. find_route(graph, origin, destination)
   -> finds the shortest route between two locations using the
      road distances as weights (Dijkstra's algorithm, via NetworkX).

2. simulate_road_failure(graph, road_id)
   -> returns a NEW graph with that road removed. The original
      graph is never touched, so we can simulate multiple failures
      independently. This matches Section 10 of the project doc:
      "Original network stays intact."

3. compare_routes(original, alternative)
   -> compares two route results and reports the cost difference,
      or flags that the destination became unreachable.
"""

import networkx as nx


def find_route(graph: nx.Graph, origin: str, destination: str) -> dict:
    """
    Finds the shortest route between origin and destination.

    Returns a dict:
        {
            "reachable": bool,
            "path": [list of nodes] or None,
            "cost": total distance, or None if unreachable
        }
    """
    try:
        path = nx.shortest_path(graph, origin, destination, weight="distance")
        cost = nx.shortest_path_length(graph, origin, destination, weight="distance")
        return {"reachable": True, "path": path, "cost": cost}
    except nx.NetworkXNoPath:
        return {"reachable": False, "path": None, "cost": None}
    except nx.NodeNotFound as e:
        # Helpful error if someone typos a location name.
        raise ValueError(f"Unknown location: {e}")


def simulate_road_failure(graph: nx.Graph, road_id: str) -> nx.Graph:
    """
    Returns a COPY of the graph with the given road_id removed.
    The original graph passed in is never modified.

    Raises ValueError if no edge with that road_id exists.
    """
    new_graph = graph.copy()

    edge_to_remove = None
    for u, v, data in new_graph.edges(data=True):
        if data.get("road_id") == road_id:
            edge_to_remove = (u, v)
            break

    if edge_to_remove is None:
        raise ValueError(f"No road found with road_id='{road_id}'")

    new_graph.remove_edge(*edge_to_remove)
    return new_graph


def compare_routes(original: dict, alternative: dict) -> dict:
    """
    Compares an original route result to a post-failure route result.

    Returns a dict:
        {
            "destination_reachable": bool,
            "original_cost": number or None,
            "alternative_cost": number or None,
            "cost_increase": number or None,
            "recommendation": str
        }
    """
    if not alternative["reachable"]:
        return {
            "destination_reachable": False,
            "original_cost": original["cost"],
            "alternative_cost": None,
            "cost_increase": None,
            "recommendation": "Destination disconnected. No alternate route available.",
        }

    cost_increase = alternative["cost"] - original["cost"]

    if cost_increase <= 0:
        recommendation = "Alternate route available with no extra cost."
    else:
        recommendation = f"Use alternate route. Cost increases by {cost_increase}."

    return {
        "destination_reachable": True,
        "original_cost": original["cost"],
        "alternative_cost": alternative["cost"],
        "cost_increase": cost_increase,
        "recommendation": recommendation,
    }
