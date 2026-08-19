from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# STOCKAI — LIVE ML FEATURE ENGINE
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "dataset" / "live_ticks.csv"
OUTPUT_FILE = ROOT / "dataset" / "live_ml_features.csv"


# ============================================================
# CONFIG
# ============================================================

EPSILON = 1e-9


# ============================================================
# CHECK INPUT
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Live tick file not found:\n{INPUT_FILE}"
    )


print("=" * 75)
print("STOCKAI — LIVE ML FEATURE ENGINE")
print("=" * 75)

print()
print("Input:")
print(INPUT_FILE)


# ============================================================
# LOAD LIVE TICKS
# ============================================================

df = pd.read_csv(INPUT_FILE)


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
)

# ============================================================
# NORMALIZE ANGEL ONE LIVE TICK COLUMNS
# ============================================================

df = df.rename(
    columns={
        "bidprice1": "bid_price",
        "bidqty1": "bid_qty",
        "askprice1": "ask_price",
        "askqty1": "ask_qty",
    }
)
# ============================================================
# REQUIRED LIVE TICK COLUMNS
# ============================================================

required = [
    "timestamp",
    "symbol",
    "ltp",
    "ltq",
    "bid_price",
    "bid_qty",
    "ask_price",
    "ask_qty",
]


missing = [
    c for c in required
    if c not in df.columns
]


if missing:
    raise ValueError(
        "Missing columns in live_ticks.csv: "
        + str(missing)
    )


# ============================================================
# NUMERIC CONVERSION
# ============================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)


numeric_columns = [
    "ltp",
    "ltq",
    "bid_price",
    "bid_qty",
    "ask_price",
    "ask_qty",
]


for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


df = df.dropna(
    subset=[
        "timestamp",
        "symbol",
        "ltp",
    ]
)


df = df.sort_values(
    [
        "symbol",
        "timestamp",
    ]
).reset_index(
    drop=True
)


# ============================================================
# BASIC CLEANING
# ============================================================

df["ltq"] = df["ltq"].fillna(0).clip(lower=0)

df["bid_qty"] = (
    df["bid_qty"]
    .fillna(0)
    .clip(lower=0)
)

df["ask_qty"] = (
    df["ask_qty"]
    .fillna(0)
    .clip(lower=0)
)

df["volume"] = 0.0


# ============================================================
# VOLUME
# ============================================================
#
# The assignment defines Volume as cumulative traded quantity.
#
# If the FYERS tick contains cumulative volume, use it.
# Otherwise reconstruct cumulative volume from LTQ.
# ============================================================

if "volume" in df.columns:

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce"
    ).fillna(0)

else:

    df["volume"] = (
        df.groupby("symbol")["ltq"]
        .cumsum()
    )


# ============================================================
# BID/ASK IMBALANCE
# ============================================================

df["bid_ask_imbalance"] = (
    (
        df["bid_qty"]
        -
        df["ask_qty"]
    )
    /
    (
        df["bid_qty"]
        +
        df["ask_qty"]
        +
        EPSILON
    )
)


# ============================================================
# FEATURE CALCULATION
# ============================================================

feature_frames = []


