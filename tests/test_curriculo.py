"""
Tests del currículo (spec PUZZLE_APRENDIBLE, bloque B, decisiones 8 a 12 y 16).

Cada test se corrió una vez contra el código de antes del bloque B y falló: es su control (cuáles
fallaron por AttributeError, en la bitácora del spec). El que mira el CSV corre la simulación adentro
del test, sin ventana y con generaciones de 30 ticks: así el corte del currículo entra en pocos
segundos (los tests de humo cuestan ~15 s por corrida).
"""

import math
import random
import re
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
from src.evolution.genetic_algorithm import GeneticAlgorithm  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402
from src.world.world import World  # noqa: E402

# Un tick sin moverse, sin girar, sin comer y sin golpear; uno igual pero golpeando; y uno caminando
QUIETO = {"move_forward": 0.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}
GOLPE = dict(QUIETO, hit=1.0)
CAMINAR = dict(QUIETO, move_forward=1.0)

TICK_INICIAL = 1000  # Lejos de cualquier cooldown: el del agente es de 120 ticks y arranca en 0
MANZANAS = 4  # Para que ningún tope del fitness recorte el término de acercarse
LINEA_DE_HITO = re.compile(r"^🏆 (¡.+!) Agente \d+, generación (\d+), segundo")


@pytest.fixture
def curriculo(monkeypatch):
    # raising=False: el control corrió contra el código de antes, cuando el switch no existía
    monkeypatch.setattr(SimulationConfig, "CURRICULO", True, raising=False)


@pytest.fixture
def mundo():
    random.seed(11)
    np.random.seed(11)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT,
                 SimulationConfig.FOOD_COUNT)


def _centro(objeto):
    """Centro de una puerta: desde ahí se miden el golpe y la brújula."""
    return objeto.x + objeto.width // 2, objeto.y + objeto.height // 2


def _etapas(agentes):
    return {(agente.etapa, agente.etapa_inicial) for agente in agentes}


def _nacer(agentes, generacion):
    main._fijar_etapa_inicial(agentes, generacion)
    return agentes


# --- Nacen con la llave roja (decisiones 8 y 9) ---

def test_apagado_por_defecto_con_corte_en_la_15_y_los_flags(capsys):
    # Decisión 2: los dos switches, apagados; --curriculo lo prende en main.py y en experimento.py
    import experimento  # noqa: E402
    assert SimulationConfig.CURRICULO is False
    assert SimulationConfig.CURRICULO_HASTA_GENERACION == 15
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).curriculo is False
        assert modulo._leer_argumentos(["--curriculo"]).curriculo is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--curriculo" in capsys.readouterr().out, modulo.__name__


def test_prendido_nacen_en_la_etapa_1_hasta_el_corte_elites_incluidas(curriculo):
    random.seed(3)
    np.random.seed(3)
    ga = GeneticAlgorithm(**SimulationConfig.get_genetic_params())
    assert ga.elitism >= 1
    agentes = _nacer(ga._create_random_population(), 1)
    assert _etapas(agentes) == {(1, 1)}
    hasta = SimulationConfig.CURRICULO_HASTA_GENERACION
    for generacion in (2, hasta, hasta + 1):
        for i, agente in enumerate(agentes):
            agente.food_eaten = i % 5  # fitness distintos: la élite es una sola
        agentes = _nacer(ga.evolve(agentes, generacion - 1), generacion)
        assert _etapas(agentes) == ({(1, 1)} if generacion <= hasta else {(0, 0)}), generacion


def test_la_llave_dada_al_nacer_no_trae_su_premio(curriculo):
    # Decisión 8: nacen con la llave, sin RED_KEY_REWARD, porque no la agarraron
    nacido, sin_llave = AdvancedAgent(100, 100), AdvancedAgent(100, 100)
    _nacer([nacido], 1)
    for agente in (nacido, sin_llave):
        agente.food_eaten = MANZANAS
    assert nacido.puzzle_rewards == 0
    assert nacido._calculate_fitness() == sin_llave._calculate_fitness()


def test_con_otro_CURRICULO_HASTA_GENERACION_el_corte_se_mueve(monkeypatch, curriculo):
    # config.py manda: un valor distinto del de hoy (15)
    monkeypatch.setattr(SimulationConfig, "CURRICULO_HASTA_GENERACION", 3, raising=False)
    for generacion, etapa in ((1, 1), (3, 1), (4, 0), (15, 0)):
        assert _etapas(_nacer([AdvancedAgent(0, 0) for _ in range(3)], generacion)) == {(etapa, etapa)}


def test_apagado_nacen_siempre_en_la_etapa_0(monkeypatch):
    monkeypatch.setattr(SimulationConfig, "CURRICULO", False, raising=False)
    for generacion in (1, 15, 16):
        assert _etapas(_nacer([AdvancedAgent(0, 0) for _ in range(3)], generacion)) == {(0, 0)}


