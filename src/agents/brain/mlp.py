"""
Red neuronal MLP para los agentes del ecosistema evolutivo.
Implementa una red neuronal simple con PyTorch.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple, Optional
import random


class MLP(nn.Module):
    """Red neuronal MLP para agentes."""
    
    def __init__(self, input_size: int, hidden_layers: List[int], output_size: int, 
                 activation: str = "relu", weight_range: Tuple[float, float] = (-1.0, 1.0)):
        """
        Inicializa la red neuronal.
        
        Args:
            input_size: Número de entradas
            hidden_layers: Lista con tamaños de capas ocultas
            output_size: Número de salidas
            activation: Función de activación ('relu', 'tanh', 'sigmoid')
            weight_range: Rango para inicialización de pesos
        """
        super(MLP, self).__init__()
        
        self.input_size = input_size
        self.hidden_layers = hidden_layers
        self.output_size = output_size
        self.activation = activation
        self.weight_range = weight_range
        
        # Construir capas
        self.layers = nn.ModuleList()
        
        # Primera capa (entrada -> primera oculta)
        if hidden_layers:
            self.layers.append(nn.Linear(input_size, hidden_layers[0]))
            
            # Capas ocultas intermedias
            for i in range(len(hidden_layers) - 1):
                self.layers.append(nn.Linear(hidden_layers[i], hidden_layers[i + 1]))
            
            # Capa de salida
            self.layers.append(nn.Linear(hidden_layers[-1], output_size))
        else:
            # Sin capas ocultas
            self.layers.append(nn.Linear(input_size, output_size))
        
        # Inicializar pesos
        self._initialize_weights()
    
    def _initialize_weights(self) -> None:
        """Inicializa los pesos de la red con valores aleatorios."""
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                # Inicialización uniforme en el rango especificado
                nn.init.uniform_(layer.weight, self.weight_range[0], self.weight_range[1])
                nn.init.uniform_(layer.bias, self.weight_range[0], self.weight_range[1])
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass de la red.
        
        Args:
            x: Tensor de entrada
            
        Returns:
            Tensor de salida
        """
        for i, layer in enumerate(self.layers[:-1]):
            x = layer(x)
            x = self._apply_activation(x)
        
        # Capa de salida sin activación
        x = self.layers[-1](x)
        return x
    
    def _apply_activation(self, x: torch.Tensor) -> torch.Tensor:
        """
        Aplica la función de activación.
        
        Args:
            x: Tensor de entrada
            
        Returns:
            Tensor con activación aplicada
        """
        if self.activation == "relu":
            return F.relu(x)
        elif self.activation == "tanh":
            return torch.tanh(x)
        elif self.activation == "sigmoid":
            return torch.sigmoid(x)
        else:
            return x
    
    def get_weights_as_list(self) -> List[float]:
        """
        Obtiene todos los pesos de la red como una lista.
        
        Returns:
            Lista con todos los pesos
        """
        weights = []
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                weights.extend(layer.weight.data.flatten().tolist())
                weights.extend(layer.bias.data.flatten().tolist())
        return weights
    
    def set_weights_from_list(self, weights: List[float]) -> None:
        """
        Establece los pesos de la red desde una lista.
        
        Args:
            weights: Lista con todos los pesos
        """
        weight_idx = 0
        
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                # Pesos
                weight_size = layer.weight.numel()
                layer.weight.data = torch.tensor(
                    weights[weight_idx:weight_idx + weight_size]
                ).reshape(layer.weight.shape)
                weight_idx += weight_size
                
                # Sesgos
                bias_size = layer.bias.numel()
                layer.bias.data = torch.tensor(
                    weights[weight_idx:weight_idx + bias_size]
                ).reshape(layer.bias.shape)
                weight_idx += bias_size
    
    def mutate_weights(self, mutation_rate: float, mutation_strength: float = 0.1) -> None:
        """
        Mutación de pesos para algoritmo genético.
        
        Args:
            mutation_rate: Probabilidad de mutación por peso
            mutation_strength: Fuerza de la mutación
        """
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                # Mutar pesos
                mask = torch.rand_like(layer.weight) < mutation_rate
                noise = torch.randn_like(layer.weight) * mutation_strength
                layer.weight.data[mask] += noise[mask]
                
                # Mutar sesgos
                mask = torch.rand_like(layer.bias) < mutation_rate
                noise = torch.randn_like(layer.bias) * mutation_strength
                layer.bias.data[mask] += noise[mask]
    
    def clone(self) -> 'MLP':
        """
        Crea una copia de la red.
        
        Returns:
            Nueva instancia de MLP con los mismos pesos
        """
        clone = MLP(
            self.input_size,
            self.hidden_layers,
            self.output_size,
            self.activation,
            self.weight_range
        )
        
        # Copiar pesos
        clone.load_state_dict(self.state_dict())
        return clone
    
    def get_genome_size(self) -> int:
        """
        Obtiene el tamaño del genoma (número total de parámetros).
        
        Returns:
            Número total de parámetros
        """
        total_params = 0
        for layer in self.layers:
            if isinstance(layer, nn.Linear):
                total_params += layer.weight.numel() + layer.bias.numel()
        return total_params


