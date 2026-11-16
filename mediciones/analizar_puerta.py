"""Embudo de la puerta de madera a partir de los agentes_*.csv y geometria_*.csv de medir_puerta.py.

Espera, en la misma carpeta, las corridas de las tres condiciones: B con y sin evolución, y C (con
`acercarse`) con evolución. Uso: python mediciones/analizar_puerta.py SALIDA
"""
import csv
import glob
import itertools
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
dir_med = sys.argv[1]
filas = []
for ruta in sorted(glob.glob(os.path.join(dir_med, "agentes_s*.csv"))):
    with open(ruta, encoding="utf-8") as f:
        filas.extend(csv.DictReader(f))
for f in filas:
    for k in ("semilla", "evolucion", "generacion", "lugar", "en_pool", "elite", "golpes", "abrio",
              "ticks_etapa1", "ticks_25", "ticks_golpe", "ticks_golpe_25", "bloq_agente_inicio",
              "bloq_agente_corte", "bloq_puerta", "ticks_25_post90", "golpe_25_post90", "vivo", "edad",
              "acercarse"):
        f[k] = int(f[k])
    for k in ("dmin", "d0", "dmin_llave", "d0_llave"):
        f[k] = float(f[k]) if f.get(k, "") not in ("", "inf") else float("inf")
    f["fitness"] = float(f["fitness"])
    f["aporte"] = float(f["aporte"]) if f["aporte"] != "" else None
    f["camino"] = (f["d0"] - f["dmin"]) / f["d0"] if f["d0"] not in (0, float("inf")) else 0.0
    f["camino_llave"] = ((f["d0_llave"] - f["dmin_llave"]) / f["d0_llave"]
                         if f["d0_llave"] not in (0, float("inf")) else None)

CONDS = [(0, 1, "B con evolución"), (0, 0, "B sin evolución"), (1, 1, "C con evolución (acercarse)")]


def pct(a, b):
    return f"{a} ({100 * a / b:.1f}%)" if b else f"{a} (—)"


def embudo(grupo, titulo):
    n = len(grupo)
    c100 = [f for f in grupo if f["dmin"] < 100]
    c50 = [f for f in grupo if f["dmin"] < 50]
    c25 = [f for f in grupo if f["dmin"] < 25]
    g25 = [f for f in c25 if f["ticks_golpe_25"] > 0]
    uno = [f for f in grupo if f["golpes"] >= 1]
    abr = [f for f in grupo if f["abrio"]]
    tg = sum(f["ticks_golpe"] for f in grupo)
    te = sum(f["ticks_etapa1"] for f in grupo)
    print(f"\n### {titulo}  (agentes × generación = {n})")
    print(f"  d0 mediana {st.median(f['d0'] for f in grupo):.0f} px; dmín mediana {st.median(f['dmin'] for f in grupo):.0f} px;"
          f" camino hecho prom {st.mean(f['camino'] for f in grupo):.3f}; > 0,8: {pct(sum(1 for f in grupo if f['camino'] > 0.8), n)}")
    print(f"  < 100 px: {pct(len(c100), n)}   < 50: {pct(len(c50), n)}   < 25: {pct(len(c25), n)}")
    print(f"  de los < 25, golpearon ahí: {pct(len(g25), len(c25))};  ≥ 1 golpe que contó: {len(uno)};  abrieron: {len(abr)}")
    print(f"  ticks golpeando / ticks con la llave: {100 * tg / te:.1f}%")
    if c25:
        print(f"  de los < 25: d0 {sorted(round(f['d0']) for f in c25)}")
        print(f"     ticks a < 25 mediana {st.median(f['ticks_25'] for f in c25):.0f}; golpeando ahí, mediana "
              f"{st.median(f['ticks_golpe_25'] for f in c25):.0f}; frenados: inicio {sum(f['bloq_agente_inicio'] for f in c25)}, "
              f"corte {sum(f['bloq_agente_corte'] for f in c25)}, cooldown puerta {sum(f['bloq_puerta'] for f in c25)}")
    un_golpe = [f for f in grupo if f["golpes"] == 1]
    if un_golpe:
        print(f"  con 1 golpe y sin abrir: {len(un_golpe)}; a < 25 cuando podían dar el 2.º: "
              f"{sum(1 for f in un_golpe if f['ticks_25_post90'] > 0)}; golpeando: {sum(1 for f in un_golpe if f['golpe_25_post90'] > 0)}")
    if abr:
        print(f"  abrieron: d0 {sorted(round(f['d0']) for f in abr)}; lugar {sorted(f['lugar'] for f in abr)}; en pool {sum(f['en_pool'] for f in abr)} de {len(abr)}")
        if all(f["aporte"] is not None for f in abr):
            print(f"     aporte {[f['aporte'] for f in abr]}")
    return dict(n=n, c100=len(c100), c50=len(c50), c25=len(c25), g25=len(g25), uno=len(uno), abr=len(abr))


