import os
import csv
import time
from pathlib import Path
from datetime import datetime

import pyotp
import pandas as pd
from dotenv import load_dotenv

from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

TOKEN_FILE = DATASET / "angel_screen_tokens.csv"
OUTPUT_FILE = DATASET / "live_ticks.csv"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(ROOT / ".env")

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")


if not all([
    API_KEY,
    CLIENT_CODE,
    PASSWORD,
    TOTP_SECRET,
]):
    raise RuntimeError(
        """
Missing Angel One credentials.

Check your .env file:

ANGEL_API_KEY=...
ANGEL_CLIENT_CODE=...
ANGEL_PASSWORD=...
ANGEL_TOTP_SECRET=...
"""
    )


# ============================================================
# CHECK TOKEN FILE
# ============================================================

if not TOKEN_FILE.exists():
    raise FileNotFoundError(
        f"""
Token file not found:

{TOKEN_FILE}

Run first:

python src/angel_instruments.py
python src/angel_token_matcher.py
"""
    )


tokens_df = pd.read_csv(
    TOKEN_FILE,
    dtype=str
)

tokens_df["token"] = (
    tokens_df["token"]
    .fillna("")
    .astype(str)
    .str.strip()
)

tokens_df["Symbol"] = (
    tokens_df["Symbol"]
    .fillna("")
    .astype(str)
    .str.strip()
)

tokens_df = tokens_df[
    tokens_df["token"] != ""
].copy()

tokens_df = tokens_df[
    tokens_df["Symbol"] != ""
].copy()


if tokens_df.empty:
    raise RuntimeError(
        "No valid Angel One tokens found."
    )


# ============================================================
# TOKEN → SYMBOL MAP
# ============================================================

TOKEN_TO_SYMBOL = dict(
    zip(
        tokens_df["token"],
        tokens_df["Symbol"]
    )
)


TOKENS = list(
    TOKEN_TO_SYMBOL.keys()
)


print()
print("=" * 70)
print("STOCKAI — ANGEL ONE LIVE FEED")
print("=" * 70)

print(
    f"Stocks loaded : {len(TOKENS)}"
)

print(
    f"Output file   : {OUTPUT_FILE}"
)

print("=" * 70)


# ============================================================
# CSV COLUMNS
# ============================================================

FIELDS = [
    "Symbol",
    "Timestamp",
    "LTP",
    "LTQ",
    "BidQty",
    "AskQty",

    "BidPrice1",
    "BidQty1",
    "BidPrice2",
    "BidQty2",
    "BidPrice3",
    "BidQty3",
    "BidPrice4",
    "BidQty4",
    "BidPrice5",
    "BidQty5",

    "AskPrice1",
    "AskQty1",
    "AskPrice2",
    "AskQty2",
    "AskPrice3",
    "AskQty3",
    "AskPrice4",
    "AskQty4",
    "AskPrice5",
    "AskQty5",
]


# ============================================================
# PREPARE CSV
# ============================================================

DATASET.mkdir(
    parents=True,
    exist_ok=True
)

# Create a fresh file when the feed starts.
with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=FIELDS
    )

    writer.writeheader()


# ============================================================
# HELPERS
# ============================================================

def price_value(value):
    """
    Angel One WebSocket prices are represented
    in paise in the SDK packet.
    """
    try:
        return float(value) / 100.0
    except Exception:
        return 0.0


