"""
build_assam_gis.py

Converts the Assam synthetic prototype Excel datasets (data/*.xlsx) into
GeoJSON files consumable by network/gis_loader.py and by the frontend.

    data/districts_assam_synthetic_v2.xlsx   -> gis/data/assam_districts.geojson
    data/roads_assam_synthetic_v3.xlsx       -> gis/data/assam_roads.geojson
    data/facilities_assam_synthetic_v2.xlsx  -> gis/data/assam_facilities.geojson
    data/landslides_assam_synthetic_v2.xlsx  -> gis/data/assam_landslides.geojson

ALL DATA IN THIS PIPELINE IS SYNTHETIC_DEMO.
Road geometry in particular is NOT a real surveyed alignment -- see the
"SYNTHETIC GEOMETRY" section below and gis/GIS_README.md for exactly what
that means and why.

Design decisions made explicit here (see GIS_README.md for the full
rationale of each):

1. Graph node strategy: for this phase, a road's `source_node` /
   `destination_node` (the values network/gis_loader.py builds the
   NetworkX graph from) are set equal to that road's `origin_district`
   / `destination_district`. District IDs ARE the graph nodes for now.
   This is a deliberate, documented phase-1 simplification, not a
   silent assumption -- see GIS_README.md "Node strategy".

2. Geometry strategy: since the source Excel data has no surveyed
   coordinates for road alignments, each road's LineString is built
   deterministically from its origin and destination district
   centroids (from assam_districts.geojson), plus one deterministic
   mid-point offset derived from a hash of the road_id (so the line
   isn't a perfectly straight, visually-identical segment for every
   road, while remaining reproducible run-to-run). This is a synthetic
   visual device, not a claim about real road alignment.

3. Self-loop road (R116, dima-hasao -> dima-hasao): a road whose
   origin and destination district are the same cannot be drawn as a
   line between two different district centroids. It is given a
   small deterministic out-and-back offset from its single district's
   centroid so it still satisfies the >=2-point LineString requirement.
   This is flagged again in the validation report -- it is a genuine
   data-modeling question for the team, not something this script
   resolves on its own.

Run:
    cd gis/scripts && python build_assam_gis.py

Deterministic: running this script twice produces byte-identical
GeoJSON (no use of unseeded randomness anywhere -- offsets are derived
from a stable hash of each record's own ID).
"""

import hashlib
import json
import math
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "gis" / "data"

DISTRICTS_XLSX = DATA_DIR / "districts_assam_synthetic_v2.xlsx"
ROADS_XLSX = DATA_DIR / "roads_assam_synthetic_v3.xlsx"
FACILITIES_XLSX = DATA_DIR / "facilities_assam_synthetic_v2.xlsx"
LANDSLIDES_XLSX = DATA_DIR / "landslides_assam_synthetic_v2.xlsx"


