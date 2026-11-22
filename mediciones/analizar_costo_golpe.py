"""El costo de golpear, sin la llave dada (docs/qa/AnalisisQA.md#costo-golpe), a partir de los CSV de medir_puerta.py con
sens-golpe: sin la llave con HIT_ENERGY_COST en 0 (N0) contra sin la llave (N, la publicada), las dos con evolución y el
currículo cortado en la 30; la larga (L, la publicada), de referencia y sin criterio.

Con la misma cuenta que analizar_golpe.py (S, G, P pegado y P lejos por fila de agente con ticks en la etapa 1, divididas
por sens_ticks, promedio de las filas de la ventana; "En la puerta", con su función) y que analizar_sin_llave.py (la
puerta, las manzanas, la llave roja y la sensibilidad a la brújula antes de abrir la puerta). Con costo 0 la corrida es
otra desde la gen 1: G y S se miden desde el corte, ΔG = G(146-150) − G(26-30) y ΔS = S(146-150) − S(26-30), cada
corrida contra su propio corte.

Uso: python mediciones/analizar_costo_golpe.py SIN_COSTO PUBLICADA
SIN_COSTO tiene los CSV y los logs de N0; PUBLICADA, los CSV de N y de L con sens-golpe (results/medicion_golpe_20261121).
Con SIN_COSTO igual a PUBLICADA, N0 es N: la prueba del script, que tiene que dar los números de N (S +0,089 · G −1,221 ·
P pegado 0,117 · P lejos 0,055; la puerta 2,5; "En la puerta": llegan el 41% y golpean el 23%) y las diferencias en 0.
"""
import glob
import os
import re
import statistics as st
import sys

import analizar_golpe as ag
import analizar_largas as al
import analizar_sin_llave as sl

# Sin la llave, los SHA-256 publicados: corrida_*.csv (#sin-la-llave-dada) y agentes_*.csv con sens-golpe (#sens-golpe)
SHA_N = {1: ("c3e4e8112192e47e6a0c39e4960f0d4737aac061f2440846654fe1f542ddd134",
             "dbd97117383c3c9824aabd9ea2e87def6ae10a1b16f1fe63f85e1f48715ee36d"),
         2: ("09239ab7a2e5c5364366bf08a672294f45a8bf6dab67dc54f8379d53ae19a8fc",
             "6c02842686ae5bd307713e6dfd53be7584c2c0128429b5cb104883ca18664211"),
         3: ("34f9dff5b97689411cf1e0b1b92b9797cfbbac92788f5b790cb42171531d09e2",
             "283161530bb29ebf8d53bcc4e33dbb7b36d18eba81b227511548ed5f20f464e3"),
         4: ("367db4808c04afe382809444bd880857439301d71d12a3c3c4b8fc83a18cbf91",
             "2229083c6b0a8f93e4cf0956a10d075224682f94ed767d90e201afffb656f6ad"),
         5: ("d24812bab5f43fb8a40ff8a1ce7e46ed362efd362dce7fba2b80a4b4b8587eb1",
             "e606b46352e9ddc842b15d7db6cde66f6d086be0464e6ec56aab5278d84d0219")}
CORTE = range(26, 31)  # la última ventana con la llave dada
DOBLE = 2.0            # la puerta: el promedio de N0, al menos el doble que el de N
TERCIO = 1 / 3
C = ("N0", "N", "L")
NOM = dict(N0="Sin costo (N0)", N="Sin la llave (N)", L="Larga (L)")


def nombre(s, curriculo, costo0=False):
    x = "-HIT_ENERGY_COST0" if costo0 else ""
    return (f"s{s}_acercarse_deslizar_moviles_curriculo{curriculo}_cruce0.2_pesos-ACERCARSE40-EXPLORATION0-ANTI_CIRCLE0{x}"
            "_evolucion.csv")


