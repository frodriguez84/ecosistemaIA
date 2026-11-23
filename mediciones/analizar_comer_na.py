"""Comer, en la referencia nueva (docs/qa/AnalisisQA.md#comer-na; el paso 1 de docs/specs/active/PUZZLE_SOLOS.md, su
decisión 6), a partir de los CSV de medir_puerta.py con sens-etapa0: NA, la referencia (la recompensa por acercarse por el
camino), contra NCB0, su línea base sin evolución; sin criterio, NC (la brújula por el camino), la referencia anterior.

Con las cuentas de analizar_comida.py:
- la sensibilidad a la comida antes de abrir la puerta: (sens_comida + sens_comida0) / (sens_ticks + sens_ticks0) por fila,
  promedio de las filas de la ventana;
- dentro de cada generación con 10 agentes medidos o más, el Spearman entre la sensibilidad y las manzanas de cada agente
  (de f_comida = 10 × √manzanas; NA no cambia FITNESS_FOOD), mediana de las 121-150 de las 5 semillas.

Uso: python mediciones/analizar_comer_na.py TANDA REFERENCIA [conteo]
TANDA tiene los CSV de NA (results/medicion_acercarse_camino_20261122); REFERENCIA, los de NC y NCB0
(results/medicion_brujula_camino_20261122). Con conteo imprime solo las filas medidas de la ventana, sus ticks y los
controles: lo que se anota antes de leer.
     python mediciones/analizar_comer_na.py prueba PUBLICADA BASE
La prueba del script, con N en el lugar de NA (PUBLICADA: results/medicion_golpe_20261121) y NB en el de NCB0 (BASE:
results/medicion_sin_llave_20261120), sin NC: tiene que dar lo publicado en #comer (lo controla solo, en PUBLICADO) con 0
errores.
"""
import os
import statistics as st
import sys

import analizar_acercarse_camino as acc
import analizar_brujula_camino as bc
import analizar_comida as ac
import analizar_costo_golpe as cg
import analizar_largas as al
import analizar_sin_llave as sl

SEMILLAS = ac.SEMILLAS
TIPOS = ("corrida_", "agentes_")
TRAMO = range(121, 151)  # la medida independiente: el Spearman con las manzanas, mediana de estas generaciones
NOM = dict(NA="Referencia (NA)", NCB0="Su línea base (NCB0)", NC="Referencia anterior (NC)")
NOM_PRUEBA = dict(NA="N, en el lugar de NA", NCB0="NB, en el de NCB0")
# El SHA-256 publicado de NA (#acercarse-camino): corrida_*.csv y agentes_*.csv
SHA_NA = {1: ("019b795269d3b06346db9c02f7aa5e3742f9e338ef8f95ce6d56c27a9e78593e",
              "52aa48c1099bf0069748cee294f1fde51ae60a58291c0253f309fba11ad2b39f"),
          2: ("b6a3167e163794f0fbe6389a73d17e1439d41fc5953c031cafa844da6d5feb3e",
              "f08ee38c20ec3f92b00a4cd4b0313bb75bd44255ba696879e686e447acf01e5e"),
          3: ("8ded72bf6916ae36df4c2b807c609b50ce661afec0d3a166aee42efcf7c577d1",
              "e41b7f541492e29069177361234b760c356c193e5813ee0e9c102c6821dd455e"),
          4: ("d7dc32d0c9f771a12a17d82671f06ef597c336d605f42a9c3ef778b7f9cb056a",
              "874defdcdc826e0e365b03d0d39772fbce0b52a28a4dcc735e40240185b940ef"),
          5: ("073548e4656a558137ade412a2e2278376043f805efe6151bf8fce718cdaa6f5",
              "13bc285b928fa07844417b10bf22e83f01b7941ae0f014b587dbdc193700e6c0")}
# Lo publicado en #comer: la sensibilidad a la comida por semilla en las 146-150 (N y NB, a 4 decimales), su promedio, en
# cuántas semillas cumple la 2 de entonces (la 1 de ahora) y el Spearman con las manzanas en las 121-150 (a 3 decimales)
PUBLICADO = dict(sc=dict(NA=(0.0215, 0.0281, 0.0182, 0.0313, -0.0299), NCB0=(0.0020, 0.0005, 0.0008, 0.0006, -0.0024)),
                 promedio=dict(NA=0.0138, NCB0=0.0003), cumple=3, spearman=dict(NA=0.102, NCB0=0.041))