def test_el_que_nace_con_la_llave_va_a_la_puerta_y_es_pared_hasta_que_la_abre(curriculo, mundo):
    # Decisión 8: el mapa no cambia. La llave roja sigue ahí y no la puede agarrar; la brújula apunta
    # a la puerta, y la puerta es pared para él hasta que la abre
    x, y = _centro(mundo.door)
    agente = _nacer([AdvancedAgent(x, y + 15)], 1)[0]
    assert agente._proximo_paso(mundo) == (x, y)
    llave = mundo.red_key
    agente.x, agente.y = float(llave.x), float(llave.y)
    assert not agente._try_pickup_key(mundo)
    assert (agente.etapa, agente.puzzle_rewards) == (1, 0)

    # Una puerta sola, la del mundo, para que nada más del mapa estorbe al caminar
    solo_la_puerta = SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[],
                                     pond_obstacles=[], door=mundo.door, door_iron=None, red_key=None,
                                     gold_key=None, chest=None, screen_width=960, screen_height=800)

    def caminar_hacia_la_puerta(tick):
        agente.x, agente.y, agente.angle = float(x), float(y + 18), -math.pi / 2  # mirando a la puerta
        agente.act(dict(CAMINAR), solo_la_puerta, [], tick)
        return agente.y < y + 18

    assert not caminar_hacia_la_puerta(TICK_INICIAL)  # choca
    tick = TICK_INICIAL + 1
    for _ in range(SimulationConfig.DOOR_HITS_TO_OPEN):
        agente.x, agente.y = float(x), float(y + 15)
        agente.act(dict(GOLPE), mundo, [], tick)
        agente._try_hit_door(mundo, tick)
        tick += SimulationConfig.DOOR_HIT_COOLDOWN
    assert agente.etapa == 2
    assert agente.puzzle_rewards == SimulationConfig.DOOR_OPEN_REWARD  # la puerta sí: la abrió
    assert caminar_hacia_la_puerta(tick)  # pasa


# --- Lo que se da al nacer no es un logro (decisión 10) ---

def test_un_paso_dado_al_nacer_no_es_hito():
    def agente(id_, etapa, etapa_inicial):
        return SimpleNamespace(id=id_, etapa=etapa, etapa_inicial=etapa_inicial)

    registro = RegistroDeLaCorrida(960, 800, 16)
    assert registro.mirar_hitos([agente(1, 1, 1), agente(2, 1, 1)], 1, 10) == []
    # Con el currículo, el primer hito puede ser la puerta de madera
    assert registro.mirar_hitos([agente(1, 1, 1), agente(2, 2, 1)], 1, 11) == [
        {"paso": 2, "generacion": 1, "tick": 11, "agente": 2}]
    assert registro.mirar_hitos([agente(1, 2, 1)], 2, 3) == []
    # Desde que nacen sin la llave, la primera que alguien agarra sí es hito
    assert registro.mirar_hitos([agente(3, 0, 0), agente(4, 1, 0)], 16, 5) == [
        {"paso": 1, "generacion": 16, "tick": 5, "agente": 4}]
    assert [hito["paso"] for hito in registro.hitos] == [2, 1]


def test_en_el_boletin_la_llave_dada_no_es_la_primera_vez_y_el_curriculo_se_nombra():
    # Gen 1, del currículo: los 60 con la llave y uno abre la puerta. Gen 2, del puzzle de hoy: 3
    # agarran la llave
    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=2, etapa_inicial=1, fitness=20.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    for generacion, etapa_inicial, llave, puerta in ((1, 1, 60, 1), (2, 0, 3, 0)):
        fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
        fila.update(semilla=7, evolucion=1, modo="autonomo", generacion=generacion, ticks=960,
                    etapa_inicial=etapa_inicial, agentes_llave_roja=llave, agentes_puerta_madera=puerta)
        registro.cerrar_generacion(fila, 960, [mejor])
    boletin = armar_boletin(registro)
    primera_vez = {paso["nombre"]: paso["primera_vez"] for paso in boletin["embudo"]}
    assert primera_vez["Llave roja"] == 2
    assert primera_vez["Puerta de madera"] == 1
    assert boletin["subtitulo"].startswith("Modo autónomo + currículo · con evolución")


def test_si_la_ultima_generacion_nacio_con_la_llave_el_boletin_lo_dice():
    # Una corrida que termina adentro del currículo: los 60 tienen la llave, pero nadie la agarró. El
    # mejor agente dice hasta dónde llegó él, sin lo que le dieron
    def boletin(etapa_del_mejor):
        registro = RegistroDeLaCorrida(960, 800, 16)
        mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=etapa_del_mejor, etapa_inicial=1,
                                fitness=20.0, food_eaten=1, distance_traveled=100.0, age=960)
        fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
        fila.update(semilla=7, evolucion=1, modo="autonomo", generacion=1, ticks=960, etapa_inicial=1,
                    agentes_llave_roja=60, agentes_puerta_madera=int(etapa_del_mejor > 1))
        registro.cerrar_generacion(fila, 960, [mejor])
        return armar_boletin(registro)

    sin_pasos = boletin(1)
    assert sin_pasos["embudo"][0]["texto"] == "60 de 60 · dada al nacer"
    assert sin_pasos["embudo"][1]["texto"] == "nadie, en ninguna generación"
    assert sin_pasos["hasta_donde"] == "nadie agarró la llave roja"
    assert sin_pasos["mejor"]["renglones"][-1] == "llegó a: ningún paso (nació con la llave roja)"
    con_la_puerta = boletin(2)
    assert con_la_puerta["embudo"][1]["texto"] == "1 de 60 · 1ª vez: gen 1"
    assert con_la_puerta["mejor"]["renglones"][-1] == "llegó a: puerta de madera"


