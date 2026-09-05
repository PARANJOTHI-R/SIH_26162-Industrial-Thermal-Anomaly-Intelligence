"""
cluster_thermal_events.py  --region <region_id>

Phase 1: Thermal Event Clustering
Clusters raw FIRMS observations into deduplicated thermal events.
Works for any configured region.
"""

import argparse
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import math

# Add project root to path so config is importable when run from any dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

# ============================================================
# CLUSTERING PARAMETERS  (unchanged from Phase 1)
# ============================================================

EVENT_SPATIAL_KM      = 1.0
EVENT_TEMPORAL_MINUTES = 120
SAME_DAY_ONLY         = True


# ============================================================
# HELPERS
# ============================================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ============================================================
# CLUSTERING ALGORITHM
# ============================================================

def process_clustering(region_id: str):
    region = get_region(region_id)

    INPUT_FILE    = region["firms_dir"] / region["firms_combined_file"]
    OUTPUT_DIR    = region["analysis_dir"]
    OUTPUT_EVENTS = OUTPUT_DIR / "thermal_events.csv"
    OUTPUT_OBS    = OUTPUT_DIR / "thermal_event_observations.csv"

    print("=" * 70)
    print(f"PHASE 1: THERMAL EVENT CLUSTERING  [{region_id.upper()}]")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    print(f"Loading raw observations from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    raw_count_before = len(df)
    print(f"Raw observations loaded: {raw_count_before}")

    df['acq_time_str'] = df['acq_time'].astype(int).astype(str).str.zfill(4)
    df['datetime'] = pd.to_datetime(
        df['acq_date'] + ' ' +
        df['acq_time_str'].str[:2] + ':' +
        df['acq_time_str'].str[2:]
    )

    df['original_observation_id'] = [
        "OBS_" + str(i).zfill(5) for i in range(len(df))
    ]

    grouped = df.groupby('acq_date')

    events_data = []
    observations_data = []
    event_counter = 1

    for date, group in grouped:
        group = group.sort_values(
            ['datetime', 'satellite', 'latitude', 'longitude']
        ).reset_index(drop=True)

        n = len(group)
        visited = [False] * n

        for i in range(n):
            if visited[i]:
                continue

            cluster_indices = [i]
            visited[i] = True
            queue = [i]

            while queue:
                curr = queue.pop(0)
                curr_row = group.iloc[curr]

                for j in range(n):
                    if not visited[j]:
                        target_row = group.iloc[j]
                        time_diff_mins = abs(
                            (target_row['datetime'] - curr_row['datetime'])
                            .total_seconds() / 60.0
                        )
                        if time_diff_mins <= EVENT_TEMPORAL_MINUTES:
                            dist_km = haversine(
                                curr_row['latitude'],  curr_row['longitude'],
                                target_row['latitude'], target_row['longitude']
                            )
                            if dist_km <= EVENT_SPATIAL_KM:
                                visited[j] = True
                                cluster_indices.append(j)
                                queue.append(j)

            cluster = group.iloc[cluster_indices]

            date_str = date.replace("-", "")
            event_id = f"EVT_{date_str}_{str(event_counter).zfill(4)}"
            event_counter += 1

            event_start_time = cluster['datetime'].min().strftime('%H%M')
            event_end_time   = cluster['datetime'].max().strftime('%H%M')

            lat_mean  = cluster['latitude'].mean()
            lon_mean  = cluster['longitude'].mean()
            max_frp   = cluster['frp'].max()
            mean_frp  = cluster['frp'].mean()
            total_frp = cluster['frp'].sum()

            observation_count    = len(cluster)
            satellites_present   = cluster['satellite'].unique()
            satellite_count      = len(satellites_present)
            satellites_str       = ",".join(sorted(satellites_present))

            if observation_count > 1 and satellite_count > 1:
                cluster_confidence = "HIGH"
            elif observation_count > 1:
                cluster_confidence = "MEDIUM"
            else:
                cluster_confidence = "LOW"

            events_data.append({
                'event_id':               event_id,
                'region_id':              region_id,
                'event_date':             date,
                'event_start_time':       event_start_time,
                'event_end_time':         event_end_time,
                'latitude':               round(lat_mean, 6),
                'longitude':              round(lon_mean, 6),
                'max_frp':                round(max_frp, 2),
                'mean_frp':               round(mean_frp, 2),
                'total_frp':              round(total_frp, 2),
                'observation_count':      observation_count,
                'satellite_count':        satellite_count,
                'satellites':             satellites_str,
                'event_cluster_confidence': cluster_confidence,
                'event_cluster_method':   'spatial_temporal_bfs',
            })

            for _, obs_row in cluster.iterrows():
                observations_data.append({
                    'event_id':               event_id,
                    'region_id':              region_id,
                    'original_observation_id': obs_row['original_observation_id'],
                    'latitude':               obs_row['latitude'],
                    'longitude':              obs_row['longitude'],
                    'acq_date':               obs_row['acq_date'],
                    'acq_time':               obs_row['acq_time'],
                    'satellite':              obs_row['satellite'],
                    'frp':                    obs_row['frp'],
                    'confidence':             obs_row.get('confidence'),
                    'instrument':             obs_row.get('instrument'),
                    'daynight':               obs_row.get('daynight'),
                })

    events_df = pd.DataFrame(events_data)
    obs_df    = pd.DataFrame(observations_data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    events_df.to_csv(OUTPUT_EVENTS, index=False)
    obs_df.to_csv(OUTPUT_OBS, index=False)

    print(f"Events generated:    {len(events_df)}")
    print(f"Observations mapped: {len(obs_df)}")
    if len(df) != len(obs_df):
        print(f"WARNING: mapped ({len(obs_df)}) != raw ({len(df)})")

    cross_sat = len(events_df[events_df['satellite_count'] > 1])
    print(f"Cross-satellite merged events: {cross_sat}")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 1 thermal event clustering"
    )
    parser.add_argument(
        "--region", required=True,
        help="Region ID (e.g. jamnagar, thoothukudi)"
    )
    args = parser.parse_args()
    process_clustering(args.region)
