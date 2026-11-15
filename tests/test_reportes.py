"""
Tests de los reportes que mentían (spec LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO, decisión 18).

Usan agentes de mentira: los reportes solo leen atributos, así que no hace falta correr la
simulación.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.analytics.learning_monitor import LearningMonitor  # noqa: E402
from src.ui.pantalla_final import textos_del_cuadro  # noqa: E402

# Los textos que decían que se había completado la misión aunque el cofre siguiera cerrado (el
# "Cofre: SI" de antes pasó a ser la cantidad de agentes, spec MODO_GUIADO_Y_AUTONOMO, bloque B)
MISION_CUMPLIDA = ["Resultado: Completado", "Primera vez con cofre abierto: Gen 2",
                   "¡Los agentes evolutivos han completado su misión!"]


def _agente(i, vivo=True, etapa=0):
    """Un agente con los atributos que leen el monitor, el clustering y la pantalla final."""
    return SimpleNamespace(
        id=1000 + i, alive=vivo, fitness=float(10 + i % 7), food_eaten=i % 4, age=900 + i,
        distance_traveled=float(100 * (i % 5)), total_moves=10, metric_sr=0.3, etapa=etapa,
        brain=SimpleNamespace(weights=[np.full((2, 2), float(i))], biases=[np.zeros(2)]),
    )


@pytest.mark.parametrize("vivos, tasa", [(60, "100.0%"), (45, "75.0%")])
def test_la_supervivencia_divide_por_los_agentes_de_la_generacion(capsys, vivos, tasa):
    # DIAG-14: dividía por 50 fijo, así que 60 agentes vivos daban "Tasa: 120.0%"
    agentes = [_agente(i, vivo=i < vivos) for i in range(60)]
    monitor = LearningMonitor()
    # Generación 5: la que imprime el análisis detallado, y sin clustering (va cada 3)
    gen_data = monitor.record_generation(5, agentes, world=None)
    monitor.print_generation_summary(gen_data)
    assert f"Tasa: {tasa}" in capsys.readouterr().out


def _etapa(i, cofre_abierto):
    """En la última generación, 10 agentes tienen la llave roja y 4 abrieron la puerta de madera;
    con cofre, 3 de esos 4 lo abrieron."""
    if cofre_abierto and i < 3:
        return 5
    return 2 if i < 4 else 1 if i < 10 else 0


def _renglones_del_cuadro(cofre_abierto, id_del_top=None):
    """Todos los textos del cuadro final de una corrida de 2 generaciones (1.920 ticks). Con cofre,
    se abrió por primera vez en la generación 2. id_del_top cambia el id del agente de más fitness
    (el 6: fitness 16)."""
    agentes = [_agente(i, etapa=_etapa(i, cofre_abierto)) for i in range(60)]
    if id_del_top is not None:
        agentes[6].id = id_del_top
    monitor = LearningMonitor()
    for generacion in (1, 2):
        monitor.record_generation(generacion, agentes, world=None)
    textos = textos_del_cuadro(2, agentes, monitor, ticks_totales=1920,
                               primera_generacion_cofre=2 if cofre_abierto else None,
                               agentes_con_cofre=3 if cofre_abierto else 0)
    renglones = [textos["titulo"], textos["subtitulo"], *textos["encabezado"]]
    for titulo, lineas in textos["secciones"]:
        renglones += [titulo, *(texto for texto, _ in lineas)]
    return renglones + [textos["mensaje_final"]]


def test_sin_cofre_el_cuadro_no_dice_que_se_completo_la_mision():
    # DIAG-16: los cuatro textos salían igual con el cofre cerrado
    renglones = _renglones_del_cuadro(cofre_abierto=False)
    for texto in MISION_CUMPLIDA:
        assert texto not in renglones
    assert not any("complet" in renglon.lower() for renglon in renglones), renglones
    assert "El cofre no se abrió en ninguna generación" in renglones


def test_con_cofre_el_cuadro_dice_que_se_completo_la_mision():
    renglones = _renglones_del_cuadro(cofre_abierto=True)
    for texto in MISION_CUMPLIDA:
        assert texto in renglones
    assert "Agentes que abrieron el cofre en la corrida: 3" in renglones


@pytest.mark.parametrize("cofre_abierto, renglon_2, renglon_3", [
    (False, "Llave roja: 10   Puerta madera: 4   Llave dorada: 0", "Puerta hierro: 0   Cofre: 0"),
    (True, "Llave roja: 10   Puerta madera: 4   Llave dorada: 3", "Puerta hierro: 3   Cofre: 3"),
])
def test_los_pasos_clave_cuentan_agentes_no_el_estado_del_mundo(cofre_abierto, renglon_2, renglon_3):
    # MODOS-17: el puzzle es de cada agente; antes decía SI o NO según el estado del mundo
    renglones = _renglones_del_cuadro(cofre_abierto)
    i = renglones.index("PASOS CLAVE")
    assert renglones[i + 2:i + 4] == [renglon_2, renglon_3]


def test_el_cuadro_muestra_el_tiempo_simulado():
    # DIAG-15: el mismo número que el resumen por consola. Está en el encabezado y en la línea de tiempo
    assert _renglones_del_cuadro(cofre_abierto=False).count("Tiempo simulado: 0.5 min") == 2


def test_la_corrida_remite_a_la_linea_base_y_la_pantalla_no_usa_la_flecha():
    # Decisión 25 (MODOS-25): "¿APRENDIERON?" comparaba contra la generación 1, que no prueba nada
    # (LEC-001); y la fuente de pygame dibuja el "→" como un cuadrado. Fitness promedio 12,9 y 1,5
    # manzanas por agente, iguales en las dos generaciones
    renglones = _renglones_del_cuadro(cofre_abierto=False)
    assert "¿APRENDIERON?" not in renglones
    i = renglones.index("LA CORRIDA")
    assert renglones[i + 1:i + 4] == [
        "Fitness prom.: gen 1 12.9 -> últimas 2 12.9",
        "Manzanas por agente: gen 1 1.5 -> últimas 2 1.5",
        "Si aprendieron se mide contra la línea base: python experimento.py"]
    assert not any("→" in renglon for renglon in renglones)


def test_el_top_agente_muestra_el_id_entero():
    # Decisión 24: el id es el contador de la corrida; antes se recortaba a los últimos 4 dígitos
    renglones = _renglones_del_cuadro(cofre_abierto=False, id_del_top=12345)
    i = renglones.index("TOP AGENTE")
    assert renglones[i + 1].startswith("Agente #12345: ")
