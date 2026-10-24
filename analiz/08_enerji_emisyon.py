"""Makale 8: Türkiye'nin enerji dönüşümü ve emisyonları — OWID enerji/CO2, Kaya (LMDI) ayrıştırması, 2053 yolu."""
import numpy as np
import pandas as pd
from ortak import RENK, VERI, kaydet, mtick, plt, wb

KAYNAK = "Our World in Data (Ember, Energy Institute, Global Carbon Project)"
E = pd.read_csv(VERI / "owid_energy.csv")
C = pd.read_csv(VERI / "owid_co2.csv")
te = E[E.iso_code == "TUR"].set_index("year")
tc = C[C.iso_code == "TUR"].set_index("year")

# 1) Elektrik üretim karışımı (pay, %)
kaynaklar = [("coal", "Kömür", "#4D4D4D"), ("gas", "Doğal gaz", "#8C6D46"), ("oil", "Petrol", "#B08ED1"),
             ("hydro", "Hidroelektrik", "#1F77B4"), ("wind", "Rüzgâr", "#2CA6A4"), ("solar", "Güneş", "#F2B701"),
             ("other_renewables", "Diğer yenilenebilir (jeotermal, biyokütle)", "#6BA539")]
pay = pd.DataFrame({ad: te[f"{k}_share_elec"] for k, ad, _ in kaynaklar}).loc[2000:].fillna(0)
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.stackplot(pay.index, pay.T.values, labels=pay.columns, colors=[r for _, _, r in kaynaklar], alpha=0.92)
ax.set_xlim(2000, pay.index.max()); ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("Türkiye'nin elektrik üretim karışımı")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=9.5)
kaydet(fig, "08_1_karisim", KAYNAK)
print(pay.round(1).loc[[2005, 2015, 2020, 2023, 2024, 2025]].to_string())

# 2) Rüzgâr ve güneş üretimi (TWh)
rs = te[["wind_electricity", "solar_electricity", "hydro_electricity"]].loc[2010:]
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(rs.index, rs.wind_electricity, color="#2CA6A4", label="Rüzgâr")
ax.bar(rs.index, rs.solar_electricity, bottom=rs.wind_electricity, color="#F2B701", label="Güneş")
ax.plot(rs.index, rs.hydro_electricity, color="#1F77B4", lw=2.4, marker="o", ms=4, label="Hidroelektrik (karşılaştırma)")
ax.set_ylabel("TWh"); ax.legend(frameon=False, loc="upper left")
ax.set_title("Rüzgâr ve güneş hızla büyüyor; hidroelektrik yağışa bağlı dalgalanıyor")
kaydet(fig, "08_2_ruzgar_gunes", KAYNAK)
print(rs.round(1).tail(6).to_string())

# 3) CO2 emisyonları ve 2053 yolları
co2 = tc.co2.loc[1990:].dropna()
son_yil, son = co2.index.max(), co2.iloc[-1]
b = np.polyfit(np.arange(2015, son_yil + 1), np.log(co2.loc[2015:son_yil]), 1)[0]
yillar = np.arange(son_yil, 2054)
egilim = son * np.exp(b * (yillar - son_yil))
dogrusal = son * (2053 - yillar) / (2053 - son_yil)
gerekli_oran = (1 - (son * 0.1 / son) ** (1 / (2053 - son_yil)))   # %90 azaltım için yıllık oran (bilgi)
fig, ax = plt.subplots(figsize=(10.5, 5))
ax.plot(co2.index, co2, color="black", lw=2.6, label="Gerçekleşen CO₂")
ax.plot(yillar, egilim, color=RENK["kirmizi"], ls="--", lw=2, label=f"2015–{son_yil} eğilimi sürerse (yılda +%{100 * b:.1f})".replace(".", ","))
ax.plot(yillar, dogrusal, color=RENK["yesil"], lw=2.2, label=f"2053'te sıfıra doğrusal yol (yılda −{son / (2053 - son_yil):.0f} Mt)")
ax.fill_between(yillar, dogrusal, egilim, color=RENK["kirmizi"], alpha=0.08)
ax.set_ylabel("Milyon ton CO₂"); ax.set_xlim(1990, 2054); ax.set_ylim(0, egilim.max() * 1.05)
ax.set_title(f"Türkiye'nin CO₂ emisyonları: {son_yil}'te rekor {son:.0f} Mt")
ax.legend(frameon=False, loc="upper left")
kaydet(fig, "08_3_co2_yollar", "Global Carbon Project (OWID)")
print(f"CO2 {son_yil}: {son:.1f} Mt; 2015-{son_yil} yıllık büyüme %{100*b:.2f}; 1990: {co2.loc[1990]:.0f}; doğrusal yol yılda {son/(2053-son_yil):.1f} Mt (%{100*son/(2053-son_yil)/son:.1f} ilk yıl)")
print(f"Eğilim sürerse 2053: {egilim[-1]:.0f} Mt; 2030: {egilim[yillar == 2030][0]:.0f} Mt")

