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
    
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.cluster_names = [
            "Exploradores",
            "Recolectores",
            "Exitosos"
        ]
    
    def extract_agent_features(self, agents: List[Any]) -> np.ndarray:
        """Extrae características REALES de comportamiento de los agentes."""
        features = []
        
        for agent in agents:
            # SOLO usar características que realmente existen en AdvancedAgent
            behavior_features = [
                float(getattr(agent, 'fitness', 0)),           # Desempeño general
                float(getattr(agent, 'food_eaten', 0)),        # Estrategia de recursos
                float(getattr(agent, 'distance_traveled', 0)),  # Exploración
                float(getattr(agent, 'age', 0))                # Supervivencia
            ]
            
            features.append(behavior_features)
        
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
            
            # Calcular comportamientos promedio (solo características REALES)
            behaviors = {
                'comida': np.mean([getattr(agent, 'food_eaten', 0) for agent in cluster_agents]),
                'exploracion': np.mean([getattr(agent, 'distance_traveled', 0) for agent in cluster_agents]),
                'supervivencia': np.mean([getattr(agent, 'age', 0) for agent in cluster_agents]),
                'fitness': np.mean([getattr(agent, 'fitness', 0) for agent in cluster_agents])
            }
            
            stats['cluster_behaviors'][cluster_id] = behaviors
        
        return stats
    
    def get_cluster_interpretation(self, cluster_stats: Dict[str, Any]) -> Dict[int, str]:
        """Interpreta clusters forzando 3 roles distintos por ranking:
        - Exploradores: mayor exploración promedio
        - Recolectores: mayor comida promedio (restantes)
        - Exitosos: mayor fitness promedio (restantes)
        Resto: asignación por métrica dominante.
        """
        interpretations: Dict[int, str] = {}
        counts = cluster_stats.get('cluster_counts', {})
        if not counts:
            return interpretations

        # Preparar métricas por cluster
        metrics = []  # (cluster_id, exploracion, comida, fitness)
        for cid, cnt in counts.items():
            if cnt <= 0:
                continue
            behaviors = cluster_stats['cluster_behaviors'].get(cid, {})
            fitness_stats = cluster_stats['cluster_fitness'].get(cid, {})
            exploracion = float(behaviors.get('exploracion', 0.0))
            comida = float(behaviors.get('comida', 0.0))
            fitness = float(fitness_stats.get('promedio', 0.0))
            metrics.append((cid, exploracion, comida, fitness))

        if not metrics:
            return interpretations

        remaining = set(cid for cid, *_ in metrics)

        # 1) Exitosos: mayor fitness
        cid_exit = max(metrics, key=lambda m: m[3])[0]
        interpretations[cid_exit] = "Exitosos"
        if cid_exit in remaining:
            remaining.remove(cid_exit)

        # 2) Exploradores: mayor exploración entre restantes
        if remaining:
            cid_expl = max([m for m in metrics if m[0] in remaining], key=lambda m: m[1])[0]
            interpretations[cid_expl] = "Exploradores"
            remaining.remove(cid_expl)

        # 3) Recolectores: mayor comida entre restantes
        if remaining:
            cid_reco = max([m for m in metrics if m[0] in remaining], key=lambda m: m[2])[0]
            interpretations[cid_reco] = "Recolectores"
            remaining.remove(cid_reco)

        # 4) Resto: elegir rol por métrica dominante (normalizada por rango simple)
        if remaining:
            # Calcular rangos para normalización simple
            exps = [m[1] for m in metrics]
            foods = [m[2] for m in metrics]
            fits = [m[3] for m in metrics]
            def norm(val, arr):
                mn, mx = min(arr), max(arr)
                return 0.0 if mx == mn else (val - mn) / (mx - mn)
            for cid in list(remaining):
                _, e, c, f = next(m for m in metrics if m[0] == cid)
                scores = {
                    "Exploradores": norm(e, exps),
                    "Recolectores": norm(c, foods),
                    "Exitosos": norm(f, fits)
                }
                # Evitar duplicar etiquetas ya usadas si es posible
                unused = [r for r in ["Exploradores", "Recolectores", "Exitosos"] if r not in interpretations.values()]
                if unused:
                    # Tomar mayor entre roles no usados; si todos usados, tomar global mayor
                    best_role = max(unused, key=lambda r: scores[r])
                else:
                    best_role = max(scores.items(), key=lambda kv: kv[1])[0]
                interpretations[cid] = best_role
                remaining.remove(cid)

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