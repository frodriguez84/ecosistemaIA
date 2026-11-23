"""La brújula por el camino (docs/qa/AnalisisQA.md#brujula-camino): los pasos 2 a 6 con la brújula nueva, contra su línea
base, a partir de los CSV de medir_puerta.py con hierro y brujula-camino.

- NC, la referencia sin costo con la brújula por el camino (con evolución), contra NCB0, su línea base sin evolución, también
  con la brújula por el camino: el criterio de la decisión 5 del spec PUZZLE_SOLOS, en los pasos 2 a 6, en las gens 146-150.
- N0, la referencia sin costo, con las columnas h_ (results/medicion_hierro_20261122: la misma corrida que N0), y NB0, su
  línea base sin costo (results/medicion_base_sin_costo_20261122): lo que cambia la brújula, sin criterio, y la medida
  independiente del paso 5 (de los que tienen la llave dorada, la parte que llega a 25 px de la puerta de hierro, NC contra
  N0, en las 31-150).

Las medidas independientes de los otros pasos, contra NCB0: por 1.000 px (la llave roja, la llave dorada y el cofre, la
cuenta de analizar_cadena.py) y, en la puerta de madera, la parte que llega a 25 px de los que tienen la llave roja, en las
31-150 (en las 146-150 la línea base tiene ~30 con la llave: LEC-024).

Uso: python mediciones/analizar_brujula_camino.py TANDA HIERRO BASE
TANDA tiene los CSV y los logs de NC y NCB0 (log_s{S}_evolucion.txt y log_s{S}_sin_evolucion.txt); HIERRO, los de N0 con
hierro; BASE, los de NB0. Con TANDA igual a HIERRO, la prueba del script: NC es N0 y NCB0 es NB0, y tiene que dar lo
publicado (lo controla solo, en PUBLICADO) con 0 errores.
"""
import os
import re
import statistics as st
import sys

import analizar_cadena as cad
import analizar_costo_golpe as cg
import analizar_hierro as hi
import analizar_largas as al
import analizar_sin_llave as sl

SEMILLAS = (1, 2, 3, 4, 5)
MINIMO = 1.0  # agentes por generación que dan el paso (el tamaño mínimo de la decisión 5)
PASOS = cad.PASOS  # los pasos 2 a 6 del spec, con su columna, la etapa que los marca y su nombre
NOM = dict(NC="Con la brújula por el camino (NC)", NCB0="Su línea base (NCB0)", N0="Referencia sin costo (N0)",
           NB0="Línea base sin costo (NB0)")
COLA = "_acercarse_deslizar_moviles_brujula_camino_curriculo30"
NC_NOMBRE = "s{s}" + COLA + "_cruce0.2_pesos-ACERCARSE40-EXPLORATION0-ANTI_CIRCLE0-HIT_ENERGY_COST0_evolucion.csv"
NCB0_NOMBRE = "s{s}" + COLA + "_pesos-ACERCARSE40-EXPLORATION0-ANTI_CIRCLE0-HIT_ENERGY_COST0_sin_evolucion.csv"
# Lo publicado: #cadena-sin-costo (el criterio de N0 contra NB0 en las 146-150, la llave roja, "En la puerta" y la cadena de
# las 31-150) y #medicion-puerta-hierro (con la llave dorada y ticks en la etapa 3, llegan y la abren, en las 31-150; el
# seguidor desde la llave dorada, en los 600 mapas de las 31-150, como hoy y deslizando)
PUBLICADO = dict(
    criterio=dict(agentes_puerta_madera=((9.8, 10.2, 3.2, 6.0, 8.8), (0.2, 0, 0, 0, 0)),
                  agentes_llave_dorada=((6.0, 5.0, 1.4, 3.0, 4.6), (0,) * 5),
                  agentes_puerta_hierro=((0, 0, 0.2, 0.4, 0.2), (0,) * 5),
                  agentes_cofre=((0, 0, 0, 0.4, 0), (0,) * 5)),
    llave_roja=(42.5, 1.24), puerta_en_N0=("29%", "83%", "61%"),
    cadena_N0=dict(agentes_llave_dorada=(575, 317, 11, 290, 863), agentes_puerta_hierro=(4, 0, 1, 6, 10),
                   agentes_cofre=(3, 0, 0, 4, 0)),
    hierro_N0=(2053, 29, 21), seguidor_N0=(1, 12, 600))
