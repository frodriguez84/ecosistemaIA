"""
Sistema de monitoreo detallado para verificar aprendizaje.
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import json
import os


class LearningMonitor:
    """Monitor de aprendizaje para agentes evolutivos."""
    
    def __init__(self):
        self.generation_data = []
        self.fitness_history = []
        self.food_history = []
        self.survival_history = []
        self.diversity_history = []
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
        
        self.generation_data.append(gen_data)
        self.fitness_history.append(gen_data['avg_fitness'])
        self.food_history.append(gen_data['avg_food'])
        self.survival_history.append(gen_data['avg_age'])
        self.diversity_history.append(gen_data['diversity'])
        
        # Análisis de comportamiento
        behavior_analysis = self._analyze_behaviors(agents)
        self.behavior_patterns.append(behavior_analysis)
        
        return gen_data
    
    def _calculate_diversity(self, agents):
        """Calcula diversidad genética de la población."""
        if len(agents) < 2:
            return 0.0
            
        # Extraer pesos de todas las redes neuronales
        all_weights = []
        for agent in agents:
            weights = np.concatenate([
                agent.brain.W1.flatten(),
                agent.brain.b1.flatten(),
                agent.brain.W2.flatten(),
                agent.brain.b2.flatten()
            ])
            all_weights.append(weights)
        
        all_weights = np.array(all_weights)
        
        # Calcular varianza promedio (diversidad)
        diversity = np.mean(np.var(all_weights, axis=0))
        return float(diversity)
    
    def _analyze_behaviors(self, agents):
        """Analiza patrones de comportamiento emergentes."""
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
        """Imprime resumen detallado de la generación."""
        print(f"\n🔬 ANÁLISIS DETALLADO - GENERACIÓN {gen_data['generation']}")
        print("=" * 60)
        print(f"📊 FITNESS:")
        print(f"   - Promedio: {gen_data['avg_fitness']:.1f}")
        print(f"   - Máximo: {gen_data['max_fitness']:.1f}")
        print(f"   - Mínimo: {gen_data['min_fitness']:.1f}")
        print(f"   - Desviación: {gen_data['std_fitness']:.1f}")
        print(f"")
        print(f"🍎 COMIDA:")
        print(f"   - Promedio: {gen_data['avg_food']:.1f}")
        print(f"   - Máximo: {gen_data['max_food']:.0f}")
        print(f"")
        print(f"⏱️ SUPERVIVENCIA:")
        print(f"   - Tiempo promedio: {gen_data['avg_age']/60:.1f} min")
        print(f"   - Tiempo máximo: {gen_data['max_age']/60:.1f} min")
        print(f"   - Agentes vivos: {gen_data['alive_count']}")
        print(f"")
        print(f"🧬 DIVERSIDAD GENÉTICA: {gen_data['diversity']:.4f}")
        print(f"📏 EXPLORACIÓN: {gen_data['avg_distance']:.0f} píxeles")
        
        # Análisis de comportamiento
        if self.behavior_patterns:
            behaviors = self.behavior_patterns[-1]
            print(f"")
            print(f"🎮 COMPORTAMIENTOS EMERGENTES:")
            print(f"   - Buscadores de comida: {behaviors['food_seekers']:.1f}%")
            print(f"   - Exploradores: {behaviors['explorers']:.1f}%")
            print(f"   - Supervivientes: {behaviors['survivors']:.1f}%")
            print(f"   - Movimiento eficiente: {behaviors['efficient_movers']:.1f}%")
            print(f"   - Evasión de obstáculos: {behaviors['obstacle_avoiders']:.1f}%")
    
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
        
        # Diversity trend
        recent_diversity = np.mean([g['diversity'] for g in recent_gens])
        early_diversity = np.mean([g['diversity'] for g in early_gens])
        diversity_change = recent_diversity - early_diversity
        
        print(f"\n🧠 ANÁLISIS DE APRENDIZAJE:")
        print("=" * 40)
        print(f"📈 MEJORA EN FITNESS: {fitness_improvement:+.1f}")
        print(f"🍎 MEJORA EN COMIDA: {food_improvement:+.1f}")
        print(f"🧬 CAMBIO EN DIVERSIDAD: {diversity_change:+.4f}")
        
        # Conclusiones
        if fitness_improvement > 10:
            print("✅ APRENDIZAJE CONFIRMADO: Fitness mejorando significativamente")
        elif fitness_improvement > 5:
            print("⚠️ APRENDIZAJE PARCIAL: Fitness mejorando moderadamente")
        else:
            print("❌ PROBLEMA DE APRENDIZAJE: Fitness no mejora")
            
        if food_improvement > 2:
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
