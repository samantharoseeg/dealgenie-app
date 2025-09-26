"""
LLM Summary Enhancement Module for DealGenie Pro
Optional AI-powered summary polishing using Claude or OpenAI
"""

import streamlit as st
import json
import requests
from typing import Dict, Optional
import anthropic
from openai import OpenAI
from datetime import datetime

def get_api_settings():
    """Get API settings from Streamlit session state"""
    if 'api_provider' not in st.session_state:
        st.session_state.api_provider = None
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

    return st.session_state.api_provider, st.session_state.api_key

def render_api_settings():
    """Render API settings in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔑 API Settings")

        # API Provider selection
        provider = st.selectbox(
            "LLM Provider",
            ["None", "Claude (Anthropic)", "OpenAI GPT-4"],
            help="Select your LLM provider for AI-enhanced summaries"
        )

        if provider != "None":
            # API Key input
            api_key = st.text_input(
                f"{provider.split()[0]} API Key",
                type="password",
                help="Your API key is stored only in this session",
                placeholder="sk-..." if "OpenAI" in provider else "sk-ant-..."
            )

            if api_key:
                st.session_state.api_provider = provider
                st.session_state.api_key = api_key
                st.success("✅ API key configured")
            else:
                st.session_state.api_provider = None
                st.session_state.api_key = None

            # Usage note
            st.caption(f"💰 Cost: ~$0.001 per summary")
            st.caption("🔒 Your key is never stored permanently")
        else:
            st.session_state.api_provider = None
            st.session_state.api_key = None

def polish_summary_with_llm(
    rule_based_summary: str,
    metrics: Dict,
    provider: str,
    api_key: str
) -> Optional[str]:
    """
    Polish the rule-based summary using LLM

    Args:
        rule_based_summary: The original rule-based summary
        metrics: Dictionary of deal metrics
        provider: "Claude (Anthropic)" or "OpenAI GPT-4"
        api_key: User's API key

    Returns:
        Polished summary or None if error
    """

    # Prepare the prompt
    prompt = f"""Rewrite this CRE deal summary in a principal-style tone. Use the provided metrics. Keep it 2-3 sentences. Be decisive and investor-grade:

Rule-based summary: {rule_based_summary}

Deal metrics:
- DSCR: {metrics.get('dscr', 0):.2f}x
- Equity Multiple: {metrics.get('equity_multiple', 0):.2f}x
- IRR: {metrics.get('irr', 0):.1f}%
- Cap Rate: {metrics.get('cap_rate', 0):.2f}%
- Exit Cap: {metrics.get('exit_cap_rate', 0):.2f}%
- LTV: {metrics.get('ltv', 0):.1f}%

