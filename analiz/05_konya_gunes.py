"""Makale 5: Konya'da çatı güneş enerjisi yatırımı — PVGIS üretim verisi + NBD/İVO/LCOE + duyarlılık."""
import json

import numpy as np
import pandas as pd
import requests
from ortak import RENK, VERI, indir, kaydet, mtick, plt

SEHIRLER = {"Konya": (37.87, 32.49), "Antalya": (36.90, 30.70), "Ankara": (39.93, 32.86), "İzmir": (38.42, 27.14),
            "Diyarbakır": (37.91, 40.23), "İstanbul": (41.01, 28.98), "Trabzon": (41.00, 39.72),
            "Berlin (Almanya)": (52.52, 13.40)}


def pvgis(ad, lat, lon):
    yol = VERI / f"pvgis_{ad.split()[0]}.json"
    if not yol.exists():
        r = requests.get("https://re.jrc.ec.europa.eu/api/v5_3/PVcalc",
                         params={"lat": lat, "lon": lon, "peakpower": 1, "loss": 14, "optimalangles": 1,
                                 "outputformat": "json"}, timeout=120)
        r.raise_for_status(); yol.write_text(r.text)
    return json.loads(yol.read_text())


veri = {ad: pvgis(ad, *k) for ad, k in SEHIRLER.items()}
yillik = pd.Series({ad: v["outputs"]["totals"]["fixed"]["E_y"] for ad, v in veri.items()}).sort_values()
aci = {ad: v["inputs"]["mounting_system"]["fixed"]["slope"]["value"] for ad, v in veri.items()}
aylik = pd.DataFrame({ad: [m["E_m"] for m in v["outputs"]["monthly"]["fixed"]] for ad, v in veri.items()},
                     index=range(1, 13))
print("Yıllık kWh/kWp:", yillik.round(0).to_dict()); print("Eğim:", aci)
print("Konya yıllık değişkenlik (SD_y):", veri["Konya"]["outputs"]["totals"]["fixed"]["SD_y"])

# Elektrik şebekesinin karbon yoğunluğu (Our World in Data / Ember)
co2 = pd.read_csv(indir("https://ourworldindata.org/grapher/carbon-intensity-electricity.csv?v=1&csvType=full&useColumnShortNames=true",
                        "owid_karbon_yogunlugu.csv"))
co2_tr = co2[co2.code == "TUR"].sort_values("year").iloc[-1]
deger_sutun = [c for c in co2.columns if c not in ("entity", "code", "year")][0]
gco2 = co2_tr[deger_sutun]
print(f"Türkiye elektrik karbon yoğunluğu {int(co2_tr.year)}: {gco2:.0f} gCO2/kWh")

# --- Finansal model (reel, ABD doları) ---
KWP, OMRU, BOZULMA = 5, 25, 0.005


def nakit_akisi(maliyet_kwp, fiyat, uretim_kwp, oran, om=0.01, inverter_yil=12, inverter_pay=0.10):
    yatirim = maliyet_kwp * KWP
    yillar = np.arange(1, OMRU + 1)
    enerji = uretim_kwp * KWP * (1 - BOZULMA) ** (yillar - 1)
    akis = enerji * fiyat - om * yatirim
    akis[inverter_yil - 1] -= inverter_pay * yatirim
    iskonto = (1 + oran) ** -yillar
    nbd = -yatirim + (akis * iskonto).sum()
    lcoe = (yatirim + ((om * yatirim) * iskonto).sum() + inverter_pay * yatirim * iskonto[inverter_yil - 1]) / (enerji * iskonto).sum()
    kum = -yatirim + np.cumsum(akis * iskonto)
    geri = next((y for y in yillar if kum[y - 1] >= 0), np.nan)
    # İVO: NBD = 0 yapan oran (ikiye bölme)
    alt, ust = -0.5, 1.0
    for _ in range(80):
        o = (alt + ust) / 2
        (alt, ust) = (o, ust) if -yatirim + (akis * (1 + o) ** -yillar).sum() > 0 else (alt, o)
    return dict(yatirim=yatirim, nbd=nbd, lcoe=lcoe, geri=geri, ivo=(alt + ust) / 2, kum=kum, enerji=enerji)


TABAN = dict(maliyet_kwp=900, fiyat=0.12, oran=0.07)
konya = yillik["Konya"]
t = nakit_akisi(TABAN["maliyet_kwp"], TABAN["fiyat"], konya, TABAN["oran"])
print(f"Konya taban: yatırım {t['yatirim']:.0f}$, NBD {t['nbd']:.0f}$, LCOE {t['lcoe']:.3f}$/kWh, geri dönüş {t['geri']} yıl, İVO %{100*t['ivo']:.1f}")
print(f"İlk yıl üretim {t['enerji'][0]:.0f} kWh, 25 yıl toplam {t['enerji'].sum():.0f} kWh, kaçınılan CO2 ~{t['enerji'].sum()*gco2/1e6:.1f} ton")
for sehir in ["Berlin (Almanya)", "İstanbul", "Antalya"]:
    s = nakit_akisi(TABAN["maliyet_kwp"], TABAN["fiyat"], yillik[sehir], TABAN["oran"])
    print(f"  {sehir}: NBD {s['nbd']:.0f}, LCOE {s['lcoe']:.3f}, geri {s['geri']}, İVO %{100*s['ivo']:.1f}")

