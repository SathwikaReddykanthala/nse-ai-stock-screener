from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.impute import SimpleImputer


# ============================================================
# STOCKAI — ML CROSSOVER PROFITABILITY MODEL
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

SMMA_FILE = ROOT / "dataset" / "historical_smma.csv"
TRADES_FILE = ROOT / "dataset" / "crossover_trades.csv"

MODEL_DIR = ROOT / "models"
MODEL_FILE = MODEL_DIR / "crossover_profit_model.joblib"

TRAINING_FILE = ROOT / "dataset" / "ml_training_data.csv"


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42

# Use the latest 20% of trades as the test set.
TEST_SIZE = 0.20

# Probability above this threshold is considered ACCEPT.
ACCEPT_THRESHOLD = 0.60


# ============================================================
# CHECK FILES
# ============================================================

if not SMMA_FILE.exists():
    raise FileNotFoundError(
        f"Missing SMMA file:\n{SMMA_FILE}"
    )

if not TRADES_FILE.exists():
    raise FileNotFoundError(
        f"Missing trade file:\n{TRADES_FILE}"
    )


print("=" * 80)
print("STOCKAI — ML CROSSOVER PROFITABILITY MODEL")
print("=" * 80)

print()
print("SMMA file   :", SMMA_FILE)
print("Trades file :", TRADES_FILE)


# ============================================================
# LOAD SMMA DATA
# ============================================================

smma = pd.read_csv(
    SMMA_FILE,
    low_memory=False
)

smma.columns = (
    smma.columns
    .str.strip()
    .str.lower()
)

required_smma = {
    "timestamp",
    "symbol",
    "close",
    "smma20",
    "smma120",
}

missing_smma = (
    required_smma
    -
    set(smma.columns)
)

if missing_smma:
    raise ValueError(
        f"Missing columns in historical_smma.csv: "
        f"{sorted(missing_smma)}"
    )


smma["timestamp"] = pd.to_datetime(
    smma["timestamp"],
    errors="coerce"
)

smma["close"] = pd.to_numeric(
    smma["close"],
    errors="coerce"
)

smma["smma20"] = pd.to_numeric(
    smma["smma20"],
    errors="coerce"
)

smma["smma120"] = pd.to_numeric(
    smma["smma120"],
    errors="coerce"
)


smma = smma.dropna(
    subset=[
        "timestamp",
        "symbol",
        "close",
        "smma20",
        "smma120",
    ]
)


smma = smma.sort_values(
    [
        "symbol",
        "timestamp",
    ]
).reset_index(drop=True)


# ============================================================
# NORMALIZE SYMBOL
# ============================================================

def normalize_symbol(value):

    value = str(value).strip().upper()

    if ":" in value:
        value = value.split(":", 1)[1]

    if value.endswith("-EQ"):
        value = value[:-3]

    return value


smma["symbol_clean"] = (
    smma["symbol"]
    .map(normalize_symbol)
)


# ============================================================
# LOAD COMPLETED TRADES
# ============================================================

trades = pd.read_csv(
    TRADES_FILE,
    low_memory=False
)

trades.columns = (
    trades.columns
    .str.strip()
    .str.lower()
)

required_trades = {
    "symbol",
    "trade_type",
    "entry_time",
    "entry_price",
    "exit_time",
    "exit_price",
    "pnl",
    "profitable",
}

missing_trades = (
    required_trades
    -
    set(trades.columns)
)

if missing_trades:
    raise ValueError(
        f"Missing columns in crossover_trades.csv: "
        f"{sorted(missing_trades)}"
    )


trades["entry_time"] = pd.to_datetime(
    trades["entry_time"],
    errors="coerce"
)

trades["exit_time"] = pd.to_datetime(
    trades["exit_time"],
    errors="coerce"
)

trades["entry_price"] = pd.to_numeric(
    trades["entry_price"],
    errors="coerce"
)

trades["exit_price"] = pd.to_numeric(
    trades["exit_price"],
    errors="coerce"
)

trades["pnl"] = pd.to_numeric(
    trades["pnl"],
    errors="coerce"
)

trades["profitable"] = pd.to_numeric(
    trades["profitable"],
    errors="coerce"
)


trades["symbol_clean"] = (
    trades["symbol"]
    .map(normalize_symbol)
)


trades = trades.dropna(
    subset=[
        "entry_time",
        "entry_price",
        "profitable",
    ]
)


# ============================================================
# PREPARE HISTORICAL PRICE FEATURES
# ============================================================

