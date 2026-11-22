"""Comer, en la referencia (docs/qa/AnalisisQA.md#comer; el paso 1 de docs/specs/active/PUZZLE_SOLOS.md, su decisión 6), a
partir de los CSV publicados de medir_puerta.py: la referencia (sin la llave dada: el currículo cortado en la 30) y su línea
base; sin criterio, la larga (la llave dada hasta el final) y su línea base, y la referencia sin costo de golpear (la
candidata a referencia nueva, docs/qa/AnalisisQA.md#costo-golpe).

Con la cuenta de la llave por 1.000 px y la de la brújula de analizar_sin_llave.py (LEC-016):
- manzanas por 1.000 px: el promedio de manzanas_prom en la ventana dividido por el de distancia_prom, × 1.000;
- la sensibilidad a la comida antes de abrir la puerta: por fila de agente, (sens_comida + sens_comida0) / (sens_ticks +
  sens_ticks0), promedio de las filas de la ventana (la de la brújula, con sens_comida en lugar de sens_brujula).
Suma la comida comida de la disponible (manzanas_prom × 60 / (70 + 20 × arboles_cortados), por generación) y, dentro de
cada generación con 10 agentes medidos o más, el Spearman entre la sensibilidad a la comida y las manzanas de cada agente
(de f_comida = FITNESS_FOOD × √manzanas) y entre la sensibilidad y el fitness, mediana del tramo.

Uso: python mediciones/analizar_comida.py REFERENCIA LARGA SIN_COSTO [prueba]
REFERENCIA tiene los CSV de la referencia y de su línea base (results/medicion_sin_llave_20261120); LARGA, los de la larga
y la suya (results/medicion_corridas_largas_20261120); SIN_COSTO, los de la referencia con HIT_ENERGY_COST en 0
(results/medicion_costo_golpe_20261121). Con prueba imprime solo números ya publicados, que tiene que dar (las manzanas,
0,987 y 0,382; la brújula, +0,1105 y −0,0006; la llave por 1.000 px, 34,9 y 3,6; la larga, 1,099 y +0,0868; su línea
base, 0,379 y +0,0003; sin costo, 0,993 y +0,108), y los controles: así se prueba antes de leer nada nuevo.
"""
import os
import statistics as st
import sys

import analizar_largas as al
import analizar_sin_llave as sl

# La referencia, los SHA-256 publicados (docs/qa/AnalisisQA.md#sin-la-llave-dada): corrida_*.csv y agentes_*.csv
SHA = dict(
    N={1: ("c3e4e8112192e47e6a0c39e4960f0d4737aac061f2440846654fe1f542ddd134",
           "7be8cf6dcdcd3b88c3c32af77e06219e42333b750c4126865fea86de2f6d6ed5"),
       2: ("09239ab7a2e5c5364366bf08a672294f45a8bf6dab67dc54f8379d53ae19a8fc",
           "220af56763c035b8282c8673fd564c10493f1c5c8493513be5f775097b530010"),
       3: ("34f9dff5b97689411cf1e0b1b92b9797cfbbac92788f5b790cb42171531d09e2",
           "461ab7927aaef128a75db9f8ae977f96156878f89bd448173f7021752f3a80f7"),
       4: ("367db4808c04afe382809444bd880857439301d71d12a3c3c4b8fc83a18cbf91",
           "03993c6ca2392f26a0d5b0e616e25d56b37092af9b8355fba13b235bc64221b9"),
       5: ("d24812bab5f43fb8a40ff8a1ce7e46ed362efd362dce7fba2b80a4b4b8587eb1",
           "f05f7861175052e41fc4bbca5b558500712f9b4bd475a8f937057a77c251d0a7")},
    NB={1: ("405989b5e0c752cec11dec1ce2ab445896f1516f63a445a8fd9a819b18a449e3",
            "81db83593d989e8e11e3493e4a8c1fd111e4dac884b563d1066996076126016e"),
        2: ("a14bd0ec3838cc2fb25e4383be63f53bae79cfcbe60cd490c118502db2ff041a",
            "adbb9538c24897480f6b8d879d76b82c2f72dfd6f7aa3db6178326735fcc869f"),
        3: ("30d6596638def9e1d2f4bf030762f914b33e57dfaae3322b6a30ff77e8d0ce47",
            "4d66ae19a2b28265fc9f7c1b26f30c127bb78fcdaa47a8c8d28e44730ca6692b"),
        4: ("15dda42ce09b5f6fd2ce6f000648ce0ca410797ba3bd0599de8a741c13f55c2c",
            "6bd939380a941faf0a7c34b7ef47f8ebe2ecdb5bdf33e87a97fd842c8df72add"),
        5: ("394c34ab70814931064668dca87179fb8dd9cdfc0f6dd76c22ba5c5458d5993f",
            "9e0840e60ac10d9d1f71038efdf8e347849fa596c427eb61bd0407a7a111af39")},
    # sin costo de golpear (docs/qa/AnalisisQA.md#costo-golpe)
    N0={1: ("f53e597da821c3af1600861855a2585892e386d36e0408175c4f4f08c07330c3",
            "8a14ad4938e69d24bef7afade89d6804b52f1f105e585c3f191cb695ece52ee6"),
        2: ("64e215c753c2481c43b9d8df01edccaa2be04d9498dd28b3781aec4f63b1ad37",
            "d67387c606258de6ca866a7aebd26705df43bf7b9753ed010afa1ccf5dc14b25"),
        3: ("f7931fe924663170ec491cf5f2544bcad7d1459595625f76ea34e38abfe27857",
            "f27ecf80b62ff74677ea286f02c2b56fe5724683639a58871aeb23e8958efd5a"),
        4: ("68bfb68148b1b7f3c1c4ceac9b21387a4332ec08d927d8f5b6cd44b6af4b763a",
            "79ad70a1d798b56ab1a408eb9d35d6355c8837078160d4707fe852e3ae6269ce"),
        5: ("d29480e929ab1bd5cb8348674a866b02a2188a58bf0af4375bff04db973e4744",
            "cf952d1aeb1cfbbe3259efba9a52bc0bcc43a26de75919d521bf0eb7fc46eccb")})
