"""Dónde se traba la puerta de hierro (docs/qa/AnalisisQA.md#medicion-puerta-hierro), a partir de los CSV de
medir_puerta.py con hierro: la referencia sin costo otra vez (N0), con las columnas h_ de la etapa 3 y la geometría de la
puerta de hierro. Es un diagnóstico dentro de N0, sin línea base (LEC-024).

Cada agente × generación con la llave dorada y ticks en la etapa 3 (h_ticks > 0) va a un solo grupo, en este orden: la
abren (etapa ≥ 4); no llegan (h_dmin ≥ 25: nunca a menos de 25 px del centro); llegan sin tiempo (lo que les queda al
llegar, edad − h_t_llega25, menos que los 181 ticks que piden 3 golpes con 90 entre golpe y golpe); llegan y no golpean
ahí (h_ticks_golpe_25 = 0); golpean ahí y no cuenta ninguno (h_golpes = 0); y no completan (1 o 2 golpes). La puerta de
madera, con la misma cuenta en la misma corrida: los que tienen la llave roja (ticks_etapa1 > 0), 2 golpes (91 ticks).

Uso: python mediciones/analizar_hierro.py HIERRO REFERENCIA
HIERRO tiene los CSV y los logs (log_s{S}.txt) de la tanda con hierro; REFERENCIA, los de N0
(results/medicion_costo_golpe_20261121). Con HIERRO igual a REFERENCIA, la prueba del script: sin las columnas h_, da la
puerta de madera y lo publicado (lo controla solo, en PUBLICADO), con 0 errores.
"""
import csv
import hashlib
import io
import math
import os
import re
import statistics as st
import sys

import analizar_cadena as cad
import analizar_comida as ac
import analizar_costo_golpe as cg
import analizar_largas as al

SEMILLAS = (1, 2, 3, 4, 5)
RADIO = 25       # el de world.process_door_hit
COOLDOWN = 90    # DOOR_HIT_COOLDOWN
R_AGENTE = 6     # AGENT_RADIUS
GRUPOS = ("abren", "no_llegan", "sin_tiempo", "no_golpean", "no_cuenta", "no_completan")
ROTULO = dict(abren="la abren", no_llegan="no llegan a 25 px", sin_tiempo="llegan sin tiempo",
              no_golpean="llegan y no golpean ahí", no_cuenta="golpean ahí y no cuenta ninguno",
              no_completan="no completan los golpes")
PUERTAS = dict(
    madera=dict(tiene="ticks_etapa1", dmin="dmin", d0="d0", t_llega="t_llega25", golpe25="ticks_golpe_25",
                golpes="golpes", golpes_pide=2, ticks="ticks_etapa1", golpe="ticks_golpe", t25="ticks_25"),
    hierro=dict(tiene="h_ticks", dmin="h_dmin", d0="h_d0", t_llega="h_t_llega25", golpe25="h_ticks_golpe_25",
                golpes="h_golpes", golpes_pide=3, ticks="h_ticks", golpe="h_ticks_golpe", t25="h_ticks_25"))
# Lo publicado (#cadena-sin-costo): "En la puerta" de N0 en las 146-150 (llegan, golpean, la abren) y la cadena de N0 en
# las 31-150, por semilla
PUBLICADO = dict(puerta_en_N0=("29%", "83%", "61%"),
                 cadena_N0=dict(agentes_llave_dorada=(575, 317, 11, 290, 863), agentes_puerta_hierro=(4, 0, 1, 6, 10),
                                agentes_cofre=(3, 0, 0, 4, 0)))
# El SHA-256 de los geometria_*.csv de N0, que no estaba publicado: el de la carpeta, anotado en #medicion-puerta-hierro
GEOM_N0 = {1: "5d72c5c2c65f830a1dc4ed99fed537d82c70d6d9d4c9896f205bbb8d10227d00",
           2: "8aa0200da076fd9982e1e9c6a9dc8beb2067e1a5138d24b9b4b094fba5a0b4d6",
           3: "8fa615c87ec5a51e62a543b8f5afc0a21b7881ce90b8948308c8903329f8dcab",
           4: "ca45eab59ab9cd47882d71cfc17a8c96e15c25c23a1c6756a181b02a72afd933",
           5: "e7a1fd772fe48efdd910e466515a2a71322739211e2a5ee84d367efa63182170"}


