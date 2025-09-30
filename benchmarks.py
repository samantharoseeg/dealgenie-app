"""
Comprehensive CRE Benchmarks Module
Complete implementation per Document 13 specifications
Includes all asset classes, subclasses, metrics catalog, and helper functions
"""

from typing import Dict, List, Optional, Tuple, Any

# SECTION 1: METRICS CATALOG
# Complete dictionary of all CRE metrics with descriptions and importance
METRICS_CATALOG = {
    # Core Financial Metrics
    "cap_rate": {
        "unit": "%",
        "description": "Net Operating Income divided by Purchase Price",
        "why_it_matters": "Primary valuation metric showing annual return on investment before debt. Higher cap rates indicate higher risk/return profiles."
    },
    "dscr": {
        "unit": "x",
        "description": "Net Operating Income divided by Annual Debt Service",
        "why_it_matters": "Measures ability to cover debt payments. Lenders typically require 1.25x minimum for loan approval."
    },
    "ltv": {
        "unit": "%",
        "description": "Loan Amount divided by Property Value",
        "why_it_matters": "Leverage ratio showing loan exposure. Lower LTV means more equity cushion and lower default risk."
    },
    "equity_multiple": {
        "unit": "x",
        "description": "Total distributions divided by initial equity investment",
        "why_it_matters": "Shows total return multiple over hold period. 2.0x means doubling your money."
    },
    "irr": {
        "unit": "%",
        "description": "Internal Rate of Return accounting for timing of cash flows",
        "why_it_matters": "Time-weighted return metric. Accounts for when you receive distributions, not just how much."
    },
    "cash_on_cash": {
        "unit": "%",
        "description": "Annual cash flow after debt service divided by initial equity",
        "why_it_matters": "Current yield on invested equity. Shows immediate cash returns before sale."
    },
    "exit_cap": {
        "unit": "%",
        "description": "Assumed cap rate at sale",
        "why_it_matters": "Critical assumption for exit value. 50bps change can swing returns by 20%+."
    },
    "noi_growth": {
        "unit": "%",
        "description": "Annual growth rate of Net Operating Income",
        "why_it_matters": "Revenue growth driver. Directly impacts exit value and refinancing proceeds."
    },
    "expense_ratio": {
        "unit": "%",
        "description": "Operating expenses divided by effective gross income",
        "why_it_matters": "Operational efficiency metric. Lower ratios indicate better management and margins."
    },

    # Asset-Specific Metrics
    "occupancy": {
        "unit": "%",
        "description": "Percentage of space currently leased and occupied",
        "why_it_matters": "Revenue stability indicator. Physical occupancy drives actual cash flow."
    },
    "walt": {
        "unit": "years",
        "description": "Weighted Average Lease Term remaining",
        "why_it_matters": "Income duration metric. Longer WALT means more predictable cash flows."
    },
    "rent_psf": {
        "unit": "$/sf/yr",
        "description": "Annual rent per square foot",
        "why_it_matters": "Market positioning indicator. Compare to submarket averages for value-add potential."
    },
    "price_per_unit": {
        "unit": "$/unit",
        "description": "Purchase price divided by number of units",
        "why_it_matters": "Multifamily valuation metric. Key comp for market pricing."
    },
    "price_psf": {
        "unit": "$/sf",
        "description": "Purchase price per square foot",
        "why_it_matters": "Universal comparison metric across property types and markets."
    },
    "revpar": {
        "unit": "$",
        "description": "Revenue Per Available Room (ADR × Occupancy)",
        "why_it_matters": "Hotel performance benchmark combining rate and occupancy."
    },
    "adr": {
        "unit": "$",
        "description": "Average Daily Rate for hotel rooms",
        "why_it_matters": "Pricing power indicator. Shows competitive position in market."
    },
    "gop_margin": {
        "unit": "%",
        "description": "Gross Operating Profit margin for hotels",
        "why_it_matters": "Operational efficiency before fixed costs. Industry standard for hotel performance."
    },
    "sales_psf": {
        "unit": "$/sf/yr",
        "description": "Tenant sales per square foot (retail)",
        "why_it_matters": "Tenant health indicator. Higher sales support rent increases and renewals."
    },
    "rent_to_sales": {
        "unit": "%",
        "description": "Rent as percentage of tenant sales",
        "why_it_matters": "Affordability metric. Above 10% signals potential tenant distress."
    },
    "parking_ratio": {
        "unit": "spaces/1000sf",
        "description": "Parking spaces per 1,000 square feet",
        "why_it_matters": "Accessibility and convenience factor. Critical for suburban office and retail."
    },
    "clear_height": {
        "unit": "ft",
        "description": "Clear height in industrial buildings",
        "why_it_matters": "Modern logistics require 32'+ for efficient racking systems."
    },
    "power_density": {
        "unit": "W/sf",
        "description": "Power capacity per square foot (data centers)",
        "why_it_matters": "Revenue potential driver. Higher density commands premium rents."
    },
    "pue": {
        "unit": "ratio",
        "description": "Power Usage Effectiveness (data centers)",
        "why_it_matters": "Energy efficiency metric. Lower is better, <1.5 is excellent."
    },
    "renewal_probability": {
        "unit": "%",
        "description": "Likelihood of tenant renewal",
        "why_it_matters": "Future vacancy risk indicator. Impacts underwriting and valuations."
    },
    "tenant_improvement": {
        "unit": "$/sf",
        "description": "TI allowance for new/renewal leases",
        "why_it_matters": "Capital requirement for leasing. Major impact on net effective rents."
    },
    "leasing_commission": {
        "unit": "%",
        "description": "Commission as percentage of lease value",
        "why_it_matters": "Transaction cost impacting net proceeds. Budget 4-6% for new leases."
    },
    "replacement_reserves": {
        "unit": "$/unit/yr",
        "description": "Annual capital reserve for replacements",
        "why_it_matters": "Long-term capital planning. Lenders often require reserves."
    }
}