def _stable_unit_offset(seed: str) -> tuple:
    """
    Deterministically turns a string (e.g. a road_id) into a small,
    reproducible (dx, dy) offset in the range [-1, 1] for each axis.
    Uses a cryptographic hash (not random.seed) so the result never
    depends on process/platform-specific RNG state -- same seed always
    gives the same offset, forever.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # Take two independent 8-hex-digit chunks of the digest.
    a = int(digest[0:8], 16) / 0xFFFFFFFF  # in [0, 1]
    b = int(digest[8:16], 16) / 0xFFFFFFFF
    return (a * 2 - 1, b * 2 - 1)  # in [-1, 1]


def load_districts_df():
    df = pd.read_excel(DISTRICTS_XLSX)
    required = {"district_id", "district_name", "state", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"districts file missing required columns: {missing}")
    return df


def build_districts_geojson(districts_df: pd.DataFrame) -> dict:
    features = []
    for _, row in districts_df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])],
            },
            "properties": {
                "district_id": row["district_id"],
                "name": row["district_name"],
                "state": row["state"],
                "terrain_class": row.get("terrain_class"),
                "coordinate_note": row.get("coordinate_note"),
                "data_status": row.get("data_status"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _district_centroid_lookup(districts_df: pd.DataFrame) -> dict:
    """district_id -> (lon, lat)"""
    return {
        row["district_id"]: (float(row["longitude"]), float(row["latitude"]))
        for _, row in districts_df.iterrows()
    }


def _road_linestring(road_id: str, origin_lonlat: tuple, dest_lonlat: tuple, self_loop: bool) -> list:
    """
    Builds a deterministic LineString coordinate list ([lon, lat] pairs,
    >= 2 points) for one road. See module docstring for the rationale.
    """
    dx, dy = _stable_unit_offset(road_id)

    if self_loop:
        # Origin and destination district are the same point -- there is
        # nothing to draw a line "between". Give the road a small,
        # deterministic out-and-back spur from the shared centroid so it
        # still satisfies the >=2-distinct-point LineString requirement,
        # clearly a synthetic device (see GIS_README "Self-loop roads").
        lon, lat = origin_lonlat
        # ~0.05 deg offset (~5km at this latitude) scaled/directed by the
        # road_id hash so different self-loop roads (if any) don't collide.
        offset_lon = lon + 0.05 * dx
        offset_lat = lat + 0.05 * dy
        return [[lon, lat], [offset_lon, offset_lat], [lon, lat]]

    olon, olat = origin_lonlat
    dlon, dlat = dest_lonlat
    mid_lon = (olon + dlon) / 2 + 0.15 * dx * abs(dlon - olon or 0.1)
    mid_lat = (olat + dlat) / 2 + 0.15 * dy * abs(dlat - olat or 0.1)
    return [[olon, olat], [mid_lon, mid_lat], [dlon, dlat]]


def build_roads_geojson(roads_df: pd.DataFrame, districts_df: pd.DataFrame) -> dict:
    centroids = _district_centroid_lookup(districts_df)
    features = []
    for _, row in roads_df.iterrows():
        road_id = row["road_id"]
        origin = row["origin_district"]
        dest = row["destination_district"]

        if origin not in centroids:
            raise ValueError(f"{road_id}: origin_district '{origin}' not found in districts data")
        if dest not in centroids:
            raise ValueError(f"{road_id}: destination_district '{dest}' not found in districts data")

        self_loop = origin == dest
        coords = _road_linestring(road_id, centroids[origin], centroids[dest], self_loop)

        properties = {
            "road_id": road_id,
            # Phase-1 node strategy: graph nodes ARE district IDs.
            # See GIS_README.md "Node strategy" for why this is a
            # documented decision, not a silent assumption.
            "source_node": origin,
            "destination_node": dest,
            "distance_km": float(row["distance_km"]),
            "name": row.get("road_name"),
            "origin_district": origin,
            "destination_district": dest,
            "road_type": row.get("road_type"),
            "risk_level": row.get("risk_level"),
            "risk_score": None if pd.isna(row.get("risk_score")) else int(row.get("risk_score")),
            "official_ref": None if pd.isna(row.get("official_ref")) else row.get("official_ref"),
            "geometry_quality": row.get("geometry_quality"),
            "data_status": row.get("data_status"),
        }
        # Drop keys whose value is NaN/None from pandas so the GeoJSON
        # doesn't carry literal "NaN" (invalid JSON) anywhere.
        properties = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in properties.items()}

        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": properties,
        })
    return {"type": "FeatureCollection", "features": features}


def build_facilities_geojson(facilities_df: pd.DataFrame) -> dict:
    features = []
    for _, row in facilities_df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])],
            },
            "properties": {
                "facility_id": row["facility_id"],
                "name": row["name"],
                "type": row["type"],
                "district": row["district"],
                "critical": bool(row["critical"]),
                "source": row.get("source"),
                "data_quality_note": row.get("data_quality_note"),
                "data_status": row.get("data_status"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def build_landslides_geojson(landslides_df: pd.DataFrame) -> dict:
    features = []
    for _, row in landslides_df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])],
            },
            "properties": {
                "landslide_id": row["landslide_id"],
                "date": str(row["date"]),
                "district": row["district"],
                "hazard_type": row.get("hazard_type"),
                "severity": row.get("severity"),
                "road_related": row.get("road_related"),
                "source": row.get("source"),
                "data_quality_note": row.get("data_quality_note"),
                "data_status": row.get("data_status"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _write_geojson(obj: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys + fixed separators -> byte-identical output across runs.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def main():
    districts_df = load_districts_df()
    roads_df = pd.read_excel(ROADS_XLSX)
    facilities_df = pd.read_excel(FACILITIES_XLSX)
    landslides_df = pd.read_excel(LANDSLIDES_XLSX)

    districts_geojson = build_districts_geojson(districts_df)
    roads_geojson = build_roads_geojson(roads_df, districts_df)
    facilities_geojson = build_facilities_geojson(facilities_df)
    landslides_geojson = build_landslides_geojson(landslides_df)

    _write_geojson(districts_geojson, OUT_DIR / "assam_districts.geojson")
    _write_geojson(roads_geojson, OUT_DIR / "assam_roads.geojson")
    _write_geojson(facilities_geojson, OUT_DIR / "assam_facilities.geojson")
    _write_geojson(landslides_geojson, OUT_DIR / "assam_landslides.geojson")

    print(f"Wrote {len(districts_geojson['features'])} districts -> {OUT_DIR / 'assam_districts.geojson'}")
    print(f"Wrote {len(roads_geojson['features'])} roads -> {OUT_DIR / 'assam_roads.geojson'}")
    print(f"Wrote {len(facilities_geojson['features'])} facilities -> {OUT_DIR / 'assam_facilities.geojson'}")
    print(f"Wrote {len(landslides_geojson['features'])} landslides -> {OUT_DIR / 'assam_landslides.geojson'}")


if __name__ == "__main__":
    main()
