"""Makale 12: Yaşlanan Türkiye ve emeklilik sistemi (SKA 1.3) — Dünya Bankası nüfus tahmin ve projeksiyonları."""
import numpy as np
import pandas as pd
from ortak import RENK, kaydet, mtick, plt, wb, wb_ulkeler

KAYNAK = "Dünya Bankası, Population Estimates and Projections (BM verisine dayalı)"
ulk = wb_ulkeler(); gercek = set(ulk.ulke_kodu)
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()


def proj(kod, ulkeler="all"):
    d = wb(kod, ulkeler, "1960:2050", kaynak=40)
    d = d[d.ulke_kodu.isin(gercek)] if ulkeler == "all" else d
    return d.pivot_table(index="yil", columns="ulke_kodu", values="deger")


p65, bag = proj("SP.POP.65UP.TO.ZS"), proj("SP.POP.DPND.OL")

# 1) Nüfus piramidi 2025 ve 2050
gruplar = ["0004", "0509", "1014", "1519", "2024", "2529", "3034", "3539", "4044", "4549", "5054", "5559", "6064", "6569", "7074", "7579", "80UP"]
erk_t, kad_t = proj("SP.POP.TOTL.MA.IN", "TUR")["TUR"], proj("SP.POP.TOTL.FE.IN", "TUR")["TUR"]
P = {}
for g in gruplar:
    P[g] = {"E": proj(f"SP.POP.{g}.MA.5Y", "TUR")["TUR"] / 100 * erk_t, "K": proj(f"SP.POP.{g}.FE.5Y", "TUR")["TUR"] / 100 * kad_t}
etiket = [f"{g[:2].lstrip('0') or '0'}–{g[2:].lstrip('0')}" if g != "80UP" else "80+" for g in gruplar]
fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
for ax, yil in zip(axs, [2025, 2050]):
    e = np.array([P[g]["E"][yil] for g in gruplar]) / 1e6; k = np.array([P[g]["K"][yil] for g in gruplar]) / 1e6
    y = np.arange(len(gruplar))
    ax.barh(y, -e, color=RENK["mavi"], label="Erkek"); ax.barh(y, k, color=RENK["kirmizi"], label="Kadın")
    ax.set_yticks(y, etiket); ax.set_xlim(-4.2, 4.2)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{abs(v):g}"))
    ax.set_title(f"{yil}  ·  65+ payı %{p65['TUR'][yil]:.1f}".replace(".", ","))
    ax.set_xlabel("Milyon kişi"); ax.axvline(0, color="black", lw=0.6); ax.grid(axis="y", visible=False)
axs[0].legend(frameon=False, loc="upper left")
fig.suptitle("Türkiye'nin nüfus piramidi: 2025 ve 2050 (projeksiyon)", fontweight="bold", fontsize=14)
kaydet(fig, "12_1_piramit", KAYNAK)

# 2) 65+ payı: Türkiye ve diğer ülkeler
fig, ax = plt.subplots(figsize=(10.5, 5))
for kod, ad, renk, lw in [("TUR", "Türkiye", RENK["kirmizi"], 3), ("JPN", "Japonya", RENK["gri"], 1.8), ("DEU", "Almanya", "black", 1.8),
                          ("KOR", "G. Kore", RENK["mor"], 1.8), ("CHN", "Çin", RENK["sari"], 1.8), ("BRA", "Brezilya", RENK["yesil"], 1.8)]:
    s = p65[kod]
    ax.plot(s.loc[:2024].index, s.loc[:2024], color=renk, lw=lw, label=ad)
    ax.plot(s.loc[2024:].index, s.loc[2024:], color=renk, lw=lw, ls="--")
ax.axvline(2024.5, color=RENK["gri"], lw=0.8); ax.text(2025.5, 2, "projeksiyon →", fontsize=9, color="#555")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_title("65 yaş ve üstü nüfusun payı, 1960–2050")
ax.legend(frameon=False, loc="upper left")
kaydet(fig, "12_2_65ustu", KAYNAK)

# 3) Yaşlanma hızı: 65+ payının %10'dan %20'ye çıkma süresi
def esik_yili(s, e):
    s = s.dropna(); y = s[s >= e]
    return y.index[0] if len(y) else np.nan
hiz = pd.DataFrame({k: {"y10": esik_yili(p65[k], 10), "y20": esik_yili(p65[k], 20)} for k in p65.columns}).T.dropna()
hiz = hiz[hiz.y10 > 1960]
hiz["sure"] = hiz.y20 - hiz.y10
ad = {"TUR": "Türkiye", "JPN": "Japonya", "DEU": "Almanya", "KOR": "G. Kore", "CHN": "Çin", "BRA": "Brezilya", "ITA": "İtalya",
      "FRA": "Fransa", "USA": "ABD", "GBR": "İngiltere", "ESP": "İspanya", "POL": "Polonya", "THA": "Tayland", "IRN": "İran",
      "CHL": "Şili", "MEX": "Meksika", "VNM": "Vietnam", "RUS": "Rusya", "CAN": "Kanada", "AUS": "Avustralya", "COL": "Kolombiya", "NLD": "Hollanda", "SWE": "İsveç"}
