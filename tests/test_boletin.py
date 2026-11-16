"""
Tests del boletín de la corrida (spec PANTALLAS_VER_APRENDER, decisiones 8, 10, 14, 15 y 17): los
cuatro números, el embudo, la frase del cofre una sola vez, "murieron todos", el mejor agente, la
consola y las funciones de formato y de escala.

Arman el registro a mano, con filas del CSV de mentira: el boletín solo lee el registro.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from main import COLUMNAS_CSV  # noqa: E402
from src.analytics.boletin import (  # noqa: E402
    PIE_CON_EVOLUCION, PIE_LINEA_BASE, armar_boletin, con_signo, escala, linea_de_hito, numero,
    porcentaje, texto_de_consola, veces,
)
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402


def _fila(generacion, **valores):
    fila = dict.fromkeys(COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="guiado", generacion=generacion, ticks=960, vivos=30)
    fila.update(valores)
    return fila


def _registro(filas, ticks_max=None, mejor_etapa=1):
    """Un registro con esas filas cerradas, en orden. ticks_max: los de cada generación (960 si no)."""
    registro = RegistroDeLaCorrida(960, 800, 16)
    for i, fila in enumerate(filas):
        agente = SimpleNamespace(id=100 + i, x=50.0, y=50.0, alive=True, etapa=mejor_etapa, etapa_inicial=0,
                                 fitness=40.0 + i, food_eaten=7, distance_traveled=1515.4, age=1335)
        registro.contar_posiciones([agente])
        registro.cerrar_generacion(fila, (ticks_max or [960] * len(filas))[i], [agente])
    return registro


def _renglones(boletin):
    return texto_de_consola(boletin).splitlines()


def frases_del_cofre(renglones):
    """Los renglones que hablan del cofre, sin contar el cofre como nombre de paso (la fila del
    embudo y el paso del mejor agente). La usa también el control contra la pantalla de antes."""
    return [r for r in renglones if "cofre" in r.lower()
            and not r.strip().lower().startswith("cofre") and "llegó a: cofre" not in r]


# --- Formato (decisión 8) ---

@pytest.mark.parametrize("valor, decimales, esperado", [
    (31.2, 1, "31,2"), (2220, 0, "2.220"), (-3.5, 1, "−3,5"), (1234567.891, 2, "1.234.567,89"),
    (0.0, 1, "0,0"), (-0.04, 1, "0,0"), (1.1, 2, "1,10"),
])
def test_numero(valor, decimales, esperado):
    assert numero(valor, decimales) == esperado


def test_signos_porcentaje_y_veces():
    assert con_signo(1.1, 1) == "+1,1"
    assert con_signo(-0.4, 1) == "−0,4"
    assert con_signo(0.18, 2) == "+0,18"
    assert porcentaje(73.4) == "+73 %"
    assert porcentaje(-7.2) == "−7 %"
    assert veces(1.94) == "×1,9"


# --- Escala (decisión 10) ---

@pytest.mark.parametrize("maximo, paso, tope", [
    (75.1, 20, 80), (39.7, 10, 40), (66.0, 20, 80), (1.42, 0.5, 1.5), (0.94, 0.2, 1.0),
    (100.5, 25, 125),
])
def test_los_ejemplos_de_la_escala(maximo, paso, tope):
    assert escala([0.0, maximo / 2, maximo]) == (0, tope, paso)


def test_las_series_comparten_eje_y_todo_cero_va_de_0_a_1():
    assert escala([10.0, 20.0], [39.7]) == (0, 40, 10)
    assert escala([0.0, 0.0]) == (0, 1, 0.2)
    assert escala([]) == (0, 1, 0.2)


def test_la_escala_no_sube_un_paso_de_mas_por_la_coma_flotante():
    assert 0.1 + 0.2 != 0.3
    assert escala([0.1 + 0.2]) == (0, 0.3, 0.1)


def test_un_valor_negativo_baja_el_eje_al_multiplo_del_paso():
    assert escala([-3.0, 10.0]) == (-5, 10, 5)


# --- Los cuatro números (decisión 14 b) ---

def _siete_generaciones():
    """Gen 1 contra las últimas 5 (3 a 7); la 2 es un valor absurdo que no tiene que entrar."""
    valores = {
        1: (20.0, 0.5, 800.0, 300.0), 2: (999.0, 99.0, 9999.0, 9999.0),
        3: (30.0, 0.8, 900.0, 1000.0), 4: (32.0, 0.9, 950.0, 1100.0), 5: (34.0, 1.0, 1000.0, 1200.0),
        6: (36.0, 1.1, 1050.0, 1300.0), 7: (38.0, 1.2, 1100.0, 1400.0),
    }
    filas = [_fila(g, fitness_prom=f, manzanas_prom=m, edad_prom=e, distancia_prom=d)
             for g, (f, m, e, d) in valores.items()]
    return _registro(filas, ticks_max=[960, 960, 960, 960, 1140, 1140, 1140])


def test_los_cuatro_numeros_comparan_la_gen_1_contra_las_ultimas_5():
    fitness, manzanas, edad, recorrido = armar_boletin(_siete_generaciones())["numeros"]
    assert [d["titulo"] for d in (fitness, manzanas, edad, recorrido)] == [
        "FITNESS PROMEDIO", "MANZANAS POR AGENTE", "EDAD PROMEDIO", "RECORRIDO PROMEDIO"]
    assert (fitness["valor"], fitness["cambio"], fitness["sube"]) == ("20,0 → 34,0", "+70 %", True)
    assert (manzanas["valor"], manzanas["cambio"]) == ("0,50 → 1,00", "×2,0")
    assert (edad["valor"], edad["cambio"]) == ("800 → 1.000", "+25 %")
    assert (recorrido["valor"], recorrido["cambio"]) == ("300 → 1.200", "×4,0")
    assert fitness["nota"] == manzanas["nota"] == "gen 1 → promedio de las últimas 5"
    assert edad["nota"] == ("ticks vividos; gen 1 → promedio de las últimas 5; "
                            "sube también porque las generaciones se alargan")
    assert recorrido["nota"] == ("píxeles; gen 1 → promedio de las últimas 5; "
                                 "sube también porque las generaciones se alargan")


def test_con_3_generaciones_son_las_ultimas_2_y_sin_alargarse_no_lo_dicen():
    filas = [_fila(1, fitness_prom=20.0, edad_prom=800.0), _fila(2, fitness_prom=18.0, edad_prom=700.0),
             _fila(3, fitness_prom=18.0, edad_prom=900.0)]
    fitness, _, edad, _ = armar_boletin(_registro(filas))["numeros"]
    assert (fitness["valor"], fitness["cambio"], fitness["sube"]) == ("20,0 → 18,0", "−10 %", False)
    assert fitness["nota"] == "gen 1 → promedio de las últimas 2"
    # Las tres generaciones duran 960 ticks: decir que se alargan sería falso
    assert edad["nota"] == "ticks vividos; gen 1 → promedio de las últimas 2"


def test_con_2_generaciones_compara_contra_la_2():
    fitness = armar_boletin(_registro([_fila(1, fitness_prom=20.0), _fila(2, fitness_prom=21.0)]))["numeros"][0]
    assert (fitness["valor"], fitness["cambio"], fitness["nota"]) == ("20,0 → 21,0", "+5 %", "gen 1 → gen 2")


def test_con_1_generacion_solo_el_valor():
    boletin = armar_boletin(_registro([_fila(1, fitness_prom=21.84)]))
    assert boletin["numeros"][0] == {"titulo": "FITNESS PROMEDIO", "valor": "21,8", "cambio": None,
                                     "sube": None, "nota": "una sola generación"}
    assert len(boletin["mapas"]) == 1
    assert "1 generación ·" in boletin["subtitulo"]


def test_si_la_gen_1_vale_0_el_cambio_es_una_raya():
    filas = [_fila(1, manzanas_prom=0.0), _fila(2, manzanas_prom=0.4)]
    manzanas = armar_boletin(_registro(filas))["numeros"][1]
    assert (manzanas["valor"], manzanas["cambio"], manzanas["sube"]) == ("0,00 → 0,40", "—", None)


# --- Encabezado, embudo y cofre (decisión 14 a y e) ---

def test_el_encabezado_dice_modo_evolucion_semilla_generaciones_y_tiempo():
    boletin = armar_boletin(_registro([_fila(1), _fila(2), _fila(3)]))
    assert boletin["titulo"] == "Corrida terminada"
    assert boletin["subtitulo"] == "Modo guiado · con evolución · semilla 7 · 3 generaciones · 0,8 min simulados"
    assert boletin["pie"] == PIE_CON_EVOLUCION


def test_la_linea_base_y_el_modo_autonomo():
    filas = [_fila(g, evolucion=0, modo="autonomo") for g in (1, 2)]
    boletin = armar_boletin(_registro(filas))
    assert boletin["subtitulo"].startswith("Modo autónomo · sin evolución (línea base) · ")
    assert boletin["pie"] == PIE_LINEA_BASE
    assert PIE_LINEA_BASE in _renglones(boletin)


def test_el_embudo_es_de_la_ultima_generacion_con_la_primera_vez_de_cada_paso():
    filas = [_fila(1), _fila(2, agentes_llave_roja=3), _fila(3, agentes_llave_roja=4, agentes_puerta_madera=1),
             _fila(4, agentes_llave_roja=5)]
    boletin = armar_boletin(_registro(filas))
    assert [(p["nombre"], p["texto"]) for p in boletin["embudo"]] == [
        ("Llave roja", "5 de 60 · 1ª vez: gen 2"),
        ("Puerta de madera", "0 de 60 · 1ª vez: gen 3"),
        ("Llave dorada", "nadie, en ninguna generación"),
        ("Puerta de hierro", "nadie, en ninguna generación"),
        ("Cofre", "nadie, en ninguna generación"),
    ]
    assert boletin["embudo"][0]["fraccion"] == 5 / 60
    assert boletin["hasta_donde"] == "puerta de madera"
    assert boletin["cofre"] == "el cofre no se abrió"


def test_si_nadie_agarro_la_llave_roja():
    boletin = armar_boletin(_registro([_fila(1), _fila(2)], mejor_etapa=0))
    assert boletin["hasta_donde"] == "nadie agarró la llave roja"
    assert boletin["mejor"]["renglones"][-1] == "llegó a: ningún paso del puzzle"


def _con_cofre():
    pasos = dict(agentes_llave_roja=9, agentes_puerta_madera=6, agentes_llave_dorada=4,
                 agentes_puerta_hierro=3)
    filas = [_fila(1), _fila(2, **pasos, agentes_cofre=2), _fila(3, **pasos, agentes_cofre=1)]
    return armar_boletin(_registro(filas, mejor_etapa=5))


def test_con_cofre_la_frase_dice_la_primera_vez_y_cuantos_lo_abrieron():
    boletin = _con_cofre()
    assert boletin["hasta_donde"] == "cofre"
    assert boletin["cofre"] == ("el cofre se abrió por primera vez en la generación 2; "
                                "lo abrieron 3 agentes en la corrida")


@pytest.mark.parametrize("boletin", [
    pytest.param(lambda: _con_cofre(), id="con cofre"),
    pytest.param(lambda: armar_boletin(_registro([_fila(1), _fila(2)])), id="sin cofre"),
])
def test_la_frase_del_cofre_esta_una_sola_vez(boletin):
    renglones = _renglones(boletin())
    assert len(frases_del_cofre(renglones)) == 1, renglones


def test_un_solo_agente_con_cofre_va_en_singular():
    filas = [_fila(1, agentes_llave_roja=1, agentes_puerta_madera=1, agentes_llave_dorada=1,
                   agentes_puerta_hierro=1, agentes_cofre=1)]
    assert armar_boletin(_registro(filas))["cofre"].endswith("; lo abrió 1 agente en la corrida")


@pytest.mark.parametrize("vivos, esperado", [
    (0, "La generación 3 terminó en el tick 1.335 de 2.220: murieron todos"),
    (5, None),
])
def test_murieron_todos_solo_con_vivos_0(vivos, esperado):
    filas = [_fila(1), _fila(2), _fila(3, ticks=1335, vivos=vivos)]
    boletin = armar_boletin(_registro(filas, ticks_max=[960, 960, 2220]))
    assert boletin["murieron_todos"] == esperado
    assert any("murieron todos" in r for r in _renglones(boletin)) == (vivos == 0)


# --- Mejor agente y mapas (decisión 14 d y f) ---

def test_el_mejor_agente_con_sus_datos():
    boletin = armar_boletin(_registro([_fila(1), _fila(2), _fila(3)]))
    assert boletin["mejor"]["titulo"] == "#102 · generación 3"
    assert boletin["mejor"]["renglones"] == ["Fitness 42,0", "7 manzanas · 1.515 px de recorrido",
                                             "vivió 1.335 ticks", "llegó a: llave roja"]


def test_los_mapas_de_la_gen_1_y_la_ultima_con_su_cobertura():
    boletin = armar_boletin(_registro([_fila(1), _fila(2), _fila(3)]))
    # Un agente quieto pisa 1 de las 3.000 celdas: 0,03 %, que redondeado da 0
    assert [m["texto"] for m in boletin["mapas"]] == ["Generación 1 · 0 % del mapa",
                                                      "Generación 3 · 0 % del mapa"]


# --- La consola (decisión 15) ---

def test_la_consola_imprime_los_mismos_numeros_del_boletin():
    boletin = armar_boletin(_siete_generaciones())
    texto = texto_de_consola(boletin)
    for dato in boletin["numeros"]:
        assert dato["valor"] in texto and dato["cambio"] in texto and dato["nota"] in texto
    for paso in boletin["embudo"]:
        assert f"{paso['nombre']}: {paso['texto']}" in texto
    for renglon in [boletin["subtitulo"], boletin["mejor"]["titulo"], *boletin["mejor"]["renglones"],
                    *(m["texto"] for m in boletin["mapas"]), boletin["pie"]]:
        assert renglon in texto
    assert f"Hasta dónde llegaron: {boletin['hasta_donde']} · {boletin['cofre']}" in texto
    assert "últimas 3" not in texto


def test_la_linea_de_un_hito():
    hito = {"paso": 1, "generacion": 2, "tick": 498, "agente": 12}
    assert linea_de_hito(hito) == "🏆 ¡Primera llave roja! Agente 12, generación 2, segundo 8.3"
    assert linea_de_hito({**hito, "paso": 5}).startswith("🏆 ¡Cofre abierto! Agente 12")
