"""Makale 9: Gıda enflasyonu ve fiyat anomalileri (SKA 2.c.1) — OECD gıda TÜFE, FAO gıda fiyat endeksi, IFPA uyarlaması."""
import io

import numpy as np
import pandas as pd
import requests
from ortak import RENK, VERI, indir, kaydet, mtick, plt

ULKE = {"TUR": "Türkiye", "DEU": "Almanya", "USA": "ABD", "FRA": "Fransa", "POL": "Polonya", "HUN": "Macaristan",
        "MEX": "Meksika", "COL": "Kolombiya", "CHL": "Şili", "GBR": "İngiltere"}


def oecd(anahtar, dosya):
    yol = VERI / dosya
    if not yol.exists():
        url = f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/{anahtar}?startPeriod=2003-01&format=csvfile"
        yol.write_text(requests.get(url, timeout=180).text, encoding="utf-8")
    d = pd.read_csv(yol)
    d["t"] = pd.PeriodIndex(d.TIME_PERIOD, freq="M")
    return d.pivot_table(index="t", columns="REF_AREA", values="OBS_VALUE").sort_index()


gida = oecd("+".join(ULKE) + ".M.N.CPI.IX.CP01.N._Z", "oecd_gida_tufe.csv")
genel = oecd("+".join(ULKE) + ".M.N.CPI.IX._T.N._Z", "oecd_genel_tufe.csv")
fao = pd.read_csv(indir("https://www.fao.org/fileadmin/templates/worldfood/Reports_and_docs/Food_price_indices_data.csv", "fao_gida.csv"), skiprows=2)
fao = fao.dropna(subset=["Food Price Index"])
fao = fao[fao.Date.astype(str).str.match(r"^\d{4}-\d{2}$")]
fao["t"] = pd.PeriodIndex(pd.to_datetime(fao.Date, format="%Y-%m"), freq="M")
fao = fao.set_index("t")["Food Price Index"].astype(float)
kur = pd.read_csv(VERI / "aylik_tufe_kur.csv", index_col="donem").usdtry
kur.index = pd.PeriodIndex(kur.index, freq="M")
fao_tl = (fao * kur).dropna()
print("Gıda son:", gida["TUR"].dropna().index[-1], "FAO son:", fao.index[-1])

yoy = lambda s: (s / s.shift(12) - 1) * 100
tr_g, tr_t = yoy(gida["TUR"]).dropna(), yoy(genel["TUR"]).dropna()

# 1) Gıda ve genel enflasyon
fig, ax = plt.subplots(figsize=(11, 4.8))
t = tr_g.loc["2005":].index.to_timestamp()
ax.plot(t, tr_g.loc["2005":], color=RENK["kirmizi"], lw=2.2, label="Gıda ve alkolsüz içecekler")
ax.plot(t, tr_t.reindex(tr_g.index).loc["2005":], color="black", lw=1.6, label="Genel TÜFE")
ax.fill_between(t, tr_t.reindex(tr_g.index).loc["2005":], tr_g.loc["2005":], where=tr_g.loc["2005":] > tr_t.reindex(tr_g.index).loc["2005":], color=RENK["kirmizi"], alpha=0.15)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0)); ax.legend(frameon=False)
ax.set_title("Türkiye: Yıllık gıda enflasyonu ve genel enflasyon")
kaydet(fig, "09_1_gida_genel", "OECD (TÜİK verisi)")
kum_g = gida["TUR"].loc["2025-12"] / gida["TUR"].loc["2005-12"]
kum_t = genel["TUR"].loc["2025-12"] / genel["TUR"].loc["2005-12"]
print(f"2005-12 → 2025-12 birikimli: gıda {kum_g:.1f} kat, genel {kum_t:.1f} kat; gıda/genel göreli fiyat {kum_g / kum_t:.2f}")
print("Gıda > genel olan ay oranı (2005–2025): %", round(100 * (tr_g.loc["2005":] > tr_t.reindex(tr_g.index).loc["2005":]).mean()))
print("Zirve gıda yıllık:", tr_g.idxmax(), round(tr_g.max(), 1), " 2025-12:", round(tr_g.loc["2025-12"], 1), " genel:", round(tr_t.loc["2025-12"], 1))

# 2) Dünya gıda fiyatı (TL) ve yurt içi gıda fiyatı
B = pd.DataFrame({"yurtici": gida["TUR"], "dunya_tl": fao_tl, "dunya_usd": fao}).dropna().loc["2005-01":]
B = B / B.iloc[0] * 100
fig, ax = plt.subplots(figsize=(10.5, 4.8))
ax.plot(B.index.to_timestamp(), B.yurtici, color=RENK["kirmizi"], lw=2.4, label="Türkiye gıda TÜFE")
ax.plot(B.index.to_timestamp(), B.dunya_tl, color=RENK["mavi"], lw=2, label="Dünya gıda fiyatları, TL'ye çevrilmiş (FAO × USD/TRY)")
ax.plot(B.index.to_timestamp(), B.dunya_usd, color=RENK["gri"], lw=1.8, ls="--", label="Dünya gıda fiyatları, dolar (FAO)")
ax.set_yscale("log"); ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:g}"))
ax.set_title("Gıda fiyatları: Türkiye ve dünya (Ocak 2005 = 100, log ölçek)")
ax.legend(frameon=False, fontsize=9.5)
kaydet(fig, "09_2_dunya", "OECD · FAO · ECB kurları")
print("2005→2025 son:", B.iloc[-1].round(0).to_dict(), B.index[-1])

