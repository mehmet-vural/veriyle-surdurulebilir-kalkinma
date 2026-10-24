"""Makale 17: Hava kirliliği ve maliyeti (SKA 11.6.2, 3.9.1) — DSÖ Hava Kalitesi Veri Tabanı v8 (2026), Dünya Bankası."""
import numpy as np
import pandas as pd
from ortak import RENK, VERI, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "DSÖ Ambient Air Quality Database v8.0 (Haziran 2026)"
d = pd.read_csv(VERI / "who_hava_2026.csv")
d = d[d.pm25_concentration.notna() & (d.pm25_tempcov.fillna(0) >= 75)]       # yılın en az %75'i ölçülmüş
d["sehir"] = d.city.str.replace(r"/[A-Z]{3}$", "", regex=True)
TRK = {"Igdir": "Iğdır", "Duzce": "Düzce", "Cankiri": "Çankırı", "Cayyolu": "Çayyolu", "Kumkoy": "Kumköy", "Gaziosmanpasa": "Gaziosmanpaşa",
       "Agli": "Ağlı", "Kuyulusebil": "Kuyulusebil", "Selcuklu": "Selçuklu", "Aralik": "Aralık", "Elbistan": "Elbistan",
       "Osmangazi": "Osmangazi", "Karatay": "Karatay", "Mamak": "Mamak", "Pendik": "Pendik"}
d["sehir"] = d.sehir.replace(TRK)
tr = d[d.iso3 == "TUR"]
print("TR yıllara göre (kapsama ≥%75) yerleşim sayısı:", tr.groupby("year").size().to_dict())
YIL = 2023
t = tr[tr.year == YIL].copy()
print(f"{YIL}: {len(t)} yerleşim; medyan PM2.5 {t.pm25_concentration.median():.1f}; ortalama {t.pm25_concentration.mean():.1f}")
esik = {"DSÖ kılavuz değeri (5)": 5, "Ara hedef 4 (10)": 10, "Ara hedef 3 (15)": 15, "Ara hedef 2 (25)": 25, "Ara hedef 1 (35)": 35}
for ad, e in esik.items():
    print(f"  {ad} üstü: %{100 * (t.pm25_concentration > e).mean():.0f}")

# 1) Dağılım
fig, ax = plt.subplots(figsize=(10.5, 4.6))
ax.hist(t.pm25_concentration.clip(upper=80), bins=np.arange(0, 82, 2.5), color=RENK["gri"], edgecolor="white")
for (ad, e), r in zip(esik.items(), [RENK["yesil"], "#7FB069", RENK["sari"], "#E07A1F", RENK["kirmizi"]]):
    ax.axvline(e, color=r, lw=2, ls="--"); ax.text(e + 0.4, ax.get_ylim()[1] * 0.92, ad, rotation=90, va="top", fontsize=8.5, color=r)
ax.set_xlabel("Yıllık ortalama PM2.5 (µg/m³)"); ax.set_ylabel("Yerleşim sayısı")
ax.set_title(f"Türkiye'de {len(t)} yerleşimde yıllık ortalama PM2.5 ({YIL}) ve DSÖ eşikleri")
kaydet(fig, "17_1_dagilim", KAYNAK)

# 2) En kirli ve en temiz yerleşimler
s = t.sort_values("pm25_concentration")
sec = pd.concat([s.head(6), s.tail(12)])
fig, ax = plt.subplots(figsize=(10, 6.4))
ax.barh(sec.sehir, sec.pm25_concentration, color=[RENK["yesil"] if v <= 15 else (RENK["sari"] if v <= 35 else RENK["kirmizi"]) for v in sec.pm25_concentration])
for i, v in enumerate(sec.pm25_concentration):
    ax.text(v + 0.6, i, f"{v:.0f}", va="center", fontsize=8.5)
ax.axvline(5, color=RENK["yesil"], ls="--", lw=1.2); ax.text(5.5, -0.9, "DSÖ kılavuzu: 5", fontsize=8.5, color=RENK["yesil"])
ax.axhline(5.5, color="black", lw=0.6)
ax.set_xlabel("Yıllık ortalama PM2.5 (µg/m³)")
ax.set_title(f"En temiz 6 ve en kirli 12 yerleşim ({YIL}, ölçüm kapsamı ≥ %75)")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "17_2_sehirler", KAYNAK)
print(s[["sehir", "pm25_concentration", "pm10_concentration", "number_stations"]].tail(12).round(1).to_string())

