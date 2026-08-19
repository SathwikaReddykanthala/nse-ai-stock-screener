from pathlib import Path
import time
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

TICK_FILE = DATASET / "live_ticks.csv"
HISTORY_FILE = DATASET / "live_ltp_history.csv"
POLL_SECONDS = 2


def normalize_symbol(value):
    value = str(value).strip().upper()
    if ":" in value:
        value = value.split(":", 1)[1]
    if value.endswith("-EQ"):
        value = value[:-3]
    return value


def append_new_ticks():
    if not TICK_FILE.exists():
        return 0

    try:
        ticks = pd.read_csv(TICK_FILE, low_memory=False)
    except Exception as exc:
        print("Read error:", exc)
        return 0

    required = {"Symbol", "Timestamp", "LTP"}
    if not required.issubset(ticks.columns):
        print("Missing columns:", sorted(required))
        return 0

    ticks = ticks[["Timestamp", "Symbol", "LTP"]].copy()
    ticks["Timestamp"] = pd.to_datetime(ticks["Timestamp"], errors="coerce")
    ticks["LTP"] = pd.to_numeric(ticks["LTP"], errors="coerce")
    ticks["Symbol"] = ticks["Symbol"].astype(str).map(normalize_symbol)
    ticks = ticks.dropna(subset=["Timestamp", "LTP"])
    ticks = ticks[ticks["LTP"] > 0]

    if ticks.empty:
        return 0

    if HISTORY_FILE.exists():
        try:
            existing = pd.read_csv(HISTORY_FILE, low_memory=False)
            if not existing.empty:
                existing["Timestamp"] = pd.to_datetime(
                    existing["Timestamp"], errors="coerce"
                )
                last_ts = existing["Timestamp"].max()
                if pd.notna(last_ts):
                    ticks = ticks[ticks["Timestamp"] > last_ts]
        except Exception:
            pass

    if ticks.empty:
        return 0

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ticks.to_csv(
        HISTORY_FILE,
        mode="a",
        header=not HISTORY_FILE.exists(),
        index=False
    )
    return len(ticks)


def trim_history():
    if not HISTORY_FILE.exists():
        return

    try:
        df = pd.read_csv(HISTORY_FILE, low_memory=False)
        if df.empty:
            return

        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"], errors="coerce"
        )
        df = df.dropna(subset=["Timestamp"]).sort_values("Timestamp")
        df["_Symbol"] = df["Symbol"].astype(str).map(normalize_symbol)

        df = (
            df.groupby("_Symbol", group_keys=False)
            .tail(60)
            .drop(columns=["_Symbol"])
        )

        df.to_csv(HISTORY_FILE, index=False)

    except Exception as exc:
        print("Trim error:", exc)


if __name__ == "__main__":
    print("=" * 60)
    print("ANGEL ONE LTP HISTORY COLLECTOR")
    print("=" * 60)
    print("Input :", TICK_FILE)
    print("Output:", HISTORY_FILE)
    print("Poll  :", POLL_SECONDS, "seconds")
    print()

    while True:
        try:
            count = append_new_ticks()

            if count:
                print(f"Saved {count} new LTP ticks")

            if int(time.time()) % 60 < POLL_SECONDS:
                trim_history()

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except Exception as exc:
            print("Collector error:", exc)
            time.sleep(POLL_SECONDS)