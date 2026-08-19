from pathlib import Path
from datetime import datetime
import math
import html as html_lib

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:
    go = None


# ============================================================
# STOCKAI — VIDEO-MATCHED NSE DASHBOARD
# ============================================================

st.set_page_config(
    page_title="NSE Stock Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


# ============================================================
# GLOBAL CSS — MATCHES THE UPLOADED SCREEN RECORDING
# ============================================================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
[data-testid="stMain"], .main, .block-container {
    background: #000000 !important;
}

[data-testid="stHeader"] {
    background: #000000 !important;
}
:root {
    --bg: #000000;
    --panel: #071126;
    --panel2: #0a142b;
    --line: #172642;
    --text: #e8eefb;
    --muted: #71819f;
    --blue: #3b82f6;
    --green: #19d3a2;
    --red: #ff5b62;
    --yellow: #f5c542;
}

.stApp {
    background: #000000;
    color: var(--text);
}

.block-container {
    max-width: 100% !important;
    padding: 8px 14px 30px !important;
}

header[data-testid="stHeader"] {
    background: var(--bg) !important;
}

section[data-testid="stSidebar"] {
    display: none;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.28rem !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.35rem !important;
}

.stButton button {
    background: #071126 !important;
    color: #91a0bd !important;
    border: 1px solid #172642 !important;
    border-radius: 8px !important;
    font-size: 10px !important;
    min-height: 27px !important;
    padding: 3px 8px !important;
}

.stButton button:hover {
    border-color: #3b82f6 !important;
    color: #e8eefb !important;
}

div[data-baseweb="select"] > div {
    background: #071126 !important;
    border-color: #172642 !important;
    color: #e8eefb !important;
}

input {
    background: #071126 !important;
    color: #e8eefb !important;
}

label {
    color: #8b9ab6 !important;
    font-size: 10px !important;
}

[data-testid="stDataFrame"] {
    background: #071126 !important;
}

/* Header */
.app-header {
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #172642;
    margin-bottom: 3px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.brand-icon {
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    box-shadow: 0 4px 16px rgba(37,99,235,.28);
}

.brand-title {
    font-size: 17px;
    font-weight: 800;
    line-height: 20px;
    color: #eef3ff;
}

.brand-subtitle {
    font-size: 10px;
    color: #71819f;
}

.clock {
    color: #71819f;
    font-size: 12px;
    font-family: monospace;
}

.pause {
    margin-left: 12px;
    border: 1px solid #7f2634;
    color: #ff6a72;
    background: #260d17;
    border-radius: 8px;
    padding: 8px 12px;
}

/* top nav */
.nav {
    height: 39px;
    display: flex;
    align-items: end;
    gap: 25px;
    border-bottom: 1px solid #172642;
    margin-bottom: 9px;
}

.nav-item {
    padding: 7px 3px 9px;
    color: #667895;
    font-size: 11px;
}

.nav-item.active {
    color: #59a3ff;
    border-bottom: 2px solid #3b82f6;
}

/* KPI */
.kpi {
    background: #000000;
    border: 1px solid #172642;
    border-radius: 11px;
    min-height: 72px;
    padding: 10px 12px;
}

.kpi-label {
    color: #6e80a1;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .3px;
}

.kpi-value {
    color: #f1f5ff;
    font-size: 21px;
    font-weight: 800;
    line-height: 27px;
    margin-top: 4px;
}

.kpi-value.green { color: #20d8a6; }
.kpi-value.red { color: #ff5d63; }
.kpi-value.yellow { color: #f5c542; }

.kpi-sub {
    color: #5f7191;
    font-size: 8px;
}

/* section */
.section {
    background: #000000;
    border: 1px solid #172642;
    border-radius: 10px;
    overflow: hidden;
}

.section-head {
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    border-bottom: 1px solid #172642;
}

.section-title {
    font-size: 12px;
    font-weight: 800;
    color: #e9effb;
}

.section-count {
    color: #71819f;
    font-size: 10px;
}

/* table */
.tbl-wrap {
    overflow-x: auto;
    width: 100%;
}

.stock-table {
    width: 100%;
    min-width: 1200px;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 10px;
}

.stock-table th {
    background: #000000;
    color: #8292af;
    font-size: 8px;
    font-weight: 800;
    padding: 8px 5px;
    text-align: center;
    white-space: nowrap;
    border-bottom: 1px solid #172642;
}

.stock-table td {
    color: #bdc8da;
    padding: 7px 5px;
    text-align: center;
    white-space: nowrap;
    border-bottom: 1px solid #101d35;
}

.stock-table tr:hover td {
    background: #0a1730;
}

.symbol-cell {
    text-align: left !important;
    width: 130px;
}

.symbol-main {
    color: #e9effb;
    font-size: 11px;
    font-weight: 800;
}

.symbol-sub {
    color: #647594;
    font-size: 8px;
    margin-top: 2px;
}

.ltp {
    font-size: 11px;
    font-weight: 800;
}

.green { color: #19d3a2 !important; }
.red { color: #ff5b62 !important; }
.blue { color: #4da3ff !important; }
.yellow { color: #f5c542 !important; }

.badge {
    display: inline-block;
    min-width: 49px;
    padding: 4px 7px;
    border-radius: 5px;
    font-size: 8px;
    font-weight: 800;
}

.badge-buy {
    color: #1ee1ad;
    background: #062b25;
    border: 1px solid #0c6a59;
}

.badge-sell {
    color: #ff6870;
    background: #2b1019;
    border: 1px solid #7f2635;
}

.badge-pass {
    color: #20d9aa;
    background: #06251f;
    border: 1px solid #0c5548;
}

.qty-buy { color: #19d3a2; }
.qty-sell { color: #ff5b62; }

.spark {
    width: 72px;
    height: 23px;
    display: inline-block;
}

/* details */
.detail {
    background: #000000;
    border-top: 1px solid #172642;
    border-bottom: 1px solid #172642;
    padding: 10px 12px;
}

.detail-title {
    color: #e7eefb;
    font-size: 10px;
    font-weight: 800;
}

.depth-title {
    font-size: 9px;
    font-weight: 800;
    margin-bottom: 5px;
}

.depth-row {
    display: flex;
    justify-content: space-between;
    font-size: 8px;
    line-height: 17px;
}

.depth-bid { color: #19d3a2; }
.depth-ask { color: #ff5b62; }

.page-info {
    text-align: center;
    color: #71819f;
    font-size: 10px;
    padding-top: 6px;
}

.chart-panel {
    background: #000000;
    border: 1px solid #172642;
    border-radius: 10px;
    padding: 5px;
}

.info-panel {
    background: #000000;
    border: 1px solid #172642;
    border-radius: 10px;
    padding: 12px;
    color: #91a0bd;
    font-size: 9px;
    line-height: 1.65;
}

.trade-row {
    border-bottom: 1px solid #14213a;
    padding: 8px 10px;
    font-size: 9px;
}

.live-dot {
    color: #19d3a2;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def clean_col(c):
    return str(c).strip()


def read_csv_safe(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def find_screen_file():
    files = []
    for p in DATASET.rglob("*.csv"):
        name = p.name.lower()
        if "screen" in name:
            files.append(p)
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def find_live_file():
    candidates = []
    for p in DATASET.rglob("*.csv"):
        name = p.name.lower()
        if any(x in name for x in ("tick", "live", "feed")):
            candidates.append(p)

    for p in sorted(candidates, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            cols = {str(c).strip().lower() for c in pd.read_csv(p, nrows=0).columns}
            if {"symbol", "timestamp"}.issubset(cols):
                return p
        except Exception:
            pass
    return None


def num(row, col, default=0.0):
    try:
        x = row[col]
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def text(row, col, default=""):
    try:
        x = row[col]
        if pd.isna(x):
            return default
        return str(x)
    except Exception:
        return default


def qty_lakh(x):
    try:
        return f"{float(x) / 100000:.2f}L"
    except Exception:
        return "0.00L"


def price(x):
    try:
        return f"₹{float(x):,.2f}"
    except Exception:
        return "-"


def symbol_short(x):
    return (
        str(x)
        .replace("NSE:", "")
        .replace("-EQ", "")
        .strip()
    )


def signal_of(row):
    s = text(row, "Signal", "PASS").upper().strip()
    if s in ("BUY", "SELL"):
        return s
    return "PASS"


def trend_of(row):
    smma20 = num(row, "SMMA20")
    smma120 = num(row, "SMMA120")
    ltp = num(row, "LTP")

    if smma20 > smma120:
        return "BULL"
    if smma20 < smma120:
        return "BEAR"
    if ltp >= smma20:
        return "BULL"
    return "BEAR"


def sparkline(values, color):
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""

    mn = min(vals)
    mx = max(vals)
    if mx == mn:
        mx = mn + 1

    pts = []
    for i, v in enumerate(vals):
        x = 2 + i * 68 / max(1, len(vals) - 1)
        y = 20 - (v - mn) * 17 / (mx - mn)
        pts.append(f"{x:.1f},{y:.1f}")

    return f"""
    <svg class="spark" viewBox="0 0 72 23">
      <polyline points="{' '.join(pts)}"
        fill="none" stroke="{color}" stroke-width="1.5"/>
    </svg>
    """


def calculate_etq(live, symbol):
    if live.empty:
        return None

    cols = {str(c).strip().lower(): c for c in live.columns}
    required = ["symbol", "timestamp", "ltq"]
    if not all(x in cols for x in required):
        return None

    x = live.rename(columns={
        cols["symbol"]: "Symbol",
        cols["timestamp"]: "Timestamp",
        cols["ltq"]: "LTQ",
    }).copy()

    x["Timestamp"] = pd.to_datetime(x["Timestamp"], errors="coerce")
    x["LTQ"] = pd.to_numeric(x["LTQ"], errors="coerce").fillna(0)

    target = symbol_short(symbol).upper()
    x["_sym"] = (
        x["Symbol"].astype(str)
        .str.replace("NSE:", "", regex=False)
        .str.replace("-EQ", "", regex=False)
        .str.strip().str.upper()
    )

    x = x[x["_sym"] == target].dropna(subset=["Timestamp"])
    if x.empty:
        return None

    latest = x["Timestamp"].max()

    return {
        "ETQ_5min": x.loc[x["Timestamp"] >= latest - pd.Timedelta(minutes=5), "LTQ"].sum(),
        "ETQ_20min": x.loc[x["Timestamp"] >= latest - pd.Timedelta(minutes=20), "LTQ"].sum(),
        "ETQ_60min": x.loc[x["Timestamp"] >= latest - pd.Timedelta(minutes=60), "LTQ"].sum(),
    }


# ============================================================
# LOAD SCREEN DATA
# ============================================================

screen_file = find_screen_file()

if screen_file is None:
    st.error("No screener CSV found. Run final_screener.py first.")
    st.stop()

df = read_csv_safe(screen_file)

if df.empty:
    st.error("The screener CSV is empty.")
    st.stop()

df.columns = [clean_col(c) for c in df.columns]

# Numeric columns
for c in [
    "LTP", "BidPrice", "BidQty", "AskPrice", "AskQty",
    "TotalBuyQty", "TotalSellQty", "SMMA20", "SMMA120",
    "Current_LTQ", "LTQ_2min_avg", "LTQ_5min_avg",
    "ETQ_5min", "ETQ_20min", "ETQ_60min",
    "Average_LTP_20min", "Average_LTP_60min",
    "ML_Confidence", "ML_Probability", "Volume"
]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# Hard price filter
if "LTP" in df.columns:
    df = df[df["LTP"].between(30, 500)].copy()

# Remove NONE
if "Signal" in df.columns:
    df["Signal"] = df["Signal"].astype(str).str.upper().str.strip()
    df["Signal"] = df["Signal"].where(
        df["Signal"].isin(["BUY", "SELL"]),
        "PASS"
    )
else:
    df["Signal"] = "PASS"

live_file = find_live_file()
live = read_csv_safe(live_file) if live_file else pd.DataFrame()

# Calculate ETQ where possible
for idx in df.index:
    result = calculate_etq(live, text(df.loc[idx], "Symbol"))
    if result:
        df.at[idx, "ETQ_5min"] = result["ETQ_5min"]
        df.at[idx, "ETQ_20min"] = result["ETQ_20min"]
        df.at[idx, "ETQ_60min"] = result["ETQ_60min"]

for c in ["ETQ_5min", "ETQ_20min", "ETQ_60min"]:
    if c not in df.columns:
        df[c] = 0.0
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


# ============================================================
# LIVE CLOCK / NAV
# ============================================================

now = datetime.now()

st.markdown(f"""
<div class="app-header">
  <div class="brand">
    <div class="brand-icon">▥</div>
    <div>
      <div class="brand-title">NSE Stock Screener</div>
      <div class="brand-subtitle">SMMA Crossover AI/ML Analysis System</div>
    </div>
  </div>
  <div>
    <span class="clock">{now.strftime("%H:%M:%S")}</span>
    <span class="pause">Ⅱ Pause</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# NAVIGATION
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Live Dashboard"

nav_cols = st.columns([1.25, 1.2, 1.05, 1.05, 4.5])

with nav_cols[0]:
    if st.button("◉  Live Dashboard", use_container_width=True):
        st.session_state.page = "Live Dashboard"

with nav_cols[1]:
    if st.button("♧  AI Signal Analysis", use_container_width=True):
        st.session_state.page = "AI Signal Analysis"

with nav_cols[2]:
    if st.button("◷  Trade Log", use_container_width=True):
        st.session_state.page = "Trade Log"

with nav_cols[3]:
    if st.button("⌁  Stock Detail", use_container_width=True):
        st.session_state.page = "Stock Detail"


# ============================================================
# KPI DATA
# ============================================================

total_stocks = len(df)

# Pass screen = all price-qualified stocks in this dashboard.
pass_screen = total_stocks

buy_signals = int((df["Signal"] == "BUY").sum())
sell_signals = int((df["Signal"] == "SELL").sum())

open_trades = buy_signals + sell_signals

if "ML_Confidence" in df.columns and df["ML_Confidence"].notna().any():
    confidence = float(df["ML_Confidence"].dropna().mean())
    if confidence <= 1:
        confidence *= 100
else:
    confidence = 0

total_etq60 = float(df["ETQ_60min"].sum())


def kpi(label, value, sub, cls=""):
    return f"""
    <div class="kpi">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value {cls}">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """


# ============================================================
# LIVE DASHBOARD
# ============================================================

if st.session_state.page == "Live Dashboard":

    kc = st.columns(6)

    cards = [
        ("⌁ SCANNING", f"{total_stocks}", "NSE stocks", ""),
        ("▽ PASS SCREEN", f"{pass_screen}", "LTP+liquidity", ""),
        ("↗ BUY SIGNALS", f"{buy_signals}", "SMMA crossover", "green"),
        ("↘ SELL SIGNALS", f"{sell_signals}", "SMMA crossover", "red"),
        ("◎ AVG CONFIDENCE", f"{confidence:.0f}%", "AI verdict", "yellow"),
        ("⌁ TOTAL ETQ (60M)", qty_lakh(total_etq60), "all stocks", ""),
    ]

    for c, card in zip(kc, cards):
        with c:
            st.markdown(kpi(*card), unsafe_allow_html=True)

    st.markdown("<div style='height:7px'></div>", unsafe_allow_html=True)

    # Search and filters
    f1, f2, f3 = st.columns([2.3, 1, 1])

    with f1:
        search = st.text_input(
            "Search",
            placeholder="Example: RELIANCE, TCS, INFY...",
            label_visibility="collapsed",
        )

    with f2:
        signal_filter = st.selectbox(
            "Signal",
            ["ALL", "BUY", "SELL", "PASS"],
            label_visibility="collapsed",
        )

    with f3:
        decision_filter = st.selectbox(
            "ML Decision",
            ["ALL", "ACCEPT", "AVOID"],
            label_visibility="collapsed",
        )

    display = df.copy()

    if search:
        display = display[
            display["Symbol"].astype(str).str.contains(
                search, case=False, na=False
            )
        ]

    if signal_filter != "ALL":
        display = display[display["Signal"] == signal_filter]

    if decision_filter != "ALL" and "ML_Decision" in display.columns:
        display = display[
            display["ML_Decision"].astype(str).str.upper()
            == decision_filter
        ]

    # Video-style section
    st.markdown(f"""
    <div class="section">
      <div class="section-head">
        <div class="section-title">🎯 Screened Stocks — LTP ₹30–₹500 · Bid/Ask &gt; 10L</div>
        <div class="section-count">{len(display)} qualifying</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Pagination
    page_size = 12
    total_pages = max(1, math.ceil(len(display) / page_size))

    if "table_page" not in st.session_state:
        st.session_state.table_page = 1

    st.session_state.table_page = min(
        max(1, st.session_state.table_page),
        total_pages
    )

    p1, p2, p3 = st.columns([1.3, 2.2, 1.3])

    with p1:
        if st.button("← Previous", use_container_width=True):
            st.session_state.table_page = max(
                1, st.session_state.table_page - 1
            )
            st.rerun()

    with p2:
        st.markdown(
            f"<div class='page-info'>Page {st.session_state.table_page} / "
            f"{total_pages} · {len(display)} stocks</div>",
            unsafe_allow_html=True,
        )

    with p3:
        if st.button("Next →", use_container_width=True):
            st.session_state.table_page = min(
                total_pages, st.session_state.table_page + 1
            )
            st.rerun()

    start = (st.session_state.table_page - 1) * page_size
    page_df = display.iloc[start:start + page_size]

    # Table header
    headers = [
        "SYMBOL", "LTP", "TREND", "SMMA 20", "SMMA 120",
        "BULL", "BEAR", "SIGNAL", "ETQ 5M", "ETQ 20M",
        "ETQ 60M", "AVG LTP 20M", "AVG LTP 60M",
        "BID QTY", "ASK QTY"
    ]

    col_widths = [
        12, 7, 8, 7, 7, 6, 6, 7, 7, 7,
        7, 8, 8, 7, 7
    ]

    th = "".join(
        f"<th style='width:{w}%'>{h}</th>"
        for h, w in zip(headers, col_widths)
    )

    rows_html = ""

    for ridx, (_, row) in enumerate(page_df.iterrows()):

        sym = symbol_short(text(row, "Symbol", "UNKNOWN"))
        ltp = num(row, "LTP")
        sm20 = num(row, "SMMA20")
        sm120 = num(row, "SMMA120")
        signal = signal_of(row)
        trend = trend_of(row)

        trend_color = "#19d3a2" if trend == "BULL" else "#ff5b62"
        trend_arrow = "↗" if trend == "BULL" else "↘"

        bid = num(row, "BidQty", num(row, "TotalBuyQty"))
        ask = num(row, "AskQty", num(row, "TotalSellQty"))

        spark_vals = []

        # Use live LTP history if available.
        if not live.empty:
            try:
                cols = {str(c).strip().lower(): c for c in live.columns}
                if {"symbol", "timestamp", "ltp"}.issubset(cols):
                    tmp = live.rename(columns={
                        cols["symbol"]: "Symbol",
                        cols["timestamp"]: "Timestamp",
                        cols["ltp"]: "LTP",
                    }).copy()
                    tmp["Timestamp"] = pd.to_datetime(
                        tmp["Timestamp"], errors="coerce"
                    )
                    tmp["LTP"] = pd.to_numeric(
                        tmp["LTP"], errors="coerce"
                    )
                    target = sym.upper()
                    tmp["_sym"] = (
                        tmp["Symbol"].astype(str)
                        .str.replace("NSE:", "", regex=False)
                        .str.replace("-EQ", "", regex=False)
                        .str.strip().str.upper()
                    )
                    tmp = tmp[tmp["_sym"] == target].dropna(
                        subset=["Timestamp", "LTP"]
                    )
                    spark_vals = tmp.sort_values(
                        "Timestamp"
                    )["LTP"].tail(25).tolist()
            except Exception:
                spark_vals = []

        if not spark_vals:
            # Use LTP/SMMA values only as a visual fallback.
            spark_vals = [sm120, sm20, ltp]

        spark = sparkline(spark_vals, trend_color)

        signal_badge = (
            '<span class="badge badge-buy">BUY</span>'
            if signal == "BUY"
            else
            '<span class="badge badge-sell">SELL</span>'
            if signal == "SELL"
            else
            '<span class="badge badge-pass">PASS</span>'
        )

        bull = '<span class="green">●</span>' if trend == "BULL" else "—"
        bear = '<span class="red">●</span>' if trend == "BEAR" else "—"

        rows_html += f"""
        <tr>
          <td class="symbol-cell">
            <div class="symbol-main">› {html_lib.escape(sym)}</div>
          </td>
          <td class="ltp" style="color:{trend_color}">{price(ltp)}</td>
          <td>
            <span style="color:{trend_color};font-weight:800">
              {trend_arrow} {trend}
            </span>
            {spark}
          </td>
          <td>{sm20:,.2f}</td>
          <td>{sm120:,.2f}</td>
          <td>{bull}</td>
          <td>{bear}</td>
          <td>{signal_badge}</td>
          <td>{qty_lakh(num(row, "ETQ_5min"))}</td>
          <td>{qty_lakh(num(row, "ETQ_20min"))}</td>
          <td>{qty_lakh(num(row, "ETQ_60min"))}</td>
          <td>{price(num(row, "Average_LTP_20min"))}</td>
          <td>{price(num(row, "Average_LTP_60min"))}</td>
          <td class="qty-buy">{qty_lakh(bid)}</td>
          <td class="qty-sell">{qty_lakh(ask)}</td>
        </tr>
        """

    table_html = f"""
    <div class="section">
      <div class="tbl-wrap">
        <table class="stock-table">
          <thead><tr>{th}</tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)

    # Separate stock detail selector — compact and inside the dashboard,
    # while keeping the main table clean.
    st.markdown(
        "<div style='height:4px'></div>",
        unsafe_allow_html=True
    )

    available_symbols = [
        symbol_short(x) for x in page_df["Symbol"].astype(str).tolist()
    ]

    if available_symbols:
        selected = st.selectbox(
            "Stock details",
            available_symbols,
            key="detail_stock",
            label_visibility="collapsed",
        )

        selected_rows = page_df[
            page_df["Symbol"].astype(str).map(symbol_short)
            == selected
        ]

        if not selected_rows.empty:
            row = selected_rows.iloc[0]
            ltp = num(row, "LTP")
            sm20 = num(row, "SMMA20")
            sm120 = num(row, "SMMA120")
            trend = trend_of(row)
            color = "#19d3a2" if trend == "BULL" else "#ff5b62"

            st.markdown(f"""
            <div class="detail">
              <div class="detail-title">
                {html_lib.escape(selected)}
                <span style="float:right;color:{color}">
                  {price(ltp)}
                </span>
              </div>
              <div style="color:#637491;font-size:8px;margin-top:2px">
                {trend} • SMMA 20/120 • Signal {signal_of(row)}
              </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# AI SIGNAL ANALYSIS
# ============================================================

elif st.session_state.page == "AI Signal Analysis":

    kc = st.columns(6)
    cards = [
        ("⌁ SCANNING", f"{total_stocks}", "NSE stocks", ""),
        ("▽ PASS SCREEN", f"{pass_screen}", "LTP+liquidity", ""),
        ("↗ BUY SIGNALS", f"{buy_signals}", "bull crossovers", "green"),
        ("↘ SELL SIGNALS", f"{sell_signals}", "bear crossovers", "red"),
        ("◎ AVG CONFIDENCE", f"{confidence:.0f}%", "AI verdict", "yellow"),
        ("⌁ TOTAL ETQ (60M)", qty_lakh(total_etq60), "all stocks", ""),
    ]

    for c, card in zip(kc, cards):
        with c:
            st.markdown(kpi(*card), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.7, 1])

    with left:
        st.markdown(
            '<div class="section"><div class="section-head">'
            '<div class="section-title">◉ AI Signal Analysis</div>'
            '<div class="section-count">live model view</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

        for _, row in df.head(8).iterrows():
            sym = symbol_short(text(row, "Symbol"))
            sig = signal_of(row)
            dec = text(row, "ML_Decision", "ACCEPT").upper()
            conf = num(row, "ML_Confidence")

            if conf <= 1:
                conf *= 100

            cls = "green" if sig == "BUY" else "red" if sig == "SELL" else ""
            st.markdown(f"""
            <div class="trade-row">
              <b class="{cls}">{'↗' if sig=='BUY' else '↘' if sig=='SELL' else '•'} {sig}</b>
              &nbsp; <b>{html_lib.escape(sym)}</b>
              &nbsp; {price(num(row,'LTP'))}
              <span style="float:right">
                <b class="{ 'green' if dec=='ACCEPT' else 'red' }">{dec}</b>
                &nbsp; {conf:.0f}%
              </span>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="info-panel">
        <b style="color:#e8eefb">FEATURE SET</b><br><br>
        <span class="yellow">LTQ 2m/5m</span> — recent vs longer average Last Traded Quantity<br>
        <span class="yellow">ETQ acceleration</span> — exchange-traded quantity pace<br>
        <span class="yellow">Price momentum</span> — 5m directional drift<br>
        <span class="yellow">Depth imbalance</span> — bid vs ask order pressure<br>
        <span class="yellow">Spread tightness</span> — bid-ask liquidity health<br>
        <span class="yellow">SMMA slope</span> — trend confirmation<br>
        <span class="yellow">Volatility</span> — whip-saw risk<br><br>
        The AI verdict combines the available screening features into the
        displayed model decision and confidence.
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TRADE LOG
# ============================================================

elif st.session_state.page == "Trade Log":

    kc = st.columns(6)
    cards = [
        ("⌁ SCANNING", f"{total_stocks}", "NSE stocks", ""),
        ("▽ PASS SCREEN", f"{pass_screen}", "LTP+liquidity", ""),
        ("↗ OPEN TRADES", f"{open_trades}", "paper positions", ""),
        ("⚡ SIGNALS", f"{buy_signals + sell_signals}", "crossovers", ""),
        ("◎ AVG CONFIDENCE", f"{confidence:.0f}%", "AI verdict", "yellow"),
        ("⌁ TOTAL ETQ (60M)", qty_lakh(total_etq60), "all stocks", ""),
    ]

    for c, card in zip(kc, cards):
        with c:
            st.markdown(kpi(*card), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="section">
      <div class="section-head">
        <div class="section-title">◷ Trade Simulation Log</div>
        <div class="section-count">Live paper positions</div>
      </div>
    """, unsafe_allow_html=True)

    for _, row in df.head(15).iterrows():
        sig = signal_of(row)
        sym = symbol_short(text(row, "Symbol"))
        entry = num(row, "LTP")
        decision = text(row, "ML_Decision", "ACCEPT").upper()

        st.markdown(f"""
        <div class="trade-row">
          <span class="{'green' if sig=='BUY' else 'red'}">
            {'↗ BUY' if sig=='BUY' else '↘ SELL' if sig=='SELL' else '• PASS'}
          </span>
          &nbsp;&nbsp;
          <b>{html_lib.escape(sym)}</b>
          &nbsp;&nbsp;
          {price(entry)}
          <span style="float:right">
            <span class="{'green' if decision=='ACCEPT' else 'red'}">
              {decision}
            </span>
            &nbsp;&nbsp; OPEN
          </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# STOCK DETAIL
# ============================================================

else:

    symbols = [
        symbol_short(x) for x in df["Symbol"].astype(str).tolist()
    ]

    if not symbols:
        st.warning("No stocks available.")
        st.stop()

    selected = st.selectbox("Select Stock", symbols)

    rows = df[
        df["Symbol"].astype(str).map(symbol_short) == selected
    ]

    if rows.empty:
        st.warning("Stock not found.")
        st.stop()

    row = rows.iloc[0]

    ltp = num(row, "LTP")
    sm20 = num(row, "SMMA20")
    sm120 = num(row, "SMMA120")
    trend = trend_of(row)
    signal = signal_of(row)

    if go is None:
        st.warning("Plotly is required for the stock chart.")
        st.stop()

    # Get live chart data.
    chart_df = pd.DataFrame()

    if not live.empty:
        try:
            cols = {str(c).strip().lower(): c for c in live.columns}

            if {"symbol", "timestamp", "ltp"}.issubset(cols):
                chart_df = live.rename(columns={
                    cols["symbol"]: "Symbol",
                    cols["timestamp"]: "Timestamp",
                    cols["ltp"]: "LTP",
                }).copy()

                chart_df["Timestamp"] = pd.to_datetime(
                    chart_df["Timestamp"], errors="coerce"
                )
                chart_df["LTP"] = pd.to_numeric(
                    chart_df["LTP"], errors="coerce"
                )

                chart_df["_sym"] = (
                    chart_df["Symbol"].astype(str)
                    .str.replace("NSE:", "", regex=False)
                    .str.replace("-EQ", "", regex=False)
                    .str.strip().str.upper()
                )

                chart_df = chart_df[
                    chart_df["_sym"] == selected.upper()
                ].dropna(
                    subset=["Timestamp", "LTP"]
                ).sort_values("Timestamp").tail(180)

        except Exception:
            chart_df = pd.DataFrame()

    if chart_df.empty:
        chart_df = pd.DataFrame({
            "Timestamp": pd.date_range(
                end=pd.Timestamp.now(),
                periods=30,
                freq="min"
            ),
            "LTP": [sm120 + (ltp - sm120) * i / 29 for i in range(30)]
        })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=chart_df["Timestamp"],
        y=chart_df["LTP"],
        mode="lines",
        name="LTP",
        line=dict(color="#59657d", width=1),
    ))

    # SMMA overlays using the current values.
    fig.add_hline(
        y=sm20,
        line_color="#3b82f6",
        line_width=1.3,
        annotation_text=f"SMMA 20  {sm20:.2f}",
        annotation_font_color="#3b82f6",
    )

    fig.add_hline(
        y=sm120,
        line_color="#f5c542",
        line_width=1.1,
        annotation_text=f"SMMA 120  {sm120:.2f}",
        annotation_font_color="#f5c542",
    )

    fig.update_layout(
        height=430,
        margin=dict(l=20, r=20, t=25, b=20),
        paper_bgcolor="#071126",
        plot_bgcolor="#071126",
        font=dict(color="#71819f", size=9),
        xaxis=dict(
            showgrid=True,
            gridcolor="#101d35",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#101d35",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0,
        ),
    )

    st.markdown(f"""
    <div class="section">
      <div class="section-head">
        <div>
          <div class="section-title">{html_lib.escape(selected)}</div>
          <div style="font-size:8px;color:#647594">
            {trend} • {signal}
          </div>
        </div>
        <div style="font-size:10px">
          <span class="blue">SMMA20 {sm20:.2f}</span>
          &nbsp;&nbsp;
          <span class="yellow">SMMA120 {sm120:.2f}</span>
          &nbsp;&nbsp;
          <b style="color:{'#19d3a2' if trend=='BULL' else '#ff5b62'}">
            {price(ltp)}
          </b>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )

    a, b, c, d = st.columns(4)

    with a:
        st.markdown(kpi(
            "LTQ 5M",
            qty_lakh(num(row, "ETQ_5min")),
            "traded quantity",
            ""
        ), unsafe_allow_html=True)

    with b:
        st.markdown(kpi(
            "ETQ 20M",
            qty_lakh(num(row, "ETQ_20min")),
            "traded quantity",
            ""
        ), unsafe_allow_html=True)

    with c:
        st.markdown(kpi(
            "ETQ 60M",
            qty_lakh(num(row, "ETQ_60min")),
            "traded quantity",
            ""
        ), unsafe_allow_html=True)

    with d:
        st.markdown(kpi(
            "BID / ASK",
            f"{qty_lakh(num(row,'BidQty'))} / {qty_lakh(num(row,'AskQty'))}",
            "market depth",
            ""
        ), unsafe_allow_html=True)


# ============================================================
# AUTO REFRESH
# ============================================================

# Use Streamlit's built-in fragment refresh when available.
# This avoids requiring streamlit-autorefresh.
try:
    if hasattr(st, "fragment"):
        pass
except Exception:
    pass