# 3) Avrupa karşılaştırması: ülke içindeki yerleşimlerin medyanı
AD = {"TUR": "Türkiye", "DEU": "Almanya", "FRA": "Fransa", "ITA": "İtalya", "ESP": "İspanya", "POL": "Polonya", "GRC": "Yunanistan",
      "BGR": "Bulgaristan", "ROU": "Romanya", "HUN": "Macaristan", "CZE": "Çekya", "SVK": "Slovakya", "AUT": "Avusturya",
      "NLD": "Hollanda", "BEL": "Belçika", "PRT": "Portekiz", "SWE": "İsveç", "FIN": "Finlandiya", "NOR": "Norveç", "GBR": "İngiltere",
      "IRL": "İrlanda", "DNK": "Danimarka", "HRV": "Hırvatistan", "SRB": "Sırbistan", "SVN": "Slovenya", "MKD": "K. Makedonya",
      "BIH": "Bosna-Hersek", "CHE": "İsviçre", "LTU": "Litvanya", "LVA": "Letonya", "EST": "Estonya", "CYP": "Kıbrıs", "ALB": "Arnavutluk", "MNE": "Karadağ"}
a = d[(d.year == YIL) & d.iso3.isin(AD)].groupby("iso3").agg(medyan=("pm25_concentration", "median"), n=("sehir", "size"))
a = a[a.n >= 3].sort_values("medyan")
fig, ax = plt.subplots(figsize=(10, 7.2))
ax.barh([AD[k] for k in a.index], a.medyan, color=[RENK["kirmizi"] if k == "TUR" else RENK["gri"] for k in a.index])
for i, (k, r) in enumerate(a.iterrows()):
    ax.text(r.medyan + 0.3, i, f"{r.medyan:.1f}  (n={int(r.n)})".replace(".", ","), va="center", fontsize=8.5)
ax.axvline(5, color=RENK["yesil"], ls="--", lw=1.2)
ax.set_xlabel("Ölçüm yapılan yerleşimlerin medyan PM2.5 değeri (µg/m³)")
ax.set_title(f"Avrupa'da hava kirliliği: Ülkelere göre yerleşimlerin medyan PM2.5 değeri ({YIL})")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "17_3_avrupa", KAYNAK)
print("TR sıra (kirliden):", int(a.medyan.rank(ascending=False)["TUR"]), "/", len(a), "| AB üyelerinin medyanı:",
      round(a.drop(["TUR", "SRB", "MKD", "BIH", "CHE", "NOR", "GBR", "ALB", "MNE"], errors="ignore").medyan.median(), 1))

# 4) Eğilim: her iki dönemde de ölçüm olan yerleşimler
p = tr.pivot_table(index="sehir", columns="year", values="pm25_concentration")
ortak = p[[2019, 2023]].dropna() if 2019 in p and 2023 in p else pd.DataFrame()
print("2019 ve 2023'te ortak yerleşim:", len(ortak), "medyan 2019→2023:", ortak.median().round(1).to_dict() if len(ortak) else None,
      "iyileşen oranı %", round(100 * (ortak[2023] < ortak[2019]).mean()) if len(ortak) else None)
yillik = tr.groupby("year").pm25_concentration.median()
print("Yıllık medyan (örneklem değişiyor):", yillik.round(1).to_dict())

# 5) Sağlık ve ekonomik maliyet (Dünya Bankası)
import sys
if '--wb-yok' in sys.argv:
    sys.exit(0)
ulk = wb_ulkeler(); gercek = set(ulk.ulke_kodu)
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
for kod, ad in [("SH.STA.AIRP.P5", "Hava kirliliğine bağlı ölüm (100 bin kişide, yaşa göre standartlaştırılmış) [SKA 3.9.1]"),
                ("NY.ADJ.DPEM.GN.ZS", "Partikül emisyonu hasarı (GSMG %)"), ("EN.ATM.PM25.MC.M3", "Ulusal nüfus ağırlıklı PM2.5")]:
    x = wb(kod, donem="2010:2025"); x = x[x.ulke_kodu.isin(gercek)].dropna().sort_values("yil").groupby("ulke_kodu").last()
    print(f"{ad}: TR {x.deger.get('TUR'):.2f} ({int(x.yil.get('TUR'))}), OECD medyanı {x.deger.reindex(OECD).median():.2f}, "
          f"OECD sırası (kötüden) {int(x.deger.reindex(OECD).dropna().rank(ascending=False)['TUR'])}/{x.deger.reindex(OECD).notna().sum()}")
gsmg = wb("NY.GNP.MKTP.CD", "TUR", "2018:2024").dropna().sort_values("yil")
print("TR GSMG son:", int(gsmg.yil.iloc[-1]), round(gsmg.deger.iloc[-1] / 1e9), "mlr $")
