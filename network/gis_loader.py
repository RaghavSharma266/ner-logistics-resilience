"""
gis_loader.py

Adapter between GIS road data (GeoJSON) and our existing NetworkX-based
network module (graph_builder.py / simulator.py / impact.py).

    GeoJSON FeatureCollection
            |
            v
      gis_loader.py   <-- THIS FILE
            |
            v
      networkx.Graph  (same shape build_network() produces)
            |
            v
      simulator.find_route() / simulate_road_failure()   <-- UNCHANGED
            |
            v
      impact.calculate_impact()                           <-- UNCHANGED

This file does NOT reimplement routing, failure simulation, or impact
analysis. It only turns GeoJSON into a graph those existing functions
already know how to use.

Uses nx.MultiGraph (matching graph_builder.py) because the Team Data
Contract allows multiple roads between the same source/destination
pair. Each road is keyed by its own road_id, so parallel roads from
GIS data coexist correctly instead of overwriting one another.

--------------------------------------------------------------------
Minimum required road contract (per Feature['properties'] unless noted):

    road_id             string, unique across the whole file
    source_node         string, non-empty
    destination_node    string, non-empty
    distance_km         number, > 0
    geometry            GeoJSON geometry, type "LineString"
                         (Feature['geometry'], not in properties)

Optional properties:
    name, state, road_type, status

Coordinates inside "geometry" must be in GeoJSON's standard
[longitude, latitude] order.
--------------------------------------------------------------------

Why 'distance' AND 'distance_km' both end up on each edge:
simulator.py's find_route() hardcodes weight="distance". Rather than
changing that already-tested file, this loader sets 'distance' equal
to 'distance_km' so existing routing works unmodified, while also
keeping 'distance_km' as the explicit, GIS-native field name.
"""

import json
import networkx as nx


class GISValidationError(Exception):
    """Raised when the input GeoJSON does not satisfy the road contract."""
    pass


REQUIRED_PROPERTY_FIELDS = ["road_id", "source_node", "destination_node", "distance_km"]


def _validate_coordinates(coordinates, road_id: str, errors: list):
    """
    Sanity-checks that coordinates look like [longitude, latitude] pairs.
    This can't prove the order is correct, but it catches the common
    mistake of swapping lat/lon (latitude can't exceed 90).
    """
    if not coordinates or len(coordinates) < 2:
        errors.append(f"{road_id}: geometry must have at least 2 coordinate points")
        return

    for point in coordinates:
        if len(point) != 2:
            errors.append(f"{road_id}: each coordinate must be [longitude, latitude]")
            continue
        lon, lat = point
        if not (-180 <= lon <= 180):
            errors.append(
                f"{road_id}: longitude {lon} out of range -- "
                f"check coordinates are [longitude, latitude], not [latitude, longitude]"
            )
        if not (-90 <= lat <= 90):
            errors.append(
                f"{road_id}: latitude {lat} out of range -- "
                f"check coordinates are [longitude, latitude], not [latitude, longitude]"
            )


def _validate_feature(feature: dict, seen_road_ids: set, errors: list):
    """
    Validates a single GeoJSON Feature against the road contract.
    Appends any problems found to `errors` (does not raise directly,
    so we can report every problem in the file at once).
    """
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    # 1. Required fields present
    missing = [f for f in REQUIRED_PROPERTY_FIELDS if f not in props or props[f] in (None, "")]
    road_id = props.get("road_id", "<missing road_id>")
    if missing:
        errors.append(f"{road_id}: missing required field(s): {', '.join(missing)}")
        # Can't safely validate further without road_id/distance_km etc.
        return

    # 2. road_id uniqueness
    if road_id in seen_road_ids:
        errors.append(f"{road_id}: duplicate road_id")
    seen_road_ids.add(road_id)

    # 3. source_node / destination_node present (already covered by
    #    missing-field check above, but guard against blank strings)
    if not str(props["source_node"]).strip():
        errors.append(f"{road_id}: source_node is empty")
    if not str(props["destination_node"]).strip():
        errors.append(f"{road_id}: destination_node is empty")

    # 4. distance_km positive
    distance_km = props["distance_km"]
    if not isinstance(distance_km, (int, float)) or distance_km <= 0:
        errors.append(f"{road_id}: distance_km must be a positive number, got {distance_km!r}")

    # 5. geometry type must be LineString
    if geometry.get("type") != "LineString":
        errors.append(f"{road_id}: geometry.type must be 'LineString', got {geometry.get('type')!r}")
    else:
        # 6. coordinate order sanity check
        _validate_coordinates(geometry.get("coordinates"), road_id, errors)


def validate_feature_collection(geojson: dict) -> None:
    """
    Validates an entire GeoJSON FeatureCollection against the road
    contract. Raises GISValidationError listing every problem found,
    or returns None if the file is valid.
    """
    if geojson.get("type") != "FeatureCollection":
        raise GISValidationError("Input must be a GeoJSON FeatureCollection")

    features = geojson.get("features", [])
    if not features:
        raise GISValidationError("FeatureCollection has no features")

    errors = []
    seen_road_ids = set()
    for feature in features:
        _validate_feature(feature, seen_road_ids, errors)

    if errors:
        raise GISValidationError(
            f"{len(errors)} problem(s) found in GeoJSON:\n  " + "\n  ".join(errors)
        )


def build_graph_from_geojson(geojson: dict) -> nx.MultiGraph:
    """
    Validates and converts a GeoJSON FeatureCollection into an
    nx.MultiGraph compatible with the existing network module.

    Each edge is keyed by its road_id (so parallel roads between the
    same two nodes coexist) and carries:
        road_id, distance, distance_km, geometry,
        and any optional fields present (name, state, road_type, status).

    Raises GISValidationError if the input doesn't satisfy the road
    contract.
    """
    validate_feature_collection(geojson)

    graph = nx.MultiGraph()

    for feature in geojson["features"]:
        props = feature["properties"]
        geometry = feature["geometry"]

        road_id = props["road_id"]
        source = props["source_node"]
        destination = props["destination_node"]
        distance_km = props["distance_km"]

        edge_attrs = {
            "road_id": road_id,
            "distance": distance_km,       # matches simulator.py's weight="distance"
            "distance_km": distance_km,    # explicit GIS-native field
            "geometry": geometry.get("coordinates"),
        }

        # Preserve optional fields only if present, rather than
        # writing "None" into every edge.
        for optional_field in ("name", "state", "road_type", "status"):
            if optional_field in props:
                edge_attrs[optional_field] = props[optional_field]

        graph.add_edge(source, destination, key=road_id, **edge_attrs)

    return graph


def load_geojson_file(path: str) -> nx.Graph:
    """
    Reads a GeoJSON file from disk and builds a graph from it.
    This is the function the real GIS team's roads.geojson will
    eventually go through.
    """
    with open(path, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    return build_graph_from_geojson(geojson)
