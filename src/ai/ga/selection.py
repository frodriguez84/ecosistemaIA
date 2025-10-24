"""
Operadores de selección para el algoritmo genético.
Implementa diferentes métodos de selección de individuos.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum


class SelectionMethod(Enum):
    """Métodos de selección disponibles."""
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    ELITISM = "elitism"


class SelectionOperator:
    """Operador de selección genética."""
    
    def __init__(self, method: SelectionMethod = SelectionMethod.TOURNAMENT, 
                 tournament_size: int = 3, elite_size: int = 2):
        """
        Inicializa el operador de selección.
        
        Args:
            method: Método de selección a usar
            tournament_size: Tamaño del torneo (para selección por torneo)
            elite_size: Número de individuos élite a preservar
        """
        self.method = method
        self.tournament_size = tournament_size
        self.elite_size = elite_size
    
    def select(self, population: List[Any], fitness_scores: List[float], 
               num_parents: int = 2) -> List[Any]:
        """
        Selecciona individuos de la población.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            
        Returns:
            Lista de individuos seleccionados
        """
        if self.method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection(population, fitness_scores, num_parents)
        elif self.method == SelectionMethod.ROULETTE:
            return self._roulette_selection(population, fitness_scores, num_parents)
        elif self.method == SelectionMethod.RANK:
            return self._rank_selection(population, fitness_scores, num_parents)
        else:
            return self._tournament_selection(population, fitness_scores, num_parents)
    
    def _tournament_selection(self, population: List[Any], fitness_scores: List[float], 
                             num_parents: int) -> List[Any]:
        """
        Selección por torneo.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            
        Returns:
            Lista de individuos seleccionados
        """
        selected = []
        
        for _ in range(num_parents):
            # Seleccionar individuos aleatorios para el torneo
            tournament_indices = random.sample(range(len(population)), 
                                             min(self.tournament_size, len(population)))
            
            # Encontrar el mejor del torneo
            best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
            selected.append(population[best_index])
        
        return selected
    
    def _roulette_selection(self, population: List[Any], fitness_scores: List[float], 
                           num_parents: int) -> List[Any]:
        """
        Selección por ruleta.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            
        Returns:
            Lista de individuos seleccionados
        """
        # Normalizar fitness scores para que sean positivos
        min_fitness = min(fitness_scores)
        if min_fitness < 0:
            normalized_scores = [score - min_fitness + 1 for score in fitness_scores]
        else:
            normalized_scores = fitness_scores
        
        # Calcular probabilidades
        total_fitness = sum(normalized_scores)
        if total_fitness == 0:
            # Si todos tienen fitness 0, selección aleatoria
            return random.sample(population, num_parents)
        
        probabilities = [score / total_fitness for score in normalized_scores]
        
        # Seleccionar individuos
        selected = []
        for _ in range(num_parents):
            r = random.random()
            cumulative = 0
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(population[i])
                    break
        
        return selected
    
    def _rank_selection(self, population: List[Any], fitness_scores: List[float], 
                     num_parents: int) -> List[Any]:
        """
        Selección por rango.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            
        Returns:
            Lista de individuos seleccionados
        """
        # Crear lista de índices ordenados por fitness
        sorted_indices = sorted(range(len(population)), 
                               key=lambda i: fitness_scores[i], reverse=True)
        
        # Asignar pesos basados en el rango
        weights = []
        for i, idx in enumerate(sorted_indices):
            weight = len(population) - i  # Mejor rango = mayor peso
            weights.append(weight)
        
        # Normalizar pesos
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # Seleccionar individuos
        selected = []
        for _ in range(num_parents):
            r = random.random()
            cumulative = 0
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(population[sorted_indices[i]])
                    break
        
        return selected
    
    def select_elite(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """
        Selecciona los mejores individuos (élite).
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            
        Returns:
            Lista de individuos élite
        """
        if self.elite_size <= 0:
            return []
        
        # Crear lista de (individuo, fitness) y ordenar por fitness
        individuals_with_fitness = list(zip(population, fitness_scores))
        individuals_with_fitness.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar los mejores
        elite = [individual for individual, _ in individuals_with_fitness[:self.elite_size]]
        return elite
    
    def select_diverse(self, population: List[Any], fitness_scores: List[float], 
                      num_parents: int, diversity_threshold: float = 0.1) -> List[Any]:
        """
        Selección que promueve la diversidad.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            diversity_threshold: Umbral de diversidad
            
        Returns:
            Lista de individuos seleccionados
        """
        selected = []
        remaining_indices = list(range(len(population)))
        
        # Seleccionar el mejor individuo primero
        best_index = max(range(len(population)), key=lambda i: fitness_scores[i])
        selected.append(population[best_index])
        remaining_indices.remove(best_index)
        
        # Seleccionar individuos diversos
        for _ in range(num_parents - 1):
            if not remaining_indices:
                break
            
            # Calcular diversidad para cada individuo restante
            diversity_scores = []
            for idx in remaining_indices:
                diversity = self._calculate_diversity(population[idx], selected)
                fitness = fitness_scores[idx]
                # Combinar fitness y diversidad
                combined_score = fitness + diversity_threshold * diversity
                diversity_scores.append(combined_score)
            
            # Seleccionar el mejor balance entre fitness y diversidad
            best_diverse_index = remaining_indices[np.argmax(diversity_scores)]
            selected.append(population[best_diverse_index])
            remaining_indices.remove(best_diverse_index)
        
        return selected
    
    def _calculate_diversity(self, individual: Any, selected: List[Any]) -> float:
        """
        Calcula la diversidad de un individuo respecto a los ya seleccionados.
        
        Args:
            individual: Individuo a evaluar
            selected: Lista de individuos ya seleccionados
            
        Returns:
            Valor de diversidad
        """
        if not selected:
            return 1.0
        
        # Calcular distancia promedio a los individuos seleccionados
        distances = []
        for selected_individual in selected:
            distance = self._calculate_genetic_distance(individual, selected_individual)
            distances.append(distance)
        
        return np.mean(distances)
    
    def _calculate_genetic_distance(self, individual1: Any, individual2: Any) -> float:
        """
        Calcula la distancia genética entre dos individuos.
        
        Args:
            individual1: Primer individuo
            individual2: Segundo individuo
            
        Returns:
            Distancia genética
        """
        # Asumir que los individuos tienen un método get_genome()
        if hasattr(individual1, 'get_genome') and hasattr(individual2, 'get_genome'):
            genome1 = individual1.get_genome()
            genome2 = individual2.get_genome()
            
            # Calcular distancia euclidiana
            if len(genome1) == len(genome2):
                distance = np.sqrt(sum((g1 - g2)**2 for g1, g2 in zip(genome1, genome2)))
                return distance
            else:
                return 1.0  # Genomas de diferente tamaño
        else:
            return 0.5  # Valor por defecto si no se puede calcular


class AdaptiveSelection:
    """Selección adaptativa que cambia el método según el progreso."""
    
    def __init__(self, initial_method: SelectionMethod = SelectionMethod.TOURNAMENT):
        """
        Inicializa la selección adaptativa.
        
        Args:
            initial_method: Método inicial de selección
        """
        self.current_method = initial_method
        self.generation = 0
        self.fitness_history = []
        self.diversity_history = []
    
    def select(self, population: List[Any], fitness_scores: List[float], 
               num_parents: int = 2) -> List[Any]:
        """
        Selecciona individuos usando el método adaptativo.
        
        Args:
            population: Lista de individuos
            fitness_scores: Lista de puntuaciones de fitness
            num_parents: Número de padres a seleccionar
            
        Returns:
            Lista de individuos seleccionados
        """
        # Actualizar historial
        self.fitness_history.append(np.mean(fitness_scores))
        self.diversity_history.append(np.std(fitness_scores))
        
        # Cambiar método si es necesario
        self._adapt_selection_method()
        
        # Usar el método actual
        operator = SelectionOperator(self.current_method)
        return operator.select(population, fitness_scores, num_parents)
    
    def _adapt_selection_method(self) -> None:
        """Adapta el método de selección según el progreso."""
        if len(self.fitness_history) < 10:
            return  # No hay suficiente historial
        
        # Calcular tendencias
        recent_fitness = self.fitness_history[-5:]
        recent_diversity = self.diversity_history[-5:]
        
        fitness_trend = np.mean(np.diff(recent_fitness))
        diversity_trend = np.mean(np.diff(recent_diversity))
        
        # Si el fitness está estancado y la diversidad es baja, usar selección diversa
        if abs(fitness_trend) < 0.01 and np.mean(recent_diversity) < 0.1:
            self.current_method = SelectionMethod.RANK
        # Si el fitness está mejorando, usar selección por torneo
        elif fitness_trend > 0:
            self.current_method = SelectionMethod.TOURNAMENT
        # Si la diversidad es muy alta, usar selección por ruleta
        elif np.mean(recent_diversity) > 0.5:
            self.current_method = SelectionMethod.ROULETTE
        else:
            self.current_method = SelectionMethod.TOURNAMENT
        
        self.generation += 1
