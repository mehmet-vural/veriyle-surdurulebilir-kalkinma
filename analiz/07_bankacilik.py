"""Makale 7: Türk bankacılığının finansal sağlamlığı (SKA 10.5.1) — IMF FSI + Dünya Bankası."""
import numpy as np
import pandas as pd
from ortak import RENK, VERI, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "IMF Financial Soundness Indicators"
TR = pd.read_csv(VERI / "imf_fsic_tur.csv", low_memory=False)
TUM = pd.read_csv(VERI / "imf_fsic_tum.csv", low_memory=False)
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()


def seri(ind, frek="Q", sektor="S12CFSI"):
    g = TR[(TR.INDICATOR == ind) & (TR.FREQUENCY == frek) & (TR.SECTOR == sektor)].copy()
    if frek == "Q":
        g.index = pd.PeriodIndex(g.TIME_PERIOD.str.replace("-", ""), freq="Q").to_timestamp(how="end")
    else:
        g.index = g.TIME_PERIOD.astype(str).str[:4].astype(int)
    return g.OBS_VALUE.sort_index()


npl, car, roe, t1a = seri("AQ12_CFSI_PT"), seri("FSI688_CFSI_PT"), seri("ROE_CFSI_PT"), seri("T1KTA_CFSI_PT")
karsilik = seri("AQ14_CFSI_PT")
roe_y = seri("ROE_CFSI_PT", "A")
npl_tutar, kredi = seri("AQ12_NPF4_XDC", "A"), seri("FSI667_TGF4_XDC", "A")
print("Son çeyrek:", {k: round(v.iloc[-1], 2) for k, v in dict(npl=npl, car=car, roe=roe, t1a=t1a, karsilik=karsilik).items()}, npl.index[-1].date())
print("NPL çeyreklik son 8:", npl.tail(8).round(2).to_dict())

# Yıl sonu TÜFE (OECD, aralıktan aralığa)
aylik = pd.read_csv(VERI / "aylik_tufe_kur.csv", index_col="donem")
aralik = aylik[aylik.index.str.endswith("-12")].tufe
aralik.index = aralik.index.str[:4].astype(int)
enf = (aralik.pct_change() * 100).dropna()
R = pd.DataFrame({"roe": roe_y, "enf": enf}).dropna().loc[2015:]
R["reel"] = ((1 + R.roe / 100) / (1 + R.enf / 100) - 1) * 100
print(R.round(1))

B = pd.DataFrame({"npl": npl_tutar, "kredi": kredi, "tufe": aralik}).dropna().loc[2015:]
artis = B.pct_change() * 100
print("Nominal yıllık artış (%):\n", artis.round(0).tail(6))
print("NPL oranı (tutardan):", (B.npl / B.kredi * 100).round(2).tail(6).to_dict())

# 1) Takipteki krediler ve sermaye yeterliliği (çeyreklik)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.6))
ax1.plot(npl.index, npl, color=RENK["kirmizi"], lw=2.4)
ax1.set_title("Takipteki kredi oranı (%)"); ax1.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
ax1.annotate(f"%{npl.iloc[-1]:.1f}".replace(".", ","), (npl.index[-1], npl.iloc[-1]), xytext=(-10, 10), textcoords="offset points", color=RENK["kirmizi"], fontweight="bold")
ax2.plot(car.index, car, color=RENK["mavi"], lw=2.4, label="Sermaye yeterlilik oranı")
ax2.axhline(8, color="black", ls="--", lw=1, label="Basel asgari: %8")
ax2.set_title("Sermaye yeterlilik oranı (%)"); ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax2.set_ylim(0, max(22, car.max() + 2)); ax2.yaxis.set_major_locator(mtick.MultipleLocator(5)); ax2.legend(frameon=False, loc="lower left")
kaydet(fig, "07_1_npl_car", KAYNAK)

# 2) Nominal ve reel özsermaye kârlılığı
fig, ax = plt.subplots(figsize=(10, 4.8))
x = np.arange(len(R))
ax.bar(x - 0.27, R.roe, 0.27, color=RENK["mavi"], label="Nominal özsermaye kârlılığı (ROE)")
ax.bar(x, R.enf, 0.27, color=RENK["gri"], label="Yıl sonu enflasyon (TÜFE)")
ax.bar(x + 0.27, R.reel, 0.27, color=[RENK["yesil"] if v > 0 else RENK["kirmizi"] for v in R.reel], label="Reel ROE")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x, R.index); ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Bankaların kârlılığı: Nominal parlak, reel tablo farklı")
ax.legend(frameon=False, fontsize=9.5)
kaydet(fig, "07_2_reel_roe", KAYNAK + " · OECD TÜFE")

# 3) Paydanın gücü: NPL tutarı, toplam kredi ve fiyatlar (2015 = 100)
fig, ax = plt.subplots(figsize=(10, 4.8))
for k, ad, renk in [("npl", "Takipteki kredi tutarı", RENK["kirmizi"]), ("kredi", "Toplam kredi", RENK["mavi"]), ("tufe", "Tüketici fiyatları", RENK["gri"])]:
    ax.plot(B.index, B[k] / B[k].iloc[0] * 100, lw=2.4, color=renk, marker="o", ms=4, label=ad)
