from pathlib import Path
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
import html
import math
import textwrap
from urllib.parse import quote

import pandas as pd
import streamlit as st
import os
from supabase import create_client
# ============================================================
# OPTIONAL AUTO REFRESH
# ============================================================
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


# ============================================================
# PAGE
# ============================================================
st.set_page_config(
    page_title="StockAI — NSE AI Stock Screener",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# PATHS
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

LIVE_TICKS = DATASET / "live_ticks.csv"
LTP_HISTORY = DATASET / "live_ltp_history.csv"
LIVE_FEATURES = DATASET / "live_ml_features.csv"
LIVE_SMMA = DATASET / "live_smma.csv"
LIVE_AI = DATASET / "live_ai_signals.csv"
TRADE_LOG = DATASET / "live_trade_log.csv"

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)


# ============================================================
# SUPABASE LIVE DATA
# ============================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
    except Exception:
        supabase = None


# ============================================================
# LOAD LIVE AI SIGNALS FROM SUPABASE
# ============================================================

def load_supabase_ai_signals():
    if supabase is None:
        return pd.DataFrame()

    try:
        response = (
            supabase
            .table("live_ai_signals")
            .select("*")
            .execute()
        )

        rows = response.data or []

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)

    except Exception as e:
        st.warning(f"Supabase live signal read failed: {e}")
        return pd.DataFrame()
    
# ============================================================
# MARKET STATUS
# ============================================================
def market_is_open(now=None):
    now = datetime.now(IST) if now is None else now

    if now.weekday() >= 5:
        return False

    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


NOW = datetime.now(IST)
IS_MARKET_OPEN = market_is_open(NOW)

# ============================================================
# HTML RENDERER
#
# IMPORTANT:
# Use st.html() instead of st.code()/st.write() so HTML
# is rendered as HTML and never displayed as source code.
# ============================================================
def render_html(content):
    content = textwrap.dedent(str(content)).strip()

    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(
            content,
            unsafe_allow_html=True
        )


