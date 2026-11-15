"""
Tests de las reglas que mandan (spec MODO_GUIADO_Y_AUTONOMO, bloque A, decisión 31).

Cada test se corrió una vez contra el código de antes de su cambio y falló: es su control.
Los valores de config.py se pisan en la clase con monkeypatch, que los devuelve al terminar, y
siempre con un número distinto del que estaba fijo en el código: si no, el test pasaría también
con el código viejo.
"""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.analytics.learning_monitor import LearningMonitor  # noqa: E402
from src.world.obstacles import Obstacle  # noqa: E402

# Un tick sin moverse, sin girar, sin comer y sin golpear
QUIETO = {"move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}


def _pisar(monkeypatch, **valores):
    """Pisa valores de SimulationConfig hasta el final del test.

    raising=False: el control corrió contra el código de antes, cuando los valores nuevos todavía
    no existían en config.py.
    """
    for nombre, valor in valores.items():
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)


def _mundo(**cambios):
    """Un mundo vacío, con lo que leen perceive() (también la brújula), decide() y act()."""
    mundo = SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[], pond_obstacles=[],
                            door=None, door_iron=None, red_key=None, gold_key=None, chest=None,
                            screen_width=960, screen_height=800)
    for nombre, valor in cambios.items():
        setattr(mundo, nombre, valor)
    return mundo


def _manzana(x, y):
    return {"x": x, "y": y, "eaten": False}


def test_un_tick_consume_AGENT_ENERGY_CONSUMPTION(monkeypatch):
    _pisar(monkeypatch, AGENT_ENERGY_CONSUMPTION=0.37)
    agente = AdvancedAgent(100, 100)
    antes = agente.energy
    agente.act(dict(QUIETO), _mundo(), [], tick=1)
    assert agente.energy == pytest.approx(antes - 0.37)


def test_comer_suma_AGENT_ENERGY_GAIN_FOOD_sin_pasar_de_AGENT_ENERGY(monkeypatch):
    _pisar(monkeypatch, AGENT_ENERGY=70.0, AGENT_ENERGY_GAIN_FOOD=13)
    agente = AdvancedAgent(100, 100)

    agente.energy = 40.0
    assert agente._try_eat(_mundo(food_items=[_manzana(100, 100)]))
    assert agente.energy == pytest.approx(53.0)

    agente.energy = 65.0
    assert agente._try_eat(_mundo(food_items=[_manzana(100, 100)]))
    assert agente.energy == pytest.approx(70.0)  # el tope es AGENT_ENERGY


def test_se_arranca_y_se_cura_hasta_AGENT_ENERGY(monkeypatch):
    _pisar(monkeypatch, AGENT_ENERGY=70.0)
    agente = AdvancedAgent(100, 100)
    assert agente.energy == pytest.approx(70.0)

    agente.energy = 10.0
    pocion = Obstacle(92, 92, 16, 16, "potion")
    assert agente._try_heal(_mundo(obstacles=[pocion]))
    assert agente.energy == pytest.approx(70.0)


def test_el_agente_usa_AGENT_RADIUS_y_VISION_RANGE(monkeypatch):
    _pisar(monkeypatch, AGENT_RADIUS=11, VISION_RANGE=222)
    agente = AdvancedAgent(100, 100)
    assert agente.radius == 11
    assert agente.vision_range == 222

    # Sensor 2: la distancia a la comida se mide contra VISION_RANGE
    sensores = agente.perceive(_mundo(food_items=[_manzana(200, 100)]), [])
    assert sensores[1] == pytest.approx(100 / 222)


def test_el_agua_resta_WATER_ENERGY_LOSS(monkeypatch):
    _pisar(monkeypatch, WATER_ENERGY_LOSS=0.4)
    agente = AdvancedAgent(100, 100)
    antes = agente.energy
    agua = Obstacle(90, 90, 20, 20, "water")
    agente._check_zone_effects(_mundo(obstacles=[agua]))
    assert agente.energy == pytest.approx(antes - 0.4)


