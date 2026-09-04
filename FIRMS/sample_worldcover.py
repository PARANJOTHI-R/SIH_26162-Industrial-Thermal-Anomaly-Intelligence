from pathlib import Path

import pandas as pd
import rasterio


FIRMS_FILE = Path(
    "SIH26162_DATA/01_FIRMS/"
    "jamnagar_viirs_combined_historical.csv"
)

WORLDCOVER_FILE = Path(
    "SIH26162_DATA/03_LANDCOVER/"
    "ESA_WorldCover_10m_2021_v200_N21E069_Map.tif"
)

OUTPUT_FILE = Path(
    "SIH26162_DATA/analysis/"
    "thermal_worldcover_context.csv"
)


# ESA WorldCover class codes
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


print("=" * 60)
print("WORLD COVER SAMPLING")
print("=" * 60)

print("Loading FIRMS observations...")
firms = pd.read_csv(FIRMS_FILE)

print(f"FIRMS observations: {len(firms)}")

print("Opening WorldCover raster...")
raster = rasterio.open(WORLDCOVER_FILE)

print(f"CRS: {raster.crs}")
print(f"Bounds: {raster.bounds}")
print(f"Resolution: {raster.res}")

results = []

# ---------------------------------------------------------
# Sample WorldCover at each FIRMS point
# ---------------------------------------------------------

for _, row in firms.iterrows():

    longitude = row["longitude"]
    latitude = row["latitude"]

    try:
        value = next(
            raster.sample(
                [(longitude, latitude)]
            )
        )[0]

        class_code = int(value)

        class_name = WORLDCOVER_CLASSES.get(
            class_code,
            "UNKNOWN"
        )

    except Exception:
        class_code = None
        class_name = "UNKNOWN"

    results.append({
        "latitude": latitude,
        "longitude": longitude,
        "acq_date": row["acq_date"],
        "acq_time": row["acq_time"],
        "satellite": row["satellite"],
        "frp": row["frp"],
        "confidence": row["confidence"],
        "daynight": row["daynight"],

        "worldcover_class_code": class_code,
        "worldcover_class": class_name,
    })


raster.close()

result = pd.DataFrame(results)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 60)
print("WORLD COVER SUMMARY")
print("=" * 60)

print(
    result["worldcover_class"]
    .value_counts()
    .to_string()
)

print()
print("Saved:")
print(OUTPUT_FILE.resolve())