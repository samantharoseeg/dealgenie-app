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
# COMPREHENSIVE FIELD SYNONYMS & PATTERNS
# ============================================================================

FIELD_SYNONYMS = {
    # Core Financial Metrics
    "purchase_price": [
        r"purchase\s+price", r"acquisition\s+price", r"contract\s+price",
        r"sale\s+price", r"sales\s+price", r"closing\s+price", r"total\s+consideration",
        r"acquisition\s+cost", r"pp", r"purchase\s+amount", r"deal\s+size",
        r"transaction\s+value", r"enterprise\s+value"
    ],
    "noi": [
        r"net\s+operating\s+income", r"noi", r"operating\s+income",
        r"net\s+income", r"annual\s+noi", r"effective\s+noi"
    ],
    "noi_now": [
        r"noi(?:\s+now)?(?![\s\-]stab)", r"in[\-\s]place\s+noi", r"current\s+noi",
        r"noi\s+yr\s+1", r"noi\s+year\s+1", r"noi\s+\(t[\-\s]12\)", r"trailing\s+noi",
        r"actual\s+noi", r"t\-12\s+noi", r"ttm\s+noi", r"in\s+place\s+noi",
        r"today's\s+noi", r"as[\-\s]is\s+noi"
    ],
    "noi_stab": [
        r"stabilized\s+noi", r"proforma\s+noi", r"pro[\-\s]forma\s+noi",
        r"underwritten\s+noi", r"projected\s+noi", r"year\s+2\s+noi",
        r"noi\s+stab", r"forward\s+noi", r"uw\s+noi", r"pf\s+noi",
        r"stabilization\s+noi", r"future\s+noi"
    ],

    # Cap Rates
    "cap_rate": [
        r"cap\s+rate", r"capitalization\s+rate", r"cap", r"initial\s+yield",
        r"going\s+in\s+cap", r"acquisition\s+cap", r"entry\s+yield"
    ],
    "entry_cap": [
        r"entry\s+cap", r"going[\-\s]in\s+cap", r"in[\-\s]place\s+cap",
        r"cap\s+on\s+price", r"purchase\s+cap", r"acquisition\s+cap",
        r"initial\s+cap", r"day\s+1\s+cap", r"year\s+1\s+cap",
        r"in\s+place\s+yield", r"current\s+cap"
    ],
    "exit_cap": [
        r"exit\s+cap", r"terminal\s+cap", r"reversion\s+cap",
        r"disposition\s+cap", r"sale\s+cap", r"residual\s+cap",
        r"take[\-\s]out\s+cap", r"year\s+5\s+cap", r"terminal\s+value\s+cap"
    ],

    # Property Size
    "square_feet": [
        r"square\s+f[eo][eo]t", r"sf", r"total\s+sf", r"building\s+sf",
        r"total\s+square\s+footage", r"total\s+area"
    ],

    # Loan Terms
    "loan_amount": [
        r"loan\s+amount", r"debt", r"mortgage", r"financing",
        r"loan\s+proceeds", r"debt\s+amount", r"mortgage\s+amount",
        r"loan\s+size", r"debt\s+proceeds", r"leverage\s+amount",
        r"senior\s+debt", r"first\s+mortgage"
    ],
    "ltv": [
        r"ltv", r"loan[\-\s]to[\-\s]value", r"leverage", r"debt\s+ratio",
        r"ltv\s+ratio", r"loan\s+to\s+cost", r"ltc", r"debt[\-\s]to[\-\s]value"
    ],
    "interest_rate": [
        r"interest\s+rate", r"rate", r"coupon", r"all[\-\s]in\s+rate",
        r"loan\s+rate", r"mortgage\s+rate", r"debt\s+rate", r"borrowing\s+rate",
        r"fixed\s+rate", r"floating\s+rate", r"index\s+\+", r"sofr\s*\+",
        r"libor\s*\+", r"prime\s*\+"
    ],
    "dscr": [
        r"dscr", r"debt\s+service\s+coverage", r"debt\s+coverage",
        r"coverage\s+ratio", r"dcr", r"debt\s+service\s+cover",
        r"debt\s+yield", r"coverage", r"dsc"
    ],
    "amort_years": [
        r"amortization", r"amort", r"loan\s+term", r"term",
        r"amort\s+period", r"amortization\s+period", r"repayment\s+term",
        r"loan\s+maturity", r"maturity"
    ],
    "io_years": [
        r"io\s+period", r"interest[\-\s]only", r"io", r"i/o",
        r"interest\s+only\s+period", r"io\s+term", r"non[\-\s]amortizing",
        r"interest[\-\s]only\s+years"
    ],

    # Lease Terms
    "walt": [
        r"walt", r"weighted\s+average\s+lease\s+term", r"wall",
        r"remaining\s+lease\s+term", r"lease\s+duration", r"average\s+lease\s+term",
        r"weighted\s+avg\s+lease", r"lease\s+expiry", r"lease\s+maturity"
    ],
    "ti": [
        r"ti", r"tenant\s+improvement", r"tenant\s+improvements",
        r"ti\s+allowance", r"improvement\s+allowance", r"build[\-\s]out",
        r"ti\s+psf", r"ti\s+per\s+sf", r"tenant\s+allowance"
    ],
    "ti_new_psf": [
        r"ti[\-\s]new", r"new\s+lease\s+ti", r"new\s+tenant\s+ti",
        r"first\s+generation\s+ti", r"new\s+ti", r"ti\s+for\s+new"
    ],
    "ti_renewal_psf": [
        r"ti[\-\s]renewal", r"renewal\s+ti", r"renewing\s+ti",
        r"second\s+generation\s+ti", r"renewal\s+allowance", r"ti\s+for\s+renewals"
    ],
    "lc": [
        r"lc", r"leasing\s+commission", r"leasing\s+commissions",
        r"broker\s+commission", r"broker\s+fee", r"leasing\s+cost",
        r"commission", r"broker\s+commission"
    ],
    "lc_new_pct": [
        r"lc[\-\s]new", r"new\s+lease\s+commission", r"new\s+lc",
        r"first\s+generation\s+lc", r"new\s+tenant\s+commission"
    ],
    "lc_renewal_pct": [
        r"lc[\-\s]renewal", r"renewal\s+commission", r"renewal\s+lc",
        r"second\s+generation\s+lc", r"renewing\s+commission"
    ],

    # Property Metrics
    "square_feet": [
        r"square\s+feet", r"sf", r"sq\s+ft", r"sq\.ft\.", r"sqft",
        r"gla", r"nra", r"gross\s+leasable\s+area", r"rentable\s+area",
        r"building\s+size", r"total\s+sf", r"leasable\s+sf", r"rsf"
    ],
    "units": [
        r"units", r"unit\s+count", r"doors", r"apartments",
        r"total\s+units", r"unit\s+mix", r"number\s+of\s+units",
        r"dwelling\s+units", r"residential\s+units"
    ],
    "occupancy_pct": [
        r"occupancy", r"occupied", r"leased", r"occupancy\s+rate",
        r"occ", r"physical\s+occupancy", r"economic\s+occupancy",
        r"leased\s+%", r"occupied\s+%", r"utilization"
    ],
    "expense_ratio": [
        r"expense\s+ratio", r"opex\s+ratio", r"expense\s+%",
        r"operating\s+expense\s+ratio", r"expense\s+rate", r"opex\s+%",
        r"operating\s+margin", r"expense\s+percentage"
    ],

    # Industrial Specific
    "clear_height_ft": [
        r"clear\s+height", r"ceiling\s+height", r"clearance",
        r"height", r"clear\s+span", r"warehouse\s+height",
        r"clear\s+ceiling", r"vertical\s+clearance"
    ],
    "dock_doors": [
        r"dock\s+doors", r"loading\s+docks", r"dock[\-\s]high\s+doors",
        r"truck\s+doors", r"loading\s+doors", r"docks", r"dock\s+positions",
        r"loading\s+bays"
    ],
    "office_finish_pct": [
        r"office\s+finish", r"office\s+%", r"office\s+buildout",
        r"office\s+space", r"office\s+percentage", r"finished\s+office"
    ],

    # Hotel Specific
    "keys": [
        r"keys", r"rooms", r"room\s+count", r"guestrooms",
        r"hotel\s+rooms", r"number\s+of\s+rooms", r"room\s+keys",
        r"guest\s+units"
    ],
    "adr": [
        r"adr", r"average\s+daily\s+rate", r"room\s+rate",
        r"avg\s+rate", r"daily\s+rate", r"average\s+rate",
        r"avg\s+room\s+rate"
    ],
    "revpar": [
        r"revpar", r"rev\s+par", r"revenue\s+per\s+available\s+room",
        r"revpar\s+index", r"room\s+revenue", r"rev\s+per\s+room"
    ],
    "gop_margin_pct": [
        r"gop\s+margin", r"gross\s+operating\s+profit", r"gop",
        r"gross\s+margin", r"gop\s+%", r"operating\s+margin",
        r"gross\s+operating\s+margin"
    ],
    "pip_cost_per_key": [
        r"pip\s+cost", r"pip", r"property\s+improvement\s+plan",
        r"renovation\s+cost", r"capex\s+per\s+key", r"pip\s+per\s+room",
        r"renovation\s+per\s+key", r"refurb\s+cost"
    ],

    # Retail Specific
    "anchor_tenant": [
        r"anchor\s+tenant", r"anchor", r"major\s+tenant",
        r"anchor\s+store", r"key\s+tenant", r"primary\s+tenant",
        r"main\s+tenant"
    ],
    "anchor_term_years": [
        r"anchor\s+term", r"anchor\s+lease\s+term", r"anchor\s+expiry",
        r"anchor\s+remaining", r"major\s+tenant\s+term"
    ],
    "sales_psf": [
        r"sales\s+per\s+square\s+foot", r"sales\s+psf", r"tenant\s+sales",
        r"retail\s+sales", r"sales\s+volume", r"sales\s+per\s+sf",
        r"sales/sf", r"productivity"
    ],
    "parking_ratio": [
        r"parking\s+ratio", r"parking\s+index", r"parking\s+per\s+sf",
        r"stalls\s+per\s+1000\s+sf", r"parking\s+density", r"spaces\s+per\s+1000",
        r"parking\s+spaces/1000"
    ],

    # Multifamily Specific
    "avg_rent": [
        r"average\s+rent", r"avg\s+rent", r"mean\s+rent",
        r"avg\s+monthly\s+rent", r"effective\s+rent", r"average\s+unit\s+rent",
        r"rent\s+per\s+unit", r"monthly\s+rent"
    ],
    "market_rent": [
        r"market\s+rent", r"asking\s+rent", r"market\s+rate",
        r"comparable\s+rent", r"comp\s+rent", r"market\s+asking"
    ],
    "concessions_months": [
        r"concessions", r"rent\s+concessions", r"free\s+rent",
        r"incentives", r"move[\-\s]in\s+specials", r"discounts",
        r"months\s+free", r"concession\s+months"
    ],

    # Returns & Valuation
    "irr": [
        r"irr", r"internal\s+rate\s+of\s+return", r"levered\s+irr",
        r"unlevered\s+irr", r"project\s+irr", r"equity\s+irr"
    ],
    "equity_multiple": [
        r"equity\s+multiple", r"em", r"equity\s+mult", r"multiple",
        r"moic", r"multiple\s+on\s+invested\s+capital", r"total\s+return"
    ],
    "cash_on_cash": [
        r"cash[\-\s]on[\-\s]cash", r"coc", r"cash\s+yield",
        r"current\s+return", r"cash\s+return", r"year\s+1\s+return"
    ],
    "hold_period": [
        r"hold\s+period", r"investment\s+period", r"holding\s+period",
        r"investment\s+horizon", r"term", r"duration", r"exit\s+year",
        r"disposition\s+year", r"hold\s+years"
    ]
}

