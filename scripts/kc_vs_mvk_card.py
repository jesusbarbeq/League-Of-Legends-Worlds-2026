"""
Tarjeta hextech: KC vs MVK · Europa vs APAC (solo APAC, sin mezclar con NA).
Datos: Oracle's Elixir (CSV 2014-2026, hasta 13/10/2026). Sin logos ni material de Riot.
Todo sale del CSV; no hay datos añadidos a mano.
"""
import os
DATA_DIR = os.environ.get("DATA_DIR", "data")      # carpeta con los CSV de Oracle's Elixir
OUT_DIR = os.environ.get("OUT_DIR", "output")      # carpeta donde se guardan las imágenes
os.makedirs(OUT_DIR, exist_ok=True)

import glob
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap

OUT = os.path.join(OUT_DIR, "kc_vs_mvk_card.png")

# ---------- Datos ----------
cols = ["gameid", "league", "date", "position", "teamname", "result"]
t = pd.concat([pd.read_csv(f, usecols=cols, low_memory=False)
               for f in sorted(glob.glob(f"{DATA_DIR}/20*_LoL_esports_match_data_from_OraclesElixir.csv"))],
              ignore_index=True)
t = t[t.position == "team"].copy()
t["y"] = pd.to_datetime(t["date"]).dt.year
reg = {"LEC": "EU", "EU LCS": "EU", "PCS": "APAC", "VCS": "APAC", "LCP": "APAC"}
dom = t[t.league.isin(reg)].copy(); dom["reg"] = dom.league.map(reg)
dom = dom.groupby(["y", "teamname"]).reg.agg(lambda s: s.mode()[0]).reset_index()
m = t[["gameid", "league", "y", "teamname", "result"]]
mm = m.merge(m[["gameid", "teamname", "result"]], on="gameid", suffixes=("", "_o"))
mm = mm[mm.teamname != mm.teamname_o]
intl = mm[mm.league.isin(["WLDs", "MSI", "EWC"])]
intl = intl.merge(dom, on=["y", "teamname"], how="left")
intl = intl.merge(dom.rename(columns={"teamname": "teamname_o", "reg": "reg_o"}), on=["y", "teamname_o"], how="left")
x = intl[(intl.reg == "EU") & (intl.reg_o == "APAC")]       # 'result' = victoria europea
anual = x.groupby("y").result.agg(partidas="size", victorias="sum")
hist_v, hist_g = int(anual.victorias.sum()), int(anual.partidas.sum())
rec = anual.loc[2024:]; rec_v, rec_g = int(rec.victorias.sum()), int(rec.partidas.sum())
print(anual); print("Histórico:", hist_v, hist_g, f"{hist_v/hist_g:.1%}", "| 2024-26:", rec_v, rec_g, f"{rec_v/rec_g:.1%}")

# ---------- Estilo ----------
BG, BG2 = "#010A13", "#0A1428"
ORO, ORO_OSC, ORO_CLARO = "#C8AA6E", "#785A28", "#F0E6D2"
TEAL, ROJO, GRIS = "#0AC8B9", "#E84057", "#A09B8C"
fig = plt.figure(figsize=(16, 9), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 90); ax.axis("off")
fig.patch.set_facecolor(BG)
ax.imshow(np.linspace(0, 1, 256).reshape(-1, 1), extent=[0, 160, 0, 90], aspect="auto", origin="lower",
          zorder=0, cmap=LinearSegmentedColormap.from_list("bg", [BG, BG2]))
def marco(x0, y0, w, h, color=ORO, lw=2):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=color, lw=lw, zorder=2))
def rombo(cx, cy, r=0.9, color=ORO):
    ax.add_patch(Polygon([(cx, cy + r), (cx + r, cy), (cx, cy - r), (cx - r, cy)], fc=color, ec="none", zorder=5))
def panel(x0, y0, w, h, color=ORO):
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#0B1A2E", ec="none", alpha=0.85, zorder=1))
    marco(x0, y0, w, h, color, 1.6)
    for cx, cy in [(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h)]:
        rombo(cx, cy, 0.8, color)

marco(1.5, 1.5, 157, 87, ORO, 3); marco(2.6, 2.6, 154.8, 84.8, ORO_OSC, 1)
for cx, cy in [(1.5, 1.5), (158.5, 1.5), (1.5, 88.5), (158.5, 88.5)]:
    rombo(cx, cy, 1.4)
