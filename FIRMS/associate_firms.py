from pathlib import Path
import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FIRMS_FILE = (
    BASE_DIR
    / "SIH26162_DATA"
    / "01_FIRMS"
    / "jamnagar_viirs_combined_historical.csv"
)

OSM_FILE = (
    BASE_DIR
    / "SIH26162_DATA"
    / "02_INDUSTRY"
    / "jamnagar_osm_industrial_features.geojson"
)

OUTPUT_DIR = (
    BASE_DIR
    / "SIH26162_DATA"
    / "analysis"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "historical_thermal_osm_association.csv"
)


# Maximum distance for a nearby association
MAX_DISTANCE_KM = 5.0


# ============================================================
# LOAD FIRMS
# ============================================================

print("Loading historical FIRMS observations...")

firms = pd.read_csv(FIRMS_FILE)

print(f"FIRMS observations: {len(firms)}")


# Create point geometry
firms_gdf = gpd.GeoDataFrame(
    firms.copy(),
    geometry=gpd.points_from_xy(
        firms["longitude"],
        firms["latitude"]
    ),
    crs="EPSG:4326"
)


# ============================================================
# LOAD OSM
# ============================================================

print("\nLoading OSM industrial features...")

osm = gpd.read_file(OSM_FILE)

print(f"OSM features: {len(osm)}")

if osm.crs is None:
    osm = osm.set_crs("EPSG:4326")


# ============================================================
# PROJECT TO UTM
# ============================================================

# Jamnagar is in UTM Zone 43N
firms_metric = firms_gdf.to_crs("EPSG:32643")
osm_metric = osm.to_crs("EPSG:32643")


# ============================================================
# SPATIAL ASSOCIATION
# ============================================================

print("\nCalculating historical spatial associations...")

results = []

for idx, fire in firms_metric.iterrows():

    fire_geom = fire.geometry

    # --------------------------------------------------------
    # Find OSM features intersecting FIRMS point
    # --------------------------------------------------------

    intersecting = osm_metric[
        osm_metric.geometry.intersects(fire_geom)
    ]

    if len(intersecting) > 0:

        intersecting = intersecting.copy()

        intersecting["distance_m"] = (
            intersecting.geometry.distance(fire_geom)
        )

        match = (
            intersecting
            .sort_values("distance_m")
            .iloc[0]
        )

        distance_km = (
            match["distance_m"] / 1000.0
        )

        association_type = (
            "OSM_FEATURE_INTERSECTION"
        )

        association_confidence = "HIGH"

    else:

        # ----------------------------------------------------
        # Otherwise find nearest OSM feature
        # ----------------------------------------------------

        distances = (
            osm_metric.geometry.distance(fire_geom)
        )

        nearest_idx = distances.idxmin()

        nearest = osm_metric.loc[nearest_idx]

        distance_km = (
            distances.loc[nearest_idx] / 1000.0
        )

        if distance_km <= MAX_DISTANCE_KM:

            match = nearest

            association_type = (
                "NEARBY_OSM_INDUSTRIAL_FEATURE"
            )

            association_confidence = "SCREENING"

        else:

            match = None

            association_type = (
                "NO_NEARBY_OSM_FEATURE"
            )

            association_confidence = "NONE"


    # --------------------------------------------------------
    # Build result
    # --------------------------------------------------------

    row = {
        "observation_index": idx,

        "latitude": fire["latitude"],
        "longitude": fire["longitude"],

        "acq_date": fire["acq_date"],
        "acq_time": fire["acq_time"],

        "satellite": fire["satellite"],
        "instrument": fire["instrument"],
        "confidence": fire["confidence"],

        "bright_ti4": fire["bright_ti4"],
        "bright_ti5": fire["bright_ti5"],
        "frp": fire["frp"],

        "association_type": association_type,
        "association_confidence": association_confidence,
    }


    if match is not None:

        row["osm_type"] = match.get("osm_type")
        row["osm_id"] = match.get("osm_id")

        row["name"] = match.get("name")
        row["industrial"] = match.get("industrial")
        row["landuse"] = match.get("landuse")
        row["power"] = match.get("power")
        row["man_made"] = match.get("man_made")

        row["distance_km"] = round(
            distance_km,
            3
        )

    else:

        row["osm_type"] = None
        row["osm_id"] = None

        row["name"] = None
        row["industrial"] = None
        row["landuse"] = None
        row["power"] = None
        row["man_made"] = None

        row["distance_km"] = None


    results.append(row)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("HISTORICAL SPATIAL ASSOCIATION COMPLETE")
print("========================================")

print(
    f"FIRMS observations      : {len(firms)}"
)

print(
    f"OSM industrial features : {len(osm)}"
)

print("\nAssociation types:")

print(
    results_df[
        "association_type"
    ].value_counts()
)

print("\nHistorical associations:")

display_columns = [
    "acq_date",
    "acq_time",
    "latitude",
    "longitude",
    "frp",
    "name",
    "industrial",
    "landuse",
    "power",
    "distance_km",
    "association_type",
    "association_confidence",
]

print(
    results_df[
        display_columns
    ].to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)