# El SHA-256 publicado de NB0 (#cadena-sin-costo) y de los agentes_*.csv y geometria_*.csv de la tanda con hierro
# (#medicion-puerta-hierro); los corrida_*.csv de la tanda con hierro son los de N0 (analizar_comida.SHA)
SHA_NB0 = {1: ("485981540f2731725c5c7537f07499107a15dabddfcfb09c33bb468899afc061",
               "186aa93a610f34e8eca20192a7328d939ad11e68eae59a3688b76fd65c20c0e1"),
           2: ("b1befc2871d4476d0528380f1739cf8a8e21d572fdccc8a44ed4a959d005fde1",
               "7d24d743d58f5524b915de08786b3d4c4c43daaa6b7dd3e6d11650eb8f660038"),
           3: ("11c03da69cf847957a99d4a8b4fa23f073794fea86a3bb3a149a0d1205cbfc04",
               "6045fd6d8fb715d9d1b8e7b5295ce9b1172a4631d9c3710f3f34c94a9df269bb"),
           4: ("8e791c066f67cdf6e5e205a33a48602042212d9ed91a7969e9734ed7042ac34d",
               "6453635300cafed93990d7e8b491473368e51b9addd9657b6801a46dcf34856e"),
           5: ("e0e7c44a2a73187a7f08e0effae7705fad3b5d28e879bed004d9d8d2ec230eed",
               "3493396351de6b522300dc3d6ccc5c8e72962c22edfce6a802e56590d035709d")}
SHA_HIERRO = {1: ("6be85ffc6fecb3d6ec10d86c388794016daed4030a9d102335572373bdb2d656",
                  "36a5acd133bf4f9d70532865fec1d1706cfc8eb74b36bdcea2b6389dd36ac540"),
              2: ("4006a4a4d195be597f191561c017ac66a5849ae7e62a0a47be717e55d426e07b",
                  "87e5a2da42ebf01435ac5f8d5b2938494792f611b6b36d797ba81340d9c38497"),
              3: ("0b3c822201a17f093a1b468c5e2e83cad6d51601317db030938b73ef0f408709",
                  "a8948e4d2673bf753db7f4096d7856a2a1c6004a0aaccaff1cace9f9d1fa1cd6"),
              4: ("58f22783bfb7c5028b193ff0794800c48dd4493e04ca2e3f72891687bddabe29",
                  "f6d65e06176ae88292b4b7d61b3990054477510e4ed53b46cdaf14da4b633f83"),
              5: ("2f1b74c7683814c1006cef2f04005e5f089219dca867a1dd0bb6bba29bc44c4e",
                  "e95fe67702e205b0b4224f3fef73e716721fb46dc11c4d35bd11a5fde17ff1ea")}


def cargar(carpeta, nombre, geometria=True):
    tipos = ("corrida", "agentes") + (("geometria",) if geometria else ())
    rutas = {t: os.path.join(carpeta, f"{t}_{nombre}") for t in tipos}
    for r in rutas.values():
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    return dict(co=al.leer(rutas["corrida"]), ag=hi.leer_csv(rutas["agentes"]),
                ge=hi.leer_csv(rutas["geometria"]) if geometria else [], rutas=rutas)


def llegan_madera(ag, gens):
    """De los que tienen la llave roja (etapa ≥ 1), los que llegan a 25 px de la puerta de madera (ticks_25 > 0)."""
    gens = set(gens)
    F = [f for f in ag if f["gen"] in gens and int(f["etapa"]) >= 1]
    return len(F), sum(int(f["ticks_25"]) > 0 for f in F)


def hierro(ag, gens):
    """De los que tienen la llave dorada y ticks en la etapa 3 (h_ticks > 0), los que llegan a 25 px de la puerta de hierro
    (h_dmin < 25) y los que la abren (etapa ≥ 4)."""
    gens = set(gens)
    F = [f for f in ag if f["gen"] in gens and hi.tiene(f, "hierro")]
    return len(F), sum(hi.num(f, "h_dmin") < hi.RADIO for f in F), sum(int(f["etapa"]) >= 4 for f in F)


