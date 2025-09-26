"""
Comprehensive OCR Parser for Commercial Real Estate Documents
Extracts 50+ fields from deal decks, term sheets, and property summaries
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class ComprehensiveDataParser:
    """Parse CRE documents extracting all possible deal fields with confidence scoring"""

    def __init__(self):
        self.extracted_fields = {}
        self.confidence_scores = {}
        self.extraction_notes = []
        self.missing_critical = []

    def parse(self, text: str, page_num: int = 1) -> Dict[str, Any]:
        """Main parsing function that extracts all fields from text"""
        if not text:
            return self._empty_result()

        # Clean and normalize text
        text = self._normalize_text(text)

        # Extract all field categories
        self._extract_deal_asset_fields(text, page_num)
        self._extract_pricing_exit_fields(text, page_num)
        self._extract_income_operations_fields(text, page_num)
        self._extract_leasing_fields(text, page_num)
        self._extract_debt_fields(text, page_num)
        self._extract_refinance_fields(text, page_num)
        self._extract_development_fields(text, page_num)
        self._extract_insurance_legal_fields(text, page_num)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence()

        # Identify missing critical fields
        self._identify_missing_critical()

        return {
            "extracted_fields": self.extracted_fields,
            "confidence_scores": self.confidence_scores,
            "extraction_notes": self.extraction_notes,
            "missing_critical": self.missing_critical,
            "overall_confidence": overall_confidence
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching"""
        # Convert to uppercase for consistent matching
        text = text.upper()
        # Normalize spacing
        text = re.sub(r'\s+', ' ', text)
        # Add spaces around punctuation for better matching
        text = re.sub(r'([:\-,])', r' \1 ', text)
        return text

    def _extract_value(self, text: str, patterns: List[Tuple[str, float]],
                      field_name: str, page_num: int = 1) -> Optional[float]:
        """Extract numeric value using multiple patterns"""
        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Extract the numeric value
                    value_str = match.group(1).replace(',', '').replace('$', '')
                    value = float(value_str) * multiplier

                    # Set confidence based on pattern clarity
                    if '?' in text[max(0, match.start()-10):match.end()+10]:
                        confidence = 0.6
                    else:
                        confidence = 0.9

                    self.extracted_fields[field_name] = value
                    self.confidence_scores[field_name] = confidence
                    self.extraction_notes.append(f"Found {field_name} on page {page_num}")
                    return value
                except:
                    continue
        return None

    def _extract_text_value(self, text: str, patterns: List[str],
                           field_name: str, page_num: int = 1) -> Optional[str]:
        """Extract text value using multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                self.extracted_fields[field_name] = value
                self.confidence_scores[field_name] = 0.85
                self.extraction_notes.append(f"Found {field_name} on page {page_num}")
                return value
        return None

    # ============================================================================
    # DEAL & ASSET SECTION
    # ============================================================================

    def _extract_deal_asset_fields(self, text: str, page_num: int):
        """Extract deal and asset identification fields"""

        # Property name
        self._extract_text_value(text, [
            r'PROPERTY\s*[:]\s*([^,\n]+)',
            r'DEAL\s*[:]\s*([^,\n]+)',
            r'PROJECT\s*[:]\s*([^,\n]+)',
            r'NAME\s*[:]\s*([^,\n]+)'
        ], 'property_name', page_num)

        # Address components
        self._extract_text_value(text, [
            r'ADDRESS\s*[:]\s*([^,\n]+)',
            r'LOCATION\s*[:]\s*([^,\n]+)',
            r'(\d+\s+[A-Z][A-Z0-9\s]+(?:STREET|ST|AVENUE|AVE|ROAD|RD|BLVD|BOULEVARD|WAY|DRIVE|DR|LANE|LN))'
        ], 'street_address', page_num)

        # City, State, ZIP
        city_state_zip = re.search(r'([A-Z][A-Z\s]+)\s*,\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', text)
        if city_state_zip:
            self.extracted_fields['city'] = city_state_zip.group(1).strip()
            self.extracted_fields['state'] = city_state_zip.group(2)
            self.extracted_fields['zip_code'] = city_state_zip.group(3)
            self.confidence_scores['city'] = 0.9
            self.confidence_scores['state'] = 0.95
            self.confidence_scores['zip_code'] = 0.95

        # Year built and renovated
        self._extract_value(text, [
            (r'YEAR\s+BUILT\s*[:]\s*(\d{4})', 1),
            (r'BUILT\s*[:]\s*(\d{4})', 1),
            (r'CONSTRUCTION\s+DATE\s*[:]\s*(\d{4})', 1)
        ], 'year_built', page_num)

        self._extract_value(text, [
            (r'RENOVATED\s*[:]\s*(\d{4})', 1),
            (r'RENOVATION\s*[:]\s*(\d{4})', 1),
            (r'GUT\s+REHAB\s*[:]\s*(\d{4})', 1),
            (r'LAST\s+RENOVATION\s*[:]\s*(\d{4})', 1)
        ], 'year_renovated', page_num)

        # Construction class
        self._extract_text_value(text, [
            r'CLASS\s*[:]\s*([A-C][+-]?)',
            r'BUILDING\s+CLASS\s*[:]\s*([A-C][+-]?)',
            r'CONSTRUCTION\s+TYPE\s*[:]\s*([IVX]+|[A-C])'
        ], 'construction_class', page_num)

        # Site and building metrics
        self._extract_value(text, [
            (r'SITE\s*[:]\s*(\d+(?:\.\d+)?)\s*ACRES?', 1),
            (r'LAND\s*[:]\s*(\d+(?:\.\d+)?)\s*ACRES?', 1),
            (r'(\d+(?:\.\d+)?)\s*ACRE\s+SITE', 1)
        ], 'site_acres', page_num)

        self._extract_value(text, [
            (r'(\d+(?:,\d{3})*)\s*(?:SF|SQ\.?\s*FT\.?|SQUARE\s+FEET)', 1),
            (r'BUILDING\s+SIZE\s*[:]\s*(\d+(?:,\d{3})*)', 1),
            (r'GLA\s*[:]\s*(\d+(?:,\d{3})*)', 1),
            (r'NRA\s*[:]\s*(\d+(?:,\d{3})*)', 1)
        ], 'building_sf', page_num)

        self._extract_value(text, [
            (r'(\d+)\s*UNITS?', 1),
            (r'UNIT\s+COUNT\s*[:]\s*(\d+)', 1),
            (r'NUMBER\s+OF\s+UNITS\s*[:]\s*(\d+)', 1)
        ], 'unit_count', page_num)

        # Parking
        self._extract_value(text, [
            (r'(\d+)\s*PARKING\s+SPACES?', 1),
            (r'PARKING\s*[:]\s*(\d+)\s*SPACES?', 1),
            (r'(\d+)\s*STALLS?', 1)
        ], 'parking_spaces', page_num)

        self._extract_value(text, [
            (r'PARKING\s+RATIO\s*[:]\s*(\d+(?:\.\d+)?)', 1),
            (r'(\d+(?:\.\d+)?)\s*/\s*1\s*,?\s*000\s+SF', 1)
        ], 'parking_ratio', page_num)

        # Occupancy and leasing metrics
        self._extract_value(text, [
            (r'OCCUPANCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+OCCUPIED', 0.01),
            (r'CURRENT\s+OCCUPANCY\s*[:]\s*(\d+(?:\.\d+)?)', 0.01)
        ], 'occupancy_pct', page_num)

        self._extract_value(text, [
            (r'WALT\s*[:]\s*(\d+(?:\.\d+)?)\s*(?:YEARS?|YRS?)', 1),
            (r'WEIGHTED\s+AVERAGE\s+LEASE\s+TERM\s*[:]\s*(\d+(?:\.\d+)?)', 1),
            (r'AVG\s+LEASE\s+TERM\s*[:]\s*(\d+(?:\.\d+)?)', 1)
        ], 'walt_years', page_num)

        # Tenant information
        self._extract_value(text, [
            (r'(\d+)\s*TENANTS?', 1),
            (r'NUMBER\s+OF\s+TENANTS\s*[:]\s*(\d+)', 1),
            (r'TENANT\s+COUNT\s*[:]\s*(\d+)', 1)
        ], 'num_tenants', page_num)

        # Extract top tenants
        tenant_pattern = r'([A-Z][A-Z\s&\.\-]+(?:LLC|INC|CORP|LP|LLP)?)\s*[\(\-]\s*(\d+(?:,\d{3})*)\s*(?:SF|SQ\.?\s*FT\.?)'
        tenant_matches = re.findall(tenant_pattern, text)
        if tenant_matches:
            top_tenants = []
            for i, (name, sf) in enumerate(tenant_matches[:5]):  # Top 5
                top_tenants.append({
                    'name': name.strip(),
                    'sf': float(sf.replace(',', ''))
                })
            self.extracted_fields['top_tenants'] = top_tenants
            self.confidence_scores['top_tenants'] = 0.8

        # Anchor tenant
        self._extract_text_value(text, [
            r'ANCHOR\s+TENANT\s*[:]\s*([A-Z][A-Z\s&\.\-]+)',
            r'ANCHOR\s*[:]\s*([A-Z][A-Z\s&\.\-]+)',
            r'MAJOR\s+TENANT\s*[:]\s*([A-Z][A-Z\s&\.\-]+)'
        ], 'anchor_tenant', page_num)

        # Environmental
        self._extract_text_value(text, [
            r'PHASE\s+I\s*[:]\s*([^,\n]+)',
            r'ESA\s*[:]\s*([^,\n]+)',
            r'ENVIRONMENTAL\s*[:]\s*([^,\n]+)'
        ], 'environmental_status', page_num)

    # ============================================================================
    # PRICING & EXIT SECTION
    # ============================================================================

    def _extract_pricing_exit_fields(self, text: str, page_num: int):
        """Extract pricing and exit strategy fields"""

        # Purchase price
        self._extract_value(text, [
            (r'PURCHASE\s+PRICE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)?', 1000000),
            (r'PRICE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)?', 1000000),
            (r'\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)\s+PURCHASE', 1000000),
            (r'ACQUISITION\s+PRICE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'purchase_price', page_num)

        # Closing costs
        self._extract_value(text, [
            (r'CLOSING\s+COSTS?\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'CLOSING\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'TRANSACTION\s+COSTS?\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'closing_costs', page_num)

        # Exit cap rate
        self._extract_value(text, [
            (r'EXIT\s+CAP\s*(?:RATE)?\s*[:]\s*(\d+(?:\.\d+)?)\s*%?', 0.01),
            (r'TERMINAL\s+CAP\s*[:]\s*(\d+(?:\.\d+)?)\s*%?', 0.01),
            (r'REVERSION\s+CAP\s*[:]\s*(\d+(?:\.\d+)?)\s*%?', 0.01)
        ], 'exit_cap_rate', page_num)

        # Hold period / exit year
        self._extract_value(text, [
            (r'HOLD\s+PERIOD\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'EXIT\s+YEAR\s*[:]\s*(\d+)', 1),
            (r'INVESTMENT\s+HORIZON\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1)
        ], 'hold_period_years', page_num)

        # Disposition fee
        self._extract_value(text, [
            (r'DISPOSITION\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'SALE\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'EXIT\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'disposition_fee_pct', page_num)

        # Transfer tax
        self._extract_value(text, [
            (r'TRANSFER\s+TAX\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'TRANSFER\s+TAX\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'DOCUMENTARY\s+STAMP\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'transfer_tax', page_num)

    # ============================================================================
    # INCOME & OPERATIONS SECTION
    # ============================================================================

    def _extract_income_operations_fields(self, text: str, page_num: int):
        """Extract income and operating expense fields"""

        # NOI
        self._extract_value(text, [
            (r'NOI\s*[:]\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)?', 1000000),
            (r'NET\s+OPERATING\s+INCOME\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'YEAR\s+1\s+NOI\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'STABILIZED\s+NOI\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'noi', page_num)

        # Gross income
        self._extract_value(text, [
            (r'EGI\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'EFFECTIVE\s+GROSS\s+INCOME\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'GROSS\s+INCOME\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'T-12\s+EGI\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'gross_income', page_num)

        # Operating expenses
        self._extract_value(text, [
            (r'OPERATING\s+EXPENSES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'OPEX\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'EXPENSES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'T-12\s+EXPENSES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'operating_expenses', page_num)

        # Real estate taxes
        self._extract_value(text, [
            (r'RE\s+TAXES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'REAL\s+ESTATE\s+TAXES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'PROPERTY\s+TAXES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'real_estate_taxes', page_num)

        # Insurance
        self._extract_value(text, [
            (r'INSURANCE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'PROPERTY\s+INSURANCE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'LIABILITY\s+INSURANCE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'insurance_cost', page_num)

        # Market rent
        self._extract_value(text, [
            (r'MARKET\s+RENT\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF', 1),
            (r'\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF\s+MARKET', 1),
            (r'MARKET\s+RATE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)\s*/\s*UNIT', 1),
            (r'\$?\s*(\d+(?:,\d{3})*)\s*/\s*UNIT\s+MARKET', 1)
        ], 'market_rent', page_num)

        # Vacancy and collection loss
        self._extract_value(text, [
            (r'VACANCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'VACANCY\s+RATE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+VACANCY', 0.01)
        ], 'vacancy_rate', page_num)

        # Management fee
        self._extract_value(text, [
            (r'MANAGEMENT\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'PM\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'PROPERTY\s+MANAGEMENT\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'management_fee_pct', page_num)

        # Replacement reserves
        self._extract_value(text, [
            (r'RESERVES?\s*[:]\s*\$?\s*(\d+)\s*/\s*UNIT', 1),
            (r'REPLACEMENT\s+RESERVES?\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF', 1),
            (r'CAPEX\s+RESERVES?\s*[:]\s*\$?\s*(\d+)\s*/\s*UNIT', 1)
        ], 'replacement_reserves', page_num)

    # ============================================================================
    # LEASING SECTION (Office/Retail)
    # ============================================================================

    def _extract_leasing_fields(self, text: str, page_num: int):
        """Extract leasing-related fields for office and retail properties"""

        # Check if this is office/retail
        if not any(word in text for word in ['OFFICE', 'RETAIL', 'SHOPPING', 'STRIP']):
            return

        # TI allowances
        self._extract_value(text, [
            (r'TI\s+ALLOWANCE\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF', 1),
            (r'TENANT\s+IMPROVEMENTS?\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF', 1),
            (r'NEW\s+TI\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)', 1)
        ], 'ti_allowance_new', page_num)

        self._extract_value(text, [
            (r'RENEWAL\s+TI\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)\s*/\s*SF', 1),
            (r'TI\s+RENEWAL\s*[:]\s*\$?\s*(\d+(?:\.\d+)?)', 1)
        ], 'ti_allowance_renewal', page_num)

        # Leasing commissions
        self._extract_value(text, [
            (r'LEASING\s+COMMISSION\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'LC\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'BROKER\s+COMMISSION\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'leasing_commission_pct', page_num)

        # Free rent
        self._extract_value(text, [
            (r'FREE\s+RENT\s*[:]\s*(\d+)\s*MONTHS?', 1),
            (r'(\d+)\s*MONTHS?\s+FREE\s+RENT', 1),
            (r'RENT\s+ABATEMENT\s*[:]\s*(\d+)\s*MONTHS?', 1)
        ], 'free_rent_months', page_num)

        # Renewal probability
        self._extract_value(text, [
            (r'RENEWAL\s+PROBABILITY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'RENEWAL\s+RATE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'RETENTION\s+RATE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'renewal_probability_pct', page_num)

        # Downtime
        self._extract_value(text, [
            (r'DOWNTIME\s*[:]\s*(\d+)\s*MONTHS?', 1),
            (r'LEASE-UP\s+PERIOD\s*[:]\s*(\d+)\s*MONTHS?', 1),
            (r'ABSORPTION\s*[:]\s*(\d+)\s*MONTHS?', 1)
        ], 'downtime_months', page_num)

    # ============================================================================
    # DEBT SECTION
    # ============================================================================

    def _extract_debt_fields(self, text: str, page_num: int):
        """Extract comprehensive debt and financing fields"""

        # Loan amount
        self._extract_value(text, [
            (r'LOAN\s+AMOUNT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)?', 1000000),
            (r'DEBT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:MM?|MILLION)?', 1000000),
            (r'MORTGAGE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'FINANCING\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'loan_amount', page_num)

        # Interest rate components
        rate_pattern = r'(?:SOFR|LIBOR|PRIME|BASE\s+RATE)\s*\+\s*(\d+(?:\.\d+)?)\s*(?:%|BPS|BASIS\s+POINTS?)?'
        rate_match = re.search(rate_pattern, text, re.IGNORECASE)
        if rate_match:
            spread = float(rate_match.group(1))
            if 'BPS' in text[rate_match.start():rate_match.end()+20].upper() or spread > 50:
                spread = spread / 100  # Convert basis points to percentage
            self.extracted_fields['rate_spread'] = spread
            self.confidence_scores['rate_spread'] = 0.9
            self.extraction_notes.append(f"Found rate spread on page {page_num}")

        # Fixed rate
        self._extract_value(text, [
            (r'INTEREST\s+RATE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'RATE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'COUPON\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+(?:INTEREST|FIXED)', 0.01)
        ], 'interest_rate', page_num)

        # Amortization
        self._extract_value(text, [
            (r'AMORTIZATION\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'AMORT\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'(\d+)\s*[-/]\s*YEAR\s+AMORT', 1)
        ], 'amort_years', page_num)

        # Interest only period
        self._extract_value(text, [
            (r'IO\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?|MONTHS?)', 1),
            (r'INTEREST[\s-]ONLY\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'(\d+)\s*(?:YEARS?|YRS?)\s+IO', 1),
            (r'IO\s+PERIOD\s*[:]\s*(\d+)\s*MONTHS?', 1/12)
        ], 'io_period_years', page_num)

        # Loan term
        self._extract_value(text, [
            (r'TERM\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'LOAN\s+TERM\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'MATURITY\s*[:]\s*(\d+)\s*(?:YEARS?|YRS?)', 1),
            (r'(\d+)\s*[-/]\s*YEAR\s+TERM', 1)
        ], 'loan_term_years', page_num)

        # LTV
        self._extract_value(text, [
            (r'LTV\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'LOAN[\s-]TO[\s-]VALUE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+LTV', 0.01)
        ], 'ltv_pct', page_num)

        # DSCR requirements
        self._extract_value(text, [
            (r'MIN(?:IMUM)?\s+DSCR\s*[:]\s*(\d+(?:\.\d+)?)', 1),
            (r'DSCR\s+REQUIREMENT\s*[:]\s*(\d+(?:\.\d+)?)', 1),
            (r'DEBT\s+SERVICE\s+COVERAGE\s*[:]\s*(\d+(?:\.\d+)?)', 1)
        ], 'min_dscr', page_num)

        # Debt yield
        self._extract_value(text, [
            (r'DEBT\s+YIELD\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'MIN(?:IMUM)?\s+DEBT\s+YIELD\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+DEBT\s+YIELD', 0.01)
        ], 'min_debt_yield', page_num)

        # Origination fee
        self._extract_value(text, [
            (r'ORIGINATION\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'LOAN\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'POINTS?\s*[:]\s*(\d+(?:\.\d+)?)', 0.01)
        ], 'origination_fee_pct', page_num)

        # Prepayment terms
        prepay_terms = ['OPEN', 'LOCKOUT', 'YIELD MAINTENANCE', 'DEFEASANCE']
        for term in prepay_terms:
            if term in text:
                self.extracted_fields['prepayment_type'] = term.lower()
                self.confidence_scores['prepayment_type'] = 0.85
                break

        # Rate cap
        self._extract_value(text, [
            (r'RATE\s+CAP\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'CAP\s+STRIKE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'HEDGE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'rate_cap_strike', page_num)

        # Extension options
        extension_pattern = r'(\d+)\s*[Xx]\s*(\d+)\s*MO(?:NTH)?S?\s+(?:EXTENSION|OPTION)'
        extension_match = re.search(extension_pattern, text)
        if extension_match:
            self.extracted_fields['extension_count'] = int(extension_match.group(1))
            self.extracted_fields['extension_term_months'] = int(extension_match.group(2))
            self.confidence_scores['extension_count'] = 0.85
            self.confidence_scores['extension_term_months'] = 0.85

        # Extension fee
        self._extract_value(text, [
            (r'EXTENSION\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+EXTENSION\s+FEE', 0.01),
            (r'OPTION\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'extension_fee_pct', page_num)

        # Reserve requirements
        self._extract_value(text, [
            (r'INTEREST\s+RESERVE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'DEBT\s+SERVICE\s+RESERVE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'(\d+)\s+MONTHS?\s+RESERVES?', 1)  # Assuming monthly debt service
        ], 'interest_reserve', page_num)

        self._extract_value(text, [
            (r'TI[/\\]LC\s+RESERVE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'TENANT\s+IMPROVEMENT\s+RESERVE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'ti_lc_reserve', page_num)

    # ============================================================================
    # REFINANCE SECTION
    # ============================================================================

    def _extract_refinance_fields(self, text: str, page_num: int):
        """Extract refinance assumption fields"""

        # Refinance cap rate
        self._extract_value(text, [
            (r'REFI(?:NANCE)?\s+CAP\s*(?:RATE)?\s*[:]\s*(\d+(?:\.\d+)?)\s*%?', 0.01),
            (r'MARKET\s+CAP\s+(?:RATE\s+)?FOR\s+REFI\s*[:]\s*(\d+(?:\.\d+)?)', 0.01),
            (r'REFINANCE\s+AT\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'refi_cap_rate', page_num)

        # Target refinance LTV
        self._extract_value(text, [
            (r'REFI(?:NANCE)?\s+LTV\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'TARGET\s+LTV\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'NEW\s+LOAN\s+LTV\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'refi_ltv_target', page_num)

        # Underwriting haircuts
        self._extract_value(text, [
            (r'UNDERWRITING\s+VACANCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'LENDER\s+VACANCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'UW\s+VACANCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01)
        ], 'underwriting_vacancy', page_num)

    # ============================================================================
    # DEVELOPMENT SECTION
    # ============================================================================

    def _extract_development_fields(self, text: str, page_num: int):
        """Extract development and construction fields"""

        # Check if this is a development deal
        if not any(word in text for word in ['DEVELOPMENT', 'CONSTRUCTION', 'BUILD', 'GROUND-UP']):
            return

        # Land cost
        self._extract_value(text, [
            (r'LAND\s+(?:COST|PRICE)\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'SITE\s+ACQUISITION\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'LAND\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'land_cost', page_num)

        # Hard costs
        self._extract_value(text, [
            (r'HARD\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'CONSTRUCTION\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'DIRECT\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'GMP\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'hard_costs', page_num)

        # Soft costs
        self._extract_value(text, [
            (r'SOFT\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'INDIRECT\s+COSTS?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'PROFESSIONAL\s+FEES?\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'soft_costs', page_num)

        # Developer fee
        self._extract_value(text, [
            (r'DEVELOPER\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'DEV\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'SPONSOR\s+FEE\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'DEVELOPER\s+FEE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'developer_fee', page_num)

        # Contingency
        self._extract_value(text, [
            (r'CONTINGENCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'HARD\s+COST\s+CONTINGENCY\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+CONTINGENCY', 0.01)
        ], 'contingency_pct', page_num)

        # Contract type
        contract_types = ['GMP', 'GUARANTEED MAXIMUM PRICE', 'COST-PLUS', 'COST PLUS',
                         'DESIGN-BUILD', 'DESIGN BUILD', 'FIXED PRICE', 'LUMP SUM']
        for contract_type in contract_types:
            if contract_type in text:
                self.extracted_fields['construction_contract_type'] = contract_type.replace(' ', '_').lower()
                self.confidence_scores['construction_contract_type'] = 0.85
                break

        # Pre-leasing
        self._extract_value(text, [
            (r'PRE[\s-]LEASING\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'PRE[\s-]LEASED\s*[:]\s*(\d+(?:\.\d+)?)\s*%', 0.01),
            (r'(\d+(?:\.\d+)?)\s*%\s+PRE[\s-]LEASED', 0.01)
        ], 'preleasing_pct', page_num)

        # Delivery date
        delivery_pattern = r'(?:DELIVERY|COMPLETION|COO?)\s*[:]\s*([QJF][1-4]?\s*\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|[A-Z]+\s+\d{4})'
        delivery_match = re.search(delivery_pattern, text)
        if delivery_match:
            self.extracted_fields['expected_delivery'] = delivery_match.group(1)
            self.confidence_scores['expected_delivery'] = 0.8

        # Interest reserve period
        self._extract_value(text, [
            (r'INTEREST\s+RESERVE\s*[:]\s*(\d+)\s*MONTHS?', 1),
            (r'CARRY\s*[:]\s*(\d+)\s*MONTHS?', 1),
            (r'(\d+)\s*MONTHS?\s+(?:OF\s+)?INTEREST\s+RESERVE', 1)
        ], 'interest_reserve_months', page_num)

        # General contractor
        self._extract_text_value(text, [
            r'GENERAL\s+CONTRACTOR\s*[:]\s*([A-Z][A-Z\s&\.\-]+)',
            r'GC\s*[:]\s*([A-Z][A-Z\s&\.\-]+)',
            r'CONTRACTOR\s*[:]\s*([A-Z][A-Z\s&\.\-]+)'
        ], 'general_contractor', page_num)

        # Permit status
        permit_keywords = ['PERMITS? APPROVED', 'PERMITS? IN HAND', 'PERMITS? OBTAINED',
                          'PERMITS? PENDING', 'PERMITS? IN PROCESS']
        for keyword in permit_keywords:
            if re.search(keyword, text):
                self.extracted_fields['permit_status'] = keyword.lower().replace(' ', '_')
                self.confidence_scores['permit_status'] = 0.85
                break

    # ============================================================================
    # INSURANCE & LEGAL SECTION
    # ============================================================================

    def _extract_insurance_legal_fields(self, text: str, page_num: int):
        """Extract insurance and legal related fields"""

        # Insurance coverage
        self._extract_value(text, [
            (r'INSURANCE\s+COVERAGE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'LIABILITY\s+LIMIT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'COVERAGE\s+LIMIT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'insurance_coverage_limit', page_num)

        # Deductible
        self._extract_value(text, [
            (r'DEDUCTIBLE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
            (r'INSURANCE\s+DEDUCTIBLE\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
        ], 'insurance_deductible', page_num)

        # Ground lease
        if 'GROUND LEASE' in text:
            self.extracted_fields['ground_lease'] = True
            self.confidence_scores['ground_lease'] = 0.9

            # Ground lease term
            self._extract_value(text, [
                (r'GROUND\s+LEASE\s+TERM\s*[:]\s*(\d+)\s*YEARS?', 1),
                (r'LEASE\s+EXPIRES?\s*[:]\s*(\d{4})', 1),
                (r'(\d+)\s*YEAR\s+GROUND\s+LEASE', 1)
            ], 'ground_lease_term_years', page_num)

            # Ground rent
            self._extract_value(text, [
                (r'GROUND\s+RENT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1),
                (r'ANNUAL\s+GROUND\s+RENT\s*[:]\s*\$?\s*(\d+(?:,\d{3})*)', 1)
            ], 'ground_rent_annual', page_num)

        # Litigation flags
        litigation_keywords = ['LITIGATION', 'LAWSUIT', 'LEGAL ACTION', 'COURT', 'DISPUTE']
        for keyword in litigation_keywords:
            if keyword in text:
                self.extracted_fields['litigation_flag'] = True
                self.confidence_scores['litigation_flag'] = 0.7
                self.extraction_notes.append(f"Litigation keyword '{keyword}' found on page {page_num}")
                break

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _calculate_overall_confidence(self) -> float:
        """Calculate overall extraction confidence"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)

    def _identify_missing_critical(self):
        """Identify critical missing fields for calculations"""
        critical_fields = [
            'purchase_price', 'noi', 'loan_amount', 'interest_rate',
            'exit_cap_rate', 'hold_period_years'
        ]

        for field in critical_fields:
            if field not in self.extracted_fields:
                self.missing_critical.append(field)

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "extracted_fields": {},
            "confidence_scores": {},
            "extraction_notes": ["No text provided"],
            "missing_critical": [],
            "overall_confidence": 0.0
        }

    def aggregate_multipage_data(self, page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data from multiple pages"""
        aggregated = {
            "extracted_fields": {},
            "confidence_scores": {},
            "extraction_notes": [],
            "missing_critical": set(),
            "overall_confidence": 0.0
        }

        # Merge all page results
        for page_result in page_results:
            # Merge fields, preferring higher confidence values
            for field, value in page_result.get('extracted_fields', {}).items():
                current_confidence = aggregated['confidence_scores'].get(field, 0)
                new_confidence = page_result['confidence_scores'].get(field, 0)

                if new_confidence > current_confidence:
                    aggregated['extracted_fields'][field] = value
                    aggregated['confidence_scores'][field] = new_confidence

            # Collect all notes
            aggregated['extraction_notes'].extend(page_result.get('extraction_notes', []))

            # Collect missing fields
            aggregated['missing_critical'].update(page_result.get('missing_critical', []))

        # Convert set back to list
        aggregated['missing_critical'] = list(aggregated['missing_critical'])

        # Recalculate overall confidence
        if aggregated['confidence_scores']:
            aggregated['overall_confidence'] = sum(aggregated['confidence_scores'].values()) / len(aggregated['confidence_scores'])

        return aggregated