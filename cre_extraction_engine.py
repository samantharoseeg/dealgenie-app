"""
CRE Extraction & Analysis Engine
Comprehensive extraction, normalization, validation, and risk assessment
for all commercial real estate asset classes and subclasses
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

# ============================================================================
# ASSET CLASS & SUBCLASS DEFINITIONS
# ============================================================================

ASSET_CLASSES = {
    "multifamily": ["garden_lowrise", "midrise", "highrise", "student_housing",
                   "senior_IL", "senior_AL", "senior_MemoryCare"],
    "office": ["cbd_A_trophy", "cbd_BC", "suburban", "medical_office", "flex_creative"],
    "industrial": ["bulk_distribution", "light_industrial_flex", "last_mile",
                   "cold_storage", "manufacturing"],
    "retail": ["grocery_anchored", "power_center", "lifestyle_open_air",
               "mall_regional", "single_tenant_nnn"],
    "hospitality": ["full_service", "limited_service", "extended_stay",
                    "resort", "boutique_lifestyle", "luxury"],
    "self_storage": ["climate_controlled", "non_climate", "mixed"],
    "data_center": ["wholesale", "retail_colocation", "hyperscale"],
    "life_science": ["wet_lab", "dry_lab", "GMP_bio", "R&D"],
    "senior_living": ["IL", "AL", "MemoryCare", "CCRC"],
    "student_housing": ["by_bed", "by_unit"],
    "manufactured_housing": ["MHC", "RV"],
    "mixed_use": ["res+retail", "res+office", "custom"]
}

# ============================================================================
# FIELD SYNONYMS & PATTERNS
# ============================================================================

FIELD_SYNONYMS = {
    "purchase_price": [
        r"purchase\s+price", r"acquisition\s+price", r"contract\s+price",
        r"sale\s+price", r"closing\s+price", r"total\s+consideration"
    ],
    "noi_now": [
        r"noi(?:\s+now)?(?![\s\-]stab)", r"in[\-\s]place\s+noi", r"current\s+noi",
        r"noi\s+yr\s+1", r"noi\s+\(t[\-\s]12\)", r"trailing\s+noi", r"actual\s+noi"
    ],
    "noi_stab": [
        r"stabilized\s+noi", r"proforma\s+noi", r"underwritten\s+noi",
        r"projected\s+noi", r"year\s+2\s+noi"
    ],
    "entry_cap": [
        r"entry\s+cap", r"going[\-\s]in\s+cap", r"in[\-\s]place\s+cap",
        r"cap\s+on\s+price", r"purchase\s+cap", r"acquisition\s+cap"
    ],
    "exit_cap": [
        r"exit\s+cap", r"terminal\s+cap", r"reversion\s+cap",
        r"disposition\s+cap", r"sale\s+cap"
    ],
    "loan_amount": [
        r"loan\s+amount", r"debt", r"mortgage", r"financing",
        r"loan\s+proceeds", r"debt\s+amount"
    ],
    "ltv": [
        r"ltv", r"loan[\-\s]to[\-\s]value", r"leverage", r"debt\s+ratio"
    ],
    "rate": [
        r"interest\s+rate", r"rate", r"coupon", r"all[\-\s]in\s+rate"
    ],
    "clear_height_ft": [
        r"clear\s+height", r"ceiling\s+height", r"clearance",
        r"height", r"clear\s+span"
    ],
    "gop_margin_pct": [
        r"gop\s+margin", r"gross\s+operating\s+profit", r"gop",
        r"gross\s+margin"
    ],
    "pip_cost_per_key": [
        r"pip\s+cost", r"pip", r"property\s+improvement\s+plan",
        r"renovation\s+cost", r"capex\s+per\s+key"
    ],
    "occupancy_pct": [
        r"occupancy", r"occupied", r"leased", r"occupancy\s+rate"
    ],
    "dscr": [
        r"dscr", r"debt\s+service\s+coverage", r"debt\s+coverage",
        r"coverage\s+ratio"
    ],
    "expense_ratio": [
        r"expense\s+ratio", r"opex\s+ratio", r"expense\s+%",
        r"operating\s+expense\s+ratio"
    ],
    "amort_years": [
        r"amortization", r"amort", r"loan\s+term", r"term"
    ],
    "io_years": [
        r"io\s+period", r"interest[\-\s]only", r"io", r"i/o"
    ],
    "hold_years": [
        r"hold\s+period", r"investment\s+horizon", r"exit\s+year",
        r"disposition\s+year"
    ],
    "units": [
        r"units?", r"apartments?", r"doors?", r"keys?", r"beds?", r"pads?"
    ],
    "sf": [
        r"square\s+feet", r"sq\.?\s*ft\.?", r"sf", r"gsf", r"nrsf", r"gla"
    ],
    "walt": [
        r"walt", r"weighted\s+average\s+lease\s+term", r"remaining\s+lease\s+term",
        r"average\s+lease\s+term"
    ],
    "occupancy_pct": [
        r"occupancy", r"occupied", r"leased", r"physical\s+occupancy"
    ],
    "ti_new_psf": [
        r"ti\s+new", r"tenant\s+improvement.*new", r"ti\s+\$/sf\s+new",
        r"new\s+tenant\s+ti", r"ti\s+allowance.*new"
    ],
    "ti_renew_psf": [
        r"ti\s+renewal", r"tenant\s+improvement.*renewal", r"ti\s+\$/sf\s+renewal",
        r"renewal\s+ti", r"ti\s+allowance.*renewal"
    ]
}

# ============================================================================
# BENCHMARKS BY SUBCLASS
# ============================================================================

# SUBCLASS-SPECIFIC BENCHMARKS (specialized metrics not in main app benchmarks)
# Note: Primary metrics (cap_rate, dscr, ltv) use app's industry benchmarks with proper sources
SUBCLASS_BENCHMARKS = {
    # Multifamily
    "garden_lowrise": {
        "expense_ratio": {"min": 0.35, "target": 0.40, "max": 0.45, "source": "RCA Multifamily Survey 2024"},
        "concessions_months": {"min": 0, "target": 1, "max": 2, "source": "NMHC/NAA Rent Survey 2024"},
        "replacement_reserves_per_unit": {"min": 250, "target": 300, "max": 350, "source": "IREM Income/Expense Analysis"},
        "renewal_rate_pct": {"min": 0.50, "target": 0.60, "max": 0.70, "source": "RealPage Analytics 2024"},
        "turnover_cost_per_unit": {"min": 1500, "target": 2000, "max": 2500, "source": "NMHC Operations Survey"}
    },
    "midrise": {
        "expense_ratio": {"min": 0.38, "target": 0.43, "max": 0.48},
        "concessions_months": {"min": 0, "target": 1.5, "max": 2.5},
        "replacement_reserves_per_unit": {"min": 275, "target": 325, "max": 375}
    },
    "highrise": {
        "expense_ratio": {"min": 0.40, "target": 0.45, "max": 0.50},
        "concessions_months": {"min": 1, "target": 2, "max": 3},
        "replacement_reserves_per_unit": {"min": 300, "target": 350, "max": 400},
        "mgmt_fee_pct": {"min": 0.03, "target": 0.035, "max": 0.04}
    },

    # Office
    "cbd_A_trophy": {
        "ti_new_psf": {"min": 100, "target": 125, "max": 150},
        "ti_renew_psf": {"min": 25, "target": 35, "max": 50},
        "lc_new_pct": {"min": 0.05, "target": 0.055, "max": 0.06},
        "lc_renew_pct": {"min": 0.02, "target": 0.025, "max": 0.03},
        "downtime_months": {"min": 6, "target": 7.5, "max": 9},
        "walt_years": {"min": 5, "target": 6.5, "max": 7}
    },
    "suburban": {
        "ti_new_psf": {"min": 50, "target": 70, "max": 90},
        "ti_renew_psf": {"min": 15, "target": 25, "max": 35},
        "lc_new_pct": {"min": 0.04, "target": 0.045, "max": 0.05},
        "downtime_months": {"min": 6, "target": 9, "max": 12}
    },
    "medical_office": {
        "ti_new_psf": {"min": 70, "target": 95, "max": 120},
        "parking_ratio": {"min": 4, "target": 5, "max": 6},
        "walt_years": {"min": 7, "target": 10, "max": 12}
    },

    # Industrial
    "bulk_distribution": {
        "clear_height_ft": {"min": 32, "target": 36, "max": 40, "source": "CBRE Industrial Q4 2024"},
        "dock_ratio": {"min": 7000, "target": 8500, "max": 10000, "source": "JLL Logistics Report 2024"},
        "office_finish_pct": {"min": 0.05, "target": 0.08, "max": 0.10, "source": "CBRE Industrial Survey"},
        "column_spacing": {"min": 40, "target": 50, "max": 60, "source": "NAIOP Industrial Development"}
    },
    "last_mile": {
        "clear_height_ft": {"min": 24, "target": 28, "max": 32, "source": "CBRE Industrial Q4 2024"},
        "dock_ratio": {"min": 3000, "target": 5000, "max": 7000, "source": "JLL Logistics Report 2024"},
        "yard_depth": {"min": 100, "target": 130, "max": 160, "source": "Prologis Research 2024"}
    },

    # Retail
    "grocery_anchored": {
        "anchor_remaining_term_years": {"min": 10, "target": 15, "max": 20},
        "cam_recovery_pct": {"min": 0.85, "target": 0.92, "max": 0.95},
        "grocer_occupancy_cost_pct": {"min": 0.02, "target": 0.025, "max": 0.03}
    },

    # Hospitality
    "limited_service": {
        "gop_margin_pct": {"min": 0.40, "target": 0.45, "max": 0.50, "source": "STR/HVS Operating Survey 2024"},
        "ffe_reserve_pct": {"min": 0.04, "target": 0.045, "max": 0.05, "source": "HVS Capital Reserve Study"},
        "pip_cost_per_key": {"min": 10000, "target": 17500, "max": 25000, "source": "STR Capital Investment Report"}
    },
    "full_service": {
        "gop_margin_pct": {"min": 0.25, "target": 0.30, "max": 0.35, "source": "STR/HVS Operating Survey 2024"},
        "ffe_reserve_pct": {"min": 0.04, "target": 0.045, "max": 0.05, "source": "HVS Capital Reserve Study"},
        "pip_cost_per_key": {"min": 25000, "target": 37500, "max": 50000, "source": "STR Capital Investment Report"}
    },

    # Self-Storage
    "climate_controlled": {
        "expense_ratio": {"min": 0.28, "target": 0.33, "max": 0.38},
        "lease_up_velocity_units_per_month": {"min": 0.02, "target": 0.025, "max": 0.03}
    },

    # Data Center
    "wholesale": {
        "pue": {"min": 1.2, "target": 1.4, "max": 1.5},
        "base_rent_per_kw": {"min": 100, "target": 125, "max": 150}
    }
}

# ============================================================================
# REQUIRED FIELDS BY SUBCLASS
# ============================================================================

REQUIRED_FIELDS = {
    # Common to all
    "_common": [
        "purchase_price", "noi_now", "entry_cap", "loan_amount", "ltv", "rate"
    ],

    # Multifamily specific
    "garden_lowrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio"],
    "midrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio", "parking_ratio"],
    "highrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio", "concessions_months"],

    # Office specific
    "cbd_A_trophy": ["gla_sf", "walt_years", "ti_new_psf", "lc_new_pct", "occupancy_pct"],
    "suburban": ["gla_sf", "walt_years", "ti_new_psf", "occupancy_pct", "parking_ratio"],

    # Industrial specific
    "bulk_distribution": ["bldg_sf", "clear_height_ft", "dock_doors_count", "occupancy_pct"],
    "last_mile": ["bldg_sf", "clear_height_ft", "dock_doors_count", "yard_depth"],

    # Retail specific
    "grocery_anchored": ["gla_sf", "anchor_tenant", "anchor_remaining_term_years", "cam_recovery_pct"],

    # Hospitality specific
    "limited_service": ["keys", "adr", "occupancy_pct", "revpar", "gop_margin_pct"],
    "full_service": ["keys", "adr", "occupancy_pct", "revpar", "gop_margin_pct", "fb_revenue"]
}

# ============================================================================
# MAIN EXTRACTION ENGINE
# ============================================================================

class CREExtractionEngine:
    """
    Comprehensive CRE extraction and analysis engine
    """

    def __init__(self, asset_class: str, subclass: str):
        """
        Initialize with mandatory asset class and subclass

        Args:
            asset_class: One of the defined asset classes
            subclass: Specific subclass within the asset class
        """
        if asset_class not in ASSET_CLASSES:
            raise ValueError(f"Invalid asset_class: {asset_class}")

        if subclass not in ASSET_CLASSES[asset_class]:
            raise ValueError(f"Invalid subclass '{subclass}' for asset_class '{asset_class}'")

        self.asset_class = asset_class
        self.subclass = subclass
        self.ingested = {}
        self.confidence = {}
        self.conflicts = {}
        self.derived = {}
        self.bench_compare = {}
        self.risks_ranked = []
        self.known = []
        self.unknown = []
        self.sensitivities = {}
        self.glossary_refs = []
        self.notes = []

    def extract(self, raw_text: str, ocr_blocks: Optional[List[Dict]] = None) -> Dict:
        """
        Main extraction and analysis method

        Args:
            raw_text: Concatenated OCR text from all sources
            ocr_blocks: Optional list of {page, bbox, text} for positional hints

        Returns:
            Structured JSON output following the defined schema
        """
        # Step 1: Extract raw fields
        self._extract_fields(raw_text, ocr_blocks)

        # Step 2: Normalize units
        self._normalize_units()

        # Step 3: Cross-validation
        self._cross_validate()

        # Step 4: Compute derived metrics
        self._compute_derived()

        # Step 5: Compare to benchmarks
        self._compare_benchmarks()

        # Step 6: Rank risks
        self._rank_risks()

        # Step 7: Compute sensitivities
        self._compute_sensitivities()

        # Step 8: Identify known/unknown
        self._identify_known_unknown()

        # Step 9: Calculate completeness
        completeness = self._calculate_completeness()

        # Return structured output
        return {
            "ingested": self.ingested,
            "derived": self.derived,
            "bench_compare": self.bench_compare,
            "risks_ranked": self.risks_ranked,
            "known": self.known,
            "unknown": self.unknown,
            "completeness": completeness,
            "sensitivities": self.sensitivities,
            "glossary_refs": self.glossary_refs,
            "notes": self.notes
        }

    def _extract_fields(self, raw_text: str, ocr_blocks: Optional[List[Dict]]):
        """Extract fields using synonyms and patterns"""

        text_upper = raw_text.upper()

        # Extract common fields
        for field_name, patterns in FIELD_SYNONYMS.items():
            for pattern in patterns:
                # Different regex patterns for different field types
                if field_name in ["entry_cap", "exit_cap", "ltv", "occupancy_pct", "expense_ratio",
                                 "renewal_rate_pct", "gop_margin_pct", "revpar_growth_rate"]:
                    # Percentage fields
                    regex = rf"{pattern}[\s:]+([0-9]+\.?[0-9]*)\s*%?"
                    is_percentage = True
                elif field_name in ["rate", "mezz_rate"]:
                    # Interest rate fields (can be percentage or SOFR+spread)
                    regex = rf"{pattern}[\s:]+(?:([0-9]+\.?[0-9]*)\s*%?|SOFR\s*\+\s*([0-9]+))"
                    is_percentage = True
                elif field_name in ["clear_height_ft", "units_count", "keys_count", "hold_years",
                                   "io_years", "amort_years", "parking_ratio"]:
                    # Integer fields
                    regex = rf"{pattern}[\s:]+([0-9]+)"
                    is_percentage = False
                else:
                    # Money fields
                    regex = rf"{pattern}[\s:]+\$?([0-9,]+\.?[0-9]*)\s*([KMB]|THOUSAND|MILLION|BILLION)?"
                    is_percentage = False

                match = re.search(regex, text_upper, re.IGNORECASE)

                if match:
                    # Handle different match groups
                    if field_name in ["rate", "mezz_rate"] and len(match.groups()) > 1 and match.group(2):
                        # SOFR + spread format
                        parsed = float(match.group(2)) / 10000  # Convert bps to decimal
                        self.ingested[field_name] = parsed
                        self.ingested[f"{field_name}_type"] = "SOFR_spread"
                        self.confidence[field_name] = "High"
                        break

                    value = match.group(1).replace(',', '')

                    # Parse value
                    try:
                        parsed = float(value)

                        # Handle percentages
                        if is_percentage and parsed > 1:
                            parsed = parsed / 100  # Convert to decimal

                        # Apply multiplier for money fields
                        if not is_percentage and len(match.groups()) > 1:
                            multiplier = match.group(2) if match.group(2) else None
                            if multiplier:
                                if multiplier in ['K', 'THOUSAND']:
                                    parsed *= 1000
                                elif multiplier in ['M', 'MILLION']:
                                    parsed *= 1000000
                                elif multiplier in ['B', 'BILLION']:
                                    parsed *= 1000000000

                        # Store with confidence
                        if field_name not in self.ingested:
                            self.ingested[field_name] = parsed

                            # Determine confidence
                            if ocr_blocks and self._is_in_table(match, ocr_blocks):
                                self.confidence[field_name] = "High"
                            else:
                                self.confidence[field_name] = "Medium"
                        else:
                            # Track conflicts
                            if field_name not in self.conflicts:
                                self.conflicts[field_name] = [self.ingested[field_name]]
                            self.conflicts[field_name].append(parsed)

                        # Add to glossary refs
                        if field_name not in self.glossary_refs:
                            self.glossary_refs.append(field_name)

                        break  # Found value for this field

                    except ValueError:
                        continue

        # Extract percentage fields
        percent_fields = ["ltv", "occupancy_pct", "expense_ratio", "renewal_rate_pct",
                         "lc_new_pct", "lc_renew_pct", "cam_recovery_pct"]

        for field in percent_fields:
            if field in FIELD_SYNONYMS:
                patterns = FIELD_SYNONYMS[field]
            else:
                patterns = [field.replace('_', r'\s+')]

            for pattern in patterns:
                regex = rf"{pattern}[\s:]+([0-9]+\.?[0-9]*)\s*%"
                match = re.search(regex, text_upper, re.IGNORECASE)

                if match:
                    try:
                        value = float(match.group(1)) / 100  # Convert to decimal
                        self.ingested[field] = value
                        self.confidence[field] = "Medium"
                        break
                    except ValueError:
                        continue

        # Extract rate structure (SOFR + spread)
        rate_pattern = r"(SOFR|LIBOR|PRIME)\s*\+\s*([0-9]+)\s*(BPS|BASIS\s+POINTS)?"
        rate_match = re.search(rate_pattern, text_upper)
        if rate_match:
            self.ingested["index"] = rate_match.group(1)
            spread = float(rate_match.group(2))
            if rate_match.group(3):  # If BPS specified
                self.ingested["spread_bps"] = spread
            else:
                self.ingested["spread_bps"] = spread * 100  # Assume percentage
            self.confidence["spread_bps"] = "High"

    def _is_in_table(self, match, ocr_blocks: List[Dict]) -> bool:
        """Check if match is within a table structure"""
        # Simplified - would need actual bbox checking
        return False  # Placeholder

    def _normalize_units(self):
        """Normalize all units to standard format"""

        # Money fields - ensure they're in dollars
        money_fields = ["purchase_price", "loan_amount", "closing_costs", "noi_now",
                       "noi_stab", "ti_new_psf", "pip_cost_per_key"]

        for field in money_fields:
            if field in self.ingested:
                # Already normalized in extraction
                pass

        # Percentage fields - ensure they're decimals
        pct_fields = ["ltv", "occupancy_pct", "expense_ratio", "renewal_rate_pct"]

        for field in pct_fields:
            if field in self.ingested:
                if self.ingested[field] > 1:
                    # Likely entered as whole number
                    self.ingested[field] = self.ingested[field] / 100
                    self.notes.append(f"Normalized {field} from percentage to decimal")

    def _cross_validate(self):
        """Cross-validate fields and adjust confidence"""

        # Cap rate validation
        if all(k in self.ingested for k in ["entry_cap", "purchase_price", "noi_now"]):
            calculated_cap = self.ingested["noi_now"] / self.ingested["purchase_price"]
            stated_cap = self.ingested["entry_cap"]

            if abs(calculated_cap - stated_cap) / stated_cap > 0.05:
                self.confidence["entry_cap"] = "Low"
                self.notes.append(f"Cap rate mismatch: stated {stated_cap:.3f} vs calc {calculated_cap:.3f}")

        # LTV validation
        if all(k in self.ingested for k in ["ltv", "loan_amount", "purchase_price"]):
            calculated_ltv = self.ingested["loan_amount"] / self.ingested["purchase_price"]
            stated_ltv = self.ingested["ltv"]

            if abs(calculated_ltv - stated_ltv) / stated_ltv > 0.02:
                self.confidence["ltv"] = "Low"
                self.notes.append(f"LTV mismatch: stated {stated_ltv:.3f} vs calc {calculated_ltv:.3f}")

        # DSCR validation
        if all(k in self.ingested for k in ["dscr", "noi_now", "loan_amount", "rate"]):
            # Calculate ADS
            if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                ads = self.ingested["loan_amount"] * self.ingested["rate"]
            else:
                # Amortizing
                amort_years = self.ingested.get("amort_years", 30)
                r = self.ingested["rate"] / 12
                n = amort_years * 12
                if r > 0:
                    mortgage_constant = 12 * (r * (1 + r)**n) / ((1 + r)**n - 1)
                    ads = self.ingested["loan_amount"] * mortgage_constant
                else:
                    ads = self.ingested["loan_amount"] / amort_years

            calculated_dscr = self.ingested["noi_now"] / ads if ads > 0 else 0
            stated_dscr = self.ingested["dscr"]

            if abs(calculated_dscr - stated_dscr) / stated_dscr > 0.05:
                self.confidence["dscr"] = "Low"
                self.notes.append(f"DSCR mismatch: stated {stated_dscr:.3f} vs calc {calculated_dscr:.3f}")

    def _compute_derived(self):
        """Compute derived metrics"""

        # Cap Rate
        if all(k in self.ingested for k in ["noi_now", "purchase_price"]):
            self.derived["cap_rate"] = self.ingested["noi_now"] / self.ingested["purchase_price"]
            self.derived["cap_rate_calc"] = "NOI / Purchase Price"

        # Yield on Cost
        if all(k in self.ingested for k in ["noi_stab", "purchase_price"]):
            total_cost = self.ingested["purchase_price"] * (1 + self.ingested.get("closing_costs_pct", 0.02))
            self.derived["yield_on_cost"] = self.ingested["noi_stab"] / total_cost
            self.derived["yoc_calc"] = "Stabilized NOI / Total Project Cost"

        # Mortgage Constant
        if all(k in self.ingested for k in ["rate", "amort_years"]):
            r = self.ingested["rate"] / 12
            n = self.ingested["amort_years"] * 12
            if r > 0:
                self.derived["mortgage_constant"] = 12 * (r * (1 + r)**n) / ((1 + r)**n - 1)
                self.derived["mc_calc"] = "12 * (r*(1+r)^n)/((1+r)^n - 1)"

        # Annual Debt Service
        if all(k in self.ingested for k in ["loan_amount", "rate"]):
            if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                self.derived["ads"] = self.ingested["loan_amount"] * self.ingested["rate"]
                self.derived["ads_calc"] = "Loan × Rate (IO period)"
            elif "mortgage_constant" in self.derived:
                self.derived["ads"] = self.ingested["loan_amount"] * self.derived["mortgage_constant"]
                self.derived["ads_calc"] = "Loan × Mortgage Constant"

        # DSCR
        if all(k in ["noi_now", "ads"] for k in list(self.ingested.keys()) + list(self.derived.keys())):
            noi = self.ingested.get("noi_now", 0)
            ads = self.derived.get("ads", 0)
            if ads > 0:
                self.derived["dscr"] = noi / ads
                self.derived["dscr_calc"] = "NOI / Annual Debt Service"

        # Debt Yield
        if all(k in self.ingested for k in ["noi_now", "loan_amount"]):
            self.derived["debt_yield"] = self.ingested["noi_now"] / self.ingested["loan_amount"]
            self.derived["debt_yield_calc"] = "NOI / Loan Amount"

        # Exit Value
        if all(k in self.ingested for k in ["exit_cap"]):
            # Project NOI at exit
            hold_years = self.ingested.get("hold_years", 5)
            noi_growth = self.ingested.get("noi_growth_rate", 0.03)

            if "noi_now" in self.ingested:
                noi_exit = self.ingested["noi_now"] * ((1 + noi_growth) ** hold_years)
                self.derived["exit_value"] = noi_exit / self.ingested["exit_cap"]
                self.derived["exit_value_calc"] = f"NOI_Year_{hold_years} / Exit Cap"

                # Net Sale Proceeds
                sale_costs = self.ingested.get("sale_cost_pct", 0.02)
                loan_balance = self.ingested.get("loan_amount", 0) * 0.9  # Assume 10% paydown

                self.derived["net_sale_proceeds"] = self.derived["exit_value"] * (1 - sale_costs) - loan_balance
                self.derived["nsp_calc"] = "Exit Value × (1 - Sale Costs) - Loan Balance"

        # Refinance Proceeds
        if all(k in self.ingested for k in ["market_cap_for_refi"]):
            if "noi_stab" in self.ingested:
                refi_value = self.ingested["noi_stab"] / self.ingested["market_cap_for_refi"]
                refi_ltv = self.ingested.get("refi_ltv", 0.65)
                self.derived["refi_proceeds"] = refi_value * refi_ltv
                self.derived["refi_calc"] = "Stabilized Value × Refi LTV"

    def _compare_benchmarks(self):
        """Compare metrics to industry benchmarks from app + subclass-specific benchmarks"""

        # Get main app benchmarks for primary metrics
        try:
            from app import BENCHMARKS, evaluate_against_benchmarks
            app_benchmarks_available = True
        except ImportError:
            app_benchmarks_available = False

        # Asset class mapping for app benchmarks
        asset_class_map = {
            "multifamily": "Multifamily",
            "office": "Office",
            "industrial": "Industrial",
            "retail": "Retail",
            "hospitality": "Hotel"
        }

        # Use app benchmarks for primary metrics
        if app_benchmarks_available and self.asset_class in asset_class_map:
            app_asset_class = asset_class_map[self.asset_class]

            # Compare cap_rate, dscr, ltv using app benchmarks
            primary_metrics = {}
            if "cap_rate" in self.derived:
                primary_metrics["cap_rate"] = self.derived["cap_rate"]
            elif "entry_cap" in self.ingested:
                primary_metrics["cap_rate"] = self.ingested["entry_cap"]

            if "dscr" in self.derived:
                primary_metrics["dscr"] = self.derived["dscr"]
            elif "dscr" in self.ingested:
                primary_metrics["dscr"] = self.ingested["dscr"]

            if "ltv" in self.ingested:
                primary_metrics["ltv"] = self.ingested["ltv"] * 100  # App expects percentage

            # Use app's evaluation function
            app_evaluations = evaluate_against_benchmarks(app_asset_class, primary_metrics)

            for eval_result in app_evaluations:
                metric = eval_result["metric"].lower()
                status_map = {"good": "OK", "warning": "Below Target", "critical": "Poor"}
                status = status_map.get(eval_result["status"], "Unknown")

                self.bench_compare[metric] = {
                    "status": status,
                    "value": eval_result["value"],
                    "benchmark": eval_result["benchmark"],
                    "source": "App Industry Benchmarks"
                }

        # Use subclass-specific benchmarks for specialized metrics
        if self.subclass in SUBCLASS_BENCHMARKS:
            benchmarks = SUBCLASS_BENCHMARKS[self.subclass]

            for metric, targets in benchmarks.items():
                if metric in self.ingested or metric in self.derived:
                    value = self.ingested.get(metric) or self.derived.get(metric)

                    min_val = targets.get("min", 0)
                    target_val = targets.get("target", 0)
                    max_val = targets.get("max", float('inf'))

                    if value < min_val:
                        status = "Offside Low"
                        delta = min_val - value
                    elif value > max_val:
                        status = "Offside High"
                        delta = value - max_val
                    elif abs(value - target_val) / target_val < 0.1:
                        status = "OK"
                        delta = 0
                    else:
                        status = "Borderline"
                        delta = value - target_val

                    self.bench_compare[metric] = {
                        "value": value,
                        "min": min_val,
                        "target": target_val,
                        "max": max_val,
                        "status": status,
                        "delta": delta,
                        "source": targets.get("source", "Industry Research"),
                        "benchmark": f"Target: {target_val} ({targets.get('source', 'Industry Research')})"
                    }

    def _rank_risks(self):
        """Rank risks with quantified mitigations"""

        # Check each offside metric
        for metric, comparison in self.bench_compare.items():
            if comparison["status"].startswith("Offside"):

                # Determine severity
                if metric in ["dscr", "debt_yield"]:
                    severity = "High"
                elif metric in ["ltv", "expense_ratio"]:
                    severity = "Medium"
                else:
                    severity = "Low"

                # Calculate mitigation requirements
                mitigations = []

                if metric == "dscr" and comparison["status"] == "Offside Low":
                    # Calculate loan reduction needed
                    target_dscr = comparison["target"]
                    current_noi = self.ingested.get("noi_now", 0)
                    required_ads = current_noi / target_dscr
                    current_ads = self.derived.get("ads", 0)
                    ads_reduction = current_ads - required_ads

                    if "rate" in self.ingested:
                        loan_reduction = ads_reduction / self.ingested["rate"]
                        mitigations.append(f"Reduce loan by ${loan_reduction:,.0f}")

                    # Or increase NOI
                    noi_increase = (target_dscr * current_ads) - current_noi
                    mitigations.append(f"Increase NOI by ${noi_increase:,.0f}")

                elif metric == "ltv" and comparison["status"] == "Offside High":
                    target_ltv = comparison["target"]
                    price = self.ingested.get("purchase_price", 0)
                    max_loan = price * target_ltv
                    current_loan = self.ingested.get("loan_amount", 0)
                    loan_reduction = current_loan - max_loan

                    mitigations.append(f"Reduce loan by ${loan_reduction:,.0f}")
                    mitigations.append(f"Increase equity by ${loan_reduction:,.0f}")

                elif metric == "expense_ratio" and comparison["status"] == "Offside High":
                    target_ratio = comparison["target"]
                    revenue = self.ingested.get("effective_gross_income", 0)

                    if revenue > 0:
                        target_expenses = revenue * target_ratio
                        current_expenses = revenue * comparison["value"]
                        expense_reduction = current_expenses - target_expenses

                        mitigations.append(f"Reduce expenses by ${expense_reduction:,.0f}")
                        mitigations.append("Renegotiate management contract")
                        mitigations.append("Implement energy efficiency measures")

                # Add subclass-specific mitigations
                if self.asset_class == "office" and metric == "walt_years":
                    mitigations.append("Focus on longer-term lease renewals")
                    mitigations.append("Target credit tenants with 7+ year terms")

                elif self.asset_class == "industrial" and metric == "clear_height_ft":
                    mitigations.append("Limited to older-generation tenant pool")
                    mitigations.append("Consider ceiling height enhancement")

                elif self.asset_class == "retail" and metric == "anchor_remaining_term_years":
                    mitigations.append("Negotiate extension with anchor")
                    mitigations.append("Secure backfill LOIs")
                    mitigations.append("Model co-tenancy impact")

                self.risks_ranked.append({
                    "severity": severity,
                    "name": metric,
                    "value": comparison["value"],
                    "target": comparison["target"],
                    "why": f"{metric} is {comparison['status']}",
                    "calc": f"Delta: {comparison['delta']:.3f}",
                    "mitigations": mitigations
                })

        # Sort by severity
        severity_order = {"High": 0, "Medium": 1, "Low": 2}
        self.risks_ranked.sort(key=lambda x: severity_order[x["severity"]])

    def _compute_sensitivities(self):
        """Compute sensitivity analysis"""

        # Exit Cap Sensitivity
        if all(k in self.ingested for k in ["exit_cap", "noi_now"]):
            base_exit_cap = self.ingested["exit_cap"]
            hold_years = self.ingested.get("hold_years", 5)
            noi_growth = self.ingested.get("noi_growth_rate", 0.03)
            noi_exit = self.ingested["noi_now"] * ((1 + noi_growth) ** hold_years)

            sensitivities = {}
            for bps_change in [50, 100]:
                new_cap = base_exit_cap + (bps_change / 10000)
                new_value = noi_exit / new_cap
                base_value = noi_exit / base_exit_cap
                value_change = new_value - base_value

                sensitivities[f"+{bps_change}bps"] = {
                    "exit_value": new_value,
                    "value_change": value_change,
                    "pct_change": (value_change / base_value) * 100
                }

            self.sensitivities["exit_cap"] = sensitivities

        # NOI Sensitivity
        if "noi_now" in self.ingested:
            base_noi = self.ingested["noi_now"]
            sensitivities = {}

            for pct_change in [-10, -5, 5, 10]:
                new_noi = base_noi * (1 + pct_change/100)

                # Impact on DSCR
                if "ads" in self.derived:
                    new_dscr = new_noi / self.derived["ads"]
                    sensitivities[f"{pct_change:+d}%"] = {
                        "noi": new_noi,
                        "dscr": new_dscr
                    }

                    # Check if breaches covenant
                    if "min_dscr" in self.ingested:
                        if new_dscr < self.ingested["min_dscr"]:
                            sensitivities[f"{pct_change:+d}%"]["breach"] = "DSCR covenant"

            self.sensitivities["noi"] = sensitivities

        # Interest Rate Sensitivity
        if all(k in self.ingested for k in ["rate", "loan_amount"]):
            base_rate = self.ingested["rate"]
            loan = self.ingested["loan_amount"]
            sensitivities = {}

            for bps_change in [100, 200]:
                new_rate = base_rate + (bps_change / 10000)

                # New ADS
                if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                    new_ads = loan * new_rate
                else:
                    amort_years = self.ingested.get("amort_years", 30)
                    r = new_rate / 12
                    n = amort_years * 12
                    if r > 0:
                        new_mc = 12 * (r * (1 + r)**n) / ((1 + r)**n - 1)
                        new_ads = loan * new_mc
                    else:
                        new_ads = loan / amort_years

                # New DSCR
                if "noi_now" in self.ingested:
                    new_dscr = self.ingested["noi_now"] / new_ads

                    sensitivities[f"+{bps_change}bps"] = {
                        "rate": new_rate,
                        "ads": new_ads,
                        "dscr": new_dscr
                    }

            self.sensitivities["interest_rate"] = sensitivities

        # LTV Sensitivity
        if all(k in self.ingested for k in ["ltv", "purchase_price"]):
            base_ltv = self.ingested["ltv"]
            price = self.ingested["purchase_price"]
            sensitivities = {}

            for ltv_change in [-5, 5]:
                new_ltv = base_ltv + (ltv_change / 100)
                new_loan = price * new_ltv
                new_equity = price - new_loan

                sensitivities[f"{ltv_change:+d}pts"] = {
                    "ltv": new_ltv,
                    "loan": new_loan,
                    "equity": new_equity
                }

                # Calculate new DSCR if possible
                if all(k in self.ingested for k in ["noi_now", "rate"]):
                    if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                        new_ads = new_loan * self.ingested["rate"]
                    else:
                        # Use existing mortgage constant if available
                        if "mortgage_constant" in self.derived:
                            new_ads = new_loan * self.derived["mortgage_constant"]
                        else:
                            new_ads = new_loan * self.ingested["rate"]  # Simplified

                    new_dscr = self.ingested["noi_now"] / new_ads if new_ads > 0 else 0
                    sensitivities[f"{ltv_change:+d}pts"]["dscr"] = new_dscr

            self.sensitivities["ltv"] = sensitivities

    def _identify_known_unknown(self):
        """Identify what we know and what we don't"""

        # Known items with confidence
        for field, value in self.ingested.items():
            confidence = self.confidence.get(field, "Low")

            # Format value for display
            if field.endswith("_pct") or field.endswith("_rate"):
                formatted = f"{value:.2%}"
            elif isinstance(value, (int, float)) and value > 1000:
                formatted = f"${value:,.0f}"
            else:
                formatted = f"{value:.3f}"

            self.known.append(f"{field}: {formatted} ({confidence} confidence)")

        for metric, value in self.derived.items():
            if not metric.endswith("_calc"):
                if metric in ["cap_rate", "yield_on_cost", "debt_yield", "dscr"]:
                    formatted = f"{value:.3f}"
                elif metric in ["exit_value", "net_sale_proceeds", "refi_proceeds"]:
                    formatted = f"${value:,.0f}"
                else:
                    formatted = f"{value:.3f}"

                self.known.append(f"{metric}: {formatted} (Calculated)")

        # Unknown items with requirements
        required = REQUIRED_FIELDS.get(self.subclass, []) + REQUIRED_FIELDS["_common"]

        for field in required:
            if field not in self.ingested:
                # Determine what's needed for this field
                if field == "walt_years":
                    self.unknown.append(f"WALT - need weighted average lease term from rent roll")
                elif field == "ti_new_psf":
                    self.unknown.append(f"TI New - need tenant improvement allowance for new leases")
                elif field == "clear_height_ft":
                    self.unknown.append(f"Clear Height - critical for tenant marketability")
                elif field == "anchor_remaining_term_years":
                    self.unknown.append(f"Anchor Term - need remaining lease years for co-tenancy risk")
                else:
                    self.unknown.append(f"{field} - required for {self.subclass} analysis")

        # Check for derived metrics we couldn't compute
        if "exit_value" not in self.derived:
            if "exit_cap" not in self.ingested:
                self.unknown.append("Exit Value - need exit_cap assumption")
            elif "noi_now" not in self.ingested:
                self.unknown.append("Exit Value - need current NOI to project")

        # Hotel-specific checks
        if self.asset_class == "hospitality" and "pip_cost_per_key" not in self.ingested:
            self.unknown.append("PIP Cost - Property Improvement Plan budget needed for brand compliance")

        if "dscr" not in self.derived:
            missing = []
            if "noi_now" not in self.ingested:
                missing.append("NOI")
            if "loan_amount" not in self.ingested:
                missing.append("loan amount")
            if "rate" not in self.ingested:
                missing.append("interest rate")

            if missing:
                self.unknown.append(f"DSCR - need {', '.join(missing)}")

        if "net_sale_proceeds" not in self.derived:
            self.unknown.append("Net Sale Proceeds - need exit_cap, hold_years, sale costs")

    def _calculate_completeness(self) -> Dict:
        """Calculate completeness percentage"""

        required = REQUIRED_FIELDS.get(self.subclass, []) + REQUIRED_FIELDS["_common"]
        filled = sum(1 for field in required if field in self.ingested)
        total = len(required)

        return {
            "filled": filled,
            "required": total,
            "percent": (filled / total * 100) if total > 0 else 0
        }


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def extract_and_analyze(asset_class: str, subclass: str, raw_text: str,
                        benchmark_library: Dict = None, ocr_blocks: List[Dict] = None) -> Dict:
    """
    Main public function to extract and analyze CRE deal data

    Args:
        asset_class: Main asset class (e.g., 'office', 'multifamily', 'industrial')
        subclass: Specific subclass (e.g., 'cbd_A_trophy', 'garden_lowrise')
        raw_text: Raw text from OCR or document
        benchmark_library: Optional external benchmark data to use
        ocr_blocks: Optional OCR block data with bounding boxes

    Returns:
        Dictionary with comprehensive analysis results:
        - ingested: Raw extracted fields with confidence scores
        - derived: Calculated metrics
        - bench_compare: Benchmark comparisons
        - risks_ranked: Risk assessment with mitigations
        - known: List of known facts
        - unknown: List of missing critical data
        - completeness: Data completeness metrics
        - sensitivities: Sensitivity analysis results
        - glossary_refs: Referenced glossary terms
        - notes: Processing notes and warnings
        - confidence: Field-level confidence scores
    """

    # Validate inputs
    if not asset_class or not subclass:
        return {
            'error': 'Asset class and subclass are required',
            'ingested': {},
            'derived': {},
            'bench_compare': {},
            'risks_ranked': [],
            'known': [],
            'unknown': ['Asset class and subclass not specified'],
            'completeness': {'score': 0, 'required_fields': 0, 'total_required': 0},
            'sensitivities': {},
            'glossary_refs': [],
            'notes': ['Failed: Asset class and subclass required'],
            'confidence': {}
        }

    if not raw_text or not raw_text.strip():
        return {
            'error': 'No text provided for extraction',
            'ingested': {},
            'derived': {},
            'bench_compare': {},
            'risks_ranked': [],
            'known': [],
            'unknown': ['No data provided'],
            'completeness': {'score': 0, 'required_fields': 0, 'total_required': 0},
            'sensitivities': {},
            'glossary_refs': [],
            'notes': ['Failed: No text provided'],
            'confidence': {}
        }

    try:
        # Initialize extraction engine
        engine = CREExtractionEngine(asset_class, subclass)

        # Override benchmark library if provided
        if benchmark_library:
            # Store custom benchmark library for use
            engine.custom_benchmarks = benchmark_library

        # Run extraction
        result = engine.extract(raw_text, ocr_blocks)

        # Add confidence scores as separate field
        result['confidence'] = engine.confidence

        # Add glossary references (placeholder - would implement glossary matching)
        result['glossary_refs'] = extract_glossary_terms(raw_text)

        return result

    except Exception as e:
        return {
            'error': f'Extraction failed: {str(e)}',
            'ingested': {},
            'derived': {},
            'bench_compare': {},
            'risks_ranked': [],
            'known': [],
            'unknown': ['Extraction failed'],
            'completeness': {'score': 0, 'required_fields': 0, 'total_required': 0},
            'sensitivities': {},
            'glossary_refs': [],
            'notes': [f'Error: {str(e)}'],
            'confidence': {}
        }

