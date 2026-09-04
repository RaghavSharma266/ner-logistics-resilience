"""
impact_prediction.py — AI/ML Module (Member 4)
================================================
Prototype/rule-based impact estimator for road failure simulation.

THIS IS NOT A TRAINED ML MODEL. There is no labeled historical
disruption dataset available for this project (per team-data-contract.pdf
and project constraints). This module uses a transparent, explainable
formula so its behaviour can be justified to judges and swapped for a
trained model later if real labeled data becomes available.

ARCHITECTURE (per team-data-contract.pdf):
    road_risk_scoring.py -> riskScore/riskLevel
    Network module (Dijkstra/routing) -> alternate route info (real, not invented here)
    impact_prediction.py -> merges both into the simulate-failure contract shape:

        {
          "accessibilityBefore": int,
          "accessibilityAfter": int,
          "travelDelayMin": int,
          "locationsAffected": int,
          "criticalFacilitiesAffected": int
        }

This module NEVER invents:
    - real geographic distances/coordinates
    - real network accessibility
    - alternate routes (that comes from the Network module)

FACILITY IMPACT: facilities_assam_synthetic_v2.xlsx has no road-level
geometry to join against (roads_assam_synthetic_v3.xlsx carries no
lat/lon either -- geometry_quality is SYNTHETIC_GEOMETRY/SYNTHETIC_ALTERNATE
with no coordinates). Rather than inventing coordinates or distances,
"nearby" facilities for a road are defined as facilities located in
that road's origin_district OR destination_district -- the only real,
available join key. This is a documented district-level proxy, not a
geometric buffer. See ml/README.md.
"""

import json
import os
import pandas as pd

from road_risk_scoring import get_road_risk, road_segments, road_by_id, VALID_ROAD_IDS, _THIS_DIR, DATA_DIR

# -----------------------------------------------------------------
# RISK SCORE CONVENTION (documented per spec section 14)
# -----------------------------------------------------------------
# riskScore is represented as an INTEGER 0-100 throughout this module,
# matching road_risk_scoring.py and the team contract. Do not mix this
# with a 0-1 representation anywhere in this file.

FACILITIES_FILE = os.path.join(DATA_DIR, "facilities_assam_synthetic_v2.xlsx")


def _load_facilities():
    if not os.path.exists(FACILITIES_FILE):
        raise FileNotFoundError(
            f"Missing required dataset: {FACILITIES_FILE}. impact_prediction.py "
            f"requires the project's synthetic facilities dataset -- it does not "
            f"fall back to mock data."
        )
    return pd.read_excel(FACILITIES_FILE)


FACILITIES_DF = _load_facilities()


def facility_context_for_road(road):
    """
    Derives {"nearby_facilities": int, "critical_facilities": int} for a
    road from data/facilities_assam_synthetic_v2.xlsx, using the road's
    origin_district/destination_district as the join key (see module
    docstring for why -- no road geometry is available to join on).
    """
    districts = {road["origin_district"], road["destination_district"]}
    subset = FACILITIES_DF[FACILITIES_DF["district"].isin(districts)]
    return {
        "nearby_facilities": int(len(subset)),
        "critical_facilities": int(subset["critical"].sum()),
    }


# -----------------------------------------------------------------
# VALIDATION
# -----------------------------------------------------------------
def _validate_risk_score(risk_score):
    if not isinstance(risk_score, int) or isinstance(risk_score, bool):
        raise ValueError(f"risk_score must be an int (0-100), got {type(risk_score).__name__}")
    if not (0 <= risk_score <= 100):
        raise ValueError(f"risk_score must be between 0 and 100, got {risk_score}")


