"""
Operadores de cruce para el algoritmo genético.
Implementa diferentes métodos de cruce genético.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum


class CrossoverMethod(Enum):
    """Métodos de cruce disponibles."""
    UNIFORM = "uniform"
    ONE_POINT = "one_point"
    TWO_POINT = "two_point"
    ARITHMETIC = "arithmetic"
    BLEND = "blend"


class CrossoverOperator:
    """Operador de cruce genético."""
    
    def __init__(self, method: CrossoverMethod = CrossoverMethod.UNIFORM, 
                 crossover_rate: float = 0.7, alpha: float = 0.5):
        """
        Inicializa el operador de cruce.
        
        Args:
            method: Método de cruce a usar
            crossover_rate: Probabilidad de cruce
            alpha: Parámetro para cruce aritmético y blend
        """
        self.method = method
        self.crossover_rate = crossover_rate
        self.alpha = alpha
    
    def crossover(self, parent1: Any, parent2: Any) -> Tuple[Any, Any]:
        """
        Realiza cruce entre dos padres.
        
        Args:
            parent1: Primer padre
            parent2: Segundo padre
            
        Returns:
            Tupla con los dos hijos
        """
        # Verificar si se debe realizar el cruce
        if random.random() > self.crossover_rate:
            return parent1.clone(), parent2.clone()
        
        # Obtener genomas
        genome1 = parent1.get_genome()
        genome2 = parent2.get_genome()
        
        # Asegurar que tengan el mismo tamaño
        if len(genome1) != len(genome2):
            min_size = min(len(genome1), len(genome2))
            genome1 = genome1[:min_size]
            genome2 = genome2[:min_size]
        
        # Realizar cruce según el método
        if self.method == CrossoverMethod.UNIFORM:
            child1_genome, child2_genome = self._uniform_crossover(genome1, genome2)
        elif self.method == CrossoverMethod.ONE_POINT:
            child1_genome, child2_genome = self._one_point_crossover(genome1, genome2)
        elif self.method == CrossoverMethod.TWO_POINT:
            child1_genome, child2_genome = self._two_point_crossover(genome1, genome2)
        elif self.method == CrossoverMethod.ARITHMETIC:
            child1_genome, child2_genome = self._arithmetic_crossover(genome1, genome2)
        elif self.method == CrossoverMethod.BLEND:
            child1_genome, child2_genome = self._blend_crossover(genome1, genome2)
        else:
            child1_genome, child2_genome = self._uniform_crossover(genome1, genome2)
        
        # Crear hijos
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        child1.set_genome(child1_genome)
        child2.set_genome(child2_genome)
        
        return child1, child2
    
    def _uniform_crossover(self, genome1: List[float], genome2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce uniforme.
        
        Args:
            genome1: Genoma del primer padre
            genome2: Genoma del segundo padre
            
        Returns:
            Tupla con los genomas de los hijos
        """
        child1_genome = []
        child2_genome = []
        
        for g1, g2 in zip(genome1, genome2):
            if random.random() < 0.5:
                child1_genome.append(g1)
                child2_genome.append(g2)
            else:
                child1_genome.append(g2)
                child2_genome.append(g1)
        
        return child1_genome, child2_genome
    
    def _one_point_crossover(self, genome1: List[float], genome2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce de un punto.
        
        Args:
            genome1: Genoma del primer padre
            genome2: Genoma del segundo padre
            
        Returns:
            Tupla con los genomas de los hijos
        """
        if len(genome1) <= 1:
            return genome1.copy(), genome2.copy()
        
        crossover_point = random.randint(1, len(genome1) - 1)
        
        child1_genome = genome1[:crossover_point] + genome2[crossover_point:]
        child2_genome = genome2[:crossover_point] + genome1[crossover_point:]
        
        return child1_genome, child2_genome
    
    def _two_point_crossover(self, genome1: List[float], genome2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce de dos puntos.
        
        Args:
            genome1: Genoma del primer padre
            genome2: Genoma del segundo padre
            
        Returns:
            Tupla con los genomas de los hijos
        """
        if len(genome1) <= 2:
            return genome1.copy(), genome2.copy()
        
        point1 = random.randint(1, len(genome1) - 2)
        point2 = random.randint(point1 + 1, len(genome1) - 1)
        
        child1_genome = (genome1[:point1] + 
                        genome2[point1:point2] + 
                        genome1[point2:])
        child2_genome = (genome2[:point1] + 
                        genome1[point1:point2] + 
                        genome2[point2:])
        
        return child1_genome, child2_genome
    
    def _arithmetic_crossover(self, genome1: List[float], genome2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce aritmético.
        
        Args:
            genome1: Genoma del primer padre
            genome2: Genoma del segundo padre
            
        Returns:
            Tupla con los genomas de los hijos
        """
        child1_genome = []
        child2_genome = []
        
        for g1, g2 in zip(genome1, genome2):
            child1_gene = self.alpha * g1 + (1 - self.alpha) * g2
            child2_gene = (1 - self.alpha) * g1 + self.alpha * g2
            
            child1_genome.append(child1_gene)
            child2_genome.append(child2_gene)
        
        return child1_genome, child2_genome
    
    def _blend_crossover(self, genome1: List[float], genome2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Cruce blend (BLX-α).
        
        Args:
            genome1: Genoma del primer padre
            genome2: Genoma del segundo padre
            
        Returns:
            Tupla con los genomas de los hijos
        """
        child1_genome = []
        child2_genome = []
        
        for g1, g2 in zip(genome1, genome2):
            # Calcular rango
            min_gene = min(g1, g2)
            max_gene = max(g1, g2)
            range_size = max_gene - min_gene
            
            # Expandir rango
            expanded_min = min_gene - self.alpha * range_size
            expanded_max = max_gene + self.alpha * range_size
            
            # Generar genes aleatorios en el rango expandido
            child1_gene = random.uniform(expanded_min, expanded_max)
            child2_gene = random.uniform(expanded_min, expanded_max)
            
            child1_genome.append(child1_gene)
            child2_genome.append(child2_gene)
        
        return child1_genome, child2_genome
    
    def crossover_population(self, parents: List[Any]) -> List[Any]:
        """
        Realiza cruce en toda la población.
        
        Args:
            parents: Lista de padres
            
        Returns:
            Lista de hijos
        """
        children = []
        
        # Cruzar padres en pares
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            child1, child2 = self.crossover(parent1, parent2)
            children.extend([child1, child2])
        
        # Si hay un número impar de padres, el último se clona
        if len(parents) % 2 == 1:
            children.append(parents[-1].clone())
        
        return children


class AdaptiveCrossover:
    """Cruce adaptativo que ajusta parámetros según el progreso."""
    
    def __init__(self, initial_rate: float = 0.7):
        """
        Inicializa el cruce adaptativo.
        
        Args:
            initial_rate: Tasa inicial de cruce
        """
        self.crossover_rate = initial_rate
        self.generation = 0
        self.fitness_history = []
        self.diversity_history = []
    
    def crossover(self, parent1: Any, parent2: Any) -> Tuple[Any, Any]:
        """
        Realiza cruce adaptativo.
        
        Args:
            parent1: Primer padre
            parent2: Segundo padre
            
        Returns:
            Tupla con los dos hijos
        """
        # Ajustar tasa de cruce
        self._adapt_crossover_rate()
        
        # Usar cruce uniforme con tasa adaptativa
        operator = CrossoverOperator(
            method=CrossoverMethod.UNIFORM,
            crossover_rate=self.crossover_rate
        )
        
        return operator.crossover(parent1, parent2)
    
    def _adapt_crossover_rate(self) -> None:
        """Adapta la tasa de cruce según el progreso."""
        if len(self.fitness_history) < 5:
            return  # No hay suficiente historial
        
        # Calcular tendencias
        recent_fitness = self.fitness_history[-5:]
        recent_diversity = self.diversity_history[-5:]
        
        fitness_trend = np.mean(np.diff(recent_fitness))
        diversity_trend = np.mean(np.diff(recent_diversity))
        
        # Si el fitness está estancado, aumentar la tasa de cruce
        if abs(fitness_trend) < 0.01:
            self.crossover_rate = min(0.9, self.crossover_rate + 0.1)
        # Si la diversidad es muy baja, aumentar la tasa de cruce
        elif np.mean(recent_diversity) < 0.1:
            self.crossover_rate = min(0.9, self.crossover_rate + 0.05)
        # Si la diversidad es muy alta, reducir la tasa de cruce
        elif np.mean(recent_diversity) > 0.8:
            self.crossover_rate = max(0.3, self.crossover_rate - 0.05)
        else:
            # Mantener tasa actual
            pass
        
        self.generation += 1
    
    def update_stats(self, fitness_scores: List[float]) -> None:
        """
        Actualiza estadísticas para adaptación.
        
        Args:
            fitness_scores: Puntuaciones de fitness de la generación
        """
        self.fitness_history.append(np.mean(fitness_scores))
        self.diversity_history.append(np.std(fitness_scores))
