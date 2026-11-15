"""
Test del resumen de experimento.py, con CSV armados a mano y números redondos.

El resumen es lo que produce las conclusiones del experimento: si cuenta mal, la conclusión es
falsa (spec MEDIR_ANTES_DE_TOCAR, decisión 16). Los modos y las tres comparaciones son del spec
MODO_GUIADO_Y_AUTONOMO, decisión 29.
"""

import csv
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import experimento  # noqa: E402

COLUMNAS = [
    "semilla", "evolucion", "modo", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "edad_prom", "distancia_prom", "diversidad",
    "arboles_cortados", "agentes_llave_roja", "agentes_puerta_madera", "agentes_llave_dorada",
    "agentes_puerta_hierro", "agentes_cofre",
]


def _escribir_corrida(carpeta, semilla, evolucion, fitness, manzanas, puzzle_final=(0, 0, 0, 0, 0),
                      edades=None, puzzle=None, modo="guiado"):
    """Escribe un CSV como el de main.py. fitness, manzanas, edades y puzzle traen un valor por
    generación; cada valor de puzzle son las cinco columnas agentes_*.

    Sin puzzle, las columnas agentes_* valen 0 en todas las generaciones menos la última, que lleva
    puzzle_final. Las columnas que el resumen no mira van en 0, y edad_prom también si no se pasan
    edades.
    """
    ruta = carpeta / f"s{semilla}_{modo}_{int(evolucion)}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for i, (fit, manz) in enumerate(zip(fitness, manzanas)):
            fila = dict.fromkeys(COLUMNAS, 0)
            fila.update(semilla=semilla, evolucion=int(evolucion), modo=modo, generacion=i + 1,
                        fitness_prom=fit, manzanas_prom=manz)
            if edades:
                fila.update(edad_prom=edades[i])
            if puzzle:
                fila.update(zip(COLUMNAS[-5:], puzzle[i]))
            elif i == len(fitness) - 1:
                fila.update(zip(COLUMNAS[-5:], puzzle_final))
            escritor.writerow(fila)
    return ruta


def _corrida(carpeta, semilla, evolucion, fitness_dif, manzanas_dif, edad_final=0, modo="guiado",
             llave_roja=None):
    """Corrida de 10 generaciones: fitness 20 y manzanas 1 en las 5 primeras, más la diferencia en
    las 5 últimas; edad 0 en las 5 primeras y edad_final en las 5 últimas.

    Sin llave_roja, 1 agente llega a la puerta de madera en la última generación (llave roja de las
    últimas 5: 0,2). Con llave_roja, ese es el número de agentes con llave roja en cada una de las 5
    últimas, y nadie pasa de ahí.
    """
    puzzle = None if llave_roja is None else [(0, 0, 0, 0, 0)] * 5 + [(llave_roja, 0, 0, 0, 0)] * 5
    ruta = _escribir_corrida(carpeta, semilla, evolucion,
                             fitness=[20] * 5 + [20 + fitness_dif] * 5,
                             manzanas=[1] * 5 + [1 + manzanas_dif] * 5,
                             puzzle_final=(1, 1, 1, 0, 0),
                             edades=[0] * 5 + [edad_final] * 5,
                             puzzle=puzzle, modo=modo)
    return experimento.resumir_corrida(ruta)


def test_resumen_de_una_corrida(tmp_path):
    # 12 generaciones: si "las últimas 5" no fueran la 8 a la 12, los 100 de la 6 y la 7 se notarían.
    # El puzzle llega más lejos en la 6 y la 7 (etapa 4) que al final (etapa 3): la etapa máxima es
    # la de toda la corrida
    ruta = _escribir_corrida(tmp_path, semilla=3, evolucion=True,
                             fitness=[8, 9, 10, 11, 12, 100, 100, 18, 19, 20, 21, 22],
                             manzanas=[0, 0.5, 0.5, 0.5, 1, 9, 9, 1, 1.5, 1.5, 1.5, 2],
                             edades=[100] * 5 + [5000, 5000, 900, 920, 940, 960, 980],
                             puzzle=[(0, 0, 0, 0, 0)] * 5 + [(40, 9, 9, 2, 0)] * 2
                             + [(8 + i, 2, 1, 0, 0) for i in range(5)],
                             modo="autonomo")
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["semilla"] == 3
    assert resumen["modo"] == "autonomo"
    assert resumen["evolucion"] is True
    assert resumen["generaciones"] == 12
    assert resumen["fitness_inicio"] == pytest.approx(10)
    assert resumen["fitness_final"] == pytest.approx(20)
    assert resumen["fitness_dif"] == pytest.approx(10)
    assert resumen["manzanas_inicio"] == pytest.approx(0.5)
    assert resumen["manzanas_final"] == pytest.approx(1.5)
    assert resumen["manzanas_dif"] == pytest.approx(1)
    assert resumen["supervivencia"] == pytest.approx(940)  # edad_prom de las últimas 5
    assert resumen["llave_roja"] == pytest.approx(10)  # agentes_llave_roja de las últimas 5: 8 a 12
    assert resumen["etapa_maxima"] == 4
    assert resumen["generacion_cofre"] is None