def _validate_facility_counts(nearby_facilities, critical_facilities):
    if nearby_facilities < 0:
        raise ValueError("nearby_facilities cannot be negative")
    if critical_facilities < 0:
        raise ValueError("critical_facilities cannot be negative")
    if critical_facilities > nearby_facilities:
        raise ValueError("critical_facilities cannot exceed nearby_facilities")


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _get_road_safe(road_id):
    """
    Safe road lookup. Raises a clear error instead of letting a bare
    dict lookup fail silently or throw a bare KeyError.
    """
    road = road_by_id.get(road_id)
    if road is None:
        raise ValueError(f"Unknown road_id: {road_id!r}. Must be one of {sorted(VALID_ROAD_IDS)}")
    return road


def _validate_alternate_route(alternate_route):
    """
    Validates the shape of the Network module's contract object:
        {"alternativeRoute": "R117" | None, "alternativeRouteName": str | None}
    Raises a clear error on malformed input instead of silently
    misreading it as "no alternate exists".
    """
    if not isinstance(alternate_route, dict):
        raise ValueError(
            f"alternate_route must be a dict matching the contract shape "
            f"{{'alternativeRoute': str|None, 'alternativeRouteName': str|None}}, "
            f"got {type(alternate_route).__name__}"
        )
    if "alternativeRoute" not in alternate_route:
        raise ValueError("alternate_route dict is missing required key 'alternativeRoute'")
    alt_id = alternate_route["alternativeRoute"]
    if alt_id is not None and not isinstance(alt_id, str):
        raise ValueError(f"alternativeRoute must be a string road ID or None, got {type(alt_id).__name__}")


def _validate_alternate_route_matches_districts(road, alternate_route):
    """
    Project rule: an alternate route must have the SAME origin district
    and destination district as the failed road. This module does not
    invent alternate routes -- it only cross-checks the rule when the
    supplied alternate road_id happens to be one of our own dataset's
    roads (so we have its origin/destination on file). If the Network
    module supplies an alternate road_id we don't recognise, we can't
    verify it locally and trust the Network module's input rather than
    fabricating district data for it.
    """
    alt_id = alternate_route.get("alternativeRoute")
    if alt_id is None:
        return
    alt_road = road_by_id.get(alt_id)
    if alt_road is None:
        return
    if (alt_road["origin_district"] != road["origin_district"] or
            alt_road["destination_district"] != road["destination_district"]):
        raise ValueError(
            f"alternativeRoute {alt_id!r} does not share the same origin/destination "
            f"district as {road['road_id']!r} "
            f"({alt_road['origin_district']!r}->{alt_road['destination_district']!r} vs "
            f"{road['origin_district']!r}->{road['destination_district']!r}). "
            f"Per project rule, an alternate route must share both endpoints."
        )


def _validate_facility_context(facility_context):
    """Validates facility_context has the expected keys with non-negative ints."""
    if not isinstance(facility_context, dict):
        raise ValueError(
            f"facility_context must be a dict {{'nearby_facilities': int, 'critical_facilities': int}}, "
            f"got {type(facility_context).__name__}"
        )
    for key in ("nearby_facilities", "critical_facilities"):
        if key not in facility_context:
            raise ValueError(f"facility_context is missing required key '{key}'")
        if not isinstance(facility_context[key], int) or isinstance(facility_context[key], bool):
            raise ValueError(f"facility_context['{key}'] must be an int, got {type(facility_context[key]).__name__}")


# -----------------------------------------------------------------
# ESTIMATION FUNCTIONS (prototype rules — explainable, not "trained")
# -----------------------------------------------------------------
def estimate_accessibility_before(risk_score):
    """
    Baseline accessibility (%) BEFORE failure.
    Prototype rule: starts near-full accessibility (95%), reduced slightly
    for roads that are already high-risk (e.g. already degraded/slow).
    NOT a real GIS accessibility calculation.
    """
    _validate_risk_score(risk_score)
    value = 95 - (risk_score * 0.15)
    return int(round(_clamp(value)))


