"""
Tests de la recompensa por acercarse por el camino (ACERCARSE_CAMINO, --acercarse-camino; spec PUZZLE_SOLOS,
sección "La recompensa por acercarse, por el camino", decidida por Fer con la medición de la brújula por el camino,
docs/qa/AnalisisQA.md#brujula-camino).

Prendida, con la recompensa por acercarse, _medir_acercamiento mide la distancia por el camino libre (la del sensor
11 de la brújula por el camino), no la recta. camino.distancia tiene que dar lo mismo que la distancia de
camino.rumbo y no consumir azar. No pide la brújula por el camino: lee la misma grilla. Apagada, nada cambia (el CSV
de main._simular, con los valores por defecto, lo controla test_fortalezas_moviles.py,
test_apagado_el_csv_es_el_de_antes_del_switch).
"""

import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402 (main importa pygame y todo el resto)
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.analytics.boletin import armar_boletin  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402
from src.world import camino  # noqa: E402
from src.world.world import World  # noqa: E402

COLUMNAS_DEL_FITNESS = ("fitness_prom", "fitness_max", "fitness_min", "fitness_desvio")


def _mundo(monkeypatch, semilla, generaciones=1, moviles=False):
    """Un mundo de verdad. Con generaciones > 1, el de esa generación (reset_food)."""
    monkeypatch.setattr(SimulationConfig, "FORTALEZAS_MOVILES", moviles, raising=False)
    random.seed(semilla)
    np.random.seed(semilla)
    mundo = World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT, SimulationConfig.FOOD_COUNT)
    for generacion in range(2, generaciones + 1):
        mundo.reset_food(generacion)
    return mundo


def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.ACERCARSE_CAMINO is False
    for modulo in (main, experimento):
        assert modulo._leer_argumentos(["--acercarse"]).acercarse_camino is False
        assert modulo._leer_argumentos(["--acercarse", "--acercarse-camino"]).acercarse_camino is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--acercarse-camino"])  # sin la recompensa por acercarse no hace nada
        assert "va con --acercarse" in capsys.readouterr().err, modulo.__name__
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--acercarse-camino" in capsys.readouterr().out, modulo.__name__


# --- La distancia ---

