"""Makale 6: Konya Havzası'nda kuraklık — NASA POWER (1981–2025), SPI-12, eğilim testleri, Thornthwaite su dengesi."""
import json
from calendar import monthrange

import numpy as np
import pandas as pd
from scipy import stats
from ortak import RENK, VERI, kaydet, mtick, plt

KAYNAK = "NASA POWER (MERRA-2) · Konya 37,87K 32,49D"
p = json.load(open(VERI / "nasa_power_konya.json"))["properties"]["parameter"]
kayit = []
for k, v in p["PRECTOTCORR"].items():
    yil, ay = int(k[:4]), int(k[4:])
    if ay == 13:
        continue
    gun = monthrange(yil, ay)[1]
    kayit.append({"tarih": pd.Timestamp(yil, ay, 1), "yil": yil, "ay": ay, "yagis": v * gun,
                  "sicaklik": p["T2M"][k], "maks": p["T2M_MAX"][k], "gun": gun})
D = pd.DataFrame(kayit).set_index("tarih").sort_index()
D = D[D.yagis >= 0]

# Thornthwaite potansiyel evapotranspirasyon (PET)
enlem = np.radians(37.87)
def gun_uzunlugu(ay):
    j = pd.Timestamp(2001, ay, 15).day_of_year
    delta = 0.409 * np.sin(2 * np.pi * j / 365 - 1.39)
    return 24 / np.pi * np.arccos(-np.tan(enlem) * np.tan(delta))
D["N"] = D.ay.map(gun_uzunlugu)
yillik_I = D.assign(i=(D.sicaklik.clip(lower=0) / 5) ** 1.514).groupby("yil").i.sum()
D["I"] = D.yil.map(yillik_I)
a = 6.75e-7 * D.I ** 3 - 7.71e-5 * D.I ** 2 + 1.792e-2 * D.I + 0.49239
D["pet"] = np.where(D.sicaklik > 0, 16 * (D.N / 12) * (D.gun / 30) * (10 * D.sicaklik.clip(lower=0) / D.I) ** a, 0)

Y = D.groupby("yil").agg(yagis=("yagis", "sum"), sicaklik=("sicaklik", "mean"), pet=("pet", "sum"),
                         yaz_maks=("maks", lambda s: s[D.loc[s.index, "ay"].between(6, 8)].mean()))
Y["denge"] = Y.yagis - Y.pet


def egilim(s):
    r = stats.linregress(s.index, s.values)
    tau, pmk = stats.kendalltau(s.index, s.values)
    return r.slope * 10, r.pvalue, tau, pmk


for ad in ["sicaklik", "yaz_maks", "yagis", "pet", "denge"]:
    e = egilim(Y[ad])
    print(f"{ad}: on yılda {e[0]:+.2f} · OLS p={e[1]:.3f} · Kendall tau={e[2]:+.2f} p={e[3]:.3f}")
for bas, bit in [(1981, 2000), (2006, 2025)]:
    s = Y.loc[bas:bit]
    print(f"{bas}-{bit}: sıcaklık {s.sicaklik.mean():.2f}°C, yağış {s.yagis.mean():.0f} mm, PET {s.pet.mean():.0f} mm, denge {s.denge.mean():.0f} mm")

# SPI-12: 12 aylık toplam yağış, her takvim ayı için gama dağılımı → standart normal
D["y12"] = D.yagis.rolling(12).sum()
spi = pd.Series(np.nan, index=D.index)
for ay in range(1, 13):
    s = D.loc[D.ay == ay, "y12"].dropna()
    sifir = (s == 0).mean()
    sh, loc, sc = stats.gamma.fit(s[s > 0], floc=0)
    F = sifir + (1 - sifir) * stats.gamma.cdf(s, sh, loc=0, scale=sc)
    spi[s.index] = stats.norm.ppf(np.clip(F, 1e-6, 1 - 1e-6))
