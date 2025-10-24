"""
Algoritmo genético principal para el ecosistema evolutivo.
Coordina selección, cruce y mutación para evolucionar la población.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .selection import SelectionOperator, SelectionMethod, AdaptiveSelection
from .crossover import CrossoverOperator, CrossoverMethod, AdaptiveCrossover
from .mutation import MutationOperator, MutationMethod, AdaptiveMutation


class EvolutionStrategy(Enum):
    """Estrategias de evolución disponibles."""
    STANDARD = "standard"
    ADAPTIVE = "adaptive"
    MULTI_OBJECTIVE = "multi_objective"


@dataclass
class EvolutionConfig:
    """Configuración del algoritmo genético."""
    population_size: int = 100
    max_generations: int = 200
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elitism: int = 2
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    crossover_method: CrossoverMethod = CrossoverMethod.UNIFORM
    mutation_method: MutationMethod = MutationMethod.GAUSSIAN
    tournament_size: int = 3
    mutation_strength: float = 0.1
    gene_range: Tuple[float, float] = (-1.0, 1.0)


class GeneticAlgorithm:
    """Algoritmo genético principal."""
    
    def __init__(self, config: EvolutionConfig):
        """
        Inicializa el algoritmo genético.
        
        Args:
            config: Configuración del algoritmo
        """
        self.config = config
        self.generation = 0
        self.best_fitness_history = []
        self.average_fitness_history = []
        self.diversity_history = []
        
        # Inicializar operadores
        self.selection = SelectionOperator(
            method=config.selection_method,
            tournament_size=config.tournament_size,
            elite_size=config.elitism
        )
        
        self.crossover = CrossoverOperator(
            method=config.crossover_method,
            crossover_rate=config.crossover_rate
        )
        
        self.mutation = MutationOperator(
            method=config.mutation_method,
            mutation_rate=config.mutation_rate,
            mutation_strength=config.mutation_strength,
            gene_range=config.gene_range
        )
    
    def evolve(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Evoluciona la población una generación.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Nueva población evolucionada
        """
        self.generation += 1
        
        # Calcular estadísticas
        self._update_statistics(fitness_scores)
        
        # Seleccionar élite
        elite = self.selection.select_elite(population, fitness_scores)
        
        # Seleccionar padres
        parents = self._select_parents(population, fitness_scores)
        
        # Cruzar padres
        children = self.crossover.crossover_population(parents)
        
        # Mutar hijos
        mutated_children = self.mutation.mutate_population(children)
        
        # Crear nueva población
        new_population = elite + mutated_children
        
        # Ajustar tamaño de población
        if len(new_population) > self.config.population_size:
            new_population = new_population[:self.config.population_size]
        elif len(new_population) < self.config.population_size:
            # Completar con individuos aleatorios
            while len(new_population) < self.config.population_size:
                random_parent = random.choice(population)
                new_population.append(random_parent.clone())
        
        return new_population
    
    def _select_parents(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Selecciona padres para la reproducción.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Lista de padres seleccionados
        """
        # Calcular número de padres necesarios
        num_parents = self.config.population_size - self.config.elitism
        
        # Seleccionar padres
        parents = []
        for _ in range(num_parents):
            parent = self.selection.select(population, fitness_scores, 1)[0]
            parents.append(parent)
        
        return parents
    
    def _update_statistics(self, fitness_scores: List[float]) -> None:
        """
        Actualiza estadísticas de evolución.
        
        Args:
            fitness_scores: Puntuaciones de fitness
        """
        self.best_fitness_history.append(max(fitness_scores))
        self.average_fitness_history.append(np.mean(fitness_scores))
        self.diversity_history.append(np.std(fitness_scores))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de evolución.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness_history[-1] if self.best_fitness_history else 0,
            'average_fitness': self.average_fitness_history[-1] if self.average_fitness_history else 0,
            'diversity': self.diversity_history[-1] if self.diversity_history else 0,
            'best_fitness_history': self.best_fitness_history,
            'average_fitness_history': self.average_fitness_history,
            'diversity_history': self.diversity_history
        }
    
    def reset(self) -> None:
        """Reinicia el algoritmo genético."""
        self.generation = 0
        self.best_fitness_history.clear()
        self.average_fitness_history.clear()
        self.diversity_history.clear()


class AdaptiveGeneticAlgorithm:
    """Algoritmo genético adaptativo."""
    
    def __init__(self, config: EvolutionConfig):
        """
        Inicializa el algoritmo genético adaptativo.
        
        Args:
            config: Configuración del algoritmo
        """
        self.config = config
        self.generation = 0
        self.best_fitness_history = []
        self.average_fitness_history = []
        self.diversity_history = []
        
        # Inicializar operadores adaptativos
        self.selection = AdaptiveSelection()
        self.crossover = AdaptiveCrossover()
        self.mutation = AdaptiveMutation()
    
    def evolve(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Evoluciona la población una generación.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Nueva población evolucionada
        """
        self.generation += 1
        
        # Actualizar estadísticas
        self._update_statistics(fitness_scores)
        
        # Actualizar operadores adaptativos
        self.selection.update_stats(fitness_scores)
        self.crossover.update_stats(fitness_scores)
        self.mutation.update_stats(fitness_scores)
        
        # Seleccionar élite
        elite = self.selection.select_elite(population, fitness_scores)
        
        # Seleccionar padres
        parents = self._select_parents(population, fitness_scores)
        
        # Cruzar padres
        children = self._crossover_parents(parents)
        
        # Mutar hijos
        mutated_children = self._mutate_children(children)
        
        # Crear nueva población
        new_population = elite + mutated_children
        
        # Ajustar tamaño de población
        if len(new_population) > self.config.population_size:
            new_population = new_population[:self.config.population_size]
        elif len(new_population) < self.config.population_size:
            # Completar con individuos aleatorios
            while len(new_population) < self.config.population_size:
                random_parent = random.choice(population)
                new_population.append(random_parent.clone())
        
        return new_population
    
    def _select_parents(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Selecciona padres usando selección adaptativa.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Lista de padres seleccionados
        """
        num_parents = self.config.population_size - self.config.elitism
        parents = []
        
        for _ in range(num_parents):
            parent = self.selection.select(population, fitness_scores, 1)[0]
            parents.append(parent)
        
        return parents
    
    def _crossover_parents(self, parents: List[Any]) -> List[Any]:
        """
        Cruza padres usando cruce adaptativo.
        
        Args:
            parents: Lista de padres
            
        Returns:
            Lista de hijos
        """
        children = []
        
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            child1, child2 = self.crossover.crossover(parent1, parent2)
            children.extend([child1, child2])
        
        # Si hay un número impar de padres, el último se clona
        if len(parents) % 2 == 1:
            children.append(parents[-1].clone())
        
        return children
    
    def _mutate_children(self, children: List[Any]) -> List[Any]:
        """
        Mutación de hijos usando mutación adaptativa.
        
        Args:
            children: Lista de hijos
            
        Returns:
            Lista de hijos mutados
        """
        mutated_children = []
        
        for child in children:
            mutated = self.mutation.mutate(child)
            mutated_children.append(mutated)
        
        return mutated_children
    
    def _update_statistics(self, fitness_scores: List[float]) -> None:
        """
        Actualiza estadísticas de evolución.
        
        Args:
            fitness_scores: Puntuaciones de fitness
        """
        self.best_fitness_history.append(max(fitness_scores))
        self.average_fitness_history.append(np.mean(fitness_scores))
        self.diversity_history.append(np.std(fitness_scores))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de evolución.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness_history[-1] if self.best_fitness_history else 0,
            'average_fitness': self.average_fitness_history[-1] if self.average_fitness_history else 0,
            'diversity': self.diversity_history[-1] if self.diversity_history else 0,
            'best_fitness_history': self.best_fitness_history,
            'average_fitness_history': self.average_fitness_history,
            'diversity_history': self.diversity_history,
            'mutation_parameters': self.mutation.get_parameters()
        }
    
    def reset(self) -> None:
        """Reinicia el algoritmo genético."""
        self.generation = 0
        self.best_fitness_history.clear()
        self.average_fitness_history.clear()
        self.diversity_history.clear()
        self.selection = AdaptiveSelection()
        self.crossover = AdaptiveCrossover()
        self.mutation = AdaptiveMutation()


class MultiObjectiveGA:
    """Algoritmo genético multi-objetivo."""
    
    def __init__(self, config: EvolutionConfig, objectives: List[str]):
        """
        Inicializa el algoritmo genético multi-objetivo.
        
        Args:
            config: Configuración del algoritmo
            objectives: Lista de objetivos a optimizar
        """
        self.config = config
        self.objectives = objectives
        self.generation = 0
        self.pareto_front = []
        
        # Inicializar operadores
        self.selection = SelectionOperator(
            method=SelectionMethod.TOURNAMENT,
            tournament_size=config.tournament_size,
            elite_size=config.elitism
        )
        
        self.crossover = CrossoverOperator(
            method=config.crossover_method,
            crossover_rate=config.crossover_rate
        )
        
        self.mutation = MutationOperator(
            method=config.mutation_method,
            mutation_rate=config.mutation_rate,
            mutation_strength=config.mutation_strength,
            gene_range=config.gene_range
        )
    
    def evolve(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Evoluciona la población una generación.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Nueva población evolucionada
        """
        self.generation += 1
        
        # Calcular frente de Pareto
        self._update_pareto_front(population, fitness_scores)
        
        # Seleccionar élite del frente de Pareto
        elite = self._select_pareto_elite()
        
        # Seleccionar padres
        parents = self._select_parents(population, fitness_scores)
        
        # Cruzar padres
        children = self.crossover.crossover_population(parents)
        
        # Mutar hijos
        mutated_children = self.mutation.mutate_population(children)
        
        # Crear nueva población
        new_population = elite + mutated_children
        
        # Ajustar tamaño de población
        if len(new_population) > self.config.population_size:
            new_population = new_population[:self.config.population_size]
        elif len(new_population) < self.config.population_size:
            # Completar con individuos aleatorios
            while len(new_population) < self.config.population_size:
                random_parent = random.choice(population)
                new_population.append(random_parent.clone())
        
        return new_population
    
    def _update_pareto_front(self, population: List[Any], fitness_scores: List[float]) -> None:
        """
        Actualiza el frente de Pareto.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
        """
        # Implementar algoritmo de frente de Pareto
        # Por simplicidad, usar fitness promedio como criterio
        self.pareto_front = []
        
        for i, individual in enumerate(population):
            if fitness_scores[i] > np.mean(fitness_scores):
                self.pareto_front.append(individual)
    
    def _select_pareto_elite(self) -> List[Any]:
        """
        Selecciona élite del frente de Pareto.
        
        Returns:
            Lista de individuos élite
        """
        if len(self.pareto_front) <= self.config.elitism:
            return self.pareto_front.copy()
        else:
            return random.sample(self.pareto_front, self.config.elitism)
    
    def _select_parents(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Selecciona padres para la reproducción.
        
        Args:
            population: Lista de individuos
            fitness_scores: Puntuaciones de fitness
            
        Returns:
            Lista de padres seleccionados
        """
        num_parents = self.config.population_size - self.config.elitism
        parents = []
        
        for _ in range(num_parents):
            parent = self.selection.select(population, fitness_scores, 1)[0]
            parents.append(parent)
        
        return parents
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de evolución.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'generation': self.generation,
            'pareto_front_size': len(self.pareto_front),
            'objectives': self.objectives
        }
    
    def reset(self) -> None:
        """Reinicia el algoritmo genético."""
        self.generation = 0
        self.pareto_front.clear()
