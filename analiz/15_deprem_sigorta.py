"""Makale 15: Deprem riski ve sigorta açığı (SKA 1.5, 11.5, 13.1) — USGS kataloğu, DASK oranları, Dünya Bankası GRADE."""
import json

import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from matplotlib.path import Path
from ortak import RENK, VERI, kaydet, mtick, plt

BOLGE = {
    "Marmara": "Edirne Kırklareli Tekirdağ İstanbul Kocaeli Yalova Sakarya Bilecik Bursa Balıkesir Çanakkale",
    "Ege": "İzmir Manisa Aydın Denizli Muğla Afyon Kütahya Uşak",
    "Akdeniz": "Antalya Isparta Burdur Mersin Adana Hatay Osmaniye Kahramanmaraş",
    "İç Anadolu": "Ankara Konya Kayseri Eskişehir Sivas Kırıkkale Aksaray Karaman Kırşehir Niğde Nevşehir Yozgat Çankırı",
    "Karadeniz": "Bolu Düzce Zonguldak Karabük Bartın Kastamonu Sinop Samsun Amasya Tokat Çorum Ordu Giresun Trabzon Rize Artvin Gümüşhane Bayburt",
    "Doğu Anadolu": "Malatya Elazığ Bingöl Tunceli Erzincan Erzurum Kars Ardahan Iğdır Ağrı Muş Bitlis Van Hakkari",
    "Güneydoğu Anadolu": "Gaziantep Kilis Adıyaman Şanlıurfa Diyarbakır Mardin Batman Siirt Şırnak"}
IL_BOLGE = {il: b for b, s in BOLGE.items() for il in s.split()}
# DASK sigortalılık oranları (DASK verisi, AA aracılığıyla Ekonomi Gazetesi, Mart 2025)
DASK_BOLGE = {"Marmara": 64, "Doğu Anadolu": 61, "Ege": 56, "Akdeniz": 55, "Güneydoğu Anadolu": 52, "İç Anadolu": 50, "Karadeniz": 45}
DASK_IL = {"Bolu": 90, "Düzce": 89, "Yalova": 84, "Bingöl": 83, "Muğla": 83, "Şırnak": 28, "Gümüşhane": 31, "Siirt": 31, "Rize": 33, "Bayburt": 34}
KAYNAK = "USGS deprem kataloğu · DASK"

g = json.load(open(VERI / "tr_iller.geojson", encoding="utf-8"))["features"]
assert len(IL_BOLGE) == 81 and {f["properties"]["name"] for f in g} == set(IL_BOLGE)
dep = pd.read_csv(VERI / "usgs_tr.csv", parse_dates=["time"])
dep = dep[dep.type == "earthquake"]
xy = dep[["longitude", "latitude"]].values

iller = []
for f in g:
    ad = f["properties"]["name"]
    geo = f["geometry"]
    polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    halkalar = [np.array(p[0]) for p in polys]
    icinde = np.zeros(len(dep), bool)
    alan = 0.0
    for h in halkalar:
        icinde |= Path(h).contains_points(xy)
        lat = np.radians(h[:, 1].mean())
        x, y = h[:, 0] * 111.32 * np.cos(lat), h[:, 1] * 110.57
        alan += 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    d = dep[icinde]
    iller.append({"il": ad, "bolge": IL_BOLGE[ad], "alan_km2": alan, "m5": len(d), "m6": int((d.mag >= 6).sum()),
                  "m7": int((d.mag >= 7).sum()), "maks": d.mag.max() if len(d) else np.nan,
                  "son25_m5": int((d.time.dt.year >= 2000).sum()), "halkalar": halkalar})
I = pd.DataFrame(iller)
I["yogunluk"] = I.m5 / I.alan_km2 * 10000
print(f"Türkiye sınırları içinde M≥5: {I.m5.sum()} deprem (katalogdaki {len(dep)} olaydan); M≥6: {I.m6.sum()}, M≥7: {I.m7.sum()}")
print(I.sort_values("m5", ascending=False)[["il", "bolge", "m5", "m6", "m7", "maks"]].head(12).to_string())
print("Hiç M≥5 olmayan il:", I[I.m5 == 0].il.tolist())

# 1) Harita
fig, ax = plt.subplots(figsize=(13, 6.2))
cmap = plt.cm.YlOrRd
renk = I.m5 / I.m5.max()
yamalar, renkler = [], []
for (_, r), c in zip(I.iterrows(), renk):
    for h in r.halkalar:
        yamalar.append(Polygon(h, closed=True)); renkler.append(cmap(c))
ax.add_collection(PatchCollection(yamalar, facecolor=renkler, edgecolor="white", linewidth=0.5))
tr_dep = dep[dep.longitude.between(25.5, 45) & dep.latitude.between(35.8, 42.2)]
buyuk = tr_dep[tr_dep.mag >= 6.5]
ax.scatter(buyuk.longitude, buyuk.latitude, s=(buyuk.mag - 6) ** 2 * 60 + 10, facecolor="none", edgecolor="black", lw=0.9, label="M ≥ 6,5 depremler (1900–2026)")
for _, r in tr_dep[tr_dep.mag >= 7.3].iterrows():
    ax.annotate(f"{r.time.year} · M{r.mag:.1f}".replace(".", ","), (r.longitude, r.latitude), xytext=(5, 5), textcoords="offset points", fontsize=8)
