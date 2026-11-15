"""
Fuentes de las pantallas (spec PANTALLAS_VER_APRENDER, decisión 13): Pixelify Sans para los títulos
e Inter para el resto, en TTF estáticos en assets/fonts/ (pygame 2.6 no elige el peso de una fuente
variable). Origen y licencia, en assets/fonts/LEEME.md.

No cae a la fuente de pygame si falta un archivo: dibujaría cuadrados en lugar de "→" o "×".
"""

import os

import pygame

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts")

# Papel de cada fuente → archivo, relativo a CARPETA
ARCHIVOS = {
    "titulo": os.path.join("pixelify-sans", "PixelifySans-Bold.ttf"),
    "texto": os.path.join("inter", "Inter-Regular.ttf"),
    "seminegrita": os.path.join("inter", "Inter-SemiBold.ttf"),
    "negrita": os.path.join("inter", "Inter-Bold.ttf"),
}

_cargadas = {}


def verificar():
    """Corta la corrida, con el nombre del archivo, si falta alguna fuente. main.py lo llama al
    arrancar con ventana."""
    for archivo in ARCHIVOS.values():
        ruta = os.path.normpath(os.path.join(CARPETA, archivo))
        if not os.path.isfile(ruta):
            raise SystemExit(f"❌ Falta la fuente {ruta} (de dónde sale: assets/fonts/LEEME.md)")


def fuente(papel, tamano):
    """La fuente de ese papel ('titulo', 'texto', 'seminegrita' o 'negrita') y tamaño, cargada una
    sola vez."""
    clave = (papel, tamano)
    if clave not in _cargadas:
        _cargadas[clave] = pygame.font.Font(os.path.join(CARPETA, ARCHIVOS[papel]), tamano)
    return _cargadas[clave]


def olvidar():
    """Vacía la caché. Una fuente cargada deja de servir cuando se cierra pygame.font (dibujar con
    ella cuelga el proceso): quien lo cierra y lo vuelve a abrir, como los tests, llama a esto."""
    _cargadas.clear()


def renglones(fuente_, texto, ancho):
    """El texto partido en renglones que entran en ese ancho, cortando entre palabras."""
    resultado, actual = [], ""
    for palabra in texto.split():
        probado = f"{actual} {palabra}" if actual else palabra
        if actual and fuente_.size(probado)[0] > ancho:
            resultado.append(actual)
            actual = palabra
        else:
            actual = probado
    return resultado + ([actual] if actual else [])
