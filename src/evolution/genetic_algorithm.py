"""
Algoritmo genético para evolución de agentes.
"""

import random
import numpy as np
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork


class GeneticAlgorithm:
    """Algoritmo genético para evolución de agentes."""
    
    def __init__(self, population_size=20, mutation_rate=0.1, crossover_rate=0.7, elitism=2, 
                 selection_method="elitism", tournament_size=3, meeting_pool_fraction=0.4):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism = elitism
        self.selection_method = selection_method
        self.tournament_size = tournament_size
        self.meeting_pool_fraction = meeting_pool_fraction
        
        print(f"🧬 Algoritmo genético configurado:")
        print(f"   - Población: {population_size}")
        print(f"   - Mutación: {mutation_rate*100}%")
        print(f"   - Cruce: {crossover_rate*100}%")
        print(f"   - Selección: {selection_method.upper()}")
        if selection_method == "tournament":
            print(f"   - Tamaño torneo: {tournament_size}")
        elif selection_method == "meeting_pool":
            print(f"   - Pool: top {int(meeting_pool_fraction*100)}% por ranking")
        else:
            print(f"   - Élite: {elitism}")
    
    def _create_random_population(self):
        """Crea la población con cerebros al azar, en (0, 0): la ubica main.py."""
        from config import SimulationConfig
        agents = []
        for _ in range(self.population_size):
            brain = SimpleNeuralNetwork(
                SimulationConfig.INPUT_SIZE,
                SimulationConfig.HIDDEN_SIZE,
                SimulationConfig.OUTPUT_SIZE
            )
            agents.append(AdvancedAgent(0, 0, brain))
        return agents

    def evolve(self, agents, generation=1):
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
        if self.selection_method == "tournament":
            # Solo selección por torneo (sin élite)
            parents = self._tournament_selection(agents, self.population_size)
        elif self.selection_method == "meeting_pool":
            # Meeting pool por ranking + elitismo configurable
            for i in range(min(self.elitism, len(agents))):
                # Nuevo agente con el cerebro del élite, estado reseteado
                new_agents.append(AdvancedAgent(0, 0, agents[i].brain))
            parents = self._meeting_pool_selection(agents, self.population_size - len(new_agents))
        else:
            # Elitismo: "elitism", y también cualquier método que no se reconozca
            for i in range(min(self.elitism, len(agents))):
                # Nuevo agente con el cerebro del élite, estado reseteado
                new_agents.append(AdvancedAgent(0, 0, agents[i].brain))
            # Seleccionar padres restantes por torneo
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
                # Copiar todas las capas de forma segura
                if hasattr(child_brain, 'copy_from'):
                    child_brain.copy_from(parent1.brain)
                else:
                    # Fallback para estructuras antiguas
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
            
            # Crear agente hijo (lo ubica main.py)
            child = AdvancedAgent(0, 0, child_brain)
            new_agents.append(child)
        
        new_agents = new_agents[:self.population_size]
        
        # ===== INMIGRACIÓN PERIÓDICA =====
        # Introducir agentes completamente aleatorios para mantener diversidad genética
        from config import SimulationConfig
        if (SimulationConfig.IMMIGRATION_ENABLED and 
            generation > 0 and 
            generation % SimulationConfig.IMMIGRATION_FREQUENCY == 0):
            
            immigration_count = min(SimulationConfig.IMMIGRATION_COUNT, len(new_agents))
            
            # Ordenar agentes por fitness (peores al final)
            new_agents.sort(key=lambda a: a.fitness, reverse=True)
            
            # Reemplazar los peores agentes con inmigrantes aleatorios
            immigrant_agents = self._create_immigrant_agents(immigration_count)
            
            # Reemplazar los últimos (peores) agentes
            for i in range(immigration_count):
                if i < len(immigrant_agents):
                    new_agents[-(i+1)] = immigrant_agents[i]
            
            print(f"🌍 Inmigración aplicada: {immigration_count} nuevos agentes aleatorios introducidos (gen {generation})")
        
        return new_agents
    
    def _create_immigrant_agents(self, count):
        """Crea agentes inmigrantes con cerebros al azar, en (0, 0): los ubica main.py."""
        from config import SimulationConfig
        immigrants = []
        for _ in range(count):
            random_brain = SimpleNeuralNetwork(
                SimulationConfig.INPUT_SIZE,
                SimulationConfig.HIDDEN_SIZE,
                SimulationConfig.OUTPUT_SIZE
            )
            immigrants.append(AdvancedAgent(0, 0, random_brain))
        return immigrants
    
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

    def _meeting_pool_selection(self, agents, num_parents):
        """Selección meeting pool por ranking: se toma el top X% y se elige al azar dentro del pool."""
        if num_parents <= 0:
            return []
        if not agents:
            return []
        k = max(2, int(len(agents) * max(0.05, min(0.95, self.meeting_pool_fraction))))
        pool = agents[:k]
        parents = []
        for _ in range(num_parents):
            parents.append(random.choice(pool))
        return parents