SEMILLAS = (1, 2, 3, 4, 5)
POBLACION = 60
MANZANAS = 70        # FOOD_COUNT: las de cada generación, sin reponer
POR_ARBOL = 20       # TREE_CUT_FOOD_REWARD (las casitas, 30, no están en el CSV)
FITNESS_FOOD = 10.0  # f_comida = FITNESS_FOOD × √manzanas (terminos_fitness de medir_puerta.py)
DOBLE = 2.0          # la 1: el promedio de las 5, al menos el doble que el de la línea base
UMBRAL = 0.02        # la 2: rad/tick por semilla, el de la brújula
VENTANAS = ((26, 30), (31, 35), (56, 60), (86, 90), (116, 120), (146, 150))
TRAMOS = ((1, 30), (31, 60), (61, 90), (91, 120), (121, 150))
C = ("N", "NB", "L", "LB", "N0")
NOM = dict(N="Referencia", NB="Línea base", L="Larga (la llave, dada)", LB="Línea base larga", N0="Sin costo de golpear")
DADA = ("L", "LB")   # nacen con la llave las 150 generaciones


def leer_agentes(ruta):
    """Las de analizar_sin_llave.leer (sb, sb0, sb1), con la sensibilidad a la comida de antes de abrir la puerta (sc) y la
    de cada etapa (sc0, sc1), y las manzanas de cada agente, de f_comida."""
    filas = sl.leer(ruta)
    for f in filas:
        t1, t0 = int(f.get("sens_ticks") or 0), int(f.get("sens_ticks0") or 0)
        c1, c0 = float(f.get("sens_comida") or 0), float(f.get("sens_comida0") or 0)
        f["sc"] = (c1 + c0) / (t1 + t0) if t1 + t0 else None
        f["sc1"] = c1 / t1 if t1 else None
        f["sc0"] = c0 / t0 if t0 else None
        f["manzanas"] = (float(f["f_comida"]) / FITNESS_FOOD) ** 2
    return filas


def cargar(referencia, larga, sin_costo):
    D = {}
    for s in SEMILLAS:
        d = D[s] = {}
        for c, carpeta, patron in (("N", referencia, f"s{s}_*moviles_curriculo30_cruce*_evolucion.csv"),
                                   ("NB", referencia, f"s{s}_*moviles_curriculo30_sin_evolucion.csv"),
                                   ("L", larga, f"s{s}_*moviles_curriculo150_cruce*_evolucion.csv"),
                                   ("LB", larga, f"s{s}_*moviles_curriculo150_sin_evolucion.csv"),
                                   ("N0", sin_costo, f"s{s}_*moviles_curriculo30_cruce*HIT_ENERGY_COST0_evolucion.csv")):
            rc, ra = (al.uno(os.path.join(carpeta, p + patron)) for p in ("corrida_", "agentes_"))
            d[c] = dict(co=sl.leer(rc), ag=leer_agentes(ra), rutas=(rc, ra))
    return D


def por_px(co, gens):
    """Manzanas por 1.000 px: la cuenta de sl.llave_px con manzanas_prom."""
    d = sl.columna(co, gens, "distancia_prom")
    return sl.columna(co, gens, "manzanas_prom") / d * 1000 if d else float("nan")


def comidas(co, gens):
    """Las manzanas comidas de las disponibles, promedio por generación."""
    gens = set(gens)
    return st.mean(float(f["manzanas_prom"]) * POBLACION / (MANZANAS + POR_ARBOL * int(f["arboles_cortados"]))
                   for f in co if f["gen"] in gens)


