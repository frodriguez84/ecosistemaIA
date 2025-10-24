"""
Configuración de pytest para los tests del ecosistema evolutivo.
"""

import pytest
import numpy as np
import random
from src.agents import Agent
from src.ecosistema.config.loader import load_config


@pytest.fixture
def sample_config():
    """Configuración de muestra para tests."""
    return {
        'simulation': {
            'map_size': [100, 100],
            'population': 50,
            'ticks_per_epoch': 1000,
            'max_epochs': 10
        },
        'agent': {
            'energy_max': 100.0,
            'energy_move_cost': 1.0,
            'energy_turn_cost': 0.1,
            'energy_decay_rate': 0.1,
            'energy_eat_gain': 20.0,
            'reproduction_threshold': 80.0,
            'reproduction_cost': 30.0,
            'max_age': 1000
        },
        'ga': {
            'population_size': 50,
            'mutation_rate': 0.1,
            'crossover_rate': 0.7,
            'elitism': 2,
            'max_generations': 10
        },
        'neural_net': {
            'input_size': 10,
            'hidden_layers': [16, 8],
            'output_size': 4,
            'activation': 'relu',
            'weight_range': [-1.0, 1.0]
        },
        'fitness': {
            'survival_weight': 1.0,
            'food_weight': 0.5,
            'efficiency_weight': 0.3,
            'diversity_weight': 0.2
        }
    }


@pytest.fixture
def sample_agent(sample_config):
    """Agente de muestra para tests."""
    return Agent(1, 50.0, 50.0, 0.0, sample_config)


@pytest.fixture
def sample_agents(sample_config):
    """Lista de agentes de muestra para tests."""
    agents = []
    for i in range(10):
        x = random.uniform(10, 90)
        y = random.uniform(10, 90)
        angle = random.uniform(0, 2 * np.pi)
        agent = Agent(i, x, y, angle, sample_config)
        agents.append(agent)
    return agents


@pytest.fixture
def sample_world(sample_config):
    """Mundo de muestra para tests."""
    from src.env import World
    return World(sample_config)


@pytest.fixture
def sample_genetic_algorithm(sample_config):
    """Algoritmo genético de muestra para tests."""
    from src.ai import GeneticAlgorithm, EvolutionConfig
    
    ga_config = EvolutionConfig(
        population_size=sample_config['ga']['population_size'],
        max_generations=sample_config['ga']['max_generations'],
        mutation_rate=sample_config['ga']['mutation_rate'],
        crossover_rate=sample_config['ga']['crossover_rate'],
        elitism=sample_config['ga']['elitism']
    )
    
    return GeneticAlgorithm(ga_config)


@pytest.fixture
def sample_fitness_evaluator(sample_config):
    """Evaluador de fitness de muestra para tests."""
    from src.ai import FitnessEvaluator, FitnessConfig
    
    fitness_config = FitnessConfig(
        survival_weight=sample_config['fitness']['survival_weight'],
        food_weight=sample_config['fitness']['food_weight'],
        efficiency_weight=sample_config['fitness']['efficiency_weight'],
        diversity_weight=sample_config['fitness']['diversity_weight']
    )
    
    return FitnessEvaluator(fitness_config)


@pytest.fixture
def sample_metrics_collector():
    """Recolector de métricas de muestra para tests."""
    from src.analytics import MetricsCollector
    
    config = {
        'collection_interval': 10,
        'save_interval': 100,
        'max_metrics': 1000
    }
    
    return MetricsCollector(config)


@pytest.fixture
def sample_behavior_analyzer():
    """Analizador de comportamiento de muestra para tests."""
    from src.analytics import BehaviorAnalyzer, ClusteringConfig
    
    clustering_config = ClusteringConfig(
        method='kmeans',
        n_clusters=3
    )
    
    return BehaviorAnalyzer(clustering_config)


@pytest.fixture
def sample_logger():
    """Logger de muestra para tests."""
    from src.analytics import SimulationLogger
    
    config = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'test_simulation.log',
        'metrics_file': 'test_metrics.csv'
    }
    
    return SimulationLogger(config)


@pytest.fixture
def sample_renderer():
    """Renderizador de muestra para tests."""
    from src.ui import SimulationRenderer, RenderConfig
    
    render_config = RenderConfig(
        window_size=(800, 600),
        fps=60,
        show_grid=True,
        show_vision=False
    )
    
    return SimulationRenderer(render_config)


