"""
Tests del fitness sin tope (FITNESS_SIN_TOPE, --fitness-sin-tope; spec PUZZLE_SOLOS, sección "El fitness sin tope",
decidido por Fer con la medición de comer en la referencia nueva, docs/qa/AnalisisQA.md#comer-na).

Prendido, fitness es la suma de los términos de _calculate_fitness con piso en 0, sin el recorte a 100 ni el tope por
tiempo vivido: lo que ordena la selección. fitness_con_tope es la cuenta de antes, y la leen la mutación adaptativa de
evolve y la guía del modo guiado, así el switch cambia solo el orden. No consume azar. Apagado, fitness y
fitness_con_tope son el mismo número y nada cambia (el CSV de main._simular, con los valores por defecto, lo controla
test_fortalezas_moviles.py, test_apagado_el_csv_es_el_de_antes_del_switch).
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
from src.evolution.genetic_algorithm import GeneticAlgorithm  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402

COLUMNAS_DEL_FITNESS = ("fitness_prom", "fitness_max", "fitness_min", "fitness_desvio")


def _agente(monkeypatch, sin_tope, age=0, puzzle=0.0, penalidad=0.0):
    """Un agente quieto, sin comida ni recorrido: los términos son la supervivencia, el puzzle y el agua."""
    monkeypatch.setattr(SimulationConfig, "FITNESS_SIN_TOPE", sin_tope)
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False)
    agente = AdvancedAgent(100, 100)
    agente.age, agente.puzzle_rewards, agente.fitness_env_penalty = age, puzzle, penalidad
    agente._calculate_fitness()
    return agente


def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.FITNESS_SIN_TOPE is False
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).fitness_sin_tope is False
        assert modulo._leer_argumentos(["--fitness-sin-tope"]).fitness_sin_tope is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--fitness-sin-tope" in capsys.readouterr().out, modulo.__name__


# --- La cuenta ---

def test_prendido_la_suma_pasa_de_100_y_el_tope_por_tiempo_no_corre(monkeypatch):
    supervivencia = min(SimulationConfig.BASE_TICKS * SimulationConfig.FITNESS_SURVIVAL,
                        SimulationConfig.FITNESS_SURVIVAL_MAX)
    # Vivió BASE_TICKS: con tope, 100
    agente = _agente(monkeypatch, True, age=SimulationConfig.BASE_TICKS, puzzle=150.0)
    assert agente.fitness == pytest.approx(150.0 + supervivencia)
    assert agente.fitness_con_tope == 100
    # Recién nacido: con tope, 50 (el tope por tiempo); sin tope, la suma
    agente = _agente(monkeypatch, True, age=0, puzzle=80.0)
    assert (agente.fitness, agente.fitness_con_tope) == (pytest.approx(80.0), 50)
    # Apagado, los dos son la cuenta de siempre
    agente = _agente(monkeypatch, False, age=SimulationConfig.BASE_TICKS, puzzle=150.0)
    assert agente.fitness == agente.fitness_con_tope == 100


def test_prendido_el_piso_es_0(monkeypatch):
    agente = _agente(monkeypatch, True, age=0, penalidad=25.0)  # el agua resta hasta WATER_PENALTY_MAX
    assert agente.fitness == agente.fitness_con_tope == 0


def test_no_consume_azar(monkeypatch):
    agente = AdvancedAgent(100, 100)  # crear el agente sí consume azar (los pesos de la red)
    agente.age, agente.puzzle_rewards = 500, 150.0
    monkeypatch.setattr(SimulationConfig, "FITNESS_SIN_TOPE", True)
    random.seed(11)
    np.random.seed(11)
    antes = (random.getstate(), np.random.get_state()[1].copy())
    agente._calculate_fitness()
    assert random.getstate() == antes[0]
    assert (np.random.get_state()[1] == antes[1]).all()


# --- La selección, la mutación adaptativa y la guía ---

def _evolucionar(monkeypatch, sin_tope):
    """Una generación de 60 agentes que vivieron BASE_TICKS, con el puzzle de 100 a 395: con tope, todos en 100 (el
    desvío sobre el promedio es 0 y la mutación adaptativa se dispara); sin tope, distintos. Devuelve la tasa de cada
    mutación y si la élite es el de más puzzle."""
    monkeypatch.setattr(SimulationConfig, "FITNESS_SIN_TOPE", sin_tope)
    monkeypatch.setattr(SimulationConfig, "RECOMPENSA_ACERCARSE", False)
    random.seed(3)
    np.random.seed(3)
    agentes = []
    for i in range(SimulationConfig.POPULATION_SIZE):
        agente = AdvancedAgent(100, 100)
        agente.age, agente.puzzle_rewards = SimulationConfig.BASE_TICKS, 100.0 + 5.0 * i
        agentes.append(agente)
    mejor = agentes[-1].brain
    tasas = []
    ga = GeneticAlgorithm(**SimulationConfig.get_genetic_params())  # el de main.py: meeting pool con élite
    clase = type(agentes[0].brain)
    mutar = clase.mutate
    monkeypatch.setattr(clase, "mutate", lambda red, tasa: (tasas.append(tasa), mutar(red, tasa))[1])
    hijos = ga.evolve(agentes, generation=1)
    return tasas, hijos[0].brain is mejor


def test_prendido_la_seleccion_ve_la_suma_y_la_mutacion_el_de_0_a_100(monkeypatch):
    tasas, la_elite_es_el_mejor = _evolucionar(monkeypatch, True)
    assert la_elite_es_el_mejor  # ordena por la suma
    tasa_alta = min(0.5, SimulationConfig.MUTATION_RATE * 2.5)
    assert tasas and set(tasas) == {tasa_alta}  # con el desvío de los de 0 a 100, como apagado
    tasas, la_elite_es_el_mejor = _evolucionar(monkeypatch, False)
    assert not la_elite_es_el_mejor  # todos en 100: queda el primero
    assert tasas and set(tasas) == {tasa_alta}


def test_la_guia_lee_el_fitness_de_0_a_100(monkeypatch):
    # La guía del modo guiado (fitness > 30, DIAG-13): un agente con la suma en 500 y el de 0 a 100 en 20 explora
    monkeypatch.setattr(SimulationConfig, "MODO", "guiado")
    mundo = SimpleNamespace(obstacles=[], food_items=[], perimeter_obstacles=[], pond_obstacles=[], door=None,
                            door_iron=None, red_key=None, gold_key=None, chest=None, screen_width=960,
                            screen_height=800)
    agente = AdvancedAgent(100, 100)
    agente.fitness, agente.fitness_con_tope = 500.0, 20.0
    agente.decide(mundo, [], None)
    assert agente.exploration_timer == 1


# --- La corrida, la ruta, el panel, el boletín y el experimento ---

def _correr_adentro(monkeypatch, capsys, modo, evolucion, sin_tope):
    """La simulación de main.py, sin ventana, 2 generaciones de 60 ticks, con la supervivencia pagando 5 por tick: los
    que viven pasan de 100. Devuelve las filas del CSV y lo que imprimió."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 2), ("BASE_TICKS", 60), ("MODO", modo),
                          ("FITNESS_SURVIVAL", 5.0), ("FITNESS_SURVIVAL_MAX", 1000.0),
                          ("FITNESS_SIN_TOPE", sin_tope)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, evolucion, filas.append)
    return filas, capsys.readouterr().out


