"""
gis_data.py

Loads the project's actual GIS/data sources for the read-only GET
endpoints (/districts, /roads, /facilities). This is deliberately
separate from network_client.py: network.gis_loader.build_graph_from_geojson()
only keeps the fields the NetworkX graph itself needs (road_id, distance,
name, state, road_type, status) -- it intentionally drops
origin_district/destination_district/risk_level/risk_score/etc. from the
edge data (documented in gis/GIS_README.md). Those extra fields are still
present in the raw GeoJSON files, so the GET endpoints read the GeoJSON
files directly rather than trying to recover dropped fields from the graph.

Does NOT duplicate ML's risk-scoring formula: road risk is obtained by
calling ml_client.get_road_risk() (which calls the real, unmodified
ml.road_risk_scoring.get_road_risk()) for every road.

Coordinate convention: gis/data/*.geojson is standard GeoJSON
[longitude, latitude]. The team data contract (per the project brief)
uses [latitude, longitude] for `path`/`coords`. This file performs that
conversion in one place.
"""

from . import path_setup  # noqa: F401

import json
import os
import threading

from . import ml_client

DISTRICTS_GEOJSON = os.path.join(path_setup.GIS_DATA_DIR, "assam_districts.geojson")
ROADS_GEOJSON = os.path.join(path_setup.GIS_DATA_DIR, "assam_roads.geojson")
FACILITIES_GEOJSON = os.path.join(path_setup.GIS_DATA_DIR, "assam_facilities.geojson")

_lock = threading.RLock()  # RLock: _connectivity_status_by_district() calls
# _roads_raw()/valid_district_ids() while already holding this lock
_cache = {}