def test_con_los_dos_switches_los_pasos_que_dio_no_cuentan_el_dado_al_nacer(monkeypatch, curriculo, mundo):
    # Decisiones 5 y 10: el que nace con la llave arranca el término en 0, no en FITNESS_ACERCARSE
    def termino(agente):
        monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False, raising=False)
        apagado = agente._calculate_fitness()
        monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True, raising=False)
        return agente._calculate_fitness() - apagado

    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True, raising=False)
    x, y = _centro(mundo.door)
    agente = _nacer([AdvancedAgent(x, y + 200)], 1)[0]
    agente.food_eaten = MANZANAS
    agente.act(dict(QUIETO), mundo, [], TICK_INICIAL)  # d0: 200 px de la puerta
    assert termino(agente) == pytest.approx(0)
    agente.x, agente.y = float(x), float(y + 100)
    agente.act(dict(QUIETO), mundo, [], TICK_INICIAL + 1)  # camino hecho: la mitad, sin golpes
    assert termino(agente) == pytest.approx(SimulationConfig.FITNESS_ACERCARSE * 0.5 / 2)

    tick = TICK_INICIAL + 2
    for _ in range(SimulationConfig.DOOR_HITS_TO_OPEN):
        agente.x, agente.y = float(x), float(y + 15)
        agente.act(dict(GOLPE), mundo, [], tick)
        agente._try_hit_door(mundo, tick)
        tick += SimulationConfig.DOOR_HIT_COOLDOWN
    assert agente.etapa == 2
    assert termino(agente) == pytest.approx(SimulationConfig.FITNESS_ACERCARSE)  # un paso dado


# --- CSV, ruta y pantallas (decisión 11) ---

def _correr_adentro(monkeypatch, capsys, curriculo, generaciones=3, hasta=2):
    """La simulación de main.py, sin ventana, con generaciones de 30 ticks. Devuelve las filas del
    CSV, por columna, y lo que imprimió."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", generaciones), ("BASE_TICKS", 30),
                          ("MODO", "autonomo"), ("CURRICULO", curriculo), ("CURRICULO_HASTA_GENERACION", hasta)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, True, filas.append)
    return [dict(zip(main.COLUMNAS_CSV, fila)) for fila in filas], capsys.readouterr().out


def test_etapa_inicial_en_el_csv_y_sin_hito_de_la_llave_dada(monkeypatch, capsys):
    i = main.COLUMNAS_CSV.index("etapa_inicial")
    assert main.COLUMNAS_CSV[i - 1] == "generacion"

    filas, log = _correr_adentro(monkeypatch, capsys, curriculo=True)
    poblacion = SimulationConfig.POPULATION_SIZE
    assert [fila["etapa_inicial"] for fila in filas] == [1, 1, 0]
    # Llegaron al menos a la llave roja: en el currículo, todos (decisión 10)
    assert [fila["agentes_llave_roja"] for fila in filas[:2]] == [poblacion, poblacion]
    assert filas[2]["agentes_llave_roja"] < poblacion
    hitos = [m.groups() for m in map(LINEA_DE_HITO.match, log.splitlines()) if m]
    assert not [hito for hito in hitos if hito[0] == "¡Primera llave roja!" and int(hito[1]) <= 2]

    filas, _ = _correr_adentro(monkeypatch, capsys, curriculo=False)
    assert [fila["etapa_inicial"] for fila in filas] == [0, 0, 0]


def test_la_ruta_y_el_panel_nombran_el_curriculo(monkeypatch, curriculo):
    monkeypatch.setattr(SimulationConfig, "MODO", "autonomo")
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False, raising=False)
    sin_comida = SimpleNamespace(food_items=[])
    assert main._ruta_csv_por_defecto(3, False) == str(
        Path("results") / "corrida_s3_autonomo_curriculo_sin_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], sin_comida, 0))
    assert (datos["Modo"], datos["Ayudas"]) == ("autónomo", "currículo")

    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", True)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_curriculo_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], sin_comida, 0))
    assert (datos["Modo"], datos["Ayudas"]) == ("autónomo", "acercarse + currículo")

    # Sin ayudas prendidas, no hay renglón de ayudas
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False)
    monkeypatch.setattr(SimulationConfig, "CURRICULO", False)
    assert "Ayudas" not in dict(datos_de_la_generacion(1, [], sin_comida, 0))
