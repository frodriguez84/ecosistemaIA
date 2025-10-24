"""
Sistema de evaluación de fitness para el ecosistema evolutivo.
Calcula la aptitud de los agentes basada en múltiples criterios.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FitnessComponent(Enum):
    """Componentes de fitness disponibles."""
    SURVIVAL = "survival"
    FOOD = "food"
    EFFICIENCY = "efficiency"
    DIVERSITY = "diversity"
    REPRODUCTION = "reproduction"
    EXPLORATION = "exploration"


@dataclass
class FitnessConfig:
    """Configuración del sistema de fitness."""
    survival_weight: float = 1.0
    food_weight: float = 0.5
    efficiency_weight: float = 0.3
    diversity_weight: float = 0.2
    reproduction_weight: float = 0.4
    exploration_weight: float = 0.2
    max_age: int = 1000
    energy_max: float = 100.0


class FitnessEvaluator:
    """Evaluador de fitness para agentes."""
    
    def __init__(self, config: FitnessConfig):
        """
        Inicializa el evaluador de fitness.
        
        Args:
            config: Configuración del fitness
        """
        self.config = config
        self.fitness_history = []
        self.component_history = []
    
    def evaluate(self, agent, environment=None) -> float:
        """
        Evalúa el fitness de un agente.
        
        Args:
            agent: Agente a evaluar
            environment: Entorno del agente (opcional)
            
        Returns:
            Valor de fitness
        """
        # Calcular componentes de fitness
        survival_fitness = self._calculate_survival_fitness(agent)
        food_fitness = self._calculate_food_fitness(agent)
        efficiency_fitness = self._calculate_efficiency_fitness(agent)
        diversity_fitness = self._calculate_diversity_fitness(agent)
        reproduction_fitness = self._calculate_reproduction_fitness(agent)
        exploration_fitness = self._calculate_exploration_fitness(agent)
        
        # Combinar componentes
        total_fitness = (
            self.config.survival_weight * survival_fitness +
            self.config.food_weight * food_fitness +
            self.config.efficiency_weight * efficiency_fitness +
            self.config.diversity_weight * diversity_fitness +
            self.config.reproduction_weight * reproduction_fitness +
            self.config.exploration_weight * exploration_fitness
        )
        
        # Guardar historial
        self.fitness_history.append(total_fitness)
        self.component_history.append({
            'survival': survival_fitness,
            'food': food_fitness,
            'efficiency': efficiency_fitness,
            'diversity': diversity_fitness,
            'reproduction': reproduction_fitness,
            'exploration': exploration_fitness
        })
        
        return total_fitness
    
    def _calculate_survival_fitness(self, agent) -> float:
        """
        Calcula el fitness por supervivencia.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de supervivencia
        """
        if agent.state.value == 'dead':
            return 0.0
        
        # Fitness basado en la edad y energía
        age_fitness = agent.stats.age / self.config.max_age
        energy_fitness = agent.energy / self.config.energy_max
        
        # Combinar factores
        survival_fitness = (age_fitness + energy_fitness) / 2
        
        return min(survival_fitness, 1.0)
    
    def _calculate_food_fitness(self, agent) -> float:
        """
        Calcula el fitness por alimentación.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de alimentación
        """
        if agent.stats.age == 0:
            return 0.0
        
        # Fitness basado en la cantidad de comida consumida
        food_per_tick = agent.stats.food_eaten / max(1, agent.stats.age)
        
        # Normalizar
        food_fitness = min(food_per_tick / 10.0, 1.0)  # Máximo 10 comida por tick
        
        return food_fitness
    
    def _calculate_efficiency_fitness(self, agent) -> float:
        """
        Calcula el fitness por eficiencia.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de eficiencia
        """
        if agent.stats.age == 0:
            return 0.0
        
        # Fitness basado en la distancia recorrida por unidad de energía
        if agent.stats.distance_traveled > 0:
            energy_used = self.config.energy_max - agent.energy
            if energy_used > 0:
                efficiency = agent.stats.distance_traveled / energy_used
                efficiency_fitness = min(efficiency / 10.0, 1.0)  # Normalizar
            else:
                efficiency_fitness = 0.0
        else:
            efficiency_fitness = 0.0
        
        return efficiency_fitness
    
    def _calculate_diversity_fitness(self, agent) -> float:
        """
        Calcula el fitness por diversidad de comportamiento.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de diversidad
        """
        if len(agent.action_history) < 2:
            return 0.0
        
        # Contar acciones únicas
        unique_actions = set(action['action'] for action in agent.action_history)
        diversity_ratio = len(unique_actions) / len(agent.action_history)
        
        return diversity_ratio
    
    def _calculate_reproduction_fitness(self, agent) -> float:
        """
        Calcula el fitness por reproducción.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de reproducción
        """
        # Fitness basado en el número de descendientes
        offspring_fitness = min(agent.stats.offspring_count / 5.0, 1.0)  # Máximo 5 descendientes
        
        return offspring_fitness
    
    def _calculate_exploration_fitness(self, agent) -> float:
        """
        Calcula el fitness por exploración.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Fitness de exploración
        """
        if len(agent.position_history) < 2:
            return 0.0
        
        # Calcular área explorada
        positions = agent.position_history
        if len(positions) < 3:
            return 0.0
        
        # Calcular área del polígono formado por las posiciones
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        # Usar fórmula de Shoelace para calcular área
        area = 0.5 * abs(sum(x_coords[i] * y_coords[i + 1] - x_coords[i + 1] * y_coords[i] 
                            for i in range(len(positions) - 1)))
        
        # Normalizar área
        max_area = 10000.0  # Área máxima posible
        exploration_fitness = min(area / max_area, 1.0)
        
        return exploration_fitness
    
    def evaluate_population(self, population: List[Any], environment=None) -> List[float]:
        """
        Evalúa el fitness de toda la población.
        
        Args:
            population: Lista de agentes
            environment: Entorno de los agentes (opcional)
            
        Returns:
            Lista de valores de fitness
        """
        fitness_scores = []
        
        for agent in population:
            fitness = self.evaluate(agent, environment)
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def get_fitness_components(self, agent) -> Dict[str, float]:
        """
        Obtiene los componentes de fitness de un agente.
        
        Args:
            agent: Agente a evaluar
            
        Returns:
            Diccionario con componentes de fitness
        """
        return {
            'survival': self._calculate_survival_fitness(agent),
            'food': self._calculate_food_fitness(agent),
            'efficiency': self._calculate_efficiency_fitness(agent),
            'diversity': self._calculate_diversity_fitness(agent),
            'reproduction': self._calculate_reproduction_fitness(agent),
            'exploration': self._calculate_exploration_fitness(agent)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de fitness.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.fitness_history:
            return {}
        
        return {
            'total_evaluations': len(self.fitness_history),
            'average_fitness': np.mean(self.fitness_history),
            'best_fitness': max(self.fitness_history),
            'worst_fitness': min(self.fitness_history),
            'fitness_std': np.std(self.fitness_history),
            'component_averages': {
                component: np.mean([comp[component] for comp in self.component_history])
                for component in ['survival', 'food', 'efficiency', 'diversity', 'reproduction', 'exploration']
            }
        }
    
    def reset(self) -> None:
        """Reinicia el evaluador de fitness."""
        self.fitness_history.clear()
        self.component_history.clear()


class AdaptiveFitness:
    """Sistema de fitness adaptativo que ajusta pesos según el progreso."""
    
    def __init__(self, config: FitnessConfig):
        """
        Inicializa el sistema de fitness adaptativo.
        
        Args:
            config: Configuración inicial del fitness
        """
        self.config = config
        self.generation = 0
        self.fitness_history = []
        self.component_history = []
        self.adaptation_rate = 0.1
    
    def evaluate(self, agent, environment=None) -> float:
        """
        Evalúa el fitness de un agente.
        
        Args:
            agent: Agente a evaluar
            environment: Entorno del agente (opcional)
            
        Returns:
            Valor de fitness
        """
        # Calcular componentes de fitness
        survival_fitness = self._calculate_survival_fitness(agent)
        food_fitness = self._calculate_food_fitness(agent)
        efficiency_fitness = self._calculate_efficiency_fitness(agent)
        diversity_fitness = self._calculate_diversity_fitness(agent)
        reproduction_fitness = self._calculate_reproduction_fitness(agent)
        exploration_fitness = self._calculate_exploration_fitness(agent)
        
        # Combinar componentes con pesos adaptativos
        total_fitness = (
            self.config.survival_weight * survival_fitness +
            self.config.food_weight * food_fitness +
            self.config.efficiency_weight * efficiency_fitness +
            self.config.diversity_weight * diversity_fitness +
            self.config.reproduction_weight * reproduction_fitness +
            self.config.exploration_weight * exploration_fitness
        )
        
        # Guardar historial
        self.fitness_history.append(total_fitness)
        self.component_history.append({
            'survival': survival_fitness,
            'food': food_fitness,
            'efficiency': efficiency_fitness,
            'diversity': diversity_fitness,
            'reproduction': reproduction_fitness,
            'exploration': exploration_fitness
        })
        
        return total_fitness
    
    def _calculate_survival_fitness(self, agent) -> float:
        """Calcula el fitness por supervivencia."""
        if agent.state.value == 'dead':
            return 0.0
        
        age_fitness = agent.stats.age / self.config.max_age
        energy_fitness = agent.energy / self.config.energy_max
        
        survival_fitness = (age_fitness + energy_fitness) / 2
        return min(survival_fitness, 1.0)
    
    def _calculate_food_fitness(self, agent) -> float:
        """Calcula el fitness por alimentación."""
        if agent.stats.age == 0:
            return 0.0
        
        food_per_tick = agent.stats.food_eaten / max(1, agent.stats.age)
        food_fitness = min(food_per_tick / 10.0, 1.0)
        
        return food_fitness
    
    def _calculate_efficiency_fitness(self, agent) -> float:
        """Calcula el fitness por eficiencia."""
        if agent.stats.age == 0:
            return 0.0
        
        if agent.stats.distance_traveled > 0:
            energy_used = self.config.energy_max - agent.energy
            if energy_used > 0:
                efficiency = agent.stats.distance_traveled / energy_used
                efficiency_fitness = min(efficiency / 10.0, 1.0)
            else:
                efficiency_fitness = 0.0
        else:
            efficiency_fitness = 0.0
        
        return efficiency_fitness
    
    def _calculate_diversity_fitness(self, agent) -> float:
        """Calcula el fitness por diversidad de comportamiento."""
        if len(agent.action_history) < 2:
            return 0.0
        
        unique_actions = set(action['action'] for action in agent.action_history)
        diversity_ratio = len(unique_actions) / len(agent.action_history)
        
        return diversity_ratio
    
    def _calculate_reproduction_fitness(self, agent) -> float:
        """Calcula el fitness por reproducción."""
        offspring_fitness = min(agent.stats.offspring_count / 5.0, 1.0)
        return offspring_fitness
    
    def _calculate_exploration_fitness(self, agent) -> float:
        """Calcula el fitness por exploración."""
        if len(agent.position_history) < 2:
            return 0.0
        
        positions = agent.position_history
        if len(positions) < 3:
            return 0.0
        
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        area = 0.5 * abs(sum(x_coords[i] * y_coords[i + 1] - x_coords[i + 1] * y_coords[i] 
                            for i in range(len(positions) - 1)))
        
        max_area = 10000.0
        exploration_fitness = min(area / max_area, 1.0)
        
        return exploration_fitness
    
    def adapt_weights(self, population_fitness: List[float]) -> None:
        """
        Adapta los pesos de fitness según el progreso.
        
        Args:
            population_fitness: Lista de fitness de la población
        """
        if len(self.component_history) < 10:
            return  # No hay suficiente historial
        
        # Calcular correlaciones entre componentes y fitness total
        correlations = {}
        for component in ['survival', 'food', 'efficiency', 'diversity', 'reproduction', 'exploration']:
            component_values = [comp[component] for comp in self.component_history[-10:]]
            fitness_values = self.fitness_history[-10:]
            
            if len(component_values) > 1 and len(fitness_values) > 1:
                correlation = np.corrcoef(component_values, fitness_values)[0, 1]
                correlations[component] = correlation if not np.isnan(correlation) else 0.0
            else:
                correlations[component] = 0.0
        
        # Ajustar pesos basados en correlaciones
        for component, correlation in correlations.items():
            if correlation > 0.5:  # Alta correlación positiva
                weight_attr = f"{component}_weight"
                if hasattr(self.config, weight_attr):
                    current_weight = getattr(self.config, weight_attr)
                    new_weight = min(1.0, current_weight + self.adaptation_rate)
                    setattr(self.config, weight_attr, new_weight)
            elif correlation < -0.5:  # Alta correlación negativa
                weight_attr = f"{component}_weight"
                if hasattr(self.config, weight_attr):
                    current_weight = getattr(self.config, weight_attr)
                    new_weight = max(0.0, current_weight - self.adaptation_rate)
                    setattr(self.config, weight_attr, new_weight)
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """
        Obtiene los pesos adaptativos actuales.
        
        Returns:
            Diccionario con pesos actuales
        """
        return {
            'survival_weight': self.config.survival_weight,
            'food_weight': self.config.food_weight,
            'efficiency_weight': self.config.efficiency_weight,
            'diversity_weight': self.config.diversity_weight,
            'reproduction_weight': self.config.reproduction_weight,
            'exploration_weight': self.config.exploration_weight
        }
    
    def reset(self) -> None:
        """Reinicia el sistema de fitness adaptativo."""
        self.generation = 0
        self.fitness_history.clear()
        self.component_history.clear()
