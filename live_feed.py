import os
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fyers_apiv3.FyersWebsocket import data_ws


# ============================================================
# STOCKAI — FYERS LIVE NSE MARKET + DEPTH FEED
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
LOGS = ROOT / "logs"

DATASET.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

UNIVERSE_FILE = DATASET / "nse_universe.csv"
OUTPUT_FILE = DATASET / "live_ticks.csv"
ENV_FILE = ROOT / ".env"


# ============================================================
# CONFIG
# ============================================================

CHUNK_SIZE = 500

SAVE_EVERY = 10

# Keep only recent rows in memory.
# The CSV will contain the latest live snapshot/history.
MAX_MEMORY_ROWS = 100000


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(ENV_FILE)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError(
        "ACCESS_TOKEN not found in .env"
    )


# ============================================================
# HEADER
# ============================================================

print("=" * 75)
print("STOCKAI — FYERS LIVE NSE MARKET + DEPTH FEED")
print("=" * 75)


# ============================================================
# LOAD NSE UNIVERSE
# ============================================================

if not UNIVERSE_FILE.exists():

    raise FileNotFoundError(
        f"\nNSE universe file not found:\n"
        f"{UNIVERSE_FILE}\n\n"
        f"Create dataset/nse_universe.csv first."
    )


universe = pd.read_csv(
    UNIVERSE_FILE
)


if "Symbol" not in universe.columns:

    raise ValueError(
        "nse_universe.csv must contain a 'Symbol' column."
    )


# ============================================================
# CLEAN SYMBOLS
# ============================================================

SYMBOLS = (
    universe["Symbol"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.replace("\\", "", regex=False)
    .drop_duplicates()
    .tolist()
)


# Only NSE equity symbols.
SYMBOLS = [
    symbol
    for symbol in SYMBOLS
    if symbol.startswith("NSE:")
    and symbol.endswith("-EQ")
]


# Remove obvious malformed values.
SYMBOLS = [
    symbol
    for symbol in SYMBOLS
    if symbol != "NSE:-EQ"
    and len(symbol) > 8
]


print()
print(
    "Total NSE equity symbols:",
    len(SYMBOLS)
)


# ============================================================
# LIVE MEMORY
# ============================================================

live_ticks = {}


# ============================================================
# MESSAGE CALLBACK
# ============================================================

def on_message(message):

    if not isinstance(message, dict):
        return


    symbol = message.get("symbol")

    if not symbol:
        return


    # --------------------------------------------------------
    # Normalize symbol
    # --------------------------------------------------------

    symbol = (
        str(symbol)
        .strip()
        .replace("\\", "")
    )


    # --------------------------------------------------------
    # Extract FYERS values
    # --------------------------------------------------------

    ltp = message.get("ltp")

    if ltp is None:
        return


    now = datetime.now()


    # --------------------------------------------------------
    # FYERS WebSocket fields
    # --------------------------------------------------------

    ltq = message.get("last_traded_qty")

    bid_price = message.get("bid_price")

    bid_qty = message.get("bid_size")

    ask_price = message.get("ask_price")

    ask_qty = message.get("ask_size")


    # --------------------------------------------------------
    # Additional depth fields
    # --------------------------------------------------------

    total_buy_qty = message.get(
        "tot_buy_qty"
    )

    total_sell_qty = message.get(
        "tot_sell_qty"
    )


    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    volume = message.get(
        "vol_traded_today"
    )


    # --------------------------------------------------------
    # If FYERS gives alternate field names
    # --------------------------------------------------------

    if ltq is None:
        ltq = message.get("ltq")


    if bid_qty is None:
        bid_qty = message.get("bid_qty")


    if ask_qty is None:
        ask_qty = message.get("ask_qty")


    if total_buy_qty is None:
        total_buy_qty = message.get(
            "total_buy_qty"
        )


    if total_sell_qty is None:
        total_sell_qty = message.get(
            "total_sell_qty"
        )


    if volume is None:
        volume = message.get(
            "volume"
        )


    # --------------------------------------------------------
    # Build row
    # --------------------------------------------------------

    row = {
        "Timestamp": now,
        "Symbol": symbol,
        "LTP": ltp,
        "LTQ": ltq,
        "BidPrice": bid_price,
        "BidQty": bid_qty,
        "AskPrice": ask_price,
        "AskQty": ask_qty,
        "TotalBuyQty": total_buy_qty,
        "TotalSellQty": total_sell_qty,
        "Volume": volume,
    }


    # --------------------------------------------------------
    # Store latest tick for symbol
    # --------------------------------------------------------

    live_ticks[symbol] = row


    # --------------------------------------------------------
    # Console
    # --------------------------------------------------------

    print(
        f"{now:%H:%M:%S} | "
        f"{symbol:<28} | "
        f"LTP={ltp} | "
        f"LTQ={ltq} | "
        f"BID={bid_price} ({bid_qty}) | "
        f"ASK={ask_price} ({ask_qty})"
    )


    # --------------------------------------------------------
    # Save periodically
    # --------------------------------------------------------

    if len(live_ticks) % SAVE_EVERY == 0:

        save_live_data()


# ============================================================
# SAVE FUNCTION
# ============================================================

def save_live_data():

    if not live_ticks:
        return


    output = pd.DataFrame(
        list(live_ticks.values())
    )


    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "LTP",
        "LTQ",
        "BidPrice",
        "BidQty",
        "AskPrice",
        "AskQty",
        "TotalBuyQty",
        "TotalSellQty",
        "Volume",
    ]


    for column in numeric_columns:

        if column in output.columns:

            output[column] = pd.to_numeric(
                output[column],
                errors="coerce"
            ).fillna(0)


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    output = output.sort_values(
        "Symbol"
    )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# ERROR CALLBACK
