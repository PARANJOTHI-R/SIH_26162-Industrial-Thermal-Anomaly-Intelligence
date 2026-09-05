import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import math
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.regions import REGIONS


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SIH26162 Thermal Intelligence API",
    description=(
        "Context-aware monitoring of industrial-associated "
        "thermal activity and historical site behaviour."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL DATA
# ============================================================
# Map of region_id -> dict of dataframes and lookups
region_store: Dict[str, Dict[str, Any]] = {}


# ============================================================
# BASELINE FIELDS
# ============================================================

BASELINE_FIELDS = [
    "baseline_mean_frp",
    "baseline_median_frp",
    "baseline_p75_frp",
    "baseline_p90_frp",
    "baseline_p95_frp",
    "baseline_std_frp",
    "activity_rate",
    "baseline_active_days",
    "baseline_period_days",
    "baseline_detection_mean",
    "baseline_detection_median",
    "baseline_detection_p90",
    "baseline_detection_p95",
]

SPATIAL_FIELDS = [
    "spatial_behavior_state",
    "spatial_behavior_score",
    "spatial_behavior_confidence",
    "historical_centroid_lat",
    "historical_centroid_lon",
    "current_centroid_lat",
    "current_centroid_lon",
    "centroid_shift_km",
    "historical_spatial_radius_km",
    "current_spatial_radius_km",
    "spatial_expansion_ratio",
    "historical_spatial_observation_count",
]

BASELINE_MAPPING = {
    "baseline_mean_frp": "frp_mean_mw",
    "baseline_median_frp": "frp_median_mw",
    "baseline_p75_frp": "frp_p75_mw",
    "baseline_p90_frp": "frp_p90_mw",
    "baseline_p95_frp": "frp_p95_mw",
    "baseline_std_frp": "frp_std_mw",
    "activity_rate": "activity_frequency",
    "baseline_active_days": "active_days",
    "baseline_period_days": "observation_window_days",
    "baseline_detection_mean": "detection_mean",
    "baseline_detection_median": "detection_median",
    "baseline_detection_p90": "detection_p90",
    "baseline_detection_p95": "detection_p95",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_facility_name(value: Any) -> str:
    """
    Normalize facility/source names so joins between
    thermal observations, intelligence records and
    baseline records are reliable.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip().upper()

    # Normalize whitespace
    value = " ".join(value.split())

    return value


def clean_value(value: Any) -> Any:
    """
    Convert pandas/numpy values into JSON-safe Python values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    # numpy scalar -> Python scalar
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    # Handle infinity
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively make dataframe records JSON serializable.
    """

    output = {}

    for key, value in record.items():
        output[key] = clean_value(value)

    return output


def safe_float(value: Any) -> Optional[float]:
    """
    Convert a value to float safely.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        result = float(value)

        if math.isnan(result) or math.isinf(result):
            return None

        return result

    except (TypeError, ValueError):
        return None


def calculate_ratio(
    numerator: Any,
    denominator: Any,
) -> Optional[float]:
    """
    Calculate numerator / denominator safely.
    """

    num = safe_float(numerator)
    den = safe_float(denominator)

    if num is None or den is None or den <= 0:
        return None

    return num / den


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c


# ============================================================
# DATA LOADING
# ============================================================

def load_csv(path: Path, label: str) -> pd.DataFrame:
    """
    Load a CSV safely.
    """

    if not path.exists():
        print(f"WARNING: {label} file not found: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)

        print(f"Loaded {label}: {len(df)} rows")

        return df

    except Exception as exc:
        print(f"ERROR loading {label}: {exc}")
        return pd.DataFrame()


# ============================================================
# BASELINE LOOKUP
# ============================================================

def build_baseline_lookup(
    df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    """
    Build a normalized facility -> baseline dictionary.

    Important:
    Thermal observations use the 'name' field while the
    baseline dataset may use 'facility_name', 'facility',
    'name', etc.

    This function explicitly normalizes both sides.
    """

    lookup: Dict[str, Dict[str, Any]] = {}

    if df.empty:
        return lookup

    # --------------------------------------------------------
    # Find facility-name column
    # --------------------------------------------------------

    facility_col = None

    candidate_columns = [
        "facility_name",
        "name",
        "facility",
        "source_name",
        "source",
    ]

    for candidate in candidate_columns:
        if candidate in df.columns:
            facility_col = candidate
            break

    if facility_col is None:
        print(
            "WARNING: no facility-name column found "
            "in baseline data."
        )

        print(
            "Available baseline columns:",
            list(df.columns),
        )

        return lookup

    print(
        f"Baseline facility-name column: {facility_col}"
    )

    # --------------------------------------------------------
    # Build lookup
    # --------------------------------------------------------

    for _, row in df.iterrows():

        facility_name = normalize_facility_name(
            row.get(facility_col)
        )

        if not facility_name:
            continue

        record: Dict[str, Any] = {}

        for field in BASELINE_FIELDS:
            csv_col = BASELINE_MAPPING.get(field, field)

            if csv_col not in df.columns:
                record[field] = None
                continue

            record[field] = clean_value(
                row.get(csv_col)
            )

        # Preserve original name for debugging/UI if useful
        record["facility_name"] = clean_value(
            row.get(facility_col)
        )

        lookup[facility_name] = record

    return lookup


# ============================================================
# INTELLIGENCE LOOKUP
# ============================================================

def build_intelligence_lookup(
    df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    """
    Build facility + date lookup for facility-day intelligence.
    """

    lookup: Dict[str, Dict[str, Any]] = {}

    if df.empty:
        return lookup

    for _, row in df.iterrows():

        facility_name = normalize_facility_name(
            row.get("facility_name", row.get("name"))
        )

        acq_date = clean_value(
            row.get("acq_date", row.get("date"))
        )

        if not facility_name or not acq_date:
            continue

        key = f"{facility_name}|{acq_date}"

        lookup[key] = clean_record(
            row.to_dict()
        )

    return lookup


# ============================================================
# SPATIAL BEHAVIOUR
# ============================================================

def build_spatial_lookup(
    intelligence_df: pd.DataFrame,
    thermal_df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    """
    Build walk-forward spatial behaviour logic for facility-days.
    """
    lookup: Dict[str, Dict[str, Any]] = {}
    
    if intelligence_df.empty or thermal_df.empty:
        return lookup

    print("Building spatial behaviour lookup...")

    fac_keys = thermal_df.get("name", thermal_df.get("facility_name", thermal_df.get("facility")))
    if fac_keys is None:
        return lookup
        
    thermal_copy = thermal_df.copy()
    if "event_date" in thermal_copy.columns and "acq_date" not in thermal_copy.columns:
        thermal_copy = thermal_copy.rename(columns={"event_date": "acq_date"})
    thermal_copy["facility_key"] = fac_keys.apply(normalize_facility_name)
    
    for _, row in intelligence_df.iterrows():
        fac_name = row.get("facility_name", row.get("name"))
        fac_key = normalize_facility_name(fac_name)
        acq_date = clean_value(row.get("acq_date", row.get("date")))
        
        if not fac_key or not acq_date:
            continue
            
        key = f"{fac_key}|{acq_date}"
        
        default_insufficient = {
            "spatial_behavior_state": "INSUFFICIENT_HISTORY",
            "spatial_behavior_confidence": "LOW",
        }
        
        if "UNKNOWN" in fac_key:
            lookup[key] = default_insufficient
            continue
            
        fac_thermal = thermal_copy[thermal_copy["facility_key"] == fac_key].copy()
        
        hist_obs = fac_thermal[fac_thermal["acq_date"] < acq_date].copy()
        curr_obs = fac_thermal[fac_thermal["acq_date"] == acq_date].copy()
        
        if len(hist_obs) < 10 or len(curr_obs) == 0:
            lookup[key] = default_insufficient
            continue
            
        daily_centroids = hist_obs.groupby("acq_date")[["latitude", "longitude"]].median()
        hist_centroid_lat = float(daily_centroids["latitude"].median())
        hist_centroid_lon = float(daily_centroids["longitude"].median())
        
        hist_obs["dist_to_centroid"] = haversine_vectorized(
            hist_obs["latitude"].values, hist_obs["longitude"].values,
            hist_centroid_lat, hist_centroid_lon
        )
        hist_radius = float(np.percentile(hist_obs["dist_to_centroid"].dropna(), 90))
        
        curr_centroid_lat = float(curr_obs["latitude"].median())
        curr_centroid_lon = float(curr_obs["longitude"].median())
        
        curr_obs["dist_to_centroid"] = haversine_vectorized(
            curr_obs["latitude"].values, curr_obs["longitude"].values,
            curr_centroid_lat, curr_centroid_lon
        )
        
        if len(curr_obs) > 1:
            curr_radius = float(np.percentile(curr_obs["dist_to_centroid"].dropna(), 90))
        else:
            curr_radius = 0.0
            
        shift_km = haversine(curr_centroid_lat, curr_centroid_lon, hist_centroid_lat, hist_centroid_lon)
        
        MIN_RADIUS = 0.375 
        hist_r_adj = max(hist_radius, MIN_RADIUS)
        curr_r_adj = max(curr_radius, MIN_RADIUS)
        exp_ratio = curr_r_adj / hist_r_adj
        shift_ratio = shift_km / hist_r_adj
        
        shift_score = min(shift_ratio * 30, 50)
        exp_score = min(max(exp_ratio - 1, 0) * 30, 50)
        total_score = min(shift_score + exp_score, 100)
        
        if total_score < 40:
            state = "NORMAL"
        elif total_score < 70:
            state = "WATCH"
        else:
            state = "UNUSUAL"
            
        lookup[key] = {
            "spatial_behavior_state": state,
            "spatial_behavior_score": round(total_score, 1),
            "spatial_behavior_confidence": "HIGH",
            "historical_centroid_lat": round(hist_centroid_lat, 5),
            "historical_centroid_lon": round(hist_centroid_lon, 5),
            "current_centroid_lat": round(curr_centroid_lat, 5),
            "current_centroid_lon": round(curr_centroid_lon, 5),
            "centroid_shift_km": round(shift_km, 3),
            "historical_spatial_radius_km": round(hist_radius, 3),
            "current_spatial_radius_km": round(curr_radius, 3),
            "spatial_expansion_ratio": round(exp_ratio, 2),
            "historical_spatial_observation_count": len(hist_obs),
        }
    return lookup


# ============================================================
# BASELINE ENRICHMENT
# ============================================================

def attach_baseline(
    record: Dict[str, Any],
    baseline_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Attach facility baseline to an individual thermal observation.

    Thermal observations normally contain:
        name = "Reliance Refinery"

    Baseline may contain:
        facility_name = "Reliance Refinery"

    Both are normalized before lookup.
    """

    facility_name = record.get("name")

    # Fallbacks for compatibility
    if not facility_name:
        facility_name = record.get("facility_name")

    if not facility_name:
        facility_name = record.get("facility")

    facility_key = normalize_facility_name(
        facility_name
    )

    baseline = baseline_lookup.get(
        facility_key,
        {},
    )

    # --------------------------------------------------------
    # Attach raw baseline metrics
    # --------------------------------------------------------

    for field in BASELINE_FIELDS:
        record[field] = clean_value(
            baseline.get(field)
        )

    # --------------------------------------------------------
    # Current observation FRP
    # --------------------------------------------------------

    current_frp = safe_float(
        record.get("frp")
    )

    # --------------------------------------------------------
    # FRP deviation ratios
    # --------------------------------------------------------

    record["frp_vs_p90_ratio"] = calculate_ratio(
        current_frp,
        baseline.get("baseline_p90_frp"),
    )

    record["frp_vs_p95_ratio"] = calculate_ratio(
        current_frp,
        baseline.get("baseline_p95_frp"),
    )

    # --------------------------------------------------------
    # Deviation flags
    # --------------------------------------------------------

    p90 = safe_float(
        baseline.get("baseline_p90_frp")
    )

    p95 = safe_float(
        baseline.get("baseline_p95_frp")
    )

    record["frp_above_p90"] = (
        current_frp is not None
        and p90 is not None
        and current_frp > p90
    )

    record["frp_above_p95"] = (
        current_frp is not None
        and p95 is not None
        and current_frp > p95
    )

    # --------------------------------------------------------
    # Explicit baseline availability
    # --------------------------------------------------------

    has_metrics = any(
        record.get(field) is not None for field in BASELINE_FIELDS
    )

    record["baseline_available"] = bool(baseline) and has_metrics

    return record


# ============================================================
# FACILITY-DAY BASELINE ENRICHMENT
# ============================================================

def attach_baseline_to_facility_day(
    record: Dict[str, Any],
    baseline_lookup: Dict[str, Dict[str, Any]],
    spatial_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Attach baseline information to a facility-day record.
    """

    facility_name = (
        record.get("facility_name")
        or record.get("name")
        or record.get("source_name")
    )

    facility_key = normalize_facility_name(
        facility_name
    )

    baseline = baseline_lookup.get(
        facility_key,
        {},
    )

    for field in BASELINE_FIELDS:
        record[field] = clean_value(
            baseline.get(field)
        )

    current_frp = safe_float(
        record.get("max_frp_mw")
    )

    record["frp_vs_p90_ratio"] = calculate_ratio(
        current_frp,
        baseline.get("baseline_p90_frp"),
    )

    record["frp_vs_p95_ratio"] = calculate_ratio(
        current_frp,
        baseline.get("baseline_p95_frp"),
    )

    p90 = safe_float(
        baseline.get("baseline_p90_frp")
    )

    p95 = safe_float(
        baseline.get("baseline_p95_frp")
    )

    record["frp_above_p90"] = (
        current_frp is not None
        and p90 is not None
        and current_frp > p90
    )

    record["frp_above_p95"] = (
        current_frp is not None
        and p95 is not None
        and current_frp > p95
    )

    has_metrics = any(
        record.get(field) is not None for field in BASELINE_FIELDS
    )
    record["baseline_available"] = bool(baseline) and has_metrics

    # --------------------------------------------------------
    # Spatial enrichment
    # --------------------------------------------------------
    acq_date = record.get("acq_date", record.get("date"))
    spatial_key = f"{facility_key}|{acq_date}"
    spatial = spatial_lookup.get(spatial_key, {})
    
    for field in SPATIAL_FIELDS:
        if field in spatial:
            record[field] = spatial[field]
        else:
            record[field] = None

    return record


# ============================================================
# STARTUP / DATA INITIALIZATION
# ============================================================

def initialize_data():
    global region_store
    
    print("=" * 70)
    print("SIH26162 THERMAL INTELLIGENCE API")
    print("=" * 70)

    for region_id, region_config in REGIONS.items():
        print(f"\nInitializing Region: {region_id.upper()}")
        print("-" * 50)
        
        data_dir = Path(region_config["analysis_dir"])
        
        intel_df = load_csv(data_dir / "thermal_source_behavior_intelligence.csv", "intelligence data")
        thermal_df = load_csv(data_dir / "thermal_source_classification_v2.csv", "thermal events")
        raw_df = load_csv(data_dir / "thermal_event_observations.csv", "raw observations")
        unknown_sources_df = load_csv(data_dir / "unknown_thermal_sources.csv", "unknown sources")
        unknown_events_df = load_csv(data_dir / "unknown_source_events.csv", "unknown events")
        baseline_df = load_csv(data_dir / "facility_behavior_baseline.csv", "facility baselines")
        
        b_lookup = build_baseline_lookup(baseline_df)
        i_lookup = build_intelligence_lookup(intel_df)
        s_lookup = build_spatial_lookup(intel_df, thermal_df)
        
        region_store[region_id] = {
            "intelligence_df": intel_df,
            "thermal_df": thermal_df,
            "raw_observations_df": raw_df,
            "unknown_sources_df": unknown_sources_df,
            "unknown_events_df": unknown_events_df,
            "baseline_df": baseline_df,
            "baseline_lookup": b_lookup,
            "intelligence_lookup": i_lookup,
            "spatial_lookup": s_lookup,
        }

        print(f"Facility baseline lookup: {len(b_lookup)} facilities")
        print(f"Facility-day intelligence lookup: {len(i_lookup)} records")

    print("\n" + "=" * 70)
    print("ALL REGIONS INITIALIZED")
    print("=" * 70 + "\n")

initialize_data()



# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
async def startup_event():
    print(
        "SIH26162 API startup complete."
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root(region: str = Query("jamnagar")):
    r_data = region_store.get(region, {})
    return {
        "status": "operational",
        "service": "SIH26162 Thermal Intelligence API",
        "thermal_observations": len(r_data.get("thermal_df", [])),
        "facility_days": len(r_data.get("intelligence_df", [])),
        "facilities_with_baselines": len(r_data.get("baseline_lookup", {})),
        "intelligence_lookup_records": len(r_data.get("intelligence_lookup", {})),
    }


# ============================================================
# REGIONS
# ============================================================

@app.get("/regions")
def get_regions():
    return {
        "regions": [
            {
                "id": region_id,
                "name": config["display_name"],
                "center": config["map_center"],
                "bbox": config["bbox"],
            }
            for region_id, config in REGIONS.items()
        ]
    }

# ============================================================
# DATA STATUS
# ============================================================

@app.get("/data-status")
def data_status(region: str = Query("jamnagar")):
    
    r_data = region_store.get(region, {})
    
    return {
        "status": "operational",
        "thermal_observations": len(r_data.get("raw_observations_df", [])),
        "thermal_events": len(r_data.get("thermal_df", [])),
        "unknown_sources": len(r_data.get("unknown_sources_df", [])),
        "facility_days": len(r_data.get("intelligence_df", [])),
        "facilities_with_baselines": len(r_data.get("baseline_lookup", {})),
        "intelligence_lookup_records": len(r_data.get("intelligence_lookup", {})),
    }


# ============================================================
# THERMAL OBSERVATIONS
# ============================================================

@app.get("/thermal-events")
def get_thermal_events(
    limit: Optional[int] = None,
    region: str = Query("jamnagar")
):
    """
    Return thermal observations enriched with:

    - facility baseline
    - FRP / P90 ratio
    - FRP / P95 ratio
    - P90/P95 flags
    """
    
    r_data = region_store.get(region, {})
    thermal_df = r_data.get("thermal_df", pd.DataFrame())
    b_lookup = r_data.get("baseline_lookup", {})

    if thermal_df.empty:
        return {
            "count": 0,
            "observations": [],
        }

    records: List[Dict[str, Any]] = []

    dataframe = thermal_df

    if limit is not None:
        if limit < 1:
            raise HTTPException(
                status_code=400,
                detail="limit must be >= 1",
            )

        dataframe = dataframe.head(limit)

    for _, row in dataframe.iterrows():

        record = clean_record(
            row.to_dict()
        )

        record = attach_baseline(
            record,
            b_lookup
        )

        records.append(record)

    return {
        "count": len(records),
        "events": records,
    }

# ============================================================
# RAW THERMAL OBSERVATIONS
# ============================================================

@app.get("/thermal-observations")
def get_raw_thermal_observations(
    limit: Optional[int] = None,
    region: str = Query("jamnagar")
):
    r_data = region_store.get(region, {})
    raw_df = r_data.get("raw_observations_df", pd.DataFrame())
    
    if raw_df.empty:
        return {"count": 0, "observations": []}
        
    records = []
    dataframe = raw_df
    
    if limit is not None:
        if limit < 1:
            raise HTTPException(status_code=400, detail="limit must be >= 1")
        dataframe = dataframe.head(limit)
        
    for _, row in dataframe.iterrows():
        records.append(clean_record(row.to_dict()))
        
    return {
        "count": len(records),
        "observations": records,
    }

# ============================================================
# UNKNOWN SOURCES
# ============================================================

@app.get("/unknown-sources")
def get_unknown_sources(region: str = Query("jamnagar")):
    r_data = region_store.get(region, {})
    unknown_sources_df = r_data.get("unknown_sources_df", pd.DataFrame())
    
    if unknown_sources_df.empty:
        return {"count": 0, "sources": []}
        
    records = []
    for _, row in unknown_sources_df.iterrows():
        records.append(clean_record(row.to_dict()))
        
    return {
        "count": len(records),
        "sources": records,
    }
    
@app.get("/unknown-source-events")
def get_unknown_source_events(region: str = Query("jamnagar")):
    r_data = region_store.get(region, {})
    unknown_events_df = r_data.get("unknown_events_df", pd.DataFrame())
    
    if unknown_events_df.empty:
        return {"count": 0, "events": []}
        
    records = []
    for _, row in unknown_events_df.iterrows():
        records.append(clean_record(row.to_dict()))
        
    return {
        "count": len(records),
        "events": records,
    }

# ============================================================
# FACILITY DAYS
# ============================================================

@app.get("/facility-days")
def get_facility_days(
    facility: Optional[str] = None,
    region: str = Query("jamnagar"),
):
    """
    Return facility-day intelligence records.
    """
    r_data = region_store.get(region, {})
    intelligence_df = r_data.get("intelligence_df", pd.DataFrame())
    b_lookup = r_data.get("baseline_lookup", {})
    s_lookup = r_data.get("spatial_lookup", {})

    if facility:
        normalized = normalize_facility_name(
            facility
        )

        if "facility_name" in dataframe.columns:
            mask = dataframe[
                "facility_name"
            ].apply(
                normalize_facility_name
            ) == normalized

        elif "name" in dataframe.columns:
            mask = dataframe[
                "name"
            ].apply(
                normalize_facility_name
            ) == normalized

        else:
            mask = pd.Series(
                False,
                index=dataframe.index,
            )

        dataframe = dataframe[mask]

    records = []

    for _, row in dataframe.iterrows():

        record = clean_record(
            row.to_dict()
        )

        record = attach_baseline_to_facility_day(
            record,
            b_lookup,
            s_lookup,
        )

        records.append(record)

    return {
        "count": len(records),
        "facility_days": records,
    }


# ============================================================
# INVESTIGATIONS
# ============================================================

@app.get("/investigations")
def get_investigations(region: str = Query("jamnagar")):
    
    r_data = region_store.get(region, {})
    intelligence_df = r_data.get("intelligence_df", pd.DataFrame())
    b_lookup = r_data.get("baseline_lookup", {})
    s_lookup = r_data.get("spatial_lookup", {})

    records = []

    for _, row in intelligence_df.iterrows():

        record = clean_record(
            row.to_dict()
        )

        record = attach_baseline_to_facility_day(
            record,
            b_lookup,
            s_lookup,
        )

        records.append(record)

    return {
        "count": len(records),
        "investigations": records,
    }


# ============================================================
# FACILITIES
# ============================================================

@app.get("/facilities")
def get_facilities(region: str = Query("jamnagar")):

    r_data = region_store.get(region, {})
    intelligence_df = r_data.get("intelligence_df", pd.DataFrame())
    baseline_lookup = r_data.get("baseline_lookup", {})

    facility_column = None

    for candidate in [
        "facility_name",
        "name",
        "source_name",
    ]:
        if candidate in intelligence_df.columns:
            facility_column = candidate
            break

    if facility_column is None:
        return {
            "count": 0,
            "facilities": [],
        }

    facilities = []

    grouped = intelligence_df.groupby(
        facility_column,
        dropna=False,
    )

    for facility_name, group in grouped:

        facility_record = {
            "facility_name": clean_value(
                facility_name
            ),
            "facility_days": len(group),
        }

        # ----------------------------------------------------
        # Baseline
        # ----------------------------------------------------

        facility_key = normalize_facility_name(
            facility_name
        )

        baseline = baseline_lookup.get(
            facility_key,
            {},
        )

        for field in BASELINE_FIELDS:
            facility_record[field] = clean_value(
                baseline.get(field)
            )

        has_metrics = any(
            facility_record.get(field) is not None for field in BASELINE_FIELDS
        )

        facility_record[
            "baseline_available"
        ] = bool(baseline) and has_metrics

        # ----------------------------------------------------
        # Basic historical information
        # ----------------------------------------------------

        if "max_frp_mw" in group.columns:

            frp_values = pd.to_numeric(
                group["max_frp_mw"],
                errors="coerce",
            ).dropna()

            if not frp_values.empty:

                facility_record[
                    "historical_max_frp"
                ] = clean_value(
                    frp_values.max()
                )

                facility_record[
                    "historical_mean_max_frp"
                ] = clean_value(
                    frp_values.mean()
                )

        facilities.append(
            clean_record(
                facility_record
            )
        )

    return {
        "count": len(facilities),
        "facilities": facilities,
    }


# ============================================================
# SUMMARY DASHBOARD
# ============================================================

@app.get("/summary")
def summary():
    high_priority = 0
    if not intelligence_df.empty and "investigation_priority" in intelligence_df.columns:
        high_priority = len(intelligence_df[intelligence_df["investigation_priority"].astype(str).str.upper() == "HIGH"])
    
    return {
        "thermal_observations": len(thermal_df) if not thermal_df.empty else 0,
        "facility_days": len(intelligence_df) if not intelligence_df.empty else 0,
        "facilities": len(baseline_lookup),
        "high_priority": high_priority
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "thermal_data_loaded": not thermal_df.empty,
        "intelligence_data_loaded": not intelligence_df.empty,
        "baseline_data_loaded": not baseline_df.empty,
        "baseline_facilities": len(
            baseline_lookup
        ),
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )