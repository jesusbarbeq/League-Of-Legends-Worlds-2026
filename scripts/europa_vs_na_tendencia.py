"""
Europa vs Norteamérica en torneos internacionales (Worlds, MSI y EWC).
Datos: Oracle's Elixir (CSV por año). Genera un PNG listo para Twitter/X.

Uso: python europa_vs_na_tendencia.py  (ajusta DATA_DIR si hace falta)
"""
import os
DATA_DIR = os.environ.get("DATA_DIR", "data")      # carpeta con los CSV de Oracle's Elixir
OUT_DIR = os.environ.get("OUT_DIR", "output")      # carpeta donde se guardan las imágenes
os.makedirs(OUT_DIR, exist_ok=True)

import glob
import pandas as pd
import matplotlib.pyplot as plt

OUT_PNG = os.path.join(OUT_DIR, "europa_vs_na_tendencia.png")

# 1) Cargar solo las columnas necesarias y quedarnos con filas de equipo
cols = ["gameid", "league", "date", "position", "teamname", "result"]
frames = [pd.read_csv(f, usecols=cols, low_memory=False)
          for f in sorted(glob.glob(f"{DATA_DIR}/20*_LoL_esports_match_data_from_OraclesElixir.csv"))]
t = pd.concat(frames, ignore_index=True)
t = t[t.position == "team"].copy()
# Año real a partir de la fecha (la columna 'year' tiene filas con año siguiente)
t["y"] = pd.to_datetime(t["date"]).dt.year

# 2) Región de cada equipo cada año, según su liga doméstica
regiones = {"LEC": "EU", "EU LCS": "EU", "LCS": "NA", "NA LCS": "NA", "LTA N": "NA"}
dom = t[t.league.isin(regiones)].copy()
dom["reg"] = dom.league.map(regiones)
dom = dom.groupby(["y", "teamname"]).reg.agg(lambda s: s.mode()[0]).reset_index()

# 3) Emparejar cada partida internacional con el rival
m = t[["gameid", "league", "y", "teamname", "result"]]
mm = m.merge(m, on="gameid", suffixes=("", "_o"))
mm = mm[mm.teamname != mm.teamname_o]
intl = mm[mm.league.isin(["WLDs", "MSI", "EWC"])]
intl = intl.merge(dom, on=["y", "teamname"], how="left")
intl = intl.merge(dom.rename(columns={"teamname": "teamname_o", "reg": "reg_o"}),
                  on=["y", "teamname_o"], how="left")

# 4) Solo partidas Europa (equipo) vs NA (rival): 'result' = victoria europea
x = intl[(intl.reg == "EU") & (intl.reg_o == "NA")]
anual = x.groupby("y").result.agg(partidas="size", victorias="sum")
anual["wr"] = anual.victorias / anual.partidas
reciente = anual.loc[2024:]
wr_rec = reciente.victorias.sum() / reciente.partidas.sum()

# 5) Gráfico
BG, TXT, SUB = "#0f1419", "#e7e9ea", "#8b98a5"
AZUL, ROJO = "#4d9de0", "#e15554"
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

colores = [AZUL if v >= 0.5 else ROJO for v in anual.wr]
barras = ax.bar(anual.index.astype(str), anual.wr * 100, color=colores, width=0.68)
ax.axhline(50, color=SUB, lw=1.4, ls="--")
ax.text(len(anual) - 0.4, 51.5, "50%", color=SUB, fontsize=13, ha="right")

for b, (_, r) in zip(barras, anual.iterrows()):
    x_c = b.get_x() + b.get_width() / 2
    if r.victorias == 0:
        # Una barra de 0% no tiene altura: lo explicamos con texto en rojo
        ax.text(x_c, 9, "0%", ha="center", color=ROJO, fontsize=22, fontweight="bold")
        ax.text(x_c, 2.5, f"0/{int(r.partidas)}", ha="center", color=TXT, fontsize=14)
    else:
        ax.text(x_c, r.wr * 100 + 2, f"{int(r.victorias)}/{int(r.partidas)}",
                ha="center", color=TXT, fontsize=14)

# Resaltar 2024-2026
i0 = list(anual.index).index(2024)
ax.axvspan(i0 - 0.5, len(anual) - 0.5, color=ROJO, alpha=0.10)
ax.text((i0 + len(anual) - 1) / 2, 108,
        f"2024-26: {int(reciente.victorias.sum())} de {int(reciente.partidas.sum())} ({wr_rec:.0%})",
        ha="center", color=ROJO, fontsize=20, fontweight="bold")

ax.set_ylim(0, 118)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels([f"{v}%" for v in [0, 25, 50, 75, 100]], color=SUB, fontsize=13)
ax.tick_params(axis="x", colors=TXT, labelsize=14, length=0)
ax.tick_params(axis="y", length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.grid(axis="y", color="#2a3139", lw=0.8); ax.set_axisbelow(True)

fig.text(0.06, 0.93, "Europa vs NA en torneos internacionales", color=TXT,
         fontsize=30, fontweight="bold", ha="left")
fig.text(0.06, 0.885, "% de partidas ganadas por equipos europeos contra norteamericanos (Worlds, MSI y EWC)",
         color=SUB, fontsize=16, ha="left")
fig.text(0.06, 0.03, "Datos: Oracle's Elixir (hasta 13/10/2026) · Partidas, no series · Número = victorias EU / partidas",
         color=SUB, fontsize=12, ha="left")
plt.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.11)
fig.savefig(OUT_PNG, facecolor=BG)
print(anual.round(2))
print("2024-26:", int(reciente.victorias.sum()), "/", int(reciente.partidas.sum()), f"= {wr_rec:.1%}")