# ============================================================

def on_error(message):

    print()
    print("=" * 75)
    print("FYERS WEBSOCKET ERROR")
    print("=" * 75)
    print(message)
    print()


# ============================================================
# CLOSE CALLBACK
# ============================================================

def on_close(message):

    print()
    print("=" * 75)
    print("FYERS WEBSOCKET CLOSED")
    print("=" * 75)
    print(message)
    print()


# ============================================================
# OPEN CALLBACK
# ============================================================

def on_open():

    print()
    print("=" * 75)
    print("FYERS WEBSOCKET CONNECTED")
    print("=" * 75)

    print()
    print(
        "Total symbols:",
        len(SYMBOLS)
    )

    print(
        "Subscription chunks:",
        (
            len(SYMBOLS) + CHUNK_SIZE - 1
        ) // CHUNK_SIZE
    )

    print()


    # --------------------------------------------------------
    # Subscribe in chunks
    # --------------------------------------------------------

    total_chunks = (
        len(SYMBOLS)
        + CHUNK_SIZE
        - 1
    ) // CHUNK_SIZE


    for start in range(
        0,
        len(SYMBOLS),
        CHUNK_SIZE
    ):

        chunk = SYMBOLS[
            start:start + CHUNK_SIZE
        ]

        chunk_number = (
            start // CHUNK_SIZE
        ) + 1


        print(
            f"Subscribing chunk "
            f"{chunk_number}/{total_chunks} "
            f"({len(chunk)} symbols)"
        )


        try:

            fyers.subscribe(
                symbols=chunk,
                data_type="SymbolUpdate"
            )


            print(
                f"Subscribed chunk "
                f"{chunk_number}"
            )


        except Exception as exc:

            print(
                f"Subscription error "
                f"for chunk {chunk_number}:"
            )

            print(exc)


        # Small delay between subscriptions.
        time.sleep(1)


    print()
    print("=" * 75)
    print("SUBSCRIPTION COMPLETE")
    print("=" * 75)

    print()
    print(
        "Waiting for live market + depth data..."
    )

    print()


    # Keep WebSocket alive.
    fyers.keep_running()


# ============================================================
# FYERS WEBSOCKET
# ============================================================

fyers = data_ws.FyersDataSocket(

    access_token=ACCESS_TOKEN,

    log_path=str(LOGS),

    litemode=False,

    write_to_file=False,

    reconnect=True,

    on_connect=on_open,

    on_close=on_close,

    on_error=on_error,

    on_message=on_message,
)


# ============================================================
# START
# ============================================================

print()
print("Starting FYERS WebSocket...")
print()


try:

    fyers.connect()


except KeyboardInterrupt:

    print()
    print("=" * 75)
    print("STOPPING STOCKAI LIVE FEED")
    print("=" * 75)

    save_live_data()

    print()
    print(
        "Saved live data to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print("Feed stopped.")


except Exception as exc:

    print()
    print("=" * 75)
    print("FATAL WEBSOCKET ERROR")
    print("=" * 75)

    print(exc)

    print()

    save_live_data()

    raise