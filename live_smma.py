import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# STOCKAI — LIVE SMMA ENGINE
# Historical 5-min candles + live ticks
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

HISTORY_DIR = ROOT / "dataset" / "history"
LIVE_FILE = ROOT / "dataset" / "live_ticks.csv"
OUTPUT_FILE = ROOT / "dataset" / "live_smma.csv"


print("=" * 75)
print("STOCKAI — LIVE SMMA 20 / 120 ENGINE")
print("=" * 75)


# ============================================================
# CHECK FILES
# ============================================================

if not HISTORY_DIR.exists():
    raise FileNotFoundError(
        f"History directory not found:\n{HISTORY_DIR}"
    )

if not LIVE_FILE.exists():
    raise FileNotFoundError(
        f"Live tick file not found:\n{LIVE_FILE}"
    )


history_files = list(
    HISTORY_DIR.glob("*.csv")
)

print(
    f"Historical files found: {len(history_files)}"
)


# ============================================================
# SMMA FUNCTION
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

    first_index = valid.index[period - 1]

    first_sma = (
        valid.iloc[:period]
        .mean()
    )

    result.loc[first_index] = first_sma

    previous = first_sma

    for i in range(
        period,
        len(valid)
    ):

        current = valid.iloc[i]

        previous = (
            (
                previous * (period - 1)
            )
            + current
        ) / period

        result.loc[
            valid.index[i]
        ] = previous

    return result


# ============================================================
# LOAD HISTORY
# ============================================================

history_frames = []

print()
print("Loading historical data...")


for i, file in enumerate(
    history_files,
    start=1
):

    try:

        df = pd.read_csv(
            file
        )

        required = {
            "Timestamp",
            "Close"
        }

        if not required.issubset(
            df.columns
        ):
            print(
                "Skipping:",
                file.name,
                "missing columns"
            )
            continue

        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"],
            errors="coerce"
        )

        df["Close"] = pd.to_numeric(
            df["Close"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "Timestamp",
                "Close"
            ]
        )

        symbol = (
            "NSE:"
            + file.stem
            + "-EQ"
        )

        df["Symbol"] = symbol

        df = df[
            [
                "Timestamp",
                "Symbol",
                "Close"
            ]
        ]

        history_frames.append(
            df
        )

    except Exception as e:

        print(
            "ERROR:",
            file.name,
            e
        )


if not history_frames:

    raise RuntimeError(
        "No historical data loaded."
    )


history = pd.concat(
    history_frames,
    ignore_index=True
)


history = history.sort_values(
    [
        "Symbol",
        "Timestamp"
    ]
)


history = history.rename(
    columns={
        "Close": "LTP"
    }
)


print(
    "Historical rows:",
    len(history)
)

print(
    "Historical stocks:",
    history["Symbol"].nunique()
)


# ============================================================
# LOAD LIVE TICKS
# ============================================================

live = pd.read_csv(
    LIVE_FILE
)


live["Timestamp"] = pd.to_datetime(
    live["Timestamp"],
    errors="coerce"
)


live["LTP"] = pd.to_numeric(
    live["LTP"],
    errors="coerce"
)


live = live.dropna(
    subset=[
        "Timestamp",
        "Symbol",
        "LTP"
    ]
)


live = live[
    [
        "Timestamp",
        "Symbol",
        "LTP"
    ]
]


print(
    "Live ticks:",
    len(live)
)

print(
    "Live stocks:",
    live["Symbol"].nunique()
)


# ============================================================
# CONVERT LIVE TICKS TO 5-MINUTE CLOSES
# ============================================================

live["Timestamp"] = (
    live["Timestamp"]
    .dt.floor("5min")
)


live_5m = (
    live
    .sort_values("Timestamp")
    .groupby(
        [
            "Symbol",
            "Timestamp"
        ],
        as_index=False
    )
    .last()
)


live_5m = live_5m[
    [
        "Timestamp",
        "Symbol",
        "LTP"
    ]
]


# ============================================================
# COMBINE HISTORY + LIVE
# ============================================================

combined = pd.concat(
    [
        history,
        live_5m
    ],
    ignore_index=True
)


combined = combined.sort_values(
    [
        "Symbol",
        "Timestamp"
    ]
)


combined = (
    combined
    .drop_duplicates(
        subset=[
            "Symbol",
            "Timestamp"
        ],
        keep="last"
    )
)


# ============================================================
# CALCULATE SMMA
# ============================================================

results = []

print()
print("Calculating SMMA20 / SMMA120...")


for symbol, group in combined.groupby(
    "Symbol"
):

    group = group.sort_values(
        "Timestamp"
    ).copy()

    group["SMMA20"] = calculate_smma(
        group["LTP"],
        20
    )

    group["SMMA120"] = calculate_smma(
        group["LTP"],
        120
    )

    group["Previous_SMMA20"] = (
        group["SMMA20"].shift(1)
    )

    group["Previous_SMMA120"] = (
        group["SMMA120"].shift(1)
    )


    # ========================================================
    # CROSSOVER
    # ========================================================

    group["Signal"] = "NONE"


    buy = (
        group["Previous_SMMA20"].notna()
        &
        group["Previous_SMMA120"].notna()
        &
        (
            group["Previous_SMMA20"]
            <=
            group["Previous_SMMA120"]
        )
        &
        (
            group["SMMA20"]
            >
            group["SMMA120"]
        )
    )


    sell = (
        group["Previous_SMMA20"].notna()
        &
        group["Previous_SMMA120"].notna()
        &
        (
            group["Previous_SMMA20"]
            >=
            group["Previous_SMMA120"]
        )
        &
        (
            group["SMMA20"]
            <
            group["SMMA120"]
        )
    )


    group.loc[
        buy,
        "Signal"
    ] = "BUY"


    group.loc[
        sell,
        "Signal"
    ] = "SELL"


    results.append(
        group
    )


# ============================================================
# FINAL DATASET
# ============================================================

result = pd.concat(
    results,
    ignore_index=True
)


result = result.sort_values(
    [
        "Symbol",
        "Timestamp"
    ]
)


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# LATEST STATUS
# ============================================================

latest = (
    result
    .sort_values("Timestamp")
    .groupby("Symbol")
    .tail(1)
    .copy()
)


valid_smma = latest[
    latest["SMMA120"].notna()
]


print()
print("=" * 75)
print("SMMA COMPLETE")
print("=" * 75)

print(
    "Total stocks:",
    len(latest)
)

print(
    "SMMA120 ready:",
    len(valid_smma)
)

print(
    "SMMA120 missing:",
    len(latest) - len(valid_smma)
)

print(
    "BUY signals:",
    (
        result["Signal"] == "BUY"
    ).sum()
)

print(
    "SELL signals:",
    (
        result["Signal"] == "SELL"
    ).sum()
)


print()
print("LATEST SMMA STATUS")
print("-" * 75)


print(
    valid_smma[
        [
            "Timestamp",
            "Symbol",
            "LTP",
            "SMMA20",
            "SMMA120",
            "Signal"
        ]
    ]
    .sort_values("Symbol")
    .tail(30)
    .to_string(index=False)
)


print()
print("Output:")
print(OUTPUT_FILE)