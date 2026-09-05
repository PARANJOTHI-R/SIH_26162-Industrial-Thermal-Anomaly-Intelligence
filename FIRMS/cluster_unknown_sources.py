import os
import argparse
import sys
import pandas as pd
import numpy as np
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

# ============================================================
# CONFIGURATION
# ============================================================
UNKNOWN_SOURCE_RADIUS_KM       = 2.0
UNKNOWN_SOURCE_MAX_GAP_DAYS    = 30
UNKNOWN_SOURCE_MIN_EVENTS      = 3
UNKNOWN_SOURCE_MIN_ACTIVE_DAYS = 3
UNKNOWN_SOURCE_MAX_DIAMETER_KM = 3.0


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def main(region_id: str):
    region = get_region(region_id)
    DATA_DIR             = region["analysis_dir"]
    EVENTS_FILE          = DATA_DIR / "thermal_events.csv"
    CLASS_FILE           = DATA_DIR / "thermal_source_classification_v2.csv"
    OBS_FILE             = DATA_DIR / "thermal_event_observations.csv"
    UNKNOWN_SOURCES_FILE = DATA_DIR / "unknown_thermal_sources.csv"
    UNKNOWN_EVENTS_FILE  = DATA_DIR / "unknown_source_events.csv"

    print("=" * 60)
    print("PHASE 2: UNKNOWN / UNMATCHED THERMAL SOURCE DISCOVERY")
    print("=" * 60)

    # 1. Load Data
    events = pd.read_csv(EVENTS_FILE)
    classification = pd.read_csv(CLASS_FILE)
    obs = pd.read_csv(OBS_FILE)

    # Identify unmatched events
    # We define unmatched as any event not classified as INDUSTRIAL_ASSOCIATED
    classification['is_unmatched'] = classification['source_class_v2'] != 'INDUSTRIAL_ASSOCIATED'
    unmatched_event_ids = classification[classification['is_unmatched']]['event_id'].unique()
    
    unmatched_events = events[events['event_id'].isin(unmatched_event_ids)].copy()
    print(f"Total events: {len(events)}")
    print(f"Unmatched events: {len(unmatched_events)}")

    if len(unmatched_events) == 0:
        print("No unmatched events found.")
        # Create empty outputs
        pd.DataFrame(columns=[
            'source_id', 'source_class', 'centroid_lat', 'centroid_lon',
            'event_count', 'active_days', 'first_observed_date', 'last_observed_date',
            'date_span_days', 'max_frp', 'mean_event_frp', 'median_event_frp',
            'satellite_count', 'satellites', 'nearest_known_facility',
            'nearest_known_facility_distance_km', 'landcover_context', 'osm_context',
            'persistence_class', 'evidence_strength', 'interpretation',
            'event_ids', 'raw_observation_count', 'raw_observation_ids'
        ]).to_csv(UNKNOWN_SOURCES_FILE, index=False)
        pd.DataFrame(columns=[
            'source_id', 'event_id', 'event_date', 'event_start_time', 'event_end_time',
            'event_lat', 'event_lon', 'max_frp', 'observation_count', 'satellites'
        ]).to_csv(UNKNOWN_EVENTS_FILE, index=False)
        return

    # 2. Source Clustering
    unmatched_events['event_date_parsed'] = pd.to_datetime(unmatched_events['event_date'])
    unmatched_events = unmatched_events.sort_values('event_date_parsed').reset_index(drop=True)

    sources = []
    
    for _, event in unmatched_events.iterrows():
        event_lat = event['latitude']
        event_lon = event['longitude']
        event_date = event['event_date_parsed']
        
        assigned = False
        
        # Try to assign to an existing candidate source
        for source in sources:
            # Check maximum gap days
            last_date = source['last_observed_date']
            gap_days = (event_date - last_date).days
            if gap_days > UNKNOWN_SOURCE_MAX_GAP_DAYS:
                continue
                
            # Check spatial distance to centroid
            dist_to_centroid = haversine(source['centroid_lat'], source['centroid_lon'], event_lat, event_lon)
            if dist_to_centroid <= UNKNOWN_SOURCE_RADIUS_KM:
                # Check maximum diameter safeguard
                max_dist = 0
                for e in source['events']:
                    d = haversine(e['latitude'], e['longitude'], event_lat, event_lon)
                    if d > max_dist:
                        max_dist = d
                
                potential_diameter = max(source['max_diameter_km'], max_dist)
                
                if potential_diameter <= UNKNOWN_SOURCE_MAX_DIAMETER_KM:
                    # Valid to add
                    source['events'].append(event)
                    source['last_observed_date'] = max(source['last_observed_date'], event_date)
                    source['max_diameter_km'] = potential_diameter
                    source['centroid_lat'] = sum(e['latitude'] for e in source['events']) / len(source['events'])
                    source['centroid_lon'] = sum(e['longitude'] for e in source['events']) / len(source['events'])
                    assigned = True
                    break
                    
        if not assigned:
            sources.append({
                'centroid_lat': event_lat,
                'centroid_lon': event_lon,
                'first_observed_date': event_date,
                'last_observed_date': event_date,
                'max_diameter_km': 0.0,
                'events': [event]
            })

    # 3. Assess and Format Sources
    candidate_sources = []
    unmatched_source_events = []
    
    def sort_key(s):
        events_list = s['events']
        active_days = len(set(e['event_date'] for e in events_list))
        return (-len(events_list), -active_days, s['first_observed_date'], s['centroid_lat'], s['centroid_lon'])
        
    sources.sort(key=sort_key)
    source_counter = 1
    
    for s in sources:
        events_list = s['events']
        event_count = len(events_list)
        active_dates = set(e['event_date'] for e in events_list)
        active_days = len(active_dates)
        date_span_days = (s['last_observed_date'] - s['first_observed_date']).days + 1
        
        # Determine Persistence Class
        if event_count >= UNKNOWN_SOURCE_MIN_EVENTS and active_days >= UNKNOWN_SOURCE_MIN_ACTIVE_DAYS and date_span_days >= 7:
            persistence_class = "PERSISTENT"
        elif event_count < UNKNOWN_SOURCE_MIN_EVENTS or active_days < UNKNOWN_SOURCE_MIN_ACTIVE_DAYS:
            persistence_class = "TRANSIENT"
        else:
            persistence_class = "INTERMITTENT"
            
        if persistence_class == "TRANSIENT":
            source_id = None 
        else:
            source_id = f"SRC_UNKNOWN_{source_counter:03d}"
            source_counter += 1
            
        max_frp = max(e['max_frp'] for e in events_list)
        mean_event_frp = np.mean([e['max_frp'] for e in events_list])
        median_event_frp = np.median([e['max_frp'] for e in events_list])
        
        all_sats = set()
        for e in events_list:
            all_sats.update(str(e['satellites']).split(','))
        satellites_str = ",".join(sorted(list(all_sats)))
        satellite_count = len(all_sats)
        
        event_ids = [e['event_id'] for e in events_list]
        source_class_df = classification[classification['event_id'].isin(event_ids)]
        
        wc_context = source_class_df['worldcover_context'].mode().iloc[0] if len(source_class_df) > 0 else "UNKNOWN"
        
        nearest_known_facility = None
        nearest_distance = None
        if len(source_class_df) > 0 and source_class_df['name'].notna().any():
            names = [n for n in source_class_df['name'].dropna().tolist() if str(n).strip() != "" and str(n).strip() != "nan"]
            if names:
                nearest_known_facility = pd.Series(names).mode().iloc[0]
                nearest_distance = source_class_df[source_class_df['name'] == nearest_known_facility]['distance_km'].min()
            
        osm_types = source_class_df['osm_type'].dropna().unique()
        osm_context = ";".join(str(t) for t in osm_types if str(t) != 'nan') if len(osm_types) > 0 else "None"
        
        raw_obs = obs[obs['event_id'].isin(event_ids)]
        raw_observation_count = len(raw_obs)
        raw_observation_ids = ",".join(raw_obs['original_observation_id'].tolist())
        
        if persistence_class == "PERSISTENT" and wc_context == "BUILT_UP" and nearest_known_facility is not None:
            evidence_strength = "VERY_HIGH"
        elif persistence_class == "PERSISTENT":
            evidence_strength = "HIGH"
        elif persistence_class == "INTERMITTENT":
            evidence_strength = "MEDIUM"
        else:
            evidence_strength = "LOW"
            
        if persistence_class == "TRANSIENT":
            interpretation = "Transient unmatched thermal event."
        else:
            interpretation = f"{persistence_class.capitalize()} unmatched thermal source with {event_count} events across {active_days} active days."
            if nearest_known_facility:
                interpretation += f" Located near {nearest_known_facility} ({nearest_distance:.1f} km). Candidate industrial-associated source."
            elif wc_context == "BUILT_UP":
                interpretation += " Context suggests built-up/infrastructure."

        if source_id is not None:
            candidate_sources.append({
                'source_id': source_id,
                'source_class': 'UNMATCHED',
                'centroid_lat': round(s['centroid_lat'], 6),
                'centroid_lon': round(s['centroid_lon'], 6),
                'event_count': event_count,
                'active_days': active_days,
                'first_observed_date': s['first_observed_date'].strftime('%Y-%m-%d'),
                'last_observed_date': s['last_observed_date'].strftime('%Y-%m-%d'),
                'date_span_days': date_span_days,
                'max_frp': round(max_frp, 2),
                'mean_event_frp': round(mean_event_frp, 2),
                'median_event_frp': round(median_event_frp, 2),
                'satellite_count': satellite_count,
                'satellites': satellites_str,
                'nearest_known_facility': nearest_known_facility,
                'nearest_known_facility_distance_km': round(nearest_distance, 3) if nearest_distance is not None else None,
                'landcover_context': wc_context,
                'osm_context': osm_context,
                'persistence_class': persistence_class,
                'evidence_strength': evidence_strength,
                'interpretation': interpretation,
                'event_ids': ";".join(event_ids),
                'raw_observation_count': raw_observation_count,
                'raw_observation_ids': raw_observation_ids
            })
            
        for e in events_list:
            unmatched_source_events.append({
                'source_id': source_id if source_id else "UNMATCHED_TRANSIENT_EVENT",
                'event_id': e['event_id'],
                'event_date': e['event_date'],
                'event_start_time': e['event_start_time'],
                'event_end_time': e['event_end_time'],
                'event_lat': e['latitude'],
                'event_lon': e['longitude'],
                'max_frp': e['max_frp'],
                'observation_count': e['observation_count'],
                'satellites': e['satellites']
            })

    print(f"Discovered candidate sources: {len(candidate_sources)}")
    print(f"Transient unmatched sources: {len(sources) - len(candidate_sources)}")
    
    if len(candidate_sources) > 0:
        pd.DataFrame(candidate_sources).to_csv(UNKNOWN_SOURCES_FILE, index=False)
    else:
        pd.DataFrame(columns=[
            'source_id', 'source_class', 'centroid_lat', 'centroid_lon',
            'event_count', 'active_days', 'first_observed_date', 'last_observed_date',
            'date_span_days', 'max_frp', 'mean_event_frp', 'median_event_frp',
            'satellite_count', 'satellites', 'nearest_known_facility',
            'nearest_known_facility_distance_km', 'landcover_context', 'osm_context',
            'persistence_class', 'evidence_strength', 'interpretation',
            'event_ids', 'raw_observation_count', 'raw_observation_ids'
        ]).to_csv(UNKNOWN_SOURCES_FILE, index=False)
        
    if len(unmatched_source_events) > 0:
        pd.DataFrame(unmatched_source_events).to_csv(UNKNOWN_EVENTS_FILE, index=False)
    else:
        pd.DataFrame(columns=[
            'source_id', 'event_id', 'event_date', 'event_start_time', 'event_end_time',
            'event_lat', 'event_lon', 'max_frp', 'observation_count', 'satellites'
        ]).to_csv(UNKNOWN_EVENTS_FILE, index=False)
    
    print("Files written successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unknown source clustering")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    main(args.region)
