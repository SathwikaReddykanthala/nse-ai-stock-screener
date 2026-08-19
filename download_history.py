import os
import time
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel


# ============================================================
# STOCKAI — FYERS HISTORICAL 5-MINUTE CANDLE DOWNLOADER
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "dataset"
HISTORY = DATASET / "history"

UNIVERSE_FILE = DATASET / "nse_universe.csv"

ENV_FILE = ROOT / ".env"

HISTORY.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD ENV
# ============================================================

load_dotenv(ENV_FILE)

CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not CLIENT_ID:
    raise RuntimeError("FYERS_CLIENT_ID not found in .env")

if not ACCESS_TOKEN:
    raise RuntimeError("ACCESS_TOKEN not found in .env")


# ============================================================
# FYERS CLIENT
# ============================================================

fyers = fyersModel.FyersModel(
    client_id=CLIENT_ID,
    token=ACCESS_TOKEN,
    log_path=str(ROOT / "logs")
)


# ============================================================
# LOAD NSE UNIVERSE
# ============================================================

if not UNIVERSE_FILE.exists():

    raise FileNotFoundError(
        f"NSE universe not found:\n{UNIVERSE_FILE}"
    )


universe = pd.read_csv(
    UNIVERSE_FILE
)


if "Symbol" not in universe.columns:

    raise ValueError(
        "nse_universe.csv must contain Symbol column"
    )


symbols = (
    universe["Symbol"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .tolist()
)


# Only NSE equity symbols
symbols = [
    s for s in symbols
    if s.startswith("NSE:")
    and s.endswith("-EQ")
]


print("=" * 75)
print("STOCKAI — FYERS HISTORICAL 5-MINUTE DOWNLOADER")
print("=" * 75)

print(
    "NSE equity symbols:",
    len(symbols)
)

print(
    "History directory:",
    HISTORY
)


# ============================================================
# DATE RANGE
# ============================================================

# Download approximately 20 trading days.
#
# FYERS historical API uses epoch timestamps.
#
# We request 5-minute candles.

TO_DATE = datetime.now()

FROM_DATE = TO_DATE - timedelta(
    days=35
)


FROM_STR = FROM_DATE.strftime(
    "%Y-%m-%d"
)

TO_STR = TO_DATE.strftime(
    "%Y-%m-%d"
)


print(
    "From:",
    FROM_STR
)

print(
    "To:",
    TO_STR
)


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_symbol(symbol):

    safe_symbol = (
        symbol
        .replace("NSE:", "")
        .replace("-EQ", "")
        .replace(":", "")
        .replace("\\", "")
        .strip()
    )

    output = HISTORY / f"{safe_symbol}.csv"


    # --------------------------------------------------------
    # Skip if we already have sufficient history
    # --------------------------------------------------------

    if output.exists():

        try:

            existing = pd.read_csv(
                output
            )

            if len(existing) >= 1000:

                return (
                    "SKIP",
                    symbol,
                    len(existing)
                )

        except Exception:

            pass


    # --------------------------------------------------------
    # FYERS request
    # --------------------------------------------------------

    data = {
        "symbol": symbol,
        "resolution": "5",
        "date_format": "1",
        "range_from": FROM_STR,
        "range_to": TO_STR,
        "cont_flag": "1"
    }


    try:

        response = fyers.history(
            data=data
        )


        if not isinstance(
            response,
            dict
        ):

            return (
                "ERROR",
                symbol,
                "Invalid response"
            )


        if response.get("s") != "ok":

            return (
                "NO_DATA",
                symbol,
                response.get(
                    "message",
                    response
                )
            )


        candles = response.get(
            "candles",
            []
        )


        if not candles:

            return (
                "NO_DATA",
                symbol,
                0
            )


        df = pd.DataFrame(
            candles,
            columns=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        )


        # ----------------------------------------------------
        # Convert timestamp
        # ----------------------------------------------------

        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"],
            unit="s",
            errors="coerce"
        )


        # ----------------------------------------------------
        # Numeric columns
        # ----------------------------------------------------

        numeric = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]


        for col in numeric:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )


        df = df.dropna(
            subset=[
                "Timestamp",
                "Close"
            ]
        )


        df = df.sort_values(
            "Timestamp"
        )


        df = df.drop_duplicates(
            "Timestamp",
            keep="last"
        )


        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        df.to_csv(
            output,
            index=False
        )


        return (
            "DOWNLOADED",
            symbol,
            len(df)
        )


    except Exception as e:

        return (
            "ERROR",
            symbol,
            str(e)
        )


# ============================================================
# MAIN LOOP
# ============================================================

downloaded = 0
skipped = 0
no_data = 0
errors = 0


for i, symbol in enumerate(
    symbols,
    start=1
):

    status, name, info = download_symbol(
        symbol
    )


    if status == "DOWNLOADED":

        downloaded += 1

    elif status == "SKIP":

        skipped += 1

    elif status == "NO_DATA":

        no_data += 1

    else:

        errors += 1


    print(
        f"[{i:4d}/{len(symbols)}] "
        f"{status:<10} "
        f"{name:<30} "
        f"{info}"
    )


    # Avoid hammering the API.
    time.sleep(
        0.15
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 75)
print("DOWNLOAD COMPLETE")
print("=" * 75)

print(
    "Downloaded:",
    downloaded
)

print(
    "Skipped:",
    skipped
)

print(
    "No data:",
    no_data
)

print(
    "Errors:",
    errors
)

print(
    "History files:",
    len(
        list(
            HISTORY.glob("*.csv")
        )
    )
)

print()
print(
    "History directory:"
)

print(HISTORY)