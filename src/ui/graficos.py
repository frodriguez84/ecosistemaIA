"""
Gráfico de líneas de las pantallas (spec PANTALLAS_VER_APRENDER, decisiones 9, 10 y 14 c): una o
más series por generación terminada, con la escala automática de boletin.escala, el último valor de
cada serie rotulado y, si hace falta, marcas punteadas en algunas generaciones. Lo usan el panel y la
pantalla final. No usa el azar.
"""

import pygame

from ..analytics.boletin import escala, numero
from . import fuentes

# Colores de la maqueta
TEXTO = (0xf0, 0xef, 0xec)
SECUNDARIO = (0xc3, 0xc2, 0xb7)
APAGADO = (0xa1, 0x9f, 0x96)
PROMEDIO = (0x39, 0x87, 0xe5)
MAXIMO = (0xd9, 0x59, 0x26)
MARCA = (0x6b, 0x6a, 0x64)


def x_de(indice, cantidad, izquierda, ancho):
    """La x de la generación número indice (desde 0) de cantidad. Una sola generación va a la
    izquierda, con su rótulo al lado."""
    if cantidad == 1:
        return izquierda
    return izquierda + ancho * indice / (cantidad - 1)


def rotulo_del_eje(valor):
    """El valor de una línea del eje con los decimales justos: 0 · 0,5 · 1 · 2,5 · 125."""
    for decimales in range(4):
        if abs(round(valor, decimales) - valor) < 1e-9:
            return numero(valor, decimales)
    return numero(valor, 4)


def _linea_punteada(superficie, color, x, arriba, abajo):
    for y in range(int(arriba), int(abajo), 6):
        pygame.draw.line(superficie, color, (x, y), (x, min(y + 3, abajo)))


def dibujar_grafico(superficie, rect, series, *, fondo, grilla, eje, tamano=11, prefijo="G",
                    rotulo_medio=False, marcas=()):
    """Dibuja el gráfico en rect.

    series: lista de (valores, color, rótulo del último valor, destacada), en el orden en que se
    dibujan (la última queda arriba). Todas tienen un valor por generación terminada y comparten eje.
    marcas: lista de (generación, texto): una línea punteada en esa generación, con su etiqueta
    arriba; las etiquetas se apilan, una por renglón.
    """
    fuente_eje = fuentes.fuente("texto", tamano)
    alto_texto = fuente_eje.get_height()
    cantidad = len(series[0][0])
    bajo, alto, paso = escala(*(valores for valores, *_ in series))
    divisiones = round((alto - bajo) / paso)

    rotulos_y = [fuente_eje.render(rotulo_del_eje(bajo + k * paso), True, APAGADO)
                 for k in range(divisiones + 1)]
    finales = [fuentes.fuente("seminegrita" if destacada else "texto", tamano + 1)
               .render(rotulo, True, TEXTO if destacada else SECUNDARIO)
               for _, _, rotulo, destacada in series]
    izquierda = rect.x + max(r.get_width() for r in rotulos_y) + 6
    derecha = rect.right - max(r.get_width() for r in finales) - 10
    arriba = rect.y + alto_texto // 2
    abajo = rect.bottom - alto_texto - 4
    ancho, alto_area = derecha - izquierda, abajo - arriba

    def y_de(valor):
        return abajo - alto_area * (valor - bajo) / (alto - bajo)

    # Líneas del eje: la del 0 más marcada. Si no entran todos los rótulos, uno cada tanto
    salto = 1
    while alto_area / divisiones * salto < alto_texto:
        salto += 1
    for k, rotulo in enumerate(rotulos_y):
        valor = bajo + k * paso
        y = round(y_de(valor))
        pygame.draw.line(superficie, eje if abs(valor) < 1e-9 else grilla, (izquierda, y), (derecha, y))
        if k % salto == 0:
            superficie.blit(rotulo, (izquierda - 6 - rotulo.get_width(), y - alto_texto // 2))

    # Generaciones: la primera, la del medio (si se pide) y la última
    rotulos_x = [(1, 0)] + ([((cantidad + 1) // 2, 0.5)] if rotulo_medio and cantidad >= 5 else []) \
        + ([(cantidad, 1)] if cantidad > 1 else [])
    for generacion, alineacion in rotulos_x:
        rotulo = fuente_eje.render(f"{prefijo}{generacion}", True, APAGADO)
        x = x_de(generacion - 1, cantidad, izquierda, ancho) - rotulo.get_width() * alineacion
        superficie.blit(rotulo, (round(x), abajo + 4))

    for fila, (generacion, texto) in enumerate(marcas):
        x = round(x_de(generacion - 1, cantidad, izquierda, ancho))
        _linea_punteada(superficie, MARCA, x, arriba, abajo)
        etiqueta = fuente_eje.render(texto, True, SECUNDARIO)
        x_etiqueta = x + 5 if x + 5 + etiqueta.get_width() <= rect.right else x - 5 - etiqueta.get_width()
        y_etiqueta = arriba + 2 + fila * alto_texto
        # Con fondo, para que se lea sobre las líneas de las series
        pygame.draw.rect(superficie, fondo, (x_etiqueta - 2, y_etiqueta, etiqueta.get_width() + 4, alto_texto))
        superficie.blit(etiqueta, (x_etiqueta, y_etiqueta))

    x_final = round(x_de(cantidad - 1, cantidad, izquierda, ancho))
    for valores, color, _, _ in series:
        puntos = [(round(x_de(i, cantidad, izquierda, ancho)), round(y_de(v))) for i, v in enumerate(valores)]
        if len(puntos) > 1:
            pygame.draw.lines(superficie, color, False, puntos, 2)
        pygame.draw.circle(superficie, fondo, puntos[-1], 5)
        pygame.draw.circle(superficie, color, puntos[-1], 3)

    # El último valor de cada serie, a la derecha de su punto, sin pisarse entre sí
    alturas = sorted(((y_de(valores[-1]), rotulo) for (valores, *_), rotulo in zip(series, finales)),
                     key=lambda par: par[0])
    for i in range(1, len(alturas)):
        if alturas[i][0] - alturas[i - 1][0] < alto_texto:
            alturas[i] = (alturas[i - 1][0] + alto_texto, alturas[i][1])
    for y, rotulo in alturas:
        superficie.blit(rotulo, (x_final + 8, round(y - rotulo.get_height() / 2)))
