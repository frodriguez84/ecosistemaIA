"""
Tests de la comida que rebrota (COMIDA_REBROTA, --comida-rebrota; spec PUZZLE_SOLOS, sección "La comida que rebrota",
decidida por Fer con la medición de la comida al doble, docs/qa/AnalisisQA.md#comida20-sin-tope).

Prendido, main.py llama a World.rebrotar_comida después de world.update(), con los vivos y RADIO_LIBRE: cada manzana
comida vuelve COMIDA_REBROTA_TICKS ticks después, la misma manzana, en un lugar al azar con las reglas de _generate_food
y a RADIO_LIBRE o más de cada vivo. Consume azar solo cuando vuelve una. Apagado, main.py no la llama: no consume azar y
el CSV es el de antes (test_fortalezas_moviles.py, test_apagado_el_csv_es_el_de_antes_del_switch, y las corridas
cortas de la bitácora del spec).
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
from src.analytics.boletin import armar_boletin  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402
from src.world.world import World  # noqa: E402

R = 250  # COMIDA_REBROTA_TICKS


def _mundo(monkeypatch, semilla=3, prendido=True):
    monkeypatch.setattr(SimulationConfig, "COMIDA_REBROTA", prendido)
    monkeypatch.setattr(SimulationConfig, "COMIDA_REBROTA_TICKS", R)
    random.seed(semilla)
    np.random.seed(semilla)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT, SimulationConfig.FOOD_COUNT)


def _tick(mundo, vivos=()):
    """Lo que hace main.py al final de cada tick, con el switch prendido."""
    mundo.update()
    mundo.rebrotar_comida(list(vivos), main.RADIO_LIBRE)


def _vivo(x, y):
    return SimpleNamespace(x=float(x), y=float(y), alive=True)


def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.COMIDA_REBROTA is False
    assert SimulationConfig.COMIDA_REBROTA_TICKS == R
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).comida_rebrota is False
        assert modulo._leer_argumentos(["--comida-rebrota"]).comida_rebrota is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--comida-rebrota" in capsys.readouterr().out, modulo.__name__


# --- Cuándo vuelve ---

def test_una_manzana_comida_vuelve_a_los_R_ticks_y_no_antes(monkeypatch):
    mundo = _mundo(monkeypatch)
    manzana = mundo.food_items[0]
    cuantas, antes = len(mundo.food_items), (manzana['x'], manzana['y'])
    manzana['eaten'] = True  # la comió un agente en el tick 0 de main.py
    for _ in range(R):  # falta en los ticks 1 a R
        _tick(mundo)
        assert manzana['eaten']
    assert manzana['vuelve'] == 1 + R  # el reloj del mundo después del tick 0, más R
    _tick(mundo)  # el R: está en el R + 1
    assert not manzana['eaten'] and 'vuelve' not in manzana
    assert mundo.food_items[0] is manzana and len(mundo.food_items) == cuantas  # la misma, en otro lugar
    assert (manzana['x'], manzana['y']) != antes


def test_no_consume_azar_hasta_que_vuelve_una(monkeypatch):
    mundo = _mundo(monkeypatch)
    estado = random.getstate()
    for _ in range(50):  # sin nada comido
        _tick(mundo)
    mundo.food_items[5]['eaten'] = True
    for _ in range(R):
        _tick(mundo)
    assert random.getstate() == estado
    _tick(mundo)
    assert random.getstate() != estado and not mundo.food_items[5]['eaten']


def test_las_de_la_tala_tambien_vuelven(monkeypatch):
    mundo = _mundo(monkeypatch)
    mundo._generate_food_from_tree_cut()
    cuantas = len(mundo.food_items)
    de_la_tala = mundo.food_items[-1]
    assert de_la_tala.get('type') == 'apple'
    de_la_tala['eaten'] = True
    for _ in range(R + 1):
        _tick(mundo)
    assert not de_la_tala['eaten'] and len(mundo.food_items) == cuantas


# --- Dónde vuelve ---

def test_vuelven_con_las_reglas_del_arranque_y_lejos_de_los_vivos(monkeypatch):
    mundo = _mundo(monkeypatch, semilla=11)
    rng = random.Random(5)
    vivos = [_vivo(rng.randint(50, 900), rng.randint(50, 750)) for _ in range(60)]
    for manzana in mundo.food_items:
        manzana['eaten'] = True
    for _ in range(R + 1):
        _tick(mundo, vivos)
    sin_comer = [m for m in mundo.food_items if not m['eaten']]
    assert len(sin_comer) > 40  # vuelve la mayoría: con 60 vivos y 20 intentos, alguna espera al tick siguiente
    for manzana in sin_comer:
        otras = [m for m in sin_comer if m is not manzana]
        assert mundo._lugar_para_manzana(manzana['x'], manzana['y'], otras)
        assert all(((manzana['x'] - a.x)**2 + (manzana['y'] - a.y)**2)**0.5 >= main.RADIO_LIBRE for a in vivos)
    for _ in range(30):  # las que esperaban, vuelven en los ticks siguientes
        _tick(mundo, vivos)
    assert all(not m['eaten'] for m in mundo.food_items)


def test_un_lugar_cerca_de_un_vivo_se_descarta(monkeypatch):
    mundo = _mundo(monkeypatch)
    manzana = mundo.food_items[0]
    manzana['eaten'] = True
    for _ in range(R):
        _tick(mundo)
    lejos = next((x, y) for x in range(100, 900, 37) for y in range(100, 700, 41)
                 if mundo._lugar_para_manzana(x, y, [m for m in mundo.food_items if not m['eaten']]))
    vivo = _vivo(lejos[0] + 20, lejos[1])  # a 20 px del primer lugar sorteado
    sorteos = iter([lejos[0], lejos[1], lejos[0] + 300 if lejos[0] < 600 else lejos[0] - 300, lejos[1]])
    monkeypatch.setattr(random, "randint", lambda a, b: next(sorteos))
    monkeypatch.setattr(World, "_lugar_para_manzana", lambda self, x, y, manzanas: True)
    _tick(mundo, [vivo])
    assert not manzana['eaten'] and (manzana['x'], manzana['y']) != lejos  # el segundo lugar, no el primero


def test_sin_lugar_sigue_comida_y_prueba_en_el_tick_siguiente(monkeypatch):
    mundo = _mundo(monkeypatch)
    manzana = mundo.food_items[0]
    manzana['eaten'] = True
    for _ in range(R):
        _tick(mundo)
    lugar = World._lugar_para_manzana
    monkeypatch.setattr(World, "_lugar_para_manzana", lambda self, x, y, manzanas: False)
    estado = random.getstate()
    _tick(mundo)
    assert manzana['eaten'] and manzana['vuelve'] == 1 + R
    assert random.getstate() != estado  # probó sus 20 lugares
    monkeypatch.setattr(World, "_lugar_para_manzana", lugar)
    _tick(mundo)
    assert not manzana['eaten']


def test_la_generacion_nueva_no_hereda_vueltas(monkeypatch):
    mundo = _mundo(monkeypatch)
    mundo.food_items[0]['eaten'] = True
    _tick(mundo)
    mundo.reset_food(2)
    assert not any('vuelve' in m or m['eaten'] for m in mundo.food_items)


# --- main.py ---

def _correr_adentro(monkeypatch, capsys, prendido):
    """main._simular sin ventana, autónomo con evolución, semilla 7, 3 generaciones de 60 ticks."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 3), ("BASE_TICKS", 60), ("MODO", "autonomo"),
                          ("RECOMPENSA_ACERCARSE", False), ("CURRICULO", False), ("DESLIZAR", False),
                          ("FORTALEZAS_MOVILES", False), ("COMIDA_REBROTA", prendido)):
        monkeypatch.setattr(SimulationConfig, nombre, valor)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, True, filas.append)
    capsys.readouterr()
    return filas