# ============================================================================
# ADVANCED PARSING FUNCTIONS
# ============================================================================

def parse_with_synonyms(text: str, field_name: str) -> Optional[Union[float, Dict[str, Any]]]:
    """
    Parse a field value using all known synonyms from FIELD_SYNONYMS

    Args:
        text: OCR text to search
        field_name: Standard field name to search for

    Returns:
        Extracted value as float, or dict for ranges/spreads, or None if not found
    """
    if field_name not in FIELD_SYNONYMS:
        return None

    # Clean text for better matching
    text_lower = text.lower()
    text_clean = re.sub(r'\s+', ' ', text_lower)

    # Try each synonym pattern
    for pattern in FIELD_SYNONYMS[field_name]:
        # Build regex to capture value after the field name
        value_patterns = [
            rf"{pattern}[\s:]*\$?([\d,]+\.?\d*)\s*(?:mm?|m|k)?",  # Basic number
            rf"{pattern}[\s:]*(\d+\.?\d*)\s*%",  # Percentage
            rf"{pattern}[\s:]*\$?([\d,]+\.?\d*)\s*-\s*\$?([\d,]+\.?\d*)",  # Range
            rf"{pattern}[\s:]*(sofr|libor|prime|wsjp|bsby|term\s+sofr)[\s\+]*([\d\.]+)",  # Index + spread
            rf"{pattern}[\s:]*([a-zA-Z\s]+)",  # Text value (for tenant names, etc)
        ]

        for val_pattern in value_patterns:
            match = re.search(val_pattern, text_clean, re.IGNORECASE)
            if match:
                return parse_value_match(match, field_name)

    return None

def parse_value_match(match: re.Match, field_name: str) -> Union[float, Dict[str, Any]]:
    """
    Parse the matched value based on its format
    """
    groups = match.groups()

    # Check for index + spread format (e.g., "SOFR + 275")
    if len(groups) == 2 and isinstance(groups[0], str) and groups[0].lower() in ['sofr', 'libor', 'prime', 'wsjp', 'bsby', 'term sofr']:
        return {
            "type": "spread",
            "index": groups[0].upper(),
            "spread_bps": float(groups[1])
        }

    # Check for range format (e.g., "5.0 - 5.5")
    if '-' in match.group(0):
        range_match = re.findall(r'[\d,]+\.?\d*', match.group(0))
        if len(range_match) >= 2:
            low = parse_number(range_match[0])
            high = parse_number(range_match[1])
            return {
                "type": "range",
                "low": low,
                "high": high,
                "mid": (low + high) / 2
            }

    # Single value
    if groups:
        value_str = groups[0]

        # Check if it's a text value (for fields like anchor_tenant)
        if field_name in ["anchor_tenant", "brand_flag", "asset_class"]:
            return value_str.strip()

        # Parse as number
        return parse_number(value_str)

    return None

def parse_number(value_str: str) -> float:
    """
    Parse a number string with various formats
    """
    if not value_str:
        return 0.0

    # Remove commas and dollar signs
    clean = value_str.replace(',', '').replace('$', '').strip()

    # Handle multipliers (M, MM, K)
    multiplier = 1
    if clean.lower().endswith('mm'):
        multiplier = 1_000_000
        clean = clean[:-2]
    elif clean.lower().endswith('m'):
        multiplier = 1_000_000
        clean = clean[:-1]
    elif clean.lower().endswith('k'):
        multiplier = 1_000
        clean = clean[:-1]

    try:
        return float(clean) * multiplier
    except ValueError:
        return 0.0

def parse_range(text: str) -> Dict[str, float]:
    """
    Parse range expressions like "5.0-5.5%" or "$200-$250 PSF"

    Returns:
        Dict with 'low', 'high', and 'mid' values
    """
    # Find all numbers in the text
    numbers = re.findall(r'[\d,]+\.?\d*', text)

    if len(numbers) >= 2:
        low = parse_number(numbers[0])
        high = parse_number(numbers[1])
        return {
            "low": min(low, high),
            "high": max(low, high),
            "mid": (low + high) / 2
        }
    elif len(numbers) == 1:
        value = parse_number(numbers[0])
        return {
            "low": value,
            "high": value,
            "mid": value
        }

    return {"low": 0, "high": 0, "mid": 0}