@pytest.fixture
def sample_hud():
    """HUD de muestra para tests."""
    from src.ui import HUD, HUDConfig
    
    hud_config = HUDConfig(
        position=(10, 10),
        width=300,
        height=400
    )
    
    return HUD(hud_config)


@pytest.fixture
def sample_controls():
    """Controles de muestra para tests."""
    from src.ui import SimulationControls, ControlConfig
    
    control_config = ControlConfig()
    return SimulationControls(control_config)


@pytest.fixture
def sample_simulation_data():
    """Datos de simulación de muestra para tests."""
    return {
        'tick': 100,
        'epoch': 5,
        'generation': 10,
        'alive_agents': 45,
        'dead_agents': 5,
        'average_fitness': 0.75,
        'best_fitness': 0.95,
        'average_energy': 60.0,
        'average_age': 250.0,
        'total_distance': 1250.0,
        'total_food': 150,
        'total_collisions': 25,
        'total_offspring': 8
    }


@pytest.fixture
def sample_fitness_scores():
    """Puntuaciones de fitness de muestra para tests."""
    return [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 0.95]


@pytest.fixture
def sample_genome():
    """Genoma de muestra para tests."""
    return [0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8, 0.9, -1.0]


@pytest.fixture
def sample_perceptions():
    """Percepciones de muestra para tests."""
    return np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])


@pytest.fixture
def sample_actions():
    """Acciones de muestra para tests."""
    from src.agents.brain.policy import ActionType
    return [
        ActionType.MOVE_FORWARD,
        ActionType.TURN_LEFT,
        ActionType.TURN_RIGHT,
        ActionType.EAT
    ]


@pytest.fixture
def sample_environment_data():
    """Datos de entorno de muestra para tests."""
    return {
        'food_positions': [(10, 10), (20, 20), (30, 30)],
        'obstacle_positions': [(5, 5), (15, 15), (25, 25)],
        'world_size': (100, 100),
        'total_food': 15,
        'total_obstacles': 3
    }


@pytest.fixture
def sample_clustering_result():
    """Resultado de clustering de muestra para tests."""
    return {
        'cluster_labels': [0, 1, 2, 0, 1, 2, 0, 1, 2, 0],
        'n_clusters': 3,
        'cluster_stats': {
            0: {'size': 4, 'mean': [0.1, 0.2, 0.3]},
            1: {'size': 3, 'mean': [0.4, 0.5, 0.6]},
            2: {'size': 3, 'mean': [0.7, 0.8, 0.9]}
        },
        'quality_metrics': {
            'silhouette_score': 0.75,
            'calinski_harabasz_score': 150.0
        }
    }


@pytest.fixture
def sample_metrics_data():
    """Datos de métricas de muestra para tests."""
    return {
        'fitness': {
            'average': 0.75,
            'best': 0.95,
            'worst': 0.25,
            'std': 0.15
        },
        'population': {
            'total': 50,
            'alive': 45,
            'dead': 5
        },
        'behavior': {
            'total_distance': 1250.0,
            'total_food': 150,
            'total_collisions': 25
        },
        'environment': {
            'food_positions': 20,
            'total_food': 100,
            'obstacle_positions': 10
        }
    }


@pytest.fixture
def sample_performance_metrics():
    """Métricas de rendimiento de muestra para tests."""
    return {
        'cpu_percent': 25.5,
        'memory_usage': 128.5,
        'memory_available': 1024.0,
        'disk_usage': 45.2,
        'timestamp': 1234567890.0
    }


@pytest.fixture
def sample_timer():
    """Timer de muestra para tests."""
    from src.utils.profiling import Timer
    return Timer("test_timer")


@pytest.fixture
def sample_profiler():
    """Profiler de muestra para tests."""
    from src.utils.profiling import Profiler
    return Profiler()


@pytest.fixture
def sample_random_state():
    """Estado aleatorio de muestra para tests."""
    return {
        'python_random': (3, (12345, 67890, 11111), None),
        'numpy_random': ('MT19937', np.array([12345, 67890, 11111, 22222], dtype=np.uint32), 0, 0, 0.0)
    }


@pytest.fixture
def sample_geometry_data():
    """Datos geométricos de muestra para tests."""
    return {
        'points': [(0, 0), (10, 0), (10, 10), (0, 10)],
        'center': (5, 5),
        'radius': 5.0,
        'angle': np.pi / 4
    }