def test_apagado_main_no_la_llama(monkeypatch, capsys):
    def no_deberia(self, vivos, distancia):
        raise AssertionError("con el switch apagado no se llama a rebrotar_comida")

    monkeypatch.setattr(World, "rebrotar_comida", no_deberia)
    assert len(_correr_adentro(monkeypatch, capsys, prendido=False)) == 3


def test_prendido_main_la_llama_en_cada_tick_con_los_vivos(monkeypatch, capsys):
    llamadas = []
    original = World.rebrotar_comida

    def anotar(self, vivos, distancia):
        llamadas.append((self.tick, len(vivos), all(a.alive for a in vivos), distancia))
        original(self, vivos, distancia)

    apagado = _correr_adentro(monkeypatch, capsys, prendido=False)
    monkeypatch.setattr(World, "rebrotar_comida", anotar)
    prendido = _correr_adentro(monkeypatch, capsys, prendido=True)
    assert len(llamadas) == 3 * 60
    assert [t for t, _, _, _ in llamadas] == list(range(1, 61)) * 3  # después de update(), con el reloj del mundo
    assert all(vivos and d == main.RADIO_LIBRE for _, _, vivos, d in llamadas)
    # Con generaciones de 60 ticks (R = 250) ninguna vuelve: no consume azar y la corrida es la de apagado
    assert prendido == apagado


def test_la_ruta_el_panel_el_boletin_y_el_experimento_nombran_la_comida_que_rebrota(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", True), ("CURRICULO", False),
                          ("DESLIZAR", False), ("FORTALEZAS_MOVILES", False), ("BRUJULA_CAMINO", True),
                          ("ACERCARSE_CAMINO", True), ("FITNESS_SIN_TOPE", True), ("COMIDA_REBROTA", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_camino_brujula_camino_sin_tope_rebrota_evolucion.csv")
    assert dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))["Manzanas"] == "rebrotan"

    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=250.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", acercarse=1, generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    assert "fitness sin tope · comida que rebrota · con evolución" in armar_boletin(registro)["subtitulo"]

    comandos = []
    monkeypatch.setattr(experimento.subprocess, "run",
                        lambda comando, **_: comandos.append(comando) or SimpleNamespace(returncode=0))
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, acercarse=True, rebrota=True)
    assert "--comida-rebrota" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_acercarse_rebrota_evolucion.csv"
    assert ("**Comida:** cada manzana comida vuelve a los `COMIDA_REBROTA_TICKS` ticks (`config.py`), en otro lugar "
            "al azar.") in experimento.resumen_markdown([], [], "", rebrota=True)
    assert "**Comida:**" not in experimento.resumen_markdown([], [], "")

    monkeypatch.setattr(SimulationConfig, "COMIDA_REBROTA", False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_acercarse_camino_brujula_camino_sin_tope_evolucion.csv")
    assert "Manzanas" not in dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert "comida que rebrota" not in armar_boletin(registro)["subtitulo"]
