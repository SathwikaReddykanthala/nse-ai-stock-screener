from pathlib import Path
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
import html
import math
import textwrap
from urllib.parse import quote

import pandas as pd
import streamlit as st

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
    page_title="NSE Stock Screener",
    page_icon="📊",
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
   STOCKAI — BLACK TERMINAL THEME
   VISUAL-ONLY UPDATE: DASHBOARD LOGIC IS UNCHANGED
   ============================================================ */

:root {
    --black: #000000;
    --panel: #070707;
    --panel2: #0b0b0b;
    --panel3: #111111;
    --border: #242424;
    --border2: #303030;
    --white: #f5f7fa;
    --text: #d8dde5;
    --muted: #7d8795;
    --green: #18e6a4;
    --green-bg: #06251d;
    --red: #ff5964;
    --red-bg: #2a0b10;
    --yellow: #f5c84c;
    --blue: #6e8cff;
}

/* ============================================================
   FULL PAGE BLACK
   ============================================================ */

html,
body,
.stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stHeader"],
[data-testid="stDecoration"],
section.main,
.main,
.block-container,
footer {
    background: #000000 !important;
    background-color: #000000 !important;
    color: var(--white) !important;
}

html,
body,
.stApp,
[data-testid="stApp"] {
    font-family:
        Inter,
        ui-sans-serif,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif !important;
}

* {
    box-sizing: border-box;
}

.block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 14px 12px 42px !important;
    margin: 0 !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
    background: #000000 !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 12px !important;
    background: #000000 !important;
}

header[data-testid="stHeader"] {
    background: #000000 !important;
    height: 0 !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

section[data-testid="stSidebar"] {
    background: #000000 !important;
}

section[data-testid="stSidebar"] > div {
    background: #000000 !important;
}

/* ============================================================
   TEXT
   ============================================================ */

h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, span, label, small {
    color: inherit;
}

/* ============================================================
   TOP BAR / HEADER
   ============================================================ */

.topbar {
    background: #000000 !important;
    border: 1px solid #171717 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 35px rgba(0,0,0,.45) !important;
}

.brand-title,
.logo-text {
    color: #ffffff !important;
    font-weight: 900 !important;
    letter-spacing: -.3px !important;
}

.brand-sub {
    color: #707b89 !important;
}

.clock {
    color: #8d98a7 !important;
    font-family: "JetBrains Mono", Consolas, monospace !important;
}

.status-live {
    color: var(--green) !important;
    background: var(--green-bg) !important;
    border: 1px solid #0c735b !important;
}

.status-closed {
    color: #ff6b75 !important;
    background: var(--red-bg) !important;
    border: 1px solid #7d2637 !important;
}

/* ============================================================
   DASHBOARD NAVIGATION
   ============================================================ */

div[data-testid="stRadio"] {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 0 12px !important;
    overflow: visible !important;
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
    box-sizing: border-box !important;
    background: #080808 !important;
    border: 1px solid #292929 !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    color: #8f99a7 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    white-space: nowrap !important;
    transition: all .18s ease !important;
}

div[data-testid="stRadio"] label:hover {
    background: #111111 !important;
    border-color: #414141 !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}

div[data-testid="stRadio"] label:has(input:checked) {
    background: #071d17 !important;
    border-color: #18b88c !important;
    color: #18e6a4 !important;
    box-shadow:
        inset 0 0 0 1px rgba(24,230,164,.12),
        0 0 20px rgba(24,230,164,.06) !important;
}

div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span {
    color: inherit !important;
    font-weight: inherit !important;
}

/* ============================================================
   KPI CARDS
   ============================================================ */

.kpi,
.metric-card {
    background: #050505 !important;
    border: 1px solid #242424 !important;
    border-radius: 13px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.015) !important;
}

.kpi:hover,
.metric-card:hover {
    border-color: #3a3a3a !important;
}

.kpi-label,
.metric-label {
    color: #7f8997 !important;
    font-size: 10px !important;
    font-weight: 900 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}

.kpi-value,
.metric-value {
    color: #ffffff !important;
    font-weight: 950 !important;
}

.kpi-sub,
.metric-sub {
    color: #687380 !important;
}

/* ============================================================
   WORKSPACE / GENERAL CARDS
   ============================================================ */

.workspace-card,
.ai-card,
.detail-box,
.live-stock-detail,
.screen-shell {
    background: #050505 !important;
    border: 1px solid #242424 !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    box-shadow: 0 10px 25px rgba(0,0,0,.25) !important;
}

.workspace-label,
.ai-label {
    color: #808a98 !important;
    font-weight: 900 !important;
    letter-spacing: .08em !important;
}

.workspace-title,
.detail-title {
    color: #ffffff !important;
    font-weight: 900 !important;
}

.workspace-muted,
.ai-sub,
.detail-sub {
    color: #727d8a !important;
}

.workspace-value,
.ai-buy {
    color: var(--green) !important;
}

.ai-sell {
    color: var(--red) !important;
}

.ai-hold {
    color: var(--yellow) !important;
}

/* ============================================================
   TABLES
   ============================================================ */

.stock-table,
.ai-table,
.trade-table {
    background: #030303 !important;
    color: var(--text) !important;
}

.stock-table th,
.ai-table th,
.trade-table th {
    background: #0c0c0c !important;
    color: #858f9c !important;
    border-bottom: 1px solid #292929 !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
}

.stock-table td,
.ai-table td,
.trade-table td {
    background: #030303 !important;
    color: #cbd1da !important;
    border-bottom: 1px solid #171717 !important;
}

.stock-table tr:hover td,
.ai-table tr:hover td,
.trade-table tr:hover td {
    background: #0b0b0b !important;
}

.symbol,
.stock-table .symbol {
    color: #ffffff !important;
    font-weight: 950 !important;
}

.company {
    color: #717c89 !important;
}

.ltp {
    color: #ffffff !important;
    font-weight: 950 !important;
}

.metric {
    color: #c5ccd5 !important;
}

.bid,
.buy {
    color: var(--green) !important;
}

.ask,
.sell {
    color: var(--red) !important;
}

/* ============================================================
   SIGNAL PILLS
   ============================================================ */

.signal,
.pass,
.buy,
.sell {
    font-weight: 900 !important;
}

.pass,
.buy {
    color: var(--green) !important;
    background: var(--green-bg) !important;
    border: 1px solid #0c735b !important;
}

.sell {
    color: var(--red) !important;
    background: var(--red-bg) !important;
    border: 1px solid #7d2637 !important;
}

/* ============================================================
   INPUTS / SELECTS / SEARCH
   ============================================================ */

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] input,
div[data-baseweb="select"] > div {
    background: #080808 !important;
    color: #f5f7fa !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 9px !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: #18b88c !important;
    box-shadow: 0 0 0 1px #18b88c !important;
}

