"""
Configuración centralizada para el ecosistema evolutivo.
"""

class SimulationConfig:
    """Configuración centralizada de todos los parámetros."""
    
    # === SIMULACIÓN ===
    POPULATION_SIZE = 50
    TARGET_FPS = 60
    MAX_GENERATIONS = 100    # Extendido para ver tendencias a largo plazo
    HEADLESS_MODE = False             # True = sin render (rápido), False = con render (visual)
    
    # === SISTEMA ADAPTATIVO DE TIEMPO ===
    ADAPTIVE_TIME_ENABLED = True      # Habilitar tiempo adaptativo
    BASE_TICKS = 500                 # Tiempo base inicial
    TICKS_INCREMENT_AMOUNT = 500     # Cuántos ticks aumentar cada incremento
    TICKS_INCREMENT_FREQUENCY = 2      # Cada cuántas generaciones aumentar (ej: cada 5)
    
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.15        # 15% de mutación 
    CROSSOVER_RATE = 0.5        # 70% de cruce 
    
    # === SELECCIÓN DE PADRES ===
    SELECTION_METHOD = "elitism"  # "elitism" o "tournament"
    TOURNAMENT_SIZE = 6             # Tamaño del torneo 
    ELITISM = 2                     # Mejores agentes que se mantienen 
    
    # === RED NEURONAL ===
    INPUT_SIZE = 23              # 23 sensores (8 básicos + 15 de fortalezas/árboles)
    HIDDEN_SIZE = 16             # 16 neuronas ocultas
    OUTPUT_SIZE = 4              # 4 acciones
    
    # === AGENTE ===
    AGENT_SPEED = 3.0            # Velocidad de movimiento
    VISION_RANGE = 150           # Rango de visión
    AGENT_ENERGY = 150.0         # Energía inicial
    AGENT_ENERGY_CONSUMPTION = 0.05  # Consumo de energía por tick 
    AGENT_ENERGY_GAIN_FOOD = 15      # Energía ganada al comer 
    AGENT_RADIUS = 8             # Tamaño del agente
    
    # === MUNDO ===
    SCREEN_WIDTH = 800          # Ancho de pantalla
    SCREEN_HEIGHT = 600          # Alto de pantalla
    FOOD_COUNT = 80              # Cantidad de comida inicial
    
    # === SISTEMA DE CORTE DE ÁRBOLES ===
    TREE_CUTTING_ENABLED = True   # Habilitar sistema de corte
    TREE_CUTTING_THRESHOLD = 30  # Umbral para activar corte (≤30 manzanas)
    TREE_HITS_TO_CUT = 2         # Golpes necesarios para cortar árbol
    TREE_CUT_REWARD = 7         # Fitness ganado por cortar árbol
    TREE_CUT_FOOD_REWARD = 20      # Manzanas generadas al cortar árbol
    
    # === SISTEMA DE CORTE DE HUTS ===
    HUT_CUTTING_ENABLED = True     # Habilitar sistema de corte de huts
    HUT_CUTTING_THRESHOLD = 20     # Umbral para activar corte (≤20 manzanas)
    HUT_HITS_TO_CUT = 4            # Golpes necesarios para destruir hut
    HUT_CUT_REWARD = 15            # Fitness ganado por destruir hut
    HUT_CUT_FOOD_REWARD = 30       # Manzanas generadas al destruir hut
    
    # === SISTEMA DE AGUA ===
    WATER_FITNESS_PENALTY = 5      # Fitness perdido por tick en agua (equilibrado con comida)
    
    # === SISTEMA DE FORTALEZAS/LLAVES/PUERTAS/COFRE ===
    FORTRESSES_ENABLED = True     # Habilitar sistema de fortalezas
    
    # Fortalezas
    SMALL_FORTRESS_SIZE = 5       # Tamaño de fortaleza pequeña (4x5 tiles)
    LARGE_FORTRESS_SIZE = 6       # Tamaño de fortaleza grande (6x6 tiles)
    TILE_SIZE = 32                # Tamaño de cada tile en píxeles
    
    # Llaves
    RED_KEY_SPAWN_GEN = 1         # Generación en que aparece red_key libremente
    RED_KEY_REWARD = 5            # Fitness por recoger red_key
    GOLD_KEY_REWARD = 15          # Fitness por recoger gold_key
    
    # Puertas
    DOOR_HITS_TO_OPEN = 3         # Golpes necesarios para abrir door
    DOOR_IRON_HITS_TO_OPEN = 3    # Golpes necesarios para abrir door_iron
    DOOR_OPEN_REWARD = 10         # Fitness por abrir door
    DOOR_IRON_OPEN_REWARD = 20    # Fitness por abrir door_iron
    DOOR_HIT_COOLDOWN = 120       # Cooldown entre golpes (ticks)
    
    # Cofre
    CHEST_REWARD = 50             # Fitness por abrir cofre
    
    # === RENDIMIENTO ===
    STATS_UPDATE_FREQUENCY = 5   # Actualizar stats cada N frames
    PARTICLE_UPDATE_FREQUENCY = 2  # Actualizar partículas cada N frames
    
    @classmethod
    def get_genetic_params(cls):
        """Obtiene parámetros del algoritmo genético."""
        return {
            'population_size': cls.POPULATION_SIZE,
            'mutation_rate': cls.MUTATION_RATE,
            'crossover_rate': cls.CROSSOVER_RATE,
            'elitism': cls.ELITISM,
            'selection_method': cls.SELECTION_METHOD,
            'tournament_size': cls.TOURNAMENT_SIZE
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
        print(f"🎯 Selección: {cls.SELECTION_METHOD.upper()}, élite: {cls.ELITISM}, torneo: {cls.TOURNAMENT_SIZE}")
        print(f"🧠 Neuronal: {cls.INPUT_SIZE}→{cls.HIDDEN_SIZE}→{cls.OUTPUT_SIZE}")
        print(f"⚡ Agente: {cls.AGENT_SPEED} velocidad, {cls.VISION_RANGE} visión")
        print(f"🔋 Energía: {cls.AGENT_ENERGY} inicial, -{cls.AGENT_ENERGY_CONSUMPTION}/tick, +{cls.AGENT_ENERGY_GAIN_FOOD} comida")
        print(f"🌍 Mundo: {cls.SCREEN_WIDTH}x{cls.SCREEN_HEIGHT}, {cls.FOOD_COUNT} comida")
        print("=" * 50)
