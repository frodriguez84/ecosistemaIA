"""La comida al doble con el fitness sin tope (docs/qa/AnalisisQA.md#comida20-sin-tope; el paso 1 de
docs/specs/active/PUZZLE_SOLOS.md), a partir de los CSV de medir_puerta.py con sens-etapa0, hierro, brujula-camino,
acercarse-camino y fitness-sin-tope: NF, la referencia (NT) con FITNESS_FOOD en 20, contra NCB0, la línea base de la
referencia. Sin evolución, un peso del fitness no cambia lo que hacen: la línea base de NF es NCB0.

El criterio, fijado antes de lanzar (gens 146-150; por semilla, NF contra NCB0 de la misma semilla), el de
analizar_sin_tope.py con NF en el lugar de NT:
- comer, la decisión 6: la sensibilidad a la comida antes de abrir la puerta ≥ 0,02 rad/tick y más que NCB0 en 4 de 5, y
  el Spearman entre la sensibilidad y las manzanas dentro de cada generación, mediana de las 121-150 de las 5 semillas, por
  arriba del de NCB0;
- las guardas, los pasos 2 a 6 con la decisión 5: al menos 1 agente por generación que da el paso y más que NCB0, en 4 de 5,
  cada uno.
Sin criterio: cada paso y comer contra NT, lo que ve la selección, la sensibilidad por ventana, las medidas independientes
de las puertas, el embudo, la mutación adaptativa y el tope.

Las manzanas de cada agente salen de f_comida = FITNESS_FOOD × √manzanas, con el FITNESS_FOOD de su columna pesos (la cuenta
de analizar_comida20.py): analizar_comida.leer_agentes divide por 10 fijo, y con NF daría cuatro veces de más.

Uso: python mediciones/analizar_comida20_sin_tope.py TANDA REFERENCIA BASE [conteo]
TANDA tiene los CSV y los logs de NF (log_s{S}_evolucion.txt); REFERENCIA, los de NT (results/medicion_sin_tope_20261123);
BASE, los de NCB0 (results/medicion_brujula_camino_20261122). Con conteo, solo las filas medidas de la ventana y los
controles: lo que se anota antes de leer. Con TANDA igual a REFERENCIA, la prueba del script: NF es NT, y tiene que dar lo
publicado en #sin-tope (lo controla solo, en PUBLICADO) con 0 errores. Los controles propios de NF corren también en la
prueba, con lo que se espera de NT: pesos y log sin FITNESS_FOOD, y f_comida igual a la de NT.
"""
import os
import re
import statistics as st
import sys

import analizar_acercarse_camino as acc
import analizar_brujula_camino as bc
import analizar_cadena as cad
import analizar_comer_na as cna
import analizar_comida as ac
import analizar_comida20 as c20
import analizar_hierro as hi
import analizar_largas as al
import analizar_sin_llave as sl
import analizar_sin_tope as stp

