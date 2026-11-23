"""La recompensa por acercarse por el camino (docs/qa/AnalisisQA.md#acercarse-camino): los pasos 2 a 6 con
ACERCARSE_CAMINO, a partir de los CSV de medir_puerta.py con hierro, brujula-camino y acercarse-camino.

- NA, la referencia (NC) con la recompensa por acercarse medida por el camino, contra NCB0, la línea base de la referencia.
  Sin evolución, el fitness no cambia lo que hacen (lo controla la corrida corta de la Sesión 7 del spec PUZZLE_SOLOS): la
  línea base de NA es NCB0, y no se corre otra vez. El criterio de la decisión 5 del spec, en los pasos 2 a 6, en las gens
  146-150.
- NC, la referencia (la brújula por el camino, docs/qa/AnalisisQA.md#brujula-camino): los pasos 2 a 4 no pierden si siguen
  pasando, y la medida independiente del paso 5 (de los que tienen la llave dorada, la parte que llega a 25 px de la
  puerta de hierro, NA contra NC, en las 31-150).

Las otras medidas independientes, contra NCB0, como en analizar_brujula_camino.py: por 1.000 px (la llave roja, la llave
dorada y el cofre) y, en la puerta de madera, la parte que llega a 25 px de los que tienen la llave roja, en las 31-150.

Uso: python mediciones/analizar_acercarse_camino.py TANDA REFERENCIA
TANDA tiene los CSV y los logs de NA (log_s{S}_evolucion.txt); REFERENCIA, los de NC y NCB0
(results/medicion_brujula_camino_20261122). Con TANDA igual a REFERENCIA, la prueba del script: NA es NC, y tiene que dar
lo publicado en #brujula-camino (lo controla solo, en PUBLICADO) con 0 errores.
"""
import os
import re
import statistics as st
import sys

import analizar_brujula_camino as bc
import analizar_cadena as cad
import analizar_hierro as hi
import analizar_largas as al
import analizar_sin_llave as sl

SEMILLAS = bc.SEMILLAS
MINIMO = bc.MINIMO  # agentes por generación que dan el paso (el tamaño mínimo de la decisión 5)
PASOS = cad.PASOS  # los pasos 2 a 6 del spec, con su columna, la etapa que los marca y su nombre
NOM = dict(NA="Acercarse por el camino (NA)", NCB0="Línea base de la referencia (NCB0)", NC="Referencia (NC)")
NA_NOMBRE = ("s{s}_acercarse_camino_deslizar_moviles_brujula_camino_curriculo30_cruce0.2_pesos-ACERCARSE40-"
             "EXPLORATION0-ANTI_CIRCLE0-HIT_ENERGY_COST0_evolucion.csv")
# Lo que el fitness cambia en la gen 1. Con la misma población inicial y el mismo mundo, NA hace lo mismo que NC: cambian el
# fitness, el término de acercarse y lo que sale del fitness (el lugar, el pool, la élite y lo que aporta a la gen 2)
FITNESS_CO = cad.FITNESS
FITNESS_AG = ("fitness", "lugar", "en_pool", "elite", "aporte", "f_acercarse")
# Lo publicado en #brujula-camino: el criterio de NC contra NCB0 en las 146-150; la puerta de madera (con la llave roja y
# los que llegan, 31-150, NC y NCB0); la puerta de hierro de NC (con la llave dorada, llegan y la abren, 31-150); y la
# puerta de hierro y el cofre de NC por semilla, 31-150
PUBLICADO = dict(
    criterio=dict(agentes_llave_roja=((52.2, 52.8, 54.2, 56.2, 45.4), (1.6, 1.0, 0.6, 1.2, 1.8)),
                  agentes_puerta_madera=((32.8, 42.8, 46.8, 30.4, 12.0), (0,) * 5),
                  agentes_llave_dorada=((27.2, 35.0, 45.4, 22.2, 5.0), (0,) * 5),
                  agentes_puerta_hierro=((1.6, 4.4, 12.6, 0.4, 0), (0,) * 5),
                  agentes_cofre=((0.4, 0.8, 9.4, 0, 0), (0,) * 5)),
    madera=((24441, 18127), (671, 47)), hierro_NC=(10915, 4070, 1504),
    cadena_NC=dict(agentes_puerta_hierro=(563, 217, 696, 28, 0), agentes_cofre=(278, 99, 477, 2, 0)))
