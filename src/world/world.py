"""
Mundo del ecosistema con obstáculos, comida y objetos.
"""

import random
import pygame
from .obstacles import Obstacle


class World:
    """Mundo del ecosistema con obstáculos."""
    
    def __init__(self, screen_width, screen_height, food_count=40):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.food_count = food_count  # Cantidad de comida configurable
        self.food_items = []
        self.obstacles = []
        self.manual_obstacles = []  # Obstáculos creados manualmente
        self.tick = 0
        
        # Generar obstáculos automáticamente
        self._generate_obstacles()
        
        # Generar comida inicial (solo una vez por generación)
        self._generate_food(self.food_count)  # Usar cantidad configurable
    
    def _check_collision_with_objects(self, x, y, radius, existing_objects):
        """Verifica colisión con objetos existentes."""
        for obj in existing_objects:
            if hasattr(obj, 'collides_with'):
                if obj.collides_with(x, y, radius):
                    return True
            elif hasattr(obj, 'x') and hasattr(obj, 'y'):
                # Para objetos simples como comida
                distance = ((x - obj['x'])**2 + (y - obj['y'])**2)**0.5
                if distance < radius + 15:  # Radio de seguridad
                    return True
        return False
    
    def _generate_food(self, count):
        """Genera comida en el mundo, evitando obstáculos y otros objetos."""
        attempts = 0
        max_attempts = count * 20  # Más intentos para evitar superposición
        
        while len(self.food_items) < count and attempts < max_attempts:
            food_x = random.randint(20, self.screen_width - 20)
            food_y = random.randint(20, self.screen_height - 20)
            
            # Verificar que no esté sobre obstáculos
            valid_position = True
            for obstacle in self.obstacles:
                if obstacle.collides_with(food_x, food_y, 20):  # Radio más grande
                    valid_position = False
                    break
            
            # Verificar que no se superponga con otra comida
            if valid_position:
                if not self._check_collision_with_objects(food_x, food_y, 25, self.food_items):
                    food = {
                        'x': food_x,
                        'y': food_y,
                        'eaten': False
                    }
                    self.food_items.append(food)
            
            attempts += 1
    
    def _generate_obstacles_with_manual(self, manual_obstacles):
        """Genera obstáculos automáticos respetando los obstáculos manuales."""
        self.obstacles = []
        
        # Añadir obstáculos manuales primero
        self.obstacles.extend(manual_obstacles)
        self.manual_obstacles = manual_obstacles
        
        # Generar obstáculos automáticos (respetando manuales)
        self._generate_obstacles_auto()
    
    def _generate_obstacles(self):
        """Genera un bosque con caminos naturales."""
        self.obstacles = []
        self._generate_obstacles_auto()
    
    def _generate_obstacles_auto(self):
        """Genera obstáculos automáticos respetando los existentes."""
        
        # Generar paredes conectadas (líneas, L, cuadrado 2x2)
        self._generate_connected_walls()
        
        # Generar BOSQUE DENSO con caminos
        self._generate_forest_with_paths()
        
        # Generar grupos de árboles conectados
        self._generate_connected_trees()
        
        # Generar agua conectada
        self._generate_connected_water()
        
        
        # Generar casitas (hut) con colisión - SIN SUPERPOSICIÓN
        for _ in range(random.randint(6, 7)):
            attempts = 0
            max_attempts = 50
            placed = False
            
            while not placed and attempts < max_attempts:
                x = random.randint(50, self.screen_width - 50)
                y = random.randint(50, self.screen_height - 50)
                
                # Verificar que no se superponga con otros obstáculos
                if not self._check_collision_with_objects(x, y, 30, self.obstacles):
                    self.obstacles.append(Obstacle(x, y, 20, 20, "hut"))
                    placed = True
                attempts += 1
        
        # Generar pociones rojas que curan - SIN SUPERPOSICIÓN
        for _ in range(random.randint(3, 5)):
            attempts = 0
            max_attempts = 50
            placed = False
            
            while not placed and attempts < max_attempts:
                x = random.randint(50, self.screen_width - 50)
                y = random.randint(50, self.screen_height - 50)
                
                # Verificar que no se superponga con otros obstáculos
                if not self._check_collision_with_objects(x, y, 25, self.obstacles):
                    self.obstacles.append(Obstacle(x, y, 16, 16, "potion"))
                    placed = True
                attempts += 1
    
    def _generate_forest_with_paths(self):
        """Genera árboles aleatorios con algunos caminos - SIN SUPERPOSICIÓN."""
        # Generar árboles aleatorios (más árboles)
        for _ in range(random.randint(25, 35)):
            attempts = 0
            max_attempts = 50
            placed = False
            
            while not placed and attempts < max_attempts:
                x = random.randint(50, self.screen_width - 50)
                y = random.randint(50, self.screen_height - 50)
                
                # Verificar que no se superponga con otros obstáculos
                if not self._check_collision_with_objects(x, y, 25, self.obstacles):
                    self.obstacles.append(Obstacle(x, y, 20, 20, "tree"))
                    placed = True
                attempts += 1
    
    def _generate_connected_trees(self):
        """Genera grupos de árboles conectados."""
        # Crear 3-4 grupos de árboles
        for _ in range(random.randint(3, 4)):
            center_x = random.randint(100, self.screen_width - 100)
            center_y = random.randint(100, self.screen_height - 100)
            
            # Generar 3-5 árboles alrededor del centro
            for _ in range(random.randint(3, 5)):
                attempts = 0
                max_attempts = 30
                placed = False
                
                while not placed and attempts < max_attempts:
                    # Posición aleatoria cerca del centro
                    x = center_x + random.randint(-60, 60)
                    y = center_y + random.randint(-60, 60)
                    
                    # Verificar que esté dentro de la pantalla
                    if 50 <= x <= self.screen_width - 50 and 50 <= y <= self.screen_height - 50:
                        # Verificar que no se superponga
                        if not self._check_collision_with_objects(x, y, 25, self.obstacles):
                            self.obstacles.append(Obstacle(x, y, 20, 20, "tree"))
                            placed = True
                    
                    attempts += 1
    
    def _generate_connected_water(self):
        """Genera agua conectada en grupos."""
        # Crear 2-3 grupos de agua
        for _ in range(random.randint(2, 3)):
            center_x = random.randint(100, self.screen_width - 100)
            center_y = random.randint(100, self.screen_height - 100)
            
            # Generar 4-6 bloques de agua conectados
            for _ in range(random.randint(4, 6)):
                attempts = 0
                max_attempts = 30
                placed = False
                
                while not placed and attempts < max_attempts:
                    # Posición aleatoria cerca del centro
                    x = center_x + random.randint(-80, 80)
                    y = center_y + random.randint(-80, 80)
                    
                    # Verificar que esté dentro de la pantalla
                    if 50 <= x <= self.screen_width - 50 and 50 <= y <= self.screen_height - 50:
                        # Verificar que no se superponga
                        if not self._check_collision_with_objects(x, y, 25, self.obstacles):
                            self.obstacles.append(Obstacle(x, y, 20, 20, "water"))
                            placed = True
                    
                    attempts += 1
    
    def _generate_connected_walls(self):
        """Genera paredes conectadas (líneas, L, cuadrado 2x2)."""
        # Generar algunas líneas de paredes
        for _ in range(random.randint(2, 3)):
            start_x = random.randint(100, self.screen_width - 200)
            start_y = random.randint(100, self.screen_height - 200)
            
            # Línea horizontal o vertical
            if random.choice([True, False]):
                # Línea horizontal
                for i in range(random.randint(3, 6)):
                    x = start_x + i * 20
                    y = start_y
                    if x < self.screen_width - 20:
                        self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
            else:
                # Línea vertical
                for i in range(random.randint(3, 6)):
                    x = start_x
                    y = start_y + i * 20
                    if y < self.screen_height - 20:
                        self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
        
        # Generar algunas formas L
        for _ in range(random.randint(1, 2)):
            start_x = random.randint(100, self.screen_width - 200)
            start_y = random.randint(100, self.screen_height - 200)
            
            # Forma L
            for i in range(3):
                x = start_x + i * 20
                y = start_y
                if x < self.screen_width - 20:
                    self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
            
            for i in range(2):
                x = start_x
                y = start_y + (i + 1) * 20
                if y < self.screen_height - 20:
                    self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
        
        # Generar algunos cuadrados 2x2
        for _ in range(random.randint(1, 2)):
            start_x = random.randint(100, self.screen_width - 200)
            start_y = random.randint(100, self.screen_height - 200)
            
            # Cuadrado 2x2
            for i in range(2):
                for j in range(2):
                    x = start_x + i * 20
                    y = start_y + j * 20
                    if x < self.screen_width - 20 and y < self.screen_height - 20:
                        self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
    
    def update(self):
        """Actualiza el mundo."""
        self.tick += 1
        # NO regenerar comida - solo la inicial por generación
    
    def reset_food(self):
        """Resetea toda la comida y regenera obstáculos, preservando objetos manuales."""
        self.food_items = []
        
        # Preservar objetos manuales
        manual_obstacles_backup = self.manual_obstacles.copy()
        
        # Regenerar obstáculos automáticos (respetando manuales)
        self._generate_obstacles_with_manual(manual_obstacles_backup)
        
        # Regenerar comida (evitando superposición con TODOS los obstáculos)
        self._generate_food(self.food_count)  # Usar cantidad configurable