SEMILLAS = bc.SEMILLAS
MINIMO = bc.MINIMO  # agentes por generación que dan el paso (el tamaño mínimo de la decisión 5)
PASOS = cad.PASOS  # los pasos 2 a 6 del spec, con su columna, la etapa que los marca y su nombre
TRAMO = cna.TRAMO  # la medida independiente de comer: el Spearman con las manzanas, mediana de las 121-150
PESO = 20.0  # el FITNESS_FOOD de NF (el de NT, ac.FITNESS_FOOD: 10)
C = ("NF", "NT", "NCB0")
NOM = dict(NF="Comida 20 (NF)", NT="Referencia (NT)", NCB0="Línea base (NCB0)")
NF_NOMBRE = stp.NT_NOMBRE.replace("_evolucion.csv", "-FOOD20_evolucion.csv")
# lo que el peso cambia en la gen 1 de agentes_*.csv (más las que agrega el lector)
FITNESS_AG = stp.FITNESS_AG + ("fitness_con_tope", "f_comida", "pesos", "sc", "sc0", "sc1", "manzanas", "sb", "sb0", "sb1")
REDONDEO = 2e-4  # f_comida va a 4 decimales: |f20 − 2 × f10| ≤ 0,00005 + 2 × 0,00005 (LEC-023)
SHA_NT = {1: ("62ac2baff3ca34e138c69bf609506f9d7576a4a3734d0eb5bd8e62357908f739",
              "0716d70de1a45f788c4121eb9949a4f833a6067bfb82ffcc4a92ceb41f5ca940"),
          2: ("d21f2a2fa8d57a56bdfd9cace88ab85b4f8295e09fc23fa8f1eb59519c929db3",
              "d605e421f65a6b1b8dfd4e248e9eb89440a97d648614cc0016c32317899fcd79"),
          3: ("9d612d4a7837137c1d0322235b77e49b68807392c38f8cd04ea24a3a4fa562e1",
              "2d588a78598c2462711a73f3af828f49b2d5e0a65f7ad0d13ab40040ad761ca2"),
          4: ("9c605e8f4caac9f45c5ff0ef97615e18b51ff79cff72e95004986619eca4ee8c",
              "e1c74fa6ea28bee5e30b6eb3484da1832f16b43b27f1a7ac2a486cc697515369"),
          5: ("6c39f421ada646aa686ed75fa83395a9c944210eea9a06db7749b2388c9b019d",
              "d4d61b645246e80b7ef46a17f994552b7e2616eda18c99341650017f4d87075a")}
# Lo publicado en #sin-tope: la sensibilidad a la comida por semilla en las 146-150 (a 4 decimales), su promedio, las
# semillas que cumplen la 1a, el Spearman con las manzanas de las 121-150 (a 3), las guardas de NT contra NCB0 en las
# 146-150, la puerta de madera de NT y NCB0 y la de hierro de NT en las 31-150, el tope de NT en las 146-150, lo de adentro
# de la generación de NT en las 121-150 (con el fitness y con la etapa) y la mutación adaptativa de NT en las 31-150
PUBLICADO = dict(
    sc=dict(NT=(-0.0288, -0.0073, 0.0311, -0.0179, -0.0131), NCB0=(0.0018, -0.0003, 0.0017, 0.0007, -0.0022)),
    promedio=dict(NT=-0.0072, NCB0=0.0003), cumple=1, spearman=dict(NT=0.097, NCB0=0.049),
    criterio=dict(agentes_llave_roja=((55.8, 57.6, 54.4, 53.6, 53.6), (1.6, 1.0, 0.6, 1.2, 1.8)),
                  agentes_puerta_madera=((49.6, 46.8, 30.4, 48.2, 44.4), (0,) * 5),
                  agentes_llave_dorada=((47.8, 45.8, 27.0, 48.2, 43.4), (0,) * 5),
                  agentes_puerta_hierro=((19.4, 25.0, 4.4, 10.8, 5.8), (0,) * 5),
                  agentes_cofre=((13.4, 22.6, 3.8, 6.6, 1.8), (0,) * 5)),
    madera=((26342, 20360), (671, 47)), hierro_NT=(16728, 8450, 4275), tope_NT="74%",
    dentro_NT=(0.049, 0.024), mutacion_NT=79)