# Aylık log değişimlerle dağıtılmış gecikme regresyonu: yurt içi gıda ~ dünya gıda (TL) gecikmeleri
dl = np.log(pd.DataFrame({"y": gida["TUR"], "x": fao_tl})).diff().dropna().loc["2005":]
X = pd.concat({f"x{k}": dl.x.shift(k) for k in range(0, 7)}, axis=1)
Z = pd.concat([dl.y, X], axis=1).dropna()
A = np.column_stack([np.ones(len(Z)), Z.drop(columns="y").values])
beta, *_ = np.linalg.lstsq(A, Z.y.values, rcond=None)
yhat = A @ beta
r2 = 1 - ((Z.y - yhat) ** 2).sum() / ((Z.y - Z.y.mean()) ** 2).sum()
print(f"Geçişkenlik: toplam esneklik {beta[1:].sum():.2f} (0–6 ay), R² {r2:.2f}, n={len(Z)}; sabit (aylık) {beta[0]*100:.2f}%")

# 3) IFPA uyarlaması (SKA 2.c.1): üç aylık ve yıllık bileşik büyüme anomalilerinin ağırlıklı ortalaması
p = gida["TUR"].dropna()
cqgr = (p / p.shift(3)) ** (1 / 3) - 1
cagr = (p / p.shift(12)) ** (1 / 12) - 1
def z(s):
    s = s.dropna(); ay = s.index.month
    return (s - s.groupby(ay).transform("mean")) / s.groupby(ay).transform("std")
zq, za = z(cqgr), z(cagr)
sq, sa = cqgr.std(), cagr.std()
g = (1 / sq) / (1 / sq + 1 / sa)       # oynaklığa ters ağırlık
ifpa = (g * zq + (1 - g) * za).dropna()
yil_ifpa = ifpa.groupby(ifpa.index.year).mean()
fig, ax = plt.subplots(figsize=(11, 4.6))
renk = [RENK["kirmizi"] if v >= 1 else (RENK["sari"] if v >= 0.5 else RENK["yesil"]) for v in yil_ifpa]
ax.bar(yil_ifpa.index, yil_ifpa.values, color=renk)
ax.axhline(1, color=RENK["kirmizi"], ls="--", lw=1); ax.axhline(0.5, color=RENK["sari"], ls="--", lw=1)
ax.text(yil_ifpa.index[0] - 0.4, 1.05, "anormal derecede yüksek", fontsize=8.5, color=RENK["kirmizi"])
ax.text(yil_ifpa.index[0] - 0.4, 0.55, "orta düzeyde yüksek", fontsize=8.5, color="#a07400")
ax.axhline(0, color="black", lw=0.8)
ax.set_title("Gıda fiyatı anomalisi göstergesi (SKA 2.c.1 yöntemi uyarlaması), Türkiye")
ax.set_ylabel("Anomali puanı (yıllık ortalama)")
kaydet(fig, "09_3_ifpa", "OECD gıda TÜFE · FAO IFPA yöntemi uyarlaması")
print("IFPA ağırlık γ:", round(g, 2)); print("IFPA yıllık:", yil_ifpa.round(2).to_dict())
print("Anormal (>=1) ay oranı son 5 yıl: %", round(100 * (ifpa.loc["2021":] >= 1).mean()), " önceki 15 yıl: %", round(100 * (ifpa.loc["2005":"2020"] >= 1).mean()))

# 4) Ülkeler: 2020-12 → 2025-12 birikimli gıda enflasyonu
K = (gida.loc["2025-12"] / gida.loc["2020-12"] - 1) * 100
K = K.dropna().rename(ULKE).sort_values()
fig, ax = plt.subplots(figsize=(10, 4.8))
c = ax.barh(K.index, K.values, color=[RENK["kirmizi"] if i == "Türkiye" else RENK["gri"] for i in K.index])
ax.bar_label(c, labels=[f"%{v:,.0f}".replace(",", ".") for v in K.values], padding=4)
ax.set_xscale("log"); ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"%{v:g}"))
ax.set_xlim(K.min() * 0.7, K.max() * 2.2)
ax.set_title("Son beş yılda gıda fiyatları ne kadar arttı? (Aralık 2020 → Aralık 2025, log ölçek)")
ax.grid(axis="y", visible=False)
kaydet(fig, "09_4_ulkeler", "OECD")
print(K.round(0).to_dict())
