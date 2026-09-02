"""
impact.py

Builds on graph_builder.py and simulator.py (unchanged) to answer:

    "When this road fails, which important locations are affected?"

This matches Section 12 of the project doc: villages, hospitals,
and warehouses are "critical locations" mapped onto graph nodes.
We do NOT do any logistics optimization here -- just classify each
critical location as one of:

    - "unaffected"     : still reachable at the same cost
    - "longer_route"    : still reachable, but costs more
    - "unreachable"      : no longer reachable at all

Nothing here modifies graph_builder.py or simulator.py.
"""

from simulator import find_route, simulate_road_failure


# Example critical locations for our tiny artificial network.
# Maps a human-readable name to a node in the graph.
# Real critical locations (from real GIS data) will replace this later.
CRITICAL_LOCATIONS = {
    "warehouse_1": "A",
    "village_1": "D",
    "hospital_1": "C",
}


def classify_location(original_result: dict, alternative_result: dict) -> str:
    """
    Compares a location's route before/after a failure and classifies it.
    """
    if not alternative_result["reachable"]:
        return "unreachable"
    if alternative_result["cost"] > original_result["cost"]:
        return "longer_route"
    return "unaffected"


def calculate_impact(
    graph, road_id: str, origin: str, critical_locations: dict = None
) -> dict:
    """
    Simulates a road failure and reports the impact on critical locations
    reachable from `origin`.

    Args:
        graph: the original network (networkx.Graph), left untouched.
        road_id: the road to simulate as failed.
        origin: the starting point (e.g. a warehouse node).
        critical_locations: dict of name -> node. Defaults to
            CRITICAL_LOCATIONS if not provided.

    Returns:
        {
            "failed_road": road_id,
            "origin": origin,
            "locations": {
                "hospital_1": {
                    "status": "unreachable" / "longer_route" / "unaffected",
                    "original_cost": ...,
                    "alternative_cost": ...,
                },
                ...
            },
            "affected_locations": [names that are NOT "unaffected"]
        }
    """
    if critical_locations is None:
        critical_locations = CRITICAL_LOCATIONS

    failed_graph = simulate_road_failure(graph, road_id)

    locations_report = {}
    affected = []

    for name, node in critical_locations.items():
        if node == origin:
            # Skip the origin itself -- distance to itself isn't meaningful.
            continue

        original_result = find_route(graph, origin, node)
        alternative_result = find_route(failed_graph, origin, node)

        status = classify_location(original_result, alternative_result)

        locations_report[name] = {
            "status": status,
            "original_cost": original_result["cost"],
            "alternative_cost": alternative_result["cost"],
        }

        if status != "unaffected":
            affected.append(name)

    return {
        "failed_road": road_id,
        "origin": origin,
        "locations": locations_report,
        "affected_locations": affected,
    }
