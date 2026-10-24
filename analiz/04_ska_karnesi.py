"""Makale 4: Türkiye'nin SKA karnesi — 17 amaç, Dünya Bankası göstergeleri, yüzdelik sıra yöntemi."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası WDI ve WGI"
# (SKA, gösterge kodu, Türkçe ad, yön: +1 yüksek iyi / -1 düşük iyi, resmî SKA göstergesi)
GOSTERGELER = [
    (1, "SI.POV.UMIC", "Günlük 8,30 $ altında yaşayanlar (%)", -1, "1.1.1"),
    (2, "SN.ITK.DEFC.ZS", "Yetersiz beslenme (%)", -1, "2.1.1"),
    (2, "SH.STA.STNT.ME.ZS", "5 yaş altı bodurluk (%)", -1, "2.2.1"),
    (3, "SH.DYN.MORT", "5 yaş altı ölüm (binde)", -1, "3.2.1"),
    (3, "SP.DYN.LE00.IN", "Doğumda beklenen yaşam süresi", +1, "—"),
    (3, "SH.STA.TRAF.P5", "Trafik kazası ölümü (100 binde)", -1, "3.6.1"),
    (4, "SE.SEC.CMPT.LO.ZS", "Ortaokul tamamlama (%)", +1, "4.1"),
    (4, "SE.TER.ENRR", "Yükseköğretime kayıt (%)", +1, "4.3"),
    (5, "SG.GEN.PARL.ZS", "Mecliste kadın oranı (%)", +1, "5.5.1"),
    (5, "SL.TLF.CACT.FM.ZS", "Kadın/erkek işgücüne katılım oranı", +1, "8.5"),
    (6, "SH.H2O.SMDW.ZS", "Güvenli içme suyu (%)", +1, "6.1.1"),
    (6, "ER.H2O.FWST.ZS", "Su stresi (%)", -1, "6.4.2"),
    (7, "EG.FEC.RNEW.ZS", "Yenilenebilir enerji payı (%)", +1, "7.2.1"),
    (7, "EG.EGY.PRIM.PP.KD", "Enerji yoğunluğu", -1, "7.3.1"),
    (8, "SL.UEM.TOTL.ZS", "İşsizlik (%)", -1, "8.5.2"),
    (8, "SL.UEM.NEET.ZS", "Ne eğitimde ne istihdamda gençler (%)", -1, "8.6.1"),
    (8, "FX.OWN.TOTL.ZS", "Hesabı olan yetişkinler (%)", +1, "8.10.2"),
    (9, "GB.XPD.RSDV.GD.ZS", "Ar-Ge harcaması (GSYH %)", +1, "9.5.1"),
    (9, "SP.POP.SCIE.RD.P6", "Araştırmacı (milyonda)", +1, "9.5.2"),
    (10, "SI.POV.GINI", "Gini katsayısı", -1, "10.1"),
    (10, "SI.DST.FRST.20", "En yoksul %20'nin gelir payı (%)", +1, "10.1"),
    (11, "EN.ATM.PM25.MC.M3", "PM2.5 hava kirliliği (µg/m³)", -1, "11.6.2"),
    (12, "NY.ADJ.DRES.GN.ZS", "Doğal kaynak tükenmesi (GSMG %)", -1, "12.2"),
    (13, "EN.GHG.CO2.PC.CE.AR5", "Kişi başı CO₂ (ton)", -1, "13.2"),
    (14, "ER.MRN.PTMR.ZS", "Deniz koruma alanları (%)", +1, "14.5.1"),
    (15, "ER.LND.PTLD.ZS", "Kara koruma alanları (%)", +1, "15.1.2"),
    (15, "AG.LND.FRST.ZS", "Orman alanı (%)", +1, "15.1.1"),
    (16, "VC.IHR.PSRC.P5", "Kasten öldürme (100 binde)", -1, "16.1.1"),
    (16, "GOV_WGI_CC.EST", "Yolsuzluğun kontrolü (WGI)", +1, "16.5"),
    (17, "GC.TAX.TOTL.GD.ZS", "Vergi geliri (GSYH %)", +1, "17.1.1"),
    (17, "IT.NET.USER.ZS", "İnternet kullanan bireyler (%)", +1, "17.8.1"),
]
SKA_AD = {1: "Yoksulluğa son", 2: "Açlığa son", 3: "Sağlık ve kaliteli yaşam", 4: "Nitelikli eğitim",
          5: "Toplumsal cinsiyet eşitliği", 6: "Temiz su ve sanitasyon", 7: "Erişilebilir ve temiz enerji",
          8: "İnsana yakışır iş ve büyüme", 9: "Sanayi, yenilikçilik ve altyapı", 10: "Eşitsizliklerin azaltılması",
          11: "Sürdürülebilir şehirler", 12: "Sorumlu üretim ve tüketim", 13: "İklim eylemi", 14: "Sudaki yaşam",
          15: "Karasal yaşam", 16: "Barış, adalet ve güçlü kurumlar", 17: "Amaçlar için ortaklıklar"}
SKA_RENK = {1: "#E5243B", 2: "#DDA63A", 3: "#4C9F38", 4: "#C5192D", 5: "#FF3A21", 6: "#26BDE2", 7: "#FCC30B",
            8: "#A21942", 9: "#FD6925", 10: "#DD1367", 11: "#FD9D24", 12: "#BF8B2E", 13: "#3F7E44", 14: "#0A97D9",
            15: "#56C02B", 16: "#00689D", 17: "#19486A"}
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()

ulkeler = wb_ulkeler()
gercek = set(ulkeler.ulke_kodu)
gelir_grubu = ulkeler.set_index("ulke_kodu").gelir


def son_deger(d, bas, bit):
    d = d[d.ulke_kodu.isin(gercek) & d.yil.between(bas, bit)].dropna(subset=["deger"])
    return d.sort_values("yil").groupby("ulke_kodu").last()


satirlar, eksik = [], []
for ska, kod, ad, yon, resmi in GOSTERGELER:
    try:
        d = wb(kod, donem="2010:2025", kaynak=None)
    except Exception as e:  # gösterge API'de yoksa
        eksik.append((kod, str(e)[:60])); continue
    simdi, once = son_deger(d, 2018, 2025), son_deger(d, 2012, 2016)
    if "TUR" not in simdi.index or len(simdi) < 60:
        eksik.append((kod, f"TUR yok ya da az ülke ({len(simdi)})")); continue
    yuzdelik = (simdi.deger * yon).rank(pct=True) * 100       # 100 = en iyi
    satir = {"ska": ska, "kod": kod, "ad": ad, "resmi": resmi, "yon": yon, "n": len(simdi),
             "tr_deger": simdi.deger["TUR"], "tr_yil": int(simdi.yil["TUR"]), "tr_yuzdelik": yuzdelik["TUR"],
             "oecd_medyan_yuzdelik": yuzdelik.reindex(OECD).median(),
             "oecd_medyan_deger": simdi.deger.reindex(OECD).median(),
             "umi_medyan_deger": simdi.deger[[k for k in simdi.index if gelir_grubu.get(k) == "Upper middle income"]].median()}
    if "TUR" in once.index:
        satir["tr_once"], satir["tr_once_yil"] = once.deger["TUR"], int(once.yil["TUR"])
        satir["iyilesme"] = (simdi.deger["TUR"] - once.deger["TUR"]) * yon
        ortak = once.index.intersection(simdi.index)
        satir["yuzdelik_once"] = ((once.deger[ortak] * yon).rank(pct=True) * 100)["TUR"]
        satir["yuzdelik_simdi_ortak"] = ((simdi.deger[ortak] * yon).rank(pct=True) * 100)["TUR"]
    satirlar.append(satir)
G = pd.DataFrame(satirlar)
G.to_csv("../veri/04_ska_karnesi_gostergeler.csv", index=False)
pd.set_option("display.width", 250)
print(G[["ska", "ad", "tr_deger", "tr_yil", "tr_yuzdelik", "oecd_medyan_deger", "umi_medyan_deger", "tr_once", "iyilesme"]].round(1).to_string())
print("EKSİK:", eksik)

skor = G.groupby("ska").agg(tr=("tr_yuzdelik", "mean"), oecd=("oecd_medyan_yuzdelik", "mean"), n=("kod", "size"))
skor = skor.reindex(range(1, 18))
print(skor.round(0))

# 1) 17 amaçlık karne
fig, ax = plt.subplots(figsize=(11, 7.2))
y = np.arange(17)[::-1]
ax.barh(y, skor.tr, color=[SKA_RENK[i] for i in skor.index], height=0.68)
ax.scatter(skor.oecd, y, marker="|", s=380, color="black", lw=2.4, zorder=5, label="OECD ülkelerinin medyanı")
for yy, (i, r) in zip(y, skor.iterrows()):
    ax.text(-2, yy, f"SKA {i} · {SKA_AD[i]}", ha="right", va="center", fontsize=10)
    if not np.isnan(r.tr):
        ax.text(r.tr + 1.2, yy, f"{r.tr:.0f}", va="center", fontsize=9.5, fontweight="bold")
ax.set_yticks([]); ax.set_xlim(0, 105); ax.axvline(50, color=RENK["gri"], ls=":", lw=1)
ax.set_xlabel("Türkiye'nin dünya içindeki yüzdelik sırası (100 = en iyi, 50 = dünya ortası)")
ax.set_title("Türkiye'nin SKA karnesi: 17 amaçta dünyadaki yeri", pad=26)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.62, 1.0), ncol=1)
ax.set_ylim(-0.8, 17.4)
ax.grid(axis="y", visible=False)
kaydet(fig, "04_1_karne", KAYNAK)

# 2) Gösterge düzeyinde: Türkiye ve OECD medyanı (yüzdelik)
Gs = G.sort_values(["ska", "tr_yuzdelik"])
fig, ax = plt.subplots(figsize=(10.5, 11))
yy = np.arange(len(Gs))[::-1]
for k, (_, r) in zip(yy, Gs.iterrows()):
    ax.plot([r.oecd_medyan_yuzdelik, r.tr_yuzdelik], [k, k], color="#ccc", lw=2, zorder=1)
ax.scatter(Gs.oecd_medyan_yuzdelik, yy, color="black", s=26, label="OECD medyanı", zorder=2)
ax.scatter(Gs.tr_yuzdelik, yy, color=[SKA_RENK[s] for s in Gs.ska], s=70, edgecolor="black", lw=0.6, label="Türkiye", zorder=3)
ax.set_yticks(yy, [f"{r.ska:>2}. {r.ad}" for _, r in Gs.iterrows()], fontsize=9)
ax.set_xlim(0, 101); ax.axvline(50, color=RENK["gri"], ls=":", lw=1)
ax.set_xlabel("Dünya içindeki yüzdelik sıra (100 = en iyi)")
ax.set_title("Gösterge gösterge Türkiye ve OECD")
ax.legend(frameon=False, loc="lower left")
kaydet(fig, "04_2_gostergeler", KAYNAK)

# 3) 2012–16'dan bugüne değişim: aynı ülke kümesinde dünya sıralamasındaki kayma (yüzdelik puan)
D = G.dropna(subset=["yuzdelik_once"]).copy()
D = D[~D.kod.isin(["ER.MRN.PTMR.ZS", "ER.LND.PTLD.ZS"])]   # koruma alanı kayıtlarında yöntem değişimi
D["kayma"] = D.yuzdelik_simdi_ortak - D.yuzdelik_once
D = D.sort_values("kayma")
fig, ax = plt.subplots(figsize=(10, 8.5))
ax.barh([f"{r.ska}. {r.ad}" for _, r in D.iterrows()], D.kayma,
        color=[RENK["yesil"] if v > 0 else RENK["kirmizi"] for v in D.kayma])
for i, v in enumerate(D.kayma):
    ax.text(v + (0.6 if v >= 0 else -0.6), i, f"{v:+.0f}", va="center", ha="left" if v >= 0 else "right", fontsize=8.5)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("Dünya sıralamasındaki değişim (yüzdelik puan; + = dünyaya göre iyileşti)")
ax.set_title("2012–16'dan bugüne: Türkiye dünyaya göre nerede ilerledi, nerede geriledi?")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "04_3_degisim", KAYNAK)
print(D[["ad", "tr_once_yil", "tr_once", "tr_yil", "tr_deger", "yuzdelik_once", "yuzdelik_simdi_ortak", "kayma"]].round(1).to_string())
