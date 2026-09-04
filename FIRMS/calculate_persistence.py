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
    / "facility_daily_thermal_history.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "SIH26162_DATA"
    / "analysis"
    / "facility_persistence_summary.csv"
)


# ============================================================
# LOAD
# ============================================================

print("Loading facility history...")

df = pd.read_csv(INPUT_FILE)

df["acq_date"] = pd.to_datetime(
    df["acq_date"]
)

print(f"Facility-day records: {len(df)}")


# ============================================================
# CALCULATE SUMMARY
# ============================================================

results = []

for facility, group in df.groupby("facility_name"):

    group = group.sort_values("acq_date")

    first_date = group["acq_date"].min()
    last_date = group["acq_date"].max()

    observation_window_days = (
        last_date - first_date
    ).days + 1

    active_days = len(group)

    activity_frequency = (
        active_days / observation_window_days
    )

    # Gaps between active days
    date_diffs = (
        group["acq_date"]
        .diff()
        .dt.days
        .dropna()
    )

    if len(date_diffs) > 0:
        median_gap_days = date_diffs.median()
        max_gap_days = date_diffs.max()
    else:
        median_gap_days = None
        max_gap_days = None

    # Maximum number of consecutive active days
    active_dates = set(
        group["acq_date"].dt.date
    )

    max_consecutive_days = 0
    current_streak = 0

    date = first_date

    while date <= last_date:

        if date.date() in active_dates:
            current_streak += 1
            max_consecutive_days = max(
                max_consecutive_days,
                current_streak
            )
        else:
            current_streak = 0

        date += pd.Timedelta(days=1)

    results.append({
        "facility_name": facility,
        "first_observation": first_date.date(),
        "last_observation": last_date.date(),
        "observation_window_days": observation_window_days,
        "active_days": active_days,
        "activity_frequency": round(
            activity_frequency,
            4
        ),
        "median_gap_days": median_gap_days,
        "max_gap_days": max_gap_days,
        "max_consecutive_active_days":
            max_consecutive_days,
        "total_detections":
            group["detection_count"].sum(),
        "maximum_frp_mw":
            group["max_frp_mw"].max(),
        "mean_daily_max_frp_mw":
            group["max_frp_mw"].mean(),
    })


summary = pd.DataFrame(results)


# ============================================================
# SAVE
# ============================================================

summary.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n========================================")
print("PERSISTENCE SUMMARY")
print("========================================")

print(
    summary.to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)