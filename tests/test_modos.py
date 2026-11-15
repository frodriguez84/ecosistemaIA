"""
Tests del switch entre el modo guiado y el autónomo (spec MODO_GUIADO_Y_AUTONOMO, bloque C,
decisión 31).

Cada test se corrió una vez contra el código de antes del bloque C y falló: es su control. El modo
se pisa en la clase, como lo hace main.py, y monkeypatch lo devuelve al terminar. El caso del guiado
que pide la decisión 31 (alineado con su puerta, aprieta golpear) está en test_puzzle.py.
"""

import math
import random
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.world.world import World  # noqa: E402

# Un tick sin moverse, sin girar, sin comer y sin golpear
QUIETO = {"move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}

# Los casos en que la guía del modo guiado hace algo: fitness bajo (el temporizador de exploración),
# medio (la comida) y alto (la comida y el puzzle), con el próximo paso en una llave y en una puerta
CASOS = [(20.0, 0), (50.0, 0), (80.0, 0), (80.0, 1)]


@pytest.fixture
def mundo():
    random.seed(11)
    np.random.seed(11)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT,
                 SimulationConfig.FOOD_COUNT)


def _modo(monkeypatch, modo):
    # raising=False: el control corrió contra el código de antes, cuando MODO no existía
    monkeypatch.setattr(SimulationConfig, "MODO", modo, raising=False)


def _agentes(mundo):
    """Un agente por caso, a 60 px de la puerta de madera y mirándola, con el temporizador de
    exploración a punto de girar."""
    puerta = mundo.door
    x, y = puerta.x + puerta.width // 2, puerta.y + puerta.height // 2 + 60
    agentes = []
    for fitness, etapa in CASOS:
        agente = AdvancedAgent(x, y)
        agente.fitness, agente.etapa, agente.angle = fitness, etapa, -math.pi / 2
        agente.exploration_timer = 100
        agentes.append(agente)
    return agentes


def _mismo_estado_np(a, b):
    """np.random.get_state() trae un array: se compara pieza por pieza."""
    return a[0] == b[0] and np.array_equal(a[1], b[1]) and a[2:] == b[2:]


def test_en_autonomo_decide_es_la_salida_de_la_red_recortada(monkeypatch, mundo):
    # Decisión 5. En guiado, cada uno de estos agentes recibe algo de la guía (decisión 3)
    _modo(monkeypatch, "autonomo")
    for agente in _agentes(mundo):
        salida = agente.brain.forward(agente.perceive(mundo, []))
        esperado = {accion: min(1.0, max(0.0, valor)) for accion, valor in salida.items()}
        angulo = agente.angle
        assert agente.decide(mundo, [], None) == esperado, (agente.fitness, agente.etapa)
        # Ni el rumbo al azar del 2% ni el temporizador de exploración tocan el rumbo
        assert agente.angle == angulo, (agente.fitness, agente.etapa)


def test_en_autonomo_decide_y_act_no_consumen_azar(monkeypatch, mundo):
    # Decisión 5: 50 ticks completos de cuatro agentes, sin tocar random ni np.random
    _modo(monkeypatch, "autonomo")
    agentes = _agentes(mundo)
    estado_random, estado_np = random.getstate(), np.random.get_state()
    for tick in range(1000, 1050):
        for agente in agentes:
            agente.act(agente.decide(mundo, agentes, None), mundo, agentes, tick)
    assert random.getstate() == estado_random
    assert _mismo_estado_np(np.random.get_state(), estado_np)


def test_en_autonomo_act_gira_sin_reflejo_ni_ruido(monkeypatch, mundo):
    # Decisión 3: el reflejo que anula los giros y el ruido al girar son guía. Lo común (decisión 4):
    # giro × 0,12, reducido × 0,6 si pasa de 0,08
    def girar(modo):
        _modo(monkeypatch, modo)
        agente = AdvancedAgent(400, 400)
        agente.recent_angles.extend(i * 0.5 for i in range(20))  # venía girando sin parar
        angulo = agente.angle
        agente.act(dict(QUIETO, turn_right=1.0), mundo, [], tick=1)
        return agente.angle - angulo

    assert girar("autonomo") == pytest.approx(0.12 * 0.6)
    # En guiado, el reflejo deja el giro en la quinta parte (0,024, que no pasa de 0,08: sin ruido)
    assert girar("guiado") == pytest.approx(0.12 * 0.2)


def test_el_modo_por_defecto_es_guiado_y_el_flag_lo_pisa(capsys):
    # Decisión 1: sin flags, el guiado; --modo lo pisa, y --help lo lista en español
    assert SimulationConfig.MODO == "guiado"
    assert main._leer_argumentos([]).modo is None
    assert main._leer_argumentos(["--modo", "autonomo"]).modo == "autonomo"
    with pytest.raises(SystemExit):
        main._leer_argumentos(["--modo", "otro"])
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main._leer_argumentos(["--help"])
    ayuda = capsys.readouterr().out
    assert "--modo" in ayuda and "guiado" in ayuda and "autonomo" in ayuda