# SECTION 2: COMPREHENSIVE BENCHMARKS STRUCTURE
# Nested dictionary: asset_class -> subclass -> metric -> [min, preferred, max, source]
BENCHMARKS = {
    # MULTIFAMILY BENCHMARKS
    "multifamily": {
        "garden_lowrise": {
            "cap_rate": [4.5, 5.5, 7.0, "RCA Analytics Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [92, 95, 98, "NMHC Market Report Q4 2024"],
            "expense_ratio": [35, 40, 45, "IREM Benchmark 2024"],
            "price_per_unit": [100000, 150000, 250000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.0, 3.5, 5.0, "JLL Research Q4 2024"],
            "replacement_reserves": [250, 350, 500, "Fannie Mae Guidelines 2024"]
        },
        "midrise": {
            "cap_rate": [4.0, 5.0, 6.5, "RCA Analytics Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [93, 96, 98, "NMHC Market Report Q4 2024"],
            "expense_ratio": [30, 35, 40, "IREM Benchmark 2024"],
            "price_per_unit": [150000, 225000, 350000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.5, 4.0, 5.5, "JLL Research Q4 2024"],
            "replacement_reserves": [300, 400, 550, "Fannie Mae Guidelines 2024"]
        },
        "highrise": {
            "cap_rate": [3.5, 4.5, 6.0, "RCA Analytics Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [94, 96, 98, "NMHC Market Report Q4 2024"],
            "expense_ratio": [28, 33, 38, "IREM Benchmark 2024"],
            "price_per_unit": [250000, 400000, 600000, "RCA Analytics Q4 2024"],
            "noi_growth": [3.0, 4.5, 6.0, "JLL Research Q4 2024"],
            "replacement_reserves": [400, 500, 650, "Fannie Mae Guidelines 2024"]
        },
        "student_housing": {
            "cap_rate": [5.0, 6.0, 7.5, "RCA Analytics Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "Axiometrics Student Housing 2024"],
            "expense_ratio": [40, 45, 52, "IREM Benchmark 2024"],
            "price_per_unit": [40000, 60000, 85000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.0, 3.0, 4.5, "JLL Student Housing 2024"],
            "replacement_reserves": [200, 300, 400, "Fannie Mae Guidelines 2024"]
        },
        "senior_IL": {
            "cap_rate": [5.5, 6.5, 8.0, "NIC MAP Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "NIC MAP Q4 2024"],
            "expense_ratio": [45, 50, 55, "ASHA Benchmark 2024"],
            "price_per_unit": [125000, 175000, 250000, "NIC Investment Guide 2024"],
            "noi_growth": [2.5, 3.5, 5.0, "JLL Seniors Housing 2024"],
            "replacement_reserves": [350, 450, 600, "HUD Guidelines 2024"]
        },
        "senior_AL": {
            "cap_rate": [6.0, 7.0, 8.5, "NIC MAP Q4 2024"],
            "dscr": [1.15, 1.25, 1.40, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "NIC MAP Q4 2024"],
            "expense_ratio": [55, 60, 65, "ASHA Benchmark 2024"],
            "price_per_unit": [150000, 225000, 325000, "NIC Investment Guide 2024"],
            "noi_growth": [3.0, 4.0, 5.5, "JLL Seniors Housing 2024"],
            "replacement_reserves": [400, 500, 650, "HUD Guidelines 2024"]
        },
        "senior_MemoryCare": {
            "cap_rate": [6.5, 7.5, 9.0, "NIC MAP Q4 2024"],
            "dscr": [1.15, 1.25, 1.35, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [82, 88, 92, "NIC MAP Q4 2024"],
            "expense_ratio": [60, 65, 70, "ASHA Benchmark 2024"],
            "price_per_unit": [175000, 250000, 350000, "NIC Investment Guide 2024"],
            "noi_growth": [3.0, 4.5, 6.0, "JLL Seniors Housing 2024"],
            "replacement_reserves": [450, 550, 700, "HUD Guidelines 2024"]
        }
    },

    # OFFICE BENCHMARKS
    "office": {
        "cbd_A_trophy": {
            "cap_rate": [3.5, 4.5, 5.5, "CBRE EA Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Survey Q4 2024"],
            "occupancy": [90, 93, 96, "JLL Office Insight Q4 2024"],
            "walt": [5.0, 7.0, 10.0, "CBRE Research Q4 2024"],
            "expense_ratio": [35, 40, 45, "BOMA Experience Report 2024"],
            "price_psf": [400, 600, 900, "RCA Analytics Q4 2024"],
            "tenant_improvement": [50, 75, 100, "JLL Construction Cost Guide 2024"],
            "parking_ratio": [2.0, 2.5, 3.5, "ULI Parking Standards 2024"]
        },
        "cbd_BC": {
            "cap_rate": [5.0, 6.0, 7.5, "CBRE EA Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "JLL Office Insight Q4 2024"],
            "walt": [3.0, 5.0, 7.0, "CBRE Research Q4 2024"],
            "expense_ratio": [38, 43, 48, "BOMA Experience Report 2024"],
            "price_psf": [200, 350, 500, "RCA Analytics Q4 2024"],
            "tenant_improvement": [35, 50, 75, "JLL Construction Cost Guide 2024"],
            "parking_ratio": [1.5, 2.0, 3.0, "ULI Parking Standards 2024"]
        },
        "suburban": {
            "cap_rate": [5.5, 6.5, 8.0, "CBRE EA Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [83, 88, 92, "JLL Office Insight Q4 2024"],
            "walt": [2.5, 4.0, 6.0, "CBRE Research Q4 2024"],
            "expense_ratio": [40, 45, 50, "BOMA Experience Report 2024"],
            "price_psf": [100, 200, 350, "RCA Analytics Q4 2024"],
            "tenant_improvement": [25, 40, 60, "JLL Construction Cost Guide 2024"],
            "parking_ratio": [3.0, 4.0, 5.0, "ULI Parking Standards 2024"]
        },
        "medical_office": {
            "cap_rate": [5.0, 6.0, 7.0, "CBRE Healthcare Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "Revista MOB Report Q4 2024"],
            "walt": [4.0, 6.0, 8.0, "CBRE Healthcare Q4 2024"],
            "expense_ratio": [42, 47, 52, "BOMA Healthcare 2024"],
            "price_psf": [250, 350, 500, "RCA Analytics Q4 2024"],
            "tenant_improvement": [40, 60, 85, "JLL Healthcare Construction 2024"],
            "parking_ratio": [4.0, 5.0, 6.5, "ULI Healthcare Standards 2024"]
        },
        "flex_creative": {
            "cap_rate": [6.0, 7.0, 8.5, "CBRE EA Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [80, 87, 92, "JLL Flex Space Report Q4 2024"],
            "walt": [2.0, 3.5, 5.0, "CBRE Research Q4 2024"],
            "expense_ratio": [35, 40, 45, "BOMA Experience Report 2024"],
            "price_psf": [75, 150, 250, "RCA Analytics Q4 2024"],
            "tenant_improvement": [15, 30, 45, "JLL Construction Cost Guide 2024"],
            "parking_ratio": [2.5, 3.5, 4.5, "ULI Parking Standards 2024"]
        }
    },

    # INDUSTRIAL BENCHMARKS
    "industrial": {
        "bulk_distribution": {
            "cap_rate": [4.0, 5.0, 6.0, "CBRE Industrial Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [92, 95, 98, "JLL Industrial Insight Q4 2024"],
            "walt": [4.0, 6.0, 8.0, "CBRE Research Q4 2024"],
            "price_psf": [60, 85, 120, "RCA Analytics Q4 2024"],
            "clear_height": [32, 36, 40, "NAIOP Industrial Standards 2024"],
            "expense_ratio": [15, 20, 25, "IREM Industrial Benchmark 2024"],
            "parking_ratio": [0.5, 1.0, 1.5, "ULI Industrial Standards 2024"]
        },
        "light_industrial_flex": {
            "cap_rate": [5.0, 6.0, 7.5, "CBRE Industrial Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "JLL Industrial Insight Q4 2024"],
            "walt": [2.5, 4.0, 6.0, "CBRE Research Q4 2024"],
            "price_psf": [75, 125, 175, "RCA Analytics Q4 2024"],
            "clear_height": [18, 24, 28, "NAIOP Industrial Standards 2024"],
            "expense_ratio": [18, 23, 28, "IREM Industrial Benchmark 2024"],
            "parking_ratio": [1.5, 2.5, 3.5, "ULI Industrial Standards 2024"]
        },
        "last_mile": {
            "cap_rate": [3.5, 4.5, 5.5, "CBRE Last Mile Report Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [94, 97, 99, "JLL Last Mile Insight Q4 2024"],
            "walt": [5.0, 7.0, 10.0, "CBRE Research Q4 2024"],
            "price_psf": [150, 250, 400, "RCA Analytics Q4 2024"],
            "clear_height": [24, 28, 32, "NAIOP Industrial Standards 2024"],
            "expense_ratio": [12, 17, 22, "IREM Industrial Benchmark 2024"],
            "parking_ratio": [1.0, 2.0, 3.0, "ULI Industrial Standards 2024"]
        },
        "cold_storage": {
            "cap_rate": [5.5, 6.5, 8.0, "CBRE Cold Storage Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "IARW Market Report Q4 2024"],
            "walt": [5.0, 7.0, 10.0, "CBRE Research Q4 2024"],
            "price_psf": [100, 175, 275, "RCA Analytics Q4 2024"],
            "clear_height": [30, 35, 40, "IARW Standards 2024"],
            "expense_ratio": [20, 25, 30, "IARW Benchmark 2024"],
            "power_density": [15, 25, 35, "IARW Energy Standards 2024"]
        },
        "manufacturing": {
            "cap_rate": [6.0, 7.0, 8.5, "CBRE Industrial Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "NAM Manufacturing Report Q4 2024"],
            "walt": [3.0, 5.0, 7.0, "CBRE Research Q4 2024"],
            "price_psf": [40, 75, 125, "RCA Analytics Q4 2024"],
            "clear_height": [20, 28, 35, "NAIOP Industrial Standards 2024"],
            "expense_ratio": [22, 28, 34, "IREM Industrial Benchmark 2024"],
            "power_density": [10, 20, 30, "NAM Energy Standards 2024"]
        }
    },

    # RETAIL BENCHMARKS
    "retail": {
        "grocery_anchored": {
            "cap_rate": [5.0, 6.0, 7.0, "CBRE Retail Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [92, 95, 98, "JLL Retail Insight Q4 2024"],
            "walt": [4.0, 6.0, 8.0, "CBRE Research Q4 2024"],
            "price_psf": [150, 225, 350, "RCA Analytics Q4 2024"],
            "sales_psf": [350, 450, 600, "ICSC Benchmark Q4 2024"],
            "rent_to_sales": [3.0, 4.5, 6.0, "ICSC Benchmark Q4 2024"],
            "parking_ratio": [4.0, 5.0, 6.5, "ULI Retail Standards 2024"]
        },
        "power_center": {
            "cap_rate": [5.5, 6.5, 8.0, "CBRE Retail Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 93, 96, "JLL Retail Insight Q4 2024"],
            "walt": [3.0, 5.0, 7.0, "CBRE Research Q4 2024"],
            "price_psf": [75, 125, 200, "RCA Analytics Q4 2024"],
            "sales_psf": [250, 350, 450, "ICSC Benchmark Q4 2024"],
            "rent_to_sales": [4.0, 6.0, 8.0, "ICSC Benchmark Q4 2024"],
            "parking_ratio": [4.5, 5.5, 7.0, "ULI Retail Standards 2024"]
        },
        "lifestyle_open_air": {
            "cap_rate": [4.5, 5.5, 7.0, "CBRE Retail Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "JLL Retail Insight Q4 2024"],
            "walt": [3.5, 5.5, 7.5, "CBRE Research Q4 2024"],
            "price_psf": [200, 350, 550, "RCA Analytics Q4 2024"],
            "sales_psf": [400, 550, 750, "ICSC Benchmark Q4 2024"],
            "rent_to_sales": [5.0, 7.0, 9.0, "ICSC Benchmark Q4 2024"],
            "parking_ratio": [3.5, 4.5, 6.0, "ULI Retail Standards 2024"]
        },
        "mall_regional": {
            "cap_rate": [6.0, 7.5, 9.5, "Green Street Mall Report Q4 2024"],
            "dscr": [1.15, 1.25, 1.40, "MBA Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Survey Q4 2024"],
            "occupancy": [80, 87, 92, "Green Street Mall Report Q4 2024"],
            "walt": [2.0, 3.5, 5.0, "CBRE Research Q4 2024"],
            "price_psf": [50, 125, 250, "RCA Analytics Q4 2024"],
            "sales_psf": [300, 425, 575, "ICSC Benchmark Q4 2024"],
            "rent_to_sales": [8.0, 11.0, 14.0, "ICSC Benchmark Q4 2024"],
            "parking_ratio": [4.0, 5.0, 6.5, "ULI Retail Standards 2024"]
        },
        "single_tenant_nnn": {
            "cap_rate": [4.5, 5.5, 7.0, "Boulder Group Net Lease Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [100, 100, 100, "Net Lease Market Report Q4 2024"],
            "walt": [7.0, 10.0, 15.0, "Boulder Group Research Q4 2024"],
            "price_psf": [150, 275, 450, "RCA Analytics Q4 2024"],
            "renewal_probability": [70, 80, 90, "Boulder Group Research Q4 2024"],
            "rent_to_sales": [4.0, 6.0, 8.0, "ICSC Benchmark Q4 2024"],
            "expense_ratio": [0, 5, 10, "IREM Net Lease Benchmark 2024"]
        }
    },

    # HOSPITALITY BENCHMARKS
    "hospitality": {
        "full_service": {
            "cap_rate": [6.0, 7.5, 9.0, "HVS Hotel Valuation Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Hospitality Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [65, 72, 78, "STR US Hotel Review Q4 2024"],
            "adr": [150, 200, 275, "STR US Hotel Review Q4 2024"],
            "revpar": [95, 145, 215, "STR US Hotel Review Q4 2024"],
            "gop_margin": [28, 35, 42, "CBRE Hotels Americas Q4 2024"],
            "expense_ratio": [70, 75, 80, "CBRE Hotels Benchmark 2024"],
            "price_per_unit": [125000, 200000, 350000, "HVS Hotel Valuation Q4 2024"]
        },
        "limited_service": {
            "cap_rate": [6.5, 8.0, 9.5, "HVS Hotel Valuation Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Hospitality Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [60, 68, 75, "STR US Hotel Review Q4 2024"],
            "adr": [85, 110, 145, "STR US Hotel Review Q4 2024"],
            "revpar": [50, 75, 110, "STR US Hotel Review Q4 2024"],
            "gop_margin": [32, 38, 45, "CBRE Hotels Americas Q4 2024"],
            "expense_ratio": [62, 68, 74, "CBRE Hotels Benchmark 2024"],
            "price_per_unit": [60000, 90000, 130000, "HVS Hotel Valuation Q4 2024"]
        },
        "extended_stay": {
            "cap_rate": [6.0, 7.0, 8.5, "HVS Hotel Valuation Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Hospitality Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [72, 78, 84, "STR Extended Stay Report Q4 2024"],
            "adr": [75, 95, 120, "STR Extended Stay Report Q4 2024"],
            "revpar": [55, 75, 100, "STR Extended Stay Report Q4 2024"],
            "gop_margin": [35, 42, 48, "CBRE Hotels Americas Q4 2024"],
            "expense_ratio": [58, 64, 70, "CBRE Hotels Benchmark 2024"],
            "price_per_unit": [70000, 100000, 140000, "HVS Hotel Valuation Q4 2024"]
        },
        "resort": {
            "cap_rate": [5.5, 7.0, 8.5, "HVS Resort Valuation Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Hospitality Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [62, 70, 77, "STR Resort Report Q4 2024"],
            "adr": [250, 400, 650, "STR Resort Report Q4 2024"],
            "revpar": [155, 280, 500, "STR Resort Report Q4 2024"],
            "gop_margin": [25, 32, 40, "CBRE Resort Americas Q4 2024"],
            "expense_ratio": [72, 78, 84, "CBRE Resort Benchmark 2024"],
            "price_per_unit": [200000, 400000, 750000, "HVS Resort Valuation Q4 2024"]
        },
        "boutique_lifestyle": {
            "cap_rate": [5.0, 6.5, 8.0, "HVS Boutique Hotel Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Hospitality Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [68, 75, 82, "STR Boutique Report Q4 2024"],
            "adr": [175, 275, 425, "STR Boutique Report Q4 2024"],
            "revpar": [120, 205, 350, "STR Boutique Report Q4 2024"],
            "gop_margin": [26, 33, 40, "CBRE Boutique Hotels Q4 2024"],
            "expense_ratio": [72, 77, 82, "CBRE Boutique Benchmark 2024"],
            "price_per_unit": [150000, 300000, 550000, "HVS Boutique Valuation Q4 2024"]
        },
        "luxury": {
            "cap_rate": [4.0, 5.5, 7.0, "HVS Luxury Hotel Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Hospitality Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Hospitality Survey Q4 2024"],
            "occupancy": [65, 72, 78, "STR Luxury Report Q4 2024"],
            "adr": [400, 650, 1000, "STR Luxury Report Q4 2024"],
            "revpar": [260, 470, 780, "STR Luxury Report Q4 2024"],
            "gop_margin": [22, 30, 38, "CBRE Luxury Hotels Q4 2024"],
            "expense_ratio": [75, 80, 85, "CBRE Luxury Benchmark 2024"],
            "price_per_unit": [400000, 750000, 1500000, "HVS Luxury Valuation Q4 2024"]
        }
    },

    # SPECIALTY ASSET BENCHMARKS
    "self_storage": {
        "climate_controlled": {
            "cap_rate": [5.0, 6.0, 7.5, "Marcus & Millichap Self Storage Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "SSA Quarterly Report Q4 2024"],
            "price_psf": [100, 150, 225, "RCA Analytics Q4 2024"],
            "expense_ratio": [30, 35, 40, "SSA Benchmark Report 2024"],
            "noi_growth": [3.0, 4.5, 6.0, "JLL Self Storage Outlook 2024"]
        },
        "non_climate": {
            "cap_rate": [5.5, 6.5, 8.0, "Marcus & Millichap Self Storage Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "SSA Quarterly Report Q4 2024"],
            "price_psf": [60, 90, 130, "RCA Analytics Q4 2024"],
            "expense_ratio": [28, 33, 38, "SSA Benchmark Report 2024"],
            "noi_growth": [2.5, 3.5, 5.0, "JLL Self Storage Outlook 2024"]
        },
        "mixed": {
            "cap_rate": [5.25, 6.25, 7.75, "Marcus & Millichap Self Storage Q4 2024"],
            "dscr": [1.22, 1.32, 1.47, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [86, 91, 94, "SSA Quarterly Report Q4 2024"],
            "price_psf": [75, 115, 175, "RCA Analytics Q4 2024"],
            "expense_ratio": [29, 34, 39, "SSA Benchmark Report 2024"],
            "noi_growth": [2.75, 4.0, 5.5, "JLL Self Storage Outlook 2024"]
        }
    },

    "data_center": {
        "wholesale": {
            "cap_rate": [5.0, 6.0, 7.0, "CBRE Data Center Q4 2024"],
            "dscr": [1.30, 1.45, 1.60, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [85, 92, 97, "451 Research Datacenter Q4 2024"],
            "walt": [7.0, 10.0, 15.0, "CBRE Data Center Q4 2024"],
            "power_density": [100, 150, 250, "Uptime Institute Standards 2024"],
            "pue": [1.3, 1.5, 1.7, "Uptime Institute Standards 2024"],
            "price_psf": [800, 1200, 1800, "RCA Analytics Q4 2024"]
        },
        "retail_colocation": {
            "cap_rate": [4.5, 5.5, 6.5, "CBRE Data Center Q4 2024"],
            "dscr": [1.35, 1.50, 1.65, "MBA Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Survey Q4 2024"],
            "occupancy": [88, 94, 98, "451 Research Datacenter Q4 2024"],
            "walt": [3.0, 5.0, 7.0, "CBRE Data Center Q4 2024"],
            "power_density": [75, 125, 200, "Uptime Institute Standards 2024"],
            "pue": [1.4, 1.6, 1.8, "Uptime Institute Standards 2024"],
            "price_psf": [600, 900, 1400, "RCA Analytics Q4 2024"]
        },
        "hyperscale": {
            "cap_rate": [4.0, 5.0, 6.0, "CBRE Data Center Q4 2024"],
            "dscr": [1.40, 1.55, 1.70, "MBA Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Survey Q4 2024"],
            "occupancy": [90, 95, 99, "451 Research Hyperscale Q4 2024"],
            "walt": [10.0, 15.0, 20.0, "CBRE Data Center Q4 2024"],
            "power_density": [150, 250, 400, "Uptime Institute Standards 2024"],
            "pue": [1.2, 1.4, 1.6, "Uptime Institute Standards 2024"],
            "price_psf": [1000, 1500, 2500, "RCA Analytics Q4 2024"]
        }
    },

    "life_science": {
        "wet_lab": {
            "cap_rate": [4.5, 5.5, 6.5, "CBRE Life Sciences Q4 2024"],
            "dscr": [1.25, 1.40, 1.55, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [88, 93, 96, "JLL Life Sciences Q4 2024"],
            "walt": [5.0, 7.0, 10.0, "CBRE Life Sciences Q4 2024"],
            "price_psf": [500, 750, 1100, "RCA Analytics Q4 2024"],
            "tenant_improvement": [150, 250, 400, "JLL Lab Construction 2024"],
            "parking_ratio": [2.5, 3.5, 4.5, "BioMed Realty Standards 2024"]
        },
        "dry_lab": {
            "cap_rate": [5.0, 6.0, 7.0, "CBRE Life Sciences Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "JLL Life Sciences Q4 2024"],
            "walt": [3.5, 5.5, 7.5, "CBRE Life Sciences Q4 2024"],
            "price_psf": [300, 450, 650, "RCA Analytics Q4 2024"],
            "tenant_improvement": [75, 125, 200, "JLL Lab Construction 2024"],
            "parking_ratio": [2.0, 3.0, 4.0, "BioMed Realty Standards 2024"]
        },
        "GMP_bio": {
            "cap_rate": [4.0, 5.0, 6.0, "CBRE Life Sciences Q4 2024"],
            "dscr": [1.30, 1.45, 1.60, "MBA Survey Q4 2024"],
            "ltv": [55, 60, 65, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "JLL Life Sciences Q4 2024"],
            "walt": [7.0, 10.0, 15.0, "CBRE Life Sciences Q4 2024"],
            "price_psf": [600, 900, 1400, "RCA Analytics Q4 2024"],
            "tenant_improvement": [200, 350, 550, "JLL GMP Construction 2024"],
            "parking_ratio": [2.0, 2.5, 3.5, "BioMed Realty Standards 2024"]
        },
        "R&D": {
            "cap_rate": [4.75, 5.75, 6.75, "CBRE Life Sciences Q4 2024"],
            "dscr": [1.22, 1.37, 1.52, "MBA Survey Q4 2024"],
            "ltv": [62, 67, 72, "MBA Survey Q4 2024"],
            "occupancy": [86, 91, 95, "JLL Life Sciences Q4 2024"],
            "walt": [4.0, 6.0, 8.5, "CBRE Life Sciences Q4 2024"],
            "price_psf": [400, 600, 900, "RCA Analytics Q4 2024"],
            "tenant_improvement": [100, 175, 275, "JLL R&D Construction 2024"],
            "parking_ratio": [2.25, 3.25, 4.25, "BioMed Realty Standards 2024"]
        }
    },

    "senior_living": {
        "IL": {
            "cap_rate": [5.5, 6.5, 8.0, "NIC MAP Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "NIC MAP Q4 2024"],
            "expense_ratio": [45, 50, 55, "ASHA Benchmark 2024"],
            "price_per_unit": [125000, 175000, 250000, "NIC Investment Guide 2024"],
            "noi_growth": [2.5, 3.5, 5.0, "JLL Seniors Housing 2024"]
        },
        "AL": {
            "cap_rate": [6.0, 7.0, 8.5, "NIC MAP Q4 2024"],
            "dscr": [1.15, 1.25, 1.40, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [85, 90, 94, "NIC MAP Q4 2024"],
            "expense_ratio": [55, 60, 65, "ASHA Benchmark 2024"],
            "price_per_unit": [150000, 225000, 325000, "NIC Investment Guide 2024"],
            "noi_growth": [3.0, 4.0, 5.5, "JLL Seniors Housing 2024"]
        },
        "MemoryCare": {
            "cap_rate": [6.5, 7.5, 9.0, "NIC MAP Q4 2024"],
            "dscr": [1.15, 1.25, 1.35, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [82, 88, 92, "NIC MAP Q4 2024"],
            "expense_ratio": [60, 65, 70, "ASHA Benchmark 2024"],
            "price_per_unit": [175000, 250000, 350000, "NIC Investment Guide 2024"],
            "noi_growth": [3.0, 4.5, 6.0, "JLL Seniors Housing 2024"]
        },
        "CCRC": {
            "cap_rate": [5.0, 6.0, 7.5, "NIC CCRC Report Q4 2024"],
            "dscr": [1.20, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [87, 92, 95, "NIC CCRC Report Q4 2024"],
            "expense_ratio": [50, 55, 60, "ASHA CCRC Benchmark 2024"],
            "price_per_unit": [200000, 300000, 450000, "NIC Investment Guide 2024"],
            "noi_growth": [2.5, 3.5, 5.0, "JLL CCRC Outlook 2024"]
        }
    },

    "student_housing": {
        "by_bed": {
            "cap_rate": [5.0, 6.0, 7.5, "Axiometrics Student Housing Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "Axiometrics Report Q4 2024"],
            "expense_ratio": [40, 45, 52, "NMHC Student Housing 2024"],
            "price_per_unit": [25000, 35000, 50000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.0, 3.0, 4.5, "JLL Student Housing 2024"]
        },
        "by_unit": {
            "cap_rate": [4.75, 5.75, 7.25, "Axiometrics Student Housing Q4 2024"],
            "dscr": [1.22, 1.32, 1.47, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [91, 95, 98, "Axiometrics Report Q4 2024"],
            "expense_ratio": [38, 43, 50, "NMHC Student Housing 2024"],
            "price_per_unit": [80000, 120000, 175000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.25, 3.25, 4.75, "JLL Student Housing 2024"]
        }
    },

    "manufactured_housing": {
        "MHC": {
            "cap_rate": [5.0, 6.0, 7.0, "JLL Manufactured Housing Q4 2024"],
            "dscr": [1.25, 1.35, 1.50, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [92, 95, 98, "MHI Community Report Q4 2024"],
            "expense_ratio": [35, 40, 45, "MHI Benchmark 2024"],
            "price_per_unit": [15000, 25000, 40000, "RCA Analytics Q4 2024"],
            "noi_growth": [3.0, 4.0, 5.5, "JLL MH Outlook 2024"]
        },
        "RV": {
            "cap_rate": [6.0, 7.0, 8.5, "JLL RV Resort Report Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [65, 70, 75, "MBA Survey Q4 2024"],
            "occupancy": [70, 80, 90, "ARVC Park Report Q4 2024"],
            "expense_ratio": [40, 45, 50, "ARVC Benchmark 2024"],
            "price_per_unit": [20000, 35000, 55000, "RCA Analytics Q4 2024"],
            "noi_growth": [2.5, 3.5, 5.0, "JLL RV Outlook 2024"]
        }
    },

    "mixed_use": {
        "res+retail": {
            "cap_rate": [4.75, 5.75, 7.0, "CBRE Mixed-Use Q4 2024"],
            "dscr": [1.22, 1.35, 1.48, "MBA Survey Q4 2024"],
            "ltv": [62, 67, 72, "MBA Survey Q4 2024"],
            "occupancy": [90, 94, 97, "JLL Mixed-Use Report Q4 2024"],
            "walt": [3.5, 5.5, 7.5, "CBRE Research Q4 2024"],
            "expense_ratio": [37, 42, 47, "IREM Mixed-Use Benchmark 2024"],
            "price_psf": [175, 275, 425, "RCA Analytics Q4 2024"]
        },
        "res+office": {
            "cap_rate": [5.0, 6.0, 7.5, "CBRE Mixed-Use Q4 2024"],
            "dscr": [1.20, 1.32, 1.45, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [88, 92, 95, "JLL Mixed-Use Report Q4 2024"],
            "walt": [3.0, 5.0, 7.0, "CBRE Research Q4 2024"],
            "expense_ratio": [38, 43, 48, "IREM Mixed-Use Benchmark 2024"],
            "price_psf": [150, 250, 400, "RCA Analytics Q4 2024"]
        },
        "custom": {
            "cap_rate": [5.25, 6.25, 7.75, "CBRE Mixed-Use Q4 2024"],
            "dscr": [1.20, 1.30, 1.45, "MBA Survey Q4 2024"],
            "ltv": [60, 65, 70, "MBA Survey Q4 2024"],
            "occupancy": [87, 91, 94, "JLL Mixed-Use Report Q4 2024"],
            "walt": [3.0, 4.5, 6.5, "CBRE Research Q4 2024"],
            "expense_ratio": [40, 45, 50, "IREM Mixed-Use Benchmark 2024"],
            "price_psf": [125, 225, 375, "RCA Analytics Q4 2024"]
        }
    }
}

# SECTION 3: OCR FIELD ALIASES
# Maps common synonyms and variations to standard field names
OCR_FIELD_ALIASES = {
    # Financial Fields
    "purchase_price": ["sales price", "acquisition price", "contract price", "pp", "sale price", "acquisition cost", "purchase amount"],
    "noi": ["net operating income", "net income", "operating income", "annual noi", "effective noi", "stabilized noi"],
    "cap_rate": ["capitalization rate", "cap", "going in cap", "initial yield", "acquisition cap", "entry cap"],
    "loan_amount": ["debt", "mortgage", "loan proceeds", "financing", "debt amount", "mortgage amount", "loan size"],
    "interest_rate": ["rate", "coupon", "interest", "loan rate", "mortgage rate", "debt rate", "borrowing rate"],
    "dscr": ["debt service coverage", "debt coverage", "coverage ratio", "dcr", "debt service cover"],
    "ltv": ["loan to value", "leverage", "ltv ratio", "debt to value", "loan-to-value ratio"],

    # Property Fields
    "asset_class": ["property type", "asset type", "product type", "property class", "real estate type"],
    "address": ["property address", "location", "street address", "property location", "site address"],
    "year_built": ["construction year", "built", "year constructed", "construction date", "vintage", "age"],
    "square_feet": ["sf", "sq ft", "gla", "nra", "gross leasable area", "rentable area", "building size", "total sf"],
    "units": ["unit count", "doors", "apartments", "total units", "unit mix", "number of units"],
    "occupancy": ["occupied", "occupancy rate", "leased", "physical occupancy", "economic occupancy", "occ"],

    # Lease Terms
    "walt": ["weighted average lease term", "wall", "remaining lease term", "lease duration", "average lease term"],
    "rent": ["rental rate", "lease rate", "rent roll", "base rent", "contract rent", "rental income"],
    "expense_ratio": ["opex ratio", "operating expense ratio", "expense rate", "operating expenses", "expense percentage"],
    "tenant": ["lessee", "occupant", "tenant name", "tenant roster", "rent roll"],

    # Hotel Specific
    "adr": ["average daily rate", "room rate", "avg rate", "daily rate", "average rate"],
    "revpar": ["rev par", "revenue per available room", "revpar index", "room revenue"],
    "occupancy_rate": ["occ rate", "occupancy %", "occupied percentage", "utilization"],
    "keys": ["rooms", "room count", "guestrooms", "hotel rooms", "number of rooms"],

    # Industrial Specific
    "clear_height": ["ceiling height", "clearance", "height", "clear ceiling", "warehouse height"],
    "dock_doors": ["loading docks", "dock high doors", "truck doors", "loading doors", "docks"],
    "parking_spaces": ["parking", "parking count", "spaces", "parking stalls", "car spaces"],

    # Retail Specific
    "anchor_tenant": ["anchor", "major tenant", "anchor store", "key tenant", "primary tenant"],
    "sales_psf": ["sales per square foot", "tenant sales", "retail sales", "sales volume", "sales per sf"],
    "parking_ratio": ["parking index", "parking per sf", "stalls per 1000 sf", "parking density"],

    # Multifamily Specific
    "unit_mix": ["bedroom mix", "unit types", "floorplan mix", "apartment mix", "unit breakdown"],
    "avg_rent": ["average rent", "mean rent", "avg monthly rent", "effective rent", "average unit rent"],
    "concessions": ["rent concessions", "free rent", "incentives", "move-in specials", "discounts"],

    # Office Specific
    "class": ["building class", "property class", "class a/b/c", "office class", "quality"],
    "floor_plate": ["floor size", "typical floor", "floor area", "plate size", "floor plan"],
    "elevator_count": ["elevators", "lifts", "vertical transportation", "elevator banks"],

    # Senior Living Specific
    "care_level": ["level of care", "care type", "acuity", "service level", "care services"],
    "medicaid": ["medicaid beds", "medicaid mix", "medicaid percentage", "medicaid units"],
    "private_pay": ["private pay mix", "private percentage", "private pay residents"]
}

# SECTION 4: HELPER FUNCTIONS

def get_benchmark_range(
    asset_class: str,
    subclass: str,
    metric: str
) -> Optional[List]:
    """
    Get benchmark range for a specific metric

    Args:
        asset_class: Main property type (e.g., "multifamily", "office")
        subclass: Specific subtype (e.g., "garden_lowrise", "cbd_A_trophy")
        metric: Metric name (e.g., "cap_rate", "dscr")

    Returns:
        List with [min, preferred, max, source] or None if not found
    """
    # Normalize inputs
    asset_class = asset_class.lower().replace(" ", "_").replace("-", "_")
    subclass = subclass.lower().replace(" ", "_").replace("-", "_")
    metric = metric.lower().replace(" ", "_")

    # Try to get benchmark
    try:
        if asset_class in BENCHMARKS:
            if subclass in BENCHMARKS[asset_class]:
                if metric in BENCHMARKS[asset_class][subclass]:
                    return BENCHMARKS[asset_class][subclass][metric]
            # Try without subclass (use first available)
            elif BENCHMARKS[asset_class]:
                first_subclass = list(BENCHMARKS[asset_class].keys())[0]
                if metric in BENCHMARKS[asset_class][first_subclass]:
                    return BENCHMARKS[asset_class][first_subclass][metric]
    except (KeyError, IndexError):
        pass

    return None

def get_status(
    value: float,
    benchmark_range: List
) -> str:
    """
    Determine if a value is OK, Borderline, or Offside based on benchmark

    Args:
        value: The actual metric value
        benchmark_range: List with [min, preferred, max, source]

    Returns:
        "OK" if within preferred range
        "Borderline" if between min-preferred or preferred-max
        "Offside" if outside min-max range
    """
    if not benchmark_range or len(benchmark_range) < 3:
        return "Unknown"

    min_val, preferred_val, max_val = benchmark_range[:3]

    # Handle reversed metrics (where lower is better, like expense ratio)
    if min_val > max_val:
        min_val, max_val = max_val, min_val
        if value <= preferred_val:
            return "OK"
        elif value <= min_val:
            return "Borderline"
        else:
            return "Offside"

    # Normal metrics (where mid-range is preferred)
    if isinstance(preferred_val, (list, tuple)):
        # Preferred is a range
        if preferred_val[0] <= value <= preferred_val[1]:
            return "OK"
        elif min_val <= value < preferred_val[0] or preferred_val[1] < value <= max_val:
            return "Borderline"
        else:
            return "Offside"
    else:
        # Single preferred value - use tolerance
        tolerance = abs(preferred_val * 0.1)  # 10% tolerance
        if abs(value - preferred_val) <= tolerance:
            return "OK"
        elif min_val <= value <= max_val:
            return "Borderline"
        else:
            return "Offside"

def get_metric_info(metric: str) -> Dict[str, str]:
    """
    Get detailed information about a metric

    Args:
        metric: The metric name

    Returns:
        Dictionary with unit, description, and why_it_matters
    """
    metric = metric.lower().replace(" ", "_")
    return METRICS_CATALOG.get(metric, {
        "unit": "",
        "description": "No description available",
        "why_it_matters": "Metric importance not documented"
    })

def normalize_field_name(field: str) -> Optional[str]:
    """
    Convert OCR-extracted field name to standard field name

    Args:
        field: Raw field name from OCR

    Returns:
        Standardized field name or None if not recognized
    """
    field_lower = field.lower().strip()

    # Check direct match first
    for standard_name, aliases in OCR_FIELD_ALIASES.items():
        if field_lower == standard_name:
            return standard_name
        if field_lower in [alias.lower() for alias in aliases]:
            return standard_name

    # Check partial matches
    for standard_name, aliases in OCR_FIELD_ALIASES.items():
        for alias in aliases:
            if alias.lower() in field_lower or field_lower in alias.lower():
                return standard_name

    return None

def get_all_metrics_for_asset_class(
    asset_class: str,
    subclass: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Get all available metrics and benchmarks for an asset class

    Args:
        asset_class: Main property type
        subclass: Optional specific subtype

    Returns:
        Dictionary of metric names to benchmark data
    """
    asset_class = asset_class.lower().replace(" ", "_").replace("-", "_")

    if asset_class not in BENCHMARKS:
        return {}

    if subclass:
        subclass = subclass.lower().replace(" ", "_").replace("-", "_")
        if subclass in BENCHMARKS[asset_class]:
            return BENCHMARKS[asset_class][subclass]

    # Return first available subclass benchmarks
    if BENCHMARKS[asset_class]:
        first_subclass = list(BENCHMARKS[asset_class].keys())[0]
        return BENCHMARKS[asset_class][first_subclass]

    return {}

# Export key components
__all__ = [
    'METRICS_CATALOG',
    'BENCHMARKS',
    'OCR_FIELD_ALIASES',
    'get_benchmark_range',
    'get_status',
    'get_metric_info',
    'normalize_field_name',
    'get_all_metrics_for_asset_class'
]