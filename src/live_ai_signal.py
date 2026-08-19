from pathlib import Path
import joblib
import pandas as pd
import numpy as np


# ============================================================
# STOCKAI — LIVE AI/ML + LTQ/ETQ SIGNAL ENGINE
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
MODEL_FILE = ROOT / "models" / "crossover_profit_model.joblib"

SMMA_FILE = DATASET / "live_smma.csv"
FEATURE_FILE = DATASET / "live_ml_features.csv"

OUTPUT_FILE = DATASET / "live_ai_signals.csv"
TRADE_LOG_FILE = DATASET / "live_trade_log.csv"


# ============================================================
# CONFIGURATION
# ============================================================

MIN_PRICE = 30
MAX_PRICE = 500

MIN_BID_QTY = 1_000_000
MIN_ASK_QTY = 1_000_000

ML_THRESHOLD = 0.60


print("=" * 80)
print("STOCKAI — LIVE AI/ML + LTQ/ETQ SIGNAL ENGINE")
print("=" * 80)


# ============================================================
# CHECK FILES
# ============================================================

for file in [
    MODEL_FILE,
    SMMA_FILE,
    FEATURE_FILE,
]:
    if not file.exists():
        raise FileNotFoundError(
            f"Missing file:\n{file}"
        )


# ============================================================
# LOAD MODEL
# ============================================================

model_package = joblib.load(MODEL_FILE)

if not isinstance(model_package, dict):
    raise TypeError(
        "Expected model package to be a dictionary."
    )

model = model_package["model"]
imputer = model_package.get("imputer")
MODEL_FEATURES = model_package["features"]
ML_THRESHOLD = model_package.get(
    "accept_threshold",
    0.50
)

print()
print("ML model loaded.")
print("Model type:", type(model).__name__)
print("ML features:", MODEL_FEATURES)
print("Acceptance threshold:", ML_THRESHOLD)


# ============================================================
# LOAD SMMA
# ============================================================

smma = pd.read_csv(
    SMMA_FILE,
    low_memory=False
)

smma["Timestamp"] = pd.to_datetime(
    smma["Timestamp"],
    errors="coerce"
)

for column in [
    "LTP",
    "SMMA20",
    "SMMA120",
]:
    smma[column] = pd.to_numeric(
        smma[column],
        errors="coerce"
    )


# ============================================================
# LOAD LIVE FEATURES
# ============================================================

features = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)

features["Timestamp"] = pd.to_datetime(
    features["Timestamp"],
    errors="coerce"
)

