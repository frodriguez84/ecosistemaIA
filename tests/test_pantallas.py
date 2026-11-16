"""
Tests de las pantallas (spec PANTALLAS_VER_APRENDER, decisiones 9 a 12, 14 y 17): el panel, los avisos
y la pantalla final se dibujan sin error sobre la superficie de 1200×800, con 0, 1 y 30 generaciones,
con cofre y sin él, y en la línea base; los avisos duran lo que dicen, con un reloj inyectado; y con
ventana no hay aviso después de la última generación.

Con SDL_VIDEODRIVER=dummy: no abre ninguna ventana. Arman el registro a mano, como test_boletin.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config import SimulationConfig  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
from src.ui import avisos as modulo_avisos, fuentes  # noqa: E402
from src.ui.avisos import PilaDeAvisos, textos_de_generacion  # noqa: E402
from src.ui.pantalla_final import dibujar_boletin, marcas_del_grafico  # noqa: E402
from src.ui.stats import NADIE_TODAVIA, StatsPanel, renglones_del_puzzle  # noqa: E402
from test_boletin import _fila, _registro  # noqa: E402
from src.analytics.boletin import armar_boletin  # noqa: E402

FORTALEZAS = SimpleNamespace(small_fortress_pos={"x": 50, "y": 50, "size": 5},
                             large_fortress_pos={"x": 718, "y": 558, "size": 6})


@pytest.fixture(scope="module")
def sprites():
    """Una pantalla de mentira (los sprites la necesitan para cargarse) y los sprites del juego,
    que se cargan con rutas relativas a la raíz del repo."""
    anterior_driver, anterior_cwd = os.environ.get("SDL_VIDEODRIVER"), os.getcwd()
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.chdir(RAIZ)
    fuentes.olvidar()
    pygame.init()
    pygame.display.set_mode((1200, 800))
    from src.ui.renderer import SpriteManager
    yield SpriteManager()
    pygame.quit()
    fuentes.olvidar()
    os.chdir(anterior_cwd)
    if anterior_driver is None:
        os.environ.pop("SDL_VIDEODRIVER", None)
    else:
        os.environ["SDL_VIDEODRIVER"] = anterior_driver


def _corrida(generaciones, cofre=False, evolucion=1, vivos_al_final=20):
    """Un registro de mentira: el fitness y las manzanas suben de a poco; la llave roja desde la
    generación 2 y, con cofre, todo el puzzle desde la 3; la última termina con vivos_al_final."""
    filas = []
    for g in range(1, generaciones + 1):
        pasos = {"agentes_llave_roja": 5} if g >= 2 else {}
        if cofre and g >= 3:
            pasos.update(agentes_puerta_madera=4, agentes_llave_dorada=3, agentes_puerta_hierro=3,
                         agentes_cofre=2)
        filas.append(_fila(g, evolucion=evolucion, fitness_prom=20.0 + g / 2, fitness_max=55.0 + g % 7,
                           manzanas_prom=0.6 + g / 50, edad_prom=860.0 + 6 * g, distancia_prom=365.0 + 34 * g,
                           vivos=vivos_al_final if g == generaciones else 20, **pasos))
    return _registro(filas, ticks_max=[960 + 180 * ((g - 1) // 4) for g in range(1, generaciones + 1)],
                     mejor_etapa=5 if cofre else 1)


CORRIDAS = {
    "1 generación": lambda: _corrida(1),
    "30 generaciones": lambda: _corrida(30),
    "con cofre": lambda: _corrida(30, cofre=True),
    "línea base": lambda: _corrida(3, evolucion=0),
    "murieron todos": lambda: _corrida(30, vivos_al_final=0),
}


def _agentes():
    return [SimpleNamespace(alive=i < 40, tiene_hacha=i < 3, etapa=1 if i < 2 else 0) for i in range(60)]


# --- El panel (decisión 9) ---

@pytest.mark.parametrize("registro", [
    pytest.param(lambda: RegistroDeLaCorrida(960, 800, 16), id="0 generaciones"),
    *(pytest.param(armar, id=nombre) for nombre, armar in CORRIDAS.items()),
])
def test_el_panel_se_dibuja(sprites, registro):
    superficie = pygame.Surface((1200, 800))
    superficie.fill((0, 0, 0))
    mundo = SimpleNamespace(food_items=[{"eaten": False}] * 70)
    StatsPanel(960, 0, 240, 800).draw(superficie, 2, _agentes(), mundo, 600, registro(), sprites)
    # Ocupa la columna entera, a la derecha del mundo, y no toca el mundo
    assert superficie.get_at((961, 799))[:3] != (0, 0, 0)
    assert superficie.get_at((959, 400))[:3] == (0, 0, 0)


def test_el_puzzle_del_panel_dice_esta_generacion_y_la_anterior():
    nadie = [SimpleNamespace(tiene_hacha=False, etapa=0)] * 60
    assert renglones_del_puzzle(nadie, []) == ([NADIE_TODAVIA], None)
    historia = _corrida(11).historia
    esta, anterior = renglones_del_puzzle(_agentes(), historia)
    assert esta == ["Con hacha: 3", "Llave roja: 2"]
    assert anterior == (1, "Gen 11: 5 agentes con llave roja")
    historia[-1]["agentes_llave_roja"] = 0
    assert renglones_del_puzzle(nadie, historia)[1] == (0, "Gen 11: nadie agarró la llave roja")
    historia[-1].update(agentes_llave_roja=3, agentes_puerta_madera=1)
    assert renglones_del_puzzle(nadie, historia)[1] == (2, "Gen 11: 1 agente abrió la puerta de madera")


# --- Los avisos (decisiones 11 y 12) ---

class Reloj:
    """Un reloj que avanza a mano, en milisegundos."""

    def __init__(self):
        self.ahora = 0

    def __call__(self):
        return self.ahora


def _hito(paso, generacion=2):
    return {"paso": paso, "generacion": generacion, "tick": 498, "agente": 12}


def test_el_aviso_de_generacion_dura_2_5_segundos():
    reloj = Reloj()
    pila = PilaDeAvisos(reloj)
    pila.avisar_generacion(_corrida(11).historia)
    reloj.ahora = 2400
    (tipo, queda, titulo, _), = pila.vigentes()
    assert (tipo, titulo) == ("generacion", "Generación 11 terminada")
    assert queda == pytest.approx(0.04)
    reloj.ahora = 2600
    assert pila.vigentes() == []


def test_el_aviso_de_hito_dura_4_segundos():
    reloj = Reloj()
    pila = PilaDeAvisos(reloj)
    pila.avisar_hito(_hito(1))
    reloj.ahora = 3900
    assert pila.vigentes() == [("hito", 1, "¡Primera llave roja!", "Un agente la agarró en la generación 2")]
    reloj.ahora = 4100
    assert pila.vigentes() == []


def test_los_avisos_se_apilan_en_orden_y_no_hay_mas_de_3_hitos():
    reloj = Reloj()
    pila = PilaDeAvisos(reloj)
    for paso in (1, 2, 3):
        pila.avisar_hito(_hito(paso))
        reloj.ahora += 100
    pila.avisar_generacion(_corrida(2).historia)
    # El de generación arriba; debajo los hitos, el más nuevo último
    assert [(aviso[0], aviso[1]) for aviso in pila.vigentes()][1:] == [("hito", 1), ("hito", 2), ("hito", 3)]
    assert pila.vigentes()[0][0] == "generacion"
    pila.avisar_hito(_hito(4))
    assert [aviso[1] for aviso in pila.vigentes()[1:]] == [2, 3, 4]  # Se fue el más viejo


def test_los_subtitulos_de_los_cinco_hitos():
    assert [modulo_avisos.textos_de_hito(_hito(paso, 7)) for paso in range(1, 6)] == [
        ("¡Primera llave roja!", "Un agente la agarró en la generación 7"),
        ("¡Primera puerta abierta!", "Un agente abrió la de madera en la generación 7"),
        ("¡Primera llave dorada!", "Un agente la agarró en la generación 7"),
        ("¡Puerta de hierro abierta!", "Un agente la abrió en la generación 7"),
        ("¡Cofre abierto!", "Un agente lo abrió en la generación 7"),
    ]


def test_el_aviso_de_generacion_compara_contra_la_anterior():
    anterior = _fila(10, fitness_prom=30.1, manzanas_prom=1.2)
    fila = _fila(11, fitness_prom=31.2, manzanas_prom=1.1)
    titulo, segmentos = textos_de_generacion(fila, anterior)
    assert titulo == "Generación 11 terminada"
    assert "".join(texto for texto, _ in segmentos) == \
        "Fitness promedio 31,2 +1,1 · Manzanas por agente 1,10 −0,10"
    assert [estilo for texto, estilo in segmentos if texto.startswith(" ") and texto.strip()[0] in "+−"] == \
        ["sube", "baja"]
    # La generación 1 va sin diferencias
    assert "".join(t for t, _ in textos_de_generacion(fila, None)[1]) == \
        "Fitness promedio 31,2 · Manzanas por agente 1,10"


def test_los_avisos_se_dibujan(sprites):
    reloj = Reloj()
    pila = PilaDeAvisos(reloj)
    pila.avisar_generacion(_corrida(2).historia)
    for paso in range(1, 6):
        pila.avisar_hito(_hito(paso))
    superficie = pygame.Surface((1200, 800))
    superficie.fill((0, 0, 0))
    pila.dibujar(superficie, sprites)
    # Arriba y al centro del mundo, 440 px de ancho
    assert superficie.get_at((480, 30))[:3] != (0, 0, 0)
    assert superficie.get_at((250, 30))[:3] == (0, 0, 0)


def test_con_ventana_no_hay_aviso_despues_de_la_ultima_generacion(sprites, monkeypatch):
    # La corrida de verdad, con ventana (en el driver dummy) y 3 generaciones cortas: hay aviso al
    # terminar la 1 y la 2, no al terminar la 3, que tiene la pantalla final
    import main  # noqa: E402 (main importa pygame y todo el resto)
    for nombre, valor in {"HEADLESS_MODE": False, "MAX_GENERATIONS": 3, "BASE_TICKS": 3,
                          "TARGET_FPS": 100_000}.items():
        monkeypatch.setattr(SimulationConfig, nombre, valor)
    avisadas = []
    monkeypatch.setattr(PilaDeAvisos, "avisar_generacion",
                        lambda self, historia: avisadas.append(historia[-1]["generacion"]))
    finales = []
    monkeypatch.setattr(main, "mostrar_pantalla_final", lambda *args: finales.append(args[1]))
    main._simular(7, True, lambda fila: None)
    assert (avisadas, finales) == ([1, 2], [3])


# --- La pantalla final (decisión 14) ---

@pytest.mark.parametrize("registro", [pytest.param(armar, id=nombre) for nombre, armar in CORRIDAS.items()])
def test_la_pantalla_final_se_dibuja_sin_pisar_el_pie(sprites, registro):
    superficie = pygame.Surface((1200, 800))
    abajo, pie = dibujar_boletin(superficie, registro(), FORTALEZAS, sprites)
    assert abajo <= pie - 4


def test_cada_mapa_dibuja_las_fortalezas_de_su_generacion(sprites, monkeypatch):
    """Con las fortalezas móviles, el mapa de la generación 1 y el de la última tienen las suyas; un
    registro que no las guardó usa las del mundo."""
    from src.ui import pantalla_final
    dibujadas = []
    original = pantalla_final.mapa_de_calor

    def mapa(registro, grilla, maximo, fortalezas):
        dibujadas.append(fortalezas)
        return original(registro, grilla, maximo, fortalezas)

    monkeypatch.setattr(pantalla_final, "mapa_de_calor", mapa)
    registro = _corrida(2)
    primera, ultima = [{"x": 50, "y": 50, "size": 5}], [{"x": 300, "y": 200, "size": 5}]
    registro.calor_gen1["fortalezas"], registro.calor_ultima["fortalezas"] = primera, ultima
    dibujar_boletin(pygame.Surface((1200, 800)), registro, FORTALEZAS, sprites)
    assert dibujadas == [primera, ultima]

    dibujadas.clear()
    dibujar_boletin(pygame.Surface((1200, 800)), _corrida(2), FORTALEZAS, sprites)
    del_mundo = [FORTALEZAS.small_fortress_pos, FORTALEZAS.large_fortress_pos]
    assert dibujadas == [del_mundo, del_mundo]


def test_el_grafico_marca_cada_paso_alcanzado_en_su_primera_generacion():
    assert marcas_del_grafico(armar_boletin(_corrida(30))) == [(2, "1ª llave roja · gen 2")]
    assert marcas_del_grafico(armar_boletin(_corrida(30, cofre=True))) == [
        (2, "1ª llave roja · gen 2"), (3, "1ª puerta de madera · gen 3"), (3, "1ª llave dorada · gen 3"),
        (3, "1ª puerta de hierro · gen 3"), (3, "1er cofre · gen 3")]
    assert marcas_del_grafico(armar_boletin(_corrida(1))) == []
