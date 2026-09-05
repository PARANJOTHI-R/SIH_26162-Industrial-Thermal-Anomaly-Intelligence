"""
sample_worldcover.py  --region <region_id>

Samples ESA WorldCover land-cover class at each thermal event centroid.
Works for any configured region.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.regions import get_region

WORLDCOVER_CLASSES = {
    10: "TREE_COVER",
    20: "SHRUBLAND",
    30: "GRASSLAND",
    40: "CROPLAND",
    50: "BUILT_UP",
    60: "BARE_SPARSE_VEGETATION",
    70: "SNOW_ICE",
    80: "PERMANENT_WATER_BODIES",
    90: "HERBACEOUS_WETLAND",
    95: "MANGROVES",
    100: "MOSS_LICHEN",
}


def run_sampling(region_id: str):
    region = get_region(region_id)

    FIRMS_FILE    = region["analysis_dir"] / "thermal_events.csv"
    WC_FILE       = region["landcover_dir"] / region["worldcover_tif_file"]
    OUTPUT_FILE   = region["analysis_dir"] / "thermal_worldcover_context.csv"

    print("=" * 60)
    print(f"WORLD COVER SAMPLING  [{region_id.upper()}]")
    print("=" * 60)

    firms = pd.read_csv(FIRMS_FILE)
    print(f"Events: {len(firms)}")

    if not WC_FILE.exists():
        print(f"WARNING: WorldCover file not found: {WC_FILE}")
        print("Writing empty context file.")
        firms["worldcover_class_code"] = None
        firms["worldcover_class"] = "UNKNOWN"
        firms[["event_id","latitude","longitude","event_date",
               "event_start_time","max_frp","observation_count",
               "worldcover_class_code","worldcover_class"]].to_csv(OUTPUT_FILE, index=False)
        return

    print(f"Opening WorldCover raster: {WC_FILE}")
    raster = rasterio.open(WC_FILE)

    results = []
    for _, row in firms.iterrows():
        lon = row["longitude"]
        lat = row["latitude"]
        try:
            value = next(raster.sample([(lon, lat)]))[0]
            class_code = int(value)
            class_name = WORLDCOVER_CLASSES.get(class_code, "UNKNOWN")
        except Exception:
            class_code = None
            class_name = "UNKNOWN"

        results.append({
            "event_id":            row.get("event_id"),
            "latitude":            lat,
            "longitude":           lon,
            "event_date":          row.get("event_date"),
            "event_start_time":    row.get("event_start_time"),
            "max_frp":             row.get("max_frp"),
            "observation_count":   row.get("observation_count"),
            "worldcover_class_code": class_code,
            "worldcover_class":    class_name,
        })

    raster.close()
    result = pd.DataFrame(results)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print()
    print(result["worldcover_class"].value_counts().to_string())
    print(f"\nSaved: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WorldCover sampling")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    run_sampling(args.region)