Output only the polished summary, no explanations."""

    try:
        if "Claude" in provider:
            return polish_with_claude(prompt, api_key)
        elif "OpenAI" in provider:
            return polish_with_openai(prompt, api_key)
    except Exception as e:
        st.error(f"LLM API Error: {str(e)}")
        return None

def polish_with_claude(prompt: str, api_key: str) -> Optional[str]:
    """Polish summary using Claude API"""
    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
            max_tokens=200,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text.strip()

    except Exception as e:
        raise Exception(f"Claude API error: {str(e)}")

def polish_with_openai(prompt: str, api_key: str) -> Optional[str]:
    """Polish summary using OpenAI API"""
    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for cost efficiency
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior principal at a leading CRE investment firm. Write concise, decisive investment summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

def render_summary_with_llm_option(rule_based_summary: str, metrics: Dict):
    """
    Render summary section with optional LLM enhancement

    Args:
        rule_based_summary: The original rule-based summary
        metrics: Dictionary of deal metrics
    """

    # Get API settings
    provider, api_key = get_api_settings()

    # Initialize session state for polished summary
    if 'polished_summary' not in st.session_state:
        st.session_state.polished_summary = None
    if 'show_comparison' not in st.session_state:
        st.session_state.show_comparison = False

    # Main summary display
    st.markdown("---")

    # Container for summary and polish button
    col1, col2 = st.columns([5, 1])

    with col1:
        st.markdown("""
        <h2 style="margin: 0; font-size: 1.8rem;">
            📋 Investment Summary
        </h2>
        """, unsafe_allow_html=True)

    with col2:
        if provider and api_key:
            if st.button("✨ Polish with AI", help=f"Enhance with {provider.split()[0]} (~$0.001)"):
                with st.spinner("Polishing summary..."):
                    polished = polish_summary_with_llm(
                        rule_based_summary,
                        metrics,
                        provider,
                        api_key
                    )
                    if polished:
                        st.session_state.polished_summary = polished
                        st.session_state.show_comparison = True
                        st.rerun()
        else:
            st.caption("Configure API key in sidebar to enable AI polish")

    # Display summaries
    if st.session_state.show_comparison and st.session_state.polished_summary:
        # Show comparison view
        tab1, tab2 = st.tabs(["🤖 AI-Polished", "📝 Rule-Based"])

        with tab1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 2rem;
                        border-radius: 12px;
                        color: white;
                        margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <span style="background: rgba(255,255,255,0.2);
                                padding: 0.25rem 0.75rem;
                                border-radius: 20px;
                                font-size: 0.9rem;">
                        ✨ AI-Enhanced ({provider.split()[0]})
                    </span>
                    <span style="font-size: 0.8rem; opacity: 0.8;">
                        {datetime.now().strftime('%I:%M %p')}
                    </span>
                </div>
                <p style="font-size: 1.1rem; line-height: 1.8; margin: 0;">
                    {st.session_state.polished_summary}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Option to clear comparison
            if st.button("Clear comparison", key="clear_ai"):
                st.session_state.show_comparison = False
                st.rerun()

        with tab2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
                        padding: 2rem;
                        border-radius: 12px;
                        color: white;
                        margin: 1rem 0;">
                <div style="margin-bottom: 1rem;">
                    <span style="background: rgba(255,255,255,0.2);
                                padding: 0.25rem 0.75rem;
                                border-radius: 20px;
                                font-size: 0.9rem;">
                        📝 Rule-Based (Instant, Free)
                    </span>
                </div>
                <p style="font-size: 1.1rem; line-height: 1.8; margin: 0;">
                    {rule_based_summary}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Show only rule-based summary
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 12px;
                    color: white;
                    margin: 1rem 0;">
            <div style="margin-bottom: 1rem;">
                <span style="background: rgba(255,255,255,0.2);
                            padding: 0.25rem 0.75rem;
                            border-radius: 20px;
                            font-size: 0.9rem;">
                    📝 Rule-Based Summary (Instant, Free)
                </span>
            </div>
            <p style="font-size: 1.1rem; line-height: 1.8; margin: 0;">
                {rule_based_summary}
            </p>
        </div>
        """, unsafe_allow_html=True)

def calculate_metrics_for_llm(data: Dict) -> Dict:
    """Calculate all metrics needed for LLM context"""

    # Basic metrics
    purchase_price = data.get('purchase_price', 0)
    noi = data.get('noi', 0)
    loan_amount = data.get('loan_amount', 0)
    interest_rate = data.get('interest_rate', 0.065)
    amort_years = data.get('amort_years', 30)

    metrics = {}

    # Cap rate
    if purchase_price > 0:
        metrics['cap_rate'] = (noi / purchase_price) * 100
    else:
        metrics['cap_rate'] = 0

    # LTV
    if purchase_price > 0:
        metrics['ltv'] = (loan_amount / purchase_price) * 100
    else:
        metrics['ltv'] = 0

    # DSCR calculation
    if loan_amount > 0 and interest_rate > 0:
        if amort_years == 0:  # Interest only
            annual_debt_service = loan_amount * interest_rate
        else:
            monthly_rate = interest_rate / 12
            n_payments = amort_years * 12
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                annual_debt_service = monthly_payment * 12
            else:
                annual_debt_service = loan_amount / amort_years

        metrics['dscr'] = noi / annual_debt_service if annual_debt_service > 0 else 0
    else:
        metrics['dscr'] = 0

    # Equity multiple and IRR estimates
    equity = purchase_price - loan_amount
    exit_cap = data.get('exit_cap_rate', metrics['cap_rate'] + 0.5)
    hold_period = data.get('hold_period', 5)

    if exit_cap > 0 and hold_period > 0 and equity > 0:
        future_noi = noi * (1.03 ** hold_period)
        exit_value = future_noi / (exit_cap / 100)
        remaining_balance = loan_amount * 0.9
        net_proceeds = exit_value - remaining_balance

        metrics['equity_multiple'] = net_proceeds / equity if equity > 0 else 0
        metrics['irr'] = ((metrics['equity_multiple'] ** (1/hold_period)) - 1) * 100 if metrics['equity_multiple'] > 0 else 0
    else:
        metrics['equity_multiple'] = 0
        metrics['irr'] = 0

    metrics['exit_cap_rate'] = exit_cap

    return metrics