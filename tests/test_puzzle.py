"""
Tests del puzzle por agente (spec MODO_GUIADO_Y_AUTONOMO, bloque B, decisión 31).

Cada test se corrió una vez contra el código de antes del bloque B y falló: es su control. Usan un
mundo real, con semilla fija, y ponen a los agentes donde haga falta; el de la puerta que frena a
uno y no a otro usa un mundo de mentira con una puerta sola, para que nada más del mapa estorbe.
"""

import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.evolution.genetic_algorithm import GeneticAlgorithm  # noqa: E402
from src.world.world import World  # noqa: E402

# Un tick sin moverse, sin girar, sin comer y sin golpear; y uno igual, pero golpeando
QUIETO = {"move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}
GOLPE = dict(QUIETO, hit=1.0)

# Lejos de cualquier cooldown: el del agente es de 120 ticks y arranca en 0
TICK_INICIAL = 1000


@pytest.fixture
def mundo():
    random.seed(11)
    np.random.seed(11)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT,
                 SimulationConfig.FOOD_COUNT)


def _centro(objeto):
    """Centro de una puerta o del cofre: desde ahí se miden el golpe y el contacto."""
    return objeto.x + objeto.width // 2, objeto.y + objeto.height // 2


def _agente_en(x, y, etapa=0):
    agente = AdvancedAgent(x, y)
    agente.etapa = etapa
    return agente


def _tick(agente, mundo, tick, golpea=True):
    """Un tick de act(), golpeando o no; lo que se golpea lo prueba cada test con su _try_*."""
    agente.act(dict(GOLPE if golpea else QUIETO), mundo, [], tick)


def _golpear_puerta(agente, mundo, veces, tick=TICK_INICIAL):
    """Golpea la puerta `veces` veces, con DOOR_HIT_COOLDOWN entre golpes. True si la abrió."""
    abrio = False
    for _ in range(veces):
        _tick(agente, mundo, tick)
        abrio = agente._try_hit_door(mundo, tick) or abrio
        tick += SimulationConfig.DOOR_HIT_COOLDOWN
    return abrio


def test_la_puerta_que_abre_un_agente_sigue_siendo_pared_para_otro(mundo):
    x, y = _centro(mundo.door)
    a = _agente_en(x, y + 15, etapa=1)  # con la llave roja, a menos de 25 px del centro
    assert _golpear_puerta(a, mundo, SimulationConfig.DOOR_HITS_TO_OPEN)
    assert a.etapa == 2
    assert mundo.door.is_open  # se dibuja abierta: alguien la abrió

    # Una puerta sola, con el estado que dejó A. B también tiene la llave roja, pero no la abrió
    puerta = mundo.door
    solo_la_puerta = SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[],
                                     pond_obstacles=[], door=puerta, door_iron=None, red_key=None,
                                     gold_key=None, chest=None, screen_width=960, screen_height=800)
    caminar = dict(QUIETO, move_forward=1.0)
    b = _agente_en(x, y + 18, etapa=1)
    for agente in (a, b):
        agente.x, agente.y, agente.angle = float(x), float(y + 18), -math.pi / 2  # mirando a la puerta
    a.act(dict(caminar), solo_la_puerta, [], TICK_INICIAL)
    b.act(dict(caminar), solo_la_puerta, [], TICK_INICIAL)
    assert a.y < y + 18  # A pasa
    assert b.y == y + 18  # B choca


def test_sin_golpear_o_sin_llave_roja_no_hay_golpe(mundo):
    # Para el control: el mundo de antes abría la puerta por cercanía si alguien tenía la llave
    mundo.red_key_collected = True
    x, y = _centro(mundo.door)
    sin_golpear = _agente_en(x, y + 15, etapa=1)
    sin_llave = _agente_en(x, y + 15, etapa=0)
    tick = TICK_INICIAL
    for _ in range(SimulationConfig.DOOR_HITS_TO_OPEN + 2):
        _tick(sin_golpear, mundo, tick, golpea=False)
        assert not sin_golpear._try_hit_door(mundo, tick)
        _tick(sin_llave, mundo, tick)
        assert not sin_llave._try_hit_door(mundo, tick)
        tick += SimulationConfig.DOOR_HIT_COOLDOWN
    assert (sin_golpear.etapa, sin_llave.etapa) == (1, 0)
    assert not mundo.door.is_open


