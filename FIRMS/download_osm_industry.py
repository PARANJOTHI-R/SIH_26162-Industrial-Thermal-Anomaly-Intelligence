import requests
import pandas as pd
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
import geopandas as gpd


# ============================================================
# CONFIGURATION
# ============================================================

SOUTH = 22.20
WEST = 69.70
NORTH = 22.50
EAST = 70.00

# Try these in order
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

OUTPUT_DIR = Path("SIH26162_DATA/02_INDUSTRY")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GEOJSON_FILE = OUTPUT_DIR / "jamnagar_osm_industrial_features.geojson"
CSV_FILE = OUTPUT_DIR / "jamnagar_osm_industrial_features.csv"


# ============================================================
# OVERPASS QUERY
# ============================================================

query = f"""
[out:json][timeout:120];

(
  way["landuse"="industrial"]({SOUTH},{WEST},{NORTH},{EAST});
  way["industrial"]({SOUTH},{WEST},{NORTH},{EAST});
  way["man_made"="works"]({SOUTH},{WEST},{NORTH},{EAST});
  way["power"="plant"]({SOUTH},{WEST},{NORTH},{EAST});
  way["power"="substation"]({SOUTH},{WEST},{NORTH},{EAST});
  way["man_made"="storage_tank"]({SOUTH},{WEST},{NORTH},{EAST});
  way["man_made"="silo"]({SOUTH},{WEST},{NORTH},{EAST});

  node["industrial"]({SOUTH},{WEST},{NORTH},{EAST});
  node["power"="plant"]({SOUTH},{WEST},{NORTH},{EAST});
  node["man_made"="works"]({SOUTH},{WEST},{NORTH},{EAST});
);

out body geom;
"""


# ============================================================
# DOWNLOAD
# ============================================================

headers = {
    "User-Agent": "SIH26162-Thermal-Source-Research/1.0"
}

data = None

for overpass_url in OVERPASS_URLS:

    print()
    print("Trying:", overpass_url)

    try:

        response = requests.post(
            overpass_url,
            data={"data": query},
            headers=headers,
            timeout=180
        )

        print("HTTP status:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            print("Successfully received Overpass data.")
            break

        else:
            print(response.text[:500])

    except requests.RequestException as e:

        print("Request error:", e)


if data is None:
    raise SystemExit(
        "\nAll Overpass endpoints failed. "
        "No OSM data downloaded."
    )


# ============================================================
# EXTRACT ELEMENTS
# ============================================================

elements = data.get("elements", [])

print("OSM elements returned:", len(elements))


# ============================================================
# CONVERT OSM ELEMENTS TO GEOMETRIES
# ============================================================

records = []

for element in elements:

    osm_type = element.get("type")
    osm_id = element.get("id")

    tags = element.get("tags", {})

    name = tags.get("name", "")
    industrial_type = tags.get("industrial", "")
    landuse = tags.get("landuse", "")
    man_made = tags.get("man_made", "")
    power = tags.get("power", "")

    geometry = None

    # --------------------------------------------------------
    # NODE
    # --------------------------------------------------------

    if osm_type == "node":

        lat = element.get("lat")
        lon = element.get("lon")

        if lat is not None and lon is not None:
            geometry = Point(lon, lat)

    # --------------------------------------------------------
    # WAY
    # --------------------------------------------------------

    elif osm_type == "way":

        points = []

        for node in element.get("geometry", []):

            lat = node.get("lat")
            lon = node.get("lon")

            if lat is not None and lon is not None:
                points.append((lon, lat))

        if len(points) >= 3:

            if points[0] == points[-1]:

                try:
                    polygon = Polygon(points)

                    if polygon.is_valid and not polygon.is_empty:
                        geometry = polygon
                    else:
                        geometry = polygon.buffer(0)

                except Exception:
                    geometry = None

        elif len(points) >= 2:

            geometry = LineString(points)

    if geometry is None:
        continue

    records.append({
        "osm_type": osm_type,
        "osm_id": osm_id,
        "name": name,
        "industrial": industrial_type,
        "landuse": landuse,
        "man_made": man_made,
        "power": power,
        "geometry": geometry
    })


# ============================================================
# CREATE GEODATAFRAME
# ============================================================

if not records:
    raise SystemExit(
        "Overpass returned data, but no usable geometries were found."
    )

gdf = gpd.GeoDataFrame(
    records,
    geometry="geometry",
    crs="EPSG:4326"
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

gdf = gdf.drop_duplicates(
    subset=["osm_type", "osm_id"]
).reset_index(drop=True)


# ============================================================
# SAVE GEOJSON
# ============================================================

gdf.to_file(
    GEOJSON_FILE,
    driver="GeoJSON"
)


# ============================================================
# SAVE CSV
# ============================================================

csv_gdf = gdf.copy()

csv_gdf["geometry_wkt"] = csv_gdf.geometry.to_wkt()

csv_gdf = csv_gdf.drop(
    columns=["geometry"]
)

csv_gdf.to_csv(
    CSV_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("========================================")
print("OSM INDUSTRY DOWNLOAD COMPLETE")
print("========================================")

print("Total usable features:", len(gdf))

print()
print("Feature types:")
print(gdf["osm_type"].value_counts())

print()
print("Industrial tags:")
print(
    gdf["industrial"]
    .replace("", "NONE")
    .value_counts()
    .head(20)
)

print()
print("Landuse tags:")
print(
    gdf["landuse"]
    .replace("", "NONE")
    .value_counts()
    .head(20)
)

print()
print("Power tags:")
print(
    gdf["power"]
    .replace("", "NONE")
    .value_counts()
    .head(20)
)

print()
print("Named features:")
print(
    gdf[gdf["name"] != ""]["name"]
    .value_counts()
    .head(30)
)

print()
print("Saved:")
print(GEOJSON_FILE)
print(CSV_FILE)