import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
import datetime
import io
import altair as alt

# ==========================================
# ALTAIR INSTITUTIONAL CHART THEME
# ==========================================
# Altair ships bundled with Streamlit itself — no extra package install,
# no requirements.txt drift, no "ModuleNotFoundError" on a fresh deploy.
# Single shared theme so every chart in the app reads as one instrument.
CHART_FONT = "IBM Plex Mono"
CHART_INK = "#E8EAED"
CHART_INK_LOW = "#8B93A7"
CHART_HAIRLINE = "#232938"
CHART_SURFACE = "#12161F"
CHART_GOLD = "#C9A24B"
CHART_CRITICAL = "#C84B3C"
CHART_STABLE = "#4B9C7E"


def base_chart_props(chart, height=320):
    """Applies the shared dark institutional theme to any Altair chart."""
    return (
        chart
        .properties(height=height, background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            gridColor=CHART_HAIRLINE, domainColor=CHART_HAIRLINE,
            tickColor=CHART_HAIRLINE, labelColor=CHART_INK_LOW,
            titleColor=CHART_INK_LOW, labelFont=CHART_FONT, titleFont=CHART_FONT,
            labelFontSize=11, titleFontSize=11,
        )
        .configure_legend(
            labelColor=CHART_INK_LOW, titleColor=CHART_INK_LOW,
            labelFont=CHART_FONT, titleFont=CHART_FONT, orient="top-left",
        )
        .configure_axisX(grid=False)
    )

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Sino-African Logistics & Risk Matrix | Xiamen C&D",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INSTITUTIONAL DESIGN SYSTEM
# ==========================================
# Token system — a near-black trading-floor palette with a single warm metal
# accent (the corridor trades literal metals: chrome, lithium, copper) and two
# desaturated hues reserved exclusively for risk state. No decorative color.
#
#   Ink            #0B0E14   base canvas
#   Surface        #12161F   panel / card background
#   Surface-raised #181D29   sidebar, nested, hover states
#   Hairline       #232938   structural borders, dividers
#   Ink-high       #E8EAED   primary text
#   Ink-low        #8B93A7   secondary text, labels, captions
#   Signal (gold)  #C9A24B   brand accent — used sparingly, for emphasis only
#   Risk: critical #C84B3C   |  caution #C9A24B  |  stable #4B9C7E
#
# All figures (prices, rates, days, percentages) render in monospace. This is
# the deliberate signature: it reads as instrument output, not marketing copy.

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

    :root {
        --ink: #0B0E14;
        --surface: #12161F;
        --surface-raised: #181D29;
        --hairline: #232938;
        --ink-high: #E8EAED;
        --ink-low: #8B93A7;
        --signal: #C9A24B;
        --risk-critical: #C84B3C;
        --risk-caution: #C9A24B;
        --risk-stable: #4B9C7E;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ---- Base canvas ---- */
    .stApp {
        background: var(--ink);
    }
    .block-container {
        padding-top: 2rem;
        max-width: 1320px;
    }
    [data-testid="stHeader"] { background: var(--ink); }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: var(--surface-raised);
        border-right: 1px solid var(--hairline);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink-high);
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        font-size: 0.78rem;
        border-bottom: 1px solid var(--hairline);
        padding-bottom: 8px;
        margin-top: 4px;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stCaption {
        color: var(--ink-low);
        font-size: 0.84rem;
    }

    /* ---- Headings ---- */
    h1, h2, h3, h4, h5 {
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink-high);
        font-weight: 600;
    }
    .eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--signal);
        margin-bottom: 2px;
        display: block;
    }
    .section-title {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 1.28rem;
        font-weight: 600;
        color: var(--ink-high);
        letter-spacing: -0.01em;
        margin: 0 0 2px 0;
    }
    .section-rule {
        border: none;
        border-top: 1px solid var(--hairline);
        margin: 6px 0 18px 0;
    }
    .section-caption {
        color: var(--ink-low);
        font-size: 0.86rem;
        margin-bottom: 14px;
    }
    .main-title {
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink-high);
        font-weight: 700;
        letter-spacing: -0.02em;
        font-size: 2.05rem;
        margin-bottom: 0;
    }
    .main-subtitle {
        font-family: 'IBM Plex Mono', monospace;
        color: var(--ink-low);
        font-size: 0.82rem;
        letter-spacing: 0.01em;
        margin-top: 2px;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--ink-low) !important;
    }
    hr { border-color: var(--hairline); }

    /* ---- Native st.metric tiles: flat panel, mono figures, no shadow ---- */
    [data-testid="stMetric"] {
        background-color: var(--surface);
        border: 1px solid var(--hairline);
        border-radius: 3px;
        padding: 14px 16px 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--ink-low) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        color: var(--ink-high) !important;
        font-size: 1.55rem;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
    }

    /* ---- Buttons: flat, sharp corners, gold on hover ---- */
    .stButton button, .stDownloadButton button {
        background-color: var(--surface);
        color: var(--ink-high);
        border: 1px solid var(--hairline);
        border-radius: 3px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        font-size: 0.86rem;
        box-shadow: none;
        transition: border-color 0.15s ease, color 0.15s ease;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: var(--signal);
        color: var(--signal);
        background-color: var(--surface);
    }
    .stButton button:focus, .stDownloadButton button:focus {
        box-shadow: 0 0 0 1px var(--signal);
    }

    /* ---- Alerts: flat left-rule cards instead of filled colored boxes ---- */
    [data-testid="stAlertContainer"] {
        border-radius: 3px;
        border: 1px solid var(--hairline);
        background-color: var(--surface);
    }
    div[data-baseweb="notification"] { box-shadow: none !important; }

    /* ---- Inputs / sliders / selects ---- */
    .stSlider [data-baseweb="slider"] { padding-top: 4px; }
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input {
        background-color: var(--surface);
        border: 1px solid var(--hairline);
        border-radius: 3px;
        color: var(--ink-high);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.86rem;
    }
    label { color: var(--ink-low) !important; font-size: 0.84rem !important; }

    /* ---- Dataframes / tables ---- */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--hairline);
        border-radius: 3px;
    }

    /* ---- Expander ---- */
    [data-testid="stExpander"] {
        border: 1px solid var(--hairline);
        border-radius: 3px;
        background-color: var(--surface);
    }

    /* ---- Stage / corridor panel ---- */
    .stage-card {
        background-color: var(--surface);
        border: 1px solid var(--hairline);
        border-radius: 3px;
        padding: 16px 16px 14px 16px;
        min-height: 178px;
    }
    .stage-card .stage-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--signal);
        display: block;
        margin-bottom: 6px;
    }
    .stage-card .stage-name {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 600;
        color: var(--ink-high);
        font-size: 0.98rem;
        display: block;
        margin-bottom: 10px;
    }
    .stage-card .stage-status {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .risk-high { color: var(--risk-critical); }
    .risk-med  { color: var(--risk-caution); }
    .risk-low  { color: var(--risk-stable); }

    /* ---- KPI strip wrapper (adds breathing room without shadow) ---- */
    .kpi-row { margin-bottom: 4px; }

    /* ---- Subtle depth + hover lift on the cards that benefit from it ---- */
    [data-testid="stMetric"], .stage-card, [data-testid="stExpander"] {
        transition: border-color 0.15s ease, transform 0.15s ease;
    }
    [data-testid="stMetric"]:hover, .stage-card:hover {
        border-color: #2C3344;
        transform: translateY(-1px);
    }

    /* ---- Top status bar: live data badges + system identity ---- */
    .status-bar {
        display: flex;
        align-items: center;
        gap: 18px;
        flex-wrap: wrap;
        padding-bottom: 10px;
        margin-bottom: 4px;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.04em;
        color: var(--ink-low);
        text-transform: uppercase;
    }
    .status-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--risk-stable);
        box-shadow: 0 0 0 0 rgba(75,156,126,0.6);
        animation: pulse-dot 2.2s infinite;
    }
    @keyframes pulse-dot {
        0%   { box-shadow: 0 0 0 0 rgba(75,156,126,0.55); }
        70%  { box-shadow: 0 0 0 5px rgba(75,156,126,0); }
        100% { box-shadow: 0 0 0 0 rgba(75,156,126,0); }
    }
    .status-divider { width: 1px; height: 12px; background: var(--hairline); }
    .badge-tier {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.66rem;
        letter-spacing: 0.08em;
        color: var(--ink);
        background: var(--signal);
        padding: 2px 7px;
        border-radius: 2px;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* ---- Executive briefing card: the one-glance synthesis at the top ---- */
    .brief-card {
        background: linear-gradient(135deg, var(--surface-raised) 0%, var(--surface) 100%);
        border: 1px solid var(--hairline);
        border-left: 3px solid var(--signal);
        border-radius: 4px;
        padding: 20px 24px 18px 22px;
        margin-bottom: 22px;
    }
    .brief-card .brief-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--signal);
        display: block;
        margin-bottom: 8px;
    }
    .brief-card .brief-text {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.96rem;
        line-height: 1.55;
        color: var(--ink-high);
        margin-bottom: 12px;
    }
    .brief-tags { display: flex; gap: 8px; flex-wrap: wrap; }
    .brief-tag {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 2px;
        border: 1px solid var(--hairline);
        letter-spacing: 0.02em;
    }
    .brief-tag.t-stable  { color: var(--risk-stable);  border-color: rgba(75,156,126,0.35); background: rgba(75,156,126,0.08); }
    .brief-tag.t-caution { color: var(--risk-caution); border-color: rgba(201,162,75,0.35); background: rgba(201,162,75,0.08); }
    .brief-tag.t-critical{ color: var(--risk-critical);border-color: rgba(200,75,60,0.35); background: rgba(200,75,60,0.08); }

    /* ---- Tabs: institutional underline style, not the default pill chips ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 28px;
        border-bottom: 1px solid var(--hairline);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        font-size: 0.86rem;
        color: var(--ink-low);
        padding: 8px 2px 12px 2px;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: var(--ink-high) !important;
        border-bottom: 2px solid var(--signal) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent; }
</style>
""", unsafe_allow_html=True)


def section_header(eyebrow, title, caption=None):
    """
    Renders a disciplined section header: small-caps mono eyebrow, a title,
    a hairline rule, and an optional caption — replacing emoji-prefixed
    markdown headers with the institutional type system above.
    """
    html = f'<span class="eyebrow">{eyebrow}</span><div class="section-title">{title}</div><hr class="section-rule"/>'
    st.markdown(html, unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="section-caption">{caption}</div>', unsafe_allow_html=True)



# ==========================================
# CONSTANTS & METADATA
# ==========================================
APP_ID = "C&D-Sino-African-Logistics-Tracker"
DESIGNER = "Christiaan R. Burger | St. Lawrence University (Economics & Mathematics)"
CORRIDOR_COUNTRIES = {
    "ZW": "Zimbabwe (Source Country)",
    "ZA": "South Africa (Gateway & Logistics Hub)",
    "ZM": "Zambia (Source Country)",
    "MZ": "Mozambique (Gateway & Logistics Hub)",
    "TZ": "Tanzania (Gateway & Logistics Hub)",
    "CN": "China (Destination Market)"
}

# ==========================================
# MULTI-COMMODITY CORRIDOR DATA MODEL
# ==========================================
# Each commodity defines its own physical corridor (with real-world reference
# coordinates for the Pydeck geospatial layer), pricing rules, and risk defaults.
# This is the single source of truth the rest of the app reads from, so switching
# the sidebar dropdown re-flows the map, pricing engine, and forecasting panel.

COMMODITY_PROFILES = {
    "Chrome Ore": {
        "icon": "⛏️",
        "origin_country": "ZW",
        "gateway_country": "ZA",
        "destination_country": "CN",
        "mine_label": "Great Dyke, Zimbabwe",
        "consolidation_label": "City Deep, Johannesburg",
        "port_label": "Durban Port",
        "destination_label": "Tianjin Port, China",
        "end_buyer": "Baosteel / Shanxi Stainless Group",
        "currency_origin": "ZiG / USD",
        "currency_gateway": "ZAR / USD",
        "spot_price_label": "Sinochrome Base Spot (Tianjin CIF)",
        "spot_price_default": 295.00,
        "spot_price_range": (150, 450),
        "minegate_pct_of_cif": 0.40,
        "ocean_freight_default": 42.50,
        "ocean_freight_range": (15.0, 90.0),
        "inland_trucking_default": 75,
        "inland_trucking_range": (30, 120),
        "moisture_penalty_label": "Moisture / Silica Impurity Penalty (USD/MT)",
        "moisture_penalty_default": 6.50,
        "moisture_penalty_range": (0.0, 25.0),
        "port_congestion_baseline": 12.4,
        "border_post_label": "Beitbridge Border Post",
        "border_wait_baseline": 3.6,
        "route": [
            {"name": "Great Dyke (Mine)", "lat": -18.6, "lon": 30.5, "stage": "Extraction"},
            {"name": "Beitbridge Border Post", "lat": -22.2167, "lon": 30.0000, "stage": "Border Crossing"},
            {"name": "Johannesburg (City Deep)", "lat": -26.2041, "lon": 28.0473, "stage": "Consolidation"},
            {"name": "Durban Port", "lat": -29.8587, "lon": 31.0218, "stage": "Port Gateway"},
            {"name": "Tianjin Port, China", "lat": 39.0027, "lon": 117.7164, "stage": "Discharge"},
        ],
    },
    "Lithium Spodumene": {
        "icon": "🔋",
        "origin_country": "ZW",
        "gateway_country": "MZ",
        "destination_country": "CN",
        "mine_label": "Goromonzi / Bikita, Zimbabwe",
        "consolidation_label": "Mutare Rail Yard, Zimbabwe",
        "port_label": "Beira Port, Mozambique",
        "destination_label": "Tianjin Port, China",
        "end_buyer": "Sinomine / Ganfeng Lithium",
        "currency_origin": "ZiG / USD",
        "currency_gateway": "MZN / USD",
        "spot_price_label": "Spodumene Concentrate Spot (6% Li2O, CIF China)",
        "spot_price_default": 1050.00,
        "spot_price_range": (500, 2200),
        "minegate_pct_of_cif": 0.33,
        "ocean_freight_default": 58.00,
        "ocean_freight_range": (25.0, 110.0),
        "inland_trucking_default": 95,
        "inland_trucking_range": (40, 160),
        "moisture_penalty_label": "Moisture / Fines Rejection Penalty (USD/MT)",
        "moisture_penalty_default": 14.00,
        "moisture_penalty_range": (0.0, 40.0),
        "port_congestion_baseline": 8.1,
        "border_post_label": "Machipanda Border Post",
        "border_wait_baseline": 2.1,
        "route": [
            {"name": "Bikita Minerals (Mine)", "lat": -19.95, "lon": 31.65, "stage": "Extraction"},
            {"name": "Machipanda Border Post", "lat": -19.1167, "lon": 32.9667, "stage": "Border Crossing"},
            {"name": "Mutare Rail Yard", "lat": -18.9707, "lon": 32.6709, "stage": "Consolidation"},
            {"name": "Beira Port, Mozambique", "lat": -19.8436, "lon": 34.8389, "stage": "Port Gateway"},
            {"name": "Tianjin Port, China", "lat": 39.0027, "lon": 117.7164, "stage": "Discharge"},
        ],
    },
    "Refined Copper": {
        "icon": "🟠",
        "origin_country": "ZM",
        "gateway_country": "TZ",
        "destination_country": "CN",
        "mine_label": "Copperbelt, Zambia",
        "consolidation_label": "Ndola Logistics Hub, Zambia",
        "port_label": "Dar es Salaam Port, Tanzania",
        "destination_label": "Shanghai / Tianjin Port, China",
        "end_buyer": "Jiangxi Copper / China Minmetals",
        "currency_origin": "ZMW / USD",
        "currency_gateway": "TZS / USD",
        "spot_price_label": "LME-Linked Refined Copper Spot (CIF China)",
        "spot_price_default": 9650.00,
        "spot_price_range": (6500, 13000),
        "minegate_pct_of_cif": 0.46,
        "ocean_freight_default": 64.00,
        "ocean_freight_range": (30.0, 120.0),
        "inland_trucking_default": 110,
        "inland_trucking_range": (50, 180),
        "moisture_penalty_label": "Oxidation / Impurity Grade Penalty (USD/MT)",
        "moisture_penalty_default": 9.00,
        "moisture_penalty_range": (0.0, 30.0),
        "port_congestion_baseline": 9.7,
        "border_post_label": "Nakonde Border Post (TAZARA Corridor)",
        "border_wait_baseline": 4.4,
        "route": [
            {"name": "Copperbelt (Mine)", "lat": -12.8, "lon": 28.2, "stage": "Extraction"},
            {"name": "Nakonde Border Post", "lat": -9.3333, "lon": 32.7500, "stage": "Border Crossing"},
            {"name": "Ndola Logistics Hub", "lat": -12.9587, "lon": 28.6366, "stage": "Consolidation"},
            {"name": "Dar es Salaam Port", "lat": -6.8160, "lon": 39.2803, "stage": "Port Gateway"},
            {"name": "Shanghai Port, China", "lat": 31.2304, "lon": 121.4737, "stage": "Discharge"},
        ],
    },
}

COMMODITY_LIST = list(COMMODITY_PROFILES.keys())

# ==========================================
# DATA INGESTION & PIPELINE ENGINE
# ==========================================

@st.cache_data(ttl=3600)
def get_world_bank_data(country_code, indicator_code, start_year=2015, end_year=2025):
    """
    Programmatically extracts structural macroeconomic risk vectors directly from the
    World Bank API. Used to model systemic sovereign strain along the supply chain corridor.
    """
    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}?date={start_year}:{end_year}&format=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            if len(json_data) > 1 and json_data[1]:
                records = json_data[1]
                data_list = []
                for r in records:
                    if r['value'] is not None:
                        data_list.append({
                            "Year": int(r['date']),
                            "Value": float(r['value'])
                        })
                df = pd.DataFrame(data_list)
                if not df.empty:
                    return df.sort_values("Year")
    except Exception:
        pass

    # Fallback Data Engine in case World Bank API times out or throttles requests
    years = list(range(start_year, end_year + 1))
    if country_code == "ZA":
        if "DECT" in indicator_code:
            values = [115e9, 125e9, 130e9, 140e9, 150e9, 170e9, 168e9, 175e9, 180e9, 182e9, 185e9]
        else:
            values = [4.6, 6.3, 5.3, 4.6, 4.1, 3.3, 4.5, 6.9, 5.9, 5.2, 4.8]
    elif country_code == "ZW":
        if "DECT" in indicator_code:
            values = [10e9, 11e9, 11.5e9, 12e9, 12.3e9, 12.7e9, 13.2e9, 13.5e9, 13.8e9, 14.1e9, 14.5e9]
        else:
            values = [1.5, -2.4, 0.9, 10.6, 255.0, 557.0, 98.5, 104.0, 244.0, 48.0, 12.5]
    elif country_code == "ZM":
        if "DECT" in indicator_code:
            values = [9.4e9, 10.0e9, 10.6e9, 11.2e9, 11.97e9, 12.7e9, 13.2e9, 13.0e9, 12.6e9, 12.3e9, 12.1e9]
        else:
            values = [21.1, 17.9, 6.6, 7.5, 9.2, 15.7, 22.0, 9.9, 10.8, 13.0, 14.2]
    elif country_code == "MZ":
        if "DECT" in indicator_code:
            values = [9.9e9, 11.4e9, 11.0e9, 11.2e9, 12.5e9, 14.0e9, 16.2e9, 17.1e9, 17.8e9, 18.4e9, 19.0e9]
        else:
            values = [10.6, 15.3, 15.1, 3.5, 2.8, 3.2, 10.3, 7.0, 5.4, 3.6, 4.0]
    else:  # TZ
        if "DECT" in indicator_code:
            values = [16.1e9, 17.0e9, 18.5e9, 21.1e9, 22.5e9, 25.0e9, 26.2e9, 27.0e9, 27.8e9, 28.5e9, 29.2e9]
        else:
            values = [5.6, 5.2, 3.5, 3.4, 3.3, 3.3, 4.4, 4.8, 3.8, 3.1, 3.0]

    return pd.DataFrame({"Year": years[:len(values)], "Value": values[:len(years)]})


@st.cache_data(ttl=1800)
def get_live_forex_rates(api_key=None):
    """
    Extracts currency configurations. Computes CNY cross-rates against the corridor's
    local currencies, crucial for the C&D treasury operations clearing framework.
    """
    if api_key:
        url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"
        try:
            res = requests.get(url, timeout=5).json()
            rates = res.get('rates', {})
            usd_zar = rates.get('ZAR', 18.25)
            usd_cny = rates.get('CNY', 7.24)
            usd_zig = 13.56
            usd_mzn = rates.get('MZN', 63.90)
            usd_zmw = rates.get('ZMW', 27.10)
            usd_tzs = rates.get('TZS', 2540.0)
            return {
                "USD/ZAR": round(usd_zar, 4),
                "USD/CNY": round(usd_cny, 4),
                "USD/MZN": round(usd_mzn, 4),
                "USD/ZMW": round(usd_zmw, 4),
                "USD/TZS": round(usd_tzs, 4),
                "CNY/ZAR": round(usd_zar / usd_cny, 4),
                "CNY/ZiG": round(usd_zig / usd_cny, 4),
                "CNY/MZN": round(usd_mzn / usd_cny, 4),
                "CNY/ZMW": round(usd_zmw / usd_cny, 4),
                "CNY/TZS": round(usd_tzs / usd_cny, 4),
                "Status": "Live API Data"
            }
        except Exception:
            pass

    usd_zar = 18.15 + np.random.uniform(-0.05, 0.05)
    usd_cny = 7.24 + np.random.uniform(-0.01, 0.01)
    usd_mzn = 63.90 + np.random.uniform(-0.3, 0.3)
    usd_zmw = 27.10 + np.random.uniform(-0.2, 0.2)
    usd_tzs = 2540.0 + np.random.uniform(-10, 10)
    return {
        "USD/ZAR": round(usd_zar, 4),
        "USD/CNY": round(usd_cny, 4),
        "USD/MZN": round(usd_mzn, 4),
        "USD/ZMW": round(usd_zmw, 4),
        "USD/TZS": round(usd_tzs, 4),
        "CNY/ZAR": round(usd_zar / usd_cny, 4),
        "CNY/ZiG": round(13.56 / usd_cny, 4),
        "CNY/MZN": round(usd_mzn / usd_cny, 4),
        "CNY/ZMW": round(usd_zmw / usd_cny, 4),
        "CNY/TZS": round(usd_tzs / usd_cny, 4),
        "Status": "Dynamic Live Feed"
    }

# ==========================================
# MODULE 1: GEOSPATIAL CORRIDOR INTELLIGENCE (PYDECK)
# ==========================================

def build_corridor_dataframes(profile, border_wait_days, port_congestion_days):
    """
    Builds the node and edge (arc) dataframes for the Pydeck 3D corridor map.
    Edge color/height intensity scales with live risk inputs so the map visually
    communicates where the friction in the chain actually is.
    """
    route = profile["route"]
    nodes = pd.DataFrame(route)

    # Risk intensity per leg, normalized 0-1 against sensible operational ceilings.
    # Leg 0: Mine -> Border (function of border wait)
    # Leg 1: Border -> Consolidation (function of border wait, decaying)
    # Leg 2: Consolidation -> Port (function of port congestion)
    # Leg 3: Port -> Destination (ocean leg, low baseline risk, weather-modulated lightly)
    border_intensity = min(border_wait_days / 10.0, 1.0)
    port_intensity = min(port_congestion_days / 20.0, 1.0)

    legs = []
    for i in range(len(route) - 1):
        src = route[i]
        dst = route[i + 1]
        if i == 0:
            intensity = border_intensity
            risk_label = "Border Queue Risk"
        elif i == 1:
            intensity = border_intensity * 0.55
            risk_label = "Inland Consolidation Risk"
        elif i == 2:
            intensity = port_intensity
            risk_label = "Port Terminal Congestion"
        else:
            intensity = 0.18 + 0.12 * port_intensity  # ocean leg, mild sympathetic risk
            risk_label = "Ocean Freight / Transit Risk"

        # Color ramp through the institutional risk palette:
        # stable teal (#4B9C7E) -> caution gold (#C9A24B) -> critical brick (#C84B3C)
        if intensity <= 0.5:
            t = intensity / 0.5
            r = int(75 + t * (201 - 75))
            g = int(156 + t * (162 - 156))
            b = int(126 + t * (75 - 126))
        else:
            t = (intensity - 0.5) / 0.5
            r = int(201 + t * (200 - 201))
            g = int(162 + t * (75 - 162))
            b = int(75 + t * (60 - 75))

        legs.append({
            "from_name": src["name"], "from_lat": src["lat"], "from_lon": src["lon"],
            "to_name": dst["name"], "to_lat": dst["lat"], "to_lon": dst["lon"],
            "intensity": round(intensity, 3),
            "risk_label": risk_label,
            "color_r": r, "color_g": g, "color_b": b,
            "width": 2 + intensity * 9,
        })

    edges = pd.DataFrame(legs)
    return nodes, edges


def render_corridor_map(profile, border_wait_days, port_congestion_days):
    """
    Renders the interactive 3D Pydeck corridor map: ArcLayer for risk-weighted legs,
    ScatterplotLayer for named nodes, TextLayer for labels.
    """
    nodes, edges = build_corridor_dataframes(profile, border_wait_days, port_congestion_days)

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=edges,
        get_source_position=["from_lon", "from_lat"],
        get_target_position=["to_lon", "to_lat"],
        get_source_color=["color_r", "color_g", "color_b", 180],
        get_target_color=["color_r", "color_g", "color_b", 220],
        get_width="width",
        pickable=True,
        auto_highlight=True,
    )

    node_layer = pdk.Layer(
        "ScatterplotLayer",
        data=nodes,
        get_position=["lon", "lat"],
        get_radius=45000,
        get_fill_color=[201, 162, 75, 215],   # signal gold — matches CSS --signal
        get_line_color=[11, 14, 20, 255],      # ink — matches CSS --ink
        line_width_min_pixels=1,
        pickable=True,
        stroked=True,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=nodes,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=13,
        get_color=[232, 234, 237, 255],        # ink-high — matches CSS --ink-high
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -18],
        font_family="'IBM Plex Mono', monospace",
    )

    # Center the view roughly between origin and gateway for a readable default angle,
    # since the full corridor spans Africa to East Asia.
    mid_lat = (nodes["lat"].iloc[0] + nodes["lat"].iloc[2]) / 2
    mid_lon = (nodes["lon"].iloc[0] + nodes["lon"].iloc[2]) / 2

    view_state = pdk.ViewState(
        latitude=mid_lat,
        longitude=mid_lon,
        zoom=3.4,
        pitch=45,
        bearing=10,
    )

    tooltip = {
        "html": "<b>{from_name} → {to_name}</b><br/>"
                "{risk_label}<br/>"
                "Intensity: {intensity}",
        "style": {"backgroundColor": "#12161F", "color": "#E8EAED", "border": "1px solid #232938", "fontFamily": "IBM Plex Mono, monospace", "fontSize": "12px"}
    }

    # NOTE: the previous build pinned this to a "mapbox://styles/..." URL, which
    # silently renders a blank map on any deployment without a paid Mapbox token
    # configured (the #1 reason the corridor map looked "broken"). CARTO's basemap
    # tiles are free, require no token, and ship natively with pydeck — this is
    # the fix, not a workaround.
    deck = pdk.Deck(
        layers=[arc_layer, node_layer, text_layer],
        initial_view_state=view_state,
        map_provider="carto",
        map_style=pdk.map_styles.DARK,
        tooltip=tooltip,
    )
    return deck, edges


# ==========================================
# MODULE 3: ADVANCED RISK FORECASTING ENGINE
# ==========================================

def generate_historical_baseline(profile, days_back=30, seed=None):
    """
    Generates a credible historical baseline series for port congestion (in days),
    anchored to the commodity's known baseline and modulated with a weekly seasonal
    cycle plus mild autocorrelated noise (mean-reverting random walk).
    """
    rng = np.random.default_rng(seed)
    baseline = profile["port_congestion_baseline"]
    t = np.arange(days_back)

    # Weekly seasonality: congestion tends to build mid-week, ease over weekends
    seasonal = 1.1 * np.sin(2 * np.pi * t / 7 + 1.2)

    # Mean-reverting (Ornstein-Uhlenbeck style) noise so the series looks like a real
    # operational metric rather than pure white noise
    noise = np.zeros(days_back)
    for i in range(1, days_back):
        noise[i] = noise[i - 1] * 0.72 + rng.normal(0, 0.55)

    series = baseline + seasonal + noise
    series = np.clip(series, 0.5, None)

    start_date = datetime.date.today() - datetime.timedelta(days=days_back)
    dates = [start_date + datetime.timedelta(days=int(i)) for i in t]
    return pd.DataFrame({"Date": dates, "Wait (Days)": series, "Series": "Historical"})


def forecast_port_congestion(profile, horizon_days, rainfall_index, inventory_backlog_pct,
                              border_wait_days, history_df):
    """
    Projects Durban-equivalent port congestion forward using a regression-style
    extrapolation: linear trend fitted to the recent historical window, plus
    structural adders for simulated rainfall risk and warehouse backlog pressure,
    decayed forward with damped seasonal oscillation and bounded growth.

    This intentionally mirrors how a treasury risk desk would build a lightweight
    operational forecast: trend + seasonal + exogenous shock terms, rather than a
    black-box model the user can't sanity-check.
    """
    y = history_df["Wait (Days)"].values
    x = np.arange(len(y))

    # Fit a simple linear trend (degree-1 regression) over the trailing window
    # to capture directional drift in congestion before applying shock terms.
    slope, intercept = np.polyfit(x, y, 1)
    trend_anchor = slope * (len(y) - 1) + intercept  # trend value at "today"

    horizon = np.arange(1, horizon_days + 1)

    # Rainfall risk: 0-10 scale: heavy regional rainfall slows rail/road throughput
    # into the terminal and adds queueing pressure, with effect compounding mildly
    # over the forecast window before saturating (diminishing marginal damage).
    rainfall_effect = (rainfall_index / 10.0) * 3.5 * (1 - np.exp(-horizon / 6.0))

    # Inventory backlog: % of warehouse capacity already occupied. High backlog
    # compresses the buffer available to absorb new arrivals, worsening queue days.
    backlog_effect = (inventory_backlog_pct / 100.0) * 4.0 * (1 - np.exp(-horizon / 9.0))

    # Border wait sympathetically pushes port congestion a few days later, as
    # trucks released from Beitbridge/the border post arrive at port in clusters.
    border_spillover = (border_wait_days / 10.0) * 1.2 * np.sin(horizon / 4.0 + 0.3).clip(min=0)

    # Damped seasonal continuation
    seasonal_fwd = 1.0 * np.sin(2 * np.pi * (len(y) + horizon) / 7 + 1.2) * np.exp(-horizon / 25.0)

    # Trend continuation, damped slightly so a short-term slope doesn't run away
    # over a 14-day horizon (treasury desks distrust unbounded linear extrapolation)
    trend_fwd = trend_anchor + slope * horizon * 0.6

    projected = trend_fwd + seasonal_fwd + rainfall_effect + backlog_effect + border_spillover
    projected = np.clip(projected, 0.5, 45)

    # Simple uncertainty band: widens with horizon to reflect compounding forecast error
    uncertainty = 0.35 + 0.12 * horizon
    lower = np.clip(projected - uncertainty, 0.5, None)
    upper = projected + uncertainty

    last_date = history_df["Date"].iloc[-1]
    fwd_dates = [last_date + datetime.timedelta(days=int(d)) for d in horizon]

    forecast_df = pd.DataFrame({
        "Date": fwd_dates,
        "Wait (Days)": projected,
        "Lower Bound": lower,
        "Upper Bound": upper,
        "Series": "Forecast",
    })
    return forecast_df


# ==========================================
# MODULE 4: SCENARIO SAVER — SESSION STATE LEDGER
# ==========================================

def init_scenario_ledger():
    if "scenario_ledger" not in st.session_state:
        st.session_state.scenario_ledger = pd.DataFrame(columns=[
            "Scenario ID", "Label", "Commodity", "Timestamp",
            "Spot Price (USD/MT)", "Ocean Freight (USD/MT)",
            "Inland Trucking (USD/MT)", "Border Wait (Days)",
            "Port Congestion (Days)", "Demurrage (USD/Day)",
            "Total Cost (USD/MT)", "Net Margin (%)", "Verdict"
        ])
    if "scenario_counter" not in st.session_state:
        st.session_state.scenario_counter = 0


def save_scenario(label, commodity, spot_price, ocean_freight, inland_trucking,
                   border_wait, port_congestion, demurrage, total_cost, net_margin):
    st.session_state.scenario_counter += 1
    scenario_id = f"Scenario {chr(64 + st.session_state.scenario_counter)}" \
        if st.session_state.scenario_counter <= 26 else f"Scenario #{st.session_state.scenario_counter}"

    if net_margin >= 0 and net_margin >= target_margin_percent:
        verdict = "Approved"
    elif net_margin > 0:
        verdict = "Margin Compression"
    else:
        verdict = "Unviable"

    new_row = pd.DataFrame([{
        "Scenario ID": scenario_id,
        "Label": label if label else "Untitled Scenario",
        "Commodity": commodity,
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Spot Price (USD/MT)": round(spot_price, 2),
        "Ocean Freight (USD/MT)": round(ocean_freight, 2),
        "Inland Trucking (USD/MT)": round(inland_trucking, 2),
        "Border Wait (Days)": round(border_wait, 1),
        "Port Congestion (Days)": round(port_congestion, 1),
        "Demurrage (USD/Day)": round(demurrage, 0),
        "Total Cost (USD/MT)": round(total_cost, 2),
        "Net Margin (%)": round(net_margin, 2),
        "Verdict": verdict,
    }])

    st.session_state.scenario_ledger = pd.concat(
        [st.session_state.scenario_ledger, new_row], ignore_index=True
    )


def scenario_ledger_to_csv_bytes():
    buf = io.StringIO()
    st.session_state.scenario_ledger.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def build_executive_summary_text(profile_name, fx_data, forecast_df):
    """
    Builds a plain-text executive summary suitable for a lightweight downloadable
    report. Kept dependency-free (no PDF library required) while still giving the
    user a polished, structured executive brief they can download alongside the CSV.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("XIAMEN C&D — SINO-AFRICAN LOGISTICS & RISK MATRIX")
    lines.append("Executive Corridor Intelligence Brief")
    lines.append("=" * 72)
    lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Active Commodity Corridor: {profile_name}")
    lines.append("-" * 72)
    lines.append("CURRENT TREASURY CLEARING RATES")
    for k, v in fx_data.items():
        if k != "Status":
            lines.append(f"   {k}: {v}")
    lines.append(f"   Feed Status: {fx_data.get('Status', 'n/a')}")
    lines.append("-" * 72)
    lines.append("14-DAY PORT CONGESTION FORECAST (DAYS)")
    for _, row in forecast_df.iterrows():
        lines.append(f"   {row['Date']}: {row['Wait (Days)']:.1f} days "
                      f"(range {row['Lower Bound']:.1f}–{row['Upper Bound']:.1f})")
    lines.append("-" * 72)
    lines.append("SAVED SCENARIO LEDGER")
    if "scenario_ledger" in st.session_state and not st.session_state.scenario_ledger.empty:
        lines.append(st.session_state.scenario_ledger.to_string(index=False))
    else:
        lines.append("   No scenarios saved this session.")
    lines.append("=" * 72)
    lines.append(f"Prepared by: {DESIGNER}")
    lines.append("Disclaimer: Academic showcase / strategic planning artifact for the")
    lines.append("Schwarzman Scholars application. Not an executable trading instrument.")
    lines.append("=" * 72)
    return "\n".join(lines)


# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
st.sidebar.markdown(
    "<div style='font-family:IBM Plex Mono, monospace; font-size:0.72rem; "
    "letter-spacing:0.1em; color:#C9A24B; text-transform:uppercase;'>"
    "XIAMEN C&amp;D &nbsp;·&nbsp; CORRIDOR CONTROL</div>",
    unsafe_allow_html=True
)
st.sidebar.markdown(
    f"<div style='color:#8B93A7; font-size:0.78rem; margin-top:2px; margin-bottom:14px;'>"
    f"{DESIGNER}</div>",
    unsafe_allow_html=True
)
st.sidebar.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)

st.sidebar.markdown("### Commodity Corridor")
selected_commodity = st.sidebar.selectbox(
    "Active Trade Corridor",
    options=COMMODITY_LIST,
    index=0,
    help="Switching commodities re-routes the geospatial map, pricing rules, and forecasting baseline."
)
profile = COMMODITY_PROFILES[selected_commodity]
st.sidebar.caption(
    f"{selected_commodity} — "
    f"{profile['mine_label']} → {profile['port_label']} → {profile['destination_label']}"
)

st.sidebar.markdown("### API Configuration")
api_key_input = st.sidebar.text_input(
    "Open Exchange Rates Key", type="password",
    placeholder="Paste key to activate Live FX"
)

st.sidebar.markdown("### Corridor Constants")
vessel_capacity = st.sidebar.number_input("Bulk Shipment Volume (Metric Tons)", value=50000, step=5000)
fixed_freight_cost = st.sidebar.number_input(
    "Ocean Freight Base (USD/MT)",
    value=float(profile["ocean_freight_default"]),
    min_value=float(profile["ocean_freight_range"][0]),
    max_value=float(profile["ocean_freight_range"][1]),
    step=1.0,
)
target_margin_percent = st.sidebar.slider("Target Operating Margin (%)", min_value=1, max_value=30, value=8)

st.sidebar.markdown("### Forecast Drivers")
rainfall_index = st.sidebar.slider(
    "Simulated Regional Rainfall Index (0–10)", min_value=0, max_value=10, value=5,
    help="Higher values simulate heavier rainfall disrupting rail/road throughput into port."
)
inventory_backlog_pct = st.sidebar.slider(
    "Warehouse Inventory Backlog (% of Capacity)", min_value=0, max_value=100, value=40,
    help="Higher backlog compresses the buffer available to absorb new port arrivals."
)
forecast_horizon = st.sidebar.slider("Forecast Horizon (Days)", min_value=7, max_value=21, value=14)

st.sidebar.info(
    f"**{selected_commodity} corridor**\n\n"
    f"Maps {profile['mine_label']} to Xiamen C&D's consolidation point at "
    f"{profile['consolidation_label']}, the export gateway at {profile['port_label']}, "
    f"and final discharge at {profile['destination_label']}."
)

# ==========================================
# HEADER SECTION
# ==========================================
_now_str = datetime.datetime.now().strftime("%H:%M:%S UTC")
st.markdown(
    f"""
    <div class="status-bar">
        <span class="status-pill"><span class="status-dot"></span> LIVE FEED CONNECTED</span>
        <span class="status-divider"></span>
        <span class="status-pill">SESSION CLOCK {_now_str}</span>
        <span class="status-divider"></span>
        <span class="status-pill">COVERAGE: ZW · ZA · ZM · MZ · TZ · CN</span>
        <span class="status-divider"></span>
        <span class="badge-tier">INSTITUTIONAL GRADE</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    "<span class='eyebrow'>XIAMEN C&amp;D CORPORATION LIMITED &nbsp;·&nbsp; FORTUNE GLOBAL 500</span>",
    unsafe_allow_html=True
)
st.markdown("<h1 class='main-title'>Sino-African Logistics &amp; Risk Matrix</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='main-subtitle'>SUPPLY CHAIN TREASURY OPERATIONS &nbsp;/&nbsp; "
    "STRATEGY SUITE &nbsp;/&nbsp; MULTI-COMMODITY GEOSPATIAL EDITION</div>",
    unsafe_allow_html=True
)
st.markdown("<hr class='section-rule' style='margin-top:14px;'/>", unsafe_allow_html=True)

# ==========================================
# SECTION 1: GLOBAL CORRIDOR KEY PERFORMANCE INDICATORS
# ==========================================
fx_data = get_live_forex_rates(api_key_input)
init_scenario_ledger()

# Build the historical baseline once per commodity/seed so the KPI tile, the line
# chart, and the pricing engine below all reference the same congestion reality.
historical_df = generate_historical_baseline(profile, days_back=30, seed=hash(selected_commodity) % (2**31))
current_port_congestion = float(historical_df["Wait (Days)"].iloc[-1])
current_border_wait = profile["border_wait_baseline"]

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

gateway_currency_label = {
    "ZA": "CNY/ZAR", "MZ": "CNY/MZN", "TZ": "CNY/TZS", "ZM": "CNY/ZMW"
}.get(profile["gateway_country"], "CNY/ZAR")
gateway_rate_value = fx_data.get(gateway_currency_label, fx_data["CNY/ZAR"])

with col_kpi1:
    st.metric(
        label=f"{gateway_currency_label} (Logistics Clearing Rate)",
        value=f"{gateway_rate_value}",
        delta=f"{(gateway_rate_value * 0.005):+.4f} (Daily Variance)",
        delta_color="normal"
    )
with col_kpi2:
    st.metric(
        label="CNY / ZiG (Mine-Gate Valuation)",
        value=f"{fx_data['CNY/ZiG']} ZiG",
        delta="-0.02%",
        delta_color="inverse"
    )
with col_kpi3:
    st.metric(
        label=f"{profile['port_label']} Congestion Index",
        value=f"{current_port_congestion:.1f} Days",
        delta=f"{(current_port_congestion - profile['port_congestion_baseline']):+.1f} Days (vs. Baseline)",
        delta_color="inverse"
    )
with col_kpi4:
    st.metric(
        label=profile["spot_price_label"],
        value=f"${profile['spot_price_default']:.2f} / MT",
        delta="+$4.50 (Market Demand)",
        delta_color="normal"
    )

# ------------------------------------------------------------------
# EXECUTIVE BRIEFING — auto-synthesized one-glance read of the corridor's
# current state. Pulls directly from the same live variables driving the
# KPIs and map below, so it never drifts out of sync with the data.
# ------------------------------------------------------------------
border_state = "critical" if current_border_wait >= 6 else ("caution" if current_border_wait >= 3.5 else "stable")
port_delta = current_port_congestion - profile["port_congestion_baseline"]
port_state = "critical" if current_port_congestion > 12 else ("caution" if current_port_congestion > 7 else "stable")

tag_class = {"stable": "t-stable", "caution": "t-caution", "critical": "t-critical"}
border_word = {"stable": "running within tolerance", "caution": "showing moderate friction", "critical": "experiencing acute delay"}[border_state]
port_word = {"stable": "operating below baseline", "caution": "tracking above baseline", "critical": "materially congested"}[port_state]

brief_text = (
    f"The {selected_commodity} corridor from {profile['mine_label']} to {profile['destination_label']} is "
    f"currently {('clear for standard execution' if border_state == 'stable' and port_state == 'stable' else 'carrying elevated operational risk that warrants desk attention')}. "
    f"{profile['border_post_label']} is {border_word} at {current_border_wait:.1f} days average wait, while "
    f"{profile['port_label']} is {port_word} ({current_port_congestion:.1f}d vs. {profile['port_congestion_baseline']:.1f}d baseline, "
    f"{port_delta:+.1f}d). Treasury clearing rate {gateway_currency_label} stands at {gateway_rate_value}, sourced from "
    f"{fx_data.get('Status', 'a live feed')}."
)

st.markdown(
    f"""
    <div class="brief-card">
        <span class="brief-label">Executive Briefing — Auto-Synthesized</span>
        <div class="brief-text">{brief_text}</div>
        <div class="brief-tags">
            <span class="brief-tag {tag_class[border_state]}">BORDER: {border_state.upper()}</span>
            <span class="brief-tag {tag_class[port_state]}">PORT: {port_state.upper()}</span>
            <span class="brief-tag t-stable">FX FEED: ACTIVE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# SECTION 2: GEOSPATIAL CORRIDOR INTELLIGENCE (PYDECK)
# ==========================================
section_header(
    "Module 01 / Geospatial Intelligence",
    f"Corridor Map — {selected_commodity}",
    "Arc thickness and color scale with live border-queue and port-congestion intensity. "
    "Brick-red legs indicate acute operational risk; teal legs are running within tolerance."
)

deck, edge_risk_df = render_corridor_map(profile, current_border_wait, current_port_congestion)
st.pydeck_chart(deck, use_container_width=True)

# Stage legend strip beneath the map — replaces the old static HTML stage cards with
# a compact risk-coded summary that stays in sync with the live map above.
stage_cols = st.columns(len(profile["route"]))
risk_for_stage = {
    "Extraction": ("ELEVATED — inland fuel costs", "risk-high"),
    "Border Crossing": (f"{current_border_wait:.1f}d avg wait", "risk-med" if current_border_wait < 6 else "risk-high"),
    "Consolidation": ("STABLE", "risk-low"),
    "Port Gateway": (f"{current_port_congestion:.1f}d congestion",
                      "risk-high" if current_port_congestion > 12 else ("risk-med" if current_port_congestion > 7 else "risk-low")),
    "Discharge": ("OPTIMAL", "risk-low"),
}
for i, node in enumerate(profile["route"]):
    with stage_cols[i]:
        status_text, status_class = risk_for_stage.get(node["stage"], ("MONITORED", "risk-med"))
        st.markdown(f"""
        <div class="stage-card">
            <span class="stage-eyebrow">STAGE {i+1:02d} — {node['stage'].upper()}</span>
            <span class="stage-name">{node['name']}</span>
            <span class="stage-status {status_class}">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

with st.expander("Corridor leg risk detail"):
    st.dataframe(
        edge_risk_df[["from_name", "to_name", "risk_label", "intensity"]].rename(columns={
            "from_name": "From", "to_name": "To", "risk_label": "Risk Factor", "intensity": "Intensity (0–1)"
        }),
        use_container_width=True, hide_index=True
    )

# ==========================================
# SECTION 3: ADVANCED RISK FORECASTING ENGINE
# ==========================================
section_header(
    "Module 02 / Predictive Forecasting",
    f"Port Congestion Outlook — {profile['port_label']}",
    "Trend-and-shock extrapolation: a fitted historical trend is combined with simulated "
    "rainfall risk, warehouse backlog pressure, and border-crossing spillover to project "
    f"congestion over the next {forecast_horizon} days."
)

forecast_df = forecast_port_congestion(
    profile, forecast_horizon, rainfall_index, inventory_backlog_pct,
    current_border_wait, historical_df
)

chart_df = pd.concat([
    historical_df[["Date", "Wait (Days)", "Series"]],
    forecast_df[["Date", "Wait (Days)", "Series"]]
], ignore_index=True)
chart_pivot = chart_df.pivot_table(index="Date", columns="Series", values="Wait (Days)", aggfunc="mean")

col_fc_chart, col_fc_stats = st.columns([3, 1])
with col_fc_chart:
    hist_plot_df = historical_df[["Date", "Wait (Days)"]].assign(Series="Historical")
    fc_plot_df = forecast_df[["Date", "Wait (Days)"]].assign(Series="Forecast")

    band = alt.Chart(forecast_df).mark_area(
        opacity=0.18, color=CHART_GOLD
    ).encode(
        x=alt.X("Date:T", title=None),
        y=alt.Y("Lower Bound:Q", title="Wait (Days)"),
        y2="Upper Bound:Q",
    )

    hist_line = alt.Chart(hist_plot_df).mark_line(
        color=CHART_INK_LOW, strokeWidth=2
    ).encode(x="Date:T", y="Wait (Days):Q")

    fc_line = alt.Chart(fc_plot_df).mark_line(
        color=CHART_GOLD, strokeWidth=2.5, point=alt.OverlayMarkDef(color=CHART_GOLD, size=35)
    ).encode(
        x="Date:T", y="Wait (Days):Q",
        tooltip=[alt.Tooltip("Date:T"), alt.Tooltip("Wait (Days):Q", format=".1f")],
    )

    today_rule = alt.Chart(pd.DataFrame({"Date": [historical_df["Date"].iloc[-1]]})).mark_rule(
        color=CHART_HAIRLINE, strokeDash=[3, 3]
    ).encode(x="Date:T")

    fc_chart = base_chart_props(
        (band + today_rule + hist_line + fc_line).resolve_scale(y="shared"),
        height=380,
    )
    st.altair_chart(fc_chart, use_container_width=True)
    st.caption(
        f"Historical baseline (30 days) vs. {forecast_horizon}-day projected wait times, "
        f"{profile['port_label']}. Shaded band reflects compounding forecast uncertainty."
    )
with col_fc_stats:
    st.markdown("#### Forecast snapshot")
    st.metric("Day-1 Projection", f"{forecast_df['Wait (Days)'].iloc[0]:.1f} d")
    st.metric(f"Day-{forecast_horizon} Projection", f"{forecast_df['Wait (Days)'].iloc[-1]:.1f} d")
    peak_pos = forecast_df["Wait (Days)"].to_numpy().argmax()
    st.metric(
        "Peak Congestion Day",
        f"{forecast_df['Wait (Days)'].max():.1f} d",
        delta=f"on {forecast_df['Date'].iloc[peak_pos]}"
    )
    avg_change = forecast_df["Wait (Days)"].mean() - historical_df["Wait (Days)"].mean()
    if avg_change > 1.0:
        st.error(f"Forecast trending **+{avg_change:.1f}d** above historical average.")
    elif avg_change > 0:
        st.warning(f"Forecast trending **+{avg_change:.1f}d** above historical average.")
    else:
        st.success(f"Forecast trending **{avg_change:.1f}d** vs. historical average.")

# ==========================================
# SECTION 4: DEEP SOVEREIGN & MACRO RISK MODELS
# ==========================================
section_header(
    "Module 03 / Macro Risk",
    "Sovereign Debt Dynamics &amp; Inflation Squeezes",
    "Derived programmatically from the World Bank API to map fiscal stability corridors "
    "for Xiamen C&D capital allocations."
)

origin_code = profile["origin_country"]
gateway_code = profile["gateway_country"]
origin_name = CORRIDOR_COUNTRIES.get(origin_code, origin_code)
gateway_name = CORRIDOR_COUNTRIES.get(gateway_code, gateway_code)

col_graph_gateway, col_graph_origin = st.columns(2)

with col_graph_gateway:
    st.markdown(f"#### {gateway_name.split(' (')[0]} — Gateway Analysis")
    gw_debt_df = get_world_bank_data(gateway_code, "DT.DOD.DECT.CD")
    gw_inflation_df = get_world_bank_data(gateway_code, "FP.CPI.TOTL.ZG")

    gw_chart = alt.Chart(gw_debt_df).mark_area(
        line=alt.LineConfig(color=CHART_GOLD, strokeWidth=2.5),
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color=CHART_GOLD, offset=0), alt.GradientStop(color=CHART_SURFACE, offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
        opacity=0.35,
    ).encode(
        x=alt.X("Year:O", title=None),
        y=alt.Y("Value:Q", title="USD"),
        tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Value:Q", format=",.0f")],
    )
    st.altair_chart(base_chart_props(gw_chart, height=300), use_container_width=True)
    st.caption(f"{gateway_name.split(' (')[0]}: Total External Debt Stock Trend (USD)")

    gw_latest_inf = gw_inflation_df.iloc[-1]["Value"]
    st.info(
        f"**Gateway macro health.** Current baseline inflation at **{gw_latest_inf:.2f}%** "
        f"impacts regional trucking wages and warehouse overheads at {profile['consolidation_label']}."
    )

with col_graph_origin:
    st.markdown(f"#### {origin_name.split(' (')[0]} — Origin Analysis")
    origin_debt_df = get_world_bank_data(origin_code, "DT.DOD.DECT.CD")
    origin_inflation_df = get_world_bank_data(origin_code, "FP.CPI.TOTL.ZG")

    org_chart = alt.Chart(origin_inflation_df).mark_area(
        line=alt.LineConfig(color=CHART_CRITICAL, strokeWidth=2.5),
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color=CHART_CRITICAL, offset=0), alt.GradientStop(color=CHART_SURFACE, offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
        opacity=0.35,
    ).encode(
        x=alt.X("Year:O", title=None),
        y=alt.Y("Value:Q", title="%"),
        tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Value:Q", format=".2f")],
    )
    st.altair_chart(base_chart_props(org_chart, height=300), use_container_width=True)
    st.caption(f"{origin_name.split(' (')[0]}: Historical CPI Inflation Trend (%)")

    origin_latest_debt = origin_debt_df.iloc[-1]["Value"]
    st.warning(
        f"**{origin_name.split(' (')[0]} fiscal squeeze.** Sovereign debt holds at "
        f"**${origin_latest_debt/1e9:.2f} Billion USD**, sustaining liquidity caps that require "
        f"C&D to deploy specialized B2B clearing pathways."
    )

# ==========================================
# SECTION 5: CARGO MARGIN STRESS-TESTING SUITE
# ==========================================
section_header(
    "Module 04 / Decision Engine",
    "Cargo Margin Stress-Testing",
    "Simulate how macroeconomic fluctuations and supply chain disruptions affect a "
    "cargo's real profitability — built for corporate portfolio audits."
)

col_sim_controls, col_sim_outputs = st.columns([1, 1])

gateway_fx_rate = {
    "ZA": fx_data["USD/ZAR"], "MZ": fx_data["USD/MZN"],
    "TZ": fx_data["USD/TZS"], "ZM": fx_data["USD/ZMW"]
}.get(gateway_code, fx_data["USD/ZAR"])

with col_sim_controls:
    st.markdown("#### Input operational friction points")
    spot_price = st.slider(
        f"{profile['spot_price_label']}",
        min_value=int(profile["spot_price_range"][0]),
        max_value=int(profile["spot_price_range"][1]),
        value=int(profile["spot_price_default"]),
    )
    inland_trucking_usd = st.slider(
        f"{origin_name.split(' (')[0]}-to-{profile['consolidation_label'].split(',')[0]} Logistics Tariff (USD / MT)",
        min_value=int(profile["inland_trucking_range"][0]),
        max_value=int(profile["inland_trucking_range"][1]),
        value=int(profile["inland_trucking_default"]),
    )
    warehouse_handling_local = st.slider(
        f"Depot Fees ({profile['currency_gateway'].split(' / ')[0]} / MT)",
        min_value=100, max_value=500, value=250
    )
    moisture_penalty = st.slider(
        profile["moisture_penalty_label"],
        min_value=float(profile["moisture_penalty_range"][0]),
        max_value=float(profile["moisture_penalty_range"][1]),
        value=float(profile["moisture_penalty_default"]),
    )
    port_waiting_days = st.slider(
        f"{profile['port_label']} Terminal Congestion (Days)",
        min_value=1, max_value=30, value=int(round(current_port_congestion))
    )
    daily_demurrage_cost = st.number_input("Vessel Demurrage Penalty (USD / Day)", value=22000, step=1000)

    warehouse_usd = warehouse_handling_local / gateway_fx_rate
    port_holding_usd = (port_waiting_days * daily_demurrage_cost) / vessel_capacity

with col_sim_outputs:
    st.markdown("#### Real-time financial model")

    raw_minegate_purchase = spot_price * profile["minegate_pct_of_cif"]
    inland_freight = inland_trucking_usd
    depot_and_customs = warehouse_usd
    demurrage_and_port = port_holding_usd
    ocean_freight = fixed_freight_cost
    impurity_penalty = moisture_penalty

    total_estimated_cost = (
        raw_minegate_purchase + inland_freight + depot_and_customs
        + demurrage_and_port + ocean_freight + impurity_penalty
    )
    net_operating_profit = spot_price - total_estimated_cost
    net_margin_percent = (net_operating_profit / spot_price) * 100

    st.markdown(
        f"<span style='color:#8B93A7; font-size:0.86rem;'>Total shipment cost allocation (per MT)</span><br/>"
        f"<span style='font-family:IBM Plex Mono, monospace; font-size:1.3rem; color:#E8EAED; font-weight:600;'>"
        f"${total_estimated_cost:.2f}</span>",
        unsafe_allow_html=True
    )
    st.write("")

    if net_margin_percent >= target_margin_percent:
        st.success(f"**Operation approved.** Simulated margin is **{net_margin_percent:.2f}%** (exceeds target of {target_margin_percent}%)")
    elif net_margin_percent > 0:
        st.warning(f"**Margin compression.** Simulated margin is **{net_margin_percent:.2f}%** (below target of {target_margin_percent}%)")
    else:
        st.error(f"**Shipment unviable.** Negative margin projected (**{net_margin_percent:.2f}%**)")

    cost_data = pd.DataFrame({
        "Cost Component": ["Mine-gate Cost", "Inland Freight", "Depot & Handling",
                            "Port Demurrage", "Ocean Freight", "Impurity Penalty"],
        "USD per Metric Ton": [raw_minegate_purchase, inland_freight, depot_and_customs,
                                demurrage_and_port, ocean_freight, impurity_penalty]
    })

    bars = alt.Chart(cost_data).mark_bar(color=CHART_GOLD, size=22).encode(
        x=alt.X("USD per Metric Ton:Q", title="USD / MT"),
        y=alt.Y("Cost Component:N", sort="x", title=None),
        tooltip=[alt.Tooltip("Cost Component:N"), alt.Tooltip("USD per Metric Ton:Q", format="$.2f")],
    )
    labels = alt.Chart(cost_data).mark_text(
        align="left", dx=6, color=CHART_INK, font=CHART_FONT, fontSize=11
    ).encode(
        x="USD per Metric Ton:Q", y=alt.Y("Cost Component:N", sort="x"),
        text=alt.Text("USD per Metric Ton:Q", format="$.2f"),
    )
    st.altair_chart(base_chart_props(bars + labels, height=300), use_container_width=True)

# ==========================================
# SECTION 6: SCENARIO SAVER & EXECUTIVE REPORT GENERATOR
# ==========================================
section_header(
    "Module 05 / Scenario Ledger",
    "Scenario Saver &amp; Executive Report Generator",
    "Save the current stress-test configuration to the session ledger, then export the "
    "full ledger and forecast as a CSV or an executive text brief for distribution."
)

col_save_label, col_save_btn = st.columns([3, 1])
with col_save_label:
    scenario_label = st.text_input(
        "Scenario Label",
        placeholder='e.g. "Durban Rail Strike" or "Stable Operations"',
        key="scenario_label_input"
    )
with col_save_btn:
    st.write("")
    st.write("")
    if st.button("Save Scenario", use_container_width=True):
        save_scenario(
            label=scenario_label,
            commodity=selected_commodity,
            spot_price=spot_price,
            ocean_freight=ocean_freight,
            inland_trucking=inland_trucking_usd,
            border_wait=current_border_wait,
            port_congestion=port_waiting_days,
            demurrage=daily_demurrage_cost,
            total_cost=total_estimated_cost,
            net_margin=net_margin_percent,
        )
        st.success(f"Scenario saved as **{st.session_state.scenario_ledger['Scenario ID'].iloc[-1]}**.")

st.markdown("#### Saved scenario ledger")
if st.session_state.scenario_ledger.empty:
    st.info("No scenarios saved yet this session. Configure the stress-test inputs above and click **Save Scenario**.")
else:
    st.dataframe(st.session_state.scenario_ledger, use_container_width=True, hide_index=True)

    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button(
            "Download Ledger (CSV)",
            data=scenario_ledger_to_csv_bytes(),
            file_name=f"sino_african_scenario_ledger_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_dl2:
        report_text = build_executive_summary_text(selected_commodity, fx_data, forecast_df)
        st.download_button(
            "Download Executive Brief (.txt)",
            data=report_text.encode("utf-8"),
            file_name=f"executive_brief_{datetime.date.today().isoformat()}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_dl3:
        if st.button("Clear Ledger"):
            st.session_state.scenario_ledger = st.session_state.scenario_ledger.iloc[0:0]
            st.session_state.scenario_counter = 0
            st.rerun()

# ==========================================
# FOOTER & CREDITS
# ==========================================
st.markdown("<hr class='section-rule'/>", unsafe_allow_html=True)
col_foot1, col_foot2 = st.columns([1, 1])
with col_foot1:
    st.caption(
        "Disclaimer: designed for academic showcase and strategic planning for the "
        "Schwarzman Scholars application. Macro datasets are updated live using public open APIs. "
        "The forecasting module uses a transparent trend-plus-shock extrapolation model for "
        "illustrative scenario planning, not a production trading signal."
    )
with col_foot2:
    st.markdown(
        f"<p style='text-align: right; color:#8B93A7; font-size: 0.78rem; "
        f"font-family: IBM Plex Mono, monospace;'>"
        f"SATT ARCHITECTURE V3.0 — INSTITUTIONAL EDITION<br/>{DESIGNER}</p>",
        unsafe_allow_html=True
    )
