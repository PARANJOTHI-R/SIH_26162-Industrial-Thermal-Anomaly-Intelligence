import urllib.request
import os
import rasterio
from rasterio.merge import merge

base_url = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{}_Map.tif"
tiles = ["N06E075", "N06E078"]

out_dir = "SIH26162_DATA/regions/thoothukudi/03_LANDCOVER"
os.makedirs(out_dir, exist_ok=True)

out_fp = os.path.join(out_dir, "ESA_WorldCover_10m_2021_v200_N08E077_Map.tif")

dl_paths = []
for t in tiles:
    url = base_url.format(t)
    fp = os.path.join(out_dir, f"{t}.tif")
    if not os.path.exists(fp):
        print(f"Downloading {t}...")
        urllib.request.urlretrieve(url, fp)
    dl_paths.append(fp)

print("Merging...")
src_files_to_mosaic = []
for fp in dl_paths:
    src = rasterio.open(fp)
    src_files_to_mosaic.append(src)

mosaic, out_trans = merge(src_files_to_mosaic)
out_meta = src_files_to_mosaic[0].meta.copy()

out_meta.update({
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans,
    "compress": "lzw"
})

print(f"Writing to {out_fp}...")
with rasterio.open(out_fp, "w", **out_meta) as dest:
    dest.write(mosaic)

for src in src_files_to_mosaic:
    src.close()

print("Done!")
