"""
Test de humo: corre main.py como lo correría una persona, con sus flags reales.

Cuida lo que el spec MEDIR_ANTES_DE_TOCAR necesita que siga andando: que la corrida sin ventana
termine, que deje el CSV con las columnas acordadas y que la misma semilla dé el mismo archivo. En
los dos modos (spec MODO_GUIADO_Y_AUTONOMO, decisión 31). Las seis corridas se lanzan juntas, así el
test tarda lo que tarda una.
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 7
GENERACIONES = 2
TIMEOUT_S = 180

# Decisión 6 del spec (con modo, edad_prom y agentes_*, de MODO_GUIADO_Y_AUTONOMO), escrita acá a
# propósito (no importada de main.py): si cambia, el test avisa
COLUMNAS = [
    "semilla", "evolucion", "modo", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "edad_prom", "distancia_prom", "diversidad",
    "arboles_cortados", "agentes_llave_roja", "agentes_puerta_madera", "agentes_llave_dorada",
    "agentes_puerta_hierro", "agentes_cofre",
]

# Nombre de la corrida → flags extra. Las del guiado van sin --modo: es el modo por defecto
CORRIDAS = {
    "evolucion_1": [],
    "evolucion_2": [],
    "sin_evolucion": ["--sin-evolucion"],
    "autonomo_evolucion_1": ["--modo", "autonomo"],
    "autonomo_evolucion_2": ["--modo", "autonomo"],
    "autonomo_sin_evolucion": ["--modo", "autonomo", "--sin-evolucion"],
}


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    """Lanza las seis corridas en paralelo y devuelve, por nombre, su código de salida, CSV y log."""
    carpeta = tmp_path_factory.mktemp("humo")
    lanzadas = {}
    for nombre, extra in CORRIDAS.items():
        ruta_csv = carpeta / f"{nombre}.csv"
        ruta_log = carpeta / f"{nombre}.log"
        comando = [sys.executable, "main.py", "--sin-ventana",
                   "--generaciones", str(GENERACIONES), "--semilla", str(SEMILLA),
                   "--csv", str(ruta_csv), *extra]
        # La salida va a un archivo: así también se prueba que main.py no se cae con la salida
        # redirigida (DIAG-25)
        log = open(ruta_log, "wb")
        proceso = subprocess.Popen(comando, cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT)
        lanzadas[nombre] = (proceso, log, ruta_csv, ruta_log)

    resultados = {}
    for nombre, (proceso, log, ruta_csv, ruta_log) in lanzadas.items():
        try:
            codigo = proceso.wait(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            proceso.kill()
            codigo = f"timeout de {TIMEOUT_S} s"
        log.close()
        resultados[nombre] = {"codigo": codigo, "csv": ruta_csv, "log": ruta_log}
    return resultados


def _cola_del_log(corrida, lineas=30):
    texto = corrida["log"].read_text(encoding="utf-8", errors="replace")
    return "\n".join(texto.splitlines()[-lineas:])


def _filas(ruta_csv):
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        return list(csv.reader(archivo))


def test_las_corridas_terminan_con_codigo_0(corridas):
    for nombre, corrida in corridas.items():
        assert corrida["codigo"] == 0, f"{nombre} salió con {corrida['codigo']}:\n{_cola_del_log(corrida)}"


def test_el_csv_tiene_las_columnas_y_una_fila_por_generacion(corridas):
    for nombre, corrida in corridas.items():
        encabezado, *filas = _filas(corrida["csv"])
        assert encabezado == COLUMNAS, nombre
        assert [fila[COLUMNAS.index("generacion")] for fila in filas] == ["1", "2"], nombre
        assert {fila[COLUMNAS.index("semilla")] for fila in filas} == {str(SEMILLA)}, nombre


@pytest.mark.parametrize("prefijo", ["", "autonomo_"])
def test_la_misma_semilla_da_el_mismo_csv(corridas, prefijo):
    uno, dos = corridas[f"{prefijo}evolucion_1"]["csv"], corridas[f"{prefijo}evolucion_2"]["csv"]
    assert uno.read_bytes() == dos.read_bytes()


@pytest.mark.parametrize("prefijo", ["", "autonomo_"])
def test_sin_evolucion_arranca_igual_que_con_evolucion(corridas, prefijo):
    con = _filas(corridas[f"{prefijo}evolucion_1"]["csv"])[1]
    sin = _filas(corridas[f"{prefijo}sin_evolucion"]["csv"])[1]
    i = COLUMNAS.index("evolucion")
    assert (con[i], sin[i]) == ("1", "0")
    # Con la misma semilla, la generación 1 es la misma con evolución y sin ella: lo distinto
    # empieza cuando se arma la generación 2
    assert con[:i] + con[i + 1:] == sin[:i] + sin[i + 1:]


def test_el_csv_dice_el_modo_y_el_modo_cambia_la_corrida(corridas):
    # Decisión 28: la columna modo. Sin --modo corre el guiado (decisión 1), y el autónomo, con la
    # misma semilla, da otra corrida desde la generación 1: la guía cambia lo que hacen los agentes
    i = COLUMNAS.index("modo")
    filas = {nombre: _filas(corrida["csv"])[1:] for nombre, corrida in corridas.items()}
    for nombre, filas_de_la_corrida in filas.items():
        esperado = "autonomo" if nombre.startswith("autonomo_") else "guiado"
        assert {fila[i] for fila in filas_de_la_corrida} == {esperado}, nombre
    guiado, autonomo = filas["evolucion_1"][0], filas["autonomo_evolucion_1"][0]
    j = COLUMNAS.index("fitness_prom")
    assert guiado[j] != autonomo[j]


def test_el_resumen_final_dice_el_tiempo_simulado(corridas):
    # DIAG-15: decía "Tiempo total: 0.0 minutos" (división entera, y solo de la última generación).
    # Dos generaciones de 960 ticks, a 60 ticks por segundo, son 0,53 minutos simulados; el boletín
    # lo dice en su encabezado (spec PANTALLAS_VER_APRENDER, decisión 15)
    for nombre, corrida in corridas.items():
        log = corrida["log"].read_text(encoding="utf-8", errors="replace")
        assert " · 2 generaciones · 0,5 min simulados" in log, f"{nombre}:\n{_cola_del_log(corrida)}"


# Los pasos del puzzle: el título de su línea de hito y su columna del CSV, en orden
HITOS = [("¡Primera llave roja!", "agentes_llave_roja"), ("¡Primera puerta abierta!", "agentes_puerta_madera"),
         ("¡Primera llave dorada!", "agentes_llave_dorada"), ("¡Puerta de hierro abierta!", "agentes_puerta_hierro"),
         ("¡Cofre abierto!", "agentes_cofre")]
LINEA_DE_HITO = re.compile(r"^🏆 (¡.+!) Agente (\d+), generación (\d+), segundo (\d+\.\d)$")


def test_cada_hito_del_log_coincide_con_la_primera_generacion_del_csv(corridas):
    # Decisión 5: un hito es la primera vez en la corrida que un agente llega a un paso. Su generación
    # es la primera fila del CSV con esa columna mayor que 0, y cada paso con agentes tiene su línea
    for nombre, corrida in corridas.items():
        log = corrida["log"].read_text(encoding="utf-8", errors="replace")
        lineas = [LINEA_DE_HITO.match(linea) for linea in log.splitlines()]
        generacion_del_log = {m.group(1): int(m.group(3)) for m in lineas if m}
        assert len(generacion_del_log) == len([m for m in lineas if m]), f"{nombre}: un hito repetido"
        encabezado, *filas = _filas(corrida["csv"])
        for titulo, columna in HITOS:
            i = encabezado.index(columna)
            primera = next((int(fila[encabezado.index("generacion")]) for fila in filas if int(fila[i]) > 0),
                           None)
            assert generacion_del_log.get(titulo) == primera, f"{nombre}: {titulo}"
