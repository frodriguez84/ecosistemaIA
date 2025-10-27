"""
Agente avanzado con cerebro, sensores y actuadores.
"""

import numpy as np
import pygame
import random
import math
from config import SimulationConfig


class AdvancedAgent:
    """Agente avanzado con cerebro, sensores y actuadores."""
    
    def __init__(self, x, y, brain=None):
        # Identificador único
        self.id = id(self)  # Usar el id del objeto Python como identificador único
        
        # Posición y movimiento
        self.x = float(x)
        self.y = float(y)
        self.angle = random.uniform(0, 2 * np.pi)
        self.speed = SimulationConfig.AGENT_SPEED  # Velocidad desde config
        self.radius = 8
        
        # Estado
        self.alive = True
        self.energy = 100.0
        self.max_energy = 100.0
        self.age = 0
        self.fitness = 0.0
        
        # Cerebro
        if brain:
            self.brain = brain
        else:
            self.brain = SimpleNeuralNetwork(
                SimulationConfig.INPUT_SIZE,
                SimulationConfig.HIDDEN_SIZE,
                SimulationConfig.OUTPUT_SIZE
            )
        
        # Sensores
        self.vision_range = 150
        self.vision_angle = np.pi / 3  # 60 grados
        
        # Actuadores
        self.moving = False
        self.eating = False
        
        # Estadísticas
        self.food_eaten = 0
        self.distance_traveled = 0.0
        self.obstacles_avoided = 0
        self.total_moves = 0
        self.movement_distance = 0.0
        self.total_food_attempts = 0
        self.food_found_count = 0
        self.obstacle_avoidance_count = 0
        self.total_obstacle_encounters = 0
        
        # Objetivo de comida
        self.target_food = None
        
        # Efectos visuales
        self.death_effect_frames = 0
        self.death_effect_max_frames = 10
        
        # Cooldown para golpear árboles
        self.last_tree_hit_tick = 0
        self.tree_hit_cooldown = 120  # 120 ticks entre golpes (2 segundos a 60 FPS)
    
    def perceive(self, world, other_agents):
        """Recopila información del entorno."""
        perceptions = []
        
        # 1. Energía normalizada
        perceptions.append(self.energy / self.max_energy)
        
        # 2. Distancia a la comida más cercana
        nearest_food = self._find_nearest_food(world)
        if nearest_food:
            nearest_food_dist = float(np.sqrt((float(self.x) - nearest_food[0])**2 + (float(self.y) - nearest_food[1])**2))
        else:
            nearest_food_dist = self.vision_range
        perceptions.append(min(nearest_food_dist / self.vision_range, 1.0))
        
        # 3. Dirección a la comida más cercana
        if nearest_food:
            dx = nearest_food[0] - float(self.x)
            dy = nearest_food[1] - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            # Normalizar ángulo
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)  # Normalizar a [-1, 1]
        else:
            perceptions.append(0.0)
        
        # 4. Distancia a otros agentes
        min_agent_dist = float('inf')
        for agent in other_agents:
            if agent != self and agent.alive:
                dist = float(np.sqrt((float(self.x) - float(agent.x))**2 + (float(self.y) - float(agent.y))**2))
                min_agent_dist = min(min_agent_dist, dist)
        perceptions.append(min(min_agent_dist / self.vision_range, 1.0) if min_agent_dist != float('inf') else 1.0)
        
        # 5. Distancia a obstáculos
        min_obstacle_dist = float('inf')
        for obstacle in world.obstacles:
            if obstacle.type in ["wall", "tree", "hut"]:
                dist = float(np.sqrt((float(self.x) - float(obstacle.x))**2 + (float(self.y) - float(obstacle.y))**2))
                min_obstacle_dist = min(min_obstacle_dist, dist)
        perceptions.append(min(min_obstacle_dist / self.vision_range, 1.0) if min_obstacle_dist != float('inf') else 1.0)
        
        # 6. Posición normalizada
        perceptions.append(self.x / world.screen_width)
        perceptions.append(self.y / world.screen_height)
        
        # 7. Ángulo normalizado
        perceptions.append(self.angle / (2 * np.pi))
        
        # 8-22. SENSORES DE FORTALEZAS/LLAVES/PUERTAS/COFRE/ÁRBOLES
        from config import SimulationConfig
        
        # 8-9. Distancia y dirección a red_key
        if world.red_key and not world.red_key.collected:
            red_key_dist = float(np.sqrt((float(self.x) - world.red_key.x)**2 + (float(self.y) - world.red_key.y)**2))
            perceptions.append(min(red_key_dist / self.vision_range, 1.0))
            
            dx = world.red_key.x - float(self.x)
            dy = world.red_key.y - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)
        else:
            perceptions.append(1.0)  # No visible (distancia máxima)
            perceptions.append(0.0)   # Sin dirección
        
        # 10-11. Distancia y dirección a gold_key
        if world.gold_key and not world.gold_key.collected:
            gold_key_dist = float(np.sqrt((float(self.x) - world.gold_key.x)**2 + (float(self.y) - world.gold_key.y)**2))
            perceptions.append(min(gold_key_dist / self.vision_range, 1.0))
            
            dx = world.gold_key.x - float(self.x)
            dy = world.gold_key.y - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)
        else:
            perceptions.append(1.0)  # No visible
            perceptions.append(0.0)   # Sin dirección
        
        # 12-13. Distancia y dirección a door
        if world.door and not world.door.is_open:
            door_dist = float(np.sqrt((float(self.x) - (world.door.x + world.door.width // 2))**2 + 
                                  (float(self.y) - (world.door.y + world.door.height // 2))**2))
            perceptions.append(min(door_dist / self.vision_range, 1.0))
            
            dx = (world.door.x + world.door.width // 2) - float(self.x)
            dy = (world.door.y + world.door.height // 2) - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)
        else:
            perceptions.append(1.0)  # No visible
            perceptions.append(0.0)   # Sin dirección
        
        # 14-15. Distancia y dirección a door_iron
        if world.door_iron and not world.door_iron.is_open:
            door_iron_dist = float(np.sqrt((float(self.x) - (world.door_iron.x + world.door_iron.width // 2))**2 + 
                                        (float(self.y) - (world.door_iron.y + world.door_iron.height // 2))**2))
            perceptions.append(min(door_iron_dist / self.vision_range, 1.0))
            
            dx = (world.door_iron.x + world.door_iron.width // 2) - float(self.x)
            dy = (world.door_iron.y + world.door_iron.height // 2) - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)
        else:
            perceptions.append(1.0)  # No visible
            perceptions.append(0.0)   # Sin dirección
        
        # 16-17. Distancia y dirección a chest
        if world.chest and not world.chest.is_open:
            chest_dist = float(np.sqrt((float(self.x) - (world.chest.x + world.chest.width // 2))**2 + 
                                  (float(self.y) - (world.chest.y + world.chest.height // 2))**2))
            perceptions.append(min(chest_dist / self.vision_range, 1.0))
            
            dx = (world.chest.x + world.chest.width // 2) - float(self.x)
            dy = (world.chest.y + world.chest.height // 2) - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            angle_diff = target_angle - self.angle
            while angle_diff > np.pi:
                angle_diff -= 2 * np.pi
            while angle_diff < -np.pi:
                angle_diff += 2 * np.pi
            perceptions.append(angle_diff / np.pi)
        else:
            perceptions.append(1.0)  # No visible
            perceptions.append(0.0)   # Sin dirección
        
        # 18. Estado: red_key recogida (0 o 1)
        perceptions.append(1.0 if (hasattr(world, 'red_key_collected') and world.red_key_collected) else 0.0)
        
        # 19. Estado: gold_key recogida (0 o 1)
        perceptions.append(1.0 if (hasattr(world, 'gold_key_collected') and world.gold_key_collected) else 0.0)
        
        # 20. Estado: puede cortar árboles (0 o 1)
        perceptions.append(1.0 if (hasattr(world, 'axe_picked_up') and world.axe_picked_up) else 0.0)
        
        # 21. Ratio de comida disponible (normalizado)
        from config import SimulationConfig
        available_food = len([f for f in world.food_items if not f['eaten']])
        food_ratio = available_food / SimulationConfig.FOOD_COUNT if SimulationConfig.FOOD_COUNT > 0 else 0.0
        perceptions.append(min(food_ratio, 1.0))
        
        # 22. Distancia al árbol más cercano cortable
        if hasattr(world, 'trees') and hasattr(world, 'axe_picked_up') and world.axe_picked_up:
            min_tree_dist = float('inf')
            for tree in world.trees:
                if tree.can_be_cut and not tree.is_cut:
                    tree_dist = float(np.sqrt((float(self.x) - tree.x)**2 + (float(self.y) - tree.y)**2))
                    min_tree_dist = min(min_tree_dist, tree_dist)
            perceptions.append(min(min_tree_dist / self.vision_range, 1.0) if min_tree_dist != float('inf') else 1.0)
        else:
            perceptions.append(1.0)  # No hay árboles cortables o no tiene hacha
        
        return np.array(perceptions, dtype=np.float32)
    
    def decide(self, world, other_agents, sprite_manager):
        """Toma decisiones basadas en percepciones."""
        perceptions = self.perceive(world, other_agents)
        decisions = self.brain.forward(perceptions)
        
        # Aplicar lógica adicional para comportamiento inteligente (sistema mejorado)
        if self.fitness > 30:  # Agentes con fitness medio-alto
            # Verificar si hay poca comida y puede cortar árboles
            food_ratio = perceptions[20] if len(perceptions) > 20 else 1.0
            has_axe = perceptions[19] if len(perceptions) > 19 else 0.0
            
            # Si hay poca comida (<40%) y tiene hacha, buscar árboles para cortar
            if food_ratio < 0.4 and has_axe > 0.5:
                nearest_tree = self._find_nearest_cuttable_tree(world)
                if nearest_tree:
                    target_angle = float(np.arctan2(nearest_tree[1] - float(self.y), nearest_tree[0] - float(self.x)))
                    angle_diff = target_angle - self.angle
                    
                    # Normalizar ángulo
                    while angle_diff > np.pi:
                        angle_diff -= 2 * np.pi
                    while angle_diff < -np.pi:
                        angle_diff += 2 * np.pi
                    
                    # Movimiento hacia árbol
                    if abs(angle_diff) < 0.3:
                        decisions['move_forward'] = max(decisions['move_forward'], 0.7)
                    elif angle_diff > 0:
                        decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.4)
                        decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.4)
                    else:
                        decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.4)
                        decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.4)
                    self.target_food = None
                else:
                    # Si no hay árboles cercanos, buscar comida
                    nearest_food = self._find_nearest_food(world)
                    if nearest_food:
                        self.target_food = nearest_food
                        target_angle = float(np.arctan2(nearest_food[1] - float(self.y), nearest_food[0] - float(self.x)))
                        angle_diff = target_angle - self.angle
                        
                        # Normalizar ángulo
                        while angle_diff > np.pi:
                            angle_diff -= 2 * np.pi
                        while angle_diff < -np.pi:
                            angle_diff += 2 * np.pi
                        
                        # Movimiento más directo hacia el objetivo
                        if abs(angle_diff) < 0.3:  # Casi alineado
                            decisions['move_forward'] = max(decisions['move_forward'], 0.8)
                            decisions['eat'] = 0.9  # Intentar comer
                        elif angle_diff > 0:
                            decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.5)
                            decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.5)
                        else:
                            decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.5)
                            decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.5)
                    else:
                        self.target_food = None
            else:
                # Dirigirse hacia comida cercana (comportamiento normal)
                nearest_food = self._find_nearest_food(world)
                if nearest_food:
                    # Guardar objetivo para mostrar línea amarilla
                    self.target_food = nearest_food
                    target_angle = float(np.arctan2(nearest_food[1] - float(self.y), nearest_food[0] - float(self.x)))
                    angle_diff = target_angle - self.angle
                    
                    # Normalizar ángulo
                    while angle_diff > np.pi:
                        angle_diff -= 2 * np.pi
                    while angle_diff < -np.pi:
                        angle_diff += 2 * np.pi
                    
                    # Movimiento más directo hacia el objetivo
                    if abs(angle_diff) < 0.3:  # Casi alineado
                        decisions['move_forward'] = max(decisions['move_forward'], 0.8)
                        decisions['eat'] = 0.9  # Intentar comer
                    elif angle_diff > 0:
                        decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.5)
                        decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.5)
                    else:
                        decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.5)
                        decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.5)
                else:
                    self.target_food = None
        # NUEVA LÓGICA INTELIGENTE PARA PUZZLE
        if self.fitness > 70:  # Agentes con fitness alto
            # Buscar puertas para golpear
            nearest_door = self._find_nearest_door(world)
            if nearest_door:
                target_angle = float(np.arctan2(nearest_door[1] - float(self.y), nearest_door[0] - float(self.x)))
                angle_diff = target_angle - self.angle
                
                # Normalizar ángulo
                while angle_diff > np.pi:
                    angle_diff -= 2 * np.pi
                while angle_diff < -np.pi:
                    angle_diff += 2 * np.pi
                
                # Movimiento hacia puerta
                if abs(angle_diff) < 0.3:
                    decisions['move_forward'] = max(decisions['move_forward'], 0.8)
                elif angle_diff > 0:
                    decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.5)
                    decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.5)
                else:
                    decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.5)
                    decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.5)
                self.target_food = None
        
        if self.fitness > 80:  # Agentes con fitness muy alto
            # Buscar llaves y cofre
            nearest_key = self._find_nearest_key(world)
            if nearest_key:
                target_angle = float(np.arctan2(nearest_key[1] - float(self.y), nearest_key[0] - float(self.x)))
                angle_diff = target_angle - self.angle
                
                # Normalizar ángulo
                while angle_diff > np.pi:
                    angle_diff -= 2 * np.pi
                while angle_diff < -np.pi:
                    angle_diff += 2 * np.pi
                
                # Movimiento hacia llave
                if abs(angle_diff) < 0.3:
                    decisions['move_forward'] = max(decisions['move_forward'], 0.9)
                elif angle_diff > 0:
                    decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.6)
                    decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.6)
                else:
                    decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.6)
                    decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.6)
                self.target_food = None
        
        else:
            # Para agentes con fitness bajo, agregar comportamiento exploratorio
            if not hasattr(self, 'exploration_timer'):
                self.exploration_timer = 0
            self.exploration_timer += 1
            
            # Cada 100 ticks, cambiar dirección aleatoriamente
            if self.exploration_timer > 100:
                self.angle += random.uniform(-0.3, 0.3)
                self.exploration_timer = 0
        
        # Agregar exploración continua pero reducida
        exploration_factor = 0.08  # Más exploración para evitar patrones circulares
        decisions['move_forward'] += random.uniform(-exploration_factor, exploration_factor)
        decisions['turn_left'] += random.uniform(-exploration_factor, exploration_factor)
        decisions['turn_right'] += random.uniform(-exploration_factor, exploration_factor)
        
        # Agregar movimiento aleatorio ocasional para romper patrones
        if random.random() < 0.1:  # 10% de las veces
            # Movimiento en línea recta aleatoria
            random_direction = random.uniform(0, 2 * np.pi)
            self.angle = random_direction
            decisions['move_forward'] += 0.3
        
        # Normalizar decisiones
        decisions['move_forward'] = max(0, min(1, decisions['move_forward']))
        decisions['turn_left'] = max(0, min(1, decisions['turn_left']))
        decisions['turn_right'] = max(0, min(1, decisions['turn_right']))
        decisions['eat'] = max(0, min(1, decisions['eat']))
        
        return decisions
    
    def act(self, decisions, world, other_agents, tick):
        """Ejecuta acciones basadas en decisiones."""
        if not self.alive:
            return
        
        # Envejecer
        self.age += 1
        
        # Consumir energía (REDUCIDO para mejor supervivencia)
        self.energy -= 0.05
        
        # Girar (sistema mejorado para evitar círculos)
        turn_amount = (decisions['turn_right'] - decisions['turn_left']) * 0.12  # Giro moderado
        
        # Limitar giro excesivo para evitar círculos
        if abs(turn_amount) > 0.08:  # Si está girando mucho
            turn_amount *= 0.6  # Reducir giro
            # Agregar pequeña aleatoriedad para romper patrones
            turn_amount += random.uniform(-0.02, 0.02)
        
        self.angle += turn_amount
        
        # Moverse hacia adelante
        self.moving = False
        if decisions['move_forward'] > 0.5:
            angle_float = float(self.angle)
            dx = float(np.cos(angle_float) * self.speed * decisions['move_forward'])
            dy = float(np.sin(angle_float) * self.speed * decisions['move_forward'])
            
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Verificar colisiones con obstáculos
            can_move = not self._check_obstacle_collision(new_x, new_y, world.obstacles)
            
            # Verificar colisión con puertas
            if can_move:
                # Verificar puertas temporalmente
                if world.door and world.door.collides_with(new_x, new_y, self.radius):
                    can_move = False
                if world.door_iron and world.door_iron.collides_with(new_x, new_y, self.radius):
                    can_move = False
            
            if can_move:
                # Mantener dentro de la pantalla
                new_x = max(self.radius, min(world.screen_width - self.radius, new_x))
                new_y = max(self.radius, min(world.screen_height - self.radius, new_y))
                
                # Calcular distancia recorrida
                move_distance = float(np.sqrt((float(new_x) - float(self.x))**2 + (float(new_y) - float(self.y))**2))
                self.distance_traveled += move_distance
                self.movement_distance += move_distance
                self.total_moves += 1
                
                self.x = new_x
                self.y = new_y
                self.moving = True
                
                # Actualizar fitness cada 50 movimientos para feedback visual
                if self.total_moves % 50 == 0:
                    self._calculate_fitness()
        
        # Verificar efectos de zonas especiales
        self._check_zone_effects(world)
        
        # Intentar comer
        self.eating = False
        if decisions['eat'] > 0.5:
            self.total_food_attempts += 1
            self.eating = self._try_eat(world)
            if self.eating:
                self.food_found_count += 1
        
        # Intentar curarse con pociones
        self._try_heal(world)
        
        # Verificar efectos de zonas especiales
        self._check_zone_effects(world)
        
        # Morir si no hay energía
        if self.energy <= 0:
            self.alive = False
            self.death_effect_frames = self.death_effect_max_frames
            self.target_food = None  # Limpiar objetivo al morir
    
    def _check_obstacle_collision(self, x, y, obstacles):
        """Verifica colisión con obstáculos (paredes, árboles y casitas). El agua NO tiene colisión."""
        for obstacle in obstacles:
            if obstacle.type in ["wall", "tree", "hut"] and obstacle.collides_with(x, y, self.radius):
                return True
        return False
    
    def _check_zone_effects(self, world):
        """Verifica efectos de zonas especiales."""
        for obstacle in world.obstacles:
            if obstacle.type in ["water", "safe"] and obstacle.collides_with(self.x, self.y, self.radius):
                effect = obstacle.get_effect()
                
                # Aplicar efectos de energía
                if "energy_loss" in effect:
                    self.energy -= effect["energy_loss"]
                elif "energy_gain" in effect:
                    self.energy = min(self.max_energy, self.energy + effect["energy_gain"])
                
                # Aplicar efectos de fitness
                if "fitness_loss" in effect:
                    self.fitness = max(0, self.fitness - effect["fitness_loss"])
                
                # Aplicar efectos de velocidad
                if "speed_reduction" in effect:
                    self.speed = max(1.0, self.speed * effect["speed_reduction"])
                elif "speed_boost" in effect:
                    self.speed = min(4.0, self.speed * effect["speed_boost"])
    
    def _try_eat(self, world):
        """Intenta comer comida cercana."""
        for food in world.food_items:
            if not food['eaten']:
                # Convertir coordenadas a float para evitar problemas con NumPy
                x_float = float(self.x)
                y_float = float(self.y)
                food_x = float(food['x'])
                food_y = float(food['y'])
                
                dist = float(np.sqrt((x_float - food_x)**2 + (y_float - food_y)**2))
                
                if dist < 40:  # Rango MÁS grande para comer (AUMENTADO)
                    food['eaten'] = True
                    self.energy = min(self.max_energy, self.energy + 30)
                    self.food_eaten += 1
                    # Actualizar fitness en tiempo real para feedback visual
                    self._calculate_fitness()
                    return True
        return False
    
    def _try_pickup_axe(self, world):
        """Intenta agarrar el hacha."""
        if world.check_axe_pickup(self.x, self.y):
            return True
        return False
    
    def _try_cut_tree(self, world, current_tick):
        """Intenta cortar un árbol."""
        # Verificar cooldown del agente
        if current_tick - self.last_tree_hit_tick < self.tree_hit_cooldown:
            return False
        
        if world.process_tree_hit(self.x, self.y, current_tick):
            # Recompensa por cortar árbol
            self.fitness += 10  # TREE_CUT_REWARD
            # Actualizar cooldown del agente
            self.last_tree_hit_tick = current_tick
            return True
        
        # Intentar golpear huts
        if world.process_hut_hit(self.x, self.y, current_tick):
            # Recompensa por destruir hut
            from config import SimulationConfig
            self.fitness += SimulationConfig.HUT_CUT_REWARD  # Usar config
            # Actualizar cooldown del agente
            self.last_tree_hit_tick = current_tick
            return True
        
        return False
    
    def _try_pickup_key(self, world, generation):
        """Intenta recoger una llave."""
        key_type = world.check_key_pickup(self.x, self.y, generation)
        if key_type == "red_key":
            self.fitness += SimulationConfig.RED_KEY_REWARD
            self._calculate_fitness()
            return True
        elif key_type == "gold_key":
            self.fitness += SimulationConfig.GOLD_KEY_REWARD
            self._calculate_fitness()
            return True
        return False
    
    def _try_hit_door(self, world, current_tick):
        """Intenta golpear una puerta."""
        # Verificar cooldown del agente
        if current_tick - self.last_tree_hit_tick < self.tree_hit_cooldown:
            return False
        
        door_type = world.process_door_hit(self.x, self.y, current_tick)
        if door_type == "door":
            self.fitness += SimulationConfig.DOOR_OPEN_REWARD
            self._calculate_fitness()
            self.last_tree_hit_tick = current_tick
            return True
        elif door_type == "door_iron":
            self.fitness += SimulationConfig.DOOR_IRON_OPEN_REWARD
            self._calculate_fitness()
            self.last_tree_hit_tick = current_tick
            return True
        return False
    
    def _try_open_chest(self, world):
        """Intenta abrir el cofre."""
        if world.check_chest_open(self.x, self.y):
            self.fitness += SimulationConfig.CHEST_REWARD
            self._calculate_fitness()
            return True
        return False
    
    def _try_heal(self, world):
        """Intenta usar pociones para curarse."""
        for obstacle in world.obstacles:
            if obstacle.type == "potion":
                distance = float(((float(self.x) - float(obstacle.x))**2 + (float(self.y) - float(obstacle.y))**2)**0.5)
                if distance < 20:  # Rango de usar poción
                    # Curar completamente
                    self.energy = 100
                    self.health = 100
                    # Remover la poción (opcional)
                    world.obstacles.remove(obstacle)
                    return True
        return False
    
    def _find_nearest_food(self, world):
        """Encuentra la comida más cercana."""
        min_distance = float('inf')
        nearest_food = None
        
        for food in world.food_items:
            if not food['eaten']:
                distance = float(np.sqrt((float(self.x) - food['x'])**2 + (float(self.y) - food['y'])**2))
                if distance < min_distance:
                    min_distance = distance
                    nearest_food = (food['x'], food['y'])
        
        return nearest_food
    
    def _find_nearest_cuttable_tree(self, world):
        """Encuentra el árbol más cercano que se puede cortar."""
        if not hasattr(world, 'trees') or not hasattr(world, 'axe_picked_up') or not world.axe_picked_up:
            return None
        
        min_distance = float('inf')
        nearest_tree = None
        
        for tree in world.trees:
            if tree.can_be_cut and not tree.is_cut:
                distance = float(np.sqrt((float(self.x) - tree.x)**2 + (float(self.y) - tree.y)**2))
                if distance < min_distance:
                    min_distance = distance
                    nearest_tree = (tree.x, tree.y)
        
        return nearest_tree
    
    def _find_nearest_door(self, world):
        """Encuentra la puerta más cercana que se puede golpear."""
        doors = []
        
        # Verificar puerta de madera
        if hasattr(world, 'door') and world.door and not world.door.is_open:
            doors.append((world.door.x, world.door.y))
        
        # Verificar puerta de hierro
        if hasattr(world, 'door_iron') and world.door_iron and not world.door_iron.is_open:
            doors.append((world.door_iron.x, world.door_iron.y))
        
        if not doors:
            return None
        
        min_distance = float('inf')
        nearest_door = None
        
        for door_x, door_y in doors:
            distance = float(np.sqrt((float(self.x) - door_x)**2 + (float(self.y) - door_y)**2))
            if distance < min_distance:
                min_distance = distance
                nearest_door = (door_x, door_y)
        
        return nearest_door
    
    def _find_nearest_key(self, world):
        """Encuentra la llave o cofre más cercano."""
        targets = []
        
        # Verificar red_key
        if hasattr(world, 'red_key') and world.red_key and not world.red_key.collected:
            targets.append((world.red_key.x, world.red_key.y))
        
        # Verificar gold_key
        if hasattr(world, 'gold_key') and world.gold_key and not world.gold_key.collected:
            targets.append((world.gold_key.x, world.gold_key.y))
        
        # Verificar cofre
        if hasattr(world, 'chest') and world.chest and not world.chest.is_open:
            targets.append((world.chest.x, world.chest.y))
        
        if not targets:
            return None
        
        min_distance = float('inf')
        nearest_target = None
        
        for target_x, target_y in targets:
            distance = float(np.sqrt((float(self.x) - target_x)**2 + (float(self.y) - target_y)**2))
            if distance < min_distance:
                min_distance = distance
                nearest_target = (target_x, target_y)
        
        return nearest_target
    
    def _calculate_fitness(self):
        """Calcula el fitness del agente."""
        # Fitness base por supervivencia (MÁS IMPORTANTE)
        survival_fitness = min(self.age * 0.008, 15)  # Máximo 15 puntos por supervivencia
        
        # Fitness por comida (VALOR INTERMEDIO)
        food_fitness = self.food_eaten * 5  # 5 puntos por manzana
        
        # Fitness por exploración (VALOR INTERMEDIO)
        exploration_fitness = min(self.distance_traveled / 1000, 6)  # Máximo 6 puntos
        
        # Fitness por evitar obstáculos (MANTENER BAJO)
        obstacle_fitness = 0
        # Usar fitness base en lugar de self.fitness para evitar dependencia circular
        base_fitness = survival_fitness + food_fitness + exploration_fitness
        if base_fitness > 15:  # Umbral ajustado para obstáculos
            obstacle_fitness = self.obstacles_avoided * 1  # Recompensa moderada
        
        # Penalización por movimiento circular
        circular_penalty = 0
        if self.total_moves > 0:
            efficiency = self.distance_traveled / self.total_moves
            if efficiency < 0.5:  # Movimiento muy ineficiente
                circular_penalty = -5
        
        # Fitness total
        total_fitness = survival_fitness + food_fitness + exploration_fitness + obstacle_fitness + circular_penalty
        
        # Normalizar a 0-100
        self.fitness = max(0, min(100, total_fitness))
        
        return self.fitness
    
    def get_movement_skill(self):
        """Calcula el porcentaje de habilidad de movimiento."""
        if self.total_moves == 0:
            return 0
        efficiency = self.distance_traveled / self.total_moves
        return min(100, efficiency * 20)  # Escalar a porcentaje
    
    def get_food_skill(self):
        """Calcula el porcentaje de habilidad para encontrar comida."""
        if self.total_food_attempts == 0:
            return 0
        success_rate = self.food_found_count / self.total_food_attempts
        return success_rate * 100
    
    def get_obstacle_skill(self):
        """Calcula el porcentaje de habilidad para evitar obstáculos."""
        if self.total_obstacle_encounters == 0:
            return 0
        avoidance_rate = self.obstacle_avoidance_count / self.total_obstacle_encounters
        return avoidance_rate * 100
    
    def get_energy_skill(self):
        """Calcula el porcentaje de habilidad de gestión de energía."""
        if self.age == 0:
            return 0
        energy_efficiency = self.energy / (self.age * 0.1 + 1)
        return min(100, energy_efficiency)
    
    def draw(self, screen, tick, sprite_manager, particle_system):
        """Dibuja el agente en la pantalla."""
        if not self.alive:
            self._draw_death_effect(screen, tick)
            return
        
        # Obtener sprite del agente (animado y direccional)
        sprite = sprite_manager.get_agent_sprite(self.angle, tick, self.moving)
        
        if sprite:
            # Escalar sprite a tamaño apropiado para agentes
            scaled_sprite = pygame.transform.scale(sprite, (16, 16))
            sprite_rect = scaled_sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(scaled_sprite, sprite_rect)
        else:
            # Fallback mejorado: agente más nítido
            color_intensity = int(255 * (self.energy / self.max_energy))
            base_color = (color_intensity, 255 - color_intensity, 0)
            
            # Dibujar agente como círculo nítido
            pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)
            
            # Indicador de dirección más nítido
            end_x = int(self.x + np.cos(self.angle) * (self.radius + 5))
            end_y = int(self.y + np.sin(self.angle) * (self.radius + 5))
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x), int(self.y)), (end_x, end_y), 3)
            
            # Punto central para mejor definición
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), 2)
        
        # Dibujar barra de vida
        self._draw_health_bar(screen)
        
        # Dibujar color según fitness
        self._draw_fitness_indicator(screen)
        
        # Efecto de comer
        if hasattr(self, 'eating') and self.eating and particle_system:
            particle_system.add_food_effect(self.x, self.y)
    
    def _draw_health_bar(self, screen):
        """Dibuja barra de vida del agente."""
        if not self.alive:
            return
        
        # Posición de la barra (arriba del agente)
        bar_x = int(self.x - 15)
        bar_y = int(self.y - 20)
        bar_width = 30
        bar_height = 4
        
        # Fondo de la barra (rojo)
        pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Barra de vida (verde)
        health_percentage = self.energy / self.max_energy
        health_width = int(bar_width * health_percentage)
        if health_width > 0:
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
        
        # Borde de la barra
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _draw_fitness_indicator(self, screen):
        """Dibuja indicador de fitness como color de fondo."""
        if not self.alive:
            return
        
        # Calcular color según fitness
        fitness_percentage = self.fitness / 100.0
        
        if fitness_percentage < 0.25:
            # Rojo (fitness bajo)
            color = (255, 0, 0)
        elif fitness_percentage < 0.5:
            # Naranja (fitness medio-bajo)
            color = (255, 165, 0)
        elif fitness_percentage < 0.75:
            # Amarillo (fitness medio)
            color = (255, 255, 0)
        else:
            # Verde (fitness alto)
            color = (0, 255, 0)
        
        # Dibujar círculo de fitness (más grande que el agente)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius + 3, 2)
        
        # Dibujar número de fitness (opcional, solo si es alto)
        if self.fitness > 50:
            font = pygame.font.Font(None, 12)
            fitness_text = font.render(f"{int(self.fitness)}", True, (255, 255, 255))
            text_rect = fitness_text.get_rect(center=(int(self.x), int(self.y) - 25))
            screen.blit(fitness_text, text_rect)
    
    def _draw_death_effect(self, screen, tick):
        """Dibuja efecto de muerte simplificado."""
        if self.death_effect_frames > 0:
            # Efecto simple: círculo rojo con X
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 5)
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x - 3), int(self.y - 3)), 
                           (int(self.x + 3), int(self.y + 3)), 2)
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x + 3), int(self.y - 3)), 
                           (int(self.x - 3), int(self.y + 3)), 2)
            self.death_effect_frames -= 1


