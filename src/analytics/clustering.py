"""
Sistema de clustering para análisis de comportamiento en el ecosistema evolutivo.
Identifica patrones emergentes en el comportamiento de los agentes.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score


class ClusteringMethod(Enum):
    """Métodos de clustering disponibles."""
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    AGGLOMERATIVE = "agglomerative"


@dataclass
class ClusteringConfig:
    """Configuración del sistema de clustering."""
    method: ClusteringMethod = ClusteringMethod.KMEANS
    n_clusters: int = 5
    eps: float = 0.5
    min_samples: int = 5
    linkage: str = "ward"
    random_state: int = 42


class BehaviorAnalyzer:
    """Analizador de comportamiento de agentes."""
    
    def __init__(self, config: ClusteringConfig):
        """
        Inicializa el analizador de comportamiento.
        
        Args:
            config: Configuración del clustering
        """
        self.config = config
        self.scaler = StandardScaler()
        self.pca = None
        self.clusterer = None
        self.feature_names = []
        self.cluster_labels = []
        self.cluster_centers = []
        self.cluster_stats = {}
    
    def extract_features(self, agents: List[Any]) -> np.ndarray:
        """
        Extrae características de comportamiento de los agentes.
        
        Args:
            agents: Lista de agentes
            
        Returns:
            Array de características
        """
        features = []
        self.feature_names = []
        
        for agent in agents:
            if agent.state.value != 'alive':
                continue
            
            # Extraer características del agente
            agent_features = self._extract_agent_features(agent)
            features.append(agent_features)
        
        if not features:
            return np.array([])
        
        # Convertir a array numpy
        features_array = np.array(features)
        
        # Normalizar características
        features_normalized = self.scaler.fit_transform(features_array)
        
        return features_normalized
    
    def _extract_agent_features(self, agent) -> List[float]:
        """
        Extrae características de un agente individual.
        
        Args:
            agent: Agente a analizar
            
        Returns:
            Lista de características
        """
        features = []
        
        # Características básicas
        features.append(agent.stats.age)
        features.append(agent.energy)
        features.append(agent.stats.fitness)
        
        # Características de movimiento
        features.append(agent.stats.distance_traveled)
        if agent.stats.age > 0:
            features.append(agent.stats.distance_traveled / agent.stats.age)
        else:
            features.append(0.0)
        
        # Características de alimentación
        features.append(agent.stats.food_eaten)
        if agent.stats.age > 0:
            features.append(agent.stats.food_eaten / agent.stats.age)
        else:
            features.append(0.0)
        
        # Características de colisiones
        features.append(agent.stats.collisions)
        if agent.stats.age > 0:
            features.append(agent.stats.collisions / agent.stats.age)
        else:
            features.append(0.0)
        
        # Características de reproducción
        features.append(agent.stats.offspring_count)
        if agent.stats.age > 0:
            features.append(agent.stats.offspring_count / agent.stats.age)
        else:
            features.append(0.0)
        
        # Características de diversidad de comportamiento
        if len(agent.action_history) > 0:
            unique_actions = len(set(action['action'] for action in agent.action_history))
            features.append(unique_actions)
            features.append(unique_actions / len(agent.action_history))
        else:
            features.extend([0.0, 0.0])
        
        # Características de exploración
        if len(agent.position_history) > 1:
            positions = agent.position_history
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            
            # Calcular área explorada
            area = self._calculate_explored_area(positions)
            features.append(area)
            
            # Calcular distancia máxima desde el punto inicial
            initial_pos = positions[0]
            max_distance = max(
                np.sqrt((pos[0] - initial_pos[0])**2 + (pos[1] - initial_pos[1])**2)
                for pos in positions
            )
            features.append(max_distance)
        else:
            features.extend([0.0, 0.0])
        
        # Características de eficiencia energética
        if agent.stats.distance_traveled > 0 and agent.stats.age > 0:
            energy_used = 100.0 - agent.energy  # Asumiendo energía máxima de 100
            if energy_used > 0:
                efficiency = agent.stats.distance_traveled / energy_used
                features.append(efficiency)
            else:
                features.append(0.0)
        else:
            features.append(0.0)
        
        return features
    
    def _calculate_explored_area(self, positions: List[Tuple[float, float]]) -> float:
        """
        Calcula el área explorada por un agente.
        
        Args:
            positions: Lista de posiciones
            
        Returns:
            Área explorada
        """
        if len(positions) < 3:
            return 0.0
        
        # Usar fórmula de Shoelace para calcular área del polígono
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        area = 0.5 * abs(sum(
            x_coords[i] * y_coords[i + 1] - x_coords[i + 1] * y_coords[i]
            for i in range(len(positions) - 1)
        ))
        
        return area
    
    def cluster_agents(self, agents: List[Any]) -> Dict[str, Any]:
        """
        Agrupa agentes por comportamiento.
        
        Args:
            agents: Lista de agentes
            
        Returns:
            Diccionario con resultados del clustering
        """
        # Extraer características
        features = self.extract_features(agents)
        
        if features.size == 0:
            return {'error': 'No hay agentes vivos para analizar'}
        
        # Aplicar PCA si es necesario
        if features.shape[1] > 10:
            self.pca = PCA(n_components=10, random_state=self.config.random_state)
            features = self.pca.fit_transform(features)
        
        # Aplicar clustering
        if self.config.method == ClusteringMethod.KMEANS:
            self.clusterer = KMeans(
                n_clusters=self.config.n_clusters,
                random_state=self.config.random_state
            )
        elif self.config.method == ClusteringMethod.DBSCAN:
            self.clusterer = DBSCAN(
                eps=self.config.eps,
                min_samples=self.config.min_samples
            )
        elif self.config.method == ClusteringMethod.AGGLOMERATIVE:
            self.clusterer = AgglomerativeClustering(
                n_clusters=self.config.n_clusters,
                linkage=self.config.linkage
            )
        
        # Entrenar clusterer
        self.cluster_labels = self.clusterer.fit_predict(features)
        
        # Calcular estadísticas de clusters
        self._calculate_cluster_stats(features)
        
        # Calcular métricas de calidad
        quality_metrics = self._calculate_quality_metrics(features)
        
        return {
            'cluster_labels': self.cluster_labels.tolist(),
            'cluster_stats': self.cluster_stats,
            'quality_metrics': quality_metrics,
            'feature_names': self.feature_names,
            'n_features': features.shape[1],
            'n_clusters': len(set(self.cluster_labels)) - (1 if -1 in self.cluster_labels else 0)
        }
    
    def _calculate_cluster_stats(self, features: np.ndarray) -> None:
        """
        Calcula estadísticas de cada cluster.
        
        Args:
            features: Array de características
        """
        unique_labels = set(self.cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # Remover ruido de DBSCAN
        
        self.cluster_stats = {}
        
        for label in unique_labels:
            cluster_mask = self.cluster_labels == label
            cluster_features = features[cluster_mask]
            
            if len(cluster_features) > 0:
                self.cluster_stats[label] = {
                    'size': len(cluster_features),
                    'mean': np.mean(cluster_features, axis=0).tolist(),
                    'std': np.std(cluster_features, axis=0).tolist(),
                    'min': np.min(cluster_features, axis=0).tolist(),
                    'max': np.max(cluster_features, axis=0).tolist()
                }
    
    def _calculate_quality_metrics(self, features: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas de calidad del clustering.
        
        Args:
            features: Array de características
            
        Returns:
            Diccionario con métricas de calidad
        """
        metrics = {}
        
        # Silhouette score
        if len(set(self.cluster_labels)) > 1 and -1 not in self.cluster_labels:
            try:
                metrics['silhouette_score'] = silhouette_score(features, self.cluster_labels)
            except:
                metrics['silhouette_score'] = 0.0
        else:
            metrics['silhouette_score'] = 0.0
        
        # Calinski-Harabasz score
        if len(set(self.cluster_labels)) > 1 and -1 not in self.cluster_labels:
            try:
                metrics['calinski_harabasz_score'] = calinski_harabasz_score(features, self.cluster_labels)
            except:
                metrics['calinski_harabasz_score'] = 0.0
        else:
            metrics['calinski_harabasz_score'] = 0.0
        
        # Inertia (solo para KMeans)
        if hasattr(self.clusterer, 'inertia_'):
            metrics['inertia'] = self.clusterer.inertia_
        
        return metrics
    
    def get_cluster_behavior_patterns(self, agents: List[Any]) -> Dict[str, Any]:
        """
        Identifica patrones de comportamiento por cluster.
        
        Args:
            agents: Lista de agentes
            
        Returns:
            Diccionario con patrones de comportamiento
        """
        if not self.cluster_labels:
            return {}
        
        alive_agents = [agent for agent in agents if agent.state.value == 'alive']
        if len(alive_agents) != len(self.cluster_labels):
            return {}
        
        patterns = {}
        unique_labels = set(self.cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)
        
        for label in unique_labels:
            cluster_agents = [agent for i, agent in enumerate(alive_agents) 
                             if self.cluster_labels[i] == label]
            
            if not cluster_agents:
                continue
            
            # Analizar patrones del cluster
            pattern = self._analyze_cluster_pattern(cluster_agents)
            patterns[f'cluster_{label}'] = pattern
        
        return patterns
    
    def _analyze_cluster_pattern(self, cluster_agents: List[Any]) -> Dict[str, Any]:
        """
        Analiza el patrón de comportamiento de un cluster.
        
        Args:
            cluster_agents: Agentes del cluster
            
        Returns:
            Diccionario con patrón de comportamiento
        """
        if not cluster_agents:
            return {}
        
        # Calcular estadísticas del cluster
        ages = [agent.stats.age for agent in cluster_agents]
        energies = [agent.energy for agent in cluster_agents]
        distances = [agent.stats.distance_traveled for agent in cluster_agents]
        food_eaten = [agent.stats.food_eaten for agent in cluster_agents]
        collisions = [agent.stats.collisions for agent in cluster_agents]
        offspring = [agent.stats.offspring_count for agent in cluster_agents]
        
        # Analizar acciones
        all_actions = []
        for agent in cluster_agents:
            all_actions.extend([action['action'] for action in agent.action_history])
        
        action_counts = {}
        for action in all_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Determinar comportamiento dominante
        dominant_behavior = self._determine_dominant_behavior(
            ages, energies, distances, food_eaten, collisions, offspring, action_counts
        )
        
        return {
            'size': len(cluster_agents),
            'average_age': np.mean(ages),
            'average_energy': np.mean(energies),
            'average_distance': np.mean(distances),
            'average_food': np.mean(food_eaten),
            'average_collisions': np.mean(collisions),
            'average_offspring': np.mean(offspring),
            'action_distribution': action_counts,
            'dominant_behavior': dominant_behavior
        }
    
    def _determine_dominant_behavior(self, ages, energies, distances, food_eaten, 
                                   collisions, offspring, action_counts) -> str:
        """
        Determina el comportamiento dominante de un cluster.
        
        Args:
            ages: Lista de edades
            energies: Lista de energías
            distances: Lista de distancias
            food_eaten: Lista de comida consumida
            collisions: Lista de colisiones
            offspring: Lista de descendientes
            action_counts: Conteo de acciones
            
        Returns:
            Comportamiento dominante
        """
        # Calcular ratios
        avg_age = np.mean(ages)
        avg_energy = np.mean(energies)
        avg_distance = np.mean(distances)
        avg_food = np.mean(food_eaten)
        avg_collisions = np.mean(collisions)
        avg_offspring = np.mean(offspring)
        
        # Determinar comportamiento basado en ratios
        if avg_food > avg_distance * 0.5:
            return "food_focused"
        elif avg_distance > avg_food * 2:
            return "explorer"
        elif avg_collisions > avg_distance * 0.1:
            return "aggressive"
        elif avg_offspring > 1:
            return "reproductive"
        elif avg_energy > 80:
            return "conservative"
        else:
            return "balanced"
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de los clusters.
        
        Returns:
            Diccionario con resumen de clusters
        """
        if not self.cluster_stats:
            return {}
        
        summary = {
            'n_clusters': len(self.cluster_stats),
            'cluster_sizes': [stats['size'] for stats in self.cluster_stats.values()],
            'total_agents': sum(stats['size'] for stats in self.cluster_stats.values()),
            'cluster_details': self.cluster_stats
        }
        
        return summary
    
    def reset(self) -> None:
        """Reinicia el analizador."""
        self.scaler = StandardScaler()
        self.pca = None
        self.clusterer = None
        self.feature_names = []
        self.cluster_labels = []
        self.cluster_centers = []
        self.cluster_stats = {}
