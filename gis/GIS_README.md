# GIS Module — Assam Prototype (Phase 1)

**Everything in `gis/data/*.geojson` is synthetic prototype data (`SYNTHETIC_DEMO`), generated from synthetic Excel inputs. It is not real surveyed road geometry, not official IMD/GSI/ISRO/PWD/SRTM data, and should never be presented as such.** See "Data sources and status" below for exactly what "synthetic" means for each layer.

## What's in this directory

```
gis/
  data/
    assam_roads.geojson        23 road corridors
    assam_districts.geojson    20 Assam districts
    assam_facilities.geojson   45 facilities (hospitals/supply/villages)
    assam_landslides.geojson   60 landslide/hazard point records
  scripts/
    build_assam_gis.py         regenerates all four files above
  tests/
    test_gis_validation.py     validates the generated files + Network integration
  GIS_README.md                this file
```

## Data sources and status

Inputs, all under `data/` at the repo root:

| Input file | Rows | Feeds |
|---|---|---|
| `districts_assam_synthetic_v2.xlsx` | 20 | `assam_districts.geojson` |
| `roads_assam_synthetic_v3.xlsx` | 23 | `assam_roads.geojson` |
| `facilities_assam_synthetic_v2.xlsx` | 45 | `assam_facilities.geojson` |
| `landslides_assam_synthetic_v2.xlsx` | 60 | `assam_landslides.geojson` |
| `rainfall_assam_synthetic_v2.xlsx`, `terrain_assam_synthetic_v3.xlsx` | 192 / 22 | **not consumed here** — see "Rainfall/terrain ownership" below |

Every row in every input file carries an explicit `data_status` / `source` column reading `SYNTHETIC_DEMO`. None of it is claimed as real. Per `data/V2_DATA_README.md`: *"In deployment, these records would be replaced with verified real datasets."*

**The earlier, much larger `Assam_Road_Data_Full_Column_Names.xlsx` (303,927 real-OSM-style attribute rows, no geometry) is deliberately NOT used anywhere in this pipeline.** That file has no coordinates, no endpoints, and no distances (confirmed by inspection) — it would need a separate geometry-acquisition and corridor-stitching effort to be usable at all, which is explicitly out of scope for this phase per the "don't process hundreds of thousands of unrelated segments" instruction. The current pipeline uses the purpose-built synthetic corridor dataset instead, which already has clean IDs, endpoints, and distances.

### ⚠️ `data/V2_VALIDATION_REPORT.md` and `data/validate_synthetic_v2.py` are stale

Both describe a **17-road** dataset with only **one** alternate-route pair (`R101`/`R117`, `kamrup-metropolitan → dima-hasao`), and `validate_synthetic_v2.py` reads a file named `roads_assam_synthetic_v2.xlsx`, which does not exist in this repo. The file actually present, `roads_assam_synthetic_v3.xlsx`, has **23 roads and 7 alternate-route pairs**:

| Origin → Destination | Roads |
|---|---|
| kamrup-metropolitan → dima-hasao | R101, R117 |
| kamrup-metropolitan → goalpara | R107, R121 |
| nagaon → karbi-anglong | R104, R118 |
| cachar → dima-hasao | R105, R119 |
| dima-hasao → hojai | R106, R120 |
| jorhat → golaghat | R112, R123 |
| sonitpur → biswanath | R109, R122 |

Plus 9 single-road (no-alternate) pairs: `R102, R103, R108, R110, R111, R113, R114, R115`, and `R116` (see below). This was recomputed directly from `roads_assam_synthetic_v3.xlsx` with pandas, not copied from the stale report — treat the table above, not `V2_VALIDATION_REPORT.md`, as authoritative for the current dataset. Whoever generates data next should regenerate `V2_VALIDATION_REPORT.md` from `roads_assam_synthetic_v3.xlsx` (or delete it) so it doesn't keep contradicting the real file.

### ⚠️ R116 is a self-loop (`dima-hasao → dima-hasao`)

One road, "Dima Hasao Hill Corridor," has the same origin and destination district. This is real data, not a bug I introduced — but it's a genuine modeling question: a self-loop edge in the graph can never appear on a shortest path between two *different* nodes, so routing and impact analysis will never actually exercise it (confirmed in `test_gis_validation.py`'s `test_19`, which flags rather than fails on this). If this road is meant to represent a real named route between two towns *within* Dima Hasao, the team should decide whether to model it at a finer-than-district node granularity for this one case, or accept that it's present in the data but functionally inert for routing. I generated a small synthetic out-and-back spur geometry for it so it's still valid GeoJSON (see "Geometry strategy" below) — I did not resolve the modeling question, which isn't mine to resolve unilaterally.

