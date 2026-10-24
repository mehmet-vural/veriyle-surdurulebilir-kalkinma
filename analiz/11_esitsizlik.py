"""Makale 11: Gelir eşitsizliği ve en alt %40 (SKA 10.1.1, 10.2.1) — Dünya Bankası Yoksulluk ve Eşitsizlik Platformu."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası, Poverty and Inequality Platform (WDI)"
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
AD = {"AUS": "Avustralya", "AUT": "Avusturya", "BEL": "Belçika", "CAN": "Kanada", "CHL": "Şili", "COL": "Kolombiya", "CRI": "Kosta Rika",
      "CZE": "Çekya", "DNK": "Danimarka", "EST": "Estonya", "FIN": "Finlandiya", "FRA": "Fransa", "DEU": "Almanya", "GRC": "Yunanistan",
      "HUN": "Macaristan", "ISL": "İzlanda", "IRL": "İrlanda", "ISR": "İsrail", "ITA": "İtalya", "JPN": "Japonya", "KOR": "G. Kore",
      "LVA": "Letonya", "LTU": "Litvanya", "LUX": "Lüksemburg", "MEX": "Meksika", "NLD": "Hollanda", "NZL": "Yeni Zelanda", "NOR": "Norveç",
      "POL": "Polonya", "PRT": "Portekiz", "SVK": "Slovakya", "SVN": "Slovenya", "ESP": "İspanya", "SWE": "İsveç", "CHE": "İsviçre",
      "TUR": "Türkiye", "GBR": "İngiltere", "USA": "ABD"}
ulk = wb_ulkeler(); gercek = set(ulk.ulke_kodu); grup = ulk.set_index("ulke_kodu").gelir


def tablo(kod, donem="2000:2025"):
    d = wb(kod, donem=donem)
    return d[d.ulke_kodu.isin(gercek)].pivot_table(index="yil", columns="ulke_kodu", values="deger")


def son(t, bas=2015):
    return t.loc[bas:].ffill().iloc[-1]


gini = tablo("SI.POV.GINI")
umi = [c for c in gini.columns if grup.get(c) == "Upper middle income"]

# 1) Gini eğilimi
fig, ax = plt.subplots(figsize=(10, 4.6))
tr = gini["TUR"].dropna()
ax.plot(tr.index, tr, color=RENK["kirmizi"], lw=2.8, marker="o", ms=4, label="Türkiye")
def medyan(t, asgari):
    t = t.interpolate(limit_area="inside")
    return t.median(axis=1).where(t.notna().sum(axis=1) >= asgari).loc[2003:].dropna()
o = medyan(gini[[c for c in OECD if c in gini]], 20)
u = medyan(gini[umi], 15)
ax.plot(o.index, o, color="black", lw=2, label="OECD medyanı")
ax.plot(u.index, u, color=RENK["gri"], lw=2, ls="--", label="Üst-orta gelirli ülkeler medyanı")
ax.set_title("Gini katsayısı: Türkiye'de eşitsizlik 2010'dan bu yana yeniden arttı")
ax.set_ylabel("Gini (0 = tam eşitlik, 100 = tam eşitsizlik)"); ax.legend(frameon=False)
kaydet(fig, "11_1_gini", KAYNAK)
print("TR Gini:", tr.round(1).to_dict())
print("OECD medyanı son:", o.index[-1], round(o.iloc[-1], 1), "UMI medyanı son:", u.index[-1], round(u.iloc[-1], 1))

# 2) Gelir dilimleri
dilim = {"En yoksul %20": "SI.DST.FRST.20", "2. %20": "SI.DST.02ND.20", "3. %20": "SI.DST.03RD.20",
         "4. %20": "SI.DST.04TH.20", "En zengin %20": "SI.DST.05TH.20"}
D = pd.DataFrame({k: {"Türkiye": son(tablo(v))["TUR"], "OECD medyanı": son(tablo(v)).reindex(OECD).median()} for k, v in dilim.items()}).T
fig, ax = plt.subplots(figsize=(10, 4.6))
x = np.arange(len(D))
for i, (s, r) in enumerate(zip(D.columns, [RENK["kirmizi"], RENK["gri"]])):
    c = ax.bar(x + (i - 0.5) * 0.38, D[s], 0.38, color=r, label=s)
    ax.bar_label(c, labels=[f"%{v:.1f}".replace(".", ",") for v in D[s]], padding=2, fontsize=9)
ax.axhline(20, color="black", ls=":", lw=1); ax.text(4.55, 20.6, "tam eşitlikte\nher dilim %20", fontsize=8.5, ha="right")
ax.set_xticks(x, D.index); ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Toplam gelirden kim ne kadar pay alıyor?")
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="x", visible=False)
kaydet(fig, "11_2_dilimler", KAYNAK)
print(D.round(1))

# 3) Palma oranı: en zengin %10 / en yoksul %40 — OECD ülkeleri
ust10 = son(tablo("SI.DST.10TH.10"))
alt40 = son(tablo("SI.DST.FRST.20")) + son(tablo("SI.DST.02ND.20"))
palma = (ust10 / alt40).reindex(OECD).dropna().sort_values()
fig, ax = plt.subplots(figsize=(10, 8))
ax.barh([AD[k] for k in palma.index], palma.values, color=[RENK["kirmizi"] if k == "TUR" else RENK["gri"] for k in palma.index])
for i, v in enumerate(palma.values):
    ax.text(v + 0.02, i, f"{v:.2f}".replace(".", ","), va="center", fontsize=8.5)
ax.axvline(1, color="black", ls=":", lw=1)
ax.set_title("Palma oranı: En zengin %10'un geliri, en yoksul %40'ın kaç katı? (OECD ülkeleri)")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "11_3_palma", KAYNAK)
print("Palma TR:", round(palma["TUR"], 2), "sıra (yüksekten):", int(palma.rank(ascending=False)["TUR"]), "/", len(palma))

# 4) Paylaşılan refah (10.1.1): alt %40'ın gelir büyümesi - ortalama büyüme
b40, bort = tablo("SI.SPR.PC40.ZG", "2015:2025"), tablo("SI.SPR.PCAP.ZG", "2015:2025")
prim = (son(b40) - son(bort)).dropna()
prim_oecd = prim.reindex(OECD).dropna().sort_values()
fig, ax = plt.subplots(figsize=(10, 7.6))
ax.barh([AD[k] for k in prim_oecd.index], prim_oecd.values,
        color=[RENK["kirmizi"] if k == "TUR" else (RENK["yesil"] if v > 0 else RENK["sari"]) for k, v in prim_oecd.items()])
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("En alt %40'ın yıllık gelir büyümesi − ortalama büyüme (puan)")
ax.set_title("Paylaşılan refah primi (SKA 10.1.1): Yoksullar ortalamadan hızlı mı büyüdü?")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "11_4_paylasilan_refah", KAYNAK)
print("Prim TR:", round(prim["TUR"], 2), "| OECD'de pozitif olan ülke oranı %", round(100 * (prim_oecd > 0).mean()),
      "| dünya medyanı", round(prim.median(), 2), "n", len(prim))

# 5) Göreli yoksulluk (10.2.1): medyan gelirin yarısının altında yaşayanlar
g50 = son(tablo("SI.DST.50MD"))
print("10.2.1 TR:", g50["TUR"], "OECD medyanı:", round(g50.reindex(OECD).median(), 1), "OECD sırası (yüksekten):",
      int(g50.reindex(OECD).dropna().rank(ascending=False)["TUR"]), "/", g50.reindex(OECD).notna().sum())
print("Gini OECD sırası:", int(son(gini).reindex(OECD).dropna().rank(ascending=False)["TUR"]), "/", son(gini).reindex(OECD).notna().sum(),
      "en yüksek 3:", son(gini).reindex(OECD).dropna().nlargest(3).round(1).to_dict())
