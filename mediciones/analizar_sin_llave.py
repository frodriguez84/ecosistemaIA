"""Sin la llave dada (docs/qa/AnalisisQA.md#sin-la-llave-dada), a partir de los CSV de medir_puerta.py: la condición de
las móviles a 150 generaciones con el currículo cortado (sin la llave: desde el corte nacen en la etapa 0 y la brújula
apunta a la llave roja) y su línea base, contra la larga (el currículo hasta el final) y la tanda publicada de las
móviles (las primeras 30 generaciones).

Con las funciones y la misma cuenta de analizar_largas.py, salvo la sensibilidad, que es la de antes de abrir la puerta:
por fila de agente, (sens_brujula + sens_brujula0) / (sens_ticks + sens_ticks0), promedio de las filas de la ventana. Sin
las columnas de la etapa 0 (medir_puerta.py sin sens-etapa0) o con la llave dada, es la de analizar_largas.py. Suma la
llave roja (agentes_llave_roja, promedio por generación, y por 1.000 px: dividida por distancia_prom, la cuenta de
experimento.py) y la sensibilidad de cada etapa por separado.

Uso: python mediciones/analizar_sin_llave.py NUEVA LARGA PUBLICADA
NUEVA tiene los CSV de la corrida sin la llave y de su línea base; LARGA, los de la larga y la suya; PUBLICADA, los de la
tanda de las fortalezas móviles. Con NUEVA igual a LARGA, la prueba del script: tiene que dar los números de la larga
(+0,0868 de sensibilidad, 1,099 manzanas, 10,3 de puerta; +0,358 de selección en las gens 121-150; la trayectoria, 48,
18, 24, 37 y 19).
"""
import csv
import glob
import os
import statistics as st
import sys

import analizar_largas as al

LLAVE = 2.0   # la llave roja: el promedio de las 5, al menos el doble que el de la línea base
NOMBRES = dict(N="Sin la llave", NB="Línea base sin la llave", L="Larga (con la llave)", LB="Línea base larga")


def leer(ruta):
    """Como analizar_largas.leer, con la sensibilidad de antes de abrir la puerta (sb) y la de cada etapa (sb0, sb1)."""
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        f["gen"] = int(f["generacion"])
        t1, t0 = int(f.get("sens_ticks") or 0), int(f.get("sens_ticks0") or 0)
        b1, b0 = float(f.get("sens_brujula") or 0), float(f.get("sens_brujula0") or 0)
        f["sb"] = (b1 + b0) / (t1 + t0) if t1 + t0 else None
        f["sb1"] = b1 / t1 if t1 else None
        f["sb0"] = b0 / t0 if t0 else None
    return filas


def val(ag, gens, clave="sb"):
    gens = set(gens)
    return al.media([f[clave] for f in ag if f["gen"] in gens])


def columna(co, gens, k):
    gens = set(gens)
    return st.mean(float(f[k]) for f in co if f["gen"] in gens)


def llave(co, gens):
    return columna(co, gens, "agentes_llave_roja")


def llave_px(co, gens):
    d = columna(co, gens, "distancia_prom")
    return llave(co, gens) / d * 1000 if d else float("nan")


def cuando_pasa_desde(ag, desde):
    """Como analizar_largas.cuando_pasa, con las seis ventanas dentro de las gens desde-última: la primera n ≥ desde + 4."""
    d = al.por_gen(ag)
    ultima = max(d)

    def m(a, b):
        return st.mean([v for g in range(a, b + 1) for v in d.get(g, [])])

    for n in range(desde + 4, ultima - 4):
        if all(m(k - 4, k) >= al.UMBRAL for k in range(n, n + 6)):
            return n
    return None


