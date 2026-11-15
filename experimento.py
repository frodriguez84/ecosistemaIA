"""
Experimento: con evolución contra sin evolución, en varias semillas.

Corre main.py sin ventana para cada semilla, una vez con evolución y otra con la línea base
(--sin-evolucion), varias a la vez. Cada corrida deja su CSV y su log en
results/experimento_<AAAAMMDD-HHMMSS>/. Al final arma resumen.md: tablas Markdown para pegar tal
cual en docs/qa/AnalisisQA.md (spec MEDIR_ANTES_DE_TOCAR, decisiones 12 a 14).

Uso: python experimento.py [--semillas 1 2 3 4 5] [--generaciones 20] [--paralelo K]

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

# Los números del resumen por corrida que se promedian entre semillas (decisiones 13 y 14;
# supervivencia y puzzle: spec MODO_GUIADO_Y_AUTONOMO, decisión 29)
CLAVES = ["fitness_inicio", "fitness_final", "fitness_dif",
          "manzanas_inicio", "manzanas_final", "manzanas_dif",
          "supervivencia", "llave_roja", "etapa_maxima", "generacion_cofre"]


# --- Resumen ------------------------------------------------------------------------------------

def _etapa(fila):
    """La etapa más alta a la que llegó algún agente en esa generación, de 0 a 5."""
    return max((etapa for etapa, columna in enumerate(COLUMNAS_PUZZLE, start=1)
                if int(fila[columna]) > 0), default=0)


def resumir_corrida(ruta_csv):
    """Resume el CSV de una corrida (decisión 13; el puzzle, spec MODO_GUIADO_Y_AUTONOMO, decisión 29).

    fitness y manzanas: promedio de la columna *_prom en las generaciones 1-5 (inicio), en las
    últimas 5 (final) y su diferencia. supervivencia: promedio de edad_prom (ticks vividos) en las
    últimas 5. llave_roja: promedio de agentes_llave_roja en las últimas 5. Si la corrida tiene
    menos de 10 generaciones, todos quedan en None. etapa_maxima: la etapa más alta a la que llegó
    algún agente en cualquier generación. generacion_cofre: la primera generación en que algún
    agente abrió el cofre, o None.
    """
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    ultima = filas[-1]
    con_cofre = [int(fila["generacion"]) for fila in filas if int(fila["agentes_cofre"]) > 0]
    resumen = {
        "semilla": int(ultima["semilla"]),
        "evolucion": ultima["evolucion"] == "1",
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
    for clave, columna in (("supervivencia", "edad_prom"), ("llave_roja", "agentes_llave_roja")):
        resumen[clave] = (statistics.mean(float(fila[columna]) for fila in filas[-VENTANA:])
                          if len(filas) >= MINIMO_GENERACIONES else None)
    return resumen


def resumir_modo(corridas):
    """Promedio, desvío muestral y cantidad, entre semillas, de cada número de CLAVES (decisión 14).

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


def comparar_por_semilla(corridas):
    """En cuántas semillas la evolución subió más que la línea base (decisión 14).

    Devuelve {"fitness": (K, N), "manzanas": (K, N)}. N son las semillas con las dos corridas
    dentro de las ventanas. Un empate no cuenta como que la evolución subió más.
    """
    por_semilla = {}
    for corrida in corridas:
        por_semilla.setdefault(corrida["semilla"], {})[corrida["evolucion"]] = corrida
    comparacion = {}
    for nombre in ("fitness", "manzanas"):
        clave = f"{nombre}_dif"
        pares = [(par[True][clave], par[False][clave]) for par in por_semilla.values()
                 if True in par and False in par
                 and par[True][clave] is not None and par[False][clave] is not None]
        comparacion[nombre] = (sum(con > sin for con, sin in pares), len(pares))
    return comparacion


def _modo(evolucion):
    return "Con evolución" if evolucion else "Sin evolución"


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


def resumen_markdown(corridas, fallidas, comando):
    """Arma el resumen en Markdown: por modo, la comparación pareada, por corrida y las que fallaron."""
    lineas = [f"`{comando}`", "",
              "**Por modo** (promedio ± desvío muestral entre semillas):", "",
              _fila_md(["Modo", "Corridas", "Fitness prom., gens 1-5", "Fitness prom., últimas 5",
                        "Diferencia", "Manzanas por agente, gens 1-5", "Manzanas por agente, últimas 5",
                        "Diferencia", "Edad prom. (ticks), últimas 5",
                        "Agentes con llave roja, últimas 5", "Etapa máxima (0-5)", "Cofre abierto"]),
              _fila_md(["---"] * 12)]
    for evolucion in (True, False):
        del_modo = [corrida for corrida in corridas if corrida["evolucion"] == evolucion]
        if not del_modo:
            continue
        modo = resumir_modo(del_modo)
        cofre = f"{modo['generacion_cofre']['n']} de {len(del_modo)}"
        if modo["generacion_cofre"]["n"]:
            cofre += f" (gen. {_promedio_desvio(modo['generacion_cofre'], 1)})"
        lineas.append(_fila_md(
            [_modo(evolucion), str(len(del_modo))]
            + [_promedio_desvio(modo[clave]) for clave in CLAVES[:6]]
            + [_promedio_desvio(modo["supervivencia"], 0), _promedio_desvio(modo["llave_roja"]),
               _promedio_desvio(modo["etapa_maxima"], 1), cofre]))

    comparacion = comparar_por_semilla(corridas)
    fitness_k, fitness_n = comparacion["fitness"]
    manzanas_k, manzanas_n = comparacion["manzanas"]
    lineas += ["",
               f"**Comparación pareada por semilla:** la evolución subió más que la línea base en "
               f"{fitness_k} de {fitness_n} semillas en fitness, y en {manzanas_k} de {manzanas_n} "
               f"en manzanas por agente.",
               "",
               "**Por corrida:**", "",
               _fila_md(["Semilla", "Modo", "Generaciones", "Fitness prom., gens 1-5",
                         "Fitness prom., últimas 5", "Diferencia", "Manzanas por agente, gens 1-5",
                         "Manzanas por agente, últimas 5", "Diferencia", "Edad prom., últimas 5",
                         "Agentes con llave roja, últimas 5", "Etapa máxima", "Cofre en la gen."]),
               _fila_md(["---"] * 13)]
    for corrida in sorted(corridas, key=lambda c: (c["semilla"], not c["evolucion"])):
        lineas.append(_fila_md(
            [str(corrida["semilla"]), _modo(corrida["evolucion"]), str(corrida["generaciones"])]
            + [_numero(corrida[clave]) for clave in CLAVES[:6]]
            + [_numero(corrida["supervivencia"], 0), _numero(corrida["llave_roja"]),
               str(corrida["etapa_maxima"]),
               "—" if corrida["generacion_cofre"] is None else str(corrida["generacion_cofre"])]))

    if fallidas:
        lineas += ["", "**Corridas que fallaron** (fuera del resumen):", ""]
        lineas += [f"- Semilla {f['semilla']}, {_modo(f['evolucion']).lower()}: salió con código "
                   f"{f['codigo']}. Log: `{_ruta_md(f['log'])}`" for f in fallidas]
    return "\n".join(lineas) + "\n"