def seguidor(ge, gens):
    """En cuántos mapas el seguidor de brújula perfecto llega de la llave dorada a la puerta de hierro, como hoy y
    deslizando, y cuántos mapas son; y la parte de los arranques que llega a la puerta de madera deslizando."""
    gens = set(gens)
    G = [g for g in ge if g["gen"] in gens]
    madera = sum(int(g["desliza_25"]) for g in G) / sum(int(g["arranques"]) for g in G)
    return sum(g["h_seguidor_t25"] != "" for g in G), sum(g["h_desliza_t25"] != "" for g in G), len(G), madera


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    tanda, hierro_dir, base = sys.argv[1:4]
    prueba = os.path.samefile(tanda, hierro_dir)  # NC es N0 y NCB0 es NB0: la prueba del script
    D = {}
    for s in SEMILLAS:
        n0 = cargar(hierro_dir, cg.nombre(s, 30, costo0=True))
        nb0 = cargar(base, cad.NB0_NOMBRE.format(s=s), geometria=False)
        D[s] = dict(N0=n0, NB0=nb0,
                    NC=n0 if prueba else cargar(tanda, NC_NOMBRE.format(s=s)),
                    NCB0=nb0 if prueba else cargar(tanda, NCB0_NOMBRE.format(s=s)))
    G = max(f["gen"] for f in D[1]["NC"]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    print(f"La brújula por el camino: semillas {list(SEMILLAS)}, {G} generaciones"
          f"{' (PRUEBA: NC es N0 y NCB0 es NB0)' if prueba else ''}; pesos de NC: {D[1]['NC']['ag'][0]['pesos']}")

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    errores = 0
    dio = {}

    # ---------- El criterio ----------
    print(f"\n### Gens {W[0]}-{W[-1]}: agentes por generación que dan el paso (entre paréntesis, por 1.000 px)")
    for col, _, nombre in PASOS:
        v = {c: {s: cad.paso(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        p = {c: {s: cad.px(D[s][c]["co"], W, col) for s in SEMILLAS} for c in NOM}
        dio[col] = (tuple(round(v["NC"][s], 1) for s in SEMILLAS), tuple(round(v["NCB0"][s], 1) for s in SEMILLAS))
        print(f"  {nombre}:")
        for c in NOM:
            print(f"    {NOM[c]}: " + " · ".join(f"s{s} {v[c][s]:.1f} ({p[c][s]:.2f})" for s in SEMILLAS)
                  + f" | promedio {st.mean(v[c].values()):.2f} ({st.mean(p[c].values()):.2f})")
        pasan = [s for s in SEMILLAS if v["NC"][s] >= MINIMO and v["NC"][s] > v["NCB0"][s]]
        acomp = all(p["NC"][s] > p["NCB0"][s] for s in pasan) if pasan else False
        ceros = bool(pasan) and all(v["NCB0"][s] == 0 for s in pasan)
        print(f"    -> NC ≥ {MINIMO:g} por generación y más que NCB0 en {len(pasan)} de 5 (semillas {pasan}; pide 4): "
              f"{'PASA' if len(pasan) >= 4 else 'NO PASA'}; por 1.000 px, NC arriba de NCB0 en todas las que pasan: "
              f"{acomp}{' (NCB0 da 0 en todas: no agrega)' if ceros else ''}")
        print(f"    NC contra N0 (sin criterio): promedio {st.mean(v['NC'].values()):.2f} contra "
              f"{st.mean(v['N0'].values()):.2f}; por semilla, NC más que N0 en "
              f"{sum(v['NC'][s] > v['N0'][s] for s in SEMILLAS)} de 5")

    # ---------- Las medidas independientes de las puertas ----------
    print(f"\n### La puerta de madera, gens 31-{G}, todas las semillas: de los que tienen la llave roja, los que llegan a 25 px")
    for c in NOM:
        F, L = (sum(x) for x in zip(*(llegan_madera(D[s][c]["ag"], DESDE) for s in SEMILLAS)))
        print(f"  {NOM[c]}: con la llave {F} · llegan {L} ({cad.pct(L, F)})")
    print(f"\n### La puerta de hierro, gens 31-{G} y {W[0]}-{W[-1]}: con la llave dorada y ticks en la etapa 3 · llegan a 25 px "
          f"· la abren")
    tiene_h = "h_ticks" in D[1]["NC"]["ag"][0]
    for c in ("NC", "N0", "NCB0"):
        if "h_ticks" not in D[1][c]["ag"][0]:
            print(f"  {NOM[c]}: sin las columnas h_")
            continue
        for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
            por = [hierro(D[s][c]["ag"], gens) for s in SEMILLAS]
            F, L, A = (sum(x) for x in zip(*por))
            if c == "N0" and gens == DESDE:
                dio["hierro_N0"] = (F, L, A)
            print(f"  {NOM[c]}, {rotulo}: con la llave {F} · llegan {L} ({cad.pct(L, F)}) · la abren {A} ({cad.pct(A, F)})"
                  f" | por semilla, llegan/con la llave: " + " · ".join(f"s{s} {x[1]}/{x[0]}" for s, x in zip(SEMILLAS, por)))
    if tiene_h:
        nc, n0 = (hierro([f for s in SEMILLAS for f in D[s][c]["ag"]], DESDE) for c in ("NC", "N0"))
        print(f"  -> la parte que llega, más alta en NC que en N0 (31-{G}): "
              f"{nc[0] > 0 and n0[0] > 0 and nc[1] / nc[0] > n0[1] / n0[0]} ({cad.pct(nc[1], nc[0])} contra "
              f"{cad.pct(n0[1], n0[0])})")
        print(f"  Dónde se traba en NC (31-{G}, la cuenta de analizar_hierro.py):")
        F, c = hi.clasificar([f for s in SEMILLAS for f in D[s]["NC"]["ag"]], "hierro", DESDE)
        hi.imprimir_grupos(c, len(F))
        print(f"    se traba en: {hi.trabado(c)}")

    # ---------- El seguidor ----------
    print(f"\n### El seguidor de brújula perfecto, gens 31-{G}: mapas donde llega de la llave dorada a la puerta de hierro, "
          f"como hoy · deslizando · de; arranques que llegan a la puerta de madera deslizando")
    for c in ("NC", "N0"):
        t = [seguidor(D[s][c]["ge"], DESDE) for s in SEMILLAS]
        hoy, desl, n = (sum(x[k] for x in t) for k in range(3))
        if c == "N0":
            dio["seguidor_N0"] = (hoy, desl, n)
        print(f"  {NOM[c]}: {hoy} · {desl} · {n} | la de madera, deslizando: " + " · ".join(
            f"s{s} {x[3]:.0%}" for s, x in zip(SEMILLAS, t)))

    # ---------- Por ventana ----------
    print("\n### Por ventana: agentes por generación que dan el paso, promedio de las semillas")
    for col, _, nombre in PASOS:
        for c in NOM:
            print(f"  {nombre}, {NOM[c]}: " + " | ".join(
                f"{a}-{b} {prom(lambda s: cad.paso(D[s][c]['co'], range(a, b + 1), col)):.2f}"
                for a, b in cad.ag.VENTANAS))

    # ---------- El embudo ----------
    print("\n### El embudo: agentes que dan cada paso, sumados (las 5 semillas), y entre paréntesis la parte de los del paso "
          "anterior")
    for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
        for c in NOM:
            t = [sum(cad.suma(D[s][c]["co"], gens, col) for s in SEMILLAS) for col, _, _ in PASOS]
            print(f"  {rotulo}, {NOM[c]}: " + " → ".join(
                f"{nombre} {n}" + (f" ({cad.pct(n, t[i - 1])})" if i else "")
                for i, (n, (_, _, nombre)) in enumerate(zip(t, PASOS))))
    print(f"  por semilla, 31-{G}, NC: " + " | ".join(
        f"s{s} " + " · ".join(str(cad.suma(D[s]["NC"]["co"], DESDE, col)) for col, _, _ in PASOS) for s in SEMILLAS))

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio, gens {W[0]}-{W[-1]}: edad promedio · manzanas · distancia promedio")
    for c in NOM:
        print(f"  {NOM[c]}: " + " · ".join(
            f"{prom(lambda s: sl.columna(D[s][c]['co'], W, k)):.1f}" for k in ("edad_prom", "distancia_prom"))
            + f" · manzanas {prom(lambda s: al.comida(D[s][c]['co'], W)):.3f}")

    # ---------- Controles ----------
    print("\n### Controles")
    for s in SEMILLAS:
        partes = []
        r0, rb = D[s]["N0"]["rutas"], D[s]["NB0"]["rutas"]
        sha = dict(N0=(al.sha(r0["corrida"]), al.sha(r0["agentes"]), al.sha(r0["geometria"])),
                   NB0=(al.sha(rb["corrida"]), al.sha(rb["agentes"])))
        ok = dict(N0=sha["N0"] == (cad.ac.SHA["N0"][s][0],) + SHA_HIERRO[s], NB0=sha["NB0"] == SHA_NB0[s])
        errores += (not ok["N0"]) + (not ok["NB0"])
        partes.append(f"N0 con hierro y NB0, SHA-256 publicado {ok['N0']} {ok['NB0']}")
        if not prueba:
            # La gen 1: la misma población inicial y el mismo mundo, así que NCB0 es NC salvo evolucion
            a, b = D[s]["NCB0"]["co"][0], D[s]["NC"]["co"][0]
            dif = [k for k in a if k not in ("evolucion", "gen", "sb") and a[k] != b[k]]
            errores += bool(dif) or a["evolucion"] == b["evolucion"]
            partes.append(f"gen 1 de NCB0 = la de NC salvo evolucion: {'sí' if not dif else dif}")
            for c in ("NC", "NCB0"):
                d = D[s][c]
                filas = len(d["ag"]) == 60 * G and len(d["co"]) == G and len(d["ge"]) == G
                etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["co"] + d["ag"])
                pasos = 0
                for f in d["co"]:
                    filas_g = [x for x in d["ag"] if x["gen"] == f["gen"]]
                    pasos += int(f["agentes_puerta_madera"]) != sum(int(x["abrio"]) for x in filas_g)
                    pasos += sum(int(f[col]) != sum(int(x["etapa"]) >= e for x in filas_g) for col, e, _ in PASOS)
                brujula = all(x.get("brujula_camino") == "1" for x in d["ag"] + d["ge"])
                pesos = all(x["pesos"].endswith(",HIT_ENERGY_COST:0") for x in d["ag"])
                tipo = "evolucion" if c == "NC" else "sin_evolucion"
                with open(os.path.join(tanda, f"log_s{s}_{tipo}.txt"), encoding="utf-8", errors="replace") as fl:
                    log = fl.read()
                en_log = "'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
                medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
                e = cad.energia(log)
                costo0 = (bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6
                          and float(e[4]) == 0)
                errores += ((not filas) + etapa + pasos + (not brujula) + (not pesos) + (not en_log)
                            + (medicion != [("0", str(60 * G))]) + (not costo0))
                partes.append(f"{c}: filas {filas}, etapa_inicial distinta {etapa}, agentes_* distintos {pasos}, "
                              f"brujula_camino=1 {brujula}, pesos {pesos}, log {en_log}, MEDICION {medicion}, costo 0 {costo0}")
        print(f"  s{s}: " + " | ".join(partes))
    if prueba:
        chequeos = [(f"{col}, N0 · NB0, {W[0]}-{W[-1]}", dio[col], v) for col, v in PUBLICADO["criterio"].items()]
        chequeos += [("la llave roja, N0 · NB0, promedio", (round(st.mean(dio["agentes_llave_roja"][0]), 1),
                                                           round(st.mean(dio["agentes_llave_roja"][1]), 2)),
                      PUBLICADO["llave_roja"]),
                     ("En la puerta de N0", tuple(x for x in _en_la_puerta(D, W)), PUBLICADO["puerta_en_N0"]),
                     (f"la puerta de hierro de N0, 31-{G}", dio["hierro_N0"], PUBLICADO["hierro_N0"]),
                     (f"el seguidor de N0, 31-{G}", dio["seguidor_N0"], PUBLICADO["seguidor_N0"])]
        chequeos += [(f"{col} de N0, 31-{G}", tuple(cad.suma(D[s]["N0"]["co"], DESDE, col) for s in SEMILLAS), v)
                     for col, v in PUBLICADO["cadena_N0"].items()]
        for nombre, valor, pub in chequeos:
            errores += tuple(valor) != tuple(pub)
            print(f"  publicado, {nombre}: {valor} (publicado {pub}) {tuple(valor) == tuple(pub)}")
    print(f"  errores: {errores}")


def _en_la_puerta(D, W):
    """"En la puerta" de N0 en la ventana, con la cuenta de analizar_cadena.py: llegan, golpean ahí y la abren."""
    F, L, gl, ab = (sum(x) for x in zip(*(cad.en_la_puerta(D[s]["N0"]["ag"], W) for s in SEMILLAS)))
    return cad.pct(L, F), cad.pct(gl, L), cad.pct(ab, L)


if __name__ == "__main__":
    main()
