"""
calculate_persistence.py  --region <region_id>

Calculates facility-level persistence from daily thermal history.
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
    INPUT_FILE  = region["analysis_dir"] / "facility_daily_thermal_history.csv"
    OUTPUT_FILE = region["analysis_dir"] / "facility_persistence_summary.csv"

    print(f"Loading facility history  [{region_id}]...")
    df = pd.read_csv(INPUT_FILE)
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    print(f"Facility-day records: {len(df)}")

    results = []
    for facility, group in df.groupby("facility_name"):
        group = group.sort_values("acq_date")
        first_date = group["acq_date"].min()
        last_date  = group["acq_date"].max()
        observation_window_days = (last_date - first_date).days + 1
        active_days = len(group)
        activity_frequency = active_days / observation_window_days if observation_window_days > 0 else 0

        date_diffs = group["acq_date"].diff().dt.days.dropna()
        median_gap_days = date_diffs.median() if len(date_diffs) > 0 else None
        max_gap_days    = date_diffs.max()    if len(date_diffs) > 0 else None

        active_dates = set(group["acq_date"].dt.date)
        max_consecutive = 0
        current_streak  = 0
        date = first_date
        while date <= last_date:
            if date.date() in active_dates:
                current_streak += 1
                max_consecutive = max(max_consecutive, current_streak)
            else:
                current_streak = 0
            date += pd.Timedelta(days=1)

        results.append({
            "facility_name":             facility,
            "first_observation":         first_date.date(),
            "last_observation":          last_date.date(),
            "observation_window_days":   observation_window_days,
            "active_days":               active_days,
            "activity_frequency":        round(activity_frequency, 4),
            "median_gap_days":           median_gap_days,
            "max_gap_days":              max_gap_days,
            "max_consecutive_active_days": max_consecutive,
            "total_detections":          group["detection_count"].sum(),
            "maximum_frp_mw":            group["max_frp_mw"].max(),
            "mean_daily_max_frp_mw":     group["max_frp_mw"].mean(),
        })

    summary = pd.DataFrame(results)
    summary.to_csv(OUTPUT_FILE, index=False)

    print("\nPERSISTENCE SUMMARY")
    print(summary.to_string(index=False))
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate persistence")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    run(args.region)