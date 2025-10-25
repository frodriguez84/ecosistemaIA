"""
Mundo del ecosistema con obstáculos, comida y objetos.
"""

import random
import pygame
from .obstacles import Obstacle


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
        
        # Generar obstáculos automáticamente
        self._generate_obstacles()
        
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
        
        # Reinicializar sistema de árboles
        self._initialize_trees()
        
        # NO regenerar hacha - se mantiene entre generaciones
        # Solo resetear cooldown de corte
        self.last_tree_cut_tick = 0
        
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
        """Actualiza el estado de corte de árboles."""
        if self.axe_picked_up:
            # Contar manzanas no comidas
            available_food = len([f for f in self.food_items if not f['eaten']])
            
            # Activar/desactivar corte según umbral
            from config import SimulationConfig
            can_cut = available_food <= SimulationConfig.TREE_CUTTING_THRESHOLD
            
            for tree in self.trees:
                tree.can_be_cut = can_cut
                tree.obstacle.can_be_cut = can_cut  # Actualizar obstáculo también
                if not can_cut:
                    tree.hit_count = 0  # Resetear contador
                    tree.obstacle.collision_count = 0  # Resetear obstáculo también
    
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
