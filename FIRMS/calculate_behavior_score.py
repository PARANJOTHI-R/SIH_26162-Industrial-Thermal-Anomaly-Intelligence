import os
import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

parser = argparse.ArgumentParser(description="Calculate behavior scores")
parser.add_argument("--region", required=True)
args = parser.parse_args()
_region = get_region(args.region)

HISTORY_FILE = str(_region["analysis_dir"] / "facility_daily_thermal_history.csv")
OUTPUT_FILE  = str(_region["analysis_dir"] / "facility_behavior_assessment.csv")


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum number of PREVIOUS active days required before
# attempting a behaviour assessment.
MIN_PREVIOUS_ACTIVE_DAYS = 5

# Components of the behaviour score.
FRP_WEIGHT = 0.45
DETECTION_WEIGHT = 0.35
FREQUENCY_WEIGHT = 0.20

# Recent window used for frequency behaviour.
RECENT_WINDOW_DAYS = 30

# State thresholds.
UNUSUAL_THRESHOLD = 70
WATCH_THRESHOLD = 40


# ============================================================
# VALIDATION
# ============================================================

REQUIRED_COLUMNS = [
    "facility_name",
    "acq_date",
    "detection_count",
    "max_frp_mw",
    "mean_frp_mw",
    "total_frp_mw",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_percentile(series, percentile):
    """
    Return a percentile safely.

    Returns NaN if there is no usable history.
    """
    values = pd.to_numeric(series, errors="coerce").dropna()

    if len(values) == 0:
        return np.nan

    return float(np.percentile(values, percentile))


def deviation_score(value, historical_values):
    """
    Convert the current value into a 0-100 deviation score
    using the historical distribution.

    Logic:

    <= historical P75        -> low deviation
    P75-P90                 -> moderate deviation
    P90-P95                 -> high deviation
    > P95                   -> very high deviation

    The current observation is NEVER included in historical_values.
    """

    if pd.isna(value):
        return np.nan

    values = pd.to_numeric(
        pd.Series(historical_values),
        errors="coerce"
    ).dropna()

    if len(values) == 0:
        return np.nan

    p75 = np.percentile(values, 75)
    p90 = np.percentile(values, 90)
    p95 = np.percentile(values, 95)

    # Constant historical value.
    if p75 == p95:
        if value <= p75:
            return 0.0

        # Any increase over a completely stable baseline
        # is meaningful, but cap the score.
        ratio = (value - p75) / max(abs(p75), 1.0)

        return float(min(100.0, 70.0 + ratio * 30.0))

    if value <= p75:
        return 0.0

    if value <= p90:

        if p90 == p75:
            return 60.0

        score = 25.0 + (
            (value - p75) /
            (p90 - p75)
        ) * 35.0

        return float(score)

    if value <= p95:

        if p95 == p90:
            return 85.0

        score = 60.0 + (
            (value - p90) /
            (p95 - p90)
        ) * 25.0

        return float(score)

    # Above P95.
    excess_ratio = (
        (value - p95) /
        max(abs(p95), 1.0)
    )

    return float(
        min(100.0, 85.0 + excess_ratio * 30.0)
    )


def calculate_frequency_score(
    current_date,
    historical_dates
):
    """
    Estimate whether the site has become unusually active
    recently.

    We compare:

        active days in recent window
        vs
        historical active-day frequency

    using ONLY dates before the current observation.

    Returns a 0-100 score.
    """

    if len(historical_dates) == 0:
        return np.nan

    historical_dates = pd.Series(
        pd.to_datetime(historical_dates)
    ).dt.normalize()

    current_date = pd.Timestamp(current_date).normalize()

    # Historical observation period.
    first_date = historical_dates.min()

    total_history_days = (
        current_date - first_date
    ).days

    if total_history_days <= 0:
        return 0.0

    historical_active_days = len(
        historical_dates.unique()
    )

    # Overall historical activity rate.
    historical_frequency = (
        historical_active_days /
        total_history_days
    )

    # Recent window.
    recent_start = (
        current_date -
        pd.Timedelta(days=RECENT_WINDOW_DAYS)
    )

    recent_dates = historical_dates[
        historical_dates >= recent_start
    ]

    recent_active_days = len(
        recent_dates.unique()
    )

    recent_frequency = (
        recent_active_days /
        RECENT_WINDOW_DAYS
    )

    if historical_frequency <= 0:
        return 0.0

    frequency_ratio = (
        recent_frequency /
        historical_frequency
    )

    # Ratio <= 1 means recent activity is not more frequent
    # than the historical pattern.
    if frequency_ratio <= 1:
        return 0.0

    # Map:
    #
    # 1x -> 0
    # 2x -> 50
    # 3x -> 75
    # 4x+ -> 100
    #
    score = (
        (frequency_ratio - 1.0) /
        3.0
    ) * 100.0

    return float(
        min(100.0, score)
    )


def build_reason(
    frp_score,
    detection_score,
    frequency_score,
    previous_active_days
):
    """
    Create a human-readable explanation.
    """

    reasons = []

    if not pd.isna(frp_score):

        if frp_score >= 85:
            reasons.append(
                "peak FRP is well above the site's previous range"
            )

        elif frp_score >= 60:
            reasons.append(
                "peak FRP is above the site's previous range"
            )

    if not pd.isna(detection_score):

        if detection_score >= 85:
            reasons.append(
                "detection count is well above the site's previous range"
            )

        elif detection_score >= 60:
            reasons.append(
                "detection count is above the site's previous range"
            )

    if not pd.isna(frequency_score):

        if frequency_score >= 60:
            reasons.append(
                "recent activity is occurring more frequently than the historical pattern"
            )

        elif frequency_score >= 40:
            reasons.append(
                "recent activity frequency is elevated"
            )

    if not reasons:

        reasons.append(
            "thermal behaviour is within the site's previous historical range"
        )

    return "; ".join(reasons)


def classify_state(
    behavior_score,
    previous_active_days
):
    """
    Classify the behaviour.

    Important:
    We do NOT classify a site as NORMAL when there is
    insufficient historical evidence.
    """

    if previous_active_days < MIN_PREVIOUS_ACTIVE_DAYS:
        return "INSUFFICIENT_HISTORY"

    if pd.isna(behavior_score):
        return "INSUFFICIENT_HISTORY"

    if behavior_score >= UNUSUAL_THRESHOLD:
        return "UNUSUAL"

    if behavior_score >= WATCH_THRESHOLD:
        return "WATCH"

    return "NORMAL"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading facility daily thermal history...")

history = pd.read_csv(
    HISTORY_FILE
)

print(
    f"Rows loaded: {len(history)}"
)


# ============================================================
# VALIDATION
# ============================================================

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in history.columns
]