# El SHA-256 publicado de NC y de NCB0 (#brujula-camino): corrida, agentes y geometría
SHA = dict(
    NC={1: ("442f236bf4d62ad8fd5c0db725626122f6dcb6ac818d347308efbcc07362b512",
            "6e202a46d7215f09b826d954baa9fa4e91d746f7d6c5a09df6dfbd977a0acdfc",
            "fb42646fea2cf0c7ec717c5fd81d893a0f4fdf11d5ad2f42f7e6ff31a11c3318"),
        2: ("3bc504bc3c7ada077f19c749b7e9fdfc397a0101088dbe2ed029c858e33e2000",
            "fc90a88df6b44dad0b6e20575501949ece65afa35a462a1cbbdbde4fcabf0cbe",
            "6087a8ef08940ff4c08b03aa10834b0f8ee67df98bbb1a9955b49086475c7b88"),
        3: ("0191fdb6683dc70a04e4af3a8d825da8e894bddcf52748ffdc494e91719e7298",
            "0ec731b6a95cf21e2dbb50f31d1de46821c38229831539d76c964f448626f11c",
            "960d36a0078a14407dc871527f6e1140cb7e88aa2bdc16ed02b60ff44b962de2"),
        4: ("27c49566dc780efab6659116b8454fb2049e84731ab7c61b6f72a5f561e4f90c",
            "03e334d523bdf144d5e3bcbc195f836fcecde4176d6a3b575b742c27ab63e92b",
            "625f5fb6e61ebf8d8a07281330e6a6e804ddb464fdd0afeab3ff31c0235b5f9e"),
        5: ("1ea042b9287980d826a49f362502b7fde35144ba9ba21bc0bc7da897fa7ac77c",
            "b87975c64635d54f85be752b55bcdcf8616f7986f1abf2a005fcfd0e8a5fff8d",
            "c58464fbae99ec9541464dbf9a0c515696536b4ac2fc4a642ae18df026ad76c8")},
    NCB0={1: ("b591da4251363891235c80b38917e5fe294731669f169577898c9d1d55e05b02",
              "38d697bbbd42638311794a3ad612d7765132066d67b9378e89ccf8108a7f8b2e",
              "72b5163504610845d577fc38bcbc351b85b108649b6f5366d77056e65996d54c"),
          2: ("97bbfd903b1cd3e102764eb6f6122b0549f69012e6e7ebeb186445a03e03b611",
              "8cf94e3956b8a39d9cd3b039962ced06608d2d926f1f1f297dd322f851f3bb8b",
              "12be18f4a49277526dcc035ed15bac41b2d8967d9568df9d4aaf0873a3daedf5"),
          3: ("a6ad626d9ceb4baaca959c725bc2cd4537919dcf5ebdaa2cae4ed5157aa890b4",
              "801bd976ee84cda776f1722710afa94dc7846671f36c185a0b83ce6aea5fb587",
              "b84889bb6d67568393e2e5a5985dafe46e0a6a68fff49c416b851bbdd01218f0"),
          4: ("d6072aa26e25b70e91f51a8e23861b0e7ad6918140ffb6c1b8405a67e272253e",
              "13453ed23052f9b74491dc7547876bfa419254d6b713751f566ba9c570015de3",
              "2a1272c4fce58c1a8a88cc5c0e95338c74e4315f4113f904988e010bde52e20c"),
          5: ("a7cd3a1a9faab2b03c9100570448e5aae6702e314db4b95fdf06cdbdb08a6fec",
              "7e46eb67dc8f4ee668349007c486552b9857acdd3f7b112dcf554fab78dda342",
              "0269c2f29ad66070be0b7f7abd9f1a3bc69d04d252d634d87ac6de5d06684548")})