D["spi12"] = spi
kurak = D.spi12 < -1
print("SPI-12 < -1 olan ay oranı: 1981–2000 %{:.0f}, 2006–2025 %{:.0f}".format(
    100 * kurak["1982":"2000"].mean(), 100 * kurak["2006":"2025"].mean()))
print("En kurak 12 aylık dönemler:", D.spi12.nsmallest(5).round(2).to_dict())
D.to_csv(VERI / "06_konya_aylik.csv")

# Grafik 1: sıcaklık
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.plot(Y.index, Y.sicaklik, color=RENK["kirmizi"], marker="o", ms=3.5, lw=1.6, label="Yıllık ortalama sıcaklık")
e = stats.linregress(Y.index, Y.sicaklik)
ax.plot(Y.index, e.intercept + e.slope * Y.index, color="black", ls="--", lw=1.4,
        label=f"Eğilim: on yılda +{10 * e.slope:.2f} °C".replace(".", ","))
ax.set_ylabel("°C"); ax.legend(frameon=False)
ax.set_title(f"Konya ısınıyor: 1981'den bu yana yaklaşık +{e.slope * (Y.index[-1] - Y.index[0]):.1f} °C".replace(".", ","))
kaydet(fig, "06_1_sicaklik", KAYNAK)

# Grafik 2: yağış ve buharlaşma ihtiyacı
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar(Y.index, Y.yagis, color=RENK["mavi"], alpha=0.75, label="Yıllık yağış")
ax.plot(Y.index, Y.pet, color=RENK["sari"], lw=2.4, label="Potansiyel buharlaşma ihtiyacı (Thornthwaite)")
ax.plot(Y.index, Y.yagis.rolling(10, center=True).mean(), color=RENK["mavi"], lw=2.4, ls="--", label="Yağış, 10 yıllık hareketli ortalama")
ax.set_ylabel("mm / yıl"); ax.legend(frameon=False, loc="upper left", fontsize=9.5)
ax.set_title("Yağış yatay seyrediyor, atmosferin su talebi artıyor")
kaydet(fig, "06_2_yagis_pet", KAYNAK)

# Grafik 3: SPI-12
fig, ax = plt.subplots(figsize=(11, 4.8))
s = D.spi12.dropna()
ax.fill_between(s.index, 0, s, where=s >= 0, color=RENK["mavi"], alpha=0.6, lw=0)
ax.fill_between(s.index, 0, s, where=s < 0, color=RENK["kirmizi"], alpha=0.6, lw=0)
for esik, ad in [(-1, "orta kuraklık"), (-1.5, "şiddetli"), (-2, "aşırı")]:
    ax.axhline(esik, color="black", lw=0.6, ls=":")
    ax.text(s.index[0], esik - 0.18, ad, fontsize=8.5, color="#444")
ax.axhline(0, color="black", lw=0.8)
ax.set_title("Standartlaştırılmış Yağış İndeksi (SPI-12): Konya'da kurak ve yağışlı dönemler")
ax.set_ylabel("SPI-12")
kaydet(fig, "06_3_spi", KAYNAK)

# Grafik 4: iklimsel su dengesi
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(Y.index, Y.denge, color=[RENK["kirmizi"] if v < Y.denge.median() else RENK["sari"] for v in Y.denge])
e = stats.linregress(Y.index, Y.denge)
ax.plot(Y.index, e.intercept + e.slope * Y.index, color="black", ls="--", lw=1.4,
        label=f"Eğilim: on yılda {10 * e.slope:+.0f} mm")
ax.axhline(0, color="black", lw=0.8)
ax.set_ylabel("Yağış − buharlaşma ihtiyacı (mm)"); ax.legend(frameon=False)
ax.set_title("İklimsel su dengesi: 2025, 1981'den bu yana en büyük açığın yaşandığı yıl")
kaydet(fig, "06_4_su_dengesi", KAYNAK)
print(Y.round(1).tail(6))