def num(f, k):
    """El valor de la columna como número; None si está vacío."""
    v = f.get(k, "")
    return None if v in ("", None) else float(v)


def pide(puerta):
    """Los ticks desde el primer golpe hasta el último: los golpes que pide, con COOLDOWN entre golpe y golpe."""
    return (PUERTAS[puerta]["golpes_pide"] - 1) * COOLDOWN + 1


def tiene(f, puerta):
    return (num(f, PUERTAS[puerta]["tiene"]) or 0) > 0


def abrio(f, puerta):
    return int(f["abrio"]) == 1 if puerta == "madera" else int(f["etapa"]) >= 4


def grupo(f, puerta):
    """El grupo del agente × generación con la llave de esa puerta (ver el docstring del módulo)."""
    P = PUERTAS[puerta]
    if abrio(f, puerta):
        return "abren"
    if num(f, P["dmin"]) >= RADIO:
        return "no_llegan"
    if int(f["edad"]) - num(f, P["t_llega"]) < pide(puerta):
        return "sin_tiempo"
    if num(f, P["golpe25"]) == 0:
        return "no_golpean"
    if num(f, P["golpes"]) == 0:
        return "no_cuenta"
    return "no_completan"


def ultimo_golpe(f, puerta):
    claves = ("t_golpe1", "t_golpe2") if puerta == "madera" else ("h_t_golpe1", "h_t_golpe2", "h_t_golpe3")
    return max(v for v in (num(f, k) for k in claves) if v is not None)


def entre_golpes(f, puerta):
    """De los que no completan: sin otra oportunidad (el cooldown del último golpe pasa después de su último tick: se
    acabó la generación o murieron), se fueron (con otra oportunidad, nunca estuvieron a 25 px con el cooldown cumplido)
    o estuvieron listos y no golpearon."""
    if ultimo_golpe(f, puerta) + COOLDOWN > int(f["edad"]) - 1:
        return "sin_otra"
    listo = num(f, "ticks_25_post90" if puerta == "madera" else "h_ticks_25_listo")
    return "listos" if listo > 0 else "se_fueron"


def pct(a, b):
    return f"{a / b:.0%}" if b else "-"


def mediana(v):
    v = [x for x in v if x is not None]
    return st.median(v) if v else float("nan")


def paredes(x0, y0, n, puerta):
    """Los tiles de pared (20x20, la esquina de arriba a la izquierda) de una fortaleza de n tiles, sin el de la puerta,
    como world._generate_fortress_walls."""
    tiles = {(x0 + 20 * i, y) for i in range(n) for y in (y0, y0 + 20 * (n - 1))}
    tiles |= {(x, y0 + 20 * i) for i in range(1, n - 1) for x in (x0, x0 + 20 * (n - 1))}
    return tiles - {puerta}


def recta_libre(p, t, tiles):
    """Si la recta de p hasta RADIO px de t no toca ningún tile inflado por el radio del agente (mira cada 1 px)."""
    d = math.hypot(t[0] - p[0], t[1] - p[1])
    ux, uy = ((t[0] - p[0]) / d, (t[1] - p[1]) / d) if d else (0.0, 0.0)
    for k in range(max(0, int(d - RADIO)) + 1):
        x, y = p[0] + ux * k, p[1] + uy * k
        if any(tx - R_AGENTE < x < tx + 20 + R_AGENTE and ty - R_AGENTE < y < ty + 20 + R_AGENTE for tx, ty in tiles):
            return False
    return True


def sha_sin_h(ruta):
    """SHA-256 del CSV sin las columnas que empiezan con h_, escrito como lo escribe csv.DictWriter."""
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    quedan = [i for i, c in enumerate(filas[0]) if not c.startswith("h_")]
    out = io.StringIO(newline="")
    w = csv.writer(out)
    for fila in filas:
        w.writerow([fila[i] for i in quedan])
    return hashlib.sha256(out.getvalue().encode("utf-8")).hexdigest(), len(filas[0]) - len(quedan)


