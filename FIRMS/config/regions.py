"""
SIH26162 — Region Configuration
================================
Single source of truth for all region definitions.
Each region specifies exactly the paths and metadata needed
to run the intelligence pipeline. Scripts resolve all paths
through this config — no Jamnagar or Thoothukudi strings
are hard-coded in the pipeline scripts themselves.

Usage:
    from config.regions import get_region, REGIONS
    region = get_region("jamnagar")
"""

from pathlib import Path

# Root of the project (config/ is one level below FIRMS/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# REGION DEFINITIONS
# ============================================================

REGIONS = {

    "jamnagar": {
        "region_id":     "jamnagar",
        "display_name":  "Jamnagar",
        "state":         "Gujarat",
        "country":       "India",

        # Bounding box: west, south, east, north
        "bbox":          [69.70, 22.20, 70.00, 22.50],
        # Map center [lon, lat] and zoom
        "map_center":    [69.85, 22.35],
        "map_zoom":      9,

        # UTM CRS for metric spatial operations
        "utm_crs":       "EPSG:32643",

        # Data directories (relative to PROJECT_ROOT)
        "data_dir":      PROJECT_ROOT / "SIH26162_DATA",
        "firms_dir":     PROJECT_ROOT / "SIH26162_DATA" / "01_FIRMS",
        "industry_dir":  PROJECT_ROOT / "SIH26162_DATA" / "02_INDUSTRY",
        "landcover_dir": PROJECT_ROOT / "SIH26162_DATA" / "03_LANDCOVER",
        "analysis_dir":  PROJECT_ROOT / "SIH26162_DATA" / "analysis",

        # Input files
        "firms_combined_file":  "jamnagar_viirs_combined_historical.csv",
        "osm_geojson_file":     "jamnagar_osm_industrial_features.geojson",
        "osm_csv_file":         "jamnagar_osm_industrial_features.csv",
        "worldcover_tif_file":  "ESA_WorldCover_10m_2021_v200_N21E069_Map.tif",
        "known_facilities_file": PROJECT_ROOT / "known_facilities.csv",
    },

    "thoothukudi": {
        "region_id":     "thoothukudi",
        "display_name":  "Thoothukudi",
        "state":         "Tamil Nadu",
        "country":       "India",

        # Bounding box: west, south, east, north
        # Covers the coastal industrial/thermal corridor
        "bbox":          [77.90, 8.50, 78.30, 8.90],
        "map_center":    [78.12, 8.72],
        "map_zoom":      11,

        # UTM CRS — Zone 44N covers Tamil Nadu coast
        "utm_crs":       "EPSG:32644",

        "data_dir":      PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi",
        "firms_dir":     PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi" / "01_FIRMS",
        "industry_dir":  PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi" / "02_INDUSTRY",
        "landcover_dir": PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi" / "03_LANDCOVER",
        "analysis_dir":  PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi" / "analysis",

        "firms_combined_file":  "thoothukudi_viirs_combined_historical.csv",
        "osm_geojson_file":     "thoothukudi_osm_industrial_features.geojson",
        "osm_csv_file":         "thoothukudi_osm_industrial_features.csv",
        "worldcover_tif_file":  "ESA_WorldCover_10m_2021_v200_N06E078_Map.tif",
        "known_facilities_file": PROJECT_ROOT / "SIH26162_DATA" / "regions" / "thoothukudi" / "known_facilities_thoothukudi.csv",
    },

}


# ============================================================
# HELPERS
# ============================================================

def get_region(region_id: str) -> dict:
    """Return the config dict for a region, raising ValueError if unknown."""
    if region_id not in REGIONS:
        raise ValueError(
            f"Unknown region '{region_id}'. "
            f"Available: {list(REGIONS.keys())}"
        )
    return REGIONS[region_id]


def list_regions() -> list:
    """Return a list of dicts suitable for the /regions API endpoint."""
    return [
        {
            "region_id":    r["region_id"],
            "display_name": r["display_name"],
            "state":        r["state"],
            "country":      r["country"],
            "bbox":         r["bbox"],
            "map_center":   r["map_center"],
            "map_zoom":     r["map_zoom"],
        }
        for r in REGIONS.values()
    ]


def get_analysis_path(region_id: str, filename: str) -> Path:
    """Return a full path to a file in the region's analysis directory."""
    region = get_region(region_id)
    return region["analysis_dir"] / filename
