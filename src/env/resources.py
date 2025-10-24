"""
Gestión de recursos del entorno.
Maneja comida, obstáculos y regeneración de recursos.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ResourceConfig:
    """Configuración de recursos."""
    food_regeneration_rate: float = 0.01
    food_max_per_position: int = 10
    obstacle_penalty: float = 5.0
    boundary_penalty: float = 10.0
    collision_penalty: float = 2.0


class ResourceManager:
    """Gestor de recursos del entorno."""
    
    def __init__(self, config: ResourceConfig):
        """
        Inicializa el gestor de recursos.
        
        Args:
            config: Configuración de recursos
        """
        self.config = config
        self.food_positions = []
        self.obstacle_positions = []
        self.regeneration_timer = 0
        
        # Estadísticas
        self.total_food_generated = 0
        self.total_food_consumed = 0
        self.total_obstacles = 0
    
    def add_food(self, x: float, y: float, amount: int = 1) -> None:
        """
        Agrega comida en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad de comida
        """
        # Verificar si ya hay comida en esa posición
        for i, (fx, fy, food_amount) in enumerate(self.food_positions):
            if abs(x - fx) < 1 and abs(y - fy) < 1:
                new_amount = min(food_amount + amount, self.config.food_max_per_position)
                self.food_positions[i] = (fx, fy, new_amount)
                self.total_food_generated += amount
                return
        
        # Agregar nueva comida
        self.food_positions.append((x, y, amount))
        self.total_food_generated += amount
    
    def remove_food(self, x: float, y: float, amount: int = 1) -> int:
        """
        Remueve comida de una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            amount: Cantidad a remover
            
        Returns:
            Cantidad realmente removida
        """
        for i, (fx, fy, food_amount) in enumerate(self.food_positions):
            if abs(x - fx) < 1 and abs(y - fy) < 1:
                removed = min(amount, food_amount)
                if removed >= food_amount:
                    self.food_positions.pop(i)
                else:
                    self.food_positions[i] = (fx, fy, food_amount - removed)
                
                self.total_food_consumed += removed
                return removed
        
        return 0
    
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
        positions_to_remove = []
        
        for i, (fx, fy, amount) in enumerate(self.food_positions):
            distance = np.sqrt((x - fx)**2 + (y - fy)**2)
            if distance <= radius:
                total_food += amount
                positions_to_remove.append(i)
        
        # Remover comida encontrada
        for i in reversed(positions_to_remove):
            self.food_positions.pop(i)
            self.total_food_consumed += self.food_positions[i][2]
        
        return total_food
    
    def add_obstacle(self, x: float, y: float) -> None:
        """
        Agrega un obstáculo en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
        """
        self.obstacle_positions.append((x, y))
        self.total_obstacles += 1
    
    def check_obstacle(self, x: float, y: float) -> bool:
        """
        Verifica si hay un obstáculo en una posición.
        
        Args:
            x: Posición X
            y: Posición Y
            
        Returns:
            True si hay obstáculo
        """
        for ox, oy in self.obstacle_positions:
            if abs(x - ox) < 1 and abs(y - oy) < 1:
                return True
        return False
    
    def regenerate_resources(self) -> None:
        """Regenera recursos en el mundo."""
        self.regeneration_timer += 1
        
        # Regenerar comida periódicamente
        if self.regeneration_timer >= 100:  # Cada 100 ticks
            self.regeneration_timer = 0
            
            if random.random() < self.config.food_regeneration_rate:
                # Generar comida en posición aleatoria
                x = random.uniform(0, 100)  # Asumiendo mundo de 100x100
                y = random.uniform(0, 100)
                amount = random.randint(1, 3)
                self.add_food(x, y, amount)
    
    def get_food_positions(self) -> List[Tuple[float, float]]:
        """
        Obtiene todas las posiciones de comida.
        
        Returns:
            Lista de tuplas (x, y) con posiciones de comida
        """
        return [(x, y) for x, y, _ in self.food_positions]
    
    def get_obstacle_positions(self) -> List[Tuple[float, float]]:
        """
        Obtiene todas las posiciones de obstáculos.
        
        Returns:
            Lista de tuplas (x, y) con posiciones de obstáculos
        """
        return self.obstacle_positions.copy()
    
    def get_resource_density(self, x: float, y: float, radius: float = 10.0) -> Dict[str, float]:
        """
        Obtiene la densidad de recursos en un área.
        
        Args:
            x: Posición X central
            y: Posición Y central
            radius: Radio del área
            
        Returns:
            Diccionario con densidades de recursos
        """
        food_count = 0
        obstacle_count = 0
        total_area = np.pi * radius**2
        
        for fx, fy, _ in self.food_positions:
            distance = np.sqrt((x - fx)**2 + (y - fy)**2)
            if distance <= radius:
                food_count += 1
        
        for ox, oy in self.obstacle_positions:
            distance = np.sqrt((x - ox)**2 + (y - oy)**2)
            if distance <= radius:
                obstacle_count += 1
        
        return {
            'food_density': food_count / total_area,
            'obstacle_density': obstacle_count / total_area,
            'food_count': food_count,
            'obstacle_count': obstacle_count
        }
    
    def get_resource_info(self) -> Dict[str, Any]:
        """
        Obtiene información de los recursos.
        
        Returns:
            Diccionario con información de recursos
        """
        total_food = sum(amount for _, _, amount in self.food_positions)
        
        return {
            'food_positions': len(self.food_positions),
            'total_food': total_food,
            'obstacle_positions': len(self.obstacle_positions),
            'regeneration_timer': self.regeneration_timer,
            'total_food_generated': self.total_food_generated,
            'total_food_consumed': self.total_food_consumed,
            'total_obstacles': self.total_obstacles,
            'food_consumption_rate': self.total_food_consumed / max(1, self.regeneration_timer)
        }
    
    def clear_food(self) -> None:
        """Limpia toda la comida del mundo."""
        self.food_positions.clear()
    
    def clear_obstacles(self) -> None:
        """Limpia todos los obstáculos del mundo."""
        self.obstacle_positions.clear()
    
    def clear_all(self) -> None:
        """Limpia todos los recursos del mundo."""
        self.clear_food()
        self.clear_obstacles()
        self.regeneration_timer = 0
        self.total_food_generated = 0
        self.total_food_consumed = 0
        self.total_obstacles = 0
    
    def save_state(self) -> Dict[str, Any]:
        """
        Guarda el estado de los recursos.
        
        Returns:
            Diccionario con el estado de los recursos
        """
        return {
            'food_positions': self.food_positions,
            'obstacle_positions': self.obstacle_positions,
            'regeneration_timer': self.regeneration_timer,
            'total_food_generated': self.total_food_generated,
            'total_food_consumed': self.total_food_consumed,
            'total_obstacles': self.total_obstacles
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Carga un estado de recursos.
        
        Args:
            state: Estado a cargar
        """
        self.food_positions = state['food_positions']
        self.obstacle_positions = state['obstacle_positions']
        self.regeneration_timer = state['regeneration_timer']
        self.total_food_generated = state['total_food_generated']
        self.total_food_consumed = state['total_food_consumed']
        self.total_obstacles = state['total_obstacles']