class Brain:
    """Cerebro de un agente que encapsula la red neuronal."""
    
    def __init__(self, mlp: MLP):
        """
        Inicializa el cerebro.
        
        Args:
            mlp: Red neuronal MLP
        """
        self.mlp = mlp
        self.input_size = mlp.input_size
        self.output_size = mlp.output_size
    
    def think(self, inputs: np.ndarray) -> np.ndarray:
        """
        Procesa las entradas y devuelve las acciones.
        
        Args:
            inputs: Array de entradas (percepciones)
            
        Returns:
            Array de acciones
        """
        # Convertir a tensor
        input_tensor = torch.tensor(inputs, dtype=torch.float32)
        
        # Forward pass
        with torch.no_grad():
            output_tensor = self.mlp(input_tensor)
        
        # Convertir a numpy
        return output_tensor.numpy()
    
    def get_genome(self) -> List[float]:
        """
        Obtiene el genoma del cerebro.
        
        Returns:
            Lista con todos los parámetros
        """
        return self.mlp.get_weights_as_list()
    
    def set_genome(self, genome: List[float]) -> None:
        """
        Establece el genoma del cerebro.
        
        Args:
            genome: Lista con todos los parámetros
        """
        self.mlp.set_weights_from_list(genome)
    
    def mutate(self, mutation_rate: float, mutation_strength: float = 0.1) -> None:
        """
        Mutación del cerebro.
        
        Args:
            mutation_rate: Probabilidad de mutación
            mutation_strength: Fuerza de la mutación
        """
        self.mlp.mutate_weights(mutation_rate, mutation_strength)
    
    def clone(self) -> 'Brain':
        """
        Crea una copia del cerebro.
        
        Returns:
            Nueva instancia de Brain
        """
        return Brain(self.mlp.clone())


def create_random_brain(input_size: int, hidden_layers: List[int], output_size: int,
                       activation: str = "relu", weight_range: Tuple[float, float] = (-1.0, 1.0)) -> Brain:
    """
    Crea un cerebro aleatorio.
    
    Args:
        input_size: Número de entradas
        hidden_layers: Lista con tamaños de capas ocultas
        output_size: Número de salidas
        activation: Función de activación
        weight_range: Rango para inicialización de pesos
        
    Returns:
        Nuevo cerebro aleatorio
    """
    mlp = MLP(input_size, hidden_layers, output_size, activation, weight_range)
    return Brain(mlp)


def crossover_brains(brain1: Brain, brain2: Brain, crossover_rate: float = 0.5) -> Tuple[Brain, Brain]:
    """
    Cruza dos cerebros para crear descendencia.
    
    Args:
        brain1: Primer cerebro padre
        brain2: Segundo cerebro padre
        crossover_rate: Probabilidad de cruce por gen
        
    Returns:
        Tupla con los dos cerebros hijos
    """
    genome1 = brain1.get_genome()
    genome2 = brain2.get_genome()
    
    # Asegurar que tengan el mismo tamaño
    min_size = min(len(genome1), len(genome2))
    genome1 = genome1[:min_size]
    genome2 = genome2[:min_size]
    
    # Crear genomas hijos
    child1_genome = []
    child2_genome = []
    
    for g1, g2 in zip(genome1, genome2):
        if random.random() < crossover_rate:
            # Cruce
            child1_genome.append(g2)
            child2_genome.append(g1)
        else:
            # Sin cruce
            child1_genome.append(g1)
            child2_genome.append(g2)
    
    # Crear cerebros hijos
    child1 = brain1.clone()
    child2 = brain2.clone()
    
    child1.set_genome(child1_genome)
    child2.set_genome(child2_genome)
    
    return child1, child2
