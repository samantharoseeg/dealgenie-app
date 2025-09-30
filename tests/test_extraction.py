"""
Acceptance Test Suite for CRE Extraction Engine
Tests the 5 scenarios from Document 12 with comprehensive validation
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cre_extraction_engine import CREExtractionEngine
import json


class TestCREExtraction(unittest.TestCase):
    """Test suite for CRE extraction scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.maxDiff = None  # Show full diff on failures

    def test_scenario_1_mf_garden_partial_data(self):
        """
        Scenario 1: Multifamily Garden with Partial Data
        - Missing: Expense ratio, replacement reserves
        - Should identify gaps and suggest industry standard assumptions
        """
        # OCR text simulating partial MF data
        ocr_text = """
        INVESTMENT OPPORTUNITY - GARDEN APARTMENTS

        Property: Willowbrook Gardens
        Location: Austin, TX
        Type: Multifamily - Garden/Low-rise

        Purchase Price: $45,000,000
        Units: 250
        Average Rent: $1,450/month
        Occupancy: 93%

        NOI: $2,700,000

        Loan Terms:
        Loan Amount: $31,500,000
        Interest Rate: 6.25%
        Amortization: 30 years

        Cap Rate: 6.0%
        Exit Cap: 6.5%
        """

        # Initialize engine
        engine = CREExtractionEngine("multifamily", "garden_lowrise")
        result = engine.extract(ocr_text)

        # Test 1: Verify correct fields extracted
        self.assertIn("purchase_price", result["ingested"])
        self.assertEqual(result["ingested"]["purchase_price"], 45000000)
        self.assertEqual(result["ingested"]["units"], 250)
        self.assertEqual(result["ingested"]["avg_rent"], 1450)
        self.assertAlmostEqual(result["ingested"]["occupancy_pct"], 0.93, places=2)
        self.assertEqual(result["ingested"]["noi"], 2700000)

        # Test 2: Verify derived metrics
        self.assertIn("cap_rate", result["derived"])
        self.assertAlmostEqual(result["derived"]["cap_rate"], 0.06, places=3)

        # Test 3: Check for missing fields identification
        missing_fields = [item["metric"] for item in result["unknown"]]
        self.assertIn("expense_ratio", missing_fields)
        self.assertIn("replacement_reserves", missing_fields)

        # Test 4: Verify risk ranking
        high_risks = [r for r in result["risks_ranked"] if r["severity"] == "HIGH"]
        self.assertTrue(len(high_risks) > 0, "Should identify high severity risks")

        # Check for DSCR risk if it's below threshold
        dscr_risks = [r for r in result["risks_ranked"] if "dscr" in r["metric"].lower()]
        if dscr_risks:
            # Should have quantified mitigations
            for risk in dscr_risks:
                self.assertTrue(len(risk["mitigations"]) > 0)
                # Check for dollar impacts
                dollar_mitigations = [m for m in risk["mitigations"]
                                     if "dollar_impact" in m and m["dollar_impact"] != 0]
                self.assertTrue(len(dollar_mitigations) > 0,
                               "DSCR risk should have dollar-quantified mitigations")

        # Test 5: Verify confidence levels
        self.assertIn("confidence", result)
        # High confidence for directly stated values
        if "purchase_price" in result["confidence"]:
            self.assertIn(result["confidence"]["purchase_price"], ["High", "Medium"])

        # Test 6: Check completeness score
        self.assertIn("completeness", result)
        self.assertLess(result["completeness"], 1.0,
                       "Completeness should be less than 100% due to missing fields")

    def test_scenario_2_office_suburban_aggressive_exit(self):
        """
        Scenario 2: Office Suburban with Aggressive Exit Cap
        - Exit cap lower than entry (cap compression)
        - Should flag aggressive assumption
        """
        ocr_text = """
        SUBURBAN OFFICE ACQUISITION

        Asset: Tech Center Plaza
        Class: B+ Suburban Office
        Location: Plano, TX

        Purchase Price: $52,500,000
        Square Feet: 175,000

        In-Place NOI: $3,412,500
        Entry Cap Rate: 6.5%

        Stabilized NOI: $3,675,000
        Exit Cap Rate: 6.0%
        Hold Period: 5 years

        Loan Amount: $36,750,000
        Rate: SOFR + 275 bps

        WALT: 4.2 years
        Occupancy: 88%
        TI Allowance: $35/SF for new leases
        Parking Ratio: 3.5 spaces per 1,000 SF
        """

        engine = CREExtractionEngine("office", "suburban")
        result = engine.extract(ocr_text)

        # Test 1: Verify fields extracted
        self.assertEqual(result["ingested"]["purchase_price"], 52500000)
        self.assertEqual(result["ingested"]["square_feet"], 175000)
        self.assertAlmostEqual(result["ingested"]["entry_cap"], 0.065, places=3)
        self.assertAlmostEqual(result["ingested"]["exit_cap"], 0.06, places=3)

        # Test 2: Verify SOFR spread parsing
        self.assertIn("interest_rate_spread_bps", result["ingested"])
        self.assertEqual(result["ingested"]["interest_rate_spread_bps"], 275)

        # Test 3: Check for cap compression warning
        cap_warnings = [w for w in result.get("validation_warnings", [])
                       if "cap" in w.get("type", "").lower()]
        self.assertTrue(len(cap_warnings) > 0,
                       "Should warn about exit cap lower than entry cap")

        # Test 4: Verify WALT risk (4.2 years is borderline)
        walt_risks = [r for r in result["risks_ranked"]
                     if "walt" in r["metric"].lower()]
        if walt_risks:
            # Should suggest renewal strategies
            for risk in walt_risks:
                renewal_mitigations = [m for m in risk["mitigations"]
                                      if "renewal" in m["action"].lower()]
                self.assertTrue(len(renewal_mitigations) > 0)

        # Test 5: Check TI reserves calculation
        ti_risks = [r for r in result["risks_ranked"]
                   if "ti" in r["metric"].lower() or "tenant_improvement" in r["metric"].lower()]
        if ti_risks and ti_risks[0]["severity"] in ["HIGH", "MEDIUM"]:
            # Should calculate TI reserve needs
            for risk in ti_risks:
                reserve_mitigations = [m for m in risk["mitigations"]
                                      if "reserve" in m["action"].lower()]
                self.assertTrue(len(reserve_mitigations) > 0)

    def test_scenario_3_industrial_bulk_missing_specs(self):
        """
        Scenario 3: Industrial Bulk Distribution with Missing Physical Specs
        - Missing: Clear height, dock doors, power
        - Should flag as critical for industrial valuation
        """
        ocr_text = """
        INDUSTRIAL ACQUISITION OPPORTUNITY

        Property Type: Bulk Distribution Warehouse
        Location: Dallas, TX

        Building Size: 450,000 SF
        Land: 25 acres

        Purchase Price: $67,500,000
        NOI: $4,050,000
        Cap Rate: 6.0%

        Occupancy: 100%
        Tenant: Amazon (investment grade)
        Lease Term Remaining: 7.5 years

        Loan: $47,250,000
        LTV: 70%
        Rate: 6.5%
        DSCR: 1.31x
        """

        engine = CREExtractionEngine("industrial", "bulk_distribution")
        result = engine.extract(ocr_text)

        # Test 1: Verify extracted fields
        self.assertEqual(result["ingested"]["square_feet"], 450000)
        self.assertEqual(result["ingested"]["purchase_price"], 67500000)
        self.assertAlmostEqual(result["ingested"]["ltv"], 0.70, places=2)

        # Test 2: Check for missing critical specs
        missing_fields = [item["metric"] for item in result["unknown"]]
        self.assertIn("clear_height", missing_fields)
        self.assertIn("dock_doors", missing_fields)

        # Test 3: These missing specs should be flagged as high importance
        clear_height_missing = [item for item in result["unknown"]
                               if item["metric"] == "clear_height"]
        if clear_height_missing:
            # Should explain why clear height matters
            self.assertIn("required", clear_height_missing[0].get("explanation", "").lower())

        # Test 4: Despite missing specs, strong credit should be recognized
        known_strengths = [item for item in result["known"]
                          if "amazon" in str(item.get("value", "")).lower() or
                          "investment grade" in str(item.get("value", "")).lower()]
        self.assertTrue(len(known_strengths) > 0, "Should recognize investment grade tenant")

        # Test 5: Price per SF benchmark check
        price_psf = 67500000 / 450000
        self.assertAlmostEqual(price_psf, 150, places=0)

        # Should compare to industrial benchmarks
        bench_comparisons = [b for b in result["bench_compare"]
                            if "price_psf" in b.get("metric", "").lower()]
        self.assertTrue(len(bench_comparisons) > 0)

    def test_scenario_4_grocery_retail_cotenancy(self):
        """
        Scenario 4: Grocery-Anchored Retail with Co-tenancy Risk
        - Anchor term < 10 years
        - Should calculate co-tenancy impact
        """
        ocr_text = """
        GROCERY-ANCHORED SHOPPING CENTER

        Property: Village Shopping Center
        Type: Grocery-Anchored Retail

        Total GLA: 125,000 SF
        Anchor: Kroger (45,000 SF)
        Anchor Lease Expiration: 6.5 years

        Purchase Price: $31,250,000
        NOI: $2,187,500
        Cap Rate: 7.0%

        Occupancy: 94%
        Inline Occupancy: 88%

        Average Inline Rent: $22/SF NNN
        Anchor Rent: $12/SF NNN

        Sales/SF (inline tenants): $385

        Financing:
        LTV: 65%
        Loan Amount: $20,312,500
        Interest Rate: 6.75%
        Amortization: 25 years

        Co-tenancy Clauses: Yes - 30% of inline tenants
        """

        engine = CREExtractionEngine("retail", "grocery_anchored")
        result = engine.extract(ocr_text)

        # Test 1: Verify key fields
        self.assertEqual(result["ingested"]["purchase_price"], 31250000)
        self.assertEqual(result["ingested"]["square_feet"], 125000)
        self.assertAlmostEqual(result["ingested"]["cap_rate"], 0.07, places=3)

        # Test 2: Anchor term should trigger risk
        anchor_risks = [r for r in result["risks_ranked"]
                       if "anchor" in r["metric"].lower()]
        self.assertTrue(len(anchor_risks) > 0, "Should identify anchor term risk")

        # Test 3: Co-tenancy impact should be calculated
        for risk in anchor_risks:
            cotenancy_mitigations = [m for m in risk["mitigations"]
                                    if "co-tenancy" in m["action"].lower() or
                                    "cotenancy" in m["action"].lower()]
            if cotenancy_mitigations:
                # Should quantify the potential rent reduction
                impact_mitigation = [m for m in cotenancy_mitigations
                                   if "dollar_impact" in m and m["dollar_impact"] < 0]
                self.assertTrue(len(impact_mitigation) > 0,
                               "Should quantify co-tenancy dollar impact")

        # Test 4: Should suggest ROFR or backfill strategies
        for risk in anchor_risks:
            strategic_mitigations = [m for m in risk["mitigations"]
                                    if "rofr" in m["action"].lower() or
                                    "backfill" in m["action"].lower() or
                                    "loi" in m["action"].lower()]
            self.assertTrue(len(strategic_mitigations) > 0,
                           "Should suggest ROFR or backfill LOI strategies")

        # Test 5: Sales/SF benchmark comparison
        sales_comparisons = [b for b in result["bench_compare"]
                            if "sales" in b.get("metric", "").lower()]
        if sales_comparisons:
            # $385/SF should be evaluated against benchmarks
            self.assertTrue(sales_comparisons[0]["value"] == 385)

    def test_scenario_5_hotel_limited_missing_pip(self):
        """
        Scenario 5: Limited Service Hotel Missing PIP
        - Missing: PIP costs, brand requirements
        - Low GOP margin should trigger exit cap widening
        """
        ocr_text = """
        LIMITED SERVICE HOTEL ACQUISITION

        Property: Hampton Inn Airport
        Type: Limited Service Hotel
        Keys: 125 rooms

        Purchase Price: $15,625,000
        Price Per Key: $125,000

        Financial Performance:
        Occupancy: 68%
        ADR: $95
        RevPAR: $64.60

        Total Revenue: $2,950,000
        NOI: $887,500
        Cap Rate: 5.68%

        GOP Margin: 28%

        Debt:
        Loan Amount: $10,937,500
        LTV: 70%
        Interest Rate: 7.25%
        DSCR: 1.08x

        Brand: Hilton
        Franchise Agreement: 8 years remaining

        Market Comps:
        Comp Set RevPAR: $78
        Market Occupancy: 72%
        """

        engine = CREExtractionEngine("hospitality", "limited_service")
        result = engine.extract(ocr_text)

        # Test 1: Verify hotel metrics
        self.assertEqual(result["ingested"]["keys"], 125)
        self.assertEqual(result["ingested"]["adr"], 95)
        self.assertAlmostEqual(result["ingested"]["revpar"], 64.60, places=1)
        self.assertAlmostEqual(result["ingested"]["gop_margin_pct"], 0.28, places=2)

        # Test 2: Check for missing PIP identification
        missing_fields = [item["metric"] for item in result["unknown"]]
        self.assertIn("pip_cost_per_key", missing_fields)

        # Test 3: Low GOP margin should trigger exit cap risk
        gop_risks = [r for r in result["risks_ranked"]
                    if "gop" in r["metric"].lower()]
        if gop_risks:
            # Should calculate exit cap widening
            for risk in gop_risks:
                cap_widening_mitigations = [m for m in risk["mitigations"]
                                           if "exit cap" in m["action"].lower() or
                                           "cap widening" in m["action"].lower()]
                self.assertTrue(len(cap_widening_mitigations) > 0,
                               "Low GOP should trigger exit cap widening calculation")

        # Test 4: Low DSCR should be high severity risk
        dscr_risks = [r for r in result["risks_ranked"]
                     if "dscr" in r["metric"].lower()]
        self.assertTrue(len(dscr_risks) > 0, "DSCR of 1.08x should be flagged")
        if dscr_risks:
            self.assertEqual(dscr_risks[0]["severity"], "HIGH",
                           "DSCR below 1.20x should be HIGH severity")

        # Test 5: RevPAR gap should be identified
        revpar_comparisons = [b for b in result["bench_compare"]
                             if "revpar" in b.get("metric", "").lower()]
        if revpar_comparisons:
            # Should show underperformance vs comp set
            self.assertTrue(revpar_comparisons[0]["value"] < 78)

        # Test 6: Should suggest revenue management improvements
        revenue_mitigations = []
        for risk in result["risks_ranked"]:
            revenue_mitigations.extend([m for m in risk["mitigations"]
                                       if "revenue management" in m["action"].lower() or
                                       "revpar" in m["action"].lower()])
        self.assertTrue(len(revenue_mitigations) > 0,
                       "Should suggest revenue management system")


