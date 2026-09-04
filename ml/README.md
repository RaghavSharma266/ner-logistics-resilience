# ML Module — Road Risk Scoring & Impact Prediction

## 1. What this is (and isn't)

This is a **synthetic-data prototype**, built for the SIH deadline. It is:

- **NOT a trained ML model.** There is no labeled historical road-failure
  dataset available for this project. Instead, this module uses a
  transparent, rule-based **weighted scoring formula** whose weights and
  assumptions are documented below and can be interrogated/challenged.
- **NOT working with real observations.** Every dataset it reads is
  explicitly labeled `SYNTHETIC_DEMO` in the source files. Numbers here
  are prototype data, not official IMD / GSI / PWD / SRTM records.
- **NOT reporting accuracy/precision/recall/F1.** Those metrics require a
  labeled ground-truth dataset and a real train/test split, neither of
  which exists here. No such claim is made anywhere in this module.

## 2. Datasets used

All read from `data/` at import time (paths resolved relative to this
file, not the working directory):

| File | Role |
|---|---|
| `roads_assam_synthetic_v3.xlsx` | Primary per-road table: origin/destination district, road type, distance, road-level rainfall/terrain/hazard aggregates, and the dataset author's own `risk_score`/`risk_level` (reference only, see §5). |
| `terrain_assam_synthetic_v3.xlsx` | Per-road terrain profile (slope, elevation, terrain class), joined on `road_id`. Missing for one road (R117) — see §4. |
| `rainfall_assam_synthetic_v2.xlsx` | Per-district, per-date rainfall observations vs. normal, used to derive a district-level rainfall-anomaly signal. |
| `landslides_assam_synthetic_v2.xlsx` | Individual synthetic landslide/hazard event records, used to derive a district-level hazard signal. |
| `facilities_assam_synthetic_v2.xlsx` | Hospitals/supply points/villages with a `critical` flag, used in impact prediction (§7). |

`districts_assam_synthetic_v2.xlsx` is not read directly by this module —
district IDs already appear on the roads/rainfall/landslides/facilities
files and are used as join keys directly.

## 3. Road Risk Scoring (`road_risk_scoring.py`)

### Features used

| Feature | Source | Weight |
|---|---|---|
| `rainfall_mm` | roads file's own `annual_rainfall_mm` (road-level) | 0.25 |
| `rainfall_anomaly_pct` | rainfall file, `departure_percent` averaged over the road's origin+destination district | 0.10 |
| `slope_percent` | terrain file `mean_slope_percent`, joined on `road_id` | 0.20 |
| `elevation_range_m` | terrain file `elevation_range_m`, joined on `road_id` | 0.10 |
| `historical_landslide_count` | roads file's own road-level count | 0.20 |
| `landslide_district_hazard` | landslides file, severity-weighted event count (LOW=1/MEDIUM=2/HIGH=3) summed per district, averaged over origin+destination district | 0.10 |
| `road_type` | roads file (`MAJOR_CORRIDOR` / `STATE_HIGHWAY`) | 0.05 |

Weights sum to 1.0. **They are an assumption, not a scientifically
derived value** — say so plainly if asked. `road_type` gets the smallest
weight because it's the least certain assumption (see below).

### How the score is calculated

1. Each numeric feature is min-max normalized to `[0, 1]` using the
   **actual min/max observed in the loaded dataset** (not assumed
   constants — the original mock version assumed e.g. rainfall in
   0-300mm and slope in degrees 0-45; the real data uses annual
   rainfall around 1600-2500mm and slope as a **percent** around
   2.5-11.5, so dataset-derived ranges are used instead).
