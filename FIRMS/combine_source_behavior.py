import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

parser = argparse.ArgumentParser(description="Combine source + behavior")
parser.add_argument("--region", required=True)
args = parser.parse_args()
_region = get_region(args.region)

SOURCE_FILE      = _region["analysis_dir"] / "thermal_source_classification_v2.csv"
BEHAVIOR_FILE    = _region["analysis_dir"] / "facility_behavior_assessment.csv"
PERSISTENCE_FILE = _region["analysis_dir"] / "facility_persistence_summary.csv"
OUTPUT_FILE      = _region["analysis_dir"] / "thermal_source_behavior_intelligence.csv"

print("=" * 70)
print("SIH26162 — Source + Behaviour Intelligence")
print("=" * 70)

# ------------------------------------------------------------
# 1. Load
# ------------------------------------------------------------

source = pd.read_csv(SOURCE_FILE)
behavior = pd.read_csv(BEHAVIOR_FILE)
persistence = pd.read_csv(PERSISTENCE_FILE)

print(f"\nSource observations: {len(source)}")
print(f"Behaviour facility-days: {len(behavior)}")
print(f"Persistence facilities: {len(persistence)}")


# ------------------------------------------------------------
# 2. Normalize dates
# ------------------------------------------------------------

if "event_date" in source.columns:
    source = source.rename(columns={"event_date": "acq_date", "event_start_time": "acq_time"})

source["acq_date"] = pd.to_datetime(
    source["acq_date"]
).dt.date.astype(str)

behavior["acq_date"] = pd.to_datetime(
    behavior["acq_date"]
).dt.date.astype(str)

# persistence["first_active_date"] = pd.to_datetime(
#     persistence["first_active_date"]
# ).dt.date.astype(str)

# persistence["last_active_date"] = pd.to_datetime(
#     persistence["last_active_date"]
# ).dt.date.astype(str)


# ------------------------------------------------------------
# 3. Determine facility name
# ------------------------------------------------------------

# OSM name is the primary facility identifier for this pilot.
# Unmatched observations remain UNKNOWN.

source["facility_name"] = (
    source.get("nearest_osm_name", source.get("name"))
    .fillna("")
    .astype(str)
    .str.strip()
)

source.loc[
    source["facility_name"].isin(["", "nan", "None"]),
    "facility_name"
] = "UNKNOWN"


# ------------------------------------------------------------
# 4. Clean malformed behaviour numeric fields
# ------------------------------------------------------------

numeric_behavior_cols = [
    "frp_score",
    "detection_score",
    "frequency_score",
    "behavior_score",
    "baseline_activity_frequency",
    "frp_p75_mw",
    "frp_p90_mw",
    "frp_p95_mw",
    "detection_p75",
    "detection_p90",
    "detection_p95",
]

for col in numeric_behavior_cols:

    if col in behavior.columns:

        # Handle values such as "NaNNaN"
        behavior[col] = (
            behavior[col]
            .astype(str)
            .replace({
                "NaNNaN": np.nan,
                "nan": np.nan,
                "None": np.nan,
                "": np.nan,
            })
        )

        behavior[col] = pd.to_numeric(
            behavior[col],
            errors="coerce"
        )


# ------------------------------------------------------------
# 5. Aggregate source observations to facility-day
# ------------------------------------------------------------

source_daily = (
    source
    .groupby(
        ["facility_name", "acq_date"],
        as_index=False
    )
    .agg(
        observation_count=("latitude", "count"),
        max_frp_mw=("max_frp", "max"),
        mean_frp_mw=("max_frp", "mean"),
        total_frp_mw=("max_frp", "sum"),

        source_class=("source_class_v2", "first"),
        classification_confidence=(
            "classification_confidence_v2",
            "first"
        ),
        evidence_strength=("evidence_strength", "first"),

        worldcover_context=("worldcover_context", "first"),
        worldcover_class=("worldcover_class", "first"),

        association_type=("association_type", "first"),
        association_confidence=(
            "association_confidence",
            "first"
        ),

        osm_feature_name=("name", "first"),
        osm_industrial=("industrial", "first"),
        osm_landuse=("landuse", "first"),

        evidence_summary=("evidence_summary", "first"),
    )
)


# ------------------------------------------------------------
# 6. Merge behaviour
# ------------------------------------------------------------

result = source_daily.merge(
    behavior,
    on=["facility_name", "acq_date"],
    how="left",
    suffixes=("", "_behavior")
)


# ------------------------------------------------------------
# 7. Merge persistence
# ------------------------------------------------------------

persistence_cols = [
    "facility_name",
    "active_days",
    "window_days",
    "activity_frequency",
    "median_gap_days",
    "max_gap_days",
    "max_consecutive_active_days",
    "total_detections",
    "max_frp_mw",
    "mean_daily_max_frp_mw",
]

persistence_small = persistence[
    [
        c for c in persistence_cols
        if c in persistence.columns
    ]
].copy()

persistence_small = persistence_small.rename(
    columns={
        "max_frp_mw": "historical_max_frp_mw",
    }
)

result = result.merge(
    persistence_small,
    on="facility_name",
    how="left"
)