class TestCrossValidation(unittest.TestCase):
    """Test cross-validation logic"""

    def test_cap_rate_noi_validation(self):
        """Test that cap rate and NOI cross-validate correctly"""
        ocr_text = """
        Purchase Price: $10,000,000
        NOI: $600,000
        Entry Cap Rate: 5.5%
        """

        engine = CREExtractionEngine("office", "suburban")
        result = engine.extract(ocr_text)

        # Should detect mismatch (6% actual vs 5.5% stated)
        warnings = result.get("validation_warnings", [])
        cap_warnings = [w for w in warnings if "cap" in w.get("type", "").lower()]
        self.assertTrue(len(cap_warnings) > 0,
                       "Should detect cap rate vs NOI mismatch")

    def test_ltv_loan_validation(self):
        """Test that LTV and loan amount cross-validate"""
        ocr_text = """
        Purchase Price: $20,000,000
        Loan Amount: $15,000,000
        LTV: 70%
        """

        engine = CREExtractionEngine("multifamily", "midrise")
        result = engine.extract(ocr_text)

        # Should detect mismatch (75% actual vs 70% stated)
        warnings = result.get("validation_warnings", [])
        ltv_warnings = [w for w in warnings if "ltv" in w.get("type", "").lower()]
        self.assertTrue(len(ltv_warnings) > 0,
                       "Should detect LTV vs loan amount mismatch")

    def test_dscr_calculation_validation(self):
        """Test DSCR calculation from loan terms"""
        ocr_text = """
        NOI: $1,000,000
        Loan Amount: $10,000,000
        Interest Rate: 7%
        Amortization: 25 years
        DSCR: 1.50x
        """

        engine = CREExtractionEngine("industrial", "light_industrial_flex")
        result = engine.extract(ocr_text)

        # Calculate expected DSCR
        # Should validate DSCR calculation
        if "ads_calculated" in result["derived"]:
            calculated_dscr = 1000000 / result["derived"]["ads_calculated"]
            # Should be closer to 1.17x, not 1.50x
            self.assertLess(calculated_dscr, 1.3,
                          "Calculated DSCR should be less than stated 1.50x")

        warnings = result.get("validation_warnings", [])
        dscr_warnings = [w for w in warnings if "dscr" in w.get("type", "").lower()]
        self.assertTrue(len(dscr_warnings) > 0,
                       "Should detect DSCR calculation mismatch")