ax.set_xlim(25.6, 46.2); ax.set_ylim(35.7, 42.3); ax.set_aspect(1.25); ax.axis("off")
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, I.m5.max())); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01); cb.set_label("İl sınırları içindeki M ≥ 5 deprem sayısı (1900–2026)")
ax.legend(frameon=False, loc="lower left")
ax.set_title("Türkiye'de 1900'den bu yana büyük depremler")
kaydet(fig, "15_1_harita", "USGS")

# 2) Bölgeler: deprem yoğunluğu ve DASK oranı
B = I.groupby("bolge").agg(m5=("m5", "sum"), alan=("alan_km2", "sum"), m6=("m6", "sum"))
B["yogunluk"] = B.m5 / B.alan * 10000
B["dask"] = pd.Series(DASK_BOLGE)
B = B.sort_values("dask")
fig, ax1 = plt.subplots(figsize=(10.5, 4.8))
y = np.arange(len(B))
ax1.barh(y - 0.2, B.dask, 0.4, color=RENK["mavi"], label="DASK sigortalılık oranı (%)")
ax2 = ax1.twiny()
ax2.barh(y + 0.2, B.yogunluk, 0.4, color=RENK["kirmizi"], alpha=0.8, label="10 bin km² başına M≥5 deprem")
ax1.set_yticks(y, B.index); ax1.set_xlim(0, 80); ax2.set_xlim(0, B.yogunluk.max() * 1.25)
ax1.set_xlabel("DASK sigortalılık oranı (%)", color=RENK["mavi"]); ax2.set_xlabel("10 bin km² başına M≥5 deprem (1900–2026)", color=RENK["kirmizi"])
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="lower right", fontsize=9)
ax1.grid(axis="y", visible=False); ax2.grid(False)
ax1.set_title("Bölgelere göre deprem sıklığı ve sigortalılık", pad=34)
kaydet(fig, "15_2_bolgeler", KAYNAK)
print(B.round(2).to_string()); print("Bölge düzeyinde korelasyon (yoğunluk, DASK):", round(B.yogunluk.corr(B.dask), 2))

# 3) En yüksek ve en düşük sigortalı iller
E = I.set_index("il").loc[list(DASK_IL)].assign(dask=pd.Series(DASK_IL)).sort_values("dask")
fig, ax = plt.subplots(figsize=(10.5, 5))
c = ax.barh(E.index, E.dask, color=[RENK["yesil"] if v > 60 else RENK["kirmizi"] for v in E.dask])
for i, (il, r) in enumerate(E.iterrows()):
    son = dep[(dep.mag >= 6)].copy()
    ax.text(r.dask + 1, i, f"%{r.dask:.0f}  ·  il sınırında M≥5: {int(r.m5)}, M≥6: {int(r.m6)}", va="center", fontsize=9)
ax.set_xlim(0, 125); ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.axvline(56, color="black", ls="--", lw=1); ax.text(57, len(E) - 0.45, "Türkiye: %56", fontsize=9)
ax.set_title("DASK sigortalılığı en yüksek ve en düşük beş il")
ax.grid(axis="y", visible=False)
kaydet(fig, "15_3_iller", KAYNAK)
print(E[["dask", "m5", "m6", "maks", "son25_m5"]].to_string())

# 4) 2023 depremleri: hasar ve sigorta ödemesi
hasar, konut = 34.2, 18.0            # milyar $, Dünya Bankası GRADE (27 Şubat 2023)
dask_tl = 39.7                       # milyar TL, DASK (Şubat 2025 itibarıyla)
kur = pd.read_csv(VERI / "aylik_tufe_kur.csv", index_col="donem").usdtry
kur_ort = kur.loc["2023-02":"2024-12"].mean()
dask_usd = dask_tl / kur_ort
print(f"DASK ödemesi ≈ {dask_usd:.2f} mlr $ (2023-02/2024-12 ortalama kur {kur_ort:.1f}); konut hasarının %{100 * dask_usd / konut:.0f}'i, toplam hasarın %{100 * dask_usd / hasar:.0f}'i")
fig, ax = plt.subplots(figsize=(10, 3.6))
c = ax.barh(["Toplam doğrudan fiziksel hasar", "Konut hasarı", "DASK ödemesi"], [hasar, konut, dask_usd],
            color=[RENK["gri"], RENK["sari"], RENK["mavi"]])
ax.bar_label(c, labels=[f"{v:.1f} milyar $".replace(".", ",") for v in [hasar, konut, dask_usd]], padding=4)
ax.invert_yaxis(); ax.set_xlim(0, 42); ax.grid(axis="y", visible=False)
ax.set_title("6 Şubat 2023 depremleri: Hasar ve sigortanın karşıladığı")
kaydet(fig, "15_4_2023", "Dünya Bankası GRADE raporu · DASK · ECB kurları")
