"""La comida que rebrota (docs/qa/AnalisisQA.md#rebrota; el paso 1 de docs/specs/active/PUZZLE_SOLOS.md), a partir de los
CSV de medir_puerta.py con sens-etapa0, hierro, brujula-camino, acercarse-camino, fitness-sin-tope y comida-rebrota: NR, la
referencia (NT) con la comida que rebrota, contra NRB0, su línea base (NCB0 con la comida que rebrota). Sin evolución, la
comida que rebrota cambia lo que hacen (comen más y viven más): la línea base de NR es NRB0, no NCB0.

El criterio, fijado antes de lanzar (gens 146-150; por semilla, NR contra NRB0 de la misma semilla), el de
analizar_comida20_sin_tope.py con NR en el lugar de NF y NRB0 en el de NCB0:
- comer, la decisión 6: la sensibilidad a la comida antes de abrir la puerta ≥ 0,02 rad/tick y más que NRB0 en 4 de 5, y
  el Spearman entre la sensibilidad y las manzanas dentro de cada generación, mediana de las 121-150 de las 5 semillas, por
  arriba del de NRB0;
- las guardas, los pasos 2 a 6 con la decisión 5: al menos 1 agente por generación que da el paso y más que NRB0, en 4 de
  5, cada uno.
Sin criterio: NR contra NT y NRB0 contra NCB0 (cuánto cambia la línea base); cuánto viven y cuánto duran las generaciones;
la comida comida de la disponible, con las que volvieron (rebrotes de geometria_*.csv); la sensibilidad y la puerta de
madera por semilla y por ventana; lo que ve la selección, las puertas, el embudo, el tope y la mutación adaptativa.

Uso: python mediciones/analizar_rebrota.py TANDA REFERENCIA BASE [conteo]
TANDA tiene los CSV y los logs de NR (log_s{S}_evolucion.txt) y de NRB0 (log_s{S}_sin_evolucion.txt); REFERENCIA, los de
NT (results/medicion_sin_tope_20261123); BASE, los de NCB0 (results/medicion_brujula_camino_20261122). Con conteo, solo las
filas medidas de la ventana y los controles: lo que se anota antes de leer. Con TANDA igual a REFERENCIA, la prueba del
script: NR es NT y NRB0 es NCB0, y tiene que dar lo publicado en #sin-tope (lo controla solo) con 0 errores. Los controles
propios de NR y NRB0 corren también en la prueba, con lo que se espera de NT y NCB0: sin las columnas comida_rebrota ni
rebrotes, y con los logs de la carpeta de cada uno.
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
import analizar_comida20_sin_tope as nf
import analizar_hierro as hi
import analizar_largas as al
import analizar_sin_llave as sl
import analizar_sin_tope as stp

SEMILLAS = bc.SEMILLAS
MINIMO = bc.MINIMO  # agentes por generación que dan el paso (el tamaño mínimo de la decisión 5)
PASOS = cad.PASOS  # los pasos 2 a 6 del spec, con su columna, la etapa que los marca y su nombre
TRAMO = cna.TRAMO  # la medida independiente de comer: el Spearman con las manzanas, mediana de las 121-150
C = ("NR", "NT", "NRB0", "NCB0")
NOM = dict(NR="Rebrota (NR)", NT="Referencia (NT)", NRB0="Línea base con rebrote (NRB0)", NCB0="Línea base de NT (NCB0)")
NR_NOMBRE = stp.NT_NOMBRE.replace("_sin_tope_", "_sin_tope_rebrota_")
NRB0_NOMBRE = bc.NCB0_NOMBRE.replace("_brujula_camino_", "_brujula_camino_rebrota_")
SOLO_REBROTE = ("rebrotes", "comida_rebrota")  # lo que el switch agrega a geometria_*.csv


def comidas(co, ge, gens):
    """Las manzanas comidas de las disponibles, promedio por generación: la cuenta de analizar_comida.comidas (las 70, más 20
    por árbol talado), más las que volvieron en la generación (rebrotes de geometria_*.csv; sin la columna, 0)."""
    reb = {g["gen"]: int(g.get("rebrotes") or 0) for g in ge}
    return st.mean(float(f["manzanas_prom"]) * ac.POBLACION
                   / (ac.MANZANAS + ac.POR_ARBOL * int(f["arboles_cortados"]) + reb[f["gen"]])
                   for f in co if f["gen"] in gens)


def rebrotes(ge, gens):
    return st.mean(int(g.get("rebrotes") or 0) for g in ge if g["gen"] in gens)


def horas(log):
    """El tiempo de la corrida, del último 'Tiempo real acumulado' del log."""
    t = re.findall(r"Tiempo real acumulado: (\d+)m (\d+)s", log)
    return (int(t[-1][0]) * 60 + int(t[-1][1])) / 3600 if t else float("nan")


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    tanda, ref, base = sys.argv[1:4]
    conteo = len(sys.argv) > 4 and sys.argv[4] == "conteo"
    prueba = os.path.samefile(tanda, ref)  # NR es NT y NRB0 es NCB0: la prueba del script
    D, LOGS = {}, {}
    for s in SEMILLAS:
        nt = nf.cargar(ref, stp.NT_NOMBRE.format(s=s), geometria=True)
        ncb0 = nf.cargar(base, bc.NCB0_NOMBRE.format(s=s), geometria=True)
        D[s] = dict(NR=nt if prueba else nf.cargar(tanda, NR_NOMBRE.format(s=s), geometria=True), NT=nt,
                    NRB0=ncb0 if prueba else nf.cargar(tanda, NRB0_NOMBRE.format(s=s), geometria=True), NCB0=ncb0)
        for c, carpeta, tipo in (("NR", ref if prueba else tanda, "evolucion"), ("NT", ref, "evolucion"),
                                 ("NRB0", base if prueba else tanda, "sin_evolucion"), ("NCB0", base, "sin_evolucion")):
            with open(os.path.join(carpeta, f"log_s{s}_{tipo}.txt"), encoding="utf-8", errors="replace") as fl:
                LOGS[s, c] = fl.read()
    G = max(f["gen"] for f in D[1]["NR"]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    print(f"La comida que rebrota: semillas {list(SEMILLAS)}, {G} generaciones; ventana {W[0]}-{W[-1]}"
          f"{' (PRUEBA: NR es NT y NRB0 es NCB0)' if prueba else ''}{' (CONTEO: antes de leer)' if conteo else ''}")

    def co(s, c):
        return D[s][c]["co"]

    def ag(s, c):
        return D[s][c]["ag"]

    def ge(s, c):
        return D[s][c]["ge"]

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
    for s in SEMILLAS:
        partes = []
        for c, sha in (("NT", nf.SHA_NT[s]), ("NCB0", acc.SHA["NCB0"][s][:2])):
            r = D[s][c]["rutas"]
            ok = (al.sha(r["corrida"]), al.sha(r["agentes"])) == sha
            errores += not ok
            partes.append(f"{c}, SHA-256 publicado {ok}")
        for c in C:
            # Los de analizar_comida20_sin_tope.py: 60 filas por generación, las manzanas (de f_comida, con su peso) enteras
            # y que suman manzanas_prom × 60 con la tolerancia del redondeo (LEC-023), ticks en la etapa 0 desde la 31, la
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
        for c, b, evolucion in (("NR", "NT", True), ("NRB0", "NCB0", False)):
            d, n = D[s][c], D[s][b]
            # El switch se ve (LEC-029): las que volvieron, en la gen 1 y en total, y nunca más que las comidas de la
            # generación. En la prueba (sin el switch) no está la columna
            con_col = all("rebrotes" in g and g.get("comida_rebrota") == "1" for g in d["ge"])
            sin_col = not any(k in g for g in d["ge"] for k in SOLO_REBROTE)
            reb = {g["gen"]: int(g.get("rebrotes") or 0) for g in d["ge"]}
            mas_que_comidas = sum(reb[int(r["generacion"])] > round(float(r["manzanas_prom"]) * ac.POBLACION)
                                  for r in d["co"])
            en_cero = sum(v == 0 for v in reb.values())
            ve = reb.get(1, 0) > 0 and sum(reb.values()) > 0
            errores += (not sin_col if prueba else (not con_col) + (not ve)) + mas_que_comidas
            # La gen 1 nace igual (la misma semilla, y el rebrote no consume azar hasta la primera vuelta): los mismos
            # agentes y el mismo mapa; si nadie taló en las dos, la misma geometría al final de la gen 1
            ids = sorted(int(f["id"]) for f in d["ag"] if f["gen"] == 1) == sorted(int(f["id"]) for f in n["ag"]
                                                                                    if f["gen"] == 1)
            talan = int(d["co"][0]["arboles_cortados"]) + int(n["co"][0]["arboles_cortados"])
            g1 = [k for k in (set(d["ge"][0]) & set(n["ge"][0])) - set(SOLO_REBROTE) if d["ge"][0][k] != n["ge"][0][k]]
            errores += (not ids) + (bool(g1) and talan == 0)
            # Desde cuándo se separan (sin criterio): el mapa (la geometría) y la corrida
            sep_mapa = next((g["gen"] for g, h in zip(d["ge"], n["ge"])
                             if any(g[k] != h[k] for k in (set(g) & set(h)) - set(SOLO_REBROTE))), "-")
            sep_co = next((f["gen"] for f, g in zip(d["co"], n["co"]) if acc.gen1_distinta(f, g, ())), "-")
            filas = len(d["ag"]) == 60 * G and len(d["co"]) == G and len(d["ge"]) == G
            etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in d["co"] + d["ag"])
            pasos = 0
            for f in d["co"]:
                filas_g = [x for x in d["ag"] if x["gen"] == f["gen"]]
                pasos += int(f["agentes_puerta_madera"]) != sum(int(x["abrio"]) for x in filas_g)
                pasos += sum(int(f[col]) != sum(int(x["etapa"]) >= e for x in filas_g) for col, e, _ in PASOS)
            claves = ("brujula_camino", "acercarse_camino", "fitness_sin_tope") if evolucion else ("brujula_camino",)
            switches = all(x.get(k) == "1" for x in d["ag"] + d["ge"] for k in claves)
            pesos = all(x["pesos"].endswith(",HIT_ENERGY_COST:0") for x in d["ag"])
            log = LOGS[s, c]
            en_log = ("'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
                      and (("CROSSOVER_RATE=0.2\n" in log) == evolucion))
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            e = cad.energia(log)
            costo0 = bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6 and float(e[4]) == 0
            errores += ((not filas) + etapa + pasos + (not switches) + (not pesos) + (not en_log)
                        + (medicion != [("0", str(60 * G))]) + (not costo0))
            partes.append(f"{c}: rebrotes {'sin la columna ' + str(sin_col) if prueba else str(con_col)}, en la gen 1 "
                          f"{reb.get(1, 0)}, en total {sum(reb.values())}, gens en 0 {en_cero}, más que las comidas "
                          f"{mas_que_comidas}; gen 1 como {b}: los mismos agentes {ids}, geometría distinta "
                          f"{g1 or 'no'} (talados {talan}); se separan en el mapa desde la gen {sep_mapa} y en la corrida "
                          f"desde la {sep_co}; filas {filas}, etapa_inicial distinta {etapa}, agentes_* distintos {pasos}, "
                          f"{', '.join(claves)} = 1 {switches}, pesos {pesos}, log {en_log}, MEDICION {medicion}, "
                          f"costo 0 {costo0}")
        print(f"  s{s}: " + " | ".join(partes))
    if conteo:
        print(f"  errores: {errores}")
        return

    sc = {c: {s: sl.val(ag(s, c), W, "sc") for s in SEMILLAS} for c in C}
    rm = {c: [r for s in SEMILLAS for r in ac.dentro(ag(s, c), TRAMO, "manzanas")] for c in C}

    # ---------- El criterio: comer ----------
    print(f"\n### El criterio, 1: comer (la decisión 6, NR contra NRB0 de la misma semilla, gens {W[0]}-{W[-1]})")
    for c in C:
        print(f"  {NOM[c]}: " + " · ".join(f"s{s} {sc[c][s]:+.4f}" for s in SEMILLAS)
              + f" | promedio {st.mean(sc[c].values()):+.4f}")
    cumplen = [s for s in SEMILLAS if sc["NR"][s] >= ac.UMBRAL and sc["NR"][s] > sc["NRB0"][s]]
    c1 = len(cumplen) >= 4
    print(f"  1a. Giran hacia la comida: ≥ {ac.UMBRAL:g} y más que NRB0 en {len(cumplen)} de 5 (pide 4; semillas "
          f"{cumplen}) -> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    mR, mB = al.mediana(rm["NR"]), al.mediana(rm["NRB0"])
    c2 = mR > mB
    print(f"  1b. Los que giran comen más que los de su generación: Spearman con las manzanas, mediana de las "
          f"{TRAMO[0]}-{TRAMO[-1]}, {mR:+.3f} ({len(rm['NR'])} generaciones) contra {mB:+.3f} de NRB0 "
          f"({len(rm['NRB0'])}) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    print(f"  Comer aprendido (los dos): {'SÍ' if c1 and c2 else 'NO'}")
    print(f"  NT contra NCB0 con la misma cuenta (sin criterio): la 1a en "
          f"{sum(sc['NT'][s] >= ac.UMBRAL and sc['NT'][s] > sc['NCB0'][s] for s in SEMILLAS)} de 5; la 1b, "
          f"{al.mediana(rm['NT']):+.3f} contra {al.mediana(rm['NCB0']):+.3f}; por semilla, NR más que NT en "
          f"{sum(sc['NR'][s] > sc['NT'][s] for s in SEMILLAS)} de 5")
    print(f"  El Spearman con las manzanas en las {TRAMO[0]}-{TRAMO[-1]}, por semilla: " + " | ".join(
        f"{c} " + " · ".join(f"{al.mediana(ac.dentro(ag(s, c), TRAMO, 'manzanas')):+.3f}" for s in SEMILLAS) for c in C))

    # ---------- El criterio: las guardas ----------
    print(f"\n### El criterio, 2: las guardas, los pasos 2 a 6 (la decisión 5, gens {W[0]}-{W[-1]}): agentes por generación "
          f"que dan el paso (entre paréntesis, por 1.000 px)")
    guardas = {}
    for col, _, nombre in PASOS:
        v = {c: {s: cad.paso(co(s, c), W, col) for s in SEMILLAS} for c in C}
        p = {c: {s: cad.px(co(s, c), W, col) for s in SEMILLAS} for c in C}
        dio[col] = (tuple(round(v["NR"][s], 1) for s in SEMILLAS), tuple(round(v["NRB0"][s], 1) for s in SEMILLAS))
        print(f"  {nombre}:")
        for c in C:
            print(f"    {NOM[c]}: " + " · ".join(f"s{s} {v[c][s]:.1f} ({p[c][s]:.2f})" for s in SEMILLAS)
                  + f" | promedio {st.mean(v[c].values()):.2f} ({st.mean(p[c].values()):.2f})")
        pasan = [s for s in SEMILLAS if v["NR"][s] >= MINIMO and v["NR"][s] > v["NRB0"][s]]
        guardas[nombre] = len(pasan) >= 4
        acomp = all(p["NR"][s] > p["NRB0"][s] for s in pasan) if pasan else False
        ceros = bool(pasan) and all(v["NRB0"][s] == 0 for s in pasan)
        print(f"    -> NR ≥ {MINIMO:g} por generación y más que NRB0 en {len(pasan)} de 5 (semillas {pasan}; pide 4): "
              f"{'PASA' if guardas[nombre] else 'NO PASA'}; por 1.000 px, NR arriba de NRB0 en todas las que pasan: "
              f"{acomp}{' (NRB0 da 0 en todas: no agrega)' if ceros else ''}")
        print(f"    NR contra NT (sin criterio): promedio {st.mean(v['NR'].values()):.2f} contra "
              f"{st.mean(v['NT'].values()):.2f}; por semilla, NR más que NT en "
              f"{sum(v['NR'][s] > v['NT'][s] for s in SEMILLAS)} de 5")
    print(f"  Las guardas: {'pasan las 5' if all(guardas.values()) else 'NO pasan: ' + str([k for k, x in guardas.items() if not x])}")
    print(f"  NR cumple los seis pasos en la misma tanda: {'SÍ' if c1 and c2 and all(guardas.values()) else 'NO'}")

    # ---------- Sin criterio: el tiempo y la comida ----------
    print("\n### Cuánto viven y cuánto comen, por ventana (promedio de las 5 semillas): ticks de la generación · edad · vivos "
          "al final · manzanas por agente · las que volvieron · comida comida de la disponible (con las que volvieron)")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: sl.columna(co(s, c), range(a, b + 1), 'ticks')):.0f} · "
            f"{prom(lambda s: sl.columna(co(s, c), range(a, b + 1), 'edad_prom')):.0f} · "
            f"{prom(lambda s: sl.columna(co(s, c), range(a, b + 1), 'vivos')):.1f} · "
            f"{prom(lambda s: al.comida(co(s, c), range(a, b + 1))):.2f} · "
            f"{prom(lambda s: rebrotes(ge(s, c), range(a, b + 1))):.0f} · "
            f"{100 * prom(lambda s: comidas(co(s, c), ge(s, c), range(a, b + 1))):.0f}%" for a, b in ac.VENTANAS))
    print("  el tiempo de cada corrida, en horas: " + " | ".join(
        f"{c} " + " · ".join(f"{horas(LOGS[s, c]):.2f}" for s in SEMILLAS) for c in C))

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
    print("\n### Por ventana (promedio de las 5 semillas): sensibilidad a la comida · manzanas por 1.000 px")
    for c in C:
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: sl.val(ag(s, c), range(a, b + 1), 'sc')):+.4f} · "
            f"{prom(lambda s: ac.por_px(co(s, c), range(a, b + 1))):.3f}" for a, b in ac.VENTANAS))
    print("  la sensibilidad a la comida, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in ac.VENTANAS)
        for c in ("NR", "NT") for s in SEMILLAS))
    bloques = [(a, a + 4) for a in range(TRAMO[0], TRAMO[-1] + 1, 5)]
    print(f"  la sensibilidad a la comida de a 5 generaciones, {TRAMO[0]}-{TRAMO[-1]}, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in bloques)
        for c in ("NR", "NT") for s in SEMILLAS))
    print(f"  por etapa (gens {W[0]}-{W[-1]}): " + " | ".join(
        f"{c} etapa 0 {al.media([f['sc0'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} · etapa 1 "
        f"{al.media([f['sc1'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f}" for c in C))
    print("  los pasos por ventana: " + " | ".join(
        f"{nombre}, {c} " + " ".join(f"{prom(lambda s: cad.paso(co(s, c), range(a, b + 1), col)):.2f}"
                                     for a, b in ac.VENTANAS)
        for col, _, nombre in PASOS for c in ("NR", "NT")))
    print("  la puerta de madera, por semilla y por ventana: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{cad.paso(co(s, c), range(a, b + 1), 'agentes_puerta_madera'):.1f}"
                                for a, b in ac.VENTANAS)
        for c in ("NR", "NT") for s in SEMILLAS))

    print(f"\n### Sin criterio (gens {W[0]}-{W[-1]}): distancia · término de la comida · sensibilidad a la brújula (el control "
          f"positivo) · árboles talados por generación")
    for c in C:
        print(f"  {NOM[c]}: {prom(lambda s: sl.columna(co(s, c), W, 'distancia_prom')):.0f} · "
              f"{al.media([float(f['f_comida']) for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):.2f} · "
              f"{prom(lambda s: sl.val(ag(s, c), W)):+.4f} · {prom(lambda s: sl.columna(co(s, c), W, 'arboles_cortados')):.2f}")

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
    for c in ("NR", "NT"):
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
    for c in ("NR", "NT"):
        dio[f"mutacion_{c}"] = sum(stp.mutacion(ag(s, c), DESDE) for s in SEMILLAS)
        print(f"  {NOM[c]}: " + " | ".join(
            f"{a}-{b} {sum(stp.mutacion(ag(s, c), range(a, b + 1)) for s in SEMILLAS)}" for a, b in ac.TRAMOS)
              + f" || 31-{G}: {dio[f'mutacion_{c}']} de {5 * len(DESDE)}")

    if prueba:
        pub = nf.PUBLICADO
        chequeos = [(f"la sensibilidad a la comida de {c}, por semilla", tuple(round(sc[x][s], 4) for s in SEMILLAS),
                     pub["sc"][c]) for c, x in (("NT", "NR"), ("NCB0", "NRB0"))]
        chequeos += [(f"su promedio, {c}", (round(st.mean(sc[x].values()), 4),), (pub["promedio"][c],))
                     for c, x in (("NT", "NR"), ("NCB0", "NRB0"))]
        chequeos += [("la 1a, semillas que cumplen", (len(cumplen),), (pub["cumple"],))]
        chequeos += [(f"el Spearman con las manzanas, {TRAMO[0]}-{TRAMO[-1]}, {c}", (round(al.mediana(rm[x]), 3),),
                      (pub["spearman"][c],)) for c, x in (("NT", "NR"), ("NCB0", "NRB0"))]
        chequeos += [(f"{col}, NT · NCB0, {W[0]}-{W[-1]}", dio[col], v) for col, v in pub["criterio"].items()]
        chequeos += [(f"la puerta de madera, NT · NCB0, 31-{G}", (dio["madera_NR"], dio["madera_NRB0"]), pub["madera"]),
                     (f"la puerta de hierro de NT, 31-{G}", dio["hierro_NR"], pub["hierro_NT"]),
                     (f"el tope de NT, {W[0]}-{W[-1]}", dio["tope_NR"], pub["tope_NT"]),
                     (f"adentro de la generación de NT, {TRAMO[0]}-{TRAMO[-1]}, con el fitness y con la etapa",
                      dio["dentro_NR"], pub["dentro_NT"]),
                     (f"la mutación adaptativa de NT, 31-{G}", dio["mutacion_NR"], pub["mutacion_NT"])]
        print("\n### Lo publicado (#sin-tope)")
        for nombre, valor, p in chequeos:
            errores += valor != p
            print(f"  {nombre}: {valor} (publicado {p}) {valor == p}")
    print(f"\n  errores: {errores}")


if __name__ == "__main__":
    main()
