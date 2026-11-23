"""
Panel derecho, durante la corrida (spec PANTALLAS_VER_APRENDER, decisión 9): los datos de la
generación, los gráficos de fitness y de manzanas por agente por generación terminada, el puzzle y
las teclas. Ocupa la columna entera, a la derecha del mundo. No usa el azar.
"""

import pygame

from config import SimulationConfig
from ..agents.advanced_agent import PASOS_DEL_PUZZLE, agentes_por_paso
from ..analytics.boletin import NOMBRES_DE_MODOS, nombre_de_las_ayudas, numero
from ..analytics.registro import COLUMNAS_DE_PASOS
from . import fuentes
from .avisos import SPRITES_DE_HITOS
from .graficos import TEXTO, SECUNDARIO, APAGADO, PROMEDIO, MAXIMO, dibujar_grafico

FONDO = (0x16, 0x18, 0x26)
BORDE = (0x2b, 0x2f, 0x45)
EJE = (0x3b, 0x40, 0x60)
VERDE = (0x64, 0xff, 0x96)

# Pixelify Sans Bold cierra la "C" a 22 px (y a 21, 30 y de 33 a 35): 24 la deja abierta
TAMANO_TITULO = 24
TITULO = "Ecosistema"
TITULO_FITNESS = "FITNESS POR GENERACIÓN"
TITULO_MANZANAS = "MANZANAS POR AGENTE"
TITULO_PUZZLE = "PUZZLE"
LEYENDA = (("Promedio", PROMEDIO), ("Máximo", MAXIMO))
SIN_GRAFICOS = "Se dibuja al terminar la generación 1"
ESTA_GENERACION = "Esta generación:"
NADIE_TODAVIA = "nadie todavía"
TECLAS = ((("ESPACIO",), "pausa"), (("+", "−"), "zoom"), (("ESC",), "salir"))
# Lo que logró la generación anterior, según el paso más lejano al que llegaron: (uno, varios)
LOGROS = (
    ("1 agente con llave roja", "{} agentes con llave roja"),
    ("1 agente abrió la puerta de madera", "{} agentes abrieron la puerta de madera"),
    ("1 agente con llave dorada", "{} agentes con llave dorada"),
    ("1 agente abrió la puerta de hierro", "{} agentes abrieron la puerta de hierro"),
    ("1 agente abrió el cofre", "{} agentes abrieron el cofre"),
)

ALTO_FITNESS = 120
ALTO_MANZANAS = 80


def datos_de_la_generacion(generation, agents, world, tick):
    """Los renglones de datos: (rótulo, valor). M, las generaciones de la corrida, sale de la clase
    SimulationConfig, donde main.py pisa --generaciones; el modo y los switches de las ayudas, igual.
    Las ayudas van en su renglón, solo si hay alguna prendida: con el modo no entran (spec
    PUZZLE_APRENDIBLE, decisión 11). Las fortalezas móviles, en otro, solo si están prendidas: con las
    ayudas no entran. La brújula por el camino, igual."""
    segundos = tick // 60
    vivos = len([agent for agent in agents if agent.alive])
    ayudas = nombre_de_las_ayudas(SimulationConfig.RECOMPENSA_ACERCARSE, SimulationConfig.CURRICULO,
                                  SimulationConfig.DESLIZAR, SimulationConfig.ACERCARSE_CAMINO)
    return [
        ("Generación", f"{generation} de {SimulationConfig.MAX_GENERATIONS}"),
        ("Modo", NOMBRES_DE_MODOS.get(SimulationConfig.MODO, SimulationConfig.MODO)),
        *([("Ayudas", ayudas)] if ayudas else []),
        *([("Fortalezas", "móviles")] if SimulationConfig.FORTALEZAS_MOVILES else []),
        *([("Brújula", "por el camino")] if SimulationConfig.BRUJULA_CAMINO else []),
        ("Tiempo", f"{segundos // 60:02d}:{segundos % 60:02d}"),
        ("Vivos", str(vivos)),
        ("Muertos", str(len(agents) - vivos)),
        ("Comida", str(len([food for food in world.food_items if not food['eaten']]))),
    ]


