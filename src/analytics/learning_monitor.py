"""
Sistema de monitoreo detallado para verificar aprendizaje.
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import json
import os
from .clustering import BehaviorClusterer


class LearningMonitor:
    """Monitor de aprendizaje para agentes evolutivos."""
    
    def __init__(self):
        self.generation_data = []
        self.fitness_history = []
        self.food_history = []
        self.survival_history = []
        self.diversity_history = []
        self.clusterer = BehaviorClusterer(n_clusters=3)  # 3 clusters claros: Exploradores, Recolectores, Exitosos
        self.clustering_history = []
        self.behavior_patterns = []
        
    def record_generation(self, generation, agents, world):
        """Registra datos de una generación."""
        if not agents:
            return
            
        # Calcular métricas básicas
        fitnesses = [agent.fitness for agent in agents]
        food_eaten = [agent.food_eaten for agent in agents]
        ages = [agent.age for agent in agents]
        distances = [agent.distance_traveled for agent in agents]
        
        # Métricas de la generación
        gen_data = {
            'generation': generation,
            'avg_fitness': float(np.mean(fitnesses)),
            'max_fitness': float(np.max(fitnesses)),
            'min_fitness': float(np.min(fitnesses)),
            'std_fitness': float(np.std(fitnesses)),
            'avg_food': float(np.mean(food_eaten)),
            'max_food': int(np.max(food_eaten)),
            'avg_age': float(np.mean(ages)),
            'max_age': float(np.max(ages)),
            'avg_distance': float(np.mean(distances)),
            'diversity': float(self._calculate_diversity(agents)),
            'alive_count': len([a for a in agents if a.alive])
        }
        
        # Realizar clustering de comportamientos (solo cada 3 generaciones para velocidad)
        if len(agents) >= 4 and generation % 3 == 0:  # Solo cada 3 generaciones
            try:
                clusters, cluster_stats = self.clusterer.cluster_agents(agents)
                gen_data['clusters'] = clusters.tolist()
                gen_data['cluster_stats'] = cluster_stats
                self.clustering_history.append({
                    'generation': generation,
                    'clusters': clusters.tolist(),
                    'cluster_stats': cluster_stats
                })
            except Exception as e:
                print(f"⚠️ Error en clustering generación {generation}: {e}")
                gen_data['clusters'] = []
                gen_data['cluster_stats'] = {}
        else:
            gen_data['clusters'] = []
            gen_data['cluster_stats'] = {}
        
        self.generation_data.append(gen_data)
        self.fitness_history.append(gen_data['avg_fitness'])
        self.food_history.append(gen_data['avg_food'])
        self.survival_history.append(gen_data['avg_age'])
        self.diversity_history.append(gen_data['diversity'])
        
        # Análisis de comportamiento
        behavior_analysis = self._analyze_behaviors(agents)
        self.behavior_patterns.append(behavior_analysis)
        
        return gen_data
    
    def calculate_diversity(self, agents):
        """Calcula diversidad genética de la población"""
        if len(agents) < 2:
            return 0.0
            
        # Extraer pesos de todas las redes neuronales (soporte multi-capa)
        all_weights = []
        for agent in agents:
            brain = getattr(agent, 'brain', None)
            if brain is None:
                continue
            flat_parts = []
            if hasattr(brain, 'weights') and hasattr(brain, 'biases'):
                # Nueva API: listas de capas
                for W, b in zip(brain.weights, brain.biases):
                    flat_parts.append(W.flatten())
                    flat_parts.append(b.flatten())
            else:
                # Compatibilidad con W1/W2
                flat_parts.append(getattr(brain, 'W1', np.zeros(0)).flatten())
                flat_parts.append(getattr(brain, 'b1', np.zeros(0)).flatten())
                flat_parts.append(getattr(brain, 'W2', np.zeros(0)).flatten())
                flat_parts.append(getattr(brain, 'b2', np.zeros(0)).flatten())
            if flat_parts:
                weights = np.concatenate(flat_parts)
                all_weights.append(weights)
        
        all_weights = np.array(all_weights)
        
        # Calcular varianza promedio (diversidad)
        diversity = np.mean(np.var(all_weights, axis=0))
        return float(diversity)
    
    def _calculate_diversity(self, agents):
        """Calcula diversidad genética de la población"""
        return self.calculate_diversity(agents)
    
    def _analyze_behaviors(self, agents):
        """Analiza patrones de comportamiento emergentes"""
        behaviors = {
            'food_seekers': 0,      # Agentes que buscan comida activamente
            'explorers': 0,          # Agentes que exploran mucho
            'survivors': 0,         # Agentes que sobreviven mucho tiempo
            'efficient_movers': 0,  # Agentes con movimiento eficiente
            'obstacle_avoiders': 0  # Agentes que evitan obstáculos
        }
        
        for agent in agents:
            # Food seekers: comen más de 2 manzanas
            if agent.food_eaten > 2:
                behaviors['food_seekers'] += 1
                
            # Explorers: viajan más de 1000 píxeles
            if agent.distance_traveled > 1000:
                behaviors['explorers'] += 1
                
            # Survivors: viven más de 2000 ticks
            if agent.age > 2000:
                behaviors['survivors'] += 1
                
            # Efficient movers: ratio distancia/movimientos > 0.8
            if agent.total_moves > 0:
                efficiency = agent.distance_traveled / agent.total_moves
                if efficiency > 0.8:
                    behaviors['efficient_movers'] += 1
                    
            # Obstacle avoiders: evitan más de 3 obstáculos
            if agent.obstacles_avoided > 3:
                behaviors['obstacle_avoiders'] += 1
        
        # Convertir a porcentajes
        total_agents = len(agents)
        for key in behaviors:
            behaviors[key] = (behaviors[key] / total_agents) * 100 if total_agents > 0 else 0
            
        return behaviors
    
    def print_generation_summary(self, gen_data):
        """Imprime resumen detallado de la generación (formato estandarizado)."""
        print(f"\n🔬 ANÁLISIS DETALLADO - GENERACIÓN {gen_data['generation']}")
        print("=" * 60)
        # Formato estandarizado igual que los logs básicos
        print(f"   📊 FITNESS:")
        print(f"      - Promedio: {gen_data['avg_fitness']:.1f}/100")
        print(f"      - Máximo: {gen_data['max_fitness']:.1f}/100")
        print(f"      - Mínimo: {gen_data['min_fitness']:.1f}/100")
        print(f"      - Desviación: {gen_data['std_fitness']:.1f}")
        print(f"   🍎 COMIDA:")
        print(f"      - Promedio: {gen_data['avg_food']:.1f}")
        print(f"      - Máximo: {gen_data['max_food']:.0f}")
        print(f"   ⏱️ SUPERVIVENCIA:")
        print(f"      - Tasa: {(gen_data['alive_count']/gen_data.get('total_agents', 50)*100):.1f}%")
        print(f"      - Tiempo promedio: {gen_data['avg_age']/60/60:.1f} min")
        print(f"      - Tiempo máximo: {gen_data['max_age']/60/60:.1f} min")
        print(f"   🧬 DIVERSIDAD GENÉTICA: {gen_data['diversity']:.4f}")
        print(f"   📏 EXPLORACIÓN: {gen_data['avg_distance']:.0f} píxeles")
        
        # Análisis de comportamiento (información extra del análisis detallado)
        if self.behavior_patterns:
            behaviors = self.behavior_patterns[-1]
            print(f"   🎮 COMPORTAMIENTOS EMERGENTES:")
            print(f"      - Buscadores de comida: {behaviors['food_seekers']:.1f}%")
            print(f"      - Exploradores: {behaviors['explorers']:.1f}%")
            print(f"      - Supervivientes: {behaviors['survivors']:.1f}%")
            print(f"      - Movimiento eficiente: {behaviors['efficient_movers']:.1f}%")
            # print(f"      - Evasión de obstáculos: {behaviors['obstacle_avoiders']:.1f}%")
        
        # Análisis de clustering
        if gen_data.get('cluster_stats'):
            # Crear un reporte simplificado sin necesidad de los agentes originales
            self._print_cluster_summary(gen_data['cluster_stats'])
    
    def detect_learning_patterns(self):
        """Detecta patrones de aprendizaje."""
        if len(self.generation_data) < 5:
            return "Necesita más generaciones para análisis"
        
        # Análisis de tendencias
        recent_gens = self.generation_data[-5:]
        early_gens = self.generation_data[:5]
        
        # Fitness trend
        recent_fitness = np.mean([g['avg_fitness'] for g in recent_gens])
        early_fitness = np.mean([g['avg_fitness'] for g in early_gens])
        fitness_improvement = recent_fitness - early_fitness
        
        # Food trend
        recent_food = np.mean([g['avg_food'] for g in recent_gens])
        early_food = np.mean([g['avg_food'] for g in early_gens])
        food_improvement = recent_food - early_food
        # Mejora relativa para umbral más justo
        food_improvement_relative = (food_improvement / max(early_food, 0.1)) * 100 if early_food > 0 else 0
        
        # Diversity trend
        recent_diversity = np.mean([g['diversity'] for g in recent_gens])
        early_diversity = np.mean([g['diversity'] for g in early_gens])
        diversity_change = recent_diversity - early_diversity
        
        print(f"\n🧠 ANÁLISIS DE APRENDIZAJE:")
        print("=" * 40)
        print(f"📈 MEJORA EN FITNESS: {fitness_improvement:+.1f}")
        print(f"🍎 MEJORA EN COMIDA: {food_improvement:+.1f} ({food_improvement_relative:+.1f}% relativa)")
        print(f"🧬 CAMBIO EN DIVERSIDAD: {diversity_change:+.4f}")
        
        # Conclusiones
        if fitness_improvement > 10:
            print("✅ APRENDIZAJE CONFIRMADO: Fitness mejorando significativamente")
        elif fitness_improvement > 5:
            print("⚠️ APRENDIZAJE PARCIAL: Fitness mejorando moderadamente")
        else:
            print("❌ PROBLEMA DE APRENDIZAJE: Fitness no mejora")
            
        # Umbral más justo: al menos 1 manzana absoluta O al menos 50% de mejora relativa
        if food_improvement > 1.0 or food_improvement_relative > 50:
            print("✅ COMPORTAMIENTO EMERGENTE: Agentes aprendiendo a comer")
        else:
            print("⚠️ PROBLEMA DE COMPORTAMIENTO: Agentes no mejoran en comer")
            
        if diversity_change < -0.01:
            print("⚠️ CONVERGENCIA PREMATURA: Diversidad genética disminuyendo")
        else:
            print("✅ DIVERSIDAD MANTENIDA: Población mantiene variabilidad")
    
    def save_data(self, filename="learning_data.json"):
        """Guarda datos para análisis posterior."""
        data = {
            'generation_data': self.generation_data,
            'fitness_history': self.fitness_history,
            'food_history': self.food_history,
            'survival_history': self.survival_history,
            'diversity_history': self.diversity_history,
            'behavior_patterns': self.behavior_patterns
        }
        
        # Convertir datos de NumPy a Python nativo para JSON
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        # Convertir todos los datos
        data_converted = {}
        for key, value in data.items():
            if isinstance(value, list):
                data_converted[key] = [convert_numpy(item) for item in value]
            else:
                data_converted[key] = convert_numpy(value)
        
        with open(filename, 'w') as f:
            json.dump(data_converted, f, indent=2)
        
        print(f"💾 Datos guardados en {filename}")
    
    def create_learning_report(self):
        """Crea reporte completo de aprendizaje."""
        if len(self.generation_data) < 3:
            return "Necesita al menos 3 generaciones para reporte"
        
        print(f"\n📊 REPORTE COMPLETO DE APRENDIZAJE")
        print("=" * 50)
        
        # Estadísticas generales
        total_gens = len(self.generation_data)
        final_fitness = self.fitness_history[-1]
        initial_fitness = self.fitness_history[0]
        improvement = final_fitness - initial_fitness
        
        print(f"📈 GENERACIONES ANALIZADAS: {total_gens}")
        print(f"🎯 FITNESS INICIAL: {initial_fitness:.1f}")
        print(f"🎯 FITNESS FINAL: {final_fitness:.1f}")
        print(f"📈 MEJORA TOTAL: {improvement:+.1f}")
        
        # Análisis de tendencias
        self.detect_learning_patterns()
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if improvement < 5:
            print("   - Aumentar tasa de mutación")
            print("   - Reducir presión selectiva")
            print("   - Verificar configuración del entorno")
        elif improvement > 20:
            print("   - Sistema funcionando bien")
            print("   - Considerar aumentar complejidad")
        else:
            print("   - Aprendizaje moderado, continuar observando")
        
        return "Reporte completado"
    
    def _print_cluster_summary(self, cluster_stats):
        """Imprime resumen de clustering con 3 clusters claros."""
        interpretations = self.clusterer.get_cluster_interpretation(cluster_stats)
        
        print("   🧬 CLUSTERING:")
        
        # Ordenar clusters por interpretación (Exploradores, Recolectores, Exitosos)
        cluster_order = ["Exploradores", "Recolectores", "Exitosos"]
        sorted_clusters = []
        
        for cluster_id in cluster_stats['cluster_counts'].keys():
            count = cluster_stats['cluster_counts'][cluster_id]
            if count > 0:
                strategy = interpretations.get(cluster_id, f"Cluster {cluster_id}")
                fitness = cluster_stats['cluster_fitness'][cluster_id]
                behaviors = cluster_stats['cluster_behaviors'][cluster_id]
                sorted_clusters.append((cluster_id, count, strategy, fitness, behaviors))
        
        # Ordenar por tipo (Exploradores primero, luego Recolectores, luego Exitosos)
        sorted_clusters.sort(key=lambda x: (cluster_order.index(x[2]) if x[2] in cluster_order else 999, -x[1]))
        
        for cluster_id, count, strategy, fitness, behaviors in sorted_clusters:
            comida = behaviors.get('comida', 0)
            exploracion = behaviors.get('exploracion', 0) / 100  # En metros
            print(f"      - {strategy}: {count} agentes | Fitness: {fitness['promedio']:.1f} | Comida: {comida:.1f} | Exploracion: {exploracion:.0f} m")
