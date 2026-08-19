from pathlib import Path
import pandas as pd
import numpy as np
import time


ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

LIVE_FILE = DATASET / "live_market.csv"
HISTORY_FILE = DATASET / "price_history.csv"
OUTPUT_FILE = DATASET / "live_indicators.csv"


# ============================================================
# SMMA
# ============================================================

def smma(series, period):

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

    first_value = (
        valid.iloc[:period]
        .mean()
    )

    result.loc[first_index] = first_value

    previous = first_value

    for i in range(period, len(valid)):

        current = valid.iloc[i]

        previous = (
            (previous * (period - 1))
            + current
        ) / period

        result.loc[valid.index[i]] = previous

    return result


# ============================================================
# LOAD LIVE DATA
# ============================================================

def load_live():

    if not LIVE_FILE.exists():
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            LIVE_FILE
        )

    except Exception:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["ltp"] = pd.to_numeric(
        df["ltp"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "timestamp",
            "symbol",
            "ltp"
        ]
    )

    return df


# ============================================================
# UPDATE HISTORY
# ============================================================

def update_history(live):

    if live.empty:
        return pd.DataFrame()

    new_data = live[
        [
            "timestamp",
            "symbol",
            "ltp"
        ]
    ].copy()

    if HISTORY_FILE.exists():

        try:

            old = pd.read_csv(
                HISTORY_FILE
            )

            old["timestamp"] = pd.to_datetime(
                old["timestamp"],
                errors="coerce"
            )

            old["ltp"] = pd.to_numeric(
                old["ltp"],
                errors="coerce"
            )

            history = pd.concat(
                [
                    old,
                    new_data
                ],
                ignore_index=True
            )

        except Exception:

            history = new_data.copy()

    else:

        history = new_data.copy()

    history = history.dropna(
        subset=[
            "timestamp",
            "symbol",
            "ltp"
        ]
    )

    # Remove exact duplicate ticks
    history = history.drop_duplicates(
        subset=[
            "timestamp",
            "symbol",
            "ltp"
        ]
    )

    history = history.sort_values(
        [
            "symbol",
            "timestamp"
        ]
    )

    # Keep a reasonable rolling history
    cutoff = (
        pd.Timestamp.now()
        - pd.Timedelta(days=5)
    )

    history = history[
        history["timestamp"] >= cutoff
    ]

    history.to_csv(
        HISTORY_FILE,
        index=False
    )

    return history


# ============================================================
# CREATE 1-MINUTE PRICE DATA
# ============================================================

def create_indicators(history):

    if history.empty:
        return pd.DataFrame()

    history = history.copy()

    history["timestamp"] = pd.to_datetime(
        history["timestamp"],
        errors="coerce"
    )

    history["ltp"] = pd.to_numeric(
        history["ltp"],
        errors="coerce"
    )

    history = history.dropna(
        subset=[
            "timestamp",
            "symbol",
            "ltp"
        ]
    )

    candles = (
        history
        .set_index("timestamp")
        .groupby("symbol")["ltp"]
        .resample("1min")
        .last()
        .dropna()
        .reset_index()
    )

    result = []

    for symbol, group in candles.groupby(
        "symbol"
    ):

        group = group.sort_values(
            "timestamp"
        ).copy()

        group["smma20"] = smma(
            group["ltp"],
            20
        )

        group["smma120"] = smma(
            group["ltp"],
            120
        )

        group["previous_smma20"] = (
            group["smma20"].shift(1)
        )

        group["previous_smma120"] = (
            group["smma120"].shift(1)
        )

        # ----------------------------------------------------
        # BUY CROSSOVER
        # ----------------------------------------------------

        buy = (
            (group["previous_smma20"]
             <=
             group["previous_smma120"])
            &
            (group["smma20"]
             >
             group["smma120"])
        )

        # ----------------------------------------------------
        # SELL CROSSOVER
        # ----------------------------------------------------

        sell = (
            (group["previous_smma20"]
             >=
             group["previous_smma120"])
            &
            (group["smma20"]
             <
             group["smma120"])
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

        result.append(group)

    if not result:
        return pd.DataFrame()

    return pd.concat(
        result,
        ignore_index=True
    )


# ============================================================
# MAIN LOOP
# ============================================================

print("=" * 80)
print("STOCKAI — SMMA INDICATOR ENGINE")
print("=" * 80)

print()
print("Waiting for live data...")


while True:

    live = load_live()

    if live.empty:

        time.sleep(5)
        continue

    history = update_history(
        live
    )

    indicators = create_indicators(
        history
    )

    if not indicators.empty:

        indicators.to_csv(
            OUTPUT_FILE,
            index=False
        )

        latest = (
            indicators
            .sort_values("timestamp")
            .groupby("symbol")
            .tail(1)
        )

        buy_count = (
            latest["signal"]
            .eq("BUY")
            .sum()
        )

        sell_count = (
            latest["signal"]
            .eq("SELL")
            .sum()
        )

        ready = (
            latest["smma120"]
            .notna()
            .sum()
        )

        print(
            f"\rStocks={len(latest):4d} | "
            f"SMMA-ready={ready:4d} | "
            f"BUY={buy_count:3d} | "
            f"SELL={sell_count:3d}",
            end="",
            flush=True
        )

    time.sleep(5)