from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

FILE = ROOT / "dataset" / "ml_test_predictions.csv"

if not FILE.exists():
    raise FileNotFoundError(
        f"File not found:\n{FILE}"
    )

df = pd.read_csv(FILE)

print("=" * 70)
print("STOCKAI — ML THRESHOLD ANALYSIS")
print("=" * 70)

print()

print("Current decision summary:")
print(
    df.groupby("decision")["target"]
    .agg(["count", "sum", "mean"])
    .to_string()
)

print()
print("=" * 70)
print("THRESHOLD ANALYSIS")
print("=" * 70)

print()

thresholds = [
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90,
]

for threshold in thresholds:

    accepted = df[
        df["predicted_probability"] >= threshold
    ]

    count = len(accepted)

    profitable = int(
        accepted["target"].sum()
    )

    if count > 0:
        win_rate = (
            profitable
            /
            count
            *
            100
        )
    else:
        win_rate = 0.0

    print(
        f"Threshold {threshold:.2f} | "
        f"Accepted {count:3d} | "
        f"Profitable {profitable:3d} | "
        f"WinRate {win_rate:.2f}%"
    )

print()
print("=" * 70)
print("COMPLETE")
print("=" * 70)