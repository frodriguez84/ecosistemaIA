"""
Tests de deslizar contra lo que choca (DESLIZAR, --deslizar; mejora sugerida por la medición de la
puerta, docs/qa/AnalisisQA.md#medicion-puerta-madera).

Si el paso choca, el agente prueba moverse solo en x y, si no, solo en y, con las mismas colisiones
del paso entero: obstáculos, las puertas que no abrió, el perímetro y el estanque, con la caja
descentrada de los dos últimos (DIAG-30). Apagado, no se mueve, como siempre.

Se corrieron una vez contra el código de antes del switch y fallaron: es su control (en
AnalisisQA, sección de deslizar).
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
from src.world.obstacles import Door, Obstacle, PondObstacle  # noqa: E402

CAMINAR = {"move_forward": 1.0, "turn_left": 0.0, "turn_right": 0.0, "eat": 0.0, "hit": 0.0}
TICK = 1000
PASO = SimulationConfig.AGENT_SPEED * math.cos(math.pi / 4)  # cada eje de un paso en diagonal: ~2,12 px

# Rumbos en diagonal (y crece hacia abajo)
ARRIBA_DERECHA = -math.pi / 4
ABAJO_DERECHA = math.pi / 4
ABAJO_IZQUIERDA = 3 * math.pi / 4


def _mundo(obstaculos=(), estanque=(), puerta=None):
    """Un mundo con solo lo que el test pone: así nada más del mapa estorba al caminar."""
    return SimpleNamespace(obstacles=list(obstaculos), food_items=[], perimeter_obstacles=[],
                           pond_obstacles=list(estanque), door=puerta, door_iron=None, red_key=None,
                           gold_key=None, chest=None, screen_width=960, screen_height=800)


def _caminar(monkeypatch, mundo, x, y, angulo, deslizar, etapa=0):
    """Un tick caminando con ese rumbo, desde (x, y). Devuelve dónde quedó y el agente."""
    monkeypatch.setattr(SimulationConfig, "DESLIZAR", deslizar, raising=False)
    monkeypatch.setattr(SimulationConfig, "MODO", "autonomo")
    agente = AdvancedAgent(x, y)
    agente.x, agente.y, agente.angle, agente.etapa = float(x), float(y), angulo, etapa
    agente.act(dict(CAMINAR), mundo, [], TICK)
    return (agente.x, agente.y), agente


@pytest.fixture
def pared():
    # Pared de 20 × 20 con centro en (210, 110): el centro de un agente (radio 6) choca en x de 194 a
    # 226 y en y de 94 a 126
    return Obstacle(200, 100, 20, 20, "wall")


def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.DESLIZAR is False
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).deslizar is False
        assert modulo._leer_argumentos(["--deslizar"]).deslizar is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--deslizar" in capsys.readouterr().out, modulo.__name__


# --- El movimiento ---

def test_contra_una_pared_al_costado_desliza_solo_en_y(monkeypatch, pared):
    mundo = _mundo([pared])
    # A la izquierda de la pared, yendo arriba a la derecha: el paso entero y el de solo x chocan
    assert _caminar(monkeypatch, mundo, 192, 110, ARRIBA_DERECHA, deslizar=False)[0] == (192, 110)
    (x, y), agente = _caminar(monkeypatch, mundo, 192, 110, ARRIBA_DERECHA, deslizar=True)
    assert (x, y) == pytest.approx((192, 110 - PASO))
    assert agente.moving
    assert agente.distance_traveled == pytest.approx(PASO)  # cuenta lo que se movió, no el paso entero


def test_contra_una_pared_arriba_desliza_solo_en_x(monkeypatch, pared):
    mundo = _mundo([pared])
    # Debajo de la pared, yendo arriba a la derecha: el de solo x no choca, y se prueba primero
    assert _caminar(monkeypatch, mundo, 210, 128, ARRIBA_DERECHA, deslizar=False)[0] == (210, 128)
    assert _caminar(monkeypatch, mundo, 210, 128, ARRIBA_DERECHA, deslizar=True)[0] == pytest.approx(
        (210 + PASO, 128))


def test_en_una_esquina_no_se_mueve(monkeypatch, pared):
    # Una pared a la derecha (la del fixture, corrida) y otra arriba: los tres pasos chocan
    derecha = Obstacle(200, 120, 20, 20, "wall")  # choca en x de 194 a 226, en y de 114 a 146
    arriba = Obstacle(170, 90, 20, 20, "wall")    # choca en x de 164 a 196, en y de 84 a 116
    mundo = _mundo([derecha, arriba])
    (x, y), agente = _caminar(monkeypatch, mundo, 193, 117, ARRIBA_DERECHA, deslizar=True)
    assert (x, y) == (193, 117)
    assert not agente.moving
    assert agente.distance_traveled == 0


def test_sin_choque_deslizar_no_cambia_el_paso(monkeypatch):
    mundo = _mundo()
    apagado = _caminar(monkeypatch, mundo, 300, 300, ARRIBA_DERECHA, deslizar=False)[0]
    assert apagado == pytest.approx((300 + PASO, 300 - PASO))
    assert _caminar(monkeypatch, mundo, 300, 300, ARRIBA_DERECHA, deslizar=True)[0] == apagado


def test_la_puerta_que_no_abrio_es_pared_para_deslizar_y_la_que_abrio_no(monkeypatch):
    puerta = Door(100, 130, "door")  # centro (110, 140): choca en x de 94 a 126, en y de 124 a 156
    mundo = _mundo(puerta=puerta)
    assert _caminar(monkeypatch, mundo, 110, 157, ARRIBA_DERECHA, deslizar=True)[0] == pytest.approx(
        (110 + PASO, 157))
    # Con la puerta abierta (etapa 2), el paso entero pasa
    assert _caminar(monkeypatch, mundo, 110, 157, ARRIBA_DERECHA, deslizar=True, etapa=2)[0] == pytest.approx(
        (110 + PASO, 157 - PASO))


def test_contra_el_estanque_desliza_con_la_caja_de_act_DIAG_30(monkeypatch):
    # Una baldosa del estanque en (300, 300), de 20 × 20. La caja del agente va de (x, y) a (x + 6,
    # y + 6), no centrada (DIAG-30): el centro choca con x entre 294 y 320, y lo mismo en y
    baldosa = PondObstacle(300, 300, '020')
    mundo = _mundo(estanque=[baldosa])
    # Por la derecha: queda pegado al borde y desliza hacia abajo con medio cuerpo sobre el agua,
    # lo mismo que deja hoy un paso derecho
    assert _caminar(monkeypatch, mundo, 321, 310, ABAJO_IZQUIERDA, deslizar=False)[0] == (321, 310)
    (x, y), agente = _caminar(monkeypatch, mundo, 321, 310, ABAJO_IZQUIERDA, deslizar=True)
    assert (x, y) == pytest.approx((321, 310 + PASO))
    assert not agente._choca(x, y, mundo)
    # Por la izquierda: desliza a un radio del borde
    (x, y), agente = _caminar(monkeypatch, mundo, 293, 310, ABAJO_DERECHA, deslizar=True)
    assert (x, y) == pytest.approx((293, 310 + PASO))
    assert not agente._choca(x, y, mundo)


def test_desliza_solo_a_donde_el_paso_entero_podria_llegar(monkeypatch, pared):
    # Desde una grilla alrededor de la pared y del estanque, en ocho rumbos: donde termina, el paso
    # entero no chocaría (las mismas colisiones), y se movió a lo sumo un paso por eje
    mundo = _mundo([pared], estanque=[PondObstacle(300, 300, '020')])
    monkeypatch.setattr(SimulationConfig, "DESLIZAR", True, raising=False)
    monkeypatch.setattr(SimulationConfig, "MODO", "autonomo")
    agente = AdvancedAgent(0, 0)
    rumbos = [i * math.pi / 4 for i in range(8)]
    for x0 in range(186, 334, 7):
        for y0 in range(86, 334, 7):
            if agente._choca(x0, y0, mundo):
                continue
            for angulo in rumbos:
                agente.x, agente.y, agente.angle = float(x0), float(y0), angulo
                agente.energy = SimulationConfig.AGENT_ENERGY  # que no se muera de tanto caminar
                agente.act(dict(CAMINAR), mundo, [], TICK)
                x, y = agente.x, agente.y
                assert agente.alive
                assert not agente._choca(x, y, mundo), (x0, y0, angulo)
                assert abs(x - x0) <= SimulationConfig.AGENT_SPEED + 1e-9
                assert abs(y - y0) <= SimulationConfig.AGENT_SPEED + 1e-9


# --- Corrida, ruta, panel y boletín ---

def _correr_adentro(monkeypatch, capsys, deslizar):
    """La simulación de main.py, sin ventana, 2 generaciones de 60 ticks, autónomo. Devuelve las filas
    del CSV."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 2), ("BASE_TICKS", 60),
                          ("MODO", "autonomo"), ("DESLIZAR", deslizar)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, True, filas.append)
    capsys.readouterr()
    return filas


