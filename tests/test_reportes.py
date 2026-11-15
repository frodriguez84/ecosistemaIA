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

# Los cuatro textos que decían que se había completado la misión aunque el cofre siguiera cerrado
MISION_CUMPLIDA = ["Resultado: Completado", "Cofre: SI", "Primera vez con cofre abierto: Gen 2",
                   "¡Los agentes evolutivos han completado su misión!"]


def _agente(i, vivo=True):
    """Un agente con los atributos que leen el monitor y el clustering."""
    return SimpleNamespace(
        id=1000 + i, alive=vivo, fitness=float(10 + i % 7), food_eaten=i % 4, age=900 + i,
        distance_traveled=float(100 * (i % 5)), total_moves=10, metric_sr=0.3,
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


def _mundo(cofre_abierto):
    """El estado del puzzle que lee el cuadro. Sin cofre, solo se recogió la llave roja."""
    return SimpleNamespace(red_key_collected=True, gold_key_collected=cofre_abierto,
                           door=SimpleNamespace(is_open=cofre_abierto),
                           door_iron=SimpleNamespace(is_open=cofre_abierto))


def _renglones_del_cuadro(cofre_abierto):
    """Todos los textos del cuadro final de una corrida de 2 generaciones (1.920 ticks)."""
    agentes = [_agente(i) for i in range(60)]
    monitor = LearningMonitor()
    for generacion in (1, 2):
        monitor.record_generation(generacion, agentes, world=None)
    textos = textos_del_cuadro(2, agentes, _mundo(cofre_abierto), monitor,
                               ticks_totales=1920, cofre_abierto=cofre_abierto)
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
    assert "Cofre: NO" in renglones


def test_con_cofre_el_cuadro_dice_que_se_completo_la_mision():
    renglones = _renglones_del_cuadro(cofre_abierto=True)
    for texto in MISION_CUMPLIDA:
        assert texto in renglones


def test_el_cuadro_muestra_el_tiempo_simulado():
    # DIAG-15: el mismo número que el resumen por consola. Está en el encabezado y en la línea de tiempo
    assert _renglones_del_cuadro(cofre_abierto=False).count("Tiempo simulado: 0.5 min") == 2
