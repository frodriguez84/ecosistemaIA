"""
Mundo del ecosistema con obstáculos, comida y objetos.
"""

import random
import pygame
from .obstacles import Obstacle, Key, Door, Chest


class Tree:
    """Árbol con sistema de corte."""
    
    def __init__(self, x, y, obstacle):
        self.x = x
        self.y = y
        self.obstacle = obstacle  # Referencia al obstáculo original
        self.hit_count = 0
        self.can_be_cut = False
        self.is_cut = False
        self.cut_sprite = "036"  # Sprite del tronco cortado
    
    def hit(self):
        """Registra un golpe al árbol."""
        if self.can_be_cut and not self.is_cut:
            self.hit_count += 1
            return self.hit_count
    
    def should_be_cut(self):
        """Verifica si el árbol debe ser cortado."""
        return self.hit_count >= 3  # TREE_HITS_TO_CUT
    
    def cut(self):
        """Corta el árbol."""
        self.is_cut = True
        self.obstacle.is_cut = True  # Marcar obstáculo como cortado


class World:
    """Mundo del ecosistema con obstáculos."""
    
    def __init__(self, screen_width, screen_height, food_count=40):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.food_count = food_count  # Cantidad de comida configurable
        self.food_items = []
        self.obstacles = []
        self.manual_obstacles = []  # Obstáculos creados manualmente
        self.trees = []  # Lista de árboles para corte
        self.axe = None  # Hacha del sistema
        self.axe_picked_up = False  # Si alguien agarró el hacha
        self.last_tree_cut_tick = 0  # Último tick que se cortó un árbol
        self.tick = 0
        
        # Sistema de fortalezas
        self.red_key = None
        self.gold_key = None
        self.red_key_collected = False
        self.gold_key_collected = False
        self.door = None
        self.door_iron = None
        self.chest = None
        self.small_fortress_pos = None
        self.large_fortress_pos = None
        
        # Generar obstáculos automáticamente
        self._generate_obstacles()
        
        # Generar fortalezas (desde gen 1)
        self._generate_fortresses()
        
        # Limpiar obstáculos dentro de las fortalezas
        self._clean_fortresses()
        
        # Limpiar obstáculos frente a las puertas
        self._clear_area_around_doors()
        
        # Inicializar sistema de árboles
        self._initialize_trees()
        
        # Generar comida inicial (solo una vez por generación)
        self._generate_food(self.food_count)  # Usar cantidad configurable
        
        # Generar hacha al inicio
        self._generate_axe()
    
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
            
            # Verificar que no esté dentro de fortalezas
            if self._is_inside_fortress(food_x, food_y):
                attempts += 1
                continue
            
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
                
                # Verificar que no esté dentro de fortalezas
                if self._is_inside_fortress(x, y):
                    attempts += 1
                    continue
                
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
                        # Verificar que no esté dentro de fortalezas
                        if self._is_inside_fortress(x, y):
                            attempts += 1
                            continue
                        
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
                        # Verificar que no esté dentro de fortalezas
                        if self._is_inside_fortress(x, y):
                            attempts += 1
                            continue
                        
                        # Verificar que no se superponga
                        if not self._check_collision_with_objects(x, y, 25, self.obstacles):
                            self.obstacles.append(Obstacle(x, y, 20, 20, "water"))
                            placed = True
                    
                    attempts += 1
    
    def _generate_connected_walls(self):
        """Genera paredes conectadas (líneas, L, cuadrado 2x2) evitando fortalezas."""
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
                        # Verificar que no esté dentro de fortalezas
                        if not self._is_inside_fortress(x, y):
                            self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
            else:
                # Línea vertical
                for i in range(random.randint(3, 6)):
                    x = start_x
                    y = start_y + i * 20
                    if y < self.screen_height - 20:
                        # Verificar que no esté dentro de fortalezas
                        if not self._is_inside_fortress(x, y):
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
                    # Verificar que no esté dentro de fortalezas
                    if not self._is_inside_fortress(x, y):
                        self.obstacles.append(Obstacle(x, y, 20, 20, "wall"))
            
            for i in range(2):
                x = start_x
                y = start_y + (i + 1) * 20
                if y < self.screen_height - 20:
                    # Verificar que no esté dentro de fortalezas
                    if not self._is_inside_fortress(x, y):
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
                        # Verificar que no esté dentro de fortalezas
                        if not self._is_inside_fortress(x, y):
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
        
        # Guardar posiciones de fortalezas antes de regenerar
        small_pos = self.small_fortress_pos
        large_pos = self.large_fortress_pos
        
        # Regenerar obstáculos automáticos (incluyendo muros normales, SIN muros de fortalezas)
        self._generate_obstacles_with_manual(manual_obstacles_backup)
        
        # Restaurar posiciones de fortalezas
        self.small_fortress_pos = small_pos
        self.large_fortress_pos = large_pos
        
        # Regenerar muros de fortalezas
        if small_pos and large_pos:
            from config import SimulationConfig
            tile_size = SimulationConfig.TILE_SIZE
            
            # Definir posiciones de puertas ANTES de generar muros
            door_x = small_pos['x'] + 40  # col 3 (tercera columna) - nueva posición
            door_y = small_pos['y'] + 80  # fila 4 (cuarta fila, que es la pared sur) - nueva posición
            door_iron_x = large_pos['x'] + 40  # col 3 (tercera columna)
            door_iron_y = large_pos['y']  # fila 1 (primera fila, que es la pared norte)
            
            self._generate_fortress_walls(small_pos['x'], small_pos['y'], small_pos['size'], tile_size, door_x, door_y)
            self._generate_fortress_walls(large_pos['x'], large_pos['y'], large_pos['size'], tile_size, door_iron_x, door_iron_y)
        
        # Limpiar obstáculos dentro de las fortalezas SOLO si se completó el puzzle
        if self.gold_key_collected:
            # Solo limpiar fortaleza pequeña si se completó el puzzle
            self._clean_small_fortress()
        else:
            # Limpiar ambas fortalezas si no se completó el puzzle
            self._clean_fortresses()
        
        # Limpiar obstáculos frente a las puertas
        self._clear_area_around_doors()
        
        # Reinicializar sistema de árboles
        self._initialize_trees()
        
        # NO regenerar hacha - se mantiene entre generaciones
        # Solo resetear cooldown de corte
        self.last_tree_cut_tick = 0
        
        # NO resetear llaves si ya se recogieron (persistencia entre generaciones)
        # Solo resetear si no se han recogido
        if not self.red_key_collected:
            self.red_key = None
        if not self.gold_key_collected:
            self.gold_key = None
            self.gold_key_collected = False
        else:
            # Mantener gold_key_collected = True
            pass
        
        # Regenerar gold_key si no se ha recogido (con nueva posición - movida 2 tiles a la derecha)
        if not self.gold_key_collected and small_pos:
            gold_key_x = small_pos['x'] + 60  # col 4 (cuarta columna) - movida 2 tiles a la derecha
            gold_key_y = small_pos['y'] + 40  # fila 3 (tercera fila)
            self.gold_key = Key(gold_key_x, gold_key_y, "gold_key")
        
        # Resetear puertas SOLO si no se han abierto antes (persistencia del puzzle)
        if self.door and not self.door.is_open:
            # Solo resetear si la puerta nunca se abrió
            self.door.hit_count = 0
        if self.door_iron and not self.door_iron.is_open:
            # Solo resetear si la puerta nunca se abrió
            self.door_iron.hit_count = 0
        
        # Resetear cofre
        if self.chest:
            self.chest.is_open = False
        
        # Regenerar comida (evitando superposición con TODOS los obstáculos)
        self._generate_food(self.food_count)  # Usar cantidad configurable
    
    def _initialize_trees(self):
        """Inicializa el sistema de árboles."""
        self.trees = []
        for obstacle in self.obstacles:
            if obstacle.type == "tree":
                tree = Tree(obstacle.x, obstacle.y, obstacle)
                self.trees.append(tree)
    
    def _generate_axe(self):
        """Genera el hacha en una posición segura."""
        max_attempts = 1000
        for _ in range(max_attempts):
            x = random.randint(50, self.screen_width - 50)
            y = random.randint(50, self.screen_height - 50)
            
            # Verificar que no esté en obstáculos
            safe_position = True
            for obstacle in self.obstacles:
                if obstacle.collides_with(x, y, 30):
                    safe_position = False
                    break
            
            # Verificar que tenga espacio libre alrededor
            if safe_position:
                free_space = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        test_x = x + dx * 30
                        test_y = y + dy * 30
                        if (0 <= test_x < self.screen_width and 
                            0 <= test_y < self.screen_height):
                            # Verificar que no esté en obstáculo
                            obstacle_free = True
                            for obstacle in self.obstacles:
                                if obstacle.collides_with(test_x, test_y, 20):
                                    obstacle_free = False
                                    break
                            if obstacle_free:
                                free_space += 1
                
                if free_space >= 4:  # Al menos 4 direcciones libres
                    self.axe = {'x': x, 'y': y, 'picked_up': False}
                    return
        
        # Fallback: posición segura conocida
        self.axe = {'x': 100, 'y': 100, 'picked_up': False}
    
    def _generate_fortresses(self):
        """Genera las dos fortalezas con muros, puertas y contenido."""
        from config import SimulationConfig
        
        tile_size = SimulationConfig.TILE_SIZE
        small_size = SimulationConfig.SMALL_FORTRESS_SIZE
        large_size = SimulationConfig.LARGE_FORTRESS_SIZE
        
        # Fortaleza pequeña: esquina superior izquierda
        small_x = 50
        small_y = 50
        self.small_fortress_pos = {
            'x': small_x,
            'y': small_y,
            'size': small_size
        }
        
        # Fortaleza grande: esquina inferior derecha
        large_x = self.screen_width - (large_size * tile_size) - 50
        large_y = self.screen_height - (large_size * tile_size) - 50
        self.large_fortress_pos = {
            'x': large_x,
            'y': large_y,
            'size': large_size
        }
        
        # Definir posiciones de puertas ANTES de generar muros
        # Puerta pequeña (fila 4, col 3 de la fortaleza 4x5) - nueva posición
        door_x = small_x + 40  # col 3 (tercera columna)
        door_y = small_y + 80  # fila 4 (cuarta fila, que es la pared sur)
        
        # Puerta grande (fila 1, col 3 de la fortaleza 6x6)
        door_iron_x = large_x + 40  # col 3 (tercera columna)
        door_iron_y = large_y  # fila 1 (primera fila, que es la pared norte)
        
        
        # Generar muros de ambas fortalezas (evitando posiciones de puertas)
        self._generate_fortress_walls(small_x, small_y, small_size, tile_size, door_x, door_y)
        self._generate_fortress_walls(large_x, large_y, large_size, tile_size, door_iron_x, door_iron_y)
        
        # Crear objetos de puertas
        self.door = Door(door_x, door_y, "door")
        self.door_iron = Door(door_iron_x, door_iron_y, "door_iron")
        
        # Gold key en posición (4, 3) de la fortaleza pequeña 4x5 - movida 2 tiles a la derecha
        gold_key_x = small_x + 60  # col 4 (cuarta columna) - movida 2 tiles a la derecha
        gold_key_y = small_y + 40  # fila 3 (tercera fila)
        self.gold_key = Key(gold_key_x, gold_key_y, "gold_key")
        
        # Chest en el centro de la fortaleza grande
        chest_x = large_x + (large_size * 20) // 2  # Centro horizontal
        chest_y = large_y + (large_size * 20) // 2  # Centro vertical
        self.chest = Chest(chest_x, chest_y)
    
    def _generate_fortress_walls(self, start_x, start_y, size, tile_size, door_x=None, door_y=None):
        """Genera los muros de una fortaleza, evitando la posición de la puerta."""
        walls_generated = 0
        
        # Paredes norte y sur
        for i in range(size):
            # Pared norte
            wall_x = start_x + i * 20
            wall_y = start_y
            
            # Verificar si esta posición coincide con la puerta (más preciso)
            if door_x is not None and door_y is not None:
                if wall_x == door_x and wall_y == door_y:
                    pass  # Saltar esta posición (donde va la puerta)
                else:
                    self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
                    walls_generated += 1
            else:
                self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
                walls_generated += 1
            
            # Pared sur
            wall_x = start_x + i * 20
            wall_y = start_y + (size - 1) * 20
            
            # Verificar si esta posición coincide con la puerta (más preciso)
            if door_x is not None and door_y is not None:
                if wall_x == door_x and wall_y == door_y:
                    pass  # Saltar esta posición (donde va la puerta)
                else:
                    self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
                    walls_generated += 1
            else:
                self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
                walls_generated += 1
        
        # Paredes este y oeste
        for i in range(1, size - 1):  # Volver a evitar esquinas duplicadas
            # Pared oeste
            wall_x = start_x
            wall_y = start_y + i * 20
            
            # Verificar si esta posición coincide con la puerta (más preciso)
            if door_x is not None and door_y is not None:
                if wall_x == door_x and wall_y == door_y:
                    print(f"🚪 Saltando muro oeste en ({wall_x}, {wall_y}) - posición de puerta")
                    continue  # Saltar esta posición (donde va la puerta)
            
            self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
            walls_generated += 1
            
            # Pared este
            wall_x = start_x + (size - 1) * 20
            wall_y = start_y + i * 20
            
            # Verificar si esta posición coincide con la puerta (más preciso)
            if door_x is not None and door_y is not None:
                if wall_x == door_x and wall_y == door_y:
                    print(f"🚪 Saltando muro este en ({wall_x}, {wall_y}) - posición de puerta")
                    continue  # Saltar esta posición (donde va la puerta)
            
            self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
            walls_generated += 1
        
    
    def _is_inside_fortress(self, x, y):
        """Verifica si una posición está dentro de alguna fortaleza."""
        # Usar 20px en lugar de tile_size para consistencia con los muros
        
        # Verificar fortaleza pequeña
        if self.small_fortress_pos:
            small_x = self.small_fortress_pos['x']
            small_y = self.small_fortress_pos['y']
            small_size = self.small_fortress_pos['size']
            
            if (small_x <= x <= small_x + small_size * 20 and
                small_y <= y <= small_y + small_size * 20):
                return True
        
        # Verificar fortaleza grande
        if self.large_fortress_pos:
            large_x = self.large_fortress_pos['x']
            large_y = self.large_fortress_pos['y']
            large_size = self.large_fortress_pos['size']
            
            if (large_x <= x <= large_x + large_size * 20 and
                large_y <= y <= large_y + large_size * 20):
                return True
        
        return False
    
    def _clean_fortresses(self):
        """Elimina todos los obstáculos dentro de las fortalezas (excepto muros)."""
        obstacles_to_remove = []
        
        for obstacle in self.obstacles:
            # Verificar si el obstáculo está dentro de una fortaleza
            # Usar el centro del obstáculo para la verificación
            obstacle_center_x = obstacle.x + obstacle.width // 2
            obstacle_center_y = obstacle.y + obstacle.height // 2
            
            if self._is_inside_fortress(obstacle_center_x, obstacle_center_y):
                # NO eliminar muros (son parte de las fortalezas)
                if obstacle.type != "wall":
                    obstacles_to_remove.append(obstacle)
        
        # Eliminar obstáculos
        for obstacle in obstacles_to_remove:
            self.obstacles.remove(obstacle)
        
        print(f"🧹 Limpieza de fortalezas: {len(obstacles_to_remove)} obstáculos eliminados")
    
    def _clean_small_fortress(self):
        """Elimina todos los obstáculos dentro de la fortaleza pequeña (solo después de completar el puzzle)."""
        obstacles_to_remove = []
        
        for obstacle in self.obstacles:
            # Verificar si el obstáculo está dentro de la fortaleza pequeña
            obstacle_center_x = obstacle.x + obstacle.width // 2
            obstacle_center_y = obstacle.y + obstacle.height // 2
            
            if self._is_inside_small_fortress(obstacle_center_x, obstacle_center_y):
                # NO eliminar muros (son parte de las fortalezas)
                if obstacle.type != "wall":
                    obstacles_to_remove.append(obstacle)
        
        # Eliminar obstáculos
        for obstacle in obstacles_to_remove:
            if obstacle in self.obstacles:
                self.obstacles.remove(obstacle)
        
        if obstacles_to_remove:
            print(f"🧹 Limpieza de fortaleza pequeña: {len(obstacles_to_remove)} obstáculos eliminados")
    
    def _is_inside_small_fortress(self, x, y):
        """Verifica si un punto está dentro de la fortaleza pequeña."""
        if not hasattr(self, 'small_fortress_pos') or not self.small_fortress_pos:
            return False
        
        small_x = self.small_fortress_pos['x']
        small_y = self.small_fortress_pos['y']
        small_size = self.small_fortress_pos['size']
        
        return (small_x <= x <= small_x + small_size * 20 and 
                small_y <= y <= small_y + small_size * 20)
    
    def _clear_area_around_doors(self):
        """Elimina obstáculos en el área alrededor de las puertas."""
        from config import SimulationConfig
        tile_size = SimulationConfig.TILE_SIZE
        obstacles_to_remove = []
        
        # Área alrededor de la puerta pequeña (una tile al frente)
        if self.door:
            door_area = {
                'x': self.door.x - tile_size,
                'y': self.door.y - tile_size * 2,  # Frente de la puerta
                'width': tile_size * 3,
                'height': tile_size * 2
            }
            
            for obstacle in self.obstacles:
                if obstacle.type != "wall":  # No eliminar muros
                    obstacle_center_x = obstacle.x + obstacle.width // 2
                    obstacle_center_y = obstacle.y + obstacle.height // 2
                    
                    if (door_area['x'] <= obstacle_center_x <= door_area['x'] + door_area['width'] and
                        door_area['y'] <= obstacle_center_y <= door_area['y'] + door_area['height']):
                        obstacles_to_remove.append(obstacle)
        
        # Área alrededor de la puerta grande
        if self.door_iron:
            door_iron_area = {
                'x': self.door_iron.x - tile_size,
                'y': self.door_iron.y - tile_size * 2,  # Frente de la puerta
                'width': tile_size * 3,
                'height': tile_size * 2
            }
            
            for obstacle in self.obstacles:
                if obstacle.type != "wall":  # No eliminar muros
                    obstacle_center_x = obstacle.x + obstacle.width // 2
                    obstacle_center_y = obstacle.y + obstacle.height // 2
                    
                    if (door_iron_area['x'] <= obstacle_center_x <= door_iron_area['x'] + door_iron_area['width'] and
                        door_iron_area['y'] <= obstacle_center_y <= door_iron_area['y'] + door_iron_area['height']):
                        obstacles_to_remove.append(obstacle)
        
        # Eliminar obstáculos duplicados
        obstacles_to_remove = list(set(obstacles_to_remove))
        
        # Eliminar obstáculos
        for obstacle in obstacles_to_remove:
            if obstacle in self.obstacles:
                self.obstacles.remove(obstacle)
        
        if obstacles_to_remove:
            print(f"🚪 Limpieza alrededor de puertas: {len(obstacles_to_remove)} obstáculos eliminados")
    
    def check_axe_pickup(self, agent_x, agent_y):
        """Verifica si un agente agarró el hacha."""
        if self.axe and not self.axe['picked_up']:
            distance = ((agent_x - self.axe['x'])**2 + (agent_y - self.axe['y'])**2)**0.5
            if distance < 30:  # Rango para agarrar hacha
                self.axe['picked_up'] = True
                self.axe_picked_up = True
                return True
        return False
    
    def update_tree_cutting_status(self):
        """Actualiza el estado de corte de árboles y huts."""
        if self.axe_picked_up:
            # Contar manzanas no comidas
            available_food = len([f for f in self.food_items if not f['eaten']])
            
            # Activar/desactivar corte según umbral
            from config import SimulationConfig
            can_cut_trees = available_food <= SimulationConfig.TREE_CUTTING_THRESHOLD
            can_cut_huts = SimulationConfig.HUT_CUTTING_ENABLED and available_food <= SimulationConfig.HUT_CUTTING_THRESHOLD
            
            # Actualizar árboles
            for tree in self.trees:
                tree.can_be_cut = can_cut_trees
                tree.obstacle.can_be_cut = can_cut_trees  # Actualizar obstáculo también
                # NO resetear contador cuando se desactiva - mantener estado
                # if not can_cut_trees:
                #     tree.hit_count = 0  # Resetear contador
                #     tree.obstacle.collision_count = 0  # Resetear obstáculo también
            
            # Actualizar huts
            for obstacle in self.obstacles:
                if obstacle.type == "hut" and not obstacle.is_cut:
                    obstacle.can_be_cut = can_cut_huts
                    # NO resetear contador cuando se desactiva - mantener estado
                    # if not can_cut_huts:
                    #     obstacle.collision_count = 0  # Resetear contador
    
    def process_hut_hit(self, agent_x, agent_y, current_tick):
        """Procesa un golpe a un hut."""
        from config import SimulationConfig
        
        if not SimulationConfig.HUT_CUTTING_ENABLED:
            return False
            
        if not self.axe_picked_up:
            return False
        
        # Cooldown global de 30 ticks entre golpes
        if current_tick - self.last_tree_cut_tick < 30:
            return False
        
        for obstacle in self.obstacles:
            if obstacle.type == "hut" and not obstacle.is_cut and obstacle.can_be_cut:
                distance = ((agent_x - (obstacle.x + obstacle.width // 2))**2 + 
                           (agent_y - (obstacle.y + obstacle.height // 2))**2)**0.5
                if distance < 25:  # Rango para golpear hut
                    # Verificar cooldown del hut específico
                    if not hasattr(obstacle, 'last_hit_tick'):
                        obstacle.last_hit_tick = 0
                    
                    if current_tick - obstacle.last_hit_tick >= 120:  # 120 ticks entre golpes al mismo hut
                        hits = obstacle.hit()
                        obstacle.last_hit_tick = current_tick
                        
                        if hits:
                            # Hut destruido - generar manzanas
                            self._generate_food_from_hut_destruction()
                            # Registrar tick del golpe
                            self.last_tree_cut_tick = current_tick
                            return True
        return False
    
    def _generate_food_from_hut_destruction(self):
        """Genera manzanas al destruir un hut."""
        from config import SimulationConfig
        
        count = SimulationConfig.HUT_CUT_FOOD_REWARD  # Usar config
        attempts = 0
        max_attempts = count * 50
        
        # Generar exactamente 'count' manzanas
        generated = 0
        while generated < count and attempts < max_attempts:
            food_x = random.randint(20, self.screen_width - 20)
            food_y = random.randint(20, self.screen_height - 20)
            
            # Verificar que no esté dentro de fortalezas
            if self._is_inside_fortress(food_x, food_y):
                attempts += 1
                continue
            
            # Verificar que no esté en obstáculos
            valid_position = True
            for obstacle in self.obstacles:
                if obstacle.collides_with(food_x, food_y, 20):
                    valid_position = False
                    break
            
            # Verificar que no esté en comida existente
            if valid_position:
                if not self._check_collision_with_objects(food_x, food_y, 25, self.food_items):
                    food = {
                        'x': food_x,
                        'y': food_y,
                        'eaten': False,
                        'type': 'apple'
                    }
                    self.food_items.append(food)
                    generated += 1
            
            attempts += 1

    def process_tree_hit(self, agent_x, agent_y, current_tick):
        """Procesa un golpe a un árbol."""
        if not self.axe_picked_up:
            return False
        
        # Cooldown global de 30 ticks entre cortes para ver mejor el proceso
        if current_tick - self.last_tree_cut_tick < 30:
            return False
        
        for tree in self.trees:
            if tree.can_be_cut and not tree.is_cut:
                distance = ((agent_x - tree.x)**2 + (agent_y - tree.y)**2)**0.5
                if distance < 25:  # Rango para golpear árbol
                    # Verificar cooldown del árbol específico
                    if not hasattr(tree, 'last_hit_tick'):
                        tree.last_hit_tick = 0
                    
                    if current_tick - tree.last_hit_tick >= 120:  # 120 ticks entre golpes al mismo árbol
                        hits = tree.hit()
                        tree.last_hit_tick = current_tick  # Actualizar cooldown del árbol
                        
                        if hits and tree.should_be_cut():
                            # Cortar árbol
                            tree.cut()
                            # Generar manzanas
                            self._generate_food_from_tree_cut()
                            # Registrar tick del corte
                            self.last_tree_cut_tick = current_tick
                            return True
        return False
    
    def _generate_food_from_tree_cut(self):
        """Genera manzanas al cortar un árbol."""
        from config import SimulationConfig
        count = SimulationConfig.TREE_CUT_FOOD_REWARD
        attempts = 0
        max_attempts = count * 50
        
        # Generar exactamente 'count' manzanas
        generated = 0
        while generated < count and attempts < max_attempts:
            food_x = random.randint(20, self.screen_width - 20)
            food_y = random.randint(20, self.screen_height - 20)
            
            # Verificar que no esté dentro de fortalezas
            if self._is_inside_fortress(food_x, food_y):
                attempts += 1
                continue
            
            # Verificar que no esté en obstáculos
            valid_position = True
            for obstacle in self.obstacles:
                if obstacle.collides_with(food_x, food_y, 20):
                    valid_position = False
                    break
            
            # Verificar que no esté en comida existente
            if valid_position:
                if not self._check_collision_with_objects(food_x, food_y, 25, self.food_items):
                    food = {
                        'x': food_x,
                        'y': food_y,
                        'eaten': False,
                        'type': 'apple'
                    }
                    self.food_items.append(food)
                    generated += 1  # Incrementar contador de generadas
            
            attempts += 1
    
    def check_key_pickup(self, agent_x, agent_y, generation):
        """Verifica si un agente recogió una llave."""
        from config import SimulationConfig
        
        # Verificar red_key (desde gen 11)
        if not self.red_key_collected and generation >= SimulationConfig.RED_KEY_SPAWN_GEN:
            if self.red_key and not self.red_key.collected:
                if self.red_key.collides_with(agent_x, agent_y, 8):
                    if self.red_key.collect(None):
                        self.red_key_collected = True
                        return "red_key"
        
        # Verificar gold_key SOLO si la puerta de madera está abierta
        if not self.gold_key_collected and self.gold_key and not self.gold_key.collected:
            # Verificar que la puerta de madera esté abierta
            if self.door and self.door.is_open:
                if self.gold_key.collides_with(agent_x, agent_y, 8):
                    if self.gold_key.collect(None):
                        self.gold_key_collected = True
                        return "gold_key"
        
        return None
    
    def process_door_hit(self, agent_x, agent_y, current_tick):
        """Procesa un golpe a una puerta."""
        from config import SimulationConfig
        
        # Verificar si el agente tiene la llave requerida
        red_key_available = self.red_key_collected  # ✅ CORRECTO
        gold_key_available = self.gold_key_collected  # ✅ CORRECTO
        
        # Golpear door
        if self.door and not self.door.is_open:
            if red_key_available:  # ✅ CORRECTO - Agente tiene red_key
                distance = ((agent_x - (self.door.x + self.door.width // 2))**2 + 
                           (agent_y - (self.door.y + self.door.height // 2))**2)**0.5
                if distance < 25:
                    if self.door.hit(current_tick, SimulationConfig.DOOR_HIT_COOLDOWN):
                        return "door"
        
        # Golpear door_iron
        if self.door_iron and not self.door_iron.is_open:
            if gold_key_available:  # ✅ CORRECTO - Agente tiene gold_key
                distance = ((agent_x - (self.door_iron.x + self.door_iron.width // 2))**2 + 
                           (agent_y - (self.door_iron.y + self.door_iron.height // 2))**2)**0.5
                if distance < 25:
                    if self.door_iron.hit(current_tick, SimulationConfig.DOOR_HIT_COOLDOWN):
                        return "door_iron"
        
        return None
    
    def check_chest_open(self, agent_x, agent_y):
        """Verifica si un agente abrió el cofre."""
        if self.chest and not self.chest.is_open:
            if self.chest.collides_with(agent_x, agent_y, 8):
                if self.chest.open(None):
                    return True
        return False
    
    def _generate_red_key(self, generation):
        """Genera la red_key en el mapa libremente (desde gen 11)."""
        from config import SimulationConfig
        
        if generation >= SimulationConfig.RED_KEY_SPAWN_GEN and not self.red_key_collected:
            if not self.red_key:
                # Generar posición aleatoria fuera de fortalezas
                max_attempts = 1000
                for _ in range(max_attempts):
                    x = random.randint(50, self.screen_width - 50)
                    y = random.randint(50, self.screen_height - 50)
                    
                    # Verificar que no esté dentro de fortalezas
                    if not self._is_inside_fortress(x, y):
                        # Verificar que no esté en obstáculos
                        safe_position = True
                        for obstacle in self.obstacles:
                            if obstacle.collides_with(x, y, 30):
                                safe_position = False
                                break
                        
                        if safe_position:
                            self.red_key = Key(x, y, "red_key")
                            return
