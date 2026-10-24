"""Makale 16: İklim riski ve kredi portföyü stres testi (SKA 13.1, 8) — 81 il NASA POWER + temsilî portföy."""
import json
from calendar import monthrange

import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from scipy import stats
from ortak import RENK, VERI, kaydet, mtick, plt

KAYNAK = "NASA POWER (MERRA-2), 81 il merkezi"
g = json.load(open(VERI / "tr_iller.geojson", encoding="utf-8"))["features"]
SEKIL = {}
for f in g:
    geo = f["geometry"]; polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    SEKIL[f["properties"]["name"]] = [np.array(p[0]) for p in polys]


def il_verisi(ad):
    p = json.load(open(VERI / "power_iller" / f"{ad}.json", encoding="utf-8"))["properties"]["parameter"]
    r = []
    for k, v in p["PRECTOTCORR"].items():
        y, a = int(k[:4]), int(k[4:])
        if a == 13:
            continue
        r.append({"t": pd.Timestamp(y, a, 1), "yil": y, "ay": a, "yagis": v * monthrange(y, a)[1], "sic": p["T2M"][k], "maks": p["T2M_MAX"][k]})
    return pd.DataFrame(r).set_index("t").sort_index()


def spi12(d):
    y12 = d.yagis.rolling(12).sum()
    out = pd.Series(np.nan, index=d.index)
    for a in range(1, 13):
        s = y12[d.ay == a].dropna(); s = s[s > 0]
        sh, _, sc = stats.gamma.fit(s, floc=0)
        out[s.index] = stats.norm.ppf(np.clip(stats.gamma.cdf(s, sh, scale=sc), 1e-6, 1 - 1e-6))
    return out


R = []
for ad in SEKIL:
    d = il_verisi(ad)
    yil = d.groupby("yil").sic.mean()
    yaz = d[d.ay.between(6, 8)].groupby("yil").maks.mean()
    s = spi12(d)
    R.append({"il": ad, "isinma": stats.linregress(yil.index, yil.values).slope * 10,
              "yaz_artis": yaz.loc[2006:2025].mean() - yaz.loc[1981:2000].mean(),
              "kurak_pay": (s.loc["2016":"2025"] < -1).mean() * 100, "spi_2025": s.loc["2025-12"].iloc[0],
              "yagis_ort": d.groupby("yil").yagis.sum().mean()})
R = pd.DataFrame(R).set_index("il")
z = lambda x: (x - x.mean()) / x.std()
R["skor"] = (z(R.isinma) + z(R.yaz_artis) + z(R.kurak_pay) + z(-R.spi_2025)) / 4
R["skor_100"] = (R.skor - R.skor.min()) / (R.skor.max() - R.skor.min()) * 100
R = R.sort_values("skor", ascending=False)
R.round(3).to_csv(VERI / "16_iklim_risk_iller.csv")
print(R.round(2).head(15).to_string()); print("...\n", R.round(2).tail(5).to_string())
print("Ortalama ısınma (°C/10 yıl):", round(R.isinma.mean(), 2), "aralık", round(R.isinma.min(), 2), round(R.isinma.max(), 2))
print("2025 sonunda SPI-12 < -1 olan il:", int((R.spi_2025 < -1).sum()), " < -1,5:", int((R.spi_2025 < -1.5).sum()))


def harita(deger, ad, baslik, cbar, cmap, vmin=None, vmax=None, bicim="{:.0f}"):
    fig, ax = plt.subplots(figsize=(13, 6))
    norm = plt.Normalize(vmin if vmin is not None else deger.min(), vmax if vmax is not None else deger.max())
    yama, renk = [], []
    for il, h in SEKIL.items():
        for p in h:
            yama.append(Polygon(p, closed=True)); renk.append(cmap(norm(deger[il])))
    ax.add_collection(PatchCollection(yama, facecolor=renk, edgecolor="white", linewidth=0.5))
    for il in deger.sort_values().index[-5:] if "risk" in ad else []:
        p = max(SEKIL[il], key=len); ax.text(p[:, 0].mean(), p[:, 1].mean(), il, fontsize=8, ha="center", fontweight="bold")
    ax.set_xlim(25.6, 45); ax.set_ylim(35.7, 42.3); ax.set_aspect(1.25); ax.axis("off")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01).set_label(cbar)
    ax.set_title(baslik)
    kaydet(fig, ad, KAYNAK)