def test_la_distancia_es_la_de_rumbo(monkeypatch):
    # Un mapa con las fortalezas movidas y un árbol talado después de armar la grilla (que no lo ve: ahí no hay celda
    # libre cerca y va la recta), con puntos al azar de un generador propio y los de cerca de las puertas y del árbol
    mundo = _mundo(monkeypatch, 3, generaciones=4, moviles=True)
    campos = camino.campos(mundo)
    arbol = next(o for o in mundo.obstacles if o.type == "tree")
    arbol.is_cut = True
    generador = np.random.default_rng(0)
    xs = list(generador.uniform(6, mundo.screen_width - 6, 2000))
    ys = list(generador.uniform(6, mundo.screen_height - 6, 2000))
    for o in (mundo.door, mundo.door_iron, arbol):
        for dx in range(-30, 31, 3):
            for dy in range(-30, 31, 3):
                xs.append(o.x + o.width / 2 + dx + 0.37)
                ys.append(o.y + o.height / 2 + dy + 0.61)
    for etapa in camino.ETAPAS:
        esperadas = camino.rumbo(mundo, etapa, np.array(xs), np.array(ys))[1]
        distintas = [(x, y) for x, y, d in zip(xs, ys, esperadas) if camino.distancia(mundo, etapa, x, y) != float(d)]
        assert distintas == [], (etapa, distintas[:5])
        # Los dos casos: la recta (el objetivo, sin camino o sin celda libre cerca) y la celda
        recta = [bool(campos[etapa].recta[int(y // camino.CELDA), int(x // camino.CELDA)]) for x, y in zip(xs, ys)]
        assert 0 < sum(recta) < len(recta), etapa


def test_leer_la_distancia_no_consume_azar(monkeypatch):
    mundo = _mundo(monkeypatch, 4)
    agente = AdvancedAgent(300, 300)  # crear el agente sí consume azar (los pesos de la red)
    agente.x, agente.y, agente.etapa = 300.0, 300.0, 3
    monkeypatch.setattr(SimulationConfig, "ACERCARSE_CAMINO", True)
    random.seed(11)
    np.random.seed(11)
    antes = (random.getstate(), np.random.get_state()[1].copy())
    camino.distancia(mundo, 1, 400.0, 500.0)
    agente._medir_acercamiento(mundo)
    assert random.getstate() == antes[0]
    assert (np.random.get_state()[1] == antes[1]).all()


# --- El avance ---

def _avances(monkeypatch, mundo, por_el_camino, puntos):
    """El avance en el paso de un agente con la llave dorada (etapa 3) que pasa por esos puntos, uno por tick."""
    monkeypatch.setattr(SimulationConfig, "ACERCARSE_CAMINO", por_el_camino)
    agente = AdvancedAgent(0, 0)
    agente.etapa = 3
    avances = []
    for x, y in puntos:
        agente.x, agente.y = x, y
        agente._medir_acercamiento(mundo)
        avances.append(agente._avance_en_el_paso())
    return avances


def test_desde_donde_se_traba_la_recta_salir_por_la_puerta_de_madera_sube_el_avance(monkeypatch):
    # Generación 1 de la semilla 5: la llave dorada en (110, 90), adentro de la fortaleza chica, y la puerta de madera
    # con centro en (100, 140). Con la llave dorada, el seguidor de la recta a la puerta de hierro queda en el rincón
    # (122, 123), y de ahí a la puerta de madera se aleja en línea recta. Con la brújula recta (BRUJULA_CAMINO apagada):
    # acercarse por el camino no la pide
    assert SimulationConfig.BRUJULA_CAMINO is False
    mundo = _mundo(monkeypatch, 5)
    assert (mundo.gold_key.x, mundo.gold_key.y) == (110, 90)
    assert camino.punto_del_paso(mundo, 1) == (100, 140)
    puntos = [(110.0, 90.0), (122.0, 123.0), (100.0, 140.0)]
    recta = _avances(monkeypatch, mundo, False, puntos)
    por_el_camino = _avances(monkeypatch, mundo, True, puntos)
    assert recta[0] == por_el_camino[0] == 0
    assert recta[2] == recta[1] > 0  # en la puerta, lo mismo que en el rincón
    assert por_el_camino[2] > por_el_camino[1] > 0


# --- La corrida, la ruta, el panel, el boletín y el experimento ---

def _correr_adentro(monkeypatch, capsys, por_el_camino):
    """La simulación de main.py, sin ventana, con la recompensa por acercarse, 2 generaciones de 60 ticks,
    autónomo. Devuelve las filas del CSV."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 2), ("BASE_TICKS", 60),
                          ("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", True),
                          ("ACERCARSE_CAMINO", por_el_camino)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, True, filas.append)
    capsys.readouterr()
    return filas


def test_prendido_en_la_generacion_1_cambia_solo_el_fitness(monkeypatch, capsys):
    recta = _correr_adentro(monkeypatch, capsys, False)
    por_el_camino = _correr_adentro(monkeypatch, capsys, True)
    distintas = {columna for columna, a, b in zip(main.COLUMNAS_CSV, recta[0], por_el_camino[0]) if a != b}
    assert distintas and distintas <= set(COLUMNAS_DEL_FITNESS), distintas
    assert _correr_adentro(monkeypatch, capsys, True) == por_el_camino
    assert "acercarse_camino" not in main.COLUMNAS_CSV


def test_la_ruta_el_panel_y_el_boletin_nombran_acercarse_por_el_camino(monkeypatch):
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", True), ("CURRICULO", True),
                          ("DESLIZAR", False), ("FORTALEZAS_MOVILES", False), ("BRUJULA_CAMINO", False),
                          ("ACERCARSE_CAMINO", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_camino_curriculo_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert datos["Ayudas"] == "acercarse por el camino + currículo"

    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=20.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", acercarse=1, generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    assert armar_boletin(registro)["subtitulo"].startswith("Modo autónomo + acercarse por el camino · con evolución")

    monkeypatch.setattr(SimulationConfig, "ACERCARSE_CAMINO", False)
    assert main._ruta_csv_por_defecto(3, True) == str(Path("results") / "corrida_s3_autonomo_acercarse_curriculo_evolucion.csv")
    assert dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))["Ayudas"] == "acercarse + currículo"
    assert armar_boletin(registro)["subtitulo"].startswith("Modo autónomo + acercarse · con evolución")

    # Sin la recompensa por acercarse no hace nada, y no se nombra
    monkeypatch.setattr(SimulationConfig, "ACERCARSE_CAMINO", True)
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False)
    assert main._ruta_csv_por_defecto(3, True) == str(Path("results") / "corrida_s3_autonomo_curriculo_evolucion.csv")
    assert dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))["Ayudas"] == "currículo"


def test_experimento_pasa_el_flag_y_lo_nombra(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    comandos = []

    def correr(comando, **_):
        comandos.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(experimento.subprocess, "run", correr)
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, acercarse=True, curriculo=True,
                                    brujula=True, acercarse_camino=True)
    assert "--acercarse-camino" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_acercarse_camino_curriculo_brujula_camino_evolucion.csv"
    experimento._correr(1, "autonomo", False, 10, tmp_path, acercarse=True)
    assert "--acercarse-camino" not in comandos[1]
    # El resumen lo nombra: test_resumen.py, test_el_resumen_dice_las_ayudas_prendidas
