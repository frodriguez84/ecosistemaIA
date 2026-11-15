"""
Avisos arriba del mundo (spec PANTALLAS_VER_APRENDER, decisiones 11 y 12): el fin de cada generación
y la primera vez en la corrida que un agente llega a cada paso del puzzle.

No toman clics ni teclas y no frenan nada. Duran tiempo de reloj, también en pausa; el reloj es un
parámetro, para el test. Las duraciones y medidas son de la pantalla, no de la simulación: por eso
están acá y no en config.py. No usa el azar.
"""

import pygame

from ..analytics.boletin import TITULOS_DE_HITOS, con_signo, numero
from . import fuentes
from .graficos import TEXTO, SECUNDARIO, MARCA

DURACION_GENERACION_MS = 2500
DURACION_HITO_MS = 4000
HITOS_A_LA_VEZ = 3          # Con uno más, se va el más viejo
ANCHO = 440
ARRIBA = 16
SEPARACION = 8
CENTRO_DEL_MUNDO = 480      # El mundo ocupa x de 0 a 960
# Tamaños de los títulos, en Pixelify Sans: con estos la "C" queda abierta (test_fuentes lo mira)
TAMANO_TITULO_GENERACION = 18
TAMANO_TITULO_HITO = 16

FONDO_GENERACION = (26, 26, 25, 230)
BORDE_GENERACION = (255, 255, 255, 31)
FONDO_BARRA = (0x2c, 0x2c, 0x2a)
FONDO_HITO = (0x2a, 0x24, 0x16)
BORDE_HITO = (0x6b, 0x54, 0x20)
DORADO = (0xff, 0xd2, 0x7a)
TEXTO_HITO = (0xe6, 0xdc, 0xc4)
SUBE = (0x0c, 0xa3, 0x0c)
BAJA = (0xe8, 0x8a, 0x3c)
COLORES = {"secundario": SECUNDARIO, "valor": TEXTO, "sube": SUBE, "baja": BAJA}

SUBTITULOS_DE_HITOS = (
    "Un agente la agarró en la generación {}",
    "Un agente abrió la de madera en la generación {}",
    "Un agente la agarró en la generación {}",
    "Un agente la abrió en la generación {}",
    "Un agente lo abrió en la generación {}",
)
SPRITES_DE_HITOS = ("red_key", "door", "gold_key", "door_iron", "chest")


def textos_de_generacion(fila, anterior):
    """El título y la segunda línea del aviso de fin de generación, en segmentos (texto, estilo).

    fila y anterior son filas del CSV (por columna); con anterior None (la generación 1) va sin
    diferencias. estilo: 'secundario', 'valor', 'sube' o 'baja'.
    """
    segmentos = []
    for nombre, columna, decimales in (("Fitness promedio", "fitness_prom", 1),
                                       ("Manzanas por agente", "manzanas_prom", 2)):
        separador = " · " if segmentos else ""
        segmentos += [(f"{separador}{nombre} ", "secundario"), (numero(fila[columna], decimales), "valor")]
        if anterior is not None:
            diferencia = round(fila[columna] - anterior[columna], decimales)
            estilo = "sube" if diferencia > 0 else "baja" if diferencia < 0 else "secundario"
            segmentos.append((f" {con_signo(diferencia, decimales)}", estilo))
    return f"Generación {fila['generacion']} terminada", segmentos


def textos_de_hito(hito):
    """El título y el subtítulo del aviso de un hito (decisión 12)."""
    return TITULOS_DE_HITOS[hito["paso"] - 1], SUBTITULOS_DE_HITOS[hito["paso"] - 1].format(hito["generacion"])


