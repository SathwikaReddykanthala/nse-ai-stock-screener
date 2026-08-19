from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# STOCKAI — HISTORICAL SMMA ENGINE
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

HISTORICAL_FILE = (
    ROOT.parent
    / "StockAI"
    / "dataset"
    / "historical_20days.csv"
)

OUTPUT_FILE = (
    ROOT
    / "dataset"
    / "historical_smma.csv"
)


# ============================================================
# SMMA
# ============================================================

def calculate_smma(series, period):

    series = pd.to_numeric(
        series,
        errors="coerce"
    )

    result = pd.Series(
        np.nan,
        index=series.index,
        dtype=float
    )

    valid = series.dropna()

    if len(valid) < period:
        return result

    first_position = valid.index[period - 1]

    first_smma = (
        valid.iloc[:period]
        .mean()
    )

    result.loc[first_position] = first_smma

    previous = first_smma

    for i in range(period, len(valid)):

        current = valid.iloc[i]

        previous = (
            (
                previous * (period - 1)
            )
            +
            current
        ) / period

        result.loc[
            valid.index[i]
        ] = previous

    return result


# ============================================================
# LOAD DATA
# ============================================================

if not HISTORICAL_FILE.exists():

    raise FileNotFoundError(
        f"Historical file not found:\n"
        f"{HISTORICAL_FILE}"
    )


print("=" * 80)
print("STOCKAI — HISTORICAL SMMA ENGINE")
print("=" * 80)

print()
print("Input:")
print(HISTORICAL_FILE)


df = pd.read_csv(
    HISTORICAL_FILE
)


# ============================================================
# STANDARDIZE COLUMNS
# ============================================================

df = df.rename(
    columns={
        "Timestamp": "timestamp",
        "Symbol": "symbol",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
)


required = [
    "timestamp",
    "symbol",
    "close",
]


missing = [
    column
    for column in required
    if column not in df.columns
]


if missing:

    raise ValueError(
        f"Missing columns: {missing}"
    )


# ============================================================
# TIMESTAMP
# ============================================================

df["timestamp"] = pd.to_datetime(
    pd.to_numeric(
        df["timestamp"],
        errors="coerce"
    ),
    unit="s",
    errors="coerce"
)


# ============================================================
# NUMERIC
# ============================================================

df["close"] = pd.to_numeric(
    df["close"],
    errors="coerce"
)


df = df.dropna(
    subset=[
        "timestamp",
        "symbol",
        "close",
    ]
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    [
        "symbol",
        "timestamp",
    ]
).reset_index(
    drop=True
)


# ============================================================
# CALCULATE SMMA PER STOCK
# ============================================================

results = []


for symbol, group in df.groupby(
    "symbol",
    sort=False
):

    group = group.copy()

    group["smma20"] = calculate_smma(
        group["close"],
        20
    )

    group["smma120"] = calculate_smma(
        group["close"],
        120
    )

    # --------------------------------------------------------
    # Previous values
    # --------------------------------------------------------

    group["previous_smma20"] = (
        group["smma20"].shift(1)
    )

    group["previous_smma120"] = (
        group["smma120"].shift(1)
    )

    # --------------------------------------------------------
    # BUY CROSSOVER
    # --------------------------------------------------------

    buy = (
        group["previous_smma20"].notna()
        &
        group["previous_smma120"].notna()
        &
        (
            group["previous_smma20"]
            <=
            group["previous_smma120"]
        )
        &
        (
            group["smma20"]
            >
            group["smma120"]
        )
    )

    # --------------------------------------------------------
    # SELL CROSSOVER
    # --------------------------------------------------------

    sell = (
        group["previous_smma20"].notna()
        &
        group["previous_smma120"].notna()
        &
        (
            group["previous_smma20"]
            >=
            group["previous_smma120"]
        )
        &
        (
            group["smma20"]
            <
            group["smma120"]
        )
    )

    group["signal"] = "NONE"

    group.loc[
        buy,
        "signal"
    ] = "BUY"

    group.loc[
        sell,
        "signal"
    ] = "SELL"

    results.append(
        group
    )


# ============================================================
# COMBINE
# ============================================================

result = pd.concat(
    results,
    ignore_index=True
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

smma_ready = (
    result["smma120"]
    .notna()
    .sum()
)

buy_count = (
    result["signal"]
    .eq("BUY")
    .sum()
)

sell_count = (
    result["signal"]
    .eq("SELL")
    .sum()
)


print()
print("=" * 80)
print("SMMA CALCULATION COMPLETE")
print("=" * 80)

print()
print("Rows:", len(result))

print(
    "Stocks:",
    result["symbol"].nunique()
)

print(
    "SMMA120-ready rows:",
    smma_ready
)

print(
    "BUY crossovers:",
    buy_count
)

print(
    "SELL crossovers:",
    sell_count
)

print()
print("Output:")
print(OUTPUT_FILE)

print("=" * 80)