"""
Pantalla final: el boletín de la corrida (spec PANTALLAS_VER_APRENDER, decisiones 14 y 15). Por
consola, con ventana y sin ella; con ventana, además, en una sola pantalla sobre el último cuadro del
mundo oscurecido, hasta que se aprieta ESC o ENTER. No usa el azar.
"""

import math

import pygame

from config import SimulationConfig
from ..analytics.boletin import armar_boletin, numero, texto_de_consola
from . import fuentes
from .avisos import SPRITES_DE_HITOS, SUBE, BAJA
from .graficos import TEXTO, SECUNDARIO, APAGADO, PROMEDIO, MAXIMO, dibujar_grafico
from .renderer import dibujar_mundo

# Colores de la maqueta
FONDO_PANEL = (0x16, 0x18, 0x26)
OSCURECER = (0, 0, 0, 184)
FONDO_CUADRO = (26, 26, 25, 242)
BORDE_CUADRO = (255, 255, 255, 26)
FONDO_TARJETA = (0x22, 0x22, 0x20)
BORDE_TARJETA = (0x33, 0x33, 0x31)
GRILLA = (0x2c, 0x2c, 0x2a)
EJE = (0x38, 0x38, 0x35)
TECLA = (0x4a, 0x49, 0x44)
CALOR_POCO = (0x3a, 0x34, 0x18)
CALOR_MUCHO = (0xff, 0xb0, 0x20)
FORTALEZA = (0x8a, 0x89, 0x82)

# Medidas: el cuadro de 1144×744 sobre la superficie de 1200×800
CUADRO = pygame.Rect(28, 28, 1144, 744)
MARGEN_X, MARGEN_Y = 28, 24
SEPARACION = 12
ANCHO_IZQUIERDA = 660        # Gráficos y embudo; a la derecha, los mapas y el mejor agente
TAMANO_MAPA = (196, 163)     # 960×800 en chico
ALTO_FITNESS, ALTO_MANZANAS = 132, 76
ALTO_PASO = 25               # Cada renglón del embudo
ANCHO_FRASE_DEL_COFRE = 400
# Pixelify Sans Bold cierra la "C" a 34 px (y a 21, 22, 30, 33 y 35): 32 la deja abierta
TAMANO_TITULO = 32

TITULO_FITNESS = "FITNESS POR GENERACIÓN"
TITULO_MANZANAS = "MANZANAS POR AGENTE"
TITULO_MAPAS = "POR DÓNDE CAMINARON"
TITULO_EMBUDO = "PUZZLE: CUÁNTOS LLEGARON A CADA PASO EN LA ÚLTIMA GENERACIÓN"
TITULO_MEJOR = "MEJOR AGENTE DE LA CORRIDA"
HASTA_DONDE = "Hasta dónde llegaron: "
LEYENDA = (("Promedio", PROMEDIO), ("Máximo", MAXIMO))
LEYENDA_CALOR = ("poco tiempo", "mucho")
NOTA_CALOR = ("El calor es el tiempo que pasaron en cada lugar, por tick. Los recuadros grises son "
              "las dos fortalezas; el resto del mapa cambia en cada generación.")
COMANDO = "python experimento.py"
SALIR = ("ESC", " o ", "ENTER", " para salir")
# Cómo se nombra la primera vez de cada paso en el gráfico: "1ª llave roja · gen 2"
ORDINALES = ("1ª", "1ª", "1ª", "1ª", "1er")


def mostrar_pantalla_final(render_surface, generation, tick, agents, world, learning_monitor,
                           screen_width, screen_height, display_screen, sprite_manager,
                           particle_system, registro):
    """Muestra el resumen final. Lee SimulationConfig.HEADLESS_MODE de la clase: main.py lo pisa ahí.

    registro es el RegistroDeLaCorrida, con todas las generaciones ya cerradas: de ahí sale todo lo
    que se muestra. generation queda en la firma por los tests que la reemplazan.
    """
    imprimir_resumen_final(registro)
    if SimulationConfig.HEADLESS_MODE:
        return

    learning_monitor.create_learning_report()

    # Se dibuja una sola vez: el mundo con el dibujo del loop, los agentes vivos, las partículas
    # quietas, todo oscurecido, y el boletín encima (DIAG-17)
    dibujar_mundo(render_surface, world, sprite_manager, tick)
    for agent in agents:
        if agent.alive:
            agent.draw(render_surface, tick, sprite_manager, particle_system)
    particle_system.draw(render_surface)
    dibujar_boletin(render_surface, registro, world, sprite_manager)
    display_screen.blit(pygame.transform.scale(render_surface, (screen_width, screen_height)), (0, 0))

    # El loop solo atiende eventos y muestra lo ya dibujado
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                running = False
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def imprimir_resumen_final(registro):
    """El boletín de la corrida por consola (decisión 15): así el log guarda el mejor agente."""
    print("\n" + texto_de_consola(armar_boletin(registro)))