def test_el_cofre_pide_etapa_4_y_golpear_y_la_llave_dorada_etapa_2(mundo):
    cx, cy = _centro(mundo.chest)
    sin_golpear = _agente_en(cx, cy, etapa=4)
    _tick(sin_golpear, mundo, TICK_INICIAL, golpea=False)
    assert not sin_golpear._try_open_chest(mundo)
    for etapa in (0, 3):
        agente = _agente_en(cx, cy, etapa)
        _tick(agente, mundo, TICK_INICIAL)
        assert not agente._try_open_chest(mundo)
    assert not mundo.chest.is_open
    con_todo = _agente_en(cx, cy, etapa=4)
    _tick(con_todo, mundo, TICK_INICIAL)
    assert con_todo._try_open_chest(mundo)
    assert con_todo.etapa == 5

    llave = mundo.gold_key
    for etapa in (0, 1, 3):
        agente = _agente_en(llave.x, llave.y, etapa)
        assert not agente._try_pickup_key(mundo)
        assert agente.etapa == etapa
    agente = _agente_en(llave.x, llave.y, etapa=2)
    assert agente._try_pickup_key(mundo)
    assert agente.etapa == 3


def test_la_recompensa_es_para_quien_dio_el_paso(mundo):
    # B no tiene la llave y golpea la puerta: no abre nada ni cobra. Antes la abría porque otro la
    # había recogido
    llave = mundo.red_key
    a = _agente_en(llave.x, llave.y)
    assert a._try_pickup_key(mundo)
    assert (a.etapa, a.puzzle_rewards) == (1, SimulationConfig.RED_KEY_REWARD)

    x, y = _centro(mundo.door)
    b = _agente_en(x, y + 15)
    assert not _golpear_puerta(b, mundo, SimulationConfig.DOOR_HITS_TO_OPEN)
    assert b.puzzle_rewards == 0

    a.x, a.y = float(x), float(y + 15)
    assert _golpear_puerta(a, mundo, SimulationConfig.DOOR_HITS_TO_OPEN)
    assert a.puzzle_rewards == SimulationConfig.RED_KEY_REWARD + SimulationConfig.DOOR_OPEN_REWARD

    # La llave queda en el mapa: otro agente también la recoge, y cobra él
    c = _agente_en(llave.x, llave.y)
    assert c._try_pickup_key(mundo)
    assert (c.etapa, c.puzzle_rewards) == (1, SimulationConfig.RED_KEY_REWARD)


def test_golpear_gasta_HIT_ENERGY_COST_golpee_algo_o_no(monkeypatch):
    monkeypatch.setattr(SimulationConfig, "HIT_ENERGY_COST", 0.3, raising=False)
    vacio = SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[], pond_obstacles=[],
                            door=None, door_iron=None, screen_width=960, screen_height=800)
    quieto, golpea = AdvancedAgent(100, 100), AdvancedAgent(100, 100)
    quieto.act(dict(QUIETO), vacio, [], 1)
    golpea.act(dict(GOLPE), vacio, [], 1)
    assert quieto.energy - golpea.energy == pytest.approx(0.3)


def test_la_brujula_apunta_al_paso_de_cada_etapa(mundo):
    pasos = {0: (mundo.red_key.x, mundo.red_key.y), 1: _centro(mundo.door),
             2: (mundo.gold_key.x, mundo.gold_key.y), 3: _centro(mundo.door_iron),
             4: _centro(mundo.chest)}
    for etapa, (px, py) in pasos.items():
        agente = _agente_en(px + 30, py + 40, etapa)  # a 50 px del paso
        agente.angle = 0.0
        sensores = agente.perceive(mundo, [])
        assert len(sensores) == 11
        assert sensores[7] == pytest.approx(etapa / 5)
        assert sensores[8] == pytest.approx(math.atan2(-40, -30) / math.pi, abs=1e-5)
        assert sensores[10] == pytest.approx(50 / SimulationConfig.VISION_RANGE, abs=1e-5)

    sensores = _agente_en(400, 400, etapa=5).perceive(mundo, [])
    assert (sensores[7], sensores[8], sensores[10]) == (1.0, 0.0, 1.0)


def test_un_agente_nuevo_arranca_en_etapa_0_y_sin_hacha():
    ga = GeneticAlgorithm(**SimulationConfig.get_genetic_params())
    padres = ga._create_random_population()
    for padre in padres:
        padre.etapa, padre.tiene_hacha = 5, True
    hijos = ga.evolve(padres, generation=1)  # con élite: también ella arranca de cero
    assert all((hijo.etapa, hijo.tiene_hacha) == (0, False) for hijo in hijos)


def test_el_hacha_de_un_agente_no_habilita_a_otro_a_cortar(mundo):
    con_hacha = _agente_en(mundo.axe['x'], mundo.axe['y'])
    assert con_hacha._try_pickup_axe(mundo)

    # Poca comida: los árboles se pueden cortar
    for manzana in mundo.food_items:
        manzana['eaten'] = True
    mundo.update_tree_cutting_status()
    arbol = mundo.trees[0]

    sin_hacha = _agente_en(arbol.x, arbol.y)
    tick = TICK_INICIAL
    for _ in range(4):  # más golpes de los que hacen falta, con los cooldowns cumplidos
        _tick(sin_hacha, mundo, tick)
        assert not sin_hacha._try_cut_tree(mundo, tick)
        tick += 200
    assert all(t.hit_count == 0 for t in mundo.trees)

    con_hacha.x, con_hacha.y = float(arbol.x), float(arbol.y)
    corto = False
    for _ in range(4):
        _tick(con_hacha, mundo, tick)
        corto = con_hacha._try_cut_tree(mundo, tick) or corto
        tick += 200
    assert corto
    assert con_hacha.tiene_hacha and not sin_hacha.tiene_hacha


