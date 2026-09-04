# Backend — NER Logistics Resilience Platform (SIH Prototype)

**Module:** Backend / orchestration layer
**Parent Project:** AI-Based Smart Logistics and Road Resilience Platform (Assam, synthetic prototype)
**Workflow:** PREDICT (ML) → SIMULATE (Network) → RESPOND (Backend)

> ⚠️ All data served by this API — roads, districts, facilities, risk scores, impact estimates — is **SYNTHETIC_DEMO** prototype data (see `gis/GIS_README.md`, `ml/README.md`, `data/V2_DATA_README.md`). It is not real government, disaster, or official observation data.

## 1. What Backend does — and doesn't do

Backend is an **orchestrator only**:

```
request → calls Network (network/) → calls ML (ml/) → combines → response
```

It does **not** reimplement NetworkX routing, road-failure logic, GIS loading, or ML risk/impact formulas. Every route, every risk score, every impact number in a response comes from calling the existing, **unmodified** `network/` and `ml/` modules.

No files outside `backend/` were changed, except that running `ml/road_risk_scoring.py` directly during testing (as required, to confirm "ML tests still pass") regenerates its own pre-existing `ml/outputs/road_risk_predictions.json` output file — that's the script's own designed behavior when run as `__main__`, not a Backend code change.

## 2. Architecture

```
backend/
├── main.py                    # FastAPI app + route registration
├── requirements.txt
├── README.md                  # this file
├── models/
│   └── schemas.py             # Pydantic request/response models
├── services/
│   ├── path_setup.py          # puts network/ and ml/ on sys.path (see §3)
│   ├── network_client.py      # calls network.gis_loader + network.simulator
│   ├── ml_client.py           # calls ml.road_risk_scoring + ml.impact_prediction
│   ├── gis_data.py            # reads gis/data/*.geojson for GET endpoints
│   └── orchestrator.py        # POST /simulate-failure: combines Network + ML
└── tests/
    └── test_backend.py
```

## 3. Why `path_setup.py` exists (the one necessary cross-boundary touch)

`network/` and `ml/` have no `__init__.py` and their own files use bare imports (e.g. `network/impact.py` does `from simulator import ...`). That only works when the folder itself is on `sys.path` — exactly how their own test scripts run (`cd network && python test_scenarios.py`).

`backend/services/path_setup.py` inserts the absolute paths of `network/` and `ml/` onto `sys.path` at import time. **This is the only thing Backend does that reaches outside `backend/`, and it is purely additive** (a `sys.path` entry) — no file outside `backend/` is created, edited, or deleted.

## 4. Setup & running

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive API docs.

Must be run with `network/`, `ml/`, `gis/`, and `data/` present as siblings of `backend/` (i.e. from inside the repo) — `path_setup.py` raises a clear error otherwise.

## 5. Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/v1/districts` | All 20 Assam districts, from `gis/data/assam_districts.geojson` |
| GET | `/api/v1/roads` | All 23 roads, from `gis/data/assam_roads.geojson`, with **live** ML risk scores |
| GET | `/api/v1/facilities` | All 45 facilities, from `gis/data/assam_facilities.geojson` |
| POST | `/api/v1/simulate-failure` | Core what-if simulation (see §7) |

### GET /api/v1/districts

```json
[
  {
    "id": "kamrup-metropolitan",
    "name": "Kamrup Metropolitan",
    "state": "Assam",
    "terrainClass": "PLAINS",
    "coords": [26.1445, 91.7362],
    "connectivityStatus": "VULNERABLE",
    "dataStatus": "SYNTHETIC_DEMO"
  }
]
```

`connectivityStatus` (`CONNECTED` / `AT_RISK` / `VULNERABLE`) is **derived, not fabricated** — computed from the real road graph + live ML risk per district-pair (documented rule in `services/gis_data.py`, mirroring the same rule `frontend/src/data/mockDistricts.js` documents for its own hand-authored data): a district-pair is `CONNECTED` if its lowest-risk direct road is LOW risk, `AT_RISK` if the lowest-risk road is MEDIUM/HIGH but a parallel alternate exists, `VULNERABLE` if MEDIUM/HIGH with no alternate. A district's status is the worst status across all its pairs.

**Known limitation:** applying this rule to ML's *live-computed* risk scores (as opposed to the frontend mock's hand-picked scores) currently yields `VULNERABLE` for all 20 districts in this synthetic dataset — most district-pairs are single-road, and ML's live scores for several of those single roads land in MEDIUM/HIGH. This is an honest computation on real data, not a bug, but it makes the field visually uninteresting right now; flagging for a team decision rather than tuning it to look better.