def estimate_accessibility_after(accessibility_before, alternate_exists, risk_score):
    """
    Accessibility (%) AFTER the road fails.
    Prototype rule:
      - alternate route exists -> moderate drop
      - no alternate route -> sharp drop
      - higher risk score -> slightly larger drop (assumption: risky roads
        often serve harder-to-reach areas)
    Production version should replace this with real network accessibility
    from the GIS/routing system.
    """
    _validate_risk_score(risk_score)
    if not (0 <= accessibility_before <= 100):
        raise ValueError("accessibility_before must be between 0 and 100")

    if alternate_exists:
        drop = 30 + (risk_score * 0.1)
    else:
        drop = 55 + (risk_score * 0.2)

    value = accessibility_before - drop
    return int(round(_clamp(value)))


def estimate_travel_delay(alternate_exists, risk_score):
    """
    Extra travel time (minutes) caused by the failure.
    Prototype rule: alternate route -> smaller base delay; no alternate ->
    larger base delay; scaled slightly by risk score (terrain difficulty
    proxy). Never negative.
    This is a placeholder formula, NOT a real route-time difference. It
    should be replaced once the Network module can supply a real cost
    delta (see travel_delay_min_override on predict_impact) -- this
    module does not convert route distance into minutes itself, since
    that would require inventing a speed assumption not present in any
    dataset.
    """
    _validate_risk_score(risk_score)
    base_delay = 15 if alternate_exists else 45
    value = base_delay + (risk_score * 0.3)
    return max(0, int(round(value)))


def estimate_locations_affected(nearby_facilities):
    """Passes through facility context derived from facilities_assam_synthetic_v2.xlsx
    (or explicitly supplied by the caller)."""
    if nearby_facilities < 0:
        raise ValueError("nearby_facilities cannot be negative")
    return int(nearby_facilities)


def estimate_critical_facilities_affected(critical_facilities, nearby_facilities):
    """Passes through critical facility count, validated against total."""
    _validate_facility_counts(nearby_facilities, critical_facilities)
    return int(critical_facilities)


# -----------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------
def predict_impact(road_id, alternate_route=None, facility_context=None, travel_delay_min_override=None):
    """
    Produces the exact simulate-failure contract shape:
        {
          "accessibilityBefore": int,
          "accessibilityAfter": int,
          "travelDelayMin": int,
          "locationsAffected": int,
          "criticalFacilitiesAffected": int
        }

    Args:
        road_id: e.g. "R101" -- must exist in road_risk_scoring.road_segments
        alternate_route: dict from the Network module in contract shape
            {"alternativeRoute": "R117", "alternativeRouteName": "..."} or
            {"alternativeRoute": None, "alternativeRouteName": None}.
            If None (not supplied), this is treated as "no alternate route
            information is available" and defaults to the no-alternate
            shape -- it is NEVER used to invent or look up a mock
            alternate. Only the Network module's routing/Dijkstra output
            should ever set alternativeRoute to a road_id.
        facility_context: dict {"nearby_facilities": int, "critical_facilities": int}.
            If None, this is derived directly from
            data/facilities_assam_synthetic_v2.xlsx via
            facility_context_for_road() (real project data, not mock).
            Callers (e.g. Backend/GIS with a better geometry-based join)
            may override by passing this explicitly.
        travel_delay_min_override: optional int. If the Network module can
            supply a real route-cost-based delay in minutes, pass it here
            to bypass the prototype estimate_travel_delay() formula. Left
            None by default since ML does not invent a distance->minutes
            conversion.
    """
    road = _get_road_safe(road_id)
    risk = get_road_risk(road)
    risk_score = risk["riskScore"]

    if alternate_route is None:
        alternate_route = {"alternativeRoute": None, "alternativeRouteName": None}
    _validate_alternate_route(alternate_route)
    _validate_alternate_route_matches_districts(road, alternate_route)
    alternate_exists = alternate_route["alternativeRoute"] is not None

    if facility_context is None:
        facility_context = facility_context_for_road(road)
    _validate_facility_context(facility_context)
    nearby_facilities = facility_context["nearby_facilities"]
    critical_facilities = facility_context["critical_facilities"]
    _validate_facility_counts(nearby_facilities, critical_facilities)

    before = estimate_accessibility_before(risk_score)
    after = estimate_accessibility_after(before, alternate_exists, risk_score)

    if travel_delay_min_override is not None:
        if not isinstance(travel_delay_min_override, int) or isinstance(travel_delay_min_override, bool) or travel_delay_min_override < 0:
            raise ValueError(
                f"travel_delay_min_override must be a non-negative int, got {travel_delay_min_override!r}"
            )
        delay = travel_delay_min_override
    else:
        delay = estimate_travel_delay(alternate_exists, risk_score)

    locations = estimate_locations_affected(nearby_facilities)
    critical = estimate_critical_facilities_affected(critical_facilities, nearby_facilities)

    return {
        "accessibilityBefore": before,
        "accessibilityAfter": after,
        "travelDelayMin": delay,
        "locationsAffected": locations,
        "criticalFacilitiesAffected": critical,
    }


