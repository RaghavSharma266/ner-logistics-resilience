"""
test_scenarios.py

Run this file directly to see the network simulator working
end-to-end on the tiny artificial network.

    python test_scenarios.py

This walks through the tests described in Section 6 of the
project doc: normal routing, road failure, alternate routing,
cost comparison, and a total-disconnection case.
"""

from graph_builder import build_network
from simulator import find_route, simulate_road_failure, compare_routes


def print_route_result(label: str, result: dict):
    if result["reachable"]:
        path_str = " -> ".join(result["path"])
        print(f"{label}: {path_str}  (cost = {result['cost']})")
    else:
        print(f"{label}: NOT REACHABLE")


def test_1_normal_route():
    print("\n--- Test 1: Normal route A -> C ---")
    graph = build_network()
    result = find_route(graph, "A", "C")
    print_route_result("Route", result)


def test_2_3_4_road_failure_and_alternative():
    print("\n--- Test 2/3/4: Fail R4 (D-C), find alternative, compare cost ---")
    graph = build_network()

    original = find_route(graph, "A", "C")
    print_route_result("Original route", original)

    # R4 (D-C) is on the shortest A-C route (A -> D -> C), so failing it
    # should actually force a detour through B, unlike R2 which wasn't
    # being used at all.
    failed_graph = simulate_road_failure(graph, "R4")
    alternative = find_route(failed_graph, "A", "C")
    print_route_result("Route after R4 fails", alternative)

    comparison = compare_routes(original, alternative)
    print("Comparison:", comparison)

    # Confirm the ORIGINAL graph was not modified.
    still_has_r4 = any(
        data.get("road_id") == "R4" for _, _, data in graph.edges(data=True)
    )
    print("Original graph still has R4:", still_has_r4)


def test_5_no_alternative_route():
    print("\n--- Test 5: Disconnect a location entirely ---")
    graph = build_network()

    # Add an isolated location "E" connected to A only by road "R5".
    graph.add_edge("A", "E", road_id="R5", distance=5)

    original = find_route(graph, "A", "E")
    print_route_result("Original route to E", original)

    failed_graph = simulate_road_failure(graph, "R5")
    alternative = find_route(failed_graph, "A", "E")
    print_route_result("Route to E after R5 fails", alternative)

    comparison = compare_routes(original, alternative)
    print("Comparison:", comparison)


if __name__ == "__main__":
    test_1_normal_route()
    test_2_3_4_road_failure_and_alternative()
    test_5_no_alternative_route()
