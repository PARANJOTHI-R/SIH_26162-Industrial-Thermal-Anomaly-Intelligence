"""
build_facility_history.py  --region <region_id>

Builds per-facility daily thermal history from OSM association output.
Works for any configured region.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region


def run(region_id: str):
    region = get_region(region_id)
    INPUT_FILE  = region["analysis_dir"] / "historical_thermal_osm_association.csv"
    OUTPUT_DIR  = region["analysis_dir"]
    OUTPUT_FILE = OUTPUT_DIR / "facility_daily_thermal_history.csv"

    print(f"Loading historical associations  [{region_id}]...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Rows loaded: {len(df)}")

    df["acq_time"] = df["acq_time"].astype(int).astype(str).str.zfill(4)
    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " +
        df["acq_time"].str[:2] + ":" + df["acq_time"].str[2:]
    )

    df["facility_name"] = df["name"].fillna("UNKNOWN")

    daily = (
        df.groupby(["facility_name", "acq_date"])
        .agg(
            detection_count=("frp", "count"),
            max_frp_mw=("frp", "max"),
            mean_frp_mw=("frp", "mean"),
            total_frp_mw=("frp", "sum"),
            latitude_mean=("latitude", "mean"),
            longitude_mean=("longitude", "mean"),
        )
        .reset_index()
    )

    daily = daily.sort_values(["facility_name", "acq_date"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT_FILE, index=False)

    print(f"\nFacility-day records: {len(daily)}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build facility daily history")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    run(args.region)