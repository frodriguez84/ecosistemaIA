"""
Experimento: modo guiado y modo autónomo, con evolución y sin ella, en varias semillas.

Corre main.py sin ventana para cada semilla y cada modo, una vez con evolución y otra con la línea
base (--sin-evolucion), varias a la vez. Cada corrida deja su CSV y su log en
results/experimento_<AAAAMMDD-HHMMSS>/. Al final arma resumen.md: tablas Markdown para pegar tal
cual en docs/qa/AnalisisQA.md (spec MEDIR_ANTES_DE_TOCAR, decisiones 12 a 14; los modos y las
comparaciones entre ellos: spec MODO_GUIADO_Y_AUTONOMO, decisión 29; la recompensa por acercarse, el
currículo, la puerta de madera y el criterio del ítem 5: spec PUZZLE_APRENDIBLE, decisiones 12 y 13).

Uso: python experimento.py [--semillas 1 2 3 4 5] [--generaciones 20] [--modos guiado autonomo]
                           [--acercarse] [--curriculo] [--deslizar] [--paralelo K]

El resumen usa solo la librería estándar (decisión 18).
"""

import argparse
import csv
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Se comparan las primeras y las últimas VENTANA generaciones; con menos de dos ventanas se pisarían
VENTANA = 5
MINIMO_GENERACIONES = 2 * VENTANA
# Cuántos agentes de la generación llegaron al menos a cada paso del puzzle, en orden
COLUMNAS_PUZZLE = ["agentes_llave_roja", "agentes_puerta_madera", "agentes_llave_dorada",
                   "agentes_puerta_hierro", "agentes_cofre"]
# Los de main.py (decisión 1), escritos acá: importar main.py cargaría pygame
MODOS = ("guiado", "autonomo")
NOMBRES_DE_MODOS = {"guiado": "Guiado", "autonomo": "Autónomo"}

# Los números del resumen por corrida que se promedian entre semillas (decisiones 13 y 14;
# supervivencia y puzzle: spec MODO_GUIADO_Y_AUTONOMO, decisión 29)
CLAVES = ["fitness_inicio", "fitness_final", "fitness_dif",
          "manzanas_inicio", "manzanas_final", "manzanas_dif",
          "supervivencia", "llave_roja", "etapa_maxima", "generacion_cofre"]

# El criterio del ítem 5, fijado antes de medir (spec PUZZLE_APRENDIBLE, decisión 13): en el autónomo,
# en 4 o más de las 5 semillas
CRITERIO_SEMILLAS = 5
CRITERIO_MINIMO = 4


# --- Resumen ------------------------------------------------------------------------------------

def _etapa(fila):
    """La etapa más alta a la que llegó algún agente en esa generación, de 0 a 5."""
    return max((etapa for etapa, columna in enumerate(COLUMNAS_PUZZLE, start=1)
                if int(fila[columna]) > 0), default=0)


