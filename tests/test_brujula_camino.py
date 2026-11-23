"""
Tests de la brújula por el camino (BRUJULA_CAMINO, --brujula-camino; spec PUZZLE_SOLOS, sección "La
brújula por el camino", sugerida por la medición de la puerta de hierro,
docs/qa/AnalisisQA.md#medicion-puerta-hierro).

Prendida, los sensores 9 y 11 siguen el camino libre más corto al próximo paso, no la recta. La grilla
de src/world/camino.py tiene que ver lo mismo que _choca, no consumir azar y, en campo abierto, dar la
recta. Apagada, nada cambia: no se arma ninguna grilla, y el CSV de main._simular es el de antes del
switch (lo controla test_fortalezas_moviles.py, test_apagado_el_csv_es_el_de_antes_del_switch, con los
valores por defecto).
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

import main  # noqa: E402 (main importa pygame y todo el resto)
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.analytics.boletin import armar_boletin  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402
from src.world import camino  # noqa: E402
from src.world.obstacles import Key, Obstacle  # noqa: E402
from src.world.world import World  # noqa: E402

PASO = SimulationConfig.AGENT_SPEED
RADIO_GOLPE = 25  # el de world.process_door_hit


def _mundo(monkeypatch, semilla, generaciones=1, moviles=False):
    """Un mundo de verdad. Con generaciones > 1, el de esa generación (reset_food)."""
    monkeypatch.setattr(SimulationConfig, "FORTALEZAS_MOVILES", moviles, raising=False)
    random.seed(semilla)
    np.random.seed(semilla)
    mundo = World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT, SimulationConfig.FOOD_COUNT)
    for generacion in range(2, generaciones + 1):
        mundo.reset_food(generacion)
    return mundo


def _vacio(**objetos):
    """Un mundo con solo lo que el test pone."""
    base = dict(obstacles=[], food_items=[], perimeter_obstacles=[], pond_obstacles=[], door=None, door_iron=None,
                red_key=None, gold_key=None, chest=None, screen_width=960, screen_height=800)
    base.update(objetos)
    return SimpleNamespace(**base)


def _angulo(a, b):
    """La diferencia entre dos ángulos, en grados, de 0 a 180."""
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(math.degrees(d))


def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.BRUJULA_CAMINO is False
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).brujula_camino is False
        assert modulo._leer_argumentos(["--brujula-camino"]).brujula_camino is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--brujula-camino" in capsys.readouterr().out, modulo.__name__


# --- La grilla ---

def test_la_grilla_ve_lo_mismo_que_choca(monkeypatch):
    # Un mapa con las fortalezas movidas, un árbol talado y, para cada etapa, los centros de celda cerca
    # de las dos puertas y del estanque, y uno de cada cuatro del resto
    mundo = _mundo(monkeypatch, 3, generaciones=4, moviles=True)
    arbol = next(o for o in mundo.obstacles if o.type == "tree")
    arbol.is_cut = True
    xs, ys = camino.centros(mundo)
    cerca = [(o.x, o.y) for o in (mundo.door, mundo.door_iron, arbol, *mundo.pond_obstacles)]
    muestra = [(i, j) for i, y in enumerate(ys) for j, x in enumerate(xs)
               if (i % 4 == 0 and j % 4 == 0) or any(abs(x - cx) < 40 and abs(y - cy) < 40 for cx, cy in cerca)]
    agente = AdvancedAgent(0, 0)
    for etapa in camino.ETAPAS:
        agente.etapa = etapa
        libre = camino.libres(mundo, etapa)
        distintas = [(xs[j], ys[i]) for i, j in muestra if libre[i, j] == agente._choca(xs[j], ys[i], mundo)]
        assert distintas == [], (etapa, distintas[:5])
    assert len(muestra) > 3000


def test_armar_y_leer_no_consume_azar(monkeypatch):
    mundo = _mundo(monkeypatch, 4)
    random.seed(11)
    np.random.seed(11)
    antes = (random.getstate(), np.random.get_state()[1].copy())
    camino.campos(mundo)
    camino.rumbo(mundo, 3, 300.0, 300.0)
    camino.rumbo(mundo, 1, np.array([300.0, 400.0]), np.array([300.0, 500.0]))
    assert random.getstate() == antes[0]
    assert (np.random.get_state()[1] == antes[1]).all()


def test_en_campo_abierto_es_la_recta(monkeypatch):
    # Sin paredes, el camino más corto es la recta. El esquema es de primer orden: el error baja con la
    # distancia. Medido el 2026-11-22 con 20.000 puntos: afuera del objetivo, hasta 5,7° y 10%; desde
    # 100 px, hasta 3,4° y 5,3%
    mundo = _vacio(red_key=Key(480, 400, "red_key"))
    rng = np.random.default_rng(0)
    x, y = rng.uniform(10, 950, 2000), rng.uniform(10, 790, 2000)
    d = np.hypot(480 - x, 400 - y)
    rumbo, distancia = camino.rumbo(mundo, 0, x, y)
    error = np.array([_angulo(a, b) for a, b in zip(rumbo, np.arctan2(400 - y, 480 - x))])
    error_d = np.abs(distancia / d - 1)
    afuera, lejos = d >= 27, d >= 100
    assert error[afuera].max() < 6 and error[lejos].max() < 3.5
    assert error_d[afuera].max() < 0.11 and error_d[lejos].max() < 0.055


def test_en_el_objetivo_y_sin_camino_es_la_recta_de_hoy():
    # En el objetivo (a menos de 27 px de la llave), la recta exacta
    mundo = _vacio(red_key=Key(480, 400, "red_key"))
    rumbo, distancia = camino.rumbo(mundo, 0, 470.0, 390.0)
    assert float(rumbo) == math.atan2(10, 10) and float(distancia) == math.hypot(10, 10)
    # Sin camino: la llave adentro de una caja de paredes cerrada. Desde afuera, la recta exacta
    caja = [Obstacle(400 + 20 * k, 320, 20, 20, "wall") for k in range(9)]
    caja += [Obstacle(400 + 20 * k, 460, 20, 20, "wall") for k in range(9)]
    caja += [Obstacle(400, 340 + 20 * k, 20, 20, "wall") for k in range(6)]
    caja += [Obstacle(560, 340 + 20 * k, 20, 20, "wall") for k in range(6)]
    mundo = _vacio(red_key=Key(480, 400, "red_key"), obstacles=caja)
    rumbo, distancia = camino.rumbo(mundo, 0, 200.0, 100.0)
    assert float(rumbo) == math.atan2(300, 280) and float(distancia) == math.hypot(280, 300)


def test_rodea_una_pared_que_corta_la_recta():
    # Una pared vertical entre el punto y la llave: la recta apunta contra la pared, el camino la rodea
    # por la punta más cercana (la de arriba)
    pared = [Obstacle(400, 300 + 20 * k, 20, 20, "wall") for k in range(15)]  # x 400-420, y 300-600
    mundo = _vacio(red_key=Key(600, 400, "red_key"), obstacles=pared)
    rumbo, distancia = camino.rumbo(mundo, 0, 300.0, 400.0)
    punta = math.atan2(300 - 6 - 400, 420 + 6 - 300)  # hacia la esquina de arriba de la pared, con el radio
    assert _angulo(float(rumbo), punta) < 10
    assert _angulo(float(rumbo), 0.0) > 30  # la recta
    assert float(distancia) > 300 * 1.1


# --- El agente y el seguidor ---

def test_prendido_adentro_de_la_fortaleza_chica_apunta_a_la_puerta_de_madera(monkeypatch):
    # Generación 1: la fortaleza chica en (50, 50); la llave dorada en (110, 90) y la puerta de madera
    # con centro en (100, 140). Con la llave dorada (etapa 3), la recta a la puerta de hierro cruza la
    # pared este; la brújula por el camino sale por la puerta de madera
    mundo = _mundo(monkeypatch, 5)
    assert (mundo.gold_key.x, mundo.gold_key.y) == (110, 90)
    agente = AdvancedAgent(110, 90)
    agente.x, agente.y, agente.angle, agente.etapa = 110.0, 90.0, 0.0, 3
    a_la_puerta = math.atan2(140 - 90, 100 - 110)
    monkeypatch.setattr(SimulationConfig, "BRUJULA_CAMINO", False)
    recta = float(agente.perceive(mundo, [])[8]) * math.pi
    monkeypatch.setattr(SimulationConfig, "BRUJULA_CAMINO", True)
    p = agente.perceive(mundo, [])
    assert _angulo(float(p[8]) * math.pi, a_la_puerta) < 25
    assert _angulo(recta, a_la_puerta) > 45
    rumbo, distancia = camino.rumbo(mundo, 3, 110.0, 90.0)
    assert p[8] == np.float32(float(rumbo) / math.pi) and p[10] == np.float32(min(float(distancia) / 150, 1.0))


def _seguir(mundo, etapa, x, y, brujula, pasos=1000):
    """Un seguidor de brújula perfecto que desliza, con las colisiones de act(): devuelve el primer paso a
    menos del alcance del punto del paso, o −1."""
    agente = AdvancedAgent(0, 0)
    agente.etapa = etapa
    px, py = camino.punto_del_paso(mundo, etapa)
    for paso in range(1, pasos + 1):
        ang = float(camino.rumbo(mundo, etapa, x, y)[0]) if brujula else math.atan2(py - y, px - x)
        nx = min(max(x + math.cos(ang) * PASO, 6), mundo.screen_width - 6)
        ny = min(max(y + math.sin(ang) * PASO, 6), mundo.screen_height - 6)
        if not agente._choca(nx, ny, mundo):
            x, y = nx, ny
        elif not agente._choca(nx, y, mundo):
            x = nx
        elif not agente._choca(x, ny, mundo):
            y = ny
        if math.hypot(x - px, y - py) < RADIO_GOLPE:
            return paso
    return -1


def test_el_seguidor_llega_de_la_llave_dorada_a_la_puerta_de_hierro(monkeypatch):
    mundo = _mundo(monkeypatch, 5)
    assert _seguir(mundo, 3, 110.0, 90.0, brujula=False) == -1  # la recta queda contra la pared
    assert _seguir(mundo, 3, 110.0, 90.0, brujula=True) > 0


def test_apagado_no_arma_grillas(monkeypatch, capsys):
    def no_deberia(*_):
        raise AssertionError("apagado, no se arma ninguna grilla")

    monkeypatch.setattr(camino, "CampoCamino", no_deberia)
    _correr_adentro(monkeypatch, capsys, brujula=False)


# --- La corrida, la ruta, el panel, el boletín y el experimento ---

def _correr_adentro(monkeypatch, capsys, brujula):
    """La simulación de main.py, sin ventana, 2 generaciones de 60 ticks, autónomo. Devuelve las filas
    del CSV."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 2), ("BASE_TICKS", 60),
                          ("MODO", "autonomo"), ("BRUJULA_CAMINO", brujula)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, True, filas.append)
    capsys.readouterr()
    return filas


