"""Golpear en la puerta (docs/qa/AnalisisQA.md#sens-golpe), a partir de los CSV de medir_puerta.py con sens-golpe: la
larga (el currículo hasta el final) y sin la llave (cortado en la 30), las dos con evolución.

Por fila de agente con ticks en la etapa 1, divididas por sens_ticks (promedio de las filas de la ventana, la cuenta de la
sensibilidad a la brújula): S = zgolpe_pegado − zgolpe_lejos, el golpe condicionado al sensor 11 (z: la salida 'hit' antes
del tanh); G = zgolpe_lejos, el golpe en general; Z pegado = S + G; P pegado y P lejos, la parte de los ticks en que
golpearía. En la etapa 0 de la corrida sin la llave (con sens-etapa0), lo mismo con las columnas del 0 y sens_ticks0. Y
"En la puerta", la cuenta de analizar_sin_llave.py.

Uso: python mediciones/analizar_golpe.py LARGA SIN_LLAVE [LARGA_PUBLICADA SIN_LLAVE_PUBLICADA]
LARGA y SIN_LLAVE son las carpetas de cada corrida (pueden ser la misma). Con las publicadas, los controles de la misma
corrida: corrida_*.csv igual, y agentes_*.csv sin las columnas nuevas, igual. Con las carpetas publicadas, que no tienen
las columnas nuevas, da solo "En la puerta": la prueba del script (llegan el 41% y el 35%; golpean el 23% y el 82%).
"""
import csv
import glob
import hashlib
import io
import os
import statistics as st
import sys

import analizar_largas as al

NUEVAS = [p + s for s in ("", "0") for p in ("zgolpe_pegado", "zgolpe_lejos", "golpea_pegado", "golpea_lejos")]
VENTANAS = ((26, 30), (31, 35), (56, 60), (86, 90), (116, 120), (146, 150))
NOMBRES = dict(L="Larga", N="Sin la llave")
PATRON = dict(L="s{s}_*moviles_curriculo150_cruce*_evolucion.csv", N="s{s}_*moviles_curriculo30_cruce*_evolucion.csv")
DOBLE = 2.0      # la premisa: P pegado de la larga, al menos el doble que el de sin la llave
TERCIO = 1 / 3   # cada parte pesa si lleva al menos un tercio de ΔZ


def medidas(f, suf):
    t = int(f.get("sens_ticks" + suf) or 0)
    if not t or "zgolpe_pegado" + suf not in f:
        return None
    zp, zl = float(f["zgolpe_pegado" + suf]), float(f["zgolpe_lejos" + suf])
    return dict(S=(zp - zl) / t, G=zl / t, Z=zp / t, Pp=int(f["golpea_pegado" + suf]) / t,
                Pl=int(f["golpea_lejos" + suf]) / t)


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        f["gen"] = int(f["generacion"])
        f["m1"], f["m0"] = medidas(f, ""), medidas(f, "0")
    return filas


def val(ag, gens, k, etapa="m1"):
    gens = set(gens)
    return al.media([f[etapa][k] for f in ag if f["gen"] in gens and f[etapa] is not None])


def filas_medidas(ag, gens, etapa="m1"):
    gens = set(gens)
    return sum(f["gen"] in gens and f[etapa] is not None for f in ag)