2. `road_type` maps to a fixed score instead of being normalized:
   `MAJOR_CORRIDOR → 0.3`, `STATE_HIGHWAY → 1.0` — mirroring the
   original paved/unpaved logic, on the assumption that major-corridor
   roads are built/maintained to a higher standard.
   **Caveat**: in this particular synthetic dataset, `MAJOR_CORRIDOR`
   roads actually have a *higher* average reference risk score than
   `STATE_HIGHWAY` roads, likely because major corridors here
   disproportionately cross steep hill terrain (Guwahati–Shillong, Dima
   Hasao). That effect is already captured by the slope/elevation/
   rainfall features, not by `road_type` — which is why `road_type`
   only gets a 0.05 weight.
3. The seven weighted, normalized values are summed (range `0-1`) and
   scaled to an integer `0-100` (`riskScore`).
4. `riskScore` is thresholded into `riskLevel`:
   `>= 60 → HIGH`, `>= 35 → MEDIUM`, else `LOW`.

### Target leakage

`roads_assam_synthetic_v3.xlsx` already ships its own `risk_score` /
`risk_level` columns. **These are never read by `compute_risk_score()`.**
They are copied onto each road record under different key names —
`reference_risk_score` / `reference_risk_level` — exposed only via
`get_reference_risk(road_id)`, for optional comparison, never as a model
input. A test (`test_no_target_leakage_...`) checks this structurally.

### A known data-quality discrepancy (documented, not silently fixed)

The roads file's own `mean_slope_percent` / `elevation_range_m` values
don't always match `terrain_assam_synthetic_v3.xlsx` for the same
`road_id` (differences of several percentage points / hundreds of
metres in places — both are `SYNTHETIC_DEMO`). This module treats the
dedicated terrain file as authoritative for slope/elevation, and only
falls back to the roads file's own columns for the one road the terrain
file doesn't cover (**R117**). This choice is documented here rather
than silently averaging or "fixing" the mismatch.

### Public functions (kept compatible with the original mock version)

```
normalize(value, min_val, max_val)
road_type_score(road_type)
compute_risk_score(road)          # road = a record from road_segments
score_to_level(risk_score_0_100)
get_road_risk(road)               # -> {"riskLevel": ..., "riskScore": ...}
get_reference_risk(road_id)       # dataset author's own score, comparison only
road_segments                     # list of per-road feature records, all 23 roads
road_by_id                        # {road_id: record}
```

## 4. R117 / the "17 roads" note

This task brief mentions "17 roads, including R101 and R117 as an
alternate-route pair." At the time of writing, `roads_assam_synthetic_v3.xlsx`
actually contains **23 roads**. That count matches `data/V2_DATA_README.md`'s
description of a *v2* 17-road set with R101/R117 added as an alternate
pair, but the dataset has since moved to v3 with six more roads (R118–R123),
each an alternate for another existing road (matching origin+destination
district). This module reads whatever is actually in the file — 23 roads
— rather than hardcoding the older count. No alternate-route relationship
(R101/R117 or any other pair) is hardcoded in this module; that logic
lives entirely in the Network module (see §6).

## 5. Reproducible output

Running `python road_risk_scoring.py` from `ml/` prints a table and
writes `ml/outputs/road_risk_predictions.json`:

```json
[
  {"road_id": "R101", "riskLevel": "MEDIUM", "riskScore": 51},
  ...
]
```

`ml/outputs/` is generated output, not source of truth — re-run the
script to regenerate it. `__pycache__` and generated `outputs/*.json`
are not meant to be committed.

## 6. Impact Prediction (`impact_prediction.py`)

`predict_impact(road_id, alternate_route=None, facility_context=None, travel_delay_min_override=None)`
returns exactly:

```json
{
  "accessibilityBefore": 87,
  "accessibilityAfter": 22,
  "travelDelayMin": 60,
  "locationsAffected": 6,
  "criticalFacilitiesAffected": 2
}
```

### Alternate routes come from the Network module, never invented here

- `alternate_route` must be `None` or a dict shaped
  `{"alternativeRoute": "R117" | None, "alternativeRouteName": str | None}`.
- If `alternate_route` is not supplied (`None`), this is treated as **"no
  alternate route information is available,"** and defaults to the
  no-alternate shape. It is never used to look up or invent a mock
  alternate — only the Network/Dijkstra module's routing output should
  ever set `alternativeRoute` to a real road id.