# El tope del fitness (sumado después de leer, sin criterio): _calculate_fitness de advanced_agent.py recorta la suma de los
# términos a [0, 100] (y a 50 + 50 × la parte vivida de BASE_TICKS)
TERMINOS = ("f_supervivencia", "f_comida", "f_exploracion", "f_anticirculo", "f_puzzle", "f_acercarse", "f_agua")
TOPE = 100.0


def cargar(rutas):
    for r in rutas:
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    return dict(co=sl.leer(rutas[0]), ag=ac.leer_agentes(rutas[1]), rutas=rutas)


def ticks(f, suf=None):
    """Los ticks medidos de la fila: los de las etapas 0 y 1, o los de una ("0" o "")."""
    return sum(int(f["sens_ticks" + x]) for x in (("0", "") if suf is None else (suf,)))


def dentro_ticks(ag, gens):
    """Spearman (ticks medidos, manzanas) dentro de cada generación con 10 agentes medidos o más: si los que se miden menos
    (los que abren antes la puerta) comen distinto."""
    rs = []
    for g in gens:
        fg = [f for f in ag if f["gen"] == g and f["sc"] is not None]
        if len(fg) >= 10:
            r = al.spearman([ticks(f) for f in fg], [f["manzanas"] for f in fg])
            if r == r:
                rs.append(r)
    return rs


def suma(f):
    """Lo que suman los términos del fitness de la fila, sin el recorte."""
    return sum(float(f[k]) for k in TERMINOS)


