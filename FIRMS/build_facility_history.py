from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "SIH26162_DATA"
    / "analysis"
    / "historical_thermal_osm_association.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "SIH26162_DATA"
    / "analysis"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "facility_daily_thermal_history.csv"
)


# ============================================================
# LOAD
# ============================================================

print("Loading historical associations...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df)}")


# ============================================================
# DATETIME
# ============================================================

# FIRMS acq_time is HHMM.
# Convert to a consistent string first.

df["acq_time"] = (
    df["acq_time"]
    .astype(int)
    .astype(str)
    .str.zfill(4)
)

df["acq_datetime"] = pd.to_datetime(
    df["acq_date"].astype(str)
    + " "
    + df["acq_time"].str[:2]
    + ":"
    + df["acq_time"].str[2:]
)


# ============================================================
# FACILITY IDENTIFIER
# ============================================================

# For now the OSM name is our site identifier.
# Later we will create a proper facility table.

df["facility_name"] = df["name"].fillna(
    "UNKNOWN"
)


# ============================================================
# DAILY AGGREGATION
# ============================================================

daily = (
    df
    .groupby(
        [
            "facility_name",
            "acq_date"
        ]
    )
    .agg(
        detection_count=(
            "frp",
            "count"
        ),

        max_frp_mw=(
            "frp",
            "max"
        ),

        mean_frp_mw=(
            "frp",
            "mean"
        ),

        total_frp_mw=(
            "frp",
            "sum"
        ),

        latitude_mean=(
            "latitude",
            "mean"
        ),

        longitude_mean=(
            "longitude",
            "mean"
        )
    )
    .reset_index()
)


# ============================================================
# SORT
# ============================================================

daily = daily.sort_values(
    [
        "facility_name",
        "acq_date"
    ]
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

daily.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n========================================")
print("FACILITY HISTORY CREATED")
print("========================================")

print(
    f"Facility-day records: {len(daily)}"
)

print("\nDaily thermal history:")

print(
    daily.to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)