def test_la_recompensa_por_arbol_y_por_casita_sobrevive_a_calculate_fitness(monkeypatch):
    # DIAG-08: se sumaba a self.fitness, y _calculate_fitness() la pisaba
    _pisar(monkeypatch, TREE_CUT_REWARD=7, HUT_CUT_REWARD=4)
    agente = AdvancedAgent(100, 100)  # recién creado: el resto del fitness vale 0
    agente.golpeando = True  # cortar pide golpear (bloque B)

    arbol = SimpleNamespace(process_tree_hit=lambda agente, tick: True,
                            process_hut_hit=lambda agente, tick: False)
    assert agente._try_cut_tree(arbol, 1000)
    agente._calculate_fitness()
    assert agente.fitness == pytest.approx(7)

    casita = SimpleNamespace(process_tree_hit=lambda agente, tick: False,
                             process_hut_hit=lambda agente, tick: True)
    assert agente._try_cut_tree(casita, 2000)
    agente._calculate_fitness()
    assert agente.fitness == pytest.approx(7 + 4)


def test_no_quedan_los_contadores_de_obstaculos():
    # DIAG-09: nunca se incrementaban, así que el término de fitness y la "habilidad" valían 0
    agente = AdvancedAgent(100, 100)
    for nombre in ("obstacles_avoided", "obstacle_avoidance_count", "total_obstacle_encounters",
                   "get_obstacle_skill"):
        assert not hasattr(agente, nombre), nombre
    assert "obstacle_avoiders" not in LearningMonitor()._analyze_behaviors([agente])


def test_el_sensor_de_angulo_queda_en_0_1_despues_de_muchas_vueltas():
    # DIAG-10: el ángulo se acumula sin normalizar, y el sensor salía de [0, 1]
    agente = AdvancedAgent(100, 100)
    for angulo in (7 * 2 * math.pi + 0.3, -3 * 2 * math.pi - 0.3, -0.001, 1000.0):
        agente.angle = angulo
        sensor = agente.perceive(_mundo(), [])[6]
        assert 0.0 <= sensor < 1.0, angulo
    agente.angle = 7 * 2 * math.pi + 0.3
    assert agente.perceive(_mundo(), [])[6] == pytest.approx(0.3 / (2 * math.pi), abs=1e-6)


def test_la_penalizacion_por_agua_se_topea_en_WATER_PENALTY_MAX(monkeypatch):
    # DIAG-11
    _pisar(monkeypatch, WATER_PENALTY_MAX=4)
    agente = AdvancedAgent(100, 100)
    agente.puzzle_rewards = 40.0
    agente.fitness_env_penalty = 25.0  # cinco ticks en el agua
    agente._calculate_fitness()
    assert agente.fitness == pytest.approx(40 - 4)


def test_la_exploracion_extra_es_solo_para_fitness_bajo():
    # DIAG-13: el else colgaba del if de la guía de llaves, así que corría también con fitness 50
    con_50 = AdvancedAgent(100, 100)
    con_50.fitness = 50.0
    con_50.decide(_mundo(), [], None)
    assert getattr(con_50, "exploration_timer", 0) == 0

    con_20 = AdvancedAgent(100, 100)
    con_20.fitness = 20.0
    con_20.decide(_mundo(), [], None)
    assert con_20.exploration_timer == 1


def test_los_agentes_de_la_generacion_1_tienen_ids_1_a_60(monkeypatch):
    # Decisión 24: el id era id(self), que cambia entre dos corridas iguales. Dos _simular seguidos
    # prueban que el contador se reinicia al empezar cada corrida
    _pisar(monkeypatch, HEADLESS_MODE=True, MAX_GENERATIONS=1, BASE_TICKS=3)
    ids_por_corrida = []
    monkeypatch.setattr(main, "mostrar_pantalla_final",
                        lambda _superficie, _generacion, _tick, agentes, *resto, **claves:
                        ids_por_corrida.append([agente.id for agente in agentes]))
    for _ in range(2):
        main._simular(7, True, lambda fila: None)
    assert ids_por_corrida == [list(range(1, 61))] * 2