def dentro(ag, gens, y):
    """Spearman (sensibilidad a la comida, y) dentro de cada generación con 10 agentes medidos o más: una por generación
    (la cuenta de al.seleccion)."""
    rs = []
    for g in gens:
        fg = [f for f in ag if f["gen"] == g and f["sc"] is not None]
        if len(fg) >= 10:
            r = al.spearman([f["sc"] for f in fg], [float(f[y]) for f in fg])
            if r == r:  # sin los nan
                rs.append(r)
    return rs


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    referencia, larga, sin_costo = sys.argv[1], sys.argv[2], sys.argv[3]
    prueba = len(sys.argv) > 4 and sys.argv[4] == "prueba"
    D = cargar(referencia, larga, sin_costo)
    G = max(f["gen"] for f in D[1]["N"]["co"])
    W = range(G - 4, G + 1)

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    def co(s, c):
        return D[s][c]["co"]

    def ag(s, c):
        return D[s][c]["ag"]

    print(f"Comer, en la referencia: semillas {list(SEMILLAS)}, {G} generaciones; ventana {W[0]}-{W[-1]}"
          f"{' (PRUEBA: solo números publicados y controles)' if prueba else ''}")

    # ---------- Lo publicado: la prueba del script ----------
    print(f"\n### Lo publicado (gens {W[0]}-{W[-1]}): manzanas por agente · sensibilidad a la brújula antes de abrir la "
          f"puerta · llave roja por 1.000 px")
    for c in C:
        llave = "" if c in DADA else f" · {prom(lambda s: sl.llave_px(co(s, c), W)):.1f}"
        print(f"  {NOM[c]}: {prom(lambda s: al.comida(co(s, c), W)):.3f} · {prom(lambda s: sl.val(ag(s, c), W)):+.4f}"
              + llave)
        print("    por semilla: " + " | ".join(
            f"s{s} {al.comida(co(s, c), W):.3f} · {sl.val(ag(s, c), W):+.4f}" for s in SEMILLAS))

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in SEMILLAS:
        partes = []
        for c in SHA:
            igual = (al.sha(D[s][c]["rutas"][0]), al.sha(D[s][c]["rutas"][1])) == SHA[c][s]
            errores += not igual
            partes.append(f"{c} SHA-256 publicado {igual}")
        for c in C:
            filas = {}
            for f in ag(s, c):
                filas.setdefault(f["gen"], []).append(f)
            mal_filas = sum(len(v) != POBLACION for v in filas.values()) + (len(filas) != G)
            # las manzanas de cada agente (de f_comida) suman manzanas_prom × 60; manzanas_prom va redondeado a 4 decimales
            mal_suma = sum(abs(sum(f["manzanas"] for f in filas[int(r["generacion"])]) / POBLACION
                               - float(r["manzanas_prom"])) > 1e-3 for r in co(s, c))
            enteras = sum(abs(f["manzanas"] - round(f["manzanas"])) > 1e-3 for f in ag(s, c))
            errores += mal_filas + mal_suma + enteras
            partes.append(f"{c}: generaciones con otras que 60 filas {mal_filas}, manzanas que no suman {mal_suma}, "
                          f"no enteras {enteras}")
        for c in C:
            dada = c in DADA
            etapa = sum(int(f["etapa_inicial"]) != (1 if dada or f["gen"] <= 30 else 0) for f in ag(s, c))
            sin0 = 0 if dada else sum(int(f["sens_ticks0"]) == 0 for f in ag(s, c) if f["gen"] > 30)
            sin_medir = sum(f["sc"] is None for f in ag(s, c) if f["gen"] in W)
            errores += etapa + sin0 + sin_medir
            partes.append(f"{c}: etapa_inicial distinta de {'1' if dada else '1/0'} {etapa}, filas sin ticks en la etapa 0 "
                          f"desde la 31 {sin0}, filas de la ventana sin medir {sin_medir}")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")
    if prueba:
        return

    px = {c: {s: por_px(co(s, c), W) for s in SEMILLAS} for c in C}
    sc = {c: {s: sl.val(ag(s, c), W, "sc") for s in SEMILLAS} for c in C}

    # ---------- Criterio ----------
    print(f"\n### Criterio (gens {W[0]}-{W[-1]}): manzanas por 1.000 px (manzanas por agente / distancia en px) · "
          f"sensibilidad a la comida antes de abrir la puerta")
    for c in C:
        for s in SEMILLAS:
            print(f"  {NOM[c]} s{s}: {px[c][s]:.3f} ({al.comida(co(s, c), W):.3f} / "
                  f"{sl.columna(co(s, c), W, 'distancia_prom'):.0f}) · {sc[c][s]:+.4f}")
        print(f"  {NOM[c]}, promedio: {st.mean(px[c].values()):.3f} ({prom(lambda s: al.comida(co(s, c), W)):.3f} / "
              f"{prom(lambda s: sl.columna(co(s, c), W, 'distancia_prom')):.0f}) · {st.mean(sc[c].values()):+.4f}")
    mN, mB = st.mean(px["N"].values()), st.mean(px["NB"].values())
    k1 = sum(px["N"][s] > px["NB"][s] for s in SEMILLAS)
    c1 = k1 >= 4 and mN >= DOBLE * mB
    print(f"  1. Más manzanas por 1.000 px: más que la línea base en {k1} de 5 (pide 4); promedio {mN:.3f} contra {mB:.3f}, "
          f"{mN / mB:.2f} veces (pide {DOBLE:g}) -> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    k2 = sum(sc["N"][s] >= UMBRAL and sc["N"][s] > sc["NB"][s] for s in SEMILLAS)
    c2 = k2 >= 4
    print(f"  2. Giran hacia la comida: ≥ {UMBRAL:g} y más que la línea base en {k2} de 5 (pide 4); promedio "
          f"{st.mean(sc['N'].values()):+.4f} contra {st.mean(sc['NB'].values()):+.4f} -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    print(f"  Comer aprendido (los dos): {'SÍ' if c1 and c2 else 'NO'}")

    # ---------- La comida que queda ----------
    print(f"\n### La comida comida de la disponible, por generación (gens {W[0]}-{W[-1]}); árboles cortados en la ventana")
    for c in C:
        print(f"  {NOM[c]}: {100 * prom(lambda s: comidas(co(s, c), W)):.0f}% · " + " | ".join(
            f"s{s} {100 * comidas(co(s, c), W):.0f}%" for s in SEMILLAS) + "; árboles: "
              + " ".join(str(sum(int(f["arboles_cortados"]) for f in co(s, c) if f["gen"] in W)) for s in SEMILLAS))

    # ---------- Por etapa ----------
    print(f"\n### La sensibilidad a la comida por etapa (gens {W[0]}-{W[-1]}; filas con ticks en cada etapa): etapa 0 · "
          f"etapa 1")
    for c in C:
        n0 = sum(f["sc0"] is not None for s in SEMILLAS for f in ag(s, c) if f["gen"] in W)
        n1 = sum(f["sc1"] is not None for s in SEMILLAS for f in ag(s, c) if f["gen"] in W)
        print(f"  {NOM[c]}: {al.media([f['sc0'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} ({n0} filas) · "
              f"{al.media([f['sc1'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} ({n1} filas)")

    # ---------- Dentro de cada generación ----------
    print("\n### Dentro de cada generación (Spearman con la sensibilidad a la comida; mediana de las generaciones del tramo "
          "de las 5 semillas, y % con r > 0): con las manzanas del agente · con el fitness")
    for c in C:
        partes = []
        for a, b in TRAMOS:
            gens = range(a, b + 1)
            rm = [r for s in SEMILLAS for r in dentro(ag(s, c), gens, "manzanas")]
            rf = [r for s in SEMILLAS for r in dentro(ag(s, c), gens, "fitness")]
            partes.append(f"{a}-{b}: {al.mediana(rm):+.3f} ({100 * sum(r > 0 for r in rm) / len(rm):.0f}%) · "
                          f"{al.mediana(rf):+.3f} ({100 * sum(r > 0 for r in rf) / len(rf):.0f}%)")
        print(f"  {NOM[c]}: " + " | ".join(partes))

    # ---------- Por ventana ----------
    print("\n### Por ventana (promedio de las 5 semillas): manzanas por 1.000 px · sensibilidad a la comida · comida comida "
          "de la disponible · manzanas por agente · distancia")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: por_px(co(s, c), range(a, b + 1))):.3f} · "
            f"{prom(lambda s: sl.val(ag(s, c), range(a, b + 1), 'sc')):+.4f} · "
            f"{100 * prom(lambda s: comidas(co(s, c), range(a, b + 1))):.0f}% · "
            f"{prom(lambda s: al.comida(co(s, c), range(a, b + 1))):.3f} · "
            f"{prom(lambda s: sl.columna(co(s, c), range(a, b + 1), 'distancia_prom')):.0f}" for a, b in VENTANAS))
    print("  la sensibilidad a la comida, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in VENTANAS)
        for c in ("N", "NB") for s in SEMILLAS))

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio (gens {W[0]}-{W[-1]}): edad promedio · término de la comida (promedio de las filas)")
    for c in C:
        print(f"  {NOM[c]}: {prom(lambda s: sl.columna(co(s, c), W, 'edad_prom')):.0f} · "
              f"{al.media([float(f['f_comida']) for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):.2f}")


if __name__ == "__main__":
    main()