def sha_sin_nuevas(ruta):
    """SHA-256 de agentes_*.csv sin las columnas de sens-golpe, escrito como lo escribe medir_puerta.py."""
    with open(ruta, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        campos = [c for c in r.fieldnames if c not in NUEVAS]
        filas = list(r)
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    w.writeheader()
    w.writerows(filas)
    return hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest()


def en_la_puerta(D, semillas, W):
    """La cuenta de "En la puerta" de analizar_sin_llave.py, sin cambios."""
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


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    carpetas = dict(L=sys.argv[1], N=sys.argv[2])
    publicadas = dict(L=sys.argv[3], N=sys.argv[4]) if len(sys.argv) > 4 else None
    semillas = sorted({int(os.path.basename(r).split("_")[1][1:]) for r in
                       glob.glob(os.path.join(carpetas["N"], "corrida_" + PATRON["N"].format(s="*")))})
    D = {}
    for s in semillas:
        d = D[s] = {}
        for c in ("L", "N"):
            for t in ("corrida_", "agentes_"):
                d[f"{c}_{t}ruta"] = al.uno(os.path.join(carpetas[c], t + PATRON[c].format(s=s)))
            d[c + "_ag"] = leer(d[f"{c}_agentes_ruta"])
    s0 = D[semillas[0]]
    G = max(f["gen"] for f in s0["N_ag"])
    W = range(G - 4, G + 1)
    con_golpe = "zgolpe_pegado" in s0["N_ag"][0] and "zgolpe_pegado" in s0["L_ag"][0]
    print(f"Golpear en la puerta: semillas {semillas}, {G} generaciones; larga, currículo hasta la "
          f"{s0['L_ag'][0]['curriculo_hasta']}; sin la llave, hasta la {s0['N_ag'][0]['curriculo_hasta']} (sens-golpe: "
          f"{'sí' if con_golpe else 'no'}; etapa 0: {'sí' if 'zgolpe_pegado0' in s0['N_ag'][0] else 'no'})")

    if con_golpe:
        K = ("S", "G", "Z", "Pp", "Pl")
        for s in semillas:
            for c in ("L", "N"):
                D[s][c] = {k: val(D[s][c + "_ag"], W, k) for k in K}

        def prom(c, k):
            return st.mean(D[s][c][k] for s in semillas)

        print(f"\n### Gens {W[0]}-{W[-1]}, etapa 1: S (z pegado − z lejos) · G (z lejos) · Z pegado · P pegado · P lejos "
              f"(filas medidas); el umbral de z es atanh(0,5) = 0,549")
        for c in ("L", "N"):
            for s in semillas:
                v = D[s][c]
                print(f"  {NOMBRES[c]} s{s}: {v['S']:+.3f} · {v['G']:+.3f} · {v['Z']:+.3f} · {v['Pp']:.3f} · {v['Pl']:.3f} "
                      f"({filas_medidas(D[s][c + '_ag'], W)})")
            print(f"  {NOMBRES[c]}, promedio: " + " · ".join(f"{k} {prom(c, k):+.3f}" for k in K))

        # ---------- Criterio ----------
        print("\n### Criterio (fijado antes de correr)")
        k0 = sum(D[s]["L"]["Pp"] > D[s]["N"]["Pp"] for s in semillas)
        tam0 = prom("L", "Pp") >= DOBLE * prom("N", "Pp")
        c0 = k0 >= 4 and tam0
        print(f"  0. Premisa: P pegado de la larga > sin la llave en {k0} de {len(semillas)} (pide 4); promedio "
              f"{prom('L', 'Pp'):.3f} contra {prom('N', 'Pp'):.3f}, "
              f"{prom('L', 'Pp') / prom('N', 'Pp') if prom('N', 'Pp') else float('inf'):.2f} veces (pide {DOBLE:g}) "
              f"-> {'CUMPLE' if c0 else 'NO CUMPLE'}")
        dS = {s: D[s]["L"]["S"] - D[s]["N"]["S"] for s in semillas}
        dG = {s: D[s]["L"]["G"] - D[s]["N"]["G"] for s in semillas}
        mS, mG = st.mean(dS.values()), st.mean(dG.values())
        mZ = mS + mG
        print("  por semilla: " + " | ".join(f"s{s} ΔS {dS[s]:+.3f} ΔG {dG[s]:+.3f} ΔZ {dS[s] + dG[s]:+.3f}"
                                            for s in semillas))
        k1, k2 = sum(v > 0 for v in dS.values()), sum(v > 0 for v in dG.values())
        c1 = mZ > 0 and k1 >= 4 and mS >= TERCIO * mZ
        c2 = mZ > 0 and k2 >= 4 and mG >= TERCIO * mZ
        print(f"  promedio: ΔS {mS:+.3f} + ΔG {mG:+.3f} = ΔZ {mZ:+.3f}"
              + (f" (ΔS lleva el {mS / mZ:.0%}, ΔG el {mG / mZ:.0%})" if mZ > 0 else ""))
        print(f"  1. El golpe condicionado pesa: ΔS > 0 en {k1} de {len(semillas)} (pide 4), y al menos un tercio de ΔZ "
              f"-> {'CUMPLE' if c1 else 'NO CUMPLE'}")
        print(f"  2. El golpe en general pesa: ΔG > 0 en {k2} de {len(semillas)} (pide 4), y al menos un tercio de ΔZ "
              f"-> {'CUMPLE' if c2 else 'NO CUMPLE'}")
        if not c0 or mZ <= 0:
            veredicto = "ninguna de las dos (la premisa no se cumple)" if not c0 else "sin decidir (ΔZ ≤ 0)"
        else:
            veredicto = {(True, False): "es el golpe condicionado (a)", (False, True): "es el golpe en general (b)",
                         (True, True): "son las dos", (False, False): "sin decidir"}[(c1, c2)]
        print(f"  Veredicto: {veredicto}")

        # ---------- Por ventana ----------
        print("\n### Por ventana, etapa 1 (promedio de las semillas): S · G · P pegado · P lejos; y S y G por semilla")
        for c in ("L", "N"):
            partes = []
            for a, b in VENTANAS:
                g = range(a, b + 1)
                partes.append(f"{a}-{b}: " + " · ".join(
                    f"{st.mean(val(D[s][c + '_ag'], g, k) for s in semillas):{'+.3f' if k in ('S', 'G') else '.3f'}}"
                    for k in ("S", "G", "Pp", "Pl")))
            print(f"  {NOMBRES[c]}: " + " | ".join(partes))
            for k in ("S", "G"):
                print(f"    {k}: " + " | ".join(f"s{s} " + " ".join(f"{val(D[s][c + '_ag'], range(a, b + 1), k):+.2f}"
                                                                for a, b in VENTANAS) for s in semillas))

        # ---------- La gen 1: redes al azar ----------
        print("\n### Gen 1, redes al azar (la población inicial, la misma en las dos): S · G · P pegado · P lejos")
        print("  " + " | ".join(f"s{s} " + " · ".join(f"{val(D[s]['L_ag'], [1], k):+.3f}" for k in ("S", "G", "Pp", "Pl"))
                                for s in semillas)
              + " || promedio " + " · ".join(f"{st.mean(val(D[s]['L_ag'], [1], k) for s in semillas):+.3f}"
                                            for k in ("S", "G", "Pp", "Pl")))

        # ---------- La etapa 0 ----------
        if "zgolpe_pegado0" in s0["N_ag"][0]:
            print("\n### Sin la llave, la etapa 0 (hacia la llave; sensor 11 = distancia a la llave) contra la etapa 1 "
                  "(hacia la puerta): S · G · P pegado · P lejos, promedio de las semillas (filas medidas)")
            for a, b in VENTANAS[1:]:
                g = range(a, b + 1)
                e = {et: [st.mean(val(D[s]["N_ag"], g, k, et) for s in semillas) for k in ("S", "G", "Pp", "Pl")]
                     for et in ("m0", "m1")}
                n = {et: sum(filas_medidas(D[s]["N_ag"], g, et) for s in semillas) for et in ("m0", "m1")}
                print(f"  {a}-{b}: etapa 0 " + " · ".join(f"{x:+.3f}" for x in e["m0"]) + f" ({n['m0']}) | etapa 1 "
                      + " · ".join(f"{x:+.3f}" for x in e["m1"]) + f" ({n['m1']})")
            print("  por semilla, gens " + f"{W[0]}-{W[-1]}, G etapa 0 / etapa 1: " + " | ".join(
                f"s{s} {val(D[s]['N_ag'], W, 'G', 'm0'):+.2f} / {val(D[s]['N_ag'], W, 'G'):+.2f}" for s in semillas))

        # ---------- En decisiones ----------
        print(f"\n### El golpe condicionado en decisiones, gens {W[0]}-{W[-1]}: P pegado − P lejos")
        for c in ("L", "N"):
            print(f"  {NOMBRES[c]}: " + " | ".join(f"s{s} {D[s][c]['Pp'] - D[s][c]['Pl']:+.3f}" for s in semillas)
                  + f" || promedio {prom(c, 'Pp') - prom(c, 'Pl'):+.3f}")

    en_la_puerta(D, semillas, W)

    # ---------- Controles ----------
    print("\n### Controles")
    errores = 0
    for s in semillas:
        d, partes = D[s], []
        if publicadas:
            for c in ("L", "N"):
                pub_co = al.uno(os.path.join(publicadas[c], "corrida_" + PATRON[c].format(s=s)))
                pub_ag = al.uno(os.path.join(publicadas[c], "agentes_" + PATRON[c].format(s=s)))
                igual_co = al.sha(d[f"{c}_corrida_ruta"]) == al.sha(pub_co)
                igual_ag = sha_sin_nuevas(d[f"{c}_agentes_ruta"]) == al.sha(pub_ag)
                errores += (not igual_co) + (not igual_ag)
                partes.append(f"{NOMBRES[c]}: corrida = publicada {igual_co} ({al.sha(pub_co)[:12]}), agentes sin las "
                              f"nuevas = publicado {igual_ag} ({al.sha(pub_ag)[:12]})")
        if con_golpe:
            clave = ("gen", "id", "zgolpe_pegado", "zgolpe_lejos", "golpea_pegado", "golpea_lejos")
            iguales = ([tuple(f[k] for k in clave) for f in d["L_ag"] if f["gen"] <= 30]
                       == [tuple(f[k] for k in clave) for f in d["N_ag"] if f["gen"] <= 30])
            etapa0 = (sum(any(float(f[k]) != 0 for k in NUEVAS[4:]) for f in d["N_ag"] if f["gen"] <= 30)
                      if "zgolpe_pegado0" in d["N_ag"][0] else 0)
            sin_ticks = sum(any(float(f[k]) != 0 for k in NUEVAS[:4]) for c in ("L", "N") for f in d[c + "_ag"]
                            if int(f["sens_ticks"]) == 0)
            errores += (not iguales) + etapa0 + sin_ticks
            partes.append(f"gens 1-30, etapa 1 igual en las dos {iguales}; etapa 0 distinta de 0 en las 1-30 {etapa0}; "
                          f"filas sin ticks con valor {sin_ticks}")
        print(f"  s{s}: " + " | ".join(partes))
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
