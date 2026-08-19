from pathlib import Path
import time
import pandas as pd


# ============================================================
# STOCKAI — ANGEL ONE LTP HISTORY COLLECTOR
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

TICK_FILE = DATASET / "live_ticks.csv"
HISTORY_FILE = DATASET / "live_ltp_history.csv"

POLL_SECONDS = 2


# ============================================================
# SYMBOL NORMALIZATION
# ============================================================

def normalize_symbol(value):
    value = str(value).strip().upper()

    if ":" in value:
        value = value.split(":", 1)[1]

    if value.endswith("-EQ"):
        value = value[:-3]

    return value


# ============================================================
# COLLECT NEW TICKS
# ============================================================

def append_new_ticks():

    if not TICK_FILE.exists():
        return 0

    try:
        ticks = pd.read_csv(
            TICK_FILE,
            low_memory=False
        )
    except Exception as exc:
        print("Read error:", exc)
        return 0

    required = {
        "Symbol",
        "Timestamp",
        "LTP",
        "LTQ",
    }

    missing = required - set(ticks.columns)

    if missing:
        print(
            "Missing columns:",
            sorted(missing)
        )
        return 0

    ticks = ticks[
        [
            "Timestamp",
            "Symbol",
            "LTP",
            "LTQ",
        ]
    ].copy()

    ticks["Timestamp"] = pd.to_datetime(
        ticks["Timestamp"],
        errors="coerce"
    )

    ticks["LTP"] = pd.to_numeric(
        ticks["LTP"],
        errors="coerce"
    )

    ticks["LTQ"] = pd.to_numeric(
        ticks["LTQ"],
        errors="coerce"
    )

    ticks["Symbol"] = (
        ticks["Symbol"]
        .astype(str)
        .map(normalize_symbol)
    )

    ticks = ticks.dropna(
        subset=[
            "Timestamp",
            "LTP",
        ]
    )

    ticks = ticks[
        ticks["LTP"] > 0
    ]

    if ticks.empty:
        return 0

    ticks = ticks.sort_values(
        "Timestamp"
    )

    # --------------------------------------------------------
    # LOAD EXISTING HISTORY
    # --------------------------------------------------------

    if HISTORY_FILE.exists():

        try:

            existing = pd.read_csv(
                HISTORY_FILE,
                low_memory=False
            )

            if not existing.empty:

                existing["Timestamp"] = pd.to_datetime(
                    existing["Timestamp"],
                    errors="coerce"
                )

                # Remove corrupted timestamps
                existing = existing.dropna(
                    subset=["Timestamp"]
                )

                # Normalize existing symbols
                existing["Symbol"] = (
                    existing["Symbol"]
                    .astype(str)
                    .map(normalize_symbol)
                )

                # Keep only valid LTP
                existing["LTP"] = pd.to_numeric(
                    existing["LTP"],
                    errors="coerce"
                )

                existing = existing.dropna(
                    subset=["LTP"]
                )

                # ------------------------------------------------
                # Remove duplicate ticks already stored
                # ------------------------------------------------

                existing_keys = set(
                    zip(
                        existing["Timestamp"].astype(str),
                        existing["Symbol"],
                        existing["LTP"].astype(str),
                    )
                )

                tick_keys = list(
                    zip(
                        ticks["Timestamp"].astype(str),
                        ticks["Symbol"],
                        ticks["LTP"].astype(str),
                    )
                )

                mask = [
                    key not in existing_keys
                    for key in tick_keys
                ]

                ticks = ticks.loc[
                    mask
                ]

        except Exception as exc:

            print(
                "History read warning:",
                exc
            )

    if ticks.empty:
        return 0

    # --------------------------------------------------------
    # APPEND
    # --------------------------------------------------------

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ticks.to_csv(
        HISTORY_FILE,
        mode="a",
        header=not HISTORY_FILE.exists(),
        index=False
    )

    return len(ticks)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("STOCKAI — ANGEL ONE LTP HISTORY COLLECTOR")
    print("=" * 65)

    print()
    print("Input :", TICK_FILE)
    print("Output:", HISTORY_FILE)
    print("Poll  :", POLL_SECONDS, "seconds")
    print()

    while True:

        try:

            count = append_new_ticks()

            if count:
                print(
                    f"Saved {count} new LTP/LTQ ticks"
                )

            time.sleep(
                POLL_SECONDS
            )

        except KeyboardInterrupt:

            print()
            print("Stopped.")
            break

        except Exception as exc:

            print(
                "Collector error:",
                exc
            )

            time.sleep(
                POLL_SECONDS
            )