ax.set_yscale("log"); ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:g}"))
ax.set_title("Takipteki krediler son iki yılda hızlandı (2015 = 100, log ölçek)")
ax.legend(frameon=False)
kaydet(fig, "07_3_payda", KAYNAK + " · OECD")

# 4) Ülkeler arası: nominal ROE ve enflasyon
ulk = wb_ulkeler(); ad = ulk.set_index("ulke_kodu").ulke
son = TUM[TUM.INDICATOR == "ROE_CFSI_PT"].copy()
son["yil"] = son.TIME_PERIOD.astype(str).str[:4].astype(int)
son = son[son.yil.between(2023, 2025)].sort_values("yil").groupby("COUNTRY").last()
cpi = wb("FP.CPI.TOTL.ZG", donem="2023:2025")
cpi = cpi.dropna().sort_values("yil").groupby("ulke_kodu").last().deger
K = pd.DataFrame({"roe": son.OBS_VALUE, "enf": cpi}).dropna()
K = K[K.enf < 120]
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(K.enf, K.roe, s=28, alpha=0.55, color=RENK["mavi"], lw=0)
m = max(K.enf.max(), K.roe.max())
ax.plot([0, m], [0, m], color="black", ls="--", lw=1, label="ROE = enflasyon (reel kârlılık sıfır)")
for kod, isim in [("TUR", "Türkiye"), ("ARG", "Arjantin"), ("EGY", "Mısır"), ("NGA", "Nijerya"), ("USA", "ABD"), ("DEU", "Almanya"), ("BRA", "Brezilya"), ("POL", "Polonya"), ("PAK", "Pakistan"), ("GHA", "Gana"), ("UKR", "Ukrayna"), ("MEX", "Meksika")]:
    if kod in K.index:
        ax.annotate(isim, (K.enf[kod], K.roe[kod]), xytext=(4, 3), textcoords="offset points", fontsize=9,
                    color=RENK["kirmizi"] if kod == "TUR" else "#333", fontweight="bold" if kod == "TUR" else "normal")
if "TUR" in K.index:
    ax.scatter([K.enf["TUR"]], [K.roe["TUR"]], s=150, marker="*", color=RENK["kirmizi"], edgecolor="black", zorder=5)
ax.set_ylim(-5, 50); ax.set_xlim(-6, 45)
ax.set_xlabel("Enflasyon (%, son yıl)"); ax.set_ylabel("Bankacılık sektörü ROE (%, son yıl)")
disari = ((K.roe < -5) | (K.roe > 50)).sum()
print("eksen dışı ülke:", disari)
ax.set_title("Yüksek enflasyonlu ülkelerde nominal kârlılık yüksek görünüyor")
ax.legend(frameon=False)
kaydet(fig, "07_4_ulkeler_roe", KAYNAK + " · Dünya Bankası")
print("Ülke sayısı:", len(K), "TR:", K.loc["TUR"].round(1).to_dict() if "TUR" in K.index else None)

# 5) Kredi derinliği
kd = wb("FD.AST.PRVT.GD.ZS", donem="2005:2025")
gercek = set(ulk.ulke_kodu); gelir = ulk.set_index("ulke_kodu").gelir
kd = kd[kd.ulke_kodu.isin(gercek)].pivot_table(index="yil", columns="ulke_kodu", values="deger")
umi = [c for c in kd.columns if gelir.get(c) == "Upper middle income"]
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.plot(kd.index, kd["TUR"], color=RENK["kirmizi"], lw=2.8, marker="o", ms=3.5, label="Türkiye")
ax.plot(kd.index, kd[[c for c in OECD if c in kd]].median(axis=1), color="black", lw=2, label="OECD medyanı")
ax.plot(kd.index, kd[umi].median(axis=1), color=RENK["gri"], lw=2, ls="--", label="Üst-orta gelirli ülkeler medyanı")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Bankaların özel sektöre verdiği kredinin GSYH'ye oranı")
ax.legend(frameon=False)
kaydet(fig, "07_5_kredi_derinligi", "Dünya Bankası WDI")
print("Kredi/GSYH TR:", kd["TUR"].dropna().round(1).tail(8).to_dict())
print("OECD medyan son:", round(kd[[c for c in OECD if c in kd]].median(axis=1).dropna().iloc[-1], 1))

# Ülke karşılaştırması: NPL ve sermaye
for ind, ad_ in [("AQ12_CFSI_PT", "NPL"), ("FSI688_CFSI_PT", "SYR")]:
    s = TUM[TUM.INDICATOR == ind].copy(); s["yil"] = s.TIME_PERIOD.astype(str).str[:4].astype(int)
    s = s[s.yil.between(2023, 2025)].sort_values("yil").groupby("COUNTRY").last().OBS_VALUE
    print(f"{ad_}: TR {s.get('TUR'):.1f}, dünya medyanı {s.median():.1f}, OECD medyanı {s.reindex(OECD).median():.1f}, TR yüzdelik {s.rank(pct=True)['TUR']*100:.0f}")
