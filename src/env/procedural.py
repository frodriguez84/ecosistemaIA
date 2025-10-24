"""
Generación procedural del entorno para el ecosistema evolutivo.
Crea mapas, comida y obstáculos usando ruido Perlin y semillas reproducibles.
"""

import numpy as np
import random
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
# import noise  # Comentado temporalmente
import random
import math


@dataclass
class WorldConfig:
    """Configuración para la generación del mundo."""
    width: int = 80
    height: int = 80
    food_density: float = 0.1
    obstacle_density: float = 0.05
    seed: int = 42
    noise_scale: float = 0.1
    food_regeneration_rate: float = 0.01
    obstacle_penalty: float = 5.0


class ProceduralGenerator:
    """Generador procedural de entornos."""
    
    def __init__(self, config: WorldConfig):
        """
        Inicializa el generador.
        
        Args:
            config: Configuración del mundo
        """
        self.config = config
        self.noise_map = None
        self.food_map = None
        self.obstacle_map = None
        
        # Generar mapas
        self._generate_noise_map()
        self._generate_obstacle_map()
        self._generate_food_map()
    
    def _generate_noise_map(self) -> None:
        """Genera el mapa de ruido base."""
        self.noise_map = np.zeros((self.config.height, self.config.width))
        
        for y in range(self.config.height):
            for x in range(self.config.width):
                # Usar ruido simple para generar variación natural
                noise_value = self._simple_noise(
                    x * self.config.noise_scale,
                    y * self.config.noise_scale
                )
                self.noise_map[y, x] = noise_value
    
    def _simple_noise(self, x: float, y: float) -> float:
        """Implementación simple de ruido."""
        # Función de ruido simple basada en seno y coseno
        return (math.sin(x) * math.cos(y) + math.sin(x * 2) * math.cos(y * 2) * 0.5) / 2
    
    def _generate_obstacle_map(self) -> None:
        """Genera el mapa de obstáculos."""
        self.obstacle_map = np.zeros((self.config.height, self.config.width), dtype=bool)
        
        # Usar ruido para determinar ubicación de obstáculos
        obstacle_threshold = np.percentile(self.noise_map, (1 - self.config.obstacle_density) * 100)
        
        for y in range(self.config.height):
            for x in range(self.config.width):
                if self.noise_map[y, x] > obstacle_threshold:
                    self.obstacle_map[y, x] = True
    
    def _generate_food_map(self) -> None:
        """Genera el mapa de comida."""
        self.food_map = np.zeros((self.config.height, self.config.width), dtype=int)
        
        # Distribuir comida basada en ruido
        food_threshold = np.percentile(self.noise_map, (1 - self.config.food_density) * 100)
        
        for y in range(self.config.height):
            for x in range(self.config.width):
                if (self.noise_map[y, x] < food_threshold and 
                    not self.obstacle_map[y, x]):
                    # Cantidad de comida basada en el ruido local
                    food_amount = int((food_threshold - self.noise_map[y, x]) * 10)
                    self.food_map[y, x] = max(1, food_amount)
    
    def get_obstacle_positions(self) -> List[Tuple[int, int]]:
        """
        Obtiene las posiciones de todos los obstáculos.
        
        Returns:
            Lista de tuplas (x, y) con posiciones de obstáculos
        """
        positions = []
        for y in range(self.config.height):
            for x in range(self.config.width):
                if self.obstacle_map[y, x]:
                    positions.append((x, y))
        return positions
    
    def get_food_positions(self) -> List[Tuple[int, int, int]]:
        """
        Obtiene las posiciones de toda la comida.
        
        Returns:
            Lista de tuplas (x, y, amount) con posiciones y cantidades de comida
        """
        positions = []
        for y in range(self.config.height):
            for x in range(self.config.width):
                if self.food_map[y, x] > 0:
                    positions.append((x, y, self.food_map[y, x]))
        return positions
    
    def check_obstacle(self, x: int, y: int) -> bool:
        """
        Verifica si hay un obstáculo en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            True si hay obstáculo
        """
        if (0 <= x < self.config.width and 0 <= y < self.config.height):
            return self.obstacle_map[y, x]
        return True  # Fuera de límites se considera obstáculo
    
    def get_food_at(self, x: int, y: int) -> int:
        """
        Obtiene la cantidad de comida en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            Cantidad de comida
        """
        if (0 <= x < self.config.width and 0 <= y < self.config.height):
            return self.food_map[y, x]
        return 0
    
    def remove_food_at(self, x: int, y: int, amount: int = 1) -> int:
        """
        Remueve comida de una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            amount: Cantidad a remover
            
        Returns:
            Cantidad realmente removida
        """
        if (0 <= x < self.config.width and 0 <= y < self.config.height):
            available = self.food_map[y, x]
            removed = min(amount, available)
            self.food_map[y, x] -= removed
            return removed
        return 0
    
    def add_food_at(self, x: int, y: int, amount: int = 1) -> None:
        """
        Agrega comida en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            amount: Cantidad a agregar
        """
        if (0 <= x < self.config.width and 0 <= y < self.config.height):
            self.food_map[y, x] += amount
    
    def regenerate_food(self) -> None:
        """Regenera comida en el mapa."""
        for y in range(self.config.height):
            for x in range(self.config.width):
                if (not self.obstacle_map[y, x] and 
                    random.random() < self.config.food_regeneration_rate):
                    self.food_map[y, x] += 1
    
    def get_world_info(self) -> Dict[str, Any]:
        """
        Obtiene información del mundo generado.
        
        Returns:
            Diccionario con información del mundo
        """
        obstacle_count = np.sum(self.obstacle_map)
        food_count = np.sum(self.food_map)
        total_cells = self.config.width * self.config.height
        
        return {
            'dimensions': (self.config.width, self.config.height),
            'obstacle_count': int(obstacle_count),
            'food_count': int(food_count),
            'obstacle_density': obstacle_count / total_cells,
            'food_density': food_count / total_cells,
            'seed': self.config.seed
        }