numeric_columns = [
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

for column in numeric_columns:
    if column in features.columns:
        features[column] = pd.to_numeric(
            features[column],
            errors="coerce"
        )


# ============================================================
# GET LATEST SMMA PER STOCK
# ============================================================

latest_smma = (
    smma
    .dropna(subset=["Timestamp"])
    .sort_values("Timestamp")
    .groupby("Symbol")
    .tail(1)
    .copy()
)


# ============================================================
# GET LATEST LIVE FEATURES PER STOCK
# ============================================================

latest_features = (
    features
    .dropna(subset=["Timestamp"])
    .sort_values("Timestamp")
    .groupby("Symbol")
    .tail(1)
    .copy()
)


# ============================================================
# MERGE
# ============================================================

signals = latest_smma.merge(
    latest_features,
    on="Symbol",
    how="inner",
    suffixes=("_SMMA", "_LIVE")
)


# ============================================================
# NORMALIZE LTP
# ============================================================

if "LTP_LIVE" in signals.columns:
    signals["Current_LTP"] = signals["LTP_LIVE"]
else:
    signals["Current_LTP"] = signals["LTP_SMMA"]


# ============================================================
# SMMA FEATURES
# ============================================================

signals["smma_diff"] = (
    signals["SMMA20"]
    -
    signals["SMMA120"]
)

signals["smma_diff_pct"] = (
    signals["smma_diff"]
    /
    signals["SMMA120"].replace(0, np.nan)
)
# Model-compatible lowercase feature names
signals["smma20"] = signals["SMMA20"]
signals["smma120"] = signals["SMMA120"]
signals["return_1"] = signals["Return_1"]
signals["return_5"] = signals["Return_5"]

signals["direction"] = (
    signals["Signal"]
    .map({
        "BUY": 1,
        "SELL": -1
    })
    .fillna(0)
)

signals["entry_price"] = (
    signals["Current_LTP"]
)


signals["directional_return"] = (
    signals["Return_5"]
    *
    signals["direction"]
)


# ============================================================
# MODEL FEATURES
# ============================================================

# These four features existed in the historical
# training model but are not available in the
# historical OHLCV source at this time.
#
# Use neutral values rather than inventing data.

signals["range_pct"] = 0.0
signals["body_pct"] = 0.0
signals["volume_change_pct"] = 0.0
signals["volume_ratio"] = 1.0





X = signals[
    MODEL_FEATURES
].copy()

X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

if imputer is not None:
    X = pd.DataFrame(
        imputer.transform(X),
        columns=MODEL_FEATURES,
        index=X.index
    )
else:
    X = X.fillna(0)


# ============================================================
# RANDOM FOREST PROBABILITY
# ============================================================

signals["ML_Probability"] = (
    model.predict_proba(X)[:, 1]
)


# ============================================================
# ASSIGNMENT STOCK SCREENING
# ============================================================

signals["Price_Filter"] = (
    signals["Current_LTP"].between(
        MIN_PRICE,
        MAX_PRICE
    )
)

signals["Liquidity_Filter"] = (
    (signals["BidQty"] > MIN_BID_QTY)
    &
    (signals["AskQty"] > MIN_ASK_QTY)
)


# ============================================================
# LTQ ANALYSIS
# ============================================================

signals["LTQ_Strong"] = (
    signals["LTQ_Spike_Ratio"] >= 1.50
)


signals["LTQ_Moderate"] = (
    signals["LTQ_Spike_Ratio"] >= 1.20
)


# ============================================================
# DIRECTIONAL MARKET DEPTH
# ============================================================

signals["Depth_Bullish"] = (
    signals["BidAsk_Imbalance"] >= 0.20
)

signals["Depth_Bearish"] = (
    signals["BidAsk_Imbalance"] <= -0.20
)


# ============================================================
# FINAL DECISION
# ============================================================

signals["Decision"] = "AVOID"


# BUY

buy_accept = (
    (signals["Signal"] == "BUY")
    &
    (signals["ML_Probability"] >= ML_THRESHOLD)
    &
    signals["Price_Filter"]
    &
    signals["Liquidity_Filter"]
    &
    (
        signals["LTQ_Moderate"]
        |
        signals["Depth_Bullish"]
    )
)


# SELL

sell_accept = (
    (signals["Signal"] == "SELL")
    &
    (signals["ML_Probability"] >= ML_THRESHOLD)
    &
    signals["Price_Filter"]
    &
    signals["Liquidity_Filter"]
    &
    (
        signals["LTQ_Moderate"]
        |
        signals["Depth_Bearish"]
    )
)


signals.loc[
    buy_accept,
    "Decision"
] = "ACCEPT"


signals.loc[
    sell_accept,
    "Decision"
] = "ACCEPT"


# ============================================================
# REASON
# ============================================================

def explain(row):

    if row["Signal"] == "NONE":
        return "No SMMA crossover detected."

    reasons = []

    if not row["Price_Filter"]:
        reasons.append(
            "LTP outside ₹30–₹500 range."
        )

    if not row["Liquidity_Filter"]:
        reasons.append(
            "Bid/Ask quantity below 10 lakh."
        )

    if row["ML_Probability"] < ML_THRESHOLD:
        reasons.append(
            "ML profitability probability below 50%."
        )

    if row["LTQ_Spike_Ratio"] >= 1.50:
        reasons.append(
            "Strong LTQ spike detected."
        )

    elif row["LTQ_Spike_Ratio"] >= 1.20:
        reasons.append(
            "Moderate LTQ increase detected."
        )

    else:
        reasons.append(
            "No significant LTQ spike."
        )

    if row["Signal"] == "BUY":

        if row["BidAsk_Imbalance"] >= 0.20:
            reasons.append(
                "Bid-side market pressure supports BUY."
            )
        else:
            reasons.append(
                "Bid-side pressure does not strongly support BUY."
            )

    elif row["Signal"] == "SELL":

        if row["BidAsk_Imbalance"] <= -0.20:
            reasons.append(
                "Ask-side market pressure supports SELL."
            )
        else:
            reasons.append(
                "Ask-side pressure does not strongly support SELL."
            )

    if (
        row["Decision"] == "ACCEPT"
    ):
        reasons.insert(
            0,
            "Crossover passes AI/ML and market filters."
        )

    else:
        reasons.insert(
            0,
            "Crossover rejected by one or more filters."
        )

    return " ".join(reasons)


signals["Reason"] = signals.apply(
    explain,
    axis=1
)


# ============================================================
# SAVE ALL STOCK SIGNALS
# ============================================================

signals.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# TRADE SIGNAL LOG
# ============================================================

trade_log = signals[
    signals["Signal"].isin(
        ["BUY", "SELL"]
    )
].copy()


if not trade_log.empty:

    trade_columns = [
        "Symbol",
        "Timestamp_SMMA",
        "Current_LTP",
        "SMMA20",
        "SMMA120",
        "Signal",
        "ML_Probability",
        "Decision",
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
        "Reason",
    ]

    trade_columns = [
        c
        for c in trade_columns
        if c in trade_log.columns
    ]

    trade_log[
        trade_columns
    ].to_csv(
        TRADE_LOG_FILE,
        index=False
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 80)
print("LIVE AI/ML SIGNAL ANALYSIS COMPLETE")
print("=" * 80)

print()
print(
    "Stocks analysed:",
    len(signals)
)

print(
    "Price-screened:",
    signals["Price_Filter"].sum()
)

print(
    "Liquidity-qualified:",
    signals["Liquidity_Filter"].sum()
)

print(
    "BUY signals:",
    (
        signals["Signal"] == "BUY"
    ).sum()
)

print(
    "SELL signals:",
    (
        signals["Signal"] == "SELL"
    ).sum()
)

print(
    "ACCEPT:",
    (
        signals["Decision"] == "ACCEPT"
    ).sum()
)

print(
    "AVOID:",
    (
        signals["Decision"] == "AVOID"
    ).sum()
)

print()
print("Signal file:")
print(OUTPUT_FILE)

print()
print("Trade log:")
print(TRADE_LOG_FILE)

print("=" * 80)