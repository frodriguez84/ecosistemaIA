"""Varias evaluaciones por agente contra el control de igual costo (docs/qa/AnalisisQA.md#varias-evaluaciones), a partir
de los CSV de medir_puerta.py con evaluaciones=K y con reloj=R, y de la tanda publicada de las móviles (la comparación,
con una evaluación, y la línea base sin evolución).

Por semilla:
- El costo, en ticks simulados (la suma de la columna ticks del CSV de main.py): T(e), los de K hasta su episodio e, y
  T_C(n), los del control hasta su generación n. El control se lee hasta la primera n con T_C(n) >= T(último episodio), y
  sus ventanas son las mismas en ticks que las de K: las generaciones que terminan después de T(primer episodio - 1),
  hasta el corte.
- La sensibilidad a la brújula (sens_brujula / sens_ticks por fila de agente, promedio de las filas de la ventana, como
  analizar_brujula.py) y las manzanas por agente (manzanas_prom del CSV de main.py, promedio de las filas), en las
  últimas 5 generaciones del AG.
- Lo que ve la selección: en cada selección, el Spearman entre la sensibilidad de un episodio y el fitness con que eligió
  la selección (con K, fitness_prom; con una evaluación, el del episodio), con 10 agentes o más; una cuenta por episodio,
  mediana de las de la ventana (de la generación 16 a la última). Informativo, solo con K: con la sensibilidad promedio
  de los K episodios, y con el fitness de un episodio (lo que vería una sola evaluación).
- El criterio fijado antes de correr; los términos del fitness, la puerta y cuánto se repite el ranking entre los
  episodios de una generación (con K).
- Los controles que se leen de los CSV: la cabecera y las primeras filas iguales a la tanda publicada; cada cerebro juega
  K episodios con un solo hash; el lugar del promedio, recalculado; la élite y los padres en el pool del promedio; los
  límites de ticks y la etapa inicial; cuántas selecciones suben la mutación (desvío / media del fitness < 0,15).

Uso: python mediciones/analizar_evaluaciones.py NUEVA PUBLICADA
NUEVA tiene los CSV de evaluaciones=K y de reloj=R; PUBLICADA, los de la tanda de las fortalezas móviles.
"""
import csv
import glob
import itertools
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)

UMBRAL = 0.02         # rad/tick, el de las móviles
VECES = 1.5           # tamaño mínimo: el promedio, 1,5 veces el de las móviles y el del control
MINIMO = 0.040        # 1,5 veces +0,0268, el promedio de las móviles
COMIDA = 0.90         # manzanas, al menos el 90% de las de las móviles
SUBA_SELECCION = 0.03  # lo que ve la selección, al menos +0,03 sobre las móviles y el control
TOPE_RELOJ = 30       # el de medir_puerta.py
DESDE_SELECCION = 16  # las ventanas de la selección, de la 16 a la última generación del AG


def rangos(v):
    """Rangos con los empates promediados (los de analizar_brujula.py)."""
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


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        t = int(f.get("sens_ticks") or 0)
        f["sb"] = float(f["sens_brujula"]) / t if t else None
    return filas


def uno(patron):
    rutas = sorted(glob.glob(patron))
    if len(rutas) != 1:
        sys.exit(f"se esperaba un archivo para {patron}, hay {len(rutas)}")
    return rutas[0]