def renglones_del_puzzle(agents, historia):
    """Esta generación (agentes con hacha y cada paso con alguien, o "nadie todavía") y la anterior:
    hasta qué paso llegaron y cuántos. Devuelve (renglones de esta, (paso, texto) de la anterior); la
    anterior es None antes de que termine la generación 1, y su paso es 0 si nadie agarró la llave."""
    esta = []
    con_hacha = len([agent for agent in agents if agent.tiene_hacha])
    if con_hacha:
        esta.append(f"Con hacha: {con_hacha}")
    esta += [f"{nombre}: {cantidad}" for nombre, cantidad in zip(PASOS_DEL_PUZZLE, agentes_por_paso(agents))
             if cantidad]

    anterior = None
    if historia:
        fila = historia[-1]
        alcanzados = [paso for paso, columna in enumerate(COLUMNAS_DE_PASOS, start=1) if fila[columna] > 0]
        if alcanzados:
            paso = alcanzados[-1]
            agentes = fila[COLUMNAS_DE_PASOS[paso - 1]]
            uno, varios = LOGROS[paso - 1]
            anterior = (paso, f"Gen {fila['generacion']}: {uno if agentes == 1 else varios.format(agentes)}")
        else:
            anterior = (0, f"Gen {fila['generacion']}: nadie agarró la llave roja")
    return esta or [NADIE_TODAVIA], anterior


def _titulo_de_seccion(texto):
    return fuentes.fuente("seminegrita", 11).render(texto, True, APAGADO)


def graficos_del_panel(historia, ancho):
    """Los dos gráficos, en una superficie: se dibujan una vez por generación terminada."""
    fuente_leyenda = fuentes.fuente("texto", 11)
    alto_titulo = _titulo_de_seccion(TITULO_FITNESS).get_height()
    alto = (alto_titulo + 4 + fuente_leyenda.get_height() + 6 + ALTO_FITNESS + 14
            + alto_titulo + 6 + ALTO_MANZANAS)
    superficie = pygame.Surface((ancho, alto))
    superficie.fill(FONDO)

    y = 0
    superficie.blit(_titulo_de_seccion(TITULO_FITNESS), (0, y))
    y += alto_titulo + 4
    x = 0
    for nombre, color in LEYENDA:
        pygame.draw.line(superficie, color, (x, y + 7), (x + 11, y + 7), 2)
        rotulo = fuente_leyenda.render(nombre, True, SECUNDARIO)
        superficie.blit(rotulo, (x + 16, y))
        x += 16 + rotulo.get_width() + 12
    y += fuente_leyenda.get_height() + 6
    rect_fitness = pygame.Rect(0, y, ancho, ALTO_FITNESS)
    y += ALTO_FITNESS + 14
    superficie.blit(_titulo_de_seccion(TITULO_MANZANAS), (0, y))
    y += alto_titulo + 6
    rect_manzanas = pygame.Rect(0, y, ancho, ALTO_MANZANAS)

    if not historia:
        fuente_ = fuentes.fuente("texto", 12)
        for i, renglon in enumerate(fuentes.renglones(fuente_, SIN_GRAFICOS, ancho)):
            superficie.blit(fuente_.render(renglon, True, APAGADO),
                            (0, rect_fitness.y + 40 + i * fuente_.get_height()))
        return superficie

    promedio = [fila["fitness_prom"] for fila in historia]
    maximo = [fila["fitness_max"] for fila in historia]
    manzanas = [fila["manzanas_prom"] for fila in historia]
    estilo = {"fondo": FONDO, "grilla": BORDE, "eje": EJE, "tamano": 10}
    dibujar_grafico(superficie, rect_fitness, [(maximo, MAXIMO, numero(maximo[-1], 1), False),
                                               (promedio, PROMEDIO, numero(promedio[-1], 1), True)], **estilo)
    dibujar_grafico(superficie, rect_manzanas, [(manzanas, PROMEDIO, numero(manzanas[-1], 2), True)], **estilo)
    return superficie


