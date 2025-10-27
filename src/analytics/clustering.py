"""
Análisis de clustering para comportamientos emergentes en el ecosistema evolutivo.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple, Dict, Any
import config as SimulationConfig


class BehaviorClusterer:
    """Analizador de clustering para comportamientos emergentes de agentes."""
    
    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.cluster_names = [
            "Estrategia Puzzle",
            "Estrategia Supervivencia", 
            "Estrategia Híbrida",
            "Estrategia Élite",
            "Estrategia Intermedia",
            "Estrategia Básica",
            "Estrategia Fallida"
        ]
    
    def extract_agent_features(self, agents: List[Any]) -> np.ndarray:
        """Extrae características de comportamiento de los agentes."""
        features = []
        
        for agent in agents:
            # Características de la red neuronal (pesos)
            neural_features = []
            if hasattr(agent, 'brain') and hasattr(agent.brain, 'weights'):
                # Aplanar todos los pesos de la red neuronal
                for layer_weights in agent.brain.weights:
                    neural_features.extend(layer_weights.flatten())
            
            # Características de comportamiento
            behavior_features = [
                getattr(agent, 'food_eaten', 0),
                getattr(agent, 'exploration_distance', 0),
                getattr(agent, 'survival_time', 0),
                getattr(agent, 'fitness', 0),
                getattr(agent, 'trees_cut', 0),
                getattr(agent, 'huts_destroyed', 0),
                getattr(agent, 'keys_collected', 0),
                getattr(agent, 'doors_opened', 0),
                getattr(agent, 'chest_opened', 0),
                getattr(agent, 'water_penalties', 0),
                getattr(agent, 'energy_efficiency', 0),
                getattr(agent, 'movement_efficiency', 0)
            ]
            
            # Combinar características neuronales y de comportamiento
            all_features = neural_features + behavior_features
            features.append(all_features)
        
        return np.array(features)
    
    def cluster_agents(self, agents: List[Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Realiza clustering de agentes basado en sus características."""
        if len(agents) < self.n_clusters:
            # Si hay menos agentes que clusters, asignar cada uno a su propio cluster
            clusters = np.arange(len(agents))
            cluster_stats = self._calculate_cluster_stats(agents, clusters)
            return clusters, cluster_stats
        
        # Extraer características
        features = self.extract_agent_features(agents)
        
        # Normalizar características
        features_scaled = self.scaler.fit_transform(features)
        
        # Reducir dimensionalidad para visualización
        features_pca = self.pca.fit_transform(features_scaled)
        
        # Realizar clustering
        clusters = self.kmeans.fit_predict(features_scaled)
        
        # Calcular estadísticas de clusters
        cluster_stats = self._calculate_cluster_stats(agents, clusters)
        
        # Agregar información de PCA para visualización
        cluster_stats['pca_features'] = features_pca
        cluster_stats['cluster_centers_pca'] = self.pca.transform(
            self.kmeans.cluster_centers_
        )
        
        return clusters, cluster_stats
    
    def _calculate_cluster_stats(self, agents: List[Any], clusters: np.ndarray) -> Dict[str, Any]:
        """Calcula estadísticas para cada cluster."""
        stats = {
            'cluster_counts': {},
            'cluster_fitness': {},
            'cluster_behaviors': {},
            'cluster_names': self.cluster_names
        }
        
        for cluster_id in range(self.n_clusters):
            cluster_agents = [agents[i] for i in range(len(agents)) if clusters[i] == cluster_id]
            
            if not cluster_agents:
                continue
            
            # Contar agentes en el cluster
            stats['cluster_counts'][cluster_id] = len(cluster_agents)
            
            # Calcular fitness promedio
            fitness_values = [getattr(agent, 'fitness', 0) for agent in cluster_agents]
            stats['cluster_fitness'][cluster_id] = {
                'promedio': np.mean(fitness_values),
                'maximo': np.max(fitness_values),
                'minimo': np.min(fitness_values),
                'desviacion': np.std(fitness_values)
            }
            
            # Calcular comportamientos promedio
            behaviors = {
                'comida': np.mean([getattr(agent, 'food_eaten', 0) for agent in cluster_agents]),
                'exploracion': np.mean([getattr(agent, 'exploration_distance', 0) for agent in cluster_agents]),
                'supervivencia': np.mean([getattr(agent, 'survival_time', 0) for agent in cluster_agents]),
                'arboles_cortados': np.mean([getattr(agent, 'trees_cut', 0) for agent in cluster_agents]),
                'llaves_recogidas': np.mean([getattr(agent, 'keys_collected', 0) for agent in cluster_agents]),
                'puertas_abiertas': np.mean([getattr(agent, 'doors_opened', 0) for agent in cluster_agents]),
                'cofre_abierto': np.mean([getattr(agent, 'chest_opened', 0) for agent in cluster_agents])
            }
            
            stats['cluster_behaviors'][cluster_id] = behaviors
        
        return stats
    
    def get_cluster_interpretation(self, cluster_stats: Dict[str, Any]) -> Dict[int, str]:
        """Interpreta cada cluster basado en sus características."""
        interpretations = {}
        
        for cluster_id in cluster_stats['cluster_counts'].keys():
            behaviors = cluster_stats['cluster_behaviors'][cluster_id]
            fitness = cluster_stats['cluster_fitness'][cluster_id]['promedio']
            
            # Determinar tipo de estrategia basado en comportamientos (criterios más flexibles)
            if behaviors['cofre_abierto'] > 0.1:  # Más flexible
                strategy = "Estrategia Puzzle"
            elif behaviors['comida'] > 8 and fitness > 40:  # Más flexible
                strategy = "Estrategia Supervivencia"
            elif fitness > 70 and behaviors['exploracion'] > 500:  # Más flexible
                strategy = "Estrategia Híbrida"
            elif fitness > 80:  # Agentes de alto rendimiento
                strategy = "Estrategia Élite"
            elif fitness > 50:  # Agentes de rendimiento medio
                strategy = "Estrategia Intermedia"
            elif fitness > 30:  # Agentes de rendimiento bajo
                strategy = "Estrategia Básica"
            else:  # Agentes con muy bajo rendimiento
                strategy = "Estrategia Fallida"
            
            interpretations[cluster_id] = strategy
        
        return interpretations
    
    def print_cluster_report(self, agents: List[Any], clusters: np.ndarray, cluster_stats: Dict[str, Any]):
        """Imprime reporte de clustering en consola."""
        interpretations = self.get_cluster_interpretation(cluster_stats)
        
        print("\n🧬 ANÁLISIS DE CLUSTERING:")
        print("=" * 50)
        
        for cluster_id in sorted(cluster_stats['cluster_counts'].keys()):
            count = cluster_stats['cluster_counts'][cluster_id]
            fitness = cluster_stats['cluster_fitness'][cluster_id]
            behaviors = cluster_stats['cluster_behaviors'][cluster_id]
            strategy = interpretations.get(cluster_id, f"Cluster {cluster_id}")
            
            print(f"\n📊 {strategy}:")
            print(f"   - Agentes: {count}")
            print(f"   - Fitness promedio: {fitness['promedio']:.1f}")
            print(f"   - Fitness máximo: {fitness['maximo']:.1f}")
            print(f"   - Comida promedio: {behaviors['comida']:.1f}")
            print(f"   - Exploración: {behaviors['exploracion']:.0f}px")
            print(f"   - Árboles cortados: {behaviors['arboles_cortados']:.1f}")
            print(f"   - Llaves recogidas: {behaviors['llaves_recogidas']:.1f}")
            print(f"   - Puertas abiertas: {behaviors['puertas_abiertas']:.1f}")
            print(f"   - Cofre abierto: {behaviors['cofre_abierto']:.1f}")
        
        # Análisis de diversidad
        total_agents = len(agents)
        cluster_diversity = len([c for c in cluster_stats['cluster_counts'].values() if c > 0])
        diversity_ratio = cluster_diversity / self.n_clusters
        
        print(f"\n📈 ANÁLISIS DE DIVERSIDAD:")
        print(f"   - Clusters activos: {cluster_diversity}/{self.n_clusters}")
        print(f"   - Ratio de diversidad: {diversity_ratio:.2f}")
        
        if diversity_ratio < 0.5:
            print("   ⚠️ CONVERGENCIA PREMATURA: Pocos clusters activos")
        elif diversity_ratio > 0.8:
            print("   ✅ DIVERSIDAD ALTA: Múltiples estrategias emergentes")
        else:
            print("   ⚖️ DIVERSIDAD MODERADA: Balance entre exploración y explotación")