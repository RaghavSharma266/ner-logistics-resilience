"""
test_impact_prediction.py — AI/ML Module (Member 4)
=====================================================
Tests for road_risk_scoring.py and impact_prediction.py, built against
the project's real synthetic Assam datasets (NOT the old R101-R105 mock
dictionaries -- those no longer exist).

Run with:
    python -m unittest discover ml -v
or:
    python3 -m unittest test_impact_prediction.py -v
"""

import unittest
import os
import json

import road_risk_scoring
from road_risk_scoring import (
    road_segments,
    road_by_id,
    VALID_ROAD_IDS,
    compute_risk_score,
    score_to_level,
    get_road_risk,
    get_reference_risk,
)
from impact_prediction import (
    predict_impact,
    estimate_accessibility_before,
    estimate_accessibility_after,
    estimate_travel_delay,
    estimate_locations_affected,
    estimate_critical_facilities_affected,
    predict_all_impacts,
    save_predictions_to_json,
    facility_context_for_road,
    _get_road_safe,
)

CONTRACT_FIELDS = {
    "accessibilityBefore",
    "accessibilityAfter",
    "travelDelayMin",
    "locationsAffected",
    "criticalFacilitiesAffected",
}


class TestRoadRiskScoring(unittest.TestCase):
    """Covers spec items 1-5: dataset loading + risk score validity."""

    # 1. All synthetic roads load successfully
    def test_all_synthetic_roads_load(self):
        self.assertGreater(len(road_segments), 0)
        # every road_segments record has the fields compute_risk_score needs
        required_keys = {
            "road_id", "origin_district", "destination_district", "road_type",
            "rainfall_mm", "rainfall_anomaly_pct", "slope_percent",
            "elevation_range_m", "historical_landslide_count",
            "landslide_district_hazard",
        }
        for road in road_segments:
            self.assertTrue(required_keys.issubset(road.keys()))

    # 2. All road IDs are unique
    def test_road_ids_unique(self):
        ids = [r["road_id"] for r in road_segments]
        self.assertEqual(len(ids), len(set(ids)))

    # 3. Every road receives a valid riskScore
    def test_every_road_has_valid_risk_score(self):
        for road in road_segments:
            risk = get_road_risk(road)
            self.assertIn("riskScore", risk)
            self.assertIsInstance(risk["riskScore"], int)

    # 4. Every road receives HIGH/MEDIUM/LOW
    def test_every_road_has_valid_risk_level(self):
        for road in road_segments:
            risk = get_road_risk(road)
            self.assertIn(risk["riskLevel"], {"HIGH", "MEDIUM", "LOW"})

    # 5. riskScore is integer 0-100
    def test_risk_score_int_0_100(self):
        for road in road_segments:
            risk = get_road_risk(road)
            self.assertIsInstance(risk["riskScore"], int)
            self.assertTrue(0 <= risk["riskScore"] <= 100)

    # 16. No target leakage
    def test_no_target_leakage_in_road_segments_used_for_scoring(self):
        # road_segments records carry 'reference_risk_score'/'reference_risk_level'
        # for comparison only -- never the leakage-prone 'risk_score'/'risk_level'
        # key names that would tempt a predictor to read them directly.
        for road in road_segments:
            self.assertNotIn("risk_score", road)
            self.assertNotIn("risk_level", road)
            self.assertIn("reference_risk_score", road)
            self.assertIn("reference_risk_level", road)

        # compute_risk_score() must still produce a valid score even for a
        # road dict that has NO reference fields at all (proves the function
        # doesn't depend on them being present).
        sample = dict(road_by_id["R101"])
        del sample["reference_risk_score"]
        del sample["reference_risk_level"]
        score = compute_risk_score(sample)
        self.assertIsInstance(score, int)
        self.assertTrue(0 <= score <= 100)

        # get_reference_risk() is a clearly separate accessor, for
        # comparison/validation only.
        ref = get_reference_risk("R101")
        self.assertIn("riskScore", ref)
        self.assertIn("riskLevel", ref)

    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(road_risk_scoring.WEIGHTS.values()), 1.0, places=9)

    def test_score_to_level_thresholds(self):
        self.assertEqual(score_to_level(0), "LOW")
        self.assertEqual(score_to_level(34), "LOW")
        self.assertEqual(score_to_level(35), "MEDIUM")
        self.assertEqual(score_to_level(59), "MEDIUM")
        self.assertEqual(score_to_level(60), "HIGH")
        self.assertEqual(score_to_level(100), "HIGH")


