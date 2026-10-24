"""Makale 3: Finansal kapsayıcılık (SKA 8.10.2) — Global Findex verisiyle."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası, Global Findex ve WDI"
ulkeler = wb_ulkeler()
gercek = set(ulkeler.ulke_kodu)


def tablo(kod, donem="2011:2025"):
    d = wb(kod, donem=donem)
    return d[d.ulke_kodu.isin(gercek)].pivot_table(index="ulke_kodu", columns="yil", values="deger")


hesap = tablo("FX.OWN.TOTL.ZS")
kadin, erkek = tablo("FX.OWN.TOTL.FE.ZS"), tablo("FX.OWN.TOTL.MA.ZS")
alt40, ust60 = tablo("FX.OWN.TOTL.40.ZS"), tablo("FX.OWN.TOTL.60.ZS")
genc, yasli = tablo("FX.OWN.TOTL.YG.ZS"), tablo("FX.OWN.TOTL.OL.ZS")
sube, atm = tablo("FB.CBK.BRCH.P5"), tablo("FB.ATM.TOTL.P5")
gelir = tablo("NY.GDP.PCAP.PP.KD", "2020:2024")
kadin_isgucu = tablo("SL.TLF.CACT.FE.ZS", "2020:2024")
ad = ulkeler.set_index("ulke_kodu").ulke
TR_AD = {"TUR": "Türkiye", "DEU": "Almanya", "USA": "ABD", "CHN": "Çin", "IND": "Hindistan", "BRA": "Brezilya",
         "MEX": "Meksika", "EGY": "Mısır", "IRN": "İran", "PAK": "Pakistan", "POL": "Polonya", "GRC": "Yunanistan",
         "ROU": "Romanya", "BGR": "Bulgaristan", "RUS": "Rusya", "SAU": "S. Arabistan", "IDN": "Endonezya",
         "KEN": "Kenya", "MAR": "Fas", "ZAF": "G. Afrika", "ARG": "Arjantin", "KAZ": "Kazakistan", "UKR": "Ukrayna",
         "MYS": "Malezya", "THA": "Tayland", "COL": "Kolombiya", "JOR": "Ürdün", "ITA": "İtalya", "ESP": "İspanya",
         "FRA": "Fransa", "GBR": "İngiltere", "JPN": "Japonya", "KOR": "G. Kore", "DZA": "Cezayir", "TUN": "Tunus",
         "IRQ": "Irak", "BGD": "Bangladeş", "NGA": "Nijerya", "VNM": "Vietnam", "PHL": "Filipinler", "AZE": "Azerbaycan",
         "GEO": "Gürcistan", "HUN": "Macaristan", "SRB": "Sırbistan", "CHL": "Şili", "PER": "Peru", "MNG": "Moğolistan",
         "LBN": "Lübnan", "AFG": "Afganistan", "ETH": "Etiyopya", "TZA": "Tanzanya", "UGA": "Uganda", "GHA": "Gana",
         "ISR": "İsrail", "ARE": "BAE", "KWT": "Kuveyt", "BHR": "Bahreyn", "QAT": "Katar", "OMN": "Umman",
         "ALB": "Arnavutluk", "MKD": "K. Makedonya", "BIH": "Bosna-Hersek", "ARM": "Ermenistan", "UZB": "Özbekistan",
         "KGZ": "Kırgızistan", "TJK": "Tacikistan", "SEN": "Senegal", "CIV": "Fildişi Sahili", "CMR": "Kamerun",
         "MLI": "Mali", "BFA": "Burkina Faso", "NER": "Nijer", "TCD": "Çad", "GIN": "Gine", "BEN": "Benin",
         "TGO": "Togo", "SLE": "Sierra Leone", "LBR": "Liberya", "MOZ": "Mozambik", "ZMB": "Zambiya", "MWI": "Malavi",
         "ZWE": "Zimbabve", "NPL": "Nepal", "LKA": "Sri Lanka", "KHM": "Kamboçya", "LAO": "Laos", "MMR": "Myanmar",
         "YEM": "Yemen", "SYR": "Suriye", "SDN": "Sudan", "SSD": "G. Sudan", "PSE": "Filistin", "WBG": "Filistin"}
isim = lambda k: TR_AD.get(k, ad.get(k, k))
son = lambda t: t.apply(lambda r: r.dropna().iloc[-1] if r.notna().any() else np.nan, axis=1)

# 1) Türkiye'de 2011–2024 eğilimi
fig, ax = plt.subplots(figsize=(10, 5))
for seri, etiket, renk, stil in [(hesap, "Tüm yetişkinler", "black", "-"), (erkek, "Erkek", RENK["mavi"], "-"),
                                 (kadin, "Kadın", RENK["kirmizi"], "-"), (ust60, "En zengin %60", RENK["yesil"], "--"),
                                 (alt40, "En yoksul %40", RENK["sari"], "--")]:
    s = seri.loc["TUR"].dropna()
    ax.plot(s.index, s.values, marker="o", lw=2.6 if renk == "black" else 2, ls=stil, color=renk, label=etiket)
    ax.annotate(f"%{s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(6, -3), textcoords="offset points",
                color=renk, fontsize=10, fontweight="bold")
ax.set_xticks([2011, 2014, 2017, 2021, 2024]); ax.set_xlim(2010.5, 2025.3); ax.set_ylim(25, 100)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_title("Türkiye: Banka ya da mobil para hesabı olan yetişkinler (SKA 8.10.2)")
ax.legend(frameon=False, ncol=3, loc="lower right")
kaydet(fig, "03_1_turkiye_egilim", KAYNAK)

# 2) Cinsiyet farkı: dünya sıralaması (son veri)
fark = (son(erkek) - son(kadin)).dropna()
fark = fark[son(hesap).reindex(fark.index).notna()]
sira = fark.sort_values(ascending=False)
tr_sira = list(sira.index).index("TUR") + 1
ust = sira.head(25)
fig, ax = plt.subplots(figsize=(10, 7))
renkler = [RENK["kirmizi"] if k == "TUR" else RENK["gri"] for k in ust.index]
ax.barh([isim(k) for k in ust.index][::-1], ust.values[::-1], color=renkler[::-1])
for i, v in enumerate(ust.values[::-1]):
    ax.text(v + 0.3, i, f"{v:.0f}", va="center", fontsize=9)
ax.set_title(f"Hesap sahipliğinde erkek–kadın farkı en yüksek 25 ülke (puan)\nTürkiye {len(sira)} ülke içinde {tr_sira}. sırada")
ax.grid(axis="y", visible=False)
kaydet(fig, "03_2_cinsiyet_farki", KAYNAK)

# 3) Gelir ve hesap sahipliği: Türkiye beklenenin neresinde?
g = pd.DataFrame({"hesap": son(hesap), "gelir": son(gelir)}).dropna()
g["lg"] = np.log10(g.gelir)
b, a = np.polyfit(g.lg, g.hesap.clip(upper=100), 1)
g["beklenen"] = a + b * g.lg
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(g.gelir, g.hesap, s=26, alpha=0.5, color=RENK["mavi"], lw=0)
xs = np.linspace(g.lg.min(), g.lg.max(), 50)
ax.plot(10 ** xs, np.clip(a + b * xs, 0, 100), color="black", lw=1.2, ls="--", label="Gelire göre beklenen")
for k in ["DEU", "CHN", "IND", "BRA", "EGY", "POL", "SAU", "KEN", "MAR", "USA", "GRC", "ROU", "KAZ", "PAK"]:
    if k in g.index:
        ax.annotate(isim(k), (g.gelir[k], g.hesap[k]), xytext=(4, 3), textcoords="offset points", fontsize=8.5)
ax.annotate("Türkiye", (g.gelir["TUR"], g.hesap["TUR"]), xytext=(-60, 6), textcoords="offset points", fontsize=10, fontweight="bold", color=RENK["kirmizi"])
ax.scatter([g.gelir["TUR"]], [g.hesap["TUR"]], s=160, marker="*", color=RENK["kirmizi"], zorder=5, edgecolor="black")
ax.set_xscale("log"); ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v / 1000:g} bin $"))
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_xlabel("Kişi başı gelir (satın alma gücü paritesi, log ölçek)"); ax.set_ylabel("Hesabı olan yetişkinler")
ax.set_title("Gelir arttıkça hesap sahipliği artıyor; Türkiye tam beklenen yerde")
ax.legend(frameon=False, loc="lower right")
kaydet(fig, "03_3_gelir_hesap", KAYNAK)

# 4) Şube ve ATM azalırken hesap sahipliği artıyor
fig, ax = plt.subplots(figsize=(10, 4.6))
s1, s2 = sube.loc["TUR"].dropna(), atm.loc["TUR"].dropna()
ax.plot(s1.index, s1 / s1.iloc[0] * 100, lw=2.4, color=RENK["mavi"], label=f"Banka şubesi / 100 bin yetişkin ({s1.iloc[0]:.1f} → {s1.iloc[-1]:.1f})")
ax.plot(s2.index, s2 / s2.iloc[0] * 100, lw=2.4, color=RENK["sari"], label=f"ATM / 100 bin yetişkin ({s2.iloc[0]:.0f} → {s2.iloc[-1]:.0f})")
h = hesap.loc["TUR"].dropna()
ax.plot(h.index, h / h.iloc[0] * 100, lw=2.4, color="black", marker="o", label=f"Hesabı olan yetişkin oranı (%{h.iloc[0]:.0f} → %{h.iloc[-1]:.0f})")
ax.axhline(100, color=RENK["gri"], lw=0.8)
ax.set_title("Türkiye: Fiziksel şube azalırken finansal erişim arttı (2011 = 100)")
ax.legend(frameon=False, fontsize=9.5)
kaydet(fig, "03_4_sube_atm", KAYNAK)

# 5) Cinsiyet farkı ile kadın işgücüne katılımı
k = pd.DataFrame({"fark": fark, "isgucu": son(kadin_isgucu), "lg": np.log10(son(gelir))}).dropna()
r = k.fark.corr(k.isgucu)
X = np.column_stack([np.ones(len(k)), k.isgucu, k.lg])
beta = np.linalg.lstsq(X, k.fark, rcond=None)[0]
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.scatter(k.isgucu, k.fark, s=26, alpha=0.5, color=RENK["mor"], lw=0)
xs = np.linspace(k.isgucu.min(), k.isgucu.max(), 50)
b2, a2 = np.polyfit(k.isgucu, k.fark, 1)
ax.plot(xs, a2 + b2 * xs, color="black", ls="--", lw=1.2)
for kk in ["EGY", "IRN", "PAK", "IND", "SAU", "DEU", "CHN", "MAR", "JOR", "KEN", "BRA", "IRQ", "DZA", "BGD"]:
    if kk in k.index:
        ax.annotate(isim(kk), (k.isgucu[kk], k.fark[kk]), xytext=(4, 3), textcoords="offset points", fontsize=8.5)
ax.annotate("Türkiye", (k.isgucu["TUR"], k.fark["TUR"]), xytext=(-58, 6), textcoords="offset points", fontsize=10, fontweight="bold", color=RENK["kirmizi"])
ax.scatter([k.isgucu["TUR"]], [k.fark["TUR"]], s=160, marker="*", color=RENK["kirmizi"], zorder=5, edgecolor="black")
ax.axhline(0, color=RENK["gri"], lw=0.8)
ax.set_xlabel("Kadınların işgücüne katılım oranı (%)"); ax.set_ylabel("Hesap sahipliğinde erkek–kadın farkı (puan)")
ax.set_title(f"Kadın işgücüne katılımı yüksek ülkelerde hesap farkı daha küçük (r = {r:.2f})".replace(".", ","))
kaydet(fig, "03_5_isgucu_fark", KAYNAK)

# Rapor
tr = lambda t: t.loc["TUR"].dropna()
print("Türkiye hesap:", tr(hesap).round(1).to_dict())
print("Kadın:", tr(kadin).round(1).to_dict(), "Erkek:", tr(erkek).round(1).to_dict())
print("Alt40:", tr(alt40).round(1).to_dict(), "Üst60:", tr(ust60).round(1).to_dict())
print("Genç:", tr(genc).round(1).to_dict(), "Yaşlı:", tr(yasli).round(1).to_dict())
print(f"Cinsiyet farkı TR {fark['TUR']:.1f} puan; sıra {tr_sira}/{len(sira)}; dünya medyanı {fark.median():.1f}")
yuksek = ulkeler.set_index("ulke_kodu").gelir
for grup in ["Upper middle income", "High income"]:
    kods = [c for c in fark.index if yuksek.get(c) == grup]
    print(f"  {grup}: medyan fark {fark[kods].median():.1f}, TR'den yüksek fark: {[isim(c) for c in kods if fark[c] > fark['TUR']]}")
print(f"Gelir-hesap: TR gerçek {g.hesap['TUR']:.1f}, beklenen {g.beklenen['TUR']:.1f}, fark {g.hesap['TUR'] - g.beklenen['TUR']:.1f}")
print(f"Kadın işgücü TR {k.isgucu['TUR']:.1f}; r={r:.2f}; regresyon (fark ~ işgücü + log gelir): işgücü katsayısı {beta[1]:.2f}, log gelir {beta[2]:.2f}, n={len(k)}")
print("Hesabı olmayan yetişkin oranı TR 2024:", round(100 - tr(hesap).iloc[-1], 1))
print("Türkiye gelir grubu:", yuksek.get("TUR"))
