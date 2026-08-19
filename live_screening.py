from pathlib import Path
import time
import pandas as pd


# ============================================================
# STOCKAI — LIVE NSE STOCK SCREENING
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

LIVE_FILE = DATASET / "live_market.csv"
OUTPUT_FILE = DATASET / "live_screened_stocks.csv"

MIN_LTP = 30
MAX_LTP = 500
MIN_QTY = 1_000_000


# ============================================================
# LOAD LIVE DATA
# ============================================================

def load_live_data():

    if not LIVE_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(LIVE_FILE)

        if df.empty:
            return pd.DataFrame()

        return df

    except Exception as e:

        print("Unable to read live_market.csv:", e)

        return pd.DataFrame()


# ============================================================
# SCREEN
# ============================================================

def screen(df):

    required = [
        "symbol",
        "ltp",
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

        print(
            "Missing columns:",
            missing
        )

        return pd.DataFrame()

    # Numeric conversion

    numeric = [
        "ltp",
        "bid_price",
        "bid_qty",
        "ask_price",
        "ask_qty",
    ]

    for col in numeric:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Keep stocks with valid LTP
    # --------------------------------------------------------

    df = df[
        df["ltp"].notna()
    ].copy()

    # --------------------------------------------------------
    # LTP SCREEN
    # --------------------------------------------------------

    price_screen = df[
        df["ltp"].between(
            MIN_LTP,
            MAX_LTP,
            inclusive="both"
        )
    ].copy()

    # --------------------------------------------------------
    # LIQUIDITY SCREEN
    # --------------------------------------------------------

    passed = price_screen[
        (price_screen["bid_qty"] > MIN_QTY)
        &
        (price_screen["ask_qty"] > MIN_QTY)
    ].copy()

    # --------------------------------------------------------
    # Sort by Bid + Ask liquidity
    # --------------------------------------------------------

    passed["total_best_qty"] = (
        passed["bid_qty"]
        +
        passed["ask_qty"]
    )

    passed = passed.sort_values(
        "total_best_qty",
        ascending=False
    )

    return passed


# ============================================================
# MAIN LOOP
# ============================================================

print("=" * 80)
print("STOCKAI — LIVE NSE STOCK SCREENING")
print("=" * 80)

print()
print("Input :", LIVE_FILE)
print("Output:", OUTPUT_FILE)

print()
print("LTP range:")
print(f"₹{MIN_LTP} to ₹{MAX_LTP}")

print()
print(
    "Bid Quantity >",
    f"{MIN_QTY:,}"
)

print(
    "Ask Quantity >",
    f"{MIN_QTY:,}"
)

print("=" * 80)


while True:

    df = load_live_data()

    if df.empty:

        print(
            "\rWaiting for live_market.csv...",
            end="",
            flush=True
        )

        time.sleep(2)

        continue

    # --------------------------------------------------------
    # SCREEN
    # --------------------------------------------------------

    passed = screen(df)

    # --------------------------------------------------------
    # Count price-screened stocks
    # --------------------------------------------------------

    working = df.copy()

    working["ltp"] = pd.to_numeric(
        working["ltp"],
        errors="coerce"
    )

    price_count = working[
        working["ltp"].between(
            MIN_LTP,
            MAX_LTP,
            inclusive="both"
        )
    ]["symbol"].nunique()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    passed.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\033[2J\033[H", end="")

    print("=" * 80)
    print("STOCKAI — LIVE NSE STOCK SCREENING")
    print("=" * 80)

    print()
    print(
        f"Live symbols       : {df['symbol'].nunique():,}"
    )

    print(
        f"₹30–₹500           : {price_count:,}"
    )

    print(
        f"PASS SCREEN        : {len(passed):,}"
    )

    print()
    print("=" * 80)

    if passed.empty:

        print()
        print(
            "No stocks currently satisfy "
            "the liquidity conditions."
        )

    else:

        columns = [
            "symbol",
            "ltp",
            "bid_price",
            "bid_qty",
            "ask_price",
            "ask_qty",
        ]

        print()

        print(
            passed[columns]
            .to_string(index=False)
        )

    time.sleep(2)