smma["smma_diff"] = (
    smma["smma20"]
    -
    smma["smma120"]
)

smma["smma_diff_pct"] = (
    smma["smma_diff"]
    /
    smma["smma120"].replace(0, np.nan)
) * 100


# ------------------------------------------------------------
# Price returns
# ------------------------------------------------------------

smma["return_1"] = (
    smma.groupby("symbol_clean")["close"]
    .pct_change(1)
    * 100
)

smma["return_5"] = (
    smma.groupby("symbol_clean")["close"]
    .pct_change(5)
    * 100
)


# ============================================================
# LOAD ORIGINAL OHLCV DATA
# ============================================================

historical_file = (
    ROOT.parent
    / "StockAI"
    / "dataset"
    / "historical_20days.csv"
)


if not historical_file.exists():

    raise FileNotFoundError(
        f"Missing historical OHLCV file:\n"
        f"{historical_file}"
    )


ohlcv = pd.read_csv(
    historical_file,
    low_memory=False
)

ohlcv.columns = (
    ohlcv.columns
    .str.strip()
)


required_ohlcv = {
    "Timestamp",
    "Symbol",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
}

missing_ohlcv = (
    required_ohlcv
    -
    set(ohlcv.columns)
)

if missing_ohlcv:
    raise ValueError(
        f"Missing columns in historical_20days.csv: "
        f"{sorted(missing_ohlcv)}"
    )


# ============================================================
# TIMESTAMP
# ============================================================

