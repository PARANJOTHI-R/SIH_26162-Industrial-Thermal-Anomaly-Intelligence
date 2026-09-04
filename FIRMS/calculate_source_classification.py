import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point

FIRMS_FILE = "SIH26162_DATA/01_FIRMS/jamnagar_viirs_combined_historical.csv"
OSM_FILE = "SIH26162_DATA/02_INDUSTRY/jamnagar_osm_industrial_features.csv"
OUTPUT_FILE = "SIH26162_DATA/analysis/thermal_source_classification.csv"

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

# Distance used only for contextual evidence.
# It does NOT mean the hotspot is an industrial fire.
NEARBY_RADIUS_M = 1000

# OSM feature types that provide stronger industrial evidence.
STRONG_INDUSTRIAL_TYPES = {
    "refinery",
    "oil",
    "chemical",
    "steelmaking",
    "works",
    "power_plant",
}

# ---------------------------------------------------------
# Load FIRMS
# ---------------------------------------------------------

print("Loading FIRMS observations...")
firms = pd.read_csv(FIRMS_FILE)

print(f"FIRMS observations: {len(firms)}")

firms["geometry"] = [
    Point(lon, lat)
    for lon, lat in zip(firms["longitude"], firms["latitude"])
]

firms_gdf = gpd.GeoDataFrame(
    firms,
    geometry="geometry",
    crs="EPSG:4326"
)

# ---------------------------------------------------------
# Load OSM
# ---------------------------------------------------------

print("Loading OSM industrial features...")
osm = pd.read_csv(OSM_FILE)

osm["geometry"] = osm["geometry_wkt"].apply(wkt.loads)

osm_gdf = gpd.GeoDataFrame(
    osm,
    geometry="geometry",
    crs="EPSG:4326"
)

print(f"OSM features: {len(osm_gdf)}")

# Project to metric CRS for distance calculations.
firms_m = firms_gdf.to_crs("EPSG:32642")
osm_m = osm_gdf.to_crs("EPSG:32642")

# ---------------------------------------------------------
# Helper: determine industrial strength
# ---------------------------------------------------------

def industrial_strength(row):

    industrial = str(row.get("industrial", "")).lower()
    man_made = str(row.get("man_made", "")).lower()
    power = str(row.get("power", "")).lower()
    landuse = str(row.get("landuse", "")).lower()
    name = str(row.get("name", "")).lower()

    text = " ".join([
        industrial,
        man_made,
        power,
        landuse,
        name
    ])

    if any(x in text for x in STRONG_INDUSTRIAL_TYPES):
        return "STRONG"

    if industrial not in ("", "nan"):
        return "MODERATE"

    if landuse == "industrial":
        return "MODERATE"

    if power in ("plant", "substation"):
        return "WEAK"

    if man_made == "works":
        return "MODERATE"

    return "WEAK"


osm_m["industrial_strength"] = osm_m.apply(
    industrial_strength,
    axis=1
)

# ---------------------------------------------------------
# Classify each thermal observation
# ---------------------------------------------------------

results = []

for idx, fire in firms_m.iterrows():

    point = fire.geometry

    # Features intersecting the FIRMS point
    intersections = osm_m[osm_m.geometry.intersects(point)]

    # Features within 1 km
    distances = osm_m.geometry.distance(point)

    nearby = osm_m[distances <= NEARBY_RADIUS_M].copy()
    nearby["distance_m"] = distances[distances <= NEARBY_RADIUS_M]

    strong = nearby[
        nearby["industrial_strength"] == "STRONG"
    ]

    moderate = nearby[
        nearby["industrial_strength"] == "MODERATE"
    ]

    # -----------------------------------------------------
    # Evidence score
    # -----------------------------------------------------

    score = 0
    evidence = []

    if len(intersections) > 0:
        score += 3
        evidence.append("thermal_point_intersects_osm_feature")

    if len(strong) > 0:
        score += 3
        evidence.append("strong_industrial_feature_nearby")

    if len(moderate) > 0:
        score += 2
        evidence.append("industrial_feature_nearby")

    # -----------------------------------------------------
    # Classification
    # -----------------------------------------------------

    if score >= 5:
        source_class = "INDUSTRIAL_ASSOCIATED"
        confidence = "HIGH"

    elif score >= 2:
        source_class = "INDUSTRIAL_ASSOCIATED"
        confidence = "MEDIUM"

    else:
        source_class = "UNKNOWN"
        confidence = "LOW"

    # -----------------------------------------------------
    # Best nearby feature
    # -----------------------------------------------------

    if len(nearby) > 0:

        best = nearby.sort_values("distance_m").iloc[0]

        nearest_name = best["name"]
        nearest_distance = best["distance_m"]
        nearest_type = best["industrial_strength"]

    else:

        nearest_name = None
        nearest_distance = None
        nearest_type = None

    results.append({
        "latitude": fire["latitude"],
        "longitude": fire["longitude"],
        "acq_date": fire["acq_date"],
        "acq_time": fire["acq_time"],
        "satellite": fire["satellite"],
        "frp": fire["frp"],
        "confidence": fire["confidence"],
        "daynight": fire["daynight"],

        "source_class": source_class,
        "classification_confidence": confidence,

        "industrial_evidence_score": score,
        "evidence": ";".join(evidence),

        "osm_intersections": len(intersections),
        "osm_nearby_features": len(nearby),

        "nearest_osm_name": nearest_name,
        "nearest_osm_distance_m": nearest_distance,
        "nearest_osm_strength": nearest_type,
    })

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

result_df = pd.DataFrame(results)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 50)
print("SOURCE CLASSIFICATION SUMMARY")
print("=" * 50)

print(
    result_df["source_class"].value_counts()
)

print()
print(
    result_df[
        [
            "source_class",
            "classification_confidence",
            "industrial_evidence_score"
        ]
    ].head(10).to_string(index=False)
)

print()
print("Saved:")
print(os.path.abspath(OUTPUT_FILE))