def parse_spread(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse spread expressions like "SOFR+275" or "LIBOR + 3.25%"

    Returns:
        Dict with 'index' and 'spread_bps' or None
    """
    # Pattern for index + spread
    pattern = r'(sofr|libor|prime|wsjp|bsby|term\s+sofr)[\s\+]*([\d\.]+)\s*(?:bps|bp|basis|%)?'
    match = re.search(pattern, text.lower())

    if match:
        index = match.group(1).upper()
        spread_value = float(match.group(2))

        # Convert to basis points if necessary
        if '%' in text:
            spread_bps = spread_value * 100
        elif spread_value < 10:  # Assume it's in percentage
            spread_bps = spread_value * 100
        else:  # Assume it's already in bps
            spread_bps = spread_value

        return {
            "type": "floating_rate",
            "index": index.replace(' ', '_'),
            "spread_bps": spread_bps,
            "all_in_estimate": get_index_rate(index) + (spread_bps / 10000)
        }

    return None

def get_index_rate(index: str) -> float:
    """
    Get current index rate (would connect to real data source in production)
    """
    # Placeholder rates as of Q4 2024
    rates = {
        "SOFR": 0.0533,
        "TERM_SOFR": 0.0545,
        "LIBOR": 0.0565,  # Being phased out
        "PRIME": 0.085,
        "WSJP": 0.085,
        "BSBY": 0.0548
    }
    return rates.get(index.upper().replace(' ', '_'), 0.05)

def extract_all_fields_with_synonyms(text: str, asset_class: str = None) -> Dict[str, Any]:
    """
    Extract all fields using synonym matching

    Args:
        text: OCR text to parse
        asset_class: Optional asset class to prioritize specific fields

    Returns:
        Dictionary of extracted fields and values
    """
    extracted = {}

    # Priority order based on asset class
    if asset_class:
        priority_fields = get_priority_fields(asset_class)
    else:
        priority_fields = list(FIELD_SYNONYMS.keys())

    for field in priority_fields:
        value = parse_with_synonyms(text, field)
        if value is not None:
            extracted[field] = value

    # Post-process for consistency
    extracted = post_process_extracted(extracted)

    return extracted

def get_priority_fields(asset_class: str) -> List[str]:
    """
    Get priority field order based on asset class
    """
    common = ["purchase_price", "noi", "noi_now", "noi_stab", "cap_rate",
              "loan_amount", "ltv", "interest_rate", "dscr"]

    specific = {
        "multifamily": ["units", "avg_rent", "market_rent", "occupancy_pct", "expense_ratio"],
        "office": ["square_feet", "walt", "ti_new_psf", "lc_new_pct", "parking_ratio"],
        "industrial": ["square_feet", "clear_height_ft", "dock_doors", "office_finish_pct"],
        "retail": ["square_feet", "anchor_tenant", "sales_psf", "parking_ratio"],
        "hospitality": ["keys", "adr", "revpar", "gop_margin_pct", "pip_cost_per_key"]
    }

    asset_fields = specific.get(asset_class.lower(), [])
    return common + asset_fields + [f for f in FIELD_SYNONYMS.keys() if f not in common + asset_fields]

def post_process_extracted(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process extracted values for consistency
    """
    # Convert percentages to decimals where appropriate
    pct_fields = ["ltv", "occupancy_pct", "expense_ratio", "gop_margin_pct",
                  "office_finish_pct", "lc_new_pct", "lc_renewal_pct"]

    for field in pct_fields:
        if field in extracted:
            value = extracted[field]
            if isinstance(value, (int, float)):
                # If value is > 1, assume it's a percentage and convert to decimal
                if value > 1:
                    extracted[field] = value / 100
            elif isinstance(value, dict) and value.get("type") == "range":
                if value["high"] > 1:
                    value["low"] /= 100
                    value["high"] /= 100
                    value["mid"] /= 100

    # Ensure cap rates are decimals
    cap_fields = ["cap_rate", "entry_cap", "exit_cap"]
    for field in cap_fields:
        if field in extracted:
            value = extracted[field]
            if isinstance(value, (int, float)) and value > 0.15:  # Likely percentage
                extracted[field] = value / 100

    return extracted

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
# METRIC DEPENDENCIES - What's needed to calculate each derived metric
# ============================================================================

METRIC_DEPENDENCIES = {
    # Basic Metrics
    "cap_rate": {
        "required": ["noi_now", "purchase_price"],
        "explanation": "Current cap rate requires NOI and purchase price to calculate yield"
    },
    "ltv": {
        "required": ["loan_amount", "purchase_price"],
        "explanation": "Loan-to-value ratio requires loan amount and purchase price"
    },
    "dscr": {
        "required": ["noi_now", "loan_amount", "interest_rate", "amort_years"],
        "explanation": "Debt service coverage requires NOI and debt service calculation inputs"
    },
    "debt_yield": {
        "required": ["noi_now", "loan_amount"],
        "explanation": "Debt yield measures NOI as percentage of loan amount"
    },
    "yield_on_cost": {
        "required": ["noi_stab", "purchase_price"],
        "explanation": "Stabilized yield requires stabilized NOI and total project cost"
    },

    # Return Metrics
    "irr": {
        "required": ["purchase_price", "loan_amount", "noi_now", "noi_growth_rate", "hold_years", "exit_cap", "sale_costs"],
        "explanation": "IRR calculation needs complete cash flow projections including entry, operations, and exit"
    },
    "equity_multiple": {
        "required": ["purchase_price", "loan_amount", "exit_value", "net_cash_flows"],
        "explanation": "Equity multiple requires initial equity investment and total proceeds over hold period"
    },
    "cash_on_cash": {
        "required": ["noi_now", "loan_amount", "interest_rate", "purchase_price"],
        "explanation": "Cash-on-cash return needs net cash flow after debt service and initial equity"
    },

    # Exit Metrics
    "exit_value": {
        "required": ["noi_now", "noi_growth_rate", "hold_years", "exit_cap"],
        "explanation": "Exit value requires projected NOI at sale and exit cap rate assumption"
    },
    "net_sale_proceeds": {
        "required": ["exit_value", "loan_amount", "sale_costs"],
        "explanation": "Net proceeds need exit value less outstanding debt and transaction costs"
    },
    "refi_proceeds": {
        "required": ["noi_stab", "market_cap_for_refi", "refi_ltv"],
        "explanation": "Refinance proceeds require stabilized value and new loan parameters"
    },

    # Operational Metrics
    "effective_gross_income": {
        "required": ["potential_gross_income", "vacancy_rate", "credit_loss"],
        "explanation": "EGI needs gross potential rent less vacancy and credit losses"
    },
    "operating_expenses": {
        "required": ["expense_ratio", "effective_gross_income"],
        "explanation": "Operating expenses require expense ratio and gross income"
    },
    "noi": {
        "required": ["effective_gross_income", "operating_expenses"],
        "explanation": "NOI equals effective gross income less operating expenses"
    },

    # Asset-Specific Metrics
    "revpar": {
        "required": ["adr", "occupancy_pct"],
        "explanation": "RevPAR (Revenue Per Available Room) needs ADR and occupancy rate"
    },
    "gross_operating_profit": {
        "required": ["revenue", "gop_margin_pct"],
        "explanation": "GOP requires total revenue and gross operating profit margin"
    },
    "rent_psf": {
        "required": ["annual_rent", "square_feet"],
        "explanation": "Rent per square foot needs total rent and leasable area"
    },
    "price_per_unit": {
        "required": ["purchase_price", "units"],
        "explanation": "Price per unit requires purchase price and total unit count"
    },
    "price_psf": {
        "required": ["purchase_price", "square_feet"],
        "explanation": "Price per SF needs purchase price and building size"
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
    "garden_lowrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio", "replacement_reserves"],
    "midrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio", "parking_ratio", "replacement_reserves"],
    "highrise": ["units", "avg_rent", "occupancy_pct", "expense_ratio", "concessions_months", "replacement_reserves"],

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
        self.field_confidence = {}  # New detailed confidence tracking
        self.conflicts = {}
        self.derived = {}
        self.bench_compare = {}
        self.validation_warnings = []
        self.risks_ranked = []
        self.known = []
        self.unknown = []
        self.sensitivities = {}
        self.glossary_refs = []
        self.notes = []

    def _is_in_table(self, text: str, ocr_blocks: Optional[List[Dict]] = None) -> bool:
        """
        Check if text appears to be in a table structure

        Args:
            text: The text to check
            ocr_blocks: Optional OCR blocks with positional data

        Returns:
            True if text appears to be in a table
        """
        if not ocr_blocks:
            # Fallback: Check for table-like patterns in surrounding text
            lines = text.split('\n')
            for line in lines:
                # Check for patterns like aligned columns, headers, separators
                if any(sep in line for sep in ['|', '\t\t', '   ']) and len(line.split()) > 2:
                    return True
                # Check for header keywords
                if any(header in line.upper() for header in ['METRIC', 'VALUE', 'AMOUNT', 'RATE', 'TERM']):
                    return True
            return False

        # If we have OCR blocks, check for table structure
        for block in ocr_blocks:
            if text in block.get('text', ''):
                # Check if block has table indicators
                if 'table' in block.get('type', '').lower():
                    return True
                # Check bbox alignment with other blocks (indicates table)
                bbox = block.get('bbox', {})
                if bbox:
                    # Simple heuristic: tables have aligned x-coordinates
                    x_coord = bbox.get('x', 0)
                    aligned_blocks = [b for b in ocr_blocks
                                    if abs(b.get('bbox', {}).get('x', 0) - x_coord) < 5]
                    if len(aligned_blocks) > 3:
                        return True
        return False

    def _has_unit_suffix(self, text: str, value: str) -> bool:
        """
        Check if extracted value has a clear unit suffix

        Args:
            text: The full text context
            value: The extracted value

        Returns:
            True if value has unit suffix like $, %, SF, etc.
        """
        # Find value in text and check what follows
        import re

        # Common unit patterns
        unit_patterns = [
            r'\$[\d,]+',  # Dollar amounts
            r'[\d.]+\s*%',  # Percentages
            r'[\d,]+\s*(?:sf|SF|sq\.?\s*ft)',  # Square feet
            r'[\d,]+\s*(?:units?|keys?|rooms?)',  # Unit counts
            r'[\d.]+[xX]',  # Multiples (1.25x)
            r'[\d.]+\s*(?:years?|yrs?|months?|mos?)',  # Time periods
            r'[\d,]+\s*(?:psf|/sf|per\s+sf)',  # Per square foot
            r'[\d.]+\s*(?:cap|bps|basis\s+points?)',  # Financial metrics
        ]

        for pattern in unit_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _assign_confidence(self, field_name: str, value: Any,
                          extraction_method: str, ocr_blocks: Optional[List[Dict]] = None,
                          source_text: str = "") -> None:
        """
        Assign confidence level to extracted field

        Args:
            field_name: Name of the field
            value: Extracted value
            extraction_method: How the value was extracted
            ocr_blocks: Optional OCR blocks for position analysis
            source_text: Text context where value was found
        """
        confidence_level = "Medium"  # Default
        reason = "Found in document text"

        # HIGH confidence scenarios
        if extraction_method == "table":
            confidence_level = "High"
            reason = "Extracted from structured table"
        elif self._is_in_table(source_text, ocr_blocks):
            confidence_level = "High"
            reason = "Found in table with header match"
        elif extraction_method == "explicit_label":
            confidence_level = "High"
            reason = "Found with explicit field label"
        elif field_name in ["purchase_price", "noi", "loan_amount"] and self._has_unit_suffix(source_text, str(value)):
            confidence_level = "High"
            reason = "Primary metric with clear unit identifier"

        # MEDIUM confidence scenarios
        elif extraction_method == "pattern_match":
            confidence_level = "Medium"
            reason = "Pattern matched in body text"
        elif self._has_unit_suffix(source_text, str(value)):
            confidence_level = "Medium"
            reason = "Found with unit suffix"
        elif extraction_method == "synonym_match":
            confidence_level = "Medium"
            reason = "Matched using field synonyms"

        # LOW confidence scenarios
        elif extraction_method == "calculated":
            confidence_level = "Low"
            reason = "Back-calculated from other fields"
        elif extraction_method == "inferred":
            confidence_level = "Low"
            reason = "Inferred from context"
        elif extraction_method == "default":
            confidence_level = "Low"
            reason = "Using industry default assumption"

        # Store both simple and detailed confidence
        self.confidence[field_name] = confidence_level
        self.field_confidence[field_name] = {
            "level": confidence_level,
            "reason": reason,
            "method": extraction_method,
            "value": value
        }

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
            "field_confidence": self.field_confidence,  # Add detailed confidence tracking
            "validation_warnings": self.validation_warnings if hasattr(self, 'validation_warnings') else [],
            "glossary_refs": self.glossary_refs,
            "notes": self.notes
        }

    def _extract_fields(self, raw_text: str, ocr_blocks: Optional[List[Dict]]):
        """Extract fields using advanced synonym matching and parsing"""

        # Use the new comprehensive extraction function
        extracted = extract_all_fields_with_synonyms(raw_text, self.asset_class)

        # Process extracted values
        for field_name, value in extracted.items():
            # Determine extraction context for confidence
            source_text = raw_text  # Could be enhanced with specific match context

            # Handle different value types
            if isinstance(value, dict):
                if value.get("type") == "range":
                    # Store range values
                    self.ingested[field_name] = value["mid"]  # Use midpoint as primary value
                    self.ingested[f"{field_name}_low"] = value["low"]
                    self.ingested[f"{field_name}_high"] = value["high"]
                    # Assign confidence for range values
                    self._assign_confidence(field_name, value["mid"], "pattern_match",
                                           ocr_blocks, source_text)
                    self.notes.append(f"{field_name}: range {value['low']:.2f}-{value['high']:.2f}")

                elif value.get("type") in ["spread", "floating_rate"]:
                    # Store spread details
                    self.ingested[field_name] = value.get("all_in_estimate", 0)
                    self.ingested[f"{field_name}_index"] = value["index"]
                    self.ingested[f"{field_name}_spread_bps"] = value["spread_bps"]
                    # High confidence for structured rate data
                    self._assign_confidence(field_name, value.get("all_in_estimate", 0),
                                           "explicit_label", ocr_blocks, source_text)
                    self.notes.append(f"{field_name}: {value['index']} + {value['spread_bps']}bps")

            else:
                # Simple value
                self.ingested[field_name] = value

                # Determine extraction method for confidence
                if field_name in ["purchase_price", "noi", "loan_amount"]:
                    # Check if value appears in a table
                    if self._is_in_table(source_text, ocr_blocks):
                        method = "table"
                    elif self._has_unit_suffix(source_text, str(value)):
                        method = "explicit_label"
                    else:
                        method = "pattern_match"
                else:
                    method = "synonym_match"

                # Assign detailed confidence
                self._assign_confidence(field_name, value, method, ocr_blocks, source_text)

        # Legacy fallback for any fields not captured by new parser
        text_upper = raw_text.upper()

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
        """Comprehensive cross-validation with detailed warnings"""

        self.validation_warnings = []

        # 1. Entry Cap vs NOI validation
        if "entry_cap" in self.ingested and "purchase_price" in self.ingested:
            expected_noi = self.ingested["entry_cap"] * self.ingested["purchase_price"]

            if "noi_now" in self.ingested:
                variance = abs(expected_noi - self.ingested["noi_now"]) / expected_noi if expected_noi > 0 else 0

                if variance > 0.05:  # >5% variance
                    self.confidence["noi_now"] = "Low"
                    self.confidence["entry_cap"] = "Low"
                    warning = {
                        "type": "cap_rate_noi_mismatch",
                        "severity": "HIGH" if variance > 0.10 else "MEDIUM",
                        "message": f"Cap rate implies NOI of ${expected_noi:,.0f}, but extracted NOI is ${self.ingested['noi_now']:,.0f} ({variance*100:.1f}% variance)",
                        "fields_affected": ["entry_cap", "noi_now"],
                        "expected_value": expected_noi,
                        "actual_value": self.ingested["noi_now"],
                        "variance_pct": variance * 100
                    }
                    self.validation_warnings.append(warning)
                    self.notes.append(f"⚠️ Cap/NOI mismatch: {variance*100:.1f}% variance")
            elif "noi" in self.ingested:
                # Check against generic NOI field
                variance = abs(expected_noi - self.ingested["noi"]) / expected_noi if expected_noi > 0 else 0

                if variance > 0.05:
                    self.confidence["noi"] = "Low"
                    self.confidence["entry_cap"] = "Low"
                    warning = {
                        "type": "cap_rate_noi_mismatch",
                        "severity": "MEDIUM",
                        "message": f"Cap rate implies NOI of ${expected_noi:,.0f}, extracted NOI is ${self.ingested['noi']:,.0f}",
                        "fields_affected": ["entry_cap", "noi"],
                        "variance_pct": variance * 100
                    }
                    self.validation_warnings.append(warning)

        # Alternative cap rate check using cap_rate field
        if "cap_rate" in self.ingested and "purchase_price" in self.ingested and "noi_now" in self.ingested:
            calculated_cap = self.ingested["noi_now"] / self.ingested["purchase_price"]
            stated_cap = self.ingested["cap_rate"]

            variance = abs(calculated_cap - stated_cap) / stated_cap if stated_cap > 0 else 0

            if variance > 0.05:
                self.confidence["cap_rate"] = "Low"
                warning = {
                    "type": "cap_rate_calculation_mismatch",
                    "severity": "MEDIUM",
                    "message": f"Stated cap {stated_cap*100:.2f}% vs calculated {calculated_cap*100:.2f}%",
                    "fields_affected": ["cap_rate"],
                    "calculated_value": calculated_cap,
                    "stated_value": stated_cap,
                    "variance_pct": variance * 100
                }
                self.validation_warnings.append(warning)

        # 2. LTV vs Loan Amount validation
        if "ltv" in self.ingested and "purchase_price" in self.ingested:
            expected_loan = self.ingested["ltv"] * self.ingested["purchase_price"]

            if "loan_amount" in self.ingested:
                variance = abs(expected_loan - self.ingested["loan_amount"]) / expected_loan if expected_loan > 0 else 0

                if variance > 0.02:  # >2% variance (tighter for LTV)
                    self.confidence["loan_amount"] = "Low"
                    self.confidence["ltv"] = "Low"
                    warning = {
                        "type": "ltv_loan_mismatch",
                        "severity": "HIGH" if variance > 0.05 else "MEDIUM",
                        "message": f"LTV {self.ingested['ltv']*100:.1f}% implies loan of ${expected_loan:,.0f}, but extracted loan is ${self.ingested['loan_amount']:,.0f}",
                        "fields_affected": ["ltv", "loan_amount"],
                        "expected_value": expected_loan,
                        "actual_value": self.ingested["loan_amount"],
                        "variance_pct": variance * 100
                    }
                    self.validation_warnings.append(warning)
                    self.notes.append(f"⚠️ LTV/Loan mismatch: {variance*100:.1f}% variance")

        # 3. DSCR validation with ADS calculation
        if "loan_amount" in self.ingested and ("interest_rate" in self.ingested or "rate" in self.ingested):
            rate = self.ingested.get("interest_rate", self.ingested.get("rate", 0))

            # Calculate Annual Debt Service (ADS)
            if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                # Interest-only period
                ads = self.ingested["loan_amount"] * rate
                ads_type = "IO"
            else:
                # Amortizing loan
                amort_years = self.ingested.get("amort_years", 30)

                if rate > 0 and amort_years > 0:
                    r = rate / 12  # Monthly rate
                    n = amort_years * 12  # Number of payments

                    if r > 0:
                        # Standard amortization formula
                        mortgage_constant = 12 * (r * (1 + r)**n) / ((1 + r)**n - 1)
                        ads = self.ingested["loan_amount"] * mortgage_constant
                    else:
                        # Zero interest (rare)
                        ads = self.ingested["loan_amount"] / amort_years
                    ads_type = f"{amort_years}yr amort"
                else:
                    ads = 0
                    ads_type = "unknown"

            # Store calculated ADS
            self.derived["ads_calculated"] = ads
            self.derived["ads_type"] = ads_type

            # Validate DSCR if we have NOI
            if ads > 0 and ("noi_now" in self.ingested or "noi" in self.ingested):
                noi = self.ingested.get("noi_now", self.ingested.get("noi", 0))
                calculated_dscr = noi / ads

                if "dscr" in self.ingested:
                    stated_dscr = self.ingested["dscr"]
                    variance = abs(calculated_dscr - stated_dscr) / stated_dscr if stated_dscr > 0 else 0

                    if variance > 0.05:  # >5% variance
                        self.confidence["dscr"] = "Low"
                        warning = {
                            "type": "dscr_calculation_mismatch",
                            "severity": "HIGH" if variance > 0.10 else "MEDIUM",
                            "message": f"DSCR calc: NOI ${noi:,.0f} / ADS ${ads:,.0f} = {calculated_dscr:.2f}x, but stated is {stated_dscr:.2f}x",
                            "fields_affected": ["dscr", "noi_now", "loan_amount", "interest_rate"],
                            "calculated_dscr": calculated_dscr,
                            "stated_dscr": stated_dscr,
                            "ads": ads,
                            "ads_type": ads_type,
                            "variance_pct": variance * 100
                        }
                        self.validation_warnings.append(warning)
                        self.notes.append(f"⚠️ DSCR mismatch: stated {stated_dscr:.2f}x vs calc {calculated_dscr:.2f}x")
                else:
                    # No stated DSCR, store calculated value
                    self.derived["dscr_calculated"] = calculated_dscr
                    self.notes.append(f"ℹ️ Calculated DSCR: {calculated_dscr:.2f}x")

        # 4. Additional validation: Equity check
        if "purchase_price" in self.ingested and "loan_amount" in self.ingested:
            equity = self.ingested["purchase_price"] - self.ingested["loan_amount"]

            if equity < 0:
                warning = {
                    "type": "negative_equity",
                    "severity": "HIGH",
                    "message": f"Loan amount ${self.ingested['loan_amount']:,.0f} exceeds purchase price ${self.ingested['purchase_price']:,.0f}",
                    "fields_affected": ["purchase_price", "loan_amount"],
                    "equity": equity
                }
                self.validation_warnings.append(warning)
                self.confidence["loan_amount"] = "Low"

        # 5. Exit cap vs entry cap validation
        if "entry_cap" in self.ingested and "exit_cap" in self.ingested:
            cap_spread = self.ingested["exit_cap"] - self.ingested["entry_cap"]

            if cap_spread < -0.005:  # Exit cap lower than entry (negative spread)
                warning = {
                    "type": "cap_rate_compression",
                    "severity": "LOW",
                    "message": f"Exit cap {self.ingested['exit_cap']*100:.2f}% lower than entry {self.ingested['entry_cap']*100:.2f}% (aggressive assumption)",
                    "fields_affected": ["exit_cap", "entry_cap"],
                    "spread_bps": cap_spread * 10000
                }
                self.validation_warnings.append(warning)

        # 6. Occupancy validation
        if "occupancy_pct" in self.ingested:
            occ = self.ingested["occupancy_pct"]

            if occ > 1.0:
                # Likely still in percentage form
                self.ingested["occupancy_pct"] = occ / 100
                self.notes.append(f"ℹ️ Converted occupancy from {occ}% to {occ/100:.2%}")
            elif occ < 0.5:
                warning = {
                    "type": "low_occupancy",
                    "severity": "HIGH",
                    "message": f"Occupancy {occ*100:.1f}% is unusually low",
                    "fields_affected": ["occupancy_pct"],
                    "value": occ
                }
                self.validation_warnings.append(warning)

        # Summary of validation issues
        if self.validation_warnings:
            high_severity = len([w for w in self.validation_warnings if w["severity"] == "HIGH"])
            medium_severity = len([w for w in self.validation_warnings if w["severity"] == "MEDIUM"])

            self.notes.append(f"📊 Validation: {high_severity} high, {medium_severity} medium severity issues")

    def _compute_derived(self):
        """Compute derived metrics with confidence tracking"""

        # LTV
        if all(k in self.ingested for k in ["loan_amount", "purchase_price"]):
            if self.ingested["purchase_price"] > 0:
                ltv_value = self.ingested["loan_amount"] / self.ingested["purchase_price"]
                self.derived["ltv"] = ltv_value
                self.derived["ltv_calc"] = "Loan Amount / Purchase Price"
                # Assign confidence for calculated LTV
                self._assign_confidence("ltv", ltv_value, "calculated", None,
                                       "Back-calculated from loan amount and purchase price")

        # Cap Rate
        if all(k in self.ingested for k in ["noi_now", "purchase_price"]):
            cap_rate = self.ingested["noi_now"] / self.ingested["purchase_price"]
            self.derived["cap_rate"] = cap_rate
            self.derived["cap_rate_calc"] = "NOI / Purchase Price"
            # Assign confidence for calculated cap rate
            self._assign_confidence("cap_rate", cap_rate, "calculated", None,
                                   "Back-calculated from NOI and purchase price")

        # Yield on Cost
        if all(k in self.ingested for k in ["noi_stab", "purchase_price"]):
            total_cost = self.ingested["purchase_price"] * (1 + self.ingested.get("closing_costs_pct", 0.02))
            self.derived["yield_on_cost"] = self.ingested["noi_stab"] / total_cost
            self.derived["yoc_calc"] = "Stabilized NOI / Total Project Cost"

        # Mortgage Constant
        rate = self.ingested.get("rate") or self.ingested.get("interest_rate", 0)
        if rate > 0 and "amort_years" in self.ingested:
            # Handle rate as percentage (6.25) or decimal (0.0625)
            if rate > 1:
                rate = rate / 100
            r = rate / 12
            n = self.ingested["amort_years"] * 12
            if r > 0 and n > 0:
                self.derived["mortgage_constant"] = 12 * (r * (1 + r)**n) / ((1 + r)**n - 1)
                self.derived["mc_calc"] = "12 * (r*(1+r)^n)/((1+r)^n - 1)"

        # Annual Debt Service
        if "loan_amount" in self.ingested and rate > 0:
            # Normalize rate to decimal
            if rate > 1:
                rate = rate / 100
            if "io_years" in self.ingested and self.ingested["io_years"] > 0:
                self.derived["ads"] = self.ingested["loan_amount"] * rate
                self.derived["ads_calc"] = "Loan × Rate (IO period)"
            elif "mortgage_constant" in self.derived:
                self.derived["ads"] = self.ingested["loan_amount"] * self.derived["mortgage_constant"]
                self.derived["ads_calc"] = "Loan × Mortgage Constant"

        # DSCR
        if "noi_now" in self.ingested and "ads" in self.derived:
            noi = self.ingested.get("noi_now", 0)
            ads = self.derived.get("ads", 0)
            if ads > 0:
                dscr = noi / ads
                self.derived["dscr"] = dscr
                self.derived["dscr_calc"] = "NOI / Annual Debt Service"
                # Assign confidence for calculated DSCR
                self._assign_confidence("dscr", dscr, "calculated", None,
                                       "Back-calculated from NOI and debt service")

        # Debt Yield
        if all(k in self.ingested for k in ["noi_now", "loan_amount"]):
            self.derived["debt_yield"] = self.ingested["noi_now"] / self.ingested["loan_amount"]
            self.derived["debt_yield_calc"] = "NOI / Loan Amount"

        # Exit Value
        if all(k in self.ingested for k in ["exit_cap"]):
            # Project NOI at exit
            hold_years = self.ingested.get("hold_years", 5)
            noi_growth = self.ingested.get("noi_growth_rate", 0.03)

            if "noi_now" in self.ingested and self.ingested["exit_cap"] != 0:
                noi_exit = self.ingested["noi_now"] * ((1 + noi_growth) ** hold_years)
                # Handle exit_cap as either decimal (0.065) or percentage (6.5)
                exit_cap_decimal = self.ingested["exit_cap"] if self.ingested["exit_cap"] < 1 else self.ingested["exit_cap"] / 100
                if exit_cap_decimal > 0:
                    self.derived["exit_value"] = noi_exit / exit_cap_decimal
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

    def _compare_with_overrides(self):
        """Compare metrics using user-provided benchmark overrides"""

        if not self.benchmark_overrides:
            return

        # Process each override
        for metric_name, override_values in self.benchmark_overrides.items():
            # Extract override values
            if isinstance(override_values, (list, tuple)) and len(override_values) >= 3:
                min_val = override_values[0]
                pref_val = override_values[1]
                max_val = override_values[2]
                source = override_values[3] if len(override_values) > 3 else "User Override"
            else:
                continue  # Skip invalid override format

            # Get actual metric value
            value = None
            if metric_name == "cap_rate":
                if "cap_rate" in self.derived:
                    value = self.derived["cap_rate"]
                elif "entry_cap" in self.ingested:
                    value = self.ingested["entry_cap"]
            elif metric_name == "dscr":
                if "dscr" in self.derived:
                    value = self.derived["dscr"]
                elif "dscr" in self.ingested:
                    value = self.ingested["dscr"]
            elif metric_name == "ltv":
                if "ltv" in self.derived:
                    value = self.derived["ltv"]
                elif "ltv" in self.ingested:
                    value = self.ingested["ltv"]
            elif metric_name in self.derived:
                value = self.derived[metric_name]
            elif metric_name in self.ingested:
                value = self.ingested[metric_name]

            # Compare and determine status
            if value is not None:
                if value < min_val:
                    status = "Offside Low"
                    delta = min_val - value
                elif value > max_val:
                    status = "Offside High"
                    delta = value - max_val
                elif abs(value - pref_val) / max(pref_val, 0.001) < 0.1:
                    status = "OK"
                    delta = 0
                else:
                    status = "Borderline"
                    delta = value - pref_val

                self.bench_compare[metric_name] = {
                    "value": value,
                    "min": min_val,
                    "target": pref_val,
                    "max": max_val,
                    "status": status,
                    "delta": delta,
                    "source": source
                }

    def _compare_benchmarks(self):
        """Compare metrics to industry benchmarks from app + subclass-specific benchmarks"""

        # Check if user has provided benchmark overrides
        has_overrides = hasattr(self, 'benchmark_overrides') and self.benchmark_overrides

        # If overrides exist, use them preferentially
        if has_overrides:
            self._compare_with_overrides()
            return

        # Otherwise use standard benchmarks
        # Get main app benchmarks for primary metrics
        try:
            from app import BENCHMARKS, evaluate_against_benchmarks
            app_benchmarks_available = True
        except ImportError:
            app_benchmarks_available = False
            # Fallback benchmarks if app import fails
            DEFAULT_BENCHMARKS = {
                "multifamily": {
                    "cap_rate": {"min": 0.045, "target": 0.055, "max": 0.07},
                    "dscr": {"min": 1.20, "target": 1.35, "max": 1.50},
                    "ltv": {"min": 0.60, "target": 0.70, "max": 0.75}
                },
                "office": {
                    "cap_rate": {"min": 0.055, "target": 0.065, "max": 0.08},
                    "dscr": {"min": 1.25, "target": 1.40, "max": 1.55},
                    "ltv": {"min": 0.55, "target": 0.65, "max": 0.70}
                },
                "industrial": {
                    "cap_rate": {"min": 0.050, "target": 0.060, "max": 0.075},
                    "dscr": {"min": 1.25, "target": 1.40, "max": 1.55},
                    "ltv": {"min": 0.60, "target": 0.70, "max": 0.75}
                },
                "retail": {
                    "cap_rate": {"min": 0.060, "target": 0.070, "max": 0.085},
                    "dscr": {"min": 1.30, "target": 1.45, "max": 1.60},
                    "ltv": {"min": 0.55, "target": 0.65, "max": 0.70}
                },
                "hospitality": {
                    "cap_rate": {"min": 0.070, "target": 0.080, "max": 0.095},
                    "dscr": {"min": 1.35, "target": 1.50, "max": 1.65},
                    "ltv": {"min": 0.50, "target": 0.60, "max": 0.65}
                }
            }

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
        else:
            # Use fallback benchmarks when app import fails
            if self.asset_class in DEFAULT_BENCHMARKS:
                benchmarks = DEFAULT_BENCHMARKS[self.asset_class]

                # Check primary metrics
                for metric_name, targets in benchmarks.items():
                    value = None
                    if metric_name == "cap_rate":
                        if "cap_rate" in self.derived:
                            value = self.derived["cap_rate"]
                        elif "entry_cap" in self.ingested:
                            value = self.ingested["entry_cap"]
                    elif metric_name == "dscr":
                        if "dscr" in self.derived:
                            value = self.derived["dscr"]
                        elif "dscr" in self.ingested:
                            value = self.ingested["dscr"]
                    elif metric_name == "ltv":
                        if "ltv" in self.derived:
                            value = self.derived["ltv"]
                        elif "ltv" in self.ingested:
                            value = self.ingested["ltv"]

                    if value is not None:
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

                        self.bench_compare[metric_name] = {
                            "value": value,
                            "min": min_val,
                            "target": target_val,
                            "max": max_val,
                            "status": status,
                            "delta": delta,
                            "source": "Industry Standards"
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
        """Rank risks with asset-specific quantified mitigations"""

        # Process each offside metric from benchmark comparison
        for metric, comparison in self.bench_compare.items():
            if comparison["status"].startswith("Offside"):

                # Determine base severity
                if metric in ["dscr", "debt_yield", "cap_rate"]:
                    severity = "HIGH"
                elif metric in ["ltv", "expense_ratio", "walt", "occupancy"]:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

                # Build risk record
                risk = {
                    "severity": severity,
                    "metric": metric,
                    "current_value": comparison["value"],
                    "target_value": comparison["target"],
                    "explanation": f"{metric} is {comparison['status']} at {comparison['value']:.2f} vs target {comparison['target']:.2f}",
                    "mitigations": []
                }

                # Asset-specific risk analysis and mitigations
                self._add_asset_specific_mitigations(metric, comparison, risk)

                self.risks_ranked.append(risk)

        # Add validation-based risks
        for warning in self.validation_warnings:
            if warning["severity"] == "HIGH":
                risk = {
                    "severity": "HIGH",
                    "metric": warning["type"],
                    "current_value": warning.get("actual_value", 0),
                    "target_value": warning.get("expected_value", 0),
                    "explanation": warning["message"],
                    "mitigations": [
                        {"action": "Verify and reconcile data sources", "dollar_impact": 0},
                        {"action": "Request updated financials", "dollar_impact": 0}
                    ]
                }
                self.risks_ranked.append(risk)

        # Sort by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        self.risks_ranked.sort(key=lambda x: severity_order.get(x["severity"], 3))

    def _add_asset_specific_mitigations(self, metric: str, comparison: Dict, risk: Dict):
        """Add detailed asset-specific mitigations with quantified impacts"""

        # ============ OFFICE SPECIFIC ============
        if self.asset_class == "office":

            if metric in ["ti_new_psf", "tenant_improvement"] and comparison["status"] == "Offside Low":
                # Calculate TI reserve needed
                sf = self.ingested.get("square_feet", self.ingested.get("gla_sf", 100000))
                walt = self.ingested.get("walt", 3)
                annual_rollover = sf / walt if walt > 0 else sf / 3

                ti_gap = comparison["target"] - comparison["value"]
                annual_ti_shortfall = ti_gap * annual_rollover

                risk["mitigations"].append({
                    "action": f"Establish TI reserve of ${ti_gap:.0f}/SF for {annual_rollover:,.0f} SF turning annually",
                    "dollar_impact": annual_ti_shortfall
                })
                risk["mitigations"].append({
                    "action": f"Budget additional ${annual_ti_shortfall:,.0f}/year for tenant improvements",
                    "dollar_impact": annual_ti_shortfall
                })
                risk["mitigations"].append({
                    "action": "Negotiate tenant-funded improvements or rent abatement instead of TI",
                    "dollar_impact": annual_ti_shortfall * 0.5
                })

            elif metric == "walt" and comparison["value"] < 3:
                # Short WALT risk
                sf = self.ingested.get("square_feet", 100000)
                rent_psf = self.ingested.get("rent_psf", 30)

                risk["mitigations"].append({
                    "action": f"Focus on 5-7 year renewals for {sf*0.3:,.0f} SF expiring in next 24 months",
                    "dollar_impact": sf * 0.3 * rent_psf * 0.05  # 5% rent increase on renewals
                })
                risk["mitigations"].append({
                    "action": "Offer 6 months free rent for 10-year terms",
                    "dollar_impact": -(sf * 0.2 * rent_psf * 0.5)  # Cost of concessions
                })

            elif metric == "parking_ratio" and comparison["status"] == "Offside Low":
                # Parking deficiency
                current_ratio = comparison["value"]
                target_ratio = comparison["target"]
                sf = self.ingested.get("square_feet", 100000)
                spaces_short = (target_ratio - current_ratio) * (sf / 1000)

                risk["mitigations"].append({
                    "action": f"Lease {spaces_short:.0f} offsite spaces at $150/month",
                    "dollar_impact": -(spaces_short * 150 * 12)
                })
                risk["mitigations"].append({
                    "action": "Implement parking management system for 20% efficiency gain",
                    "dollar_impact": 50000  # One-time cost
                })

        # ============ INDUSTRIAL SPECIFIC ============
        elif self.asset_class == "industrial":

            if metric == "clear_height" and comparison["status"] == "Offside Low":
                # Calculate rent discount for low clearance
                current_height = comparison["value"]
                target_height = comparison["target"]
                height_gap = target_height - current_height

                # Industry standard: 2% rent discount per foot below 32'
                if current_height < 32:
                    discount_pct = min((32 - current_height) * 2, 15)  # Cap at 15%
                    annual_rent = self.ingested.get("noi", 1000000) / 0.94  # Approximate gross rent

                    risk["mitigations"].append({
                        "action": f"Accept {discount_pct:.1f}% rent discount for {current_height:.0f}' clear height",
                        "dollar_impact": -(annual_rent * discount_pct / 100)
                    })
                    risk["mitigations"].append({
                        "action": "Target last-mile/urban logistics tenants (lower height requirements)",
                        "dollar_impact": 0
                    })
                    risk["mitigations"].append({
                        "action": f"Feasibility study for raising roof to 32' (~$25/SF)",
                        "dollar_impact": -(self.ingested.get("square_feet", 100000) * 25)
                    })

            elif metric == "dock_doors" and comparison["status"] == "Offside Low":
                # Insufficient loading
                current_doors = comparison["value"]
                target_doors = comparison["target"]
                doors_short = target_doors - current_doors

                risk["mitigations"].append({
                    "action": f"Add {doors_short:.0f} dock doors at $35K each",
                    "dollar_impact": -(doors_short * 35000)
                })
                risk["mitigations"].append({
                    "action": "Install dock scheduling system to optimize throughput",
                    "dollar_impact": -25000
                })

        # ============ RETAIL SPECIFIC ============
        elif self.asset_class == "retail":

            if metric == "anchor_term" and comparison["value"] < 10:
                # Short anchor term risk
                anchor_sf = self.ingested.get("anchor_sf", 50000)
                anchor_rent = self.ingested.get("anchor_rent_psf", 15)
                years_remaining = comparison["value"]

                risk["mitigations"].append({
                    "action": f"Negotiate 10-year extension with anchor (expires in {years_remaining:.1f} years)",
                    "dollar_impact": 0  # No immediate cost
                })
                risk["mitigations"].append({
                    "action": "Secure ROFR (Right of First Refusal) on anchor space",
                    "dollar_impact": -10000  # Legal costs
                })
                risk["mitigations"].append({
                    "action": f"Obtain backfill LOIs for {anchor_sf:,.0f} SF anchor space",
                    "dollar_impact": anchor_sf * (anchor_rent - 12) * 0.5  # Potential rent loss
                })
                risk["mitigations"].append({
                    "action": "Model 15% co-tenancy rent reduction impact",
                    "dollar_impact": -(self.ingested.get("noi", 1000000) * 0.15)
                })

            elif metric == "sales_psf" and comparison["status"] == "Offside Low":
                # Low tenant sales
                current_sales = comparison["value"]
                target_sales = comparison["target"]
                total_sf = self.ingested.get("square_feet", 100000)

                risk["mitigations"].append({
                    "action": f"Remix tenant base - target ${target_sales:.0f}/SF operators",
                    "dollar_impact": (target_sales - current_sales) * total_sf * 0.06  # 6% rent-to-sales
                })
                risk["mitigations"].append({
                    "action": "Marketing fund increase $2/SF to drive traffic",
                    "dollar_impact": -(total_sf * 2)
                })

        # ============ HOTEL/HOSPITALITY SPECIFIC ============
        elif self.asset_class in ["hospitality", "hotel"]:

            if metric == "gop_margin" and comparison["status"] == "Offside Low":
                # Low GOP margin suggests exit cap widening
                current_margin = comparison["value"]
                target_margin = comparison["target"]
                margin_gap = target_margin - current_margin

                # Each 1% GOP margin miss = ~10bps exit cap widening
                cap_widening_bps = margin_gap * 1000  # Convert to percentage points then to bps

                exit_value = self.derived.get("exit_value", 10000000)
                value_impact = exit_value * (cap_widening_bps / 10000)

                risk["mitigations"].append({
                    "action": f"Model exit cap widening by {cap_widening_bps:.0f}bps due to GOP margin",
                    "dollar_impact": -value_impact
                })
                risk["mitigations"].append({
                    "action": "Implement revenue management system for 3% RevPAR lift",
                    "dollar_impact": self.ingested.get("noi", 1000000) * 0.03
                })
                risk["mitigations"].append({
                    "action": "Renegotiate management agreement - reduce base fee by 0.5%",
                    "dollar_impact": self.ingested.get("revenue", 5000000) * 0.005
                })

            elif metric == "revpar" and comparison["status"] == "Offside Low":
                # Low RevPAR
                keys = self.ingested.get("keys", 150)
                current_revpar = comparison["value"]
                target_revpar = comparison["target"]
                revpar_gap = target_revpar - current_revpar

                annual_revenue_gap = revpar_gap * keys * 365

                risk["mitigations"].append({
                    "action": f"Revenue gap of ${revpar_gap:.0f}/day across {keys} keys",
                    "dollar_impact": -annual_revenue_gap
                })
                risk["mitigations"].append({
                    "action": f"PIP investment $15K/key to reach comp set RevPAR",
                    "dollar_impact": -(keys * 15000)
                })

        # ============ MULTIFAMILY SPECIFIC ============
        elif self.asset_class == "multifamily":

            if metric == "expense_ratio" and comparison["status"] == "Offside High":
                # High expense ratio
                current_ratio = comparison["value"]
                target_ratio = comparison["target"]
                revenue = self.ingested.get("effective_gross_income", self.ingested.get("noi", 1000000) / 0.6)

                expense_reduction = (current_ratio - target_ratio) * revenue

                risk["mitigations"].append({
                    "action": f"Reduce operating expenses by ${expense_reduction:,.0f}/year to reach {target_ratio*100:.0f}%",
                    "dollar_impact": expense_reduction
                })
                risk["mitigations"].append({
                    "action": "RUBS implementation for utilities ($30/unit/month)",
                    "dollar_impact": self.ingested.get("units", 100) * 30 * 12
                })
                risk["mitigations"].append({
                    "action": "Self-manage to save 3% management fee",
                    "dollar_impact": revenue * 0.03
                })

            elif metric == "occupancy" and comparison["status"] == "Offside Low":
                # Low occupancy
                current_occ = comparison["value"]
                target_occ = comparison["target"]
                units = self.ingested.get("units", 100)
                avg_rent = self.ingested.get("avg_rent", 1500)

                units_to_lease = (target_occ - current_occ) * units
                revenue_gain = units_to_lease * avg_rent * 12

                risk["mitigations"].append({
                    "action": f"Lease-up {units_to_lease:.0f} units to reach {target_occ*100:.0f}% occupancy",
                    "dollar_impact": revenue_gain
                })
                risk["mitigations"].append({
                    "action": "Offer 1-month concession for immediate occupancy",
                    "dollar_impact": -(units_to_lease * avg_rent)
                })

        # ============ COMMON FINANCIAL RISKS ============

        if metric == "dscr" and comparison["status"] == "Offside Low":
            # DSCR below threshold
            target_dscr = comparison["target"]
            current_noi = self.ingested.get("noi_now", self.ingested.get("noi", 0))
            current_ads = self.derived.get("ads_calculated", self.derived.get("ads", 0))

            if current_ads > 0:
                required_ads = current_noi / target_dscr
                ads_reduction = current_ads - required_ads

                # Calculate loan reduction needed
                if "interest_rate" in self.ingested or "rate" in self.ingested:
                    rate = self.ingested.get("interest_rate", self.ingested.get("rate", 0.06))
                    loan_reduction = ads_reduction / rate if rate > 0 else 0

                    risk["mitigations"].append({
                        "action": f"Reduce loan amount by ${loan_reduction:,.0f} to achieve {target_dscr:.2f}x DSCR",
                        "dollar_impact": ads_reduction  # Annual cash flow improvement
                    })

                # Or increase NOI
                noi_increase = (target_dscr * current_ads) - current_noi
                risk["mitigations"].append({
                    "action": f"Increase NOI by ${noi_increase:,.0f} ({(noi_increase/current_noi)*100:.1f}% growth)",
                    "dollar_impact": noi_increase
                })

        elif metric == "ltv" and comparison["status"] == "Offside High":
            # LTV too high
            target_ltv = comparison["target"]
            price = self.ingested.get("purchase_price", 0)
            max_loan = price * target_ltv
            current_loan = self.ingested.get("loan_amount", 0)
            loan_reduction = current_loan - max_loan

            risk["mitigations"].append({
                "action": f"Reduce loan by ${loan_reduction:,.0f} to reach {target_ltv*100:.0f}% LTV",
                "dollar_impact": loan_reduction * self.ingested.get("interest_rate", 0.06)  # Interest savings
            })
            risk["mitigations"].append({
                "action": f"Increase equity contribution by ${loan_reduction:,.0f}",
                "dollar_impact": 0
            })

    def _compute_sensitivities(self):
        """Compute sensitivity analysis"""

        # Exit Cap Sensitivity
        if all(k in self.ingested for k in ["exit_cap", "noi_now"]):
            # Handle exit_cap as either decimal (0.065) or percentage (6.5)
            base_exit_cap = self.ingested["exit_cap"] if self.ingested["exit_cap"] < 1 else self.ingested["exit_cap"] / 100

            if base_exit_cap > 0:  # Avoid division by zero
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
        """Identify what we know and what we don't with structured explanations"""

        # Known items with confidence
        for field, value in self.ingested.items():
            confidence = self.confidence.get(field, "Low")

            # Format value for display
            if isinstance(value, str):
                formatted = value
            elif field.endswith("_pct") or field.endswith("_rate"):
                formatted = f"{value:.2%}"
            elif isinstance(value, (int, float)) and value > 1000:
                formatted = f"${value:,.0f}"
            elif isinstance(value, (int, float)):
                formatted = f"{value:.3f}"
            else:
                formatted = str(value)

            self.known.append(f"{field}: {formatted} ({confidence} confidence)")

        for metric, value in self.derived.items():
            if not metric.endswith("_calc"):
                # Handle string values
                if isinstance(value, str):
                    formatted = value
                elif metric in ["cap_rate", "yield_on_cost", "debt_yield", "dscr"]:
                    formatted = f"{value:.3f}"
                elif metric in ["exit_value", "net_sale_proceeds", "refi_proceeds"]:
                    formatted = f"${value:,.0f}"
                else:
                    formatted = f"{value:.3f}"

                self.known.append(f"{metric}: {formatted} (Calculated)")

        # Check for uncalculated metrics using METRIC_DEPENDENCIES
        for metric_name, dependency_info in METRIC_DEPENDENCIES.items():
            # Check if this metric could be calculated but wasn't
            if metric_name not in self.derived:
                required_fields = dependency_info["required"]
                explanation = dependency_info["explanation"]

                # Find which fields are missing
                missing_fields = []
                available_fields = list(self.ingested.keys()) + list(self.derived.keys())

                for field in required_fields:
                    # Handle field variations (e.g., interest_rate vs rate)
                    field_found = False
                    if field in available_fields:
                        field_found = True
                    elif field == "interest_rate" and "rate" in available_fields:
                        field_found = True
                    elif field == "rate" and "interest_rate" in available_fields:
                        field_found = True

                    if not field_found:
                        missing_fields.append(field)

                # If any required fields are missing, add to unknown with structured format
                if missing_fields:
                    self.unknown.append({
                        "metric": metric_name,
                        "missing": missing_fields,
                        "because": explanation
                    })

        # Check for required fields for this asset subclass
        required = REQUIRED_FIELDS.get(self.subclass, []) + REQUIRED_FIELDS["_common"]

        for field in required:
            if field not in self.ingested:
                # Special handling for important fields
                field_descriptions = {
                    "walt_years": "Weighted average lease term from rent roll - critical for office/retail valuation",
                    "ti_new_psf": "Tenant improvement allowance for new leases - impacts cash flow projections",
                    "clear_height_ft": "Clear height in feet - critical for industrial tenant marketability",
                    "anchor_remaining_term_years": "Anchor tenant's remaining lease term - co-tenancy risk factor",
                    "expense_ratio": "Operating expense ratio - percentage of gross income",
                    "replacement_reserves": "Annual capital reserves per unit - typically $250-500/unit for multifamily",
                    "pip_cost_per_key": "Property Improvement Plan cost per key - brand compliance for hotels",
                    "gop_margin_pct": "Gross operating profit margin - key hotel profitability metric",
                    "adr": "Average daily rate - fundamental hotel revenue metric",
                    "revpar": "Revenue per available room - hotel performance indicator"
                }

                # Add missing field with context
                if field not in [item.get("metric") for item in self.unknown]:
                    self.unknown.append({
                        "metric": field,
                        "missing": [],  # This is a primary field, not derived
                        "because": field_descriptions.get(field, f"Required for {self.subclass} analysis")
                    })

        # Special checks for complex metrics that need multiple derived values
        # IRR needs full cash flow series
        if "irr" not in self.derived:
            irr_missing = []
            if "purchase_price" not in self.ingested:
                irr_missing.append("purchase_price")
            if "loan_amount" not in self.ingested:
                irr_missing.append("loan_amount")
            if "noi_now" not in self.ingested:
                irr_missing.append("noi_now")
            if "exit_value" not in self.derived and "exit_cap" not in self.ingested:
                irr_missing.append("exit_cap")
            if "hold_years" not in self.ingested:
                irr_missing.append("hold_period")

            if irr_missing and "irr" not in [item.get("metric") for item in self.unknown]:
                self.unknown.append({
                    "metric": "irr",
                    "missing": irr_missing,
                    "because": "IRR requires complete cash flow projections from entry through exit"
                })

        # Equity Multiple needs total distributions
        if "equity_multiple" not in self.derived:
            em_missing = []
            equity = (self.ingested.get("purchase_price", 0) - self.ingested.get("loan_amount", 0))
            if equity <= 0:
                em_missing.append("initial_equity")
            if "net_sale_proceeds" not in self.derived:
                em_missing.append("exit_proceeds")

            if em_missing and "equity_multiple" not in [item.get("metric") for item in self.unknown]:
                self.unknown.append({
                    "metric": "equity_multiple",
                    "missing": em_missing,
                    "because": "Equity multiple requires initial equity investment and total proceeds"
                })

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
                        benchmark_library: Dict = None, ocr_blocks: List[Dict] = None,
                        benchmark_overrides: Dict = None) -> Dict:
    """
    Main public function to extract and analyze CRE deal data

    Args:
        asset_class: Main asset class (e.g., 'office', 'multifamily', 'industrial')
        subclass: Specific subclass (e.g., 'cbd_A_trophy', 'garden_lowrise')
        raw_text: Raw text from OCR or document
        benchmark_library: Optional external benchmark data to use
        ocr_blocks: Optional OCR block data with bounding boxes for table detection
        benchmark_overrides: Optional user-defined benchmark overrides

    Returns:
        Dictionary with comprehensive analysis results:
        - ingested: Raw extracted fields with confidence scores
        - derived: Calculated metrics
        - bench_compare: Benchmark comparisons
        - risks_ranked: Risk assessment with mitigations
        - known: List of known facts
        - unknown: List of missing critical data
        - completeness: Data completeness metrics
        - field_confidence: Detailed confidence tracking for each field
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

        # Apply user-defined benchmark overrides if provided
        if benchmark_overrides:
            engine.benchmark_overrides = benchmark_overrides

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