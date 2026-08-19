from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

INSTRUMENT_FILE = DATASET / "angel_nse_instruments.csv"

# ============================================================
# FIND LATEST SCREENER FILE
# ============================================================

screen_files = [
    p for p in DATASET.rglob("*.csv")
    if "screen" in p.name.lower()
    and p.name.lower() != "angel_nse_instruments.csv"
]

if not screen_files:
    raise FileNotFoundError(
        "No screener CSV found inside dataset."
    )

screen_file = max(
    screen_files,
    key=lambda p: p.stat().st_mtime
)

print("Screener:")
print(screen_file)

# ============================================================
# LOAD FILES
# ============================================================

if not INSTRUMENT_FILE.exists():
    raise FileNotFoundError(
        f"Missing instrument file:\n{INSTRUMENT_FILE}\n\n"
        "Run angel_instruments.py first."
    )

instruments = pd.read_csv(
    INSTRUMENT_FILE,
    dtype=str
)

screen = pd.read_csv(
    screen_file,
    dtype=str
)

# ============================================================
# CHECK SYMBOL COLUMN
# ============================================================

if "Symbol" not in screen.columns:
    print("Available screener columns:")
    print(screen.columns.tolist())

    raise KeyError(
        "The screener CSV does not contain a 'Symbol' column."
    )

if "token" not in instruments.columns:
    raise KeyError(
        "The Angel instrument file does not contain 'token'."
    )

if "symbol" not in instruments.columns:
    raise KeyError(
        "The Angel instrument file does not contain 'symbol'."
    )

# ============================================================
# NORMALIZE SYMBOL
# ============================================================

def normalize_symbol(value):
    value = str(value).strip().upper()

    value = value.replace("NSE:", "")
    value = value.replace("-EQ", "")

    return value.strip()


screen["base_symbol"] = (
    screen["Symbol"]
    .map(normalize_symbol)
)

instruments["base_symbol"] = (
    instruments["symbol"]
    .map(normalize_symbol)
)

# ============================================================
# REMOVE DUPLICATES
# ============================================================

instruments = instruments.drop_duplicates(
    subset=["base_symbol"],
    keep="first"
)

# ============================================================
# MATCH SCREENER → ANGEL TOKEN
# ============================================================

matched = screen.merge(
    instruments[
        [
            "token",
            "symbol",
            "name",
            "exch_seg",
            "base_symbol"
        ]
    ],
    on="base_symbol",
    how="left",
    suffixes=("", "_angel")
)

# ============================================================
# CLEAN TOKEN
# ============================================================

matched["token"] = (
    matched["token"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# ============================================================
# SORT HIGHEST LTP → LOWEST LTP
# ============================================================

if "LTP" in matched.columns:

    matched["LTP_numeric"] = pd.to_numeric(
        matched["LTP"],
        errors="coerce"
    )

    matched = matched.sort_values(
        by="LTP_numeric",
        ascending=False,
        na_position="last"
    )

    matched = matched.drop(
        columns=["LTP_numeric"]
    )

# ============================================================
# SAVE
# ============================================================

output = DATASET / "angel_screen_tokens.csv"

matched.to_csv(
    output,
    index=False,
    encoding="utf-8"
)

# ============================================================
# REPORT
# ============================================================

total = len(matched)

found = (
    matched["token"]
    .ne("")
    .sum()
)

missing = total - found

print()
print("=" * 60)
print("ANGEL ONE TOKEN MATCH")
print("=" * 60)

print(f"Screened stocks : {total}")
print(f"Matched tokens  : {found}")
print(f"Missing tokens  : {missing}")

print("=" * 60)

# ============================================================
# SHOW MATCHED STOCKS
# ============================================================

display_columns = [
    "Symbol",
]

if "LTP" in matched.columns:
    display_columns.append("LTP")

display_columns += [
    "token",
    "symbol_angel"
]

display_columns = [
    c for c in display_columns
    if c in matched.columns
]

print()
print("FIRST 20 MATCHED STOCKS")
print("-" * 60)

print(
    matched[
        display_columns
    ].head(20).to_string(index=False)
)

# ============================================================
# SHOW MISSING STOCKS
# ============================================================

missing_df = matched[
    matched["token"] == ""
]

if not missing_df.empty:

    print()
    print("STOCKS WITHOUT ANGEL TOKEN")
    print("-" * 60)

    print(
        missing_df[
            ["Symbol"]
        ].head(30).to_string(index=False)
    )

# ============================================================
# FINAL
# ============================================================

print()
print("=" * 60)
print("TOKEN FILE CREATED")
print("=" * 60)
print(output)
print("=" * 60)