[data-testid="stWidgetLabel"] p {
    color: #9aa3af !important;
}

/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button {
    background: #090909 !important;
    color: #e0e5eb !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 9px !important;
    font-weight: 800 !important;
    transition: all .18s ease !important;
}

.stButton > button:hover {
    background: #10251f !important;
    color: var(--green) !important;
    border-color: #198e70 !important;
}

.stButton > button:focus {
    box-shadow: 0 0 0 1px #18b88c !important;
}

/* ============================================================
   STOCK DETAIL / INLINE PANELS
   ============================================================ */

.inline-stock-panel,
.live-detail-card {
    background: #090909 !important;
    border: 1px solid #282828 !important;
    color: var(--text) !important;
}

.inline-stock-metrics > div {
    background: #0d0d0d !important;
    border: 1px solid #242424 !important;
}

.inline-stock-metrics span,
.live-detail-label {
    color: #737e8c !important;
}

.inline-stock-metrics b,
.live-detail-value {
    color: #e8ecf1 !important;
}

.expanded-stock-row > td,
.expanded-stock-row .inline-depth-panel {
    background: #080808 !important;
}

/* ============================================================
   DATAFRAME / ALERTS
   ============================================================ */

[data-testid="stDataFrame"] {
    background: #030303 !important;
    border: 1px solid #242424 !important;
    border-radius: 10px !important;
}

div[data-testid="stAlert"] {
    background: #080808 !important;
    border-color: #2a2a2a !important;
    color: #d9dee6 !important;
}

/* ============================================================
   FOOTER
   ============================================================ */

.footer {
    background: #000000 !important;
    color: #5f6976 !important;
    border-top: 1px solid #1b1b1b !important;
}

/* ============================================================
   SCROLLBAR
   ============================================================ */

* {
    scrollbar-width: thin;
    scrollbar-color: #3a3a3a #050505;
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #050505;
}

::-webkit-scrollbar-thumb {
    background: #3a3a3a;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555555;
}

/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 1000px) {
    div[data-testid="stRadio"] > div {
        overflow-x: auto !important;
    }

    div[data-testid="stRadio"] label {
        min-width: 180px !important;
    }
}

