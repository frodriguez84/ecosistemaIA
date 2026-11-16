"""
Tests de las fuentes (spec PANTALLAS_VER_APRENDER, decisiones 13 y 17): los archivos y sus licencias
están, y cada carácter de los textos de pantalla existe en la fuente que lo dibuja.

Un carácter que la fuente no tiene se dibuja con el glifo de reemplazo, el mismo para todos: se
detecta comparando su dibujo con el de un carácter que seguro no está (U+0378, sin asignar).
`Font.metrics()` no sirve: devuelve las medidas del glifo de reemplazo.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from main import PAUSADO  # noqa: E402
from src.analytics.boletin import TITULOS_DE_HITOS, armar_boletin  # noqa: E402
from src.ui import avisos, fuentes, pantalla_final, stats  # noqa: E402
from src.ui.graficos import rotulo_del_eje  # noqa: E402
from test_boletin import _con_cofre, _fila, _registro, _siete_generaciones  # noqa: E402

CARPETA = RAIZ / "assets" / "fonts"
SIN_ASIGNAR = "͸"


def _historia(**valores):
    """Las filas de 11 generaciones; la última con esos valores."""
    filas = [_fila(g) for g in range(1, 12)]
    filas[-1].update(valores)
    return filas


# Los títulos van con Pixelify Sans: no pueden llevar "→", que esa fuente no tiene
TITULOS = [stats.TITULO, _con_cofre()["titulo"], *TITULOS_DE_HITOS,
           avisos.textos_de_generacion(_fila(11), None)[0]]
TAMANOS_DE_TITULOS = [stats.TAMANO_TITULO, pantalla_final.TAMANO_TITULO,
                      avisos.TAMANO_TITULO_GENERACION, avisos.TAMANO_TITULO_HITO]


def _textos_de_las_pantallas():
    """Los textos del panel, de los avisos, de la pantalla final y del "PAUSADO" (decisiones 9, 11,
    12 y 14), sacados de sus módulos con datos de mentira."""
    mundo = SimpleNamespace(food_items=[{"eaten": False}] * 70)
    agentes = [SimpleNamespace(alive=i < 40, tiene_hacha=i < 3, etapa=5 - i if i < 5 else 0) for i in range(60)]
    textos = [stats.TITULO_FITNESS, stats.TITULO_MANZANAS, stats.TITULO_PUZZLE, stats.SIN_GRAFICOS,
              stats.ESTA_GENERACION, stats.NADIE_TODAVIA, PAUSADO]
    textos += [nombre for nombre, _ in stats.LEYENDA]
    textos += [tecla for teclas, que_hace in stats.TECLAS for tecla in (*teclas, que_hace)]
    for rotulo, valor in stats.datos_de_la_generacion(12, agentes, mundo, 3599):
        textos += [rotulo, valor]
    textos += stats.renglones_del_puzzle(agentes, [])[0]
    for paso in range(6):
        columnas = {columna: 2 if i < paso else 0
                    for i, columna in enumerate(("agentes_llave_roja", "agentes_puerta_madera",
                                                 "agentes_llave_dorada", "agentes_puerta_hierro",
                                                 "agentes_cofre"))}
        for cantidad in (1, 2):
            columnas = {c: (cantidad if v else 0) for c, v in columnas.items()}
            textos.append(stats.renglones_del_puzzle(agentes, _historia(**columnas))[1][1])
    for anterior in (None, _fila(10, fitness_prom=40.0, manzanas_prom=2.0)):
        titulo, segmentos = avisos.textos_de_generacion(_fila(11, fitness_prom=31.2, manzanas_prom=1.1), anterior)
        textos += [titulo, *(texto for texto, _ in segmentos)]
    for paso in range(1, 6):
        textos += avisos.textos_de_hito({"paso": paso, "generacion": 29, "tick": 1, "agente": 1})
    textos += [pantalla_final.TITULO_FITNESS, pantalla_final.TITULO_MANZANAS, pantalla_final.TITULO_MAPAS,
               pantalla_final.TITULO_EMBUDO, pantalla_final.TITULO_MEJOR, pantalla_final.HASTA_DONDE,
               pantalla_final.NOTA_CALOR, pantalla_final.NOTA_CALOR_MOVILES, *pantalla_final.LEYENDA_CALOR,
               *pantalla_final.SALIR]
    textos += [nombre for nombre, _ in pantalla_final.LEYENDA]
    textos += [texto for _, texto in pantalla_final.marcas_del_grafico(_con_cofre())]
    textos += ["Máx. 64,7", "Prom. 39,7", "G1", "G30", "Gen 1", "Gen 15", "Gen 30"]
    textos += [rotulo_del_eje(valor) for valor in (0, 0.2, 0.5, 1.5, 2.5, 125, -5)]
    return textos


@pytest.fixture(scope="module", autouse=True)
def _pygame_font():
    fuentes.olvidar()
    pygame.font.init()
    yield
    pygame.font.quit()
    fuentes.olvidar()


def _dibujo(fuente, caracter, suavizado=True):
    superficie = fuente.render(caracter, suavizado, (255, 255, 255), (0, 0, 0))
    return superficie.get_size(), pygame.image.tobytes(superficie, "RGB")


def faltan(fuente, texto):
    """Los caracteres del texto que la fuente no tiene."""
    reemplazo = _dibujo(fuente, SIN_ASIGNAR)
    return sorted({c for c in texto if not c.isspace() and _dibujo(fuente, c) == reemplazo})


def _textos_del_boletin():
    """Todos los textos del boletín de varias corridas de mentira: con cofre, sin cofre, línea base
    en el modo autónomo, una sola generación, muertos todos y con las generaciones alargadas."""
    boletines = [
        _con_cofre(),
        armar_boletin(_siete_generaciones()),
        armar_boletin(_registro([_fila(g, evolucion=0, modo="autonomo", manzanas_prom=0.0) for g in (1, 2)])),
        armar_boletin(_registro([_fila(1)], mejor_etapa=0)),
        armar_boletin(_registro([_fila(1), _fila(2, ticks=1335, vivos=0)], ticks_max=[960, 2220])),
    ]
    textos = []
    for b in boletines:
        textos += [b["titulo"], b["subtitulo"], b["hasta_donde"], b["cofre"], b["pie"],
                   b["mejor"]["titulo"], *b["mejor"]["renglones"], *(m["texto"] for m in b["mapas"])]
        textos += [b["murieron_todos"]] if b["murieron_todos"] else []
        for dato in b["numeros"]:
            textos += [dato["valor"], dato["nota"]] + ([dato["cambio"]] if dato["cambio"] else [])
        for paso in b["embudo"]:
            textos += [paso["nombre"], paso["texto"]]
    return textos


def test_estan_las_fuentes_sus_licencias_y_el_leeme():
    for archivo in fuentes.ARCHIVOS.values():
        assert (CARPETA / archivo).is_file(), archivo
    for familia in ("pixelify-sans", "inter"):
        licencia = (CARPETA / familia / "OFL.txt").read_text(encoding="utf-8")
        assert "SIL Open Font License, Version 1.1" in licencia, familia
    leeme = (CARPETA / "LEEME.md").read_text(encoding="utf-8")
    for archivo in fuentes.ARCHIVOS.values():
        assert Path(archivo).name in leeme


def test_si_falta_una_fuente_se_corta_con_su_nombre(monkeypatch):
    fuentes.verificar()
    monkeypatch.setitem(fuentes.ARCHIVOS, "texto", "inter/Inter-NoExiste.ttf")
    with pytest.raises(SystemExit, match="Inter-NoExiste.ttf"):
        fuentes.verificar()


def test_el_control_la_fuente_de_pygame_no_tiene_la_flecha():
    # Por esto la pantalla de antes escribía "->" (spec MODO_GUIADO_Y_AUTONOMO, decisión 25)
    assert faltan(pygame.font.Font(None, 20), "a→b") == ["→"]


def test_cada_caracter_de_los_titulos_esta_en_pixelify_sans():
    titulo = fuentes.fuente("titulo", 20)
    assert faltan(titulo, "→") == ["→"]  # Por eso no va en un título
    for texto in TITULOS:
        assert faltan(titulo, texto) == [], texto


def test_la_c_de_los_titulos_queda_abierta():
    # Pixelify Sans Bold cierra la "C" y la "c" en algunos tamaños (a 22 y 34 px, por ejemplo): se
    # leían "Eoosistema" y "Oorrida terminada"
    for tamano in TAMANOS_DE_TITULOS:
        titulo = fuentes.fuente("titulo", tamano)
        for abierta, cerrada in (("C", "O"), ("c", "o")):
            assert _dibujo(titulo, abierta, suavizado=False) != _dibujo(titulo, cerrada, suavizado=False), tamano


@pytest.mark.parametrize("papel", ["texto", "seminegrita", "negrita"])
def test_cada_caracter_del_resto_esta_en_inter(papel):
    fuente = fuentes.fuente(papel, 14)
    textos = _textos_del_boletin() + _textos_de_las_pantallas() + TITULOS
    assert "→" in "".join(textos) and "×" in "".join(textos) and "−" in "".join(textos)
    for texto in textos:
        assert faltan(fuente, texto) == [], texto
