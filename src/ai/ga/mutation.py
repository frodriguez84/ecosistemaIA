"""
Operadores de mutación para el algoritmo genético.
Implementa diferentes métodos de mutación genética.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum


class MutationMethod(Enum):
    """Métodos de mutación disponibles."""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    POLYNOMIAL = "polynomial"
    BOUNDARY = "boundary"


class MutationOperator:
    """Operador de mutación genética."""
    
    def __init__(self, method: MutationMethod = MutationMethod.GAUSSIAN,
                 mutation_rate: float = 0.1, mutation_strength: float = 0.1,
                 gene_range: Tuple[float, float] = (-1.0, 1.0)):
        """
        Inicializa el operador de mutación.
        
        Args:
            method: Método de mutación a usar
            mutation_rate: Probabilidad de mutación por gen
            mutation_strength: Fuerza de la mutación
            gene_range: Rango de valores válidos para los genes
        """
        self.method = method
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.gene_range = gene_range
    
    def mutate(self, individual: Any) -> Any:
        """
        Mutación de un individuo.
        
        Args:
            individual: Individuo a mutar
            
        Returns:
            Individuo mutado
        """
        # Clonar individuo
        mutated = individual.clone()
        
        # Obtener genoma
        genome = mutated.get_genome()
        
        # Mutar genoma
        mutated_genome = self._mutate_genome(genome)
        
        # Establecer genoma mutado
        mutated.set_genome(mutated_genome)
        
        return mutated
    
    def _mutate_genome(self, genome: List[float]) -> List[float]:
        """
        Mutación del genoma.
        
        Args:
            genome: Genoma a mutar
            
        Returns:
            Genoma mutado
        """
        mutated_genome = []
        
        for gene in genome:
            if random.random() < self.mutation_rate:
                # Mutar gen
                if self.method == MutationMethod.GAUSSIAN:
                    mutated_gene = self._gaussian_mutation(gene)
                elif self.method == MutationMethod.UNIFORM:
                    mutated_gene = self._uniform_mutation(gene)
                elif self.method == MutationMethod.POLYNOMIAL:
                    mutated_gene = self._polynomial_mutation(gene)
                elif self.method == MutationMethod.BOUNDARY:
                    mutated_gene = self._boundary_mutation(gene)
                else:
                    mutated_gene = self._gaussian_mutation(gene)
                
                # Aplicar límites
                mutated_gene = self._apply_bounds(mutated_gene)
                mutated_genome.append(mutated_gene)
            else:
                mutated_genome.append(gene)
        
        return mutated_genome
    
    def _gaussian_mutation(self, gene: float) -> float:
        """
        Mutación gaussiana.
        
        Args:
            gene: Gen a mutar
            
        Returns:
            Gen mutado
        """
        noise = np.random.normal(0, self.mutation_strength)
        return gene + noise
    
    def _uniform_mutation(self, gene: float) -> float:
        """
        Mutación uniforme.
        
        Args:
            gene: Gen a mutar
            
        Returns:
            Gen mutado
        """
        # Generar valor aleatorio en el rango
        min_val, max_val = self.gene_range
        return random.uniform(min_val, max_val)
    
    def _polynomial_mutation(self, gene: float) -> float:
        """
        Mutación polinomial.
        
        Args:
            gene: Gen a mutar
            
        Returns:
            Gen mutado
        """
        # Calcular distancia a los límites
        min_val, max_val = self.gene_range
        delta1 = (gene - min_val) / (max_val - min_val)
        delta2 = (max_val - gene) / (max_val - min_val)
        
        # Parámetro de distribución
        eta_m = 20.0
        
        # Calcular factor de mutación
        if random.random() < 0.5:
            if delta1 < 1:
                delta = (2 * random.random() + (1 - 2 * random.random()) * 
                        (1 - delta1) ** (eta_m + 1)) ** (1 / (eta_m + 1)) - 1
            else:
                delta = 0
        else:
            if delta2 < 1:
                delta = 1 - (2 * (1 - random.random()) + 2 * (random.random() - 0.5) * 
                            (1 - delta2) ** (eta_m + 1)) ** (1 / (eta_m + 1))
            else:
                delta = 0
        
        # Aplicar mutación
        mutated_gene = gene + delta * (max_val - min_val)
        return mutated_gene
    
    def _boundary_mutation(self, gene: float) -> float:
        """
        Mutación de límite.
        
        Args:
            gene: Gen a mutar
            
        Returns:
            Gen mutado
        """
        min_val, max_val = self.gene_range
        
        if random.random() < 0.5:
            return min_val
        else:
            return max_val
    
    def _apply_bounds(self, gene: float) -> float:
        """
        Aplica límites al gen.
        
        Args:
            gene: Gen a limitar
            
        Returns:
            Gen con límites aplicados
        """
        min_val, max_val = self.gene_range
        return max(min_val, min(max_val, gene))
    
    def mutate_population(self, population: List[Any]) -> List[Any]:
        """
        Mutación de toda la población.
        
        Args:
            population: Lista de individuos
            
        Returns:
            Lista de individuos mutados
        """
        mutated_population = []
        
        for individual in population:
            mutated = self.mutate(individual)
            mutated_population.append(mutated)
        
        return mutated_population


class AdaptiveMutation:
    """Mutación adaptativa que ajusta parámetros según el progreso."""
    
    def __init__(self, initial_rate: float = 0.1, initial_strength: float = 0.1):
        """
        Inicializa la mutación adaptativa.
        
        Args:
            initial_rate: Tasa inicial de mutación
            initial_strength: Fuerza inicial de mutación
        """
        self.mutation_rate = initial_rate
        self.mutation_strength = initial_strength
        self.generation = 0
        self.fitness_history = []
        self.diversity_history = []
    
    def mutate(self, individual: Any) -> Any:
        """
        Realiza mutación adaptativa.
        
        Args:
            individual: Individuo a mutar
            
        Returns:
            Individuo mutado
        """
        # Ajustar parámetros de mutación
        self._adapt_mutation_parameters()
        
        # Usar mutación gaussiana con parámetros adaptativos
        operator = MutationOperator(
            method=MutationMethod.GAUSSIAN,
            mutation_rate=self.mutation_rate,
            mutation_strength=self.mutation_strength
        )
        
        return operator.mutate(individual)
    
    def _adapt_mutation_parameters(self) -> None:
        """Adapta los parámetros de mutación según el progreso."""
        if len(self.fitness_history) < 5:
            return  # No hay suficiente historial
        
        # Calcular tendencias
        recent_fitness = self.fitness_history[-5:]
        recent_diversity = self.diversity_history[-5:]
        
        fitness_trend = np.mean(np.diff(recent_fitness))
        diversity_trend = np.mean(np.diff(recent_diversity))
        
        # Si el fitness está estancado, aumentar la mutación
        if abs(fitness_trend) < 0.01:
            self.mutation_rate = min(0.5, self.mutation_rate + 0.05)
            self.mutation_strength = min(0.5, self.mutation_strength + 0.05)
        # Si la diversidad es muy baja, aumentar la mutación
        elif np.mean(recent_diversity) < 0.1:
            self.mutation_rate = min(0.3, self.mutation_rate + 0.02)
            self.mutation_strength = min(0.3, self.mutation_strength + 0.02)
        # Si la diversidad es muy alta, reducir la mutación
        elif np.mean(recent_diversity) > 0.8:
            self.mutation_rate = max(0.01, self.mutation_rate - 0.01)
            self.mutation_strength = max(0.01, self.mutation_strength - 0.01)
        else:
            # Mantener parámetros actuales
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
    
    def get_parameters(self) -> Dict[str, float]:
        """
        Obtiene los parámetros actuales de mutación.
        
        Returns:
            Diccionario con parámetros de mutación
        """
        return {
            'mutation_rate': self.mutation_rate,
            'mutation_strength': self.mutation_strength,
            'generation': self.generation
        }


class MultiMutation:
    """Mutación múltiple que combina diferentes métodos."""
    
    def __init__(self, methods: List[MutationMethod] = None, 
                 method_weights: List[float] = None):
        """
        Inicializa la mutación múltiple.
        
        Args:
            methods: Lista de métodos de mutación
            method_weights: Pesos para cada método
        """
        self.methods = methods or [MutationMethod.GAUSSIAN, MutationMethod.UNIFORM]
        self.method_weights = method_weights or [0.7, 0.3]
        
        # Normalizar pesos
        total_weight = sum(self.method_weights)
        self.method_weights = [w / total_weight for w in self.method_weights]
    
    def mutate(self, individual: Any, mutation_rate: float = 0.1, 
               mutation_strength: float = 0.1) -> Any:
        """
        Realiza mutación múltiple.
        
        Args:
            individual: Individuo a mutar
            mutation_rate: Tasa de mutación
            mutation_strength: Fuerza de mutación
            
        Returns:
            Individuo mutado
        """
        # Seleccionar método de mutación
        method = np.random.choice(self.methods, p=self.method_weights)
        
        # Crear operador con el método seleccionado
        operator = MutationOperator(
            method=method,
            mutation_rate=mutation_rate,
            mutation_strength=mutation_strength
        )
        
        return operator.mutate(individual)
