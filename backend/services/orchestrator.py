"""
orchestrator.py

The core of POST /api/v1/simulate-failure. Backend's job here is
ORCHESTRATION ONLY:

    validate  ->  call Network  ->  call ML  ->  combine  ->  respond

Nothing in this file recomputes a route, recomputes a risk score, or
invents an alternate road. Every number in the final response either
came directly from network_client (routing/failure/graph structure) or
from ml_client (risk/impact), or is a straightforward arithmetic
combination of the two (e.g. "extra distance" = alternate distance minus
original distance, both real GIS distance_km values).
"""

from . import network_client, ml_client, gis_data


class SimulationValidationError(ValueError):
    """Raised for bad input (unknown road_id/source/destination). main.py maps this to HTTP 404."""
    pass


def run_simulation(road_id: str, source: str = None, destination: str = None) -> dict:
    # ---- STEP 1: Validate the road ----
    if road_id not in gis_data.valid_road_ids():
        raise SimulationValidationError(f"Road '{road_id}' does not exist.")

    road = gis_data.get_road_by_id(road_id)  # raw GeoJSON properties: origin_district, destination_district, distance_km, name, ...

    # ---- STEP 2: Resolve source/destination ----
    # Per project decision: source/destination are OPTIONAL. If omitted,
    # default to the failed road's own origin/destination district (this
    # is real data taken from the road itself, not invented).
    source = source or road["origin_district"]
    destination = destination or road["destination_district"]

    valid_districts = gis_data.valid_district_ids()
    if source not in valid_districts:
        raise SimulationValidationError(f"Source district '{source}' does not exist.")
    if destination not in valid_districts:
        raise SimulationValidationError(f"Destination district '{destination}' does not exist.")

    # ---- STEP 3: Build/use the existing Network graph, find the original route ----
    graph = network_client.get_graph()
    original = network_client.find_route(graph, source, destination)

    # ---- STEP 4: Simulate failure of the exact road_id (Network module) ----
    failed_graph = network_client.simulate_failure(graph, road_id)

    # ---- STEP 5: Find the post-failure route for the requested trip ----
    alternative = network_client.find_route(failed_graph, source, destination)
    comparison = network_client.compare_routes(original, alternative)

    # ---- STEP 6: Determine the actual alternate ROAD (same origin+destination
    #      district as the failed road -- the project's Alternate Route Rule).
    #      This is a direct-edge lookup on the post-failure graph, so the
    #      failed road can never be returned as its own alternate, and
    #      nothing is hardcoded. ----
    direct_alternate = network_client.find_direct_alternate(
        failed_graph,
        origin_district=road["origin_district"],
        destination_district=road["destination_district"],
        exclude_road_id=road_id,
    )

    alternate_route_payload = {
        "alternativeRoute": direct_alternate["road_id"] if direct_alternate else None,
        "alternativeRouteName": direct_alternate["name"] if direct_alternate else None,
    }

    additional_distance_km = None
    if direct_alternate is not None:
        additional_distance_km = round(direct_alternate["distance_km"] - road["distance_km"], 2)

    # ---- STEP 7: ML risk for the failed road (existing ML module) ----
    risk = ml_client.get_road_risk(road_id)

    # ---- STEP 8: ML impact prediction, fed the REAL alternate-route info.
    #      No travel_delay_min_override: Network only has distance_km, not
    #      travel time or a speed assumption, so per project decision we do
    #      NOT invent a km->minutes conversion. ML's own (documented,
    #      explainable) estimate_travel_delay() formula is used as-is. ----
    impact = ml_client.predict_impact(road_id, alternate_route=alternate_route_payload)

    # ---- STEP 9: Combine into one frontend-friendly response ----
    recommendation = _build_recommendation(
        road_id=road_id,
        road_name=road.get("name"),
        risk_level=risk["riskLevel"],
        alternate=direct_alternate,
        destination_reachable=comparison["destination_reachable"],
        source=source,
        destination=destination,
    )

    return {
        "failedRoad": road_id,
        "roadName": road.get("name"),
        "originDistrict": road["origin_district"],
        "destinationDistrict": road["destination_district"],
        "source": source,
        "destination": destination,
        "riskScore": risk["riskScore"],
        "riskLevel": risk["riskLevel"],
        "destinationReachable": comparison["destination_reachable"],
        "originalRoute": original["path"],
        "alternateRoute": alternative["path"],
        "originalDistanceKm": original["cost"],
        "alternateDistanceKm": alternative["cost"],
        "alternativeRoute": alternate_route_payload["alternativeRoute"],
        "alternativeRouteName": alternate_route_payload["alternativeRouteName"],
        "additionalDistanceKm": additional_distance_km,
        "accessibilityBefore": impact["accessibilityBefore"],
        "accessibilityAfter": impact["accessibilityAfter"],
        "travelDelayMin": impact["travelDelayMin"],
        "locationsAffected": impact["locationsAffected"],
        "criticalFacilitiesAffected": impact["criticalFacilitiesAffected"],
        "recommendation": recommendation,
    }


def _build_recommendation(road_id, road_name, risk_level, alternate, destination_reachable, source, destination):
    label = f"{road_id} ({road_name})" if road_name else road_id

    if alternate is not None:
        return (
            f"{label} has failed ({risk_level.lower()} risk). "
            f"Use alternate corridor {alternate['road_id']} between the same districts "
            f"({source} -> {destination}); expect approximately "
            f"{alternate['distance_km']:.0f} km on the alternate route."
        )

    if destination_reachable:
        return (
            f"{label} has failed ({risk_level.lower()} risk). No direct alternate corridor "
            f"exists between {source} and {destination}, but the destination remains "
            f"reachable via a longer detour through other districts."
        )

    return (
        f"Critical disruption: {label} has failed ({risk_level.lower()} risk) and no route "
        f"currently connects {source} to {destination}. This is a single point of failure -- "
        f"flag for priority infrastructure investment or emergency logistics (airlift/portage)."
    )