def cargar(carpeta, s, curriculo, costo0=False):
    rutas = [os.path.join(carpeta, t + nombre(s, curriculo, costo0)) for t in ("corrida_", "agentes_")]
    for r in rutas:
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    filas = sl.leer(rutas[1])
    for f in filas:
        f["m1"], f["m0"] = ag.medidas(f, ""), ag.medidas(f, "0")
    return dict(co=al.leer(rutas[0]), ag=filas, rutas=rutas)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    sin_costo, publicada = sys.argv[1], sys.argv[2]
    costo0 = not os.path.samefile(sin_costo, publicada)  # si son la misma carpeta, N0 es N: la prueba del script
    semillas = sorted(int(re.match(r"corrida_s(\d+)_", os.path.basename(r)).group(1))
                      for r in glob.glob(os.path.join(sin_costo, "corrida_" + nombre("*", 30, costo0))))
    D = {s: dict(N0=cargar(sin_costo, s, 30, costo0), N=cargar(publicada, s, 30), L=cargar(publicada, s, 150))
         for s in semillas}
    s0 = semillas[0]
    G = max(f["gen"] for f in D[s0]["N0"]["ag"])
    W = range(G - 4, G + 1)
    print(f"El costo de golpear, sin la llave dada: semillas {semillas}, {G} generaciones"
          f"{'' if costo0 else ' (PRUEBA: N0 es N)'}; pesos de N0: {D[s0]['N0']['ag'][0]['pesos']}; de N: "
          f"{D[s0]['N']['ag'][0]['pesos']}; currículo N0 {D[s0]['N0']['ag'][0]['curriculo_hasta']}, N "
          f"{D[s0]['N']['ag'][0]['curriculo_hasta']}, L {D[s0]['L']['ag'][0]['curriculo_hasta']}")

    def v(s, c, k, gens=W, et="m1"):
        return ag.val(D[s][c]["ag"], gens, k, et)

    def pu(s, c, gens=W):
        return al.puerta(D[s][c]["co"], gens)

    def prom(f):
        return st.mean(f(s) for s in semillas)

    dG = {c: {s: v(s, c, "G") - v(s, c, "G", CORTE) for s in semillas} for c in C}
    dS = {c: {s: v(s, c, "S") - v(s, c, "S", CORTE) for s in semillas} for c in C}
    puerta = {c: {s: pu(s, c) for s in semillas} for c in C}

    print(f"\n### Gens {W[0]}-{W[-1]}, etapa 1: la puerta por generación · G en el corte (26-30) → al final (ΔG) · S en el "
          f"corte → al final (ΔS) · P pegado · P lejos (filas medidas)")
    for c in C:
        for s in semillas:
            print(f"  {NOM[c]} s{s}: {puerta[c][s]:.1f} · G {v(s, c, 'G', CORTE):+.3f} → {v(s, c, 'G'):+.3f} "
                  f"({dG[c][s]:+.3f}) · S {v(s, c, 'S', CORTE):+.3f} → {v(s, c, 'S'):+.3f} ({dS[c][s]:+.3f}) · "
                  f"{v(s, c, 'Pp'):.3f} · {v(s, c, 'Pl'):.3f} ({ag.filas_medidas(D[s][c]['ag'], W)})")
        print(f"  {NOM[c]}, promedio: {st.mean(puerta[c].values()):.2f} · G {prom(lambda s: v(s, c, 'G', CORTE)):+.3f} → "
              f"{prom(lambda s: v(s, c, 'G')):+.3f} ({st.mean(dG[c].values()):+.3f}) · S "
              f"{prom(lambda s: v(s, c, 'S', CORTE)):+.3f} → {prom(lambda s: v(s, c, 'S')):+.3f} "
              f"({st.mean(dS[c].values()):+.3f}) · {prom(lambda s: v(s, c, 'Pp')):.3f} · {prom(lambda s: v(s, c, 'Pl')):.3f}")

    # ---------- Criterio ----------
    print("\n### Criterio (fijado antes de correr; N0 contra N de la misma semilla)")
    m0, mN = st.mean(puerta["N0"].values()), st.mean(puerta["N"].values())
    k1 = sum(puerta["N0"][s] >= al.PUERTA and puerta["N0"][s] > puerta["N"][s] for s in semillas)
    c1 = k1 >= 4 and m0 >= DOBLE * mN
    print(f"  1. La puerta sube: N0 ≥ {al.PUERTA:g} por generación y más que N en {k1} de {len(semillas)} (pide 4); promedio "
          f"{m0:.2f} contra {mN:.2f}, {m0 / mN if mN else float('inf'):.2f} veces (pide {DOBLE:g}) "
          f"-> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    g0, gN = st.mean(dG["N0"].values()), st.mean(dG["N"].values())
    k2 = sum(dG["N0"][s] > dG["N"][s] for s in semillas)
    c2 = k2 >= 4 and g0 >= TERCIO * gN
    print(f"  2. El golpe en general no cae desde el corte: ΔG de N0 > el de N en {k2} de {len(semillas)} (pide 4); "
          f"promedio {g0:+.3f} contra {gN:+.3f} (pide al menos {TERCIO * gN:+.3f}) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    s_0, s_N, s_L = (st.mean(dS[c].values()) for c in C)
    umbral3 = s_N + TERCIO * (s_L - s_N)
    k3 = sum(dS["N0"][s] > dS["N"][s] for s in semillas)
    c3 = k3 >= 4 and s_0 >= umbral3
    print(f"  3. El golpe condicionado sube: ΔS de N0 > el de N en {k3} de {len(semillas)} (pide 4); promedio {s_0:+.3f} "
          f"contra {s_N:+.3f} (la larga {s_L:+.3f}; pide al menos {umbral3:+.3f}) -> {'CUMPLE' if c3 else 'NO CUMPLE'}")
    veredicto = {(True, True): "el costo frena la puerta sin la llave, por el golpe en general"
                               + (" (y aprenden a condicionar el golpe: el 3)" if c3 else
                                  " (sin el 3: golpean más en todos lados porque es gratis)"),
                 (False, True): "la caída del golpe en general es el costo, pero no es lo que frena la puerta",
                 (True, False): "la puerta sube, pero no por el golpe en general",
                 (False, False): "la caída no es el costo"}[(c1, c2)]
    print(f"  Veredicto: {veredicto}")

    # ---------- Por ventana ----------
    print("\n### Por ventana, etapa 1 (promedio de las semillas): S · G · P pegado · P lejos · la puerta por generación")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: " + " · ".join(f"{prom(lambda s: v(s, c, k, range(a, b + 1))):{'+.3f' if k in 'SG' else '.3f'}}"
                                      for k in ("S", "G", "Pp", "Pl"))
            + f" · {prom(lambda s: pu(s, c, range(a, b + 1))):.1f}" for a, b in ag.VENTANAS))
    for c in ("N0", "N"):
        for k in ("S", "G"):
            print(f"    {NOM[c]}, {k}: " + " | ".join(
                f"s{s} " + " ".join(f"{v(s, c, k, range(a, b + 1)):+.2f}" for a, b in ag.VENTANAS) for s in semillas))
        print(f"    {NOM[c]}, la puerta: " + " | ".join(
            f"s{s} " + " ".join(f"{pu(s, c, range(a, b + 1)):.1f}" for a, b in ag.VENTANAS) for s in semillas))

    # ---------- En la puerta ----------
    ag.NOMBRES.update(N=NOM["N0"], L=NOM["N"])  # la función de analizar_golpe.py, con N0 en el lugar de N y N en el de L
    ag.en_la_puerta({s: dict(N_ag=D[s]["N0"]["ag"], L_ag=D[s]["N"]["ag"]) for s in semillas}, semillas, W)

    # ---------- La gen 1, la etapa 0, contra la larga ----------
    print("\n### Gen 1 (la población inicial, la misma en N0 y en N): S · G · P pegado · P lejos, promedio de las semillas")
    for c in ("N0", "N"):
        print(f"  {NOM[c]}: " + " · ".join(f"{prom(lambda s: v(s, c, k, [1])):+.3f}" for k in ("S", "G", "Pp", "Pl")))
    print("\n### La etapa 0 (hacia la llave): S · G · P lejos por ventana, promedio de las semillas")
    for c in ("N0", "N"):
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: " + " · ".join(f"{prom(lambda s: v(s, c, k, range(a, b + 1), 'm0')):+.3f}" for k in ("S", "G", "Pl"))
            for a, b in ag.VENTANAS[1:]))
    print(f"  por semilla, gens {W[0]}-{W[-1]}, G etapa 0 / etapa 1: " + " | ".join(
        f"{c} s{s} {v(s, c, 'G', W, 'm0'):+.2f} / {v(s, c, 'G'):+.2f}" for c in ("N0", "N") for s in semillas))
    print(f"\n### Contra la larga, sin criterio (gens {W[0]}-{W[-1]}): la puerta · G · S · P pegado; q = N0 / L en la puerta")
    for c in C:
        print(f"  {NOM[c]}: {st.mean(puerta[c].values()):.2f} · {prom(lambda s: v(s, c, 'G')):+.3f} · "
              f"{prom(lambda s: v(s, c, 'S')):+.3f} · {prom(lambda s: v(s, c, 'Pp')):.3f}")
    print(f"  q = {st.mean(puerta['N0'].values()) / st.mean(puerta['L'].values()):.2f}; N0 arriba de L en la puerta en "
          f"{sum(puerta['N0'][s] > puerta['L'][s] for s in semillas)} de {len(semillas)}")

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio, gens {W[0]}-{W[-1]}: llave roja por generación · manzanas · sensibilidad a la brújula antes "
          f"de abrir la puerta · edad promedio; y en las 31-{G}: llave dorada · puerta de hierro · cofre (sumados); el costo "
          f"en ticks (las {G} generaciones)")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"s{s} {sl.llave(D[s][c]['co'], W):.1f} · {al.comida(D[s][c]['co'], W):.3f} · {sl.val(D[s][c]['ag'], W):+.4f} · "
            f"{sl.columna(D[s][c]['co'], W, 'edad_prom'):.0f}; "
            + " · ".join(str(sum(int(f[k]) for f in D[s][c]["co"] if f["gen"] > 30))
                         for k in ("agentes_llave_dorada", "agentes_puerta_hierro", "agentes_cofre"))
            + f"; {al.acumulados(D[s][c]['co'])[-1]}" for s in semillas))
        print(f"    promedio: {prom(lambda s: sl.llave(D[s][c]['co'], W)):.1f} · {prom(lambda s: al.comida(D[s][c]['co'], W)):.3f}"
              f" · {prom(lambda s: sl.val(D[s][c]['ag'], W)):+.4f} · {prom(lambda s: sl.columna(D[s][c]['co'], W, 'edad_prom')):.0f}")

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in semillas:
        d, partes = D[s]["N0"], []
        igual = (al.sha(D[s]["N"]["rutas"][0]), al.sha(D[s]["N"]["rutas"][1])) == SHA_N[s]
        errores += not igual
        partes.append(f"N = publicada (SHA-256 de corrida y agentes) {igual}")
        etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["ag"])
        e0 = sum(any(float(f[k]) != 0 for k in ag.NUEVAS[4:]) for f in d["ag"] if f["gen"] <= 30)
        sin_ticks = sum(any(float(f[k]) != 0 for k in ag.NUEVAS[:4]) for f in d["ag"] if int(f["sens_ticks"]) == 0)
        errores += etapa + e0 + sin_ticks + (len(d["ag"]) != 60 * G)
        partes.append(f"N0: filas {len(d['ag'])}, etapa_inicial distinta de 1/0 {etapa}, etapa 0 distinta de 0 en las 1-30 "
                      f"{e0}, filas sin ticks con valor {sin_ticks}")
        if costo0:
            gen1 = d["co"][0] != D[s]["N"]["co"][0]
            pesos = all(f["pesos"].endswith(",HIT_ENERGY_COST:0") for f in d["ag"])
            with open(os.path.join(sin_costo, f"log_s{s}_costo0.txt"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            e = re.search(r"^ENERGIA_GOLPE golpeando: (\d+) ticks, (-?[\d.]+) por tick \| sin golpear: (\d+) ticks, "
                          r"(-?[\d.]+) por tick \(HIT_ENERGY_COST=0\.0\)$", log, re.M)
            en_log = ("'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
                      and "CROSSOVER_RATE=0.2\n" in log)
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            energia = bool(e) and int(e.group(1)) > 0 and abs(float(e.group(2))) < 1e-6 and abs(float(e.group(4))) < 1e-6
            errores += (not gen1) + (not pesos) + (not en_log) + (medicion != [("0", str(60 * G))]) + (not energia)
            partes.append(f"gen 1 distinta de N {gen1}; pesos con HIT_ENERGY_COST:0 {pesos}; log (pesos, currículo, cruce) "
                          f"{en_log}; MEDICION {medicion}; ENERGIA_GOLPE {e.groups() if e else None} -> {energia}")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