def leer_csv(ruta):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        f["gen"] = int(f["generacion"])
    return filas


def cargar(carpeta, s):
    nombre = cg.nombre(s, 30, costo0=True)
    rutas = {t: os.path.join(carpeta, f"{t}_{nombre}") for t in ("corrida", "agentes", "geometria")}
    for r in rutas.values():
        if not os.path.exists(r):
            sys.exit(f"no está {r}")
    return dict(co=al.leer(rutas["corrida"]), ag=leer_csv(rutas["agentes"]), ge=leer_csv(rutas["geometria"]), rutas=rutas)


def clasificar(filas, puerta, gens):
    gens = set(gens)
    F = [f for f in filas if f["gen"] in gens and tiene(f, puerta)]
    c = {g: 0 for g in GRUPOS}
    for f in F:
        c[grupo(f, puerta)] += 1
    return F, c


def imprimir_grupos(c, total, sangria="    "):
    no_abren = total - c["abren"]
    print(f"{sangria}con la llave {total} · " + " · ".join(
        f"{ROTULO[g]} {c[g]} ({pct(c[g], total)}" + (f"; {pct(c[g], no_abren)} de los que no la abren)" if g != "abren"
                                                     else ")") for g in GRUPOS))


def trabado(c):
    """Dónde se traba (fijado antes de correr): el grupo con más agentes de los que no la abren; con él, cualquier otro
    que tenga al menos la mitad."""
    resto = {g: c[g] for g in GRUPOS if g != "abren"}
    tope = max(resto.values())
    return [g for g, n in sorted(resto.items(), key=lambda x: -x[1]) if n and n >= tope / 2]


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # con la salida redirigida, Windows usa cp1252 (DIAG-25)
    hierro_dir, referencia = sys.argv[1:3]
    prueba = os.path.samefile(hierro_dir, referencia)
    D = {s: cargar(hierro_dir, s) for s in SEMILLAS}
    R = {s: cargar(referencia, s) for s in SEMILLAS}
    G = max(f["gen"] for f in D[1]["co"])
    W = range(G - 4, G + 1)
    DESDE = range(31, G + 1)
    con_h = "h_ticks" in D[1]["ag"][0]
    if not prueba and not con_h:
        sys.exit("la tanda no tiene las columnas h_: ¿se corrió con hierro?")
    print(f"Dónde se traba la puerta de hierro: semillas {list(SEMILLAS)}, {G} generaciones"
          f"{' (PRUEBA: la carpeta de N0, sin las columnas h_)' if prueba else ''}; pesos: {D[1]['ag'][0]['pesos']}")
    errores = 0
    puertas = ("madera", "hierro") if con_h else ("madera",)
    todas = {s: D[s]["ag"] for s in SEMILLAS}

    # ---------- Los grupos ----------
    veredicto = {}
    for gens, rot in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
        print(f"\n### Gens {rot}: cada agente × generación con la llave, en un solo grupo (todas las semillas)")
        for puerta in puertas:
            tot = {g: 0 for g in GRUPOS}
            n = 0
            for s in SEMILLAS:
                F, c = clasificar(todas[s], puerta, gens)
                n += len(F)
                for g in GRUPOS:
                    tot[g] += c[g]
            print(f"  Puerta de {puerta} (pide {PUERTAS[puerta]['golpes_pide']} golpes, {pide(puerta)} ticks):")
            imprimir_grupos(tot, n)
            errores += sum(tot.values()) != n
            veredicto[(puerta, rot)] = trabado(tot)
            print(f"    -> se traba en: {', '.join(ROTULO[g] for g in veredicto[(puerta, rot)])}")
            print("    por semilla (" + " · ".join(GRUPOS) + "): " + " | ".join(
                f"s{s} " + " ".join(str(c[g]) for g in GRUPOS) for s in SEMILLAS
                for _, c in [clasificar(todas[s], puerta, gens)]))

    # ---------- Entre golpe y golpe ----------
    print(f"\n### Los que no completan los golpes, gens 31-{G}: sin otra oportunidad (se acabó su tiempo) · se fueron · "
          f"estuvieron listos y no golpearon")
    for puerta in puertas:
        F = [f for s in SEMILLAS for f in clasificar(todas[s], puerta, DESDE)[0] if grupo(f, puerta) == "no_completan"]
        e = {k: sum(entre_golpes(f, puerta) == k for f in F) for k in ("sin_otra", "se_fueron", "listos")}
        extra = ""
        if puerta == "hierro" and F:
            extra = (f"; golpes 1 / 2: {sum(num(f, 'h_golpes') == 1 for f in F)} / {sum(num(f, 'h_golpes') == 2 for f in F)}"
                     f"; ticks a 25 px o más después del primer golpe, mediana {mediana([num(f, 'h_ticks_fuera_entre') for f in F]):.0f}")
        print(f"  {puerta}: {len(F)} · sin otra oportunidad {e['sin_otra']} · se fueron {e['se_fueron']} · listos y no "
              f"golpearon {e['listos']}{extra}")

    # ---------- Lo que frena los golpes ----------
    print(f"\n### Golpear a menos de 25 px, gens 31-{G}: golpes que contaron · ticks golpeando frenados por el cooldown del "
          f"agente · por el de la puerta (cada tick del cooldown suma uno)")
    for puerta in puertas:
        F = [f for s in SEMILLAS for f in todas[s] if f["gen"] >= 31 and tiene(f, puerta)]
        if puerta == "madera":
            cuentan = sum(num(f, "golpes") for f in F)
            agente = sum(num(f, "bloq_agente_inicio") + num(f, "bloq_agente_corte") for f in F)
            puerta_b = sum(num(f, "bloq_puerta") for f in F)
        else:
            cuentan = sum(num(f, "h_golpes") for f in F)
            agente = sum(num(f, "h_bloq_agente") for f in F)
            puerta_b = sum(num(f, "h_bloq_puerta") for f in F)
        print(f"  {puerta}: {cuentan:.0f} · {agente:.0f} · {puerta_b:.0f}")

    # ---------- Cuánto golpea la red ----------
    print(f"\n### Golpear, gens 31-{G} y {W[0]}-{W[-1]}: la parte de los ticks con la llave en que golpean, en todos lados y a "
          f"menos de 25 px")
    for puerta in puertas:
        P = PUERTAS[puerta]
        partes = []
        for gens, rot in ((DESDE, f"31-{G}"), (W, f"{W[0]}-{W[-1]}")):
            F = [f for s in SEMILLAS for f in todas[s] if f["gen"] in set(gens) and tiene(f, puerta)]
            partes.append(f"{rot}: {pct(sum(num(f, P['golpe']) for f in F), sum(num(f, P['ticks']) for f in F))} en todos lados, "
                          f"{pct(sum(num(f, P['golpe25']) for f in F), sum(num(f, P['t25']) for f in F))} a 25 px")
        print(f"  {puerta}: " + " | ".join(partes))

    # ---------- La distancia ----------
    print(f"\n### La distancia al centro de la puerta, gens 31-{G}: al empezar la etapa (d0) y la mínima, medianas; de los que no "
          f"llegan, cuántos quedan a menos de 50 y de 100 px; el camino hecho, (d0 − mínima) / d0")
    for puerta in puertas:
        P = PUERTAS[puerta]
        F = [f for s in SEMILLAS for f in clasificar(todas[s], puerta, DESDE)[0]]
        NL = [f for f in F if grupo(f, puerta) == "no_llegan"]
        camino = [(num(f, P["d0"]) - num(f, P["dmin"])) / num(f, P["d0"]) for f in NL if num(f, P["d0"])]
        print(f"  {puerta}: todos, d0 {mediana([num(f, P['d0']) for f in F]):.0f} y mínima "
              f"{mediana([num(f, P['dmin']) for f in F]):.0f} | no llegan ({len(NL)}): d0 "
              f"{mediana([num(f, P['d0']) for f in NL]):.0f}, mínima {mediana([num(f, P['dmin']) for f in NL]):.0f}, "
              f"< 50 px {pct(sum(num(f, P['dmin']) < 50 for f in NL), len(NL))}, < 100 px "
              f"{pct(sum(num(f, P['dmin']) < 100 for f in NL), len(NL))}, camino {mediana(camino):.2f}")

    if con_h:
        # ---------- La geometría y el seguidor ----------
        print(f"\n### La puerta de hierro en el mapa, gens 31-{G} ({len(DESDE) * len(SEMILLAS)} mapas): lo libre a menos de "
              f"25 px y el seguidor de brújula perfecto desde la llave dorada ({'H_PASOS'} pasos)")
        GE = [g for s in SEMILLAS for g in D[s]["ge"] if g["gen"] >= 31]
        dl = [float(g["h_dmin_libre"]) for g in GE]
        area = [float(g["h_area_libre_25"]) for g in GE]
        print(f"  distancia mínima libre: mediana {mediana(dl):.1f} (de {min(dl):.1f} a {max(dl):.1f}); área libre a 25 px: "
              f"mediana {mediana(area):.0f} px², {sum(a == 0 for a in area)} mapas sin lugar a menos de 25 px")
        madera_dl = [float(g["dmin_libre"]) for g in GE]
        madera_area = [float(g["area_libre_25"]) for g in GE]
        print(f"  la de madera, la misma cuenta: mediana {mediana(madera_dl):.1f}; área mediana {mediana(madera_area):.0f} px², "
              f"{sum(a == 0 for a in madera_area)} mapas sin lugar")
        for modo, rot in (("seguidor", "como hoy"), ("desliza", "deslizando")):
            llega = [g for g in GE if g[f"h_{modo}_t25"] != ""]
            no = [g for g in GE if g[f"h_{modo}_t25"] == ""]
            print(f"  seguidor {rot}: llega en {len(llega)} de {len(GE)} mapas ({pct(len(llega), len(GE))}), en "
                  f"{mediana([int(g[f'h_{modo}_t25']) for g in llega]):.0f} pasos (mediana); donde no llega, queda a "
                  f"{mediana([float(g[f'h_{modo}_dmin']) for g in no]):.0f} px (mediana)")
        # Los que no llegan, según si el seguidor deslizando llega en su mapa
        print(f"  los agentes que no llegan, gens 31-{G}, según el seguidor deslizando en su mapa:")
        geo = {(s, g["gen"]): g for s in SEMILLAS for g in D[s]["ge"]}
        for llega_seg in (True, False):
            F = [(s, f) for s in SEMILLAS for f in clasificar(todas[s], "hierro", DESDE)[0]
                 if (geo[(s, f["gen"])]["h_desliza_t25"] != "") == llega_seg]
            NL = [(s, f) for s, f in F if grupo(f, "hierro") == "no_llegan"]
            cerca = [abs(num(f, "h_dmin") - float(geo[(s, f["gen"])]["h_desliza_dmin"])) < 10 for s, f in NL]
            ab = sum(grupo(f, "hierro") == "abren" for _, f in F)
            print(f"    donde el seguidor {'llega' if llega_seg else 'no llega'}: con la llave {len(F)}, no llegan {len(NL)} "
                  f"({pct(len(NL), len(F))}), la abren {ab}"
                  + ("" if llega_seg else f"; con la mínima a menos de 10 px de la del seguidor {sum(cerca)} "
                                           f"({pct(sum(cerca), len(NL))})"))
        # Cuánto avanzan los que no llegan. Adentro de la fortaleza chica (el interior va de +20 a +80 y la llave dorada
        # está en +60, +40), lo más que se avanza hacia cualquier lado es ~50 px: avanzar menos es compatible con no salir
        NL = [f for s in SEMILLAS for f in clasificar(todas[s], "hierro", DESDE)[0] if grupo(f, "hierro") == "no_llegan"]
        avance = [num(f, "h_d0") - num(f, "h_dmin") for f in NL]
        print(f"  los que no llegan ({len(NL)}): avanzan {mediana(avance):.0f} px hacia la puerta (d0 − mínima, mediana); "
              f"menos de 50 px, {pct(sum(a < 50 for a in avance), len(avance))}")
        # La recta a la puerta de hierro, solo contra las paredes de las dos fortalezas (sin árboles, rocas ni agua). Las
        # fortalezas salen de las puertas: la de madera en (+40, +80) de la chica (5 tiles) y la de hierro en (+40, 0) de la
        # grande (6 tiles); geometria_*.csv da el centro de cada puerta, de 20x20
        libre_llave = libre_salida = salida_norte = 0
        for g in GE:
            mx, my, hx, hy = (float(g[k]) for k in ("puerta_x", "puerta_y", "h_puerta_x", "h_puerta_y"))
            sx, sy, lx, ly = int(mx) - 50, int(my) - 90, int(hx) - 50, int(hy) - 10
            tiles = paredes(sx, sy, 5, (sx + 40, sy + 80)) | paredes(lx, ly, 6, (lx + 40, ly))
            salida = (mx, my + 10 + R_AGENTE + 1)  # apenas afuera de la puerta de madera, al sur
            libre_llave += recta_libre((sx + 60, sy + 40), (hx, hy), tiles)
            libre_salida += recta_libre(salida, (hx, hy), tiles)
            salida_norte += salida[1] < ly - R_AGENTE
        print(f"  la recta a la puerta, solo contra las paredes de las fortalezas (infladas {R_AGENTE} px), hasta {RADIO} px: "
              f"libre desde la llave dorada en {libre_llave} de {len(GE)} mapas; desde afuera de la puerta de madera, en "
              f"{libre_salida}; esa salida queda al norte de la pared norte de la grande (se llega a la puerta por su lado) "
              f"en {salida_norte}")

        # ---------- El tiempo ----------
        print(f"\n### El tiempo, gens 31-{G}: lo que les queda al agarrar la llave dorada (edad − h_t_dorada) y al llegar a 25 px")
        F = [(s, f) for s in SEMILLAS for f in clasificar(todas[s], "hierro", DESDE)[0]]
        queda = [int(f["edad"]) - num(f, "h_t_dorada") for _, f in F]
        segs = [int(geo[(s, f["gen"])]["h_desliza_t25"]) if geo[(s, f["gen"])]["h_desliza_t25"] != "" else None for s, f in F]
        alcanza = [q >= t + pide("hierro") for q, t in zip(queda, segs) if t is not None]
        print(f"  al agarrarla: mediana {mediana(queda):.0f} ticks; menos de {pide('hierro')}: "
              f"{pct(sum(q < pide('hierro') for q in queda), len(queda))}; en los mapas donde el seguidor deslizando llega, les "
              f"alcanzaría siguiéndolo (lo que tarda + {pide('hierro')}): {pct(sum(alcanza), len(alcanza))} de {len(alcanza)}")
        LL = [f for _, f in F if num(f, "h_t_llega25") is not None]
        print(f"  los que llegan ({len(LL)}): tardan {mediana([num(f, 'h_t_llega25') - num(f, 'h_t_dorada') for f in LL]):.0f} "
              f"ticks desde la llave (mediana) y les quedan {mediana([int(f['edad']) - num(f, 'h_t_llega25') for f in LL]):.0f}")
        LLm = [f for s in SEMILLAS for f in clasificar(todas[s], "madera", DESDE)[0] if num(f, "t_llega25") is not None]
        print(f"  la de madera, los que llegan ({len(LLm)}): les quedan "
              f"{mediana([int(f['edad']) - num(f, 't_llega25') for f in LLm]):.0f} ticks al llegar (mediana)")
        print(f"  con la llave dorada en el último tick, sin ticks en la etapa 3: "
              f"{sum(int(f['etapa']) >= 3 and not tiene(f, 'hierro') for s in SEMILLAS for f in todas[s] if f['gen'] >= 31)}")

    # ---------- Controles ----------
    print("\n### Controles")
    for s in SEMILLAS:
        d, partes = D[s], []
        corrida = al.sha(d["rutas"]["corrida"]) == ac.SHA["N0"][s][0]
        sh_ag, n_ag = sha_sin_h(d["rutas"]["agentes"])
        sh_ge, n_ge = sha_sin_h(d["rutas"]["geometria"])
        agentes = sh_ag == ac.SHA["N0"][s][1]
        geometria = sh_ge == GEOM_N0[s] == al.sha(R[s]["rutas"]["geometria"])
        errores += (not corrida) + (not agentes) + (not geometria)
        partes.append(f"corrida_*.csv = N0 publicado {corrida}; agentes_*.csv sin las {n_ag} h_ = N0 publicado {agentes}; "
                      f"geometria_*.csv sin las {n_ge} h_ = la de N0 {geometria}")
        filas = len(d["ag"]) == 60 * G and len(d["co"]) == G
        errores += not filas
        pasos = sum(int(f["agentes_puerta_hierro"]) != sum(int(x["etapa"]) >= 4 for x in d["ag"] if x["gen"] == f["gen"])
                    for f in d["co"])
        errores += pasos
        partes.append(f"filas {filas}; agentes_puerta_hierro distinto de etapa ≥ 4: {pasos}")
        if con_h:
            sin_etapa = sum(tiene(f, "hierro") and int(f["etapa"]) < 3 for f in d["ag"])
            abre = sum((int(f["etapa"]) >= 4) != (num(f, "h_golpes") == 3) for f in d["ag"])
            vacias = sum(not tiene(f, "hierro") and (num(f, "h_golpes") or num(f, "h_ticks_25") or f["h_t_dorada"] != "")
                         for f in d["ag"])
            sin_dorada = sum(tiene(f, "hierro") and f["h_t_dorada"] == "" for f in d["ag"])
            errores += sin_etapa + abre + vacias + sin_dorada
            partes.append(f"con ticks en la etapa 3 y etapa < 3: {sin_etapa}; etapa ≥ 4 distinto de 3 golpes: {abre}; sin "
                          f"ticks y con algo medido: {vacias}; con ticks y sin h_t_dorada: {sin_dorada}")
        if not prueba:
            with open(os.path.join(hierro_dir, f"log_s{s}.txt"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            en_log = "'HIT_ENERGY_COST': 0.0}" in log and "CURRICULO_HASTA_GENERACION=30\n" in log
            medicion = re.findall(r"^MEDICION inconsistencias=(\d+) filas=(\d+)$", log, re.M)
            e = cad.energia(log)
            costo0 = (bool(e) and int(e[0]) > 0 and abs(float(e[1])) < 1e-6 and abs(float(e[3])) < 1e-6
                      and float(e[4]) == 0)
            errores += (not en_log) + (medicion != [("0", str(60 * G))]) + (not costo0)
            partes.append(f"log (pesos, currículo) {en_log}; MEDICION {medicion}; ENERGIA_GOLPE en 0 {costo0}")
        print(f"  s{s}: " + " | ".join(partes))
    # Lo publicado: la misma corrida que N0
    F, L, gl, ab = [sum(x) for x in zip(*(cad.en_la_puerta(D[s]["ag"], W) for s in SEMILLAS))]
    chequeos = [("En la puerta de N0, 146-150", (pct(L, F), pct(gl, L), pct(ab, L)), PUBLICADO["puerta_en_N0"])]
    chequeos += [(f"{col} de N0, 31-{G}", tuple(cad.suma(D[s]["co"], DESDE, col) for s in SEMILLAS), v)
                 for col, v in PUBLICADO["cadena_N0"].items()]
    for nombre, dio, pub in chequeos:
        errores += tuple(dio) != tuple(pub)
        print(f"  publicado, {nombre}: {dio} (publicado {pub}) {tuple(dio) == tuple(pub)}")
    print(f"  errores: {errores}")


if __name__ == "__main__":
    main()
