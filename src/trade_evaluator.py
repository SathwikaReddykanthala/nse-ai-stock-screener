from pathlib import Path

import pandas as pd


# ============================================================
# STOCKAI — SMMA CROSSOVER TRADE EVALUATOR
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "dataset" / "historical_smma.csv"
OUTPUT_FILE = ROOT / "dataset" / "crossover_trades.csv"


# ============================================================
# LOAD
# ============================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Missing:\n{INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE
)


df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)


df["close"] = pd.to_numeric(
    df["close"],
    errors="coerce"
)


df = df.dropna(
    subset=[
        "timestamp",
        "symbol",
        "close",
    ]
)


df = df.sort_values(
    [
        "symbol",
        "timestamp",
    ]
).reset_index(
    drop=True
)


# ============================================================
# EVALUATE TRADES
# ============================================================

trades = []


for symbol, group in df.groupby(
    "symbol",
    sort=False
):

    group = group.reset_index(
        drop=True
    )

    open_trade = None

    for i, row in group.iterrows():

        signal = row["signal"]

        # ----------------------------------------------------
        # OPEN BUY
        # ----------------------------------------------------

        if signal == "BUY":

            # If another BUY is already open,
            # don't open another position.

            if open_trade is None:

                open_trade = {
                    "symbol": symbol,
                    "trade_type": "BUY",
                    "entry_time": row["timestamp"],
                    "entry_price": row["close"],
                    "entry_index": i,
                }

        # ----------------------------------------------------
        # CLOSE BUY
        # ----------------------------------------------------

        elif signal == "SELL":

            if (
                open_trade is not None
                and
                open_trade["trade_type"] == "BUY"
            ):

                entry_price = (
                    open_trade["entry_price"]
                )

                exit_price = row["close"]

                pnl = (
                    exit_price
                    -
                    entry_price
                )

                trades.append({

                    "symbol": symbol,

                    "trade_type": "BUY",

                    "entry_time":
                        open_trade["entry_time"],

                    "entry_price":
                        entry_price,

                    "exit_time":
                        row["timestamp"],

                    "exit_price":
                        exit_price,

                    "pnl":
                        pnl,

                    "profitable":
                        int(pnl > 0),

                    "holding_minutes":
                        (
                            row["timestamp"]
                            -
                            open_trade["entry_time"]
                        ).total_seconds()
                        / 60,

                })

                open_trade = None

            # ------------------------------------------------
            # OPEN SELL
            # ------------------------------------------------

            if open_trade is None:

                open_trade = {

                    "symbol": symbol,

                    "trade_type": "SELL",

                    "entry_time":
                        row["timestamp"],

                    "entry_price":
                        row["close"],

                    "entry_index": i,
                }

        # ----------------------------------------------------
        # BUY SIGNAL CLOSES SELL
        # ----------------------------------------------------

        # This is handled on the next iteration after
        # detecting BUY when a SELL position exists.

        if signal == "BUY":

            if (
                open_trade is not None
                and
                open_trade["trade_type"] == "SELL"
                and
                open_trade["entry_time"]
                != row["timestamp"]
            ):

                entry_price = (
                    open_trade["entry_price"]
                )

                exit_price = row["close"]

                pnl = (
                    entry_price
                    -
                    exit_price
                )

                trades.append({

                    "symbol": symbol,

                    "trade_type": "SELL",

                    "entry_time":
                        open_trade["entry_time"],

                    "entry_price":
                        entry_price,

                    "exit_time":
                        row["timestamp"],

                    "exit_price":
                        exit_price,

                    "pnl":
                        pnl,

                    "profitable":
                        int(pnl > 0),

                    "holding_minutes":
                        (
                            row["timestamp"]
                            -
                            open_trade["entry_time"]
                        ).total_seconds()
                        / 60,

                })

                open_trade = None

                # The current BUY becomes a new BUY position.

                open_trade = {

                    "symbol": symbol,

                    "trade_type": "BUY",

                    "entry_time":
                        row["timestamp"],

                    "entry_price":
                        row["close"],

                    "entry_index": i,
                }


# ============================================================
# CREATE DATAFRAME
# ============================================================

trades_df = pd.DataFrame(
    trades
)


if trades_df.empty:

    raise RuntimeError(
        "No completed crossover trades found."
    )


# ============================================================
# SAVE
# ============================================================

trades_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

total = len(trades_df)

profitable = (
    trades_df["profitable"]
    .sum()
)

losing = (
    total
    -
    profitable
)

win_rate = (
    profitable / total * 100
)


buy_trades = (
    trades_df["trade_type"]
    .eq("BUY")
    .sum()
)

sell_trades = (
    trades_df["trade_type"]
    .eq("SELL")
    .sum()
)


total_pnl = (
    trades_df["pnl"]
    .sum()
)


avg_pnl = (
    trades_df["pnl"]
    .mean()
)


print("=" * 80)
print("STOCKAI — CROSSOVER TRADE EVALUATION")
print("=" * 80)

print()
print("Completed trades :", total)

print(
    "BUY trades       :",
    buy_trades
)

print(
    "SELL trades      :",
    sell_trades
)

print()
print(
    "Profitable trades:",
    profitable
)

print(
    "Losing trades    :",
    losing
)

print(
    f"Win rate         : {win_rate:.2f}%"
)

print()
print(
    f"Total P/L        : {total_pnl:.2f}"
)

print(
    f"Average P/L      : {avg_pnl:.4f}"
)

print()
print("Output:")
print(OUTPUT_FILE)

print("=" * 80)