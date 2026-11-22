"""El costo de golpear en 0,01, sin la llave dada (docs/qa/AnalisisQA.md#costo-chico-comida20, el experimento (a)), a partir
de los CSV de medir_puerta.py con sens-golpe: la referencia con HIT_ENERGY_COST en 0,01 (N1) contra la referencia (N, con
costo 0,05), sin costo (N0) y la línea base sin evolución de la referencia (NB); la larga (L), de referencia.

Con la cuenta de analizar_costo_golpe.py (S, G, P pegado y P lejos por fila de agente con ticks en la etapa 1, divididas por
sens_ticks, promedio de las filas de la ventana; ΔS y ΔG desde el corte, gens 26-30; "En la puerta", con la función de
analizar_golpe.py) y la de analizar_comida.py (la sensibilidad a la comida antes de abrir la puerta).

Uso: python mediciones/analizar_costo_chico.py CHICO PUBLICADA SIN_COSTO LINEA_BASE
CHICO tiene los CSV y los logs de N1; PUBLICADA, los de N y L con sens-golpe (results/medicion_golpe_20261121); SIN_COSTO, los
de N0 (results/medicion_costo_golpe_20261121); LINEA_BASE, los de NB (results/medicion_sin_llave_20261120). Con CHICO igual a
PUBLICADA, N1 es N: la prueba del script, que tiene que dar los números de N (S +0,089 · G −1,221 · P pegado 0,117 · P lejos
0,055; la puerta 2,48; "En la puerta": llegan el 41% y golpean el 23%), las diferencias con N en 0 y 0 errores.
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
CORTE = cg.CORTE       # gens 26-30, la última ventana con la llave dada
SUFIJO = "-HIT_ENERGY_COST0.01"
COSTO = 0.01
C = ("N1", "N", "N0", "L")
NOM = dict(N1="Costo 0,01 (N1)", N="Referencia, costo 0,05 (N)", N0="Sin costo (N0)", L="Larga (L)",
           NB="Línea base (NB)")


def con_comida(d):
    """Suma a cada fila de agente la sensibilidad a la comida antes de abrir la puerta (sc), la cuenta de analizar_comida.py."""
    for f in d["ag"]:
        t1, t0 = int(f.get("sens_ticks") or 0), int(f.get("sens_ticks0") or 0)
        c1, c0 = float(f.get("sens_comida") or 0), float(f.get("sens_comida0") or 0)
        f["sc"] = (c1 + c0) / (t1 + t0) if t1 + t0 else None
    return d


def cargar(rutas):
    for r in rutas:
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    filas = sl.leer(rutas[1])
    for f in filas:
        f["m1"], f["m0"] = ag.medidas(f, ""), ag.medidas(f, "0")
    return con_comida(dict(co=sl.leer(rutas[0]), ag=filas, rutas=rutas))


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    chico, publicada, sin_costo, linea_base = sys.argv[1:5]
    prueba = os.path.samefile(chico, publicada)  # N1 es N: la prueba del script
    suf = "" if prueba else SUFIJO
    D = {}
    for s in SEMILLAS:
        n1 = cg.nombre(s, 30).replace("_evolucion.csv", suf + "_evolucion.csv")
        nb = al.uno(os.path.join(linea_base, f"corrida_s{s}_*moviles_curriculo30_sin_evolucion.csv"))
        D[s] = dict(N1=cargar([os.path.join(chico, t + n1) for t in ("corrida_", "agentes_")]),
                    N=con_comida(cg.cargar(publicada, s, 30)), L=con_comida(cg.cargar(publicada, s, 150)),
                    N0=con_comida(cg.cargar(sin_costo, s, 30, costo0=True)), NB=dict(co=sl.leer(nb), rutas=(nb,)))
    G = max(f["gen"] for f in D[1]["N1"]["ag"])
    W = range(G - 4, G + 1)
    print(f"El costo de golpear en 0,01, sin la llave dada: semillas {list(SEMILLAS)}, {G} generaciones"
          f"{' (PRUEBA: N1 es N)' if prueba else ''}; pesos de N1: {D[1]['N1']['ag'][0]['pesos']}; currículo N1 "
          f"{D[1]['N1']['ag'][0]['curriculo_hasta']}")

    def v(s, c, k, gens=W, et="m1"):
        return ag.val(D[s][c]["ag"], gens, k, et)

    def pu(s, c, gens=W):
        return al.puerta(D[s][c]["co"], gens)

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    dG = {c: {s: v(s, c, "G") - v(s, c, "G", CORTE) for s in SEMILLAS} for c in C}
    dS = {c: {s: v(s, c, "S") - v(s, c, "S", CORTE) for s in SEMILLAS} for c in C}
    puerta = {c: {s: pu(s, c) for s in SEMILLAS} for c in C + ("NB",)}
    pl = {c: {s: v(s, c, "Pl") for s in SEMILLAS} for c in C}

    print(f"\n### Gens {W[0]}-{W[-1]}, etapa 1: la puerta por generación · G en el corte (26-30) → al final (ΔG) · S en el "
          f"corte → al final (ΔS) · P pegado · P lejos (filas medidas)")
    for c in C:
        for s in SEMILLAS:
            print(f"  {NOM[c]} s{s}: {puerta[c][s]:.1f} · G {v(s, c, 'G', CORTE):+.3f} → {v(s, c, 'G'):+.3f} "
                  f"({dG[c][s]:+.3f}) · S {v(s, c, 'S', CORTE):+.3f} → {v(s, c, 'S'):+.3f} ({dS[c][s]:+.3f}) · "
                  f"{v(s, c, 'Pp'):.3f} · {pl[c][s]:.3f} ({ag.filas_medidas(D[s][c]['ag'], W)})")
        print(f"  {NOM[c]}, promedio: {st.mean(puerta[c].values()):.2f} · G {prom(lambda s: v(s, c, 'G', CORTE)):+.3f} → "
              f"{prom(lambda s: v(s, c, 'G')):+.3f} ({st.mean(dG[c].values()):+.3f}) · S "
              f"{prom(lambda s: v(s, c, 'S', CORTE)):+.3f} → {prom(lambda s: v(s, c, 'S')):+.3f} "
              f"({st.mean(dS[c].values()):+.3f}) · {prom(lambda s: v(s, c, 'Pp')):.3f} · {st.mean(pl[c].values()):.3f}")
    print(f"  {NOM['NB']}, la puerta: " + " · ".join(f"s{s} {puerta['NB'][s]:.1f}" for s in SEMILLAS)
          + "; la llave roja: " + " · ".join(f"s{s} {sl.llave(D[s]['NB']['co'], W):.1f}" for s in SEMILLAS))

    # ---------- Criterio ----------
    print("\n### Criterio (fijado antes de correr; por semilla)")
    k1 = sum(puerta["N1"][s] >= al.PUERTA and puerta["N1"][s] > puerta["NB"][s] for s in SEMILLAS)
    c1 = k1 >= 4
    tope = {s: sl.llave(D[s]["NB"]["co"], W) for s in SEMILLAS}
    entre = [s for s in SEMILLAS if al.PUERTA <= puerta["N1"][s] <= tope[s]]
    print(f"  1. Pasa la puerta: N1 ≥ {al.PUERTA:g} por generación y más que NB en {k1} de 5 (pide 4); promedio "
          f"{st.mean(puerta['N1'].values()):.2f} (N {st.mean(puerta['N'].values()):.2f}, N0 "
          f"{st.mean(puerta['N0'].values()):.2f}); semillas entre 1 y lo que NB tiene con la llave: {entre or 'ninguna'} "
          f"-> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    s1, sN, sL = (st.mean(dS[c].values()) for c in ("N1", "N", "L"))
    umbral2 = sN + cg.TERCIO * (sL - sN)
    k2 = sum(dS["N1"][s] > dS["N"][s] for s in SEMILLAS)
    c2 = k2 >= 4 and s1 >= umbral2
    print(f"  2. Golpean en la puerta: ΔS de N1 > el de N en {k2} de 5 (pide 4); promedio {s1:+.3f} contra {sN:+.3f} (la larga "
          f"{sL:+.3f}; pide al menos {umbral2:+.3f}) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    p1, pL = st.mean(pl["N1"].values()), st.mean(pl["L"].values())
    k3 = sum(pl["N1"][s] < pl["N0"][s] for s in SEMILLAS)
    c3 = k3 >= 4 and p1 <= pL
    print(f"  3. No golpean en todos lados: P lejos de N1 {p1:.3f} (pide a lo sumo el de la larga, {pL:.3f}; N0 "
          f"{st.mean(pl['N0'].values()):.3f}, N {st.mean(pl['N'].values()):.3f}); menor que el de N0 en {k3} de 5 (pide 4) "
          f"-> {'CUMPLE' if c3 else 'NO CUMPLE'}")
    if not c1:
        veredicto = "con 0,01 la puerta no pasa"
    elif not c3:
        veredicto = "pasa la puerta, pero golpean en todos lados, como sin costo"
    elif c2:
        veredicto = "con costo 0,01 pasa la puerta, golpeando en la puerta: la candidata a referencia"
    else:
        veredicto = "pasa la puerta sin golpear en todos lados, pero sin condicionar el golpe"
    print(f"  Veredicto: {veredicto}")
    g1, gN = st.mean(dG["N1"].values()), st.mean(dG["N"].values())
    kg = sum(dG["N1"][s] > dG["N"][s] for s in SEMILLAS)
    print(f"  Se lee con ΔG (el criterio 2 de #costo-golpe): ΔG de N1 > el de N en {kg} de 5 (pide 4); promedio {g1:+.3f} "
          f"contra {gN:+.3f} (pide al menos {cg.TERCIO * gN:+.3f}) -> "
          f"{'el golpe en general no cae' if kg >= 4 and g1 >= cg.TERCIO * gN else 'el golpe en general cae'}")
    print(f"  P pegado − P lejos (el golpe condicionado en decisiones): " + " · ".join(
        f"{c} {prom(lambda s: v(s, c, 'Pp') - v(s, c, 'Pl')):+.3f}" for c in C))

    # ---------- Por ventana ----------
    print("\n### Por ventana, etapa 1 (promedio de las semillas): S · G · P lejos · la puerta por generación")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: " + " · ".join(f"{prom(lambda s: v(s, c, k, range(a, b + 1))):{'+.2f' if k in 'SG' else '.2f'}}"
                                      for k in ("S", "G", "Pl"))
            + f" · {prom(lambda s: pu(s, c, range(a, b + 1))):.1f}" for a, b in ag.VENTANAS))
    for k in ("S", "G", "Pl"):
        print(f"    {NOM['N1']}, {k}: " + " | ".join(
            f"s{s} " + " ".join(f"{v(s, 'N1', k, range(a, b + 1)):+.2f}" for a, b in ag.VENTANAS) for s in SEMILLAS))
    print(f"    {NOM['N1']}, la puerta: " + " | ".join(
        f"s{s} " + " ".join(f"{pu(s, 'N1', range(a, b + 1)):.1f}" for a, b in ag.VENTANAS) for s in SEMILLAS))

    # ---------- En la puerta ----------
    ag.NOMBRES.update(N=NOM["N1"], L=NOM["N"])  # la función de analizar_golpe.py: N1 en el lugar de N y N en el de L
    ag.en_la_puerta({s: dict(N_ag=D[s]["N1"]["ag"], L_ag=D[s]["N"]["ag"]) for s in SEMILLAS}, SEMILLAS, W)
    ag.NOMBRES.update(N=NOM["N0"], L=NOM["L"])
    ag.en_la_puerta({s: dict(N_ag=D[s]["N0"]["ag"], L_ag=D[s]["L"]["ag"]) for s in SEMILLAS}, SEMILLAS, W)

    # ---------- La etapa 0, la gen 1 ----------
    print("\n### La etapa 0 (hacia la llave): S · G · P lejos por ventana, promedio de las semillas")
    for c in ("N1", "N", "N0"):
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: " + " · ".join(f"{prom(lambda s: v(s, c, k, range(a, b + 1), 'm0')):+.3f}" for k in ("S", "G", "Pl"))
            for a, b in ag.VENTANAS[1:]))
    print("\n### Gen 1 (la población inicial): S · G · P pegado · P lejos, promedio de las semillas")
    for c in ("N1", "N", "N0"):
        print(f"  {NOM[c]}: " + " · ".join(f"{prom(lambda s: v(s, c, k, [1])):+.3f}" for k in ("S", "G", "Pp", "Pl")))

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio, gens {W[0]}-{W[-1]}: llave roja por generación · manzanas · sensibilidad a la brújula · "
          f"sensibilidad a la comida (las dos antes de abrir la puerta) · edad; y en las 31-{G}: llave dorada · puerta de "
          f"hierro · cofre (sumados)")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"s{s} {sl.llave(D[s][c]['co'], W):.1f} · {al.comida(D[s][c]['co'], W):.3f} · {sl.val(D[s][c]['ag'], W):+.4f} · "
            f"{sl.val(D[s][c]['ag'], W, 'sc'):+.4f} · {sl.columna(D[s][c]['co'], W, 'edad_prom'):.0f}; "
            + " · ".join(str(sum(int(f[k]) for f in D[s][c]["co"] if f["gen"] > 30))
                         for k in ("agentes_llave_dorada", "agentes_puerta_hierro", "agentes_cofre")) for s in SEMILLAS))
        print(f"    promedio: {prom(lambda s: sl.llave(D[s][c]['co'], W)):.1f} · {prom(lambda s: al.comida(D[s][c]['co'], W)):.3f}"
              f" · {prom(lambda s: sl.val(D[s][c]['ag'], W)):+.4f} · {prom(lambda s: sl.val(D[s][c]['ag'], W, 'sc')):+.4f} · "
              f"{prom(lambda s: sl.columna(D[s][c]['co'], W, 'edad_prom')):.0f}; sumados: " + " · ".join(
                  str(sum(int(f[k]) for s in SEMILLAS for f in D[s][c]["co"] if f["gen"] > 30))
                  for k in ("agentes_llave_dorada", "agentes_puerta_hierro", "agentes_cofre")))

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in SEMILLAS:
        d, partes = D[s]["N1"], []
        for c, sha in (("N", cg.SHA_N[s]), ("N0", ac.SHA["N0"][s])):
            igual = (al.sha(D[s][c]["rutas"][0]), al.sha(D[s][c]["rutas"][1])) == sha
            errores += not igual
            partes.append(f"{c} SHA-256 publicado {igual}")
        igual = al.sha(D[s]["NB"]["rutas"][0]) == ac.SHA["NB"][s][0]
        errores += not igual
        partes.append(f"NB (corrida) SHA-256 publicado {igual}")
        etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["ag"])
        e0 = sum(any(float(f[k]) != 0 for k in ag.NUEVAS[4:]) for f in d["ag"] if f["gen"] <= 30)
        sin_ticks = sum(any(float(f[k]) != 0 for k in ag.NUEVAS[:4]) for f in d["ag"] if int(f["sens_ticks"]) == 0)
        errores += etapa + e0 + sin_ticks + (len(d["ag"]) != 60 * G)
        partes.append(f"N1: filas {len(d['ag'])}, etapa_inicial distinta de 1/0 {etapa}, etapa 0 distinta de 0 en las 1-30 "
                      f"{e0}, filas sin ticks con valor {sin_ticks}")
        if not prueba:
            gen1 = d["co"][0] != D[s]["N"]["co"][0]
            pesos = all(f["pesos"].endswith(",HIT_ENERGY_COST:0.01") for f in d["ag"])
            with open(os.path.join(chico, f"log_s{s}_costo001.txt"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            e = re.search(r"^ENERGIA_GOLPE golpeando: (\d+) ticks, (-?[\d.]+) por tick \| sin golpear: (\d+) ticks, "
                          r"(-?[\d.]+) por tick \(HIT_ENERGY_COST=0\.01\)$", log, re.M)
            en_log = ("'HIT_ENERGY_COST': 0.01}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
                      and "CROSSOVER_RATE=0.2\n" in log)
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            energia = (bool(e) and int(e.group(1)) > 0 and abs(float(e.group(2)) - COSTO) < 1e-6
                       and abs(float(e.group(4))) < 1e-6)
            errores += (not gen1) + (not pesos) + (not en_log) + (medicion != [("0", str(60 * G))]) + (not energia)
            golpeando = f"{int(e.group(1)) / (int(e.group(1)) + int(e.group(3))):.0%}" if e else "-"
            partes.append(f"gen 1 distinta de N {gen1}; pesos con HIT_ENERGY_COST:0.01 {pesos}; log (pesos, currículo, "
                          f"cruce) {en_log}; MEDICION {medicion}; ENERGIA_GOLPE {e.groups() if e else None} -> {energia} "
                          f"(golpeando el {golpeando} de los ticks medidos)")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
