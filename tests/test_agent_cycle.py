"""
Tests para el ciclo de vida de los agentes.
"""

import pytest
import numpy as np
from src.agents import Agent
from src.core import EventType, emit_event


class TestAgentCycle:
    """Tests para el ciclo de vida de los agentes."""
    
    def test_agent_creation(self):
        """Test de creación de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        
        assert agent.id == 1
        assert agent.x == 10.0
        assert agent.y == 20.0
        assert agent.angle == 0.0
        assert agent.state.value == 'alive'
        assert agent.energy > 0
    
    def test_agent_movement(self):
        """Test de movimiento de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        initial_x, initial_y = agent.x, agent.y
        
        # Simular movimiento
        agent.x += 5.0
        agent.y += 3.0
        
        assert agent.x == initial_x + 5.0
        assert agent.y == initial_y + 3.0
    
    def test_agent_energy_decay(self):
        """Test de decaimiento de energía."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        initial_energy = agent.energy
        
        # Simular decaimiento
        agent.energy -= 1.0
        
        assert agent.energy < initial_energy
    
    def test_agent_death(self):
        """Test de muerte de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        
        # Simular muerte
        agent.die("test")
        
        assert agent.state.value == 'dead'
        assert agent.energy == 0
    
    def test_agent_reproduction(self):
        """Test de reproducción de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        agent.energy = 100.0  # Energía suficiente
        
        # Intentar reproducirse
        offspring = agent.reproduce()
        
        assert offspring is not None
        assert offspring.id != agent.id
        assert agent.energy < 100.0  # Energía reducida
    
    def test_agent_fitness_calculation(self):
        """Test de cálculo de fitness."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        
        # Simular algunas estadísticas
        agent.stats.age = 100
        agent.stats.food_eaten = 10
        agent.stats.distance_traveled = 50.0
        
        fitness = agent.calculate_fitness()
        
        assert fitness >= 0.0
        assert fitness <= 1.0
    
    def test_agent_genome_operations(self):
        """Test de operaciones con genoma."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        
        # Obtener genoma
        genome = agent.get_genome()
        assert isinstance(genome, list)
        assert len(genome) > 0
        
        # Establecer nuevo genoma
        new_genome = [0.1, 0.2, 0.3, 0.4]
        agent.set_genome(new_genome)
        
        # Verificar que se estableció
        assert agent.get_genome() == new_genome
    
    def test_agent_cloning(self):
        """Test de clonación de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        agent.energy = 50.0
        agent.stats.age = 25
        
        clone = agent.clone()
        
        assert clone.id == agent.id
        assert clone.x == agent.x
        assert clone.y == agent.y
        assert clone.energy == agent.energy
        assert clone.stats.age == agent.stats.age
    
    def test_agent_reset(self):
        """Test de reinicio de agente."""
        agent = Agent(1, 10.0, 20.0, 0.0)
        agent.energy = 50.0
        agent.stats.age = 25
        
        # Reiniciar
        agent.reset(15.0, 25.0, 1.5)
        
        assert agent.x == 15.0
        assert agent.y == 25.0
        assert agent.angle == 1.5
        assert agent.energy == agent.energy_max
        assert agent.stats.age == 0