@pytest.fixture
def sample_event_data():
    """Datos de evento de muestra para tests."""
    return {
        'event_type': 'agent_birth',
        'timestamp': 1234567890.0,
        'data': {
            'agent_id': 1,
            'parent_ids': [0, 2]
        },
        'agent_id': 1
    }


@pytest.fixture
def sample_log_entry():
    """Entrada de log de muestra para tests."""
    from src.analytics.logger import LogEntry, LogLevel
    
    return LogEntry(
        timestamp=1234567890.0,
        level=LogLevel.INFO,
        message="Test log entry",
        module="test",
        data={'test_key': 'test_value'}
    )


@pytest.fixture
def sample_metric_data():
    """Datos de métrica de muestra para tests."""
    from src.analytics.metrics import MetricData, MetricType
    
    return MetricData(
        timestamp=1234567890.0,
        tick=100,
        epoch=5,
        generation=10,
        metric_type=MetricType.FITNESS,
        value=0.75,
        metadata={'test': True}
    )


@pytest.fixture
def sample_clustering_config():
    """Configuración de clustering de muestra para tests."""
    from src.analytics.clustering import ClusteringConfig, ClusteringMethod
    
    return ClusteringConfig(
        method=ClusteringMethod.KMEANS,
        n_clusters=3,
        eps=0.5,
        min_samples=5,
        linkage='ward',
        random_state=42
    )


@pytest.fixture
def sample_evolution_config():
    """Configuración de evolución de muestra para tests."""
    from src.ai.ga.evolve import EvolutionConfig, EvolutionStrategy
    from src.ai.ga.selection import SelectionMethod
    from src.ai.ga.crossover import CrossoverMethod
    from src.ai.ga.mutation import MutationMethod
    
    return EvolutionConfig(
        population_size=50,
        max_generations=10,
        mutation_rate=0.1,
        crossover_rate=0.7,
        elitism=2,
        selection_method=SelectionMethod.TOURNAMENT,
        crossover_method=CrossoverMethod.UNIFORM,
        mutation_method=MutationMethod.GAUSSIAN,
        tournament_size=3,
        mutation_strength=0.1,
        gene_range=(-1.0, 1.0)
    )


@pytest.fixture
def sample_fitness_config():
    """Configuración de fitness de muestra para tests."""
    from src.ai.fitness import FitnessConfig, FitnessComponent
    
    return FitnessConfig(
        survival_weight=1.0,
        food_weight=0.5,
        efficiency_weight=0.3,
        diversity_weight=0.2,
        reproduction_weight=0.4,
        exploration_weight=0.2,
        max_age=1000,
        energy_max=100.0
    )


@pytest.fixture
def sample_render_config():
    """Configuración de renderizado de muestra para tests."""
    from src.ui.renderer import RenderConfig, RenderMode
    
    return RenderConfig(
        window_size=(800, 600),
        fps=60,
        show_grid=True,
        show_vision=False,
        show_metrics=True,
        background_color=(50, 50, 50),
        agent_color=(255, 100, 100),
        food_color=(100, 255, 100),
        obstacle_color=(100, 100, 100),
        grid_color=(80, 80, 80),
        text_color=(255, 255, 255)
    )


@pytest.fixture
def sample_hud_config():
    """Configuración de HUD de muestra para tests."""
    from src.ui.hud import HUDConfig, HUDMode
    
    return HUDConfig(
        position=(10, 10),
        width=300,
        height=400,
        background_color=(0, 0, 0, 128),
        text_color=(255, 255, 255),
        border_color=(100, 100, 100),
        font_size=18,
        line_spacing=20,
        show_border=True,
        show_background=True
    )


@pytest.fixture
def sample_control_config():
    """Configuración de controles de muestra para tests."""
    from src.ui.controls import ControlConfig, ControlAction
    
    return ControlConfig(
        pause_key=32,  # Space
        reset_key=114,  # R
        speed_up_key=61,  # Plus
        slow_down_key=45,  # Minus
        grid_key=103,  # G
        vision_key=118,  # V
        metrics_key=109,  # M
        debug_key=100,  # D
        save_key=115,  # S
        load_key=108,  # L
        export_key=101,  # E
        quit_key=27,  # Escape
        camera_up_key=273,  # Up
        camera_down_key=274,  # Down
        camera_left_key=276,  # Left
        camera_right_key=275,  # Right
        zoom_in_key=61,  # Equals
        zoom_out_key=48,  # Zero
        camera_speed=5.0,
        zoom_speed=0.1,
        speed_multiplier=0.1
    )
