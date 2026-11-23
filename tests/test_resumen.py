"""
Test del resumen de experimento.py, con CSV armados a mano y números redondos.

El resumen es lo que produce las conclusiones del experimento: si cuenta mal, la conclusión es
falsa (spec MEDIR_ANTES_DE_TOCAR, decisión 16). Los modos y las tres comparaciones son del spec
MODO_GUIADO_Y_AUTONOMO, decisión 29; la puerta de madera, la llave roja por 1.000 px, el criterio del
ítem 5 y las ayudas, del spec PUZZLE_APRENDIBLE, decisiones 12 y 13.
"""

import csv
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import experimento  # noqa: E402

COLUMNAS = [
    "semilla", "evolucion", "modo", "acercarse", "generacion", "etapa_inicial", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "edad_prom", "distancia_prom", "diversidad",
    "arboles_cortados", "agentes_llave_roja", "agentes_puerta_madera", "agentes_llave_dorada",
    "agentes_puerta_hierro", "agentes_cofre",
]


def _escribir_corrida(carpeta, semilla, evolucion, fitness, manzanas, puzzle_final=(0, 0, 0, 0, 0),
                      edades=None, puzzle=None, modo="guiado", distancias=None, acercarse=0,
                      curriculo_hasta=0):
    """Escribe un CSV como el de main.py. fitness, manzanas, edades, distancias y puzzle traen un
    valor por generación; cada valor de puzzle son las cinco columnas agentes_*. Las generaciones 1 a
    curriculo_hasta nacen con la llave roja (etapa_inicial 1).

    Sin puzzle, las columnas agentes_* valen 0 en todas las generaciones menos la última, que lleva
    puzzle_final. Las columnas que el resumen no mira van en 0, y edad_prom y distancia_prom también
    si no se pasan.
    """
    ruta = carpeta / f"s{semilla}_{modo}_{int(evolucion)}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for i, (fit, manz) in enumerate(zip(fitness, manzanas)):
            fila = dict.fromkeys(COLUMNAS, 0)
            fila.update(semilla=semilla, evolucion=int(evolucion), modo=modo, generacion=i + 1,
                        fitness_prom=fit, manzanas_prom=manz, acercarse=acercarse,
                        etapa_inicial=int(i < curriculo_hasta))
            if edades:
                fila.update(edad_prom=edades[i])
            if distancias:
                fila.update(distancia_prom=distancias[i])
            if puzzle:
                fila.update(zip(COLUMNAS[-5:], puzzle[i]))
            elif i == len(fitness) - 1:
                fila.update(zip(COLUMNAS[-5:], puzzle_final))
            escritor.writerow(fila)
    return ruta


