"""Makale 16 için: 81 ilin merkez noktası (il poligonunun ağırlık merkezi) için NASA POWER aylık verisi."""
import json
import time

import numpy as np
import requests
from ortak import VERI

g = json.load(open(VERI / "tr_iller.geojson", encoding="utf-8"))["features"]
hedef = VERI / "power_iller"
hedef.mkdir(exist_ok=True)
for f in g:
    ad = f["properties"]["name"]
    yol = hedef / f"{ad}.json"
    if yol.exists():
        continue
    geo = f["geometry"]
    polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    en_buyuk = max((np.array(p[0]) for p in polys), key=len)
    lon, lat = en_buyuk[:, 0].mean(), en_buyuk[:, 1].mean()
    for deneme in range(5):
        try:
            r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point",
                             params={"parameters": "PRECTOTCORR,T2M,T2M_MAX", "community": "AG", "longitude": round(lon, 3),
                                     "latitude": round(lat, 3), "start": 1981, "end": 2025, "format": "JSON"}, timeout=120)
            r.raise_for_status(); yol.write_text(r.text); print(ad, "ok", round(lat, 2), round(lon, 2)); break
        except Exception as e:
            print(ad, "tekrar", e); time.sleep(10 * (deneme + 1))
    time.sleep(1.5)
print("bitti", len(list(hedef.glob("*.json"))))
