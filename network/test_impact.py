"""
test_impact.py

Run this file directly to see the impact-analysis layer working
on top of the already-tested network simulator.

    python test_impact.py

This does NOT touch or re-test graph_builder.py, simulator.py, or
test_scenarios.py -- it only exercises the new impact.py.
"""

from graph_builder import build_network
from impact import calculate_impact, CRITICAL_LOCATIONS


def test_impact_no_failure_baseline():
    print("\n--- Baseline: impact of a road NOT on any critical route ---")
    graph = build_network()
    # R3 (A-D) IS on some critical paths, so let's use R2 (B-C) here,
    # which sits off to the side of the shortest routes from A.
    result = calculate_impact(graph, road_id="R2", origin="A")
    print("Critical locations:", CRITICAL_LOCATIONS)
    print(result)


def test_impact_with_real_disruption():
    print("\n--- Fail R4 (D-C): affects hospital_1 (node C) ---")
    graph = build_network()
    result = calculate_impact(graph, road_id="R4", origin="A")
    print(result)
    assert "hospital_1" in result["affected_locations"], \
        "Expected hospital_1 to be affected when R4 fails"
    print("Check passed: hospital_1 correctly flagged as affected.")


def test_impact_full_disconnection():
    print("\n--- Disconnect village_1 (node D) entirely ---")
    graph = build_network()

    # Temporarily give village_1 a single road in ("R3": A-D),
    # and remove D's other connection (R4: D-C) so failing R3
    # fully isolates it.
    graph.remove_edge("D", "C")  # remove R4 first for this test only

    result = calculate_impact(graph, road_id="R3", origin="A")
    print(result)
    assert result["locations"]["village_1"]["status"] == "unreachable", \
        "Expected village_1 to be unreachable when its only road fails"
    print("Check passed: village_1 correctly flagged as unreachable.")


if __name__ == "__main__":
    test_impact_no_failure_baseline()
    test_impact_with_real_disruption()
    test_impact_full_disconnection()
