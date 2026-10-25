# Metodología y notas de calidad

## Fuente
Oracle's Elixir, CSV de partidas 2014-2026. En esta versión los datos llegan hasta el **13/10/2026**
(no incluyen el Play-In ni el Swiss de Worlds 2026).

## Series (Bo1, Bo3, Bo5)
El CSV **no indica el formato de la serie**. Se reconstruye así:
1. Se junta cada partida con su rival (pareja de equipos en orden alfabético) y se ordena por fecha y por `game`
   (nº de partida dentro de la serie).
2. Se abre una **serie nueva** cuando el nº de partida **no aumenta** (se reinicia), cambia la pareja o el torneo,
   o pasan más de 3 días.
3. Bo1 = serie de 1 partida; Bo3/Bo5 = 2 o más. Para el análisis del 2-0 se exige además que alguien llegue a
   3 victorias (así solo entran Bo5 completos).

Agrupar por **día** en lugar de por nº de partida es un error: una serie que cruza la medianoche se parte en dos.

## Regiones
Cada equipo se asigna a la liga doméstica en la que más jugó **ese año** (LCK, LPL, LEC, LCS/LTA N, LCP, PCS/VCS,
CBLOL/LTA S...). La LCS de 2025 aparece como `LTA N` en el CSV.

## Torneos
- Cruces regionales del Swiss: First Stand, MSI y Worlds desde 2025 (sin EWC).
- Europa vs NA/APAC y APAC vs Brasil: Worlds, MSI y EWC (por partidas, no por series).
- "Partidas" y "series" no son lo mismo: las cifras por partidas se indican siempre como tales.

## Datos añadidos a mano (no están en el CSV)
- `apac_vs_brasil.py`: la barra **2026\*** incluye MVK 3-0 FURIA (Play-In de Worlds 2026), dato aportado a mano.

## Historial de correcciones
- **2-0 en un Bo5 internacional**: una primera versión daba 93% (125 de 134) y 9 remontadas por un error al
  agrupar series (por día y con series incompletas). Con la segmentación correcta: **95% (129 de 136)** y
  **7 remontadas** desde 0-2.
- **LPL vs LEC / LCS vs LCP desde 2025**: los borradores iniciales (de Wikipedia/Leaguepedia) daban 6-2 y 2-2;
  con el CSV salen **7-3** y **3-2**.
- **G2 vs DK**: no es "1-1 en series"; contando todos los cruces desde 2019 (incluidos Bo1) van **DK 4 - G2 2**.

## Limitaciones
- Muestras pequeñas: son tendencias, no certezas.
- La comparación entre ligas distintas (p. ej. KC vs C9) no está ajustada por nivel de liga.
- Las etiquetas de etapa (cuartos, semifinales, grupos...) de `swiss_r1_cards.py` son manuales.
