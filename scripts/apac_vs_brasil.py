"""
APAC (PCS/VCS/LCP) vs Brasil en torneos internacionales (Worlds, MSI, EWC).
Genera 2 imágenes para Twitter/X:
  1) tarjeta de KPIs (estilo hextech, sin logos ni material de Riot)
  2) gráfico de barras por año
Datos: Oracle's Elixir (CSV por año, 2014-2026).
NOTA: MVK 3-0 FURIA (Play-In Worlds 2026) NO está en el CSV (llega hasta 13/10/2026).
      Se añade a mano en el gráfico como '2026*' y se avisa en el pie.
"""
import os
DATA_DIR = os.environ.get("DATA_DIR", "data")      # carpeta con los CSV de Oracle's Elixir
OUT_DIR = os.environ.get("OUT_DIR", "output")      # carpeta donde se guardan las imágenes
os.makedirs(OUT_DIR, exist_ok=True)

import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import LinearSegmentedColormap

OUT_CARD = os.path.join(OUT_DIR, "apac_vs_brasil_card.png")
OUT_CHART = os.path.join(OUT_DIR, "apac_vs_brasil_tendencia.png")

# ---------- 1) Datos ----------
cols = ["gameid", "league", "date", "position", "teamname", "result"]
t = pd.concat([pd.read_csv(f, usecols=cols, low_memory=False)
               for f in sorted(glob.glob(f"{DATA_DIR}/20*_LoL_esports_match_data_from_OraclesElixir.csv"))],
              ignore_index=True)
t = t[t.position == "team"].copy()
t["y"] = pd.to_datetime(t["date"]).dt.year          # año real (la columna 'year' tiene filas del año siguiente)

regiones = {"CBLOL": "BR", "LTA S": "BR", "PCS": "APAC", "VCS": "APAC", "LCP": "APAC"}
dom = t[t.league.isin(regiones)].copy()
dom["reg"] = dom.league.map(regiones)
dom = dom.groupby(["y", "teamname"]).reg.agg(lambda s: s.mode()[0]).reset_index()

m = t[["gameid", "league", "y", "teamname", "result"]]
mm = m.merge(m[["gameid", "teamname", "result"]], on="gameid", suffixes=("", "_o"))
mm = mm[mm.teamname != mm.teamname_o]
intl = mm[mm.league.isin(["WLDs", "MSI", "EWC"])]
intl = intl.merge(dom, on=["y", "teamname"], how="left")
intl = intl.merge(dom.rename(columns={"teamname": "teamname_o", "reg": "reg_o"}), on=["y", "teamname_o"], how="left")
x = intl[(intl.reg == "APAC") & (intl.reg_o == "BR")]          # 'result' = victoria del equipo APAC

anual = x.groupby("y").result.agg(partidas="size", victorias="sum")
anual["wr"] = anual.victorias / anual.partidas
tot_p, tot_v = int(anual.partidas.sum()), int(anual.victorias.sum())
print(anual.round(2)); print("Total:", tot_v, "/", tot_p, f"= {tot_v/tot_p:.1%}")

# ---------- 2) Estilo ----------
BG, BG2 = "#010A13", "#0A1428"
ORO, ORO_OSC, ORO_CLARO = "#C8AA6E", "#785A28", "#F0E6D2"
TEAL, ROJO, GRIS = "#0AC8B9", "#E84057", "#A09B8C"

# ---------- 3) Tarjeta ----------
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

