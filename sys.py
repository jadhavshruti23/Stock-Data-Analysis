import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

# Put your stock dataset in the same folder as this script.
# The program will automatically find the first CSV or Excel file.
DATA_FOLDER = Path(".")


# ============================================================
# 1. FIND STOCK DATASET
# ============================================================

def find_dataset(folder):

    supported_files = list(folder.glob("*.csv")) + \
                      list(folder.glob("*.xlsx")) + \
                      list(folder.glob("*.xls"))

    if not supported_files:
        raise FileNotFoundError(
            "No CSV or Excel stock dataset was found."
        )

    if len(supported_files) > 1:
        print("\nMultiple datasets found:")
        for i, file in enumerate(supported_files, start=1):
            print(f"{i}. {file.name}")

        choice = int(
            input("\nSelect dataset number: ")
        ) - 1

        return supported_files[choice]

    return supported_files[0]


# ============================================================
# 2. LOAD DATASET
# ============================================================

def load_dataset(file_path):

    print("\nLoading dataset:")
    print(file_path.name)

    if file_path.suffix.lower() == ".csv":
        data = pd.read_csv(file_path)

    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        data = pd.read_excel(file_path)

    else:
        raise ValueError(
            "Unsupported file format."
        )

    return data


# ============================================================
# 3. STANDARDIZE COLUMN NAMES
# ============================================================

