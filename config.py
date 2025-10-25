"""
Configuración centralizada para el ecosistema evolutivo.
"""

class SimulationConfig:
    """Configuración centralizada de todos los parámetros."""
    
    # === SIMULACIÓN ===
    MAX_TICKS_PER_GENERATION = 3000   # AUMENTADO para asegurar supervivientes
    POPULATION_SIZE = 30
    TARGET_FPS = 60
    MAX_GENERATIONS = 50
    
    # === SISTEMA ADAPTATIVO DE TIEMPO ===
    ADAPTIVE_TIME_ENABLED = True      # Habilitar tiempo adaptativo
    BASE_TICKS = 3000                 # Tiempo base (AUMENTADO para más supervivencia)
    COMPLEX_TICKS = 8000              # Tiempo para tareas complejas (generaciones 11+)
    TRANSITION_GENERATION = 10        # Generación donde cambia el tiempo
    
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.20         # 20% de mutación (AUMENTADO para combatir convergencia)
    CROSSOVER_RATE = 0.7         # 70% de cruce (REDUCIDO para más exploración)
    
    # === SELECCIÓN DE PADRES ===
    SELECTION_METHOD = "tournament"  # "elitism" o "tournament"
    TOURNAMENT_SIZE = 10             # Tamaño del torneo (AUMENTADO: más presión selectiva distribuida)
    ELITISM = 2                     # Mejores agentes que se mantienen (AUMENTADO para estabilidad)
    
    # === RED NEURONAL ===
    INPUT_SIZE = 8               # 8 sensores
    HIDDEN_SIZE = 20             # 20 neuronas ocultas (AUMENTADO para capacidad)
    OUTPUT_SIZE = 4              # 4 acciones
    
    # === AGENTE ===
    AGENT_SPEED = 3.0            # Velocidad de movimiento
    VISION_RANGE = 150           # Rango de visión
    AGENT_ENERGY = 200.0         # Energía inicial
    AGENT_ENERGY_CONSUMPTION = 0.04  # Consumo de energía por tick (REDUCIDO para más supervivencia)
    AGENT_ENERGY_GAIN_FOOD = 15      # Energía ganada al comer (AUMENTADO para compensar consumo)
    AGENT_RADIUS = 8             # Tamaño del agente
    
    # === MUNDO ===
    SCREEN_WIDTH = 1200          # Ancho de pantalla
    SCREEN_HEIGHT = 800          # Alto de pantalla
    FOOD_COUNT = 60              # Cantidad de comida inicial
    
    # === SISTEMA DE CORTE DE ÁRBOLES ===
    TREE_CUTTING_ENABLED = True   # Habilitar sistema de corte
    TREE_CUTTING_THRESHOLD = 25  # Umbral para activar corte (≤25 manzanas)
    TREE_HITS_TO_CUT = 3         # Golpes necesarios para cortar árbol
    TREE_CUT_REWARD = 20         # Fitness ganado por cortar árbol
    TREE_CUT_FOOD_REWARD = 8      # Manzanas generadas al cortar árbol
    
    # === SISTEMA FUTURO (LLAVES/PUERTAS/COFRE) ===
    KEYS_SYSTEM_ENABLED = False   # Habilitar sistema de llaves (FUTURO)
    DOORS_SYSTEM_ENABLED = False  # Habilitar sistema de puertas (FUTURO)
    CHEST_SYSTEM_ENABLED = False  # Habilitar sistema de cofre (FUTURO)
    
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
            'max_ticks': cls.MAX_TICKS_PER_GENERATION,
            'population_size': cls.POPULATION_SIZE,
            'target_fps': cls.TARGET_FPS,
            'max_generations': cls.MAX_GENERATIONS
        }
    
    @classmethod
    def print_config(cls):
        """Imprime toda la configuración."""
        print("🔧 CONFIGURACIÓN ACTUAL:")
        print("=" * 50)
        print(f"📊 Simulación: {cls.MAX_TICKS_PER_GENERATION} ticks, {cls.POPULATION_SIZE} agentes")
        print(f"🧬 Genético: {cls.MUTATION_RATE*100}% mutación, {cls.CROSSOVER_RATE*100}% cruce")
        print(f"🎯 Selección: {cls.SELECTION_METHOD.upper()}, élite: {cls.ELITISM}, torneo: {cls.TOURNAMENT_SIZE}")
        print(f"🧠 Neuronal: {cls.INPUT_SIZE}→{cls.HIDDEN_SIZE}→{cls.OUTPUT_SIZE}")
        print(f"⚡ Agente: {cls.AGENT_SPEED} velocidad, {cls.VISION_RANGE} visión")
        print(f"🔋 Energía: {cls.AGENT_ENERGY} inicial, -{cls.AGENT_ENERGY_CONSUMPTION}/tick, +{cls.AGENT_ENERGY_GAIN_FOOD} comida")
        print(f"🌍 Mundo: {cls.SCREEN_WIDTH}x{cls.SCREEN_HEIGHT}, {cls.FOOD_COUNT} comida")
        print("=" * 50)