harita(R.skor_100, "16_1_risk_harita", "İklim fiziksel risk skoru: 81 il (ısınma, yaz sıcakları ve kuraklık)", "Bileşik risk skoru (0 = en düşük, 100 = en yüksek)", plt.cm.YlOrRd)
harita(R.spi_2025, "16_2_spi2025", "Aralık 2025 itibarıyla son 12 ayın kuraklık durumu (SPI-12)", "SPI-12 (−1 altı kuraklık, −2 altı aşırı kuraklık)", plt.cm.RdBu, -2.5, 2.5)

# Bileşenler: en riskli 15 il
T = R.head(15)
fig, axs = plt.subplots(1, 4, figsize=(14, 5.6), sharey=True)
for ax, (k, baslik, renk) in zip(axs, [("isinma", "Isınma\n(°C / 10 yıl)", RENK["kirmizi"]), ("yaz_artis", "Yaz maks. sıcaklık\nartışı (°C)", RENK["sari"]),
                                       ("kurak_pay", "Kurak ay payı\n2016–2025 (%)", RENK["mor"]), ("spi_2025", "SPI-12\nAralık 2025", RENK["mavi"])]):
    ax.barh(T.index[::-1], T[k][::-1], color=renk); ax.set_title(baslik, fontsize=10.5); ax.grid(axis="y", visible=False)
    ax.axvline(0, color="black", lw=0.6)
fig.suptitle("İklim riski en yüksek 15 il ve risk bileşenleri", fontweight="bold", fontsize=13)
kaydet(fig, "16_3_bilesenler", KAYNAK)

# --- Temsilî stres testi ---
# Varsayımlar (açıkça temsilî): her ile eşit 1 milyar TL tarım kredisi; baz PD %3; LGD %45 (Basel temel IRB, teminatsız)
EAD, PD0, LGD = 1.0, 0.03, 0.45
# Kuraklık şoku: SPI-12'nin -1'in altına indiği her birim için PD'nin göreli artışı β (duyarlılık parametresi)
def beklenen_kayip(spi, beta):
    carpan = 1 + beta * np.clip(-1 - spi, 0, None)
    return (EAD * np.minimum(PD0 * carpan, 1) * LGD)
senaryo = {
    "Baz (normal yıl, SPI = 0)": pd.Series(0.0, index=R.index),
    "2025 kuraklığı tekrarlanırsa": R.spi_2025,
    "Şiddetli: her ilde SPI = 2025 − 1": R.spi_2025 - 1,
}
S = pd.DataFrame({b: {ad: beklenen_kayip(s, b).sum() for ad, s in senaryo.items()} for b in [0.5, 1.0, 2.0]})
taban = beklenen_kayip(senaryo["Baz (normal yıl, SPI = 0)"], 1.0).sum()
print("Beklenen kayıp (milyar TL, 81 milyar TL portföy):\n", S.round(3))
print("Artış %:\n", ((S / taban - 1) * 100).round(0))
fig, ax = plt.subplots(figsize=(10.5, 4.8))
x = np.arange(len(S)); w = 0.26
for i, (b, renk) in enumerate(zip(S.columns, [RENK["sari"], RENK["kirmizi"], RENK["mor"]])):
    c = ax.bar(x + (i - 1) * w, S[b], w, color=renk, label=f"Duyarlılık β = {b:g}".replace(".", ","))
    ax.bar_label(c, labels=[f"{v:.2f}".replace(".", ",") for v in S[b]], padding=2, fontsize=8.5)
ax.set_xticks(x, S.index); ax.set_ylabel("Beklenen kayıp (milyar TL)")
ax.set_title("Temsilî tarım kredisi portföyünde (81 × 1 milyar TL) kuraklık stres testi")
ax.legend(frameon=False, title="PD duyarlılığı (varsayım)"); ax.grid(axis="x", visible=False)
kaydet(fig, "16_4_stres", "NASA POWER · temsilî portföy ve varsayımlar yazıda")
kat = beklenen_kayip(R.spi_2025, 1.0)
print("2025 senaryosunda kaybın en çok arttığı iller:", (kat - EAD * PD0 * LGD).sort_values(ascending=False).head(8).round(3).to_dict())
print("Skor ile 2025 SPI korelasyonu:", round(R.skor.corr(R.spi_2025), 2))