class TerrainGenerator:
    """Generador de terreno con diferentes biomas."""
    
    def __init__(self, config: WorldConfig):
        """
        Inicializa el generador de terreno.
        
        Args:
            config: Configuración del mundo
        """
        self.config = config
        self.terrain_map = None
        self.biome_map = None
        
        self._generate_terrain()
    
    def _generate_terrain(self) -> None:
        """Genera el mapa de terreno."""
        self.terrain_map = np.zeros((self.config.height, self.config.width))
        self.biome_map = np.zeros((self.config.height, self.config.width), dtype=int)
        
        # Generar diferentes capas de ruido
        for y in range(self.config.height):
            for x in range(self.config.width):
                # Ruido de temperatura
                temp_noise = self._simple_noise(x * 0.05, y * 0.05)
                
                # Ruido de humedad
                humidity_noise = self._simple_noise(x * 0.03, y * 0.03)
                
                # Determinar bioma
                if temp_noise > 0.3:
                    if humidity_noise > 0.2:
                        biome = 0  # Bosque
                    else:
                        biome = 1  # Desierto
                else:
                    if humidity_noise > 0.1:
                        biome = 2  # Pradera
                    else:
                        biome = 3  # Tundra
                
                self.biome_map[y, x] = biome
                self.terrain_map[y, x] = temp_noise + humidity_noise
    
    def _simple_noise(self, x: float, y: float) -> float:
        """Implementación simple de ruido."""
        # Función de ruido simple basada en seno y coseno
        return (math.sin(x) * math.cos(y) + math.sin(x * 2) * math.cos(y * 2) * 0.5) / 2
    
    def get_biome_at(self, x: int, y: int) -> int:
        """
        Obtiene el bioma en una posición.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
            
        Returns:
            ID del bioma
        """
        if (0 <= x < self.config.width and 0 <= y < self.config.height):
            return self.biome_map[y, x]
        return 0
    
    def get_terrain_info(self) -> Dict[str, Any]:
        """
        Obtiene información del terreno.
        
        Returns:
            Diccionario con información del terreno
        """
        biome_counts = np.bincount(self.biome_map.flatten())
        biome_names = ['Bosque', 'Desierto', 'Pradera', 'Tundra']
        
        biome_info = {}
        for i, count in enumerate(biome_counts):
            if i < len(biome_names):
                biome_info[biome_names[i]] = int(count)
        
        return {
            'biomes': biome_info,
            'terrain_variance': float(np.var(self.terrain_map))
        }


class ResourceManager:
    """Gestor de recursos del entorno."""
    
    def __init__(self, config: WorldConfig):
        """
        Inicializa el gestor de recursos.
        
        Args:
            config: Configuración del mundo
        """
        self.config = config
        self.food_positions = []
        self.obstacle_positions = []
        self.regeneration_timer = 0
        
        self._initialize_resources()
    
    def _initialize_resources(self) -> None:
        """Inicializa los recursos del mundo."""
        # Generar comida
        total_food = int(self.config.width * self.config.height * self.config.food_density)
        
        for _ in range(total_food):
            x = random.randint(0, self.config.width - 1)
            y = random.randint(0, self.config.height - 1)
            amount = random.randint(1, 5)
            self.food_positions.append((x, y, amount))
        
        # Generar obstáculos
        total_obstacles = int(self.config.width * self.config.height * self.config.obstacle_density)
        
        for _ in range(total_obstacles):
            x = random.randint(0, self.config.width - 1)
            y = random.randint(0, self.config.height - 1)
            self.obstacle_positions.append((x, y))
    
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
        for i, (fx, fy, food_amount) in enumerate(self.food_positions):
            if abs(x - fx) < 1 and abs(y - fy) < 1:
                removed = min(amount, food_amount)
                if removed >= food_amount:
                    self.food_positions.pop(i)
                else:
                    self.food_positions[i] = (fx, fy, food_amount - removed)
                return removed
        
        return 0
    
    def check_obstacle_at_position(self, x: float, y: int) -> bool:
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
        
        if self.regeneration_timer >= 100:  # Cada 100 ticks
            self.regeneration_timer = 0
            
            # Regenerar comida
            if random.random() < self.config.food_regeneration_rate:
                x = random.randint(0, self.config.width - 1)
                y = random.randint(0, self.config.height - 1)
                amount = random.randint(1, 3)
                self.food_positions.append((x, y, amount))
    
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
            'regeneration_timer': self.regeneration_timer
        }