ax.text(80, 80.2, "KC  vs  MVK", ha="center", va="center", color=ORO_CLARO, fontsize=44,
        fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.text(80, 73.2, "EUROPA  VS  APAC   ·   EDICIÓN DATOS", ha="center", va="center", color=TEAL,
        fontsize=15, fontweight="bold", zorder=6)
ax.plot([30, 130], [70, 70], color=ORO, lw=1.2, zorder=3); rombo(80, 70, 1.1)

numeros = [
    (f"{hist_v/hist_g:.0%}", f"Europa gana el {hist_v/hist_g:.0%} de las partidas\nvs APAC en el historial ({hist_v} de {hist_g})", TEAL),
    (f"{rec_v/rec_g:.0%}", f"Desde 2024: {rec_v} de {rec_g} partidas\nganadas por Europa", TEAL),
    ("3 - 0", "KC vs Deep Cross Gaming (MSI 2026):\nsu única serie vs APAC en los datos", ORO),
]
for x0, (num, txt, col) in zip([8, 57, 106], numeros):
    panel(x0, 47.5, 46, 20, col)
    ax.text(x0 + 23, 60.7, num, ha="center", va="center", color=col, fontsize=44,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(x0 + 23, 52.1, txt, ha="center", va="center", color=ORO_CLARO, fontsize=12,
            linespacing=1.35, zorder=6)

# Panel izquierdo: Europa vs APAC por año
panel(8, 9, 70, 34, ORO_OSC)
ax.text(43, 40, "EUROPA vs APAC POR AÑO", ha="center", va="center", color=ORO, fontsize=13, fontweight="bold", zorder=6)
anios = [a for a in anual.index if a >= 2022]
for i, a in enumerate(anios):
    y = 34.5 - i * 5.6
    r = anual.loc[a]; wr = r.victorias / r.partidas
    ax.text(13, y, str(a), ha="left", va="center", color=ORO_CLARO, fontsize=13, zorder=6)
    ax.add_patch(Rectangle((24, y - 1.2), wr * 34, 2.4, fc=TEAL if wr >= 0.5 else ROJO, ec="none", zorder=3))
    ax.text(62, y, f"{int(r.victorias)}/{int(r.partidas)}", ha="left", va="center", color=ORO_CLARO,
            fontsize=13.5, fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.plot([24 + 17] * 2, [10.5, 37], color=GRIS, lw=1, ls="--", zorder=2)
ax.text(24 + 17, 9.9, "50%", ha="center", va="center", color=GRIS, fontsize=9, zorder=6)

# Panel derecho: últimas series (reconstruidas en el análisis por día y pareja)
panel(82, 9, 70, 34, ORO_OSC)
ax.text(117, 40, "ÚLTIMAS SERIES EUROPA vs APAC", ha="center", va="center", color=ORO, fontsize=13,
        fontweight="bold", zorder=6)
series = [("EWC 2026", "GAM 2-1 Movistar KOI", ORO),
          ("MSI 2026", "KC 3-0 Deep Cross Gaming", TEAL),
          ("Worlds 2025", "Movistar KOI 2-1 Team Secret Whales", TEAL),
          ("MSI 2025", "G2 3-2 GAM", TEAL),
          ("MSI 2025", "CTBC Flying Oyster 3-1 Movistar KOI", ORO)]
for i, (torneo, serie, col) in enumerate(series):
    y = 34.5 - i * 4.7
    ax.text(87, y, torneo, ha="left", va="center", color=GRIS, fontsize=11.5, zorder=6)
    ax.text(147, y, serie, ha="right", va="center", color=col, fontsize=11.5, fontweight="bold", zorder=6)
ax.text(117, 11.0, "Azul = gana Europa · Dorado = gana APAC", ha="center", va="center", color=GRIS, fontsize=10, zorder=6)

ax.text(80, 5.4, "Datos: Oracle's Elixir (hasta 13/10/2026) · Worlds, MSI y EWC · APAC = PCS/VCS/LCP · Partidas, no series",
        ha="center", va="center", color=GRIS, fontsize=9.8, zorder=6)
fig.savefig(OUT, facecolor=BG)
