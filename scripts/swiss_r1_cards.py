"""
Swiss Stage Ronda 1 (Worlds 2026): 4 tarjetas hextech, una por tweet, sin mezclar comparativas.
  1) LCK vs LPL   2) LPL vs LEC   3) LCS vs LCP   4) G2 vs DK (Caps vs ShowMaker)
Datos: Oracle's Elixir (CSV 2014-2026, hasta 13/10/2026). Sin logos ni material de Riot.

Series: el CSV no indica el formato. Se reconstruyen agrupando partidas por (torneo, pareja de equipos) y
abriendo una serie nueva cuando el nº de partida (game) NO aumenta. Bo1 = 1 partida; Bo3/Bo5 = 2 o más.
Regiones: liga doméstica de cada equipo ese año. Torneos: First Stand, MSI y Worlds desde 2025 (sin EWC).
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

INTL = ["FST", "MSI", "WLDs"]
NOMBRES = {"Gen.G": "GEN", "Invictus Gaming": "IG", "Hanwha Life Esports": "HLE", "Top Esports": "TES",
           "Bilibili Gaming": "BLG", "Anyone's Legend": "AL", "T1": "T1", "KT Rolster": "KT", "BNK FEARX": "BNK",
           "JD Gaming": "JDG", "Karmine Corp": "KC", "G2 Esports": "G2", "Movistar KOI": "KOI", "Fnatic": "FNC",
           "Team Liquid": "TL", "CTBC Flying Oyster": "CFO", "FlyQuest": "FLY", "Team Secret Whales": "TSW",
           "LYON": "LYON", "Deep Cross Gaming": "DCG", "Dplus Kia": "DK"}
def nm(x): return NOMBRES.get(x, x)

# ---------------- Datos de series (2025-2026) ----------------
cols = ["gameid", "league", "date", "position", "teamname", "result", "game"]
t = pd.concat([pd.read_csv(f, usecols=cols, low_memory=False)
               for f in sorted(glob.glob(f"{DATA_DIR}/202[56]_LoL_esports_match_data_from_OraclesElixir.csv"))], ignore_index=True)
t = t[(t.position == "team") & t.game.notna()].copy()
t["dt"] = pd.to_datetime(t["date"]); t = t[t.dt >= "2025-01-01"]; t["y"] = t.dt.dt.year
reg = {"LCK": "LCK", "LPL": "LPL", "LEC": "LEC", "LCS": "LCS", "LTA N": "LCS", "LCP": "LCP"}
dm = t[t.league.isin(reg)].copy(); dm["reg"] = dm.league.map(reg)
dm = dm.groupby(["y", "teamname"]).reg.agg(lambda s: s.mode()[0]).reset_index()
m = t[["gameid", "league", "y", "dt", "teamname", "result", "game"]]
g = m.merge(m[["gameid", "teamname", "result"]], on="gameid", suffixes=("", "_o"))
g = g[g.teamname != g.teamname_o].copy()
g["a"] = g[["teamname", "teamname_o"]].min(axis=1); g["b"] = g[["teamname", "teamname_o"]].max(axis=1)
g = g[g.teamname == g.a].rename(columns={"result": "ra"}).sort_values(["league", "a", "b", "dt", "game"])
key = g.league + "|" + g.a + "|" + g.b
g["sid"] = ((key != key.shift()) | (g.game <= g.game.shift()) | ((g.dt - g.dt.shift()).dt.days > 3)).cumsum()
S = g.groupby("sid").agg(league=("league", "first"), y=("y", "first"), start=("dt", "min"), a=("a", "first"),
                         b=("b", "first"), n=("ra", "size"), wa=("ra", "sum")).reset_index(drop=True)
S["wb"] = S.n - S.wa
S["ganador"] = np.where(S.wa > S.wb, S.a, np.where(S.wb > S.wa, S.b, None))
S = S.merge(dm.rename(columns={"teamname": "a", "reg": "ra"}), on=["y", "a"], how="left") \
     .merge(dm.rename(columns={"teamname": "b", "reg": "rb"}), on=["y", "b"], how="left")
S["fmt"] = np.where(S.n == 1, "Bo1", "Bo3/Bo5")
S = S[S.league.isin(INTL) & S.ganador.notna()].copy()
S["reg_gan"] = np.where(S.ganador == S.a, S.ra, S.rb)
TORN = {"FST": "First Stand", "MSI": "MSI", "WLDs": "Worlds"}

def cruce(r1, r2):
    x = S[((S.ra == r1) & (S.rb == r2)) | ((S.ra == r2) & (S.rb == r1))].sort_values("start").copy()
    x["perdedor"] = np.where(x.ganador == x.a, x.b, x.a)
    return x
def pareja(x, e1, e2):
    return x[((x.a == e1) & (x.b == e2)) | ((x.a == e2) & (x.b == e1))]
def resumen(x, r1, r2):
    w1, w2 = int((x.reg_gan == r1).sum()), int((x.reg_gan == r2).sum())
    l = x[x.fmt == "Bo3/Bo5"]; b = x[x.fmt == "Bo1"]
    return dict(tot=(w1, w2), largas=(int((l.reg_gan == r1).sum()), int((l.reg_gan == r2).sum())),
                bo1=(int((b.reg_gan == r1).sum()), int((b.reg_gan == r2).sum())))
def por_torneo(x, r1, r2):
    x = x.assign(clave=x.league + x.y.astype(str))
    filas = []
    for (lg, y), h in x.groupby(["league", "y"]):
        filas.append((h.start.min(), f"{TORN[lg]} {y}", int((h.reg_gan == r1).sum()), int((h.reg_gan == r2).sum())))
    return [(l, a, b) for _, l, a, b in sorted(filas)]

# ---------------- Estilo y helpers ----------------
BG, BG2 = "#010A13", "#0A1428"
ORO, ORO_OSC, ORO_CLARO = "#C8AA6E", "#785A28", "#F0E6D2"
TEAL, ROJO, GRIS = "#0AC8B9", "#E84057", "#A09B8C"

def nueva():
    fig = plt.figure(figsize=(16, 9), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 90); ax.axis("off")
    fig.patch.set_facecolor(BG)
    ax.imshow(np.linspace(0, 1, 256).reshape(-1, 1), extent=[0, 160, 0, 90], aspect="auto", origin="lower",
              zorder=0, cmap=LinearSegmentedColormap.from_list("bg", [BG, BG2]))
    return fig, ax
def marco(ax, x0, y0, w, h, color=ORO, lw=2):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=color, lw=lw, zorder=2))
def rombo(ax, cx, cy, r=0.9, color=ORO):
    ax.add_patch(Polygon([(cx, cy + r), (cx + r, cy), (cx, cy - r), (cx - r, cy)], fc=color, ec="none", zorder=5))
def panel(ax, x0, y0, w, h, color=ORO):
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#0B1A2E", ec="none", alpha=0.85, zorder=1))
    marco(ax, x0, y0, w, h, color, 1.6)
    for cx, cy in [(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h)]:
        rombo(ax, cx, cy, 0.8, color)

def cabecera(ax, titulo, subtitulo, cajas):
    marco(ax, 1.5, 1.5, 157, 87, ORO, 3); marco(ax, 2.6, 2.6, 154.8, 84.8, ORO_OSC, 1)
    for cx, cy in [(1.5, 1.5), (158.5, 1.5), (1.5, 88.5), (158.5, 88.5)]:
        rombo(ax, cx, cy, 1.4)
    ax.text(80, 80.2, titulo, ha="center", va="center", color=ORO_CLARO, fontsize=44,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(80, 73.2, subtitulo, ha="center", va="center", color=TEAL, fontsize=15, fontweight="bold", zorder=6)
    ax.plot([30, 130], [70, 70], color=ORO, lw=1.2, zorder=3); rombo(ax, 80, 70, 1.1)
    for x0, (num, txt, col) in zip([8, 57, 106], cajas):
        panel(ax, x0, 47.5, 46, 20, col)
        ax.text(x0 + 23, 60.7, num, ha="center", va="center", color=col, fontsize=40 if len(num) > 6 else 44,
                fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
        ax.text(x0 + 23, 52.1, txt, ha="center", va="center", color=ORO_CLARO, fontsize=12,
                linespacing=1.35, zorder=6)

def panel_mariposa(ax, x0, titulo, filas, nomL, nomR, colL, colR):
    """filas: [(etiqueta, vL, vR)] barras espejo con cantidades."""
    panel(ax, x0, 9, 70, 34, ORO_OSC)
    ax.text(x0 + 35, 40, titulo, ha="center", va="center", color=ORO, fontsize=13, fontweight="bold", zorder=6)
    ax.text(x0 + 30, 36.3, nomL, ha="right", va="center", color=colL, fontsize=11, fontweight="bold", zorder=6)
    ax.text(x0 + 62, 36.3, nomR, ha="left", va="center", color=colR, fontsize=11, fontweight="bold", zorder=6)
    eje = x0 + 46; mx = max(max(a, b) for _, a, b in filas) or 1
    paso = min(5.2, 22 / max(len(filas), 1))
    for i, (lab, a, b) in enumerate(filas):
        y = 32 - i * paso
        ax.text(x0 + 4, y, lab, ha="left", va="center", color=ORO_CLARO, fontsize=11.5, zorder=6)
        la, lb = a / mx * 12, b / mx * 12
        ax.add_patch(Rectangle((eje - la, y - 1.1), la, 2.2, fc=colL, ec="none", zorder=3))
        ax.add_patch(Rectangle((eje, y - 1.1), lb, 2.2, fc=colR, ec="none", zorder=3))
        ax.text(eje - la - 1, y, f"{a}", ha="right", va="center", color=ORO_CLARO, fontsize=13.5,
                fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
        ax.text(eje + lb + 1, y, f"{b}", ha="left", va="center", color=ORO_CLARO, fontsize=13.5,
                fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.plot([eje, eje], [9.8, 34.2], color=GRIS, lw=0.8, zorder=2)

def panel_filas(ax, x0, titulo, filas, pie=None):
    """filas: [(etiqueta, texto, color)]"""
    panel(ax, x0, 9, 70, 34, ORO_OSC)
    ax.text(x0 + 35, 40, titulo, ha="center", va="center", color=ORO, fontsize=13, fontweight="bold", zorder=6)
    paso = min(5.4, 24 / max(len(filas), 1))
    for i, (lab, txt, col) in enumerate(filas):
        y = 34.5 - i * paso
        ax.text(x0 + 4.5, y, lab, ha="left", va="center", color=GRIS, fontsize=11, zorder=6)
        ax.text(x0 + 65.5, y, txt, ha="right", va="center", color=col, fontsize=11, fontweight="bold", zorder=6)
    if pie:
        ax.text(x0 + 35, 11.2, pie, ha="center", va="center", color=GRIS, fontsize=9.8, zorder=6)

def pie(ax, texto):
    ax.text(80, 5.4, texto, ha="center", va="center", color=GRIS, fontsize=9.6, zorder=6)

def guardar(fig, nombre):
    fig.savefig(f"{OUT_DIR}/{nombre}", facecolor=BG); plt.close(fig)

PIE_REG = ("Datos: Oracle's Elixir (hasta 13/10/2026) · First Stand, MSI y Worlds desde 2025 · "
           "Series reconstruidas por pareja y nº de partida")

def txt_serie(r):
    ganador, perdedor = nm(r.ganador), nm(r.perdedor)
    gw = max(r.wa, r.wb); lw = min(r.wa, r.wb)
    return f"{ganador} {int(gw)}-{int(lw)} {perdedor}"

# ================= 1) LCK vs LPL =================
x = cruce("LCK", "LPL"); R = resumen(x, "LCK", "LPL")
print("LCK-LPL", R)
fig, ax = nueva()
cabecera(ax, "LCK  vs  LPL", "SWISS · RONDA 1 · GEN–IG Y HLE–TES",
         [(f"{R['tot'][0]} - {R['tot'][1]}", "LCK vs LPL: series\ninternacionales desde 2025", TEAL),
          (f"{R['largas'][0]} - {R['largas'][1]}", "En Bo3/Bo5, la LCK\nlleva claras las series", TEAL),
          (f"{R['bo1'][1]} - {R['bo1'][0]}", "Pero en Bo1 (como la ronda 1)\nlleva ventaja la LPL", ORO)])
panel_mariposa(ax, 8, "POR TORNEO (SERIES GANADAS)", [(l, a, b) for l, a, b in por_torneo(x, "LCK", "LPL")],
               "LCK", "LPL", TEAL, ORO)
hle_tes = pareja(x, "Hanwha Life Esports", "Top Esports"); gen_ig = pareja(x, "Gen.G", "Invictus Gaming")
bo1 = x[x.fmt == "Bo1"]
filas = [("Ronda 1", "GEN–IG: sin cruces previos" if len(gen_ig) == 0 else "GEN–IG: ver datos", GRIS),
         ("Ronda 1", f"HLE–TES: HLE {int((hle_tes.ganador=='Hanwha Life Esports').sum())}-"
                     f"{int((hle_tes.ganador=='Top Esports').sum())} (First Stand 2025)", TEAL)]
for _, r in bo1.iterrows():
    filas.append((f"Bo1 · {TORN[r.league]} {r.y}", f"{nm(r.ganador)} gana a {nm(r.perdedor)}", ORO))
panel_filas(ax, 82, "LO QUE HAY QUE SABER", filas)
pie(ax, PIE_REG); guardar(fig, "swiss_r1_lck_vs_lpl.png")
print(hle_tes[["start", "a", "b", "wa", "wb"]].to_string(), "\nGEN-IG:", len(gen_ig))

# ================= 2) LPL vs LEC =================
x = cruce("LPL", "LEC"); R = resumen(x, "LPL", "LEC")
print("LPL-LEC", R)
blg = x[(x.a == "Bilibili Gaming") | (x.b == "Bilibili Gaming")]
blg_l = blg[blg.fmt == "Bo3/Bo5"]
bw, bl = int((blg_l.ganador == "Bilibili Gaming").sum()), int((blg_l.ganador != "Bilibili Gaming").sum())
fig, ax = nueva()
cabecera(ax, "LPL  vs  LEC", "SWISS · RONDA 1 · BLG–KOI Y AL–KC",
         [(f"{R['tot'][0]} - {R['tot'][1]}", "LPL vs LEC: series\ninternacionales desde 2025", ORO),
          (f"{R['largas'][0]} - {R['largas'][1]}", "En Bo3/Bo5, la LPL\nlleva claras las series", ORO),
          (f"{bw} - {bl}", "BLG vs LEC en series largas\n(solo cayó en un Bo1)", ORO)])
panel_mariposa(ax, 8, "POR TORNEO (SERIES GANADAS)", [(l, a, b) for l, a, b in por_torneo(x, "LPL", "LEC")],
               "LPL", "LEC", ORO, TEAL)
blg_koi = pareja(x, "Bilibili Gaming", "Movistar KOI")
filas = [("Ronda 1", "BLG–KOI: " + txt_serie(blg_koi.iloc[0]) + " (MSI 2025)" if len(blg_koi) else "BLG–KOI: sin cruces", ORO),
         ("Ronda 1", "AL–KC: sin cruces previos", GRIS)]
for _, r in x[x.reg_gan == "LEC"].iterrows():
    filas.append((f"{r.fmt} · {TORN[r.league]} {r.y}", txt_serie(r), TEAL))
panel_filas(ax, 82, "LO QUE HAY QUE SABER (GANA EUROPA EN AZUL)", filas)
pie(ax, PIE_REG); guardar(fig, "swiss_r1_lpl_vs_lec.png")
print("AL-KC:", len(pareja(x, "Anyone's Legend", "Karmine Corp")), "| BLG largas", bw, bl)

# ================= 3) LCS vs LCP =================
x = cruce("LCS", "LCP"); R = resumen(x, "LCS", "LCP")
print("LCS-LCP", R)
cfo = x[(x.a == "CTBC Flying Oyster") | (x.b == "CTBC Flying Oyster")]
cw, cl = int((cfo.ganador == "CTBC Flying Oyster").sum()), int((cfo.ganador != "CTBC Flying Oyster").sum())
fig, ax = nueva()
cabecera(ax, "LCS  vs  LCP", "SWISS · RONDA 1 · TL–CFO Y LYON–TSW",
         [(f"{R['tot'][0]} - {R['tot'][1]}", "LCS vs LCP: series\ninternacionales desde 2025", TEAL),
          (f"{R['largas'][0]} - {R['largas'][1]}", "En Bo3/Bo5, el cruce\nestá igualado", GRIS if False else ORO),
          (f"{cw} - {cl}", "CFO vs equipos de NA:\nbarrió a TL y a FlyQuest (2-0)", ORO)])
panel_mariposa(ax, 8, "POR TORNEO (SERIES GANADAS)", [(l, a, b) for l, a, b in por_torneo(x, "LCS", "LCP")],
               "LCS", "LCP", TEAL, ORO)
filas = []
for etiqueta, e1, e2 in [("Ronda 1", "Team Liquid", "CTBC Flying Oyster"), ("Ronda 1", "LYON", "Team Secret Whales")]:
    p = pareja(x, e1, e2)
    for _, r in p.iterrows():
        filas.append((f"{etiqueta} · {nm(e1)}–{nm(e2)}", f"{txt_serie(r)} ({TORN[r.league]} {r.y})",
                      TEAL if r.reg_gan == "LCS" else ORO))
for _, r in x.iterrows():
    if not ({r.a, r.b} & set()) and not (set([r.a, r.b]) in [{"Team Liquid", "CTBC Flying Oyster"}, {"LYON", "Team Secret Whales"}]):
        filas.append((f"{r.fmt} · {TORN[r.league]} {r.y}", txt_serie(r), TEAL if r.reg_gan == "LCS" else ORO))
panel_filas(ax, 82, "LO QUE HAY QUE SABER (LCS EN AZUL, LCP EN DORADO)", filas)
pie(ax, PIE_REG); guardar(fig, "swiss_r1_lcs_vs_lcp.png")

# ================= 4) G2 vs DK · Caps vs ShowMaker =================
cols2 = ["gameid", "league", "date", "position", "teamname", "playername", "result", "game", "playoffs",
         "kills", "deaths", "assists", "dpm", "golddiffat15", "damageshare"]
df = pd.concat([pd.read_csv(f, usecols=lambda c: c in cols2, low_memory=False)
                for f in sorted(glob.glob(f"{DATA_DIR}/20*_LoL_esports_match_data_from_OraclesElixir.csv"))], ignore_index=True)
dk = ["DAMWON Gaming", "DWG KIA", "Dplus Kia", "Dplus KIA"]
ids = set(df[df.teamname == "G2 Esports"].gameid) & set(df[df.teamname.isin(dk)].gameid)
h = df[df.gameid.isin(ids)].copy(); h["dt"] = pd.to_datetime(h.date)
tm = h[h.position == "team"].sort_values(["dt", "game"])
tm = tm[tm.teamname == "G2 Esports"][["gameid", "league", "dt", "game", "result"]].rename(columns={"result": "g2"})
tm["y"] = tm.dt.dt.year
tm["sid"] = ((tm.league + tm.y.astype(str) != (tm.league + tm.y.astype(str)).shift()) | (tm.game <= tm.game.shift())
             | ((tm.dt - tm.dt.shift()).dt.days > 3)).cumsum()
ser = tm.groupby("sid").agg(league=("league", "first"), start=("dt", "min"), y=("y", "first"), n=("g2", "size"), g2=("g2", "sum")).reset_index()
ser["dk"] = ser.n - ser.g2
print(ser.to_string())
gdk = int((ser.dk > ser.g2).sum()); gg2 = int((ser.g2 > ser.dk).sum())
mid = h[h.position == "mid"]
def estad(p):
    m_ = mid[mid.playername == p]
    return dict(n=len(m_), kda=(m_.kills.sum() + m_.assists.sum()) / m_.deaths.sum(), dpm=m_.dpm.mean(),
                dano=m_.damageshare.mean() * 100, gd15=int((m_.golddiffat15 > 0).sum()), vic=int(m_.result.sum()))
C, SM = estad("Caps"), estad("ShowMaker")
print(C, SM)
fmt_n = {1: "Bo1"}
etapas = {2019: "Cuartos", 2020: "Semifinales", 2022: "Grupos", 2023: "Swiss R1", 2026: "Playoffs"}
fig, ax = nueva()
cabecera(ax, "G2  vs  DK", "SWISS · RONDA 1 · EL DUELO CAPS vs SHOWMAKER",
         [(f"{gdk} - {gg2}", "DK vs G2: cruces desde 2019\n(Bo1, Bo3 y Bo5)", ORO),
          (f"{SM['kda']:.1f} - {C['kda']:.1f}".replace(".", ","), "KDA de ShowMaker vs Caps\nen esos 13 juegos", ORO),
          (f"{SM['gd15']} de {SM['n']}", "juegos con ventaja de oro a\nlos 15' para ShowMaker", ORO)])
filas = []
for _, r in ser.iterrows():
    torneo = "EWC" if r.league == "EWC" else "Worlds"
    formato = "Bo1" if r.n == 1 else ("Bo5" if max(r.g2, r.dk) == 3 else "Bo3")
    gan = "G2" if r.g2 > r.dk else "DK"; marc = f"{int(max(r.g2, r.dk))}-{int(min(r.g2, r.dk))}"
    filas.append((f"{torneo} {r.y} · {etapas.get(r.y, '')} ({formato})", f"{gan} {marc}", TEAL if gan == "G2" else ORO))
panel_filas(ax, 8, "CRUCES G2 vs DK (G2 EN AZUL, DK EN DORADO)", filas)
# panel derecho: duelo del mid
panel(ax, 82, 9, 70, 34, ORO_OSC)
ax.text(117, 40, f"CAPS vs SHOWMAKER ({C['n']} JUEGOS)", ha="center", va="center", color=ORO, fontsize=13, fontweight="bold", zorder=6)
ax.text(87, 36.3, "Caps (G2)", ha="left", va="center", color=TEAL, fontsize=11, fontweight="bold", zorder=6)
ax.text(147, 36.3, "ShowMaker (DK)", ha="right", va="center", color=ORO, fontsize=11, fontweight="bold", zorder=6)
duelo = [("KDA", C["kda"], SM["kda"], lambda v: f"{v:.1f}".replace(".", ",")),
         ("DPM medio", C["dpm"], SM["dpm"], lambda v: f"{v:.0f}"),
         ("% del daño de su equipo", C["dano"], SM["dano"], lambda v: f"{v:.1f}%".replace(".", ",")),
         ("Juegos con ventaja a los 15'", C["gd15"], SM["gd15"], lambda v: f"{v:.0f}"),
         ("Victorias", C["vic"], SM["vic"], lambda v: f"{v:.0f}")]
for i, (lab, a, b, f) in enumerate(duelo):
    y = 32 - i * 4.7
    mxv = max(a, b); la, lb = a / mxv * 15, b / mxv * 15
    ax.text(117, y + 2.0, lab, ha="center", va="center", color=GRIS, fontsize=9.8, zorder=6)
    ax.add_patch(Rectangle((117 - 2 - la, y - 1.0), la, 1.9, fc=TEAL, ec="none", alpha=1 if a >= b else 0.45, zorder=3))
    ax.add_patch(Rectangle((117 + 2, y - 1.0), lb, 1.9, fc=ORO, ec="none", alpha=1 if b >= a else 0.45, zorder=3))
    ax.text(117 - 2 - la - 1, y, f(a), ha="right", va="center", color=TEAL if a >= b else GRIS, fontsize=13,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
    ax.text(117 + 2 + lb + 1, y, f(b), ha="left", va="center", color=ORO if b >= a else GRIS, fontsize=13,
            fontfamily="DejaVu Serif", fontweight="bold", zorder=6)
pie(ax, "Datos: Oracle's Elixir (hasta 13/10/2026) · Worlds 2019, 2020, 2022 y 2023 y EWC 2026 · "
        "DAMWON/DWG KIA = Dplus KIA · Bo1 incluidos")
guardar(fig, "swiss_r1_g2_vs_dk.png")