# 1) Şehirlere göre yıllık üretim
fig, ax = plt.subplots(figsize=(10, 4.8))
renkler = [RENK["kirmizi"] if a == "Konya" else (RENK["gri"] if "Berlin" in a else RENK["sari"]) for a in yillik.index]
c = ax.barh(yillik.index, yillik.values, color=renkler)
ax.bar_label(c, labels=[f"{v:,.0f} kWh".replace(",", ".") for v in yillik.values], padding=4)
ax.set_xlim(0, yillik.max() * 1.18)
ax.set_title("1 kWp panelin yıllık elektrik üretimi (en uygun eğim, 2005–2023 ortalaması)")
ax.set_xlabel("kWh / yıl"); ax.grid(axis="y", visible=False)
kaydet(fig, "05_1_sehirler", "AB Ortak Araştırma Merkezi, PVGIS 5.3")

# 2) Konya aylık üretim (5 kWp)
fig, ax = plt.subplots(figsize=(10, 4.4))
aylar = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
ax.bar(aylar, aylik["Konya"] * KWP, color=RENK["sari"], label="Konya")
ax.plot(aylar, aylik["Berlin (Almanya)"] * KWP, color=RENK["gri"], marker="o", lw=2, label="Berlin (karşılaştırma)")
ax.set_ylabel("kWh / ay"); ax.legend(frameon=False)
ax.set_title(f"5 kWp çatı sisteminin aylık üretimi: Konya'da yılda {konya * KWP:,.0f} kWh".replace(",", "."))
kaydet(fig, "05_2_aylik", "PVGIS 5.3")

# 3) Kümülatif iskontolu nakit akışı
fig, ax = plt.subplots(figsize=(10, 4.8))
for sehir, renk in [("Konya", RENK["kirmizi"]), ("İstanbul", RENK["mavi"]), ("Berlin (Almanya)", RENK["gri"])]:
    s = nakit_akisi(TABAN["maliyet_kwp"], TABAN["fiyat"], yillik[sehir], TABAN["oran"])
    ax.plot(range(0, OMRU + 1), np.r_[-s["yatirim"], s["kum"]], lw=2.4, color=renk, label=f"{sehir} (NBD {s['nbd']:,.0f} $)".replace(",", "."))
ax.axhline(0, color="black", lw=0.8)
ax.set_xlabel("Yıl"); ax.set_ylabel("Kümülatif iskontolu nakit akışı ($)")
ax.set_title("Aynı sistem, aynı fiyatlar: Güneş ne kadar fark yaratıyor?")
ax.legend(frameon=False)
kaydet(fig, "05_3_nakit", "PVGIS 5.3 · varsayımlar yazıda")

# 4) Duyarlılık: geri dönüş süresi (maliyet × elektrik fiyatı)
maliyetler = np.arange(500, 1501, 100)
fiyatlar = np.round(np.arange(0.06, 0.205, 0.02), 2)
tablo = pd.DataFrame([[nakit_akisi(m, f, konya, TABAN["oran"])["geri"] for f in fiyatlar] for m in maliyetler],
                     index=maliyetler, columns=fiyatlar)
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(tablo.fillna(30).values, cmap="RdYlGn_r", vmin=3, vmax=25, aspect="auto", origin="lower")
for i in range(len(maliyetler)):
    for j in range(len(fiyatlar)):
        v = tablo.iloc[i, j]
        ax.text(j, i, "—" if np.isnan(v) else f"{v:.0f}", ha="center", va="center", fontsize=9,
                color="black")
ax.set_xticks(range(len(fiyatlar)), [f"{f:.2f}" for f in fiyatlar]); ax.set_yticks(range(len(maliyetler)), maliyetler)
ax.set_xlabel("Elektrik fiyatı ($/kWh)"); ax.set_ylabel("Kurulum maliyeti ($/kWp)")
ax.set_title("Konya: İskontolu geri dönüş süresi (yıl) · reel iskonto %7\n“—” = 25 yılda geri dönmüyor")
ax.grid(False)
kaydet(fig, "05_4_duyarlilik", "PVGIS 5.3")
print(tablo)

# İVO tablosu ve iskonto oranı duyarlılığı
print("İVO (taban maliyet), fiyatlara göre:", {f: round(100 * nakit_akisi(900, f, konya, 0.07)["ivo"], 1) for f in fiyatlar})
print("NBD iskonto oranına göre:", {o: round(nakit_akisi(900, 0.12, konya, o)["nbd"]) for o in [0.04, 0.07, 0.10, 0.13]})
# Şebekeye satış senaryosu: üretimin %40'ı evde tüketiliyor, %60'ı perakendenin yarısına satılıyor
etkin = TABAN["fiyat"] * (0.4 + 0.6 * 0.5)
s = nakit_akisi(TABAN["maliyet_kwp"], etkin, konya, TABAN["oran"])
print(f"Satış senaryosu (etkin fiyat {etkin:.3f}): NBD {s['nbd']:.0f}, geri {s['geri']}, İVO %{100*s['ivo']:.1f}")
print("Başabaş fiyat (LCOE) maliyetlere göre:", {m: round(nakit_akisi(m, 0.12, konya, 0.07)["lcoe"], 3) for m in maliyetler})
