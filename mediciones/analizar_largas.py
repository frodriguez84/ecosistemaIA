"""Las corridas largas como condición propia (docs/qa/AnalisisQA.md#corridas-largas), a partir de los CSV de
medir_puerta.py: la condición de las móviles a 150 generaciones con el reloj de siempre (la larga) y su línea base sin
evolución, contra el control de varias evaluaciones (el mismo largo, con reloj=R) y la tanda publicada de las móviles
(30 generaciones).

Con la misma cuenta que analizar_evaluaciones.py en cada fila (LEC-016, LEC-021):
- sensibilidad a la brújula: sens_brujula / sens_ticks por fila de agente, promedio de las filas de la ventana;
- manzanas por agente: manzanas_prom del CSV de main.py, promedio de las filas de la ventana;
- lo que ve la selección: el Spearman entre la sensibilidad y el fitness dentro de cada generación con 10 agentes o más,
  mediana de las generaciones del tramo;
- la puerta de madera: agentes_puerta_madera del CSV de main.py, promedio por generación (se cruza con abrio).
Imprime el criterio fijado antes de correr (las últimas 5 generaciones de la larga), el reloj a igual generación y a igual
costo en ticks, la selección por tramo, la trayectoria (cuándo pasa 0,02 para quedarse), la puerta y el resto del puzzle,
los términos del fitness, el costo y los controles (las primeras generaciones, las publicadas; los límites; la etapa).

Uso: python mediciones/analizar_largas.py LARGA CONTROL PUBLICADA
LARGA tiene los CSV de la larga y de su línea base; CONTROL, los de reloj=R (varias evaluaciones); PUBLICADA, los de la
tanda de las fortalezas móviles. Con LARGA igual a PUBLICADA, la larga es la tanda publicada: la prueba del script, que
tiene que dar sus números (+0,0268 de sensibilidad, 1,089 manzanas, +0,132 de selección en las gens 16-30).
"""
import csv
import glob
import hashlib
import os
import statistics as st
import sys

import numpy as np

UMBRAL = 0.02          # rad/tick
MINIMO = 0.040         # 1,5 veces +0,0268, el promedio de las móviles
COMIDA = 0.90          # manzanas: al menos el 90% de las de las móviles
PUERTA = 1.0           # agentes con la puerta de madera abierta por generación (el criterio del ítem 5)
RANGO_RELOJ = (0.67, 1.5)  # q = larga / control: adentro, el reloj no se distingue
TOPE_RELOJ = 30        # el de medir_puerta.py: con reloj=R, desde la 30·R + 1 como la 30
DESDE_PUERTA = 90      # la puerta sostenida: en cuántas generaciones alguien la abre, desde esta
EXCLUIR = ("reloj", "evaluaciones")


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
        f["gen"] = int(f["generacion"])
        t = int(f.get("sens_ticks") or 0)
        f["sb"] = float(f["sens_brujula"]) / t if t else None
    return filas


def uno(patron, con=None):
    """El único archivo del patrón; sin los de reloj y evaluaciones, salvo el que se pide con con."""
    rutas = [r for r in sorted(glob.glob(patron))
             if (con in os.path.basename(r) if con else not any(x in os.path.basename(r) for x in EXCLUIR))]
    if len(rutas) != 1:
        sys.exit(f"se esperaba un archivo para {patron} ({con}), hay {len(rutas)}")
    return rutas[0]


def media(v):
    v = [x for x in v if x is not None]
    return st.mean(v) if v else float("nan")


def mediana(v):
    return st.median(v) if v else float("nan")


def sens(ag, gens):
    gens = set(gens)
    return media([f["sb"] for f in ag if f["gen"] in gens])


def comida(co, gens):
    gens = set(gens)
    return st.mean(float(f["manzanas_prom"]) for f in co if f["gen"] in gens)


def puerta(co, gens):
    """Agentes con la puerta de madera abierta, promedio por generación."""
    gens = set(gens)
    return st.mean(int(f["agentes_puerta_madera"]) for f in co if f["gen"] in gens)


