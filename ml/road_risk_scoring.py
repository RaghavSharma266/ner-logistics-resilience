"""
Road Risk Scoring — AI/ML Module (Member 4)
--------------------------------------------
Purpose: Score road segments as HIGH / MEDIUM / LOW risk using a simple,
explainable rule-based weighted formula. This is NOT a trained ML model —
it's a transparent scoring system built on the project's CURRENT SYNTHETIC
ASSAM DATA (SYNTHETIC_DEMO, not official observations). See ml/README.md
for the full methodology writeup.

Output feeds directly into the Network module's failure simulation.

DATA SOURCES (all under data/, loaded at import time):
    roads_assam_synthetic_v3.xlsx      -- per-road attributes (primary table)
    terrain_assam_synthetic_v3.xlsx    -- per-road terrain profile (slope/elevation)
    rainfall_assam_synthetic_v2.xlsx   -- per-district rainfall observations
    landslides_assam_synthetic_v2.xlsx -- individual landslide/hazard events

TARGET LEAKAGE:
    roads_assam_synthetic_v3.xlsx already contains its own 'risk_score' and
    'risk_level' columns. Those are NEVER used as inputs to compute_risk_score().
    They are only exposed separately as reference_risk_score / reference_risk_level
    on each road record, for optional comparison/validation -- never as predictors.
"""

import os
import pandas as pd

# -----------------------------------------------------------------
# STEP 0: File locations (resolved relative to this file, not cwd)
# -----------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "data"))

ROADS_FILE = os.path.join(DATA_DIR, "roads_assam_synthetic_v3.xlsx")
TERRAIN_FILE = os.path.join(DATA_DIR, "terrain_assam_synthetic_v3.xlsx")
RAINFALL_FILE = os.path.join(DATA_DIR, "rainfall_assam_synthetic_v2.xlsx")
LANDSLIDES_FILE = os.path.join(DATA_DIR, "landslides_assam_synthetic_v2.xlsx")

SEVERITY_WEIGHTS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


# -----------------------------------------------------------------
# STEP 1: Dataset loading + district-level aggregation helpers
# -----------------------------------------------------------------
def _load_raw_datasets():
    """Loads the four ML-relevant synthetic datasets. Raises a clear
    error if a file is missing rather than silently falling back to
    mock data."""
    missing = [p for p in (ROADS_FILE, TERRAIN_FILE, RAINFALL_FILE, LANDSLIDES_FILE) if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            "Missing required synthetic dataset(s): " + ", ".join(missing) +
            ". road_risk_scoring.py requires the project's synthetic Assam "
            "datasets under data/ -- it does not fall back to mock data."
        )
    roads_df = pd.read_excel(ROADS_FILE)
    terrain_df = pd.read_excel(TERRAIN_FILE)
    rainfall_df = pd.read_excel(RAINFALL_FILE)
    landslides_df = pd.read_excel(LANDSLIDES_FILE)
    return roads_df, terrain_df, rainfall_df, landslides_df


def _aggregate_rainfall_anomaly(rainfall_df):
    """
    Per-district average rainfall departure_percent (how far actual
    rainfall deviates from the district's normal rainfall). Returns
    (district -> value dict, dataset-wide mean fallback).
    Positive departure = wetter than normal (higher hazard signal);
    negative = drier than normal.
    """
    by_district = rainfall_df.groupby("district")["departure_percent"].mean()
    return by_district.to_dict(), float(rainfall_df["departure_percent"].mean())


def _aggregate_landslide_hazard(landslides_df):
    """
    Per-district severity-weighted landslide/hazard event total
    (LOW=1, MEDIUM=2, HIGH=3, summed per district). This uses ALL
    recorded events for a district, not just ones flagged
    road_related == 'YES', because most records carry 'UNKNOWN' for
    that field in this synthetic set -- filtering to 'YES' only would
    leave most districts with near-zero signal. Documented as a
    known prototype limitation in ml/README.md.
    Returns (district -> value dict, dataset-wide mean fallback).
    """
    sev_num = landslides_df["severity"].map(SEVERITY_WEIGHTS)
    by_district = landslides_df.assign(sev_num=sev_num).groupby("district")["sev_num"].sum()
    return by_district.to_dict(), float(by_district.mean())


