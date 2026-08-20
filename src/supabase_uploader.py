import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
SIGNAL_FILE = DATASET / "live_ai_signals.csv"

load_dotenv(ROOT / ".env")


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env"
    )

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# LOAD SIGNALS
# ============================================================

if not SIGNAL_FILE.exists():
    raise FileNotFoundError(
        f"Signal file not found: {SIGNAL_FILE}"
    )

df = pd.read_csv(
    SIGNAL_FILE,
    low_memory=False
)

if df.empty:
    raise RuntimeError(
        "live_ai_signals.csv is empty."
    )

if "Symbol" not in df.columns:
    raise RuntimeError(
        "live_ai_signals.csv does not contain Symbol."
    )


# ============================================================
# PREPARE DATA
# ============================================================

COLUMN_MAP = {
    "Timestamp_SMMA": "timestamp_smma",
    "Symbol": "symbol",
    "LTP_SMMA": "ltp_smma",
    "SMMA20": "smma20",
    "SMMA120": "smma120",
    "Previous_SMMA20": "previous_smma20",
    "Previous_SMMA120": "previous_smma120",
    "Signal": "signal",
    "Timestamp_LIVE": "timestamp_live",
    "LTP_LIVE": "ltp_live",
    "LTQ": "ltq",
    "LTQ_2min_avg": "ltq_2min_avg",
    "LTQ_5min_avg": "ltq_5min_avg",
    "LTQ_Spike_Ratio": "ltq_spike_ratio",
    "ETQ_5min": "etq_5min",
    "ETQ_20min": "etq_20min",
    "ETQ_60min": "etq_60min",
    "BidQty": "bidqty",
    "AskQty": "askqty",
    "BidAsk_Imbalance": "bidask_imbalance",
    "Volume": "volume",
    "Return_1": "return_1",
    "Return_5": "return_5",
    "Current_LTP": "current_ltp",
    "smma_diff": "smma_diff",
    "smma_diff_pct": "smma_diff_pct",
    "smma20": "smma20_live",
    "smma120": "smma120_live",
    "return_1": "return_1_live",
    "return_5": "return_5_live",
    "direction": "direction",
    "entry_price": "entry_price",
    "directional_return": "directional_return",
    "range_pct": "range_pct",
    "body_pct": "body_pct",
    "volume_change_pct": "volume_change_pct",
    "volume_ratio": "volume_ratio",
    "ML_Probability": "ml_probability",
    "Price_Filter": "price_filter",
    "Liquidity_Filter": "liquidity_filter",
    "LTQ_Strong": "ltq_strong",
    "LTQ_Moderate": "ltq_moderate",
    "Depth_Bullish": "depth_bullish",
    "Depth_Bearish": "depth_bearish",
    "Decision": "decision",
    "Reason": "reason",
}

df = df.rename(columns=COLUMN_MAP)


# ============================================================
# KEEP ONLY TABLE COLUMNS
# ============================================================

TABLE_COLUMNS = [
    "timestamp_smma",
    "symbol",
    "ltp_smma",
    "smma20",
    "smma120",
    "previous_smma20",
    "previous_smma120",
    "signal",
    "timestamp_live",
    "ltp_live",
    "ltq",
    "ltq_2min_avg",
    "ltq_5min_avg",
    "ltq_spike_ratio",
    "etq_5min",
    "etq_20min",
    "etq_60min",
    "bidqty",
    "askqty",
    "bidask_imbalance",
    "volume",
    "return_1",
    "return_5",
    "current_ltp",
    "smma_diff",
    "smma_diff_pct",
    "smma20_live",
    "smma120_live",
    "return_1_live",
    "return_5_live",
    "direction",
    "entry_price",
    "directional_return",
    "range_pct",
    "body_pct",
    "volume_change_pct",
    "volume_ratio",
    "ml_probability",
    "price_filter",
    "liquidity_filter",
    "ltq_strong",
    "ltq_moderate",
    "depth_bullish",
    "depth_bearish",
    "decision",
    "reason",
]

for column in TABLE_COLUMNS:
    if column not in df.columns:
        df[column] = None

df = df[TABLE_COLUMNS].copy()


# ============================================================
# CLEAN VALUES
# ============================================================

for column in [
    "timestamp_smma",
    "timestamp_live",
]:
    df[column] = pd.to_datetime(
        df[column],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")


BOOL_COLUMNS = [
    "price_filter",
    "liquidity_filter",
    "ltq_strong",
    "ltq_moderate",
    "depth_bullish",
    "depth_bearish",
]

for column in BOOL_COLUMNS:
    df[column] = (
        df[column]
        .fillna(False)
        .astype(bool)
    )


# ============================================================
# CLEAN NaN / INF FOR JSON
# ============================================================

import numpy as np

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.astype(object).where(
    pd.notna(df),
    None
)

# ============================================================
# REPLACE CURRENT SNAPSHOT
# ============================================================

supabase.table("live_ai_signals").delete().gte(
    "id",
    0
).execute()

records = df.to_dict(
    orient="records"
)

response = supabase.table(
    "live_ai_signals"
).insert(
    records
).execute()


print("=" * 70)
print("STOCKAI — SUPABASE UPLOAD")
print("=" * 70)
print("Rows uploaded:", len(records))
print("Supabase table: live_ai_signals")
print("Status: SUCCESS")
print("=" * 70)