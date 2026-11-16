"""
Test de humo: corre main.py como lo correría una persona, con sus flags reales.

Cuida lo que el spec MEDIR_ANTES_DE_TOCAR necesita que siga andando: que la corrida sin ventana
termine, que deje el CSV con las columnas acordadas y que la misma semilla dé el mismo archivo. En
los dos modos (spec MODO_GUIADO_Y_AUTONOMO, decisión 31), y en el autónomo con la recompensa por
acercarse y con el currículo (spec PUZZLE_APRENDIBLE, decisión 16). Las doce corridas se lanzan
juntas, así el test tarda lo que tarda una.
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

# Decisión 6 del spec (con modo, edad_prom y agentes_*, de MODO_GUIADO_Y_AUTONOMO, y acercarse y
# etapa_inicial, de PUZZLE_APRENDIBLE), escrita acá a propósito (no importada de main.py): si cambia,
# el test avisa
COLUMNAS = [
    "semilla", "evolucion", "modo", "acercarse", "generacion", "etapa_inicial", "ticks",
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
    "autonomo_acercarse_evolucion_1": ["--modo", "autonomo", "--acercarse"],
    "autonomo_acercarse_evolucion_2": ["--modo", "autonomo", "--acercarse"],
    "autonomo_acercarse_sin_evolucion": ["--modo", "autonomo", "--acercarse", "--sin-evolucion"],
    "autonomo_curriculo_evolucion_1": ["--modo", "autonomo", "--curriculo"],
    "autonomo_curriculo_evolucion_2": ["--modo", "autonomo", "--curriculo"],
    "autonomo_curriculo_sin_evolucion": ["--modo", "autonomo", "--curriculo", "--sin-evolucion"],
}
POBLACION = 60  # POPULATION_SIZE de config.py: en el currículo, todos nacen con la llave roja


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    """Lanza las doce corridas en paralelo y devuelve, por nombre, su código de salida, CSV y log."""
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


@pytest.mark.parametrize("prefijo", ["", "autonomo_", "autonomo_acercarse_", "autonomo_curriculo_"])
def test_la_misma_semilla_da_el_mismo_csv(corridas, prefijo):
    uno, dos = corridas[f"{prefijo}evolucion_1"]["csv"], corridas[f"{prefijo}evolucion_2"]["csv"]
    assert uno.read_bytes() == dos.read_bytes()


@pytest.mark.parametrize("prefijo", ["", "autonomo_", "autonomo_acercarse_", "autonomo_curriculo_"])
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


def test_acercarse_va_en_el_csv_y_no_cambia_la_linea_base(corridas):
    # Spec PUZZLE_APRENDIBLE, decisiones 11 y 16. Sin evolución el fitness no elige a nadie, y en el
    # autónomo no guía: con el switch y sin él, la corrida es la misma salvo el fitness y acercarse
    i = COLUMNAS.index("acercarse")
    for nombre, corrida in corridas.items():
        esperado = "1" if "_acercarse_" in nombre else "0"
        assert {fila[i] for fila in _filas(corrida["csv"])[1:]} == {esperado}, nombre
    sin = _filas(corridas["autonomo_sin_evolucion"]["csv"])[1:]
    con = _filas(corridas["autonomo_acercarse_sin_evolucion"]["csv"])[1:]
    assert len(sin) == len(con) == GENERACIONES
    otras = [j for j, columna in enumerate(COLUMNAS)
             if not columna.startswith("fitness_") and columna != "acercarse"]
    for fila_sin, fila_con in zip(sin, con):
        assert [fila_sin[j] for j in otras] == [fila_con[j] for j in otras]
    # El término está: el fitness promedio sube en cada generación
    j = COLUMNAS.index("fitness_prom")
    assert all(float(fila_con[j]) > float(fila_sin[j]) for fila_sin, fila_con in zip(sin, con))


def test_etapa_inicial_va_en_el_csv_y_con_el_curriculo_todos_nacen_con_la_llave(corridas):
    # Spec PUZZLE_APRENDIBLE, decisiones 8 y 11. Las dos generaciones son del currículo (las 15
    # primeras): con --curriculo nacen todos en la etapa 1, con evolución y sin ella; sin, en la 0
    i, j = COLUMNAS.index("etapa_inicial"), COLUMNAS.index("agentes_llave_roja")
    for nombre, corrida in corridas.items():
        filas = _filas(corrida["csv"])[1:]
        esperado = "1" if "_curriculo_" in nombre else "0"
        assert {fila[i] for fila in filas} == {esperado}, nombre
        if esperado == "1":
            assert {fila[j] for fila in filas} == {str(POBLACION)}, nombre


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
    # Decisión 5: un hito es la primera vez en la corrida que un agente da un paso. Su generación es
    # la primera fila del CSV con esa columna mayor que 0 que no nació con ese paso dado (spec
    # PUZZLE_APRENDIBLE, decisión 10), y cada paso dado tiene su línea
    for nombre, corrida in corridas.items():
        log = corrida["log"].read_text(encoding="utf-8", errors="replace")
        lineas = [LINEA_DE_HITO.match(linea) for linea in log.splitlines()]
        generacion_del_log = {m.group(1): int(m.group(3)) for m in lineas if m}
        assert len(generacion_del_log) == len([m for m in lineas if m]), f"{nombre}: un hito repetido"
        encabezado, *filas = _filas(corrida["csv"])
        g, e = encabezado.index("generacion"), encabezado.index("etapa_inicial")
        for paso, (titulo, columna) in enumerate(HITOS, start=1):
            i = encabezado.index(columna)
            primera = next((int(fila[g]) for fila in filas if int(fila[i]) > 0 and int(fila[e]) < paso),
                           None)
            assert generacion_del_log.get(titulo) == primera, f"{nombre}: {titulo}"
