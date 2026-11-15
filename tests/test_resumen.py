"""
Test del resumen de experimento.py, con CSV armados a mano y números redondos.

El resumen es lo que produce las conclusiones del experimento: si cuenta mal, la conclusión es
falsa (spec MEDIR_ANTES_DE_TOCAR, decisión 16).
"""

import csv
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import experimento  # noqa: E402

COLUMNAS = [
    "semilla", "evolucion", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "edad_prom", "distancia_prom", "diversidad",
    "arboles_cortados", "llave_roja", "puerta_madera", "llave_dorada", "puerta_hierro", "cofre",
]


def _escribir_corrida(carpeta, semilla, evolucion, fitness, manzanas, puzzle_final=(0, 0, 0, 0, 0),
                      edades=None):
    """Escribe un CSV como el de main.py. fitness, manzanas y edades traen un valor por generación.

    El puzzle vale 0 en todas las generaciones menos la última, que lleva puzzle_final. Las
    columnas que el resumen no mira van en 0, y edad_prom también si no se pasan edades.
    """
    ruta = carpeta / f"s{semilla}_{int(evolucion)}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for i, (fit, manz) in enumerate(zip(fitness, manzanas)):
            fila = dict.fromkeys(COLUMNAS, 0)
            fila.update(semilla=semilla, evolucion=int(evolucion), generacion=i + 1,
                        fitness_prom=fit, manzanas_prom=manz)
            if edades:
                fila.update(edad_prom=edades[i])
            if i == len(fitness) - 1:
                fila.update(zip(COLUMNAS[-5:], puzzle_final))
            escritor.writerow(fila)
    return ruta


def _corrida(carpeta, semilla, evolucion, fitness_dif, manzanas_dif, edad_final=0):
    """Corrida de 10 generaciones: fitness 20 y manzanas 1 en las 5 primeras, más la diferencia en
    las 5 últimas; edad 0 en las 5 primeras y edad_final en las 5 últimas."""
    ruta = _escribir_corrida(carpeta, semilla, evolucion,
                             fitness=[20] * 5 + [20 + fitness_dif] * 5,
                             manzanas=[1] * 5 + [1 + manzanas_dif] * 5,
                             puzzle_final=(1, 1, 1, 0, 0),
                             edades=[0] * 5 + [edad_final] * 5)
    return experimento.resumir_corrida(ruta)


def test_resumen_de_una_corrida(tmp_path):
    # 12 generaciones: si "las últimas 5" no fueran la 8 a la 12, los 100 de la 6 y la 7 se notarían
    ruta = _escribir_corrida(tmp_path, semilla=3, evolucion=True,
                             fitness=[8, 9, 10, 11, 12, 100, 100, 18, 19, 20, 21, 22],
                             manzanas=[0, 0.5, 0.5, 0.5, 1, 9, 9, 1, 1.5, 1.5, 1.5, 2],
                             puzzle_final=(1, 1, 1, 0, 0),
                             edades=[100] * 5 + [5000, 5000, 900, 920, 940, 960, 980])
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["semilla"] == 3
    assert resumen["evolucion"] is True
    assert resumen["generaciones"] == 12
    assert resumen["fitness_inicio"] == pytest.approx(10)
    assert resumen["fitness_final"] == pytest.approx(20)
    assert resumen["fitness_dif"] == pytest.approx(10)
    assert resumen["manzanas_inicio"] == pytest.approx(0.5)
    assert resumen["manzanas_final"] == pytest.approx(1.5)
    assert resumen["manzanas_dif"] == pytest.approx(1)
    assert resumen["supervivencia"] == pytest.approx(940)  # edad_prom de las últimas 5
    assert resumen["etapa_puzzle"] == 3
    assert resumen["generacion_cofre"] is None


def test_el_cofre_se_informa_y_con_10_generaciones_o_mas_las_ventanas_se_toman_igual(tmp_path):
    ruta = _escribir_corrida(tmp_path, semilla=1, evolucion=False,
                             fitness=[10] * 5 + [30] * 6, manzanas=[1] * 11,
                             puzzle_final=(1, 1, 1, 1, 1))
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["evolucion"] is False
    assert resumen["generaciones"] == 11
    assert resumen["etapa_puzzle"] == 5
    assert resumen["generacion_cofre"] == 11
    assert resumen["fitness_dif"] == pytest.approx(20)


