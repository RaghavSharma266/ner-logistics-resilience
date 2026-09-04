"""
network_client.py

Thin orchestration wrapper around the EXISTING, UNMODIFIED Network module
(`network/gis_loader.py`, `network/simulator.py`). This file does not
reimplement routing, failure simulation, or graph building -- it only:

    1. Loads the real Assam road network (gis/data/assam_roads.geojson)
       through network.gis_loader.load_geojson_file() -- the exact,
       already-tested loader.
    2. Caches the resulting nx.MultiGraph in memory (rebuilding a 23-edge
       graph from GeoJSON on every request would be wasteful; the file
       does not change while the server runs).
    3. Delegates routing/failure/comparison to network.simulator's
       find_route / simulate_road_failure / compare_routes.
    4. Adds ONE small piece of glue logic that does not exist in the
       Network module: given a road_id, find the *direct* parallel
       alternate corridor (if any) between that road's origin and
       destination districts. This is required by the project's
       "Alternate Route Rule" (same origin AND destination district),
       and is derived entirely from the graph's real edge data -- never
       hardcoded, never guessed.
"""

from . import path_setup  # noqa: F401  (must run before the imports below)

import os
import threading

import networkx as nx

import gis_loader  # network/gis_loader.py, unmodified
import simulator  # network/simulator.py, unmodified

ASSAM_ROADS_GEOJSON = os.path.join(path_setup.GIS_DATA_DIR, "assam_roads.geojson")

_graph_lock = threading.Lock()
_graph_cache = None


def get_graph() -> nx.MultiGraph:
    """
    Returns the cached MultiGraph built from the real Assam road GeoJSON via
    network.gis_loader.load_geojson_file() (unmodified). Built once, reused
    across requests -- the original graph object is never mutated (every
    failure simulation works on a copy, per simulator.simulate_road_failure).
    """
    global _graph_cache
    if _graph_cache is None:
        with _graph_lock:
            if _graph_cache is None:  # re-check inside the lock
                _graph_cache = gis_loader.load_geojson_file(ASSAM_ROADS_GEOJSON)
    return _graph_cache


def find_route(graph: nx.MultiGraph, origin: str, destination: str) -> dict:
    """Delegates directly to network.simulator.find_route (unmodified)."""
    return simulator.find_route(graph, origin, destination)


def simulate_failure(graph: nx.MultiGraph, road_id: str) -> nx.MultiGraph:
    """
    Delegates directly to network.simulator.simulate_road_failure
    (unmodified). Raises ValueError if road_id isn't an edge in the graph
    -- callers should validate road_id against the GIS road list first for
    a cleaner error message; this is the authoritative check.
    """
    return simulator.simulate_road_failure(graph, road_id)


def compare_routes(original: dict, alternative: dict) -> dict:
    """Delegates directly to network.simulator.compare_routes (unmodified)."""
    return simulator.compare_routes(original, alternative)


def find_direct_alternate(graph: nx.MultiGraph, origin_district: str, destination_district: str, exclude_road_id: str = None) -> dict:
    """
    Finds the direct parallel-corridor alternate between two districts, per
    the project's Alternate Route Rule: "An alternate route is valid ONLY
    if it has the exact same origin district AND destination district as
    the failed road."

    This is NOT a shortest-path search (a multi-hop detour through other
    districts does not qualify as an "alternate route" under this rule --
    it qualifies only as "destination is still reachable", a separate,
    already-tracked concept in the response). This function looks only at
    DIRECT edges between `origin_district` and `destination_district` in
    the given graph (an nx.MultiGraph can hold more than one parallel edge
    between the same two nodes -- exactly the R101/R117 case).

    Args:
        graph: usually the POST-FAILURE graph (so the failed road, already
            removed by simulate_road_failure, is naturally excluded).
        origin_district / destination_district: the failed road's own
            origin/destination district (district IDs = graph node IDs).
        exclude_road_id: extra safety net -- if the given graph somehow
            still contains this road_id (e.g. caller passed the original,
            pre-failure graph by mistake), it is still excluded here.

    Returns:
        dict with the surviving direct road's real data (road_id, name,
        distance) if a direct alternate exists, else None. Never invents
        a road_id -- only returns something that is an actual edge in the
        graph.
    """
    if not graph.has_edge(origin_district, destination_district):
        return None

    candidates = []
    for key, data in graph.get_edge_data(origin_district, destination_district).items():
        road_id = data.get("road_id", key)
        if exclude_road_id is not None and road_id == exclude_road_id:
            continue
        candidates.append(data)

    if not candidates:
        return None

    # Same tie-break NetworkX's own Dijkstra implicitly uses for parallel
    # edges: the lowest-weight ("distance") edge.
    best = min(candidates, key=lambda d: d["distance"])
    return {
        "road_id": best["road_id"],
        "name": best.get("name"),
        "distance_km": best.get("distance_km", best.get("distance")),
    }


def get_road_edge_data(graph: nx.MultiGraph, road_id: str) -> dict:
    """
    Finds the edge data dict for a given road_id in the graph, or None if
    not present. Read-only lookup -- does not modify the graph.
    """
    for u, v, key, data in graph.edges(keys=True, data=True):
        if data.get("road_id") == road_id:
            return data
    return None
