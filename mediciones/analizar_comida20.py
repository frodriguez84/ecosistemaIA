"""La comida al doble en el fitness (docs/qa/AnalisisQA.md#costo-chico-comida20, el experimento (b)), a partir de los CSV de
medir_puerta.py con sens-golpe: la referencia con FITNESS_FOOD en 20 (NF) contra la línea base sin evolución de la referencia
(NB; sin evolución, los pesos del fitness no cambian lo que hacen), con la decisión 6 de docs/specs/active/PUZZLE_SOLOS.md, y
contra la referencia (N), que la llave roja y la puerta no caigan.

Con la cuenta de analizar_comida.py: la sensibilidad a la comida antes de abrir la puerta ((sens_comida + sens_comida0) /
(sens_ticks + sens_ticks0) por fila, promedio de las filas de la ventana) y, dentro de cada generación con 10 agentes medidos
o más, el Spearman entre la sensibilidad y las manzanas de cada agente (y el fitness), mediana del tramo. Las manzanas de cada
agente salen de f_comida = FITNESS_FOOD × √manzanas, con el FITNESS_FOOD de la columna pesos (sin él, el de config.py, 10).

Uso: python mediciones/analizar_comida20.py COMIDA20 PUBLICADA REFERENCIA
COMIDA20 tiene los CSV y los logs de NF; PUBLICADA, los de N con sens-golpe (results/medicion_golpe_20261121); REFERENCIA, los
de NB (results/medicion_sin_llave_20261120). Con COMIDA20 igual a PUBLICADA, NF es N: la prueba del script, que tiene que dar
los números de N (la sensibilidad a la comida +0,0138 con 3 de 5; el Spearman con las manzanas en las 121-150, +0,102 contra
+0,041), las diferencias con N en 0 y 0 errores.
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

SEMILLAS = ac.SEMILLAS
SUFIJO = "-FOOD20"
PESO = 20.0
LLAVE = 0.90           # la guarda de la llave roja: el promedio de NF, al menos el 90% del de N
MITAD = 0.5            # la guarda de la puerta: el promedio de NF, al menos la mitad del de N
TRAMO = range(121, 151)  # la medida independiente: el Spearman con las manzanas, mediana de estas generaciones
C = ("NF", "N", "NB")
NOM = dict(NF="Comida 20 (NF)", N="Referencia (N)", NB="Línea base (NB)")
IGUALES_GEN1 = ("fitness", "lugar", "en_pool", "elite", "aporte", "f_supervivencia", "f_comida", "f_exploracion",
                "f_anticirculo", "f_puzzle", "f_acercarse", "f_agua", "pesos")  # lo que el fitness cambia: se excluye


def peso_comida(f):
    m = re.search(r"FITNESS_FOOD:([\d.]+)", f.get("pesos") or "")
    return float(m.group(1)) if m else ac.FITNESS_FOOD


def cargar(rutas, golpe):
    for r in rutas:
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    filas = ac.leer_agentes(rutas[1])
    for f in filas:
        f["peso"] = peso_comida(f)
        f["manzanas"] = (float(f["f_comida"]) / f["peso"]) ** 2
        if golpe:
            f["m1"], f["m0"] = ag.medidas(f, ""), ag.medidas(f, "0")
    return dict(co=sl.leer(rutas[0]), ag=filas, rutas=rutas)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    comida20, publicada, referencia = sys.argv[1:4]
    prueba = os.path.samefile(comida20, publicada)  # NF es N: la prueba del script
    suf = "" if prueba else SUFIJO
    D = {}
    for s in SEMILLAS:
        nf = cg.nombre(s, 30).replace("_evolucion.csv", suf + "_evolucion.csv")
        nb = [al.uno(os.path.join(referencia, p + f"s{s}_*moviles_curriculo30_sin_evolucion.csv"))
              for p in ("corrida_", "agentes_")]
        D[s] = dict(NF=cargar([os.path.join(comida20, t + nf) for t in ("corrida_", "agentes_")], True),
                    N=cargar([os.path.join(publicada, t + cg.nombre(s, 30)) for t in ("corrida_", "agentes_")], True),
                    NB=cargar(nb, False))
    G = max(f["gen"] for f in D[1]["NF"]["co"])
    W = range(G - 4, G + 1)
    print(f"La comida al doble en el fitness: semillas {list(SEMILLAS)}, {G} generaciones; ventana {W[0]}-{W[-1]}"
          f"{' (PRUEBA: NF es N)' if prueba else ''}; pesos de NF: {D[1]['NF']['ag'][0]['pesos']}")

    def co(s, c):
        return D[s][c]["co"]

    def agf(s, c):
        return D[s][c]["ag"]

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    sc = {c: {s: sl.val(agf(s, c), W, "sc") for s in SEMILLAS} for c in C}
    llave = {c: {s: sl.llave(co(s, c), W) for s in SEMILLAS} for c in C}
    puerta = {c: {s: al.puerta(co(s, c), W) for s in SEMILLAS} for c in C}

    print(f"\n### Gens {W[0]}-{W[-1]}: sensibilidad a la comida antes de abrir la puerta · llave roja por generación · puerta "
          f"de madera por generación")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(f"s{s} {sc[c][s]:+.4f} · {llave[c][s]:.1f} · {puerta[c][s]:.1f}" for s in SEMILLAS)
              + f" || promedio {st.mean(sc[c].values()):+.4f} · {st.mean(llave[c].values()):.1f} · "
                f"{st.mean(puerta[c].values()):.2f}")

    # ---------- Criterio ----------
    print("\n### Criterio (fijado antes de correr; la decisión 6, NF contra NB de la misma semilla)")
    k1 = sum(sc["NF"][s] >= ac.UMBRAL and sc["NF"][s] > sc["NB"][s] for s in SEMILLAS)
    c1 = k1 >= 4
    print(f"  1. Giran hacia la comida: ≥ {ac.UMBRAL:g} y más que NB en {k1} de 5 (pide 4); promedio "
          f"{st.mean(sc['NF'].values()):+.4f} (N {st.mean(sc['N'].values()):+.4f}, NB {st.mean(sc['NB'].values()):+.4f}) "
          f"-> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    rm = {c: [r for s in SEMILLAS for r in ac.dentro(agf(s, c), TRAMO, "manzanas")] for c in C}
    mF, mB = al.mediana(rm["NF"]), al.mediana(rm["NB"])
    c2 = mF > mB
    print(f"  2. Los que giran comen más que los de su generación: Spearman con las manzanas, mediana de las "
          f"{TRAMO[0]}-{TRAMO[-1]}, {mF:+.3f} contra {mB:+.3f} de NB (N {al.mediana(rm['N']):+.3f}; "
          f"{len(rm['NF'])} generaciones) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    kl = sum(llave["NF"][s] >= al.PUERTA and llave["NF"][s] > llave["NB"][s] for s in SEMILLAS)
    lF, lN = st.mean(llave["NF"].values()), st.mean(llave["N"].values())
    g_llave = kl >= 4 and lF >= LLAVE * lN
    print(f"  Guarda, la llave roja: ≥ 1 y más que NB en {kl} de 5 (pide 4); promedio {lF:.1f} contra {lN:.1f} de N (pide al "
          f"menos {LLAVE * lN:.1f}) -> {'NO CAE' if g_llave else 'CAE'}")
    kp = {c: sum(puerta[c][s] >= al.PUERTA and puerta[c][s] > puerta["NB"][s] for s in SEMILLAS) for c in ("NF", "N")}
    pF, pN = st.mean(puerta["NF"].values()), st.mean(puerta["N"].values())
    g_puerta = kp["NF"] >= kp["N"] and pF >= MITAD * pN
    print(f"  Guarda, la puerta: ≥ 1 y más que NB en {kp['NF']} de 5 (N {kp['N']}); promedio {pF:.2f} contra {pN:.2f} de N "
          f"(pide al menos {MITAD * pN:.2f}) -> {'NO CAE' if g_puerta else 'CAE'}")
    if c1 and c2:
        veredicto = ("comer aprendido, sin costar la llave ni la puerta" if g_llave and g_puerta else
                     "comer aprendido, pero cuesta " + " y ".join(x for x, ok in (("la llave", g_llave),
                                                                                   ("la puerta", g_puerta)) if not ok))
    else:
        veredicto = "comer no aprendido con FITNESS_FOOD en 20"
    print(f"  Veredicto: {veredicto}")
    print(f"  Se lee con, contra N por semilla: " + " · ".join(f"s{s} {sc['NF'][s] - sc['N'][s]:+.4f}" for s in SEMILLAS)
          + f"; el promedio de NF {'arriba' if st.mean(sc['NF'].values()) > st.mean(sc['N'].values()) else 'no arriba'} "
            f"del de N")

    # ---------- Dentro de cada generación ----------
    print("\n### Dentro de cada generación (Spearman con la sensibilidad a la comida; mediana de las generaciones del tramo "
          "de las 5 semillas, y % con r > 0): con las manzanas del agente · con el fitness (lo que ve la selección)")
    for c in C:
        partes = []
        for a, b in ac.TRAMOS:
            gens = range(a, b + 1)
            rmt = [r for s in SEMILLAS for r in ac.dentro(agf(s, c), gens, "manzanas")]
            rf = [r for s in SEMILLAS for r in ac.dentro(agf(s, c), gens, "fitness")]
            partes.append(f"{a}-{b}: {al.mediana(rmt):+.3f} ({100 * sum(r > 0 for r in rmt) / len(rmt):.0f}%) · "
                          f"{al.mediana(rf):+.3f} ({100 * sum(r > 0 for r in rf) / len(rf):.0f}%)")
        print(f"  {NOM[c]}: " + " | ".join(partes))

    # ---------- Por ventana, por etapa ----------
    print("\n### Por ventana (promedio de las 5 semillas): sensibilidad a la comida · llave roja · puerta · manzanas por "
          "1.000 px · comida comida de la disponible")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: sl.val(agf(s, c), range(a, b + 1), 'sc')):+.4f} · "
            f"{prom(lambda s: sl.llave(co(s, c), range(a, b + 1))):.1f} · "
            f"{prom(lambda s: al.puerta(co(s, c), range(a, b + 1))):.1f} · "
            f"{prom(lambda s: ac.por_px(co(s, c), range(a, b + 1))):.3f} · "
            f"{100 * prom(lambda s: ac.comidas(co(s, c), range(a, b + 1))):.0f}%" for a, b in ac.VENTANAS))
    print("  la sensibilidad a la comida, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(agf(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in ac.VENTANAS)
        for c in ("NF", "N") for s in SEMILLAS))
    print(f"\n### La sensibilidad a la comida por etapa (gens {W[0]}-{W[-1]}): etapa 0 · etapa 1")
    for c in C:
        print(f"  {NOM[c]}: {al.media([f['sc0'] for s in SEMILLAS for f in agf(s, c) if f['gen'] in W]):+.4f} · "
              f"{al.media([f['sc1'] for s in SEMILLAS for f in agf(s, c) if f['gen'] in W]):+.4f}")

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio (gens {W[0]}-{W[-1]}): manzanas por 1.000 px · comida comida de la disponible · manzanas por "
          f"agente · término de la comida · sensibilidad a la brújula · edad; y en las 31-{G}: llave dorada · puerta de "
          f"hierro · cofre (sumados)")
    for c in C:
        print(f"  {NOM[c]}: {prom(lambda s: ac.por_px(co(s, c), W)):.3f} · {100 * prom(lambda s: ac.comidas(co(s, c), W)):.0f}% · "
              f"{prom(lambda s: al.comida(co(s, c), W)):.3f} · "
              f"{al.media([float(f['f_comida']) for s in SEMILLAS for f in agf(s, c) if f['gen'] in W]):.2f} · "
              f"{prom(lambda s: sl.val(agf(s, c), W)):+.4f} · {prom(lambda s: sl.columna(co(s, c), W, 'edad_prom')):.0f}; "
              + " · ".join(str(sum(int(f[k]) for s in SEMILLAS for f in co(s, c) if f["gen"] > 30))
                           for k in ("agentes_llave_dorada", "agentes_puerta_hierro", "agentes_cofre")))
    print(f"  El golpe, etapa 1 (S · G · P pegado · P lejos): " + " | ".join(
        f"{NOM[c]} " + " · ".join(f"{prom(lambda s: ag.val(agf(s, c), W, k)):+.3f}" for k in ("S", "G", "Pp", "Pl"))
        for c in ("NF", "N")))

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in SEMILLAS:
        d, partes = D[s]["NF"], []
        for c, sha in (("N", cg.SHA_N[s]), ("NB", ac.SHA["NB"][s])):
            igual = (al.sha(D[s][c]["rutas"][0]), al.sha(D[s][c]["rutas"][1])) == sha
            errores += not igual
            partes.append(f"{c} SHA-256 publicado {igual}")
        filas = {}
        for f in d["ag"]:
            filas.setdefault(f["gen"], []).append(f)
        mal_filas = sum(len(v) != ac.POBLACION for v in filas.values()) + (len(filas) != G)
        mal_suma = sum(abs(sum(f["manzanas"] for f in filas[int(r["generacion"])]) / ac.POBLACION
                           - float(r["manzanas_prom"])) > 1e-3 for r in d["co"])
        enteras = sum(abs(f["manzanas"] - round(f["manzanas"])) > 1e-3 for f in d["ag"])
        con_10 = sum(abs((float(f["f_comida"]) / ac.FITNESS_FOOD) ** 2 - round((float(f["f_comida"]) / ac.FITNESS_FOOD) ** 2))
                     > 1e-3 for f in d["ag"])
        etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["ag"])
        sin_ticks = sum(any(float(f[k]) != 0 for k in ag.NUEVAS[:4]) for f in d["ag"] if int(f["sens_ticks"]) == 0)
        sin_medir = sum(f["sc"] is None for f in d["ag"] if f["gen"] in W)
        errores += mal_filas + mal_suma + enteras + etapa + sin_ticks + sin_medir
        partes.append(f"NF: generaciones con otras que 60 filas {mal_filas}, manzanas (con el peso {d['ag'][0]['peso']:g}) que "
                      f"no suman {mal_suma}, no enteras {enteras} (con 10: {con_10}), etapa_inicial distinta de 1/0 {etapa}, "
                      f"filas sin ticks con valor {sin_ticks}, filas de la ventana sin medir {sin_medir}")
        # la gen 1: las mismas redes con lo mismo que ven, el fitness actúa desde la selección
        n1 = {f["id"]: f for f in D[s]["N"]["ag"] if f["gen"] == 1}
        f1 = {f["id"]: f for f in d["ag"] if f["gen"] == 1}
        campos = [k for k in next(iter(f1.values())) if k not in IGUALES_GEN1 and k not in ("m1", "m0", "sb", "sb0", "sb1",
                                                                                              "sc", "sc0", "sc1", "peso",
                                                                                              "manzanas")]
        distintas = sum(f1[i][k] != n1[i][k] for i in f1 for k in campos) + (f1.keys() != n1.keys())
        # las manzanas salen de f_comida, que el CSV redondea a 4 decimales: con 2, (14,1421/10)² = 1,99999 y
        # (28,2843/20)² = 2,000004; se comparan redondeadas, como el control de enteras
        manz = sum(round(f1[i]["manzanas"]) != round(n1[i]["manzanas"]) for i in f1)
        errores += distintas + manz
        partes.append(f"gen 1 igual a N ({len(campos)} columnas, sin el fitness) {distintas} distintas, manzanas {manz}")
        if not prueba:
            pesos = all(f["pesos"].endswith(",FITNESS_FOOD:20") for f in d["ag"])
            with open(os.path.join(comida20, f"log_s{s}_food20.txt"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            en_log = ("'FITNESS_FOOD': 20.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
                      and "CROSSOVER_RATE=0.2\n" in log)
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            e = re.search(r"^ENERGIA_GOLPE golpeando: (\d+) ticks, (-?[\d.]+) por tick \| sin golpear: (\d+) ticks, "
                          r"(-?[\d.]+) por tick \(HIT_ENERGY_COST=0\.05\)$", log, re.M)
            energia = bool(e) and abs(float(e.group(2)) - 0.05) < 1e-6 and abs(float(e.group(4))) < 1e-6
            otra = d["co"][1] != D[s]["N"]["co"][1]  # desde la gen 2 la selección es otra
            errores += (not pesos) + (not en_log) + (medicion != [("0", str(60 * G))]) + (not energia) + (not otra)
            partes.append(f"pesos con FITNESS_FOOD:20 {pesos}; log (pesos, currículo, cruce) {en_log}; MEDICION {medicion}; "
                          f"ENERGIA_GOLPE (el costo, 0,05) {energia}; gen 2 distinta de N {otra}")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
