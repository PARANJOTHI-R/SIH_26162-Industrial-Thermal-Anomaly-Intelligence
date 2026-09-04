import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "SIH26162_DATA",
    "analysis",
    "facility_daily_thermal_history.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "SIH26162_DATA",
    "analysis",
    "facility_behavior_baseline.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("Loading facility daily thermal history...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df)}")

if df.empty:
    raise ValueError("Input dataset is empty.")

required_columns = [
    "facility_name",
    "acq_date",
    "detection_count",
    "max_frp_mw",
    "mean_frp_mw",
    "total_frp_mw"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# NORMALIZE DATA
# ============================================================

df["acq_date"] = pd.to_datetime(df["acq_date"])

numeric_columns = [
    "detection_count",
    "max_frp_mw",
    "mean_frp_mw",
    "total_frp_mw"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# Remove rows with invalid core values

df = df.dropna(
    subset=[
        "facility_name",
        "detection_count",
        "max_frp_mw"
    ]
)


# ============================================================
# BASELINE CALCULATION
# ============================================================

baseline_rows = []

for facility_name, group in df.groupby("facility_name"):

    group = group.sort_values("acq_date").copy()

    active_days = len(group)

    first_date = group["acq_date"].min()
    last_date = group["acq_date"].max()

    observation_window_days = (
        last_date - first_date
    ).days + 1

    # --------------------------------------------------------
    # FRP statistics
    # --------------------------------------------------------

    max_frp = group["max_frp_mw"]

    frp_mean = max_frp.mean()
    frp_median = max_frp.median()
    frp_std = max_frp.std(ddof=1)

    frp_p75 = max_frp.quantile(0.75)
    frp_p90 = max_frp.quantile(0.90)
    frp_p95 = max_frp.quantile(0.95)

    frp_min = max_frp.min()
    frp_max = max_frp.max()

    # --------------------------------------------------------
    # Detection-count statistics
    # --------------------------------------------------------

    detection_counts = group["detection_count"]

    detection_mean = detection_counts.mean()
    detection_median = detection_counts.median()

    detection_p75 = detection_counts.quantile(0.75)
    detection_p90 = detection_counts.quantile(0.90)
    detection_p95 = detection_counts.quantile(0.95)

    detection_max = detection_counts.max()

    # --------------------------------------------------------
    # Activity frequency
    # --------------------------------------------------------

    activity_frequency = (
        active_days / observation_window_days
        if observation_window_days > 0
        else np.nan
    )

    # --------------------------------------------------------
    # Gap statistics
    # --------------------------------------------------------

    dates = group["acq_date"].sort_values()

    if len(dates) > 1:

        gaps = dates.diff().dt.days.dropna()

        median_gap = gaps.median()
        mean_gap = gaps.mean()
        max_gap = gaps.max()

    else:

        median_gap = np.nan
        mean_gap = np.nan
        max_gap = np.nan

    # --------------------------------------------------------
    # Mean daily thermal activity
    # --------------------------------------------------------

    mean_daily_detections = detection_counts.mean()

    mean_daily_total_frp = group["total_frp_mw"].mean()

    # --------------------------------------------------------
    # Store baseline
    # --------------------------------------------------------

    baseline_rows.append({

        "facility_name": facility_name,

        "first_observation":
            first_date.strftime("%Y-%m-%d"),

        "last_observation":
            last_date.strftime("%Y-%m-%d"),

        "observation_window_days":
            observation_window_days,

        "active_days":
            active_days,

        "activity_frequency":
            activity_frequency,

        # FRP baseline
        "frp_mean_mw":
            frp_mean,

        "frp_median_mw":
            frp_median,

        "frp_std_mw":
            frp_std,

        "frp_p75_mw":
            frp_p75,

        "frp_p90_mw":
            frp_p90,

        "frp_p95_mw":
            frp_p95,

        "frp_min_mw":
            frp_min,

        "frp_max_mw":
            frp_max,

        # Detection-count baseline
        "detection_mean":
            detection_mean,

        "detection_median":
            detection_median,

        "detection_p75":
            detection_p75,

        "detection_p90":
            detection_p90,

        "detection_p95":
            detection_p95,

        "detection_max":
            detection_max,

        # Persistence
        "median_gap_days":
            median_gap,

        "mean_gap_days":
            mean_gap,

        "max_gap_days":
            max_gap,

        # Daily averages
        "mean_daily_detections":
            mean_daily_detections,

        "mean_daily_total_frp_mw":
            mean_daily_total_frp
    })


# ============================================================
# CREATE OUTPUT
# ============================================================

baseline_df = pd.DataFrame(baseline_rows)

baseline_df = baseline_df.sort_values(
    "facility_name"
)

baseline_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 50)
print("FACILITY BEHAVIOUR BASELINE CREATED")
print("=" * 50)

print()

print(baseline_df.to_string(index=False))

print()
print("Saved:")
print(OUTPUT_FILE)