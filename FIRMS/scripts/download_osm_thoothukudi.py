import requests
import json
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.regions import get_region

region = get_region("thoothukudi")
bbox = region["bbox"]  # [west, south, east, north]
OUTPUT_DIR = region["industry_dir"]

OVERPASS = "https://overpass.kumi.systems/api/interpreter"

query = (
    "[out:json][timeout:120];"
    "("
    f'way["industrial"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'way["landuse"="industrial"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'way["power"="plant"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'way["man_made"="works"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'way["man_made"="storage_tank"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'way["landuse"="port"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'relation["industrial"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'relation["landuse"="industrial"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    f'relation["power"="plant"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});'
    ");"
    "out body;>;out skel qt;"
)

print("Querying Overpass API (GET)...")
r = requests.get(
    OVERPASS,
    params={"data": query},
    headers={"User-Agent": "SIH26162-ThermalIntelligence/1.0 (research project)"},
    timeout=180
)
print(f"Status: {r.status_code}")

if r.status_code != 200:
    print(r.text[:500])
    sys.exit(1)

data = r.json()
elements = data.get("elements", [])
print(f"Elements returned: {len(elements)}")

nodes = {e["id"]: e for e in elements if e["type"] == "node"}

rows = []
for el in elements:
    if el["type"] not in ("way", "relation"):
        continue
    tags = el.get("tags", {})
    lat_vals, lon_vals = [], []
    if el["type"] == "way":
        for nid in el.get("nodes", []):
            if nid in nodes:
                lat_vals.append(nodes[nid]["lat"])
                lon_vals.append(nodes[nid]["lon"])
    if lat_vals:
        centroid_lat = sum(lat_vals) / len(lat_vals)
        centroid_lon = sum(lon_vals) / len(lon_vals)
    else:
        centroid_lat = None
        centroid_lon = None

    rows.append({
        "osm_type":    el["type"],
        "osm_id":      el["id"],
        "name":        tags.get("name", ""),
        "industrial":  tags.get("industrial", ""),
        "landuse":     tags.get("landuse", ""),
        "power":       tags.get("power", ""),
        "man_made":    tags.get("man_made", ""),
        "operator":    tags.get("operator", ""),
        "centroid_lat": centroid_lat,
        "centroid_lon": centroid_lon,
        "geometry_wkt": f"POINT({centroid_lon} {centroid_lat})" if centroid_lat else "",
    })

df = pd.DataFrame(rows)
print(f"Features: {len(df)}")
if len(df) > 0:
    print(df[["osm_type","name","industrial","landuse","power"]].head(15).to_string(index=False))

csv_path = OUTPUT_DIR / region["osm_csv_file"]
df.to_csv(csv_path, index=False)
print(f"\nSaved CSV: {csv_path}")

# Save GeoJSON (centroid points)
features = []
for _, row in df.iterrows():
    if row["centroid_lat"] is not None:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["centroid_lon"], row["centroid_lat"]]
            },
            "properties": {
                k: (None if (v != v) else v)
                for k, v in row.items()
                if k not in ("centroid_lat", "centroid_lon", "geometry_wkt")
            }
        })

geojson_path = OUTPUT_DIR / region["osm_geojson_file"]
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f)
print(f"Saved GeoJSON: {geojson_path}")
print("Done.")