def cargar(carpeta, nombre, geometria=False):
    """La carga de analizar_sin_tope.py, con las manzanas de cada agente divididas por el peso de su columna pesos."""
    d = stp.cargar(carpeta, nombre, geometria)
    for f in d["ag"]:
        f["manzanas"] = (float(f["f_comida"]) / c20.peso_comida(f)) ** 2
    return d


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    tanda, ref, base = sys.argv[1:4]
    conteo = len(sys.argv) > 4 and sys.argv[4] == "conteo"
    prueba = os.path.samefile(tanda, ref)  # NF es NT: la prueba del script
    D = {}
    for s in SEMILLAS:
        nt = cargar(ref, stp.NT_NOMBRE.format(s=s), geometria=True)
        D[s] = dict(NF=nt if prueba else cargar(tanda, NF_NOMBRE.format(s=s), geometria=True), NT=nt,
                    NCB0=cargar(base, bc.NCB0_NOMBRE.format(s=s)))
    G = max(f["gen"] for f in D[1]["NF"]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    print(f"La comida al doble con el fitness sin tope: semillas {list(SEMILLAS)}, {G} generaciones; ventana {W[0]}-{W[-1]}"
          f"{' (PRUEBA: NF es NT)' if prueba else ''}{' (CONTEO: antes de leer)' if conteo else ''}; pesos de NF: "
          f"{D[1]['NF']['ag'][0]['pesos']}")

    def co(s, c):
        return D[s][c]["co"]

    def ag(s, c):
        return D[s][c]["ag"]

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    errores = 0
    dio = {}

    # ---------- Las filas medidas (comer) ----------
    print(f"\n### Las filas medidas (gens {W[0]}-{W[-1]}): filas con ticks medidos · mediana de los ticks medidos (etapas 0 y "
          f"1) · de la etapa 0 · de la 1 · la parte que abre la puerta de madera")
    for c in C:
        F = [f for s in SEMILLAS for f in ag(s, c) if f["gen"] in W]
        M = [f for f in F if f["sc"] is not None]
        print(f"  {NOM[c]}: {len(M)} de {len(F)} · {al.mediana([cna.ticks(f) for f in M]):.0f} · "
              f"{al.mediana([cna.ticks(f, '0') for f in M]):.0f} · {al.mediana([cna.ticks(f, '') for f in M]):.0f} · "
              f"{100 * sum(int(f['abrio']) for f in F) / len(F):.0f}%")
        print("    por semilla, la mediana de los ticks medidos: " + " · ".join(
            f"s{s} {al.mediana([cna.ticks(f) for f in ag(s, c) if f['gen'] in W and f['sc'] is not None]):.0f}"
            for s in SEMILLAS))

    # ---------- Controles ----------
    print("\n### Controles")
    peso_nf = ac.FITNESS_FOOD if prueba else PESO
    fin_pesos = ",HIT_ENERGY_COST:0" + ("" if prueba else ",FITNESS_FOOD:20")
    fin_log = "'HIT_ENERGY_COST': 0.0" + ("}" if prueba else ", 'FITNESS_FOOD': 20.0}")
    for s in SEMILLAS:
        partes = []
        for c, sha in (("NT", SHA_NT[s]), ("NCB0", acc.SHA["NCB0"][s][:2])):
            r = D[s][c]["rutas"]
            ok = (al.sha(r["corrida"]), al.sha(r["agentes"])) == sha
            errores += not ok
            partes.append(f"{c}, SHA-256 publicado {ok}")
        for c in C:
            # Los de analizar_sin_tope.py: 60 filas por generación, las manzanas (de f_comida, con su peso) enteras y que
            # suman manzanas_prom × 60 con la tolerancia del redondeo (LEC-023), ticks en la etapa 0 desde la 31, la
            # ventana medida
            filas = {}
            for f in ag(s, c):
                filas.setdefault(f["gen"], []).append(f)
            mal_filas = sum(len(v) != ac.POBLACION for v in filas.values()) + (len(filas) != G)
            mal_suma = sum(abs(sum(f["manzanas"] for f in filas[int(r["generacion"])]) / ac.POBLACION
                               - float(r["manzanas_prom"])) > 1e-3 for r in co(s, c))
            enteras = sum(abs(f["manzanas"] - round(f["manzanas"])) > 1e-3 for f in ag(s, c))
            sin0 = sum(int(f["sens_ticks0"]) == 0 for f in ag(s, c) if f["gen"] > 30)
            sin_medir = sum(f["sc"] is None for f in ag(s, c) if f["gen"] in W)
            errores += mal_filas + mal_suma + enteras + sin0 + sin_medir
            if mal_filas + mal_suma + enteras + sin0 + sin_medir:
                partes.append(f"{c}: filas {mal_filas}, manzanas que no suman {mal_suma}, no enteras {enteras}, sin ticks en "
                              f"la etapa 0 {sin0}, sin medir {sin_medir}")
        d, n = D[s]["NF"], D[s]["NT"]
        # La gen 1: la misma población inicial y el mismo mundo, así que NF es NT salvo el fitness y lo que sale de él; el
        # peso se ve en f_comida, el doble en cada agente (LEC-029)
        dif = acc.gen1_distinta(d["co"][0], n["co"][0], cad.FITNESS)
        a1, n1 = (sorted((f for f in x["ag"] if f["gen"] == 1), key=lambda f: int(f["id"])) for x in (d, n))
        dif_ag = sorted({k for a, b in zip(a1, n1) for k in acc.gen1_distinta(a, b, FITNESS_AG)})
        manz = sum(round(a["manzanas"]) != round(b["manzanas"]) for a, b in zip(a1, n1))
        doble = sum(abs(float(a["f_comida"]) - peso_nf / ac.FITNESS_FOOD * float(b["f_comida"])) > REDONDEO
                    for a, b in zip(a1, n1))
        comen = sum(float(b["f_comida"]) > 0 for b in n1)
        fit = sum(a["fitness"] != b["fitness"] for a, b in zip(a1, n1))
        ciego = not prueba and comen == 0  # sin nadie que coma en la gen 1, el control no ve el peso
        errores += bool(dif) + bool(dif_ag) + (len(a1) != len(n1)) + manz + doble + ciego
        # Desde cuándo se separan (sin criterio): el primer fitness distinto y la primera otra columna distinta
        sep = [next((f["gen"] for f, g in zip(d["co"], n["co"]) if cond(f, g)), "-")
               for cond in (lambda f, g: f["fitness_prom"] != g["fitness_prom"],
                            lambda f, g: acc.gen1_distinta(f, g, cad.FITNESS))]
        partes.append(f"gen 1 de NF = la de NT salvo el fitness: corrida {'sí' if not dif else dif}, agentes "
                      f"{'sí' if not dif_ag else dif_ag}, manzanas distintas {manz}; f_comida × {peso_nf / ac.FITNESS_FOOD:g} "
                      f"la de NT en {len(a1) - doble} de {len(a1)} (comen en NT {comen}; con otro fitness {fit}); se separan "
                      f"en el fitness desde la gen {sep[0]} y en lo demás desde la {sep[1]}")
        filas = len(d["ag"]) == 60 * G and len(d["co"]) == G and len(d["ge"]) == G
        etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["co"] + d["ag"])
        pasos = 0
        for f in d["co"]:
            filas_g = [x for x in d["ag"] if x["gen"] == f["gen"]]
            pasos += int(f["agentes_puerta_madera"]) != sum(int(x["abrio"]) for x in filas_g)
            pasos += sum(int(f[col]) != sum(int(x["etapa"]) >= e for x in filas_g) for col, e, _ in PASOS)
        switches = all(x.get("brujula_camino") == "1" and x.get("acercarse_camino") == "1"
                       and x.get("fitness_sin_tope") == "1" for x in d["ag"] + d["ge"])
        pesos = all(x["pesos"].endswith(fin_pesos) for x in d["ag"])
        with open(os.path.join(tanda, f"log_s{s}_evolucion.txt"), encoding="utf-8", errors="replace") as fl:
            log = fl.read()
        en_log = fin_log in log and "CURRICULO_HASTA_GENERACION=30\n" in log and "CROSSOVER_RATE=0.2\n" in log
        medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
        e = cad.energia(log)
        costo0 = bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6 and float(e[4]) == 0
        errores += ((not filas) + etapa + pasos + (not switches) + (not pesos) + (not en_log)
                    + (medicion != [("0", str(60 * G))]) + (not costo0))
        partes.append(f"NF: filas {filas}, etapa_inicial distinta {etapa}, agentes_* distintos {pasos}, "
                      f"brujula_camino, acercarse_camino y fitness_sin_tope = 1 {switches}, pesos terminan en "
                      f"{fin_pesos[1:]} {pesos}, log {en_log}, MEDICION {medicion}, costo 0 {costo0}")
        print(f"  s{s}: " + " | ".join(partes))
    if conteo:
        print(f"  errores: {errores}")
        return

    sc = {c: {s: sl.val(ag(s, c), W, "sc") for s in SEMILLAS} for c in C}
    rm = {c: [r for s in SEMILLAS for r in ac.dentro(ag(s, c), TRAMO, "manzanas")] for c in C}

    # ---------- El criterio: comer ----------
    print(f"\n### El criterio, 1: comer (la decisión 6, NF contra NCB0 de la misma semilla, gens {W[0]}-{W[-1]})")
    for c in C:
        print(f"  {NOM[c]}: " + " · ".join(f"s{s} {sc[c][s]:+.4f}" for s in SEMILLAS)
              + f" | promedio {st.mean(sc[c].values()):+.4f}")
    cumplen = [s for s in SEMILLAS if sc["NF"][s] >= ac.UMBRAL and sc["NF"][s] > sc["NCB0"][s]]
    c1 = len(cumplen) >= 4
    print(f"  1a. Giran hacia la comida: ≥ {ac.UMBRAL:g} y más que NCB0 en {len(cumplen)} de 5 (pide 4; semillas "
          f"{cumplen}) -> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    mF, mB = al.mediana(rm["NF"]), al.mediana(rm["NCB0"])
    c2 = mF > mB
    print(f"  1b. Los que giran comen más que los de su generación: Spearman con las manzanas, mediana de las "
          f"{TRAMO[0]}-{TRAMO[-1]}, {mF:+.3f} ({len(rm['NF'])} generaciones) contra {mB:+.3f} de NCB0 "
          f"({len(rm['NCB0'])}) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    print(f"  Comer aprendido (los dos): {'SÍ' if c1 and c2 else 'NO'}")
    print(f"  NT con la misma cuenta (sin criterio): la 1a en "
          f"{sum(sc['NT'][s] >= ac.UMBRAL and sc['NT'][s] > sc['NCB0'][s] for s in SEMILLAS)} de 5; la 1b, "
          f"{al.mediana(rm['NT']):+.3f}; por semilla, NF más que NT en {sum(sc['NF'][s] > sc['NT'][s] for s in SEMILLAS)} de 5")
    print(f"  El Spearman con las manzanas en las {TRAMO[0]}-{TRAMO[-1]}, por semilla: " + " | ".join(
        f"{c} " + " · ".join(f"{al.mediana(ac.dentro(ag(s, c), TRAMO, 'manzanas')):+.3f}" for s in SEMILLAS) for c in C))

    # ---------- El criterio: las guardas ----------
    print(f"\n### El criterio, 2: las guardas, los pasos 2 a 6 (la decisión 5, gens {W[0]}-{W[-1]}): agentes por generación "
          f"que dan el paso (entre paréntesis, por 1.000 px)")
    guardas = {}
    for col, _, nombre in PASOS:
        v = {c: {s: cad.paso(co(s, c), W, col) for s in SEMILLAS} for c in C}
        p = {c: {s: cad.px(co(s, c), W, col) for s in SEMILLAS} for c in C}
        dio[col] = (tuple(round(v["NF"][s], 1) for s in SEMILLAS), tuple(round(v["NCB0"][s], 1) for s in SEMILLAS))
        print(f"  {nombre}:")
        for c in C:
            print(f"    {NOM[c]}: " + " · ".join(f"s{s} {v[c][s]:.1f} ({p[c][s]:.2f})" for s in SEMILLAS)
                  + f" | promedio {st.mean(v[c].values()):.2f} ({st.mean(p[c].values()):.2f})")
        pasan = [s for s in SEMILLAS if v["NF"][s] >= MINIMO and v["NF"][s] > v["NCB0"][s]]
        guardas[nombre] = len(pasan) >= 4
        acomp = all(p["NF"][s] > p["NCB0"][s] for s in pasan) if pasan else False
        ceros = bool(pasan) and all(v["NCB0"][s] == 0 for s in pasan)
        print(f"    -> NF ≥ {MINIMO:g} por generación y más que NCB0 en {len(pasan)} de 5 (semillas {pasan}; pide 4): "
              f"{'PASA' if guardas[nombre] else 'NO PASA'}; por 1.000 px, NF arriba de NCB0 en todas las que pasan: "
              f"{acomp}{' (NCB0 da 0 en todas: no agrega)' if ceros else ''}")
        print(f"    NF contra NT (sin criterio): promedio {st.mean(v['NF'].values()):.2f} contra "
              f"{st.mean(v['NT'].values()):.2f}; por semilla, NF más que NT en "
              f"{sum(v['NF'][s] > v['NT'][s] for s in SEMILLAS)} de 5")
    print(f"  Las guardas: {'pasan las 5' if all(guardas.values()) else 'NO pasan: ' + str([k for k, x in guardas.items() if not x])}")
    print(f"  NF cumple los seis pasos en la misma tanda: {'SÍ' if c1 and c2 and all(guardas.values()) else 'NO'}")

    # ---------- Sin criterio: lo que ve la selección ----------
    print("\n### Dentro de cada generación (Spearman con la sensibilidad a la comida; mediana de las generaciones del tramo "
          "de las 5 semillas, y % con r > 0): con las manzanas del agente · con el fitness (lo que ve la selección) · con la "
          "etapa en que terminan")
    for c in C:
        partes = []
        for a, b in ac.TRAMOS:
            gens = range(a, b + 1)
            rmt = [r for s in SEMILLAS for r in ac.dentro(ag(s, c), gens, "manzanas")]
            rf = [r for s in SEMILLAS for r in ac.dentro(ag(s, c), gens, "fitness")]
            re_ = [r for s in SEMILLAS for r in ac.dentro(ag(s, c), gens, "etapa")]
            if (a, b) == (TRAMO[0], TRAMO[-1]):
                dio[f"dentro_{c}"] = (round(al.mediana(rf), 3), round(al.mediana(re_), 3))
            partes.append(f"{a}-{b}: {al.mediana(rmt):+.3f} ({100 * sum(r > 0 for r in rmt) / len(rmt):.0f}%) · "
                          f"{al.mediana(rf):+.3f} ({100 * sum(r > 0 for r in rf) / len(rf):.0f}%) · "
                          + (f"{al.mediana(re_):+.3f} ({100 * sum(r > 0 for r in re_) / len(re_):.0f}%)" if re_ else "-"))
        print(f"  {NOM[c]}: " + " | ".join(partes))

    # ---------- Sin criterio: por ventana y por etapa ----------
    print("\n### Por ventana (promedio de las 5 semillas): sensibilidad a la comida · manzanas por 1.000 px · comida comida de "
          "la disponible · manzanas por agente")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: sl.val(ag(s, c), range(a, b + 1), 'sc')):+.4f} · "
            f"{prom(lambda s: ac.por_px(co(s, c), range(a, b + 1))):.3f} · "
            f"{100 * prom(lambda s: ac.comidas(co(s, c), range(a, b + 1))):.0f}% · "
            f"{prom(lambda s: al.comida(co(s, c), range(a, b + 1))):.3f}" for a, b in ac.VENTANAS))
    print("  la sensibilidad a la comida, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in ac.VENTANAS)
        for c in ("NF", "NT") for s in SEMILLAS))
    print(f"  por etapa (gens {W[0]}-{W[-1]}): " + " | ".join(
        f"{c} etapa 0 {al.media([f['sc0'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} · etapa 1 "
        f"{al.media([f['sc1'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f}" for c in C))
    print("  los pasos por ventana: " + " | ".join(
        f"{nombre}, {c} " + " ".join(f"{prom(lambda s: cad.paso(co(s, c), range(a, b + 1), col)):.2f}"
                                     for a, b in ac.VENTANAS)
        for col, _, nombre in PASOS for c in ("NF", "NT")))
    # Sumadas después de leer la tanda (sin criterio): dónde se pierde la sensibilidad, de a 5 generaciones en las 121-150,
    # por semilla; y la puerta de madera por semilla y por ventana
    bloques = [(a, a + 4) for a in range(TRAMO[0], TRAMO[-1] + 1, 5)]
    print(f"  (sumada después de leer) la sensibilidad a la comida de a 5 generaciones, {TRAMO[0]}-{TRAMO[-1]}, por "
          f"semilla: " + " | ".join(f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}"
                                                            for a, b in bloques)
                                    for c in ("NF", "NT") for s in SEMILLAS))
    print("  (sumada después de leer) la puerta de madera, por semilla y por ventana: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{cad.paso(co(s, c), range(a, b + 1), 'agentes_puerta_madera'):.1f}"
                                for a, b in ac.VENTANAS)
        for c in ("NF", "NT") for s in SEMILLAS))

    print(f"\n### Sin criterio (gens {W[0]}-{W[-1]}): manzanas por 1.000 px · comida comida de la disponible · manzanas por "
          f"agente · distancia · término de la comida · sensibilidad a la brújula (el control positivo) · edad")
    for c in C:
        print(f"  {NOM[c]}: {prom(lambda s: ac.por_px(co(s, c), W)):.3f} · {100 * prom(lambda s: ac.comidas(co(s, c), W)):.0f}% · "
              f"{prom(lambda s: al.comida(co(s, c), W)):.3f} · {prom(lambda s: sl.columna(co(s, c), W, 'distancia_prom')):.0f} · "
              f"{al.media([float(f['f_comida']) for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):.2f} · "
              f"{prom(lambda s: sl.val(ag(s, c), W)):+.4f} · {prom(lambda s: sl.columna(co(s, c), W, 'edad_prom')):.0f}")

    # ---------- Sin criterio: las puertas ----------
    print(f"\n### Las medidas independientes de las puertas, gens 31-{G}, todas las semillas")
    for c in C:
        F, L = (sum(x) for x in zip(*(bc.llegan_madera(ag(s, c), DESDE) for s in SEMILLAS)))
        dio[f"madera_{c}"] = (F, L)
        por = [bc.hierro(ag(s, c), DESDE) for s in SEMILLAS]
        Fh, Lh, Ah = (sum(x) for x in zip(*por))
        dio[f"hierro_{c}"] = (Fh, Lh, Ah)
        print(f"  {NOM[c]}: la de madera, con la llave roja {F} · llegan {L} ({cad.pct(L, F)}) | la de hierro, con la "
              f"llave dorada {Fh} · llegan {Lh} ({cad.pct(Lh, Fh)}) · la abren {Ah} ({cad.pct(Ah, Fh)}); por semilla, "
              f"llegan: " + " · ".join(cad.pct(x[1], x[0]) for x in por))
    for c in ("NF", "NT"):
        print(f"  Dónde se traba la de hierro en {c} (31-{G}, la cuenta de analizar_hierro.py):")
        F, cuenta = hi.clasificar([f for s in SEMILLAS for f in ag(s, c)], "hierro", DESDE)
        hi.imprimir_grupos(cuenta, len(F))

    print("\n### El embudo: agentes que dan cada paso, sumados (las 5 semillas), y entre paréntesis la parte de los del paso "
          "anterior")
    for gens, rotulo in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
        for c in C:
            t = [sum(cad.suma(co(s, c), gens, col) for s in SEMILLAS) for col, _, _ in PASOS]
            print(f"  {rotulo}, {NOM[c]}: " + " → ".join(
                f"{nombre} {n}" + (f" ({cad.pct(n, t[i - 1])})" if i else "")
                for i, (n, (_, _, nombre)) in enumerate(zip(t, PASOS))))

    # ---------- Sin criterio: el tope y la mutación adaptativa ----------
    print(f"\n### El tope: la parte de los agentes con el fitness de 0 a 100 en {stp.TOPE:g} (no ordena: es el que leen la "
          f"mutación y la guía) · el fitness que ordena, promedio · la mediana por la etapa en que terminan (0 a 5)")
    for c in C:
        def tope(gens):
            F = [f for s in SEMILLAS for f in ag(s, c) if f["gen"] in gens]
            return sum(stp.con_tope(f) >= stp.TOPE - 1e-4 for f in F) / len(F)
        F = [f for s in SEMILLAS for f in ag(s, c) if f["gen"] in W]
        dio[f"tope_{c}"] = f"{tope(W):.0%}"
        print(f"  {NOM[c]}: " + " | ".join(f"{a}-{b} {tope(range(a, b + 1)):.0%}" for a, b in ac.VENTANAS)
              + f" || {W[0]}-{W[-1]}: fitness {st.mean(float(f['fitness']) for f in F):.1f}; por etapa " + " · ".join(
                  f"{e}: {al.mediana([float(f['fitness']) for f in F if int(f['etapa']) == e]):.0f}"
                  f" ({sum(int(f['etapa']) == e for f in F)})" for e in range(6)))
    print(f"\n### La mutación adaptativa: generaciones en que el desvío del fitness de 0 a 100 sobre su promedio baja de "
          f"{stp.CV_MUTACION:g} (la tasa sube), de las 150 del tramo con las 5 semillas")
    for c in C:
        dio[f"mutacion_{c}"] = sum(stp.mutacion(ag(s, c), DESDE) for s in SEMILLAS)
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b} {sum(stp.mutacion(ag(s, c), range(a, b + 1)) for s in SEMILLAS)}" for a, b in ac.TRAMOS)
              + f" || 31-{G}: {dio[f'mutacion_{c}']} de {5 * len(DESDE)}")

    if prueba:
        chequeos = [(f"la sensibilidad a la comida de {c}, por semilla", tuple(round(sc[x][s], 4) for s in SEMILLAS),
                     PUBLICADO["sc"][c]) for c, x in (("NT", "NF"), ("NCB0", "NCB0"))]
        chequeos += [(f"su promedio, {c}", (round(st.mean(sc[x].values()), 4),), (PUBLICADO["promedio"][c],))
                     for c, x in (("NT", "NF"), ("NCB0", "NCB0"))]
        chequeos += [("la 1a, semillas que cumplen", (len(cumplen),), (PUBLICADO["cumple"],))]
        chequeos += [(f"el Spearman con las manzanas, {TRAMO[0]}-{TRAMO[-1]}, {c}", (round(al.mediana(rm[x]), 3),),
                      (PUBLICADO["spearman"][c],)) for c, x in (("NT", "NF"), ("NCB0", "NCB0"))]
        chequeos += [(f"{col}, NT · NCB0, {W[0]}-{W[-1]}", dio[col], v) for col, v in PUBLICADO["criterio"].items()]
        chequeos += [(f"la puerta de madera, NT · NCB0, 31-{G}", (dio["madera_NF"], dio["madera_NCB0"]),
                      PUBLICADO["madera"]),
                     (f"la puerta de hierro de NT, 31-{G}", dio["hierro_NF"], PUBLICADO["hierro_NT"]),
                     (f"el tope de NT, {W[0]}-{W[-1]}", dio["tope_NF"], PUBLICADO["tope_NT"]),
                     (f"adentro de la generación de NT, {TRAMO[0]}-{TRAMO[-1]}, con el fitness y con la etapa",
                      dio["dentro_NF"], PUBLICADO["dentro_NT"]),
                     (f"la mutación adaptativa de NT, 31-{G}", dio["mutacion_NF"], PUBLICADO["mutacion_NT"])]
        print("\n### Lo publicado (#sin-tope)")
        for nombre, valor, pub in chequeos:
            errores += valor != pub
            print(f"  {nombre}: {valor} (publicado {pub}) {valor == pub}")
    print(f"\n  errores: {errores}")


if __name__ == "__main__":
    main()