class SimpleNeuralNetwork:
    """Red neuronal simple para el cerebro del agente."""
    
    def __init__(self, input_size=8, hidden_size=8, output_size=4):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Pesos aleatorios
        self.W1 = np.random.randn(input_size, hidden_size) * 0.5
        self.b1 = np.random.randn(hidden_size) * 0.1
        self.W2 = np.random.randn(hidden_size, output_size) * 0.5
        self.b2 = np.random.randn(output_size) * 0.1
        
        # Debug: mostrar configuración de la red (solo una vez)
        if not hasattr(SimpleNeuralNetwork, '_debug_printed'):
            SimpleNeuralNetwork._debug_printed = True
            print(f"🧠 Red neuronal: {input_size}→{hidden_size}→{output_size}")
    
    def forward(self, x):
        """Propagación hacia adelante."""
        # Capa oculta
        z1 = np.dot(x, self.W1) + self.b1
        a1 = np.tanh(z1)
        
        # Capa de salida
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = np.tanh(z2)
        
        # Convertir a diccionario de acciones
        return {
            'move_forward': float(a2[0]),
            'turn_left': float(a2[1]),
            'turn_right': float(a2[2]),
            'eat': float(a2[3])
        }
    
    def mutate(self, mutation_rate=0.1):
        """Mutación de la red neuronal."""
        # Mutar pesos de la primera capa
        mask1 = np.random.random(self.W1.shape) < mutation_rate
        self.W1[mask1] += np.random.randn(*self.W1[mask1].shape) * 0.1
        
        # Mutar sesgos de la primera capa
        mask_b1 = np.random.random(self.b1.shape) < mutation_rate
        self.b1[mask_b1] += np.random.randn(*self.b1[mask_b1].shape) * 0.1
        
        # Mutar pesos de la segunda capa
        mask2 = np.random.random(self.W2.shape) < mutation_rate
        self.W2[mask2] += np.random.randn(*self.W2[mask2].shape) * 0.1
        
        # Mutar sesgos de la segunda capa
        mask_b2 = np.random.random(self.b2.shape) < mutation_rate
        self.b2[mask_b2] += np.random.randn(*self.b2[mask_b2].shape) * 0.1
    
    def crossover(self, other):
        """Cruza con otra red neuronal."""
        child = SimpleNeuralNetwork(self.input_size, self.hidden_size, self.output_size)
        
        # Cruza uniforme
        for i in range(self.input_size):
            for j in range(self.hidden_size):
                if np.random.random() < 0.5:
                    child.W1[i, j] = self.W1[i, j]
                else:
                    child.W1[i, j] = other.W1[i, j]
        
        for i in range(self.hidden_size):
            for j in range(self.output_size):
                if np.random.random() < 0.5:
                    child.W2[i, j] = self.W2[i, j]
                else:
                    child.W2[i, j] = other.W2[i, j]
        
        return child