def resumir_corrida(ruta_csv):
    """Resume el CSV de una corrida (decisión 13; el puzzle, spec MODO_GUIADO_Y_AUTONOMO, decisión 29).

    fitness y manzanas: promedio de la columna *_prom en las generaciones 1-5 (inicio), en las
    últimas 5 (final) y su diferencia. supervivencia: promedio de edad_prom (ticks vividos) en las
    últimas 5. llave_roja: promedio de agentes_llave_roja en las últimas 5. puerta_madera: promedio
    de agentes_puerta_madera en las últimas 5. llave_roja_por_1000: llave_roja / promedio de
    distancia_prom en las últimas 5 × 1.000, o None si no caminaron (spec PUZZLE_APRENDIBLE, decisión
    12). Si la corrida tiene menos de 10 generaciones, todos quedan en None. etapa_maxima: la etapa
    más alta a la que llegó algún agente en cualquier generación. generacion_cofre: la primera
    generación en que algún agente abrió el cofre, o None. acercarse: si corrió con la recompensa por
    acercarse. curriculo: si alguna generación nació con la llave roja; ultimas_con_curriculo: si
    alguna de las últimas 5 (un CSV de antes del spec no tiene esas columnas: no).
    """
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    ultima = filas[-1]
    con_cofre = [int(fila["generacion"]) for fila in filas if int(fila["agentes_cofre"]) > 0]
    con_curriculo = [int(fila.get("etapa_inicial", 0)) > 0 for fila in filas]
    resumen = {
        "semilla": int(ultima["semilla"]),
        "modo": ultima["modo"],
        "evolucion": ultima["evolucion"] == "1",
        "acercarse": ultima.get("acercarse") == "1",
        "curriculo": any(con_curriculo),
        "ultimas_con_curriculo": any(con_curriculo[-VENTANA:]),
        "generaciones": len(filas),
        "etapa_maxima": max(_etapa(fila) for fila in filas),
        "generacion_cofre": con_cofre[0] if con_cofre else None,
    }
    for nombre, columna in (("fitness", "fitness_prom"), ("manzanas", "manzanas_prom")):
        if len(filas) >= MINIMO_GENERACIONES:
            inicio = statistics.mean(float(fila[columna]) for fila in filas[:VENTANA])
            final = statistics.mean(float(fila[columna]) for fila in filas[-VENTANA:])
            resumen.update({f"{nombre}_inicio": inicio, f"{nombre}_final": final,
                            f"{nombre}_dif": final - inicio})
        else:
            resumen.update(dict.fromkeys([f"{nombre}_inicio", f"{nombre}_final", f"{nombre}_dif"]))
    for clave, columna in (("supervivencia", "edad_prom"), ("llave_roja", "agentes_llave_roja"),
                           ("puerta_madera", "agentes_puerta_madera"), ("distancia", "distancia_prom")):
        resumen[clave] = (statistics.mean(float(fila[columna]) for fila in filas[-VENTANA:])
                          if len(filas) >= MINIMO_GENERACIONES else None)
    distancia = resumen.pop("distancia")
    resumen["llave_roja_por_1000"] = (resumen["llave_roja"] / distancia * 1000 if distancia else None)
    return resumen


def resumir_grupo(corridas):
    """Promedio, desvío muestral y cantidad, entre semillas, de cada número de CLAVES (decisión 14).
    Un grupo son las corridas de un modo, con evolución o sin ella.

    Los None no cuentan: una corrida fuera de las ventanas no entra en los promedios de fitness y
    manzanas, y generacion_cofre se promedia solo entre las que abrieron el cofre.
    """
    resumen = {}
    for clave in CLAVES:
        valores = [corrida[clave] for corrida in corridas if corrida[clave] is not None]
        resumen[clave] = {
            "promedio": statistics.mean(valores) if valores else None,
            "desvio": statistics.stdev(valores) if len(valores) > 1 else None,
            "n": len(valores),
        }
    return resumen


def _pares(corridas, grupo_a, grupo_b):
    """Por cada semilla que tiene las dos corridas, el par (corrida de grupo_a, corrida de grupo_b).
    Cada grupo es un (modo, evolucion)."""
    por_semilla = {}
    for corrida in corridas:
        por_semilla.setdefault(corrida["semilla"], {})[(corrida["modo"], corrida["evolucion"])] = corrida
    return [(par[grupo_a], par[grupo_b]) for par in por_semilla.values()
            if grupo_a in par and grupo_b in par]


def _contar(pares, clave):
    """(K, N): en cuántos pares la primera corrida tiene más que la segunda en esa clave. N son los
    pares con los dos valores (fuera de las ventanas, un valor es None). Un empate no cuenta."""
    valores = [(a[clave], b[clave]) for a, b in pares if a[clave] is not None and b[clave] is not None]
    return (sum(x > y for x, y in valores), len(valores))


def comparar_evolucion(corridas, modo):
    """En cuántas semillas, en ese modo, la evolución superó a la línea base (decisión 29,
    comparaciones 1 y 2): subió más en fitness y en manzanas por agente (la diferencia entre las
    últimas 5 y las 5 primeras), y tuvo más agentes con llave roja en las últimas 5. También, en las
    últimas 5, más agentes con la puerta de madera abierta y más llave roja por 1.000 px (spec
    PUZZLE_APRENDIBLE, decisión 12).

    Devuelve {"fitness": (K, N), "manzanas": (K, N), "llave_roja": (K, N), "puerta_madera": (K, N),
    "llave_roja_por_1000": (K, N)}.
    """
    pares = _pares(corridas, (modo, True), (modo, False))
    return {"fitness": _contar(pares, "fitness_dif"), "manzanas": _contar(pares, "manzanas_dif"),
            "llave_roja": _contar(pares, "llave_roja"), "puerta_madera": _contar(pares, "puerta_madera"),
            "llave_roja_por_1000": _contar(pares, "llave_roja_por_1000")}


