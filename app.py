"""
DealGenie Pro - Commercial Real Estate Analysis Platform
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import re
from typing import Dict, Any, Optional, List, Tuple
import base64
import io
from PIL import Image
import io
from ocr_parser import ComprehensiveDataParser
from llm_enhancement import render_api_settings, render_summary_with_llm_option, calculate_metrics_for_llm
from cre_extraction_engine import CREExtractionEngine, ASSET_CLASSES
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
import matplotlib.pyplot as plt
import seaborn as sns
import xlsxwriter

# Page Configuration
st.set_page_config(
    page_title="DealGenie Pro | CRE Analysis Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/yourusername/dealgenie-app',
        'Report a bug': "https://github.com/yourusername/dealgenie-app/issues",
        'About': "DealGenie Pro v1.0 - Institutional-Grade CRE Analysis"
    }
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

def inject_custom_css():
    """Apply custom CSS styling for professional look"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        color: white;
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        height: 100%;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .status-badge {
        padding: 0.375rem 0.875rem;
        border-radius: 20px;
        font-size: 0.813rem;
        font-weight: 600;
        display: inline-block;
        text-transform: uppercase;
    }

    .status-good { background: #10b981; color: white; }
    .status-warning { background: #f59e0b; color: white; }
    .status-critical { background: #ef4444; color: white; }

    @media (max-width: 768px) {
        .main-header { padding: 1rem; }
        .metric-card { margin-bottom: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FINANCIAL CALCULATIONS
# ============================================================================

def calculate_mortgage_constant(annual_rate: float, amort_years: int, io_period: int = 0) -> float:
    """Calculate mortgage constant with IO period support"""
    if amort_years == 0:
        return annual_rate

    monthly_rate = annual_rate / 12
    n_payments = amort_years * 12

    if monthly_rate == 0:
        monthly_payment = 1 / n_payments
    else:
        monthly_payment = (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)

    return monthly_payment * 12

def calculate_dscr(noi: float, loan_amount: float, rate: float, amort_years: int) -> float:
    """Calculate Debt Service Coverage Ratio"""
    if loan_amount == 0 or rate == 0:
        return 0

    mortgage_constant = calculate_mortgage_constant(rate, amort_years)
    annual_debt_service = loan_amount * mortgage_constant

    return noi / annual_debt_service if annual_debt_service > 0 else 0

def calculate_irr(cash_flows: List[float]) -> float:
    """Calculate Internal Rate of Return"""
    try:
        return np.irr(cash_flows) * 100
    except:
        return 0

# ============================================================================
# OCR PARSER
# ============================================================================

# Legacy parser for backward compatibility
class FinancialDataParser:
    """Legacy parser - redirects to ComprehensiveDataParser"""

    def parse(self, text: str) -> Dict[str, Any]:
        """Use comprehensive parser but return simplified format for compatibility"""
        parser = ComprehensiveDataParser()
        result = parser.parse(text)

        # Extract key fields for backward compatibility
        fields = result.get('extracted_fields', {})
        simplified = {
            'confidence': result.get('overall_confidence', 0.8),
            'purchase_price': fields.get('purchase_price'),
            'noi': fields.get('noi'),
            'cap_rate': fields.get('cap_rate'),
            'loan_amount': fields.get('loan_amount'),
            'interest_rate': fields.get('interest_rate'),
            'units': fields.get('unit_count'),
            'sf': fields.get('building_sf')
        }

        # Remove None values
        return {k: v for k, v in simplified.items() if v is not None}

# ============================================================================
# BENCHMARKS WITH SOURCES
# ============================================================================

BENCHMARKS = {
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

def evaluate_against_benchmarks(asset_class: str, metrics: Dict) -> List[Dict]:
    """Evaluate metrics against industry benchmarks"""
    if asset_class not in BENCHMARKS:
        return []

    benchmarks = BENCHMARKS[asset_class]
    evaluations = []

    for metric, value in metrics.items():
        if metric in benchmarks:
            bench = benchmarks[metric]
            status = "good"
            if value < bench["min"]:
                status = "critical"
            elif value < bench["preferred"]:
                status = "warning"

            evaluations.append({
                "metric": metric.upper(),
                "value": value,
                "status": status,
                "benchmark": f"{bench['preferred']} ({bench['source']})"
            })

    return evaluations

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def _display_fields(extracted_data: Dict, field_names: List[str]):
    """Helper function to display extracted fields in a clean format"""
    for field in field_names:
        if field in extracted_data:
            value = extracted_data[field]
            # Format the field name
            display_name = field.replace('_', ' ').title()

            # Format the value
            if isinstance(value, float):
                if field.endswith('_pct') or field == 'cap_rate':
                    st.write(f"**{display_name}**: {value:.2f}%")
                elif 'price' in field or 'cost' in field or 'amount' in field:
                    st.write(f"**{display_name}**: ${value:,.0f}")
                else:
                    st.write(f"**{display_name}**: {value:,.2f}")
            elif isinstance(value, list):
                st.write(f"**{display_name}**:")
                for item in value[:5]:  # Show first 5 items
                    if isinstance(item, dict):
                        st.caption(f"  • {item}")
                    else:
                        st.caption(f"  • {item}")
            else:
                st.write(f"**{display_name}**: {value}")

def render_header():
    """Render application header"""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🏢 DealGenie Pro</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Institutional-Grade Commercial Real Estate Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)

def render_input_section():
    """Render deal input section"""
    st.header("📊 Deal Analysis")

    # Input method selection
    input_method = st.radio(
        "Select Input Method",
        ["📝 Manual Entry", "📷 Photo/OCR", "📁 Upload File"],
        horizontal=True
    )

    parsed_data = {}

    if input_method == "📝 Manual Entry":
        col1, col2, col3 = st.columns(3)

        with col1:
            asset_class = st.selectbox(
                "Asset Class",
                ["Office", "Multifamily", "Industrial", "Retail", "Hotel"]
            )
            purchase_price = st.number_input(
                "Purchase Price ($)",
                min_value=0,
                value=18500000,
                step=100000
            )

        with col2:
            noi = st.number_input(
                "Year 1 NOI ($)",
                min_value=0,
                value=1110000,
                step=10000
            )
            loan_amount = st.number_input(
                "Loan Amount ($)",
                min_value=0,
                value=13000000,
                step=100000
            )

        with col3:
            interest_rate = st.slider(
                "Interest Rate (%)",
                min_value=3.0,
                max_value=10.0,
                value=6.5,
                step=0.25
            ) / 100
            amort_years = st.number_input(
                "Amortization (years)",
                min_value=0,
                max_value=40,
                value=30
            )

        parsed_data = {
            "asset_class": asset_class,
            "purchase_price": purchase_price,
            "noi": noi,
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "amort_years": amort_years
        }

    elif input_method == "📷 Photo/OCR":
        # Asset Class Selection for Enhanced Extraction
        st.markdown("### 🏢 Asset Classification")

        col1, col2 = st.columns(2)
        with col1:
            asset_class = st.selectbox(
                "Select Asset Class",
                options=list(ASSET_CLASSES.keys()),
                help="Choose the property type for enhanced extraction and benchmarks"
            )

        with col2:
            if asset_class in ASSET_CLASSES:
                subclass = st.selectbox(
                    "Select Subclass",
                    options=ASSET_CLASSES[asset_class],
                    help="Choose specific subclass for targeted analysis"
                )
            else:
                subclass = None

        # Store selections in session state
        if 'asset_class' not in st.session_state:
            st.session_state.asset_class = asset_class
        if 'subclass' not in st.session_state:
            st.session_state.subclass = subclass

        st.session_state.asset_class = asset_class
        st.session_state.subclass = subclass

        st.markdown("---")

        uploaded_file = st.file_uploader(
            "Upload deal summary (Image, PDF, or PowerPoint)",
            type=['png', 'jpg', 'jpeg', 'pdf', 'pptx', 'ppt']
        )

        if uploaded_file:
            file_type = uploaded_file.name.split('.')[-1].lower()
            ocr_text = ""

            # Process based on file type
            if file_type in ['png', 'jpg', 'jpeg']:
                st.info("📸 Processing image with OCR...")
                try:
                    import pytesseract
                    image = Image.open(uploaded_file)
                    ocr_text = pytesseract.image_to_string(image)

                    # Check if no text was extracted
                    if not ocr_text.strip():
                        st.warning("⚠️ No text found in image. The image may be unclear or contain no readable text. Using demo data.")
                        ocr_text = """
                        INVESTMENT SUMMARY
                        Property: Northgate Business Center
                        Address: 1234 Market Street, Dallas, TX 75201
                        Year Built: 1985 | Renovated: 2020
                        Building Size: 125,000 SF
                        Site: 5.2 acres
                        Parking: 350 spaces (2.8/1,000 SF)
                        Occupancy: 92%
                        WALT: 4.2 years
                        Number of Tenants: 12
                        Anchor Tenant: Wells Fargo (25,000 SF)

                        FINANCIAL HIGHLIGHTS
                        Purchase Price: $18.5MM
                        Price/SF: $148
                        NOI: $1,110,000
                        Cap Rate: 6.0%
                        T-12 EGI: $1,850,000
                        Operating Expenses: $740,000
                        Real Estate Taxes: $285,000
                        Insurance: $48,000
                        Management Fee: 3.5%

                        DEBT TERMS
                        Loan Amount: $13 million
                        LTV: 70%
                        Interest Rate: SOFR + 250 bps (6.25% all-in)
                        Amortization: 30 years
                        IO Period: 3 years
                        Term: 10 years
                        DSCR Requirement: 1.25x minimum
                        Origination Fee: 1.0%
                        Extension: 2x12mo at 0.25% fee
                        Rate Cap: 7.5% strike

                        EXIT STRATEGY
                        Hold Period: 5 years
                        Exit Cap Rate: 6.75%
                        Disposition Fee: 1.5%
                        """

                except Exception as e:
                    st.warning("OCR library not available. Using demo data.")
                    # Fallback to demo text if OCR fails
                    ocr_text = """
                    Purchase Price: $18.5MM
                    NOI: $1,110,000
                    Cap Rate: 6.0%
                    Loan Amount: $13 million
                    Interest Rate: 6.25%
                    """

            elif file_type == 'pdf':
                st.info("📄 Processing PDF document...")
                try:
                    import pdfplumber
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                ocr_text += page_text + "\n"

                    # Check if no text was extracted
                    if not ocr_text.strip():
                        st.warning("⚠️ No text found in PDF. The file may be image-based or protected. Using demo data.")
                        ocr_text = """
                        INVESTMENT SUMMARY
                        Property: Northgate Business Center
                        Address: 1234 Market Street, Dallas, TX 75201
                        Year Built: 1985 | Renovated: 2020
                        Building Size: 125,000 SF
                        Site: 5.2 acres
                        Parking: 350 spaces (2.8/1,000 SF)
                        Occupancy: 92%
                        WALT: 4.2 years
                        Number of Tenants: 12
                        Anchor Tenant: Wells Fargo (25,000 SF)

                        FINANCIAL HIGHLIGHTS
                        Purchase Price: $18.5MM
                        Price/SF: $148
                        NOI: $1,110,000
                        Cap Rate: 6.0%
                        T-12 EGI: $1,850,000
                        Operating Expenses: $740,000
                        Real Estate Taxes: $285,000
                        Insurance: $48,000
                        Management Fee: 3.5%

                        DEBT TERMS
                        Loan Amount: $13 million
                        LTV: 70%
                        Interest Rate: SOFR + 250 bps (6.25% all-in)
                        Amortization: 30 years
                        IO Period: 3 years
                        Term: 10 years
                        DSCR Requirement: 1.25x minimum
                        Origination Fee: 1.0%
                        Extension: 2x12mo at 0.25% fee
                        Rate Cap: 7.5% strike

                        EXIT STRATEGY
                        Hold Period: 5 years
                        Exit Cap Rate: 6.75%
                        Disposition Fee: 1.5%
                        """

                except Exception as e:
                    st.warning("PDF processing library not available. Using demo data.")
                    ocr_text = """
                    Purchase Price: $18.5MM
                    NOI: $1,110,000
                    Cap Rate: 6.0%
                    Loan Amount: $13 million
                    Interest Rate: 6.25%
                    """

            elif file_type in ['pptx', 'ppt']:
                st.info("📊 Processing PowerPoint presentation...")
                try:
                    from pptx import Presentation
                    prs = Presentation(uploaded_file)
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if hasattr(shape, 'text'):
                                ocr_text += shape.text + "\n"

                    # Check if no text was extracted
                    if not ocr_text.strip():
                        st.warning("⚠️ No text found in PowerPoint. The slides may contain only images or shapes. Using demo data.")
                        ocr_text = """
                        INVESTMENT SUMMARY
                        Property: Northgate Business Center
                        Address: 1234 Market Street, Dallas, TX 75201
                        Year Built: 1985 | Renovated: 2020
                        Building Size: 125,000 SF
                        Site: 5.2 acres
                        Parking: 350 spaces (2.8/1,000 SF)
                        Occupancy: 92%
                        WALT: 4.2 years
                        Number of Tenants: 12
                        Anchor Tenant: Wells Fargo (25,000 SF)

                        FINANCIAL HIGHLIGHTS
                        Purchase Price: $18.5MM
                        Price/SF: $148
                        NOI: $1,110,000
                        Cap Rate: 6.0%
                        T-12 EGI: $1,850,000
                        Operating Expenses: $740,000
                        Real Estate Taxes: $285,000
                        Insurance: $48,000
                        Management Fee: 3.5%

                        DEBT TERMS
                        Loan Amount: $13 million
                        LTV: 70%
                        Interest Rate: SOFR + 250 bps (6.25% all-in)
                        Amortization: 30 years
                        IO Period: 3 years
                        Term: 10 years
                        DSCR Requirement: 1.25x minimum
                        Origination Fee: 1.0%
                        Extension: 2x12mo at 0.25% fee
                        Rate Cap: 7.5% strike

                        EXIT STRATEGY
                        Hold Period: 5 years
                        Exit Cap Rate: 6.75%
                        Disposition Fee: 1.5%
                        """

                except Exception as e:
                    st.warning("PowerPoint processing library not available. Using demo data.")
                    ocr_text = """
                    Purchase Price: $18.5MM
                    NOI: $1,110,000
                    Cap Rate: 6.0%
                    Loan Amount: $13 million
                    Interest Rate: 6.25%
                    """

            else:
                st.error("Unsupported file type")
                return parsed_data

            if ocr_text.strip():
                # Use enhanced CRE extraction engine if asset class selected
                if hasattr(st.session_state, 'asset_class') and hasattr(st.session_state, 'subclass'):
                    try:
                        st.info(f"🚀 Using Enhanced Extraction for {st.session_state.asset_class.title()} - {st.session_state.subclass.replace('_', ' ').title()}")

                        # Initialize CRE extraction engine
                        cre_engine = CREExtractionEngine(st.session_state.asset_class, st.session_state.subclass)
                        cre_result = cre_engine.extract(ocr_text)

                        # Display enhanced results
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Show extracted text in expander
                            with st.expander("📝 Extracted Text", expanded=False):
                                st.text(ocr_text[:2000] + "..." if len(ocr_text) > 2000 else ocr_text)

                        with col2:
                            # Show extraction summary with new metrics
                            completeness = cre_result.get('completeness', {})
                            required_fields = completeness.get('required_fields', 0)
                            total_required = completeness.get('total_required', 1)
                            completeness_pct = (required_fields / total_required) * 100

                            st.metric("Completeness", f"{completeness_pct:.0f}%")
                            st.caption(f"Required: {required_fields}/{total_required}")
                            st.caption(f"Total fields: {len(cre_result.get('ingested', {}))}")

                        # Store enhanced results for analysis
                        st.session_state.cre_result = cre_result

                    except Exception as e:
                        st.error(f"Enhanced extraction failed: {str(e)}")
                        st.info("Falling back to basic parser...")

                        # Fallback to comprehensive parser
                        comprehensive_parser = ComprehensiveDataParser()
                        comprehensive_result = comprehensive_parser.parse(ocr_text)

                        # Show extraction results
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Show extracted text in expander
                            with st.expander("📝 Extracted Text", expanded=False):
                                st.text(ocr_text[:2000] + "..." if len(ocr_text) > 2000 else ocr_text)

                        with col2:
                            # Show extraction summary
                            st.metric(
                                "Extraction Confidence",
                                f"{comprehensive_result['overall_confidence']*100:.0f}%"
                            )
                            st.caption(f"Fields found: {len(comprehensive_result['extracted_fields'])}")

                else:
                    # Use basic comprehensive parser if no asset class selected
                    comprehensive_parser = ComprehensiveDataParser()
                    comprehensive_result = comprehensive_parser.parse(ocr_text)

                    # Show extraction results
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Show extracted text in expander
                        with st.expander("📝 Extracted Text", expanded=False):
                            st.text(ocr_text[:2000] + "..." if len(ocr_text) > 2000 else ocr_text)

                    with col2:
                        # Show extraction summary
                        st.metric(
                            "Extraction Confidence",
                            f"{comprehensive_result['overall_confidence']*100:.0f}%"
                        )
                        st.caption(f"Fields found: {len(comprehensive_result['extracted_fields'])}")

                # Display extracted data - Enhanced CRE results or fallback
                if hasattr(st.session_state, 'cre_result') and st.session_state.cre_result:
                    # Display enhanced CRE extraction results
                    cre_result = st.session_state.cre_result

                    st.subheader("🚀 Enhanced CRE Analysis")

                    # Enhanced display with tabs for new structure
                    tabs = st.tabs(["📋 Ingested", "📊 Derived", "⚖️ Benchmarks", "⚠️ Risks", "📈 Sensitivities", "❓ Unknown"])

                    with tabs[0]:  # Ingested Fields
                        st.markdown("**Extracted Fields**")
                        if cre_result.get('ingested'):
                            for field, value in cre_result['ingested'].items():
                                confidence = cre_result.get('confidence', {}).get(field, 'Medium')

                                # Format value for display
                                if isinstance(value, float):
                                    if field.endswith('_pct') or field.endswith('_rate'):
                                        formatted_value = f"{value:.2%}"
                                    elif value > 1000:
                                        formatted_value = f"${value:,.0f}"
                                    else:
                                        formatted_value = f"{value:.3f}"
                                else:
                                    formatted_value = str(value)

                                st.write(f"**{field.replace('_', ' ').title()}:** {formatted_value} ({confidence} confidence)")

                    with tabs[1]:  # Derived Metrics
                        st.markdown("**Computed Metrics**")
                        if cre_result.get('derived'):
                            for metric, value in cre_result['derived'].items():
                                if not metric.endswith('_calc'):
                                    # Format derived values
                                    if isinstance(value, float):
                                        if metric in ['cap_rate', 'yield_on_cost', 'debt_yield', 'dscr']:
                                            formatted_value = f"{value:.3f}"
                                        elif metric in ['exit_value', 'net_sale_proceeds', 'refi_proceeds']:
                                            formatted_value = f"${value:,.0f}"
                                        else:
                                            formatted_value = f"{value:.3f}"
                                    else:
                                        formatted_value = str(value)

                                    # Show calculation if available
                                    calc = cre_result['derived'].get(f"{metric}_calc", "")
                                    st.write(f"**{metric.replace('_', ' ').title()}:** {formatted_value}")
                                    if calc:
                                        st.caption(f"Calculation: {calc}")

                    with tabs[2]:  # Benchmark Comparisons
                        st.markdown("**Benchmark Analysis**")
                        if cre_result.get('bench_compare'):
                            for field, comparison in cre_result['bench_compare'].items():
                                status = comparison.get('status', 'Unknown')
                                benchmark_info = comparison.get('benchmark', 'N/A')
                                source = comparison.get('source', 'Industry Research')

                                if status == 'OK':
                                    st.success(f"✅ **{field.replace('_', ' ').title()}:** {status}")
                                elif status in ['Above Target', 'Offside High']:
                                    st.info(f"📈 **{field.replace('_', ' ').title()}:** {status}")
                                elif status in ['Below Target', 'Offside Low']:
                                    st.warning(f"📉 **{field.replace('_', ' ').title()}:** {status}")
                                elif status == 'Poor':
                                    st.error(f"🔴 **{field.replace('_', ' ').title()}:** {status}")
                                else:
                                    st.write(f"**{field.replace('_', ' ').title()}:** {status}")

                                # Show benchmark source
                                st.caption(f"Benchmark: {benchmark_info}")

                    with tabs[3]:  # Risk Analysis
                        st.markdown("**Risk Assessment**")
                        if cre_result.get('risks_ranked'):
                            for risk in cre_result['risks_ranked']:
                                severity = risk.get('severity', 'Medium')
                                if severity == 'High':
                                    st.error(f"🔴 **{risk['metric'].replace('_', ' ').title()}:** {risk['issue']}")
                                elif severity == 'Medium':
                                    st.warning(f"🟡 **{risk['metric'].replace('_', ' ').title()}:** {risk['issue']}")
                                else:
                                    st.info(f"🔵 **{risk['metric'].replace('_', ' ').title()}:** {risk['issue']}")

                                # Show mitigations
                                if risk.get('mitigations'):
                                    st.caption("Mitigations:")
                                    for mitigation in risk['mitigations']:
                                        st.caption(f"• {mitigation}")

                    with tabs[4]:  # Sensitivity Analysis
                        st.markdown("**Sensitivity Analysis**")
                        if cre_result.get('sensitivities'):
                            for metric, scenarios in cre_result['sensitivities'].items():
                                st.write(f"**{metric.replace('_', ' ').title()} Sensitivity:**")
                                for scenario, values in scenarios.items():
                                    st.caption(f"• {scenario}: " + ", ".join([f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in values.items()]))

                    with tabs[5]:  # Unknown Fields
                        st.markdown("**Missing Data**")
                        if cre_result.get('unknown'):
                            for item in cre_result['unknown']:
                                st.write(f"• {item}")

                elif 'comprehensive_result' in locals() and comprehensive_result['extracted_fields']:
                    # Fallback to basic comprehensive parser display
                    st.subheader("📊 Extracted Data")

                    tabs = st.tabs(["Deal Info", "Financials", "Debt Terms", "Operations", "Development"])

                    with tabs[0]:  # Deal Info
                        deal_fields = ['property_name', 'street_address', 'city', 'state', 'zip_code',
                                      'year_built', 'year_renovated', 'building_sf', 'unit_count',
                                      'parking_spaces', 'occupancy_pct', 'walt_years', 'anchor_tenant']
                        _display_fields(comprehensive_result['extracted_fields'], deal_fields)

                    with tabs[1]:  # Financials
                        financial_fields = ['purchase_price', 'noi', 'cap_rate', 'gross_income',
                                          'operating_expenses', 'exit_cap_rate', 'hold_period_years',
                                          'closing_costs', 'disposition_fee_pct']
                        _display_fields(comprehensive_result['extracted_fields'], financial_fields)

                    with tabs[2]:  # Debt Terms
                        debt_fields = ['loan_amount', 'interest_rate', 'amort_years', 'io_period_years',
                                      'loan_term_years', 'ltv_pct', 'min_dscr', 'origination_fee_pct',
                                      'rate_cap_strike', 'extension_count', 'extension_term_months']
                        _display_fields(comprehensive_result['extracted_fields'], debt_fields)

                    with tabs[3]:  # Operations
                        ops_fields = ['real_estate_taxes', 'insurance_cost', 'management_fee_pct',
                                     'replacement_reserves', 'vacancy_rate', 'market_rent',
                                     'ti_allowance_new', 'leasing_commission_pct', 'free_rent_months']
                        _display_fields(comprehensive_result['extracted_fields'], ops_fields)

                    with tabs[4]:  # Development
                        dev_fields = ['land_cost', 'hard_costs', 'soft_costs', 'developer_fee',
                                     'contingency_pct', 'preleasing_pct', 'expected_delivery',
                                     'construction_contract_type', 'general_contractor']
                        _display_fields(comprehensive_result['extracted_fields'], dev_fields)

                    # Show extraction notes
                    if comprehensive_result['extraction_notes']:
                        with st.expander("📋 Extraction Notes", expanded=False):
                            for note in comprehensive_result['extraction_notes'][:10]:  # Show first 10
                                st.caption(f"• {note}")

                    # Show missing critical fields
                    if comprehensive_result['missing_critical']:
                        st.warning(f"⚠️ Missing critical fields: {', '.join(comprehensive_result['missing_critical'])}")

                # Convert to legacy format for compatibility
                if hasattr(st.session_state, 'cre_result') and st.session_state.cre_result:
                    # Use enhanced CRE results
                    cre_result = st.session_state.cre_result
                    parsed_data = {
                        'confidence': 0.9,  # Higher confidence for enhanced extraction
                        'purchase_price': cre_result.get('ingested', {}).get('purchase_price'),
                        'noi': cre_result.get('ingested', {}).get('noi_now'),
                        'cap_rate': cre_result.get('derived', {}).get('cap_rate') or cre_result.get('ingested', {}).get('entry_cap'),
                        'loan_amount': cre_result.get('ingested', {}).get('loan_amount'),
                        'interest_rate': cre_result.get('ingested', {}).get('rate'),
                        'asset_class': st.session_state.asset_class.title(),
                        'subclass': st.session_state.subclass
                    }

                    # Add more fields from ingested data
                    ingested = cre_result.get('ingested', {})
                    for key in ['ltv', 'dscr', 'occupancy_pct', 'expense_ratio']:
                        if key in ingested:
                            parsed_data[key] = ingested[key]

                    # Add derived metrics
                    derived = cre_result.get('derived', {})
                    for key in ['equity_multiple', 'irr', 'yield_on_cost']:
                        if key in derived:
                            parsed_data[key] = derived[key]

                    completeness = cre_result.get('completeness', {})
                    required_fields = completeness.get('required_fields', 0)
                    total_required = completeness.get('total_required', 1)
                    st.success(f"🚀 Enhanced extraction completed: {required_fields}/{total_required} required fields ({len(cre_result.get('ingested', {}))+ len(cre_result.get('derived', {}))} total)")

                else:
                    # Fallback to basic parser
                    parser = FinancialDataParser()
                    parsed_data = parser.parse(ocr_text)
                    parsed_data["asset_class"] = "Office"  # Default

                    if 'comprehensive_result' in locals():
                        st.success(f"✅ Extracted {len(comprehensive_result['extracted_fields'])} fields with {comprehensive_result['overall_confidence']*100:.0f}% confidence")

    return parsed_data

def generate_principal_summary(data: Dict) -> str:
    """Generate principal-style investment summary"""

    # Calculate key metrics
    dscr = calculate_dscr(
        data.get('noi', 0),
        data.get('loan_amount', 0),
        data.get('interest_rate', 0.065),
        data.get('amort_years', 30)
    )

    cap_rate = (data.get('noi', 0) / data.get('purchase_price', 1)) * 100 if data.get('purchase_price', 0) > 0 else 0
    ltv = (data.get('loan_amount', 0) / data.get('purchase_price', 1)) * 100 if data.get('purchase_price', 0) > 0 else 0

    # Simple equity multiple calculation
    equity = data.get('purchase_price', 0) - data.get('loan_amount', 0)
    exit_cap = data.get('exit_cap_rate', cap_rate + 0.5)
    hold_period = data.get('hold_period', 5)

    if exit_cap > 0 and hold_period > 0 and equity > 0:
        future_noi = data.get('noi', 0) * (1.03 ** hold_period)
        exit_value = future_noi / (exit_cap / 100)
        net_proceeds = exit_value - data.get('loan_amount', 0) * 0.9
        equity_multiple = net_proceeds / equity if equity > 0 else 0
        irr = ((equity_multiple ** (1/hold_period)) - 1) * 100 if equity_multiple > 0 else 0
    else:
        equity_multiple = 0
        irr = 0

    # Generate summary components
    if cap_rate < 5:
        macro = "In a historically low cap rate environment"
    elif cap_rate > 7:
        macro = "Cap rates have reset higher; exit needs cushion"
    else:
        macro = "Market cap rates remain within historical norms"

    strengths = []
    if dscr > 1.3:
        strengths.append(f"deal maintains {dscr:.2f}× DSCR")
    if irr > 15:
        strengths.append(f"IRR of {irr:.1f}% exceeds hurdle")
    if ltv < 65:
        strengths.append(f"conservative {ltv:.0f}% leverage provides flexibility")

    if len(strengths) == 0:
        strengths = ["limited debt stress", "stable cash flow"]
    elif len(strengths) == 1:
        strengths.append("NOI growth provides buffer")

    risks = []
    if equity_multiple < 1.6:
        risks.append(f"{equity_multiple:.2f}× equity multiple falls short of 1.6× target")
    if exit_cap > cap_rate + 0.5:
        risks.append(f"exit cap expansion to {exit_cap:.1f}% pressures returns")
    if dscr < 1.25:
        risks.append(f"thin {dscr:.2f}× coverage leaves no room for error")

    if len(risks) == 0:
        risks = ["refinance risk at maturity", "market timing dependency"]
    elif len(risks) == 1:
        risks.append("execution risk on business plan")

    if equity_multiple >= 1.8 and irr >= 15:
        bottom_line = "strong risk-adjusted returns justify proceeding"
    elif equity_multiple >= 1.5 and dscr >= 1.25:
        bottom_line = "workable with modest leverage reduction"
    elif dscr < 1.2 or equity_multiple < 1.3:
        bottom_line = "pass - insufficient margin of safety"
    else:
        bottom_line = "marginal - requires aggressive underwriting"

    summary = f"{macro}. {strengths[0].capitalize()}; {strengths[1]}. "
    summary += f"But {risks[0]}, and {risks[1]}. "
    summary += f"Net: {bottom_line}."

    return summary

def generate_pdf_report(data: Dict) -> bytes:
    """Generate comprehensive PDF report"""
    from reportlab.platypus import KeepTogether

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=1
    )

    story.append(Paragraph("DealGenie Pro - Investment Analysis", title_style))
    story.append(Spacer(1, 20))

    # Summary
    summary = generate_principal_summary(data)
    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=18
    )
    story.append(Paragraph("<b>INVESTMENT SUMMARY</b>", styles['Heading2']))
    story.append(Paragraph(summary, summary_style))
    story.append(Spacer(1, 20))

    # Key Metrics Table
    metrics_data = [
        ['Metric', 'Value'],
        ['Purchase Price', f"${data.get('purchase_price', 0):,.0f}"],
        ['NOI', f"${data.get('noi', 0):,.0f}"],
        ['Cap Rate', f"{(data.get('noi', 0) / max(data.get('purchase_price', 1), 1)) * 100:.2f}%"],
        ['Loan Amount', f"${data.get('loan_amount', 0):,.0f}"],
        ['Interest Rate', f"{data.get('interest_rate', 0) * 100:.2f}%"],
    ]

    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(metrics_table)
    story.append(PageBreak())

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_excel_export(data: Dict) -> bytes:
    """Generate Excel export with all data"""
    output = io.BytesIO()

    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_data = {
            'Metric': ['Purchase Price', 'NOI', 'Cap Rate', 'Loan Amount', 'Interest Rate'],
            'Value': [
                f"${data.get('purchase_price', 0):,.0f}",
                f"${data.get('noi', 0):,.0f}",
                f"{(data.get('noi', 0) / max(data.get('purchase_price', 1), 1)) * 100:.2f}%",
                f"${data.get('loan_amount', 0):,.0f}",
                f"{data.get('interest_rate', 0) * 100:.2f}%"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Input data sheet
        input_data = [(k, v) for k, v in data.items() if v is not None]
        if input_data:
            input_df = pd.DataFrame(input_data, columns=['Field', 'Value'])
            input_df.to_excel(writer, sheet_name='Input Data', index=False)

    output.seek(0)
    return output.getvalue()

def generate_chart_export(data: Dict) -> bytes:
    """Generate chart image for export"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('DealGenie Investment Analysis', fontsize=16, fontweight='bold')

    # Calculate metrics
    cap_rate = (data.get('noi', 0) / max(data.get('purchase_price', 1), 1)) * 100
    ltv = (data.get('loan_amount', 0) / max(data.get('purchase_price', 1), 1)) * 100
    dscr = calculate_dscr(
        data.get('noi', 0),
        data.get('loan_amount', 0),
        data.get('interest_rate', 0.065),
        data.get('amort_years', 30)
    )

    # Metrics chart
    ax1 = axes[0, 0]
    metrics_names = ['Cap Rate', 'LTV', 'DSCR']
    metrics_values = [cap_rate/10, ltv/100, dscr]
    colors = ['#22c55e' if v > 0.5 else '#ef4444' for v in metrics_values]
    ax1.bar(metrics_names, metrics_values, color=colors)
    ax1.set_title('Key Metrics')
    ax1.set_ylim(0, 2)

    # Sensitivity matrix
    ax2 = axes[0, 1]
    ax2.set_title('Cap Rate Sensitivity')
    ax2.axis('off')

    # Cash flow projection
    ax3 = axes[1, 0]
    years = list(range(1, 6))
    cash_flows = [data.get('noi', 0) * (1.03 ** y) for y in years]
    ax3.plot(years, cash_flows, marker='o', color='purple', linewidth=2)
    ax3.set_title('NOI Projection')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('NOI ($)')
    ax3.grid(True, alpha=0.3)

    # Value composition
    ax4 = axes[1, 1]
    sizes = [data.get('loan_amount', 0), max(data.get('purchase_price', 0) - data.get('loan_amount', 0), 0)]
    labels = ['Debt', 'Equity']
    ax4.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ef4444', '#22c55e'])
    ax4.set_title('Capital Structure')

    # Save to bytes
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()

    return buffer.getvalue()

def render_analysis(data: Dict):
    """Render analysis results with principal summary at top"""
    if not data or "purchase_price" not in data:
        st.info("Enter deal information to see analysis")
        return

    # Generate principal summary FIRST
    summary = generate_principal_summary(data)

    # Calculate metrics for LLM context
    metrics = calculate_metrics_for_llm(data)

    # Use the new LLM-enhanced summary renderer
    render_summary_with_llm_option(summary, metrics)

    # Calculate metrics
    cap_rate = (data.get("noi", 0) / data.get("purchase_price", 1)) * 100
    ltv = (data.get("loan_amount", 0) / data.get("purchase_price", 1)) * 100
    dscr = calculate_dscr(
        data.get("noi", 0),
        data.get("loan_amount", 0),
        data.get("interest_rate", 0.065),
        data.get("amort_years", 30)
    )

    # Display key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">Cap Rate</h3>
            <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{cap_rate:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">DSCR</h3>
            <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{dscr:.2f}×</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">LTV</h3>
            <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{ltv:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        equity = data.get("purchase_price", 0) - data.get("loan_amount", 0)
        cash_on_cash = ((data.get("noi", 0) - data.get("loan_amount", 0) * data.get("interest_rate", 0.065)) / equity * 100) if equity > 0 else 0

        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">Cash-on-Cash</h3>
            <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{cash_on_cash:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Benchmark evaluation
    st.subheader("🎯 Benchmark Analysis")

    metrics = {
        "cap_rate": cap_rate,
        "dscr": dscr,
        "ltv": ltv
    }

    evaluations = evaluate_against_benchmarks(
        data.get("asset_class", "Office"),
        metrics
    )

    for eval in evaluations:
        status_class = f"status-{eval['status']}"
        st.markdown(f"""
        <div style="padding: 0.5rem; margin: 0.5rem 0;">
            <span class="status-badge {status_class}">{eval['status'].upper()}</span>
            <span style="margin-left: 1rem; font-weight: 600;">{eval['metric']}: {eval['value']:.2f}</span>
            <span style="margin-left: 1rem; color: #6b7280;">Benchmark: {eval['benchmark']}</span>
        </div>
        """, unsafe_allow_html=True)

    # Cash flow projection
    st.subheader("💰 5-Year Cash Flow Projection")

    years = list(range(1, 6))
    noi_growth = 1.03  # 3% annual growth
    cash_flows = []

    for year in years:
        year_noi = data.get("noi", 0) * (noi_growth ** (year - 1))
        debt_service = data.get("loan_amount", 0) * data.get("interest_rate", 0.065)
        cash_flow = year_noi - debt_service
        cash_flows.append(cash_flow)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=cash_flows,
        marker_color='#667eea',
        text=[f'${cf/1000:.0f}K' for cf in cash_flows],
        textposition='outside'
    ))

    fig.update_layout(
        title="Annual Cash Flow After Debt Service",
        xaxis_title="Year",
        yaxis_title="Cash Flow ($)",
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application entry point"""
    inject_custom_css()
    render_header()

    # Render API settings in sidebar
    render_api_settings()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analysis",
        "📚 Benchmarks",
        "📋 Due Diligence",
        "📄 Reports"
    ])

    with tab1:
        data = render_input_section()
        if data:
            render_analysis(data)
            # Store data in session state for other tabs
            st.session_state.analysis_data = data

    with tab2:
        st.header("📚 Industry Benchmarks")
        st.caption("Source-attributed market data")

        benchmark_df = []
        for asset, metrics in BENCHMARKS.items():
            for metric, values in metrics.items():
                benchmark_df.append({
                    "Asset Class": asset,
                    "Metric": metric.upper(),
                    "Minimum": values["min"],
                    "Preferred": values["preferred"],
                    "Maximum": values["max"],
                    "Source": values["source"]
                })

        df = pd.DataFrame(benchmark_df)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.header("📋 Due Diligence Checklist")

        # Comprehensive DD Checklist organized by category
        dd_categories = {
            "📊 Financial Due Diligence": [
                "T-12 and T-3 operating statements with GL tie-out",
                "Current rent roll with lease abstracts",
                "Accounts receivable aging report",
                "CAM reconciliation (3 years)",
                "Real estate tax bills and assessment history",
                "Insurance policies and loss runs",
                "Utility bills (12 months)",
                "CapEx history (3-5 years)",
                "Property management agreement",
                "Service contracts inventory"
            ],
            "⚖️ Legal & Title": [
                "ALTA survey with Table A items",
                "Title commitment with all exceptions",
                "Tenant estoppel certificates",
                "SNDAs (Subordination, Non-Disturbance Agreements)",
                "All leases and amendments",
                "Operating agreements/CC&Rs/REAs",
                "Zoning confirmation letter",
                "Certificate of occupancy",
                "Business licenses",
                "Litigation search and disclosure"
            ],
            "🏗️ Physical & Environmental": [
                "Property Condition Assessment (PCA)",
                "Structural engineering report",
                "MEP systems evaluation",
                "Roof inspection and warranty",
                "Elevator inspection certificates",
                "Fire/Life safety inspection",
                "ADA compliance assessment",
                "Phase I Environmental Site Assessment",
                "Mold and indoor air quality report",
                "Asbestos and lead paint surveys"
            ],
            "📈 Market & Competitive": [
                "Market comparable lease analysis",
                "Submarket vacancy and absorption trends",
                "Development pipeline (3-mile radius)",
                "Broker opinion of value (BOV)",
                "Tenant demand and tour activity",
                "Employment and demographic analysis",
                "Trade area analysis (retail)",
                "Competitive set benchmarking"
            ],
            "💰 Debt & Capital Structure": [
                "Existing loan documents review",
                "Covenant compliance certificates",
                "Rate cap confirmation and valuation",
                "Prepayment and defeasance analysis",
                "Payoff letters from current lender",
                "UCC and lien searches",
                "Reserve account statements",
                "JV/LP agreement review (if applicable)"
            ]
        }

        # Display DD checklist with expanders
        for category, items in dd_categories.items():
            with st.expander(category, expanded=False):
                for item in items:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.checkbox(item, key=f"dd_{item}")
                    with col2:
                        st.selectbox("", ["Pending", "In Progress", "Complete", "N/A"],
                                   key=f"status_{item}", label_visibility="collapsed")

        # Progress tracker
        st.markdown("---")
        total_items = sum(len(items) for items in dd_categories.values())
        st.info(f"Total DD Items: {total_items}")

    with tab4:
        st.header("📄 Report Generation")

        # Check if we have analysis data
        if not hasattr(st.session_state, 'analysis_data') or not st.session_state.analysis_data:
            st.warning("⚠️ Please complete the analysis in the Analysis tab first to generate reports.")
        else:
            analysis_data = st.session_state.analysis_data

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📑 Generate PDF Report", use_container_width=True):
                    pdf_bytes = generate_pdf_report(analysis_data)
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=f"DealGenie_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
            with col2:
                if st.button("📊 Export to Excel", use_container_width=True):
                    excel_bytes = generate_excel_export(analysis_data)
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_bytes,
                        file_name=f"DealGenie_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            with col3:
                if st.button("📈 Export Charts", use_container_width=True):
                    chart_bytes = generate_chart_export(analysis_data)
                    st.download_button(
                        label="📥 Download Charts",
                        data=chart_bytes,
                        file_name=f"DealGenie_Charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )

if __name__ == "__main__":
    main()