"""
Tests del registro de la corrida (spec PANTALLAS_VER_APRENDER, decisiones 3 a 7 y 17): el mapa de
calor, los hitos, el mejor agente y que nada de lo nuevo consuma azar.

Usan agentes de mentira: el registro solo lee atributos, así que no hace falta correr la simulación.
"""

import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from main import COLUMNAS_CSV  # noqa: E402
from src.analytics.boletin import armar_boletin, texto_de_consola  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402

ANCHO, ALTO, CELDA = 960, 800, 16
COLUMNAS, FILAS = ANCHO // CELDA, ALTO // CELDA  # 60 × 50


def _agente(id_, x=100.0, y=100.0, vivo=True, etapa=0, fitness=10.0):
    return SimpleNamespace(id=id_, x=x, y=y, alive=vivo, etapa=etapa, fitness=fitness, food_eaten=2,
                           distance_traveled=300.0, age=500)


def _fila(generacion, ticks=960, **valores):
    """Una fila del CSV como la arma main.py, por columna; lo que no se pasa vale 0."""
    fila = dict.fromkeys(COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="guiado", generacion=generacion, ticks=ticks)
    fila.update(valores)
    return fila


def _registro():
    return RegistroDeLaCorrida(ANCHO, ALTO, CELDA)


def _celda(grilla, columna, fila):
    return grilla["cuentas"][fila * COLUMNAS + columna]


# --- Mapa de calor (decisión 7) ---

def test_la_grilla_es_de_60_por_50():
    registro = _registro()
    registro.cerrar_generacion(_fila(1), 960, [_agente(1)])
    assert len(registro.calor_gen1["cuentas"]) == 3000


def test_cada_agente_cuenta_en_su_celda_tambien_en_los_bordes():
    registro = _registro()
    esquinas = [(0.0, 0.0), (959.9, 0.0), (0.0, 799.9), (959.9, 799.9), (16.0, 15.9)]
    registro.contar_posiciones([_agente(i, x, y) for i, (x, y) in enumerate(esquinas)])
    registro.cerrar_generacion(_fila(1, ticks=1), 960, [_agente(1)])
    grilla = registro.calor_gen1
    for columna, fila in [(0, 0), (59, 0), (0, 49), (59, 49), (1, 0)]:
        assert _celda(grilla, columna, fila) == 1, (columna, fila)
    assert sum(grilla["cuentas"]) == 5


def test_fuera_del_area_se_recorta_a_la_grilla():
    registro = _registro()
    registro.contar_posiciones([_agente(1, -3.0, 900.0), _agente(2, 1000.0, -1.0)])
    registro.cerrar_generacion(_fila(1, ticks=1), 960, [_agente(1)])
    assert _celda(registro.calor_gen1, 0, 49) == 1
    assert _celda(registro.calor_gen1, 59, 0) == 1


def test_solo_cuentan_los_vivos():
    registro = _registro()
    registro.contar_posiciones([_agente(1, 100, 100), _agente(2, 100, 100, vivo=False)])
    registro.cerrar_generacion(_fila(1, ticks=1), 960, [_agente(1)])
    assert sum(registro.calor_gen1["cuentas"]) == 1


def test_el_valor_se_normaliza_por_los_ticks_de_su_generacion():
    # Generación 1: 3 ticks con un agente en la celda (6, 6). Generación 2: 6 ticks, 3 en esa celda
    registro = _registro()
    for _ in range(3):
        registro.contar_posiciones([_agente(1, 100, 100)])
    registro.cerrar_generacion(_fila(1, ticks=3), 960, [_agente(1)])
    for i in range(6):
        registro.contar_posiciones([_agente(1, 100 if i < 3 else 500, 100)])
    registro.cerrar_generacion(_fila(2, ticks=6), 960, [_agente(1)])
    celda = 6 * COLUMNAS + 6
    assert registro.valores(registro.calor_gen1)[celda] == 1.0
    assert registro.valores(registro.calor_ultima)[celda] == 0.5


def test_guarda_la_generacion_1_y_la_ultima_y_arranca_cada_una_en_cero():
    registro = _registro()
    for generacion, x in [(1, 100), (2, 300), (3, 500)]:
        registro.contar_posiciones([_agente(1, x, 100)])
        registro.cerrar_generacion(_fila(generacion, ticks=1), 960, [_agente(1)])
    assert registro.calor_gen1["generacion"] == 1 and registro.calor_ultima["generacion"] == 3
    assert sum(registro.calor_gen1["cuentas"]) == 1 and _celda(registro.calor_gen1, 6, 6) == 1
    # La última solo tiene lo suyo: no arrastra lo de la 1 ni lo de la 2
    assert sum(registro.calor_ultima["cuentas"]) == 1 and _celda(registro.calor_ultima, 31, 6) == 1


