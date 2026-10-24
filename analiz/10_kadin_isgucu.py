"""Makale 10: Kadınların işgücüne katılımı (SKA 5.5, 8.5, 8.6) — Dünya Bankası / ILO modellenmiş tahminler."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası WDI (ILO modellenmiş tahminleri)"
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
ulk = wb_ulkeler(); gercek = set(ulk.ulke_kodu); gelir_grubu = ulk.set_index("ulke_kodu").gelir


def tablo(kod, donem="1990:2025"):
    d = wb(kod, donem=donem)
    return d[d.ulke_kodu.isin(gercek)].pivot_table(index="yil", columns="ulke_kodu", values="deger")


son = lambda t: t.ffill().iloc[-1]
kad, erk = tablo("SL.TLF.CACT.FE.ZS"), tablo("SL.TLF.CACT.MA.ZS")
oecd_med = lambda t: t[[c for c in OECD if c in t.columns]].median(axis=1)

# 1) Türkiye'de katılım, 1990–2025
fig, ax = plt.subplots(figsize=(10.5, 4.8))
ax.plot(erk.index, erk["TUR"], color=RENK["mavi"], lw=2.4, label="Türkiye, erkek")
ax.plot(kad.index, kad["TUR"], color=RENK["kirmizi"], lw=2.8, label="Türkiye, kadın")
ax.plot(kad.index, oecd_med(kad), color="black", lw=1.8, ls="--", label="OECD medyanı, kadın")
ax.fill_between(kad.index, kad["TUR"], oecd_med(kad), color=RENK["kirmizi"], alpha=0.08)
ax.set_ylim(0, 90); ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("İşgücüne katılım oranı: Türkiye'de kadınlar 35 yılda yerinde saydı")
ax.legend(frameon=False, loc="lower right")
kaydet(fig, "10_1_egilim", KAYNAK)
print("TR kadın:", kad["TUR"].loc[[1990, 2000, 2004, 2010, 2015, 2020, 2025]].round(1).to_dict())
print("TR erkek:", erk["TUR"].loc[[1990, 2025]].round(1).to_dict(), "OECD kadın medyan:", oecd_med(kad).loc[[1990, 2025]].round(1).to_dict())

# 2) Ülkeler arası: kadın katılımı ve gelir
gelir = son(tablo("NY.GDP.PCAP.PP.KD", "2018:2025"))
K = pd.DataFrame({"kad": son(kad), "gelir": gelir}).dropna()
sira = K.kad.rank(ascending=False)
fig, ax = plt.subplots(figsize=(10.5, 6))
ax.scatter(K.gelir, K.kad, s=26, alpha=0.5, color=RENK["mor"], lw=0)
ad = {"DEU": "Almanya", "USA": "ABD", "CHN": "Çin", "IND": "Hindistan", "BRA": "Brezilya", "MEX": "Meksika", "EGY": "Mısır",
      "IRN": "İran", "SAU": "S. Arabistan", "POL": "Polonya", "GRC": "Yunanistan", "ITA": "İtalya", "KOR": "G. Kore",
      "JPN": "Japonya", "SWE": "İsveç", "RUS": "Rusya", "PAK": "Pakistan", "JOR": "Ürdün", "MAR": "Fas", "IDN": "Endonezya",
      "VNM": "Vietnam", "ROU": "Romanya", "AZE": "Azerbaycan", "KAZ": "Kazakistan", "CHL": "Şili", "IRQ": "Irak", "DZA": "Cezayir"}
for k, v in ad.items():
    if k in K.index:
        ax.annotate(v, (K.gelir[k], K.kad[k]), xytext=(4, 3), textcoords="offset points", fontsize=8.5)
ax.scatter([K.gelir["TUR"]], [K.kad["TUR"]], s=170, marker="*", color=RENK["kirmizi"], edgecolor="black", zorder=5)
ax.annotate("Türkiye", (K.gelir["TUR"], K.kad["TUR"]), xytext=(6, -14), textcoords="offset points", fontsize=10.5, fontweight="bold", color=RENK["kirmizi"])
ax.set_xscale("log"); ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v / 1000:g} bin $"))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_xlabel("Kişi başı gelir (satın alma gücü paritesi, log ölçek)"); ax.set_ylabel("Kadınların işgücüne katılım oranı")
ax.set_title(f"Türkiye kadın işgücüne katılımında {len(K)} ülke içinde {int(sira['TUR'])}. sırada")
kaydet(fig, "10_2_ulkeler", KAYNAK)
benzer = K[(K.gelir > K.gelir["TUR"] * 0.67) & (K.gelir < K.gelir["TUR"] * 1.5)]
print(f"Sıra {int(sira['TUR'])}/{len(K)}; benzer gelirli {len(benzer)} ülkede medyan %{benzer.kad.median():.1f}, TR'den düşük: {list(benzer[benzer.kad < K.kad['TUR']].index)}")

# 3) Eğitime göre katılım
egitim = {"Temel eğitim": "BASC", "Orta eğitim": "INTM", "Yükseköğretim": "ADVN"}
E = pd.DataFrame({ad_: {"Türkiye, kadın": son(tablo(f"SL.TLF.{k}.FE.ZS", "2015:2025"))["TUR"],
                        "OECD medyanı, kadın": son(tablo(f"SL.TLF.{k}.FE.ZS", "2015:2025")).reindex(OECD).median(),
                        "Türkiye, erkek": son(tablo(f"SL.TLF.{k}.MA.ZS", "2015:2025"))["TUR"]} for ad_, k in egitim.items()}).T
fig, ax = plt.subplots(figsize=(10, 4.8))
x = np.arange(len(E))
for i, (sut, renk) in enumerate(zip(E.columns, [RENK["kirmizi"], "black", RENK["mavi"]])):
    c = ax.bar(x + (i - 1) * 0.27, E[sut], 0.27, color=renk, label=sut, alpha=0.9 if sut != "OECD medyanı, kadın" else 0.55)
    ax.bar_label(c, labels=[f"%{v:.0f}" for v in E[sut]], padding=2, fontsize=9)
ax.set_xticks(x, E.index); ax.set_ylim(0, 100); ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("Eğitim düzeyine göre işgücüne katılım: Yükseköğretim farkı kapatıyor")
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="x", visible=False)
kaydet(fig, "10_3_egitim", KAYNAK)
print(E.round(1))

# 4) Cinsiyet farkları panosu
gosterge = [("SL.TLF.CACT.FE.ZS", "Kadınların işgücüne katılımı (%)", "8.5"),
            ("SL.EMP.SMGT.FE.ZS", "Üst ve orta düzey yöneticilerde kadın payı (%)", "5.5.2"),
            ("SG.GEN.PARL.ZS", "Mecliste kadın milletvekili payı (%)", "5.5.1"),
            ("SL.UEM.NEET.FE.ZS", "Ne eğitimde ne istihdamda genç kadınlar (%)", "8.6.1"),
            ("SL.UEM.TOTL.FE.ZS", "Kadın işsizlik oranı (%)", "8.5.2")]
P = pd.DataFrame([{"ad": a, "kod": r, "TR": son(tablo(k, "2015:2025"))["TUR"], "OECD": son(tablo(k, "2015:2025")).reindex(OECD).median()}
                  for k, a, r in gosterge])
fig, ax = plt.subplots(figsize=(10.5, 4.6))
y = np.arange(len(P))[::-1]
ax.barh(y + 0.18, P.TR, 0.36, color=RENK["kirmizi"], label="Türkiye")
ax.barh(y - 0.18, P.OECD, 0.36, color=RENK["gri"], label="OECD medyanı")
for yy, (_, r) in zip(y, P.iterrows()):
    ax.text(r.TR + 0.8, yy + 0.18, f"%{r.TR:.1f}".replace(".", ","), va="center", fontsize=9)
    ax.text(r.OECD + 0.8, yy - 0.18, f"%{r.OECD:.1f}".replace(".", ","), va="center", fontsize=9, color="#555")
ax.set_yticks(y, [f"{r.ad}  [SKA {r.kod}]" for _, r in P.iterrows()], fontsize=9.5)
ax.set_xlim(0, P[["TR", "OECD"]].max().max() * 1.15)
ax.set_title("Toplumsal cinsiyet eşitliği göstergeleri: Türkiye ve OECD")
ax.legend(frameon=False, loc="lower right"); ax.grid(axis="y", visible=False)
kaydet(fig, "10_4_pano", KAYNAK + " · IPU")
print(P.round(1))

# 5) Senaryo: Türkiye OECD medyanına ulaşsaydı
nufus_k = son(tablo("SP.POP.TOTL.FE.IN", "2020:2025"))["TUR"] - son(tablo("SP.POP.0014.FE.IN", "2020:2025"))["TUR"]
hedef = oecd_med(kad).iloc[-1]
ek = nufus_k * (hedef - kad["TUR"].iloc[-1]) / 100
print(f"15+ kadın nüfus {nufus_k / 1e6:.1f} milyon; OECD medyanı %{hedef:.1f}; ek kadın işgücü ≈ {ek / 1e6:.1f} milyon")
isgucu = (nufus_k * kad["TUR"].iloc[-1] / 100)
print(f"Bugünkü kadın işgücü ≈ {isgucu / 1e6:.1f} milyon; artış %{100 * ek / isgucu:.0f}")