@pytest.mark.parametrize("modo", ["autonomo", "guiado"])
def test_prendido_en_la_generacion_1_cambia_solo_el_fitness(monkeypatch, capsys, modo):
    con_tope, salida = _correr_adentro(monkeypatch, capsys, modo, True, False)
    sin_tope, salida_sin_tope = _correr_adentro(monkeypatch, capsys, modo, True, True)
    distintas = {columna for columna, a, b in zip(main.COLUMNAS_CSV, con_tope[0], sin_tope[0]) if a != b}
    assert distintas and distintas <= set(COLUMNAS_DEL_FITNESS), distintas
    assert dict(zip(main.COLUMNAS_CSV, sin_tope[0]))["fitness_max"] > 100
    assert _correr_adentro(monkeypatch, capsys, modo, True, True)[0] == sin_tope
    assert "fitness_sin_tope" not in main.COLUMNAS_CSV
    # El reporte por consola: sin tope, el fitness no es "/100"
    assert "Máximo: 100.0/100" in salida
    assert "/100" not in salida_sin_tope


def test_prendido_sin_evolucion_cambia_solo_el_fitness(monkeypatch, capsys):
    # La línea base (NCB0) no se corre otra vez: sin evolución, el switch no cambia lo que hacen
    con_tope, _ = _correr_adentro(monkeypatch, capsys, "autonomo", False, False)
    sin_tope, _ = _correr_adentro(monkeypatch, capsys, "autonomo", False, True)
    assert len(con_tope) == len(sin_tope) == 2
    for fila_con, fila_sin in zip(con_tope, sin_tope):
        distintas = {columna for columna, a, b in zip(main.COLUMNAS_CSV, fila_con, fila_sin) if a != b}
        assert distintas and distintas <= set(COLUMNAS_DEL_FITNESS), distintas


def test_la_ruta_el_panel_y_el_boletin_nombran_el_fitness_sin_tope(monkeypatch):
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", True), ("CURRICULO", False),
                          ("DESLIZAR", False), ("FORTALEZAS_MOVILES", False), ("BRUJULA_CAMINO", True),
                          ("ACERCARSE_CAMINO", True), ("FITNESS_SIN_TOPE", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_camino_brujula_camino_sin_tope_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert datos["Fitness"] == "sin tope"

    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=250.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", acercarse=1, generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    assert "brújula por el camino · fitness sin tope · con evolución" in armar_boletin(registro)["subtitulo"]

    monkeypatch.setattr(SimulationConfig, "FITNESS_SIN_TOPE", False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_camino_brujula_camino_evolucion.csv")
    assert "Fitness" not in dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert "fitness sin tope" not in armar_boletin(registro)["subtitulo"]


def test_experimento_pasa_el_flag_y_lo_nombra(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    comandos = []

    def correr(comando, **_):
        comandos.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(experimento.subprocess, "run", correr)
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, acercarse=True, brujula=True,
                                    acercarse_camino=True, sin_tope=True)
    assert "--fitness-sin-tope" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_acercarse_camino_brujula_camino_sin_tope_evolucion.csv"
    experimento._correr(1, "autonomo", False, 10, tmp_path, acercarse=True)
    assert "--fitness-sin-tope" not in comandos[1]
    # El resumen lo nombra: test_resumen.py, test_el_resumen_dice_las_ayudas_prendidas