def test_el_cofre_se_informa_y_con_10_generaciones_o_mas_las_ventanas_se_toman_igual(tmp_path):
    # Algún agente abre el cofre en la 7 y en la 11: cuenta la primera
    puzzle = [(0, 0, 0, 0, 0)] * 11
    puzzle[6] = puzzle[10] = (3, 2, 2, 1, 1)
    ruta = _escribir_corrida(tmp_path, semilla=1, evolucion=False,
                             fitness=[10] * 5 + [30] * 6, manzanas=[1] * 11, puzzle=puzzle)
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["evolucion"] is False
    assert resumen["generaciones"] == 11
    assert resumen["etapa_maxima"] == 5
    assert resumen["generacion_cofre"] == 7
    assert resumen["fitness_dif"] == pytest.approx(20)


def test_con_menos_de_10_generaciones_queda_fuera_de_las_ventanas(tmp_path):
    ruta = _escribir_corrida(tmp_path, semilla=1, evolucion=True,
                             fitness=[10] * 8, manzanas=[1] * 8, puzzle_final=(1, 1, 1, 1, 1))
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["generacion_cofre"] == 8
    for clave in ("fitness_inicio", "fitness_final", "fitness_dif",
                  "manzanas_inicio", "manzanas_final", "manzanas_dif", "supervivencia", "llave_roja"):
        assert resumen[clave] is None, clave


def test_resumen_por_grupo_promedio_y_desvio_entre_semillas(tmp_path):
    corridas = [_corrida(tmp_path, s, True, fitness_dif=d, manzanas_dif=0.5, edad_final=e)
                for s, d, e in [(1, 10, 900), (2, 12, 1000), (3, 14, 1100)]]
    grupo = experimento.resumir_grupo(corridas)

    assert grupo["fitness_inicio"]["promedio"] == pytest.approx(20)
    assert grupo["fitness_inicio"]["desvio"] == pytest.approx(0)
    assert grupo["fitness_final"]["promedio"] == pytest.approx(32)
    assert grupo["fitness_dif"]["promedio"] == pytest.approx(12)
    assert grupo["fitness_dif"]["desvio"] == pytest.approx(2)  # muestral: 10, 12, 14
    assert grupo["fitness_dif"]["n"] == 3
    assert grupo["manzanas_dif"]["promedio"] == pytest.approx(0.5)
    assert grupo["supervivencia"]["promedio"] == pytest.approx(1000)
    assert grupo["supervivencia"]["desvio"] == pytest.approx(100)
    assert grupo["llave_roja"]["promedio"] == pytest.approx(0.2)  # 1 agente en la última de las 5
    assert grupo["etapa_maxima"]["promedio"] == pytest.approx(3)
    assert grupo["generacion_cofre"]["n"] == 0
    assert grupo["generacion_cofre"]["promedio"] is None


def test_con_una_sola_semilla_no_hay_desvio(tmp_path):
    grupo = experimento.resumir_grupo([_corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1)])

    assert grupo["fitness_dif"]["promedio"] == pytest.approx(10)
    assert grupo["fitness_dif"]["desvio"] is None


def test_comparacion_de_la_evolucion_con_la_linea_base_en_un_modo(tmp_path):
    # Comparaciones 1 y 2 de la decisión 29
    corridas = [
        _corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0, llave_roja=4),
        _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5, llave_roja=1),
        _corrida(tmp_path, 2, True, fitness_dif=3, manzanas_dif=1.0, llave_roja=0),
        _corrida(tmp_path, 2, False, fitness_dif=4, manzanas_dif=1.0, llave_roja=0),  # empates: no cuentan
        _corrida(tmp_path, 3, True, fitness_dif=14, manzanas_dif=1.0, llave_roja=2),
        _corrida(tmp_path, 3, False, fitness_dif=6, manzanas_dif=0.25, llave_roja=3),
        # La semilla 4 no tiene línea base (su corrida falló): queda fuera de la comparación
        _corrida(tmp_path, 4, True, fitness_dif=50, manzanas_dif=5, llave_roja=9),
        # La línea base del autónomo en la semilla 1: si se mezclara con la del guiado, la semilla 1
        # dejaría de contar en las tres
        _corrida(tmp_path, 1, False, fitness_dif=50, manzanas_dif=5, llave_roja=9, modo="autonomo"),
    ]

    assert experimento.comparar_evolucion(corridas, "guiado") == {
        "fitness": (2, 3), "manzanas": (2, 3), "llave_roja": (1, 3)}
    # El autónomo no tiene ninguna semilla con las dos corridas
    assert experimento.comparar_evolucion(corridas, "autonomo") == {
        "fitness": (0, 0), "manzanas": (0, 0), "llave_roja": (0, 0)}


