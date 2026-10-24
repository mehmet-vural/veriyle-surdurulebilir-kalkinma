"""Makale 14: AB Sınırda Karbon Düzenlemesi (SKDM/CBAM) ve Türk ihracatı — UN Comtrade."""
import hashlib
import json
import time

import numpy as np
import pandas as pd
import requests
from ortak import RENK, VERI, kaydet, mtick, plt

AB27 = {40: "Avusturya", 56: "Belçika", 100: "Bulgaristan", 191: "Hırvatistan", 196: "Kıbrıs", 203: "Çekya", 208: "Danimarka",
        233: "Estonya", 246: "Finlandiya", 251: "Fransa", 276: "Almanya", 300: "Yunanistan", 348: "Macaristan", 372: "İrlanda",
        380: "İtalya", 428: "Letonya", 440: "Litvanya", 442: "Lüksemburg", 470: "Malta", 528: "Hollanda", 616: "Polonya",
        620: "Portekiz", 642: "Romanya", 703: "Slovakya", 705: "Slovenya", 724: "İspanya", 752: "İsveç"}
URUN = {"72": "Demir ve çelik (72)", "73": "Demir-çelik eşya (73)", "76": "Alüminyum (76)", "2523": "Çimento (2523)",
        "3102": "Azotlu gübreler (3102)", "3105": "Karma gübreler (3105)", "2814": "Amonyak (2814)", "2804": "Hidrojen vb. (2804)",
        "2716": "Elektrik (2716)"}


def comtrade(yil, ortaklar, urunler):
    anahtar = hashlib.md5(f"{ortaklar}{urunler}".encode()).hexdigest()[:10]
    yol = VERI / f"comtrade_tur_{yil}_{anahtar}.json"
    if not yol.exists():
        for deneme in range(8):
            r = requests.get("https://comtradeapi.un.org/public/v1/preview/C/A/HS",
                             params={"reporterCode": 792, "period": yil, "partnerCode": ",".join(map(str, ortaklar)),
                                     "cmdCode": ",".join(urunler), "flowCode": "X"}, timeout=180)
            if r.status_code == 429:
                time.sleep(20 * (deneme + 1)); continue
            r.raise_for_status(); yol.write_text(r.text); time.sleep(8); break
        else:
            raise RuntimeError("Comtrade sınırı aşıldı")
    return pd.DataFrame(json.loads(yol.read_text())["data"])


satir = []
for yil in [2019, 2021, 2023, 2024]:
    try:
        d1 = comtrade(yil, list(AB27)[:14], list(URUN)); d2 = comtrade(yil, list(AB27)[14:], list(URUN))
        dt = comtrade(yil, list(AB27) + [0], ["TOTAL"])
    except Exception as e:
        print(yil, "hata", e); continue
    d = pd.concat([d1, d2])
    if d.empty:
        print(yil, "veri yok"); continue
    d["yil"] = yil; satir.append(d)
    ab_toplam = dt[dt.partnerCode != 0].primaryValue.sum(); dunya = dt[dt.partnerCode == 0].primaryValue.sum()
    print(yil, f"AB'ye toplam ihracat {ab_toplam / 1e9:.1f} mlr $, dünyaya {dunya / 1e9:.1f} mlr $ (AB payı %{100 * ab_toplam / dunya:.0f});",
          f"SKDM ürünleri AB'ye {d.primaryValue.sum() / 1e9:.2f} mlr $ (%{100 * d.primaryValue.sum() / ab_toplam:.1f})")
    if yil == max(2019, yil):
        TOPLAM = {"yil": yil, "ab": ab_toplam, "dunya": dunya}
D = pd.concat(satir)
D.to_csv(VERI / "14_comtrade_skdm.csv", index=False)
son_yil = D.yil.max()
S = D[D.yil == son_yil]

# 1) Ürün bazında AB'ye ihracat (son yıl)
U = S.groupby("cmdCode").agg(deger=("primaryValue", "sum"), ton=("netWgt", "sum"))
U["ton"] = U.ton / 1000
U.index = U.index.map(URUN)
# 72, 73, 76 bölüm düzeyinde ağırlık yok: 4 haneli kalemlerde dünyaya ihracatın birim değerini kullan
HS4 = {"72": [f"72{i:02d}" for i in range(1, 30)], "73": [f"73{i:02d}" for i in range(1, 27)], "76": [f"76{i:02d}" for i in range(1, 17)]}
for bolum, kalemler in HS4.items():
    w = comtrade(son_yil, [0], kalemler)
    w = w[(w.netWgt.fillna(0) > 0)]
    bd = w.primaryValue.sum() / (w.netWgt.sum() / 1000)
    ad = URUN[bolum]
    print(f"{ad}: dünya ihracatı birim değeri {bd:,.0f} $/t ({len(w)} kalem)")
    U.loc[ad, "ton"] = U.loc[ad, "deger"] / bd if ad in U.index else np.nan
