"""
Test de humo: corre main.py como lo correría una persona, con sus flags reales.

Cuida lo que el spec MEDIR_ANTES_DE_TOCAR necesita que siga andando: que la corrida sin ventana
termine, que deje el CSV con las columnas acordadas y que la misma semilla dé el mismo archivo.
Las tres corridas se lanzan juntas, así el test tarda lo que tarda una.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 7
GENERACIONES = 2
TIMEOUT_S = 180

# Decisión 6 del spec, escrita acá a propósito (no importada de main.py): si cambia, el test avisa
COLUMNAS = [
    "semilla", "evolucion", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "distancia_prom", "diversidad",
    "arboles_cortados", "llave_roja", "puerta_madera", "llave_dorada", "puerta_hierro", "cofre",
]

# Nombre de la corrida → flags extra
CORRIDAS = {
    "evolucion_1": [],
    "evolucion_2": [],
    "sin_evolucion": ["--sin-evolucion"],
}


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    """Lanza las tres corridas en paralelo y devuelve, por nombre, su código de salida, CSV y log."""
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


def test_la_misma_semilla_da_el_mismo_csv(corridas):
    assert corridas["evolucion_1"]["csv"].read_bytes() == corridas["evolucion_2"]["csv"].read_bytes()


def test_sin_evolucion_arranca_igual_que_con_evolucion(corridas):
    con = _filas(corridas["evolucion_1"]["csv"])[1]
    sin = _filas(corridas["sin_evolucion"]["csv"])[1]
    i = COLUMNAS.index("evolucion")
    assert (con[i], sin[i]) == ("1", "0")
    # Con la misma semilla, la generación 1 es la misma en los dos modos: lo distinto empieza
    # cuando se arma la generación 2
    assert con[:i] + con[i + 1:] == sin[:i] + sin[i + 1:]


def test_el_resumen_final_dice_el_tiempo_simulado(corridas):
    # DIAG-15: decía "Tiempo total: 0.0 minutos" (división entera, y solo de la última generación).
    # Dos generaciones de 960 ticks, a 60 ticks por segundo, son 0,53 minutos simulados
    for nombre, corrida in corridas.items():
        log = corrida["log"].read_text(encoding="utf-8", errors="replace")
        assert "Tiempo simulado: 0.5 minutos" in log, f"{nombre}:\n{_cola_del_log(corrida)}"