ax.text(80, 80.2, "MVK  vs  FURIA", ha="center", va="center", color=ORO_CLARO, fontsize=44,
        fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.text(80, 73.2, "APAC  VS  BRASIL   ·   EDICIÓN DATOS", ha="center", va="center", color=TEAL,
        fontsize=15, fontweight="bold", zorder=6)
ax.plot([30, 130], [70, 70], color=ORO, lw=1.2, zorder=3); rombo(80, 70, 1.1)

caja_y, caja_h, caja_w = 47.5, 20, 46
numeros = [
    ("3 - 0", "MVK Esports a FURIA\nPlay-In de Worlds 2026 (Bo5)", TEAL),
    (f"{tot_v/tot_p:.0%}", f"APAC gana el {tot_v/tot_p:.0%} de las partidas\nvs Brasil ({tot_v} de {tot_p}, 2021-25)", TEAL),
    ("1º", "3-0 en Bo5 de APAC a un\nequipo brasileño en los datos", ORO),
]
for x0, (num, txt, col) in zip([8, 57, 106], numeros):
    panel(x0, caja_y, caja_w, caja_h, col)
    ax.text(x0 + caja_w / 2, caja_y + 13.2, num, ha="center", va="center", color=col, fontsize=44,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(x0 + caja_w / 2, caja_y + 4.6, txt, ha="center", va="center", color=ORO_CLARO,
            fontsize=12.5, linespacing=1.35, zorder=6)

# Panel izquierdo: historial por año
panel(8, 9, 70, 34, ORO_OSC)
ax.text(43, 40, "APAC vs BRASIL POR AÑO", ha="center", va="center", color=ORO, fontsize=13,
        fontweight="bold", zorder=6)
for i, (anio, r) in enumerate(anual.iterrows()):
    y = 35 - i * 5.6
    ax.text(14, y, str(anio), ha="left", va="center", color=ORO_CLARO, fontsize=13, zorder=6)
    ancho = r.wr * 36
    ax.add_patch(Rectangle((24, y - 1.2), max(ancho, 0.2), 2.4, fc=TEAL if r.wr >= 0.5 else ROJO, ec="none", zorder=3))
    ax.text(24 + ancho + 1.5, y, f"{int(r.victorias)}/{int(r.partidas)}", ha="left", va="center",
            color=ORO_CLARO, fontsize=14, fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.plot([24 + 0.5 * 36] * 2, [8.5 + 2, 38 - 1.5], color=GRIS, lw=1, ls="--", zorder=2)
ax.text(24 + 0.5 * 36, 10.2, "50%", ha="center", va="center", color=GRIS, fontsize=9, zorder=6)

# Panel derecho: precedentes (series reconstruidas a mano del análisis)
panel(82, 9, 70, 34, ORO_OSC)
ax.text(117, 40, "SERIES MÁS PARECIDAS", ha="center", va="center", color=ORO, fontsize=13,
        fontweight="bold", zorder=6)
prec = [("MSI 2025", "GAM 3-2 FURIA"),
        ("MSI 2023", "PSG Talon 2-0 LOUD"),
        ("Worlds 2023", "PSG Talon 2-0 LOUD"),
        ("Worlds 2023", "LOUD 2-0 GAM")]
for i, (torneo, serie) in enumerate(prec):
    y = 34 - i * 5.2
    ax.text(87, y, torneo, ha="left", va="center", color=GRIS, fontsize=12, zorder=6)
    ax.text(147, y, serie, ha="right", va="center", color=ORO_CLARO, fontsize=13,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.text(117, 12.5, "Ningún 3-0 en Bo5 antes de este partido", ha="center", va="center",
        color=ORO, fontsize=11.5, zorder=6)

ax.text(80, 5.2, "Datos: Oracle's Elixir (hasta 13/10/2026) · Worlds, MSI y EWC · APAC = PCS/VCS/LCP · "
        "MVK 3-0 FURIA no está en el CSV (añadido a mano)",
        ha="center", va="center", color=GRIS, fontsize=9.5, zorder=6)
fig.savefig(OUT_CARD, facecolor=BG); plt.close(fig)

# ---------- 4) Gráfico por años (mismo estilo que Europa vs NA) ----------
BG_C, TXT, SUB, AZUL, ROJO_C = "#0f1419", "#e7e9ea", "#8b98a5", "#4d9de0", "#e15554"
datos = anual.copy()
datos.loc[2026] = [3, 3, 1.0]            # 2026*: MVK 3-0 FURIA (juegos), añadido a mano
datos = datos.sort_index()
fig, ax2 = plt.subplots(figsize=(16, 9), dpi=100)
fig.patch.set_facecolor(BG_C); ax2.set_facecolor(BG_C)
etq = [str(a) if a != 2026 else "2026*" for a in datos.index]
cols_b = [AZUL if v >= 0.5 else ROJO_C for v in datos.wr]
barras = ax2.bar(etq, datos.wr * 100, color=cols_b, width=0.62)
barras[-1].set_hatch("//"); barras[-1].set_edgecolor(BG_C)       # la barra manual se distingue
ax2.axhline(50, color=SUB, lw=1.4, ls="--")
ax2.text(len(datos) - 0.45, 51.5, "50%", color=SUB, fontsize=13, ha="right")
for b, (_, r) in zip(barras, datos.iterrows()):
    ax2.text(b.get_x() + b.get_width() / 2, r.wr * 100 + 2, f"{int(r.victorias)}/{int(r.partidas)}",
             ha="center", color=TXT, fontsize=16)
ax2.set_ylim(0, 118); ax2.set_yticks([0, 25, 50, 75, 100])
ax2.set_yticklabels([f"{v}%" for v in [0, 25, 50, 75, 100]], color=SUB, fontsize=13)
ax2.tick_params(axis="x", colors=TXT, labelsize=15, length=0); ax2.tick_params(axis="y", length=0)
for s in ax2.spines.values(): s.set_visible(False)
ax2.grid(axis="y", color="#2a3139", lw=0.8); ax2.set_axisbelow(True)
ax2.text(-0.4, 110, f"2021-25: {tot_v} de {tot_p} ({tot_v/tot_p:.0%})", ha="left", color=AZUL, fontsize=20,
         fontweight="bold", transform=ax2.transData)
fig.text(0.06, 0.93, "APAC vs Brasil en torneos internacionales", color=TXT, fontsize=30, fontweight="bold", ha="left")
fig.text(0.06, 0.885, "% de partidas ganadas por equipos de PCS/VCS/LCP contra brasileños (Worlds, MSI y EWC)",
         color=SUB, fontsize=16, ha="left")
fig.text(0.06, 0.045, "Fuente: Oracle's Elixir (hasta 13/10/2026) · Partidas, no series · Número = victorias APAC / partidas",
         color=SUB, fontsize=12, ha="left")
fig.text(0.06, 0.015, "*2026: MVK Esports 3-0 FURIA (Play-In de Worlds), añadido a mano; no está en el CSV",
         color=SUB, fontsize=12, ha="left")
plt.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.13)
fig.savefig(OUT_CHART, facecolor=BG_C)