@media (max-width: 700px) {
    .block-container {
        padding: 10px 8px 30px !important;
    }

    div[data-testid="stRadio"] label {
        min-width: 165px !important;
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
    return f"₹{to_num(value):,.2f}"


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
# LOAD DATA
# ============================================================
# ============================================================
# LOAD STOCKAI PIPELINE FILES
# ============================================================

ai_df = read_csv(LIVE_AI)
smma_df = read_csv(LIVE_SMMA)
features_df = read_csv(LIVE_FEATURES)
live = read_csv(LIVE_TICKS)

# ============================================================
# LIVE DATA STATUS
# ============================================================

if ai_df.empty:
    st.warning(
        "Live AI signals are not currently available. "
        "The live signal engine must be running to generate "
        "real-time signals."
    )

    ai_df = pd.DataFrame()

if smma_df.empty:
    st.warning(
        "Live SMMA data is not currently available."
    )

    smma_df = pd.DataFrame()

if features_df.empty:
    st.warning(
        "Live ML features are not currently available."
    )

    features_df = pd.DataFrame()

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

if "Current_LTP" in df.columns:
    df["LTP"] = pd.to_numeric(
        df["Current_LTP"],
        errors="coerce"
    )
else:
    df["LTP"] = pd.to_numeric(
        df.get("LTP", 0),
        errors="coerce"
    )

df["Signal"] = (
    df.get("Signal", "NONE")
    .fillna("NONE")
    .astype(str)
    .str.upper()
)

df["Decision"] = (
    df.get("Decision", "AVOID")
    .fillna("AVOID")
    .astype(str)
    .str.upper()
)

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

df["Signal"] = (
    df.get("Signal", "NONE")
    .fillna("NONE")
    .astype(str)
    .str.upper()
)

df["Decision"] = (
    df.get("Decision", "AVOID")
    .fillna("AVOID")
    .astype(str)
    .str.upper()
)
# ============================================================
# NORMALIZE
# ============================================================
df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")
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
        '<span class="status-live blink">● LIVE · 2 SEC</span>'
        if market_is_open(header_now)
        else '<span class="status-closed">● MARKET CLOSED · DATA FROZEN</span>'
    )

    render_html(f"""
    <div class="topbar">
        <div class="brand">
            <div class="logo">▥</div>
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
# NAV
# ============================================================
page = st.radio(
    "Dashboard sections",
    [
        "Live Dashboard",
        "AI Signal Analysis",
        "Trade Log",
        "Stock Detail"
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="dashboard_page"
)

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
        '<span class="status-live blink">● LIVE · 2 SEC</span>'
        if live_market_open
        else '<span class="status-closed">● MARKET CLOSED · DATA FROZEN</span>'
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
            "〽 SCANNING",
            f"{scanning_count:,}",
            "₹30–₹500 stocks"
        ),
        (
            "▽ PASS SCREEN",
            f"{len(passed):,}",
            "Bid + Ask > 1L"
        ),
        (
            "↗ ETQ 5M",
            qty_format(total_5),
            "qualified stocks"
        ),
        (
            "↗ ETQ 20M",
            qty_format(total_20),
            "qualified stocks"
        ),
        (
            "↗ ETQ 60M",
            qty_format(total_60),
            "qualified stocks"
        ),
        (
            "◉ MARKET",
            "OPEN" if IS_MARKET_OPEN else "CLOSED",
            "09:15–15:30 IST"
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
        '<span class="live-dot"></span>LIVE · 2 SEC'
        if IS_MARKET_OPEN
        else "MARKET CLOSED · DATA FROZEN"
    )

    render_html(
        f"""
        <div class="screen-shell">
            <div class="screen-head">
                <div class="screen-title">
                    🎯 Qualified Stocks —
                    LTP ₹30–₹500 · Bid/Ask &gt; 1L
                </div>
                <div class="screen-count">
                    {len(view):,} qualifying · {state_text}
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
            Angel One · Real LTP history · 5-level market depth ·
            AI signal engine · ETQ = real LTQ ·
            Auto refresh = 2 seconds · Status = {frozen}
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

    def atext(names, default="—"):
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
            <span class="stock-arrow">▶</span>
            <span class="symbol">{html.escape(symbol)}</span>
        </summary>

        <div class="inline-stock-panel">
            <div class="inline-stock-top">
                <div>
                    <div class="inline-stock-title">{html.escape(symbol)} · LIVE ANALYSIS</div>
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
    stats=[("AI STOCKS",len(AI_ALL),"every ₹30–₹500 stock"),("BUY",buy_count,"bullish setups"),("SELL",sell_count,"bearish setups"),("AVG CONFIDENCE",f"{avg_conf:.0f}%","signal engine")]
    for col,(lab,val,sub) in zip([c1,c2,c3,c4],stats):
        with col:
            render_html(f'<div class="ai-card"><div class="ai-label">{lab}</div><div class="ai-value">{val}</div><div class="ai-sub">{sub}</div></div>')

    st.caption("AI analysis is generated locally from SMMA crossover, LTP trend history, market depth and ETQ. It is a paper-analysis signal, not an order sent to Angel One.")

    if AI_ALL.empty:
        st.info("No ₹30–₹500 stocks available for AI analysis.")
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
    st.caption("Paper trade log only — this dashboard does not place real Angel One orders.")

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
<div class="detail-metric">Entry: <b>{money(r['Entry'])}</b> · Stop: <b>{money(r['Stop Loss'])}</b> · Target: <b>{money(r['Target'])}</b></div>
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
                Reason: {html.escape(str(ai.get("Reason", "—")))}
            </div>
        </div>

        <div class="workspace-card">
            <div class="workspace-label">TRADE LOG · PAPER</div>
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
            <div class="detail-title">{html.escape(selected)} · LIVE LTP TREND</div>
            <div class="detail-sub">Latest real LTP ticks</div>
            {sparkline(vals, graph_color)}
        </div>
        """)



# ============================================================
# PAGE ROUTING
# ============================================================
if page == "Live Dashboard":
    live_dashboard_fragment()
    # Selected stock details are rendered directly under the expanded row.
elif page == "AI Signal Analysis":
    render_ai_analysis()
elif page == "Trade Log":
    render_trade_log()
else:
    render_stock_detail()