U["birim_deger"] = U.deger / U.ton     # $ / ton
U = U.sort_values("deger")
print(U.round(0))
fig, ax = plt.subplots(figsize=(10, 4.8))
c = ax.barh(U.index, U.deger / 1e9, color=RENK["mavi"])
ax.bar_label(c, labels=[f"{v / 1e9:.2f} mlr $".replace(".", ",") for v in U.deger], padding=3, fontsize=9)
ax.set_xlim(0, U.deger.max() / 1e9 * 1.25)
ax.set_title(f"SKDM kapsamındaki ürünlerde Türkiye'nin AB'ye ihracatı ({son_yil})")
ax.set_xlabel("Milyar ABD doları"); ax.grid(axis="y", visible=False)
kaydet(fig, "14_1_urunler", "BM Comtrade")

# 2) Hedef ülkeler
P = S.groupby("partnerCode").primaryValue.sum()
P.index = [AB27.get(int(k), str(k)) for k in P.index]
print("eşleşmeyen ortak kodları:", [k for k in S.partnerCode.unique() if int(k) not in AB27])
P = P.sort_values().tail(10)
fig, ax = plt.subplots(figsize=(10, 4.6))
c = ax.barh(P.index, P.values / 1e9, color=RENK["sari"])
ax.bar_label(c, labels=[f"{v / 1e9:.2f}".replace(".", ",") for v in P.values], padding=3, fontsize=9)
ax.set_title(f"SKDM ürünlerinde en büyük 10 AB pazarı ({son_yil}, milyar $)")
ax.grid(axis="y", visible=False); ax.set_xlim(0, P.max() / 1e9 * 1.2)
kaydet(fig, "14_2_ulkeler", "BM Comtrade")
print(P.round(-6).to_dict())

# 3) Yıllara göre
Y = D.groupby(["yil", "cmdCode"]).primaryValue.sum().unstack().fillna(0) / 1e9
Y.columns = [URUN[c] for c in Y.columns]
print(Y.round(2))

# 4) Duyarlılık: SKDM maliyeti / ihracat değeri (emisyon yoğunluğu × karbon fiyatı / birim değer)
yogunluk = [0.5, 1.0, 1.5, 2.0, 3.0]                # ton CO2 / ton ürün
fiyat_eur, kur = 80, 1.08                            # € / ton CO2, $ / €
ana = [u for u in ["Demir ve çelik (72)", "Demir-çelik eşya (73)", "Alüminyum (76)", "Çimento (2523)", "Azotlu gübreler (3102)"] if u in U.index]
M = pd.DataFrame({y: (y * fiyat_eur * kur) / U.loc[ana, "birim_deger"] * 100 for y in yogunluk})
fig, ax = plt.subplots(figsize=(10, 4.6))
im = ax.imshow(M.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=60)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"%{M.iloc[i, j]:.0f}", ha="center", va="center", fontsize=10, color="black" if M.iloc[i, j] < 40 else "white")
ax.set_xticks(range(len(yogunluk)), [f"{y:g}" for y in yogunluk]); ax.set_yticks(range(len(ana)), [f"{u}\n(birim değer {U.loc[u, 'birim_deger']:,.0f} $/t)".replace(",", ".") for u in ana], fontsize=9)
ax.set_xlabel("Gömülü emisyon yoğunluğu (ton CO₂ / ton ürün)")
ax.set_title(f"SKDM maliyeti, ihracat değerinin yüzde kaçı?\n(karbon fiyatı {fiyat_eur} €/t, tam uygulama)")
ax.grid(False)
kaydet(fig, "14_3_duyarlilik", "BM Comtrade · senaryo hesabı")
print(M.round(1))

# 5) Toplam maruziyet senaryosu (yalnızca ton bazlı ürünler)
for y_dusuk, y_yuksek in [(0.5, 2.0)]:
    ton = U.loc[ana, "ton"]
    dusuk, yuksek = (ton * y_dusuk * fiyat_eur * kur).sum(), (ton * y_yuksek * fiyat_eur * kur).sum()
    print(f"Toplam yıllık SKDM maliyeti (tam uygulama, {fiyat_eur}€/t): {dusuk / 1e9:.2f}–{yuksek / 1e9:.2f} mlr $; ürünlerin AB ihracatı {U.loc[ana, 'deger'].sum() / 1e9:.2f} mlr $")
