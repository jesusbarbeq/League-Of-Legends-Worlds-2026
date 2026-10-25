"""
Tarjeta de KPIs: KC vs C9 · Europa vs NA (estilo hextech, sin logos ni material de Riot).
Datos: Oracle's Elixir. Los KPIs de KC y C9 se calculan del CSV de 2026.
"""
import os
DATA_DIR = os.environ.get("DATA_DIR", "data")      # carpeta con los CSV de Oracle's Elixir
OUT_DIR = os.environ.get("OUT_DIR", "output")      # carpeta donde se guardan las imágenes
os.makedirs(OUT_DIR, exist_ok=True)

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch

DATA_2026 = os.path.join(DATA_DIR, "2026_LoL_esports_match_data_from_OraclesElixir.csv")
OUT_PNG = os.path.join(OUT_DIR, "kpi_card_kc_c9.png")

# --- 1) KPIs de equipo (una fila por equipo y partida) ---
cols = ["gameid", "date", "position", "teamname", "result", "golddiffat15", "golddiffat25",
        "firstblood", "firsttower", "teamkills"]
df = pd.read_csv(DATA_2026, usecols=cols, low_memory=False)
t = df[df.position == "team"]

def kpis(nombre):
    x = t[t.teamname == nombre].sort_values("date")
    ult10 = x.tail(10).result.sum()
    return {
        "wr": x.result.mean() * 100,
        "gd15": x.golddiffat15.mean(),
        "fb": x.firstblood.mean() * 100,
        "ft": x.firsttower.mean() * 100,
        "kills": x.teamkills.mean(),
        "gd25": x.golddiffat25.mean(),
        "ult10": int(ult10),
    }

kc, c9 = kpis("Karmine Corp"), kpis("Cloud9")

# --- 2) Paleta hextech ---
BG, BG2 = "#010A13", "#0A1428"
ORO, ORO_OSC, ORO_CLARO = "#C8AA6E", "#785A28", "#F0E6D2"
TEAL, ROJO, GRIS = "#0AC8B9", "#E84057", "#A09B8C"
C_KC, C_C9 = TEAL, ORO

fig = plt.figure(figsize=(16, 9), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 90); ax.axis("off")
fig.patch.set_facecolor(BG)
# degradado vertical de fondo
import numpy as np
grad = np.linspace(0, 1, 256).reshape(-1, 1)
from matplotlib.colors import LinearSegmentedColormap
ax.imshow(grad, extent=[0, 160, 0, 90], aspect="auto", origin="lower", zorder=0,
          cmap=LinearSegmentedColormap.from_list("bg", [BG, BG2]))

def marco(x0, y0, w, h, color=ORO, lw=2, z=2):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=color, lw=lw, zorder=z))

def rombo(x, y, r=0.9, color=ORO):
    ax.add_patch(Polygon([(x, y + r), (x + r, y), (x, y - r), (x - r, y)], fc=color, ec="none", zorder=5))

def panel(x0, y0, w, h, color=ORO):
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#0B1A2E", ec="none", alpha=0.85, zorder=1))
    marco(x0, y0, w, h, color=color, lw=1.6)
    for cx, cy in [(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h)]:
        rombo(cx, cy, 0.8, color)

# Marco general
marco(1.5, 1.5, 157, 87, ORO, 3)
marco(2.6, 2.6, 154.8, 84.8, ORO_OSC, 1)
for cx, cy in [(1.5, 1.5), (158.5, 1.5), (1.5, 88.5), (158.5, 88.5)]:
    rombo(cx, cy, 1.4)

