import urllib.request
from urllib.error import HTTPError

tiles = ['N08E077', 'N06E075', 'N06E078', 'N09E075', 'N09E078']
for t in tiles:
    try:
        urllib.request.urlopen(f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{t}_Map.tif')
        print(f'{t} : Exists')
    except HTTPError as e:
        print(f'{t} : {e.code}')