# ------------------------------------------------------------
# 8. Persistence state
# ------------------------------------------------------------

def persistence_state(row):

    active_days = row.get("active_days", np.nan)
    frequency = row.get("activity_frequency", np.nan)
    consecutive = row.get(
        "max_consecutive_active_days",
        np.nan
    )

    if pd.isna(active_days):
        return "UNKNOWN"

    if active_days <= 1:
        return "TRANSIENT"

    if (
        (not pd.isna(consecutive) and consecutive >= 3)
        or
        (not pd.isna(frequency) and frequency >= 0.20)
    ):
        return "RECURRING"

    return "INTERMITTENT"


result["persistence_state"] = result.apply(
    persistence_state,
    axis=1
)


# ------------------------------------------------------------
# 9. Investigation priority
# ------------------------------------------------------------

def investigation_priority(row):

    source_class = row.get("source_class", "")
    behavior_state = row.get("behavior_state", "")
    persistence = row.get("persistence_state", "")
    score = row.get("behavior_score", np.nan)

    # Strongest case:
    # industrial-associated + unusual behaviour
    if (
        source_class == "INDUSTRIAL_ASSOCIATED"
        and behavior_state == "UNUSUAL"
    ):
        return "HIGH"

    # Industrial watch condition
    if (
        source_class == "INDUSTRIAL_ASSOCIATED"
        and behavior_state == "WATCH"
    ):
        return "MEDIUM"

    # Recurring unmatched source.
    # Important: this is NOT evidence of an unregistered industry.
    if (
        row.get("facility_name") == "UNKNOWN"
        and persistence == "RECURRING"
    ):
        return "MEDIUM"

    return "LOW"


result["investigation_priority"] = result.apply(
    investigation_priority,
    axis=1
)


# ------------------------------------------------------------
# 10. Human-readable interpretation
# ------------------------------------------------------------

def interpretation(row):

    source_class = row.get("source_class", "")
    behavior_state = row.get("behavior_state", "")
    persistence = row.get("persistence_state", "")
    facility = row.get("facility_name", "UNKNOWN")

    if (
        source_class == "INDUSTRIAL_ASSOCIATED"
        and behavior_state == "UNUSUAL"
    ):
        return (
            f"{facility}: industrial-associated thermal activity "
            f"shows unusual behaviour relative to its historical "
            f"baseline. Suitable for human investigation."
        )

    if (
        source_class == "INDUSTRIAL_ASSOCIATED"
        and behavior_state == "WATCH"
    ):
        return (
            f"{facility}: industrial-associated thermal activity "
            f"shows a watch-level deviation from historical behaviour."
        )

    if (
        facility == "UNKNOWN"
        and persistence == "RECURRING"
    ):
        return (
            "Recurring thermal source without a matched facility "
            "in the current infrastructure data. Candidate for "
            "further investigation; not evidence of an unregistered "
            "industry."
        )

    if behavior_state == "INSUFFICIENT_HISTORY":
        return (
            f"{facility}: insufficient historical observations "
            "for reliable behavioural assessment."
        )

    return (
        f"{facility}: thermal behaviour is currently within "
        "the available historical context."
    )


result["decision_interpretation"] = result.apply(
    interpretation,
    axis=1
)


# ------------------------------------------------------------
# 11. Final columns
# ------------------------------------------------------------

final_columns = [
    "facility_name",
    "acq_date",

    "observation_count",
    "max_frp_mw",
    "mean_frp_mw",
    "total_frp_mw",

    "source_class",
    "classification_confidence",
    "evidence_strength",

    "worldcover_context",
    "worldcover_class",

    "association_type",
    "association_confidence",
    "osm_feature_name",
    "osm_industrial",
    "osm_landuse",

    "behavior_state",
    "behavior_score",
    "frp_score",
    "detection_score",
    "frequency_score",
    "previous_active_days",

    "persistence_state",
    "active_days",
    "window_days",
    "activity_frequency",
    "median_gap_days",
    "max_gap_days",
    "max_consecutive_active_days",

    "investigation_priority",

    "evidence_summary",
    "reason",
    "decision_interpretation",
]

final_columns = [
    c for c in final_columns
    if c in result.columns
]

result = result[final_columns]


# ------------------------------------------------------------
# 12. Save
# ------------------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 13. Summary
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("INTELLIGENCE SUMMARY")
print("=" * 70)

print("\nFacility-day records:")
print(len(result))

print("\nSource classes:")
print(
    result["source_class"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nBehaviour states:")
print(
    result["behavior_state"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nPersistence states:")
print(
    result["persistence_state"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nInvestigation priorities:")
print(
    result["investigation_priority"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nHIGH priority cases:")

high = result[
    result["investigation_priority"] == "HIGH"
]

if len(high):

    cols = [
        "facility_name",
        "acq_date",
        "max_frp_mw",
        "observation_count",
        "source_class",
        "behavior_state",
        "behavior_score",
        "persistence_state",
        "investigation_priority",
    ]

    print(
        high[cols]
        .sort_values(
            "behavior_score",
            ascending=False
        )
        .to_string(index=False)
    )

else:
    print("None")

print("\nOutput:")
print(OUTPUT_FILE)

print("\nDone.")