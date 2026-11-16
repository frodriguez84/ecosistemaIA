"""Si usan la brújula y si la selección la empuja, a partir de los agentes_*.csv de medir_puerta.py.

Por condición (acercarse, deslizar, evolución) de las que estén en la carpeta:
- El criterio "usa la brújula": en las generaciones 11 a 15, (camino hacia la puerta − camino hacia el
  control) con evolución, mayor que en su línea base, por semilla.
- La sensibilidad de la red a la brújula (sensor 9) y a la comida (sensor 3, control positivo): el
  promedio por agente de cuánto cambia el giro (radianes por tick) si el sensor marca el objetivo +90°
  contra −90°. Positivo: gira hacia donde marca. Solo los CSV con sens_ticks (medir_puerta.py desde
  2026-11-16, sesión de la brújula).
- La selección: dentro de cada generación, la correlación de rangos (Spearman) entre el fitness y la
  sensibilidad a la brújula, a la comida y el uso por agente (camino a la puerta − al control); y, con
  evolución, cuánto dejan a la generación siguiente los que más usan la brújula.
- Si el CSV trae los términos del fitness y el giro (medir_puerta.py, desde la tanda del B deslizando
  de la misma sesión): qué término mueve el fitness dentro de la generación, y cuánto giran.
- El criterio del laboratorio de la brújula (docs/qa/AnalisisQA.md#laboratorio-brujula), por semilla en
  las últimas 5 generaciones: sensibilidad a la brújula con evolución >= 0,02 y mayor que la línea
  base; secundario, (uso con evolución − uso sin) >= 0,05. Y cuántos agentes cobran algo (fitness > 0).
- Si el CSV trae el origen y los padres (medir_puerta.py, desde el laboratorio): si los hijos heredan
  la sensibilidad y el camino (correlación con la del padre, o el promedio de los dos en el cruce).

Las generaciones salen de la carpeta: ventanas 1-5, 11-15 y, si la corrida pasa de 15, las últimas 5;
la selección, en las gens 1-15 y en las 16 a la última.

Uso: python mediciones/analizar_brujula.py SALIDA
"""
import csv
import glob
import os
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)


def rangos(v):
    """Rangos con los empates promediados."""
    v = np.asarray(v, dtype=float)
    r = np.empty(len(v))
    r[v.argsort(kind="mergesort")] = np.arange(len(v))
    _, inv, cuantos = np.unique(v, return_inverse=True, return_counts=True)
    return (np.bincount(inv, weights=r) / cuantos)[inv]