ohlcv["Timestamp"] = pd.to_datetime(
    pd.to_numeric(
        ohlcv["Timestamp"],
        errors="coerce"
    ),
    unit="s",
    errors="coerce"
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

for column in [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]:

    ohlcv[column] = pd.to_numeric(
        ohlcv[column],
        errors="coerce"
    )


ohlcv = ohlcv.dropna(
    subset=[
        "Timestamp",
        "Symbol",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
)


ohlcv["symbol_clean"] = (
    ohlcv["Symbol"]
    .map(normalize_symbol)
)


ohlcv = ohlcv.sort_values(
    [
        "symbol_clean",
        "Timestamp",
    ]
).reset_index(drop=True)


# ============================================================
# OHLCV FEATURES
# ============================================================

ohlcv["range_pct"] = (
    (
        ohlcv["High"]
        -
        ohlcv["Low"]
    )
    /
    ohlcv["Close"].replace(0, np.nan)
) * 100


ohlcv["body_pct"] = (
    (
        ohlcv["Close"]
        -
        ohlcv["Open"]
    )
    /
    ohlcv["Open"].replace(0, np.nan)
) * 100


ohlcv["return_1"] = (
    ohlcv.groupby("symbol_clean")["Close"]
    .pct_change(1)
    * 100
)


ohlcv["return_5"] = (
    ohlcv.groupby("symbol_clean")["Close"]
    .pct_change(5)
    * 100
)


ohlcv["volume_change_pct"] = (
    ohlcv.groupby("symbol_clean")["Volume"]
    .pct_change()
    * 100
)


ohlcv["volume_ma_5"] = (
    ohlcv.groupby("symbol_clean")["Volume"]
    .transform(
        lambda x:
        x.rolling(
            5,
            min_periods=1
        ).mean()
    )
)


ohlcv["volume_ratio"] = (
    ohlcv["Volume"]
    /
    ohlcv["volume_ma_5"].replace(0, np.nan)
)


# ============================================================
# PREPARE OHLCV FOR MERGE
# ============================================================

ohlcv_features = ohlcv[
    [
        "Timestamp",
        "symbol_clean",
        "range_pct",
        "body_pct",
        "return_1",
        "return_5",
        "volume_change_pct",
        "volume_ratio",
    ]
].copy()


ohlcv_features = ohlcv_features.rename(
    columns={
        "Timestamp": "timestamp"
    }
)


# ============================================================
# MERGE TRADE ENTRY WITH SMMA FEATURES
# ============================================================

training = trades.merge(
    smma,
    left_on=[
        "symbol_clean",
        "entry_time",
    ],
    right_on=[
        "symbol_clean",
        "timestamp",
    ],
    how="left",
    suffixes=(
        "",
        "_smma"
    )
)


# ============================================================
# FALLBACK TIME MATCH
# ============================================================

# Exact timestamps may differ slightly.
# For unmatched trades, use the latest historical
# observation at or before the crossover time.

missing_feature_rows = (
    training["smma20"]
    .isna()
)


if missing_feature_rows.any():

    lookup = (
        smma[
            [
                "symbol_clean",
                "timestamp",
                "close",
                "smma20",
                "smma120",
                "smma_diff",
                "smma_diff_pct",
                "return_1",
                "return_5",
            ]
        ]
        .sort_values(
            [
                "symbol_clean",
                "timestamp",
            ]
        )
    )

    unmatched = (
        training.loc[
            missing_feature_rows,
            [
                "symbol_clean",
                "entry_time",
            ]
        ]
        .copy()
    )

    unmatched["_original_index"] = (
        unmatched.index
    )

    unmatched = unmatched.sort_values(
        [
            "symbol_clean",
            "entry_time",
        ]
    )

    matched = pd.merge_asof(
        unmatched,
        lookup,
        left_on="entry_time",
        right_on="timestamp",
        by="symbol_clean",
        direction="backward"
    )

    matched = matched.set_index(
        "_original_index"
    )

    for column in [
        "close",
        "smma20",
        "smma120",
        "smma_diff",
        "smma_diff_pct",
        "return_1",
        "return_5",
    ]:

        if column in matched.columns:

            training.loc[
                matched.index,
                column
            ] = matched[column]


# ============================================================
# MERGE OHLCV FEATURES
# ============================================================

training = training.merge(
    ohlcv_features,
    left_on=[
        "symbol_clean",
        "entry_time",
    ],
    right_on=[
        "symbol_clean",
        "timestamp",
    ],
    how="left",
    suffixes=(
        "",
        "_ohlcv"
    )
)


# ============================================================
# FALLBACK OHLCV TIME MATCH
# ============================================================

if (
    training["range_pct"]
    .isna()
    .any()
):

    lookup = (
        ohlcv_features
        .sort_values(
            [
                "symbol_clean",
                "timestamp",
            ]
        )
    )

    unmatched = (
        training.loc[
            training["range_pct"].isna(),
            [
                "symbol_clean",
                "entry_time",
            ]
        ]
        .copy()
    )

    unmatched["_original_index"] = (
        unmatched.index
    )

    unmatched = unmatched.sort_values(
        [
            "symbol_clean",
            "entry_time",
        ]
    )

    matched = pd.merge_asof(
        unmatched,
        lookup,
        left_on="entry_time",
        right_on="timestamp",
        by="symbol_clean",
        direction="backward"
    )

    matched = matched.set_index(
        "_original_index"
    )

    for column in [
        "range_pct",
        "body_pct",
        "return_1",
        "return_5",
        "volume_change_pct",
        "volume_ratio",
    ]:

        if column in matched.columns:

            training.loc[
                matched.index,
                column
            ] = matched[column]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

training["direction"] = (
    training["trade_type"]
    .map({
        "BUY": 1,
        "SELL": -1,
    })
    .fillna(0)
)


# Direction-adjusted momentum.
training["directional_return"] = (
    training["return_5"]
    *
    training["direction"]
)


# ============================================================
# TARGET
# ============================================================

training["target"] = (
    pd.to_numeric(
        training["profitable"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

training = training.sort_values(
    "entry_time"
).reset_index(drop=True)


# ============================================================
# FEATURE LIST
# ============================================================

FEATURES = [
    "entry_price",
    "smma20",
    "smma120",
    "smma_diff",
    "smma_diff_pct",
    "return_1",
    "return_5",
    "range_pct",
    "body_pct",
    "volume_change_pct",
    "volume_ratio",
    "direction",
    "directional_return",
]


# ============================================================
# CHECK FEATURE AVAILABILITY
# ============================================================

available_features = [
    feature
    for feature in FEATURES
    if feature in training.columns
]


if len(available_features) < 5:

    raise RuntimeError(
        "Not enough ML features available."
    )


# ============================================================
# CLEAN TRAINING DATA
# ============================================================

model_data = training[
    available_features
    +
    [
        "target",
    ]
].copy()


model_data = model_data.replace(
    [
        np.inf,
        -np.inf,
    ],
    np.nan
)


# Remove rows where the target is missing.
model_data = model_data.dropna(
    subset=[
        "target",
    ]
)


# ============================================================
# SAVE TRAINING DATA
# ============================================================

TRAINING_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

training.to_csv(
    TRAINING_FILE,
    index=False
)


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

class_counts = (
    model_data["target"]
    .value_counts()
    .sort_index()
)


print()
print("=" * 80)
print("ML TRAINING DATA")
print("=" * 80)

print()
print("Training rows:", len(model_data))

print(
    "Profitable:",
    int(class_counts.get(1, 0))
)

print(
    "Losing:",
    int(class_counts.get(0, 0))
)

print()
print("Features:")
for feature in available_features:
    print(" -", feature)


# ============================================================
# CHRONOLOGICAL TRAIN / TEST SPLIT
# ============================================================

model_data = model_data.sort_index()

split_index = int(
    len(model_data)
    *
    (1 - TEST_SIZE)
)

train_data = model_data.iloc[
    :split_index
].copy()

test_data = model_data.iloc[
    split_index:
].copy()


X_train = train_data[
    available_features
]

y_train = train_data[
    "target"
]

X_test = test_data[
    available_features
]

y_test = test_data[
    "target"
]


# ============================================================
# IMPUTATION
# ============================================================

imputer = SimpleImputer(
    strategy="median"
)

X_train_imp = (
    imputer.fit_transform(
        X_train
    )
)

X_test_imp = (
    imputer.transform(
        X_test
    )
)


# ============================================================
# MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=6,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1,
)


print()
print("Training Random Forest...")


model.fit(
    X_train_imp,
    y_train
)


# ============================================================
# PREDICTION
# ============================================================

y_pred = model.predict(
    X_test_imp
)

y_probability = (
    model.predict_proba(
        X_test_imp
    )[:, 1]
)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)


try:

    roc_auc = roc_auc_score(
        y_test,
        y_probability
    )

except ValueError:

    roc_auc = float("nan")


cm = confusion_matrix(
    y_test,
    y_pred
)


# ============================================================
# ACCEPT / AVOID ANALYSIS
# ============================================================

test_results = test_data.copy()

test_results["predicted_probability"] = (
    y_probability
)

test_results["predicted_class"] = (
    y_pred
)

test_results["decision"] = np.where(
    y_probability >= ACCEPT_THRESHOLD,
    "ACCEPT",
    "AVOID"
)


accepted = (
    test_results[
        test_results["decision"] == "ACCEPT"
    ]
)

avoided = (
    test_results[
        test_results["decision"] == "AVOID"
    ]
)


accepted_win_rate = (
    accepted["target"].mean() * 100
    if not accepted.empty
    else 0
)

avoided_win_rate = (
    avoided["target"].mean() * 100
    if not avoided.empty
    else 0
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "Feature": available_features,
    "Importance": model.feature_importances_,
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


artifact = {
    "model": model,
    "imputer": imputer,
    "features": available_features,
    "accept_threshold": ACCEPT_THRESHOLD,
}


joblib.dump(
    artifact,
    MODEL_FILE
)


# ============================================================
# SAVE TEST RESULTS
# ============================================================

test_output = (
    ROOT
    / "dataset"
    / "ml_test_predictions.csv"
)

test_results.to_csv(
    test_output,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 80)
print("ML MODEL RESULTS")
print("=" * 80)

print()
print(
    f"Training rows : {len(train_data)}"
)

print(
    f"Testing rows  : {len(test_data)}"
)

print()
print(
    f"Accuracy      : {accuracy * 100:.2f}%"
)

print(
    f"Precision     : {precision * 100:.2f}%"
)

print(
    f"Recall        : {recall * 100:.2f}%"
)

print(
    f"F1 Score      : {f1 * 100:.2f}%"
)

if not np.isnan(roc_auc):

    print(
        f"ROC-AUC       : {roc_auc:.4f}"
    )

print()
print("Confusion Matrix:")
print(cm)

print()
print("Classification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


print()
print("=" * 80)
print("ACCEPT / AVOID ANALYSIS")
print("=" * 80)

print()
print(
    f"Accepted trades : {len(accepted)}"
)

print(
    f"Accepted win %  : {accepted_win_rate:.2f}%"
)

print()
print(
    f"Avoided trades  : {len(avoided)}"
)

print(
    f"Avoided win %   : {avoided_win_rate:.2f}%"
)


print()
print("=" * 80)
print("TOP ML FEATURES")
print("=" * 80)

print(
    importance
    .head(10)
    .to_string(index=False)
)


print()
print("=" * 80)
print("FILES CREATED")
print("=" * 80)

print()
print("Training data:")
print(TRAINING_FILE)

print()
print("ML model:")
print(MODEL_FILE)

print()
print("Test predictions:")
print(test_output)

print()
print("=" * 80)
print("ML TRAINING COMPLETE")
print("=" * 80)