class TestImpactPrediction(unittest.TestCase):

    # 6. R101 receives a valid prediction
    def test_r101_valid_prediction(self):
        result = predict_impact("R101")
        self.assertEqual(set(result.keys()), CONTRACT_FIELDS)
        self.assertTrue(0 <= result["accessibilityBefore"] <= 100)
        self.assertTrue(0 <= result["accessibilityAfter"] <= 100)

    # 7. R117 receives a valid prediction
    def test_r117_valid_prediction(self):
        result = predict_impact("R117")
        self.assertEqual(set(result.keys()), CONTRACT_FIELDS)
        self.assertTrue(0 <= result["accessibilityBefore"] <= 100)
        self.assertTrue(0 <= result["accessibilityAfter"] <= 100)

    # 8. R101/R117 treated as alternate-route scenario ONLY when Network supplies it
    def test_r101_r117_alternate_only_when_supplied(self):
        # No alternate supplied -> ML does NOT invent R117 as R101's alternate.
        no_alt = predict_impact("R101")
        # Network explicitly supplies R117 as the alternate (same origin/dest
        # district pair as R101, per the project's synthetic data design).
        with_alt = predict_impact(
            "R101",
            alternate_route={"alternativeRoute": "R117", "alternativeRouteName": "Alternate Guwahati - Shillong Corridor"},
        )
        self.assertEqual(set(no_alt.keys()), CONTRACT_FIELDS)
        self.assertEqual(set(with_alt.keys()), CONTRACT_FIELDS)
        # Having a real alternate should reduce the accessibility drop / delay
        # relative to the no-alternate case for the same road.
        self.assertGreater(with_alt["accessibilityAfter"], no_alt["accessibilityAfter"])
        self.assertLess(with_alt["travelDelayMin"], no_alt["travelDelayMin"])

    def test_alternate_route_must_share_districts(self):
        # R102 does NOT share R101's origin/destination district pair,
        # so it must be rejected as an alternate for R101.
        with self.assertRaises(ValueError):
            predict_impact(
                "R101",
                alternate_route={"alternativeRoute": "R102", "alternativeRouteName": "Wrong pair"},
            )

    # 9. No-alternate road works correctly with alternativeRoute=None
    def test_no_alternate_road_works(self):
        result = predict_impact(
            "R103",
            alternate_route={"alternativeRoute": None, "alternativeRouteName": None},
        )
        self.assertEqual(set(result.keys()), CONTRACT_FIELDS)
        # default (alternate_route omitted entirely) behaves the same way
        result_default = predict_impact("R103")
        self.assertEqual(result, result_default)

    # 3. Unknown road ID (kept from original suite, also covers item 12)
    def test_unknown_road_id_raises(self):
        with self.assertRaises(ValueError):
            predict_impact("R999")

    # Risk score at 0 / max, still valid
    def test_risk_score_zero(self):
        before = estimate_accessibility_before(0)
        self.assertTrue(0 <= before <= 100)
        after = estimate_accessibility_after(before, True, 0)
        self.assertTrue(0 <= after <= 100)
        delay = estimate_travel_delay(True, 0)
        self.assertGreaterEqual(delay, 0)

    def test_risk_score_max(self):
        before = estimate_accessibility_before(100)
        self.assertTrue(0 <= before <= 100)
        after = estimate_accessibility_after(before, False, 100)
        self.assertTrue(0 <= after <= 100)
        delay = estimate_travel_delay(False, 100)
        self.assertGreaterEqual(delay, 0)

    def test_invalid_risk_score_raises(self):
        with self.assertRaises(ValueError):
            estimate_accessibility_before(150)
        with self.assertRaises(ValueError):
            estimate_accessibility_before(-5)
        with self.assertRaises(ValueError):
            estimate_accessibility_before(0.5)  # not an int

    def test_negative_facility_count_raises(self):
        with self.assertRaises(ValueError):
            estimate_locations_affected(-1)
        with self.assertRaises(ValueError):
            estimate_critical_facilities_affected(1, -2)

    def test_critical_exceeds_total_raises(self):
        with self.assertRaises(ValueError):
            estimate_critical_facilities_affected(5, 2)  # 5 critical > 2 total
        with self.assertRaises(ValueError):
            predict_impact(
                "R101",
                alternate_route={"alternativeRoute": None, "alternativeRouteName": None},
                facility_context={"nearby_facilities": 1, "critical_facilities": 3},
            )

    # 10. Exact output field names
    def test_exact_output_field_names(self):
        result = predict_impact("R101")
        self.assertEqual(set(result.keys()), CONTRACT_FIELDS)

    # 11. All impact output values have correct types/ranges
    def test_output_types_and_ranges_all_roads(self):
        for road in road_segments:
            result = predict_impact(road["road_id"])
            for field in CONTRACT_FIELDS:
                self.assertIsInstance(result[field], int, f"{field} should be int, got {type(result[field])}")
            self.assertTrue(0 <= result["accessibilityBefore"] <= 100)
            self.assertTrue(0 <= result["accessibilityAfter"] <= 100)
            self.assertGreaterEqual(result["travelDelayMin"], 0)
            self.assertGreaterEqual(result["locationsAffected"], 0)
            self.assertGreaterEqual(result["criticalFacilitiesAffected"], 0)
            self.assertLessEqual(result["criticalFacilitiesAffected"], result["locationsAffected"])

    # 12. Invalid road IDs raise clear errors
    def test_invalid_road_id_raises_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            _get_road_safe("R999")
        self.assertIn("R999", str(ctx.exception))
        with self.assertRaises(ValueError):
            predict_impact("NOT_A_ROAD")

    # 13. Invalid alternate-route objects raise clear errors
    def test_malformed_alternate_route_raises(self):
        with self.assertRaises(ValueError):
            predict_impact("R101", alternate_route="not-a-dict", facility_context={"nearby_facilities": 1, "critical_facilities": 0})
        with self.assertRaises(ValueError):
            predict_impact("R101", alternate_route={"wrongKey": "R117"}, facility_context={"nearby_facilities": 1, "critical_facilities": 0})
        with self.assertRaises(ValueError):
            predict_impact("R101", alternate_route={"alternativeRoute": 123}, facility_context={"nearby_facilities": 1, "critical_facilities": 0})

    # 14. Invalid facility contexts raise clear errors
    def test_malformed_facility_context_raises(self):
        with self.assertRaises(ValueError):
            predict_impact("R101", alternate_route={"alternativeRoute": None, "alternativeRouteName": None}, facility_context="not-a-dict")
        with self.assertRaises(ValueError):
            predict_impact("R101", alternate_route={"alternativeRoute": None, "alternativeRouteName": None}, facility_context={"nearby_facilities": 1})

    # 15. Batch prediction works for all synthetic roads
    def test_batch_prediction_all_roads(self):
        results = predict_all_impacts()
        self.assertEqual(len(results), len(road_segments))
        seen_ids = set()
        for r in results:
            self.assertIn("road_id", r)
            seen_ids.add(r["road_id"])
            for field in CONTRACT_FIELDS:
                self.assertIn(field, r)
        self.assertEqual(seen_ids, VALID_ROAD_IDS)

    def test_json_export(self):
        path = os.path.join(os.path.dirname(__file__), "outputs", "test_impact_predictions.json")
        saved_path = save_predictions_to_json(path)
        self.assertTrue(os.path.exists(saved_path))
        with open(saved_path) as f:
            data = json.load(f)
        self.assertEqual(len(data), len(road_segments))
        os.remove(saved_path)

    def test_output_types_are_int(self):
        result = predict_impact("R101")
        for field in CONTRACT_FIELDS:
            self.assertIsInstance(result[field], int, f"{field} should be int, got {type(result[field])}")

    def test_facility_context_derived_from_real_dataset(self):
        # No facility_context passed -> derived from facilities_assam_synthetic_v2.xlsx
        # via the road's origin/destination district, not a mock table.
        road = road_by_id["R101"]
        ctx = facility_context_for_road(road)
        self.assertIn("nearby_facilities", ctx)
        self.assertIn("critical_facilities", ctx)
        self.assertGreaterEqual(ctx["nearby_facilities"], 0)
        self.assertGreaterEqual(ctx["critical_facilities"], 0)
        self.assertLessEqual(ctx["critical_facilities"], ctx["nearby_facilities"])

        result = predict_impact("R101")
        result_explicit = predict_impact("R101", facility_context=ctx)
        self.assertEqual(result["locationsAffected"], result_explicit["locationsAffected"])
        self.assertEqual(result["criticalFacilitiesAffected"], result_explicit["criticalFacilitiesAffected"])

    def test_travel_delay_override(self):
        # Backend/Network can supply a real delay in minutes instead of the
        # prototype formula.
        result = predict_impact("R101", travel_delay_min_override=17)
        self.assertEqual(result["travelDelayMin"], 17)
        with self.assertRaises(ValueError):
            predict_impact("R101", travel_delay_min_override=-5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
