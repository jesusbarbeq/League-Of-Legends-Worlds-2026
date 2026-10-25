"""
Tarjeta hextech: ¿cuántas veces gana la serie quien se pone 2-0 en un Bo5 internacional?
Datos: Oracle's Elixir (CSV 2014-2026, hasta 13/10/2026). Worlds, MSI y EWC. Sin logos ni material de Riot.

Método: el CSV no indica el formato de la serie, así que se reconstruye agrupando partidas por
(torneo, pareja de equipos) y abriendo una serie nueva cuando el nº de partida no aumenta. Se cuenta como Bo5 completo toda serie con 3+ partidas en la que
el mismo equipo gana las dos primeras y alguien llega a 3 victorias (descarta series con datos incompletos).
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

OUT = os.path.join(OUT_DIR, "bo5_2_0_card.png")
EUROPEOS = {"G2 Esports", "Team BDS", "Fnatic", "TSM"}   # equipos EU de las remontadas (TSM es NA: no está aquí)

# ---------- Datos ----------
cols = ["gameid", "league", "date", "position", "teamname", "result", "game"]
t = pd.concat([pd.read_csv(f, usecols=cols, low_memory=False)
               for f in sorted(glob.glob(f"{DATA_DIR}/20*_LoL_esports_match_data_from_OraclesElixir.csv"))],
              ignore_index=True)
t = t[(t.position == "team") & t.game.notna()].copy()
t["dt"] = pd.to_datetime(t["date"]); t["y"] = t.dt.dt.year
t = t[t.league.isin(["WLDs", "MSI", "EWC"])]
m = t[["gameid", "league", "y", "dt", "teamname", "result", "game"]]
mm = m.merge(m[["gameid", "teamname", "result"]], on="gameid", suffixes=("", "_o"))
mm = mm[mm.teamname != mm.teamname_o].copy()
mm["a"] = mm[["teamname", "teamname_o"]].min(axis=1); mm["b"] = mm[["teamname", "teamname_o"]].max(axis=1)
mm = mm[mm.teamname == mm.a].sort_values(["league", "a", "b", "dt", "game"])
key = mm.league + "|" + mm.a + "|" + mm.b
# nueva serie cuando el nº de partida (game) no aumenta (así una serie que cruza la medianoche no se parte)
mm["sid"] = ((key != key.shift()) | (mm.game <= mm.game.shift()) | ((mm.dt - mm.dt.shift()).dt.days > 3)).cumsum()
rows = []
for sid, x in mm.groupby("sid"):
    res = x.result.tolist(); wa = sum(res); wb = len(res) - wa
    if len(res) >= 3 and res[0] == res[1] and max(wa, wb) == 3 and x.game.iloc[0] == 1:
        a_, b_ = x.a.iloc[0], x.b.iloc[0]
        lider = a_ if res[0] == 1 else b_
        ganador = a_ if wa == 3 else b_
        rows.append((x.league.iloc[0], x.y.iloc[0], x.dt.iloc[0], lider, ganador, f"3-{min(wa, wb)}"))
s = pd.DataFrame(rows, columns=["league", "y", "day", "lider", "ganador", "marc"])
s["lider_gana"] = s.lider == s.ganador
N, W = len(s), int(s.lider_gana.sum())
fin = s[s.lider_gana].marc.value_counts()
rem = s[~s.lider_gana].sort_values("day")
print(N, W, f"{W/N:.1%}", fin.to_dict(), len(rem)); print(rem)

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
ax.text(80, 80.2, "EL 2-0 EN UN BO5", ha="center", va="center", color=ORO_CLARO, fontsize=44,
        fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
ax.text(80, 73.2, "WORLDS · MSI · EWC   ·   EDICIÓN DATOS", ha="center", va="center", color=TEAL,
        fontsize=15, fontweight="bold", zorder=6)
ax.plot([30, 130], [70, 70], color=ORO, lw=1.2, zorder=3); rombo(80, 70, 1.1)

n30 = int(fin.get("3-0", 0))
numeros = [
    (f"{W/N:.0%}", f"de las series las gana quien\nse pone 2-0 ({W} de {N})", TEAL),
    (f"{n30/W:.0%}", f"de esos 2-0 acaban en 3-0\n({n30} de {W})", TEAL),
    (f"{len(rem)}", f"remontadas desde el 0-2\nen {N} series (desde 2014)", ROJO),
]
for x0, (num, txt, col) in zip([8, 57, 106], numeros):
    panel(x0, 47.5, 46, 20, col)
    ax.text(x0 + 23, 60.7, num, ha="center", va="center", color=col, fontsize=44,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(x0 + 23, 52.1, txt, ha="center", va="center", color=ORO_CLARO, fontsize=12.5,
            linespacing=1.35, zorder=6)

# Panel izquierdo: cómo acaban los 2-0
panel(8, 9, 70, 34, ORO_OSC)
ax.text(43, 40, "CÓMO ACABAN LOS 2-0", ha="center", va="center", color=ORO, fontsize=13, fontweight="bold", zorder=6)
barras = [("3-0", int(fin.get("3-0", 0)), TEAL), ("3-1", int(fin.get("3-1", 0)), TEAL),
          ("3-2", int(fin.get("3-2", 0)), TEAL), ("Remonta el rival", len(rem), ROJO)]
mx = max(v for _, v, _ in barras)
for i, (nom, v, col) in enumerate(barras):
    y = 33.5 - i * 6.6
    ax.text(12, y, nom, ha="left", va="center", color=ORO_CLARO, fontsize=12.5, zorder=6)
    ax.add_patch(Rectangle((36, y - 1.4), max(v / mx * 28, 0.3), 2.8, fc=col, ec="none", zorder=3))
    ax.text(36 + v / mx * 28 + 1.5, y, f"{v}", ha="left", va="center", color=ORO_CLARO, fontsize=15,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)

# Panel derecho: las remontadas
panel(82, 9, 70, 34, ORO_OSC)
ax.text(117, 40, f"LAS {len(rem)} REMONTADAS DESDE 0-2", ha="center", va="center", color=ORO, fontsize=13,
        fontweight="bold", zorder=6)
torneo = {"WLDs": "Worlds", "MSI": "MSI", "EWC": "EWC"}
for i, (_, r) in enumerate(rem.iterrows()):
    y = 35.5 - i * 3.4
    col = TEAL if r.ganador in {"G2 Esports", "Team BDS", "Fnatic"} else ORO
    ax.text(87, y, f"{torneo[r.league]} {r.y}", ha="left", va="center", color=GRIS, fontsize=11.5, zorder=6)
    ax.text(147, y, f"{r.ganador} (vs {r.lider})", ha="right", va="center", color=col, fontsize=11,
            fontweight="bold", zorder=6)
ax.text(117, 11.0, "Azul = remonta un equipo europeo", ha="center", va="center", color=GRIS, fontsize=10, zorder=6)

ax.text(80, 5.4, "Datos: Oracle's Elixir (hasta 13/10/2026) · Bo5 reconstruidos por pareja y nº de partida (series con 3 victorias)",
        ha="center", va="center", color=GRIS, fontsize=9.6, zorder=6)
fig.savefig(OUT, facecolor=BG)