def spearman(x, y):
    rx, ry = rangos(x), rangos(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


dir_med = sys.argv[1]
TERMINOS = ("f_supervivencia", "f_comida", "f_exploracion", "f_anticirculo", "f_puzzle", "f_acercarse", "f_agua")
filas = []
for ruta in sorted(glob.glob(os.path.join(dir_med, "agentes_s*.csv"))):
    with open(ruta, encoding="utf-8") as f:
        filas.extend(csv.DictReader(f))
for f in filas:
    f["deslizar"] = f.get("deslizar") or 0
    f["laboratorio"] = f.get("laboratorio") or 0
    for k in ("semilla", "evolucion", "generacion", "id", "lugar", "en_pool", "abrio", "golpes", "acercarse", "deslizar",
              "laboratorio"):
        f[k] = int(f[k])
    # El currículo hasta la 30: el laboratorio (sin la columna) y su control, curriculo30
    f["c30"] = int(f["laboratorio"] == 1 or f.get("curriculo_hasta") == "30")
    f["origen"] = f.get("origen") or None
    f["padres"] = [int(f[k]) for k in ("padre1", "padre2") if f.get(k)]
    for k in ("dmin", "d0", "dmin_llave", "d0_llave"):
        f[k] = float(f[k]) if f.get(k, "") not in ("", "inf") else float("inf")
    f["fitness"] = float(f["fitness"])
    f["aporte"] = float(f["aporte"]) if f["aporte"] != "" else None
    f["camino"] = (f["d0"] - f["dmin"]) / f["d0"] if f["d0"] not in (0, float("inf")) else 0.0
    f["camino_llave"] = ((f["d0_llave"] - f["dmin_llave"]) / f["d0_llave"]
                         if f["d0_llave"] not in (0, float("inf")) else None)
    f["uso"] = f["camino"] - f["camino_llave"] if f["camino_llave"] is not None else None
    n = int(f.get("sens_ticks") or 0)
    f["sb"] = float(f["sens_brujula"]) / n if n else None
    f["sc"] = float(f["sens_comida"]) / n if n else None
    # Desde la tanda del B deslizando con los términos del fitness: el giro y los términos
    f["gira"] = int(f["ticks_gira"]) / n if n and f.get("ticks_gira") else None
    f["giro"] = float(f["giro_abs"]) / n if n and f.get("giro_abs") else None
    f["avanza"] = int(f["ticks_avanza"]) / n if n and f.get("ticks_avanza") else None
    for k in TERMINOS:
        f[k] = float(f[k]) if f.get(k, "") != "" else None

NOMBRES = {(0, 0, 0, 0): "B", (1, 0, 0, 0): "C", (0, 1, 0, 0): "B deslizando", (1, 1, 0, 0): "C deslizando",
           (1, 1, 1, 1): "Laboratorio", (1, 1, 0, 1): "C deslizando, currículo hasta la 30"}


def cond(f):
    return f["acercarse"], f["deslizar"], f["laboratorio"], f["c30"]


def nombre(c):
    return NOMBRES.get(c, str(c))


conds = sorted({cond(f) for f in filas})
ULTIMA = {c: max(f["generacion"] for f in filas if cond(f) == c) for c in conds}


def ventanas(c):
    """Gens 1-5 y 11-15 y, si la corrida pasa de 15, las últimas 5."""
    u = ULTIMA[c]
    return [(1, 5), (11, 15)] + ([(u - 4, u)] if u > 15 else [])


def tramos(c):
    """Gens 1-15 y, si la corrida pasa de 15, de la 16 a la última."""
    u = ULTIMA[c]
    return [(1, min(15, u))] + ([(16, u)] if u > 15 else [])


def de(c, evo, desde=1, hasta=99, semilla=None):
    return [f for f in filas if cond(f) == c and f["evolucion"] == evo
            and desde <= f["generacion"] <= hasta and (semilla is None or f["semilla"] == semilla)]


def media(g, k):
    v = [f[k] for f in g if f[k] is not None]
    return st.mean(v) if v else float("nan")


def mediana(v):
    """La mediana, o nan si no hay datos (en el laboratorio, un término que vale 0 no correlaciona)."""
    return st.median(v) if v else float("nan")


semillas = sorted({f["semilla"] for f in filas})
print("### Criterio 'usa la brújula': (camino a la puerta − al control), con evolución contra sin, gens 11-15 "
      "y últimas 5")
for c in conds:
    for desde, hasta in ventanas(c)[1:]:
        k, n = 0, 0
        partes = []
        for s in semillas:
            con, sin = de(c, 1, desde, hasta, s), de(c, 0, desde, hasta, s)
            if not con or not sin:
                continue
            uc, us = media(con, "uso"), media(sin, "uso")
            n += 1
            k += uc > us
            partes.append(f"s{s} {uc:+.3f} / {us:+.3f}")
        if n:
            print(f"  {nombre(c)}, gens {desde}-{hasta}: {k} de {n} semillas  ({'; '.join(partes)})")

con_sens = [f for f in filas if f["sb"] is not None]
if not con_sens:
    sys.exit("\n(sin columnas de sensibilidad: CSV de antes de esta medición)")
conds_sens = sorted({cond(f) for f in con_sens})

print("\n### Sensibilidad del giro (rad/tick, +90° contra −90°), promedio por agente: brújula | comida")
for c in conds_sens:
    for evo in (1, 0):
        linea = []
        for gen in range(1, ULTIMA[c] + 1):
            g = [f for f in de(c, evo, gen, gen) if f["sb"] is not None]
            if g:
                linea.append(f"g{gen} {media(g, 'sb'):+.4f}|{media(g, 'sc'):+.4f}")
        print(f"  {nombre(c)} {'con' if evo else 'sin'} evolución: " + "  ".join(linea))

print("\n### Sensibilidad por semilla, por ventana (brújula | comida); y cuántas semillas con evolución > sin, "
      "en las 11-15 y en las últimas 5")
for c in conds_sens:
    vs = ventanas(c)
    kb, kc, n = [0] * len(vs), [0] * len(vs), 0
    for s in semillas:
        partes = []
        vals = {}
        for evo in (1, 0):
            gs = [de(c, evo, desde, hasta, s) for desde, hasta in vs]
            if not all(gs):
                continue
            vals[evo] = [(media(g, "sb"), media(g, "sc")) for g in gs]
            partes.append(f"{'con' if evo else 'sin'} " + "→".join(f"{b:+.4f}" for b, _ in vals[evo]) + " | "
                          + "→".join(f"{cc:+.4f}" for _, cc in vals[evo]))
        if len(vals) == 2:
            n += 1
            for i in range(len(vs)):
                kb[i] += vals[1][i][0] > vals[0][i][0]
                kc[i] += vals[1][i][1] > vals[0][i][1]
        print(f"  {nombre(c)} s{s}: " + "   ".join(partes))
    print(f"  {nombre(c)}: con evolución > sin, " + "; ".join(
        f"gens {d}-{h}: brújula {kb[i]} de {n}, comida {kc[i]} de {n}" for i, (d, h) in enumerate(vs) if i))

print("\n### Criterio del laboratorio, últimas 5 generaciones, por semilla: sensibilidad a la brújula con / sin "
      "evolución (pide >= 0,02 y mayor); uso (puerta − control) con − sin (pide >= 0,05). Cada uno, 4 de 5")
for c in conds_sens:
    u = ULTIMA[c]
    k1 = k2 = n = 0
    partes = []
    for s in semillas:
        con, sin = de(c, 1, u - 4, u, s), de(c, 0, u - 4, u, s)
        if not con or not sin:
            continue
        bc, bs = media(con, "sb"), media(sin, "sb")
        du = media(con, "uso") - media(sin, "uso")
        n += 1
        k1 += bc >= 0.02 and bc > bs
        k2 += du >= 0.05
        partes.append(f"s{s} {bc:+.4f} / {bs:+.4f}, uso {du:+.3f}")
    if n:
        print(f"  {nombre(c)}, gens {u - 4}-{u}: principal {k1} de {n}, secundario {k2} de {n}  ({'; '.join(partes)})")

print("\n### Cuántos cobran algo: % de agentes con fitness > 0 y fitness medio, por ventana")
for c in conds_sens:
    for evo in (1, 0):
        partes = []
        for desde, hasta in ventanas(c):
            g = de(c, evo, desde, hasta)
            if not g:
                continue
            partes.append(f"gens {desde}-{hasta}: {100 * st.mean(f['fitness'] > 0 for f in g):.0f}%, "
                          f"{media(g, 'fitness'):.2f}")
        print(f"  {nombre(c)} {'con' if evo else 'sin'} evolución: " + " | ".join(partes))

print("\n### Selección: Spearman (x, fitness) dentro de cada generación; mediana y % de generaciones con r > 0")
for c in conds_sens:
    for desde, hasta in tramos(c):
        for evo in (1, 0):
            for etiqueta, k in (("sens. brújula", "sb"), ("sens. comida", "sc"), ("uso (puerta − control)", "uso"),
                                ("camino a la puerta", "camino")):
                rs = []
                for s in semillas:
                    for gen in range(desde, hasta + 1):
                        g = [f for f in de(c, evo, gen, gen, s) if f[k] is not None]
                        if len(g) >= 10:
                            r = spearman([f[k] for f in g], [f["fitness"] for f in g])
                            if not np.isnan(r):
                                rs.append(r)
                if rs:
                    print(f"  {nombre(c)} {'con' if evo else 'sin'} evolución, gens {desde}-{hasta}, {etiqueta}: "
                          f"mediana {st.median(rs):+.3f}, r > 0 en {100 * sum(r > 0 for r in rs) / len(rs):.0f}% "
                          f"de {len(rs)} generaciones")

print("\n### Los que más usan la brújula (quintil de sensibilidad dentro de la generación), con evolución")
for c in conds_sens:
    for desde, hasta in tramos(c):
        evo = [f for f in de(c, 1, desde, hasta) if f["sb"] is not None and f["aporte"] is not None]
        if not evo:
            continue
        print(f"  {nombre(c)}, gens {desde}-{min(hasta, ULTIMA[c] - 1)}:")
        for etiqueta, k in (("brújula", "sb"), ("comida", "sc")):
            quintiles = {q: [] for q in range(5)}
            for s in semillas:
                for gen in range(desde, hasta + 1):
                    g = sorted([f for f in evo if f["semilla"] == s and f["generacion"] == gen], key=lambda f: f[k])
                    for i, f in enumerate(g):
                        quintiles[min(4, i * 5 // len(g))].append(f)
            partes = [f"Q{q + 1}: aporte {st.mean(f['aporte'] for f in v):.2f}, "
                      f"pool {100 * st.mean(f['en_pool'] for f in v):.0f}%, "
                      f"fitness {st.mean(f['fitness'] for f in v):.1f}" for q, v in quintiles.items() if v]
            print(f"    por {etiqueta} (Q1 la menor): " + " | ".join(partes))

con_origen = [f for f in filas if f["origen"] is not None and f["evolucion"] == 1]
if con_origen:
    print("\n### Herencia: correlación (Pearson) entre el hijo y su padre (el promedio de los dos en el cruce), "
          "y pendiente; por origen, con evolución")
    por_id = {(f["semilla"], cond(f), f["generacion"], f["id"]): f for f in filas if f["evolucion"] == 1}
    for c in sorted({cond(f) for f in con_origen}):
        for desde, hasta in tramos(c):
            for origen in ("elite", "copia", "cruce"):
                partes = []
                for etiqueta, k in (("sens. brújula", "sb"), ("sens. comida", "sc"), ("camino a la puerta", "camino")):
                    x, y = [], []
                    for f in con_origen:
                        if (cond(f) != c or f["origen"] != origen or not desde <= f["generacion"] <= hasta
                                or f[k] is None):
                            continue
                        ps = [por_id.get((f["semilla"], c, f["generacion"] - 1, p)) for p in f["padres"]]
                        vs = [p[k] for p in ps if p is not None and p[k] is not None]
                        if len(vs) == len(f["padres"]) and vs:
                            x.append(st.mean(vs))
                            y.append(f[k])
                    if len(x) >= 10:
                        r = float(np.corrcoef(x, y)[0, 1])
                        pend = float(np.polyfit(x, y, 1)[0])
                        partes.append(f"{etiqueta} r {r:+.2f}, pendiente {pend:+.2f}")
                    if etiqueta == "sens. brújula":
                        n_pares = len(x)
                if partes:
                    print(f"  {nombre(c)}, gens {desde}-{hasta}, {origen} ({n_pares} hijos): " + " | ".join(partes))

print("\n### Qué paga el fitness: los que llegaron a < 50 px de la puerta contra el resto, misma generación (con evolución)")
for c in conds_sens:
    dif, lug = [], []
    for s in semillas:
        for gen in range(1, ULTIMA[c] + 1):
            g = de(c, 1, gen, gen, s)
            cerca = [f for f in g if f["dmin"] < 50 and not f["abrio"]]
            lejos = [f for f in g if f["dmin"] >= 50]
            if cerca and lejos:
                dif.append(st.mean(f["fitness"] for f in cerca) - st.mean(f["fitness"] for f in lejos))
                lug += [f["lugar"] for f in cerca]
    if dif:
        print(f"  {nombre(c)}: sin abrir, fitness de los < 50 px menos el del resto: mediana {st.median(dif):+.1f} "
              f"(en {len(dif)} generaciones); lugar mediano de los < 50 px: {st.median(lug):.0f} de 60")

con_terminos = [f for f in filas if f["f_comida"] is not None]
conds_t = sorted({cond(f) for f in con_terminos})
if conds_t:
    print("\n### Qué mueve el fitness: por término, promedio; desvío dentro de la generación (mediana); "
          "Spearman con el fitness (mediana)")
    for c in conds_t:
        for evo in (1, 0):
            for desde, hasta in ventanas(c):
                g = [f for f in de(c, evo, desde, hasta) if f["f_comida"] is not None]
                if not g:
                    continue
                partes = []
                for k in TERMINOS:
                    desvios, rs = [], []
                    for s in semillas:
                        for gen in range(desde, hasta + 1):
                            gg = [f for f in g if f["semilla"] == s and f["generacion"] == gen]
                            if len(gg) >= 10:
                                desvios.append(float(np.std([f[k] for f in gg])))
                                r = spearman([f[k] for f in gg], [f["fitness"] for f in gg])
                                if not np.isnan(r):
                                    rs.append(r)
                    partes.append(f"{k[2:]} {media(g, k):.1f}, de {mediana(desvios):.1f}, "
                                  f"r {st.median(rs) if rs else float('nan'):+.2f}")
                print(f"  {nombre(c)} {'con' if evo else 'sin'} evolución, gens {desde}-{hasta}: " + " | ".join(partes))

    print("\n### Cuánto giran (ticks con la llave): % de ticks girando, giro medio |rad/tick|, % de ticks avanzando; "
          "Spearman (giro medio, fitness) y (giro medio, anti-círculo)")
    for c in conds_t:
        for evo in (1, 0):
            for desde, hasta in ventanas(c):
                g = [f for f in de(c, evo, desde, hasta) if f["giro"] is not None]
                if not g:
                    continue
                rf, ra = [], []
                for s in semillas:
                    for gen in range(desde, hasta + 1):
                        gg = [f for f in g if f["semilla"] == s and f["generacion"] == gen]
                        if len(gg) >= 10:
                            for lista, k in ((rf, "fitness"), (ra, "f_anticirculo")):
                                r = spearman([f["giro"] for f in gg], [f[k] for f in gg])
                                if not np.isnan(r):
                                    lista.append(r)
                print(f"  {nombre(c)} {'con' if evo else 'sin'} evolución, gens {desde}-{hasta}: "
                      f"gira {100 * media(g, 'gira'):.0f}%, |giro| {media(g, 'giro'):.4f}, avanza {100 * media(g, 'avanza'):.0f}%; "
                      f"r(giro, fitness) {mediana(rf):+.2f}, r(giro, anti-círculo) {mediana(ra):+.2f}")
