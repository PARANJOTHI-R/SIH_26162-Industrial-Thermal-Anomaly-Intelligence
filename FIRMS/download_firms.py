import requests
from pathlib import Path

# Keep your FIRMS MAP_KEY here locally.
MAP_KEY = "470253c79c89b0ca2e8e331bb0e8a996"

# Jamnagar pilot area
AREA = "69.70,22.20,70.00,22.50"

# Start with NOAA-20 only
SOURCE = "MODIS_TERRA_NRT "

# 5 days
DAY_RANGE = 5

url = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{MAP_KEY}/{SOURCE}/{AREA}/{DAY_RANGE}"
)

output_dir = Path("SIH26162_DATA/01_FIRMS")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "jamnagar_MODIS_5days.csv"

response = requests.get(url, timeout=60)

print("HTTP status:", response.status_code)

if response.status_code != 200:
    print(response.text)
    raise SystemExit("FIRMS download failed.")

output_file.write_bytes(response.content)

print("Saved:", output_file)
print("Size:", output_file.stat().st_size, "bytes")