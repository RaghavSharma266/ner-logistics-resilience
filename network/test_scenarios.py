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
    # key=road_id keeps this consistent with how graph_builder.py
    # keys every edge, now that the graph is a MultiGraph.
    graph.add_edge("A", "E", key="R5", road_id="R5", distance=5)

    original = find_route(graph, "A", "E")
    print_route_result("Original route to E", original)

    failed_graph = simulate_road_failure(graph, "R5")
    alternative = find_route(failed_graph, "A", "E")
    print_route_result("Route to E after R5 fails", alternative)

    comparison = compare_routes(original, alternative)
    print("Comparison:", comparison)


def test_6_parallel_roads():
    """
    Dedicated parallel-road scenario (MultiGraph support).

    A -- R110 (10 km) -- B
    A -- R113 (14 km) -- B

    Checks:
    - both roads exist at once
    - shortest routing initially prefers R110 (cheaper)
    - failing R110 removes ONLY R110, R113 still exists
    - routing after R110 fails uses R113
    - failing R113 afterwards removes the remaining parallel road
    - with no roads left between A and B, B becomes unreachable
    """
    print("\n--- Test 6: Parallel roads A <-> B (R110 vs R113) ---")

    graph = build_network()
    # Add a second, more expensive parallel road between A and B,
    # on top of the existing R1 (A-B, distance 10) from build_network().
    # To keep this scenario self-contained and match the exact
    # example in the brief, we build a small dedicated graph instead
    # of reusing R1, so road_ids/costs match exactly (R110=10, R113=14).
    import networkx as nx
    parallel_graph = nx.MultiGraph()
    parallel_graph.add_nodes_from(["A", "B"])
    parallel_graph.add_edge("A", "B", key="R110", road_id="R110", distance=10)
    parallel_graph.add_edge("A", "B", key="R113", road_id="R113", distance=14)

    # Both roads exist at once.
    edge_count = parallel_graph.number_of_edges("A", "B")
    print("Number of parallel roads A-B:", edge_count)
    assert edge_count == 2

    # Shortest routing initially prefers R110 (cost 10).
    original = find_route(parallel_graph, "A", "B")
    print_route_result("Route before any failure", original)
    assert original["cost"] == 10

    # Fail R110. Only R110 should be removed; R113 must remain.
    after_r110_fails = simulate_road_failure(parallel_graph, "R110")
    r113_still_present = any(
        data.get("road_id") == "R113"
        for _, _, data in after_r110_fails.edges(data=True)
    )
    r110_still_present = any(
        data.get("road_id") == "R110"
        for _, _, data in after_r110_fails.edges(data=True)
    )
    print("After R110 fails -- R113 present:", r113_still_present, "| R110 present:", r110_still_present)
    assert r113_still_present is True
    assert r110_still_present is False

    # Routing after R110 fails should now use R113 (cost 14).
    alt_route = find_route(after_r110_fails, "A", "B")
    print_route_result("Route after R110 fails", alt_route)
    assert alt_route["reachable"] is True
    assert alt_route["cost"] == 14

    comparison = compare_routes(original, alt_route)
    print("Comparison (R110 failure):", comparison)
    assert comparison["cost_increase"] == 4

    # Confirm the graph passed into simulate_road_failure was untouched.
    original_still_has_both = parallel_graph.number_of_edges("A", "B") == 2
    print("Original parallel_graph still has both roads:", original_still_has_both)
    assert original_still_has_both

    # Now fail R113 as well, on top of the already-R110-failed graph.
    after_both_fail = simulate_road_failure(after_r110_fails, "R113")
    final_route = find_route(after_both_fail, "A", "B")
    print_route_result("Route after BOTH R110 and R113 fail", final_route)
    assert final_route["reachable"] is False

    final_comparison = compare_routes(original, final_route)
    print("Comparison (both failed):", final_comparison)
    assert final_comparison["destination_reachable"] is False


if __name__ == "__main__":
    test_1_normal_route()
    test_2_3_4_road_failure_and_alternative()
    test_5_no_alternative_route()
    test_6_parallel_roads()
    print("\nAll test_scenarios.py checks passed.")
