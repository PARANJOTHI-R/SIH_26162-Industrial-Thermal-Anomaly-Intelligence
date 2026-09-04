from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = (
    BASE_DIR
    / "SIH26162_DATA"
    / "01_FIRMS"
)

NOAA20_FILE = (
    DATA_DIR
    / "jamnagar_viirs_noaa20_historical.csv"
)

NOAA21_FILE = (
    DATA_DIR
    / "jamnagar_viirs_noaa21_historical.csv"
)

OUTPUT_FILE = (
    DATA_DIR
    / "jamnagar_viirs_combined_historical.csv"
)


# ============================================================
# LOAD
# ============================================================

print("Loading NOAA-20...")
n20 = pd.read_csv(NOAA20_FILE)

print(f"NOAA-20 rows: {len(n20)}")


print("\nLoading NOAA-21...")
n21 = pd.read_csv(NOAA21_FILE)

print(f"NOAA-21 rows: {len(n21)}")


# ============================================================
# COMBINE
# ============================================================

combined = pd.concat(
    [n20, n21],
    ignore_index=True
)


# ============================================================
# NORMALIZE
# ============================================================

combined["acq_date"] = pd.to_datetime(
    combined["acq_date"]
).dt.strftime("%Y-%m-%d")

combined["acq_time"] = (
    combined["acq_time"]
    .astype(int)
    .astype(str)
    .str.zfill(4)
)


# ============================================================
# SORT
# ============================================================

combined = combined.sort_values(
    [
        "acq_date",
        "acq_time",
        "satellite",
        "latitude",
        "longitude"
    ]
).reset_index(drop=True)


# ============================================================
# EXACT DUPLICATES
# ============================================================

before = len(combined)

combined = combined.drop_duplicates()

after = len(combined)


# ============================================================
# SAVE
# ============================================================

combined.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("VIIRS DATASET COMBINED")
print("========================================")

print(f"Rows before deduplication: {before}")
print(f"Rows after deduplication : {after}")

print("\nSatellite:")
print(
    combined["satellite"].value_counts()
)

print("\nDate range:")
print(
    combined["acq_date"].min(),
    "to",
    combined["acq_date"].max()
)

print("\nObservations by date:")
print(
    combined.groupby("acq_date")
    .size()
    .to_string()
)

print("\nFRP statistics:")
print(
    combined["frp"].describe()
)

print("\nSaved:")
print(OUTPUT_FILE)