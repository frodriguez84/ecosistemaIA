"""
Tests de las fuentes (spec PANTALLAS_VER_APRENDER, decisiones 13 y 17): los archivos y sus licencias
están, y cada carácter de los textos de pantalla existe en la fuente que lo dibuja.

Un carácter que la fuente no tiene se dibuja con el glifo de reemplazo, el mismo para todos: se
detecta comparando su dibujo con el de un carácter que seguro no está (U+0378, sin asignar).
`Font.metrics()` no sirve: devuelve las medidas del glifo de reemplazo.
"""

import sys
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.analytics.boletin import TITULOS_DE_HITOS, armar_boletin  # noqa: E402
from src.ui import fuentes  # noqa: E402
from test_boletin import _con_cofre, _fila, _registro, _siete_generaciones  # noqa: E402

CARPETA = RAIZ / "assets" / "fonts"
SIN_ASIGNAR = "͸"

# Los títulos van con Pixelify Sans: no pueden llevar "→", que esa fuente no tiene
TITULOS = [
    "Ecosistema", "Corrida terminada", "FITNESS POR GENERACIÓN", "MANZANAS POR AGENTE", "PUZZLE",
    "FITNESS PROMEDIO", "EDAD PROMEDIO", "RECORRIDO PROMEDIO", "POR DÓNDE CAMINARON", "MEJOR AGENTE",
    "PUZZLE: CUÁNTOS LLEGARON A CADA PASO EN LA ÚLTIMA GENERACIÓN",
]
# Los textos fijos del panel, de los avisos y de la pantalla final (decisiones 9, 11, 12 y 14), con
# números de ejemplo. El bloque B los reemplaza por los de sus módulos
TEXTOS_FIJOS = [
    "Generación", "12 de 30", "Modo", "guiado", "autónomo", "Tiempo", "00:00", "Vivos", "Muertos",
    "Comida", "Promedio", "Máximo", "Máx. 64,7", "Prom. 39,7", "G1", "G11", "Esta generación:",
    "nadie todavía", "agentes con hacha", "Gen 11: 2 agentes con llave roja",
    "Gen 11: nadie agarró la llave roja", "ESPACIO pausa", "+ − zoom", "ESC salir",
    "Se dibuja al terminar la generación 1", "Generación 11 terminada",
    "Fitness promedio 31,2 +1,1 · Manzanas por agente 1,10 −0,18", *TITULOS_DE_HITOS,
    "Un agente la agarró en la generación 2", "Un agente abrió la de madera en la generación 2",
    "Un agente la abrió en la generación 2", "Un agente lo abrió en la generación 2",
    "Hasta dónde llegaron:", "1ª llave roja · gen 2", "poco tiempo", "mucho", "ESC o ENTER para salir",
    "PAUSADO - Presiona ESPACIO", "0,5", "1,5", "−5", "125",
]


@pytest.fixture(scope="module", autouse=True)
def _pygame_font():
    pygame.font.init()
    yield
    pygame.font.quit()


def _dibujo(fuente, caracter):
    superficie = fuente.render(caracter, True, (255, 255, 255), (0, 0, 0))
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


@pytest.mark.parametrize("papel", ["texto", "seminegrita", "negrita"])
def test_cada_caracter_del_resto_esta_en_inter(papel):
    fuente = fuentes.fuente(papel, 14)
    textos = _textos_del_boletin() + TEXTOS_FIJOS + TITULOS
    assert "→" in "".join(textos) and "×" in "".join(textos) and "−" in "".join(textos)
    for texto in textos:
        assert faltan(fuente, texto) == [], texto