for ac, ev, nombre in CONDS:
    for desde, hasta in ((1, 15), (1, 5), (11, 15)):
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and desde <= f["generacion"] <= hasta]
        if g:
            embudo(g, f"{nombre}, generaciones {desde} a {hasta}")

print("\n### Llegar a < 25 según la distancia al nacer (gens 1 a 15)")
for ac, ev, nombre in CONDS:
    g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev]
    linea = []
    for a, b in ((0, 100), (100, 200), (200, 400), (400, 2000)):
        s = [f for f in g if a <= f["d0"] < b]
        linea.append(f"{a}-{b}: {sum(1 for f in s if f['dmin'] < 25)}/{len(s)} (abrieron {sum(f['abrio'] for f in s)})")
    print(f"  {nombre}: " + "; ".join(linea))

print("\n### Camino hecho promedio por generación (B evo / B sin / C evo)")
for gen in range(1, 16):
    vals = []
    for ac, ev, _ in CONDS:
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and f["generacion"] == gen]
        vals.append(st.mean(f["camino"] for f in g) if g else float("nan"))
    print(f"  g{gen:2d}: " + "  ".join(f"{v:.3f}" for v in vals))

print("\n### Por semilla, gens 11 a 15: camino hecho prom (B evo / B sin / C evo)")
for s in sorted({f["semilla"] for f in filas}):
    vals = []
    for ac, ev, _ in CONDS:
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and f["semilla"] == s and f["generacion"] >= 11]
        vals.append(st.mean(f["camino"] for f in g) if g else float("nan"))
    print(f"  s{s}: " + "  ".join(f"{v:.3f}" for v in vals))

print("\n### Puerta contra punto de control (la llave roja, a la que la brújula no apunta), camino hecho prom")
for desde, hasta in ((1, 1), (1, 5), (11, 15)):
    partes = []
    for ac, ev, nombre in CONDS:
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and desde <= f["generacion"] <= hasta
             and f["camino_llave"] is not None]
        partes.append(f"{nombre}: puerta {st.mean(f['camino'] for f in g):.3f}, control {st.mean(f['camino_llave'] for f in g):.3f}")
    print(f"  gens {desde}-{hasta}: " + " | ".join(partes))
print("  por semilla, gens 11-15 (puerta / control): B evo | B sin | C evo")
for s in sorted({f["semilla"] for f in filas}):
    partes = []
    for ac, ev, _ in CONDS:
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and f["semilla"] == s
             and f["generacion"] >= 11 and f["camino_llave"] is not None]
        partes.append(f"{st.mean(f['camino'] for f in g):.3f} / {st.mean(f['camino_llave'] for f in g):.3f}")
    print(f"  s{s}: " + " | ".join(partes))

print("\n### Golpear por generación (% de ticks con la llave): B evo / B sin / C evo")
for gen in range(1, 16):
    vals = []
    for ac, ev, _ in CONDS:
        g = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == ev and f["generacion"] == gen]
        vals.append(100 * sum(f["ticks_golpe"] for f in g) / max(1, sum(f["ticks_etapa1"] for f in g)))
    print(f"  g{gen:2d}: " + "  ".join(f"{v:5.1f}" for v in vals))