def test_con_menos_de_10_generaciones_queda_fuera_de_las_ventanas(tmp_path):
    ruta = _escribir_corrida(tmp_path, semilla=1, evolucion=True,
                             fitness=[10] * 8, manzanas=[1] * 8, puzzle_final=(1, 1, 1, 1, 1))
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["generacion_cofre"] == 8
    for clave in ("fitness_inicio", "fitness_final", "fitness_dif",
                  "manzanas_inicio", "manzanas_final", "manzanas_dif", "supervivencia"):
        assert resumen[clave] is None, clave


def test_resumen_por_modo_promedio_y_desvio_entre_semillas(tmp_path):
    corridas = [_corrida(tmp_path, s, True, fitness_dif=d, manzanas_dif=0.5, edad_final=e)
                for s, d, e in [(1, 10, 900), (2, 12, 1000), (3, 14, 1100)]]
    modo = experimento.resumir_modo(corridas)

    assert modo["fitness_inicio"]["promedio"] == pytest.approx(20)
    assert modo["fitness_inicio"]["desvio"] == pytest.approx(0)
    assert modo["fitness_final"]["promedio"] == pytest.approx(32)
    assert modo["fitness_dif"]["promedio"] == pytest.approx(12)
    assert modo["fitness_dif"]["desvio"] == pytest.approx(2)  # muestral: 10, 12, 14
    assert modo["fitness_dif"]["n"] == 3
    assert modo["manzanas_dif"]["promedio"] == pytest.approx(0.5)
    assert modo["supervivencia"]["promedio"] == pytest.approx(1000)
    assert modo["supervivencia"]["desvio"] == pytest.approx(100)
    assert modo["etapa_puzzle"]["promedio"] == pytest.approx(3)
    assert modo["generacion_cofre"]["n"] == 0
    assert modo["generacion_cofre"]["promedio"] is None


def test_con_una_sola_semilla_no_hay_desvio(tmp_path):
    modo = experimento.resumir_modo([_corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1)])

    assert modo["fitness_dif"]["promedio"] == pytest.approx(10)
    assert modo["fitness_dif"]["desvio"] is None


def test_comparacion_pareada_por_semilla(tmp_path):
    corridas = [
        _corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0),
        _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5),
        _corrida(tmp_path, 2, True, fitness_dif=3, manzanas_dif=1.0),
        _corrida(tmp_path, 2, False, fitness_dif=4, manzanas_dif=1.0),  # empate: no cuenta
        _corrida(tmp_path, 3, True, fitness_dif=14, manzanas_dif=1.0),
        _corrida(tmp_path, 3, False, fitness_dif=6, manzanas_dif=0.25),
        # La semilla 4 no tiene línea base (su corrida falló): queda fuera de la comparación
        _corrida(tmp_path, 4, True, fitness_dif=50, manzanas_dif=5),
    ]
    comparacion = experimento.comparar_por_semilla(corridas)

    assert comparacion["fitness"] == (2, 3)
    assert comparacion["manzanas"] == (2, 3)


def test_el_markdown_trae_la_comparacion_las_corridas_y_las_que_fallaron(tmp_path):
    corridas = [
        _corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0, edad_final=950),
        _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5),
    ]
    fallidas = [{"semilla": 2, "evolucion": False, "codigo": 1,
                 "log": RAIZ / "results" / "x" / "corrida_s2_sin_evolucion.log"}]
    texto = experimento.resumen_markdown(corridas, fallidas, "python experimento.py --semillas 1 2")

    assert "subió más que la línea base en 1 de 1 semillas en fitness" in texto
    assert "y en 1 de 1 en manzanas por agente" in texto
    assert "| 1 | Con evolución | 10 | 20.00 | 30.00 | 10.00 |" in texto
    # Por modo y por corrida, la edad promedio de las últimas 5, entre las manzanas y el puzzle
    assert "| Con evolución | 1 | 20.00 | 30.00 | 10.00 | 1.00 | 2.00 | 1.00 | 950 | 3.0 | 0 de 1 |" in texto
    assert "| 1.00 | 2.00 | 1.00 | 950 | 3 | — |" in texto
    assert "results/x/corrida_s2_sin_evolucion.log" in texto
