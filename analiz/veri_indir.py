"""Depoya konmayan büyük veri dosyalarını kaynaklarından indirir. Diğer veriler veri/ klasöründe hazır.

Çalıştırma:  python analiz/veri_indir.py
"""
import io

import pandas as pd
import requests
from ortak import VERI

DOSYALAR = {
    "owid_energy.csv": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
    "owid_co2.csv": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
    "who_hava_2026.xlsx": "https://cdn.who.int/media/docs/default-source/air-pollution-documents/air-quality-and-health/"
                          "who-ambient-air-quality-database-version-2026-v8.xlsx?sfvrsn=95d122a4_5&download=true",
}

for ad, url in DOSYALAR.items():
    yol = VERI / ad
    if yol.exists():
        print("var:", ad); continue
    print("indiriliyor:", ad)
    yol.write_bytes(requests.get(url, timeout=300, headers={"User-Agent": "Mozilla/5.0"}).content)

# DSÖ dosyası Excel içinde CSV satırları olarak geliyor; hücreleri birleştirip gerçek CSV'ye çevir
csv = VERI / "who_hava_2026.csv"
if not csv.exists():
    x = pd.read_excel(VERI / "who_hava_2026.xlsx", header=None, dtype=str)
    satirlar = [",".join(c for c in r if isinstance(c, str)) for r in x.itertuples(index=False)]
    pd.read_csv(io.StringIO("\n".join(satirlar)), na_values=["NA"]).to_csv(csv, index=False)
    print("yazıldı:", csv.name)