def test_prendido_cambia_la_corrida_y_la_misma_semilla_da_lo_mismo(monkeypatch, capsys):
    apagado = _correr_adentro(monkeypatch, capsys, deslizar=False)
    prendido = _correr_adentro(monkeypatch, capsys, deslizar=True)
    assert prendido != apagado
    assert _correr_adentro(monkeypatch, capsys, deslizar=True) == prendido
    # No es una columna del CSV: apagado, el CSV es el de antes del switch, byte a byte
    assert "deslizar" not in main.COLUMNAS_CSV


def test_la_ruta_y_el_panel_nombran_deslizar(monkeypatch):
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", False), ("CURRICULO", False),
                          ("DESLIZAR", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    sin_comida = SimpleNamespace(food_items=[])
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_deslizar_evolucion.csv")
    assert dict(datos_de_la_generacion(1, [], sin_comida, 0))["Ayudas"] == "deslizar"

    monkeypatch.setattr(SimulationConfig, "CURRICULO", True)
    assert main._ruta_csv_por_defecto(3, False) == str(
        Path("results") / "corrida_s3_autonomo_curriculo_deslizar_sin_evolucion.csv")
    assert dict(datos_de_la_generacion(1, [], sin_comida, 0))["Ayudas"] == "currículo + deslizar"

    monkeypatch.setattr(SimulationConfig, "DESLIZAR", False)
    assert main._ruta_csv_por_defecto(3, False) == str(
        Path("results") / "corrida_s3_autonomo_curriculo_sin_evolucion.csv")


def test_el_boletin_nombra_deslizar(monkeypatch):
    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=20.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    monkeypatch.setattr(SimulationConfig, "DESLIZAR", False, raising=False)
    assert armar_boletin(registro)["subtitulo"].startswith("Modo autónomo · con evolución")
    monkeypatch.setattr(SimulationConfig, "DESLIZAR", True)
    assert armar_boletin(registro)["subtitulo"].startswith("Modo autónomo + deslizar · con evolución")


def test_experimento_pasa_el_flag_y_lo_nombra(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    comandos = []

    def correr(comando, **_):
        comandos.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(experimento.subprocess, "run", correr)
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, curriculo=True, deslizar=True)
    assert "--deslizar" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_curriculo_deslizar_evolucion.csv"
    experimento._correr(1, "autonomo", False, 10, tmp_path)
    assert "--deslizar" not in comandos[1]

    assert "**Ayudas prendidas:** deslizar al chocar." in experimento.resumen_markdown([], [], "", deslizar=True)
    assert "**Ayudas prendidas:** ninguna." in experimento.resumen_markdown([], [], "")
