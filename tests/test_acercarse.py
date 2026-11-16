"""
Tests de la recompensa por acercarse (spec PUZZLE_APRENDIBLE, bloque A, decisiones 4 a 7 y 16).

Cada test se corrió una vez contra el código de antes del bloque A y falló: es su control (cuáles
fallaron por AttributeError, en la bitácora del spec). El término se mide como la diferencia entre
el fitness del mismo agente con el switch prendido y apagado: así se prueba también que
_calculate_fitness lo suma. Los agentes tienen 4 manzanas, para que ningún tope del fitness (0 a
100, y el del tiempo vivido) recorte esa diferencia. Un recorrido pone al agente en cada punto y le
da un tick quieto: el punto es su posición después de moverse en ese tick.
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
from src.world.world import World  # noqa: E402

# Un tick sin moverse, sin girar, sin comer y sin golpear; uno igual pero golpeando; y uno caminando
QUIETO = {"move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}
GOLPE = dict(QUIETO, hit=1.0)
CAMINAR = dict(QUIETO, move_forward=1.0)

TICK_INICIAL = 1000  # Lejos de cualquier cooldown: el del agente es de 120 ticks y arranca en 0
MANZANAS = 4
LLAVE = (400.0, 300.0)  # La llave roja del mundo de mentira


@pytest.fixture
def prendido(monkeypatch):
    # raising=False: el control corrió contra el código de antes, cuando el switch no existía
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True, raising=False)


@pytest.fixture
def mundo():
    random.seed(11)
    np.random.seed(11)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT,
                 SimulationConfig.FOOD_COUNT)


def _solo_la_llave():
    """Un mundo de mentira con la llave roja sola: nada del mapa estorba al caminar ni resta."""
    return SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[], pond_obstacles=[],
                           red_key=SimpleNamespace(x=LLAVE[0], y=LLAVE[1]), door=None,
                           door_iron=None, gold_key=None, chest=None, screen_width=960,
                           screen_height=800)


def _a_la_llave(*distancias):
    """Puntos a esas distancias de la llave del mundo de mentira, a su derecha."""
    return [(LLAVE[0] + d, LLAVE[1]) for d in distancias]


def _centro(objeto):
    """Centro de una puerta: desde ahí se miden el golpe y la brújula."""
    return objeto.x + objeto.width // 2, objeto.y + objeto.height // 2


def _agente(x, y, etapa=0):
    agente = AdvancedAgent(x, y)
    agente.etapa = etapa
    agente.food_eaten = MANZANAS
    return agente


def _recorrer(agente, mundo, puntos, tick=TICK_INICIAL):
    """Un tick quieto en cada punto. Devuelve el tick siguiente."""
    for x, y in puntos:
        agente.x, agente.y = float(x), float(y)
        agente.act(dict(QUIETO), mundo, [], tick)
        tick += 1
    return tick


def _golpe(agente, mundo, tick):
    """Un tick golpeando, y la puerta que le toca. True si la abrió."""
    agente.act(dict(GOLPE), mundo, [], tick)
    return agente._try_hit_door(mundo, tick)


def _termino(monkeypatch, agente):
    """El término del fitness: el fitness con el switch prendido menos el de apagado. Lo deja prendido."""
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False, raising=False)
    apagado = agente._calculate_fitness()
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True, raising=False)
    return agente._calculate_fitness() - apagado


def test_de_200_a_50_px_de_la_llave_suma_tres_cuartos(monkeypatch, prendido):
    # Decisión 4: camino hecho = (d0 − dmín) / d0 = (200 − 50) / 200
    agente = _agente(*_a_la_llave(200)[0])
    _recorrer(agente, _solo_la_llave(), _a_la_llave(200, 150, 100, 50))
    assert _termino(monkeypatch, agente) == pytest.approx(SimulationConfig.FITNESS_ACERCARSE * 0.75)


def test_dar_vueltas_no_suma_y_alejarse_no_resta(monkeypatch, prendido):
    # Decisión 6: cuenta lo más cerca que llegó, no los ticks que pasó cerca
    mundo = _solo_la_llave()
    una_vez = _agente(*_a_la_llave(200)[0])
    _recorrer(una_vez, mundo, _a_la_llave(200, 50))
    esperado = _termino(monkeypatch, una_vez)
    assert esperado == pytest.approx(SimulationConfig.FITNESS_ACERCARSE * 0.75)

    quieto_cerca = _agente(*_a_la_llave(200)[0])
    _recorrer(quieto_cerca, mundo, _a_la_llave(200) + _a_la_llave(50) * 300)
    en_circulos = _agente(*_a_la_llave(200)[0])
    vueltas = [(LLAVE[0] + 50 * math.cos(a), LLAVE[1] + 50 * math.sin(a))
               for a in np.linspace(0, 6 * math.pi, 300)]
    _recorrer(en_circulos, mundo, _a_la_llave(200) + vueltas)
    for agente in (quieto_cerca, en_circulos):
        assert _termino(monkeypatch, agente) == pytest.approx(esperado)

    # Después se aleja, más lejos que donde empezó (por ejemplo, para comer)
    _recorrer(una_vez, mundo, _a_la_llave(100, 300, 500), tick=TICK_INICIAL + 10)
    assert _termino(monkeypatch, una_vez) == pytest.approx(esperado)


def test_en_la_puerta_el_avance_suma_los_golpes_que_contaron(monkeypatch, prendido, mundo):
    # Decisión 4: (camino hecho + golpes que contaron / necesarios) / 2, más el paso que ya dio
    x, y = _centro(mundo.door)
    agente = _agente(x, y + 200, etapa=1)  # con la llave roja
    tick = _recorrer(agente, mundo, [(x, y + 200), (x, y + 100)])
    assert not _golpe(agente, mundo, tick)  # a 100 px: no cuenta
    agente.x, agente.y = float(x), float(y + 15)
    assert not _golpe(agente, mundo, tick + 1)  # a 15 px, con la llave: cuenta
    assert not _golpe(agente, mundo, tick + 2)  # en el cooldown de la puerta: no cuenta
    assert agente.golpes_puerta["door"][0] == 1

    camino = (200 - 15) / 200
    avance = (camino + 1 / SimulationConfig.DOOR_HITS_TO_OPEN) / 2
    assert _termino(monkeypatch, agente) == pytest.approx(SimulationConfig.FITNESS_ACERCARSE * (1 + avance))


def test_agarrar_la_llave_no_baja_el_termino_y_suma_su_premio_mas_el_paso(monkeypatch, prendido, mundo):
    # Decisión 5: dar un paso vale su premio de hoy más FITNESS_ACERCARSE, y el término no baja
    llave = mundo.red_key
    agente = _agente(llave.x + 200, llave.y)
    _recorrer(agente, mundo, [(llave.x + 200, llave.y), (llave.x + 100, llave.y), (llave.x + 5, llave.y)])
    antes = _termino(monkeypatch, agente)
    assert antes == pytest.approx(SimulationConfig.FITNESS_ACERCARSE * 195 / 200)
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False)
    de_hoy_sin_la_llave = agente._calculate_fitness()
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True)

    assert agente._try_pickup_key(mundo)
    despues = _termino(monkeypatch, agente)
    assert despues >= antes
    assert despues == pytest.approx(SimulationConfig.FITNESS_ACERCARSE)  # un paso dado, avance 0
    assert agente._calculate_fitness() - de_hoy_sin_la_llave == pytest.approx(
        SimulationConfig.RED_KEY_REWARD + SimulationConfig.FITNESS_ACERCARSE)

    # En el tick siguiente empieza el paso de la puerta, con d0 medido ahí: tampoco baja
    _recorrer(agente, mundo, [(llave.x + 5, llave.y)], tick=TICK_INICIAL + 10)
    assert _termino(monkeypatch, agente) == pytest.approx(SimulationConfig.FITNESS_ACERCARSE)


def test_con_otro_FITNESS_ACERCARSE_el_termino_cambia(monkeypatch, prendido):
    # config.py manda: un valor distinto del de hoy (10)
    monkeypatch.setattr(SimulationConfig, "FITNESS_ACERCARSE", 20.0, raising=False)
    agente = _agente(*_a_la_llave(200)[0])
    _recorrer(agente, _solo_la_llave(), _a_la_llave(200, 50))
    assert _termino(monkeypatch, agente) == pytest.approx(20.0 * 0.75)


def test_apagado_por_defecto_y_sin_termino():
    # Decisión 2: apagado, acercarse a la llave no cambia el fitness
    assert SimulationConfig.RECOMPENSA_ACERCARSE is False
    assert SimulationConfig.FITNESS_ACERCARSE == 10
    mundo = _solo_la_llave()
    acercado, quieto = _agente(*_a_la_llave(200)[0]), _agente(*_a_la_llave(200)[0])
    _recorrer(acercado, mundo, _a_la_llave(200, 150, 100, 50))
    _recorrer(quieto, mundo, _a_la_llave(200, 200, 200, 200))
    assert acercado._calculate_fitness() == quieto._calculate_fitness()


def test_los_flags_prenden_el_switch_y_estan_en_la_ayuda(capsys):
    import experimento  # noqa: E402
    import main  # noqa: E402 (main importa pygame y todo el resto: solo lo usan estos tests)
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).acercarse is False
        assert modulo._leer_argumentos(["--acercarse"]).acercarse is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--acercarse" in capsys.readouterr().out, modulo.__name__


def test_la_ruta_por_defecto_el_panel_y_el_boletin_nombran_el_switch(monkeypatch):
    # Decisión 11: la ruta lleva _acercarse, y el panel y el encabezado del boletín nombran la
    # recompensa cuando está prendida. En el panel va en el renglón de las ayudas (bloque B: con el
    # modo, las dos ayudas no entran)
    import main  # noqa: E402
    from src.analytics.boletin import armar_boletin  # noqa: E402
    from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
    from src.ui.stats import datos_de_la_generacion  # noqa: E402

    def boletin(acercarse):
        fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
        fila.update(semilla=7, evolucion=1, modo="autonomo", acercarse=acercarse, generacion=1, ticks=960)
        registro = RegistroDeLaCorrida(960, 800, 16)
        agente = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=20.0,
                                 food_eaten=1, distance_traveled=100.0, age=960)
        registro.cerrar_generacion(fila, 960, [agente])
        return armar_boletin(registro)["subtitulo"]

    sin_comida = SimpleNamespace(food_items=[])
    monkeypatch.setattr(SimulationConfig, "MODO", "autonomo")
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False, raising=False)
    assert main._ruta_csv_por_defecto(3, False) == str(Path("results") / "corrida_s3_autonomo_sin_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], sin_comida, 0))
    assert datos["Modo"] == "autónomo" and "Ayudas" not in datos
    assert boletin(0).startswith("Modo autónomo · con evolución")

    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True)
    assert main._ruta_csv_por_defecto(3, True) == str(Path("results") / "corrida_s3_autonomo_acercarse_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], sin_comida, 0))
    assert (datos["Modo"], datos["Ayudas"]) == ("autónomo", "acercarse")
    assert boletin(1).startswith("Modo autónomo + acercarse · con evolución")


class _RedQueCamina:
    """Una red de mentira: siempre adelante y golpeando, sin girar ni comer."""

    def forward(self, _sensores):
        return {"move_forward": 1.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 1.0}


def test_prendido_en_autonomo_decide_y_act_no_consumen_azar(monkeypatch, prendido, mundo):
    # Decisión 7: 60 ticks de cuatro agentes con cerebros al azar y uno que camina hacia la llave
    monkeypatch.setattr(SimulationConfig, "MODO", "autonomo")
    llave = mundo.red_key
    agentes = [_agente(llave.x + dx, llave.y + dy) for dx, dy in ((60, 0), (-60, 0), (0, 60), (0, -60))]
    caminante = _agente(llave.x - 60, llave.y)
    caminante.brain, caminante.angle = _RedQueCamina(), 0.0  # mirando a la llave
    agentes.append(caminante)
    estado_random, estado_np = random.getstate(), np.random.get_state()
    for tick in range(TICK_INICIAL, TICK_INICIAL + 60):
        for agente in agentes:
            agente.act(agente.decide(mundo, agentes, None), mundo, agentes, tick)
    for agente in agentes:
        agente._calculate_fitness()
    assert random.getstate() == estado_random
    estado = np.random.get_state()
    assert estado[0] == estado_np[0] and np.array_equal(estado[1], estado_np[1]) and estado[2:] == estado_np[2:]
    # El término se movió: el caminante se acercó a la llave
    assert _termino(monkeypatch, caminante) > 0


def test_la_misma_trayectoria_da_el_mismo_termino_en_los_dos_modos(monkeypatch, prendido):
    # Decisión 3: los modos difieren solo en la guía. Caminando derecho, act() no gira ni sortea
    terminos = {}
    for modo in ("guiado", "autonomo"):
        monkeypatch.setattr(SimulationConfig, "MODO", modo)
        agente = _agente(*_a_la_llave(200)[0])
        agente.angle = math.pi  # mirando a la llave, que está a su izquierda
        for tick in range(TICK_INICIAL, TICK_INICIAL + 20):
            agente.act(dict(CAMINAR), _solo_la_llave(), [], tick)
        terminos[modo] = _termino(monkeypatch, agente)
    assert terminos["guiado"] == terminos["autonomo"]
    assert terminos["guiado"] > 0
