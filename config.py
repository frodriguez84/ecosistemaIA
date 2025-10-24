"""
Configuración centralizada para el ecosistema evolutivo.
"""

class SimulationConfig:
    """Configuración centralizada de todos los parámetros."""
    
    # === SIMULACIÓN ===
    MAX_TICKS_PER_GENERATION = 10000
    POPULATION_SIZE = 30
    TARGET_FPS = 60
    MAX_GENERATIONS = 50
    
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.25         # 25% de mutación (MUY AUMENTADO para diversidad)
    CROSSOVER_RATE = 0.8         # 80% de cruce (OPTIMIZADO)
    
    # === SELECCIÓN DE PADRES ===
    SELECTION_METHOD = "tournament"  # "elitism" o "tournament"
    TOURNAMENT_SIZE = 7             # Tamaño del torneo (MUY AUMENTADO para diversidad)
    ELITISM = 1                     # Mejores agentes que se mantienen (solo si SELECTION_METHOD = "elitism")
    
    # === RED NEURONAL ===
    INPUT_SIZE = 8               # 8 sensores
    HIDDEN_SIZE = 20             # 20 neuronas ocultas (AUMENTADO para capacidad)
    OUTPUT_SIZE = 4              # 4 acciones
    
    # === AGENTE ===
    AGENT_SPEED = 3.0            # Velocidad de movimiento
    VISION_RANGE = 150           # Rango de visión
    AGENT_ENERGY = 100.0         # Energía inicial
    AGENT_ENERGY_CONSUMPTION = 0.05  # Consumo de energía por tick
    AGENT_ENERGY_GAIN_FOOD = 10      # Energía ganada al comer
    AGENT_RADIUS = 8             # Tamaño del agente
    
    # === MUNDO ===
    SCREEN_WIDTH = 1200          # Ancho de pantalla
    SCREEN_HEIGHT = 800          # Alto de pantalla
    FOOD_COUNT = 40              # Cantidad de comida inicial
    
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
