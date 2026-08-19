import requests
import pandas as pd
from pathlib import Path

# ============================================================
# ANGEL ONE INSTRUMENT MASTER
# NSE EQUITY ONLY
# ============================================================

URL = (
    "https://margincalculator.angelbroking.com/"
    "OpenAPI_File/files/OpenAPIScripMaster.json"
)

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
OUTPUT = DATASET / "angel_nse_instruments.csv"

print("Downloading Angel One instrument master...")

response = requests.get(URL, timeout=60)
response.raise_for_status()

data = response.json()

print(f"Downloaded {len(data):,} instruments")

# ============================================================
# CORRECT NSE EQUITY FILTER
#
# Angel One NSE equity rows:
#   exch_seg = NSE
#   symbol   usually ends with -EQ
#
# instrumenttype may be EMPTY for NSE equity.
# ============================================================

rows = []

for item in data:

    exchange = str(
        item.get("exch_seg", "")
    ).strip().upper()

    symbol = str(
        item.get("symbol", "")
    ).strip().upper()

    # Correct filter
    if exchange != "NSE":
        continue

    if not symbol.endswith("-EQ"):
        continue

    rows.append({
        "token": str(item.get("token", "")).strip(),
        "symbol": symbol,
        "name": str(item.get("name", "")).strip(),
        "expiry": str(item.get("expiry", "")).strip(),
        "strike": str(item.get("strike", "")).strip(),
        "lotsize": str(item.get("lotsize", "")).strip(),
        "instrumenttype": str(
            item.get("instrumenttype", "")
        ).strip(),
        "exch_seg": exchange,
        "tick_size": str(
            item.get("tick_size", "")
        ).strip(),
    })

# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(rows)

if df.empty:
    raise RuntimeError(
        "No NSE-EQ instruments found. "
        "Check the Angel One instrument master format."
    )

# Remove duplicate tokens
df = df.drop_duplicates(
    subset=["token"],
    keep="first"
)

# Sort alphabetically
df = df.sort_values(
    "symbol"
).reset_index(drop=True)

# ============================================================
# SAVE
# ============================================================

DATASET.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

# ============================================================
# RESULT
# ============================================================

print()
print("=" * 60)
print("ANGEL ONE NSE EQUITY INSTRUMENTS READY")
print("=" * 60)

print(f"Output : {OUTPUT}")
print(f"Stocks : {len(df):,}")

print("=" * 60)

print()
print("FIRST 20 NSE EQUITY STOCKS")
print("-" * 60)

print(
    df[
        [
            "token",
            "symbol",
            "name",
            "exch_seg"
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print()
print("Example token lookup:")

for stock in [
    "RELIANCE-EQ",
    "TCS-EQ",
    "INFY-EQ",
    "HDFCBANK-EQ",
    "ICICIBANK-EQ"
]:

    match = df[
        df["symbol"] == stock
    ]

    if not match.empty:
        print(
            f"{stock:20} -> "
            f"{match.iloc[0]['token']}"
        )