def standardize_column_names(data):

    data.columns = (
        data.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return data


# ============================================================
# 4. DETECT STOCK COLUMNS
# ============================================================

COLUMN_ALIASES = {

    "date": [
        "date",
        "datetime",
        "timestamp",
        "time"
    ],

    "open": [
        "open",
        "opening_price",
        "open_price"
    ],

    "high": [
        "high",
        "highest_price",
        "high_price"
    ],

    "low": [
        "low",
        "lowest_price",
        "low_price"
    ],

    "close": [
        "close",
        "closing_price",
        "close_price",
        "adj_close",
        "adjusted_close",
        "adjusted_closing_price"
    ],

    "volume": [
        "volume",
        "trading_volume",
        "trade_volume"
    ]
}


def detect_columns(data):

    detected = {}

    for standard_name, aliases in COLUMN_ALIASES.items():

        detected[standard_name] = None

        for column in data.columns:

            if column in aliases:
                detected[standard_name] = column
                break

    return detected


# ============================================================
# 5. STANDARDIZE DETECTED COLUMNS
# ============================================================

def rename_detected_columns(data, detected):

    rename_mapping = {}

    for standard_name, actual_name in detected.items():

        if actual_name is not None:
            rename_mapping[actual_name] = standard_name

    data = data.rename(
        columns=rename_mapping
    )

    return data


# ============================================================
# 6. VALIDATE REQUIRED DATA
# ============================================================

def validate_dataset(data):

    required_columns = [
        "date",
        "close"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            "\nThis does not appear to be a valid stock dataset.\n"
            f"Missing required columns: {missing_columns}\n"
            "At minimum, the dataset must contain Date and Close."
        )


# ============================================================
# 7. CLEAN DATA
# ============================================================

def clean_dataset(data):

    data = data.copy()

    # Convert date
    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    # Convert available numeric stock columns
    numeric_columns = [
        column
        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
        if column in data.columns
    ]

    for column in numeric_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Remove rows without date or close
    data = data.dropna(
        subset=["date", "close"]
    )

    # Remove completely duplicated rows
    data = data.drop_duplicates()

    # Sort chronologically
    data = (
        data
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Remove invalid closing prices
    data = data[
        data["close"] > 0
    ]

    # Handle optional numeric columns
    optional_columns = [
        column
        for column in [
            "open",
            "high",
            "low",
            "volume"
        ]
        if column in data.columns
    ]

    for column in optional_columns:

        data[column] = data[column].interpolate(
            method="linear"
        )

    # Remove remaining missing values
    data = data.dropna()

    return data


# ============================================================
# 8. STOCK DATA VALIDATION
# ============================================================

def validate_stock_data(data):

    print("\n========== DATA VALIDATION ==========")

    print("\nDataset Shape:")
    print(data.shape)

    print("\nAvailable Columns:")
    print(data.columns.tolist())

    print("\nDate Range:")
    print(
        data["date"].min(),
        "to",
        data["date"].max()
    )

    print("\nMissing Values:")
    print(data.isnull().sum())

    print("\nDuplicate Rows:")
    print(data.duplicated().sum())

    print("\nDuplicate Dates:")
    print(data["date"].duplicated().sum())

    # OHLC validation only if all columns exist
    ohlc_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    if all(
        column in data.columns
        for column in ohlc_columns
    ):

        print("\nOHLC Validation:")

        print(
            "High < Low:",
            (data["high"] < data["low"]).sum()
        )

        print(
            "High < Open:",
            (data["high"] < data["open"]).sum()
        )

        print(
            "High < Close:",
            (data["high"] < data["close"]).sum()
        )

        print(
            "Low > Open:",
            (data["low"] > data["open"]).sum()
        )

        print(
            "Low > Close:",
            (data["low"] > data["close"]).sum()
        )

    # Volume validation only if available
    if "volume" in data.columns:

        print("\nVolume Validation:")

        print(
            "Negative Volume:",
            (data["volume"] < 0).sum()
        )

    print("\n=====================================")


# ============================================================
# 9. MAIN PROGRAM
# ============================================================

try:

    # Find dataset
    dataset_path = find_dataset(
        DATA_FOLDER
    )

    # Load dataset
    df = load_dataset(
        dataset_path
    )

    print("\nOriginal Shape:")
    print(df.shape)

    # Standardize column names
    df = standardize_column_names(
        df
    )

    # Detect columns
    detected_columns = detect_columns(
        df
    )

    print("\nDetected Columns:")

    for standard, actual in detected_columns.items():

        print(
            f"{standard}: {actual}"
        )

    # Rename columns
    df = rename_detected_columns(
        df,
        detected_columns
    )

    # Validate
    validate_dataset(
        df
    )

    # Clean
    df_clean = clean_dataset(
        df
    )

    # Validate cleaned data
    validate_stock_data(
        df_clean
    )

    print("\n========== CLEANING COMPLETE ==========")

    print(
        "\nCleaned Dataset Shape:",
        df_clean.shape
    )

    print("\nFirst 5 Rows:")
    print(
        df_clean.head()
    )

except Exception as error:

    print("\nERROR:")
    print(error)

# ============================================================
# STAGE 3.1 - RETURNS AND PRICE CHANGE
# ============================================================

# Work with the cleaned dataset
df_features = df_clean.copy()


# ------------------------------------------------------------
# Daily Price Change
# ------------------------------------------------------------

if "close" in df_features.columns:

    df_features["price_change"] = (
        df_features["close"].diff()
    )


# ------------------------------------------------------------
# Daily Return
# ------------------------------------------------------------

if "close" in df_features.columns:

    df_features["daily_return"] = (
        df_features["close"].pct_change()
    )


# ------------------------------------------------------------
# Percentage Return
# ------------------------------------------------------------

if "daily_return" in df_features.columns:

    df_features["daily_return_pct"] = (
        df_features["daily_return"] * 100
    )


# ------------------------------------------------------------
# Display Results
# ------------------------------------------------------------

print("\n========== FEATURE ENGINEERING ==========")

print("\nNew Columns:")

print(
    df_features.columns.tolist()
)

print("\nSample Feature Values:")

columns_to_show = [
    column
    for column in [
        "date",
        "close",
        "price_change",
        "daily_return",
        "daily_return_pct"
    ]
    if column in df_features.columns
]

print(
    df_features[columns_to_show].head(10)
)
# ============================================================
# STAGE 3.2 - MOVING AVERAGES
# ============================================================

if "close" in df_features.columns:

    data_size = len(df_features)

    # 20-period moving average
    if data_size >= 20:
        df_features["ma_20"] = (
            df_features["close"]
            .rolling(window=20)
            .mean()
        )

    # 50-period moving average
    if data_size >= 50:
        df_features["ma_50"] = (
            df_features["close"]
            .rolling(window=50)
            .mean()
        )

    # 200-period moving average
    if data_size >= 200:
        df_features["ma_200"] = (
            df_features["close"]
            .rolling(window=200)
            .mean()
        )


# ------------------------------------------------------------
# Display available moving averages
# ------------------------------------------------------------

moving_average_columns = [
    column
    for column in [
        "ma_20",
        "ma_50",
        "ma_200"
    ]
    if column in df_features.columns
]

print("\nMoving Average Features:")

print(moving_average_columns)

print("\nLatest Moving Average Values:")

if moving_average_columns:
    print(
        df_features[
            ["date", "close"] + moving_average_columns
        ].tail()
    )
# ============================================================
# STAGE 3.3 - VOLATILITY
# ============================================================

if "daily_return" in df_features.columns:

    data_size = len(df_features)

    # 20-period rolling volatility
    if data_size >= 20:

        df_features["volatility_20"] = (
            df_features["daily_return"]
            .rolling(window=20)
            .std()
        )

    # 50-period rolling volatility
    if data_size >= 50:

        df_features["volatility_50"] = (
            df_features["daily_return"]
            .rolling(window=50)
            .std()
        )


# ------------------------------------------------------------
# Display volatility features
# ------------------------------------------------------------

volatility_columns = [
    column
    for column in [
        "volatility_20",
        "volatility_50"
    ]
    if column in df_features.columns
]

print("\nVolatility Features:")
print(volatility_columns)

print("\nLatest Volatility Values:")

if volatility_columns:

    print(
        df_features[
            ["date", "daily_return"] + volatility_columns
        ].tail()
    )

# ============================================================
# STAGE 3.4 - DATE FEATURES
# ============================================================

if "date" in df_features.columns:

    # Calendar features
    df_features["year"] = df_features["date"].dt.year
    df_features["month"] = df_features["date"].dt.month
    df_features["quarter"] = df_features["date"].dt.quarter
    df_features["day_of_week"] = (
        df_features["date"].dt.dayofweek
    )

    # Day name
    df_features["day_name"] = (
        df_features["date"].dt.day_name()
    )

    # Month name
    df_features["month_name"] = (
        df_features["date"].dt.month_name()
    )


# ------------------------------------------------------------
# Display date features
# ------------------------------------------------------------

date_features = [
    column
    for column in [
        "date",
        "year",
        "month",
        "quarter",
        "day_of_week",
        "day_name",
        "month_name"
    ]
    if column in df_features.columns
]

print("\nDate Features:")

print(
    df_features[date_features].head(10)
)

# ============================================================
# STAGE 3.5 - OHLC & VOLUME FEATURES
# ============================================================

# ------------------------------------------------------------
# High-Low Price Range
# ------------------------------------------------------------

if all(
    column in df_features.columns
    for column in ["high", "low"]
):

    df_features["price_range"] = (
        df_features["high"] - df_features["low"]
    )


# ------------------------------------------------------------
# High-Low Range as Percentage of Close
# ------------------------------------------------------------

if all(
    column in df_features.columns
    for column in ["high", "low", "close"]
):

    df_features["price_range_pct"] = (
        (df_features["high"] - df_features["low"])
        / df_features["close"]
    ) * 100


# ------------------------------------------------------------
# Open-Close Price Change
# ------------------------------------------------------------

if all(
    column in df_features.columns
    for column in ["open", "close"]
):

    df_features["open_close_change"] = (
        df_features["close"] - df_features["open"]
    )


# ------------------------------------------------------------
# Open-Close Change Percentage
# ------------------------------------------------------------

if all(
    column in df_features.columns
    for column in ["open", "close"]
):

    df_features["open_close_change_pct"] = (
        (
            df_features["close"]
            - df_features["open"]
        )
        / df_features["open"]
    ) * 100


# ------------------------------------------------------------
# Volume Features
# ------------------------------------------------------------

if "volume" in df_features.columns:

    # Change in trading volume
    df_features["volume_change"] = (
        df_features["volume"].diff()
    )

    # Percentage change in volume
    df_features["volume_change_pct"] = (
        df_features["volume"].pct_change()
    )

    # 20-period volume moving average
    if len(df_features) >= 20:

        df_features["volume_ma_20"] = (
            df_features["volume"]
            .rolling(window=20)
            .mean()
        )


# ------------------------------------------------------------
# Display New Features
# ------------------------------------------------------------

new_features = [
    column
    for column in [
        "price_range",
        "price_range_pct",
        "open_close_change",
        "open_close_change_pct",
        "volume_change",
        "volume_change_pct",
        "volume_ma_20"
    ]
    if column in df_features.columns
]

print("\nOHLC & Volume Features:")
print(new_features)

print("\nLatest Feature Values:")

print(
    df_features[
        ["date"] + new_features
    ].tail()
)
# ============================================================
# STAGE 4.1 - STOCK PRICE TREND
# ============================================================

import matplotlib.pyplot as plt


if "date" in df_features.columns and "close" in df_features.columns:

    plt.figure(figsize=(12, 6))

    plt.plot(
        df_features["date"],
        df_features["close"]
    )

    plt.title("Stock Closing Price Over Time")
    plt.xlabel("Date")
    plt.ylabel("Closing Price")

    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 4.2 - DAILY RETURN DISTRIBUTION
# ============================================================

if "daily_return_pct" in df_features.columns:

    return_data = df_features[
        "daily_return_pct"
    ].dropna()

    plt.figure(figsize=(12, 6))

    plt.hist(
        return_data,
        bins=50
    )

    plt.title("Distribution of Stock Returns")
    plt.xlabel("Daily Return (%)")
    plt.ylabel("Frequency")

    plt.axvline(
        return_data.mean(),
        linestyle="--",
        label="Mean Return"
    )

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 4.3 - MOVING AVERAGE TREND ANALYSIS
# ============================================================

if "date" in df_features.columns and "close" in df_features.columns:

    plt.figure(figsize=(14, 7))

    # Closing price
    plt.plot(
        df_features["date"],
        df_features["close"],
        label="Closing Price"
    )

    # Add moving averages only if available
    if "ma_20" in df_features.columns:
        plt.plot(
            df_features["date"],
            df_features["ma_20"],
            label="20-Period MA"
        )

    if "ma_50" in df_features.columns:
        plt.plot(
            df_features["date"],
            df_features["ma_50"],
            label="50-Period MA"
        )

    if "ma_200" in df_features.columns:
        plt.plot(
            df_features["date"],
            df_features["ma_200"],
            label="200-Period MA"
        )

    plt.title("Stock Price and Moving Averages")
    plt.xlabel("Date")
    plt.ylabel("Price")

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 4.4 - VOLATILITY OVER TIME
# ============================================================

if "date" in df_features.columns:

    volatility_columns = [
        column
        for column in [
            "volatility_20",
            "volatility_50"
        ]
        if column in df_features.columns
    ]

    if volatility_columns:

        plt.figure(figsize=(14, 6))

        for column in volatility_columns:

            plt.plot(
                df_features["date"],
                df_features[column],
                label=column.replace("_", " ").title()
            )

        plt.title("Stock Volatility Over Time")
        plt.xlabel("Date")
        plt.ylabel("Volatility")

        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.show()

# ============================================================
# STAGE 4.5 - TRADING VOLUME ANALYSIS
# ============================================================

if "date" in df_features.columns and "volume" in df_features.columns:

    plt.figure(figsize=(14, 6))

    # Convert volume to millions for readability
    volume_millions = df_features["volume"] / 1_000_000

    plt.plot(
        df_features["date"],
        volume_millions,
        label="Trading Volume"
    )

    if "volume_ma_20" in df_features.columns:

        volume_ma_millions = (
            df_features["volume_ma_20"] / 1_000_000
        )

        plt.plot(
            df_features["date"],
            volume_ma_millions,
            label="20-Period Volume MA"
        )

    plt.title("Trading Volume Over Time")
    plt.xlabel("Date")
    plt.ylabel("Trading Volume (Millions)")

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 4.6 - ANNUAL PERFORMANCE ANALYSIS
# ============================================================

if "date" in df_features.columns and "close" in df_features.columns:

    # Make sure year exists
    if "year" not in df_features.columns:
        df_features["year"] = df_features["date"].dt.year

    # Get first and last closing price for each year
    yearly_prices = (
        df_features
        .groupby("year")["close"]
        .agg(["first", "last"])
        .reset_index()
    )

    # Calculate annual return
    yearly_prices["annual_return_pct"] = (
        (yearly_prices["last"] - yearly_prices["first"])
        / yearly_prices["first"]
    ) * 100

    print("\n========== ANNUAL PERFORMANCE ==========")

    print(
        yearly_prices[
            ["year", "annual_return_pct"]
        ].tail(10)
    )

    # --------------------------------------------------------
    # Annual Return Chart
    # --------------------------------------------------------

    plt.figure(figsize=(14, 6))

    plt.bar(
        yearly_prices["year"],
        yearly_prices["annual_return_pct"]
    )

    plt.axhline(
        0,
        linestyle="--"
    )

    plt.title("Annual Stock Performance")
    plt.xlabel("Year")
    plt.ylabel("Annual Return (%)")

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 4.7 - DRAWDOWN ANALYSIS
# ============================================================

if "close" in df_features.columns:

    # Calculate running highest closing price
    df_features["running_peak"] = (
        df_features["close"]
        .cummax()
    )

    # Calculate drawdown percentage
    df_features["drawdown_pct"] = (
        (
            df_features["close"]
            - df_features["running_peak"]
        )
        / df_features["running_peak"]
    ) * 100

    # --------------------------------------------------------
    # Display drawdown information
    # --------------------------------------------------------

    print("\n========== DRAWDOWN ANALYSIS ==========")

    print("\nMaximum Drawdown:")

    print(
        f"{df_features['drawdown_pct'].min():.2f}%"
    )

    print("\nLatest Drawdown:")

    print(
        f"{df_features['drawdown_pct'].iloc[-1]:.2f}%"
    )

    # --------------------------------------------------------
    # Drawdown Chart
    # --------------------------------------------------------

    plt.figure(figsize=(14, 6))

    plt.plot(
        df_features["date"],
        df_features["drawdown_pct"]
    )

    plt.axhline(
        0,
        linestyle="--"
    )

    plt.title("Stock Drawdown Over Time")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")

    plt.grid(True)
    plt.tight_layout()

    plt.show()

# ============================================================
# STAGE 5.1 - TIME SERIES PREPARATION
# ============================================================

print("\n========== TIME SERIES PREPARATION ==========")

# Select only the columns needed for forecasting
forecast_data = df_features[
    ["date", "close"]
].copy()

# Remove rows where the forecasting target is missing
forecast_data = forecast_data.dropna(
    subset=["close"]
)

# Sort chronologically
forecast_data = (
    forecast_data
    .sort_values("date")
    .reset_index(drop=True)
)

print("\nForecast Dataset Shape:")
print(forecast_data.shape)

print("\nForecast Date Range:")
print(
    forecast_data["date"].min(),
    "to",
    forecast_data["date"].max()
)

print("\nMissing Values:")
print(forecast_data.isnull().sum())

print("\nFirst 5 Rows:")
print(forecast_data.head())

print("\nLast 5 Rows:")
print(forecast_data.tail())

# ============================================================
# STAGE 5.2 - STATIONARITY TEST
# ============================================================

from statsmodels.tsa.stattools import adfuller

print("\n========== STATIONARITY TEST ==========")

# Extract closing price
price_series = forecast_data["close"].dropna()

# Perform Augmented Dickey-Fuller test
adf_result = adfuller(price_series)

adf_statistic = adf_result[0]
p_value = adf_result[1]

print("\nADF Statistic:")
print(adf_statistic)

print("\nP-Value:")
print(p_value)

print("\nCritical Values:")

for key, value in adf_result[4].items():
    print(f"{key}: {value}")

# Interpretation
print("\nInterpretation:")

if p_value < 0.05:
    print("The series is likely stationary.")
else:
    print("The series is likely non-stationary.")

# ============================================================
# STAGE 5.3 - LOG RETURN TRANSFORMATION
# ============================================================

import numpy as np

print("\n========== LOG RETURN TRANSFORMATION ==========")

# Calculate log returns
forecast_data["log_return"] = np.log(
    forecast_data["close"]
    / forecast_data["close"].shift(1)
)

# Remove the first NaN created by the shift
log_return_data = forecast_data[
    ["date", "log_return"]
].dropna().copy()

print("\nLog Return Dataset Shape:")
print(log_return_data.shape)

print("\nMissing Values:")
print(log_return_data.isnull().sum())

print("\nFirst 5 Log Returns:")
print(log_return_data.head())

# ------------------------------------------------------------
# Test stationarity again
# ------------------------------------------------------------

adf_log = adfuller(
    log_return_data["log_return"]
)

print("\nADF Statistic:")
print(adf_log[0])

print("\nP-Value:")
print(adf_log[1])

print("\nInterpretation:")

if adf_log[1] < 0.05:
    print("Log return series is stationary.")
else:
    print("Log return series is still non-stationary.")

# ============================================================
# STAGE 5.4 - TRAIN / TEST SPLIT
# ============================================================

print("\n========== TRAIN / TEST SPLIT ==========")

# Use stationary log-return series
model_data = log_return_data.copy()

# Calculate split point automatically
split_index = int(
    len(model_data) * 0.80
)

# Chronological split
train_data = model_data.iloc[:split_index].copy()
test_data = model_data.iloc[split_index:].copy()

print("\nTotal Observations:")
print(len(model_data))

print("\nTraining Observations:")
print(len(train_data))

print("\nTesting Observations:")
print(len(test_data))

print("\nTraining Period:")
print(
    train_data["date"].min(),
    "to",
    train_data["date"].max()
)

print("\nTesting Period:")
print(
    test_data["date"].min(),
    "to",
    test_data["date"].max()
)

print("\nTraining/Test Ratio:")
print(
    f"{len(train_data) / len(model_data):.1%}"
    " / "
    f"{len(test_data) / len(model_data):.1%}"
)

# ============================================================
# STAGE 5.5 - ML FORECASTING FEATURE ENGINEERING
# ============================================================

print("\n========== ML FORECASTING FEATURES ==========")

# Start with the complete feature-engineered dataset
ml_data = df_features.copy()

# ------------------------------------------------------------
# Lagged Closing Prices
# ------------------------------------------------------------

ml_data["close_lag_1"] = ml_data["close"].shift(1)
ml_data["close_lag_2"] = ml_data["close"].shift(2)
ml_data["close_lag_5"] = ml_data["close"].shift(5)
ml_data["close_lag_10"] = ml_data["close"].shift(10)

# ------------------------------------------------------------
# Lagged Returns
# ------------------------------------------------------------

ml_data["return_lag_1"] = ml_data["daily_return"].shift(1)
ml_data["return_lag_5"] = ml_data["daily_return"].shift(5)

# ------------------------------------------------------------
# Lagged Volume
# ------------------------------------------------------------

if "volume" in ml_data.columns:
    ml_data["volume_lag_1"] = ml_data["volume"].shift(1)

# ------------------------------------------------------------
# Create Prediction Target
# ------------------------------------------------------------

# Next trading day's closing price
ml_data["target_close"] = ml_data["close"].shift(-1)

# ------------------------------------------------------------
# Select ML Features
# ------------------------------------------------------------

feature_columns = [
    "close_lag_1",
    "close_lag_2",
    "close_lag_5",
    "close_lag_10",
    "return_lag_1",
    "return_lag_5",
    "ma_20",
    "ma_50",
    "ma_200",
    "volatility_20",
    "volatility_50"
]

# Add volume-related features only when available
if "volume" in ml_data.columns:
    feature_columns.append("volume_lag_1")

if "volume_ma_20" in ml_data.columns:
    feature_columns.append("volume_ma_20")

# Keep only features that actually exist
feature_columns = [
    column
    for column in feature_columns
    if column in ml_data.columns
]

print("\nML Features:")
print(feature_columns)

# ------------------------------------------------------------
# Prepare ML Dataset
# ------------------------------------------------------------

ml_model_data = ml_data[
    ["date", "close", "target_close"] + feature_columns
].copy()

# Remove rows where features or target are unavailable
ml_model_data = ml_model_data.dropna().reset_index(drop=True)

print("\nML Dataset Shape:")
print(ml_model_data.shape)

print("\nTarget:")
print("target_close = next trading day's closing price")

print("\nFirst 5 ML Rows:")
print(ml_model_data.head())

print("\nMissing Values:")
print(ml_model_data.isnull().sum())

print("\n==============================================")
# ============================================================
# STAGE 5.6 - CHRONOLOGICAL TRAIN / TEST SPLIT
# ============================================================

print("\n========== TRAIN / TEST SPLIT ==========")

# ------------------------------------------------------------
# Split ML data chronologically
# ------------------------------------------------------------

split_index = int(len(ml_model_data) * 0.80)

train_ml = ml_model_data.iloc[:split_index].copy()
test_ml = ml_model_data.iloc[split_index:].copy()

# ------------------------------------------------------------
# Create X and y
# ------------------------------------------------------------

X_train = train_ml[feature_columns]
y_train = train_ml["target_close"]

X_test = test_ml[feature_columns]
y_test = test_ml["target_close"]

# ------------------------------------------------------------
# Display split information
# ------------------------------------------------------------

print("\nTotal ML Rows:", len(ml_model_data))

print("\nTraining Rows:", len(train_ml))
print("Testing Rows:", len(test_ml))

print("\nTraining Period:")
print(train_ml["date"].min(), "to", train_ml["date"].max())

print("\nTesting Period:")
print(test_ml["date"].min(), "to", test_ml["date"].max())

print("\nTraining Features Shape:")
print(X_train.shape)

print("\nTesting Features Shape:")
print(X_test.shape)

print("\nTraining Target Shape:")
print(y_train.shape)

print("\nTesting Target Shape:")
print(y_test.shape)

print("\n========================================")

# ============================================================
# STAGE 5.7 - RANDOM FOREST REGRESSION
# ============================================================

from sklearn.ensemble import RandomForestRegressor

print("\n========== RANDOM FOREST MODEL ==========")

# Create Random Forest model
rf_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

# Train the model
rf_model.fit(X_train, y_train)

print("\nRandom Forest model training completed.")

print("\nNumber of Trees:")
print(rf_model.n_estimators)

print("\nTraining Samples:")
print(len(X_train))

print("\nTesting Samples:")
print(len(X_test))

print("\n==========================================")

# ============================================================
# STAGE 5.8 - RANDOM FOREST PREDICTIONS & EVALUATION
# ============================================================

from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

print("\n========== RANDOM FOREST EVALUATION ==========")

# Generate predictions on unseen test data
y_pred = rf_model.predict(X_test)

# ------------------------------------------------------------
# Calculate evaluation metrics
# ------------------------------------------------------------

mae = mean_absolute_error(y_test, y_pred)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("\nModel Evaluation Results:")

print("\nMAE:")
print(mae)

print("\nRMSE:")
print(rmse)

# ------------------------------------------------------------
# Compare actual vs predicted values
# ------------------------------------------------------------

results = test_ml[["date", "close", "target_close"]].copy()

results["predicted_close"] = y_pred

print("\nFirst 10 Predictions:")
print(results.head(10))

print("\nResults Shape:")
print(results.shape)

print("\n============================================")

# ============================================================
# STAGE 5.9 - RETURN-BASED ML FORECASTING
# ============================================================

print("\n========== RETURN-BASED ML FORECASTING ==========")

# Start from the ML dataset
return_ml_data = ml_data.copy()

# ------------------------------------------------------------
# Create next-day return target
# ------------------------------------------------------------

return_ml_data["target_return"] = (
    return_ml_data["close"].shift(-1) / return_ml_data["close"]
) - 1

# ------------------------------------------------------------
# Prepare ML data
# ------------------------------------------------------------

return_model_data = return_ml_data[
    ["date", "close", "target_return"] + feature_columns
].copy()

return_model_data = (
    return_model_data
    .replace([np.inf, -np.inf], np.nan)
    .dropna()
    .reset_index(drop=True)
)

print("\nReturn ML Dataset Shape:")
print(return_model_data.shape)

# ------------------------------------------------------------
# Chronological 80/20 split
# ------------------------------------------------------------

split_index = int(len(return_model_data) * 0.80)

train_return = return_model_data.iloc[:split_index].copy()
test_return = return_model_data.iloc[split_index:].copy()

X_train_return = train_return[feature_columns]
y_train_return = train_return["target_return"]

X_test_return = test_return[feature_columns]
y_test_return = test_return["target_return"]

print("\nTraining Rows:", len(train_return))
print("Testing Rows:", len(test_return))

print("\nTraining Period:")
print(
    train_return["date"].min(),
    "to",
    train_return["date"].max()
)

print("\nTesting Period:")
print(
    test_return["date"].min(),
    "to",
    test_return["date"].max()
)

print("\nFeature Shape:")
print(X_train_return.shape)

print("\n==============================================")
# ============================================================
# STAGE 5.10 - RETURN-BASED RANDOM FOREST
# ============================================================

print("\n========== RETURN-BASED RANDOM FOREST ==========")

# Create model
rf_return_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

# Train model
rf_return_model.fit(
    X_train_return,
    y_train_return
)

print("\nReturn-based Random Forest training completed.")

print("\nNumber of Trees:")
print(rf_return_model.n_estimators)

print("\nTraining Samples:")
print(len(X_train_return))

print("\nTesting Samples:")
print(len(X_test_return))

print("\n==============================================")
# ============================================================
# STAGE 5.11 - RETURN PREDICTIONS & PRICE EVALUATION
# ============================================================

print("\n========== RETURN MODEL EVALUATION ==========")

# ------------------------------------------------------------
# Predict next-day returns
# ------------------------------------------------------------

predicted_returns = rf_return_model.predict(X_test_return)

# ------------------------------------------------------------
# Convert predicted returns into predicted prices
# ------------------------------------------------------------

predicted_prices = (
    test_return["close"].values * (1 + predicted_returns)
)

actual_prices = test_return["target_return"].copy()

# Actual next-day closing prices
actual_next_prices = (
    test_return["close"].values *
    (1 + test_return["target_return"].values)
)

# ------------------------------------------------------------
# Calculate price prediction errors
# ------------------------------------------------------------

mae_return_model = mean_absolute_error(
    actual_next_prices,
    predicted_prices
)

rmse_return_model = np.sqrt(
    mean_squared_error(
        actual_next_prices,
        predicted_prices
    )
)

# ------------------------------------------------------------
# MAPE
# ------------------------------------------------------------

mape_return_model = (
    np.mean(
        np.abs(
            (actual_next_prices - predicted_prices)
            / actual_next_prices
        )
    ) * 100
)

# ------------------------------------------------------------
# Display metrics
# ------------------------------------------------------------

print("\nReturn-Based Random Forest Results:")

print("\nMAE:")
print(mae_return_model)

print("\nRMSE:")
print(rmse_return_model)

print("\nMAPE:")
print(mape_return_model, "%")

# ------------------------------------------------------------
# Create results dataframe
# ------------------------------------------------------------

return_results = test_return[
    ["date", "close"]
].copy()

return_results["actual_next_close"] = actual_next_prices
return_results["predicted_return"] = predicted_returns
return_results["predicted_next_close"] = predicted_prices

print("\nFirst 10 Predictions:")
print(return_results.head(10))

print("\nResults Shape:")
print(return_results.shape)

print("\n============================================")

# ============================================================
# STAGE 5.12 - NAIVE FORECAST BASELINE
# ============================================================

print("\n========== NAIVE FORECAST BASELINE ==========")

# ------------------------------------------------------------
# Naive prediction
# ------------------------------------------------------------

# Assume tomorrow's closing price will be today's closing price
naive_predictions = test_return["close"].values

# Actual next-day prices
naive_actual_prices = test_return["target_return"].copy()

naive_actual_prices = (
    test_return["close"].values *
    (1 + test_return["target_return"].values)
)

# ------------------------------------------------------------
# Calculate evaluation metrics
# ------------------------------------------------------------

naive_mae = mean_absolute_error(
    naive_actual_prices,
    naive_predictions
)

naive_rmse = np.sqrt(
    mean_squared_error(
        naive_actual_prices,
        naive_predictions
    )
)

naive_mape = (
    np.mean(
        np.abs(
            (naive_actual_prices - naive_predictions)
            / naive_actual_prices
        )
    ) * 100
)

# ------------------------------------------------------------
# Display results
# ------------------------------------------------------------

print("\nNaive Baseline Results:")

print("\nMAE:")
print(naive_mae)

print("\nRMSE:")
print(naive_rmse)

print("\nMAPE:")
print(naive_mape, "%")

print("\n============================================")

# ============================================================
# STAGE 5.13 - GRADIENT BOOSTING REGRESSION
# ============================================================

from sklearn.ensemble import GradientBoostingRegressor

print("\n========== GRADIENT BOOSTING MODEL ==========")

# Create Gradient Boosting model
gb_return_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.05,
    max_depth=3,
    random_state=42
)

# Train model
gb_return_model.fit(
    X_train_return,
    y_train_return
)

print("\nGradient Boosting model training completed.")

print("\nNumber of Trees:")
print(gb_return_model.n_estimators)

print("\nLearning Rate:")
print(gb_return_model.learning_rate)

print("\nMax Depth:")
print(gb_return_model.max_depth)

print("\nTraining Samples:")
print(len(X_train_return))

print("\nTesting Samples:")
print(len(X_test_return))

print("\n============================================")

# ============================================================
# STAGE 5.14 - GRADIENT BOOSTING EVALUATION
# ============================================================

print("\n========== GRADIENT BOOSTING EVALUATION ==========")

# ------------------------------------------------------------
# Predict next-day returns
# ------------------------------------------------------------

gb_predicted_returns = gb_return_model.predict(X_test_return)

# ------------------------------------------------------------
# Convert predicted returns to prices
# ------------------------------------------------------------

gb_predicted_prices = (
    test_return["close"].values *
    (1 + gb_predicted_returns)
)

# Actual next-day prices
gb_actual_prices = (
    test_return["close"].values *
    (1 + test_return["target_return"].values)
)

# ------------------------------------------------------------
# Calculate evaluation metrics
# ------------------------------------------------------------

gb_mae = mean_absolute_error(
    gb_actual_prices,
    gb_predicted_prices
)

gb_rmse = np.sqrt(
    mean_squared_error(
        gb_actual_prices,
        gb_predicted_prices
    )
)

gb_mape = (
    np.mean(
        np.abs(
            (gb_actual_prices - gb_predicted_prices)
            / gb_actual_prices
        )
    ) * 100
)

# ------------------------------------------------------------
# Display results
# ------------------------------------------------------------

print("\nGradient Boosting Results:")

print("\nMAE:")
print(gb_mae)

print("\nRMSE:")
print(gb_rmse)

print("\nMAPE:")
print(gb_mape, "%")

# ------------------------------------------------------------
# Create results dataframe
# ------------------------------------------------------------

gb_results = test_return[
    ["date", "close"]
].copy()

gb_results["actual_next_close"] = gb_actual_prices
gb_results["predicted_return"] = gb_predicted_returns
gb_results["predicted_next_close"] = gb_predicted_prices

print("\nFirst 10 Predictions:")
print(gb_results.head(10))

print("\nResults Shape:")
print(gb_results.shape)

print("\n==============================================")

# ============================================================
# STAGE 5.15 - FINAL MODEL COMPARISON
# ============================================================

print("\n========== FINAL MODEL COMPARISON ==========")

model_comparison = pd.DataFrame({
    "Model": [
        "Random Forest - Direct Price",
        "Random Forest - Return Based",
        "Naive Baseline",
        "Gradient Boosting - Return Based"
    ],
    "MAE": [
        mae,
        mae_return_model,
        naive_mae,
        gb_mae
    ],
    "RMSE": [
        rmse,
        rmse_return_model,
        naive_rmse,
        gb_rmse
    ],
    "MAPE (%)": [
        np.nan,
        mape_return_model,
        naive_mape,
        gb_mape
    ]
})

# Sort by MAPE where available
model_comparison = model_comparison.sort_values(
    by="MAPE (%)",
    na_position="last"
).reset_index(drop=True)

print("\nModel Performance:")
print(model_comparison.to_string(index=False))

print("\n============================================")

# ============================================================
# STAGE 5.16 - ACTUAL VS PREDICTED PRICE
# ============================================================

import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))

