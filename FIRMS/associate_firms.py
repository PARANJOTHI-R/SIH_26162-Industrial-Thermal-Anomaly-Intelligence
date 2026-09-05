"""
associate_firms.py  --region <region_id>

OSM spatial association for thermal events.
Works for any configured region.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

MAX_DISTANCE_KM = 5.0


def run_association(region_id: str):
    region = get_region(region_id)

    FIRMS_FILE  = region["analysis_dir"] / "thermal_events.csv"
    OSM_FILE    = region["industry_dir"] / region["osm_geojson_file"]
    OUTPUT_DIR  = region["analysis_dir"]
    OUTPUT_FILE = OUTPUT_DIR / "historical_thermal_osm_association.csv"
    UTM_CRS     = region["utm_crs"]

    print("=" * 70)
    print(f"OSM SPATIAL ASSOCIATION  [{region_id.upper()}]")
    print("=" * 70)

    print("Loading thermal events...")
    firms = pd.read_csv(FIRMS_FILE)
    print(f"Events: {len(firms)}")

    firms_gdf = gpd.GeoDataFrame(
        firms.copy(),
        geometry=gpd.points_from_xy(firms["longitude"], firms["latitude"]),
        crs="EPSG:4326"
    )

    print("Loading OSM industrial features...")
    osm = gpd.read_file(OSM_FILE)
    print(f"OSM features: {len(osm)}")
    if osm.crs is None:
        osm = osm.set_crs("EPSG:4326")

    firms_metric = firms_gdf.to_crs(UTM_CRS)
    osm_metric   = osm.to_crs(UTM_CRS)

    print("Calculating spatial associations...")
    results = []

    for idx, fire in firms_metric.iterrows():
        fire_geom = fire.geometry
        intersecting = osm_metric[osm_metric.geometry.intersects(fire_geom)]

        if len(intersecting) > 0:
            intersecting = intersecting.copy()
            intersecting["distance_m"] = intersecting.geometry.distance(fire_geom)
            match = intersecting.sort_values("distance_m").iloc[0]
            distance_km = match["distance_m"] / 1000.0
            association_type = "OSM_FEATURE_INTERSECTION"
            association_confidence = "HIGH"
        else:
            distances = osm_metric.geometry.distance(fire_geom)
            nearest_idx = distances.idxmin()
            nearest = osm_metric.loc[nearest_idx]
            distance_km = distances.loc[nearest_idx] / 1000.0

            if distance_km <= MAX_DISTANCE_KM:
                match = nearest
                association_type = "NEARBY_OSM_INDUSTRIAL_FEATURE"
                association_confidence = "SCREENING"
            else:
                match = None
                association_type = "NO_NEARBY_OSM_FEATURE"
                association_confidence = "NONE"

        row = {
            "event_id":              fire.get("event_id"),
            "region_id":             region_id,
            "latitude":              fire["latitude"],
            "longitude":             fire["longitude"],
            "acq_date":              fire["event_date"],
            "acq_time":              fire["event_start_time"],
            "observation_count":     fire["observation_count"],
            "satellite_count":       fire["satellite_count"],
            "satellites":            fire["satellites"],
            "frp":                   fire["max_frp"],
            "association_type":      association_type,
            "association_confidence": association_confidence,
        }

        if match is not None:
            row["osm_type"]   = match.get("osm_type")
            row["osm_id"]     = match.get("osm_id")
            row["name"]       = match.get("name")
            row["industrial"] = match.get("industrial")
            row["landuse"]    = match.get("landuse")
            row["power"]      = match.get("power")
            row["man_made"]   = match.get("man_made")
            row["distance_km"] = round(distance_km, 3)
        else:
            row["osm_type"]   = None
            row["osm_id"]     = None
            row["name"]       = None
            row["industrial"] = None
            row["landuse"]    = None
            row["power"]      = None
            row["man_made"]   = None
            row["distance_km"] = None

        results.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nFIRMS events           : {len(firms)}")
    print(f"OSM features           : {len(osm)}")
    print("\nAssociation types:")
    print(results_df["association_type"].value_counts().to_string())
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSM spatial association")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    run_association(args.region)