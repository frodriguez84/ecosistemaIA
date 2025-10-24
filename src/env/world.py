"""
Mundo principal del ecosistema evolutivo.
Coordina el entorno, física y recursos.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from .procedural import ProceduralGenerator, WorldConfig, ResourceManager
from .physics import PhysicsEngine, CollisionType
from .resources import ResourceManager as BaseResourceManager


@dataclass
class WorldState:
    """Estado actual del mundo."""
    tick: int = 0
    epoch: int = 0
    total_food: int = 0
    total_obstacles: int = 0
    food_regeneration_rate: float = 0.01
    energy_decay_rate: float = 0.1


class World:
    """Mundo principal del ecosistema evolutivo."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el mundo.
        
        Args:
            config: Configuración del mundo
        """
        self.config = config
        self.state = WorldState()
        
        # Configuración del mundo
        world_config = WorldConfig(
            width=config['simulation']['map_size'][0],
            height=config['simulation']['map_size'][1],
            food_density=config['simulation']['food_density'],
            obstacle_density=config['simulation']['obstacle_density'],
            seed=config['simulation']['random_seed'],
            food_regeneration_rate=config['environment']['food_regeneration_rate']
        )
        
        # Inicializar componentes
        self.generator = ProceduralGenerator(world_config)
        self.physics = PhysicsEngine(world_config.width, world_config.height)
        self.resource_manager = ResourceManager(world_config)
        
        # Configurar obstáculos y comida
        self._setup_world()
        
        # Agentes en el mundo
        self.agents = []
        self.agent_positions = {}
    
    def _setup_world(self) -> None:
        """Configura el mundo inicial."""
        # Agregar obstáculos al motor de física
        for x, y in self.generator.get_obstacle_positions():
            self.physics.add_obstacle(x, y)
        
        # Agregar comida al motor de física
        for x, y, amount in self.generator.get_food_positions():
            self.physics.add_food(x, y, amount)
    
    def add_agent(self, agent) -> None:
        """
        Agrega un agente al mundo.
        
        Args:
            agent: Agente a agregar
        """
        self.agents.append(agent)
        self.agent_positions[agent.id] = (agent.x, agent.y)
        self.physics.add_agent(agent.id, agent.x, agent.y)
    
    def remove_agent(self, agent_id: int) -> None:
        """
        Remueve un agente del mundo.
        
        Args:
            agent_id: ID del agente a remover
        """
        self.agents = [a for a in self.agents if a.id != agent_id]
        if agent_id in self.agent_positions:
            del self.agent_positions[agent_id]
    
    def update(self) -> None:
        """Actualiza el estado del mundo."""
        self.state.tick += 1
        
        # Regenerar recursos
        self.resource_manager.regenerate_resources()
        
        # Actualizar posiciones de agentes en el motor de física
        for agent in self.agents:
            if agent.state.value == 'alive':
                self.physics.update_agent_position(agent.id, agent.x, agent.y)
                self.agent_positions[agent.id] = (agent.x, agent.y)
    
    def check_collision(self, x: float, y: float, radius: float = 1.0, 
                       exclude_agent_id: Optional[int] = None) -> bool:
        """
        Verifica si hay colisión en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            radius: Radio del objeto
            exclude_agent_id: ID de agente a excluir
            
        Returns:
            True si hay colisión
        """
        collision = self.physics.check_collision(x, y, radius, exclude_agent_id)
        return collision.collision_type != CollisionType.NONE
    
    def raycast(self, start_x: float, start_y: float, end_x: float, end_y: float) -> float:
        """
        Realiza un raycast en el mundo.
        
        Args:
            start_x: Posición X inicial
            start_y: Posición Y inicial
            end_x: Posición X final
            end_y: Posición Y final
            
        Returns:
            Distancia normalizada hasta la primera colisión
        """
        return self.physics.raycast(start_x, start_y, end_x, end_y)
    
    def get_food_at_position(self, x: float, y: float, radius: float = 2.0) -> int:
        """
        Obtiene comida en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            radius: Radio de búsqueda
            
        Returns:
            Cantidad de comida encontrada
        """
        return self.physics.get_food_at_position(x, y, radius)
    
    def remove_food_at_position(self, x: float, y: float, amount: int = 1) -> int:
        """
        Remueve comida de una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad a remover
            
        Returns:
            Cantidad realmente removida
        """
        return self.physics.remove_food_at_position(x, y, amount)
    
    def add_food_at_position(self, x: float, y: float, amount: int = 1) -> None:
        """
        Agrega comida en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad a agregar
        """
        self.physics.add_food_at_position(x, y, amount)
    
    def get_food_positions(self) -> List[Tuple[float, float]]:
        """
        Obtiene todas las posiciones de comida.
        
        Returns:
            Lista de tuplas (x, y) con posiciones de comida
        """
        return [(food['x'], food['y']) for food in self.physics.food_items]
    
    def get_other_agents(self, current_agent) -> List[Dict[str, Any]]:
        """
        Obtiene otros agentes (excluyendo el actual).
        
        Args:
            current_agent: Agente actual
            
        Returns:
            Lista de otros agentes
        """
        other_agents = []
        for agent in self.agents:
            if agent.id != current_agent.id and agent.state.value == 'alive':
                other_agents.append({
                    'id': agent.id,
                    'x': agent.x,
                    'y': agent.y,
                    'energy': agent.energy
                })
        return other_agents
    
    def get_agent_count(self) -> int:
        """
        Obtiene el número de agentes vivos.
        
        Returns:
            Número de agentes vivos
        """
        return sum(1 for agent in self.agents if agent.state.value == 'alive')
    
    def get_alive_agents(self) -> List:
        """
        Obtiene todos los agentes vivos.
        
        Returns:
            Lista de agentes vivos
        """
        return [agent for agent in self.agents if agent.state.value == 'alive']
    
    def reset_epoch(self) -> None:
        """Reinicia el mundo para una nueva época."""
        self.state.epoch += 1
        self.state.tick = 0
        
        # Regenerar recursos
        self.resource_manager.regenerate_resources()
        
        # Limpiar agentes muertos
        self.agents = [agent for agent in self.agents if agent.state.value == 'alive']
    
    def get_world_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa del mundo.
        
        Returns:
            Diccionario con información del mundo
        """
        return {
            'state': {
                'tick': self.state.tick,
                'epoch': self.state.epoch,
                'total_food': self.state.total_food,
                'total_obstacles': self.state.total_obstacles
            },
            'agents': {
                'total': len(self.agents),
                'alive': self.get_agent_count(),
                'dead': len(self.agents) - self.get_agent_count()
            },
            'resources': self.resource_manager.get_resource_info(),
            'physics': self.physics.get_physics_info(),
            'world_generator': self.generator.get_world_info()
        }
    
    def get_terrain_info(self) -> Dict[str, Any]:
        """
        Obtiene información del terreno.
        
        Returns:
            Diccionario con información del terreno
        """
        return self.generator.get_world_info()
    
    def save_state(self) -> Dict[str, Any]:
        """
        Guarda el estado actual del mundo.
        
        Returns:
            Diccionario con el estado del mundo
        """
        return {
            'state': {
                'tick': self.state.tick,
                'epoch': self.state.epoch
            },
            'agents': [
                {
                    'id': agent.id,
                    'x': agent.x,
                    'y': agent.y,
                    'angle': agent.angle,
                    'energy': agent.energy,
                    'state': agent.state.value
                }
                for agent in self.agents
            ],
            'food_positions': self.get_food_positions(),
            'config': self.config
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Carga un estado del mundo.
        
        Args:
            state: Estado a cargar
        """
        self.state.tick = state['state']['tick']
        self.state.epoch = state['state']['epoch']
        
        # Limpiar agentes actuales
        self.agents.clear()
        self.agent_positions.clear()
        
        # Cargar agentes
        for agent_data in state['agents']:
            # Crear agente temporal para cargar datos
            # Nota: En una implementación real, necesitarías recrear los agentes
            pass
        
        # Cargar posiciones de comida
        for x, y in state['food_positions']:
            self.add_food_at_position(x, y)
    
    def clear(self) -> None:
        """Limpia el mundo."""
        self.agents.clear()
        self.agent_positions.clear()
        self.physics.clear()
        self.state = WorldState()