## Node strategy

**Decision: for this phase, `source_node` / `destination_node` (the values `network/gis_loader.py` uses to build the NetworkX graph) are set equal to `origin_district` / `destination_district`.** District IDs *are* the graph nodes right now. This is a deliberate simplification, stated explicitly here per the "don't silently assume district IDs are node IDs" instruction — it is not hidden in code.

Consequence worth knowing: routing/impact analysis currently operates at district granularity, not intersection/facility granularity. Two hospitals in the same district are indistinguishable to `find_route`/`calculate_impact` as things stand.

## Facility-to-node mapping

Facilities are **not** graph nodes. `assam_facilities.geojson` carries each facility's own `district` property (from `facilities_assam_synthetic_v2.xlsx`), so the explicit, deterministic mapping is: **a facility's node, for impact analysis, is its `district` field** — the same district-ID-as-node scheme as roads. This is spelled out here rather than assumed inside code; whoever wires up a real `critical_locations` dict for `impact.calculate_impact()` should build it as `{facility_name: facility_district}`, reusing this file's `district` property directly.

## Geometry strategy

There is no surveyed road geometry anywhere in the input data. Each road's `LineString` is built deterministically by `build_assam_gis.py`:
- Endpoint coordinates = the origin/destination district's centroid (from `assam_districts.geojson`).
- One midpoint, offset from the straight-line midpoint by an amount derived from a SHA-256 hash of the road's own `road_id` — so lines aren't perfectly straight/visually identical, while remaining exactly reproducible (verified: running `build_assam_gis.py` twice produces byte-identical output).
- **This is a visual/structural device for the prototype, not a claim about where the real road runs.** `geometry_quality` (`SYNTHETIC_GEOMETRY` / `SYNTHETIC_ALTERNATE`, carried over from the source Excel) is preserved on every road feature so this is traceable in the data itself, not just in this README.
- R116 (self-loop) gets a small deterministic spur from its single centroid instead — see the flag above.

## Rainfall/terrain ownership

`rainfall_assam_synthetic_v2.xlsx` (192 rows, daily district-level rainfall) and `terrain_assam_synthetic_v3.xlsx` (22 rows, per-road elevation/slope) are **left in their original Excel form and not converted to GeoJSON or touched by this pipeline.** Looking at `roads_assam_synthetic_v3.xlsx`, its own columns (`elevation_mean_m`, `elevation_range_m`, `mean_slope_percent`, `historical_landslide_count`, `annual_rainfall_mm`, `risk_score`, `risk_level`) already look like a merged/derived output of exactly this terrain+rainfall+landslide data — i.e., this looks like ML/risk-scoring's feature table, already computed upstream of GIS. Treating that ownership as ML's, not GIS's, per "do not duplicate ML logic" — these two files are available for whoever owns that scoring to confirm, but this pipeline doesn't touch them.

## GeoJSON → Network loader contract

`assam_roads.geojson` is built to satisfy `network/gis_loader.py`'s existing, **unmodified** requirements exactly:

| Loader requires | Source in this GeoJSON |
|---|---|
| `road_id` (unique) | `properties.road_id` (from `roads_assam_synthetic_v3.xlsx`, already unique — verified, 0 duplicates) |
| `source_node` / `destination_node` (non-empty) | `properties.source_node` / `destination_node` = origin/destination district ID (see "Node strategy") |
| `distance_km` (> 0) | `properties.distance_km`, taken directly from the source data — no invented distances anywhere |
| `geometry.type == "LineString"`, ≥2 points, `[lon, lat]` order | see "Geometry strategy" |

Verified end-to-end (`test_gis_validation.py`, `test_15`–`test_18`): the loader builds a 16-node, 23-edge `MultiGraph` from `assam_roads.geojson` with zero modifications to `gis_loader.py`, `simulator.py`, or `impact.py`. R101/R117 coexist, failing either leaves the other intact, and routing correctly falls back to R117 after R101 fails.

