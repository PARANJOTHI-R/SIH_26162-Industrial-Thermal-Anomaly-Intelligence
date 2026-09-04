from pathlib import Path
import requests

TILE = "N21E069"

BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map/"
)

FILENAME = (
    f"ESA_WorldCover_10m_2021_v200_{TILE}_Map.tif"
)

OUTPUT_DIR = Path("SIH26162_DATA/03_LANDCOVER")
OUTPUT_FILE = OUTPUT_DIR / FILENAME

URL = BASE_URL + FILENAME

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("ESA WORLDCOVER DOWNLOAD")
print("=" * 60)
print(f"Tile:    {TILE}")
print(f"URL:     {URL}")
print(f"Output:  {OUTPUT_FILE}")
print()

# ---------------------------------------------------------
# Check remote file
# ---------------------------------------------------------

print("Checking remote file...")

response = requests.head(
    URL,
    allow_redirects=True,
    timeout=30
)

print(f"HTTP status: {response.status_code}")

if response.status_code != 200:
    raise RuntimeError(
        f"ESA WorldCover tile unavailable. "
        f"HTTP status: {response.status_code}"
    )

remote_size = response.headers.get("Content-Length")

if remote_size:
    remote_size = int(remote_size)
    print(f"Remote size: {remote_size / (1024**3):.2f} GB")

# ---------------------------------------------------------
# Avoid accidental re-download
# ---------------------------------------------------------

if OUTPUT_FILE.exists():

    local_size = OUTPUT_FILE.stat().st_size

    print(
        f"Local file already exists: "
        f"{local_size / (1024**3):.2f} GB"
    )

    if remote_size and local_size == remote_size:
        print("File size matches remote file.")
        print("Skipping download.")
        raise SystemExit(0)

    print("Existing file size differs. Re-downloading.")

# ---------------------------------------------------------
# Download
# ---------------------------------------------------------

print()
print("Downloading...")
print("This may take some time because the tile is large.")
print()

with requests.get(
    URL,
    stream=True,
    timeout=60
) as r:

    r.raise_for_status()

    total = int(
        r.headers.get("Content-Length", 0)
    )

    downloaded = 0

    with open(OUTPUT_FILE, "wb") as f:

        for chunk in r.iter_content(
            chunk_size=1024 * 1024
        ):

            if not chunk:
                continue

            f.write(chunk)
            downloaded += len(chunk)

            if total:
                percent = (
                    downloaded / total
                ) * 100

                print(
                    f"\rDownloaded: "
                    f"{downloaded / (1024**2):,.1f} MB "
                    f"({percent:5.1f}%)",
                    end=""
                )

print()
print()
print("=" * 60)
print("DOWNLOAD COMPLETE")
print("=" * 60)
print(f"File: {OUTPUT_FILE}")
print(
    f"Size: "
    f"{OUTPUT_FILE.stat().st_size / (1024**3):.2f} GB"
)