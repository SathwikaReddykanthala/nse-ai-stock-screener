import os
from pathlib import Path

from dotenv import load_dotenv
from fyers_apiv3.FyersWebsocket import data_ws


ROOT = Path(__file__).resolve().parent.parent

load_dotenv(ROOT / ".env")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("ACCESS_TOKEN not found in .env")


SYMBOLS = [
    "NSE:RELIANCE-EQ",
    "NSE:TCS-EQ",
    "NSE:INFY-EQ",
    "NSE:HDFCBANK-EQ",
    "NSE:ICICIBANK-EQ",
]


def on_message(message):

    print("\n" + "=" * 80)
    print("DEPTH MESSAGE")
    print("=" * 80)

    print(message)


def on_error(message):
    print("\nERROR:")
    print(message)


def on_close(message):
    print("\nCLOSED:")
    print(message)


def on_open():
    print("\nWEBSOCKET CONNECTED")

    print("\nSubscribing to DepthUpdate:")

    for symbol in SYMBOLS:
        print(symbol)

    fyers.subscribe(
        symbols=SYMBOLS,
        data_type="DepthUpdate"
    )

    fyers.keep_running()


logs = ROOT / "logs"
logs.mkdir(exist_ok=True)


fyers = data_ws.FyersDataSocket(
    access_token=ACCESS_TOKEN,
    log_path=str(logs) + "\\",
    litemode=False,
    write_to_file=False,
    reconnect=True,
    on_connect=on_open,
    on_close=on_close,
    on_error=on_error,
    on_message=on_message,
)


print("=" * 80)
print("STOCKAI — FYERS DEPTH TEST")
print("=" * 80)

fyers.connect()