def _road_level_from_district_map(origin_district, dest_district, district_map, dataset_mean):
    """
    Averages a per-district value across a road's origin and
    destination district, using only whichever endpoint(s) the
    source dataset actually covers. Falls back to the dataset-wide
    mean if NEITHER endpoint district is present (some districts
    aren't covered by every source file). Also returns a short
    string documenting which case applied, kept on the road record
    for transparency.
    """
    vals = []
    if origin_district in district_map:
        vals.append(district_map[origin_district])
    if dest_district in district_map:
        vals.append(district_map[dest_district])
    if vals:
        source = "both_endpoints" if len(vals) == 2 else "single_endpoint"
        return sum(vals) / len(vals), source
    return dataset_mean, "dataset_mean_fallback"


# -----------------------------------------------------------------
# STEP 2: Build the per-road feature table (replaces the old mock
# `road_segments` list with one built from the real synthetic data)
# -----------------------------------------------------------------
def build_feature_table():
    """
    Builds one feature record per road in roads_assam_synthetic_v3.xlsx.

    Feature provenance:
      - rainfall_mm                : roads file's own annual_rainfall_mm (road-level)
      - rainfall_anomaly_pct       : rainfall_assam_synthetic_v2, district-level
                                      departure_percent, averaged across the road's
                                      origin/destination district
      - slope_percent              : terrain_assam_synthetic_v3 mean_slope_percent,
                                      joined on road_id; falls back to the roads
                                      file's own mean_slope_percent for the one road
                                      (R117) the terrain file doesn't cover
      - elevation_range_m          : same source/fallback pattern as slope_percent
      - historical_landslide_count : roads file's own road-level count
      - landslide_district_hazard  : landslides_assam_synthetic_v2, severity-weighted
                                      event count, averaged across origin/destination
                                      district
      - road_type                  : roads file (MAJOR_CORRIDOR / STATE_HIGHWAY)

    NOTE ON A DATA-QUALITY DISCREPANCY: the roads file's own
    mean_slope_percent/elevation_range_m values do not always match
    terrain_assam_synthetic_v3.xlsx for the same road_id (differences of
    several percentage points / hundreds of metres in places). Both
    are SYNTHETIC_DEMO sources. This module treats the dedicated
    terrain file as authoritative (its stated purpose is terrain
    characterization) and only falls back to the roads file's own
    columns when terrain data is absent. This is documented, not
    silently reconciled -- see ml/README.md.

    reference_risk_score / reference_risk_level are copied from the
    roads file for comparison/validation ONLY. They are never read
    by compute_risk_score().
    """
    roads_df, terrain_df, rainfall_df, landslides_df = _load_raw_datasets()

    terrain_lookup = terrain_df.set_index("road_id")[["mean_slope_percent", "elevation_range_m"]].to_dict("index")
    rain_district_map, rain_mean = _aggregate_rainfall_anomaly(rainfall_df)
    hazard_district_map, hazard_mean = _aggregate_landslide_hazard(landslides_df)

    records = []
    for _, row in roads_df.iterrows():
        road_id = row["road_id"]

        terrain_row = terrain_lookup.get(road_id)
        if terrain_row is not None:
            slope_percent = float(terrain_row["mean_slope_percent"])
            elevation_range_m = float(terrain_row["elevation_range_m"])
            terrain_source = "terrain_dataset"
        else:
            slope_percent = float(row["mean_slope_percent"])
            elevation_range_m = float(row["elevation_range_m"])
            terrain_source = "roads_dataset_fallback"

        rainfall_anomaly_pct, rain_source = _road_level_from_district_map(
            row["origin_district"], row["destination_district"], rain_district_map, rain_mean
        )
        landslide_district_hazard, hazard_source = _road_level_from_district_map(
            row["origin_district"], row["destination_district"], hazard_district_map, hazard_mean
        )

        records.append({
            "road_id": road_id,
            "road_name": row["road_name"],
            "origin_district": row["origin_district"],
            "destination_district": row["destination_district"],
            "distance_km": float(row["distance_km"]),
            "road_type": row["road_type"],
            # --- model input features ---
            "rainfall_mm": float(row["annual_rainfall_mm"]),
            "rainfall_anomaly_pct": float(rainfall_anomaly_pct),
            "rainfall_anomaly_source": rain_source,
            "slope_percent": slope_percent,
            "elevation_range_m": elevation_range_m,
            "terrain_source": terrain_source,
            "historical_landslide_count": int(row["historical_landslide_count"]),
            "landslide_district_hazard": float(landslide_district_hazard),
            "landslide_hazard_source": hazard_source,
            # --- reference only: NEVER fed into compute_risk_score() ---
            "reference_risk_score": int(row["risk_score"]),
            "reference_risk_level": row["risk_level"],
        })
    return records


