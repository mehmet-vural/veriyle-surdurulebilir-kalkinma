"""Makale analizlerinde ortak grafik stili ve yardımcılar."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick  # noqa: F401  (analiz dosyalarında kullanılıyor)
import pandas as pd
import requests

KOK = Path(__file__).resolve().parent.parent
GORSEL = KOK / "gorseller"
VERI = KOK / "veri"
GORSEL.mkdir(exist_ok=True)
VERI.mkdir(exist_ok=True)

RENK = {"mavi": "#1F5AA6", "kirmizi": "#C8102E", "sari": "#E3A21A", "yesil": "#1B7F4B",
        "mor": "#6A1B9A", "gri": "#8A8F98", "turkuaz": "#138D90", "turkiye": "#C8102E"}
PALET = [RENK[k] for k in ["mavi", "kirmizi", "sari", "yesil", "mor", "turkuaz", "gri"]]
plt.rcParams.update({
    "figure.figsize": (10, 5), "figure.dpi": 110, "savefig.dpi": 160,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "axes.titleweight": "bold",
    "axes.titlesize": 13, "font.size": 10.5, "axes.prop_cycle": plt.cycler(color=PALET),
})


def kaydet(fig, ad, kaynak=None):
    """Grafiği kaydeder; alt köşeye veri kaynağını yazar."""
    if kaynak:
        fig.text(0.99, 0.005, f"Kaynak: {kaynak} · Analiz: Mehmet Vural", ha="right", va="bottom",
                 fontsize=8, color="#777")
    fig.tight_layout(rect=(0, 0.03 if kaynak else 0, 1, 1))
    yol = GORSEL / f"{ad}.png"
    fig.savefig(yol, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return yol


def indir(url, dosya, **kw):
    """URL'yi bir kez indirir, veri/ klasöründe saklar."""
    yol = VERI / dosya
    if not yol.exists():
        r = requests.get(url, timeout=kw.pop("timeout", 120), **kw)
        r.raise_for_status()
        yol.write_bytes(r.content)
    return yol


def wb(gosterge, ulkeler="all", donem="2000:2025", kaynak=None):
    """Dünya Bankası API: uzun formatlı tablo (ulke_kodu, ulke, yil, deger)."""
    dosya = VERI / f"wb_{gosterge}_{ulkeler.replace(';', '-')[:40]}_{donem.replace(':', '-')}.csv"
    if not dosya.exists():
        url = f"https://api.worldbank.org/v2/country/{ulkeler}/indicator/{gosterge}"
        sayfa, satirlar = 1, []
        while True:
            p = {"format": "json", "date": donem, "per_page": 20000, "page": sayfa}
            if kaynak:
                p["source"] = kaynak
            for deneme in range(4):
                try:
                    j = requests.get(url, params=p, timeout=120).json(); break
                except requests.RequestException:
                    if deneme == 3:
                        raise
                    import time; time.sleep(15 * (deneme + 1))
            satirlar += [{"ulke_kodu": k["countryiso3code"], "ulke": k["country"]["value"],
                          "yil": int(k["date"]), "deger": k["value"]} for k in j[1] or []]
            if sayfa >= j[0]["pages"]:
                break
            sayfa += 1
        pd.DataFrame(satirlar).to_csv(dosya, index=False)
    return pd.read_csv(dosya)


def wb_ulkeler():
    """Toplulaştırılmış bölgeler hariç gerçek ülkeler: kod -> (ad, bölge, gelir grubu)."""
    dosya = VERI / "wb_ulkeler.csv"
    if not dosya.exists():
        j = requests.get("https://api.worldbank.org/v2/country", params={"format": "json", "per_page": 400},
                         timeout=60).json()[1]
        pd.DataFrame([{"ulke_kodu": u["id"], "ulke": u["name"], "bolge": u["region"]["value"],
                       "gelir": u["incomeLevel"]["value"]} for u in j if u["region"]["id"] != "NA"]
                     ).to_csv(dosya, index=False)
    return pd.read_csv(dosya)