def _corrida(carpeta, semilla, evolucion, fitness_dif, manzanas_dif, edad_final=0, modo="guiado",
             llave_roja=None, puerta_madera=0, distancia=0):
    """Corrida de 10 generaciones: fitness 20 y manzanas 1 en las 5 primeras, más la diferencia en
    las 5 últimas; edad 0 en las 5 primeras y edad_final en las 5 últimas; distancia_prom igual en
    todas.

    Sin llave_roja, 1 agente llega a la puerta de madera en la última generación (llave roja de las
    últimas 5: 0,2). Con llave_roja, ese es el número de agentes con llave roja en cada una de las 5
    últimas, y puerta_madera el de los que además abrieron la puerta (un número para las 5, o una
    lista con uno por generación); nadie pasa de ahí.
    """
    puertas = puerta_madera if isinstance(puerta_madera, list) else [puerta_madera] * 5
    puzzle = (None if llave_roja is None
              else [(0, 0, 0, 0, 0)] * 5 + [(llave_roja, puerta, 0, 0, 0) for puerta in puertas])
    ruta = _escribir_corrida(carpeta, semilla, evolucion,
                             fitness=[20] * 5 + [20 + fitness_dif] * 5,
                             manzanas=[1] * 5 + [1 + manzanas_dif] * 5,
                             puzzle_final=(1, 1, 1, 0, 0),
                             edades=[0] * 5 + [edad_final] * 5,
                             puzzle=puzzle, modo=modo, distancias=[distancia] * 10)
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
                             + [(8 + i, i % 3, 1, 0, 0) for i in range(5)],
                             distancias=[100] * 7 + [400, 450, 500, 550, 600],
                             modo="autonomo")
    resumen = experimento.resumir_corrida(ruta)

    assert resumen["semilla"] == 3
    assert resumen["modo"] == "autonomo"
    assert resumen["evolucion"] is True
    assert resumen["acercarse"] is False
    # Puerta de madera en las últimas 5: 0, 1, 2, 0, 1. Llave roja por 1.000 px: 10 / 500 × 1.000
    assert resumen["puerta_madera"] == pytest.approx(0.8)
    assert resumen["llave_roja_por_1000"] == pytest.approx(20)
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
    for clave in ("fitness_inicio", "fitness_final", "fitness_dif", "manzanas_inicio", "manzanas_final",
                  "manzanas_dif", "supervivencia", "llave_roja", "puerta_madera", "llave_roja_por_1000"):
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

    # Sin distancia, la llave roja por 1.000 px no se puede calcular: no entra en ninguna comparación
    assert experimento.comparar_evolucion(corridas, "guiado") == {
        "fitness": (2, 3), "manzanas": (2, 3), "llave_roja": (1, 3), "puerta_madera": (0, 3),
        "llave_roja_por_1000": (0, 0)}
    # El autónomo no tiene ninguna semilla con las dos corridas
    assert experimento.comparar_evolucion(corridas, "autonomo") == {
        "fitness": (0, 0), "manzanas": (0, 0), "llave_roja": (0, 0), "puerta_madera": (0, 0),
        "llave_roja_por_1000": (0, 0)}


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
    # Las tres comparaciones, el autónomo primero (la pregunta 1). La llave roja y la puerta de madera
    # empatan (0,2 en todas); sin distancia, la llave roja por 1.000 px no se compara
    autonomo = ("- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 1 de 1 "
                "semillas, en manzanas por agente en 0 de 1, y tuvo más agentes con llave roja en las "
                "últimas 5 en 0 de 1, más con la puerta de madera abierta en 0 de 1 y más llave roja por "
                "1.000 px en 0 de 0.")
    guiado = ("- **Guiado, con evolución contra sin:** la evolución subió más en fitness en 1 de 1 "
              "semillas, en manzanas por agente en 1 de 1, y tuvo más agentes con llave roja en las "
              "últimas 5 en 0 de 1, más con la puerta de madera abierta en 0 de 1 y más llave roja por "
              "1.000 px en 0 de 0.")
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
    assert "| 1.00 | 2.00 | 1.00 | 950 | 0.20 | 0.20 | — | 3 | — |" in texto
    assert "**Ayudas prendidas:** ninguna." in texto
    assert ("- Semilla 2, autonomo, sin evolución: salió con código 1. Log: "
            "`results/x/corrida_s2_autonomo_sin_evolucion.log`") in texto


def _criterio(tmp_path, puertas, por_1000=None):
    """Corridas del autónomo: por semilla, (puerta de madera con evolución, sin evolución). La llave
    roja vale 5 en todas; la distancia, 1.000 px, o la de por_1000: (con, sin) por semilla."""
    corridas = []
    for semilla, (con, sin) in enumerate(puertas, start=1):
        distancias = por_1000[semilla - 1] if por_1000 else (1000, 1000)
        for evolucion, puerta, distancia in ((True, con, distancias[0]), (False, sin, distancias[1])):
            corridas.append(_corrida(tmp_path, semilla, evolucion, fitness_dif=0, manzanas_dif=0,
                                     modo="autonomo", llave_roja=5, puerta_madera=puerta,
                                     distancia=distancia))
    return corridas


def test_el_criterio_del_item_5(tmp_path):
    # Decisión 13: al menos 1 por generación con evolución y más que la línea base, en 4 de 5. La
    # semilla 3 no llega a 1 (0,8) aunque supera a su línea base; la 4 empata en 1: no cuentan
    puertas = [(1, 0), (2, 1), ([1, 1, 1, 1, 0], 0), (1, 1), (3, 0)]
    # Llave roja por 1.000 px: 5 / 500 × 1.000 = 10 contra 5 / 1.000 × 1.000 = 5 en las semillas 1 y 2
    por_1000 = [(500, 1000), (500, 1000), (1000, 1000), (1000, 500), (1000, 1000)]
    corridas = _criterio(tmp_path, puertas, por_1000)
    assert experimento.criterio_puerta_de_madera(corridas) == (3, 5)
    comparacion = experimento.comparar_evolucion(corridas, "autonomo")
    assert comparacion["puerta_madera"] == (4, 5)
    assert comparacion["llave_roja_por_1000"] == (2, 5)
    texto = experimento.resumen_markdown(corridas, [], "python experimento.py --modos autonomo")
    assert ("- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por "
            "generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 3 "
            "de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 2 de 5. Cada "
            "uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no."
            ) in texto
    # La del guiado no tiene criterio
    assert texto.count("Criterio del ítem 5") == 1
    # Por corrida: la puerta de madera y la llave roja por 1.000 px de la semilla 1
    assert "| 1 | autonomo | Con evolución | 10 |" in texto
    assert "| 5.00 | 1.00 | 10.00 | 2 | — |" in texto

    puertas[2] = ([1, 1, 2, 1, 1], 0)  # la semilla 3 pasa a cumplir (1,2): 4 de 5
    por_1000 = [(500, 1000)] * 4 + [(1000, 1000)]
    texto = experimento.resumen_markdown(_criterio(tmp_path, puertas, por_1000), [], "")
    assert "en 4 de 5 semillas" in texto
    assert "**El autónomo aprende a pasar la puerta de madera: sí.** Secundario: sí." in texto


