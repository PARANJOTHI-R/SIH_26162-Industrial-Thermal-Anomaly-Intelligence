from pathlib import Path
from datetime import datetime, timedelta
import requests
import pandas as pd
import io
import time


# ============================================================
# CONFIG
# ============================================================

MAP_KEY = "470253c79c89b0ca2e8e331bb0e8a996"

SOURCE = "VIIRS_NOAA21_NRT"

# Jamnagar pilot bbox:
# west, south, east, north
BBOX = "69.70,22.20,70.00,22.50"

# Historical period
START_DATE = "2026-03-01"
END_DATE   = "2026-08-29"

# FIRMS allows maximum 5 days per request
CHUNK_DAYS = 5


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = (
    BASE_DIR
    / "SIH26162_DATA"
    / "01_FIRMS"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "jamnagar_viirs_noaa21_historical.csv"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATE HELPERS
# ============================================================

start = datetime.strptime(
    START_DATE,
    "%Y-%m-%d"
).date()

end = datetime.strptime(
    END_DATE,
    "%Y-%m-%d"
).date()


# ============================================================
# DOWNLOAD
# ============================================================

all_data = []

current_date = start

while current_date <= end:

    remaining_days = (
        end - current_date
    ).days + 1

    days = min(
        CHUNK_DAYS,
        remaining_days
    )

    date_string = current_date.strftime(
        "%Y-%m-%d"
    )

    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{MAP_KEY}/"
        f"{SOURCE}/"
        f"{BBOX}/"
        f"{days}/"
        f"{date_string}"
    )

    print("\n----------------------------------------")
    print(f"Requesting: {date_string}")
    print(f"Days      : {days}")
    print("----------------------------------------")

    try:

        response = requests.get(
            url,
            timeout=120
        )

        print(
            f"HTTP status: {response.status_code}"
        )

        if response.status_code != 200:

            print(response.text[:1000])

            raise RuntimeError(
                f"FIRMS request failed for {date_string}"
            )

        df = pd.read_csv(
            io.StringIO(response.text)
        )

        print(
            f"Rows received: {len(df)}"
        )

        if len(df) > 0:

            all_data.append(df)

    except Exception as e:

        print(
            f"ERROR: {e}"
        )

        raise

    current_date += timedelta(
        days=days
    )

    # Small delay between requests
    time.sleep(1)


# ============================================================
# COMBINE
# ============================================================

if not all_data:

    print("\nNo FIRMS observations found.")
    raise SystemExit()


historical = pd.concat(
    all_data,
    ignore_index=True
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(historical)

historical = historical.drop_duplicates()

after = len(historical)

print("\n========================================")
print("HISTORICAL FIRMS DOWNLOAD COMPLETE")
print("========================================")

print(
    f"Rows before deduplication: {before}"
)

print(
    f"Rows after deduplication : {after}"
)


# ============================================================
# INSPECTION
# ============================================================

print("\nColumns:")
print(list(historical.columns))

print("\nDate range:")

if "acq_date" in historical.columns:

    print(
        historical["acq_date"].min(),
        "to",
        historical["acq_date"].max()
    )


print("\nSatellite:")
if "satellite" in historical.columns:
    print(
        historical["satellite"].value_counts()
    )


print("\nConfidence:")
if "confidence" in historical.columns:
    print(
        historical["confidence"].value_counts()
    )


print("\nMissing values:")
print(
    historical.isna().sum()
)


# ============================================================
# SAVE
# ============================================================

historical.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:")
print(OUTPUT_FILE)