class TestAssetSpecificMitigations(unittest.TestCase):
    """Test asset-specific risk mitigations"""

    def test_office_ti_mitigation(self):
        """Test Office TI reserve calculation"""
        ocr_text = """
        Office Building
        Square Feet: 100,000
        WALT: 3 years
        TI Allowance New: $25/SF
        Purchase Price: $30,000,000
        NOI: $1,800,000
        """

        engine = CREExtractionEngine("office", "suburban")
        result = engine.extract(ocr_text)

        # Find TI-related risks
        ti_risks = [r for r in result["risks_ranked"]
                   if "ti" in r["metric"].lower()]

        if ti_risks:
            # Should calculate annual TI needs based on rollover
            for risk in ti_risks:
                dollar_mitigations = [m for m in risk["mitigations"]
                                     if "dollar_impact" in m]
                self.assertTrue(len(dollar_mitigations) > 0,
                               "TI risk should have dollar-quantified mitigations")

    def test_industrial_clear_height_discount(self):
        """Test Industrial clear height rent discount calculation"""
        ocr_text = """
        Industrial Warehouse
        Square Feet: 200,000
        Clear Height: 24 feet
        NOI: $1,000,000
        Purchase Price: $15,000,000
        """

        engine = CREExtractionEngine("industrial", "bulk_distribution")
        result = engine.extract(ocr_text)

        # Clear height of 24' is below modern standard of 32'
        height_risks = [r for r in result["risks_ranked"]
                       if "clear_height" in r["metric"].lower()]

        if height_risks:
            for risk in height_risks:
                # Should suggest rent discount
                discount_mitigations = [m for m in risk["mitigations"]
                                       if "discount" in m["action"].lower()]
                self.assertTrue(len(discount_mitigations) > 0,
                               "Low clear height should suggest rent discount")

    def test_hotel_gop_exit_cap_widening(self):
        """Test Hotel GOP margin impact on exit cap"""
        ocr_text = """
        Full Service Hotel
        Keys: 200
        GOP Margin: 25%
        NOI: $3,000,000
        Purchase Price: $40,000,000
        Exit Cap Rate: 7.5%
        """

        engine = CREExtractionEngine("hospitality", "full_service")
        result = engine.extract(ocr_text)

        # GOP margin of 25% is below target
        gop_risks = [r for r in result["risks_ranked"]
                    if "gop" in r["metric"].lower()]

        if gop_risks:
            for risk in gop_risks:
                # Should calculate exit cap widening impact
                cap_mitigations = [m for m in risk["mitigations"]
                                  if "cap widening" in m["action"].lower() or
                                  "exit cap" in m["action"].lower()]
                self.assertTrue(len(cap_mitigations) > 0,
                               "Low GOP should trigger exit cap widening calculation")

                # Should have dollar impact
                if cap_mitigations:
                    self.assertIn("dollar_impact", cap_mitigations[0])


def run_tests():
    """Run all tests and report results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCREExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestAssetSpecificMitigations))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)