def extract_glossary_terms(text: str) -> List[str]:
    """
    Extract glossary terms mentioned in the text
    Simple implementation - would be enhanced with actual glossary database
    """
    glossary_terms = [
        'NOI', 'DSCR', 'LTV', 'Cap Rate', 'WALT', 'TI', 'LC',
        'RevPAR', 'ADR', 'GOP', 'FFE', 'PIP', 'SOFR', 'IRR',
        'Equity Multiple', 'Cash-on-Cash', 'Yield on Cost'
    ]

    found_terms = []
    text_upper = text.upper()

    for term in glossary_terms:
        if term.upper() in text_upper:
            found_terms.append(term)

    return found_terms

def load_benchmarks() -> Dict:
    """
    Load benchmark library from app configuration
    This function provides the interface to get benchmarks from the main app
    """
    try:
        from app import BENCHMARKS
        return BENCHMARKS
    except ImportError:
        # Return default benchmarks if app not available
        return {
            "Office": {
                "cap_rate": {"min": 5.5, "preferred": 6.5, "max": 7.5, "source": "CBRE Q4 2024"},
                "dscr": {"min": 1.25, "preferred": 1.40, "max": 1.60, "source": "MBA Survey Q4 2024"},
                "ltv": {"min": 50, "preferred": 65, "max": 75, "source": "CMBS Market Report 2024"}
            },
            "Multifamily": {
                "cap_rate": {"min": 4.5, "preferred": 5.5, "max": 6.5, "source": "RCA Analytics Q4 2024"},
                "dscr": {"min": 1.20, "preferred": 1.35, "max": 1.50, "source": "Freddie Mac 2024"},
                "ltv": {"min": 55, "preferred": 70, "max": 80, "source": "Fannie Mae Guidelines 2024"}
            },
            "Industrial": {
                "cap_rate": {"min": 5.0, "preferred": 6.0, "max": 7.0, "source": "JLL Research Q4 2024"},
                "dscr": {"min": 1.25, "preferred": 1.40, "max": 1.55, "source": "Life Co Survey 2024"},
                "ltv": {"min": 55, "preferred": 65, "max": 70, "source": "CMBS Market Report 2024"}
            },
            "Retail": {
                "cap_rate": {"min": 6.0, "preferred": 7.0, "max": 8.0, "source": "Cushman & Wakefield 2024"},
                "dscr": {"min": 1.35, "preferred": 1.50, "max": 1.75, "source": "Regional Banks Survey"},
                "ltv": {"min": 50, "preferred": 60, "max": 65, "source": "Insurance Co Guidelines"}
            },
            "Hotel": {
                "cap_rate": {"min": 7.0, "preferred": 8.5, "max": 10.0, "source": "STR/HVS Report 2024"},
                "dscr": {"min": 1.30, "preferred": 1.45, "max": 1.60, "source": "Hospitality Lenders 2024"},
                "ltv": {"min": 50, "preferred": 60, "max": 65, "source": "CMBS Hotel Loans 2024"}
            }
        }