def test_el_criterio_fuera_de_las_5_semillas_no_se_aplica(tmp_path):
    texto = experimento.resumen_markdown(_criterio(tmp_path, [(2, 0)] * 4), [], "")
    assert "en 4 de 4 semillas" in texto
    assert "**No se aplica:** el criterio es sobre 5 semillas." in texto
    assert "aprende a pasar la puerta de madera: sí" not in texto


def test_el_resumen_dice_las_ayudas_prendidas(tmp_path):
    ruta = _escribir_corrida(tmp_path, semilla=1, evolucion=True, fitness=[10] * 10,
                             manzanas=[1] * 10, modo="autonomo", acercarse=1)
    corrida = experimento.resumir_corrida(ruta)
    assert corrida["acercarse"] is True
    assert corrida["curriculo"] is False
    texto = experimento.resumen_markdown([corrida], [], "python experimento.py --acercarse")
    assert "**Ayudas prendidas:** recompensa por acercarse." in texto
    texto = experimento.resumen_markdown([corrida], [], "", acercarse_camino=True)  # viene del flag
    assert "**Ayudas prendidas:** recompensa por acercarse, por el camino." in texto

    # El currículo se ve en etapa_inicial: alguna generación nació con la llave roja
    ruta = _escribir_corrida(tmp_path, semilla=2, evolucion=True, fitness=[10] * 10,
                             manzanas=[1] * 10, modo="autonomo", curriculo_hasta=3)
    solo_curriculo = experimento.resumir_corrida(ruta)
    assert (solo_curriculo["acercarse"], solo_curriculo["curriculo"]) == (False, True)
    texto = experimento.resumen_markdown([solo_curriculo], [], "python experimento.py --curriculo")
    assert "**Ayudas prendidas:** currículo." in texto
    texto = experimento.resumen_markdown([corrida, solo_curriculo], [], "")
    assert "**Ayudas prendidas:** recompensa por acercarse y currículo." in texto


def test_el_resumen_marca_las_corridas_con_el_curriculo_en_las_ultimas_5(tmp_path):
    # Decisión 12: de 10 generaciones, las últimas 5 son la 6 a la 10. Con el currículo hasta la 5,
    # son todas del puzzle de hoy; hasta la 6, no
    hasta_la_5, hasta_la_6 = [
        experimento.resumir_corrida(_escribir_corrida(tmp_path, semilla=1, evolucion=evolucion,
                                                      fitness=[10] * 10, manzanas=[1] * 10,
                                                      modo="autonomo", curriculo_hasta=hasta))
        for hasta, evolucion in ((5, True), (6, False))]
    assert hasta_la_5["ultimas_con_curriculo"] is False
    assert hasta_la_6["ultimas_con_curriculo"] is True
    texto = experimento.resumen_markdown([hasta_la_5, hasta_la_6], [], "")
    assert ("**Corridas con generaciones del currículo entre las últimas 5** (no son todas del puzzle "
            "de hoy: alguna nació con la llave roja):\n\n- Semilla 1, autonomo, sin evolución.\n") in texto
    assert "Semilla 1, autonomo, con evolución." not in texto
    # Sin ninguna marcada, no hay sección
    assert "Corridas con generaciones del currículo" not in experimento.resumen_markdown([hasta_la_5], [], "")


def test_con_un_solo_modo_no_se_comparan_los_modos(tmp_path):
    corridas = [_corrida(tmp_path, 1, True, fitness_dif=10, manzanas_dif=1.0),
                _corrida(tmp_path, 1, False, fitness_dif=2, manzanas_dif=0.5)]
    texto = experimento.resumen_markdown(corridas, [], "python experimento.py --modos guiado")

    assert "- **Guiado, con evolución contra sin:**" in texto
    assert "Autónomo, con evolución" not in texto
    assert "Guiado contra autónomo" not in texto