def test_prendido_cambia_la_corrida_y_la_misma_semilla_da_lo_mismo(monkeypatch, capsys):
    apagado = _correr_adentro(monkeypatch, capsys, brujula=False)
    prendido = _correr_adentro(monkeypatch, capsys, brujula=True)
    assert prendido != apagado
    assert _correr_adentro(monkeypatch, capsys, brujula=True) == prendido
    assert "brujula_camino" not in main.COLUMNAS_CSV


def test_la_ruta_el_panel_y_el_boletin_nombran_la_brujula(monkeypatch):
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", False), ("CURRICULO", False),
                          ("DESLIZAR", True), ("FORTALEZAS_MOVILES", False), ("BRUJULA_CAMINO", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_deslizar_brujula_camino_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert (datos["Ayudas"], datos["Brújula"]) == ("deslizar", "por el camino")

    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=20.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    assert armar_boletin(registro)["subtitulo"].startswith(
        "Modo autónomo + deslizar · brújula por el camino · con evolución")

    monkeypatch.setattr(SimulationConfig, "BRUJULA_CAMINO", False)
    assert main._ruta_csv_por_defecto(3, True) == str(Path("results") / "corrida_s3_autonomo_deslizar_evolucion.csv")
    assert "Brújula" not in dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert "brújula" not in armar_boletin(registro)["subtitulo"]


def test_experimento_pasa_el_flag_y_lo_nombra(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    comandos = []

    def correr(comando, **_):
        comandos.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(experimento.subprocess, "run", correr)
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, deslizar=True, moviles=True, brujula=True)
    assert "--brujula-camino" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_deslizar_fortalezas_moviles_brujula_camino_evolucion.csv"
    experimento._correr(1, "autonomo", False, 10, tmp_path)
    assert "--brujula-camino" not in comandos[1]

    assert "**Brújula:**" in experimento.resumen_markdown([], [], "", brujula=True)
    assert "Brújula" not in experimento.resumen_markdown([], [], "")
