"""
Registro de la corrida (spec PANTALLAS_VER_APRENDER, decisiones 4 a 7): lo que pasó en cada
generación, en memoria, para las pantallas y el boletín por consola. main.py lo alimenta por un solo
camino, con ventana y sin ella.

No usa pygame ni el azar: contar posiciones, mirar hitos y cerrar una generación no tocan `random`
ni `np.random`, así la corrida da el mismo CSV que sin el registro (decisión 3).
"""

from config import SimulationConfig

# Los cinco pasos del puzzle, en orden: la etapa de un agente llega a 1, 2, 3, 4 o 5
PASOS = ("llave roja", "puerta de madera", "llave dorada", "puerta de hierro", "cofre")
# La columna del CSV de cada paso, en el mismo orden
COLUMNAS_DE_PASOS = ("agentes_llave_roja", "agentes_puerta_madera", "agentes_llave_dorada",
                     "agentes_puerta_hierro", "agentes_cofre")


class RegistroDeLaCorrida:
    """La historia de la corrida, sus hitos, el mejor agente y el mapa de calor.

    historia: una entrada por generación terminada, con la fila del CSV tal cual (por columna) y
    'ticks_max', los ticks que podía durar. hitos: la primera vez que un agente llegó a cada paso.
    mejor: el récord de la corrida. calor_gen1 y calor_ultima: las grillas de la generación 1 y de la
    última terminada, cada una con su generación, sus ticks, la cuenta de cada celda y sus fortalezas.
    """

    def __init__(self, ancho, alto, celda=None):
        self.celda = celda or SimulationConfig.HEATMAP_CELL_SIZE
        self.columnas = ancho // self.celda
        self.filas = alto // self.celda
        self.historia = []
        self.hitos = []
        self.mejor = None
        self.calor_gen1 = None
        self.calor_ultima = None
        self._en_curso = self._grilla_vacia()
        self._pasos_con_hito = set()  # Los pasos que algún agente ya dio en la corrida

    def _grilla_vacia(self):
        return [0] * (self.columnas * self.filas)

    def contar_posiciones(self, agents):
        """Suma 1 en la celda de cada agente vivo. Va después de cada tick simulado (decisión 7)."""
        for agent in agents:
            if agent.alive:
                columna = min(max(int(agent.x) // self.celda, 0), self.columnas - 1)
                fila = min(max(int(agent.y) // self.celda, 0), self.filas - 1)
                self._en_curso[fila * self.columnas + columna] += 1

    def mirar_hitos(self, agents, generacion, tick):
        """Registra y devuelve los pasos del puzzle que un agente dio por primera vez en la corrida
        (decisión 5). Lo que se le dio al nacer no cuenta (spec PUZZLE_APRENDIBLE, decisión 10): con el
        currículo, el primer hito puede ser la puerta de madera. Si pasan dos en el mismo tick, van
        los dos, en el orden del puzzle; el agente de cada uno es el primero de la lista que dio ese
        paso."""
        nuevos = []
        etapa_maxima = max((agent.etapa for agent in agents), default=0)
        for paso in range(1, etapa_maxima + 1):
            if paso in self._pasos_con_hito:
                continue
            agente = next((agent for agent in agents
                           if agent.etapa_inicial < paso <= agent.etapa), None)
            if agente is None:
                continue
            hito = {"paso": paso, "generacion": generacion, "tick": tick, "agente": agente.id}
            self.hitos.append(hito)
            nuevos.append(hito)
            self._pasos_con_hito.add(paso)
        return nuevos

    def cerrar_generacion(self, fila, ticks_max, agents, fortalezas=()):
        """Guarda la fila del CSV de la generación (un dict por columna), el récord y su mapa de calor,
        con las fortalezas de la generación (las posiciones del mundo; con FORTALEZAS_MOVILES cambian).

        Espera el fitness ya calculado en cada agente: el mismo de la fila (decisión 6).
        """
        entrada = dict(fila)
        entrada["ticks_max"] = ticks_max
        self.historia.append(entrada)

        # El mejor de la generación reemplaza al récord solo si lo supera: un empate deja el anterior
        mejor = max(agents, key=lambda agent: float(agent.fitness))
        if self.mejor is None or float(mejor.fitness) > self.mejor["fitness"]:
            self.mejor = {
                "id": mejor.id,
                "generacion": fila["generacion"],
                "fitness": float(mejor.fitness),
                "manzanas": mejor.food_eaten,
                "recorrido": float(mejor.distance_traveled),
                "ticks_vividos": mejor.age,
                "etapa": mejor.etapa,
                "etapa_inicial": mejor.etapa_inicial,
            }

        grilla = {"generacion": fila["generacion"], "ticks": fila["ticks"], "cuentas": self._en_curso,
                  "fortalezas": [dict(fortaleza) for fortaleza in fortalezas if fortaleza]}
        if fila["generacion"] == 1:
            self.calor_gen1 = grilla
        self.calor_ultima = grilla
        self._en_curso = self._grilla_vacia()

    def valores(self, grilla):
        """Cuántos agentes hubo en promedio en cada celda por tick: así se comparan generaciones de
        largos distintos."""
        return [cuenta / grilla["ticks"] for cuenta in grilla["cuentas"]]

    def cobertura(self, grilla):
        """El porcentaje de celdas que alguien pisó en la generación."""
        cuentas = grilla["cuentas"]
        return 100 * sum(1 for cuenta in cuentas if cuenta > 0) / len(cuentas)