def marcas_del_grafico(boletin):
    """Cada paso del puzzle que se alcanzó, en la primera generación con algún agente en él (la del
    embudo, es decir, la del CSV): (generación, "1ª llave roja · gen 2")."""
    return [(paso["primera_vez"], f"{ORDINALES[paso['paso'] - 1]} {paso['nombre'].lower()} · gen {paso['primera_vez']}")
            for paso in boletin["embudo"] if paso["primera_vez"] is not None]


def color_de_calor(fraccion):
    """De ocre oscuro a ámbar; fraccion es la raíz cuadrada de valor / máximo, de 0 a 1."""
    return tuple(round(a + (b - a) * fraccion) for a, b in zip(CALOR_POCO, CALOR_MUCHO))


def mapa_de_calor(registro, grilla, maximo, fortalezas):
    """El mapa de una generación sobre fondo liso, con el contorno de las fortalezas. maximo es el
    valor más alto de los mapas que se muestran juntos: así comparten la escala de color."""
    chico = pygame.Surface((registro.columnas, registro.filas))
    chico.fill(FONDO_TARJETA)
    for i, (cuenta, valor) in enumerate(zip(grilla["cuentas"], registro.valores(grilla))):
        if cuenta > 0:
            chico.set_at((i % registro.columnas, i // registro.columnas),
                         color_de_calor(math.sqrt(valor / maximo)))
    mapa = pygame.transform.scale(chico, TAMANO_MAPA)
    escala_x = TAMANO_MAPA[0] / (registro.columnas * registro.celda)
    escala_y = TAMANO_MAPA[1] / (registro.filas * registro.celda)
    # Los recuadros de _is_inside_fortress: tamaño × 20 px desde la esquina de cada fortaleza
    for fortaleza in fortalezas:
        lado = fortaleza["size"] * 20
        pygame.draw.rect(mapa, FORTALEZA, (round(fortaleza["x"] * escala_x), round(fortaleza["y"] * escala_y),
                                           round(lado * escala_x), round(lado * escala_y)), 1)
    return mapa


def _texto(superficie, texto, papel, tamano, color, x, y):
    """Dibuja un renglón y devuelve su ancho."""
    renglon = fuentes.fuente(papel, tamano).render(texto, True, color)
    superficie.blit(renglon, (x, y))
    return renglon.get_width()


def _titulo_de_seccion(superficie, texto, x, y):
    _texto(superficie, texto, "seminegrita", 13, APAGADO, x, y)
    return y + fuentes.fuente("seminegrita", 13).get_height() + 6


def _parrafo(superficie, texto, tamano, color, x, y, ancho, derecha=False):
    """Un texto partido en renglones; devuelve la y de abajo."""
    fuente_ = fuentes.fuente("texto", tamano)
    for renglon in fuentes.renglones(fuente_, texto, ancho):
        imagen = fuente_.render(renglon, True, color)
        superficie.blit(imagen, (x + ancho - imagen.get_width() if derecha else x, y))
        y += fuente_.get_height()
    return y


def dibujar_boletin(superficie, registro, world, sprite_manager):
    """Dibuja el boletín sobre la superficie de 1200×800, que ya tiene el último cuadro del mundo.

    Devuelve (y de abajo del contenido, y de arriba del pie): el test mira que no se pisen.
    """
    boletin = armar_boletin(registro)
    superficie.fill(FONDO_PANEL, (960, 0, 240, 800))
    velo = pygame.Surface(superficie.get_size(), pygame.SRCALPHA)
    velo.fill(OSCURECER)
    superficie.blit(velo, (0, 0))
    cuadro = pygame.Surface(CUADRO.size, pygame.SRCALPHA)
    pygame.draw.rect(cuadro, FONDO_CUADRO, cuadro.get_rect(), border_radius=12)
    pygame.draw.rect(cuadro, BORDE_CUADRO, cuadro.get_rect(), 1, border_radius=12)
    superficie.blit(cuadro, CUADRO.topleft)

    x0, ancho = CUADRO.x + MARGEN_X, CUADRO.w - 2 * MARGEN_X
    y = _encabezado(superficie, boletin, x0, CUADRO.y + MARGEN_Y, ancho) + SEPARACION
    y = _cuatro_numeros(superficie, boletin["numeros"], x0, y, ancho) + SEPARACION

    x_derecha = x0 + ANCHO_IZQUIERDA + 20
    ancho_derecha = ancho - ANCHO_IZQUIERDA - 20
    abajo_graficos = _graficos(superficie, registro.historia, marcas_del_grafico(boletin), x0, y)
    fortalezas = [f for f in (world.small_fortress_pos, world.large_fortress_pos) if f]
    abajo_mapas = _mapas(superficie, registro, boletin["mapas"], fortalezas, x_derecha, y, ancho_derecha)
    y = max(abajo_graficos, abajo_mapas) + SEPARACION

    abajo_embudo = _embudo(superficie, boletin, sprite_manager, x0, y)
    abajo_mejor = _mejor_agente(superficie, boletin["mejor"], sprite_manager, x_derecha, y, ancho_derecha)
    abajo = max(abajo_embudo, abajo_mejor)

    return abajo, _pie(superficie, boletin["pie"], x0, CUADRO.bottom - MARGEN_Y, ancho)


def _encabezado(superficie, boletin, x, y, ancho):
    """Título y subtítulo a la izquierda; a la derecha, hasta dónde llegaron y la frase del cofre."""
    titulo = fuentes.fuente("titulo", TAMANO_TITULO).render(boletin["titulo"], True, TEXTO)
    superficie.blit(titulo, (x, y))
    subtitulo_y = y + titulo.get_height() + 6
    ancho_subtitulo = _texto(superficie, boletin["subtitulo"], "texto", 14, SECUNDARIO, x, subtitulo_y)
    abajo_izquierda = subtitulo_y + fuentes.fuente("texto", 14).get_height()

    # Angosto, para que la frase del cofre se parta en el punto y coma y no deje una palabra sola
    ancho_derecha = min(ANCHO_FRASE_DEL_COFRE, ancho - max(titulo.get_width(), ancho_subtitulo) - 24)
    fuente_ = fuentes.fuente("texto", 14)
    cofre = fuentes.renglones(fuente_, boletin["cofre"], ancho_derecha)
    alto_derecha = (1 + len(cofre)) * fuente_.get_height()
    y_derecha = abajo_izquierda - alto_derecha  # Alineado abajo con el subtítulo
    paso = fuentes.fuente("seminegrita", 14).render(boletin["hasta_donde"], True, TEXTO)
    rotulo = fuente_.render(HASTA_DONDE, True, SECUNDARIO)
    superficie.blit(paso, (x + ancho - paso.get_width(), y_derecha))
    superficie.blit(rotulo, (x + ancho - paso.get_width() - rotulo.get_width(), y_derecha))
    _parrafo(superficie, boletin["cofre"], 14, SECUNDARIO, x + ancho - ancho_derecha,
             y_derecha + fuente_.get_height(), ancho_derecha, derecha=True)
    return max(abajo_izquierda, y_derecha + alto_derecha)


def _cuatro_numeros(superficie, numeros, x, y, ancho):
    """Cuatro tarjetas: el valor de la generación 1 → el de las últimas, el cambio y la nota."""
    ancho_tarjeta = (ancho - 3 * 12) // 4
    adentro = ancho_tarjeta - 28
    fuente_nota = fuentes.fuente("texto", 12)
    alto_titulo = fuentes.fuente("seminegrita", 12).get_height()
    alto_valor = fuentes.fuente("negrita", 28).get_height()
    renglones_nota = max(len(fuentes.renglones(fuente_nota, dato["nota"], adentro)) for dato in numeros)
    alto = 12 + alto_titulo + 6 + alto_valor + 4 + renglones_nota * fuente_nota.get_height() + 12

    for i, dato in enumerate(numeros):
        tarjeta = pygame.Rect(x + i * (ancho_tarjeta + 12), y, ancho_tarjeta, alto)
        pygame.draw.rect(superficie, FONDO_TARJETA, tarjeta, border_radius=8)
        pygame.draw.rect(superficie, BORDE_TARJETA, tarjeta, 1, border_radius=8)
        cx, cy = tarjeta.x + 14, tarjeta.y + 12
        _texto(superficie, dato["titulo"], "seminegrita", 12, APAGADO, cx, cy)
        cy += alto_titulo + 6

        # Todo el renglón sobre la misma línea de base que el número grande
        base = cy + fuentes.fuente("negrita", 28).get_ascent()
        desde, _, hasta = dato["valor"].rpartition(" → ")
        partes = ([(desde, "texto", 15, SECUNDARIO), ("→", "texto", 15, APAGADO)] if desde else []) \
            + [(hasta, "negrita", 28, TEXTO)]
        if dato["cambio"]:
            color = SUBE if dato["sube"] else BAJA if dato["sube"] is False else SECUNDARIO
            partes.append((dato["cambio"], "seminegrita", 13, color))
        for texto, papel, tamano, color in partes:
            cx += _texto(superficie, texto, papel, tamano, color, cx,
                         base - fuentes.fuente(papel, tamano).get_ascent()) + 8
        _parrafo(superficie, dato["nota"], 12, APAGADO, tarjeta.x + 14, cy + alto_valor + 4, adentro)
    return y + alto


def _graficos(superficie, historia, marcas, x, y):
    """Fitness promedio y máximo, con los pasos del puzzle marcados, y debajo manzanas por agente."""
    titulo_y = y
    y = _titulo_de_seccion(superficie, TITULO_FITNESS, x, y)
    fuente_ = fuentes.fuente("texto", 12)
    leyenda_x = x + ANCHO_IZQUIERDA
    for nombre, color in reversed(LEYENDA):
        rotulo = fuente_.render(nombre, True, SECUNDARIO)
        leyenda_x -= rotulo.get_width()
        superficie.blit(rotulo, (leyenda_x, titulo_y))
        pygame.draw.line(superficie, color, (leyenda_x - 22, titulo_y + 8), (leyenda_x - 6, titulo_y + 8), 2)
        leyenda_x -= 22 + 16

    promedio = [fila["fitness_prom"] for fila in historia]
    maximo = [fila["fitness_max"] for fila in historia]
    manzanas = [fila["manzanas_prom"] for fila in historia]
    estilo = {"fondo": FONDO_CUADRO[:3], "grilla": GRILLA, "eje": EJE, "tamano": 11, "prefijo": "Gen ",
              "rotulo_medio": True}
    dibujar_grafico(superficie, pygame.Rect(x, y, ANCHO_IZQUIERDA, ALTO_FITNESS),
                    [(maximo, MAXIMO, f"Máx. {numero(maximo[-1], 1)}", False),
                     (promedio, PROMEDIO, f"Prom. {numero(promedio[-1], 1)}", True)],
                    marcas=marcas, **estilo)
    y = _titulo_de_seccion(superficie, TITULO_MANZANAS, x, y + ALTO_FITNESS + 8)
    dibujar_grafico(superficie, pygame.Rect(x, y, ANCHO_IZQUIERDA, ALTO_MANZANAS),
                    [(manzanas, PROMEDIO, numero(manzanas[-1], 2), True)], **estilo)
    return y + ALTO_MANZANAS


def _mapas(superficie, registro, mapas, fortalezas, x, y, ancho):
    """El mapa de calor de la generación 1 y el de la última, con la misma escala de color."""
    y = _titulo_de_seccion(superficie, TITULO_MAPAS, x, y)
    grillas = [registro.calor_gen1] + ([registro.calor_ultima] if len(mapas) > 1 else [])
    maximo = max(max(registro.valores(grilla)) for grilla in grillas) or 1
    for i, (grilla, mapa) in enumerate(zip(grillas, mapas)):
        mx = x + i * (TAMANO_MAPA[0] + 16)
        superficie.blit(mapa_de_calor(registro, grilla, maximo, fortalezas), (mx, y))
        pygame.draw.rect(superficie, BORDE_TARJETA, (mx, y, *TAMANO_MAPA), 1)
        _texto(superficie, mapa["texto"], "texto", 12, SECUNDARIO, mx, y + TAMANO_MAPA[1] + 6)
    y += TAMANO_MAPA[1] + 6 + fuentes.fuente("texto", 12).get_height() + 8

    # Leyenda: poco tiempo, la barra de colores, mucho
    lx = x + _texto(superficie, LEYENDA_CALOR[0], "texto", 12, APAGADO, x, y) + 8
    for i in range(120):
        pygame.draw.line(superficie, color_de_calor(i / 119), (lx + i, y + 5), (lx + i, y + 12))
    _texto(superficie, LEYENDA_CALOR[1], "texto", 12, APAGADO, lx + 128, y)
    y += fuentes.fuente("texto", 12).get_height() + 6
    return _parrafo(superficie, NOTA_CALOR, 12, APAGADO, x, y, ancho)


def _embudo(superficie, boletin, sprite_manager, x, y):
    """Los cinco pasos de la última generación, con su barra y la primera vez; y "murieron todos"."""
    y = _titulo_de_seccion(superficie, TITULO_EMBUDO, x, y)
    ancho_texto = 196
    barra_x = x + 20 + 10 + 118 + 10
    ancho_barra = ANCHO_IZQUIERDA - (barra_x - x) - 10 - ancho_texto
    for paso in boletin["embudo"]:
        sprite = sprite_manager.get_environment_sprite(SPRITES_DE_HITOS[paso["paso"] - 1])
        if sprite is not None:
            superficie.blit(pygame.transform.scale(sprite, (18, 18)), (x, y + 1))
        _texto(superficie, paso["nombre"], "texto", 13, TEXTO, x + 30, y + 1)
        pygame.draw.rect(superficie, GRILLA, (barra_x, y + 5, ancho_barra, 10), border_radius=4)
        if paso["agentes"]:
            pygame.draw.rect(superficie, PROMEDIO, (barra_x, y + 5, max(2, round(ancho_barra * paso["fraccion"])), 10),
                             border_radius=4)
        _texto(superficie, paso["texto"], "texto", 12, SECUNDARIO, barra_x + ancho_barra + 10, y + 2)
        y += ALTO_PASO
    if boletin["murieron_todos"]:
        _texto(superficie, boletin["murieron_todos"], "texto", 13, SECUNDARIO, x, y + 2)
        y += fuentes.fuente("texto", 13).get_height() + 2
    return y


def _mejor_agente(superficie, mejor, sprite_manager, x, y, ancho):
    """La tarjeta del récord de la corrida: sprite, id y generación, y sus datos."""
    fuente_ = fuentes.fuente("texto", 13)
    alto_titulo = fuentes.fuente("seminegrita", 12).get_height()
    alto = 12 + alto_titulo + 6 + (1 + len(mejor["renglones"])) * (fuente_.get_height() + 2) + 10
    tarjeta = pygame.Rect(x, y, ancho, alto)
    pygame.draw.rect(superficie, FONDO_TARJETA, tarjeta, border_radius=8)
    pygame.draw.rect(superficie, BORDE_TARJETA, tarjeta, 1, border_radius=8)
    sprite = sprite_manager.sprites.get("agent_down_1") or sprite_manager.sprites.get("agent")
    if sprite is not None:
        superficie.blit(pygame.transform.scale(sprite, (48, 48)), (x + 14, y + 12))
    cx, cy = x + 14 + 48 + 14, y + 12
    _texto(superficie, TITULO_MEJOR, "seminegrita", 12, APAGADO, cx, cy)
    cy += alto_titulo + 6
    _texto(superficie, mejor["titulo"], "seminegrita", 13, TEXTO, cx, cy)
    for renglon in mejor["renglones"]:
        cy += fuente_.get_height() + 2
        _texto(superficie, renglon, "texto", 13, SECUNDARIO, cx, cy)
    return y + alto


def _pie(superficie, pie, x, abajo, ancho):
    """La invitación a medir contra la línea base (o que esta es la línea base), y cómo salir.
    Devuelve la y de arriba del pie."""
    fuente_ = fuentes.fuente("texto", 13)
    y = abajo - fuente_.get_height()
    antes, comando, _ = pie.partition(COMANDO)
    ancho_antes = _texto(superficie, antes, "texto", 13, APAGADO, x, y)
    if comando:
        _texto(superficie, comando, "texto", 13, SECUNDARIO, x + ancho_antes, y)

    rotulos = [fuente_.render(texto, True, SECUNDARIO if texto.strip() in ("ESC", "ENTER") else APAGADO)
               for texto in SALIR]
    sx = x + ancho - sum(r.get_width() for r in rotulos) - 2 * 12
    for rotulo, texto in zip(rotulos, SALIR):
        if texto.strip() in ("ESC", "ENTER"):
            pygame.draw.rect(superficie, TECLA, (sx, y - 1, rotulo.get_width() + 12, rotulo.get_height() + 2),
                             1, border_radius=4)
            superficie.blit(rotulo, (sx + 6, y))
            sx += rotulo.get_width() + 12
        else:
            superficie.blit(rotulo, (sx, y))
            sx += rotulo.get_width()
    return y - 1
