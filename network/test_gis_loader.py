"""
test_gis_loader.py

Run this file directly:

    python test_gis_loader.py

Proves the full chain:

    GeoJSON --> gis_loader --> networkx.Graph --> simulator.find_route()
             --> simulator.simulate_road_failure() --> impact.calculate_impact()

using a tiny embedded test fixture (NOT real GIS data -- see the
project doc, Section 9 / your instructions: real data comes later).

This file does not modify graph_builder.py, simulator.py, or impact.py.
It only imports and reuses them.
"""

from gis_loader import build_graph_from_geojson, GISValidationError
from simulator import find_route, simulate_road_failure, compare_routes
from impact import calculate_impact


def _road_feature(road_id, source, destination, distance_km, **extra_props):
    """Small helper so the fixture below stays readable."""
    # Fake but plausible LineString: two points, valid [lon, lat] order.
    # Coordinates are arbitrary test values, not real NER geography.
    coordinates = [[90.0, 25.0], [90.1, 25.1]]
    properties = {
        "road_id": road_id,
        "source_node": source,
        "destination_node": destination,
        "distance_km": distance_km,
    }
    properties.update(extra_props)
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "LineString", "coordinates": coordinates},
    }


# ---------------------------------------------------------------------
# Tiny test fixture: 4 roads, same shape as graph_builder.py's network
# (a diamond: N1-N2-N3 and N1-N4-N3), so results are easy to compare.
#
#         N2
#        /  \
#      N1    N3
#        \  /
#         N4
# ---------------------------------------------------------------------
VALID_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        _road_feature("R101", "N1", "N2", 10, name="Test Road 1", status="active"),
        _road_feature("R102", "N2", "N3", 10, name="Test Road 2", status="active"),
        _road_feature("R103", "N1", "N4", 8, name="Test Road 3", status="active"),
        _road_feature("R104", "N4", "N3", 8, name="Test Road 4", status="active"),
    ],
}


def test_loader_builds_valid_graph():
    print("\n--- Test: loader builds a graph from valid GeoJSON ---")
    graph = build_graph_from_geojson(VALID_FIXTURE)

    assert set(graph.nodes) == {"N1", "N2", "N3", "N4"}
    assert graph.number_of_edges() == 4

    # road_id and distance must be present for existing code to work.
    # get_edge_data on a MultiGraph is keyed by edge key (road_id here),
    # so this now needs the key to reach the flat attribute dict --
    # graph.get_edge_data(u, v) alone would return {road_id: {...}}.
    edge_data = graph.get_edge_data("N1", "N2", "R101")
    assert edge_data["road_id"] == "R101"
    assert edge_data["distance"] == 10
    assert edge_data["distance_km"] == 10
    assert edge_data["name"] == "Test Road 1"

    print("Graph nodes:", list(graph.nodes))
    print("Graph built successfully with road_id + distance preserved.")


def test_loader_rejects_missing_field():
    print("\n--- Test: loader rejects a road missing distance_km ---")
    bad_feature = _road_feature("R201", "N1", "N2", 10)
    del bad_feature["properties"]["distance_km"]
    bad_fixture = {"type": "FeatureCollection", "features": [bad_feature]}

    try:
        build_graph_from_geojson(bad_fixture)
        raise AssertionError("Expected GISValidationError, but none was raised")
    except GISValidationError as e:
        print("Correctly rejected:", e)


def test_loader_rejects_duplicate_road_id():
    print("\n--- Test: loader rejects duplicate road_id ---")
    fixture = {
        "type": "FeatureCollection",
        "features": [
            _road_feature("R301", "N1", "N2", 5),
            _road_feature("R301", "N2", "N3", 5),  # duplicate id
        ],
    }
    try:
        build_graph_from_geojson(fixture)
        raise AssertionError("Expected GISValidationError, but none was raised")
    except GISValidationError as e:
        print("Correctly rejected:", e)


def test_loader_rejects_bad_coordinate_order():
    print("\n--- Test: loader rejects swapped lat/lon coordinates ---")
    feature = _road_feature("R401", "N1", "N2", 5)
    # Latitude values (~25) put in the longitude slot is fine (25 is
    # valid longitude too), so instead force an out-of-range value
    # that can only happen if someone swapped lat/lon by mistake.
    feature["geometry"]["coordinates"] = [[95.0, 25.0], [200.0, 25.0]]
    fixture = {"type": "FeatureCollection", "features": [feature]}

    try:
        build_graph_from_geojson(fixture)
        raise AssertionError("Expected GISValidationError, but none was raised")
    except GISValidationError as e:
        print("Correctly rejected:", e)


def test_loader_rejects_non_positive_distance():
    print("\n--- Test: loader rejects zero/negative distance_km ---")
    feature = _road_feature("R501", "N1", "N2", -5)
    fixture = {"type": "FeatureCollection", "features": [feature]}

    try:
        build_graph_from_geojson(fixture)
        raise AssertionError("Expected GISValidationError, but none was raised")
    except GISValidationError as e:
        print("Correctly rejected:", e)


def test_end_to_end_with_existing_simulator_and_impact():
    print("\n--- Test: full chain GeoJSON -> graph -> routing -> failure -> impact ---")
    graph = build_graph_from_geojson(VALID_FIXTURE)

    # Routing (existing simulator.py, untouched)
    original = find_route(graph, "N1", "N3")
    print("Original route N1->N3:", original)
    assert original["reachable"] is True
    assert original["cost"] == 16  # N1-N4-N3 = 8+8, shorter than N1-N2-N3 = 20

    # Road failure (existing simulator.py, untouched)
    failed_graph = simulate_road_failure(graph, "R104")  # N4-N3 fails
    alternative = find_route(failed_graph, "N1", "N3")
    print("Route after R104 fails:", alternative)
    assert alternative["reachable"] is True
    assert alternative["cost"] == 20  # forced via N1-N2-N3

    comparison = compare_routes(original, alternative)
    print("Comparison:", comparison)
    assert comparison["cost_increase"] == 4

    # Original graph untouched
    still_has_r104 = any(
        data.get("road_id") == "R104" for _, _, data in graph.edges(data=True)
    )
    assert still_has_r104, "Original graph should not be modified by simulate_road_failure"

    # Impact analysis (existing impact.py, untouched) using GIS-loaded nodes
    critical_locations = {"warehouse_1": "N1", "village_1": "N4", "hospital_1": "N3"}
    impact_result = calculate_impact(graph, road_id="R104", origin="N1", critical_locations=critical_locations)
    print("Impact result:", impact_result)
    assert "hospital_1" in impact_result["affected_locations"]

    print("Full chain (GeoJSON -> graph -> routing -> failure -> impact) works.")


if __name__ == "__main__":
    test_loader_builds_valid_graph()
    test_loader_rejects_missing_field()
    test_loader_rejects_duplicate_road_id()
    test_loader_rejects_bad_coordinate_order()
    test_loader_rejects_non_positive_distance()
    test_end_to_end_with_existing_simulator_and_impact()
    print("\nAll GIS loader tests passed.")