def explain_impact(road_id, alternate_route=None, facility_context=None):
    """
    Human-readable explanation of the impact estimate, using only values
    actually computed -- no invented facts.
    """
    road = _get_road_safe(road_id)
    risk = get_road_risk(road)

    result = predict_impact(road_id, alternate_route, facility_context)

    if alternate_route is None:
        alternate_route = {"alternativeRoute": None, "alternativeRouteName": None}
    alt_id = alternate_route.get("alternativeRoute")

    alt_text = (
        f"A valid alternate route ({alt_id}) is available, which limits the estimated accessibility reduction."
        if alt_id
        else "No valid alternate route is available, which increases the estimated impact."
    )

    critical_text = (
        f"including {result['criticalFacilitiesAffected']} critical facility(ies)"
        if result["criticalFacilitiesAffected"] > 0
        else "with no critical facilities in the affected set"
    )

    return (
        f"Road {road_id} has a {risk['riskLevel'].lower()} disruption risk (riskScore={risk['riskScore']}). "
        f"{alt_text} "
        f"Estimated accessibility drops from {result['accessibilityBefore']}% to {result['accessibilityAfter']}%, "
        f"with an estimated additional travel delay of {result['travelDelayMin']} minutes. "
        f"The road is associated with {result['locationsAffected']} affected location(s), {critical_text}."
    )


def predict_all_impacts():
    """Runs predict_impact for every road in road_risk_scoring.road_segments,
    with no alternate route supplied (i.e. simulating each road in isolation,
    no Network routing info assumed) and facility context auto-derived from
    the real facilities dataset."""
    results = []
    for road in road_segments:
        road_id = road["road_id"]
        impact = predict_impact(road_id)
        results.append({"road_id": road_id, **impact})
    return results


def save_predictions_to_json(output_path=None):
    """Saves batch predictions to JSON at the given path."""
    if output_path is None:
        output_path = os.path.join(_THIS_DIR, "outputs", "impact_predictions.json")
    results = predict_all_impacts()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    return output_path


# -----------------------------------------------------------------
# MANUAL RUN
# -----------------------------------------------------------------
if __name__ == "__main__":
    print("=== R101 prediction (no alternate supplied) ===")
    print(json.dumps(predict_impact("R101"), indent=2))

    print("\n=== R101 prediction (Network supplies R117 as alternate) ===")
    print(json.dumps(
        predict_impact("R101", alternate_route={"alternativeRoute": "R117", "alternativeRouteName": "Alternate Guwahati - Shillong Corridor"}),
        indent=2,
    ))

    print("\n=== R101 explanation ===")
    print(explain_impact("R101"))

    print("\n=== Batch predictions ===")
    all_results = predict_all_impacts()
    print(json.dumps(all_results, indent=2))

    path = save_predictions_to_json()
    print(f"\nSaved batch predictions to {path}")
