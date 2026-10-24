"""Makale 13: Firmaların krediye erişimi (SKA 9.3.2, 8.3) — Dünya Bankası İşletme Anketleri (WDI üzerinden)."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası, Enterprise Surveys (WDI)"
ulk = wb_ulkeler(); gercek = set(ulk.ulke_kodu); grup = ulk.set_index("ulke_kodu").gelir; bolge = ulk.set_index("ulke_kodu").bolge
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
GOS = {"IC.FRM.BNKL.ZS": "Banka kredisi / kredi limiti olan firmalar", "IC.FRM.BNKS.ZS": "Yatırımını bankayla finanse eden firmalar",
       "IC.FRM.BKWC.ZS": "İşletme sermayesini bankayla finanse eden firmalar", "IC.FRM.CRDC.FL.ZS": "Krediye erişimi tamamen kısıtlı firmalar",
       "IC.FRM.CRDC.PT.ZS": "Krediye erişimi kısmen kısıtlı firmalar", "IC.FRM.FEMM.ZS": "Üst yöneticisi kadın olan firmalar",
       "IC.FRM.FEMO.ZS": "Ortaklığında kadın bulunan firmalar", "IC.FRM.EXS.ZS": "Doğrudan ihracat yapan firmalar"}


def tablo(kod):
    d = wb(kod, donem="2006:2025")
    return d[d.ulke_kodu.isin(gercek)].pivot_table(index="yil", columns="ulke_kodu", values="deger")


T = {k: tablo(k) for k in GOS}
for k, ad in GOS.items():
    s = T[k]["TUR"].dropna() if "TUR" in T[k] else pd.Series(dtype=float)
    print(f"{ad}: {s.round(1).to_dict()}")
son = {k: T[k].loc[2014:].ffill().iloc[-1] for k in GOS}
yil = {k: T[k].loc[2014:].apply(lambda c: c.last_valid_index()) for k in GOS}
print("Kapsanan ülke (2014+):", {k: int(son[k].notna().sum()) for k in GOS})

# 1) Türkiye: anket turları
tr_yillar = sorted(set().union(*[set(T[k]["TUR"].dropna().index) for k in GOS if "TUR" in T[k]]))
sec = ["IC.FRM.BNKL.ZS", "IC.FRM.BNKS.ZS", "IC.FRM.BKWC.ZS", "IC.FRM.CRDC.FL.ZS"]
fig, ax = plt.subplots(figsize=(10.5, 4.8))
x = np.arange(len(sec)); w = 0.8 / len(tr_yillar)
for i, y in enumerate(tr_yillar):
    v = [T[k]["TUR"].get(y, np.nan) for k in sec]
    c = ax.bar(x + (i - (len(tr_yillar) - 1) / 2) * w, v, w, label=str(y), color=[RENK["gri"], RENK["sari"], RENK["mavi"], RENK["kirmizi"]][i % 4])
    ax.bar_label(c, labels=["" if np.isnan(a) else f"%{a:.0f}" for a in v], padding=2, fontsize=8.5)
KISA = {"IC.FRM.BNKL.ZS": "Banka kredisi /\nkredi limiti var", "IC.FRM.BNKS.ZS": "Yatırımı\nbankayla finanse",
        "IC.FRM.BKWC.ZS": "İşletme sermayesi\nbankayla finanse", "IC.FRM.CRDC.FL.ZS": "Krediye erişimi\ntamamen kısıtlı"}
ax.set_xticks(x, [KISA[k] for k in sec], fontsize=9.5)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0)); ax.legend(frameon=False, title="Anket yılı")
ax.set_title("Türkiye'de firmaların banka finansmanına erişimi"); ax.grid(axis="x", visible=False)
kaydet(fig, "13_1_turkiye", KAYNAK)

# 2) Ülkeler arası: banka kredisi olan firmalar ve gelir
gelir = wb("NY.GDP.PCAP.PP.KD", donem="2015:2024")
gelir = gelir[gelir.ulke_kodu.isin(gercek)].dropna().sort_values("yil").groupby("ulke_kodu").last().deger
K = pd.DataFrame({"kredi": son["IC.FRM.BNKL.ZS"], "kisit": son["IC.FRM.CRDC.FL.ZS"] + son["IC.FRM.CRDC.PT.ZS"], "gelir": gelir}).dropna(subset=["kredi", "gelir"])
fig, ax = plt.subplots(figsize=(10.5, 6))
ax.scatter(K.gelir, K.kredi, s=26, alpha=0.5, color=RENK["mavi"], lw=0)
AD = {"DEU": "Almanya", "ITA": "İtalya", "ESP": "İspanya", "POL": "Polonya", "GRC": "Yunanistan", "ROU": "Romanya", "BGR": "Bulgaristan",
      "CHN": "Çin", "IND": "Hindistan", "BRA": "Brezilya", "MEX": "Meksika", "EGY": "Mısır", "RUS": "Rusya", "KAZ": "Kazakistan",
      "UKR": "Ukrayna", "HUN": "Macaristan", "CZE": "Çekya", "PRT": "Portekiz", "SRB": "Sırbistan", "GEO": "Gürcistan", "MAR": "Fas",
      "JOR": "Ürdün", "IDN": "Endonezya", "VNM": "Vietnam", "CHL": "Şili", "COL": "Kolombiya", "AZE": "Azerbaycan", "UZB": "Özbekistan"}
EK_AD = {"LTU": "Litvanya", "ARM": "Ermenistan", "KGZ": "Kırgızistan", "BLR": "Belarus", "TKM": "Türkmenistan", "MDA": "Moldova",
         "LVA": "Letonya", "TJK": "Tacikistan", "MNE": "Karadağ", "AUT": "Avusturya", "HRV": "Hırvatistan", "SVK": "Slovakya",
         "GBR": "İngiltere", "EST": "Estonya", "MKD": "K. Makedonya", "ALB": "Arnavutluk", "NLD": "Hollanda", "CYP": "Kıbrıs",
         "LUX": "Lüksemburg", "BEL": "Belçika", "FIN": "Finlandiya", "BIH": "Bosna-Hersek", "FRA": "Fransa", "ISL": "İzlanda",
         "NOR": "Norveç", "CHE": "İsviçre", "SVN": "Slovenya", "DNK": "Danimarka", "IRL": "İrlanda", "XKX": "Kosova", "SWE": "İsveç"}
for k, v in AD.items():
    if k in K.index:
        ax.annotate(v, (K.gelir[k], K.kredi[k]), xytext=(4, 3), textcoords="offset points", fontsize=8.5)
if "TUR" in K.index:
    ax.scatter([K.gelir["TUR"]], [K.kredi["TUR"]], s=170, marker="*", color=RENK["kirmizi"], edgecolor="black", zorder=5)
    ax.annotate(f"Türkiye ({int(yil['IC.FRM.BNKL.ZS']['TUR'])})", (K.gelir["TUR"], K.kredi["TUR"]), xytext=(6, -14), textcoords="offset points",
                fontsize=10.5, fontweight="bold", color=RENK["kirmizi"])
ax.set_xscale("log"); ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v / 1000:g} bin $"))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_xlabel("Kişi başı gelir (satın alma gücü paritesi, log ölçek)"); ax.set_ylabel("Banka kredisi / kredi limiti olan firmalar")
ax.set_title("Firmaların banka kredisine erişimi (son anket, 2014 ve sonrası)")
kaydet(fig, "13_2_ulkeler", KAYNAK)
r = K.kredi.rank(ascending=False)
print("Banka kredisi TR:", K.kredi.get("TUR"), "sıra", int(r["TUR"]) if "TUR" in r else None, "/", len(K), "medyan", round(K.kredi.median(), 1))
avr = [c for c in K.index if bolge.get(c) == "Europe & Central Asia"]
print("Avrupa ve Orta Asya medyanı:", round(K.kredi[avr].median(), 1), "n", len(avr))

# 3) Kredi kısıtı: tamamen + kısmen kısıtlı firmalar
Kk = K.dropna(subset=["kisit"])
ust = Kk.reindex([c for c in avr if c in Kk.index]).sort_values("kisit")
fig, ax = plt.subplots(figsize=(10, 8))
adlar = [{**AD, **EK_AD}.get(c, ulk.set_index("ulke_kodu").ulke.get(c, c)) if c != "TUR" else "Türkiye" for c in ust.index]
ax.barh(adlar, ust.kisit, color=[RENK["kirmizi"] if c == "TUR" else RENK["gri"] for c in ust.index])
ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Krediye erişimi kısıtlı firmalar (tamamen + kısmen), Avrupa ve Orta Asya")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=8.5)
kaydet(fig, "13_3_kisit", KAYNAK)
if "TUR" in Kk.index:
    print("Kısıt TR:", round(Kk.kisit["TUR"], 1), "Avrupa-OrtaAsya medyanı:", round(ust.kisit.median(), 1), "sıra (yüksekten):", int(ust.kisit.rank(ascending=False)["TUR"]), "/", len(ust))

# 4) Kadın yönetici / ortak ve kredi
for k in ["IC.FRM.FEMM.ZS", "IC.FRM.FEMO.ZS", "IC.FRM.EXS.ZS"]:
    s = son[k].dropna()
    if "TUR" in s:
        print(GOS[k], "TR:", round(s["TUR"], 1), "dünya medyanı:", round(s.median(), 1), "Avr-OA medyanı:", round(s.reindex(avr).median(), 1))