H = hiz.loc[[k for k in ad if k in hiz.index]].sort_values("sure")
fig, ax = plt.subplots(figsize=(10, 6))
c = ax.barh([f"{ad[k]} ({int(r.y10)}→{int(r.y20)})" for k, r in H.iterrows()], H.sure,
            color=[RENK["kirmizi"] if k == "TUR" else RENK["gri"] for k in H.index])
ax.bar_label(c, labels=[f"{v:.0f} yıl" for v in H.sure], padding=3, fontsize=9)
ax.set_title("Yaşlanma hızı: 65+ payı %10'dan %20'ye kaç yılda çıktı / çıkacak?")
ax.grid(axis="y", visible=False); ax.tick_params(axis="y", labelsize=9)
kaydet(fig, "12_3_hiz", KAYNAK)
print(H.astype(int).to_string())
print("Tüm ülkeler (1960 sonrası %10'u geçen) medyan süre:", hiz.sure.median(), "n", len(hiz), "TR'den hızlı:", list(hiz[hiz.sure < hiz.loc['TUR', 'sure']].index))

# 4) Bir yaşlıya düşen çalışan
calisma = proj("SP.POP.1564.TO", "TUR")["TUR"]; yasli = proj("SP.POP.65UP.TO", "TUR")["TUR"]
istihdam_orani = wb("SL.EMP.TOTL.SP.ZS", "TUR", "2015:2025").dropna().sort_values("yil").deger.iloc[-1] / 100   # 15+ istihdam/nüfus
nufus15 = calisma + yasli
calisan_2025 = nufus15[2025] * istihdam_orani
kadin_lfp = wb("SL.TLF.CACT.FE.ZS", "TUR", "2015:2025").dropna().sort_values("yil").deger.iloc[-1]
S = {}
for yil in [2025, 2035, 2050]:
    temel = nufus15[yil] * istihdam_orani / yasli[yil]
    S[yil] = {"Destek oranı (15–64 / 65+)": calisma[yil] / yasli[yil], "Çalışan / 65+ (bugünkü istihdam oranıyla)": temel}
S = pd.DataFrame(S).T
# Kadın katılımı OECD medyanına (≈%55,6) çıkarsa: istihdam oranına yaklaşık etki (kadınların nüfusun yarısı olduğu varsayımıyla)
artis = (55.6 - kadin_lfp) / 100 * 0.5 * (1 - 0.10)    # %10 işsizlik varsayımı
S["Çalışan / 65+ (kadın katılımı OECD medyanında)"] = [nufus15[y] * (istihdam_orani + artis) / yasli[y] for y in S.index]
print("İstihdam oranı 15+:", round(istihdam_orani * 100, 1), "kadın LFP:", kadin_lfp); print(S.round(2).to_string())
fig, ax = plt.subplots(figsize=(10, 4.8))
x = np.arange(len(S))
for i, (sut, renk) in enumerate(zip(S.columns, [RENK["gri"], RENK["kirmizi"], RENK["yesil"]])):
    c = ax.bar(x + (i - 1) * 0.27, S[sut], 0.27, color=renk, label=sut)
    ax.bar_label(c, labels=[f"{v:.1f}".replace(".", ",") for v in S[sut]], padding=2, fontsize=9)
ax.set_xticks(x, S.index)
ax.set_ylabel("65 yaş üstü bir kişiye düşen kişi sayısı")
ax.set_title("Bir yaşlıyı kaç kişi taşıyacak?")
ax.legend(frameon=False, fontsize=9.5); ax.grid(axis="x", visible=False)
kaydet(fig, "12_4_destek", KAYNAK + " · ILO")
print("65+ kişi:", {y: round(yasli[y] / 1e6, 1) for y in [2025, 2035, 2050]}, "80+:", round((P['80UP']['E'][2025] + P['80UP']['K'][2025]) / 1e6, 1), "→", round((P['80UP']['E'][2050] + P['80UP']['K'][2050]) / 1e6, 1))
print("Nüfus 2025/2050 ve zirve:", round(proj("SP.POP.TOTL", "TUR")["TUR"][2025] / 1e6, 1), round(proj("SP.POP.TOTL", "TUR")["TUR"][2050] / 1e6, 1),
      proj("SP.POP.TOTL", "TUR")["TUR"].idxmax())
print("Yaşlı bağımlılık TR:", bag["TUR"][[2000, 2025, 2050]].round(1).to_dict(), "OECD medyan 2025/2050:", bag[[c for c in OECD if c in bag]].median(axis=1)[[2025, 2050]].round(1).to_dict())
tfr = wb("SP.DYN.TFRT.IN", "TUR", "1960:2025").dropna().sort_values("yil")
print("Doğurganlık:", dict(zip(tfr.yil.tail(5), tfr.deger.tail(5).round(2))), "1960:", round(tfr.deger.iloc[0], 2))