def test_reset_food_reinicia_el_puzzle_y_sortea_llave_roja_y_hacha(mundo):
    mundo.door.is_open = mundo.door_iron.is_open = mundo.chest.is_open = True
    llave_antes = (mundo.red_key.x, mundo.red_key.y)
    hacha_antes = (mundo.axe['x'], mundo.axe['y'])
    dorada_antes = (mundo.gold_key.x, mundo.gold_key.y)
    mundo.reset_food(2)
    assert not (mundo.door.is_open or mundo.door_iron.is_open or mundo.chest.is_open)
    assert (mundo.red_key.x, mundo.red_key.y) != llave_antes
    assert (mundo.axe['x'], mundo.axe['y']) != hacha_antes
    assert (mundo.gold_key.x, mundo.gold_key.y) == dorada_antes


def test_abrir_el_cofre_no_termina_la_corrida(monkeypatch):
    # Decisión 11: antes, el primer cofre cortaba la corrida con una fila parcial. El primer intento
    # de abrirlo lo abre; los demás, no
    import main  # noqa: E402
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 2), ("BASE_TICKS", 5)):
        monkeypatch.setattr(SimulationConfig, nombre, valor)
    aperturas = iter([True])
    monkeypatch.setattr(AdvancedAgent, "_try_open_chest", lambda self, world: next(aperturas, False))
    finales = []
    monkeypatch.setattr(main, "mostrar_pantalla_final",
                        lambda *args, **kwargs: finales.append(args[-2:]))
    filas = []
    main._simular(7, True, filas.append)
    assert [(fila[2], fila[3]) for fila in filas] == [(1, 5), (2, 5)]  # generación, ticks completos
    assert finales == [(1, 1)]  # primera generación con cofre, y agentes que lo abrieron


def test_ningun_agente_arranca_sobre_la_llave_roja_ni_el_hacha(mundo):
    # Desvío de la decisión 23, decidido con Fer: arrancar encima daba la llave o el hacha gratis.
    # Diez generaciones: con la ubicación de antes, en alguna arranca alguien encima
    import main  # noqa: E402 (main importa pygame y todo el resto: solo lo usa este test)
    ga = GeneticAlgorithm(**SimulationConfig.get_genetic_params())
    for generacion in range(2, 12):
        agentes = ga._create_random_population()
        main._ubicar_agentes(mundo, agentes)
        for premio in ((mundo.red_key.x, mundo.red_key.y), (mundo.axe['x'], mundo.axe['y'])):
            cerca = [a.id for a in agentes if math.dist((a.x, a.y), premio) < main.RADIO_LIBRE]
            assert not cerca, (generacion, premio, cerca)
        mundo.reset_food(generacion)


def test_la_guia_apunta_al_paso_del_agente_y_aprieta_golpear(monkeypatch, mundo):
    # Decisión 6. random.random() en 0,1: las ramas del puzzle (40%) corren y el rumbo al azar (2%) no
    monkeypatch.setattr(random, "random", lambda: 0.1)
    x, y = _centro(mundo.door)
    con_llave = _agente_en(x, y + 60, etapa=1)
    con_llave.fitness, con_llave.angle = 80.0, -math.pi / 2  # alineado con la puerta, su paso
    assert con_llave.decide(mundo, [], None)['hit'] == pytest.approx(0.9)

    # Mismo lugar y rumbo, sin la llave: su paso es la llave roja, y la guía no golpea la puerta
    sin_llave = _agente_en(x, y + 60, etapa=0)
    sin_llave.fitness, sin_llave.angle = 80.0, -math.pi / 2
    sin_llave.brain = con_llave.brain
    assert sin_llave.decide(mundo, [], None)['hit'] != pytest.approx(0.9)

    # Rama de árboles: hace falta el hacha propia
    for manzana in mundo.food_items:
        manzana['eaten'] = True
    mundo.update_tree_cutting_status()
    arbol = mundo.trees[0]
    ax, ay = arbol.x - 60, arbol.y
    cercano = min(mundo.trees, key=lambda t: (t.x - ax) ** 2 + (t.y - ay) ** 2)
    for tiene_hacha, golpea in ((True, True), (False, False)):
        agente = _agente_en(ax, ay, etapa=5)
        agente.fitness, agente.tiene_hacha = 40.0, tiene_hacha
        agente.angle = math.atan2(cercano.y - ay, cercano.x - ax)  # alineado con el árbol más cercano
        agente.brain = con_llave.brain
        hit = agente.decide(mundo, [], None)['hit']
        assert (hit == pytest.approx(0.9)) is golpea, tiene_hacha