# --- Cabecera ---
ax.text(80, 80.2, "KC  vs  C9", ha="center", va="center", color=ORO_CLARO, fontsize=46,
        fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.text(80, 73.2, "EUROPA  VS  NA   ·   EDICIÓN DATOS", ha="center", va="center", color=TEAL,
        fontsize=15, fontweight="bold", zorder=6)
ax.plot([30, 130], [70, 70], color=ORO, lw=1.2, zorder=3); rombo(80, 70, 1.1)

# --- Tres números grandes ---
caja_y, caja_h, caja_w = 47.5, 20, 46
xs = [8, 57, 106]
datos = [
    ("53%", "Europa gana en torneos\ninternacionales (Worlds, MSI, EWC)", TEAL),
    ("8 de 24", "Desde 2024: solo 33%\nde las partidas contra NA", ROJO),
    ("0 - 6", "MSI 2026:\nEuropa vs NA", ROJO),
]
for x0, (num, txt, col) in zip(xs, datos):
    panel(x0, caja_y, caja_w, caja_h, col)
    ax.text(x0 + caja_w / 2, caja_y + 13.2, num, ha="center", va="center", color=col, fontsize=44,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(x0 + caja_w / 2, caja_y + 4.6, txt, ha="center", va="center", color=ORO_CLARO,
            fontsize=12.5, linespacing=1.35, zorder=6)

# --- Comparativa KC vs C9 (barras espejo) ---
ax.text(80, 43.3, "KARMINE CORP  vs  CLOUD9   ·   2026", ha="center", va="center", color=ORO,
        fontsize=14, fontweight="bold", zorder=6)
ax.text(29, 43.3, "KC", ha="center", va="center", color=C_KC, fontsize=20, fontfamily="DejaVu Serif",
        fontweight="bold", zorder=6)
ax.text(131, 43.3, "C9", ha="center", va="center", color=C_C9, fontsize=20, fontfamily="DejaVu Serif",
        fontweight="bold", zorder=6)

filas = [
    ("Winrate",               kc["wr"],    c9["wr"],    lambda v: f"{v:.0f}%"),
    ("Oro a los 15 min",      kc["gd15"],  c9["gd15"],  lambda v: f"{v:+.0f}"),
    ("Primera sangre",        kc["fb"],    c9["fb"],    lambda v: f"{v:.0f}%"),
    ("Primera torre",         kc["ft"],    c9["ft"],    lambda v: f"{v:.0f}%"),
    ("Kills por partida",     kc["kills"], c9["kills"], lambda v: f"{v:.1f}"),
    ("Oro a los 25 min",      kc["gd25"],  c9["gd25"],  lambda v: f"{v:+.0f}"),
    ("Victorias últimas 10",  kc["ult10"], c9["ult10"], lambda v: f"{v:.0f}/10"),
]
y_ini, paso, mitad_bar = 38.2, 4.95, 33
centro = 80
for i, (nom, a, b, fmt) in enumerate(filas):
    y = y_ini - i * paso
    m = max(abs(a), abs(b))
    la, lb = abs(a) / m * mitad_bar * 0.62, abs(b) / m * mitad_bar * 0.62
    gana_kc = a >= b
    # fondo de fila
    ax.add_patch(Rectangle((8, y - 2.0), 144, 4.0, fc="#0B1A2E", ec="none", alpha=0.55, zorder=1))
    # barras (a izquierda KC, a derecha C9)
    ax.add_patch(Rectangle((centro - 14 - la, y - 1.0), la, 2.0, fc=C_KC, ec="none",
                           alpha=1 if gana_kc else 0.45, zorder=3))
    ax.add_patch(Rectangle((centro + 14, y - 1.0), lb, 2.0, fc=C_C9, ec="none",
                           alpha=0.45 if gana_kc else 1, zorder=3))
    ax.text(centro, y, nom, ha="center", va="center", color=ORO_CLARO, fontsize=12.5, zorder=6)
    ax.text(centro - 14 - la - 1.2, y, fmt(a), ha="right", va="center", color=C_KC if gana_kc else GRIS,
            fontsize=17, fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(centro + 14 + lb + 1.2, y, fmt(b), ha="left", va="center", color=GRIS if gana_kc else C_C9,
            fontsize=17, fontfamily="DejaVu Serif", fontweight="bold", zorder=6)

ax.text(80, 4.6,
        "Datos: Oracle's Elixir (hasta 13/10/2026) · KC: LEC+EWC+MSI · C9: LCS+EWC+Americas Cup · "
        "Partidas, no series · Ligas distintas",
        ha="center", va="center", color=GRIS, fontsize=9.8, zorder=6)

fig.savefig(OUT_PNG, facecolor=BG)
print("KC", {k: round(v, 1) for k, v in kc.items()})
print("C9", {k: round(v, 1) for k, v in c9.items()})
