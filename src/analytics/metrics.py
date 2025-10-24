"""
Sistema de métricas para el ecosistema evolutivo.
Recopila y analiza datos de la simulación.
"""

import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class MetricType(Enum):
    """Tipos de métricas disponibles."""
    FITNESS = "fitness"
    POPULATION = "population"
    BEHAVIOR = "behavior"
    ENVIRONMENT = "environment"
    EVOLUTION = "evolution"


@dataclass
class MetricData:
    """Datos de una métrica."""
    timestamp: float
    tick: int
    epoch: int
    generation: int
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = None


class MetricsCollector:
    """Recolector de métricas del ecosistema."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el recolector de métricas.
        
        Args:
            config: Configuración del recolector
        """
        self.config = config or {}
        self.metrics = []
        self.current_tick = 0
        self.current_epoch = 0
        self.current_generation = 0
        
        # Configuración
        self.collection_interval = self.config.get('collection_interval', 10)
        self.save_interval = self.config.get('save_interval', 100)
        self.max_metrics = self.config.get('max_metrics', 10000)
    
    def collect_fitness_metrics(self, agents: List[Any]) -> None:
        """
        Recopila métricas de fitness.
        
        Args:
            agents: Lista de agentes
        """
        if not agents:
            return
        
        # Calcular métricas de fitness
        fitness_scores = [agent.stats.fitness for agent in agents if hasattr(agent.stats, 'fitness')]
        
        if fitness_scores:
            self._add_metric(MetricType.FITNESS, 'average_fitness', np.mean(fitness_scores))
            self._add_metric(MetricType.FITNESS, 'best_fitness', max(fitness_scores))
            self._add_metric(MetricType.FITNESS, 'worst_fitness', min(fitness_scores))
            self._add_metric(MetricType.FITNESS, 'fitness_std', np.std(fitness_scores))
    
    def collect_population_metrics(self, agents: List[Any]) -> None:
        """
        Recopila métricas de población.
        
        Args:
            agents: Lista de agentes
        """
        if not agents:
            return
        
        # Contar agentes por estado
        alive_count = sum(1 for agent in agents if agent.state.value == 'alive')
        dead_count = len(agents) - alive_count
        
        # Calcular métricas de edad y energía
        ages = [agent.stats.age for agent in agents if agent.state.value == 'alive']
        energies = [agent.energy for agent in agents if agent.state.value == 'alive']
        
        self._add_metric(MetricType.POPULATION, 'total_agents', len(agents))
        self._add_metric(MetricType.POPULATION, 'alive_agents', alive_count)
        self._add_metric(MetricType.POPULATION, 'dead_agents', dead_count)
        
        if ages:
            self._add_metric(MetricType.POPULATION, 'average_age', np.mean(ages))
            self._add_metric(MetricType.POPULATION, 'max_age', max(ages))
        
        if energies:
            self._add_metric(MetricType.POPULATION, 'average_energy', np.mean(energies))
            self._add_metric(MetricType.POPULATION, 'min_energy', min(energies))
            self._add_metric(MetricType.POPULATION, 'max_energy', max(energies))
    
    def collect_behavior_metrics(self, agents: List[Any]) -> None:
        """
        Recopila métricas de comportamiento.
        
        Args:
            agents: Lista de agentes
        """
        if not agents:
            return
        
        # Calcular métricas de comportamiento
        total_distance = sum(agent.stats.distance_traveled for agent in agents)
        total_food_eaten = sum(agent.stats.food_eaten for agent in agents)
        total_collisions = sum(agent.stats.collisions for agent in agents)
        total_offspring = sum(agent.stats.offspring_count for agent in agents)
        
        self._add_metric(MetricType.BEHAVIOR, 'total_distance', total_distance)
        self._add_metric(MetricType.BEHAVIOR, 'total_food_eaten', total_food_eaten)
        self._add_metric(MetricType.BEHAVIOR, 'total_collisions', total_collisions)
        self._add_metric(MetricType.BEHAVIOR, 'total_offspring', total_offspring)
        
        # Calcular métricas por agente
        alive_agents = [agent for agent in agents if agent.state.value == 'alive']
        if alive_agents:
            avg_distance = total_distance / len(alive_agents)
            avg_food = total_food_eaten / len(alive_agents)
            avg_collisions = total_collisions / len(alive_agents)
            
            self._add_metric(MetricType.BEHAVIOR, 'avg_distance_per_agent', avg_distance)
            self._add_metric(MetricType.BEHAVIOR, 'avg_food_per_agent', avg_food)
            self._add_metric(MetricType.BEHAVIOR, 'avg_collisions_per_agent', avg_collisions)
    
    def collect_environment_metrics(self, world) -> None:
        """
        Recopila métricas del entorno.
        
        Args:
            world: Mundo de la simulación
        """
        if not world:
            return
        
        # Obtener información del mundo
        world_info = world.get_world_info()
        
        # Métricas de recursos
        if 'resources' in world_info:
            resources = world_info['resources']
            self._add_metric(MetricType.ENVIRONMENT, 'food_positions', resources.get('food_positions', 0))
            self._add_metric(MetricType.ENVIRONMENT, 'total_food', resources.get('total_food', 0))
            self._add_metric(MetricType.ENVIRONMENT, 'obstacle_positions', resources.get('obstacle_positions', 0))
        
        # Métricas de agentes
        if 'agents' in world_info:
            agents_info = world_info['agents']
            self._add_metric(MetricType.ENVIRONMENT, 'world_agents', agents_info.get('total', 0))
            self._add_metric(MetricType.ENVIRONMENT, 'world_alive', agents_info.get('alive', 0))
            self._add_metric(MetricType.ENVIRONMENT, 'world_dead', agents_info.get('dead', 0))
    
    def collect_evolution_metrics(self, generation: int, fitness_history: List[float]) -> None:
        """
        Recopila métricas de evolución.
        
        Args:
            generation: Generación actual
            fitness_history: Historial de fitness
        """
        if not fitness_history:
            return
        
        # Calcular métricas de evolución
        self._add_metric(MetricType.EVOLUTION, 'generation', generation)
        self._add_metric(MetricType.EVOLUTION, 'fitness_trend', self._calculate_fitness_trend(fitness_history))
        self._add_metric(MetricType.EVOLUTION, 'fitness_diversity', np.std(fitness_history))
        
        # Calcular convergencia
        if len(fitness_history) > 10:
            recent_fitness = fitness_history[-10:]
            convergence = self._calculate_convergence(recent_fitness)
            self._add_metric(MetricType.EVOLUTION, 'convergence', convergence)
    
    def _add_metric(self, metric_type: MetricType, name: str, value: float, metadata: Dict[str, Any] = None) -> None:
        """
        Agrega una métrica.
        
        Args:
            metric_type: Tipo de métrica
            name: Nombre de la métrica
            value: Valor de la métrica
            metadata: Metadatos adicionales
        """
        metric = MetricData(
            timestamp=time.time(),
            tick=self.current_tick,
            epoch=self.current_epoch,
            generation=self.current_generation,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        
        # Limitar número de métricas
        if len(self.metrics) > self.max_metrics:
            self.metrics.pop(0)
    
    def _calculate_fitness_trend(self, fitness_history: List[float]) -> float:
        """
        Calcula la tendencia del fitness.
        
        Args:
            fitness_history: Historial de fitness
            
        Returns:
            Tendencia del fitness
        """
        if len(fitness_history) < 2:
            return 0.0
        
        # Calcular pendiente de la línea de tendencia
        x = np.arange(len(fitness_history))
        y = np.array(fitness_history)
        
        # Regresión lineal simple
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _calculate_convergence(self, fitness_values: List[float]) -> float:
        """
        Calcula el nivel de convergencia.
        
        Args:
            fitness_values: Valores de fitness
            
        Returns:
            Nivel de convergencia (0-1)
        """
        if len(fitness_values) < 2:
            return 0.0
        
        # Calcular varianza relativa
        mean_fitness = np.mean(fitness_values)
        if mean_fitness == 0:
            return 1.0
        
        variance = np.var(fitness_values)
        relative_variance = variance / (mean_fitness ** 2)
        
        # Convertir a nivel de convergencia (menor varianza = mayor convergencia)
        convergence = 1.0 / (1.0 + relative_variance)
        return convergence
    
    def update_tick(self, tick: int) -> None:
        """
        Actualiza el tick actual.
        
        Args:
            tick: Número de tick
        """
        self.current_tick = tick
    
    def update_epoch(self, epoch: int) -> None:
        """
        Actualiza la época actual.
        
        Args:
            epoch: Número de época
        """
        self.current_epoch = epoch
    
    def update_generation(self, generation: int) -> None:
        """
        Actualiza la generación actual.
        
        Args:
            generation: Número de generación
        """
        self.current_generation = generation
    
    def get_metrics_by_type(self, metric_type: MetricType) -> List[MetricData]:
        """
        Obtiene métricas por tipo.
        
        Args:
            metric_type: Tipo de métrica
            
        Returns:
            Lista de métricas del tipo especificado
        """
        return [metric for metric in self.metrics if metric.metric_type == metric_type]
    
    def get_metrics_by_name(self, name: str) -> List[MetricData]:
        """
        Obtiene métricas por nombre.
        
        Args:
            name: Nombre de la métrica
            
        Returns:
            Lista de métricas con el nombre especificado
        """
        return [metric for metric in self.metrics if name in str(metric.metadata)]
    
    def get_latest_metrics(self, limit: int = 100) -> List[MetricData]:
        """
        Obtiene las métricas más recientes.
        
        Args:
            limit: Número máximo de métricas
            
        Returns:
            Lista de métricas más recientes
        """
        return self.metrics[-limit:]
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Exporta métricas a un DataFrame de pandas.
        
        Returns:
            DataFrame con las métricas
        """
        if not self.metrics:
            return pd.DataFrame()
        
        data = []
        for metric in self.metrics:
            row = {
                'timestamp': metric.timestamp,
                'tick': metric.tick,
                'epoch': metric.epoch,
                'generation': metric.generation,
                'metric_type': metric.metric_type.value,
                'value': metric.value,
                'metadata': json.dumps(metric.metadata) if metric.metadata else None
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def save_metrics(self, filepath: str) -> None:
        """
        Guarda métricas en un archivo.
        
        Args:
            filepath: Ruta del archivo
        """
        df = self.export_to_dataframe()
        if not df.empty:
            df.to_csv(filepath, index=False)
    
    def load_metrics(self, filepath: str) -> None:
        """
        Carga métricas desde un archivo.
        
        Args:
            filepath: Ruta del archivo
        """
        try:
            df = pd.read_csv(filepath)
            self.metrics.clear()
            
            for _, row in df.iterrows():
                metric = MetricData(
                    timestamp=row['timestamp'],
                    tick=int(row['tick']),
                    epoch=int(row['epoch']),
                    generation=int(row['generation']),
                    metric_type=MetricType(row['metric_type']),
                    value=float(row['value']),
                    metadata=json.loads(row['metadata']) if pd.notna(row['metadata']) else {}
                )
                self.metrics.append(metric)
        except Exception as e:
            print(f"Error al cargar métricas: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del recolector.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.metrics:
            return {}
        
        # Calcular estadísticas por tipo
        type_stats = {}
        for metric_type in MetricType:
            type_metrics = self.get_metrics_by_type(metric_type)
            if type_metrics:
                values = [metric.value for metric in type_metrics]
                type_stats[metric_type.value] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        return {
            'total_metrics': len(self.metrics),
            'current_tick': self.current_tick,
            'current_epoch': self.current_epoch,
            'current_generation': self.current_generation,
            'type_statistics': type_stats
        }
    
    def clear(self) -> None:
        """Limpia todas las métricas."""
        self.metrics.clear()
        self.current_tick = 0
        self.current_epoch = 0
        self.current_generation = 0
