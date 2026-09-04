"""
test_gis_validation.py

Validates the generated Assam GIS GeoJSON files (gis/data/*.geojson)
and confirms they load correctly through the existing, unmodified
network/gis_loader.py.

Run:
    cd gis/tests && python test_gis_validation.py

This does not modify graph_builder.py, simulator.py, impact.py, or
gis_loader.py -- it only imports and exercises them, exactly like
network/test_gis_loader.py does for its own embedded fixture.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GIS_DATA_DIR = REPO_ROOT / "gis" / "data"
sys.path.insert(0, str(REPO_ROOT / "network"))

from gis_loader import build_graph_from_geojson, GISValidationError  # noqa: E402
from simulator import find_route, simulate_road_failure  # noqa: E402


def _load(name):
    with open(GIS_DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def test_1_geojson_is_valid_feature_collections():
    print("\n--- Test 1: all four files are valid FeatureCollections ---")
    for name in ("assam_roads.geojson", "assam_districts.geojson",
                 "assam_facilities.geojson", "assam_landslides.geojson"):
        data = _load(name)
        assert data["type"] == "FeatureCollection", f"{name}: not a FeatureCollection"
        assert len(data["features"]) > 0, f"{name}: no features"
    print("OK")


def test_2_every_road_is_linestring_with_2plus_points():
    print("\n--- Test 2/3: every road is a LineString with >=2 coordinates ---")
    roads = _load("assam_roads.geojson")
    for feature in roads["features"]:
        rid = feature["properties"]["road_id"]
        geom = feature["geometry"]
        assert geom["type"] == "LineString", f"{rid}: geometry is not LineString"
        assert len(geom["coordinates"]) >= 2, f"{rid}: fewer than 2 coordinate points"
    print("OK")


def test_4_coordinates_are_valid_lon_lat():
    print("\n--- Test 4: coordinates are valid [lon, lat] ---")
    roads = _load("assam_roads.geojson")
    for feature in roads["features"]:
        rid = feature["properties"]["road_id"]
        for lon, lat in feature["geometry"]["coordinates"]:
            assert -180 <= lon <= 180, f"{rid}: longitude {lon} out of range"
            assert -90 <= lat <= 90, f"{rid}: latitude {lat} out of range"
            # Assam is roughly lon 89-97, lat 24-28 -- sanity band, not a
            # hard spec requirement, but catches gross swaps immediately.
            assert 85 <= lon <= 100, f"{rid}: longitude {lon} outside plausible Assam range"
            assert 22 <= lat <= 30, f"{rid}: latitude {lat} outside plausible Assam range"
    print("OK")


def test_5_road_id_unique():
    print("\n--- Test 5: road_id is unique ---")
    roads = _load("assam_roads.geojson")
    ids = [f["properties"]["road_id"] for f in roads["features"]]
    assert len(ids) == len(set(ids)), "duplicate road_id found"
    print(f"OK ({len(ids)} unique road IDs)")


def test_6_distance_km_positive():
    print("\n--- Test 6: distance_km > 0 for every road ---")
    roads = _load("assam_roads.geojson")
    for feature in roads["features"]:
        rid = feature["properties"]["road_id"]
        dist = feature["properties"]["distance_km"]
        assert isinstance(dist, (int, float)) and dist > 0, f"{rid}: distance_km must be > 0, got {dist!r}"
    print("OK")


def test_7_8_source_destination_non_empty():
    print("\n--- Test 7/8: source_node / destination_node non-empty ---")
    roads = _load("assam_roads.geojson")
    for feature in roads["features"]:
        rid = feature["properties"]["road_id"]
        assert str(feature["properties"]["source_node"]).strip(), f"{rid}: source_node empty"
        assert str(feature["properties"]["destination_node"]).strip(), f"{rid}: destination_node empty"
    print("OK")


def test_9_district_ids_referenced_exist():
    print("\n--- Test 9: every district referenced by a road exists in assam_districts.geojson ---")
    roads = _load("assam_roads.geojson")
    districts = _load("assam_districts.geojson")
    known_ids = {f["properties"]["district_id"] for f in districts["features"]}
    for feature in roads["features"]:
        rid = feature["properties"]["road_id"]
        origin = feature["properties"]["origin_district"]
        dest = feature["properties"]["destination_district"]
        assert origin in known_ids, f"{rid}: origin_district '{origin}' not a known district"
        assert dest in known_ids, f"{rid}: destination_district '{dest}' not a known district"
    print(f"OK ({len(known_ids)} known districts)")


def test_10_11_12_r101_r117_alternate_pair():
    print("\n--- Test 10/11/12: R101 and R117 form a valid alternate pair ---")
    roads = _load("assam_roads.geojson")
    by_id = {f["properties"]["road_id"]: f for f in roads["features"]}
    r101, r117 = by_id["R101"], by_id["R117"]

    # 10. identical origin/destination district
    assert r101["properties"]["origin_district"] == r117["properties"]["origin_district"]
    assert r101["properties"]["destination_district"] == r117["properties"]["destination_district"]

    # 11. different geometries
    assert r101["geometry"]["coordinates"] != r117["geometry"]["coordinates"], \
        "R101 and R117 must not share identical geometry"

    # 12. both positive distances
    assert r101["properties"]["distance_km"] > 0
    assert r117["properties"]["distance_km"] > 0

    print(f"OK -- both {r101['properties']['origin_district']} -> {r101['properties']['destination_district']}, "
          f"distances {r101['properties']['distance_km']}km / {r117['properties']['distance_km']}km")


def test_13_facilities_have_valid_coordinates():
    print("\n--- Test 13: facilities have valid coordinates ---")
    facilities = _load("assam_facilities.geojson")
    for feature in facilities["features"]:
        fid = feature["properties"]["facility_id"]
        lon, lat = feature["geometry"]["coordinates"]
        assert -180 <= lon <= 180 and -90 <= lat <= 90, f"{fid}: invalid coordinates"
    print(f"OK ({len(facilities['features'])} facilities)")


def test_14_landslides_have_valid_coordinates():
    print("\n--- Test 14: landslide points have valid coordinates ---")
    landslides = _load("assam_landslides.geojson")
    for feature in landslides["features"]:
        lid = feature["properties"]["landslide_id"]
        lon, lat = feature["geometry"]["coordinates"]
        assert -180 <= lon <= 180 and -90 <= lat <= 90, f"{lid}: invalid coordinates"
    print(f"OK ({len(landslides['features'])} landslide records)")


def test_15_gis_loader_accepts_generated_roads():
    print("\n--- Test 15: network/gis_loader.py successfully loads assam_roads.geojson ---")
    roads = _load("assam_roads.geojson")
    graph = build_graph_from_geojson(roads)  # raises GISValidationError on failure
    print(f"OK -- graph has {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    return graph


def test_16_17_18_multigraph_parallel_behavior():
    print("\n--- Test 16/17/18: MultiGraph holds R101 + R117; failing one leaves the other ---")
    roads = _load("assam_roads.geojson")
    graph = build_graph_from_geojson(roads)

    def has_road(g, road_id):
        return any(data.get("road_id") == road_id for _, _, data in g.edges(data=True))

    # 16. both present at once
    assert has_road(graph, "R101")
    assert has_road(graph, "R117")

    # 17. failing R101 leaves R117
    after_r101_fails = simulate_road_failure(graph, "R101")
    assert not has_road(after_r101_fails, "R101")
    assert has_road(after_r101_fails, "R117")

    # 18. failing R117 (on the original graph) leaves R101
    after_r117_fails = simulate_road_failure(graph, "R117")
    assert has_road(after_r117_fails, "R101")
    assert not has_road(after_r117_fails, "R117")

    # Bonus: routing from kamrup-metropolitan to dima-hasao still works
    # after R101 fails (via R117), confirming find_route/MultiGraph
    # integration end-to-end, not just edge presence.
    route = find_route(after_r101_fails, "kamrup-metropolitan", "dima-hasao")
    assert route["reachable"], "expected dima-hasao still reachable via R117 after R101 fails"
    print(f"OK -- after R101 fails, route still reachable via R117 (cost={route['cost']})")


def test_19_self_loop_road_flagged():
    print("\n--- Test 19 (extra, not in the requested 18): self-loop road R116 is real but unusual ---")
    roads = _load("assam_roads.geojson")
    by_id = {f["properties"]["road_id"]: f for f in roads["features"]}
    r116 = by_id["R116"]
    is_self_loop = r116["properties"]["origin_district"] == r116["properties"]["destination_district"]
    if is_self_loop:
        print("FLAGGED (not failed): R116 has origin_district == destination_district "
              "('dima-hasao'). It loads fine as a NetworkX self-loop edge, but a self-loop "
              "can never appear on a shortest path between two DIFFERENT nodes, so routing/"
              "impact analysis will never actually route traffic over it. See GIS_README.md "
              "'Self-loop roads' -- this needs a team decision, this test only documents it.")
    else:
        print("R116 is no longer a self-loop -- source data changed since this test was written.")


if __name__ == "__main__":
    test_1_geojson_is_valid_feature_collections()
    test_2_every_road_is_linestring_with_2plus_points()
    test_4_coordinates_are_valid_lon_lat()
    test_5_road_id_unique()
    test_6_distance_km_positive()
    test_7_8_source_destination_non_empty()
    test_9_district_ids_referenced_exist()
    test_10_11_12_r101_r117_alternate_pair()
    test_13_facilities_have_valid_coordinates()
    test_14_landslides_have_valid_coordinates()
    test_15_gis_loader_accepts_generated_roads()
    test_16_17_18_multigraph_parallel_behavior()
    test_19_self_loop_road_flagged()
    print("\nAll GIS validation checks passed.")
