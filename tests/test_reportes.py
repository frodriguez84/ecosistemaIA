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


def _agente(i, vivo=True, etapa=0):
    """Un agente con los atributos que leen el monitor y el clustering."""
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