class StatsPanel:
    """Panel de estadísticas en tiempo real."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._graficos = (None, None)  # (generaciones terminadas, superficie)

    def draw(self, screen, generation, agents, world, tick, registro, sprite_manager=None):
        """Dibuja el panel. registro es el RegistroDeLaCorrida: los gráficos y la generación anterior
        salen de su historia, es decir, de las filas del CSV."""
        pygame.draw.rect(screen, FONDO, (self.x, self.y, self.width, self.height))
        pygame.draw.line(screen, BORDE, (self.x, self.y), (self.x, self.y + self.height - 1))
        izquierda, ancho = self.x + 16, self.width - 32
        y = self.y + 18

        titulo = fuentes.fuente("titulo", TAMANO_TITULO).render(TITULO, True, VERDE)
        screen.blit(titulo, (izquierda, y))
        y += titulo.get_height() + 10

        for rotulo, valor in datos_de_la_generacion(generation, agents, world, tick):
            screen.blit(fuentes.fuente("texto", 13).render(rotulo, True, APAGADO), (izquierda, y))
            dato = fuentes.fuente("seminegrita" if rotulo == "Generación" else "texto", 13) \
                .render(valor, True, TEXTO)
            screen.blit(dato, (izquierda + ancho - dato.get_width(), y))
            y += 20
        y += 12

        generaciones = len(registro.historia)
        if self._graficos[0] != generaciones:
            self._graficos = (generaciones, graficos_del_panel(registro.historia, ancho))
        screen.blit(self._graficos[1], (izquierda, y))
        y += self._graficos[1].get_height() + 16

        y = self._dibujar_puzzle(screen, agents, registro.historia, sprite_manager, izquierda, ancho, y)
        self._dibujar_teclas(screen, izquierda)

    def _dibujar_puzzle(self, screen, agents, historia, sprite_manager, izquierda, ancho, y):
        titulo = _titulo_de_seccion(TITULO_PUZZLE)
        screen.blit(titulo, (izquierda, y))
        y += titulo.get_height() + 6
        fuente_ = fuentes.fuente("texto", 12)
        esta, anterior = renglones_del_puzzle(agents, historia)
        screen.blit(fuente_.render(ESTA_GENERACION, True, SECUNDARIO), (izquierda, y))
        y += fuente_.get_height() + 2
        for renglon in esta:
            screen.blit(fuente_.render(renglon, True, TEXTO if renglon != NADIE_TODAVIA else APAGADO),
                        (izquierda + 8, y))
            y += fuente_.get_height() + 1
        if anterior:
            paso, texto = anterior
            y += 8
            sangria = 0
            sprite = sprite_manager.get_environment_sprite(SPRITES_DE_HITOS[paso - 1]) \
                if sprite_manager and paso else None
            if sprite is not None:
                screen.blit(pygame.transform.scale(sprite, (16, 16)), (izquierda, y))
                sangria = 22
            for renglon in fuentes.renglones(fuente_, texto, ancho - sangria):
                screen.blit(fuente_.render(renglon, True, SECUNDARIO), (izquierda + sangria, y))
                y += fuente_.get_height() + 1
        return y

    def _dibujar_teclas(self, screen, izquierda):
        fuente_ = fuentes.fuente("texto", 11)
        y = self.y + self.height - 18 - len(TECLAS) * 20
        for teclas, que_hace in TECLAS:
            x = izquierda
            for tecla in teclas:
                rotulo = fuente_.render(tecla, True, SECUNDARIO)
                caja = pygame.Rect(x, y, rotulo.get_width() + 8, rotulo.get_height() + 2)
                pygame.draw.rect(screen, EJE, caja, 1, border_radius=3)
                screen.blit(rotulo, (x + 4, y + 1))
                x = caja.right + 5
            screen.blit(fuente_.render(que_hace, True, APAGADO), (x, y + 1))
            y += 20