def criterio_puerta_de_madera(corridas):
    """El criterio del ítem 5 (spec PUZZLE_APRENDIBLE, decisión 13), en el autónomo: en cuántas
    semillas la corrida con evolución tuvo en las últimas 5 al menos 1 agente por generación con la
    puerta de madera abierta, en promedio, y más que su línea base (un empate no cuenta). (K, N)."""
    pares = [(con, sin) for con, sin in _pares(corridas, ("autonomo", True), ("autonomo", False))
             if con["puerta_madera"] is not None and sin["puerta_madera"] is not None]
    return (sum(con["puerta_madera"] >= 1 and con["puerta_madera"] > sin["puerta_madera"]
                for con, sin in pares), len(pares))


def comparar_modos(corridas, evolucion):
    """En cuántas semillas el guiado tuvo más que el autónomo en las últimas 5, con evolución o sin
    ella (decisión 29, comparación 3): manzanas por agente y agentes con llave roja.

    Devuelve {"manzanas": (K, N), "llave_roja": (K, N)}.
    """
    pares = _pares(corridas, ("guiado", evolucion), ("autonomo", evolucion))
    return {"manzanas": _contar(pares, "manzanas_final"), "llave_roja": _contar(pares, "llave_roja")}


def _evolucion(evolucion):
    return "Con evolución" if evolucion else "Sin evolución"


def _k_de_n(conteo):
    return f"{conteo[0]} de {conteo[1]}"


def _numero(valor, decimales=2):
    return "—" if valor is None else f"{valor:.{decimales}f}"


def _promedio_desvio(estadistica, decimales=2):
    texto = _numero(estadistica["promedio"], decimales)
    if estadistica["desvio"] is not None:
        texto += f" ± {estadistica['desvio']:.{decimales}f}"
    return texto


def _fila_md(celdas):
    return "| " + " | ".join(celdas) + " |"


def _ruta_md(ruta):
    """Ruta relativa a la raíz y con barras /, para que se lea igual en cualquier sistema."""
    ruta = Path(ruta)
    try:
        ruta = ruta.relative_to(RAIZ)
    except ValueError:
        pass
    return ruta.as_posix()


def _orden(corrida):
    """Por semilla, el guiado antes que el autónomo y con evolución antes que sin."""
    return (corrida["semilla"], MODOS.index(corrida["modo"]), not corrida["evolucion"])


def _linea_del_criterio(corridas, llave_roja_por_1000):
    """El renglón del criterio del ítem 5 (spec PUZZLE_APRENDIBLE, decisión 13), con su veredicto.
    Fuera de las 5 semillas del criterio, no se aplica."""
    k, n = criterio_puerta_de_madera(corridas)
    texto = (f"- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por "
             f"generación con la puerta de madera abierta en las últimas 5 y más que la línea base, "
             f"en {k} de {n} semillas; secundario, más llave roja por 1.000 px que la línea base, en "
             f"{_k_de_n(llave_roja_por_1000)}. Cada uno pide {CRITERIO_MINIMO} de {CRITERIO_SEMILLAS}. ")
    if n != CRITERIO_SEMILLAS:
        return texto + f"**No se aplica:** el criterio es sobre {CRITERIO_SEMILLAS} semillas."
    aprende = "sí" if k >= CRITERIO_MINIMO else "no"
    secundario = "sí" if llave_roja_por_1000[0] >= CRITERIO_MINIMO else "no"
    return (texto + f"**El autónomo aprende a pasar la puerta de madera: {aprende}.** "
                    f"Secundario: {secundario}.")


