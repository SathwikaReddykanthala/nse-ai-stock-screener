from pathlib import Path
import time
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

LIVE_TICKS = DATASET / "live_ticks.csv"
SCREENED_FILE = DATASET / "live_screened_stocks.csv"

MIN_PRICE = 30
MAX_PRICE = 500
MIN_QTY = 1_000_000


def load_live_data():
    if not LIVE_TICKS.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(LIVE_TICKS)

        if df.empty:
            return pd.DataFrame()

        return df

    except Exception as e:
        print("Read error:", e)
        return pd.DataFrame()


def screen_stocks(df):

    required = [
        "symbol",
        "ltp",
        "bid_qty",
        "ask_qty",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        print("Missing columns:", missing)
        print("Available columns:", list(df.columns))
        return pd.DataFrame()

    # Convert numeric columns
    for col in ["ltp", "bid_qty", "ask_qty"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # Latest tick for every stock
    latest = (
        df.sort_values("timestamp")
          .drop_duplicates(
              subset=["symbol"],
              keep="last"
          )
          .copy()
    )

    # --------------------------------------------------------
    # PRICE FILTER
    # --------------------------------------------------------

    price_filtered = latest[
        latest["ltp"].between(
            MIN_PRICE,
            MAX_PRICE,
            inclusive="both"
        )
    ].copy()

    # --------------------------------------------------------
    # LIQUIDITY FILTER
    # --------------------------------------------------------

    screened = price_filtered[
        (price_filtered["bid_qty"] > MIN_QTY)
        &
        (price_filtered["ask_qty"] > MIN_QTY)
    ].copy()

    return screened


print("=" * 70)
print("STOCKAI — LIVE NSE STOCK SCREENER")
print("=" * 70)

print()
print(f"Input : {LIVE_TICKS}")
print(f"Output: {SCREENED_FILE}")
print()
print("Price range :", f"₹{MIN_PRICE} - ₹{MAX_PRICE}")
print("Bid Qty     :", f"> {MIN_QTY:,}")
print("Ask Qty     :", f"> {MIN_QTY:,}")
print()


while True:

    df = load_live_data()

    if df.empty:
        print("Waiting for live tick data...")
        time.sleep(2)
        continue

    screened = screen_stocks(df)

    # Save results
    screened.to_csv(
        SCREENED_FILE,
        index=False
    )

    print("\033[2J\033[H", end="")

    print("=" * 70)
    print("STOCKAI — LIVE NSE STOCK SCREENER")
    print("=" * 70)

    print(
        f"Live symbols received : "
        f"{df['symbol'].nunique():,}"
    )

    print(
        f"₹30–₹500 stocks       : "
        f"{len(df[df['ltp'].between(30, 500)]):,}"
    )

    print(
        f"Liquidity passed      : "
        f"{len(screened):,}"
    )

    print("=" * 70)

    if screened.empty:

        print("No stocks currently satisfy the screen.")

    else:

        display_columns = [
            "symbol",
            "ltp",
            "bid_qty",
            "ask_qty",
        ]

        print(
            screened[
                display_columns
            ].to_string(index=False)
        )

    time.sleep(2)