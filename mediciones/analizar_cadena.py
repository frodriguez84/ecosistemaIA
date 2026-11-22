"""Los pasos 3 a 6 en la referencia sin costo, contra su línea base sin costo (docs/qa/AnalisisQA.md#cadena-sin-costo), a
partir de los CSV de medir_puerta.py: la referencia vigente, sin costo de golpear (N0, con evolución), contra su línea base
sin evolución sin costo (NB0); la línea base publicada, con costo (NB), sin criterio.

Por paso (3, la puerta de madera; 4, la llave dorada; 5, la puerta de hierro; 6, el cofre), la columna agentes_* del
corrida_*.csv, promedio por generación de las gens 146-150, y por 1.000 px (dividida por distancia_prom × 1.000, la cuenta
de la llave roja de analizar_sin_llave.py). El criterio, la decisión 5 del spec PUZZLE_SOLOS: en 4 de 5 semillas, N0 con
al menos 1 por generación y más que NB0 de la misma semilla. "En la puerta", con las definiciones de analizar_golpe.py (los
que tienen la llave, etapa ≥ 1; llegan, ticks_25 > 0; golpean ahí, ticks_golpe_25 > 0; la abren, abrio), escrita acá para
que no se caiga si en una línea base nadie llega.

Uso: python mediciones/analizar_cadena.py REFERENCIA LINEA_BASE PUBLICADA
REFERENCIA tiene los CSV de N0 (results/medicion_costo_golpe_20261121); LINEA_BASE, los CSV y los logs de NB0; PUBLICADA, los
de la referencia con costo (N) y su línea base (NB) (results/medicion_sin_llave_20261120). Con LINEA_BASE igual a PUBLICADA,
NB0 es NB: la prueba del script, que tiene que dar lo publicado (lo controla solo, en PUBLICADO) y 0 errores.
"""
import os
import re
import statistics as st
import sys

import analizar_comida as ac
import analizar_costo_golpe as cg
import analizar_golpe as ag
import analizar_largas as al
import analizar_sin_llave as sl

SEMILLAS = (1, 2, 3, 4, 5)
MINIMO = 1.0  # agentes por generación que dan el paso (el tamaño mínimo de la decisión 5)
PASOS = (("agentes_llave_roja", 1, "llave roja"), ("agentes_puerta_madera", 2, "puerta de madera"),
         ("agentes_llave_dorada", 3, "llave dorada"), ("agentes_puerta_hierro", 4, "puerta de hierro"),
         ("agentes_cofre", 5, "cofre"))
CRITERIO = PASOS[1:]  # los pasos 3 a 6 del spec (el paso 2, la llave roja, se informa)
NOM = dict(N0="Referencia sin costo (N0)", NB0="Línea base sin costo (NB0)", NB="Línea base con costo (NB)")
NB0_NOMBRE = "s{s}_acercarse_deslizar_moviles_curriculo30_pesos-ACERCARSE40-EXPLORATION0-ANTI_CIRCLE0-HIT_ENERGY_COST0_sin_evolucion.csv"
NB_NOMBRE = "s{s}_acercarse_deslizar_moviles_curriculo30_sin_evolucion.csv"
FITNESS = ("fitness_prom", "fitness_max", "fitness_min", "fitness_desvio")
# Lo publicado (#costo-golpe, #sin-la-llave-dada): la puerta de N0 en las 146-150; la cadena de N0 y de NB en las 31-150; la
# llave roja de NB en las 146-150 (por generación y por 1.000 px); "En la puerta" de N0 (llegan, golpean, la abren)
PUBLICADO = dict(puerta_N0=(9.8, 10.2, 3.2, 6.0, 8.8),
                 cadena_N0=dict(agentes_llave_dorada=(575, 317, 11, 290, 863), agentes_puerta_hierro=(4, 0, 1, 6, 10),
                                agentes_cofre=(3, 0, 0, 4, 0)),
                 cadena_NB=dict(agentes_llave_dorada=(0, 0, 0, 1, 0), agentes_puerta_hierro=(0,) * 5,
                                agentes_cofre=(0,) * 5),
                 llave_NB=(1.16, 3.6), puerta_en_N0=("29%", "83%", "61%"))


def cargar(rutas):
    for r in rutas:
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    filas = sl.leer(rutas[1])
    for f in filas:
        f["m1"], f["m0"] = ag.medidas(f, ""), ag.medidas(f, "0")
    return dict(co=al.leer(rutas[0]), ag=filas, rutas=rutas)


def paso(co, gens, col):
    return sl.columna(co, gens, col)


def px(co, gens, col):
    d = sl.columna(co, gens, "distancia_prom")
    return paso(co, gens, col) / d * 1000 if d else float("nan")