# 4) Kaya ayrıştırması (LMDI-I): CO2 = Nüfus × (GSYH/Nüfus) × (Enerji/GSYH) × (CO2/Enerji)
gsyh = wb("NY.GDP.MKTP.PP.KD", "TUR", "2000:2025").set_index("yil").deger
K = pd.DataFrame({"co2": tc.co2, "nufus": tc.population, "enerji": tc.primary_energy_consumption, "gsyh": gsyh}).dropna()
bas, bit = 2005, K.index.max()
f = lambda y: dict(nufus=K.nufus[y], refah=K.gsyh[y] / K.nufus[y], yogunluk=K.enerji[y] / K.gsyh[y], karbon=K.co2[y] / K.enerji[y])
f0, f1 = f(bas), f(bit)
L = (K.co2[bit] - K.co2[bas]) / np.log(K.co2[bit] / K.co2[bas])
katki = {k: L * np.log(f1[k] / f0[k]) for k in f0}
print(f"Kaya {bas}-{bit}: toplam değişim {K.co2[bit] - K.co2[bas]:.0f} Mt; katkılar:", {k: round(v) for k, v in katki.items()}, "toplam kontrol", round(sum(katki.values())))
etiket = {"nufus": "Nüfus artışı", "refah": "Kişi başı gelir artışı", "yogunluk": "Enerji yoğunluğu\n(GSYH başına enerji)",
          "karbon": "Karbon yoğunluğu\n(enerji başına CO₂)"}
fig, ax = plt.subplots(figsize=(10, 4.8))
deger = list(katki.values()) + [sum(katki.values())]
adlar = [etiket[k] for k in katki] + [f"Toplam değişim\n{bas}→{bit}"]
c = ax.bar(adlar, deger, color=[RENK["kirmizi"] if v > 0 else RENK["yesil"] for v in deger[:-1]] + ["black"])
ax.bar_label(c, labels=[f"{v:+.0f} Mt" for v in deger], padding=3)
ax.axhline(0, color="black", lw=0.8)
ax.set_ylabel("CO₂ değişimine katkı (milyon ton)")
ax.set_title(f"Emisyonlar neden arttı? Kaya ayrıştırması ({bas}–{bit})")
ax.grid(axis="x", visible=False)
kaydet(fig, "08_4_kaya", "OWID · Dünya Bankası · LMDI yöntemi")

# 5) Kişi başı CO2 karşılaştırması
fig, ax = plt.subplots(figsize=(10, 4.6))
for ad, kod, renk, lw in [("Türkiye", "TUR", RENK["kirmizi"], 2.8), ("Avrupa Birliği", "European Union (27)", RENK["mavi"], 2),
                          ("Dünya", "World", "black", 2), ("Çin", "CHN", RENK["sari"], 2)]:
    s = (C[C.iso_code == kod] if len(kod) == 3 else C[C.country == kod]).set_index("year").co2_per_capita.loc[1990:]
    ax.plot(s.index, s, color=renk, lw=lw, label=ad)
ax.set_ylabel("ton CO₂ / kişi"); ax.legend(frameon=False)
ax.set_title("Kişi başı CO₂: Türkiye artık Avrupa Birliği ortalamasının üstünde")
kaydet(fig, "08_5_kisi_basi", "Global Carbon Project (OWID)")
for kod in ["TUR", "CHN", "World", "European Union (27)"]:
    s = (C[C.iso_code == kod] if len(kod) == 3 else C[C.country == kod]).set_index("year").co2_per_capita
    print(kod, {y: round(s.get(y, np.nan), 2) for y in [1990, 2005, 2015, 2024]})
print("Yenilenebilir pay elektrik:", te.renewables_share_elec.loc[[2005, 2015, 2020, 2024, 2025]].round(1).to_dict())
print("Karbon yoğunluğu g/kWh:", te.carbon_intensity_elec.loc[[2005, 2015, 2024, 2025]].round(0).to_dict())