def test_la_cobertura_es_el_porcentaje_de_celdas_pisadas():
    registro = _registro()
    registro.contar_posiciones([_agente(i, 16.0 * i, 0.0) for i in range(30)])  # 30 celdas distintas
    registro.contar_posiciones([_agente(1, 0.0, 0.0)])  # una repetida no suma cobertura
    registro.cerrar_generacion(_fila(1, ticks=2), 960, [_agente(1)])
    assert registro.cobertura(registro.calor_gen1) == 1.0


# --- Hitos (decisión 5) ---

def test_un_hito_se_registra_la_primera_vez_y_no_la_segunda():
    registro = _registro()
    assert registro.mirar_hitos([_agente(1), _agente(2)], 1, 10) == []
    nuevos = registro.mirar_hitos([_agente(1), _agente(2, etapa=1)], 1, 11)
    assert nuevos == [{"paso": 1, "generacion": 1, "tick": 11, "agente": 2}]
    # Otro agente llega a la llave roja, en la misma generación y en otra: no es la primera vez
    assert registro.mirar_hitos([_agente(1, etapa=1), _agente(2, etapa=1)], 1, 12) == []
    assert registro.mirar_hitos([_agente(5, etapa=1)], 2, 3) == []
    assert registro.hitos == nuevos


def test_dos_hitos_en_el_mismo_tick_van_en_el_orden_del_puzzle():
    registro = _registro()
    nuevos = registro.mirar_hitos([_agente(1), _agente(7, etapa=2)], 3, 40)
    assert nuevos == [{"paso": 1, "generacion": 3, "tick": 40, "agente": 7},
                      {"paso": 2, "generacion": 3, "tick": 40, "agente": 7}]
    assert registro.mirar_hitos([_agente(8, etapa=3)], 4, 5) == [
        {"paso": 3, "generacion": 4, "tick": 5, "agente": 8}]


# --- Mejor agente (decisión 6) ---

def test_el_mejor_agente_es_el_record_de_la_corrida():
    registro = _registro()
    registro.cerrar_generacion(_fila(1), 960, [_agente(1, fitness=30.0), _agente(2, fitness=40.0)])
    assert (registro.mejor["id"], registro.mejor["generacion"], registro.mejor["fitness"]) == (2, 1, 40.0)
    # Una generación peor no lo cambia; un empate tampoco
    registro.cerrar_generacion(_fila(2), 960, [_agente(3, fitness=35.0)])
    registro.cerrar_generacion(_fila(3), 960, [_agente(4, fitness=40.0)])
    assert registro.mejor["id"] == 2
    # Una que lo supera, sí
    registro.cerrar_generacion(_fila(4), 960, [_agente(5, fitness=40.5, etapa=1)])
    assert registro.mejor == {"id": 5, "generacion": 4, "fitness": 40.5, "manzanas": 2,
                              "recorrido": 300.0, "ticks_vividos": 500, "etapa": 1}


def test_la_historia_guarda_la_fila_tal_cual_y_los_ticks_maximos():
    registro = _registro()
    fila = _fila(1, ticks=700, fitness_prom=21.5, vivos=0)
    registro.cerrar_generacion(fila, 960, [_agente(1)])
    assert registro.historia == [{**fila, "ticks_max": 960}]


# --- Sin azar (decisión 3) ---

def _estado_del_azar():
    return random.getstate(), np.random.get_state()


def _mismo_estado(antes, despues):
    (py_antes, np_antes), (py_despues, np_despues) = antes, despues
    return (py_antes == py_despues and np_antes[0] == np_despues[0]
            and np.array_equal(np_antes[1], np_despues[1]) and np_antes[2:] == np_despues[2:])


def test_contar_mirar_hitos_cerrar_y_armar_el_boletin_no_consumen_azar():
    random.seed(7)
    np.random.seed(7)
    antes = _estado_del_azar()
    registro = _registro()
    agentes = [_agente(i, 16.0 * i, 30.0, etapa=i % 3, fitness=float(i)) for i in range(60)]
    for generacion in (1, 2, 3):
        for tick in range(5):
            registro.contar_posiciones(agentes)
            registro.mirar_hitos(agentes, generacion, tick)
        registro.cerrar_generacion(_fila(generacion, ticks=5, fitness_prom=10.0 + generacion,
                                         agentes_llave_roja=40, agentes_puerta_madera=20), 960, agentes)
    texto_de_consola(armar_boletin(registro))
    assert _mismo_estado(antes, _estado_del_azar())
