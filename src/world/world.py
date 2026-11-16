"""
Mundo del ecosistema con obstáculos, comida y objetos.
"""

import random
from .obstacles import Obstacle, Key, Door, Chest, PerimeterObstacle, PondObstacle

# Fortalezas móviles (FORTALEZAS_MOVILES): a cuánto del borde del mapa queda cada fortaleza con el
# frente de su puerta (lo que tienen en la generación 1), a cuánto una de otra, y cuántos sorteos
MARGEN_FORTALEZAS = 50
SEPARACION_FORTALEZAS = 40
INTENTOS_FORTALEZAS = 1000


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
        self.perimeter_obstacles = []  # Obstáculos del perímetro decorativo
        self.pond_obstacles = []  # Obstáculos del estanque móvil
        self.axe = None  # Hacha: queda en el mapa, cada agente agarra la suya (decisión 8)
        self.last_tree_cut_tick = 0  # Último tick que se cortó un árbol
        self.tick = 0
        
        # Sistema de fortalezas. El puzzle es de cada agente (decisión 7): el mundo solo tiene los
        # objetos, que quedan en el mapa
        self.red_key = None
        self.gold_key = None
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
        
        # Generar estanque móvil PRIMERO
        self._generate_mobile_pond()
        
        # Generar comida inicial DESPUÉS del estanque (evitando superposición)
        self._generate_food(self.food_count)  # Usar cantidad configurable
        
        # Generar hacha y llave roja al inicio, con el mapa listo (decisión 10)
        self._generate_axe()
        self._generate_red_key(1)
        
        # Generar perímetro decorativo
        self._generate_perimeter()
    
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
        
        # Verificar colisión con obstáculos del perímetro
        for perimeter_obj in self.perimeter_obstacles:
            if perimeter_obj.collides_with(x, y, radius, radius):
                return True
        
        # Verificar colisión con obstáculos del estanque
        for pond_obj in self.pond_obstacles:
            if pond_obj.collides_with(x, y, radius, radius):
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
            
            # Verificar que no esté en el estanque
            if valid_position:
                for pond_obj in self.pond_obstacles:
                    if pond_obj.collides_with(food_x, food_y, 20, 20):
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
    
    def reset_food(self, generacion):
        """Prepara el mundo de la generación `generacion`: regenera obstáculos y comida, preservando
        los objetos manuales, y reinicia el puzzle (decisión 10)."""
        self.food_items = []
        
        # Preservar objetos manuales
        manual_obstacles_backup = self.manual_obstacles.copy()
        
        # Fortalezas móviles: un lugar nuevo, antes del estanque y del resto del mapa, que las esquivan.
        # Apagado no consume azar
        from config import SimulationConfig
        if SimulationConfig.FORTALEZAS_MOVILES:
            self._sortear_fortalezas()
        
        # Guardar posiciones de fortalezas antes de regenerar
        small_pos = self.small_fortress_pos
        large_pos = self.large_fortress_pos
        
        # Generar estanque móvil PRIMERO (nueva posición cada generación)
        self._generate_mobile_pond()
        
        # Regenerar obstáculos automáticos (incluyendo muros normales, SIN muros de fortalezas)
        # AHORA verificará colisión con el estanque
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
            
            # Fortalezas móviles: las puertas, la llave dorada y el cofre van con su fortaleza, al lugar
            # que tienen en _generate_fortresses. Antes del despeje, que mira dónde están las puertas
            if SimulationConfig.FORTALEZAS_MOVILES:
                self.door.x, self.door.y = door_x, door_y
                self.door_iron.x, self.door_iron.y = door_iron_x, door_iron_y
                self.gold_key.x, self.gold_key.y = small_pos['x'] + 60, small_pos['y'] + 40
                self.chest.x = large_pos['x'] + (large_pos['size'] * 20) // 2
                self.chest.y = large_pos['y'] + (large_pos['size'] * 20) // 2
        
        # Limpiar obstáculos dentro de las fortalezas
        self._clean_fortresses()
        
        # Limpiar obstáculos frente a las puertas
        self._clear_area_around_doors()
        
        # Reinicializar sistema de árboles
        self._initialize_trees()
        
        # Generar perímetro decorativo
        self._generate_perimeter()
        
        # Resetear cooldown de corte
        self.last_tree_cut_tick = 0
        
        # El puzzle vuelve a empezar (decisión 10): nada pasa a la generación siguiente. Puertas y
        # cofre cerrados; la llave dorada queda en su lugar
        for door in (self.door, self.door_iron):
            if door:
                door.is_open = False
                door.hit_count = 0
        if self.chest:
            self.chest.is_open = False
            self.chest.opened_by = None
        
        # Regenerar comida (evitando superposición con TODOS los obstáculos)
        self._generate_food(self.food_count)  # Usar cantidad configurable

        # Hacha y llave roja en una posición nueva, con el mapa ya regenerado (decisión 10)
        self._generate_axe()
        self._generate_red_key(generacion)
    
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
                    self.axe = {'x': x, 'y': y}
                    return
        
        # Fallback: posición segura conocida
        self.axe = {'x': 100, 'y': 100}
    
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
    
    def _sortear_fortalezas(self):
        """Fortalezas móviles (FORTALEZAS_MOVILES): un lugar al azar para cada fortaleza. La zona de
        cada una son sus muros y el frente de su puerta que despeja _clear_area_around_doors (abajo de
        la chica, arriba de la grande). Los muros y el frente quedan a MARGEN_FORTALEZAS del borde, como
        en la generación 1: el perímetro no tapa la puerta. Las dos zonas quedan a SEPARACION_FORTALEZAS
        una de otra: el despeje borra muros y no puede tocar los de la otra, y entre las dos se pasa. Si
        no encuentra lugar, quedan donde estaban."""
        from config import SimulationConfig
        t = SimulationConfig.TILE_SIZE
        chica = SimulationConfig.SMALL_FORTRESS_SIZE * 20
        grande = SimulationConfig.LARGE_FORTRESS_SIZE * 20
        m, g = MARGEN_FORTALEZAS, SEPARACION_FORTALEZAS
        for _ in range(INTENTOS_FORTALEZAS):
            # Las puertas, como en _generate_fortresses: la de la chica en (x + 40, y + 80), despejada
            # hasta 3 tiles abajo; la de la grande en (x + 40, y), despejada hasta 3 tiles arriba. El
            # despeje va de 2 tiles a la izquierda de la puerta a 3 a la derecha
            sx = random.randint(m, self.screen_width - m - chica)
            sy = random.randint(m, self.screen_height - m - (80 + 3 * t))
            lx = random.randint(m, self.screen_width - m - grande)
            ly = random.randint(m + 3 * t, self.screen_height - m - grande)
            zona_chica = (min(sx, sx + 40 - 2 * t), sy, max(sx + chica, sx + 40 + 3 * t), sy + 80 + 3 * t)
            zona_grande = (min(lx, lx + 40 - 2 * t), ly - 3 * t, max(lx + grande, lx + 40 + 3 * t), ly + grande)
            if (zona_chica[2] + g <= zona_grande[0] or zona_grande[2] + g <= zona_chica[0]
                    or zona_chica[3] + g <= zona_grande[1] or zona_grande[3] + g <= zona_chica[1]):
                self.small_fortress_pos = {'x': sx, 'y': sy, 'size': SimulationConfig.SMALL_FORTRESS_SIZE}
                self.large_fortress_pos = {'x': lx, 'y': ly, 'size': SimulationConfig.LARGE_FORTRESS_SIZE}
                return
    
    def _generate_fortress_walls(self, start_x, start_y, size, tile_size, door_x=None, door_y=None):
        """Genera los muros de una fortaleza, evitando la posición de la puerta."""
        walls_generated = 0
        
        # Paredes norte y sur
        for i in range(size):
            # Pared norte
            wall_x = start_x + i * 20
            wall_y = start_y
            
            # Verificar si esta posición coincide con la puerta (usar tolerancia de 5px)
            skip_this_wall = False
            if door_x is not None and door_y is not None:
                if abs(wall_x - door_x) < 5 and abs(wall_y - door_y) < 5:
                    skip_this_wall = True  # Saltar solo este bloque (donde va la puerta)
            
            if not skip_this_wall:
                self.obstacles.append(Obstacle(wall_x, wall_y, 20, 20, "wall"))
                walls_generated += 1
            
            # Pared sur
            wall_x = start_x + i * 20
            wall_y = start_y + (size - 1) * 20
            
            # Verificar si esta posición coincide con la puerta (usar tolerancia de 5px)
            skip_this_wall = False
            if door_x is not None and door_y is not None:
                if abs(wall_x - door_x) < 5 and abs(wall_y - door_y) < 5:
                    skip_this_wall = True  # Saltar solo este bloque (donde va la puerta)
            
            if not skip_this_wall:
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
        
        # print(f"🧹 Limpieza de fortalezas: {len(obstacles_to_remove)} obstáculos eliminados")
    
    def _clear_area_around_doors(self):
        """Elimina obstáculos (INCLUYENDO WALLS) en el área alrededor de las puertas."""
        from config import SimulationConfig
        tile_size = SimulationConfig.TILE_SIZE
        obstacles_to_remove = []
        
        # Área alrededor de la puerta pequeña (puerta está en pared sur, espacio hacia abajo)
        if self.door:
            door_area = {
                'x': self.door.x - tile_size * 2,  # Más espacio horizontal
                'y': self.door.y + tile_size,  # DESDE ABAJO de la puerta (no incluir la fila de la puerta)
                'width': tile_size * 5,  # Área más amplia
                'height': tile_size * 2  # Espacio hacia abajo (reducido porque no incluimos la fila de la puerta)
            }
            
            for obstacle in self.obstacles:
                obstacle_center_x = obstacle.x + obstacle.width // 2
                obstacle_center_y = obstacle.y + obstacle.height // 2
                
                # NO eliminar muros que están en la MISMA fila que la puerta (son parte de la pared sur)
                if obstacle.type == "wall" and abs(obstacle_center_y - self.door.y) < 10:
                    continue  # Mantener muros en la misma fila que la puerta
                
                # Eliminar otros obstáculos en el área
                if (door_area['x'] <= obstacle_center_x <= door_area['x'] + door_area['width'] and
                    door_area['y'] <= obstacle_center_y <= door_area['y'] + door_area['height']):
                    obstacles_to_remove.append(obstacle)
        
        # Área alrededor de la puerta grande (puerta está en pared norte, espacio hacia arriba)
        if self.door_iron:
            door_iron_area = {
                'x': self.door_iron.x - tile_size * 2,  # Más espacio horizontal
                'y': self.door_iron.y - tile_size * 3,  # Frente de la puerta (hacia arriba)
                'width': tile_size * 5,  # Área más amplia
                'height': tile_size * 3  # Más espacio hacia arriba
            }
            
            for obstacle in self.obstacles:
                # AHORA SÍ eliminamos walls también
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
            pass  # print(f"🚪 Limpieza alrededor de puertas: {len(obstacles_to_remove)} obstáculos eliminados (incluye walls)")
    
    def check_axe_pickup(self, agent):
        """Verifica si el agente agarró el hacha. Es suya: el hacha queda en el mapa (decisión 8)."""
        if self.axe and not agent.tiene_hacha:
            distance = ((agent.x - self.axe['x'])**2 + (agent.y - self.axe['y'])**2)**0.5
            if distance < 30:  # Rango para agarrar hacha
                agent.tiene_hacha = True
                return True
        return False
    
    def update_tree_cutting_status(self):
        """Actualiza el estado de corte de árboles y huts. Ya no espera a que alguien tenga el hacha:
        cada golpe pide el hacha del agente que golpea (decisión 8)."""
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
            
    def process_hut_hit(self, agent, current_tick):
        """Procesa un golpe del agente a un hut: hace falta su propia hacha (decisión 8)."""
        from config import SimulationConfig
        
        if not SimulationConfig.HUT_CUTTING_ENABLED:
            return False
            
        if not agent.tiene_hacha:
            return False
        agent_x, agent_y = agent.x, agent.y
        
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

    def process_tree_hit(self, agent, current_tick):
        """Procesa un golpe del agente a un árbol: hace falta su propia hacha (decisión 8)."""
        if not agent.tiene_hacha:
            return False
        agent_x, agent_y = agent.x, agent.y
        
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
            
            # Verificar que no esté en el estanque
            if valid_position:
                for pond_obj in self.pond_obstacles:
                    if pond_obj.collides_with(food_x, food_y, 20, 20):
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
    
    def check_key_pickup(self, agent):
        """Verifica si el agente recogió la llave que le toca, por contacto (decisión 8): la roja con
        etapa 0 y la dorada con etapa 2. Las dos quedan en el mapa para los demás."""
        # Radio aumentado: agente (8) + margen generoso (12) = 20 px total
        if agent.etapa == 0 and self.red_key:
            if self.red_key.collides_with(agent.x, agent.y, 12):  # Aumentado de 8 a 12
                agent.etapa = 1
                return "red_key"
        
        # La dorada está adentro de la fortaleza chica: con etapa 2, el agente ya abrió su puerta
        if agent.etapa == 2 and self.gold_key:
            if self.gold_key.collides_with(agent.x, agent.y, 12):  # Aumentado de 8 a 12
                agent.etapa = 3
                return "gold_key"
        
        return None
    
    def process_door_hit(self, agent, current_tick):
        """Procesa un golpe del agente a la puerta que le toca (decisión 8): la de madera con etapa 1
        (tiene la llave roja), la de hierro con etapa 3 (tiene la dorada). Los golpes son del agente,
        y la puerta se abre para él."""
        from config import SimulationConfig
        
        # Golpear door
        if self.door and agent.etapa == 1:
            distance = ((agent.x - (self.door.x + self.door.width // 2))**2 +
                       (agent.y - (self.door.y + self.door.height // 2))**2)**0.5
            if distance < 25:
                if self.door.hit(agent, current_tick, SimulationConfig.DOOR_HIT_COOLDOWN):
                    agent.etapa = 2
                    return "door"
        
        # Golpear door_iron
        if self.door_iron and agent.etapa == 3:
            distance = ((agent.x - (self.door_iron.x + self.door_iron.width // 2))**2 +
                       (agent.y - (self.door_iron.y + self.door_iron.height // 2))**2)**0.5
            if distance < 25:
                if self.door_iron.hit(agent, current_tick, SimulationConfig.DOOR_HIT_COOLDOWN):
                    agent.etapa = 4
                    return "door_iron"
        
        return None
    
    def check_chest_open(self, agent):
        """Verifica si el agente abrió el cofre (decisión 8): con etapa 4 y en contacto. El que golpea
        lo mira el agente. is_open queda para el dibujo."""
        if self.chest and agent.etapa == 4:
            if self.chest.collides_with(agent.x, agent.y, 8):
                agent.etapa = 5
                self.chest.open(agent)  # para el dibujo; recuerda al primero que lo abrió
                return True
        return False
    
    def _generate_red_key(self, generation):
        """Sortea la posición de la llave roja, fuera de las fortalezas y de los obstáculos: una nueva
        en cada generación (decisión 10). Sin fortalezas, o antes de RED_KEY_SPAWN_GEN, no hay llave."""
        from config import SimulationConfig
        
        self.red_key = None
        if not SimulationConfig.FORTRESSES_ENABLED or generation < SimulationConfig.RED_KEY_SPAWN_GEN:
            return
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
    
    def _generate_perimeter(self):
        """Genera el perímetro decorativo del mapa."""
        tile_size = 20
        map_width = self.screen_width
        map_height = self.screen_height
        
        # Calcular dimensiones en tiles
        tiles_x = map_width // tile_size
        tiles_y = map_height // tile_size
        
        # Limpiar perímetro anterior
        self.perimeter_obstacles.clear()
        
        # Generar perímetro según el diagrama:
        # 028,026,026,026,026,026,029
        # 024                                  023
        # 024                                  023
        # 024                                   023
        # 024                                  023
        # 024                                  023
        # 030,021,021,021,021,021,031
        
        # Lado superior (026)
        for x in range(1, tiles_x - 1):
            self.perimeter_obstacles.append(
                PerimeterObstacle(x * tile_size, 0, '026')
            )
        
        # Lado inferior (021)
        for x in range(1, tiles_x - 1):
            self.perimeter_obstacles.append(
                PerimeterObstacle(x * tile_size, (tiles_y - 1) * tile_size, '021')
            )
        
        # Lado izquierdo (024)
        for y in range(1, tiles_y - 1):
            self.perimeter_obstacles.append(
                PerimeterObstacle(0, y * tile_size, '024')
            )
        
        # Lado derecho (023)
        for y in range(1, tiles_y - 1):
            self.perimeter_obstacles.append(
                PerimeterObstacle((tiles_x - 1) * tile_size, y * tile_size, '023')
            )
        
        # Esquinas
        self.perimeter_obstacles.append(PerimeterObstacle(0, 0, '028'))  # Superior izquierda
        self.perimeter_obstacles.append(PerimeterObstacle((tiles_x - 1) * tile_size, 0, '029'))  # Superior derecha
        self.perimeter_obstacles.append(PerimeterObstacle(0, (tiles_y - 1) * tile_size, '030'))  # Inferior izquierda
        self.perimeter_obstacles.append(PerimeterObstacle((tiles_x - 1) * tile_size, (tiles_y - 1) * tile_size, '031'))  # Inferior derecha
        
        
    
    def _generate_mobile_pond(self):
        """Genera dos estanques móviles (3x3 y 4x4) en posiciones aleatorias válidas."""
        tile_size = 20
        
        # Limpiar estanques anteriores
        self.pond_obstacles.clear()
        
        # Generar estanque 3x3
        self._generate_pond_3x3(tile_size)
        
        # Generar estanque 4x4
        self._generate_pond_4x4(tile_size)
    
    def _generate_pond_3x3(self, tile_size):
        """Genera estanque 3x3 con agua animada."""
        pond_size = 3
        
        # Área válida para el estanque
        min_x = 60
        max_x = 900 - (pond_size * tile_size)
        min_y = 60
        max_y = 740 - (pond_size * tile_size)
        
        # Intentar encontrar posición válida
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            pond_x = random.randint(min_x, max_x)
            pond_y = random.randint(min_y, max_y)
            
            if self._is_pond_position_valid(pond_x, pond_y, pond_size, tile_size):
                # Generar estanque 3x3 con agua animada:
                # 020,021,022
                # 023,019/018,024
                # 025,026,027
                
                # Fila superior
                self.pond_obstacles.append(PondObstacle(pond_x, pond_y, '020'))
                self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y, '021'))
                self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y, '022'))
                
                # Fila media
                self.pond_obstacles.append(PondObstacle(pond_x, pond_y + tile_size, '023'))
                # Agua central animada (alterna entre 019 y 018)
                water_sprite = '019' if random.random() < 0.5 else '018'
                self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + tile_size, water_sprite))
                self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + tile_size, '024'))
                
                # Fila inferior
                self.pond_obstacles.append(PondObstacle(pond_x, pond_y + 2 * tile_size, '025'))
                self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + 2 * tile_size, '026'))
                self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + 2 * tile_size, '027'))
                
                
                return
            
            attempts += 1
        
        # Posición por defecto si no se encuentra válida
        pond_x, pond_y = 300, 200
        self.pond_obstacles.append(PondObstacle(pond_x, pond_y, '020'))
        self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y, '021'))
        self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y, '022'))
        self.pond_obstacles.append(PondObstacle(pond_x, pond_y + tile_size, '023'))
        self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + tile_size, '019'))
        self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + tile_size, '024'))
        self.pond_obstacles.append(PondObstacle(pond_x, pond_y + 2 * tile_size, '025'))
        self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + 2 * tile_size, '026'))
        self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + 2 * tile_size, '027'))
        
    
    def _generate_pond_4x4(self, tile_size):
        """Genera estanque 4x4 con agua animada."""
        pond_size = 4
        
        # Área válida para el estanque
        min_x = 60
        max_x = 900 - (pond_size * tile_size)
        min_y = 60
        max_y = 740 - (pond_size * tile_size)
        
        # Intentar encontrar posición válida
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            pond_x = random.randint(min_x, max_x)
            pond_y = random.randint(min_y, max_y)
            
            if self._is_pond_position_valid(pond_x, pond_y, pond_size, tile_size):
                # Generar estanque 4x4 con agua animada:
                # 020,021,021,022
                # 023,019/018,019/018,024
                # 023,019/018,019/018,024
                # 025,026,026,027
                
                # Fila superior
                self.pond_obstacles.append(PondObstacle(pond_x, pond_y, '020'))
                self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y, '021'))
                self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y, '021'))
                self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, pond_y, '022'))
                
                # Filas media (2 filas de agua)
                for row in range(2):
                    y_pos = pond_y + (row + 1) * tile_size
                    self.pond_obstacles.append(PondObstacle(pond_x, y_pos, '023'))
                    
                    # Agua animada (alterna entre 019 y 018)
                    for col in range(2):
                        x_pos = pond_x + (col + 1) * tile_size
                        water_sprite = '019' if random.random() < 0.5 else '018'
                        self.pond_obstacles.append(PondObstacle(x_pos, y_pos, water_sprite))
                    
                    self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, y_pos, '024'))
                
                # Fila inferior
                self.pond_obstacles.append(PondObstacle(pond_x, pond_y + 3 * tile_size, '025'))
                self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + 3 * tile_size, '026'))
                self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + 3 * tile_size, '026'))
                self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, pond_y + 3 * tile_size, '027'))
                
                
                return
            
            attempts += 1
        
        # Posición por defecto si no se encuentra válida
        pond_x, pond_y = 500, 400
        # Fila superior
        self.pond_obstacles.append(PondObstacle(pond_x, pond_y, '020'))
        self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y, '021'))
        self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y, '021'))
        self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, pond_y, '022'))
        
        # Filas media
        for row in range(2):
            y_pos = pond_y + (row + 1) * tile_size
            self.pond_obstacles.append(PondObstacle(pond_x, y_pos, '023'))
            self.pond_obstacles.append(PondObstacle(pond_x + tile_size, y_pos, '019'))
            self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, y_pos, '018'))
            self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, y_pos, '024'))
        
        # Fila inferior
        self.pond_obstacles.append(PondObstacle(pond_x, pond_y + 3 * tile_size, '025'))
        self.pond_obstacles.append(PondObstacle(pond_x + tile_size, pond_y + 3 * tile_size, '026'))
        self.pond_obstacles.append(PondObstacle(pond_x + 2 * tile_size, pond_y + 3 * tile_size, '026'))
        self.pond_obstacles.append(PondObstacle(pond_x + 3 * tile_size, pond_y + 3 * tile_size, '027'))
        
    
    def _is_pond_position_valid(self, pond_x, pond_y, pond_size, tile_size):
        """Verifica si la posición del estanque es válida (no bloquea fortalezas)."""
        # Verificar fortaleza pequeña
        if self.small_fortress_pos:
            fortress_x = self.small_fortress_pos['x']
            fortress_y = self.small_fortress_pos['y']
            fortress_size = self.small_fortress_pos['size']
            
            if (pond_x < fortress_x + fortress_size * tile_size + 40 and
                pond_x + pond_size * tile_size > fortress_x - 40 and
                pond_y < fortress_y + fortress_size * tile_size + 40 and
                pond_y + pond_size * tile_size > fortress_y - 40):
                return False
        
        # Verificar fortaleza grande
        if self.large_fortress_pos:
            fortress_x = self.large_fortress_pos['x']
            fortress_y = self.large_fortress_pos['y']
            fortress_size = self.large_fortress_pos['size']
            
            if (pond_x < fortress_x + fortress_size * tile_size + 40 and
                pond_x + pond_size * tile_size > fortress_x - 40 and
                pond_y < fortress_y + fortress_size * tile_size + 40 and
                pond_y + pond_size * tile_size > fortress_y - 40):
                return False
        
        # Verificar que no se superponga con otros estanques
        for existing_pond in self.pond_obstacles:
            if (pond_x < existing_pond.x + pond_size * tile_size and
                pond_x + pond_size * tile_size > existing_pond.x and
                pond_y < existing_pond.y + pond_size * tile_size and
                pond_y + pond_size * tile_size > existing_pond.y):
                return False
        
        return True