def qty_value(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def write_tick(data):

    token = str(
        data.get("token", "")
    ).strip()

    symbol = TOKEN_TO_SYMBOL.get(
        token,
        token
    )

    timestamp_ms = data.get(
        "exchange_timestamp"
    )

    if timestamp_ms:

        try:
            timestamp = datetime.fromtimestamp(
                float(timestamp_ms) / 1000
            ).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3]

        except Exception:
            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3]

    else:

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]


    row = {
        "Symbol": symbol,
        "Timestamp": timestamp,

        "LTP": price_value(
            data.get("last_traded_price", 0)
        ),

        "LTQ": qty_value(
            data.get("last_traded_quantity", 0)
        ),

        "BidQty": qty_value(
            data.get("total_buy_quantity", 0)
        ),

        "AskQty": qty_value(
            data.get("total_sell_quantity", 0)
        ),
    }


    # --------------------------------------------------------
    # BEST 5 BUY
    # --------------------------------------------------------

    buys = data.get(
        "best_5_buy_data",
        []
    )

    # --------------------------------------------------------
    # BEST 5 SELL
    # --------------------------------------------------------

    sells = data.get(
        "best_5_sell_data",
        []
    )


    for i in range(5):

        level = i + 1

        # BUY
        if i < len(buys):

            buy = buys[i]

            row[
                f"BidPrice{level}"
            ] = price_value(
                buy.get("price", 0)
            )

            row[
                f"BidQty{level}"
            ] = qty_value(
                buy.get("quantity", 0)
            )

        else:

            row[
                f"BidPrice{level}"
            ] = 0

            row[
                f"BidQty{level}"
            ] = 0


        # SELL
        if i < len(sells):

            sell = sells[i]

            row[
                f"AskPrice{level}"
            ] = price_value(
                sell.get("price", 0)
            )

            row[
                f"AskQty{level}"
            ] = qty_value(
                sell.get("quantity", 0)
            )

        else:

            row[
                f"AskPrice{level}"
            ] = 0

            row[
                f"AskQty{level}"
            ] = 0


    with open(
        OUTPUT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS
        )

        writer.writerow(row)


    print(
        f"LIVE  {symbol:<15} "
        f"LTP ₹{row['LTP']:<10.2f} "
        f"BID {row['BidQty']:<12.0f} "
        f"ASK {row['AskQty']:<12.0f}"
    )


# ============================================================
# ANGEL ONE LOGIN
# ============================================================

print()
print("Logging in to Angel One...")

smart_api = SmartConnect(
    api_key=API_KEY
)

totp = pyotp.TOTP(
    TOTP_SECRET
).now()

login_response = smart_api.generateSession(
    CLIENT_CODE,
    PASSWORD,
    totp
)


if not login_response.get("status"):

    raise RuntimeError(
        f"Angel One login failed:\n{login_response}"
    )


auth_token = login_response[
    "data"
]["jwtToken"]


feed_token = smart_api.getfeedToken()


print()
print("Angel One login SUCCESS")
print("Feed token received:", bool(feed_token))


# ============================================================
# WEBSOCKET
# ============================================================

sws = SmartWebSocketV2(
    auth_token,
    API_KEY,
    CLIENT_CODE,
    feed_token,
    max_retry_attempt=5,
    retry_strategy=1,
    retry_delay=5,
    retry_multiplier=2,
    retry_duration=30,
)


# ============================================================
# SUBSCRIBE
# ============================================================

def subscribe_tokens():

    token_list = []

    # Angel One supports up to 1000 tokens
    # per WebSocket connection.
    for start in range(
        0,
        len(TOKENS),
        1000
    ):

        batch = TOKENS[
            start:start + 1000
        ]

        token_list.append({
            "exchangeType": 1,
            "tokens": batch,
        })


    for batch_number, item in enumerate(
        token_list,
        start=1
    ):

        print(
            f"Subscribing batch "
            f"{batch_number}: "
            f"{len(item['tokens'])} stocks"
        )

        sws.subscribe(
            f"stockai{batch_number}",
            3,  # SNAP QUOTE
            [item]
        )


# ============================================================
# CALLBACKS
# ============================================================

def on_open(wsapp):

    print()
    print("=" * 70)
    print("ANGEL ONE WEBSOCKET CONNECTED")
    print("=" * 70)

    subscribe_tokens()

    print()
    print("Waiting for live ticks...")
    print()


def on_data(wsapp, message):

    try:

        if not isinstance(
            message,
            dict
        ):
            return

        mode = message.get(
            "subscription_mode"
        )

        if mode != 3:
            return

        write_tick(message)

    except Exception as e:

        print(
            "Data processing error:",
            e
        )


def on_error(wsapp, error):

    print()
    print("WEBSOCKET ERROR:")
    print(error)


def on_close(wsapp):

    print()
    print("WEBSOCKET CLOSED")


def on_control_message(
    wsapp,
    message
):

    print(
        "CONTROL:",
        message
    )


# ============================================================
# CALLBACK ASSIGNMENT
# ============================================================

sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close
sws.on_control_message = on_control_message


# ============================================================
# START
# ============================================================

print()
print("Starting SmartWebSocketV2...")
print()

try:

    sws.connect()

except KeyboardInterrupt:

    print()
    print("Stopping live feed...")

    try:
        sws.close_connection()
    except Exception:
        pass

except Exception as e:

    print()
    print("FATAL WEBSOCKET ERROR:")
    print(e)