**Known gap vs. the old frontend mock schema:** `hqTown` and `population` (present in `frontend/src/data/mockDistricts.js`) do not exist in the real dataset and are **not fabricated here** — they're simply absent from the response.

### GET /api/v1/roads

```json
{
  "id": "R101",
  "name": "Guwahati – Shillong Corridor",
  "originDistrict": "kamrup-metropolitan",
  "destinationDistrict": "dima-hasao",
  "distanceKm": 145.0,
  "roadType": "MAJOR_CORRIDOR",
  "officialRef": "NH-200(S)",
  "riskScore": 51,
  "riskLevel": "MEDIUM",
  "status": "OPERATIONAL",
  "path": [[26.1445, 91.7362], [25.84, 92.51], [25.48, 93.02]],
  "dataStatus": "SYNTHETIC_DEMO",
  "geometryQuality": "SYNTHETIC_GEOMETRY"
}
```

`riskScore`/`riskLevel` are obtained by **calling** `ml.road_risk_scoring.get_road_risk()` for every road — this is ML's live weighted-formula output, and **intentionally differs** from the GeoJSON's own static `risk_score`/`risk_level` properties (those are "reference only" values from the source dataset — see `ml/road_risk_scoring.py`'s target-leakage note. e.g. R101's GeoJSON reference is `82/HIGH`, ML's live score is `51/MEDIUM`).

`status` is `"OPERATIONAL"` for every road in this listing: no road in the base dataset is pre-marked failed. `POST /simulate-failure` is what models a road going down, not this endpoint.

`path` is converted from GeoJSON `[lon, lat]` to the team contract's `[lat, lng]` order.

### GET /api/v1/facilities

```json
{
  "id": "FAC-01",
  "name": "District Hospital Kamrup Metropolitan (SYNTHETIC)",
  "type": "HOSPITAL",
  "district": "kamrup-metropolitan",
  "coords": [26.13533, 91.7319],
  "critical": true,
  "dataStatus": "SYNTHETIC_DEMO"
}
```

### POST /api/v1/simulate-failure

**Request:**
```json
{ "road_id": "R101" }
```
`source`/`destination` are **optional** — per project decision, if omitted they default to the failed road's own `originDistrict`/`destinationDistrict`. They can be supplied explicitly as any valid district ID to simulate a longer trip that merely passes through the failed road.

**Response — alternate exists (real R101 → R117 scenario):**
```json
{
  "failedRoad": "R101",
  "roadName": "Guwahati – Shillong Corridor",
  "originDistrict": "kamrup-metropolitan",
  "destinationDistrict": "dima-hasao",
  "source": "kamrup-metropolitan",
  "destination": "dima-hasao",
  "riskScore": 51,
  "riskLevel": "MEDIUM",
  "destinationReachable": true,
  "originalRoute": ["kamrup-metropolitan", "dima-hasao"],
  "alternateRoute": ["kamrup-metropolitan", "dima-hasao"],
  "originalDistanceKm": 145.0,
  "alternateDistanceKm": 171.1,
  "alternativeRoute": "R117",
  "alternativeRouteName": "Alternate Guwahati – Shillong Corridor",
  "additionalDistanceKm": 26.1,
  "accessibilityBefore": 87,
  "accessibilityAfter": 52,
  "travelDelayMin": 30,
  "locationsAffected": 6,
  "criticalFacilitiesAffected": 2,
  "recommendation": "R101 (Guwahati – Shillong Corridor) has failed (medium risk). Use alternate corridor R117 between the same districts (kamrup-metropolitan -> dima-hasao); expect approximately 171 km on the alternate route."
}
```

**Response — no alternate (real R108 single-point-of-failure scenario):**
```json
{
  "failedRoad": "R108",
  "originDistrict": "goalpara",
  "destinationDistrict": "bongaigaon",
  "destinationReachable": false,
  "originalRoute": ["goalpara", "bongaigaon"],
  "alternateRoute": null,
  "alternativeRoute": null,
  "alternativeRouteName": null,
  "additionalDistanceKm": null,
  "accessibilityBefore": 90,
  "accessibilityAfter": 28,
  "travelDelayMin": 55,
  "locationsAffected": 6,
  "criticalFacilitiesAffected": 2,
  "recommendation": "Critical disruption: R108 (Goalpara – Bongaigaon Corridor) has failed (low risk) and no route currently connects goalpara to bongaigaon. This is a single point of failure -- flag for priority infrastructure investment or emergency logistics (airlift/portage)."
}
```

Returns `404` with a clear message for an unknown `road_id`, `source`, or `destination`.

## 6. Network integration

- `services/network_client.py` builds the graph **once** (cached) via `network.gis_loader.load_geojson_file("gis/data/assam_roads.geojson")` — the real, unmodified loader. Nodes are district IDs (per `gis/GIS_README.md`'s documented "district IDs are the graph nodes" phase-1 decision).
- Routing/failure/comparison are 100% `network.simulator.find_route` / `simulate_road_failure` / `compare_routes` — unmodified, called directly.
- **Alternate-route rule** (same origin AND destination district as the failed road): implemented in `network_client.find_direct_alternate()`, which looks at **direct edges** between the failed road's origin/destination district on the **post-failure** graph (so the failed road is structurally excluded — never returned as its own alternate). This is distinct from `destinationReachable`/`alternateRoute` (the general trip path, which can be `True`/non-null via a longer multi-hop detour even when no *direct* parallel alternate exists — see R108's difference from e.g. R110, both single-point-of-failure roads for their own direct pair but with different downstream reachability). Nothing here is hardcoded — verified against all 23 roads (see §8), reproducing exactly the 7 alternate-pairs / 16 no-alternate-roads split documented in `gis/GIS_README.md`.

## 7. ML integration

- `services/ml_client.py` calls `ml.road_risk_scoring.get_road_risk()` and `ml.impact_prediction.predict_impact()` directly — no formula is duplicated in Backend.
- `alternate_route` passed into `predict_impact()` is built from Network's real `find_direct_alternate()` result, in the exact contract shape ML already expects (`{"alternativeRoute": ..., "alternativeRouteName": ...}`).
- **`travel_delay_min_override` is intentionally never set** (per project decision): Network only has `distance_km`, not travel time or a speed assumption, and inventing a km→minutes conversion was explicitly ruled out rather than guessed at. ML's own documented `estimate_travel_delay()` formula (alternate exists → smaller base delay; no alternate → larger base delay; risk-scaled) is used unchanged as the sole source of `travelDelayMin`.
- `facility_context` is left `None`, letting ML derive it itself via `facility_context_for_road()` (district-join against `facilities_assam_synthetic_v2.xlsx`) — Backend does not compute or override this.

## 8. GIS/data integration

- GET endpoints read `gis/data/{assam_districts,assam_roads,assam_facilities}.geojson` directly (`services/gis_data.py`), because `network.gis_loader`'s graph intentionally drops fields like `origin_district`/`risk_level` that the graph itself doesn't need (documented in `gis/GIS_README.md`) — those extra fields are only recoverable from the raw GeoJSON, not from the graph.
- `road_id` stays consistent end-to-end: the same `road_id` values from `gis/data/assam_roads.geojson` are what `network.gis_loader` keys graph edges by, what `ml.road_risk_scoring.road_by_id` is keyed by, and what this API returns.
- No second/duplicate road or district dataset was created. The backend prototype's original `roads.json`/`locations.json` were **not used** as a data source anywhere in the final implementation.

## 9. Testing

```bash
cd backend
pytest tests/ -v
```

See `tests/test_backend.py` for the full suite (server import, all 4 read endpoints, valid/invalid simulate-failure requests, the real R101→R117 alternate scenario, the real R108 no-alternate scenario, ML-incorporation checks, Network-usage checks, and a full 23-road sweep).

Also re-run, unmodified, to confirm no regressions:
```bash
cd network && python test_scenarios.py && python test_impact.py && python test_gis_loader.py
cd ../gis/tests && python test_gis_validation.py
cd ../../ml && python test_impact_prediction.py
```

## 10. Known limitations / open items for the team

1. **Districts' `connectivityStatus` is `VULNERABLE` for all 20 districts** in the current dataset once computed from ML's live risk scores (see §5) — not wrong, just not very informative yet. Worth a team discussion on whether the heuristic or the underlying risk-score distribution should change.
2. **No real travel-time (minutes) data anywhere in the project.** `travelDelayMin` is entirely ML's prototype formula, never adjusted by a real Network-derived value — see §7. If real speed/travel-time data becomes available, `travel_delay_min_override` in `ml_client.predict_impact()` is the integration point already wired for it.
3. **R116 (self-loop, `dima-hasao → dima-hasao`)** behaves as documented in `gis/GIS_README.md`: `POST /simulate-failure` for R116 reports `destinationReachable: true` trivially (source==destination by default), since a self-loop can never appear on a shortest path between two *different* districts. This is inherited Network/GIS behavior, not a Backend bug.
4. **Frontend is not wired up.** `frontend/src/services/api.js` only calls a real backend for `fetchDistricts()` today; `simulateFailure()`, `fetchRoads()`, `fetchFacilities()` still use mock data and were intentionally left untouched (out of scope: "do not modify frontend unnecessarily"). The response shapes above were designed to match what `frontend/src/data/mockSimulation.js`/`mockRoads.js`/etc. already expect, to make that wiring straightforward whenever the team decides to do it.