# ============================================================
# CSS
# ============================================================
st.markdown(
    """
<style>

/* ============================================================
   STOCKAI — PREMIUM BLACK TERMINAL THEME
   ============================================================ */

:root {
    --bg: #000000;
    --panel: #070707;
    --panel-2: #0b0b0b;
    --panel-3: #101010;
    --border: #242424;
    --border-soft: #181818;
    --text: #f5f7fa;
    --text-2: #c4cad3;
    --muted: #7d8794;
    --green: #19e6a5;
    --green-soft: #06251d;
    --red: #ff5964;
    --red-soft: #2b0b10;
    --blue: #5b8cff;
    --blue-soft: #0b1730;
    --yellow: #f5c84c;
}

/* ---------- GLOBAL ---------- */

html,
body,
.stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stHeader"],
[data-testid="stDecoration"],
.main,
section.main,
.block-container,
footer {
    background: #000000 !important;
    background-color: #000000 !important;
    color: var(--text) !important;
}

html,
body,
.stApp {
    font-family:
        Inter,
        ui-sans-serif,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif !important;
}

* {
    box-sizing: border-box;
}

::selection {
    background: #173f35 !important;
    color: #ffffff !important;
}

.block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 18px 14px 42px !important;
    margin: 0 !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
    background: #000000 !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 10px !important;
    background: #000000 !important;
}

section[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="stHeader"] {
    background: #000000 !important;
    height: 0 !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 10px !important;
}

div[data-testid="stVerticalBlock"] {
    gap: 7px !important;
}

/* ---------- TOP BAR ---------- */

.topbar {
    width: 100%;
    min-height: 88px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 24px;
    margin: 4px 0 16px;
    background: #000000;
    border: 1px solid #171717;
    border-radius: 14px;
    box-shadow: 0 10px 35px rgba(0,0,0,.45);
    color: var(--text);
    position: relative;
    z-index: 100;
}

.brand {
    display: flex;
    align-items: center;
    gap: 13px;
}

.logo {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    background: linear-gradient(135deg, #19e6a5, #087c62);
    color: #00130e;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    font-weight: 950;
    box-shadow: 0 0 25px rgba(25,230,165,.18);
}

.brand-title {
    color: #ffffff !important;
    font-size: 21px;
    font-weight: 900;
    letter-spacing: -.35px;
    line-height: 23px;
}

.brand-sub {
    color: #697382 !important;
    font-size: 10px;
    margin-top: 2px;
    letter-spacing: .04em;
}

.clock {
    color: #8c97a6 !important;
    font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace !important;
    font-size: 12px;
    letter-spacing: .04em;
}

.status-live,
.status-closed {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-left: 12px;
    padding: 8px 13px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .06em;
}

.status-live {
    color: var(--green);
    background: var(--green-soft);
    border: 1px solid #0e735b;
    box-shadow: 0 0 18px rgba(25,230,165,.08);
}

.status-closed {
    color: #ff6d76;
    background: var(--red-soft);
    border: 1px solid #7d2637;
}

.blink {
    animation: liveblink 1s infinite;
}

.live-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 7px;
    border-radius: 50%;
    background: var(--green);
    vertical-align: middle;
    animation: livepulse 1.2s infinite;
}

.live-value {
    transition: all .15s ease;
}

.value-flash {
    animation: valueflash .65s ease-out;
    background: transparent !important;
    color: inherit !important;
}

/* ---------- NAVIGATION ---------- */

.nav-caption {
    color: #7c8796 !important;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin: 4px 0 6px 4px;
}

.nav-row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0 12px;
    margin: 0;
    position: relative;
    z-index: 20;
    overflow: visible !important;
}

.nav-item {
    min-width: 190px;
    height: 46px;
    padding: 11px 18px;
    border: 1px solid #222222;
    border-radius: 10px;
    color: #8b95a3;
    background: #080808;
    text-align: center;
    font-size: 12px;
    font-weight: 800;
    line-height: 22px;
    white-space: nowrap;
    transition: all .18s ease;
}

.nav-item:hover {
    color: #ffffff;
    background: #111111;
    border-color: #3a3a3a;
    transform: translateY(-1px);
}

/* Streamlit radio used for the four dashboard sections */
div[data-testid="stRadio"] {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 0 12px !important;
    overflow: visible !important;
    position: relative !important;
    z-index: 30 !important;
}

div[data-testid="stRadio"] > div {
    width: 100% !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 10px !important;
    overflow: visible !important;
}

div[data-testid="stRadio"] label {
    min-width: 190px !important;
    height: 46px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #080808 !important;
    border: 1px solid #252525 !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    color: #a1a9b5 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    white-space: nowrap !important;
    transition: all .18s ease !important;
}

div[data-testid="stRadio"] label:hover {
    background: #111111 !important;
    border-color: #444444 !important;
    color: #ffffff !important;
}

div[data-testid="stRadio"] label:has(input:checked) {
    background: #071d17 !important;
    border-color: #19a980 !important;
    color: #19e6a5 !important;
    box-shadow: inset 0 0 0 1px rgba(25,230,165,.12),
                0 0 20px rgba(25,230,165,.06) !important;
}

div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span {
    color: inherit !important;
    font-weight: inherit !important;
}

/* ---------- KPI CARDS ---------- */

.kpi {
    background: #050505;
    border: 1px solid #242424;
    border-radius: 13px;
    min-height: 108px;
    padding: 15px 16px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.015);
    transition: border-color .18s ease, transform .18s ease;
}

.kpi:hover {
    border-color: #3a3a3a;
    transform: translateY(-1px);
}

.kpi-label {
    color: #7e8896;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .08em;
    text-transform: uppercase;
}

.kpi-value {
    color: #ffffff;
    font-size: 29px;
    line-height: 34px;
    font-weight: 950;
    margin-top: 7px;
    letter-spacing: -.6px;
}

.kpi-sub {
    color: #687380;
    font-size: 10px;
    margin-top: 4px;
}

/* ---------- WORKSPACE CARDS ---------- */

.workspace-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 14px;
}

.workspace-card {
    background: #050505;
    border: 1px solid #232323;
    border-radius: 13px;
    padding: 16px;
    min-height: 155px;
    box-shadow: 0 10px 25px rgba(0,0,0,.28);
}

.workspace-label {
    color: #7f8a98;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .1em;
    margin-bottom: 9px;
}

.workspace-title {
    color: #ffffff;
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 8px;
    letter-spacing: -.2px;
}

.workspace-value {
    color: var(--green);
    font-size: 23px;
    font-weight: 950;
}

.workspace-muted {
    color: #727d8b;
    font-size: 11px;
    line-height: 18px;
}

.workspace-detail {
    color: #c4cad3;
    font-size: 12px;
    line-height: 20px;
}

/* ---------- SEARCH / INPUTS ---------- */

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] input {
    background: #080808 !important;
    color: #f5f7fa !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    font-family: inherit !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: #19a980 !important;
    box-shadow: 0 0 0 1px #19a980 !important;
}

label,
[data-testid="stWidgetLabel"] p {
    color: #9aa3af !important;
}

/* ---------- SCREEN ---------- */

.screen-shell {
    background: #050505;
    border: 1px solid #242424;
    border-radius: 13px 13px 0 0;
    overflow: hidden;
    box-shadow: 0 12px 30px rgba(0,0,0,.28);
}

.screen-head {
    min-height: 66px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #222222;
    background: #070707;
}

.screen-title {
    color: #ffffff;
    font-size: 18px;
    font-weight: 950;
    letter-spacing: -.2px;
}

.screen-count {
    color: #788391;
    font-size: 11px;
}

/* ---------- TABLE ---------- */

.table-scroll {
    width: 100%;
    overflow-x: auto;
    border-left: 1px solid #242424;
    border-right: 1px solid #242424;
    scrollbar-color: #3b3b3b #070707;
}

.stock-table {
    width: 100%;
    min-width: 1700px;
    border-collapse: collapse;
    table-layout: fixed;
    background: #030303;
}

.stock-table th {
    height: 46px;
    padding: 0 10px;
    text-align: left;
    background: #0c0c0c;
    color: #858f9c;
    border-bottom: 1px solid #2b2b2b;
    font-size: 10px;
    font-weight: 950;
    letter-spacing: .06em;
    text-transform: uppercase;
    white-space: nowrap;
}

.stock-table td {
    height: 68px;
    padding: 7px 10px;
    border-bottom: 1px solid #171717;
    white-space: nowrap;
    vertical-align: middle;
    color: #d2d7df;
    font-size: 12px;
}

.stock-table tr:hover td {
    background: #0b0b0b;
}

.stock-link {
    color: inherit;
    text-decoration: none;
    display: block;
    cursor: pointer;
}

.stock-link:hover .symbol {
    color: var(--green);
    text-decoration: underline;
}

.stock-expand {
    display: inline-flex;
    width: 22px;
    height: 22px;
    align-items: center;
    justify-content: center;
    margin-right: 7px;
    border: 1px solid #343434;
    border-radius: 6px;
    color: #aab3be;
    background: #0b0b0b;
    text-decoration: none;
    font-size: 12px;
    font-weight: 900;
    vertical-align: middle;
}

.stock-expand:hover {
    color: #ffffff;
    background: #12352d;
    border-color: #198e70;
}

.symbol {
    color: #ffffff;
    font-size: 16px;
    font-weight: 950;
    letter-spacing: -.15px;
}

.company {
    color: #707b89;
    font-size: 10px;
    margin-top: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ltp {
    font-size: 17px;
    font-weight: 950;
    color: #ffffff;
}

.metric {
    color: #c5ccd5;
    font-size: 14px;
}

.bid {
    color: var(--green);
    font-weight: 850;
    font-size: 14px;
}

.ask {
    color: var(--red);
    font-weight: 850;
    font-size: 14px;
}

/* ---------- TREND ---------- */

.trend-box {
    width: 110px;
    height: 42px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
    box-sizing: border-box;
}

.trend-box svg {
    width: 105px !important;
    height: 38px !important;
    display: block;
}

.no-trend {
    color: #4f5966;
    font-size: 13px;
}

/* ---------- SIGNALS ---------- */

.signal {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 950;
    letter-spacing: .06em;
}

.pass,
.buy {
    color: var(--green);
    background: var(--green-soft);
    border: 1px solid #0c735b;
}

.sell {
    color: var(--red);
    background: var(--red-soft);
    border: 1px solid #7d2637;
}

/* ---------- INLINE STOCK DETAILS ---------- */

.stock-inline-details {
    display: block;
    position: relative;
}

.stock-inline-details > summary {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    list-style: none;
    outline: none;
}

.stock-inline-details > summary::-webkit-details-marker,
.stock-inline-details > summary::marker {
    display: none;
}

.stock-arrow {
    display: inline-flex;
    width: 18px;
    height: 18px;
    align-items: center;
    justify-content: center;
    color: #8995a4;
    font-size: 10px;
    font-weight: 900;
    transition: transform .12s ease, color .12s ease;
}

.stock-inline-details[open] .stock-arrow {
    transform: rotate(90deg);
    color: var(--green);
}

.inline-stock-panel {
    margin-top: 12px;
    padding: 15px 17px;
    background: #080808;
    border: 1px solid #292929;
    border-radius: 10px;
    min-width: 650px;
}

.inline-stock-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 12px;
}

.inline-stock-title {
    font-size: 13px;
    font-weight: 900;
    color: #ffffff;
}

.inline-stock-sub {
    margin-top: 3px;
    font-size: 10px;
    color: #707b89;
}

.inline-stock-price {
    font-size: 20px;
    font-weight: 950;
    color: var(--green);
}

.inline-stock-metrics {
    display: grid;
    grid-template-columns: repeat(4, minmax(110px, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}

.inline-stock-metrics > div {
    padding: 9px;
    background: #0d0d0d;
    border: 1px solid #242424;
    border-radius: 7px;
}

.inline-stock-metrics span {
    display: block;
    font-size: 9px;
    color: #737e8c;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: .05em;
}

.inline-stock-metrics b {
    font-size: 12px;
    color: #e7ebf1;
}

.inline-depth-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 42px;
}

.depth-heading {
    font-size: 11px;
    font-weight: 900;
    letter-spacing: .05em;
    margin-bottom: 7px;
    color: #9ba5b1;
}

.bid-heading,
.depth-bid-price {
    color: var(--green);
}

.ask-heading,
.depth-ask-price {
    color: var(--red);
}

.depth-row {
    display: flex;
    justify-content: space-between;
    gap: 25px;
    min-height: 24px;
    font-family: "JetBrains Mono", Consolas, monospace;
    font-size: 11px;
    color: #b5bec9;
}

.depth-empty,
.detail-empty {
    color: #59636f;
    font-size: 10px;
}

.expanded-stock-row > td {
    padding: 0 !important;
    border-top: 0 !important;
}

.expanded-stock-row .inline-depth-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 48px;
    padding: 18px 36px 20px;
    background: #080808;
    border-top: 1px solid #1d1d1d;
}

.expanded-stock-row .detail-box {
    margin-bottom: 10px;
}

/* ---------- LIVE DETAIL ---------- */

.live-stock-detail {
    margin-top: 14px;
    border: 1px solid #292929;
    border-radius: 12px;
    background: #050505;
    padding: 16px;
}

.live-detail-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.live-detail-card {
    border: 1px solid #232323;
    border-radius: 9px;
    padding: 12px;
    background: #0a0a0a;
}

.live-detail-label {
    color: #74808d;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .07em;
}

.live-detail-value {
    color: #ffffff;
    font-size: 18px;
    font-weight: 950;
    margin-top: 4px;
}

.live-detail-sub {
    color: #7c8794;
    font-size: 11px;
    margin-top: 3px;
}

/* ---------- AI ---------- */

.ai-card {
    background: #050505;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 14px;
    min-height: 100px;
}

.ai-label {
    color: #7d8794;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .07em;
}

.ai-value {
    color: #ffffff;
    font-size: 25px;
    font-weight: 950;
    margin-top: 5px;
}

.ai-sub {
    color: #687380;
    font-size: 10px;
}

.ai-buy {
    color: var(--green);
    font-weight: 950;
}

.ai-sell {
    color: var(--red);
    font-weight: 950;
}

.ai-hold {
    color: var(--yellow);
    font-weight: 950;
}

.ai-table,
.trade-table {
    width: 100%;
    border-collapse: collapse;
    background: #030303;
}

.ai-table {
    min-width: 1450px;
}

.ai-table th,
.trade-table th {
    background: #0c0c0c;
    color: #858f9c;
    font-size: 10px;
    padding: 11px 9px;
    text-align: left;
    border-bottom: 1px solid #292929;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: .05em;
}

.ai-table td,
.trade-table td {
    color: #c7ced7;
    font-size: 11px;
    padding: 11px 9px;
    border-bottom: 1px solid #171717;
    vertical-align: top;
}

.ai-table tr:hover td,
.trade-table tr:hover td {
    background: #0a0a0a;
}

.ai-scroll,
.trade-scroll {
    width: 100%;
    overflow: auto;
    border: 1px solid #242424;
    border-radius: 10px;
}

.score {
    font-weight: 950;
    font-size: 14px;
}

.reason {
    color: #788390;
    white-space: normal;
    line-height: 17px;
    min-width: 260px;
}

/* ---------- TRADE LOG ---------- */

.trade-table {
    min-width: 1250px;
}

.paper-note {
    color: #687380;
    font-size: 10px;
    padding: 10px 0;
}

/* ---------- DETAIL ---------- */

.detail-box {
    background: #050505;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 10px 25px rgba(0,0,0,.22);
}

.detail-title {
    color: #ffffff;
    font-size: 21px;
    font-weight: 950;
    letter-spacing: -.25px;
}

.detail-sub {
    color: #6f7a87;
    font-size: 11px;
}

.detail-metric {
    color: #c4cbd4;
    font-size: 14px;
    padding: 7px 0;
    border-bottom: 1px solid #171717;
}

/* ---------- FOOTER ---------- */

.footer {
    margin-top: 18px;
    padding: 14px 4px;
    border-top: 1px solid #1b1b1b;
    color: #5e6875;
    font-size: 10px;
}

/* ---------- STREAMLIT DATAFRAME FALLBACK ---------- */

[data-testid="stDataFrame"] {
    border: 1px solid #242424 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ---------- BUTTONS ---------- */

.stButton > button {
    background: #090909 !important;
    color: #dfe4ea !important;
    border: 1px solid #292929 !important;
    border-radius: 9px !important;
    font-weight: 800 !important;
    transition: all .18s ease !important;
}

.stButton > button:hover {
    background: #10241f !important;
    color: var(--green) !important;
    border-color: #198e70 !important;
}

.stButton > button:focus {
    box-shadow: 0 0 0 1px #19a980 !important;
}

/* ---------- SCROLLBARS ---------- */

* {
    scrollbar-width: thin;
    scrollbar-color: #363636 #050505;
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #050505;
}

::-webkit-scrollbar-thumb {
    background: #363636;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #505050;
}

/* ---------- ANIMATIONS ---------- */

@keyframes livepulse {
    0% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(25,230,165,.65);
    }
    70% {
        opacity: .65;
        transform: scale(1.18);
        box-shadow: 0 0 0 7px rgba(25,230,165,0);
    }
    100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(25,230,165,0);
    }
}

@keyframes valueflash {
    0% {
        opacity: .35;
        transform: translateY(-1px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes liveblink {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: .25;
    }
}

/* ---------- RESPONSIVE ---------- */

@media (max-width: 1100px) {
    .workspace-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .nav-row {
        overflow-x: auto !important;
    }

    div[data-testid="stRadio"] > div {
        overflow-x: auto !important;
    }
}

@media (max-width: 900px) {
    .workspace-grid {
        grid-template-columns: 1fr;
    }

    .live-detail-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .inline-stock-metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 650px) {
    .topbar {
        min-height: 74px;
        padding: 13px 14px;
    }

    .brand-title {
        font-size: 18px;
    }

    .status-live,
    .status-closed {
        padding: 6px 9px;
        font-size: 9px;
    }

    .clock {
        display: none;
    }

    .live-detail-grid {
        grid-template-columns: 1fr;
    }
}

</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================
def to_num(value, default=0.0):
    try:
        x = float(value)
        if math.isfinite(x):
            return x
    except Exception:
        pass
    return default


def clean_symbol(value):
    return (
        str(value)
        .strip()
        .upper()
        .replace("NSE:", "")
        .replace("BSE:", "")
        .replace("-EQ", "")
    )


def get_value(row, *names, default=0):
    """Safely read a value from either a pandas Series or a dict-like row."""
    if row is None:
        return default

    for name in names:
        try:
            if isinstance(row, dict):
                if name in row:
                    value = row[name]
                    if value is not None:
                        return value
            else:
                # Pandas Series / mapping-like object.
                if hasattr(row, "index") and name in row.index:
                    value = row[name]
                    if value is not None:
                        return value

                # Fallback for objects exposing attributes.
                if hasattr(row, name):
                    value = getattr(row, name)
                    if value is not None:
                        return value
        except Exception:
            continue

    return default

def get_text(row, *names, default=""):
    """Safely read text from a pandas Series or dict-like row."""
    value = get_value(
        row,
        *names,
        default=default
    )
    if value is None:
        return default
    return str(value)

def money(value):
    return f"â‚¹{to_num(value):,.2f}"


def qty_format(value):
    """
    Quantity display:
      >= 1 Cr -> Cr
      >= 1 L  -> L
      >= 1 K  -> K
    """
    value = to_num(value)

    if value >= 10_000_000:
        return f"{value / 10_000_000:.2f} Cr"

    if value >= 100_000:
        return f"{value / 100_000:.2f} L"

    if value >= 1_000:
        return f"{value / 1_000:.2f} K"

    return f"{value:,.0f}"


def read_csv(path):
    try:
        if path.exists():
            return pd.read_csv(
                path,
                low_memory=False
            )
    except Exception:
        return pd.DataFrame()

    return pd.DataFrame()


def find_screener_file():
    candidates = []

    if DATASET.exists():
        for p in DATASET.rglob("*.csv"):
            name = p.name.lower()

            if (
                "live_ticks" not in name
                and "live_ltp_history" not in name
                and (
                    "screen" in name
                    or "final" in name
                )
            ):
                candidates.append(p)

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda p: p.stat().st_mtime
    )


# ============================================================
# 5-LEVEL MARKET DEPTH
# ============================================================
def depth_qty(row, side):
    """Read bid/ask quantity from Series or dict-like rows."""
    if side == "bid":
        names = (
            "BidQty",
            "Bid Qty",
            "BidQuantity",
            "TotalBuyQty",
        )
    else:
        names = (
            "AskQty",
            "Ask Qty",
            "AskQuantity",
            "TotalSellQty",
        )

    return to_num(
        get_value(
            row,
            *names,
            default=0
        )
    )

# ============================================================
# LATEST LIVE QUOTE
# ============================================================
def latest_quotes(live):
    if live.empty:
        return {}

    required = {
        "Symbol",
        "Timestamp"
    }

    if not required.issubset(
        live.columns
    ):
        return {}

    x = live.copy()

    x["_symbol"] = (
        x["Symbol"]
        .astype(str)
        .map(clean_symbol)
    )

    x["_time"] = pd.to_datetime(
        x["Timestamp"],
        errors="coerce"
    )

    x = x.dropna(
        subset=["_time"]
    ).sort_values("_time")

    if x.empty:
        return {}

    latest = (
        x.groupby(
            "_symbol",
            sort=False
        )
        .tail(1)
    )

    return {
        clean_symbol(row["Symbol"]): row
        for _, row in latest.iterrows()
    }


def apply_live(df, live):
    if df.empty or live.empty:
        return df

    # Outside market hours, freeze the dashboard.
    if not IS_MARKET_OPEN:
        return df

    quotes = latest_quotes(live)

    if not quotes:
        return df

    out = df.copy()

    for idx in out.index:
        symbol = clean_symbol(
            out.at[idx, "Symbol"]
        )

        q = quotes.get(symbol)

        if q is None:
            continue

        ltp = to_num(
            q.get("LTP", 0)
        )

        if ltp > 0:
            out.at[idx, "LTP"] = ltp

        out.at[idx, "BidQty"] = depth_qty(
            q,
            "bid"
        )

        out.at[idx, "AskQty"] = depth_qty(
            q,
            "ask"
        )

        if "BidPrice1" in q.index:
            out.at[idx, "BidPrice"] = to_num(
                q["BidPrice1"]
            )

        if "AskPrice1" in q.index:
            out.at[idx, "AskPrice"] = to_num(
                q["AskPrice1"]
            )

    return out


# ============================================================
# HISTORY
# ============================================================
def load_history(live):
    source = read_csv(
        LTP_HISTORY
    )

    if source.empty:
        source = live.copy()

    required = {
        "Symbol",
        "Timestamp",
        "LTP"
    }

    if source.empty or not required.issubset(
        source.columns
    ):
        return {}

    x = source[
        ["Symbol", "Timestamp", "LTP"]
    ].copy()

    x["Symbol"] = (
        x["Symbol"]
        .astype(str)
        .map(clean_symbol)
    )

    x["Timestamp"] = pd.to_datetime(
        x["Timestamp"],
        errors="coerce"
    )

    x = x.dropna(
        subset=[
            "Symbol",
            "Timestamp",
            "LTP"
        ]
    )

    x = x[
        x["LTP"] > 0
    ]

    # Remove exact duplicate history points.
    x = x.drop_duplicates(
        subset=[
            "Symbol",
            "Timestamp",
            "LTP"
        ]
    )

    x = x.sort_values(
        "Timestamp"
    )

    result = {}

    for symbol, group in x.groupby(
        "Symbol",
        sort=False
    ):
        result[symbol] = (
            group["LTP"]
            .tail(50)
            .tolist()
        )

    return result


def sparkline(values, color):
    """
    CSS-only live mini graph.

    Uses vertical bars instead of SVG so Streamlit's HTML renderer
    cannot strip/hide the chart. The latest 30 real LTP points are
    shown left-to-right.
    """
    clean = []

    for value in values:
        value = to_num(
            value,
            default=-1
        )

        if value > 0:
            clean.append(value)

    if len(clean) < 2:
        return (
            '<div class="trend-box">'
            '<div class="no-trend">Waiting...</div>'
            '</div>'
        )

    values = clean[-30:]

    low = min(values)
    high = max(values)

    if high <= low:
        high = low + max(
            abs(low) * 0.001,
            0.01
        )

    bars = []

    for value in values:
        normalized = (
            (value - low)
            / (high - low)
        )

        height = 8 + (
            normalized * 24
        )

        bars.append(
            f"""
            <span
                style="
                    display:block;
                    width:2px;
                    min-width:2px;
                    height:{height:.1f}px;
                    background:{color};
                    border-radius:2px;
                    opacity:.90;
                    align-self:flex-end;
                "
            ></span>
            """
        )

    return f"""
    <div
        class="trend-box"
        title="Live LTP trend"
        style="
            width:110px;
            height:42px;
            display:flex;
            align-items:flex-end;
            justify-content:center;
            gap:2px;
            overflow:hidden;
            padding:3px 2px;
            box-sizing:border-box;
        "
    >
        {''.join(bars)}
    </div>
    """


# ============================================================
# ETQ
# ============================================================
def etq_for_symbol(symbol, live):
    empty = {
        "5": 0.0,
        "20": 0.0,
        "60": 0.0
    }

    if live.empty:
        return empty

    required = {
        "Symbol",
        "Timestamp",
        "LTQ"
    }

    if not required.issubset(
        live.columns
    ):
        return empty

    x = live.copy()

    x["_symbol"] = (
        x["Symbol"]
        .astype(str)
        .map(clean_symbol)
    )

    target = clean_symbol(
        symbol
    )

    x = x[
        x["_symbol"] == target
    ].copy()

    if x.empty:
        return empty

    x["Timestamp"] = pd.to_datetime(
        x["Timestamp"],
        errors="coerce"
    )

    x["LTQ"] = pd.to_numeric(
        x["LTQ"],
        errors="coerce"
    ).fillna(0)

    x = x.dropna(
        subset=["Timestamp"]
    ).sort_values(
        "Timestamp"
    )

    if x.empty:
        return empty

    latest = x["Timestamp"].max()

    return {
        "5": x.loc[
            x["Timestamp"]
            >= latest - pd.Timedelta(
                minutes=5
            ),
            "LTQ"
        ].sum(),

        "20": x.loc[
            x["Timestamp"]
            >= latest - pd.Timedelta(
                minutes=20
            ),
            "LTQ"
        ].sum(),

        "60": x.loc[
            x["Timestamp"]
            >= latest - pd.Timedelta(
                minutes=60
            ),
            "LTQ"
        ].sum()
    }



# ============================================================
# LOAD DATA - FULL DIAGNOSTIC VERSION
# ============================================================

# ------------------------------------------------------------
# INITIALIZE
# ------------------------------------------------------------

ai_df = pd.DataFrame()
smma_df = pd.DataFrame()
features_df = pd.DataFrame()
live = pd.DataFrame()

# ------------------------------------------------------------
# SHOW ACTUAL PATHS
# ------------------------------------------------------------

st.write("### ðŸ” StockAI Data Loader")

st.write("ROOT:", str(ROOT))
st.write("DATASET:", str(DATASET))

# ------------------------------------------------------------
# CHECK DATASET DIRECTORY
# ------------------------------------------------------------

if not DATASET.exists():

    st.error(
        f"âŒ DATASET FOLDER NOT FOUND\n\n"
        f"Expected folder:\n{DATASET}"
    )

else:

    st.success(
        f"âœ… Dataset folder found:\n{DATASET}"
    )

    # Show every CSV that actually exists
    csv_files = list(DATASET.glob("*.csv"))

    if csv_files:

        st.write("### CSV files found:")

        for file in csv_files:

            try:

                size = file.stat().st_size

                st.write(
                    f"âœ… `{file.name}` â€” {size:,} bytes"
                )

            except Exception:

                st.write(
                    f"âœ… `{file.name}`"
                )

    else:

        st.error(
            "âŒ NO CSV FILES FOUND INSIDE DATASET FOLDER"
        )

# ============================================================
# FUNCTION TO LOAD CSV WITH REAL ERROR
# ============================================================

def load_live_csv(path, name):

    st.write(f"### Loading {name}")

    st.write(
        "Expected path:",
        str(path)
    )

    if not path.exists():

        st.error(
            f"âŒ {name} FILE NOT FOUND\n\n"
            f"Expected:\n{path}"
        )

        return pd.DataFrame()

    try:

        data = pd.read_csv(
            path,
            low_memory=False
        )

        st.success(
            f"âœ… {name} loaded â€” "
            f"{len(data):,} rows Ã— {len(data.columns):,} columns"
        )

        if not data.empty:

            st.write(
                f"{name} columns:"
            )

            st.code(
                ", ".join(
                    str(c)
                    for c in data.columns
                )
            )

        return data

    except Exception as e:

        st.error(
            f"âŒ {name} READ ERROR:\n{e}"
        )

        return pd.DataFrame()


# ============================================================
# 1. LIVE TICKS
# ============================================================

live = load_live_csv(
    LIVE_TICKS,
    "LIVE TICKS"
)


# ============================================================
# 2. SMMA
# ============================================================

smma_df = load_live_csv(
    LIVE_SMMA,
    "LIVE SMMA"
)


# ============================================================
# 3. ML FEATURES
# ============================================================

features_df = load_live_csv(
    LIVE_FEATURES,
    "LIVE ML FEATURES"
)


# ============================================================
# 4. LOCAL AI SIGNALS
# ============================================================

local_ai_df = load_live_csv(
    LIVE_AI,
    "LOCAL AI SIGNALS"
)


# ============================================================
# 5. SUPABASE AI SIGNALS
# ============================================================

supabase_ai_df = pd.DataFrame()

if supabase is None:

    st.warning(
        "âš ï¸ Supabase client is NOT initialized."
    )

    st.write(
        "SUPABASE_URL configured:",
        bool(SUPABASE_URL)
    )

    st.write(
        "SUPABASE_KEY configured:",
        bool(SUPABASE_KEY)
    )

else:

    st.success(
        "âœ… Supabase client initialized"
    )

    try:

        response = (
            supabase
            .table("live_ai_signals")
            .select("*")
            .execute()
        )

        rows = response.data or []

        if rows:

            supabase_ai_df = pd.DataFrame(
                rows
            )

            st.success(
                "âœ… SUPABASE AI SIGNALS loaded â€” "
                f"{len(supabase_ai_df):,} rows"
            )

            st.write(
                "Supabase columns:"
            )

            st.code(
                ", ".join(
                    str(c)
                    for c in supabase_ai_df.columns
                )
            )

        else:

            st.warning(
                "âš ï¸ Supabase table `live_ai_signals` "
                "returned ZERO rows."
            )

    except Exception as e:

        st.error(
            "âŒ SUPABASE READ ERROR"
        )

        st.exception(e)


# ============================================================
# 6. SELECT AI SOURCE
# ============================================================

if not supabase_ai_df.empty:

    ai_df = supabase_ai_df.copy()

    st.success(
        "ðŸŸ¢ AI SOURCE = SUPABASE"
    )

elif not local_ai_df.empty:

    ai_df = local_ai_df.copy()

    st.success(
        "ðŸŸ¢ AI SOURCE = LOCAL CSV"
    )

else:

    ai_df = pd.DataFrame()

    st.error(
        "ðŸ”´ NO AI SIGNAL DATA AVAILABLE"
    )


# ============================================================
# 7. NORMALIZE COLUMN NAMES
# ============================================================

for data_name, data in [
    ("AI", ai_df),
    ("SMMA", smma_df),
    ("FEATURES", features_df),
    ("LIVE", live),
]:

    if not data.empty:

        data.columns = [
            str(c).strip()
            for c in data.columns
        ]


# ============================================================
# 8. FINAL DATA STATUS
# ============================================================

st.write("## ðŸ“Š FINAL DATA STATUS")

status_data = pd.DataFrame({

    "Data": [
        "AI Signals",
        "SMMA",
        "ML Features",
        "Live Ticks",
    ],

    "Rows": [
        len(ai_df),
        len(smma_df),
        len(features_df),
        len(live),
    ],

    "Status": [
        "AVAILABLE" if not ai_df.empty else "EMPTY",
        "AVAILABLE" if not smma_df.empty else "EMPTY",
        "AVAILABLE" if not features_df.empty else "EMPTY",
        "AVAILABLE" if not live.empty else "EMPTY",
    ],
})

st.dataframe(
    status_data,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 9. WARNINGS
# ============================================================

if ai_df.empty:

    st.warning(
        "Live AI signals are not currently available."
    )


if smma_df.empty:

    st.warning(
        "Live SMMA data is not currently available."
    )


if features_df.empty:

    st.warning(
        "Live ML features are not currently available."
    )


if live.empty:

    st.warning(
        "Live market tick data is not currently available."
    )
# ============================================================
# NORMALIZE AI SIGNAL DATA
# ============================================================

df = ai_df.copy()

df.columns = [
    str(c).strip()
    for c in df.columns
]

if "Symbol" not in df.columns:
    # Keep the dashboard alive when the live engine has not produced
    # a CSV yet (for example on Streamlit Cloud outside market hours).
    df = pd.DataFrame(
        columns=[
            "Symbol", "Current_LTP", "LTP",
            "Signal", "Decision", "BidQty", "AskQty"
        ]
    )

# ============================================================
# SAFE LTP NORMALIZATION
# ============================================================

if "Current_LTP" in df.columns:
    df["LTP"] = pd.to_numeric(
        df["Current_LTP"],
        errors="coerce"
    )
elif "LTP" in df.columns:
    df["LTP"] = pd.to_numeric(
        df["LTP"],
        errors="coerce"
    )
else:
    df["LTP"] = 0.0

df["LTP"] = df["LTP"].fillna(0)

# ============================================================
# ============================================================
# SAFE SIGNAL / DECISION NORMALIZATION AFTER LIVE UPDATE
# ============================================================

# ---------------- SIGNAL ----------------
if "Signal" not in df.columns:
    df["Signal"] = "NONE"
else:
    df["Signal"] = pd.Series(
        df["Signal"],
        index=df.index
    ).fillna("NONE").astype(str).str.upper().str.strip()

# ---------------- DECISION ----------------
if "Decision" not in df.columns:
    df["Decision"] = "AVOID"
else:
    df["Decision"] = pd.Series(
        df["Decision"],
        index=df.index
    ).fillna("AVOID").astype(str).str.upper().str.strip()

total_stocks = len(df)

price_screened = int(
    df.get(
        "Price_Filter",
        pd.Series(
            False,
            index=df.index
        )
    ).sum()
)

liquidity_qualified = int(
    df.get(
        "Liquidity_Filter",
        pd.Series(
            False,
            index=df.index
        )
    ).sum()
)

buy_count = int(
    (df["Signal"] == "BUY").sum()
)

sell_count = int(
    (df["Signal"] == "SELL").sum()
)

accept_count = int(
    (df["Decision"] == "ACCEPT").sum()
)

avoid_count = int(
    (df["Decision"] == "AVOID").sum()
)

# ============================================================
# APPLY LIVE DATA / FREEZE OUTSIDE MARKET HOURS
# ============================================================

base = ai_df.copy()

if IS_MARKET_OPEN:

    df = base.copy()

    st.session_state[
        "last_market_snapshot"
    ] = df.copy()

else:

    frozen = st.session_state.get(
        "last_market_snapshot"
    )

    if (
        frozen is not None
        and not frozen.empty
    ):
        df = frozen.copy()
    else:
        df = base.copy()

# ============================================================
# APPLY LIVE QUOTES
# ============================================================

if IS_MARKET_OPEN and not live.empty:

    df = apply_live(
        df,
        live
    )
# Normalize columns used by the existing dashboard
if "Current_LTP" in df.columns:
    df["LTP"] = pd.to_numeric(
        df["Current_LTP"],
        errors="coerce"
    )

# ============================================================
# SAFE SIGNAL / DECISION NORMALIZATION AFTER LIVE UPDATE
# ============================================================

# ---------------- SIGNAL ----------------
if "Signal" not in df.columns:
    df["Signal"] = "NONE"
else:
    df["Signal"] = pd.Series(
        df["Signal"],
        index=df.index
    ).fillna("NONE").astype(str).str.upper().str.strip()

# ---------------- DECISION ----------------
if "Decision" not in df.columns:
    df["Decision"] = "AVOID"
else:
    df["Decision"] = pd.Series(
        df["Decision"],
        index=df.index
    ).fillna("AVOID").astype(str).str.upper().str.strip()
# ============================================================
# NORMALIZE
# ============================================================
# ============================================================
# SAFE LTP NORMALIZATION
# ============================================================

if "LTP" not in df.columns:
    if "Current_LTP" in df.columns:
        df["LTP"] = pd.to_numeric(
            df["Current_LTP"],
            errors="coerce"
        )
    else:
        df["LTP"] = 0.0
else:
    df["LTP"] = pd.to_numeric(
        df["LTP"],
        errors="coerce"
    )

df["LTP"] = df["LTP"].fillna(0)

if "BidQty" not in df.columns:
    df["BidQty"] = 0.0
if "AskQty" not in df.columns:
    df["AskQty"] = 0.0

df["BidQty"] = pd.to_numeric(df["BidQty"], errors="coerce").fillna(0)
df["AskQty"] = pd.to_numeric(df["AskQty"], errors="coerce").fillna(0)

# ============================================================
# SCREENER
# ============================================================
scanned = df[df["LTP"].between(30, 500, inclusive="both")].copy()
scanned["DepthTotal"] = scanned["BidQty"] + scanned["AskQty"]
scanned["PASS"] = (
    scanned["DepthTotal"] >= 100_000
)
passed = (
    scanned[scanned["PASS"]]
    .sort_values(
        "DepthTotal",
        ascending=False,
        kind="stable"
    )
    .reset_index(drop=True)
)

history = load_history(live)

# ============================================================
# FAST ETQ MAPS - CALCULATED ONCE PER REFRESH
# ============================================================
def build_etq_maps(live_df):
    zero = {}
    if live_df.empty or not {"Symbol", "Timestamp", "LTQ"}.issubset(live_df.columns):
        return {}, {}, {}

    x = live_df[["Symbol", "Timestamp", "LTQ"]].copy()
    x["_symbol"] = x["Symbol"].astype(str).map(clean_symbol)
    x["_time"] = pd.to_datetime(x["Timestamp"], errors="coerce")
    x["LTQ"] = pd.to_numeric(x["LTQ"], errors="coerce").fillna(0)
    x = x.dropna(subset=["_time"])
    if x.empty:
        return {}, {}, {}

    latest = x.groupby("_symbol")["_time"].transform("max")
    # Keep each symbol's most recent 60-minute window only.
    x = x[x["_time"] >= latest - pd.Timedelta(minutes=60)].copy()
    if x.empty:
        return {}, {}, {}

    last_time = x.groupby("_symbol")["_time"].transform("max")
    x["age_min"] = (last_time - x["_time"]).dt.total_seconds() / 60.0

    m5 = x[x["age_min"] <= 5].groupby("_symbol")["LTQ"].sum().to_dict()
    m20 = x[x["age_min"] <= 20].groupby("_symbol")["LTQ"].sum().to_dict()
    m60 = x.groupby("_symbol")["LTQ"].sum().to_dict()
    return m5, m20, m60

ETQ5, ETQ20, ETQ60 = build_etq_maps(live)

def etq_values(symbol, row=None):
    key = clean_symbol(symbol)
    e5 = to_num(ETQ5.get(key, 0))
    e20 = to_num(ETQ20.get(key, 0))
    e60 = to_num(ETQ60.get(key, 0))

    if row is not None:
        if e5 == 0:
            e5 = get_value(row, "ETQ_5min", "ETQ5", default=0)
        if e20 == 0:
            e20 = get_value(row, "ETQ_20min", "ETQ20", default=0)
        if e60 == 0:
            e60 = get_value(row, "ETQ_60min", "ETQ60", default=0)
    return e5, e20, e60

total_5 = sum(ETQ5.get(clean_symbol(s), 0) for s in passed["Symbol"].astype(str))
total_20 = sum(ETQ20.get(clean_symbol(s), 0) for s in passed["Symbol"].astype(str))
total_60 = sum(ETQ60.get(clean_symbol(s), 0) for s in passed["Symbol"].astype(str))

# ============================================================
# AI SIGNAL ENGINE
# ============================================================
def trend_slope(values):
    vals = [to_num(v, -1) for v in values if to_num(v, -1) > 0]
    if len(vals) < 3:
        return 0.0
    recent = vals[-20:]
    base_v = recent[0]
    last_v = recent[-1]
    if base_v == 0:
        return 0.0
    return ((last_v - base_v) / base_v) * 100.0


def ai_signal_for_row(row):
    symbol = clean_symbol(row["Symbol"])
    ltp = get_value(row, "LTP")
    smma20 = get_value(row, "SMMA20", "SMMA_20", default=ltp)
    smma120 = get_value(row, "SMMA120", "SMMA_120", default=ltp)
    bid = depth_qty(row, "bid")
    ask = depth_qty(row, "ask")
    e5, e20, e60 = etq_values(symbol, row)
    hist = history.get(symbol, [])
    slope = trend_slope(hist)

    score = 50.0
    reasons = []

    if ltp > smma20:
        score += 12
        reasons.append("LTP above SMMA20")
    else:
        score -= 12
        reasons.append("LTP below SMMA20")

    if smma20 > smma120:
        score += 15
        reasons.append("SMMA20 above SMMA120")
    else:
        score -= 15
        reasons.append("SMMA20 below SMMA120")

    if slope > 0.25:
        score += 10
        reasons.append(f"positive LTP trend {slope:.2f}%")
    elif slope < -0.25:
        score -= 10
        reasons.append(f"negative LTP trend {slope:.2f}%")
    else:
        reasons.append("trend is flat/insufficient history")

    depth_total = bid + ask
    imbalance = ((bid - ask) / depth_total * 100) if depth_total > 0 else 0
    if imbalance > 10:
        score += 8
        reasons.append("bid-side depth stronger")
    elif imbalance < -10:
        score -= 8
        reasons.append("ask-side depth stronger")

    if e5 > 0 and e20 > 0:
        if e5 >= e20 * 0.30:
            score += 3
            reasons.append("recent execution activity is healthy")
        else:
            score -= 2
            reasons.append("recent execution activity is light")

    score = max(0, min(100, score))

    if score >= 70:
        signal = "BUY"
        action = "Bullish setup"
        cls = "ai-buy"
    elif score <= 35:
        signal = "SELL"
        action = "Bearish setup"
        cls = "ai-sell"
    else:
        signal = "HOLD"
        action = "No strong edge"
        cls = "ai-hold"

    confidence = max(50, min(99, 50 + abs(score - 50)))

    if signal == "BUY":
        entry = ltp
        stop = ltp * 0.985
        target = ltp * 1.03
    elif signal == "SELL":
        entry = ltp
        stop = ltp * 1.015
        target = ltp * 0.97
    else:
        entry = ltp
        stop = ltp * 0.99
        target = ltp * 1.01

    rr = abs(target - entry) / max(abs(entry - stop), 0.01)

    return {
        "Symbol": symbol,
        "LTP": ltp,
        "SMMA20": smma20,
        "SMMA120": smma120,
        "Trend %": slope,
        "Bid Qty": bid,
        "Ask Qty": ask,
        "ETQ 5M": e5,
        "ETQ 20M": e20,
        "ETQ 60M": e60,
        "Score": score,
        "Signal": signal,
        "Confidence": confidence,
        "Action": action,
        "Reason": "; ".join(reasons),
        "Entry": entry,
        "Stop Loss": stop,
        "Target": target,
        "R:R": rr,
        "Class": cls,
    }


def build_ai_analysis(source_df):
    rows = []
    for _, row in source_df.iterrows():
        rows.append(ai_signal_for_row(row))
    return pd.DataFrame(rows)


AI_ALL = build_ai_analysis(scanned)
AI_PASSED = AI_ALL[AI_ALL["Symbol"].isin(passed["Symbol"].map(clean_symbol))].copy()

# ============================================================
# PAPER TRADE LOG - ONE CURRENT RECORD PER STOCK
# ============================================================
def update_trade_log(ai_df):
    # Keep a paper-trade history, but add a new row only when the
    # signal for a stock changes. This prevents 2-second refreshes
    # from creating thousands of duplicate records.
    if "paper_trade_log" not in st.session_state:
        st.session_state["paper_trade_log"] = []
    if "paper_last_signal" not in st.session_state:
        st.session_state["paper_last_signal"] = {}

    log = st.session_state["paper_trade_log"]
    last_signal = st.session_state["paper_last_signal"]
    now_text = NOW.strftime("%Y-%m-%d %H:%M:%S")

    for _, r in ai_df.iterrows():
        symbol = r["Symbol"]
        signal = r["Signal"]

        # First observation is logged. Later observations are logged
        # only when BUY/SELL/HOLD changes.
        if last_signal.get(symbol) == signal:
            continue

        record = {
            "Time": now_text,
            "Symbol": symbol,
            "Signal": signal,
            "Confidence": float(r["Confidence"]),
            "Entry": float(r["Entry"]),
            "Stop Loss": float(r["Stop Loss"]),
            "Target": float(r["Target"]),
            "R:R": float(r["R:R"]),
            "LTP": float(r["LTP"]),
            "Status": "PAPER WATCH" if signal == "HOLD" else "PAPER SIGNAL",
            "Reason": r["Reason"],
        }
        log.append(record)
        last_signal[symbol] = signal

    return pd.DataFrame(log)


TRADE_LOG = update_trade_log(AI_ALL)

# ============================================================
# LIVE TOP HEADER
# ============================================================
# Keep the header ABOVE the navigation. This tiny fragment refreshes
# only the clock/status every 2 seconds; it does not rerun the whole
# dashboard/table.
@st.fragment(run_every="2s")
def live_top_header():
    header_now = datetime.now(IST)
    header_status = (
        '<span class="status-live blink">â— LIVE Â· 2 SEC</span>'
        if market_is_open(header_now)
        else '<span class="status-closed">â— MARKET CLOSED Â· DATA FROZEN</span>'
    )

    render_html(f"""
    <div class="topbar">
        <div class="brand">
            <div class="logo">â–¥</div>
            <div>
                <div class="brand-title">StockAI</div>
                <div class="brand-sub">SMMA Crossover AI/ML Analysis System</div>
            </div>
        </div>
        <div>
            <span class="clock">{header_now.strftime('%H:%M:%S')}</span>
            {header_status}
        </div>
    </div>
    """)

# Header must be called before the navigation so it stays in the
# upper section of the dashboard.
live_top_header()

# ============================================================
# ONLY LIVE DASHBOARD
# ============================================================

page = "Live Dashboard"

# ============================================================
# LIVE DASHBOARD
# ============================================================

def build_live_screen(live_df):
    base = ai_df.copy()
    if base.empty:
        return pd.DataFrame()
    current = apply_live(base, live_df) if (not live_df.empty and IS_MARKET_OPEN) else base.copy()
    if "Current_LTP" in current.columns:
        current["LTP"] = pd.to_numeric(current.get("LTP", current["Current_LTP"]), errors="coerce")
        current["LTP"] = current["LTP"].where(current["LTP"] > 0, pd.to_numeric(current["Current_LTP"], errors="coerce"))
    else:
        current["LTP"] = pd.to_numeric(current.get("LTP", 0), errors="coerce")
    current["LTP"] = current["LTP"].fillna(0)
    if "BidQty" not in current.columns:
        current["BidQty"] = 0.0
    if "AskQty" not in current.columns:
        current["AskQty"] = 0.0
    current["BidQty"] = pd.to_numeric(current["BidQty"], errors="coerce").fillna(0)
    current["AskQty"] = pd.to_numeric(current["AskQty"], errors="coerce").fillna(0)
    current["DepthTotal"] = current["BidQty"] + current["AskQty"]
    current["PASS"] = current["LTP"].between(30, 500, inclusive="both") & (current["DepthTotal"] >= 100_000)
    return current[current["PASS"]].sort_values("DepthTotal", ascending=False, kind="stable").reset_index(drop=True)


def build_live_history_map(live_df):
    result = {}
    required = {"Symbol", "Timestamp", "LTP"}
    if live_df.empty or not required.issubset(live_df.columns):
        return result
    x = live_df[["Symbol", "Timestamp", "LTP"]].copy()
    x["_symbol"] = x["Symbol"].astype(str).map(clean_symbol)
    x["_time"] = pd.to_datetime(x["Timestamp"], errors="coerce")
    x["LTP"] = pd.to_numeric(x["LTP"], errors="coerce")
    x = x.dropna(subset=["_time", "LTP"])
    x = x[x["LTP"] > 0].sort_values(["_symbol", "_time"])
    for symbol, group in x.groupby("_symbol", sort=False):
        result[symbol] = group["LTP"].tail(60).tolist()
    return result


def render_live_dashboard():

    # Reload only the live tick dataframe on each 2-second update.
    live_now = read_csv(LIVE_TICKS)

    if not live_now.empty:
        live_now["Timestamp"] = pd.to_datetime(
            live_now["Timestamp"],
            errors="coerce"
        )
        live_now["LTP"] = pd.to_numeric(
            live_now["LTP"],
            errors="coerce"
        )


    # ------------------------------------------------------------
    # LIVE TREND HISTORY
    # Build once per 2-second dashboard update. The table uses
    # this precomputed map instead of scanning the full CSV
    # separately for every stock.
    # ------------------------------------------------------------
    live_history = build_live_history_map(
        live_now
    )

    # ------------------------------------------------------------
    # PRECOMPUTE LIVE ETQ MAPS
    # ------------------------------------------------------------
    live_etq5 = {}
    live_etq20 = {}
    live_etq60 = {}

    if not live_now.empty:
        tmp_etq = live_now.copy()

        tmp_etq["Timestamp"] = pd.to_datetime(
            tmp_etq["Timestamp"],
            errors="coerce"
        )

        tmp_etq["LTQ"] = pd.to_numeric(
            tmp_etq.get("LTQ", 0),
            errors="coerce"
        ).fillna(0)

        tmp_etq = tmp_etq.dropna(
            subset=["Timestamp", "Symbol"]
        )

        tmp_etq["_symbol"] = (
            tmp_etq["Symbol"]
            .astype(str)
            .map(clean_symbol)
        )

        tmp_etq = tmp_etq.sort_values(
            "Timestamp"
        )

        for symbol_key, grp in tmp_etq.groupby(
            "_symbol",
            sort=False
        ):
            if not symbol_key:
                continue

            qty = grp["LTQ"]

            live_etq5[symbol_key] = float(
                qty.tail(5).sum()
            )

            live_etq20[symbol_key] = float(
                qty.tail(20).sum()
            )

            live_etq60[symbol_key] = float(
                qty.tail(60).sum()
            )

    # Cache the current live snapshot for the selected-stock detail
    # panel. This avoids a second CSV scan for every 2-second cycle.
    st.session_state["stockai_live_detail_data"] = live_now
    st.session_state["stockai_live_detail_history"] = live_history
    st.session_state["stockai_live_detail_etq5"] = live_etq5
    st.session_state["stockai_live_detail_etq20"] = live_etq20
    st.session_state["stockai_live_detail_etq60"] = live_etq60

    # ------------------------------------------------------------
    # DETECT LIVE CHANGES
    # ------------------------------------------------------------
    # Compare the current quote with the previous 2-second snapshot.
    # Only changed rows receive the short value-flash animation.



    # ------------------------------------------------------------
    # BUILD QUALIFIED LIVE STOCKS
    # ------------------------------------------------------------
    # Start from the complete AI universe and apply current live values.
    live_base = ai_df.copy()

    if not live_now.empty and IS_MARKET_OPEN:
        live_base = apply_live(
            live_base,
            live_now
        )

    if "LTP" not in live_base.columns:
        if "Current_LTP" in live_base.columns:
            live_base["LTP"] = pd.to_numeric(
                live_base["Current_LTP"],
                errors="coerce"
            )
        else:
            live_base["LTP"] = 0.0

    live_base["LTP"] = pd.to_numeric(
        live_base["LTP"],
        errors="coerce"
    ).fillna(0)

    if "BidQty" not in live_base.columns:
        live_base["BidQty"] = 0.0

    if "AskQty" not in live_base.columns:
        live_base["AskQty"] = 0.0

    live_base["BidQty"] = pd.to_numeric(
        live_base["BidQty"],
        errors="coerce"
    ).fillna(0)

    live_base["AskQty"] = pd.to_numeric(
        live_base["AskQty"],
        errors="coerce"
    ).fillna(0)

    live_base["DepthTotal"] = (
        live_base["BidQty"]
        + live_base["AskQty"]
    )

    # Price screen + liquidity screen.
    live_base["Price_Filter"] = live_base[
        "LTP"
    ].between(
        30,
        500,
        inclusive="both"
    )

    live_base["Liquidity_Filter"] = (
        live_base["DepthTotal"] >= 100_000
    )

    live_passed = (
        live_base[
            live_base["Price_Filter"]
            & live_base["Liquidity_Filter"]
        ]
        .sort_values(
            "DepthTotal",
            ascending=False,
            kind="stable"
        )
        .reset_index(drop=True)
    )
    # This function is executed every 2 seconds by the Streamlit fragment.
    # Do NOT use the module-level NOW here because that value is created
    # only once when the app starts.
    current_time = datetime.now(IST)
    live_market_open = market_is_open(current_time)

    current_snapshot = {}

    if not live_passed.empty:
        for _, row in live_passed.iterrows():
            symbol_key = clean_symbol(
                row.get(
                    "_symbol",
                    row.get("Symbol", "")
                )
            )

            if not symbol_key:
                continue

            current_snapshot[symbol_key] = (
                round(
                    to_num(
                        row.get("LTP", 0)
                    ),
                    4
                ),
                round(
                    to_num(
                        row.get("BidQty", 0)
                    ),
                    2
                ),
                round(
                    to_num(
                        row.get("AskQty", 0)
                    ),
                    2
                )
            )

    previous_snapshot = st.session_state.get(
        "stockai_live_snapshot",
        {}
    )

    changed_symbols = {
        symbol
        for symbol, values in current_snapshot.items()
        if symbol in previous_snapshot
        and values != previous_snapshot[symbol]
    }

    st.session_state[
        "stockai_live_snapshot"
    ] = current_snapshot

    live_status = (
        '<span class="status-live blink">â— LIVE Â· 2 SEC</span>'
        if live_market_open
        else '<span class="status-closed">â— MARKET CLOSED Â· DATA FROZEN</span>'
    )

    # ------------------------------------------------------------
    # KPI COUNTS
    # ------------------------------------------------------------
    price_universe = ai_df.copy()

    if "Current_LTP" in price_universe.columns:
        price_universe["LTP"] = pd.to_numeric(
            price_universe["Current_LTP"],
            errors="coerce"
        )
    else:
        price_universe["LTP"] = pd.to_numeric(
            price_universe.get("LTP", 0),
            errors="coerce"
        )

    if not live_now.empty:
        live_all = apply_live(
            price_universe,
            live_now
        )
    else:
        live_all = price_universe

    live_all["LTP"] = pd.to_numeric(
        live_all["LTP"],
        errors="coerce"
    ).fillna(0)

    scanning_count = int(
        live_all["LTP"]
        .between(
            30,
            500,
            inclusive="both"
        )
        .sum()
    )

    pass_count = len(
        live_passed
    )

    cols = st.columns(6)

    kpis = [
        (
            "ã€½ SCANNING",
            f"{scanning_count:,}",
            "â‚¹30â€“â‚¹500 stocks"
        ),
        (
            "â–½ PASS SCREEN",
            f"{len(passed):,}",
            "Bid + Ask > 1L"
        ),
        (
            "â†— ETQ 5M",
            qty_format(total_5),
            "qualified stocks"
        ),
        (
            "â†— ETQ 20M",
            qty_format(total_20),
            "qualified stocks"
        ),
        (
            "â†— ETQ 60M",
            qty_format(total_60),
            "qualified stocks"
        ),
        (
            "â—‰ MARKET",
            "OPEN" if IS_MARKET_OPEN else "CLOSED",
            "09:15â€“15:30 IST"
        )
    ]

    for col, (label, value, sub) in zip(
        cols,
        kpis
    ):
        with col:
            render_html(
                f"""
                <div class="kpi">
                    <div class="kpi-label">
                        {html.escape(label)}
                    </div>
                    <div class="kpi-value">
                        {html.escape(str(value))}
                    </div>
                    <div class="kpi-sub">
                        {html.escape(sub)}
                    </div>
                </div>
                """
            )

    # ------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------
    search = st.text_input(
        "Search",
        placeholder="RELIANCE, TCS, INFY...",
        label_visibility="collapsed",
        key="live_search"
    )

    view = passed.copy()

    if search:
        view = view[
            view["Symbol"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # ------------------------------------------------------------
    # SCREEN HEADER
    # ------------------------------------------------------------
    state_text = (
        '<span class="live-dot"></span>LIVE Â· 2 SEC'
        if IS_MARKET_OPEN
        else "MARKET CLOSED Â· DATA FROZEN"
    )

    render_html(
        f"""
        <div class="screen-shell">
            <div class="screen-head">
                <div class="screen-title">
                    ðŸŽ¯ Qualified Stocks â€”
                    LTP â‚¹30â€“â‚¹500 Â· Bid/Ask &gt; 1L
                </div>
                <div class="screen-count">
                    {len(view):,} qualifying Â· {state_text}
                </div>
            </div>
        </div>
        """
    )

    # ------------------------------------------------------------
    # TABLE
    # ------------------------------------------------------------
    headers = [
        ("SYMBOL", 180),
        ("LTP", 110),
        ("SMMA 20", 110),
        ("SMMA 120", 110),
        ("AI SIGNAL", 105),
        ("ETQ 5M", 105),
        ("ETQ 20M", 110),
        ("ETQ 60M", 110),
        ("AVG LTP 20M", 125),
        ("AVG LTP 60M", 125),
        ("BID QTY", 110),
        ("ASK QTY", 110),
        ("SCREEN", 90)
    ]

    th = "".join(
        f'<th style="width:{w}px;min-width:{w}px">'
        f'{html.escape(label)}</th>'
        for label, w in headers
    )

    body = []

    ai_lookup = {
        clean_symbol(r["Symbol"]): r
        for _, r in AI_ALL.iterrows()
    }

    # No live_now filtering inside this loop.

    # Build latest live quote map ONCE. The expanded stock details use this
    # map, so expanding a stock never scans live_ticks.csv again.
    live_quote_map = {}
    if isinstance(live_now, pd.DataFrame) and not live_now.empty and "Symbol" in live_now.columns:
        _quotes = live_now.copy()
        _quotes["_clean_symbol"] = _quotes["Symbol"].astype(str).map(clean_symbol)
        if "Timestamp" in _quotes.columns:
            _quotes["Timestamp"] = pd.to_datetime(_quotes["Timestamp"], errors="coerce")
            _quotes = _quotes.sort_values("Timestamp")
        _quotes = _quotes.dropna(subset=["_clean_symbol"])
        _quotes = _quotes.drop_duplicates("_clean_symbol", keep="last")
        live_quote_map = {
            r["_clean_symbol"]: r.to_dict()
            for _, r in _quotes.iterrows()
        }

    for row in view.itertuples(
        index=False
    ):

        symbol = clean_symbol(
            getattr(row, "Symbol")
        )

        ltp = to_num(
            getattr(row, "LTP", 0)
        )

        smma20 = get_value(
            row._asdict(),
            "SMMA20",
            "SMMA_20",
            default=ltp
        )

        smma120 = get_value(
            row._asdict(),
            "SMMA120",
            "SMMA_120",
            default=ltp
        )

        trend_color = (
            "#19d3a2"
            if ltp >= smma20
            else "#ff5b62"
        )

        flash_class = (
            " value-flash"
            if symbol in changed_symbols
            else ""
        )

        ai = ai_lookup.get(symbol)

        signal = str(
            ai.get("Signal", "HOLD")
            if ai is not None
            else "HOLD"
        ).upper()

        signal_class = {
            "BUY": "buy",
            "SELL": "sell",
            "HOLD": "pass"
        }.get(
            signal,
            "pass"
        )

        e5 = to_num(
            live_etq5.get(symbol, 0)
        )

        e20 = to_num(
            live_etq20.get(symbol, 0)
        )

        e60 = to_num(
            live_etq60.get(symbol, 0)
        )

        bid = to_num(
            getattr(row, "BidQty", 0)
        )

        ask = to_num(
            getattr(row, "AskQty", 0)
        )

        vals = live_history.get(
            symbol,
            []
        )

        avg20 = (
            sum(vals[-20:]) /
            len(vals[-20:])
            if vals
            else ltp
        )

        avg60 = (
            sum(vals[-60:]) /
            len(vals[-60:])
            if vals
            else ltp
        )

        company = get_text(
            row._asdict(),
            "CompanyName",
            "Company",
            "Name",
            default=symbol
        )

        row_flash_class = (
            "row-flash"
            if symbol in changed_symbols
            else ""
        )

        body.append(
            f"""
            <tr class="{row_flash_class}">
                <td>
                    {render_inline_stock_details(
                        symbol,
                        live_quote_map.get(symbol),
                        ai
                    )}
                    <div class="company">
                        {html.escape(company)}
                    </div>
                </td>

                <td>
                    <span class="ltp live-value{flash_class}"
                          style="color:{trend_color}">
                        {money(ltp)}
                    </span>
                </td>

                <td>
                    <span class="metric">
                        {smma20:,.2f}
                    </span>
                </td>

                <td>
                    <span class="metric">
                        {smma120:,.2f}
                    </span>
                </td>

                <td>
                    <span class="signal {signal_class}">
                        {html.escape(signal)}
                    </span>
                </td>

                <td>
                    <span class="metric live-value{flash_class}">
                        {qty_format(e5)}
                    </span>
                </td>

                <td>
                    <span class="metric live-value{flash_class}">
                        {qty_format(e20)}
                    </span>
                </td>

                <td>
                    <span class="metric live-value{flash_class}">
                        {qty_format(e60)}
                    </span>
                </td>

                <td>
                    <span class="metric">
                        {money(avg20)}
                    </span>
                </td>

                <td>
                    <span class="metric">
                        {money(avg60)}
                    </span>
                </td>

                <td>
                    <span class="bid live-value{flash_class}">
                        {qty_format(bid)}
                    </span>
                </td>

                <td>
                    <span class="ask live-value{flash_class}">
                        {qty_format(ask)}
                    </span>
                </td>

                <td>
                    <span class="signal pass">
                        PASS
                    </span>
                </td>
            </tr>
            """
        )

    if not body:
        body.append(
            """
            <tr>
                <td colspan="14"
                    style="height:120px;
                           text-align:center;
                           color:#667794">
                    No stocks currently satisfy the screen.
                </td>
            </tr>
            """
        )

    frozen = (
        "LIVE"
        if IS_MARKET_OPEN
        else "FROZEN"
    )

    render_html(
        f"""
        <div class="table-scroll">
            <table class="stock-table">
                <thead>
                    <tr>{th}</tr>
                </thead>
                <tbody>
                    {''.join(body)}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Angel One Â· Real LTP history Â· 5-level market depth Â·
            AI signal engine Â· ETQ = real LTQ Â·
            Auto refresh = 2 seconds Â· Status = {frozen}
        </div>
        """
    )





def render_inline_stock_details(symbol, quote=None, ai=None):
    """
    Browser-only expandable stock details.
    The <details> element opens/closes without a Streamlit rerun.
    """
    # Do not use `or {}` with pandas objects: a pandas Series/DataFrame
    # has an ambiguous truth value.
    if quote is None:
        quote = {}
    if isinstance(quote, pd.Series):
        quote = quote.to_dict()

    if ai is None:
        ai = {}
    if isinstance(ai, pd.Series):
        ai = ai.to_dict()

    def qvalue(names, default=0):
        for name in names:
            if name in quote and pd.notna(quote[name]):
                return to_num(quote[name], default)
        return default

    def avalue(names, default=0):
        for name in names:
            if name in ai and pd.notna(ai[name]):
                return to_num(ai[name], default)
        return default

    def atext(names, default="â€”"):
        for name in names:
            if name in ai and pd.notna(ai[name]):
                return str(ai[name])
        return default

    bid_prices, ask_prices, bid_qtys, ask_qtys = [], [], [], []

    for level in range(1, 6):
        bid_prices.append(qvalue([
            f"BidPrice{level}", f"Bid_Price_{level}",
            f"BidPrice_{level}", f"bid_price_{level}"
        ]))
        ask_prices.append(qvalue([
            f"AskPrice{level}", f"Ask_Price_{level}",
            f"AskPrice_{level}", f"ask_price_{level}"
        ]))
        bid_qtys.append(qvalue([
            f"BidQty{level}", f"Bid_Qty_{level}",
            f"BidQuantity{level}", f"bid_qty_{level}"
        ]))
        ask_qtys.append(qvalue([
            f"AskQty{level}", f"Ask_Qty_{level}",
            f"AskQuantity{level}", f"ask_qty_{level}"
        ]))

    if not any(bid_qtys):
        bid_qtys[0] = qvalue(["BidQty", "Bid Qty", "BidQuantity", "TotalBuyQty"])
    if not any(ask_qtys):
        ask_qtys[0] = qvalue(["AskQty", "Ask Qty", "AskQuantity", "TotalSellQty"])

    def depth_rows(prices, qtys, cls):
        rows=[]
        for price, qty in zip(prices, qtys):
            if price or qty:
                rows.append(
                    f'<div class="depth-row"><span class="{cls}">{money(price)}</span><span>{qty_format(qty)}</span></div>'
                )
        return "".join(rows) or '<div class="depth-empty">Depth unavailable</div>'

    ltp = qvalue(["LTP", "Current_LTP"])
    signal = atext(["Signal"], "HOLD").upper()
    confidence = avalue(["Confidence", "ML_Probability"], 0)
    smma20 = avalue(["SMMA20", "smma20"], 0)
    smma120 = avalue(["SMMA120", "smma120"], 0)
    etq5 = qvalue(["ETQ_5min", "ETQ5", "ETQ_5M"])
    etq20 = qvalue(["ETQ_20min", "ETQ20", "ETQ_20M"])
    etq60 = qvalue(["ETQ_60min", "ETQ60", "ETQ_60M"])
    imbalance = qvalue(["BidAsk_Imbalance"], 0)

    signal_class = {
        "BUY": "buy",
        "SELL": "sell",
        "HOLD": "pass"
    }.get(signal, "pass")

    return f"""
    <details class="stock-inline-details">
        <summary>
            <span class="stock-arrow">â–¶</span>
            <span class="symbol">{html.escape(symbol)}</span>
        </summary>

        <div class="inline-stock-panel">
            <div class="inline-stock-top">
                <div>
                    <div class="inline-stock-title">{html.escape(symbol)} Â· LIVE ANALYSIS</div>
                    <div class="inline-stock-sub">Live values update every 2 seconds; changed values blink.</div>
                </div>
                <div class="inline-stock-price">{money(ltp)}</div>
            </div>

            <div class="inline-stock-metrics">
                <div><span>SMMA 20</span><b>{smma20:,.2f}</b></div>
                <div><span>SMMA 120</span><b>{smma120:,.2f}</b></div>
                <div><span>AI SIGNAL</span><b class="signal {signal_class}">{html.escape(signal)}</b></div>
                <div><span>CONFIDENCE</span><b>{confidence:.1f}%</b></div>
                <div><span>ETQ 5M</span><b>{qty_format(etq5)}</b></div>
                <div><span>ETQ 20M</span><b>{qty_format(etq20)}</b></div>
                <div><span>ETQ 60M</span><b>{qty_format(etq60)}</b></div>
                <div><span>BID/ASK IMBALANCE</span><b>{imbalance:.2f}</b></div>
            </div>

            <div class="inline-depth-grid">
                <div class="depth-column">
                    <div class="depth-heading bid-heading">BID DEPTH</div>
                    {depth_rows(bid_prices, bid_qtys, "depth-bid-price")}
                </div>
                <div class="depth-column">
                    <div class="depth-heading ask-heading">ASK DEPTH</div>
                    {depth_rows(ask_prices, ask_qtys, "depth-ask-price")}
                </div>
            </div>

        </div>
    </details>
    """


# ============================================================
# 2-SECOND LIVE FRAGMENT
# ============================================================
@st.fragment(run_every="2s")
def live_dashboard_fragment():
    render_live_dashboard()


# ============================================================
# AI SIGNAL ANALYSIS - EVERY SCANNED STOCK
# ============================================================
def render_ai_analysis():
    buy_count = int((AI_ALL["Signal"] == "BUY").sum()) if not AI_ALL.empty else 0
    sell_count = int((AI_ALL["Signal"] == "SELL").sum()) if not AI_ALL.empty else 0
    hold_count = int((AI_ALL["Signal"] == "HOLD").sum()) if not AI_ALL.empty else 0
    avg_conf = float(AI_ALL["Confidence"].mean()) if not AI_ALL.empty else 0

    c1,c2,c3,c4 = st.columns(4)
    stats=[("AI STOCKS",len(AI_ALL),"every â‚¹30â€“â‚¹500 stock"),("BUY",buy_count,"bullish setups"),("SELL",sell_count,"bearish setups"),("AVG CONFIDENCE",f"{avg_conf:.0f}%","signal engine")]
    for col,(lab,val,sub) in zip([c1,c2,c3,c4],stats):
        with col:
            render_html(f'<div class="ai-card"><div class="ai-label">{lab}</div><div class="ai-value">{val}</div><div class="ai-sub">{sub}</div></div>')

    st.caption("AI analysis is generated locally from SMMA crossover, LTP trend history, market depth and ETQ. It is a paper-analysis signal, not an order sent to Angel One.")

    if AI_ALL.empty:
        st.info("No â‚¹30â€“â‚¹500 stocks available for AI analysis.")
        return

    search = st.text_input("Search AI stock", placeholder="RELIANCE, TCS, INFY...", key="ai_search")
    signal_filter = st.selectbox("Signal", ["ALL","BUY","SELL","HOLD"], key="ai_filter")
    ai_view = AI_ALL.copy()
    if search:
        ai_view = ai_view[ai_view["Symbol"].str.contains(search,case=False,na=False)]
    if signal_filter != "ALL":
        ai_view = ai_view[ai_view["Signal"] == signal_filter]

    rows=[]
    for _,r in ai_view.iterrows():
        cls=r["Class"]
        rows.append(f"""
<tr>
<td><b>{html.escape(r['Symbol'])}</b></td>
<td>{money(r['LTP'])}</td>
<td>{r['SMMA20']:.2f}</td>
<td>{r['SMMA120']:.2f}</td>
<td>{r['Trend %']:+.2f}%</td>
<td>{qty_format(r['Bid Qty'])}</td>
<td>{qty_format(r['Ask Qty'])}</td>
<td>{qty_format(r['ETQ 60M'])}</td>
<td><span class="{cls}">{r['Signal']}</span></td>
<td><span class="score">{r['Score']:.0f}</span></td>
<td>{r['Confidence']:.0f}%</td>
<td><span class="reason">{html.escape(r['Reason'])}</span></td>
</tr>
""")

    render_html(f"""
<div class="ai-scroll">
<table class="ai-table">
<thead><tr>
<th>SYMBOL</th><th>LTP</th><th>SMMA 20</th><th>SMMA 120</th><th>TREND</th><th>BID QTY</th><th>ASK QTY</th><th>ETQ 60M</th><th>AI SIGNAL</th><th>SCORE</th><th>CONFIDENCE</th><th>AI REASON</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
""")

    render_stock_workspace(
        live_df=read_csv(LIVE_TICKS),
        source_df=AI_ALL,
        key_prefix="ai_workspace"
    )


# ============================================================
# TRADE LOG - EVERY STOCK, PAPER ONLY
# ============================================================
def render_trade_log():
    st.caption("Paper trade log only â€” this dashboard does not place real Angel One orders.")

    if TRADE_LOG.empty:
        st.info("No stock records available.")
        return

    log = TRADE_LOG.copy()
    log = log.sort_values(["Signal","Confidence"], ascending=[True,False])

    c1,c2,c3 = st.columns(3)
    with c1:
        st.metric("Stocks Logged", len(log))
    with c2:
        st.metric("Paper BUY", int((log["Signal"]=="BUY").sum()))
    with c3:
        st.metric("Paper SELL", int((log["Signal"]=="SELL").sum()))

    signal_filter = st.selectbox("Trade signal", ["ALL","BUY","SELL","HOLD"], key="trade_filter")
    search = st.text_input("Search trade log", placeholder="RELIANCE, TCS, INFY...", key="trade_search")

    if signal_filter != "ALL":
        log=log[log["Signal"]==signal_filter]
    if search:
        log=log[log["Symbol"].str.contains(search,case=False,na=False)]

    rows=[]
    for _,r in log.iterrows():
        cls={"BUY":"ai-buy","SELL":"ai-sell","HOLD":"ai-hold"}.get(r["Signal"],"")
        rows.append(f"""
<tr>
<td>{html.escape(str(r['Time']))}</td>
<td><b>{html.escape(str(r['Symbol']))}</b></td>
<td><span class="{cls}">{html.escape(str(r['Signal']))}</span></td>
<td>{r['Confidence']:.0f}%</td>
<td>{money(r['LTP'])}</td>
<td>{money(r['Entry'])}</td>
<td>{money(r['Stop Loss'])}</td>
<td>{money(r['Target'])}</td>
<td>1:{r['R:R']:.2f}</td>
<td>{html.escape(str(r['Status']))}</td>
<td>{html.escape(str(r['Reason']))}</td>
</tr>
""")

    render_html(f"""
<div class="trade-scroll">
<table class="trade-table">
<thead><tr><th>TIME</th><th>SYMBOL</th><th>SIGNAL</th><th>CONF.</th><th>LTP</th><th>ENTRY</th><th>STOP LOSS</th><th>TARGET</th><th>R:R</th><th>STATUS</th><th>REASON</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
""")

    render_stock_workspace(
        live_df=read_csv(LIVE_TICKS),
        source_df=AI_ALL,
        key_prefix="trade_workspace"
    )


# ============================================================
# STOCK DETAIL
# ============================================================
def render_stock_detail():
    symbols = AI_ALL["Symbol"].tolist() if not AI_ALL.empty else []
    if not symbols:
        st.info("No stocks available.")
        return

    selected = st.selectbox("Select stock", symbols, key="detail_symbol")
    r = AI_ALL[AI_ALL["Symbol"] == selected].iloc[0]

    render_html(f"""
<div class="detail-box">
<div class="detail-title">{html.escape(selected)}</div>
<div class="detail-sub">AI Signal + live market detail</div>
<div class="detail-metric">LTP: <b>{money(r['LTP'])}</b></div>
<div class="detail-metric">AI Signal: <b>{html.escape(r['Signal'])}</b></div>
<div class="detail-metric">Confidence: <b>{r['Confidence']:.0f}%</b></div>
<div class="detail-metric">Score: <b>{r['Score']:.0f}/100</b></div>
<div class="detail-metric">SMMA 20: <b>{r['SMMA20']:.2f}</b></div>
<div class="detail-metric">SMMA 120: <b>{r['SMMA120']:.2f}</b></div>
<div class="detail-metric">Trend: <b>{r['Trend %']:+.2f}%</b></div>
<div class="detail-metric">Bid Qty: <b>{qty_format(r['Bid Qty'])}</b></div>
<div class="detail-metric">Ask Qty: <b>{qty_format(r['Ask Qty'])}</b></div>
<div class="detail-metric">ETQ 5M: <b>{qty_format(r['ETQ 5M'])}</b></div>
<div class="detail-metric">ETQ 20M: <b>{qty_format(r['ETQ 20M'])}</b></div>
<div class="detail-metric">ETQ 60M: <b>{qty_format(r['ETQ 60M'])}</b></div>
<div class="detail-metric">Entry: <b>{money(r['Entry'])}</b> Â· Stop: <b>{money(r['Stop Loss'])}</b> Â· Target: <b>{money(r['Target'])}</b></div>
<div class="detail-metric">AI Reason: {html.escape(r['Reason'])}</div>
</div>
""")

    detail_live = read_csv(LIVE_TICKS)

    vals = []

    if not detail_live.empty:
        detail_live["Timestamp"] = pd.to_datetime(
            detail_live["Timestamp"],
            errors="coerce"
        )
        detail_live["LTP"] = pd.to_numeric(
            detail_live["LTP"],
            errors="coerce"
        )

        vals = (
            detail_live[
                detail_live["Symbol"]
                .astype(str)
                .map(clean_symbol)
                .eq(clean_symbol(selected))
            ]
            .sort_values("Timestamp")["LTP"]
            .dropna()
            .tail(30)
            .tolist()
        )

    if len(vals) < 2:
        vals = history.get(
            selected,
            []
        )

    render_html(
        sparkline(
            vals,
            "#19d3a2"
        )
    )


# ============================================================
# UNIFIED STOCK WORKSPACE
# Every stock is available for AI analysis, paper trade log,
# and stock detail from every dashboard section.
# ============================================================
def render_stock_workspace(live_df=None, source_df=None, key_prefix="workspace"):
    base = source_df.copy() if isinstance(source_df, pd.DataFrame) else AI_ALL.copy()

    if base.empty or "Symbol" not in base.columns:
        return

    symbols = (
        base["Symbol"].astype(str).map(clean_symbol)
        .dropna().drop_duplicates().tolist()
    )

    if not symbols:
        return

    live = live_df.copy() if isinstance(live_df, pd.DataFrame) else pd.DataFrame()

    if not live.empty:
        if "Timestamp" in live.columns:
            live["Timestamp"] = pd.to_datetime(live["Timestamp"], errors="coerce")
        if "LTP" in live.columns:
            live["LTP"] = pd.to_numeric(live["LTP"], errors="coerce")

    selected = st.selectbox(
        "Stock workspace",
        symbols,
        key=f"{key_prefix}_stock",
        help="Select any stock to view AI signal, paper trade log and stock detail together."
    )

    selected_key = clean_symbol(selected)
    ai_rows = base[
        base["Symbol"].astype(str).map(clean_symbol).eq(selected_key)
    ]

    if ai_rows.empty:
        st.info(f"No AI record available for {selected}.")
        return

    ai = ai_rows.iloc[0]

    ltp = to_num(ai.get("LTP", 0))
    bid = to_num(ai.get("Bid Qty", ai.get("BidQty", 0)))
    ask = to_num(ai.get("Ask Qty", ai.get("AskQty", 0)))

    selected_live = pd.DataFrame()
    if not live.empty and "Symbol" in live.columns:
        selected_live = live[
            live["Symbol"].astype(str).map(clean_symbol).eq(selected_key)
        ].sort_values("Timestamp")

        if not selected_live.empty:
            q = selected_live.iloc[-1]
            ltp = to_num(q.get("LTP", ltp))
            bid = to_num(q.get("BidQty", bid))
            ask = to_num(q.get("AskQty", ask))

    signal = str(ai.get("Signal", "HOLD")).upper()
    confidence = to_num(ai.get("Confidence", 0))
    score = to_num(ai.get("Score", 0))
    trend_pct = to_num(ai.get("Trend %", 0))

    trade = None
    if not TRADE_LOG.empty and "Symbol" in TRADE_LOG.columns:
        tr = TRADE_LOG[
            TRADE_LOG["Symbol"].astype(str).map(clean_symbol).eq(selected_key)
        ]
        if not tr.empty:
            trade = tr.sort_values("Time", ascending=False).iloc[0]

    vals = (
        pd.to_numeric(selected_live["LTP"], errors="coerce")
        .dropna().tail(60).tolist()
        if not selected_live.empty and "LTP" in selected_live.columns
        else []
    )

    if len(vals) < 2:
        vals = history.get(selected_key, history.get(selected, []))

    render_html(f"""
    <div class="workspace-grid">
        <div class="workspace-card">
            <div class="workspace-label">AI SIGNAL ANALYSIS</div>
            <div class="workspace-title">{html.escape(selected)}</div>
            <div class="workspace-value">{html.escape(signal)}</div>
            <div class="workspace-detail">
                Confidence: <b>{confidence:.0f}%</b><br>
                Score: <b>{score:.0f}/100</b><br>
                Trend: <b>{trend_pct:+.2f}%</b><br>
                Reason: {html.escape(str(ai.get("Reason", "â€”")))}
            </div>
        </div>

        <div class="workspace-card">
            <div class="workspace-label">TRADE LOG Â· PAPER</div>
            <div class="workspace-title">{html.escape(selected)}</div>
            {
                (
                    f'<div class="workspace-value">{html.escape(str(trade.get("Signal", signal)))}</div>'
                    f'<div class="workspace-detail">'
                    f'Entry: <b>{money(trade.get("Entry", ltp))}</b><br>'
                    f'Stop Loss: <b>{money(trade.get("Stop Loss", 0))}</b><br>'
                    f'Target: <b>{money(trade.get("Target", 0))}</b><br>'
                    f'Status: <b>{html.escape(str(trade.get("Status", "PAPER")))}</b>'
                    f'</div>'
                )
                if trade is not None
                else '<div class="workspace-muted">No paper trade record yet.</div>'
            }
        </div>

        <div class="workspace-card">
            <div class="workspace-label">STOCK DETAIL</div>
            <div class="workspace-title">{html.escape(selected)}</div>
            <div class="workspace-detail">
                LTP: <b>{money(ltp)}</b><br>
                SMMA 20: <b>{to_num(ai.get("SMMA20", ltp)):.2f}</b><br>
                SMMA 120: <b>{to_num(ai.get("SMMA120", ltp)):.2f}</b><br>
                Bid Qty: <b>{qty_format(bid)}</b><br>
                Ask Qty: <b>{qty_format(ask)}</b><br>
                ETQ 60M: <b>{qty_format(ai.get("ETQ 60M", 0))}</b>
            </div>
        </div>
    </div>
    """)

    if len(vals) >= 2:
        graph_color = (
            "#19d3a2" if signal == "BUY"
            else "#ff5b62" if signal == "SELL"
            else "#6f8cff"
        )
        render_html(f"""
        <div class="detail-box" style="margin-top:12px;">
            <div class="detail-title">{html.escape(selected)} Â· LIVE LTP TREND</div>
            <div class="detail-sub">Latest real LTP ticks</div>
            {sparkline(vals, graph_color)}
        </div>
        """)



# ============================================================
# ONLY LIVE DASHBOARD
# ============================================================

live_dashboard_fragment()