"""
Clase principal de agente para el ecosistema evolutivo.
Representa una criatura autónoma con cerebro, sensores y actuadores.
"""

import numpy as np
import random
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .brain import Brain, create_random_brain
from .brain.policy import Policy, ActionType, ActionExecutor
from .sensors import SensorArray
from .actuators import ActuatorArray


class AgentState(Enum):
    """Estados posibles de un agente."""
    ALIVE = "alive"
    DEAD = "dead"
    REPRODUCING = "reproducing"


@dataclass
class AgentStats:
    """Estadísticas de un agente."""
    age: int = 0
    energy: float = 100.0
    fitness: float = 0.0
    distance_traveled: float = 0.0
    food_eaten: int = 0
    collisions: int = 0
    offspring_count: int = 0
    generation: int = 0


class Agent:
    """Agente autónomo del ecosistema evolutivo."""
    
    def __init__(self, agent_id: int, x: float, y: float, angle: float = 0.0, 
                 config: Dict[str, Any] = None):
        """
        Inicializa un agente.
        
        Args:
            agent_id: Identificador único del agente
            x: Posición X inicial
            y: Posición Y inicial
            angle: Ángulo inicial
            config: Configuración del agente
        """
        self.id = agent_id
        self.x = x
        self.y = y
        self.angle = angle
        self.config = config or {}
        
        # Estado del agente
        self.state = AgentState.ALIVE
        self.stats = AgentStats()
        
        # Configuración de energía
        self.energy_max = self.config.get('energy_max', 100.0)
        self.energy = self.energy_max
        self.energy_move_cost = self.config.get('energy_move_cost', 1.2)
        self.energy_turn_cost = self.config.get('energy_turn_cost', 0.1)
        self.energy_decay_rate = self.config.get('energy_decay_rate', 0.1)
        self.energy_eat_gain = self.config.get('energy_eat_gain', 20.0)
        
        # Configuración de reproducción
        self.reproduction_threshold = self.config.get('reproduction_threshold', 80.0)
        self.reproduction_cost = self.config.get('reproduction_cost', 30.0)
        self.max_age = self.config.get('max_age', 1000)
        
        # Configuración de movimiento
        self.speed = self.config.get('speed', 2.0)
        self.turn_speed = self.config.get('turn_speed', 0.1)
        
        # Configuración de mundo
        self.world_width = self.config.get('world_width', 100)
        self.world_height = self.config.get('world_height', 100)
        
        # Inicializar componentes
        self._initialize_brain()
        self._initialize_sensors()
        self._initialize_actuators()
        
        # Historial de acciones
        self.action_history = []
        self.position_history = [(x, y)]
    
    def _initialize_brain(self) -> None:
        """Inicializa el cerebro del agente."""
        brain_config = self.config.get('brain', {})
        
        # Crear red neuronal
        input_size = brain_config.get('input_size', 10)
        hidden_layers = brain_config.get('hidden_layers', [16, 8])
        output_size = brain_config.get('output_size', 4)
        activation = brain_config.get('activation', 'relu')
        weight_range = brain_config.get('weight_range', (-1.0, 1.0))
        
        self.brain = create_random_brain(
            input_size, hidden_layers, output_size, activation, weight_range
        )
        
        # Crear política
        self.policy = Policy(self.brain)
    
    def _initialize_sensors(self) -> None:
        """Inicializa los sensores del agente."""
        self.sensors = SensorArray(self.config)
    
    def _initialize_actuators(self) -> None:
        """Inicializa los actuadores del agente."""
        actuator_config = self.config.get('actuators', {})
        self.actuators = ActuatorArray(actuator_config)
    
    def perceive(self, environment) -> np.ndarray:
        """
        Percibe el entorno usando los sensores.
        
        Args:
            environment: Entorno a percibir
            
        Returns:
            Array de percepciones
        """
        return self.sensors.sense_all(self, environment)
    
    def think(self, perceptions: np.ndarray) -> ActionType:
        """
        Procesa las percepciones y decide una acción.
        
        Args:
            perceptions: Array de percepciones
            
        Returns:
            Acción a realizar
        """
        return self.policy.decide(perceptions)
    
    def act(self, action: ActionType, environment) -> Dict[str, Any]:
        """
        Ejecuta una acción en el entorno.
        
        Args:
            action: Acción a ejecutar
            environment: Entorno donde actuar
            
        Returns:
            Resultado de la acción
        """
        result = self.actuators.execute_action(self, action, environment)
        
        # Registrar acción en historial
        self.action_history.append({
            'action': action,
            'tick': self.stats.age,
            'result': result
        })
        
        # Mantener historial limitado
        if len(self.action_history) > 100:
            self.action_history.pop(0)
        
        return result
    
    def update(self, environment) -> None:
        """
        Actualiza el estado del agente.
        
        Args:
            environment: Entorno donde se encuentra
        """
        if self.state != AgentState.ALIVE:
            return
        
        # Envejecer
        self.stats.age += 1
        
        # Decaimiento de energía
        self.energy -= self.energy_decay_rate
        self.energy = max(0, self.energy)
        
        # Verificar muerte por energía
        if self.energy <= 0:
            self.die("starvation")
            return
        
        # Verificar muerte por edad
        if self.stats.age >= self.max_age:
            self.die("old_age")
            return
        
        # Verificar límites del mundo
        if (self.x < 0 or self.x >= self.world_width or 
            self.y < 0 or self.y >= self.world_height):
            self.die("out_of_bounds")
            return
        
        # Registrar posición
        self.position_history.append((self.x, self.y))
        if len(self.position_history) > 1000:
            self.position_history.pop(0)
        
        # Calcular distancia recorrida
        if len(self.position_history) > 1:
            prev_x, prev_y = self.position_history[-2]
            distance = np.sqrt((self.x - prev_x)**2 + (self.y - prev_y)**2)
            self.stats.distance_traveled += distance
    
    def die(self, cause: str = "unknown") -> None:
        """
        Mata al agente.
        
        Args:
            cause: Causa de la muerte
        """
        self.state = AgentState.DEAD
        self.energy = 0
        
        # Registrar muerte
        self.action_history.append({
            'action': 'death',
            'tick': self.stats.age,
            'cause': cause
        })
    
    def can_reproduce(self) -> bool:
        """
        Verifica si el agente puede reproducirse.
        
        Returns:
            True si puede reproducirse
        """
        return (self.state == AgentState.ALIVE and 
                self.energy >= self.reproduction_threshold)
    
    def reproduce(self, partner: 'Agent' = None) -> Optional['Agent']:
        """
        Crea un descendiente.
        
        Args:
            partner: Pareja reproductiva (opcional)
            
        Returns:
            Nuevo agente descendiente o None
        """
        if not self.can_reproduce():
            return None
        
        # Costo de reproducción
        self.energy -= self.reproduction_cost
        self.stats.offspring_count += 1
        
        # Crear descendiente
        offspring_id = random.randint(100000, 999999)  # ID único
        
        # Posición cerca del padre
        offset_x = random.uniform(-5, 5)
        offset_y = random.uniform(-5, 5)
        offspring_x = max(0, min(self.x + offset_x, self.world_width))
        offspring_y = max(0, min(self.y + offset_y, self.world_height))
        
        # Crear agente descendiente
        offspring = Agent(
            offspring_id, offspring_x, offspring_y, 
            random.uniform(0, 2 * np.pi), self.config
        )
        
        # Heredar cerebro (cruce genético)
        if partner and partner.state == AgentState.ALIVE:
            # Cruce con pareja
            from .brain.mlp import crossover_brains
            child_brain1, child_brain2 = crossover_brains(self.brain, partner.brain)
            offspring.brain = child_brain1
            offspring.policy = Policy(offspring.brain)
        else:
            # Mutación del cerebro del padre
            mutation_rate = self.config.get('mutation_rate', 0.1)
            mutation_strength = self.config.get('mutation_strength', 0.1)
            offspring.brain = self.brain.clone()
            offspring.brain.mutate(mutation_rate, mutation_strength)
            offspring.policy = Policy(offspring.brain)
        
        return offspring
    
    def calculate_fitness(self) -> float:
        """
        Calcula el fitness del agente.
        
        Returns:
            Valor de fitness
        """
        fitness_config = self.config.get('fitness', {})
        
        # Componentes del fitness
        survival_weight = fitness_config.get('survival_weight', 1.0)
        food_weight = fitness_config.get('food_weight', 0.5)
        efficiency_weight = fitness_config.get('efficiency_weight', 0.3)
        diversity_weight = fitness_config.get('diversity_weight', 0.2)
        
        # Fitness por supervivencia
        survival_fitness = self.stats.age / self.max_age
        
        # Fitness por comida
        food_fitness = self.stats.food_eaten / max(1, self.stats.age)
        
        # Fitness por eficiencia (distancia/energía)
        if self.stats.distance_traveled > 0:
            efficiency_fitness = self.stats.distance_traveled / max(1, self.stats.age)
        else:
            efficiency_fitness = 0
        
        # Fitness por diversidad (comportamiento único)
        diversity_fitness = len(set(action['action'] for action in self.action_history)) / 10.0
        diversity_fitness = min(diversity_fitness, 1.0)
        
        # Calcular fitness total
        total_fitness = (
            survival_weight * survival_fitness +
            food_weight * food_fitness +
            efficiency_weight * efficiency_fitness +
            diversity_weight * diversity_fitness
        )
        
        self.stats.fitness = total_fitness
        return total_fitness
    
    def get_genome(self) -> List[float]:
        """
        Obtiene el genoma del agente.
        
        Returns:
            Lista con el genoma
        """
        return self.brain.get_genome()
    
    def set_genome(self, genome: List[float]) -> None:
        """
        Establece el genoma del agente.
        
        Args:
            genome: Nuevo genoma
        """
        self.brain.set_genome(genome)
        self.policy = Policy(self.brain)
    
    def clone(self) -> 'Agent':
        """
        Crea una copia del agente.
        
        Returns:
            Nueva instancia de Agent
        """
        clone = Agent(self.id, self.x, self.y, self.angle, self.config)
        clone.brain = self.brain.clone()
        clone.policy = Policy(clone.brain)
        clone.stats = self.stats
        return clone
    
    def get_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa del agente.
        
        Returns:
            Diccionario con información del agente
        """
        return {
            'id': self.id,
            'position': (self.x, self.y),
            'angle': self.angle,
            'state': self.state.value,
            'energy': self.energy,
            'stats': {
                'age': self.stats.age,
                'fitness': self.stats.fitness,
                'distance_traveled': self.stats.distance_traveled,
                'food_eaten': self.stats.food_eaten,
                'collisions': self.stats.collisions,
                'offspring_count': self.stats.offspring_count,
                'generation': self.stats.generation
            },
            'brain_size': self.brain.mlp.get_genome_size(),
            'sensor_info': self.sensors.get_sensor_info(),
            'actuator_info': self.actuators.get_actuator_info()
        }
    
    def reset(self, x: float = None, y: float = None, angle: float = None) -> None:
        """
        Reinicia el agente a un estado inicial.
        
        Args:
            x: Nueva posición X (opcional)
            y: Nueva posición Y (opcional)
            angle: Nuevo ángulo (opcional)
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if angle is not None:
            self.angle = angle
        
        self.state = AgentState.ALIVE
        self.energy = self.energy_max
        self.stats = AgentStats()
        self.action_history.clear()
        self.position_history = [(self.x, self.y)]