def limite(g):
    """El límite de ticks de la generación g (main._ticks_de_generacion, con los valores de config.py)."""
    return 960 + 180 * ((g - 1) // 4)


nueva, publicada = sys.argv[1], sys.argv[2]
semillas = sorted({int(os.path.basename(r).split("_")[1][1:])
                   for r in glob.glob(os.path.join(nueva, "corrida_s*_evaluaciones*_evolucion.csv"))})
D = {}  # semilla -> datos de las cuatro condiciones
for s in semillas:
    d = D[s] = {}
    d["k_ag"] = leer(uno(os.path.join(nueva, f"agentes_s{s}_*evaluaciones*_evolucion.csv")))
    d["k_co"] = leer(uno(os.path.join(nueva, f"corrida_s{s}_*evaluaciones*_evolucion.csv")))
    d["c_ag"] = leer(uno(os.path.join(nueva, f"agentes_s{s}_*reloj*_evolucion.csv")))
    d["c_co"] = leer(uno(os.path.join(nueva, f"corrida_s{s}_*reloj*_evolucion.csv")))
    d["m_ag"] = leer(uno(os.path.join(publicada, f"agentes_s{s}_*moviles*cruce*_evolucion.csv")))
    d["m_co_ruta"] = uno(os.path.join(publicada, f"corrida_s{s}_*moviles*cruce*_evolucion.csv"))
    d["m_co"] = leer(d["m_co_ruta"])
    d["b_ag"] = leer(uno(os.path.join(publicada, f"agentes_s{s}_*moviles*_sin_evolucion.csv")))
    d["b_co"] = leer(uno(os.path.join(publicada, f"corrida_s{s}_*moviles*_sin_evolucion.csv")))
    d["k_co_ruta"] = uno(os.path.join(nueva, f"corrida_s{s}_*evaluaciones*_evolucion.csv"))
    d["c_co_ruta"] = uno(os.path.join(nueva, f"corrida_s{s}_*reloj*_evolucion.csv"))
K = int(D[semillas[0]]["k_ag"][0]["evaluaciones"])
R = int(D[semillas[0]]["c_ag"][0]["reloj"])
G = max(int(f["gen_real"]) for f in D[semillas[0]]["k_ag"])  # generaciones del AG con K
G_PUB = max(int(f["generacion"]) for f in D[semillas[0]]["m_co"])
print(f"K = {K}, {G} generaciones del AG ({K * G} episodios); control con reloj={R}; comparación, {G_PUB} generaciones; "
      f"semillas {semillas}")


def media(v):
    v = [x for x in v if x is not None]
    return st.mean(v) if v else float("nan")


# ---------- Ventanas, por semilla ----------
for s in semillas:
    d = D[s]
    tk = np.cumsum([int(f["ticks"]) for f in d["k_co"]])  # tk[e - 1] = T(e)
    tc = np.cumsum([int(f["ticks"]) for f in d["c_co"]])
    d["T"], d["TC"] = tk, tc
    total = tk[-1]
    llega = np.nonzero(tc >= total)[0]
    d["corte"] = int(llega[0]) + 1 if len(llega) else len(tc)
    d["llega"] = bool(len(llega))

    def ventana_control(e0, d=d, tk=tk, tc=tc):
        """Las generaciones del control que terminan después de T(e0 - 1), hasta el corte."""
        antes = tk[e0 - 2] if e0 > 1 else 0
        return [n for n in range(1, d["corte"] + 1) if tc[n - 1] > antes]

    e_ult = (G - 5) * K + 1   # primer episodio de las últimas 5 generaciones del AG
    e_sel = (DESDE_SELECCION - 1) * K + 1
    d["c_ult"], d["c_sel"] = ventana_control(e_ult), ventana_control(e_sel)


def filas_k(d, desde, hasta):
    return [f for f in d["k_ag"] if desde <= int(f["gen_real"]) <= hasta]


def filas_gen(filas, gens):
    gens = set(gens)
    return [f for f in filas if int(f["generacion"]) in gens]


def sens(filas):
    return media([f["sb"] for f in filas])


def comida(corrida, gens):
    gens = set(gens)
    return st.mean(float(f["manzanas_prom"]) for f in corrida if int(f["generacion"]) in gens)


ULT_PUB = range(G_PUB - 4, G_PUB + 1)
SEL_PUB = range(DESDE_SELECCION, G_PUB + 1)
for s in semillas:
    d = D[s]
    ek = range((G - 5) * K + 1, G * K + 1)
    d["sens"] = dict(k=sens(filas_k(d, G - 4, G)), c=sens(filas_gen(d["c_ag"], d["c_ult"])),
                     m=sens(filas_gen(d["m_ag"], ULT_PUB)), b=sens(filas_gen(d["b_ag"], ULT_PUB)))
    d["comida"] = dict(k=comida(d["k_co"], ek), c=comida(d["c_co"], d["c_ult"]), m=comida(d["m_co"], ULT_PUB),
                       b=comida(d["b_co"], ULT_PUB))


# ---------- Lo que ve la selección ----------
def seleccion_una(filas_por_gen):
    """Con una evaluación: Spearman (sensibilidad, fitness) dentro de cada generación, con 10 agentes o más."""
    rs = []
    for g in filas_por_gen:
        g = [f for f in g if f["sb"] is not None]
        if len(g) >= 10:
            r = spearman([f["sb"] for f in g], [float(f["fitness"]) for f in g])
            if not np.isnan(r):
                rs.append(r)
    return rs


def seleccion_k(d, desde, hasta):
    """Con K: por generación del AG, una cuenta por episodio, Spearman (sensibilidad de ese episodio, fitness_prom); y,
    informativos, con la sensibilidad promedio de los K episodios (una por generación) y con el fitness del episodio."""
    rs, prom, un_ep = [], [], []
    for g in range(desde, hasta + 1):
        fg = [f for f in d["k_ag"] if int(f["gen_real"]) == g]
        fp = {f["cerebro"]: float(f["fitness_prom"]) for f in fg if f["episodio"] == str(K)}
        for e in range(1, K + 1):
            fe = [f for f in fg if f["episodio"] == str(e) and f["sb"] is not None]
            if len(fe) >= 10:
                for lista, y in ((rs, [fp[f["cerebro"]] for f in fe]), (un_ep, [float(f["fitness"]) for f in fe])):
                    r = spearman([f["sb"] for f in fe], y)
                    if not np.isnan(r):
                        lista.append(r)
        sb = defaultdict(list)
        for f in fg:
            if f["sb"] is not None:
                sb[f["cerebro"]].append(f["sb"])
        cer = [c for c in fp if c in sb]
        if len(cer) >= 10:
            r = spearman([st.mean(sb[c]) for c in cer], [fp[c] for c in cer])
            if not np.isnan(r):
                prom.append(r)
    return rs, prom, un_ep


def por_gen(filas, gens):
    return [[f for f in filas if int(f["generacion"]) == g] for g in gens]


SEL = {}
for s in semillas:
    d = D[s]
    rk, rk_prom, rk_un = seleccion_k(d, DESDE_SELECCION, G)
    SEL[s] = dict(k=rk, k_prom=rk_prom, k_un=rk_un, c=seleccion_una(por_gen(d["c_ag"], d["c_sel"])),
                  m=seleccion_una(por_gen(d["m_ag"], SEL_PUB)), b=seleccion_una(por_gen(d["b_ag"], SEL_PUB)))


def mediana(v):
    return st.median(v) if v else float("nan")


# ---------- Salida ----------
print("\n### El costo (ticks simulados, por semilla)")
for s in semillas:
    d = D[s]
    print(f"  s{s}: K = {K}, {d['T'][-1]:,} ticks en {len(d['T'])} episodios | control: {d['TC'][d['corte'] - 1]:,} en "
          f"{d['corte']} generaciones ({'llega' if d['llega'] else 'NO LLEGA, se lee en la última'}; corrió "
          f"{len(d['TC'])}, {d['TC'][-1]:,}) | comparación: {sum(int(f['ticks']) for f in d['m_co']):,} en {G_PUB} | "
          f"ventanas del control: últimas {d['c_ult'][0]}-{d['c_ult'][-1]}, selección {d['c_sel'][0]}-{d['c_sel'][-1]}")

NOMBRES = dict(k=f"K = {K}", c="Control de igual costo", m="Móviles (una evaluación)", b="Sin evolución (móviles)")
print(f"\n### Sensibilidad a la brújula, últimas 5 generaciones del AG (rad/tick)")
print("  semilla | " + " | ".join(NOMBRES[c] for c in "kcmb"))
for s in semillas:
    print(f"  s{s} | " + " | ".join(f"{D[s]['sens'][c]:+.4f}" for c in "kcmb"))
prom_sens = {c: st.mean(D[s]["sens"][c] for s in semillas) for c in "kcmb"}
print("  promedio | " + " | ".join(f"{prom_sens[c]:+.4f}" for c in "kcmb"))

print("\n### Manzanas por agente, últimas 5 generaciones del AG")
for s in semillas:
    print(f"  s{s} | " + " | ".join(f"{D[s]['comida'][c]:.3f}" for c in "kcmb"))
prom_com = {c: st.mean(D[s]["comida"][c] for s in semillas) for c in "kcmb"}
print("  promedio | " + " | ".join(f"{prom_com[c]:.3f}" for c in "kcmb"))

print(f"\n### Lo que ve la selección, gens {DESDE_SELECCION}-{G} (Spearman sensibilidad de un episodio ↔ fitness de la "
      "selección; mediana, y por semilla)")
med_sel = {}
for c in "kcmb":
    todos = [r for s in semillas for r in SEL[s][c]]
    med_sel[c] = mediana(todos)
    print(f"  {NOMBRES[c]}: mediana {med_sel[c]:+.3f} de {len(todos)} | por semilla "
          + " ".join(f"s{s} {mediana(SEL[s][c]):+.3f}" for s in semillas))
for c, etiqueta in (("k_prom", f"K = {K}, informativo: sensibilidad promedio de los {K} episodios ↔ fitness_prom"),
                    ("k_un", f"K = {K}, informativo: sensibilidad ↔ fitness del mismo episodio (lo que vería una evaluación)")):
    todos = [r for s in semillas for r in SEL[s][c]]
    print(f"  {etiqueta}: mediana {mediana(todos):+.3f} de {len(todos)} | por semilla "
          + " ".join(f"s{s} {mediana(SEL[s][c]):+.3f}" for s in semillas))

print("\n### Criterio (fijado antes de correr)")
k1 = 0
for s in semillas:
    v = D[s]["sens"]
    ok = v["k"] >= UMBRAL and v["k"] > v["b"] and v["k"] > v["m"] and v["k"] > v["c"]
    k1 += ok
    print(f"  s{s}: {v['k']:+.4f} >= {UMBRAL} y > línea base {v['b']:+.4f}, móviles {v['m']:+.4f}, control {v['c']:+.4f}: "
          f"{'sí' if ok else 'no'}")
pedido = max(MINIMO, VECES * prom_sens["m"], VECES * prom_sens["c"])
tam = prom_sens["k"] >= pedido
c1 = k1 >= 4 and tam
print(f"  1. {k1} de {len(semillas)} semillas (pide 4); tamaño mínimo: promedio {prom_sens['k']:+.4f}, pide {pedido:+.4f} "
      f"({prom_sens['k'] / prom_sens['m']:.2f} veces las móviles, {prom_sens['k'] / prom_sens['c']:.2f} veces el control): "
      f"{'cumple' if tam else 'no cumple'} -> {'CUMPLE' if c1 else 'NO CUMPLE'}")
c2 = prom_com["k"] >= COMIDA * prom_com["m"]
print(f"  2. Manzanas: {prom_com['k']:.3f}, el {100 * prom_com['k'] / prom_com['m']:.0f}% de las móviles "
      f"({prom_com['m']:.3f}; pide el {100 * COMIDA:.0f}%) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
print(f"  3. {'PASA' if c1 and c2 else 'NO PASA'}")
sube_m = med_sel["k"] - med_sel["m"]
sube_c = med_sel["k"] - med_sel["c"]
semillas_m = sum(mediana(SEL[s]["k"]) > mediana(SEL[s]["m"]) for s in semillas)
lee = sube_m >= SUBA_SELECCION and sube_c >= SUBA_SELECCION and semillas_m >= 4
print(f"  Se lee con la selección: {med_sel['k']:+.3f}, {sube_m:+.3f} sobre las móviles y {sube_c:+.3f} sobre el control "
      f"(pide +{SUBA_SELECCION} sobre los dos); sobre las móviles en {semillas_m} de {len(semillas)} semillas (pide 4) -> "
      f"{'sube' if lee else 'no sube'}")

print("\n### Términos del fitness, la puerta y el juego (últimas 5 generaciones del AG; la puerta, gens 16 a la última)")
TERMINOS = ("f_comida", "f_acercarse", "f_supervivencia", "f_puzzle")


def juego(filas_ult, filas_sel, episodios_sel):
    t = {k: media([float(f[k]) for f in filas_ult]) for k in TERMINOS + ("fitness", "edad")}
    t["abren"] = sum(int(f["abrio"]) for f in filas_sel)
    t["abren_por_ep"] = t["abren"] / episodios_sel
    return t


for c in "kcmb":
    partes = []
    for s in semillas:
        d = D[s]
        if c == "k":
            t = juego(filas_k(d, G - 4, G), filas_k(d, DESDE_SELECCION, G), (G - DESDE_SELECCION + 1) * K)
        elif c == "c":
            t = juego(filas_gen(d["c_ag"], d["c_ult"]), filas_gen(d["c_ag"], d["c_sel"]), len(d["c_sel"]))
        else:
            ag = d["m_ag"] if c == "m" else d["b_ag"]
            t = juego(filas_gen(ag, ULT_PUB), filas_gen(ag, SEL_PUB), len(SEL_PUB))
        partes.append(t)
    print(f"  {NOMBRES[c]}: " + " · ".join(f"{k[2:] if k.startswith('f_') else k} {st.mean(p[k] for p in partes):.2f}"
                                          for k in TERMINOS + ("fitness", "edad"))
          + f" · abren la puerta {sum(p['abren'] for p in partes)} ({', '.join(str(p['abren']) for p in partes)}), "
            f"{st.mean(p['abren_por_ep'] for p in partes):.2f} por episodio")

print(f"\n### Con K = {K}: cuánto se repite el ranking del fitness entre los episodios de una generación (Spearman, "
      "promedio de los pares; mediana de las generaciones del tramo)")
for desde, hasta in ((1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30)):
    if hasta > G:
        continue
    vals = []
    for s in semillas:
        for g in range(desde, hasta + 1):
            fg = [f for f in D[s]["k_ag"] if int(f["gen_real"]) == g]
            m = defaultdict(dict)
            for f in fg:
                m[f["cerebro"]][int(f["episodio"])] = float(f["fitness"])
            mat = np.array([[m[c][e] for e in range(1, K + 1)] for c in m])
            pares = [spearman(mat[:, i], mat[:, j]) for i, j in itertools.combinations(range(K), 2)]
            vals.append(np.nanmean(pares))
    sb_ = np.mean(vals)
    print(f"  gens {desde}-{hasta}: {st.median(vals):+.3f} (promedio {sb_:+.3f}; con el promedio de {K}, por "
          f"Spearman-Brown, {K * sb_ / (1 + (K - 1) * sb_):+.3f})")

# ---------- Controles ----------
print("\n### Controles")


def lineas(ruta):
    with open(ruta, "rb") as f:
        return f.read().split(b"\n")


errores = 0
for s in semillas:
    d = D[s]
    lp, lk, lc = lineas(d["m_co_ruta"]), lineas(d["k_co_ruta"]), lineas(d["c_co_ruta"])
    a = lk[:2] == lp[:2] and lk[2] != lp[2]
    b = lc[:5] == lp[:5] and lc[5] != lp[5]
    comunes = [k for k in d["m_ag"][0] if k in d["k_ag"][0] and k not in ("aporte", "sb")]
    gen1 = lambda filas, gens: [{k: f[k] for k in comunes} for f in filas if int(f["generacion"]) in gens]  # noqa: E731
    a_ag = gen1(d["k_ag"], {1}) == gen1(d["m_ag"], {1})
    comunes_c = [k for k in d["m_ag"][0] if k in d["c_ag"][0] and k != "sb"]
    b_ag = ([{k: f[k] for k in comunes_c} for f in d["c_ag"] if int(f["generacion"]) <= 4]
            == [{k: f[k] for k in comunes_c} for f in d["m_ag"] if int(f["generacion"]) <= 4])
    # Cada cerebro, K episodios con un hash; el lugar del promedio; la élite y los padres en el pool del promedio
    mal_cer = mal_lugar = 0
    por_g = defaultdict(list)
    for f in d["k_ag"]:
        por_g[int(f["gen_real"])].append(f)
    for g, fg in por_g.items():
        veces = Counter(f["cerebro"] for f in fg)
        hashes = defaultdict(set)
        for f in fg:
            hashes[f["cerebro"]].add(f["pesos_hash"])
        eps = {e: {f["cerebro"] for f in fg if f["episodio"] == str(e)} for e in range(1, K + 1)}
        mal_cer += not (set(veces.values()) == {K} and all(len(h) == 1 for h in hashes.values())
                        and all(len(eps[e]) == len(veces) == 60 for e in eps))
        suma = defaultdict(float)
        for f in fg:
            suma[f["cerebro"]] += float(f["fitness"])
        ult = sorted([f for f in fg if f["episodio"] == str(K)], key=lambda f: int(f["orden"]))
        esperado = sorted(ult, key=lambda f: suma[f["cerebro"]] / K, reverse=True)
        mal_lugar += sum(int(f["lugar_prom"]) != i for i, f in enumerate(esperado, start=1))
    elite_mal = padres_mal = padres = padres_pool_ep = 0
    for g in range(1, G):
        ult = {f["id"]: f for f in por_g[g] if f["episodio"] == str(K)}
        sig = [f for f in por_g[g + 1] if f["episodio"] == "1"]
        for f in sig:
            if f["origen"] == "elite":
                elite_mal += ult[f["padre1"]]["lugar_prom"] != "1"
            elif f["origen"] in ("copia", "cruce"):
                for p in (f["padre1"], f["padre2"]):
                    if p:
                        padres += 1
                        padres_mal += ult[p]["en_pool_prom"] != "1"
                        padres_pool_ep += ult[p]["en_pool"] == "1"
    # Límites de ticks y etapa inicial
    k_lim = sum(int(f["ticks"]) > limite(-(-int(f["generacion"]) // K)) for f in d["k_co"])
    k_en_lim = sum(int(f["ticks"]) == limite(-(-int(f["generacion"]) // K)) for f in d["k_co"])
    c_lim = sum(int(f["ticks"]) > limite(min(-(-int(f["generacion"]) // R), TOPE_RELOJ)) for f in d["c_co"])
    c_en_lim = sum(int(f["ticks"]) == limite(min(-(-int(f["generacion"]) // R), TOPE_RELOJ)) for f in d["c_co"])
    etapa = {f["etapa_inicial"] for f in d["k_co"] + d["c_co"]}
    e = (not a) + (not b) + (not a_ag) + (not b_ag) + mal_cer + elite_mal + padres_mal + k_lim + c_lim + (etapa != {"1"})
    errores += e
    print(f"  s{s}: K, episodio 1 = gen 1 publicada {a} (agentes {a_ag}); control, gens 1-4 = publicadas {b} "
          f"(agentes {b_ag}) | generaciones con un cerebro fuera de K episodios o de un hash: {mal_cer} | lugar_prom "
          f"distinto del recalculado: {mal_lugar} | élite fuera del primer lugar del promedio: {elite_mal} | padres fuera "
          f"del pool del promedio: {padres_mal} de {padres} (en el pool del episodio {K}: {padres_pool_ep}) | por encima "
          f"del límite: K {k_lim}, control {c_lim} (en el límite: {k_en_lim} y {c_en_lim}) | etapa inicial {sorted(etapa)}")
print(f"  errores: {errores} (lugar_prom se recalcula con el fitness redondeado a 4: una diferencia ahí es un empate)")

print("\n### La mutación adaptativa: selecciones con desvío / media del fitness < 0,15 (la mutación sube 2,5 veces)")


def cv(v):
    v = np.asarray(v, dtype=float)
    return np.std(v) / (np.mean(v) + 1e-6)


for c in "kcm":
    bajas = total = 0
    for s in semillas:
        d = D[s]
        if c == "k":
            for g in range(1, G):  # el evolve real corre después de las generaciones 1 a G - 1
                v = [float(f["fitness_prom"]) for f in d["k_ag"] if int(f["gen_real"]) == g and f["episodio"] == str(K)]
                bajas += cv(v) < 0.15
                total += 1
        else:
            ag, ult = (d["c_ag"], d["corte"]) if c == "c" else (d["m_ag"], G_PUB)
            for g in range(1, ult):
                bajas += cv([float(f["fitness"]) for f in ag if int(f["generacion"]) == g]) < 0.15
                total += 1
    print(f"  {NOMBRES[c]}: {bajas} de {total}")