def test_comparacion_del_guiado_con_el_autonomo(tmp_path):
    # Comparación 3 de la decisión 29: por nivel en las últimas 5, con evolución y sin ella
    corridas = [
        # Semilla 1, con evolución: el guiado tiene más manzanas (3 contra 1,5) y más llave roja
        _corrida(tmp_path, 1, True, fitness_dif=0, manzanas_dif=2.0, llave_roja=3),
        _corrida(tmp_path, 1, True, fitness_dif=0, manzanas_dif=0.5, llave_roja=1, modo="autonomo"),
        # Semilla 2, con evolución: el autónomo come más, y la llave roja empata en 0
        _corrida(tmp_path, 2, True, fitness_dif=0, manzanas_dif=0.5, llave_roja=0),
        _corrida(tmp_path, 2, True, fitness_dif=0, manzanas_dif=1.0, llave_roja=0, modo="autonomo"),
        # Sin evolución, solo la semilla 1 tiene los dos modos
        _corrida(tmp_path, 1, False, fitness_dif=0, manzanas_dif=1.0, llave_roja=2),
        _corrida(tmp_path, 1, False, fitness_dif=0, manzanas_dif=0.0, llave_roja=0, modo="autonomo"),
        _corrida(tmp_path, 2, False, fitness_dif=0, manzanas_dif=9.0, llave_roja=9),
    ]

    assert experimento.comparar_modos(corridas, True) == {"manzanas": (1, 2), "llave_roja": (1, 2)}
    assert experimento.comparar_modos(corridas, False) == {"manzanas": (1, 1), "llave_roja": (1, 1)}


def test_el_markdown_trae_los_grupos_las_comparaciones_las_corridas_y_las_que_fallaron(tmp_path):
    corridas = [
        _corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0, edad_final=950),
        _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5),
        _corrida(tmp_path, 1, True, fitness_dif=4, manzanas_dif=0.25, modo="autonomo"),
        _corrida(tmp_path, 1, False, fitness_dif=1, manzanas_dif=0.5, modo="autonomo"),
    ]
    fallidas = [{"semilla": 2, "modo": "autonomo", "evolucion": False, "codigo": 1,
                 "log": RAIZ / "results" / "x" / "corrida_s2_autonomo_sin_evolucion.log"}]
    texto = experimento.resumen_markdown(corridas, fallidas, "python experimento.py --semillas 1 2")

    # Por grupo: la edad promedio de las últimas 5, los agentes con llave roja de las últimas 5, la
    # etapa máxima y el cofre
    assert ("| guiado | Con evolución | 1 | 20.00 | 30.00 | 10.00 | 1.00 | 2.00 | 1.00 | 950 | 0.20 "
            "| 3.0 | 0 de 1 |") in texto
    assert "| autonomo | Sin evolución | 1 | 20.00 | 21.00 | 1.00 |" in texto
    # Las tres comparaciones, el autónomo primero (la pregunta 1). La llave roja empata (0,2 en todas)
    autonomo = ("- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 1 de 1 "
                "semillas, en manzanas por agente en 0 de 1, y tuvo más agentes con llave roja en las "
                "últimas 5 en 0 de 1.")
    guiado = ("- **Guiado, con evolución contra sin:** la evolución subió más en fitness en 1 de 1 "
              "semillas, en manzanas por agente en 1 de 1, y tuvo más agentes con llave roja en las "
              "últimas 5 en 0 de 1.")
    modos = ("- **Guiado contra autónomo, en las últimas 5:** con evolución, el guiado tuvo más "
             "manzanas por agente en 1 de 1 semillas y más agentes con llave roja en 0 de 1; sin "
             "evolución, más manzanas en 0 de 1 y más agentes con llave roja en 0 de 1.")
    assert texto.index(autonomo) < texto.index(guiado) < texto.index(modos)
    # Por corrida: el guiado antes que el autónomo, con evolución antes que sin
    filas = ["| 1 | guiado | Con evolución | 10 | 20.00 | 30.00 | 10.00 |",
             "| 1 | guiado | Sin evolución | 10 | 20.00 | 22.00 | 2.00 |",
             "| 1 | autonomo | Con evolución | 10 | 20.00 | 24.00 | 4.00 |",
             "| 1 | autonomo | Sin evolución | 10 | 20.00 | 21.00 | 1.00 |"]
    posiciones = [texto.index(fila, texto.index("**Por corrida:**")) for fila in filas]
    assert posiciones == sorted(posiciones)
    assert "| 1.00 | 2.00 | 1.00 | 950 | 0.20 | 3 | — |" in texto
    assert ("- Semilla 2, autonomo, sin evolución: salió con código 1. Log: "
            "`results/x/corrida_s2_autonomo_sin_evolucion.log`") in texto


def test_con_un_solo_modo_no_se_comparan_los_modos(tmp_path):
    corridas = [_corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0),
                _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5)]
    texto = experimento.resumen_markdown(corridas, [], "python experimento.py --modos guiado")

    assert "- **Guiado, con evolución contra sin:**" in texto
    assert "Autónomo, con evolución" not in texto
    assert "Guiado contra autónomo" not in texto
