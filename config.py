"""
Configuración centralizada para el ecosistema evolutivo.
"""

class SimulationConfig:
    """Configuración centralizada de todos los parámetros."""
    
    # === SIMULACIÓN ===
    POPULATION_SIZE = 60
    TARGET_FPS = 60
    MAX_GENERATIONS = 50    # Extendido para ver tendencias a largo plazo
    HEADLESS_MODE = False             # True = sin render (rápido), False = con render (visual)
    # "guiado": decide() suma la conducción escrita a mano hacia la comida y el puzzle.
    # "autonomo": decide() es solo la salida de la red. Lo demás es igual en los dos (--modo lo pisa)
    MODO = "guiado"

    # .venv/Scripts/python.exe main.py --generaciones 10 --semilla 1 --modo autonomo
    # .venv/Scripts/python.exe main.py --generaciones 10 --semilla 1 --modo guiado

    
    # === SISTEMA ADAPTATIVO DE TIEMPO ===
    ADAPTIVE_TIME_ENABLED = True      # Habilitar tiempo adaptativo
    BASE_TICKS = 960                  # Tiempo base inicial (aumentado para dar más tiempo por gen)
    TICKS_INCREMENT_AMOUNT = 180      # Cuántos ticks aumentar cada incremento (180 para crecimiento más gradual)
    TICKS_INCREMENT_FREQUENCY = 4     # Cada cuántas generaciones aumentar (cada 2 para más frecuencia)
    
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.30       # Mutación más alta para mayor diversidad
    CROSSOVER_RATE = 0.95        # 90% de cruce 
    
    # === SELECCIÓN DE PADRES ===
    SELECTION_METHOD = "meeting_pool"  # "elitism", "tournament" o "meeting_pool"
    TOURNAMENT_SIZE = 3             # Tamaño del torneo 
    ELITISM = 1                     # Mejores agentes que se mantienen 
    MEETING_POOL_FRACTION = 0.60    # Porción superior por ranking para el pool (reducido para más presión selectiva)
    
    # === INMIGRACIÓN ===
    IMMIGRATION_ENABLED = True      # Habilitar inmigración periódica para mantener diversidad
    IMMIGRATION_FREQUENCY = 6       # Cada cuántas generaciones aplicar inmigración
    IMMIGRATION_COUNT = 3           # Cuántos agentes nuevos aleatorios introducir
    
    # === RED NEURONAL ===
    INPUT_SIZE = 11              # 11 sensores, con la etapa del puzzle y la brújula a su próximo paso
    HIDDEN_SIZE = [24, 16]       # Capas ocultas (soporta lista o entero)
    OUTPUT_SIZE = 5              # 5 acciones: avanzar, girar a la izquierda, a la derecha, comer y golpear
    
    # === AGENTE ===
    AGENT_SPEED = 3.0            # Velocidad de movimiento
    VISION_RANGE = 150           # Rango de visión
    AGENT_ENERGY = 100.0         # Energía inicial y máxima (comer y la poción no pasan de acá)
    AGENT_ENERGY_CONSUMPTION = 0.10  # Consumo de energía por tick 
    AGENT_ENERGY_GAIN_FOOD = 8      # Energía ganada al comer 
    AGENT_RADIUS = 6             # Tamaño del agente
    HIT_ENERGY_COST = 0.05       # Energía extra que gasta golpear, golpee algo o no
    # Si el paso choca, el agente se mueve por el eje libre: primero solo en x y, si no, solo en y,
    # en los dos modos (--deslizar lo prende). Apagado, se queda donde está
    DESLIZAR = False
    
    # === MUNDO ===
    # Dimensiones iniciales (se ajustarán dinámicamente)
    SCREEN_WIDTH = 1200          # Ancho inicial de pantalla
    SCREEN_HEIGHT = 800          # Alto inicial de pantalla
    
    # Proporciones del panel de estadísticas (20% del ancho)
    STATS_PANEL_RATIO = 0.20     # 20% del ancho total
    GAME_AREA_RATIO = 0.80       # 80% del ancho total
    HEATMAP_CELL_SIZE = 16       # Lado de cada celda del mapa de calor, en píxeles (60×50 en 960×800)
    
    # Márgenes para el perímetro
    PERIMETER_MARGIN = 40        # Margen del perímetro en píxeles
    
    # Escalado de sprites (se calculará dinámicamente)
    SPRITE_SCALE_FACTOR = 1.0    # Factor de escalado de sprites
    BASE_SPRITE_SIZE = 16        # Tamaño base de sprites en píxeles
    
    FOOD_COUNT = 70             # Cantidad de comida inicial (aumentado para generaciones largas)
    
    # === SISTEMA DE CORTE DE ÁRBOLES ===
    TREE_CUTTING_ENABLED = True   # Habilitar sistema de corte
    TREE_CUTTING_THRESHOLD = 30  # Umbral para activar corte (≤30 manzanas)
    TREE_HITS_TO_CUT = 2         # Golpes necesarios para cortar árbol
    TREE_CUT_REWARD = 15        # Fitness ganado por cortar árbol (aumentado para incentivar corte)
    TREE_CUT_FOOD_REWARD = 20      # Manzanas generadas al cortar árbol
    
    # === SISTEMA DE CORTE DE HUTS ===
    HUT_CUTTING_ENABLED = True     # Habilitar sistema de corte de huts
    HUT_CUTTING_THRESHOLD = 20     # Umbral para activar corte (≤20 manzanas)
    HUT_HITS_TO_CUT = 4            # Golpes necesarios para destruir hut
    HUT_CUT_REWARD = 15           # Fitness ganado por destruir hut (era 15)
    HUT_CUT_FOOD_REWARD = 30       # Manzanas generadas al destruir hut
    
    # === SISTEMA DE AGUA ===
    WATER_FITNESS_PENALTY = 5      # Fitness perdido por tick en agua (equilibrado con comida)
    WATER_PENALTY_MAX = 10         # Tope de la penalización por agua en el fitness
    WATER_ENERGY_LOSS = 0.05       # Energía perdida por tick en agua, además del consumo
    
    # === MÉTRICAS ANTI-CÍRCULO ===
    ANTI_CIRCLE_WINDOW_TICKS = 240   # ~3s a 60 FPS
    ANTI_CIRCLE_W1_SR = 0.75          # Peso rectitud
    ANTI_CIRCLE_W2_TURN = 0.15        # Peso giro medio (suavidad)
    ANTI_CIRCLE_W3_NOVELTY = 0.40     # Peso novedad espacial
    TURN_MEAN_ABS_MAX = 0.2          # rad/tick para normalizar giro promedio
    NOVELTY_CELL_SIZE = 12           # tamaño de celda para novedad

    # === FITNESS ===
    # Fitness = supervivencia + comida + exploración + anti-círculo + puzzle + cortes - agua
    # (+ acercarse, si está prendida), entre 0 y 100, con un tope que crece con el tiempo vivido
    FITNESS_FOOD = 10.0              # × raíz de las manzanas comidas
    FITNESS_EXPLORATION = 10.0       # × log(1 + distancia recorrida / 350)
    FITNESS_EXPLORATION_MAX = 15.0   # Tope del término de exploración
    FITNESS_SURVIVAL = 0.010         # × ticks vividos
    FITNESS_SURVIVAL_MAX = 10.0      # Tope del término de supervivencia
    FITNESS_ANTI_CIRCLE = 18.0       # × puntaje anti-círculo (pesos de arriba)
    # Recompensa por acercarse al próximo paso del puzzle, en los dos modos (--acercarse la prende)
    RECOMPENSA_ACERCARSE = False
    FITNESS_ACERCARSE = 10.0         # × (pasos que dio + avance en el paso actual, de 0 a 1)
    # Currículo, en los dos modos (--curriculo lo prende): las generaciones 1 a CURRICULO_HASTA_GENERACION
    # nacen con la llave roja, sin su premio; desde la siguiente, sin ella
    CURRICULO = False
    CURRICULO_HASTA_GENERACION = 15
    
    # === SISTEMA DE FORTALEZAS/LLAVES/PUERTAS/COFRE ===
    FORTRESSES_ENABLED = True     # Habilitar sistema de fortalezas
    
    # Fortalezas
    SMALL_FORTRESS_SIZE = 5       # Tamaño de fortaleza pequeña (4x5 tiles)
    LARGE_FORTRESS_SIZE = 6       # Tamaño de fortaleza grande (6x6 tiles)
    TILE_SIZE = 32                # Tamaño de cada tile en píxeles
    
    # Llaves
    RED_KEY_SPAWN_GEN = 1         # Generación en que aparece red_key libremente (retrasado para que aprendan primero tareas básicas)
    RED_KEY_REWARD = 10            # Fitness por recoger red_key (aumentado para mejor balance)
    GOLD_KEY_REWARD = 25          # Fitness por recoger gold_key (aumentado para que más agentes suban de fitness)
    
    # Puertas
    DOOR_HITS_TO_OPEN = 2         # Golpes necesarios para abrir door
    DOOR_IRON_HITS_TO_OPEN = 3    # Golpes necesarios para abrir door_iron
    DOOR_OPEN_REWARD = 12         # Fitness por abrir door (aumentado para mejor curva)
    DOOR_IRON_OPEN_REWARD = 35    # Fitness por abrir door_iron (aumentado para que más agentes suban de fitness)
    DOOR_HIT_COOLDOWN = 90       # Cooldown entre golpes (ticks)
    
    # Cofre
    CHEST_REWARD = 50            # Fitness por abrir cofre (aumentado para que promedio suba a 70+)
    
    # === RENDIMIENTO ===
    STATS_UPDATE_FREQUENCY = 5   # Actualizar stats cada N frames
    PARTICLE_UPDATE_FREQUENCY = 2  # Actualizar partículas cada N frames
    
    @classmethod
    def get_stats_panel_width(cls):
        """Calcular ancho del panel de estadísticas dinámicamente"""
        return int(cls.SCREEN_WIDTH * cls.STATS_PANEL_RATIO)
    
    @classmethod
    def get_game_area_width(cls):
        """Calcular ancho del área de juego dinámicamente"""
        return int(cls.SCREEN_WIDTH * cls.GAME_AREA_RATIO)
    
    @classmethod
    def get_grass_area_width(cls):
        """Calcular ancho del área de pasto dinámicamente"""
        return cls.get_game_area_width() - cls.PERIMETER_MARGIN
    
    @classmethod
    def update_screen_size(cls, width, height):
        """Actualizar dimensiones de pantalla dinámicamente"""
        cls.SCREEN_WIDTH = width
        cls.SCREEN_HEIGHT = height
        
        # Calcular factor de escalado de sprites basado en el área de juego
        game_area_width = cls.get_game_area_width()
        # Factor de escalado basado en el ancho del área de juego (1200px = factor 1.0)
        cls.SPRITE_SCALE_FACTOR = max(0.5, min(2.0, game_area_width / 960.0))
    
    @classmethod
    def get_scaled_sprite_size(cls):
        """Obtener tamaño escalado de sprites"""
        return int(cls.BASE_SPRITE_SIZE * cls.SPRITE_SCALE_FACTOR)
    
    @classmethod
    def get_scaled_coordinate(cls, coord):
        """Convertir coordenada del juego a coordenada escalada"""
        return int(coord * cls.SPRITE_SCALE_FACTOR)
    
    @classmethod
    def get_genetic_params(cls):
        """Obtiene parámetros del algoritmo genético."""
        return {
            'population_size': cls.POPULATION_SIZE,
            'mutation_rate': cls.MUTATION_RATE,
            'crossover_rate': cls.CROSSOVER_RATE,
            'elitism': cls.ELITISM,
            'selection_method': cls.SELECTION_METHOD,
            'tournament_size': cls.TOURNAMENT_SIZE,
            'meeting_pool_fraction': cls.MEETING_POOL_FRACTION
        }
    
    @classmethod
    def get_neural_params(cls):
        """Obtiene parámetros de la red neuronal."""
        return {
            'input_size': cls.INPUT_SIZE,
            'hidden_size': cls.HIDDEN_SIZE,
            'output_size': cls.OUTPUT_SIZE
        }
    
    @classmethod
    def get_agent_params(cls):
        """Obtiene parámetros del agente."""
        return {
            'speed': cls.AGENT_SPEED,
            'vision_range': cls.VISION_RANGE,
            'energy': cls.AGENT_ENERGY,
            'energy_consumption': cls.AGENT_ENERGY_CONSUMPTION,
            'energy_gain_food': cls.AGENT_ENERGY_GAIN_FOOD,
            'radius': cls.AGENT_RADIUS
        }
    
    @classmethod
    def get_simulation_params(cls):
        """Obtiene parámetros de simulación."""
        return {
            'base_ticks': cls.BASE_TICKS,
            'ticks_increment': cls.TICKS_INCREMENT_AMOUNT,
            'ticks_frequency': cls.TICKS_INCREMENT_FREQUENCY,
            'population_size': cls.POPULATION_SIZE,
            'target_fps': cls.TARGET_FPS,
            'max_generations': cls.MAX_GENERATIONS
        }
    
    @classmethod
    def print_config(cls):
        """Imprime toda la configuración."""
        print("🔧 CONFIGURACIÓN ACTUAL:")
        print("=" * 50)
        print(f"📊 Simulación: {cls.POPULATION_SIZE} agentes")
        print(f"⏱️ Ticks adaptativos: Base {cls.BASE_TICKS}, +{cls.TICKS_INCREMENT_AMOUNT} cada {cls.TICKS_INCREMENT_FREQUENCY} gen")
        mode = "HEADLESS (rápido)" if cls.HEADLESS_MODE else "VISUAL (renderizado)"
        print(f"🎮 Modo: {mode}")
        print(f"🧬 Genético: {cls.MUTATION_RATE*100}% mutación, {cls.CROSSOVER_RATE*100}% cruce")
        if cls.SELECTION_METHOD == "meeting_pool":
            print(f"🎯 Selección: MEETING_POOL, élite: {cls.ELITISM}, pool: top {int(cls.MEETING_POOL_FRACTION*100)}%")
        elif cls.SELECTION_METHOD == "tournament":
            print(f"🎯 Selección: TOURNAMENT, élite: {cls.ELITISM}, torneo: {cls.TOURNAMENT_SIZE}")
        else:
            print(f"🎯 Selección: ELITISM, élite: {cls.ELITISM}, torneo: {cls.TOURNAMENT_SIZE}")
        if cls.IMMIGRATION_ENABLED:
            #print(f"🌍 Inmigración: {cls.IMMIGRATION_COUNT} agentes cada {cls.IMMIGRATION_FREQUENCY} generaciones")
            pass
        print(f"🧠 Neuronal: {cls.INPUT_SIZE}→{cls.HIDDEN_SIZE}→{cls.OUTPUT_SIZE}")
        print(f"⚡ Agente: {cls.AGENT_SPEED} velocidad, {cls.VISION_RANGE} visión")
        print(f"🔋 Energía: {cls.AGENT_ENERGY} inicial, -{cls.AGENT_ENERGY_CONSUMPTION}/tick, +{cls.AGENT_ENERGY_GAIN_FOOD} comida")
        print(f"🌍 Mundo: {cls.SCREEN_WIDTH}x{cls.SCREEN_HEIGHT}, {cls.FOOD_COUNT} comida")
        print(f"📊 Panel: {cls.get_stats_panel_width()}px, Área juego: {cls.get_game_area_width()}px, Área pasto: {cls.get_grass_area_width()}px")
        print(f"🎨 Escalado sprites: {cls.SPRITE_SCALE_FACTOR:.2f}x, Tamaño sprite: {cls.get_scaled_sprite_size()}px")
        print("=" * 50)
