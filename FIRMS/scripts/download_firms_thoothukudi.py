"""
Download Thoothukudi FIRMS VIIRS NOAA-20 + NOAA-21 historical data.
Bbox covers the industrial coastal corridor around Thoothukudi (Tuticorin), Tamil Nadu.
"""

from pathlib import Path
from datetime import datetime, timedelta
import requests
import pandas as pd
import io
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.regions import get_region

region = get_region("thoothukudi")

MAP_KEY    = "470253c79c89b0ca2e8e331bb0e8a996"
BBOX_LIST  = region["bbox"]   # [west, south, east, north]
BBOX       = f"{BBOX_LIST[0]},{BBOX_LIST[1]},{BBOX_LIST[2]},{BBOX_LIST[3]}"
START_DATE = "2026-03-01"
END_DATE   = "2026-08-29"
CHUNK_DAYS = 5

OUTPUT_DIR = region["firms_dir"]
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = [
    ("VIIRS_NOAA21_NRT", "thoothukudi_viirs_noaa21_historical.csv"),
    ("VIIRS_NOAA20_NRT", "thoothukudi_viirs_noaa20_historical.csv"),
]

start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
end   = datetime.strptime(END_DATE,   "%Y-%m-%d").date()

all_dfs = []

for SOURCE, out_filename in SOURCES:
    print(f"\n{'='*60}")
    print(f"Downloading {SOURCE} for Thoothukudi")
    print(f"{'='*60}")

    source_data = []
    current_date = start

    while current_date <= end:
        remaining_days = (end - current_date).days + 1
        days = min(CHUNK_DAYS, remaining_days)
        date_string = current_date.strftime("%Y-%m-%d")

        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{MAP_KEY}/{SOURCE}/{BBOX}/{days}/{date_string}"
        )

        print(f"  {date_string} ({days}d)...", end="", flush=True)

        try:
            response = requests.get(url, timeout=120)
            if response.status_code != 200:
                print(f" HTTP {response.status_code} - skipping")
            else:
                df = pd.read_csv(io.StringIO(response.text))
                print(f" {len(df)} rows")
                if len(df) > 0:
                    df["satellite"] = "N21" if "21" in SOURCE else "N20"
                    source_data.append(df)
        except Exception as e:
            print(f" ERROR: {e}")

        current_date += timedelta(days=days)
        time.sleep(0.5)

    if source_data:
        combined = pd.concat(source_data, ignore_index=True).drop_duplicates()
        out_path = OUTPUT_DIR / out_filename
        combined.to_csv(out_path, index=False)
        print(f"  Saved {len(combined)} rows -> {out_path}")
        all_dfs.append(combined)
    else:
        print(f"  No data for {SOURCE}")

# Combine into the master file
print("\nCombining all satellites...")
if all_dfs:
    combined_all = pd.concat(all_dfs, ignore_index=True).drop_duplicates()
    out_path = OUTPUT_DIR / region["firms_combined_file"]
    combined_all.to_csv(out_path, index=False)
    print(f"Combined: {len(combined_all)} observations → {out_path}")
    if "acq_date" in combined_all.columns:
        print(f"Date range: {combined_all['acq_date'].min()} to {combined_all['acq_date'].max()}")
    if "satellite" in combined_all.columns:
        print(combined_all["satellite"].value_counts().to_string())
else:
    print("No data downloaded. Creating empty placeholder.")
    empty = pd.DataFrame(columns=[
        "latitude","longitude","acq_date","acq_time",
        "satellite","instrument","confidence","bright_ti4","bright_ti5","frp","daynight"
    ])
    out_path = OUTPUT_DIR / region["firms_combined_file"]
    empty.to_csv(out_path, index=False)

print("\nDone.")