def _load_geojson(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _lonlat_to_latlng(coordinates):
    """[lon, lat] -> [lat, lng], recursively for LineString coordinate lists too."""
    if not coordinates:
        return coordinates
    if isinstance(coordinates[0], (int, float)):
        lon, lat = coordinates
        return [lat, lon]
    return [_lonlat_to_latlng(point) for point in coordinates]


def _districts_raw() -> list:
    if "districts" not in _cache:
        with _lock:
            if "districts" not in _cache:
                _cache["districts"] = _load_geojson(DISTRICTS_GEOJSON)["features"]
    return _cache["districts"]


def _roads_raw() -> list:
    if "roads" not in _cache:
        with _lock:
            if "roads" not in _cache:
                _cache["roads"] = _load_geojson(ROADS_GEOJSON)["features"]
    return _cache["roads"]


def _facilities_raw() -> list:
    if "facilities" not in _cache:
        with _lock:
            if "facilities" not in _cache:
                _cache["facilities"] = _load_geojson(FACILITIES_GEOJSON)["features"]
    return _cache["facilities"]


def valid_district_ids() -> set:
    return {f["properties"]["district_id"] for f in _districts_raw()}


def valid_road_ids() -> set:
    return {f["properties"]["road_id"] for f in _roads_raw()}


def get_road_by_id(road_id: str) -> dict:
    """Returns the raw GeoJSON properties dict for a road, or None."""
    for f in _roads_raw():
        if f["properties"]["road_id"] == road_id:
            return f["properties"]
    return None


# -----------------------------------------------------------------
# Connectivity status (used only by GET /districts)
# -----------------------------------------------------------------
# Derived, documented heuristic (mirrors the same rule frontend/src/data/
# mockDistricts.js documents for its own hand-authored data) -- computed
# here from REAL road + REAL live ML risk data, never fabricated:
#
#   For every pair of districts a road (or roads) directly connects:
#     - if the lowest-risk road in that pair is riskLevel LOW  -> CONNECTED
#     - if the lowest-risk road is MEDIUM/HIGH but a second (parallel)
#       road exists for the same pair                          -> AT_RISK
#     - if the lowest-risk road is MEDIUM/HIGH and it is the ONLY
#       road for that pair (single point of failure)            -> VULNERABLE
#   A district's overall status is the WORST status across all pairs it
#   participates in. A district with no roads at all is VULNERABLE
#   (fully disconnected). Self-loop roads (origin == destination, e.g.
#   R116) don't connect the district to any other district, so they are
#   excluded from this computation.
#
# This is a prototype planning heuristic, not an official classification
# -- same caveat the rest of this project's synthetic data carries.
def _connectivity_status_by_district() -> dict:
    if "connectivity" in _cache:
        return _cache["connectivity"]

    with _lock:
        if "connectivity" in _cache:
            return _cache["connectivity"]

        pair_groups = {}  # frozenset({district_a, district_b}) -> [road_id, ...]
        for f in _roads_raw():
            p = f["properties"]
            origin, dest = p["origin_district"], p["destination_district"]
            if origin == dest:
                continue  # self-loop road, doesn't connect two districts
            key = frozenset((origin, dest))
            pair_groups.setdefault(key, []).append(p["road_id"])

        status_rank = {"CONNECTED": 0, "AT_RISK": 1, "VULNERABLE": 2}
        district_status = {d: "VULNERABLE" for d in valid_district_ids()}  # default: no roads at all

        for pair, road_ids in pair_groups.items():
            risks = [(rid, ml_client.get_road_risk(rid)) for rid in road_ids]
            best_road_id, best_risk = min(risks, key=lambda item: item[1]["riskScore"])
            has_alternate = len(road_ids) > 1

            if best_risk["riskLevel"] == "LOW":
                pair_status = "CONNECTED"
            elif has_alternate:
                pair_status = "AT_RISK"
            else:
                pair_status = "VULNERABLE"

            for district in pair:
                current = district_status.get(district, "VULNERABLE")
                if status_rank[pair_status] > status_rank[current]:
                    district_status[district] = pair_status

        _cache["connectivity"] = district_status
        return district_status


# -----------------------------------------------------------------
# Public contract-shaped getters
# -----------------------------------------------------------------
def list_districts() -> list:
    """
    Returns districts in the team contract shape. Only fields that exist
    in the real dataset are included -- `hqTown`/`population` from the
    old frontend mock data are NOT fabricated here (see backend/README.md
    "Known gaps vs. old mock schema").
    """
    connectivity = _connectivity_status_by_district()
    result = []
    for f in _districts_raw():
        p = f["properties"]
        result.append({
            "id": p["district_id"],
            "name": p["name"],
            "state": p["state"],
            "terrainClass": p.get("terrain_class"),
            "coords": _lonlat_to_latlng(f["geometry"]["coordinates"]),
            "connectivityStatus": connectivity.get(p["district_id"], "VULNERABLE"),
            "dataStatus": p.get("data_status"),
        })
    return result


def list_roads() -> list:
    """
    Returns roads in the team contract shape. riskScore/riskLevel are
    obtained by CALLING ml_client.get_road_risk() (the live ML formula)
    for every road -- not read from the GeoJSON's static reference
    risk_score/risk_level fields, and not recomputed here.
    """
    result = []
    for f in _roads_raw():
        p = f["properties"]
        risk = ml_client.get_road_risk(p["road_id"])
        result.append({
            "id": p["road_id"],
            "name": p.get("name"),
            "originDistrict": p["origin_district"],
            "destinationDistrict": p["destination_district"],
            "distanceKm": p["distance_km"],
            "roadType": p.get("road_type"),
            "officialRef": p.get("official_ref"),
            "riskScore": risk["riskScore"],
            "riskLevel": risk["riskLevel"],
            # No road in the current dataset is marked failed/blocked at
            # rest -- every road in gis/data/assam_roads.geojson is a live
            # edge in the base graph. "status" reflects that baseline;
            # POST /simulate-failure is what models a road going down.
            "status": "OPERATIONAL",
            "path": _lonlat_to_latlng(f["geometry"]["coordinates"]),
            "dataStatus": p.get("data_status"),
            "geometryQuality": p.get("geometry_quality"),
        })
    return result


def list_facilities() -> list:
    """Returns facilities in the team contract shape."""
    result = []
    for f in _facilities_raw():
        p = f["properties"]
        result.append({
            "id": p["facility_id"],
            "name": p["name"],
            "type": p["type"],
            "district": p["district"],
            "coords": _lonlat_to_latlng(f["geometry"]["coordinates"]),
            "critical": bool(p["critical"]),
            "dataStatus": p.get("data_status"),
        })
    return result