plt.plot(
    gb_results["date"],
    gb_results["actual_next_close"],
    label="Actual Price"
)

plt.plot(
    gb_results["date"],
    gb_results["predicted_next_close"],
    label="Gradient Boosting Prediction"
)

plt.title("Actual vs Predicted Stock Price - Gradient Boosting")
plt.xlabel("Date")
plt.ylabel("Stock Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ============================================================
# STAGE 5.17 - BUSINESS-FRIENDLY FEATURE IMPORTANCE
# ============================================================

# Step 1: Calculate feature importance from the trained model
feature_importance = pd.DataFrame({
    "Feature": feature_columns,
    "Importance": gb_return_model.feature_importances_
})

# Step 2: Sort features from most important to least important
feature_importance = feature_importance.sort_values(
    by="Importance",
    ascending=False
).reset_index(drop=True)

# Step 3: Convert technical names into business-friendly names
feature_names = {
    "return_lag_5": "Return 5 Days Ago",
    "return_lag_1": "Return 1 Day Ago",
    "volume_lag_1": "Trading Volume 1 Day Ago",
    "volume_ma_20": "20-Day Average Volume",
    "close_lag_1": "Closing Price 1 Day Ago",
    "ma_50": "50-Day Moving Average",
    "volatility_50": "50-Day Volatility",
    "volatility_20": "20-Day Volatility",
    "ma_200": "200-Day Moving Average",
    "close_lag_10": "Closing Price 10 Days Ago",
    "close_lag_2": "Closing Price 2 Days Ago",
    "close_lag_5": "Closing Price 5 Days Ago",
    "ma_20": "20-Day Moving Average"
}

feature_importance["Feature Name"] = (
    feature_importance["Feature"]
    .map(feature_names)
    .fillna(feature_importance["Feature"])
)

# Step 4: Display importance values
print("\n========== FEATURE IMPORTANCE ==========")
print(
    feature_importance[
        ["Feature Name", "Importance"]
    ].to_string(index=False)
)
print("\n========================================")

# Step 5: Create chart
plt.figure(figsize=(11, 7))

plt.barh(
    feature_importance["Feature Name"],
    feature_importance["Importance"]
)

plt.xlabel("Importance")
plt.ylabel("Historical Stock Feature")
plt.title("What Factors Influence the Model's Prediction?")

plt.gca().invert_yaxis()

plt.tight_layout()
plt.show()

# ============================================================
# STAGE 5.18 - FINAL FORECASTING OUTPUT
# ============================================================

forecast_output = test_return[
    ["date", "close"]
].copy()

# Actual next-day price
forecast_output["actual_next_close"] = (
    test_return["close"].values *
    (1 + test_return["target_return"].values)
)

# Naive prediction
forecast_output["naive_prediction"] = (
    test_return["close"].values
)

# Random Forest prediction
forecast_output["random_forest_prediction"] = (
    predicted_prices
)

# Gradient Boosting prediction
forecast_output["gradient_boosting_prediction"] = (
    gb_predicted_prices
)

# Gradient Boosting predicted return
forecast_output["gradient_boosting_return"] = (
    gb_predicted_returns
)

print("\n========== FORECAST OUTPUT ==========")
print("\nShape:")
print(forecast_output.shape)

print("\nColumns:")
print(forecast_output.columns.tolist())

print("\nFirst 5 Rows:")
print(forecast_output.head())

print("\n======================================")

# ============================================================
# STAGE 5.19 - SAVE PROJECT OUTPUTS
# ============================================================

from pathlib import Path

# Create output folders
output_folder = Path("outputs")
cleaned_folder = output_folder / "cleaned_data"
forecast_folder = output_folder / "forecasts"
charts_folder = output_folder / "charts"

cleaned_folder.mkdir(parents=True, exist_ok=True)
forecast_folder.mkdir(parents=True, exist_ok=True)
charts_folder.mkdir(parents=True, exist_ok=True)

# Save cleaned dataset
cleaned_file = cleaned_folder / "cleaned_stock_data.csv"
df_clean.to_csv(cleaned_file, index=False)

# Save feature-engineered dataset
features_file = cleaned_folder / "stock_features.csv"
df_features.to_csv(features_file, index=False)

# Save forecasting results
forecast_file = forecast_folder / "forecast_results.csv"
forecast_output.to_csv(forecast_file, index=False)

# Save model comparison
comparison_file = forecast_folder / "model_comparison.csv"
model_comparison.to_csv(comparison_file, index=False)

# Save feature importance
importance_file = forecast_folder / "feature_importance.csv"
feature_importance.to_csv(importance_file, index=False)

print("\n========== OUTPUT FILES SAVED ==========")

print("\nCleaned Data:")
print(cleaned_file)

print("\nFeature Data:")
print(features_file)

print("\nForecast Results:")
print(forecast_file)

print("\nModel Comparison:")
print(comparison_file)

print("\nFeature Importance:")
print(importance_file)

print("\n========================================")

# ============================================================
# STAGE 6.1 - CREATE POWER BI DATASET
# ============================================================

powerbi_data = df_features.copy()

# Save dashboard-ready dataset
powerbi_file = output_folder / "powerbi_stock_data.csv"

powerbi_data.to_csv(
    powerbi_file,
    index=False
)

print("\n========== POWER BI DATASET ==========")
print("File saved:")
print(powerbi_file)

print("\nShape:")
print(powerbi_data.shape)

print("\nColumns:")
print(powerbi_data.columns.tolist())

print("\n======================================")