class PilaDeAvisos:
    """El aviso de fin de generación, arriba, y debajo los de hitos, el más nuevo último."""

    def __init__(self, reloj=None):
        self.reloj = reloj or pygame.time.get_ticks  # Milisegundos
        self._generacion = None   # (desde, título, segmentos)
        self._hitos = []          # [(desde, paso, título, subtítulo)]

    def avisar_generacion(self, historia):
        """El aviso de la última generación de la historia, contra la anterior."""
        anterior = historia[-2] if len(historia) > 1 else None
        self._generacion = (self.reloj(), *textos_de_generacion(historia[-1], anterior))

    def avisar_hito(self, hito):
        self._vencer()
        self._hitos.append((self.reloj(), hito["paso"], *textos_de_hito(hito)))
        del self._hitos[:-HITOS_A_LA_VEZ]

    def _vencer(self):
        ahora = self.reloj()
        if self._generacion and ahora - self._generacion[0] >= DURACION_GENERACION_MS:
            self._generacion = None
        self._hitos = [aviso for aviso in self._hitos if ahora - aviso[0] < DURACION_HITO_MS]

    def vigentes(self):
        """Los avisos que se ven ahora, de arriba abajo: ('generacion', fracción de tiempo que le
        queda, título, segmentos) y ('hito', paso, título, subtítulo)."""
        self._vencer()
        avisos = []
        if self._generacion:
            desde, titulo, segmentos = self._generacion
            queda = 1 - (self.reloj() - desde) / DURACION_GENERACION_MS
            avisos.append(("generacion", queda, titulo, segmentos))
        avisos += [("hito", paso, titulo, subtitulo) for _, paso, titulo, subtitulo in self._hitos]
        return avisos

    def dibujar(self, superficie, sprite_manager):
        y = ARRIBA
        for tipo, dato, titulo, resto in self.vigentes():
            if tipo == "generacion":
                tarjeta = _tarjeta_de_generacion(titulo, resto, dato)
            else:
                tarjeta = _tarjeta_de_hito(titulo, resto, sprite_manager.get_environment_sprite(
                    SPRITES_DE_HITOS[dato - 1]))
            superficie.blit(tarjeta, (CENTRO_DEL_MUNDO - ANCHO // 2, y))
            y += tarjeta.get_height() + SEPARACION


def _tarjeta_de_generacion(titulo, segmentos, queda):
    fuente_titulo, fuente_texto = fuentes.fuente("titulo", TAMANO_TITULO_GENERACION), fuentes.fuente("texto", 12)
    fuente_valor = fuentes.fuente("seminegrita", 12)
    alto = 10 + fuente_titulo.get_height() + 4 + fuente_texto.get_height() + 8 + 3 + 12
    tarjeta = pygame.Surface((ANCHO, alto), pygame.SRCALPHA)
    pygame.draw.rect(tarjeta, FONDO_GENERACION, tarjeta.get_rect(), border_radius=10)
    pygame.draw.rect(tarjeta, BORDE_GENERACION, tarjeta.get_rect(), 1, border_radius=10)
    tarjeta.blit(fuente_titulo.render(titulo, True, TEXTO), (16, 10))
    x, y = 16, 10 + fuente_titulo.get_height() + 4
    for texto, estilo in segmentos:
        fuente_ = fuente_valor if estilo == "valor" else fuente_texto
        renglon = fuente_.render(texto, True, COLORES[estilo])
        tarjeta.blit(renglon, (x, y))
        x += renglon.get_width()
    # La barra fina con el tiempo que le queda
    y_barra = alto - 12 - 3
    pygame.draw.rect(tarjeta, FONDO_BARRA, (16, y_barra, ANCHO - 32, 3), border_radius=2)
    pygame.draw.rect(tarjeta, MARCA, (16, y_barra, round((ANCHO - 32) * max(0.0, queda)), 3))
    return tarjeta


def _tarjeta_de_hito(titulo, subtitulo, sprite):
    fuente_titulo, fuente_texto = fuentes.fuente("titulo", TAMANO_TITULO_HITO), fuentes.fuente("texto", 12)
    alto = 10 + max(32, fuente_titulo.get_height() + 2 + fuente_texto.get_height()) + 10
    tarjeta = pygame.Surface((ANCHO, alto), pygame.SRCALPHA)
    pygame.draw.rect(tarjeta, FONDO_HITO, tarjeta.get_rect(), border_radius=10)
    pygame.draw.rect(tarjeta, BORDE_HITO, tarjeta.get_rect(), 1, border_radius=10)
    if sprite is not None:
        tarjeta.blit(pygame.transform.scale(sprite, (32, 32)), (14, (alto - 32) // 2))
    y = (alto - fuente_titulo.get_height() - 2 - fuente_texto.get_height()) // 2
    tarjeta.blit(fuente_titulo.render(titulo, True, DORADO), (58, y))
    tarjeta.blit(fuente_texto.render(subtitulo, True, TEXTO_HITO), (58, y + fuente_titulo.get_height() + 2))
    return tarjeta