def _comparaciones(corridas):
    """Los renglones de las comparaciones pareadas de la decisión 29, de los modos que corrieron."""
    modos = [modo for modo in MODOS if any(corrida["modo"] == modo for corrida in corridas)]
    lineas = []
    for modo in sorted(modos, key=lambda m: m != "autonomo"):  # el autónomo primero: la pregunta 1
        comparacion = comparar_evolucion(corridas, modo)
        lineas.append(f"- **{NOMBRES_DE_MODOS[modo]}, con evolución contra sin:** la evolución subió más "
                      f"en fitness en {_k_de_n(comparacion['fitness'])} semillas, en manzanas por "
                      f"agente en {_k_de_n(comparacion['manzanas'])}, y tuvo más agentes con llave "
                      f"roja en las últimas 5 en {_k_de_n(comparacion['llave_roja'])}, más con la "
                      f"puerta de madera abierta en {_k_de_n(comparacion['puerta_madera'])} y más llave "
                      f"roja por 1.000 px en {_k_de_n(comparacion['llave_roja_por_1000'])}.")
        if modo == "autonomo":
            lineas.append(_linea_del_criterio(corridas, comparacion["llave_roja_por_1000"]))
    if len(modos) == 2:
        con, sin = comparar_modos(corridas, True), comparar_modos(corridas, False)
        lineas.append(f"- **Guiado contra autónomo, en las últimas 5:** con evolución, el guiado tuvo "
                      f"más manzanas por agente en {_k_de_n(con['manzanas'])} semillas y más agentes "
                      f"con llave roja en {_k_de_n(con['llave_roja'])}; sin evolución, más manzanas "
                      f"en {_k_de_n(sin['manzanas'])} y más agentes con llave roja en "
                      f"{_k_de_n(sin['llave_roja'])}.")
    return lineas


def resumen_markdown(corridas, fallidas, comando, deslizar=False):
    """Arma el resumen en Markdown: por grupo (modo × evolución), las comparaciones pareadas, por
    corrida, las que tienen generaciones del currículo en las últimas 5 y las que fallaron. deslizar
    viene del flag: no es una columna del CSV."""
    ayudas = [nombre for nombre, clave in (("recompensa por acercarse", "acercarse"),
                                           ("currículo", "curriculo"))
              if any(corrida[clave] for corrida in corridas)]
    ayudas = " y ".join(ayudas + (["deslizar al chocar"] if deslizar else [])) or "ninguna"
    lineas = [f"`{comando}`", "",
              f"**Ayudas prendidas:** {ayudas}.", "",
              "**Por grupo** (promedio ± desvío muestral entre semillas):", "",
              _fila_md(["Modo", "Evolución", "Corridas", "Fitness prom., gens 1-5",
                        "Fitness prom., últimas 5", "Diferencia", "Manzanas por agente, gens 1-5",
                        "Manzanas por agente, últimas 5", "Diferencia", "Edad prom. (ticks), últimas 5",
                        "Agentes con llave roja, últimas 5", "Etapa máxima (0-5)", "Cofre abierto"]),
              _fila_md(["---"] * 13)]
    for modo in MODOS:
        for evolucion in (True, False):
            del_grupo = [corrida for corrida in corridas
                         if corrida["modo"] == modo and corrida["evolucion"] == evolucion]
            if not del_grupo:
                continue
            grupo = resumir_grupo(del_grupo)
            cofre = f"{grupo['generacion_cofre']['n']} de {len(del_grupo)}"
            if grupo["generacion_cofre"]["n"]:
                cofre += f" (gen. {_promedio_desvio(grupo['generacion_cofre'], 1)})"
            lineas.append(_fila_md(
                [modo, _evolucion(evolucion), str(len(del_grupo))]
                + [_promedio_desvio(grupo[clave]) for clave in CLAVES[:6]]
                + [_promedio_desvio(grupo["supervivencia"], 0), _promedio_desvio(grupo["llave_roja"]),
                   _promedio_desvio(grupo["etapa_maxima"], 1), cofre]))

    lineas += ["", "**Comparaciones pareadas por semilla** (un empate no cuenta como más):", ""]
    lineas += _comparaciones(corridas)
    lineas += ["",
               "**Por corrida:**", "",
               _fila_md(["Semilla", "Modo", "Evolución", "Generaciones", "Fitness prom., gens 1-5",
                         "Fitness prom., últimas 5", "Diferencia", "Manzanas por agente, gens 1-5",
                         "Manzanas por agente, últimas 5", "Diferencia", "Edad prom., últimas 5",
                         "Agentes con llave roja, últimas 5", "Puerta de madera, últimas 5",
                         "Llave roja por 1.000 px", "Etapa máxima", "Cofre en la gen."]),
               _fila_md(["---"] * 16)]
    for corrida in sorted(corridas, key=_orden):
        lineas.append(_fila_md(
            [str(corrida["semilla"]), corrida["modo"], _evolucion(corrida["evolucion"]),
             str(corrida["generaciones"])]
            + [_numero(corrida[clave]) for clave in CLAVES[:6]]
            + [_numero(corrida["supervivencia"], 0), _numero(corrida["llave_roja"]),
               _numero(corrida["puerta_madera"]), _numero(corrida["llave_roja_por_1000"]),
               str(corrida["etapa_maxima"]),
               "—" if corrida["generacion_cofre"] is None else str(corrida["generacion_cofre"])]))

    # Decisión 12: las últimas 5 tienen que ser del puzzle de hoy, que es donde se mide
    marcadas = [corrida for corrida in sorted(corridas, key=_orden) if corrida["ultimas_con_curriculo"]]
    if marcadas:
        lineas += ["", "**Corridas con generaciones del currículo entre las últimas 5** (no son todas del "
                       "puzzle de hoy: alguna nació con la llave roja):", ""]
        lineas += [f"- Semilla {corrida['semilla']}, {corrida['modo']}, "
                   f"{_evolucion(corrida['evolucion']).lower()}." for corrida in marcadas]

    if fallidas:
        lineas += ["", "**Corridas que fallaron** (fuera del resumen):", ""]
        lineas += [f"- Semilla {f['semilla']}, {f['modo']}, {_evolucion(f['evolucion']).lower()}: "
                   f"salió con código {f['codigo']}. Log: `{_ruta_md(f['log'])}`" for f in fallidas]
    return "\n".join(lineas) + "\n"