print("\n### Aporte a la generación siguiente (con evolución, gens 1 a 14)")
for ac, ev, nombre in CONDS:
    if not ev:
        continue
    evo = [f for f in filas if f["acercarse"] == ac and f["evolucion"] == 1 and f["aporte"] is not None]
    print(f"  {nombre}:")
    for etiqueta, cond in (("todos", lambda f: True), ("< 50 px", lambda f: f["dmin"] < 50),
                           ("< 25 px", lambda f: f["dmin"] < 25), ("abrieron", lambda f: f["abrio"] == 1),
                           ("camino > 0,8", lambda f: f["camino"] > 0.8)):
        g = [f for f in evo if cond(f)]
        if g:
            print(f"    {etiqueta}: n={len(g)}, aporte prom {st.mean(f['aporte'] for f in g):.2f}, "
                  f"en pool {100 * st.mean(f['en_pool'] for f in g):.0f}%, lugar mediano {st.median(f['lugar'] for f in g):.0f}")
    rs = []
    for _, g in itertools.groupby(sorted(evo, key=lambda f: (f["semilla"], f["generacion"])),
                                  key=lambda f: (f["semilla"], f["generacion"])):
        g = list(g)
        xs = [f["ticks_golpe"] / max(1, f["ticks_etapa1"]) for f in g]
        ys = [f["fitness"] for f in g]
        if st.pstdev(xs) > 0 and st.pstdev(ys) > 0:
            rs.append(st.correlation(xs, ys))
    print(f"    correlación (fracción golpeando, fitness) dentro de la generación: mediana {st.median(rs):.2f}")
    rs = []
    for _, g in itertools.groupby(sorted(evo, key=lambda f: (f["semilla"], f["generacion"])),
                                  key=lambda f: (f["semilla"], f["generacion"])):
        g = list(g)
        xs = [f["camino"] for f in g]
        ys = [f["fitness"] for f in g]
        if st.pstdev(xs) > 0 and st.pstdev(ys) > 0:
            rs.append(st.correlation(xs, ys))
    print(f"    correlación (camino hecho, fitness) dentro de la generación: mediana {st.median(rs):.2f}")
    sumas = {}
    for f in evo:
        sumas[(f["semilla"], f["generacion"])] = sumas.get((f["semilla"], f["generacion"]), 0.0) + f["aporte"]
    print(f"    control del aporte: sumas por generación {sorted(set(round(v, 1) for v in sumas.values()))}")

print("\n### Geometría y seguidor de brújula perfecto (todas las generaciones de todas las corridas)")
geo = []
for ruta in sorted(glob.glob(os.path.join(dir_med, "geometria_s*.csv"))):
    with open(ruta, encoding="utf-8") as f:
        geo.extend(csv.DictReader(f))
arr = sum(int(g["arranques"]) for g in geo)
for k in ("seguidor_25", "seguidor_50", "seguidor_100", "desliza_25", "desliza_50", "desliza_100"):
    print(f"  {k}: {100 * sum(int(g[k]) for g in geo) / arr:.1f}%  "
          f"(por generación, de {min(100 * int(g[k]) / int(g['arranques']) for g in geo):.0f}% a "
          f"{max(100 * int(g[k]) / int(g['arranques']) for g in geo):.0f}%)")
print(f"  mediana de las medianas: sin deslizar {st.median(float(g['seguidor_mediana']) for g in geo):.0f} px, "
      f"deslizando {st.median(float(g['desliza_mediana']) for g in geo):.0f} px; generaciones: {len(geo)}")
print(f"  dmín libre: {sorted(set(g['dmin_libre'] for g in geo))}; área libre a < 25: "
      f"mediana {st.median(float(g['area_libre_25']) for g in geo):.0f} px², mín {min(float(g['area_libre_25']) for g in geo):.0f}")