# Numeric input features that get min-max normalized. road_type is handled
# separately via road_type_score() since it's categorical.
FEATURE_KEYS = (
    "rainfall_mm",
    "rainfall_anomaly_pct",
    "slope_percent",
    "elevation_range_m",
    "historical_landslide_count",
    "landslide_district_hazard",
)


def _compute_ranges(records):
    """
    Normalization bounds are computed FROM THE ACTUAL LOADED DATASET
    (its observed min/max per feature), not assumed constants. The
    original mock version assumed e.g. rainfall 0-300mm and slope in
    degrees 0-45; the real synthetic data uses annual rainfall in the
    1600-2500mm range and slope as a PERCENT (~2.5-11.5), so dataset-
    derived ranges are required rather than reused assumptions.
    """
    ranges = {}
    for key in FEATURE_KEYS:
        values = [r[key] for r in records]
        ranges[key] = (min(values), max(values))
    return ranges


# Weight = how much each factor contributes to overall risk.
# These weights are an ASSUMPTION -- a judge-defensible starting point,
# not a scientifically derived value. Say this openly if asked.
# Weights sum to 1.0.
WEIGHTS = {
    "rainfall_mm": 0.25,
    "rainfall_anomaly_pct": 0.10,
    "slope_percent": 0.20,
    "elevation_range_m": 0.10,
    "historical_landslide_count": 0.20,
    "landslide_district_hazard": 0.10,
    "road_type": 0.05,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must sum to 1.0"


# -----------------------------------------------------------------
# STEP 3: Public scoring functions (kept API-compatible with the
# original mock-data version)
# -----------------------------------------------------------------
def normalize(value, min_val, max_val):
    """Scale a value to a 0-1 range."""
    if max_val == min_val:
        return 0
    value = max(min_val, min(value, max_val))  # clamp to range
    return (value - min_val) / (max_val - min_val)


def road_type_score(road_type):
    """
    PROTOTYPE ASSUMPTION: MAJOR_CORRIDOR roads (e.g. National Highway
    corridors) are assumed to be built/maintained to a higher standard
    than STATE_HIGHWAY roads, so they get a lower baseline road-type
    risk contribution -- mirroring the original paved/unpaved logic.
    This is a documented assumption, not a measured engineering fact.

    Note for transparency: in this synthetic dataset, MAJOR_CORRIDOR
    roads actually have a HIGHER average *reference* risk_score than
    STATE_HIGHWAY roads. That appears to be because major corridors in
    this dataset disproportionately cross steep hill terrain (e.g.
    Guwahati-Shillong, Dima Hasao) -- an effect already captured by
    this module's slope/elevation/rainfall features, not by road_type
    itself. road_type is given a small weight (0.05) precisely because
    it is the least certain assumption in the model.
    """
    return 0.3 if road_type == "MAJOR_CORRIDOR" else 1.0


def compute_risk_score(road):
    """
    Combine normalized factors into one weighted risk score.
    CONTRACT RULE (team-data-contract.pdf): riskScore must be an
    INTEGER 0-100, not a 0-1 float. We compute in 0-1 internally
    (easier math) then scale up at the end.

    IMPORTANT: `road` is expected to be one of the records produced by
    build_feature_table() (or road_segments). This function reads ONLY
    the input feature keys listed in FEATURE_KEYS plus 'road_type'. It
    never reads 'reference_risk_score' / 'reference_risk_level' --
    those exist on the record for validation/comparison only, to avoid
    target leakage.
    """
    rainfall_n = normalize(road["rainfall_mm"], *RANGES["rainfall_mm"])
    rainfall_anomaly_n = normalize(road["rainfall_anomaly_pct"], *RANGES["rainfall_anomaly_pct"])
    slope_n = normalize(road["slope_percent"], *RANGES["slope_percent"])
    elevation_n = normalize(road["elevation_range_m"], *RANGES["elevation_range_m"])
    hazard_n = normalize(road["historical_landslide_count"], *RANGES["historical_landslide_count"])
    district_hazard_n = normalize(road["landslide_district_hazard"], *RANGES["landslide_district_hazard"])
    road_type_n = road_type_score(road["road_type"])

    score_0_to_1 = (
        rainfall_n * WEIGHTS["rainfall_mm"] +
        rainfall_anomaly_n * WEIGHTS["rainfall_anomaly_pct"] +
        slope_n * WEIGHTS["slope_percent"] +
        elevation_n * WEIGHTS["elevation_range_m"] +
        hazard_n * WEIGHTS["historical_landslide_count"] +
        district_hazard_n * WEIGHTS["landslide_district_hazard"] +
        road_type_n * WEIGHTS["road_type"]
    )
    # CONTRACT: riskScore is an int 0-100
    return round(score_0_to_1 * 100)


def score_to_level(risk_score_0_100):
    """
    Convert 0-100 score into risk level.
    CONTRACT RULE: must be exactly "HIGH" / "MEDIUM" / "LOW" (all caps,
    no other spelling) -- this is what the GIS road object embeds and
    what the frontend matches against exactly.
    """
    if risk_score_0_100 >= 60:
        return "HIGH"
    elif risk_score_0_100 >= 35:
        return "MEDIUM"
    else:
        return "LOW"


def get_road_risk(road):
    """
    Returns just the two fields the GIS teammate needs to embed into
    their road object, in the exact contract shape:
        "riskLevel": "HIGH",
        "riskScore": 87
    """
    score = compute_risk_score(road)
    level = score_to_level(score)
    return {"riskLevel": level, "riskScore": score}


def get_reference_risk(road_id):
    """
    Returns the SOURCE dataset's own risk_score/risk_level for a road,
    clearly separated from get_road_risk(). For comparison/validation
    only -- e.g. sanity-checking this module's output against the
    dataset author's assumptions. Never used as a model input.
    """
    road = road_by_id.get(road_id)
    if road is None:
        raise ValueError(f"Unknown road_id: {road_id!r}. Must be one of {sorted(VALID_ROAD_IDS)}")
    return {"riskScore": road["reference_risk_score"], "riskLevel": road["reference_risk_level"]}


# -----------------------------------------------------------------
# Module-level data, built once at import time (mirrors the old
# module-level `road_segments` list so downstream code -- e.g.
# impact_prediction.py -- keeps working the same way).
# -----------------------------------------------------------------
road_segments = build_feature_table()
RANGES = _compute_ranges(road_segments)
road_by_id = {r["road_id"]: r for r in road_segments}
VALID_ROAD_IDS = set(road_by_id.keys())


# -----------------------------------------------------------------
# STEP 4: Run scoring on all roads
# -----------------------------------------------------------------
def score_all_roads():
    """Returns {road_id: {"riskScore": int, "riskLevel": str}} for every road."""
    return {road["road_id"]: get_road_risk(road) for road in road_segments}


def save_predictions_to_json(output_path=None):
    """Saves {road_id, riskScore, riskLevel} for every road to JSON."""
    import json
    if output_path is None:
        output_path = os.path.join(_THIS_DIR, "outputs", "road_risk_predictions.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results = [
        {"road_id": road["road_id"], **get_road_risk(road)}
        for road in road_segments
    ]
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    return output_path


if __name__ == "__main__":
    import json

    print(f"{'Road ID':<10}{'riskScore':<12}{'riskLevel':<10}{'reference':<12}")
    print("-" * 44)
    for road in road_segments:
        risk = get_road_risk(road)
        ref = get_reference_risk(road["road_id"])
        print(f"{road['road_id']:<10}{risk['riskScore']:<12}{risk['riskLevel']:<10}"
              f"{ref['riskScore']}/{ref['riskLevel']:<8}")

    print(f"\nProcessed {len(road_segments)} roads.")

    print("\nSample contract-shaped output for R101 (send this to GIS teammate):")
    print(json.dumps({"id": "R101", **get_road_risk(road_by_id["R101"])}, indent=2))

    path = save_predictions_to_json()
    print(f"\nSaved all-road predictions to {path}")
