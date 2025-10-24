"""
Sistema de física para el ecosistema evolutivo.
Maneja colisiones, movimiento y interacciones físicas.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class CollisionType(Enum):
    """Tipos de colisión."""
    NONE = "none"
    WALL = "wall"
    OBSTACLE = "obstacle"
    AGENT = "agent"
    FOOD = "food"


@dataclass
class CollisionResult:
    """Resultado de una colisión."""
    collision_type: CollisionType
    position: Tuple[float, float]
    normal: Tuple[float, float]
    distance: float
    energy_penalty: float = 0.0


class PhysicsEngine:
    """Motor de física del ecosistema."""
    
    def __init__(self, world_width: int, world_height: int):
        """
        Inicializa el motor de física.
        
        Args:
            world_width: Ancho del mundo
            world_height: Alto del mundo
        """
        self.world_width = world_width
        self.world_height = world_height
        self.obstacles = []
        self.agents = []
        self.food_items = []
        
        # Configuración de física
        self.gravity = 0.0  # Sin gravedad en este ecosistema
        self.friction = 0.95
        self.bounce_factor = 0.8
    
    def add_obstacle(self, x: float, y: float, width: float = 1.0, height: float = 1.0) -> None:
        """
        Agrega un obstáculo al mundo.
        
        Args:
            x: Posición X del obstáculo
            y: Posición Y del obstáculo
            width: Ancho del obstáculo
            height: Alto del obstáculo
        """
        self.obstacles.append({
            'x': x, 'y': y, 'width': width, 'height': height
        })
    
    def add_agent(self, agent_id: int, x: float, y: float, radius: float = 1.0) -> None:
        """
        Agrega un agente al mundo.
        
        Args:
            agent_id: ID del agente
            x: Posición X del agente
            y: Posición Y del agente
            radius: Radio del agente
        """
        self.agents.append({
            'id': agent_id, 'x': x, 'y': y, 'radius': radius
        })
    
    def add_food(self, x: float, y: float, amount: int = 1) -> None:
        """
        Agrega comida al mundo.
        
        Args:
            x: Posición X de la comida
            y: Posición Y de la comida
            amount: Cantidad de comida
        """
        self.food_items.append({
            'x': x, 'y': y, 'amount': amount
        })
    
    def check_collision(self, x: float, y: float, radius: float = 1.0, 
                       exclude_agent_id: Optional[int] = None) -> CollisionResult:
        """
        Verifica colisiones en una posición.
        
        Args:
            x: Posición X a verificar
            y: Posición Y a verificar
            radius: Radio del objeto
            exclude_agent_id: ID de agente a excluir de la verificación
            
        Returns:
            Resultado de la colisión
        """
        # Verificar límites del mundo
        if x < radius or x >= self.world_width - radius:
            return CollisionResult(
                collision_type=CollisionType.WALL,
                position=(x, y),
                normal=(-1 if x < radius else 1, 0),
                distance=abs(x - radius if x < radius else x - (self.world_width - radius)),
                energy_penalty=10.0
            )
        
        if y < radius or y >= self.world_height - radius:
            return CollisionResult(
                collision_type=CollisionType.WALL,
                position=(x, y),
                normal=(0, -1 if y < radius else 1),
                distance=abs(y - radius if y < radius else y - (self.world_height - radius)),
                energy_penalty=10.0
            )
        
        # Verificar colisiones con obstáculos
        for obstacle in self.obstacles:
            if self._check_rect_circle_collision(
                obstacle['x'], obstacle['y'], obstacle['width'], obstacle['height'],
                x, y, radius
            ):
                return CollisionResult(
                    collision_type=CollisionType.OBSTACLE,
                    position=(x, y),
                    normal=(0, 0),  # Se calculará después
                    distance=0,
                    energy_penalty=5.0
                )
        
        # Verificar colisiones con otros agentes
        for agent in self.agents:
            if (exclude_agent_id is None or agent['id'] != exclude_agent_id):
                distance = np.sqrt((x - agent['x'])**2 + (y - agent['y'])**2)
                if distance < radius + agent['radius']:
                    return CollisionResult(
                        collision_type=CollisionType.AGENT,
                        position=(x, y),
                        normal=self._calculate_normal(x, y, agent['x'], agent['y']),
                        distance=distance,
                        energy_penalty=2.0
                    )
        
        return CollisionResult(
            collision_type=CollisionType.NONE,
            position=(x, y),
            normal=(0, 0),
            distance=0
        )
    
    def _check_rect_circle_collision(self, rect_x: float, rect_y: float, 
                                   rect_width: float, rect_height: float,
                                   circle_x: float, circle_y: float, 
                                   circle_radius: float) -> bool:
        """
        Verifica colisión entre rectángulo y círculo.
        
        Args:
            rect_x: Posición X del rectángulo
            rect_y: Posición Y del rectángulo
            rect_width: Ancho del rectángulo
            rect_height: Alto del rectángulo
            circle_x: Posición X del círculo
            circle_y: Posición Y del círculo
            circle_radius: Radio del círculo
            
        Returns:
            True si hay colisión
        """
        # Encontrar el punto más cercano en el rectángulo al círculo
        closest_x = max(rect_x, min(circle_x, rect_x + rect_width))
        closest_y = max(rect_y, min(circle_y, rect_y + rect_height))
        
        # Calcular distancia
        distance = np.sqrt((circle_x - closest_x)**2 + (circle_y - closest_y)**2)
        
        return distance < circle_radius
    
    def _calculate_normal(self, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
        """
        Calcula el vector normal entre dos puntos.
        
        Args:
            x1, y1: Primer punto
            x2, y2: Segundo punto
            
        Returns:
            Vector normal normalizado
        """
        dx = x1 - x2
        dy = y1 - y2
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return (0, 0)
        
        return (dx / length, dy / length)
    
    def raycast(self, start_x: float, start_y: float, end_x: float, end_y: float) -> float:
        """
        Realiza un raycast desde un punto hasta otro.
        
        Args:
            start_x: Posición X inicial
            start_y: Posición Y inicial
            end_x: Posición X final
            end_y: Posición Y final
            
        Returns:
            Distancia hasta la primera colisión (normalizada)
        """
        # Calcular dirección del rayo
        dx = end_x - start_x
        dy = end_y - start_y
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return 1.0
        
        # Normalizar dirección
        dx /= length
        dy /= length
        
        # Verificar colisiones paso a paso
        step_size = 0.5
        steps = int(length / step_size)
        
        for i in range(steps):
            x = start_x + dx * i * step_size
            y = start_y + dy * i * step_size
            
            # Verificar límites del mundo
            if (x < 0 or x >= self.world_width or y < 0 or y >= self.world_height):
                return i * step_size / length
            
            # Verificar colisiones con obstáculos
            for obstacle in self.obstacles:
                if self._check_rect_circle_collision(
                    obstacle['x'], obstacle['y'], obstacle['width'], obstacle['height'],
                    x, y, 0.5
                ):
                    return i * step_size / length
        
        return 1.0  # No hay colisión
    
    def update_agent_position(self, agent_id: int, new_x: float, new_y: float) -> bool:
        """
        Actualiza la posición de un agente.
        
        Args:
            agent_id: ID del agente
            new_x: Nueva posición X
            new_y: Nueva posición Y
            
        Returns:
            True si la actualización fue exitosa
        """
        for agent in self.agents:
            if agent['id'] == agent_id:
                # Verificar colisión en la nueva posición
                collision = self.check_collision(new_x, new_y, agent['radius'], agent_id)
                
                if collision.collision_type == CollisionType.NONE:
                    agent['x'] = new_x
                    agent['y'] = new_y
                    return True
                else:
                    return False
        
        return False
    
    def get_food_at_position(self, x: float, y: float, radius: float = 2.0) -> int:
        """
        Obtiene comida en un radio de una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            radius: Radio de búsqueda
            
        Returns:
            Cantidad de comida encontrada
        """
        total_food = 0
        items_to_remove = []
        
        for i, food in enumerate(self.food_items):
            distance = np.sqrt((x - food['x'])**2 + (y - food['y'])**2)
            if distance <= radius:
                total_food += food['amount']
                items_to_remove.append(i)
        
        # Remover comida encontrada
        for i in reversed(items_to_remove):
            self.food_items.pop(i)
        
        return total_food
    
    def remove_food_at_position(self, x: float, y: float, amount: int = 1) -> int:
        """
        Remueve comida de una posición específica.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad a remover
            
        Returns:
            Cantidad realmente removida
        """
        for i, food in enumerate(self.food_items):
            if abs(x - food['x']) < 1 and abs(y - food['y']) < 1:
                removed = min(amount, food['amount'])
                if removed >= food['amount']:
                    self.food_items.pop(i)
                else:
                    self.food_items[i]['amount'] -= removed
                return removed
        
        return 0
    
    def add_food_at_position(self, x: float, y: float, amount: int = 1) -> None:
        """
        Agrega comida en una posición específica.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad a agregar
        """
        # Verificar si ya hay comida en esa posición
        for food in self.food_items:
            if abs(x - food['x']) < 1 and abs(y - food['y']) < 1:
                food['amount'] += amount
                return
        
        # Agregar nueva comida
        self.food_items.append({'x': x, 'y': y, 'amount': amount})
    
    def get_physics_info(self) -> Dict[str, Any]:
        """
        Obtiene información del estado físico.
        
        Returns:
            Diccionario con información física
        """
        return {
            'world_size': (self.world_width, self.world_height),
            'obstacles': len(self.obstacles),
            'agents': len(self.agents),
            'food_items': len(self.food_items),
            'total_food': sum(food['amount'] for food in self.food_items)
        }
    
    def clear(self) -> None:
        """Limpia todos los objetos del mundo."""
        self.obstacles.clear()
        self.agents.clear()
        self.food_items.clear()
    
    def reset(self) -> None:
        """Reinicia el motor de física."""
        self.clear()