def seleccion(ag, gens):
    """Spearman (sensibilidad, fitness) dentro de cada generación con 10 agentes o más: una cuenta por generación."""
    rs = []
    for g in gens:
        fg = [f for f in ag if f["gen"] == g and f["sb"] is not None]
        if len(fg) >= 10:
            r = spearman([f["sb"] for f in fg], [float(f["fitness"]) for f in fg])
            if not np.isnan(r):
                rs.append(r)
    return rs


def por_gen(ag):
    """Generación -> sensibilidad de cada fila."""
    d = {}
    for f in ag:
        if f["sb"] is not None:
            d.setdefault(f["gen"], []).append(f["sb"])
    return d


def cuando_pasa(ag):
    """La primera n con la media de las gens n − 4 a n ≥ 0,02, y también la de cada una de las 5 ventanas siguientes
    (la cuenta que da lo publicado del control: 14, 22, 51, 95 y nunca). None si no pasa."""
    d = por_gen(ag)
    ultima = max(d)

    def m(a, b):
        return st.mean([v for g in range(a, b + 1) for v in d.get(g, [])])

    for n in range(5, ultima - 4):
        if all(m(k - 4, k) >= UMBRAL for k in range(n, n + 6)):
            return n
    return None


def limite(n):
    """El límite de ticks de la generación n (main._ticks_de_generacion, con los valores de config.py)."""
    return 960 + 180 * ((n - 1) // 4)


def limite_reloj(n, r):
    return limite(min(-(-n // r), TOPE_RELOJ))


def acumulados(co):
    return np.cumsum([int(f["ticks"]) for f in co])  # [n - 1] = T(n)


def ventana_costo(t_a, t_b):
    """Igual costo en ticks: el presupuesto es el menor de los dos totales. La corrida que lo gastó se lee en sus últimas 5
    generaciones; la otra, hasta su primera generación con T(n) ≥ P, en las que terminan después del comienzo de esas 5.
    Devuelve las ventanas (generaciones) de a y de b, y P."""
    if t_a[-1] <= t_b[-1]:
        wa, wb, p = _ventanas(t_a, t_b)
        return wa, wb, p
    wb, wa, p = _ventanas(t_b, t_a)
    return wa, wb, p


def _ventanas(t_gasta, t_otra):
    n = len(t_gasta)
    p = int(t_gasta[-1])
    w_gasta = list(range(n - 4, n + 1))
    inicio = int(t_gasta[n - 6])  # T(n − 5): las 5 últimas terminan después
    corte = int(np.nonzero(t_otra >= p)[0][0]) + 1
    w_otra = [k for k in range(1, corte + 1) if t_otra[k - 1] > inicio]
    return w_gasta, w_otra, p


def sha_prefijo(ruta, filas):
    """SHA-256 de la cabecera y las primeras filas del CSV, con sus finales de línea."""
    with open(ruta, "rb") as f:
        lineas = f.read().split(b"\n")
    return hashlib.sha256(b"\n".join(lineas[:filas + 1]) + b"\n").hexdigest()


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def cargar(larga, control, publicada):
    semillas = sorted({int(os.path.basename(r).split("_")[1][1:])
                       for r in glob.glob(os.path.join(larga, "corrida_s*_*moviles*cruce*_evolucion.csv"))
                       if not any(x in os.path.basename(r) for x in EXCLUIR)})
    D = {}
    for s in semillas:
        d = D[s] = {}
        for clave, carpeta, patron, con in (
                ("L", larga, f"s{s}_*moviles*cruce*_evolucion.csv", None),
                ("B", larga, f"s{s}_*moviles*_sin_evolucion.csv", None),
                ("C", control, f"s{s}_*moviles*cruce*_evolucion.csv", "reloj"),
                ("M", publicada, f"s{s}_*moviles*cruce*_evolucion.csv", None),
                ("MB", publicada, f"s{s}_*moviles*_sin_evolucion.csv", None)):
            d[clave + "_co_ruta"] = uno(os.path.join(carpeta, "corrida_" + patron), con)
            d[clave + "_ag_ruta"] = uno(os.path.join(carpeta, "agentes_" + patron), con)
            d[clave + "_geo_ruta"] = uno(os.path.join(carpeta, "geometria_" + patron), con)
            d[clave + "_co"] = leer(d[clave + "_co_ruta"])
            d[clave + "_ag"] = leer(d[clave + "_ag_ruta"])
    return semillas, D


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    larga, control, publicada = sys.argv[1], sys.argv[2], sys.argv[3]
    semillas, D = cargar(larga, control, publicada)
    s0 = D[semillas[0]]
    G = max(f["gen"] for f in s0["L_co"])
    G_PUB = max(f["gen"] for f in s0["M_co"])
    R = int(s0["C_ag"][0]["reloj"])
    W = range(G - 4, G + 1)
    W_PUB = range(G_PUB - 4, G_PUB + 1)
    print(f"Larga: {G} generaciones (curriculo_hasta {s0['L_ag'][0]['curriculo_hasta']}); control con reloj={R}, "
          f"{max(f['gen'] for f in s0['C_co'])} generaciones; móviles publicadas, {G_PUB}; semillas {semillas}")

    # ---------- Por semilla ----------
    for s in semillas:
        d = D[s]
        d["sens"] = dict(L=sens(d["L_ag"], W), B=sens(d["B_ag"], W), C=sens(d["C_ag"], W), M=sens(d["M_ag"], W_PUB),
                         MB=sens(d["MB_ag"], W_PUB))
        d["comida"] = dict(L=comida(d["L_co"], W), B=comida(d["B_co"], W), C=comida(d["C_co"], W),
                           M=comida(d["M_co"], W_PUB), MB=comida(d["MB_co"], W_PUB))
        d["puerta"] = dict(L=puerta(d["L_co"], W), B=puerta(d["B_co"], W), C=puerta(d["C_co"], W),
                           M=puerta(d["M_co"], W_PUB), MB=puerta(d["MB_co"], W_PUB))
        d["TL"], d["TC"], d["TB"] = acumulados(d["L_co"]), acumulados(d["C_co"]), acumulados(d["B_co"])
        d["wL"], d["wC"], d["P"] = ventana_costo(d["TL"], d["TC"])

    def prom(clave, c):
        return st.mean(D[s][clave][c] for s in semillas)

    NOMBRES = dict(L="Larga", C="Control (reloj lento)", M="Móviles (30 gens)", B="Línea base larga",
                   MB="Línea base móviles")

    print(f"\n### Sensibilidad a la brújula · manzanas por agente · puerta de madera por generación; gens {W[0]}-{W[-1]} "
          f"(las móviles y su línea base, {W_PUB[0]}-{W_PUB[-1]})")
    for c in ("L", "C", "M", "B", "MB"):
        print(f"  {NOMBRES[c]}: " + " | ".join(
            f"s{s} {D[s]['sens'][c]:+.4f} · {D[s]['comida'][c]:.3f} · {D[s]['puerta'][c]:.2f}" for s in semillas)
              + f" || promedio {prom('sens', c):+.4f} · {prom('comida', c):.3f} · {prom('puerta', c):.2f}")

    # ---------- Criterio ----------
    print("\n### Criterio (fijado antes de correr)")
    k1 = 0
    for s in semillas:
        v = D[s]["sens"]
        ok = v["L"] >= UMBRAL and v["L"] > v["B"]
        k1 += ok
        print(f"  s{s}: {v['L']:+.4f} >= {UMBRAL} y > línea base larga {v['B']:+.4f}: {'sí' if ok else 'no'}")
    tam = prom("sens", "L") >= MINIMO
    c1 = k1 >= 4 and tam
    print(f"  1. Aprende la brújula: {k1} de {len(semillas)} (pide 4); promedio {prom('sens', 'L'):+.4f}, pide "
          f"{MINIMO:+.3f} ({prom('sens', 'L') / prom('sens', 'M'):.2f} veces las móviles) -> "
          f"{'CUMPLE' if c1 else 'NO CUMPLE'}")
    c2 = prom("comida", "L") >= COMIDA * prom("comida", "M")
    print(f"  2. Sin dejar de comer: {prom('comida', 'L'):.3f}, el {100 * prom('comida', 'L') / prom('comida', 'M'):.0f}% "
          f"de las móviles ({prom('comida', 'M'):.3f}; pide el {100 * COMIDA:.0f}%) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    k3 = 0
    for s in semillas:
        p = D[s]["puerta"]
        ok = p["L"] >= PUERTA and p["L"] > p["B"]
        k3 += ok
        print(f"  s{s}: puerta {p['L']:.2f} por generación >= {PUERTA:g} y > línea base larga {p['B']:.2f}: "
              f"{'sí' if ok else 'no'}")
    print(f"  3. Pasa la puerta: {k3} de {len(semillas)} (pide 4) -> {'CUMPLE' if k3 >= 4 else 'NO CUMPLE'}")
    print(f"  Referencia nueva (1 y 2): {'SÍ' if c1 and c2 else 'NO'}; puerta (3): {'SÍ' if k3 >= 4 else 'NO'}")

    # ---------- El reloj ----------
    print("\n### El reloj: la larga contra el control (sensibilidad; q = promedio de la larga / del control)")

    def veredicto(vl, vc):
        q = st.mean(vl) / st.mean(vc)
        arriba = sum(a > b for a, b in zip(vl, vc))
        abajo = sum(a < b for a, b in zip(vl, vc))
        if RANGO_RELOJ[0] <= q <= RANGO_RELOJ[1]:
            v = "NO SE DISTINGUE"
        elif (q > RANGO_RELOJ[1] and arriba >= 4) or (q < RANGO_RELOJ[0] and abajo >= 4):
            v = "EL RELOJ IMPORTA"
        else:
            v = "SIN DECIDIR"
        return q, arriba, abajo, v

    vl = [D[s]["sens"]["L"] for s in semillas]
    vc = [D[s]["sens"]["C"] for s in semillas]
    q, arriba, abajo, v = veredicto(vl, vc)
    print(f"  A igual generación ({W[0]}-{W[-1]}): larga {st.mean(vl):+.4f}, control {st.mean(vc):+.4f}: q = {q:.2f}; "
          f"la larga arriba en {arriba}, abajo en {abajo} -> {v}")
    vl2 = [sens(D[s]["L_ag"], D[s]["wL"]) for s in semillas]
    vc2 = [sens(D[s]["C_ag"], D[s]["wC"]) for s in semillas]
    q, arriba, abajo, v = veredicto(vl2, vc2)
    print(f"  A igual costo en ticks: larga {st.mean(vl2):+.4f}, control {st.mean(vc2):+.4f}: q = {q:.2f}; la larga "
          f"arriba en {arriba}, abajo en {abajo} -> {v}")
    for s, a, b in zip(semillas, vl2, vc2):
        d = D[s]
        print(f"    s{s}: P = {d['P']:,} ticks; larga gens {d['wL'][0]}-{d['wL'][-1]} {a:+.4f} · "
              f"{comida(d['L_co'], d['wL']):.3f} · {puerta(d['L_co'], d['wL']):.2f} | control gens "
              f"{d['wC'][0]}-{d['wC'][-1]} {b:+.4f} · {comida(d['C_co'], d['wC']):.3f} · {puerta(d['C_co'], d['wC']):.2f}")
    print("  (sensibilidad · manzanas · puerta por generación)")
    print(f"  Promedios a igual costo: manzanas larga {st.mean(comida(D[s]['L_co'], D[s]['wL']) for s in semillas):.3f}, "
          f"control {st.mean(comida(D[s]['C_co'], D[s]['wC']) for s in semillas):.3f}; puerta larga "
          f"{st.mean(puerta(D[s]['L_co'], D[s]['wL']) for s in semillas):.2f}, control "
          f"{st.mean(puerta(D[s]['C_co'], D[s]['wC']) for s in semillas):.2f}")

    # ---------- La selección ----------
    TRAMOS = [t for t in ((1, 30), (16, 30), (31, 60), (61, 90), (91, 120), (121, 150)) if t[1] <= G]
    print("\n### Lo que ve la selección: Spearman (sensibilidad, fitness) por generación; mediana del tramo y por semilla")
    for c in ("L", "C", "B"):
        for a, b in TRAMOS:
            por_s = {s: seleccion(D[s][c + "_ag"], range(a, b + 1)) for s in semillas}
            todos = [r for s in semillas for r in por_s[s]]
            print(f"  {NOMBRES[c]}, gens {a}-{b}: {mediana(todos):+.3f} ({len(todos)}) | "
                  + " ".join(f"s{s} {mediana(por_s[s]):+.2f}" for s in semillas))
    todos = [r for s in semillas for r in seleccion(D[s]["M_ag"], range(16, G_PUB + 1))]
    print(f"  {NOMBRES['M']}, gens 16-{G_PUB}: {mediana(todos):+.3f} ({len(todos)})")

    # ---------- La trayectoria ----------
    print("\n### Cuándo pasa 0,02 para quedarse (media de las gens n − 4 a n, y de las 5 ventanas siguientes)")
    for c in ("L", "C", "B"):  # hasta la G en las tres: el control corrió más
        print(f"  {NOMBRES[c]}, gens 1-{G}: " + ", ".join(
            f"s{s} {cuando_pasa([f for f in D[s][c + '_ag'] if f['gen'] <= G]) or 'nunca'}" for s in semillas))
    VENTANAS = [w for w in ((26, 30), (56, 60), (86, 90), (116, 120), (G - 4, G)) if w[1] <= G]
    VENTANAS = list(dict.fromkeys(VENTANAS))
    print("\n### Por ventana: sensibilidad · manzanas · puerta por generación, promedio de las semillas (y la sensibilidad "
          "por semilla)")
    for c in ("L", "C", "B"):
        partes = []
        for a, b in VENTANAS:
            g = range(a, b + 1)
            partes.append(f"{a}-{b}: {st.mean(sens(D[s][c + '_ag'], g) for s in semillas):+.3f} · "
                          f"{st.mean(comida(D[s][c + '_co'], g) for s in semillas):.2f} · "
                          f"{st.mean(puerta(D[s][c + '_co'], g) for s in semillas):.1f}")
        print(f"  {NOMBRES[c]}: " + " | ".join(partes))
        for s in semillas:
            print(f"    s{s}: " + " ".join(f"{sens(D[s][c + '_ag'], range(a, b + 1)):+.3f}" for a, b in VENTANAS))

    # ---------- La puerta y el resto del puzzle ----------
    print(f"\n### El puzzle, gens 1-{G} (agentes que llegan a cada paso, suma; generaciones con alguno), y la puerta "
          f"sostenida: generaciones con alguien que la abre, desde la {DESDE_PUERTA}")
    for c in ("L", "C", "B"):
        for s in semillas:
            co = [f for f in D[s][c + "_co"] if f["gen"] <= G]
            partes = []
            for k, nombre in (("agentes_puerta_madera", "madera"), ("agentes_llave_dorada", "dorada"),
                              ("agentes_puerta_hierro", "hierro"), ("agentes_cofre", "cofre")):
                partes.append(f"{nombre} {sum(int(f[k]) for f in co)} ({sum(int(f[k]) > 0 for f in co)} gens)")
            sost = [f for f in co if f["gen"] >= DESDE_PUERTA]
            print(f"  {NOMBRES[c]} s{s}: " + ", ".join(partes)
                  + (f" | desde la {DESDE_PUERTA}: {sum(int(f['agentes_puerta_madera']) > 0 for f in sost)} de {len(sost)}"
                     if sost else ""))

    # ---------- Términos del fitness ----------
    TERMINOS = ("f_comida", "f_acercarse", "f_supervivencia", "f_puzzle", "fitness", "edad")
    print(f"\n### Términos del fitness, gens {W[0]}-{W[-1]} (promedio de las filas de agentes, promedio de las semillas)")
    for c in ("L", "C", "B"):
        print(f"  {NOMBRES[c]}: " + " · ".join(
            f"{k[2:] if k.startswith('f_') else k} "
            f"{st.mean(media([float(f[k]) for f in D[s][c + '_ag'] if f['gen'] in set(W)]) for s in semillas):.2f}"
            for k in TERMINOS))

    # ---------- El costo ----------
    print("\n### El costo (ticks simulados)")
    for s in semillas:
        d = D[s]
        lc = [int(f["ticks"]) for f in d["L_co"]]
        cc = [int(f["ticks"]) for f in d["C_co"]]
        bc = [int(f["ticks"]) for f in d["B_co"]]
        print(f"  s{s}: larga {d['TL'][-1]:,} (hasta la 30: {d['TL'][min(29, G - 1)]:,}; la más larga desde la 21, "
              f"{max(lc[20:], default=0):,}; en el límite {sum(t == limite(n) for n, t in enumerate(lc, 1))}) | control "
              f"hasta la {G}: {d['TC'][G - 1]:,}, hasta la {len(cc)}: {d['TC'][-1]:,} (la más larga desde la 21, "
              f"{max(cc[20:G]):,}; en el límite hasta la {G}: "
              f"{sum(t == limite_reloj(n, R) for n, t in enumerate(cc[:G], 1))}) | línea base {d['TB'][-1]:,} "
              f"(en el límite {sum(t == limite(n) for n, t in enumerate(bc, 1))})")

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in semillas:
        d = D[s]
        partes = []
        for c, pub in (("L", "M"), ("B", "MB")):
            iguales_co = sha_prefijo(d[c + "_co_ruta"], G_PUB) == sha(d[pub + "_co_ruta"])
            excl = {"curriculo_hasta", "sb", "gen"}
            comunes = [k for k in d[pub + "_ag"][0] if k in d[c + "_ag"][0] and k not in excl]

            def recorte(filas, sin_aporte_ultima):
                return [{k: ("" if k == "aporte" and sin_aporte_ultima and f["gen"] == G_PUB else f[k]) for k in comunes}
                        for f in filas if f["gen"] <= G_PUB]

            iguales_ag = recorte(d[c + "_ag"], True) == recorte(d[pub + "_ag"], False)
            with open(d[c + "_geo_ruta"], encoding="utf-8") as f1, open(d[pub + "_geo_ruta"], encoding="utf-8") as f2:
                g1 = [r for r in csv.DictReader(f1) if int(r["generacion"]) <= G_PUB]
                g2 = list(csv.DictReader(f2))
            iguales_geo = g1 == g2
            arriba = sum(int(f["ticks"]) > limite(f["gen"]) for f in d[c + "_co"])
            etapa = {f["etapa_inicial"] for f in d[c + "_co"]} | {f["etapa_inicial"] for f in d[c + "_ag"]}
            abrieron = {}
            for a in d[c + "_ag"]:
                abrieron[a["gen"]] = abrieron.get(a["gen"], 0) + int(a["abrio"])
            abrio = sum(int(f["agentes_puerta_madera"]) != abrieron.get(f["gen"], 0) for f in d[c + "_co"])
            e = (not iguales_co) + (not iguales_ag) + (not iguales_geo) + arriba + (etapa != {"1"}) + abrio
            errores += e
            partes.append(f"{NOMBRES[c]}: corrida 1-{G_PUB} = publicada {iguales_co} (SHA-256 publicado "
                          f"{sha(d[pub + '_co_ruta'])[:12]}…), agentes {iguales_ag}, geometría {iguales_geo}; arriba del "
                          f"límite {arriba}; etapa inicial {sorted(etapa)}; puerta distinta de abrio en {abrio}")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
