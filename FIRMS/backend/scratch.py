import pandas as pd
import numpy as np
import math

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

intelligence_df = pd.read_csv("data/thermal_source_behavior_intelligence.csv")
thermal_df = pd.read_csv("data/thermal_source_classification_v2.csv")

def normalize_facility_name(value):
    if pd.isna(value) or value is None: return ""
    return " ".join(str(value).strip().upper().split())

thermal_df["facility_key"] = thermal_df["name"].apply(normalize_facility_name)
intelligence_df["facility_key"] = intelligence_df.apply(lambda r: normalize_facility_name(r.get("facility_name", r.get("name"))), axis=1)

def build_spatial_lookup():
    lookup = {}
    for _, row in intelligence_df.iterrows():
        fac_key = row["facility_key"]
        acq_date = row["acq_date"]
        
        key = f"{fac_key}|{acq_date}"
        
        if not fac_key or "UNKNOWN" in fac_key:
            lookup[key] = {"spatial_behavior_state": "INSUFFICIENT_HISTORY", "spatial_behavior_confidence": "LOW"}
            continue
            
        fac_thermal = thermal_df[thermal_df["facility_key"] == fac_key].copy()
        
        hist_obs = fac_thermal[fac_thermal["acq_date"] < acq_date]
        curr_obs = fac_thermal[fac_thermal["acq_date"] == acq_date]
        
        if len(hist_obs) < 10 or len(curr_obs) == 0:
            lookup[key] = {"spatial_behavior_state": "INSUFFICIENT_HISTORY", "spatial_behavior_confidence": "LOW"}
            continue
            
        # 1. Historical Centroid
        daily_centroids = hist_obs.groupby("acq_date")[["latitude", "longitude"]].median()
        hist_centroid_lat = daily_centroids["latitude"].median()
        hist_centroid_lon = daily_centroids["longitude"].median()
        
        # 2. Historical Radius (P90 distance to ALL historical obs)
        hist_obs["dist_to_centroid"] = haversine_vectorized(
            hist_obs["latitude"].values, hist_obs["longitude"].values,
            hist_centroid_lat, hist_centroid_lon
        )
        hist_radius = np.percentile(hist_obs["dist_to_centroid"], 90)
        
        # 3. Current Centroid
        curr_centroid_lat = curr_obs["latitude"].median()
        curr_centroid_lon = curr_obs["longitude"].median()
        
        # 4. Current Radius
        curr_obs["dist_to_centroid"] = haversine_vectorized(
            curr_obs["latitude"].values, curr_obs["longitude"].values,
            curr_centroid_lat, curr_centroid_lon
        )
        if len(curr_obs) > 1:
            curr_radius = np.percentile(curr_obs["dist_to_centroid"], 90)
        else:
            curr_radius = 0.0
            
        # 5. Centroid Shift
        shift_km = haversine(curr_centroid_lat, curr_centroid_lon, hist_centroid_lat, hist_centroid_lon)
        
        # 6. Expansion Ratio
        # Floor radius to 0.375 km (VIIRS resolution ~ 375m) to avoid div by zero / extreme ratios
        MIN_RADIUS = 0.375 
        hist_r_adj = max(hist_radius, MIN_RADIUS)
        curr_r_adj = max(curr_radius, MIN_RADIUS)
        exp_ratio = curr_r_adj / hist_r_adj
        
        shift_ratio = shift_km / hist_r_adj
        
        # Scoring logic
        # 0-39 normal, 40-69 watch, 70-100 unusual
        shift_score = min(shift_ratio * 30, 50)  # shift ratio of 1.66 -> max 50 points
        exp_score = min(max(exp_ratio - 1, 0) * 30, 50)  # exp ratio of 2.66 -> max 50 points
        
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

lookup = build_spatial_lookup()
k = "RELIANCE REFINERY|2026-06-09"
print(k, lookup.get(k))

k2 = "RELIANCE REFINERY|2026-08-24"
print(k2, lookup.get(k2))