if missing_columns:

    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# NORMALIZE DATA
# ============================================================

history["acq_date"] = pd.to_datetime(
    history["acq_date"],
    errors="coerce"
).dt.normalize()

numeric_columns = [
    "detection_count",
    "max_frp_mw",
    "mean_frp_mw",
    "total_frp_mw",
]

for column in numeric_columns:

    history[column] = pd.to_numeric(
        history[column],
        errors="coerce"
    )


# Remove rows without valid dates/facility names.

history = history.dropna(
    subset=[
        "facility_name",
        "acq_date"
    ]
).copy()


# Sort chronologically.

history = history.sort_values(
    [
        "facility_name",
        "acq_date"
    ]
).reset_index(
    drop=True
)


# ============================================================
# WALK-FORWARD BEHAVIOUR ASSESSMENT
# ============================================================

results = []

print()
print("Building walk-forward behaviour assessments...")
print(
    f"Minimum previous active days: "
    f"{MIN_PREVIOUS_ACTIVE_DAYS}"
)
print(
    f"Recent frequency window: "
    f"{RECENT_WINDOW_DAYS} days"
)


for facility_name, facility_df in history.groupby(
    "facility_name",
    sort=True
):

    facility_df = facility_df.sort_values(
        "acq_date"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Process each facility-day chronologically.
    # --------------------------------------------------------

    for index, current_row in facility_df.iterrows():

        current_date = current_row["acq_date"]

        # ----------------------------------------------------
        # IMPORTANT:
        # Only observations BEFORE the current date are used.
        # ----------------------------------------------------

        previous_df = facility_df[
            facility_df["acq_date"] < current_date
        ].copy()

        previous_active_days = len(
            previous_df
        )

        # ----------------------------------------------------
        # Default values.
        # ----------------------------------------------------

        frp_score = np.nan
        detection_score = np.nan
        frequency_score = np.nan

        frp_p75 = np.nan
        frp_p90 = np.nan
        frp_p95 = np.nan

        detection_p75 = np.nan
        detection_p90 = np.nan
        detection_p95 = np.nan

        previous_activity_frequency = np.nan

        # ----------------------------------------------------
        # Calculate baseline only when sufficient history exists.
        # ----------------------------------------------------

        if previous_active_days >= MIN_PREVIOUS_ACTIVE_DAYS:

            previous_frp = previous_df[
                "max_frp_mw"
            ].dropna()

            previous_detection = previous_df[
                "detection_count"
            ].dropna()

            # -----------------------------------------------
            # Historical percentiles.
            # -----------------------------------------------

            frp_p75 = safe_percentile(
                previous_frp,
                75
            )

            frp_p90 = safe_percentile(
                previous_frp,
                90
            )

            frp_p95 = safe_percentile(
                previous_frp,
                95
            )

            detection_p75 = safe_percentile(
                previous_detection,
                75
            )

            detection_p90 = safe_percentile(
                previous_detection,
                90
            )

            detection_p95 = safe_percentile(
                previous_detection,
                95
            )

            # -----------------------------------------------
            # FRP deviation.
            # -----------------------------------------------

            frp_score = deviation_score(
                current_row["max_frp_mw"],
                previous_frp
            )

            # -----------------------------------------------
            # Detection-count deviation.
            # -----------------------------------------------

            detection_score = deviation_score(
                current_row["detection_count"],
                previous_detection
            )

            # -----------------------------------------------
            # Frequency deviation.
            # -----------------------------------------------

            frequency_score = calculate_frequency_score(
                current_date,
                previous_df["acq_date"]
            )

            # -----------------------------------------------
            # Overall historical activity frequency.
            # -----------------------------------------------

            if len(previous_df) > 0:

                first_previous_date = previous_df[
                    "acq_date"
                ].min()

                history_days = (
                    current_date -
                    first_previous_date
                ).days

                if history_days > 0:

                    previous_activity_frequency = (
                        previous_active_days /
                        history_days
                    )

        # ====================================================
        # COMBINED SCORE
        # ====================================================

        component_scores = [
            frp_score,
            detection_score,
            frequency_score
        ]

        component_weights = [
            FRP_WEIGHT,
            DETECTION_WEIGHT,
            FREQUENCY_WEIGHT
        ]

        weighted_sum = 0.0
        available_weight = 0.0

        for score, weight in zip(
            component_scores,
            component_weights
        ):

            if not pd.isna(score):

                weighted_sum += (
                    score * weight
                )

                available_weight += weight

        if available_weight > 0:

            behavior_score = (
                weighted_sum /
                available_weight
            )

        else:

            behavior_score = np.nan

        if not pd.isna(behavior_score):

            behavior_score = round(
                behavior_score,
                2
            )

        # ====================================================
        # STATE
        # ====================================================

        behavior_state = classify_state(
            behavior_score,
            previous_active_days
        )

        # ====================================================
        # EXPLANATION
        # ====================================================

        reason = build_reason(
            frp_score,
            detection_score,
            frequency_score,
            previous_active_days
        )

        # ====================================================
        # BASELINE PERIOD
        # ====================================================

        if previous_active_days > 0:

            baseline_start = (
                previous_df["acq_date"].min()
            )

            baseline_end = (
                previous_df["acq_date"].max()
            )

        else:

            baseline_start = pd.NaT
            baseline_end = pd.NaT

        # ====================================================
        # APPEND RESULT
        # ====================================================

        results.append(
            {
                "facility_name":
                    facility_name,

                "acq_date":
                    current_date.date(),

                "detection_count":
                    current_row["detection_count"],

                "max_frp_mw":
                    current_row["max_frp_mw"],

                "mean_frp_mw":
                    current_row["mean_frp_mw"],

                "total_frp_mw":
                    current_row["total_frp_mw"],

                # ------------------------------
                # Behaviour components
                # ------------------------------

                "frp_score":
                    round(frp_score, 2)
                    if not pd.isna(frp_score)
                    else np.nan,

                "detection_score":
                    round(detection_score, 2)
                    if not pd.isna(detection_score)
                    else np.nan,

                "frequency_score":
                    round(frequency_score, 2)
                    if not pd.isna(frequency_score)
                    else np.nan,

                "behavior_score":
                    behavior_score,

                "behavior_state":
                    behavior_state,

                "reason":
                    reason,

                # ------------------------------
                # Historical context
                # ------------------------------

                "previous_active_days":
                    previous_active_days,

                "baseline_start_date":
                    baseline_start.date()
                    if not pd.isna(baseline_start)
                    else "",

                "baseline_end_date":
                    baseline_end.date()
                    if not pd.isna(baseline_end)
                    else "",

                "baseline_activity_frequency":
                    round(
                        previous_activity_frequency,
                        4
                    )
                    if not pd.isna(
                        previous_activity_frequency
                    )
                    else np.nan,

                # ------------------------------
                # Historical FRP distribution
                # ------------------------------

                "frp_p75_mw":
                    round(frp_p75, 4)
                    if not pd.isna(frp_p75)
                    else np.nan,

                "frp_p90_mw":
                    round(frp_p90, 4)
                    if not pd.isna(frp_p90)
                    else np.nan,

                "frp_p95_mw":
                    round(frp_p95, 4)
                    if not pd.isna(frp_p95)
                    else np.nan,

                # ------------------------------
                # Historical detection distribution
                # ------------------------------

                "detection_p75":
                    round(detection_p75, 4)
                    if not pd.isna(
                        detection_p75
                    )
                    else np.nan,

                "detection_p90":
                    round(detection_p90, 4)
                    if not pd.isna(
                        detection_p90
                    )
                    else np.nan,

                "detection_p95":
                    round(detection_p95, 4)
                    if not pd.isna(
                        detection_p95
                    )
                    else np.nan,

                # ------------------------------
                # Explainability
                # ------------------------------

                "assessment_basis":
                    (
                        "Walk-forward facility-level "
                        "historical thermal baseline"
                    ),
            }
        )


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

assessment = pd.DataFrame(
    results
)


# ============================================================
# SORT OUTPUT
# ============================================================

assessment = assessment.sort_values(
    [
        "facility_name",
        "acq_date"
    ]
).reset_index(
    drop=True
)


# ------------------------------------------------------------
# Clean numeric score columns before export
# ------------------------------------------------------------
score_columns = [
    "frp_score",
    "detection_score",
    "frequency_score",
    "behavior_score",
]

for col in score_columns:
    if col in assessment.columns:
        assessment[col] = pd.to_numeric(
            assessment[col],
            errors="coerce"
        )

# Round scores for clean CSV/dashboard output
for col in score_columns:
    if col in assessment.columns:
        assessment[col] = assessment[col].round(2)


# ============================================================
# SAVE
# ============================================================

assessment.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("WALK-FORWARD FACILITY BEHAVIOUR ASSESSMENT CREATED")
print("=" * 70)

print()

print(
    f"Assessment rows: {len(assessment)}"
)

print(
    f"Facilities: "
    f"{assessment['facility_name'].nunique()}"
)

print()

print("Behaviour states:")

print(
    assessment[
        "behavior_state"
    ].value_counts(
        dropna=False
    ).to_string()
)


# ============================================================
# SHOW IMPORTANT EVENTS
# ============================================================

print()
print("=" * 70)
print("HIGHEST-SCORING ASSESSMENTS")
print("=" * 70)

display_columns = [
    "facility_name",
    "acq_date",
    "detection_count",
    "max_frp_mw",
    "total_frp_mw",
    "previous_active_days",
    "frp_score",
    "detection_score",
    "frequency_score",
    "behavior_score",
    "behavior_state",
]

print()

print(
    assessment[
        display_columns
    ]
    .sort_values(
        "behavior_score",
        ascending=False,
        na_position="last"
    )
    .head(20)
    .to_string(index=False)
)


# ============================================================
# SPECIFIC RELIANCE CHECK
# ============================================================

reliance = assessment[
    assessment["facility_name"]
    .astype(str)
    .str.contains(
        "Reliance",
        case=False,
        na=False
    )
].copy()

if len(reliance) > 0:

    print()
    print("=" * 70)
    print("RELIANCE REFINERY BEHAVIOUR CHECK")
    print("=" * 70)

    print()

    print(
        reliance[
            display_columns
        ].to_string(index=False)
    )


# ============================================================
# FINAL INFORMATION
# ============================================================

print()
print("=" * 70)
print("INTERPRETATION")
print("=" * 70)

print(
    "Each facility-day is evaluated using only observations "
    "from earlier dates for that facility."
)

print(
    "The current observation is therefore not included in "
    "its own historical baseline."
)

print(
    f"A minimum of {MIN_PREVIOUS_ACTIVE_DAYS} previous "
    "active days is required before behaviour is classified."
)

print(
    "INSUFFICIENT_HISTORY does not mean normal or abnormal; "
    "it means there is not enough historical evidence."
)

print()
print("Saved:")
print(OUTPUT_FILE)