- **Project rule enforcement**: if the supplied alternate road id happens
  to be one of this module's own 23 roads, its origin/destination
  district is cross-checked against the failed road's — a mismatch
  raises a clear `ValueError`. If the Network module supplies an
  alternate id this module doesn't recognise, the check is skipped (we
  don't fabricate district data to verify an external id) and the
  Network module's input is trusted.

### Facility impact

`facilities_assam_synthetic_v2.xlsx` and `roads_assam_synthetic_v3.xlsx`
carry no shared geometry to join on (roads have no lat/lon; their
`geometry_quality` is `SYNTHETIC_GEOMETRY`/`SYNTHETIC_ALTERNATE` with no
coordinates). Rather than inventing coordinates or distances, **"nearby"
facilities for a road are the facilities located in that road's
`origin_district` or `destination_district`** — the only real join key
available. This is a documented district-level proxy, not a geometric
buffer, and is computed automatically by `facility_context_for_road()`
when `facility_context` isn't explicitly supplied. Callers (e.g. Backend
with a better geometry-based join later) may still override it.

### Travel delay

`estimate_travel_delay()` is a placeholder formula (bigger base delay
with no alternate, scaled slightly by risk score) — **not** a real
route-time difference; this module does not invent a distance→minutes
conversion. Once the Network module can supply a real cost delta,
`predict_impact(..., travel_delay_min_override=<int>)` lets Backend pass
it straight through, bypassing the placeholder formula.

### Accessibility

`estimate_accessibility_before/after()` are prototype percentage
formulas (documented in-code), not a real GIS accessibility calculation.

## 7. Contract summary

| Function | Input | Output |
|---|---|---|
| `get_road_risk(road)` | one `road_segments` record | `{"riskLevel": "HIGH"\|"MEDIUM"\|"LOW", "riskScore": int 0-100}` |
| `predict_impact(road_id, alternate_route=None, facility_context=None, travel_delay_min_override=None)` | road id + optional Network/Backend-supplied context | `{"accessibilityBefore": int, "accessibilityAfter": int, "travelDelayMin": int, "locationsAffected": int, "criticalFacilitiesAffected": int}` |

## 8. Running the tests

From the repo root:

```
python -m unittest discover ml -v
```

or, from inside `ml/`:

```
python3 -m unittest test_impact_prediction.py -v
```

The suite (`test_impact_prediction.py`) covers both `road_risk_scoring.py`
and `impact_prediction.py`: dataset loading, unique road ids, valid
risk-score/level ranges, no-target-leakage, R101/R117 alternate-route
behaviour (only when explicitly supplied), the alternate-route
same-district-pair rule, no-alternate roads, exact contract field names,
output type/range validation across all 23 roads, invalid-input error
handling, batch prediction, and JSON export.

Requires `pandas` and `openpyxl` (`pip install pandas openpyxl`) in
addition to the project's existing dependencies.

## 9. Replacing this with a trained model later

If real, labeled historical failure/disruption data becomes available:

1. Keep `road_segments` (or an equivalent feature table) as the feature
   matrix — the feature provenance in §3 already documents what each
   column means and where it comes from.
2. Replace `compute_risk_score()`'s weighted-sum formula with a trained
   classifier/regressor over the same (or an extended) feature set.
   Keep the `road → {"riskScore": int 0-100, "riskLevel": str}` contract
   unchanged so GIS/Network/Backend/Frontend don't need to change.
3. Only then would accuracy/precision/recall/F1 be reportable — evaluated
   against a genuine held-out labeled set, not this synthetic data.
4. `impact_prediction.py`'s placeholder formulas (`estimate_accessibility_*`,
   `estimate_travel_delay`) are the next candidates to replace, once real
   network accessibility/route-time data is available — the
   `travel_delay_min_override` parameter already gives Backend a way to
   supply real values without touching this module's internals.