def gen1_distinta(a, b, fitness):
    """Las columnas de la gen 1 en que a y b difieren, sin las del fitness ni las que agrega el lector (gen, sb) o tiene una
    sola de las dos (acercarse_camino)."""
    claves = (set(a) & set(b)) - set(fitness) - {"gen", "sb"}
    return sorted(k for k in claves if a[k] != b[k])


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    tanda, ref = sys.argv[1:3]
    prueba = os.path.samefile(tanda, ref)  # NA es NC: la prueba del script
    D = {}
    for s in SEMILLAS:
        nc = bc.cargar(ref, bc.NC_NOMBRE.format(s=s))
        D[s] = dict(NA=nc if prueba else bc.cargar(tanda, NA_NOMBRE.format(s=s)),
                    NCB0=bc.cargar(ref, bc.NCB0_NOMBRE.format(s=s)), NC=nc)
    G = max(f["gen"] for f in D[1]["NA"]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    print(f"Acercarse por el camino: semillas {list(SEMILLAS)}, {G} generaciones"
          f"{' (PRUEBA: NA es NC)' if prueba else ''}; pesos de NA: {D[1]['NA']['ag'][0]['pesos']}")

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    errores = 0
    dio = {}

    # ---------- El criterio ----------
    print(f"\n### Gens {W[0]}-{W[-1]}: agentes por generación que dan el paso (entre paréntesis, por 1.000 px)")
    for col, _, nombre in PASOS:
        v = {c: {s: cad.paso(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        p = {c: {s: cad.px(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        dio[col] = (tuple(round(v["NA"][s], 1) for s in SEMILLAS), tuple(round(v["NCB0"][s], 1) for s in SEMILLAS))
        print(f"  {nombre}:")
        for c in NOM:
            print(f"    {NOM[c]}: " + " · ".join(f"s{s} {v[c][s]:.1f} ({p[c][s]:.2f})" for s in SEMILLAS)
                  + f" | promedio {st.mean(v[c].values()):.2f} ({st.mean(p[c].values()):.2f})")
        for c in ("NA", "NC"):
            pasan = [s for s in SEMILLAS if v[c][s] >= MINIMO and v[c][s] > v["NCB0"][s]]
            acomp = all(p[c][s] > p["NCB0"][s] for s in pasan) if pasan else False
            ceros = bool(pasan) and all(v["NCB0"][s] == 0 for s in pasan)
            print(f"    -> {c} ≥ {MINIMO:g} por generación y más que NCB0 en {len(pasan)} de 5 (semillas {pasan}; pide 4): "
                  f"{'PASA' if len(pasan) >= 4 else 'NO PASA'}; por 1.000 px, {c} arriba de NCB0 en todas las que pasan: "
                  f"{acomp}{' (NCB0 da 0 en todas: no agrega)' if ceros else ''}")
        print(f"    NA contra NC (sin criterio): promedio {st.mean(v['NA'].values()):.2f} contra "
              f"{st.mean(v['NC'].values()):.2f}; por semilla, NA más que NC en "
              f"{sum(v['NA'][s] > v['NC'][s] for s in SEMILLAS)} de 5")

    # ---------- Las medidas independientes de las puertas ----------
    print(f"\n### La puerta de madera, gens 31-{G}, todas las semillas: de los que tienen la llave roja, los que llegan a 25 px")
    for c in NOM:
        F, L = (sum(x) for x in zip(*(bc.llegan_madera(D[s][c]["ag"], DESDE) for s in SEMILLAS)))
        dio[f"madera_{c}"] = (F, L)
        print(f"  {NOM[c]}: con la llave {F} · llegan {L} ({cad.pct(L, F)})")
    print(f"\n### La puerta de hierro, gens 31-{G} y {W[0]}-{W[-1]}: con la llave dorada y ticks en la etapa 3 · llegan a 25 px "
          f"· la abren")
    for c in NOM:
        for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
            por = [bc.hierro(D[s][c]["ag"], gens) for s in SEMILLAS]
            F, L, A = (sum(x) for x in zip(*por))
            if gens == DESDE:
                dio[f"hierro_{c}"] = (F, L, A)
            print(f"  {NOM[c]}, {rotulo}: con la llave {F} · llegan {L} ({cad.pct(L, F)}) · la abren {A} ({cad.pct(A, F)})"
                  f" | por semilla, llegan/con la llave: " + " · ".join(f"s{s} {x[1]}/{x[0]}" for s, x in zip(SEMILLAS, por)))
    na, nc = dio["hierro_NA"], dio["hierro_NC"]
    print(f"  -> la parte que llega, más alta en NA que en NC (31-{G}): "
          f"{na[0] > 0 and nc[0] > 0 and na[1] / na[0] > nc[1] / nc[0]} ({cad.pct(na[1], na[0])} contra "
          f"{cad.pct(nc[1], nc[0])})")
    for c in ("NA", "NC"):
        print(f"  Dónde se traba en {c} (31-{G}, la cuenta de analizar_hierro.py):")
        F, cuenta = hi.clasificar([f for s in SEMILLAS for f in D[s][c]["ag"]], "hierro", DESDE)
        hi.imprimir_grupos(cuenta, len(F))
        print(f"    se traba en: {hi.trabado(cuenta)}")

    # ---------- Por ventana ----------
    print("\n### Por ventana: agentes por generación que dan el paso, promedio de las semillas")
    for col, _, nombre in PASOS:
        for c in NOM:
            print(f"  {nombre}, {NOM[c]}: " + " | ".join(
                f"{a}-{b} {prom(lambda s: cad.paso(D[s][c]['co'], range(a, b + 1), col)):.2f}"
                for a, b in cad.ag.VENTANAS))
    print(f"  la puerta de hierro por semilla, {W[0]}-{W[-1]}: " + " | ".join(
        f"{c} " + " · ".join(f"{cad.paso(D[s][c]['co'], W, 'agentes_puerta_hierro'):.1f}" for s in SEMILLAS)
        for c in ("NA", "NC")))

    # ---------- El embudo ----------
    print("\n### El embudo: agentes que dan cada paso, sumados (las 5 semillas), y entre paréntesis la parte de los del paso "
          "anterior")
    for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
        for c in NOM:
            t = [sum(cad.suma(D[s][c]["co"], gens, col) for s in SEMILLAS) for col, _, _ in PASOS]
            print(f"  {rotulo}, {NOM[c]}: " + " → ".join(
                f"{nombre} {n}" + (f" ({cad.pct(n, t[i - 1])})" if i else "")
                for i, (n, (_, _, nombre)) in enumerate(zip(t, PASOS))))
    for c in ("NA", "NC"):
        print(f"  por semilla, 31-{G}, {c}: " + " | ".join(
            f"s{s} " + " · ".join(str(cad.suma(D[s][c]["co"], DESDE, col)) for col, _, _ in PASOS) for s in SEMILLAS))

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio, gens {W[0]}-{W[-1]}: edad promedio · distancia promedio · manzanas; f_acercarse promedio por "
          f"agente (NA mide el camino, NC la recta)")
    for c in NOM:
        fa = st.mean(float(f["f_acercarse"]) for s in SEMILLAS for f in D[s][c]["ag"] if f["gen"] in set(W))
        print(f"  {NOM[c]}: " + " · ".join(
            f"{prom(lambda s: sl.columna(D[s][c]['co'], W, k)):.1f}" for k in ("edad_prom", "distancia_prom"))
            + f" · manzanas {prom(lambda s: al.comida(D[s][c]['co'], W)):.3f} · f_acercarse {fa:.2f}")

    # ---------- Controles ----------
    print("\n### Controles")
    for s in SEMILLAS:
        partes = []
        for c in ("NC", "NCB0"):
            r = D[s][c]["rutas"]
            ok = (al.sha(r["corrida"]), al.sha(r["agentes"]), al.sha(r["geometria"])) == SHA[c][s]
            errores += not ok
            partes.append(f"{c}, SHA-256 publicado {ok}")
        if not prueba:
            # La gen 1: la misma población inicial y el mismo mundo, así que NA es NC salvo el fitness
            d, n = D[s]["NA"], D[s]["NC"]
            dif = gen1_distinta(d["co"][0], n["co"][0], FITNESS_CO)
            # El orden de las filas de agentes_*.csv sale del fitness: se alinean por id
            a1, n1 = (sorted((f for f in x["ag"] if f["gen"] == 1), key=lambda f: int(f["id"])) for x in (d, n))
            dif_ag = sorted({k for a, b in zip(a1, n1) for k in gen1_distinta(a, b, FITNESS_AG)})
            fit = sum(a["fitness"] != b["fitness"] for a, b in zip(a1, n1))
            errores += bool(dif) + bool(dif_ag) + (len(a1) != len(n1)) + (fit == 0)
            partes.append(f"gen 1 de NA = la de NC salvo el fitness: corrida {'sí' if not dif else dif}, agentes "
                          f"{'sí' if not dif_ag else dif_ag} ({fit} de {len(a1)} con otro fitness)")
            filas = len(d["ag"]) == 60 * G and len(d["co"]) == G and len(d["ge"]) == G
            etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["co"] + d["ag"])
            pasos = 0
            for f in d["co"]:
                filas_g = [x for x in d["ag"] if x["gen"] == f["gen"]]
                pasos += int(f["agentes_puerta_madera"]) != sum(int(x["abrio"]) for x in filas_g)
                pasos += sum(int(f[col]) != sum(int(x["etapa"]) >= e for x in filas_g) for col, e, _ in PASOS)
            switches = all(x.get("brujula_camino") == "1" and x.get("acercarse_camino") == "1" for x in d["ag"] + d["ge"])
            pesos = all(x["pesos"].endswith(",HIT_ENERGY_COST:0") for x in d["ag"])
            with open(os.path.join(tanda, f"log_s{s}_evolucion.txt"), encoding="utf-8", errors="replace") as fl:
                log = fl.read()
            en_log = "'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            e = cad.energia(log)
            costo0 = bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6 and float(e[4]) == 0
            errores += ((not filas) + etapa + pasos + (not switches) + (not pesos) + (not en_log)
                        + (medicion != [("0", str(60 * G))]) + (not costo0))
            partes.append(f"NA: filas {filas}, etapa_inicial distinta {etapa}, agentes_* distintos {pasos}, "
                          f"brujula_camino y acercarse_camino = 1 {switches}, pesos {pesos}, log {en_log}, "
                          f"MEDICION {medicion}, costo 0 {costo0}")
        print(f"  s{s}: " + " | ".join(partes))
    if prueba:
        chequeos = [(f"{col}, NC · NCB0, {W[0]}-{W[-1]}", dio[col], v) for col, v in PUBLICADO["criterio"].items()]
        chequeos += [(f"la puerta de madera, NC · NCB0, 31-{G}", (dio["madera_NA"], dio["madera_NCB0"]),
                      PUBLICADO["madera"]),
                     (f"la puerta de hierro de NC, 31-{G}", dio["hierro_NA"], PUBLICADO["hierro_NC"])]
        chequeos += [(f"{col} de NC, 31-{G}", tuple(cad.suma(D[s]["NA"]["co"], DESDE, col) for s in SEMILLAS), v)
                     for col, v in PUBLICADO["cadena_NC"].items()]
        for nombre, valor, pub in chequeos:
            errores += tuple(valor) != tuple(pub)
            print(f"  publicado, {nombre}: {valor} (publicado {pub}) {tuple(valor) == tuple(pub)}")
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