# --- Lanzador -----------------------------------------------------------------------------------

def _leer_argumentos(argv):
    parser = argparse.ArgumentParser(
        description="Corre main.py con evolución y sin evolución en varias semillas, en paralelo, "
                    "y resume la comparación en resumen.md.",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Muestra esta ayuda y sale.")
    parser.add_argument("--semillas", type=int, nargs="+", default=[1, 2, 3, 4, 5], metavar="S",
                        help="Semillas a correr, cada una con evolución y sin evolución. Por defecto, 1 a 5.")
    parser.add_argument("--generaciones", type=int, default=20, metavar="N",
                        help=f"Generaciones por corrida. Por defecto 20; el mínimo es {MINIMO_GENERACIONES}.")
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
    return args


def _correr(semilla, evolucion, generaciones, carpeta):
    """Corre main.py sin ventana, con la salida a un log, y devuelve cómo terminó."""
    nombre = f"corrida_s{semilla}_{'evolucion' if evolucion else 'sin_evolucion'}"
    ruta_csv, ruta_log = carpeta / f"{nombre}.csv", carpeta / f"{nombre}.log"
    # -u: el log se escribe a medida que corre, y una corrida cortada no pierde la cola
    comando = [sys.executable, "-u", "main.py", "--sin-ventana", "--generaciones", str(generaciones),
               "--semilla", str(semilla), "--csv", str(ruta_csv)]
    if not evolucion:
        comando.append("--sin-evolucion")
    inicio = time.monotonic()
    # cwd en la raíz: main.py carga los sprites con una ruta relativa
    with open(ruta_log, "wb") as log:
        codigo = subprocess.run(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT).returncode
    return {"semilla": semilla, "evolucion": evolucion, "codigo": codigo,
            "csv": ruta_csv, "log": ruta_log, "segundos": time.monotonic() - inicio}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")  # la salida redirigida en Windows usa cp1252 (DIAG-25)
    sys.stderr.reconfigure(encoding="utf-8")
    args = _leer_argumentos(argv)

    carpeta = RAIZ / "results" / f"experimento_{datetime.now():%Y%m%d-%H%M%S}"
    carpeta.mkdir(parents=True)
    tareas = [(semilla, evolucion) for semilla in args.semillas for evolucion in (True, False)]
    print(f"🧪 {len(tareas)} corridas ({len(args.semillas)} semillas × 2 modos) de "
          f"{args.generaciones} generaciones, {args.paralelo} a la vez")
    print(f"📁 {_ruta_md(carpeta)}")

    resultados = []
    with ThreadPoolExecutor(max_workers=args.paralelo) as pool:
        futuros = [pool.submit(_correr, semilla, evolucion, args.generaciones, carpeta)
                   for semilla, evolucion in tareas]
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            resultados.append(resultado)
            estado = "✅" if resultado["codigo"] == 0 else f"❌ código {resultado['codigo']},"
            print(f"{estado} semilla {resultado['semilla']} {_modo(resultado['evolucion']).lower()} "
                  f"({len(resultados)} de {len(tareas)}, {resultado['segundos']:.0f} s)", flush=True)

    corridas = [resumir_corrida(r["csv"]) for r in resultados if r["codigo"] == 0]
    fallidas = sorted((r for r in resultados if r["codigo"] != 0),
                      key=lambda r: (r["semilla"], not r["evolucion"]))
    comando = (f"python experimento.py --semillas {' '.join(map(str, args.semillas))} "
               f"--generaciones {args.generaciones}")
    texto = (f"# Experimento: con evolución contra sin evolución\n\n"
             f"{datetime.now():%Y-%m-%d} · carpeta `{_ruta_md(carpeta)}`\n\n"
             + resumen_markdown(corridas, fallidas, comando))
    (carpeta / "resumen.md").write_text(texto, encoding="utf-8")
    print()
    print(texto)
    print(f"📄 Resumen: {_ruta_md(carpeta / 'resumen.md')}")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
