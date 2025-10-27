"""
Algoritmo genético para evolución de agentes.
"""

import random
import numpy as np
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork


class GeneticAlgorithm:
    """Algoritmo genético para evolución de agentes."""
    
    def __init__(self, population_size=20, mutation_rate=0.1, crossover_rate=0.7, elitism=2, 
                 selection_method="elitism", tournament_size=3):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism = elitism
        self.selection_method = selection_method
        self.tournament_size = tournament_size
        self.world = None
        
        print(f"🧬 Algoritmo genético configurado:")
        print(f"   - Población: {population_size}")
        print(f"   - Mutación: {mutation_rate*100}%")
        print(f"   - Cruce: {crossover_rate*100}%")
        print(f"   - Selección: {selection_method.upper()}")
        if selection_method == "tournament":
            print(f"   - Tamaño torneo: {tournament_size}")
        else:
            print(f"   - Élite: {elitism}")
    
    def _create_random_population(self):
        """Crea población inicial aleatoria."""
        agents = []
        attempts = 0
        max_attempts = self.population_size * 50
        
        while len(agents) < self.population_size and attempts < max_attempts:
            # Posición aleatoria en área segura
            x = random.randint(50, 900)  # Evitar área de stats
            y = random.randint(50, 750)  # Evitar área de stats
            
            # Verificar que no esté en obstáculos
            valid_position = True
            if self.world:
                # Verificar colisión con obstáculos
                for obstacle in self.world.obstacles:
                    if obstacle.collides_with(x, y, 35):  # Radio más grande para spawn
                        valid_position = False
                        break
                
                # Verificar colisión con el estanque
                if valid_position:
                    for pond_obj in self.world.pond_obstacles:
                        if pond_obj.collides_with(x, y, 35, 35):
                            valid_position = False
                            break
                
                # Verificar colisión con comida
                if valid_position:
                    for food in self.world.food_items:
                        if not food['eaten']:
                            distance = ((x - food['x'])**2 + (y - food['y'])**2)**0.5
                            if distance < 35:
                                valid_position = False
                                break
                
                # Verificar que tenga al menos una dirección libre
                if valid_position:
                    free_directions = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            test_x = x + dx * 20
                            test_y = y + dy * 20
                            if (0 <= test_x < self.world.screen_width and 
                                0 <= test_y < self.world.screen_height):
                                # Verificar que no esté en obstáculo
                                obstacle_free = True
                                for obstacle in self.world.obstacles:
                                    if obstacle.collides_with(test_x, test_y, 20):
                                        obstacle_free = False
                                        break
                                if obstacle_free:
                                    free_directions += 1
                    
                    if free_directions < 1:
                        valid_position = False
            
            if valid_position:
                from config import SimulationConfig
                brain = SimpleNeuralNetwork(
                    SimulationConfig.INPUT_SIZE,
                    SimulationConfig.HIDDEN_SIZE,
                    SimulationConfig.OUTPUT_SIZE
                )
                agent = AdvancedAgent(x, y, brain)
                agents.append(agent)
            
            attempts += 1
        
        # Si no se pudieron crear suficientes agentes, crear los que se pueda
        if len(agents) < self.population_size:
            print(f"⚠️ Solo se pudieron crear {len(agents)} agentes de {self.population_size}")
        
        return agents
    
    def evolve(self, agents):
        """Evoluciona la población."""
        if not agents:
            return self._create_random_population()
        
        # Calcular fitness de todos los agentes
        for agent in agents:
            agent._calculate_fitness()
        
        # Ordenar por fitness
        agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Crear nueva generación
        new_agents = []
        
        # Aplicar método de selección configurado
        if self.selection_method == "elitism":
            # Elitismo: crear nuevos agentes con cerebros de los mejores (ESTADO RESETEADO)
            for i in range(min(self.elitism, len(agents))):
                if i < len(agents):
                    elite_brain = agents[i].brain
                    # Crear nuevo agente con cerebro del élite pero estado reseteado
                    # Buscar posición válida evitando obstáculos y estanque
                    attempts = 0
                    max_attempts = 100
                    valid_position = False
                    
                    while not valid_position and attempts < max_attempts:
                        x = random.randint(50, 900)
                        y = random.randint(50, 750)
                        valid_position = True
                        
                        # Verificar colisión con obstáculos
                        for obstacle in self.world.obstacles:
                            if obstacle.collides_with(x, y, 35):
                                valid_position = False
                                break
                        
                        # Verificar colisión con el estanque
                        if valid_position:
                            for pond_obj in self.world.pond_obstacles:
                                if pond_obj.collides_with(x, y, 35, 35):
                                    valid_position = False
                                    break
                        
                        attempts += 1
                    
                    # Si no se encontró posición válida, buscar posición segura
                    if not valid_position:
                        # Buscar posición segura que no esté en estanque
                        safe_x, safe_y = 100, 100  # Posición por defecto
                        for test_x in [100, 200, 300, 400, 500, 600, 700, 800]:
                            for test_y in [100, 200, 300, 400, 500, 600]:
                                # Verificar que no esté en estanque
                                safe_position = True
                                for pond_obj in self.world.pond_obstacles:
                                    if pond_obj.collides_with(test_x, test_y, 35, 35):
                                        safe_position = False
                                        break
                                if safe_position:
                                    safe_x, safe_y = test_x, test_y
                                    break
                            if safe_position:
                                break
                        x, y = safe_x, safe_y
                    
                    elite_agent = AdvancedAgent(x, y, elite_brain)
                    new_agents.append(elite_agent)
            # Seleccionar padres restantes por torneo
            parents = self._tournament_selection(agents, self.population_size - self.elitism)
        elif self.selection_method == "tournament":
            # Solo selección por torneo (sin élite)
            parents = self._tournament_selection(agents, self.population_size)
        else:
            # Fallback: usar elitismo
            for i in range(min(self.elitism, len(agents))):
                if i < len(agents):
                    elite_brain = agents[i].brain
                    # Crear nuevo agente con cerebro del élite pero estado reseteado
                    # Buscar posición válida evitando obstáculos y estanque
                    attempts = 0
                    max_attempts = 100
                    valid_position = False
                    
                    while not valid_position and attempts < max_attempts:
                        x = random.randint(50, 900)
                        y = random.randint(50, 750)
                        valid_position = True
                        
                        # Verificar colisión con obstáculos
                        for obstacle in self.world.obstacles:
                            if obstacle.collides_with(x, y, 35):
                                valid_position = False
                                break
                        
                        # Verificar colisión con el estanque
                        if valid_position:
                            for pond_obj in self.world.pond_obstacles:
                                if pond_obj.collides_with(x, y, 35, 35):
                                    valid_position = False
                                    break
                        
                        attempts += 1
                    
                    # Si no se encontró posición válida, buscar posición segura
                    if not valid_position:
                        # Buscar posición segura que no esté en estanque
                        safe_x, safe_y = 100, 100  # Posición por defecto
                        for test_x in [100, 200, 300, 400, 500, 600, 700, 800]:
                            for test_y in [100, 200, 300, 400, 500, 600]:
                                # Verificar que no esté en estanque
                                safe_position = True
                                for pond_obj in self.world.pond_obstacles:
                                    if pond_obj.collides_with(test_x, test_y, 35, 35):
                                        safe_position = False
                                        break
                                if safe_position:
                                    safe_x, safe_y = test_x, test_y
                                    break
                            if safe_position:
                                break
                        x, y = safe_x, safe_y
                    
                    elite_agent = AdvancedAgent(x, y, elite_brain)
                    new_agents.append(elite_agent)
            parents = self._tournament_selection(agents, self.population_size - self.elitism)
        
        # Crear hijos
        while len(new_agents) < self.population_size:
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)
            
            if random.random() < self.crossover_rate:
                # Cruza
                child_brain = parent1.brain.crossover(parent2.brain)
            else:
                # Copia (elite directa)
                from config import SimulationConfig
                child_brain = SimpleNeuralNetwork(
                    SimulationConfig.INPUT_SIZE,
                    SimulationConfig.HIDDEN_SIZE,
                    SimulationConfig.OUTPUT_SIZE
                )
                child_brain.W1 = parent1.brain.W1.copy()
                child_brain.b1 = parent1.brain.b1.copy()
                child_brain.W2 = parent1.brain.W2.copy()
                child_brain.b2 = parent1.brain.b2.copy()
            
            # Mutación adaptativa (más agresiva si diversidad baja)
            mutation_rate = self.mutation_rate
            if len(agents) > 1:
                # Calcular diversidad actual
                fitnesses = [agent.fitness for agent in agents]
                diversity = np.std(fitnesses) / (np.mean(fitnesses) + 1e-6)
                if diversity < 0.15:  # Baja diversidad (AUMENTADO umbral)
                    mutation_rate = min(0.5, self.mutation_rate * 2.5)  # Más agresivo contra convergencia
            
            if random.random() < mutation_rate:
                child_brain.mutate(mutation_rate)
            
            # Crear agente hijo con verificación de colisión
            attempts = 0
            max_attempts = 100
            valid_position = False
            
            while not valid_position and attempts < max_attempts:
                x = random.randint(50, 900)
                y = random.randint(50, 750)
                valid_position = True
                
                # Verificar colisión con obstáculos
                for obstacle in self.world.obstacles:
                    if obstacle.collides_with(x, y, 35):
                        valid_position = False
                        break
                
                # Verificar colisión con el estanque
                if valid_position:
                    for pond_obj in self.world.pond_obstacles:
                        if pond_obj.collides_with(x, y, 35, 35):
                            valid_position = False
                            break
                
                attempts += 1
            
            # Si no se encontró posición válida, usar posición segura
            if not valid_position:
                x = 100
                y = 100
            
            child = AdvancedAgent(x, y, child_brain)
            new_agents.append(child)
        
        return new_agents[:self.population_size]
    
    def _tournament_selection(self, agents, num_parents):
        """Selección por torneo."""
        parents = []
        
        for _ in range(num_parents):
            # Seleccionar agentes aleatorios para el torneo
            tournament = random.sample(agents, min(self.tournament_size, len(agents)))
            # Elegir el mejor del torneo
            winner = max(tournament, key=lambda a: a.fitness)
            parents.append(winner)
        
        return parents