for symbol, group in df.groupby(
    "symbol",
    sort=False
):

    group = group.copy()

    group = group.sort_values(
        "timestamp"
    )

    group = group.set_index(
        "timestamp"
    )

    # --------------------------------------------------------
    # LTQ
    # --------------------------------------------------------

    group["LTQ"] = (
        group["ltq"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # LTQ 2 MINUTE AVERAGE
    # --------------------------------------------------------

    group["LTQ_2min_avg"] = (
        group["LTQ"]
        .rolling(
            "2min",
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # LTQ 5 MINUTE AVERAGE
    # --------------------------------------------------------

    group["LTQ_5min_avg"] = (
        group["LTQ"]
        .rolling(
            "5min",
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # LTQ SPIKE RATIO
    # --------------------------------------------------------

    group["LTQ_Spike_Ratio"] = (
        group["LTQ"]
        /
        (
            group["LTQ_5min_avg"]
            +
            EPSILON
        )
    )

    # --------------------------------------------------------
    # ETQ
    #
    # ETQ = total executed quantity during window.
    # --------------------------------------------------------

    group["ETQ_5min"] = (
        group["LTQ"]
        .rolling(
            "5min",
            min_periods=1
        )
        .sum()
    )

    group["ETQ_20min"] = (
        group["LTQ"]
        .rolling(
            "20min",
            min_periods=1
        )
        .sum()
    )

    group["ETQ_60min"] = (
        group["LTQ"]
        .rolling(
            "60min",
            min_periods=1
        )
        .sum()
    )

    # --------------------------------------------------------
    # RETURNS
    #
    # Use time-based price observations.
    # --------------------------------------------------------

    minute_price = (
        group["ltp"]
        .resample("1min")
        .last()
        .ffill()
    )

    return_1 = (
        minute_price
        .pct_change(1)
        * 100
    )

    return_5 = (
        minute_price
        .pct_change(5)
        * 100
    )

    # --------------------------------------------------------
    # MAP RETURNS BACK TO TICKS
    # --------------------------------------------------------

    tick_minutes = (
        group.index
        .floor("min")
    )

    group["Return_1"] = (
        tick_minutes
        .map(return_1)
        .astype(float)
        .fillna(0)
    )

    group["Return_5"] = (
        tick_minutes
        .map(return_5)
        .astype(float)
        .fillna(0)
    )

    # --------------------------------------------------------
    # OTHER FEATURES
    # --------------------------------------------------------

    group["BidQty"] = (
        group["bid_qty"]
        .fillna(0)
    )

    group["AskQty"] = (
        group["ask_qty"]
        .fillna(0)
    )

    group["BidAsk_Imbalance"] = (
        group["bid_ask_imbalance"]
        .fillna(0)
    )

    group["Volume"] = (
        group["volume"]
        .fillna(0)
    )

    feature_frames.append(
        group.reset_index()
    )


# ============================================================
# COMBINE
# ============================================================

result = pd.concat(
    feature_frames,
    ignore_index=True
)


# ============================================================
# OUTPUT COLUMNS
# ============================================================

result = result.rename(
    columns={
        "timestamp": "Timestamp",
        "symbol": "Symbol",
        "ltp": "LTP",
        "bid_price": "BidPrice",
        "ask_price": "AskPrice",
    }
)


output_columns = [
    "Timestamp",
    "Symbol",
    "LTP",
    "LTQ",
    "LTQ_2min_avg",
    "LTQ_5min_avg",
    "LTQ_Spike_Ratio",
    "ETQ_5min",
    "ETQ_20min",
    "ETQ_60min",
    "BidQty",
    "AskQty",
    "BidAsk_Imbalance",
    "Volume",
    "Return_1",
    "Return_5",
]


result = result[
    [
        c
        for c in output_columns
        if c in result.columns
    ]
]


# ============================================================
# REMOVE INVALID NUMBERS
# ============================================================

result = result.replace(
    [
        np.inf,
        -np.inf
    ],
    np.nan
)


numeric_output = [
    "LTP",
    "LTQ",
    "LTQ_2min_avg",
    "LTQ_5min_avg",
    "LTQ_Spike_Ratio",
    "ETQ_5min",
    "ETQ_20min",
    "ETQ_60min",
    "BidQty",
    "AskQty",
    "BidAsk_Imbalance",
    "Volume",
    "Return_1",
    "Return_5",
]


for col in numeric_output:

    if col in result.columns:

        result[col] = (
            pd.to_numeric(
                result[col],
                errors="coerce"
            )
            .fillna(0)
        )


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 75)
print("FEATURE GENERATION COMPLETE")
print("=" * 75)

print()
print("Rows:", len(result))

print(
    "Stocks:",
    result["Symbol"].nunique()
)

print(
    "Latest tick:",
    result["Timestamp"].max()
)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print("Columns:")
print(result.columns.tolist())

print()
print("Latest 10 rows:")

print(
    result[
        [
            "Timestamp",
            "Symbol",
            "LTP",
            "LTQ",
            "LTQ_2min_avg",
            "LTQ_5min_avg",
            "LTQ_Spike_Ratio",
            "ETQ_5min",
            "ETQ_20min",
            "ETQ_60min",
            "BidQty",
            "AskQty",
            "BidAsk_Imbalance",
            "Return_1",
            "Return_5",
        ]
    ]
    .tail(10)
    .to_string(index=False)
)

print()
print("=" * 75)