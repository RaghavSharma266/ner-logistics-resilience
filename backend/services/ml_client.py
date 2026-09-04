"""
ml_client.py

Thin wrapper around the EXISTING, UNMODIFIED ML module
(`ml/road_risk_scoring.py`, `ml/impact_prediction.py`). Does not
reimplement the risk-scoring formula or the impact-estimation formulas --
only calls into them and translates ml's ValueErrors into a form the
orchestrator can turn into clean HTTP errors.
"""

from . import path_setup  # noqa: F401  (must run before the imports below)

import road_risk_scoring  # ml/road_risk_scoring.py, unmodified
import impact_prediction  # ml/impact_prediction.py, unmodified

VALID_ROAD_IDS = road_risk_scoring.VALID_ROAD_IDS
road_by_id = road_risk_scoring.road_by_id  # road_id -> ML feature record (has origin/destination district, distance_km, etc.)


def get_road_risk(road_id: str) -> dict:
    """
    Returns {"riskLevel": "HIGH"/"MEDIUM"/"LOW", "riskScore": int 0-100}
    for a road, computed live by ml.road_risk_scoring.get_road_risk() --
    the actual weighted-formula model, not a static/reference value.
    """
    road = road_by_id.get(road_id)
    if road is None:
        raise ValueError(f"Unknown road_id: {road_id!r}")
    return road_risk_scoring.get_road_risk(road)


def predict_impact(road_id: str, alternate_route: dict, facility_context: dict = None, travel_delay_min_override: int = None) -> dict:
    """
    Calls ml.impact_prediction.predict_impact() directly. `alternate_route`
    must be the contract-shaped dict Network's find_direct_alternate()
    result gets translated into by the orchestrator:
        {"alternativeRoute": "R117" | None, "alternativeRouteName": str | None}

    travel_delay_min_override is left None unless the Network module can
    supply a *real* minutes-based delay -- see backend/README.md
    "Travel delay" section for why that override is not used in this
    prototype (Network only has distance_km, not travel time/speed data;
    inventing a km->minutes conversion was explicitly ruled out).
    """
    return impact_prediction.predict_impact(
        road_id,
        alternate_route=alternate_route,
        facility_context=facility_context,
        travel_delay_min_override=travel_delay_min_override,
    )