def cargar(nueva, larga, publicada):
    semillas = sorted({int(os.path.basename(r).split("_")[1][1:])
                       for r in glob.glob(os.path.join(nueva, "corrida_s*_*moviles*cruce*_evolucion.csv"))
                       if not any(x in os.path.basename(r) for x in al.EXCLUIR)})
    D = {}
    for s in semillas:
        d = D[s] = {}
        for clave, carpeta, patron in (
                ("N", nueva, f"s{s}_*moviles*cruce*_evolucion.csv"),
                ("NB", nueva, f"s{s}_*moviles*_sin_evolucion.csv"),
                ("L", larga, f"s{s}_*moviles*cruce*_evolucion.csv"),
                ("LB", larga, f"s{s}_*moviles*_sin_evolucion.csv"),
                ("M", publicada, f"s{s}_*moviles*cruce*_evolucion.csv"),
                ("MB", publicada, f"s{s}_*moviles*_sin_evolucion.csv")):
            for t in ("co", "ag", "geo"):
                prefijo = dict(co="corrida_", ag="agentes_", geo="geometria_")[t]
                d[f"{clave}_{t}_ruta"] = al.uno(os.path.join(carpeta, prefijo + patron))
            d[clave + "_co"] = leer(d[clave + "_co_ruta"])
            d[clave + "_ag"] = leer(d[clave + "_ag_ruta"])
    return semillas, D


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    nueva, larga, publicada = sys.argv[1], sys.argv[2], sys.argv[3]
    semillas, D = cargar(nueva, larga, publicada)
    s0 = D[semillas[0]]
    G = max(f["gen"] for f in s0["N_co"])
    G_PUB = max(f["gen"] for f in s0["M_co"])
    CORTE = int(s0["N_ag"][0]["curriculo_hasta"])
    W = range(G - 4, G + 1)
    print(f"Sin la llave: {G} generaciones, currículo hasta la {CORTE} (sens-etapa0: "
          f"{'sí' if 'sens_ticks0' in s0['N_ag'][0] else 'no'}); larga: currículo hasta la "
          f"{s0['L_ag'][0]['curriculo_hasta']}; móviles publicadas, {G_PUB} generaciones; semillas {semillas}")

    for s in semillas:
        d = D[s]
        for c in ("N", "NB", "L", "LB"):
            d[c] = dict(sens=val(d[c + "_ag"], W), comida=al.comida(d[c + "_co"], W), puerta=al.puerta(d[c + "_co"], W),
                        llave=llave(d[c + "_co"], W), llave_px=llave_px(d[c + "_co"], W),
                        sb0=val(d[c + "_ag"], W, "sb0"), sb1=val(d[c + "_ag"], W, "sb1"))

    def prom(c, k):
        return st.mean(D[s][c][k] for s in semillas)

    print(f"\n### Gens {W[0]}-{W[-1]}: sensibilidad antes de abrir la puerta · manzanas por agente · puerta de madera por "
          f"generación · llave roja por generación (por 1.000 px)")
    for c in ("N", "NB", "L", "LB"):
        print(f"  {NOMBRES[c]}: " + " | ".join(
            f"s{s} {D[s][c]['sens']:+.4f} · {D[s][c]['comida']:.3f} · {D[s][c]['puerta']:.2f} · {D[s][c]['llave']:.2f} "
            f"({D[s][c]['llave_px']:.2f})" for s in semillas)
              + f" || promedio {prom(c, 'sens'):+.4f} · {prom(c, 'comida'):.3f} · {prom(c, 'puerta'):.2f} · "
                f"{prom(c, 'llave'):.2f} ({prom(c, 'llave_px'):.2f})")

    # ---------- Criterio ----------
    print("\n### Criterio (fijado antes de correr)")
    k1 = 0
    for s in semillas:
        n, b = D[s]["N"]["llave"], D[s]["NB"]["llave"]
        k1 += n > b
        print(f"  s{s}: llave roja {n:.2f} por generación > línea base {b:.2f}: {'sí' if n > b else 'no'}")
    tam1 = prom("N", "llave") >= LLAVE * prom("NB", "llave")
    c1 = k1 >= 4 and tam1
    print(f"  1. Encuentran la llave roja: {k1} de {len(semillas)} (pide 4); promedio {prom('N', 'llave'):.2f}, "
          f"{prom('N', 'llave') / prom('NB', 'llave') if prom('NB', 'llave') else float('inf'):.2f} veces la línea base "
          f"({prom('NB', 'llave'):.2f}; pide {LLAVE:g}) -> {'CUMPLE' if c1 else 'NO CUMPLE'}")
    k2 = 0
    for s in semillas:
        p, b = D[s]["N"]["puerta"], D[s]["NB"]["puerta"]
        ok = p >= al.PUERTA and p > b
        k2 += ok
        print(f"  s{s}: puerta {p:.2f} por generación >= {al.PUERTA:g} y > línea base {b:.2f}: {'sí' if ok else 'no'}")
    c2 = k2 >= 4
    print(f"  2. Pasan la puerta: {k2} de {len(semillas)} (pide 4) -> {'CUMPLE' if c2 else 'NO CUMPLE'}")
    c3 = prom("N", "comida") >= al.COMIDA * prom("L", "comida")
    print(f"  3. Sin dejar de comer: {prom('N', 'comida'):.4f}, el {100 * prom('N', 'comida') / prom('L', 'comida'):.1f}% "
          f"de la larga ({prom('L', 'comida'):.4f}; pide el {100 * al.COMIDA:.0f}%: {al.COMIDA * prom('L', 'comida'):.4f}) "
          f"-> {'CUMPLE' if c3 else 'NO CUMPLE'}")
    k4 = 0
    for s in semillas:
        v, b = D[s]["N"]["sens"], D[s]["NB"]["sens"]
        ok = v >= al.UMBRAL and v > b
        k4 += ok
        print(f"  s{s}: sensibilidad {v:+.4f} >= {al.UMBRAL} y > línea base {b:+.4f}: {'sí' if ok else 'no'}")
    c4 = k4 >= 4 and prom("N", "sens") >= al.MINIMO
    print(f"  4. Siguen la brújula: {k4} de {len(semillas)} (pide 4); promedio {prom('N', 'sens'):+.4f}, pide "
          f"{al.MINIMO:+.3f} -> {'CUMPLE' if c4 else 'NO CUMPLE'}")
    print(f"  Pasa sin la llave dada (los cuatro): {'SÍ' if c1 and c2 and c3 and c4 else 'NO'}; "
          f"ítem 5 sin la llave dada (el 2): {'SÍ' if c2 else 'NO'}")

    # ---------- Contra la larga ----------
    print("\n### Contra la larga, sin criterio (q = sin la llave / larga; por semilla, sin la llave arriba / abajo)")
    for k, nombre in (("sens", "sensibilidad"), ("comida", "manzanas"), ("puerta", "puerta")):
        arriba = sum(D[s]["N"][k] > D[s]["L"][k] for s in semillas)
        abajo = sum(D[s]["N"][k] < D[s]["L"][k] for s in semillas)
        q = prom("N", k) / prom("L", k) if prom("L", k) else float("nan")
        print(f"  {nombre}: {prom('N', k):.4f} contra {prom('L', k):.4f}: q = {q:.2f}; arriba en {arriba}, abajo en {abajo}")

    # ---------- La sensibilidad por etapa ----------
    print(f"\n### La sensibilidad por etapa, gens {W[0]}-{W[-1]} (etapa 0: hacia la llave, todos; etapa 1: hacia la puerta, "
          f"solo los que tienen la llave; filas con ticks en cada una)")
    for c in ("N", "NB", "L"):
        filas = [f for s in semillas for f in D[s][c + "_ag"] if f["gen"] in set(W)]
        print(f"  {NOMBRES[c]}: etapa 0 {prom(c, 'sb0'):+.4f} ({sum(f['sb0'] is not None for f in filas)} filas) · "
              f"etapa 1 {prom(c, 'sb1'):+.4f} ({sum(f['sb1'] is not None for f in filas)} filas) | por semilla: "
              + " ".join(f"s{s} {D[s][c]['sb0']:+.3f}/{D[s][c]['sb1']:+.3f}" for s in semillas))

    # ---------- La selección ----------
    TRAMOS = [t for t in ((1, 30), (16, 30), (31, 60), (61, 90), (91, 120), (121, 150)) if t[1] <= G]
    print("\n### Lo que ve la selección: Spearman (sensibilidad, fitness) por generación; mediana del tramo y por semilla")
    for c in ("N", "L", "NB"):
        for a, b in TRAMOS:
            por_s = {s: al.seleccion(D[s][c + "_ag"], range(a, b + 1)) for s in semillas}
            todos = [r for s in semillas for r in por_s[s]]
            print(f"  {NOMBRES[c]}, gens {a}-{b}: {al.mediana(todos):+.3f} ({len(todos)}) | "
                  + " ".join(f"s{s} {al.mediana(por_s[s]):+.2f}" for s in semillas))

    # ---------- La trayectoria ----------
    print("\n### Cuándo pasa 0,02 para quedarse (media de las gens n − 4 a n, y de las 5 ventanas siguientes)")
    for c in ("N", "L", "NB"):
        linea = f"  {NOMBRES[c]}, gens 1-{G}: " + ", ".join(
            f"s{s} {al.cuando_pasa(D[s][c + '_ag']) or 'nunca'}" for s in semillas)
        if CORTE < G:
            linea += f" | desde la {CORTE + 1}: " + ", ".join(
                f"s{s} {cuando_pasa_desde(D[s][c + '_ag'], CORTE + 1) or 'nunca'}" for s in semillas)
        print(linea)
    VENTANAS = [w for w in ((26, 30), (31, 35), (56, 60), (86, 90), (116, 120), (G - 4, G)) if w[1] <= G]
    VENTANAS = list(dict.fromkeys(VENTANAS))
    print("\n### Por ventana: sensibilidad (la de la etapa 0) · manzanas · llave roja · puerta por generación, promedio de "
          "las semillas (y la sensibilidad por semilla)")
    for c in ("N", "L", "NB"):
        partes = []
        for a, b in VENTANAS:
            g = range(a, b + 1)
            s0_ = [val(D[s][c + "_ag"], g, "sb0") for s in semillas]
            partes.append(f"{a}-{b}: {st.mean(val(D[s][c + '_ag'], g) for s in semillas):+.3f} "
                          f"({al.media([x for x in s0_ if x == x]) if any(x == x for x in s0_) else float('nan'):+.3f}) · "
                          f"{st.mean(al.comida(D[s][c + '_co'], g) for s in semillas):.2f} · "
                          f"{st.mean(llave(D[s][c + '_co'], g) for s in semillas):.1f} · "
                          f"{st.mean(al.puerta(D[s][c + '_co'], g) for s in semillas):.1f}")
        print(f"  {NOMBRES[c]}: " + " | ".join(partes))
        for s in semillas:
            print(f"    s{s}: " + " ".join(f"{val(D[s][c + '_ag'], range(a, b + 1)):+.3f}" for a, b in VENTANAS))

    # ---------- El puzzle ----------
    desde = min(CORTE + 1, G)
    print(f"\n### El puzzle, gens {desde}-{G} (agentes que llegan a cada paso, suma; generaciones con alguno), y la puerta "
          f"sostenida: generaciones con alguien que la abre, desde la {al.DESDE_PUERTA}")
    for c in ("N", "L", "NB"):
        for s in semillas:
            co = [f for f in D[s][c + "_co"] if desde <= f["gen"] <= G]
            partes = []
            for k, nombre in (("agentes_llave_roja", "llave roja"), ("agentes_puerta_madera", "madera"),
                              ("agentes_llave_dorada", "dorada"), ("agentes_puerta_hierro", "hierro"),
                              ("agentes_cofre", "cofre")):
                partes.append(f"{nombre} {sum(int(f[k]) for f in co)} ({sum(int(f[k]) > 0 for f in co)} gens)")
            sost = [f for f in co if f["gen"] >= al.DESDE_PUERTA]
            print(f"  {NOMBRES[c]} s{s}: " + ", ".join(partes)
                  + (f" | desde la {al.DESDE_PUERTA}: {sum(int(f['agentes_puerta_madera']) > 0 for f in sost)} de "
                     f"{len(sost)}" if sost else ""))

    # ---------- En la puerta, sin criterio ----------
    def con_llave(ag, gens):
        return [f for f in ag if f["gen"] in set(gens) and int(f["etapa"]) >= 1]

    def llegan(filas):  # los que tienen la llave y pasan algún tick a menos de 25 px de la puerta
        return [f for f in filas if int(f["ticks_25"]) > 0]

    def pct(a, b):
        return f"{a / b:.0%}" if b else "-"

    print(f"\n### En la puerta, sin criterio: los que tienen la llave, gens {W[0]}-{W[-1]} (todas las semillas), y por "
          f"ventana, de los que llegan a 25 px (RADIO_GOLPE de medir_puerta.py), la parte que golpea ahí")
    for c in ("N", "L"):
        F = [f for s in semillas for f in con_llave(D[s][c + "_ag"], W)]
        Ll = llegan(F)
        t1, tg = sum(int(f["ticks_etapa1"]) for f in F), sum(int(f["ticks_gen"]) for f in F)
        t25 = sum(int(f["ticks_25"]) for f in Ll)
        print(f"  {NOMBRES[c]}: con la llave {len(F) / (5 * len(semillas)):.1f}/gen, {t1 / len(F):.0f} ticks en la etapa 1 "
              f"de {tg / len(F):.0f} ({t1 / tg:.0%}) · llegan {pct(len(Ll), len(F))} · de los que llegan: "
              f"{st.mean(int(f['ticks_gen']) - int(f['t_llega25']) for f in Ll):.0f} ticks de la generación después de "
              f"llegar, {t25 / len(Ll):.0f} a 25 px, golpean ahí {pct(sum(int(f['ticks_golpe_25']) > 0 for f in Ll), len(Ll))} "
              f"(golpeando el {sum(int(f['ticks_golpe_25']) for f in Ll) / t25:.1%} de esos ticks), abren "
              f"{pct(sum(int(f['abrio']) for f in Ll), len(Ll))}")
        partes, por_s = [], {s: [] for s in semillas}
        for a, b in VENTANAS:
            g = range(a, b + 1)
            Lv = [f for s in semillas for f in llegan(con_llave(D[s][c + "_ag"], g))]
            partes.append(f"{a}-{b}: llegan {len(Lv) / ((b - a + 1) * len(semillas)):.1f}/gen, golpean "
                          f"{pct(sum(int(f['ticks_golpe_25']) > 0 for f in Lv), len(Lv))}")
            for s in semillas:
                Ls = llegan(con_llave(D[s][c + "_ag"], g))
                por_s[s].append(pct(sum(int(f["ticks_golpe_25"]) > 0 for f in Ls), len(Ls)))
        print("    " + " | ".join(partes))
        print("    golpean, por semilla: " + " | ".join(f"s{s} " + " ".join(v) for s, v in por_s.items()))

    # ---------- Términos del fitness ----------
    TERMINOS = ("f_comida", "f_acercarse", "f_supervivencia", "f_puzzle", "fitness", "edad")
    print(f"\n### Términos del fitness, gens {W[0]}-{W[-1]} (promedio de las filas de agentes, promedio de las semillas)")
    for c in ("N", "L", "NB"):
        print(f"  {NOMBRES[c]}: " + " · ".join(
            f"{k[2:] if k.startswith('f_') else k} "
            f"{st.mean(al.media([float(f[k]) for f in D[s][c + '_ag'] if f['gen'] in set(W)]) for s in semillas):.2f}"
            for k in TERMINOS))

    # ---------- El costo ----------
    print("\n### El costo (ticks simulados; generaciones en el límite)")
    for s in semillas:
        partes = []
        for c in ("N", "NB", "L"):
            t = [int(f["ticks"]) for f in D[s][c + "_co"]]
            partes.append(f"{NOMBRES[c]} {sum(t):,} (en el límite {sum(x == al.limite(n) for n, x in enumerate(t, 1))})")
        print(f"  s{s}: " + " | ".join(partes))

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in semillas:
        d = D[s]
        partes = []
        for c, pub in (("N", "M"), ("NB", "MB")):
            iguales_co = al.sha_prefijo(d[c + "_co_ruta"], G_PUB) == al.sha(d[pub + "_co_ruta"])
            excl = {"curriculo_hasta", "sb", "sb0", "sb1", "gen"}
            comunes = [k for k in d[pub + "_ag"][0] if k in d[c + "_ag"][0] and k not in excl]

            def recorte(filas, sin_aporte_ultima):
                return [{k: ("" if k == "aporte" and sin_aporte_ultima and f["gen"] == G_PUB else f[k]) for k in comunes}
                        for f in filas if f["gen"] <= G_PUB]

            iguales_ag = recorte(d[c + "_ag"], G > G_PUB) == recorte(d[pub + "_ag"], False)
            with open(d[c + "_geo_ruta"], encoding="utf-8") as f1, open(d[pub + "_geo_ruta"], encoding="utf-8") as f2:
                g1 = [r for r in csv.DictReader(f1) if int(r["generacion"]) <= G_PUB]
                g2 = list(csv.DictReader(f2))
            iguales_geo = g1 == g2
            arriba = sum(int(f["ticks"]) > al.limite(f["gen"]) for f in d[c + "_co"])
            etapa_mal = sum(f["etapa_inicial"] != ("1" if f["gen"] <= CORTE else "0") for f in d[c + "_co"] + d[c + "_ag"])
            abrieron, con_llave = {}, {}
            for a in d[c + "_ag"]:
                abrieron[a["gen"]] = abrieron.get(a["gen"], 0) + int(a["abrio"])
                con_llave[a["gen"]] = con_llave.get(a["gen"], 0) + (int(a["etapa"]) >= 1)
            abrio = sum(int(f["agentes_puerta_madera"]) != abrieron.get(f["gen"], 0) for f in d[c + "_co"])
            llave_mal = sum(int(f["agentes_llave_roja"]) != con_llave.get(f["gen"], 0) for f in d[c + "_co"])
            sin_etapa0 = (sum(int(f["sens_ticks0"]) == 0 for f in d[c + "_ag"] if f["gen"] > CORTE)
                          + sum(int(f["sens_ticks0"]) != 0 for f in d[c + "_ag"] if f["gen"] <= CORTE)
                          if "sens_ticks0" in d[c + "_ag"][0] else 0)
            e = (not iguales_co) + (not iguales_ag) + (not iguales_geo) + arriba + etapa_mal + abrio + llave_mal + sin_etapa0
            errores += e
            partes.append(f"{NOMBRES[c]}: corrida 1-{G_PUB} = publicada {iguales_co} (SHA-256 publicado "
                          f"{al.sha(d[pub + '_co_ruta'])}), agentes {iguales_ag}, geometría {iguales_geo}; arriba del "
                          f"límite {arriba}; etapa inicial distinta de la esperada {etapa_mal}; puerta distinta de abrio "
                          f"{abrio}; llave roja distinta de etapa ≥ 1 {llave_mal}; filas sin la etapa 0 medida donde "
                          f"debe (o con ella donde no) {sin_etapa0}")
        # La corrida sin la llave y la larga, iguales hasta el corte (agentes, con el aporte de la última)
        hasta = min(CORTE, int(d["L_ag"][0]["curriculo_hasta"]))
        excl = {"curriculo_hasta", "sb", "sb0", "sb1", "gen"}
        comunes = [k for k in d["L_ag"][0] if k in d["N_ag"][0] and k not in excl]
        igual_larga = ([{k: f[k] for k in comunes} for f in d["N_ag"] if f["gen"] <= hasta]
                       == [{k: f[k] for k in comunes} for f in d["L_ag"] if f["gen"] <= hasta])
        errores += not igual_larga
        print(f"  s{s}: " + " | ".join(partes) + f" | agentes 1-{hasta} = larga {igual_larga}")
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