def en_el_tope(F):
    """La parte de las filas con el fitness en el tope, y la mediana de lo que les sobra (la suma de los términos − 100)."""
    T = [f for f in F if float(f["fitness"]) >= TOPE - 1e-4]
    return len(T) / len(F), al.mediana([suma(f) - TOPE for f in T])


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    prueba = sys.argv[1] == "prueba"
    conteo = not prueba and len(sys.argv) > 3 and sys.argv[3] == "conteo"
    D = {}
    for s in SEMILLAS:
        if prueba:
            publicada, base = sys.argv[2:4]
            D[s] = dict(NA=cargar([os.path.join(publicada, t + cg.nombre(s, 30)) for t in TIPOS]),
                        NCB0=cargar([al.uno(os.path.join(base, t + f"s{s}_*moviles_curriculo30_sin_evolucion.csv"))
                                     for t in TIPOS]))
        else:
            tanda, ref = sys.argv[1:3]
            D[s] = dict(NA=cargar([os.path.join(tanda, t + acc.NA_NOMBRE.format(s=s)) for t in TIPOS]),
                        NCB0=cargar([os.path.join(ref, t + bc.NCB0_NOMBRE.format(s=s)) for t in TIPOS]),
                        NC=cargar([os.path.join(ref, t + bc.NC_NOMBRE.format(s=s)) for t in TIPOS]))
    C = tuple(D[1])
    nom = NOM_PRUEBA if prueba else NOM
    SHA = (dict(NA=cg.SHA_N, NCB0=ac.SHA["NB"]) if prueba else
           dict(NA=SHA_NA, NCB0={s: acc.SHA["NCB0"][s][:2] for s in SEMILLAS},
                NC={s: acc.SHA["NC"][s][:2] for s in SEMILLAS}))
    G = max(f["gen"] for f in D[1]["NA"]["co"])
    W = range(G - 4, G + 1)
    print(f"Comer, en la referencia nueva: semillas {list(SEMILLAS)}, {G} generaciones; ventana {W[0]}-{W[-1]}"
          f"{' (PRUEBA: N y NB en el lugar de NA y NCB0)' if prueba else ''}{' (CONTEO: antes de leer)' if conteo else ''}")

    def co(s, c):
        return D[s][c]["co"]

    def ag(s, c):
        return D[s][c]["ag"]

    def prom(f):
        return st.mean(f(s) for s in SEMILLAS)

    errores = 0

    # ---------- Las filas medidas ----------
    print(f"\n### Las filas medidas (gens {W[0]}-{W[-1]}): filas con ticks medidos · mediana de los ticks medidos (etapas 0 y "
          f"1) · de la etapa 0 · de la 1 · la parte que abre la puerta de madera")
    for c in C:
        F = [f for s in SEMILLAS for f in ag(s, c) if f["gen"] in W]
        M = [f for f in F if f["sc"] is not None]
        print(f"  {nom[c]}: {len(M)} de {len(F)} · {al.mediana([ticks(f) for f in M]):.0f} · "
              f"{al.mediana([ticks(f, '0') for f in M]):.0f} · {al.mediana([ticks(f, '') for f in M]):.0f} · "
              f"{100 * sum(int(f['abrio']) for f in F) / len(F):.0f}%")
        print("    por semilla, la mediana de los ticks medidos: " + " · ".join(
            f"s{s} {al.mediana([ticks(f) for f in ag(s, c) if f['gen'] in W and f['sc'] is not None]):.0f}"
            for s in SEMILLAS))

    # ---------- Controles ----------
    print("\n### Controles")
    for s in SEMILLAS:
        partes = []
        for c in C:
            igual = (al.sha(D[s][c]["rutas"][0]), al.sha(D[s][c]["rutas"][1])) == SHA[c][s]
            filas = {}
            for f in ag(s, c):
                filas.setdefault(f["gen"], []).append(f)
            mal_filas = sum(len(v) != ac.POBLACION for v in filas.values()) + (len(filas) != G)
            # las manzanas de cada agente (de f_comida) suman manzanas_prom × 60; los dos van redondeados (LEC-023)
            mal_suma = sum(abs(sum(f["manzanas"] for f in filas[int(r["generacion"])]) / ac.POBLACION
                               - float(r["manzanas_prom"])) > 1e-3 for r in co(s, c))
            enteras = sum(abs(f["manzanas"] - round(f["manzanas"])) > 1e-3 for f in ag(s, c))
            etapa = sum(int(f["etapa_inicial"]) != (1 if f["gen"] <= 30 else 0) for f in ag(s, c))
            sin0 = sum(int(f["sens_ticks0"]) == 0 for f in ag(s, c) if f["gen"] > 30)
            sin_medir = sum(f["sc"] is None for f in ag(s, c) if f["gen"] in W)
            errores += (not igual) + mal_filas + mal_suma + enteras + etapa + sin0 + sin_medir
            partes.append(f"{c}: SHA-256 publicado {igual}, generaciones con otras que 60 filas {mal_filas}, manzanas que no "
                          f"suman {mal_suma}, no enteras {enteras}, etapa_inicial distinta de 1/0 {etapa}, filas sin ticks en "
                          f"la etapa 0 desde la 31 {sin0}, filas de la ventana sin medir {sin_medir}")
        print(f"  s{s}: " + " | ".join(partes))
    if conteo:
        print(f"  errores: {errores}")
        return

    sc = {c: {s: sl.val(ag(s, c), W, "sc") for s in SEMILLAS} for c in C}
    rm = {c: [r for s in SEMILLAS for r in ac.dentro(ag(s, c), TRAMO, "manzanas")] for c in C}

    # ---------- Criterio ----------
    print(f"\n### Criterio (fijado antes de leer; la decisión 6, NA contra NCB0 de la misma semilla, gens {W[0]}-{W[-1]})")
    for c in C:
        print(f"  {nom[c]}: " + " · ".join(f"s{s} {sc[c][s]:+.4f}" for s in SEMILLAS)
              + f" | promedio {st.mean(sc[c].values()):+.4f}")
    k1 = sum(sc["NA"][s] >= ac.UMBRAL and sc["NA"][s] > sc["NCB0"][s] for s in SEMILLAS)
    c1 = k1 >= 4
    print(f"  1. Giran hacia la comida: ≥ {ac.UMBRAL:g} y más que NCB0 en {k1} de 5 (pide 4; semillas "
          f"{[s for s in SEMILLAS if sc['NA'][s] >= ac.UMBRAL and sc['NA'][s] > sc['NCB0'][s]]}) -> "
          f"{'CUMPLE' if c1 else 'NO CUMPLE'}")
    mA, mB = al.mediana(rm["NA"]), al.mediana(rm["NCB0"])
    c2 = mA > mB
    print(f"  2. Los que giran comen más que los de su generación: Spearman con las manzanas, mediana de las "
          f"{TRAMO[0]}-{TRAMO[-1]}, {mA:+.3f} ({len(rm['NA'])} generaciones) contra {mB:+.3f} de NCB0 "
          f"({len(rm['NCB0'])}) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    print(f"  Comer aprendido (los dos): {'SÍ' if c1 and c2 else 'NO'}")
    if "NC" in C:
        kc = sum(sc["NC"][s] >= ac.UMBRAL and sc["NC"][s] > sc["NCB0"][s] for s in SEMILLAS)
        print(f"  NC con la misma cuenta (sin criterio): la 1 en {kc} de 5; la 2, {al.mediana(rm['NC']):+.3f} contra "
              f"{mB:+.3f}")

    # ---------- Dentro de cada generación ----------
    print("\n### Dentro de cada generación (Spearman con la sensibilidad a la comida; mediana de las generaciones del tramo "
          "de las 5 semillas, y % con r > 0): con las manzanas del agente · con el fitness (lo que ve la selección)")
    for c in C:
        partes = []
        for a, b in ac.TRAMOS:
            gens = range(a, b + 1)
            rmt = [r for s in SEMILLAS for r in ac.dentro(ag(s, c), gens, "manzanas")]
            rf = [r for s in SEMILLAS for r in ac.dentro(ag(s, c), gens, "fitness")]
            partes.append(f"{a}-{b}: {al.mediana(rmt):+.3f} ({100 * sum(r > 0 for r in rmt) / len(rmt):.0f}%) · "
                          f"{al.mediana(rf):+.3f} ({100 * sum(r > 0 for r in rf) / len(rf):.0f}%)")
        print(f"  {nom[c]}: " + " | ".join(partes))
    print(f"  Sin criterio, los ticks medidos contra las manzanas, mediana de las {TRAMO[0]}-{TRAMO[-1]}: " + " · ".join(
        f"{c} {al.mediana([r for s in SEMILLAS for r in dentro_ticks(ag(s, c), TRAMO)]):+.3f}" for c in C))
    print(f"  El Spearman con las manzanas en las {TRAMO[0]}-{TRAMO[-1]}, por semilla: " + " | ".join(
        f"{c} " + " · ".join(f"{al.mediana(ac.dentro(ag(s, c), TRAMO, 'manzanas')):+.3f}" for s in SEMILLAS) for c in C))

    # ---------- Por ventana, por etapa ----------
    print("\n### Por ventana (promedio de las 5 semillas): sensibilidad a la comida · manzanas por 1.000 px · comida comida de "
          "la disponible · manzanas por agente")
    for c in C:
        print(f"  {nom[c]}: " + " | ".join(
            f"{a}-{b}: {prom(lambda s: sl.val(ag(s, c), range(a, b + 1), 'sc')):+.4f} · "
            f"{prom(lambda s: ac.por_px(co(s, c), range(a, b + 1))):.3f} · "
            f"{100 * prom(lambda s: ac.comidas(co(s, c), range(a, b + 1))):.0f}% · "
            f"{prom(lambda s: al.comida(co(s, c), range(a, b + 1))):.3f}" for a, b in ac.VENTANAS))
    print("  la sensibilidad a la comida, por semilla: " + " | ".join(
        f"{c} s{s} " + " ".join(f"{sl.val(ag(s, c), range(a, b + 1), 'sc'):+.3f}" for a, b in ac.VENTANAS)
        for c in C if c != "NCB0" for s in SEMILLAS))
    print(f"\n### La sensibilidad a la comida por etapa (gens {W[0]}-{W[-1]}; filas con ticks en cada etapa): etapa 0 · "
          f"etapa 1")
    for c in C:
        n0 = sum(f["sc0"] is not None for s in SEMILLAS for f in ag(s, c) if f["gen"] in W)
        n1 = sum(f["sc1"] is not None for s in SEMILLAS for f in ag(s, c) if f["gen"] in W)
        print(f"  {nom[c]}: {al.media([f['sc0'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} ({n0} filas) · "
              f"{al.media([f['sc1'] for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):+.4f} ({n1} filas)")

    # ---------- Sin criterio ----------
    print(f"\n### Sin criterio (gens {W[0]}-{W[-1]}): manzanas por 1.000 px · comida comida de la disponible · manzanas por "
          f"agente · distancia · término de la comida · sensibilidad a la brújula (el control positivo, en las mismas filas) "
          f"· edad")
    for c in C:
        print(f"  {nom[c]}: {prom(lambda s: ac.por_px(co(s, c), W)):.3f} · {100 * prom(lambda s: ac.comidas(co(s, c), W)):.0f}% · "
              f"{prom(lambda s: al.comida(co(s, c), W)):.3f} · {prom(lambda s: sl.columna(co(s, c), W, 'distancia_prom')):.0f} · "
              f"{al.media([float(f['f_comida']) for s in SEMILLAS for f in ag(s, c) if f['gen'] in W]):.2f} · "
              f"{prom(lambda s: sl.val(ag(s, c), W)):+.4f} · {prom(lambda s: sl.columna(co(s, c), W, 'edad_prom')):.0f}")
        print("    por semilla, manzanas por 1.000 px · comida comida: " + " | ".join(
            f"s{s} {ac.por_px(co(s, c), W):.3f} · {100 * ac.comidas(co(s, c), W):.0f}%" for s in SEMILLAS))

    # ---------- El tope del fitness (sin criterio, sumado después de leer) ----------
    print(f"\n### El tope del fitness (sin criterio, sumado después de leer): la parte de los agentes con el fitness en "
          f"{TOPE:g} y, entre paréntesis, la mediana de lo que les sobra (la suma de los términos − {TOPE:g})")
    for c in C:
        print(f"  {nom[c]}: " + " | ".join(
            "{}-{}: {:.0%} ({:.0f})".format(a, b, *en_el_tope([f for s in SEMILLAS for f in ag(s, c) if a <= f["gen"] <= b]))
            for a, b in ac.VENTANAS) + f" || {W[0]}-{W[-1]}, por semilla: " + " · ".join(
            f"s{s} {en_el_tope([f for f in ag(s, c) if f['gen'] in W])[0]:.0%}" for s in SEMILLAS))
        F = [f for s in SEMILLAS for f in ag(s, c) if f["gen"] in W]
        print(f"    los términos, promedio de las filas de las {W[0]}-{W[-1]}: " + " · ".join(
            f"{k} {st.mean(float(f[k]) for f in F):.2f}" for k in TERMINOS) + f" · suma {st.mean(suma(f) for f in F):.2f}"
              f" · fitness {st.mean(float(f['fitness']) for f in F):.2f}")
        partes = []
        for e in range(6):
            Fe = [f for f in F if int(f["etapa"]) == e]
            if Fe:
                p, _ = en_el_tope(Fe)
                partes.append(f"etapa {e}: {len(Fe)} agentes, {p:.0%} en el tope, suma {al.mediana([suma(f) for f in Fe]):.0f}"
                              f", manzanas {st.mean(f['manzanas'] for f in Fe):.2f}")
        print(f"    por la etapa en que terminan ({W[0]}-{W[-1]}; la suma, mediana): " + " | ".join(partes))

    if prueba:
        chequeos = [(f"la sensibilidad a la comida de {c}, por semilla", tuple(round(sc[c][s], 4) for s in SEMILLAS),
                     PUBLICADO["sc"][c]) for c in C]
        chequeos += [(f"su promedio, {c}", (round(st.mean(sc[c].values()), 4),), (PUBLICADO["promedio"][c],)) for c in C]
        chequeos += [("la 1, semillas que cumplen", (k1,), (PUBLICADO["cumple"],))]
        chequeos += [(f"el Spearman con las manzanas, {TRAMO[0]}-{TRAMO[-1]}, {c}", (round(al.mediana(rm[c]), 3),),
                      (PUBLICADO["spearman"][c],)) for c in C]
        print("\n### Lo publicado (#comer)")
        for nombre, valor, pub in chequeos:
            errores += valor != pub
            print(f"  {nombre}: {valor} (publicado {pub}) {valor == pub}")
    print(f"\n  errores: {errores}")


if __name__ == "__main__":
    main()