**Extra properties beyond the loader's four required + four optional (`name, state, road_type, status`) fields — `origin_district`, `destination_district`, `risk_level`, `risk_score`, `official_ref`, `geometry_quality`, `data_status` — are present in the GeoJSON files but will NOT appear on NetworkX graph edges**, because `gis_loader.py`'s optional-field allowlist doesn't include them and this pipeline does not modify that file. They're there for the backend/frontend to read directly from the GeoJSON (or from wherever the backend re-serves it), not for routing. Routing only ever needs `distance`.

## Frontend/backend contract reconciliation

Per `team-data-contract.pdf`, the app contract's road `path` and district/facility `coords` are `[latitude, longitude]`; standard GeoJSON (and everything in `gis/data/`) is `[longitude, latitude]`. `frontend/src/data/geojsonToContract.js` (new, additive file) does this conversion, plus the `road_id→id`, `origin_district→originDistrict` etc. field renames, in one place. It is a pure transform — it imports nothing from and is not imported by `mockRoads.js`/`mockDistricts.js`/`mockFacilities.js`, and it is **not** wired into `frontend/src/services/api.js`.

### Why it isn't wired in yet — this needs a team decision, not a unilateral GIS call

The current Assam synthetic dataset is **not** a drop-in replacement for the existing frontend mock data:
- **District roster is completely different.** The existing `mockDistricts.js` has 21 districts across 8 NE states (Assam, Arunachal Pradesh, Meghalaya, Nagaland, Manipur, Mizoram, Tripura, Sikkim). The new dataset has 20 Assam-only districts, most of which (`nagaon`, `hojai`, `goalpara`, `bongaigaon`, `dhemaji`, `sivasagar`, `golaghat`, `jorhat`, `lakhimpur`, `karbi-anglong`, `biswanath`, `sonitpur`, `morigaon`, `baksa`, `udalguri`, `kamrup`) **do not exist at all** in the current frontend data.
- **Road IDs are reused for different roads.** This is the important one: `R101` currently means "Guwahati – Shillong Corridor, kamrup-metropolitan → east-khasi-hills, 96km" in `mockRoads.js`. In the new dataset, `R101` means "Guwahati – Shillong Corridor, kamrup-metropolitan → **dima-hasao**, 145km" — same name, same road_id, different destination district and distance. The same collision pattern holds for `R105`, `R106`, `R107`, `R108`, `R109`, `R110`, `R113`. Swapping the active data source without everyone on the team knowing would silently change what every existing `R1xx` reference in frontend/backend/ML code means.

I'm treating this as a cross-team decision to surface, not mine to make by editing `mockRoads.js`/`mockDistricts.js` directly — doing that unilaterally is exactly the kind of "blindly replace frontend mock data" the brief said not to do. `geojsonToContract.js` exists so that whenever the team does decide to cut over (fully, or district-by-district, or by renumbering the new roads to avoid the ID collision), it's a small change in `api.js` (swap a mock import for `roadsGeojsonToContract(fetch('.../assam_roads.geojson'))`-style loading) rather than new code written under time pressure at that point.

## Alternate-route rule (unchanged, preserved)

Per `team-data-contract.pdf`: an alternate route is valid only if it shares the **exact same** `originDistrict` and `destinationDistrict` as the failed road. This pipeline doesn't compute alternates — that's the routing teammate's job — but it does guarantee the underlying data supports it correctly: verified for all 7 real alternate pairs in this dataset (see table above), and specifically re-verified for R101/R117 end-to-end through the actual `gis_loader.py` + `simulator.py` (not a manual/eyeballed check).

## How to regenerate

```
cd gis/scripts
python build_assam_gis.py
```

Reads the four Excel files from `data/`, writes all four GeoJSON files to `gis/data/`. Deterministic — re-running with unchanged inputs produces byte-identical output (verified via `diff` against a prior run).

## How to run validation

```
cd gis/tests
python test_gis_validation.py
```

Covers all 18 checks requested for this phase (GeoJSON validity, LineString/coordinate/ID/distance checks, R101/R117 alternate-pair checks, facility/landslide coordinate checks, and full integration through the real, unmodified `network/gis_loader.py` + `simulator.py`), plus one extra check (`test_19`) that flags — doesn't fail on — the R116 self-loop.

`network/test_scenarios.py`, `network/test_impact.py`, and `network/test_gis_loader.py` were re-run unmodified after this work and all still pass — no regressions introduced in the Network module.