# --- Lanzador -----------------------------------------------------------------------------------

def _leer_argumentos(argv):
    parser = argparse.ArgumentParser(
        description="Corre main.py en cada modo, con evolución y sin evolución, en varias semillas, "
                    "en paralelo, y resume las comparaciones en resumen.md.",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Muestra esta ayuda y sale.")
    parser.add_argument("--semillas", type=int, nargs="+", default=[1, 2, 3, 4, 5], metavar="S",
                        help="Semillas a correr, cada una con evolución y sin evolución. Por defecto, 1 a 5.")
    parser.add_argument("--generaciones", type=int, default=20, metavar="N",
                        help=f"Generaciones por corrida. Por defecto 20; el mínimo es {MINIMO_GENERACIONES}.")
    parser.add_argument("--modos", nargs="+", choices=MODOS, default=list(MODOS), metavar="MODO",
                        help="Modos a correr (guiado, autonomo), cada uno con evolución y sin evolución. "
                             "Por defecto, los dos.")
    parser.add_argument("--acercarse", action="store_true",
                        help="Corre todas con la recompensa por acercarse al próximo paso del puzzle "
                             "(--acercarse de main.py).")
    parser.add_argument("--curriculo", action="store_true",
                        help="Corre todas con el currículo: las primeras generaciones nacen con la llave "
                             "roja (--curriculo de main.py).")
    parser.add_argument("--deslizar", action="store_true",
                        help="Corre todas deslizando contra lo que choca: si el paso choca, se mueven "
                             "por el eje libre (--deslizar de main.py).")
    parser.add_argument("--paralelo", type=int, default=max(1, (os.cpu_count() or 2) - 1), metavar="K",
                        help="Corridas a la vez. Por defecto, los núcleos menos uno.")
    args = parser.parse_args(argv)
    if args.generaciones < MINIMO_GENERACIONES:
        parser.error(f"--generaciones tiene que ser {MINIMO_GENERACIONES} o más: el resumen compara "
                     f"las {VENTANA} primeras generaciones con las {VENTANA} últimas")
    if args.paralelo < 1:
        parser.error("--paralelo tiene que ser 1 o más")
    if any(not 0 <= semilla < 2**32 for semilla in args.semillas):
        parser.error("cada semilla tiene que estar entre 0 y 4294967295")
    args.semillas = list(dict.fromkeys(args.semillas))  # una semilla repetida pisaría su propio CSV
    args.modos = list(dict.fromkeys(args.modos))
    return args


def _correr(semilla, modo, evolucion, generaciones, carpeta, acercarse=False, curriculo=False,
            deslizar=False):
    """Corre main.py sin ventana, con la salida a un log, y devuelve cómo terminó. El CSV y el log se
    llaman como la ruta por defecto de main.py."""
    nombre = (f"corrida_s{semilla}_{modo}{'_acercarse' if acercarse else ''}"
              f"{'_curriculo' if curriculo else ''}{'_deslizar' if deslizar else ''}_"
              f"{'evolucion' if evolucion else 'sin_evolucion'}")
    ruta_csv, ruta_log = carpeta / f"{nombre}.csv", carpeta / f"{nombre}.log"
    # -u: el log se escribe a medida que corre, y una corrida cortada no pierde la cola
    comando = [sys.executable, "-u", "main.py", "--sin-ventana", "--generaciones", str(generaciones),
               "--semilla", str(semilla), "--modo", modo, "--csv", str(ruta_csv)]
    if not evolucion:
        comando.append("--sin-evolucion")
    if acercarse:
        comando.append("--acercarse")
    if curriculo:
        comando.append("--curriculo")
    if deslizar:
        comando.append("--deslizar")
    inicio = time.monotonic()
    # cwd en la raíz: main.py carga los sprites con una ruta relativa
    with open(ruta_log, "wb") as log:
        codigo = subprocess.run(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT).returncode
    return {"semilla": semilla, "modo": modo, "evolucion": evolucion, "codigo": codigo,
            "csv": ruta_csv, "log": ruta_log, "segundos": time.monotonic() - inicio}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")  # la salida redirigida en Windows usa cp1252 (DIAG-25)
    sys.stderr.reconfigure(encoding="utf-8")
    args = _leer_argumentos(argv)

    carpeta = RAIZ / "results" / f"experimento_{datetime.now():%Y%m%d-%H%M%S}"
    carpeta.mkdir(parents=True)
    tareas = [(semilla, modo, evolucion) for semilla in args.semillas for modo in args.modos
              for evolucion in (True, False)]
    print(f"🧪 {len(tareas)} corridas ({len(args.semillas)} semillas × {len(args.modos)} modos × con y "
          f"sin evolución) de {args.generaciones} generaciones, {args.paralelo} a la vez")
    print(f"📁 {_ruta_md(carpeta)}")

    resultados = []
    with ThreadPoolExecutor(max_workers=args.paralelo) as pool:
        futuros = [pool.submit(_correr, semilla, modo, evolucion, args.generaciones, carpeta, args.acercarse,
                               args.curriculo, args.deslizar)
                   for semilla, modo, evolucion in tareas]
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            resultados.append(resultado)
            estado = "✅" if resultado["codigo"] == 0 else f"❌ código {resultado['codigo']},"
            print(f"{estado} semilla {resultado['semilla']} {resultado['modo']} "
                  f"{_evolucion(resultado['evolucion']).lower()} "
                  f"({len(resultados)} de {len(tareas)}, {resultado['segundos']:.0f} s)", flush=True)

    corridas = [resumir_corrida(r["csv"]) for r in resultados if r["codigo"] == 0]
    fallidas = sorted((r for r in resultados if r["codigo"] != 0), key=_orden)
    comando = (f"python experimento.py --semillas {' '.join(map(str, args.semillas))} "
               f"--generaciones {args.generaciones} --modos {' '.join(args.modos)}"
               f"{' --acercarse' if args.acercarse else ''}{' --curriculo' if args.curriculo else ''}"
               f"{' --deslizar' if args.deslizar else ''}")
    texto = (f"# Experimento: modos guiado y autónomo, con evolución y sin ella\n\n"
             f"{datetime.now():%Y-%m-%d} · carpeta `{_ruta_md(carpeta)}`\n\n"
             + resumen_markdown(corridas, fallidas, comando, args.deslizar))
    (carpeta / "resumen.md").write_text(texto, encoding="utf-8")
    print()
    print(texto)
    print(f"📄 Resumen: {_ruta_md(carpeta / 'resumen.md')}")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
