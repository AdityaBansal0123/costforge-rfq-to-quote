"""Unit Test Suite for CostForge Chakan Costing Engine, Rate Versioning & AI Guardrails."""

import unittest
from backend.costing_engine import (
    AIExtractedField,
    MaterialRate,
    MachineRate,
    PartRFQ,
    RateMasterSnapshot,
    RoutingOperation,
    compute_cost_at_volume,
    get_seeded_rate_masters,
    validate_quote_release,
)
from backend.ai_intake import detect_document_conflicts, suggest_routing_from_history


class TestCostForgeEngine(unittest.TestCase):
    def setUp(self):
        self.rate_masters = get_seeded_rate_masters()
        # Sample 1: RFQ-2611-014 (Company B, Rear wheel spindle, EN8, 0.61 kg, 180,000/yr, 3.2 min @ ₹850/hr)
        self.rfq_014 = PartRFQ(
            rfq_no="RFQ-2611-014",
            customer="Company B (two-wheelers)",
            part_name="Rear wheel spindle",
            material_grade="EN8",
            gross_wt_kg=0.61,
            net_wt_kg=0.48,
            annual_volume=180000,
            rate_snapshot_id="RM-2026-Q4",
            operations=[
                RoutingOperation(10, "Band Sawing & Center Faced", 0.6, 850.0, 20.0),
                RoutingOperation(20, "CNC Twin-Spindle Turning", 1.8, 850.0, 45.0),
                RoutingOperation(30, "Cold Spline Rolling & Grinding", 0.8, 850.0, 25.0),
            ],
            rejection_pct=1.5,
            overhead_pct=14.0,
            packing_per_pc_inr=1.40,
            freight_per_pc_inr=1.10,
            margin_pct=12.0,
            batches_per_year=12,
        )

    def test_sample_rfq_014_exact_cost_breakup(self):
        """Verifies exact deterministic costing math for RFQ-2611-014 at 180,000 pcs/yr."""
        res = compute_cost_at_volume(self.rfq_014, self.rate_masters, 180000)
        self.assertAlmostEqual(res["gross_material_cost"], 47.58, places=2)
        self.assertAlmostEqual(res["scrap_credit"], 3.74, places=2)
        self.assertAlmostEqual(res["net_material_cost"], 43.84, places=2)
        self.assertAlmostEqual(res["total_cycle_min"], 3.20, places=2)
        self.assertAlmostEqual(res["run_cost_per_pc"], 45.33, places=2)
        self.assertAlmostEqual(res["unit_price_ex_gst"], 111.39, delta=0.05)
        self.assertAlmostEqual(res["gst_18_pct"], round(res["unit_price_ex_gst"] * 0.18, 2), places=2)
        self.assertTrue(res["requires_sales_head_approval"])

    def test_multi_volume_economies_of_scale(self):
        """Unit price must decrease monotonically as volume increases from 50% to 100% to 150%."""
        c_low = compute_cost_at_volume(self.rfq_014, self.rate_masters, 90000)
        c_base = compute_cost_at_volume(self.rfq_014, self.rate_masters, 180000)
        c_high = compute_cost_at_volume(self.rfq_014, self.rate_masters, 270000)
        self.assertGreater(c_low["unit_price_ex_gst"], c_base["unit_price_ex_gst"])
        self.assertGreater(c_base["unit_price_ex_gst"], c_high["unit_price_ex_gst"])

    def test_rate_master_version_immutability(self):
        """Adding a new Rate Master snapshot must never alter quotes locked to an older snapshot."""
        before = compute_cost_at_volume(self.rfq_014, self.rate_masters, 180000)
        # Publish new November rate revision with +15% steel price jump
        self.rate_masters["RM-2026-NOV"] = RateMasterSnapshot(
            snapshot_id="RM-2026-NOV",
            effective_from="2026-11-05",
            effective_to=None,
            status="Active",
            materials={"EN8": MaterialRate("EN8", "BS 970", 92.00, 35.00)},
            machines={"CNC-TURN-CELL": MachineRate("CNC-TURN-CELL", "CNC", 950.0)},
        )
        after = compute_cost_at_volume(self.rfq_014, self.rate_masters, 180000)
        self.assertEqual(before["unit_price_ex_gst"], after["unit_price_ex_gst"])

    def test_ai_unaccepted_field_blocks_quote_release(self):
        """Quotes with unaccepted AI-extracted fields must be blocked from release."""
        self.rfq_014.ai_fields = [
            AIExtractedField("material_grade", "EN8", "Drawing OCR", 54, accepted_by_estimator=False)
        ]
        with self.assertRaises(PermissionError):
            validate_quote_release(self.rfq_014, self.rate_masters, actor_role="sales_head")

    def test_sales_head_approval_gate_above_25_lakh(self):
        """Quotes > ₹25 Lakh annual value cannot be released by an Estimator without Sales Head approval."""
        self.rfq_014.ai_fields = [
            AIExtractedField("material_grade", "EN8", "Drawing OCR", 98, accepted_by_estimator=True)
        ]
        self.rfq_014.approved_by_sales_head = None
        with self.assertRaises(PermissionError):
            validate_quote_release(self.rfq_014, self.rate_masters, actor_role="estimator")

        # Sales Head can release or once approved_by_sales_head is populated
        validate_quote_release(self.rfq_014, self.rate_masters, actor_role="sales_head")

    def test_ai_conflict_detection_and_routing_similarity(self):
        """Verifies conflict detection when Excel and Drawing disagree on material grade."""
        fields = detect_document_conflicts(
            {"material": "EN8", "gross_wt_kg": "0.61"},
            {"material": "40Cr4", "notes": "blurred scan"},
        )
        mat_field = next(f for f in fields if f.key == "material_grade")
        self.assertLess(mat_field.confidence_pct, 60)
        self.assertIn("CONFLICT", mat_field.source_document)

        history = [
            {"quote_no": "Q1", "material": "EN8", "gross_wt_kg": 0.59, "part": "Rear Axle Spindle"},
            {"quote_no": "Q2", "material": "40Cr4 forging", "gross_wt_kg": 4.60, "part": "Lift Arm"},
        ]
        matches = suggest_routing_from_history("EN8", 0.61, history)
        self.assertEqual(matches[0]["quote_no"], "Q1")
        self.assertGreater(matches[0]["similarity_pct"], 95.0)


if __name__ == "__main__":
    unittest.main()