def suma(co, gens, col):
    gens = set(gens)
    return sum(int(f[col]) for f in co if f["gen"] in gens)


def pct(a, b):
    return f"{a / b:.0%}" if b else "-"


def en_la_puerta(filas, gens):
    """Los que tienen la llave en gens; de ellos, los que llegan a 25 px; de esos, los que golpean ahí y los que la abren."""
    gens = set(gens)
    F = [f for f in filas if f["gen"] in gens and int(f["etapa"]) >= 1]
    L = [f for f in F if int(f["ticks_25"]) > 0]
    return len(F), len(L), sum(int(f["ticks_golpe_25"]) > 0 for f in L), sum(int(f["abrio"]) for f in L)


def energia(log):
    """La línea ENERGIA_GOLPE de medir_puerta.py: ticks golpeando, por tick, ticks sin golpear, por tick, el costo."""
    e = re.search(r"^ENERGIA_GOLPE golpeando: (\d+) ticks, (-?[\d.]+) por tick \| sin golpear: (\d+) ticks, "
                  r"(-?[\d.]+) por tick \(HIT_ENERGY_COST=([\d.]+)\)$", log, re.M)
    return e.groups() if e else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    referencia, linea_base, publicada = sys.argv[1:4]
    prueba = os.path.samefile(linea_base, publicada)  # NB0 es NB: la prueba del script
    D = {}
    for s in SEMILLAS:
        nb0 = (NB_NOMBRE if prueba else NB0_NOMBRE).format(s=s)
        D[s] = dict(N0=cg.cargar(referencia, s, 30, costo0=True),
                    NB0=cargar([os.path.join(linea_base, t + nb0) for t in ("corrida_", "agentes_")]),
                    NB=cargar([os.path.join(publicada, t + NB_NOMBRE.format(s=s)) for t in ("corrida_", "agentes_")]),
                    N=dict(co=al.leer(os.path.join(publicada, "corrida_" + cg.nombre(s, 30)))))
    G = max(f["gen"] for f in D[1]["N0"]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    print(f"Los pasos 3 a 6 en la referencia sin costo: semillas {list(SEMILLAS)}, {G} generaciones"
          f"{' (PRUEBA: NB0 es NB)' if prueba else ''}; pesos de N0: {D[1]['N0']['ag'][0]['pesos']}; de NB0: "
          f"{D[1]['NB0']['ag'][0]['pesos']}")

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    errores = 0

    # ---------- El criterio ----------
    print(f"\n### Gens {W[0]}-{W[-1]}: agentes por generación que dan el paso (entre paréntesis, por 1.000 px)")
    veredictos = {}
    for col, _, nombre in PASOS:
        v = {c: {s: paso(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        p = {c: {s: px(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        print(f"  {nombre}:")
        for c in NOM:
            print(f"    {NOM[c]}: " + " · ".join(f"s{s} {v[c][s]:.1f} ({p[c][s]:.2f})" for s in SEMILLAS)
                  + f" | promedio {st.mean(v[c].values()):.2f} ({st.mean(p[c].values()):.2f})")
        pasan = [s for s in SEMILLAS if v["N0"][s] >= MINIMO and v["N0"][s] > v["NB0"][s]]
        cumple = len(pasan) >= 4
        q = " · ".join(f"s{s} {p['N0'][s] / p['NB0'][s]:.1f}" if p["NB0"][s] else f"s{s} NB0 en 0" for s in pasan)
        acomp_px = all(p["N0"][s] > p["NB0"][s] for s in pasan) if pasan else False
        ceros = bool(pasan) and all(v["NB0"][s] == 0 for s in pasan)
        print(f"    -> N0 ≥ {MINIMO:g} por generación y más que NB0 en {len(pasan)} de 5 (semillas {pasan}; pide 4): "
              f"{'PASA' if cumple else 'NO PASA'}; por 1.000 px, N0 / NB0 en las que pasan: {q or '-'}"
              f"{' (NB0 da 0 en todas: no agrega)' if ceros else ''}; N0 arriba en todas {acomp_px}")
        veredictos[nombre] = (cumple, len(pasan), acomp_px)

    # ---------- En la puerta ----------
    print(f"\n### En la puerta, gens {W[0]}-{W[-1]}, todas las semillas: con la llave por generación · llegan a 25 px · de "
          f"los que llegan, golpean ahí · la abren")
    puerta_en = {}
    for c in NOM:
        tot = [sum(x) for x in zip(*(en_la_puerta(D[s][c]["ag"], W) for s in SEMILLAS))]
        F, L, gl, ab = tot
        puerta_en[c] = (pct(L, F), pct(gl, L), pct(ab, L), ab / L if L else None)
        print(f"  {NOM[c]}: {F / (len(W) * len(SEMILLAS)):.1f}/gen · llegan {pct(L, F)} ({L}) · golpean {pct(gl, L)} ({gl}) "
              f"· la abren {pct(ab, L)} ({ab})")
        print("    por semilla (llegan / golpean / la abren): " + " | ".join(
            f"s{s} {x[1]}/{x[2]}/{x[3]}" for s in SEMILLAS for x in [en_la_puerta(D[s][c]["ag"], W)]))
    a0, ab0 = puerta_en["N0"][3], puerta_en["NB0"][3]
    print(f"  -> la parte que la abre, más alta en N0 que en NB0: "
          f"{a0 is not None and (ab0 is None or a0 > ab0)} (N0 {puerta_en['N0'][2]}, NB0 {puerta_en['NB0'][2]})")
    print(f"  P pegado · P lejos (la red, etapa 1; gen 1 y gens {W[0]}-{W[-1]}), promedio de las semillas:")
    for c in NOM:
        print(f"    {NOM[c]}: gen 1 " + " · ".join(f"{prom(lambda s: ag.val(D[s][c]['ag'], [1], k)):.3f}" for k in ("Pp", "Pl"))
              + f" | {W[0]}-{W[-1]} " + " · ".join(f"{prom(lambda s: ag.val(D[s][c]['ag'], W, k)):.3f}" for k in ("Pp", "Pl"))
              + " | etapa 0, " + " · ".join(f"{prom(lambda s: ag.val(D[s][c]['ag'], W, k, 'm0')):.3f}" for k in ("Pp", "Pl")))

    # ---------- Por ventana ----------
    print("\n### Por ventana: agentes por generación que dan el paso, promedio de las semillas")
    for col, _, nombre in CRITERIO:
        for c in ("N0", "NB0"):
            print(f"  {nombre}, {NOM[c]}: " + " | ".join(
                f"{a}-{b} {prom(lambda s: paso(D[s][c]['co'], range(a, b + 1), col)):.2f}" for a, b in ag.VENTANAS))
        print(f"    N0 por semilla: " + " | ".join(
            f"s{s} " + " ".join(f"{paso(D[s]['N0']['co'], range(a, b + 1), col):.1f}" for a, b in ag.VENTANAS)
            for s in SEMILLAS))
        k = {c: sum(paso(D[s]["N0"]["co"], range(a, b + 1), col) >= MINIMO
                    and paso(D[s]["N0"]["co"], range(a, b + 1), col) > paso(D[s]["NB0"]["co"], range(a, b + 1), col)
                    for s in SEMILLAS) for c, (a, b) in zip(("116-120", "146-150"), ag.VENTANAS[-2:])}
        print(f"    el criterio en las 116-120: {k['116-120']} de 5; en las 146-150: {k['146-150']} de 5")

    # ---------- El embudo ----------
    print(f"\n### El embudo: agentes que dan cada paso, sumados (las 5 semillas), y entre paréntesis la parte de los del paso "
          f"anterior")
    for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
        for c in NOM:
            t = [sum(suma(D[s][c]["co"], gens, col) for s in SEMILLAS) for col, _, _ in PASOS]
            print(f"  {rotulo}, {NOM[c]}: " + " → ".join(
                f"{nombre} {n}" + (f" ({pct(n, t[i - 1])})" if i else "") for i, (n, (_, _, nombre)) in enumerate(zip(t, PASOS))))
    print(f"  por semilla, 31-{G}, N0: " + " | ".join(
        f"s{s} " + " · ".join(str(suma(D[s]["N0"]["co"], DESDE, col)) for col, _, _ in PASOS) for s in SEMILLAS))
    print(f"  por semilla, 31-{G}, NB0: " + " | ".join(
        f"s{s} " + " · ".join(str(suma(D[s]["NB0"]["co"], DESDE, col)) for col, _, _ in PASOS) for s in SEMILLAS))

    # ---------- NB0 contra NB ----------
    print(f"\n### Sin criterio, gens {W[0]}-{W[-1]}: llave roja · puerta de madera por generación · edad promedio · manzanas")
    for c in NOM:
        print(f"  {NOM[c]}: " + " | ".join(
            f"s{s} {paso(D[s][c]['co'], W, 'agentes_llave_roja'):.1f} · {paso(D[s][c]['co'], W, 'agentes_puerta_madera'):.1f}"
            f" · {sl.columna(D[s][c]['co'], W, 'edad_prom'):.0f} · {al.comida(D[s][c]['co'], W):.3f}" for s in SEMILLAS)
            + f" | promedio {prom(lambda s: paso(D[s][c]['co'], W, 'agentes_llave_roja')):.2f} · "
              f"{prom(lambda s: paso(D[s][c]['co'], W, 'agentes_puerta_madera')):.2f} · "
              f"{prom(lambda s: sl.columna(D[s][c]['co'], W, 'edad_prom')):.0f} · {prom(lambda s: al.comida(D[s][c]['co'], W)):.3f}")

    # ---------- Controles ----------
    print("\n### Controles")
    for s in SEMILLAS:
        partes = []
        for c, rutas in (("N0", D[s]["N0"]["rutas"]), ("NB", D[s]["NB"]["rutas"])):
            igual = (al.sha(rutas[0]), al.sha(rutas[1])) == ac.SHA[c][s]
            errores += not igual
            partes.append(f"{c} SHA-256 publicado {igual}")
        n_igual = al.sha(os.path.join(publicada, "corrida_" + cg.nombre(s, 30))) == ac.SHA["N"][s][0]
        errores += not n_igual
        partes.append(f"N (corrida) SHA-256 publicado {n_igual}")
        # La gen 1: NB0 es N0 salvo evolucion; en la prueba, NB es N salvo evolucion y el fitness (NB no lleva los pesos)
        a, b = (D[s]["NB0"]["co"][0], D[s]["N"]["co"][0] if prueba else D[s]["N0"]["co"][0])
        fuera = {"evolucion", "gen", "sb"} | (set(FITNESS) if prueba else set())
        dif = [k for k in a if k not in fuera and a[k] != b[k]]
        errores += bool(dif) or a["evolucion"] == b["evolucion"]
        partes.append(f"gen 1 de NB0 = la de {'N' if prueba else 'N0'} salvo {sorted(fuera - {'gen', 'sb'})}: "
                      f"{'sí' if not dif else dif}")
        for c in ("N0", "NB0"):
            d = D[s][c]
            filas = len(d["ag"]) == 60 * G and len(d["co"]) == G
            etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["co"] + d["ag"])
            pasos = 0
            for f in d["co"]:
                filas_g = [x for x in d["ag"] if x["gen"] == f["gen"]]
                pasos += int(f["agentes_puerta_madera"]) != sum(int(x["abrio"]) for x in filas_g)
                pasos += sum(int(f[col]) != sum(int(x["etapa"]) >= e for x in filas_g) for col, e, _ in PASOS)
            errores += (not filas) + etapa + pasos
            partes.append(f"{c}: filas {filas}, etapa_inicial distinta de 1/0 {etapa}, agentes_* distintos de abrio y "
                          f"etapa {pasos}")
        if not prueba:
            pesos = all(f["pesos"].endswith(",HIT_ENERGY_COST:0") for f in D[s]["NB0"]["ag"])
            with open(os.path.join(linea_base, f"log_s{s}.txt"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            en_log = "'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            e = energia(log)
            costo0 = (bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6
                      and float(e[4]) == 0)
            errores += (not pesos) + (not en_log) + (medicion != [("0", str(60 * G))]) + (not costo0)
            golpea = f"{int(e[0]) / (int(e[0]) + int(e[2])):.0%}" if e else "-"
            partes.append(f"NB0: pesos con HIT_ENERGY_COST:0 {pesos}; log (pesos, currículo) {en_log}; MEDICION {medicion}; "
                          f"ENERGIA_GOLPE {e} -> {costo0} (golpeando el {golpea} de los ticks contados)")
        print(f"  s{s}: " + " | ".join(partes))
    # Lo publicado: N0 siempre (es la misma corrida); NB, en la prueba
    chequeos = [("la puerta de N0, 146-150",
                 tuple(round(paso(D[s]["N0"]["co"], W, "agentes_puerta_madera"), 1) for s in SEMILLAS),
                 PUBLICADO["puerta_N0"]),
                ("En la puerta de N0", puerta_en["N0"][:3], PUBLICADO["puerta_en_N0"])]
    chequeos += [(f"{col} de N0, 31-{G}", tuple(suma(D[s]["N0"]["co"], DESDE, col) for s in SEMILLAS), v)
                 for col, v in PUBLICADO["cadena_N0"].items()]
    if prueba:
        chequeos += [(f"{col} de NB, 31-{G}", tuple(suma(D[s]["NB0"]["co"], DESDE, col) for s in SEMILLAS), v)
                     for col, v in PUBLICADO["cadena_NB"].items()]
        chequeos.append(("la llave roja de NB, 146-150 (por generación, por 1.000 px)",
                         (round(prom(lambda s: paso(D[s]["NB0"]["co"], W, "agentes_llave_roja")), 2),
                          round(prom(lambda s: px(D[s]["NB0"]["co"], W, "agentes_llave_roja")), 1)),
                         PUBLICADO["llave_NB"]))
    for nombre, dio, pub in chequeos:
        errores += tuple(dio) != tuple(pub)
        print(f"  publicado, {nombre}: {dio} (publicado {pub}) {tuple(dio) == tuple(pub)}")
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