# ============================================================================
# ACCEPTANCE TEST RUNNER
# ============================================================================

def run_acceptance_tests():
    """Run acceptance tests to validate engine behavior"""

    tests_passed = []
    tests_failed = []

    # Test 1: MF Garden with partial data
    print("\n" + "="*60)
    print("TEST 1: Multifamily Garden - Partial Data")
    print("="*60)

    engine = CREExtractionEngine("multifamily", "garden_lowrise")
    result = engine.extract("""
        Purchase Price: $18.5 million
        Current NOI: $1,110,000
        Going-in Cap Rate: 6.0%
    """)

    # Check that cap rate was computed
    if "cap_rate" in result["derived"]:
        print("✓ Cap rate computed")
        tests_passed.append("MF Garden - cap rate")
    else:
        print("✗ Cap rate NOT computed")
        tests_failed.append("MF Garden - cap rate")

    # Check that exit cap is flagged as missing
    if any("exit" in item.lower() for item in result["unknown"]):
        print("✓ Exit cap flagged as missing")
        tests_passed.append("MF Garden - missing exit")
    else:
        print("✗ Exit cap NOT flagged")
        tests_failed.append("MF Garden - missing exit")

    # Test 2: Office Suburban with aggressive exit
    print("\n" + "="*60)
    print("TEST 2: Office Suburban - Aggressive Exit")
    print("="*60)

    engine = CREExtractionEngine("office", "suburban")
    result = engine.extract("""
        Purchase Price: $45 million
        NOI: $2.7 million
        Entry Cap: 6.0%
        Exit Cap: 6.0%
        TI New: $85/SF
        LC New: 5%
        Hold Period: 5 years
    """)

    # Check if exit cap sensitivity was computed
    if "exit_cap" in result["sensitivities"]:
        print("✓ Exit cap sensitivity computed")
        tests_passed.append("Office - exit sensitivity")
    else:
        print("✗ Exit cap sensitivity NOT computed")
        tests_failed.append("Office - exit sensitivity")

    # Test 3: Industrial Bulk - Clear Height
    print("\n" + "="*60)
    print("TEST 3: Industrial Bulk - Clear Height")
    print("="*60)

    engine = CREExtractionEngine("industrial", "bulk_distribution")
    result = engine.extract("""
        Building: 250,000 SF bulk distribution
        Clear Height: 36 feet
        Dock Doors: 30
        Purchase Price: $32 million
        NOI: $1.92 million
    """)

    # Check clear height extraction and benchmark comparison
    if "clear_height_ft" in result["ingested"]:
        print(f"✓ Clear height extracted: {result['ingested']['clear_height_ft']} ft")
        tests_passed.append("Industrial - clear height")
    else:
        print("✗ Clear height NOT extracted")
        tests_failed.append("Industrial - clear height")

    if "clear_height_ft" in result["bench_compare"]:
        status = result["bench_compare"]["clear_height_ft"]["status"]
        print(f"✓ Clear height benchmark: {status}")
        tests_passed.append("Industrial - height benchmark")
    else:
        print("✗ Clear height benchmark NOT computed")
        tests_failed.append("Industrial - height benchmark")

    # Test 4: Retail Grocery - Anchor Risk
    print("\n" + "="*60)
    print("TEST 4: Retail Grocery - Anchor Risk")
    print("="*60)

    engine = CREExtractionEngine("retail", "grocery_anchored")
    result = engine.extract("""
        Shopping Center: 125,000 SF
        Anchor: Whole Foods (45,000 SF)
        Anchor Remaining Term: 8 years
        Co-tenancy clause: Yes
        Purchase Price: $52 million
        NOI: $3.64 million
    """)

    # Check if anchor term risk was identified
    if "anchor_remaining_term_years" in result["bench_compare"]:
        status = result["bench_compare"]["anchor_remaining_term_years"]["status"]
        if "Offside" in status:
            print("✓ Anchor term risk identified")
            tests_passed.append("Retail - anchor risk")

            # Check for mitigations
            anchor_risks = [r for r in result["risks_ranked"]
                          if "anchor" in r["name"].lower()]
            if anchor_risks and anchor_risks[0]["mitigations"]:
                print(f"✓ Mitigations provided: {anchor_risks[0]['mitigations']}")
                tests_passed.append("Retail - mitigations")
        else:
            print("✗ Anchor term risk NOT identified")
            tests_failed.append("Retail - anchor risk")

    # Test 5: Hotel Limited Service - GOP
    print("\n" + "="*60)
    print("TEST 5: Hotel Limited Service - GOP")
    print("="*60)

    engine = CREExtractionEngine("hospitality", "limited_service")
    result = engine.extract("""
        Hotel: 120 keys limited service
        ADR: $125
        Occupancy: 72%
        RevPAR: $90
        GOP Margin: 42%
        Purchase Price: $18 million
        NOI: $2.16 million
    """)

    # Check GOP extraction and benchmark
    if "gop_margin_pct" in result["ingested"]:
        print(f"✓ GOP margin extracted: {result['ingested']['gop_margin_pct']:.1%}")
        tests_passed.append("Hotel - GOP extraction")
    else:
        print("✗ GOP margin NOT extracted")
        tests_failed.append("Hotel - GOP extraction")

    # Check if PIP was flagged as missing
    if any("pip" in item.lower() for item in result["unknown"]):
        print("✓ PIP flagged as missing")
        tests_passed.append("Hotel - PIP missing")
    else:
        print("✗ PIP NOT flagged")
        tests_failed.append("Hotel - PIP missing")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {len(tests_passed)}/{len(tests_passed) + len(tests_failed)}")
    print(f"Failed: {len(tests_failed)}")

    if tests_failed:
        print("\nFailed tests:")
        for test in tests_failed:
            print(f"  - {test}")

    return len(tests_failed) == 0

# Run tests if executed directly
if __name__ == "__main__":
    success = run_acceptance_tests()
    if success:
        print("\n✅ All acceptance tests passed!")
    else:
        print("\n❌ Some tests failed. Review output above.")