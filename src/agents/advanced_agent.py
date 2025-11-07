"""
Agente avanzado con cerebro, sensores y actuadores.
"""

import numpy as np
import pygame
import random
import math
import sys
import os
from collections import deque

# Agregar el directorio raíz al path para importar config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
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
        
        # Ventanas deslizantes para métricas anti-círculo
        window = int(getattr(SimulationConfig, 'ANTI_CIRCLE_WINDOW_TICKS', 180))
        self.recent_positions = deque(maxlen=window)
        self.recent_angles = deque(maxlen=window)
        self.recent_cells = deque(maxlen=window)
        self.recent_step_distances = deque(maxlen=window)
        self.metric_sr = 0.0
        self.metric_turn_smooth = 1.0
        self.metric_novelty = 0.0
        self.fitness_env_penalty = 0.0  # penalizaciones acumuladas del entorno (agua, etc.)
        self.puzzle_rewards = 0.0  # rewards acumulados del puzzle (llaves, puertas, cofre)
        
        # Objetivo de comida
        self.target_food = None
        
        # Efectos visuales
        self.death_effect_frames = 0
        self.death_effect_max_frames = 10
        
        # Cooldown para golpear árboles
        self.last_tree_hit_tick = 0
        self.tree_hit_cooldown = 120  # 120 ticks entre golpes (2 segundos a 60 FPS)
    
    def perceive(self, world, other_agents):
        """Recopila información del entorno (10 sensores)."""
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
        
        # 4. Distancia a obstáculos (optimizado: usar distancia² para comparación)
        min_obstacle_dist_sq = float('inf')
        for obstacle in world.obstacles:
            if obstacle.type in ["wall", "tree", "hut"]:
                dx = float(self.x) - float(obstacle.x)
                dy = float(self.y) - float(obstacle.y)
                dist_sq = dx*dx + dy*dy  # Comparar sin sqrt
                min_obstacle_dist_sq = min(min_obstacle_dist_sq, dist_sq)
        # Calcular sqrt solo una vez al final si es necesario
        min_obstacle_dist = float(np.sqrt(min_obstacle_dist_sq)) if min_obstacle_dist_sq != float('inf') else float('inf')
        perceptions.append(min(min_obstacle_dist / self.vision_range, 1.0) if min_obstacle_dist != float('inf') else 1.0)
        
        # 5. Posición X normalizada
        perceptions.append(self.x / world.screen_width)
        
        # 6. Posición Y normalizada
        perceptions.append(self.y / world.screen_height)
        
        # 7. Ángulo actual normalizado
        perceptions.append(self.angle / (2 * np.pi))
        
        # 8. Estado combinado de llaves (0=ninguna, 0.5=una, 1=ambas)
        red_key_collected = 1.0 if (hasattr(world, 'red_key_collected') and world.red_key_collected) else 0.0
        gold_key_collected = 1.0 if (hasattr(world, 'gold_key_collected') and world.gold_key_collected) else 0.0
        key_status = (red_key_collected + gold_key_collected) / 2.0
        perceptions.append(key_status)
        
        # 9. Estado combinado de puertas (0=cerradas, 1=abiertas)
        door_open = 1.0 if (hasattr(world, 'door') and world.door and world.door.is_open) else 0.0
        door_iron_open = 1.0 if (hasattr(world, 'door_iron') and world.door_iron and world.door_iron.is_open) else 0.0
        door_status = max(door_open, door_iron_open)  # Al menos una abierta
        perceptions.append(door_status)
        
        # 10. Ratio de comida disponible
        from config import SimulationConfig
        available_food = len([f for f in world.food_items if not f['eaten']])
        food_ratio = available_food / SimulationConfig.FOOD_COUNT if SimulationConfig.FOOD_COUNT > 0 else 0.0
        perceptions.append(min(food_ratio, 1.0))
        
        return np.array(perceptions, dtype=np.float32)
    
    def decide(self, world, other_agents, sprite_manager):
        """Toma decisiones basadas en percepciones."""
        perceptions = self.perceive(world, other_agents)
        decisions = self.brain.forward(perceptions)
        
        # Aplicar lógica adicional para comportamiento inteligente (sistema mejorado)
        if self.fitness > 30:  # Agentes con fitness medio-alto
            # Verificar si hay poca comida y puede cortar árboles
            food_ratio = perceptions[9] if len(perceptions) > 9 else 1.0  # Sensor 10: ratio de comida
            has_axe = 1.0 if (hasattr(world, 'axe_picked_up') and world.axe_picked_up) else 0.0
            
            # Si hay poca comida (<60%) y tiene hacha, buscar árboles para cortar
            if food_ratio < 0.6 and has_axe > 0.5:
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
        # LÓGICA INTELIGENTE PARA PUZZLE - SOLO DESPUÉS DE APRENDER TAREAS BÁSICAS
        # Umbrales ajustados para activarse cuando corresponde (fitness ~45-50)
        # Solo agentes con fitness medio-alto (que ya dominan tareas básicas) intentan el puzzle
        # HACEMOS LA GUÍA PROBABILÍSTICA Y MENOS AGRESIVA para evitar convergencia masiva
        puzzle_threshold_door = 65.0   # Umbral: agentes con fitness >50 intentan puertas
        puzzle_threshold_key = 65.0   # Umbral: agentes con fitness >50 buscan llaves/cofre
        
        # Solo aplicar guía del puzzle con probabilidad (no todos los agentes siguen la guía)
        # Esto evita que todos converjan al mismo punto
        puzzle_guidance_probability = 0.4  # Solo 40% de los agentes siguen la guía hardcodeada
        
        # Buscar puertas para golpear (guía probabilística y menos agresiva)
        if self.fitness > puzzle_threshold_door and random.random() < puzzle_guidance_probability:
            nearest_door = self._find_nearest_door(world)
            if nearest_door:
                target_angle = float(np.arctan2(nearest_door[1] - float(self.y), nearest_door[0] - float(self.x)))
                angle_diff = target_angle - self.angle
                
                # Normalizar ángulo
                while angle_diff > np.pi:
                    angle_diff -= 2 * np.pi
                while angle_diff < -np.pi:
                    angle_diff += 2 * np.pi
                
                # Movimiento hacia puerta (menos agresivo: solo influencia sutil)
                if abs(angle_diff) < 0.3:
                    decisions['move_forward'] = max(decisions['move_forward'], 0.6)  # Reducido de 0.8 a 0.6
                elif angle_diff > 0:
                    decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.2)  # Reducido de 0.5 a 0.2
                    decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.2)
                else:
                    decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.2)  # Reducido de 0.5 a 0.2
                    decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.2)
                self.target_food = None
        
        # Buscar llaves y cofre (guía probabilística y menos agresiva)
        if self.fitness > puzzle_threshold_key and random.random() < puzzle_guidance_probability:
            nearest_key = self._find_nearest_key(world)
            if nearest_key:
                target_angle = float(np.arctan2(nearest_key[1] - float(self.y), nearest_key[0] - float(self.x)))
                angle_diff = target_angle - self.angle
                
                # Normalizar ángulo
                while angle_diff > np.pi:
                    angle_diff -= 2 * np.pi
                while angle_diff < -np.pi:
                    angle_diff += 2 * np.pi
                
                # Movimiento hacia llave/cofre (menos agresivo: solo influencia sutil)
                if abs(angle_diff) < 0.3:
                    decisions['move_forward'] = max(decisions['move_forward'], 0.7)  # Reducido de 0.9 a 0.7
                elif angle_diff > 0:
                    decisions['turn_right'] = min(1.0, decisions['turn_right'] + 0.3)  # Reducido de 0.6 a 0.3
                    decisions['turn_left'] = max(0.0, decisions['turn_left'] - 0.3)
                else:
                    decisions['turn_left'] = min(1.0, decisions['turn_left'] + 0.3)  # Reducido de 0.6 a 0.3
                    decisions['turn_right'] = max(0.0, decisions['turn_right'] - 0.3)
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
        
        # Agregar exploración continua pero reducida (MEJORADO)
        exploration_factor = 0.02  # Reducido de 0.08 a 0.02 para movimiento más dirigido
        decisions['move_forward'] += random.uniform(-exploration_factor, exploration_factor)
        decisions['turn_left'] += random.uniform(-exploration_factor, exploration_factor)
        decisions['turn_right'] += random.uniform(-exploration_factor, exploration_factor)
        
        # Agregar movimiento aleatorio ocasional para romper patrones (REDUCIDO)
        if random.random() < 0.02:  # Reducido de 10% a 2% para menos aleatoriedad
            # Movimiento en línea recta aleatoria
            random_direction = random.uniform(0, 2 * np.pi)
            self.angle = random_direction
            decisions['move_forward'] += 0.2  # Reducido de 0.3 a 0.2
        
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
        
        # RESETEAR velocidad al valor base al inicio de cada tick
        # (los efectos de zonas se aplican después y son temporales)
        self.speed = SimulationConfig.AGENT_SPEED
        
        # Envejecer
        self.age += 1
        
        # Consumir energía (REDUCIDO para mejor supervivencia)
        self.energy -= 0.05
        
        # ===== NORMALIZACIÓN DE GIROS (Evitar turn_left y turn_right simultáneos) =====
        # Si ambos están activos, elegir solo el más fuerte (evita círculos)
        if decisions['turn_left'] > 0.3 and decisions['turn_right'] > 0.3:
            # Ambos activos: elegir el más fuerte y anular el otro
            if decisions['turn_left'] > decisions['turn_right']:
                decisions['turn_right'] = 0.0
            else:
                decisions['turn_left'] = 0.0
        
        # ===== PENALIZACIÓN REACTIVA POR GIRO CONSTANTE =====
        # Detectar giro constante en los últimos 20 ticks usando recent_angles
        if len(self.recent_angles) >= 20:
            # Calcular variación total de ángulo en los últimos 20 ticks
            angles_list = list(self.recent_angles)
            angle_changes = []
            for i in range(1, len(angles_list)):
                delta = angles_list[i] - angles_list[i-1]
                # Normalizar a [-pi, pi]
                while delta > math.pi:
                    delta -= 2 * math.pi
                while delta < -math.pi:
                    delta += 2 * math.pi
                angle_changes.append(abs(delta))
            
            # Si hay giro constante (suma de cambios > umbral), penalizar
            total_angle_change = sum(angle_changes)
            if total_angle_change > 3.0:  # ~3 radianes = ~172 grados en 20 ticks = giro constante
                # Forzar movimiento recto temporalmente (reducir giro a 0)
                decisions['turn_left'] *= 0.2
                decisions['turn_right'] *= 0.2
        
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
            
            # Verificar colisiones con obstáculos y puertas
            can_move = not self._check_obstacle_collision(new_x, new_y, world.obstacles)
            if can_move:
                can_move = not self._check_door_collision(new_x, new_y, world)
            
            # Verificar colisión con perímetro
            if can_move:
                for perimeter_obj in world.perimeter_obstacles:
                    if perimeter_obj.collides_with(new_x, new_y, self.radius, self.radius):
                        can_move = False
                        break
            
            # Verificar colisión con puertas
            if can_move:
                # Verificar puertas temporalmente
                if world.door and world.door.collides_with(new_x, new_y, self.radius):
                    can_move = False
                if world.door_iron and world.door_iron.collides_with(new_x, new_y, self.radius):
                    can_move = False
            
            # Verificar colisión con estanque
            if can_move:
                for pond_obj in world.pond_obstacles:
                    if pond_obj.collides_with(new_x, new_y, self.radius, self.radius):
                        can_move = False
                        break
            
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
                
                # Actualizar ventanas para métricas anti-círculo
                self._update_movement_metrics(move_distance)
                
                # Actualizar fitness cada 100 movimientos (reducido de 50 para mejor rendimiento)
                if self.total_moves % 100 == 0:
                    self._calculate_fitness()
        
        # Verificar efectos de zonas especiales (SOLO UNA VEZ por tick, no dos)
        self._check_zone_effects(world)
        
        # Intentar comer
        self.eating = False
        if decisions['eat'] > 0.5:
            self.total_food_attempts += 1
            self.eating = self._try_eat(world)
            if self.eating:
                self.food_found_count += 1
                # Actualizar fitness solo cuando come (feedback visual inmediato)
                self._calculate_fitness()
        
        # Intentar curarse con pociones
        self._try_heal(world)
        
        # Morir si no hay energía
        if self.energy <= 0:
            self.alive = False
            self.death_effect_frames = self.death_effect_max_frames
            self.target_food = None  # Limpiar objetivo al morir
    
    def _check_obstacle_collision(self, x, y, obstacles):
        """Verifica colisión con obstáculos (paredes, árboles, casitas y puertas). El agua NO tiene colisión."""
        for obstacle in obstacles:
            if obstacle.type in ["wall", "tree", "hut"] and obstacle.collides_with(x, y, self.radius):
                return True
        return False
    
    def _check_door_collision(self, x, y, world):
        """Verifica colisión con puertas (incluyendo el espacio reducido cuando están abiertas)."""
        # Verificar colisión con door
        if world.door and world.door.collides_with(x, y, self.radius):
            return True
        
        # Verificar colisión con door_iron
        if world.door_iron and world.door_iron.collides_with(x, y, self.radius):
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
                
                # Acumular penalización de fitness (no sobrescribir cálculo)
                if "fitness_loss" in effect:
                    self.fitness_env_penalty = max(0.0, self.fitness_env_penalty + effect["fitness_loss"])
                
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
                
                if dist < 20:  # Rango MÁS grande para comer (AUMENTADO)
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
            self.puzzle_rewards += SimulationConfig.RED_KEY_REWARD
            return True
        elif key_type == "gold_key":
            self.puzzle_rewards += SimulationConfig.GOLD_KEY_REWARD
            return True
        return False
    
    def _try_hit_door(self, world, current_tick):
        """Intenta golpear una puerta."""
        # Verificar cooldown del agente
        if current_tick - self.last_tree_hit_tick < self.tree_hit_cooldown:
            return False
        
        door_type = world.process_door_hit(self.x, self.y, current_tick)
        if door_type == "door":
            self.puzzle_rewards += SimulationConfig.DOOR_OPEN_REWARD
            self.last_tree_hit_tick = current_tick
            return True
        elif door_type == "door_iron":
            self.puzzle_rewards += SimulationConfig.DOOR_IRON_OPEN_REWARD
            self.last_tree_hit_tick = current_tick
            return True
        return False
    
    def _try_open_chest(self, world):
        """Intenta abrir el cofre."""
        if world.check_chest_open(self.x, self.y):
            self.puzzle_rewards += SimulationConfig.CHEST_REWARD
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
        min_distance_sq = float('inf')  # Usar distancia² para comparación (sin sqrt)
        nearest_food = None
        
        for food in world.food_items:
            if not food['eaten']:
                # Comparar usando distancia² (más rápido, sin sqrt)
                dx = float(self.x) - food['x']
                dy = float(self.y) - food['y']
                distance_sq = dx*dx + dy*dy
                if distance_sq < min_distance_sq:
                    min_distance_sq = distance_sq
                    nearest_food = (food['x'], food['y'])
        
        return nearest_food
    
    def _find_nearest_cuttable_tree(self, world):
        """Encuentra el árbol más cercano que se puede cortar."""
        if not hasattr(world, 'trees') or not hasattr(world, 'axe_picked_up') or not world.axe_picked_up:
            return None
        
        min_distance_sq = float('inf')  # Usar distancia² para comparación (sin sqrt)
        nearest_tree = None
        
        for tree in world.trees:
            if tree.can_be_cut and not tree.is_cut:
                # Comparar usando distancia² (más rápido, sin sqrt)
                dx = float(self.x) - tree.x
                dy = float(self.y) - tree.y
                distance_sq = dx*dx + dy*dy
                if distance_sq < min_distance_sq:
                    min_distance_sq = distance_sq
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
        
        min_distance_sq = float('inf')  # Usar distancia² para comparación (sin sqrt)
        nearest_door = None
        
        for door_x, door_y in doors:
            # Comparar usando distancia² (más rápido, sin sqrt)
            dx = float(self.x) - door_x
            dy = float(self.y) - door_y
            distance_sq = dx*dx + dy*dy
            if distance_sq < min_distance_sq:
                min_distance_sq = distance_sq
                nearest_door = (door_x, door_y)
        
        return nearest_door
    
    def _find_nearest_key(self, world):
        """Encuentra la llave o cofre más cercano."""
        targets = []
        
        # Verificar red_key
        if hasattr(world, 'red_key') and world.red_key and not world.red_key.collected:
            targets.append((world.red_key.x, world.red_key.y))
        
        # Verificar gold_key SOLO si la puerta de madera está abierta (igual que el pickup)
        if hasattr(world, 'gold_key') and world.gold_key and not world.gold_key.collected:
            # Solo incluir gold_key si la puerta de madera está abierta
            if hasattr(world, 'door') and world.door and world.door.is_open:
                targets.append((world.gold_key.x, world.gold_key.y))
        
        # Verificar cofre SOLO si la puerta de hierro está abierta (igual que el pickup)
        if hasattr(world, 'chest') and world.chest and not world.chest.is_open:
            # Solo incluir cofre si la puerta de hierro está abierta
            if hasattr(world, 'door_iron') and world.door_iron and world.door_iron.is_open:
                targets.append((world.chest.x, world.chest.y))
        
        if not targets:
            return None
        
        min_distance_sq = float('inf')  # Usar distancia² para comparación (sin sqrt)
        nearest_target = None
        
        for target_x, target_y in targets:
            # Comparar usando distancia² (más rápido, sin sqrt)
            dx = float(self.x) - target_x
            dy = float(self.y) - target_y
            distance_sq = dx*dx + dy*dy
            if distance_sq < min_distance_sq:
                min_distance_sq = distance_sq
                nearest_target = (target_x, target_y)
        
        return nearest_target
    
    def _calculate_fitness(self):
        """Calcula el fitness del agente basado en rendimiento."""       
        # MULTIPLICADORES FIJOS: premian el rendimiento real sin depender de la generación
        # Valores balanceados que permiten crecimiento natural cuando los agentes mejoran
        # Ajustados para mejorar curva de fitness promedio (presentación)
        food_multiplier = 10.0  # Premia comer más (aumentado para mejor curva promedio)
        exploration_multiplier = 10.0  # Premia explorar más (aumentado para mejor curva promedio)
        survival_multiplier = 0.008  # Premia supervivencia (reducido para fitness inicial más bajo)
        anti_circle_multiplier = 18.0  # Premia movimiento eficiente (aumentado para combatir círculos)
        obstacle_multiplier = 0.20  # Premia evitar obstáculos
        penalty_max = 10.0  # Penalización reducida (para mejor curva promedio)
        
        # Fitness por supervivencia (crece naturalmente con la edad)
        # Cap reducido de 15 a 8 para que el fitness inicial sea más bajo
        survival_fitness = min(self.age * survival_multiplier, 8)
        
        # Fitness por comida (crece naturalmente con sqrt para evitar explosión)
        food_fitness = food_multiplier * float(np.sqrt(max(0.0, float(self.food_eaten))))
        
        # Fitness por exploración (crece naturalmente con log para evitar explosión)
        exploration_fitness = exploration_multiplier * float(np.log1p(max(0.0, float(self.distance_traveled)) / 350.0))
        exploration_fitness = min(exploration_fitness, 15.0)  # Límite aumentado de 15.0 a 18.0
        
        # Fitness por evitar obstáculos (solo si el agente tiene un fitness base decente)
        obstacle_fitness = 0
        base_fitness = survival_fitness + food_fitness + exploration_fitness
        if base_fitness > 10:
            obstacle_fitness = self.obstacles_avoided * obstacle_multiplier
        
        # Métricas anti-círculo (premian movimiento eficiente)
        # Solo dar bonus si el agente realmente se mueve (más estricto para fitness inicial)
        anti_circle_bonus = 0
        if self.distance_traveled > 100:  # Mínimo movimiento requerido
            w1 = getattr(SimulationConfig, 'ANTI_CIRCLE_W1_SR', 0.4)
            w2 = getattr(SimulationConfig, 'ANTI_CIRCLE_W2_TURN', 0.3)
            w3 = getattr(SimulationConfig, 'ANTI_CIRCLE_W3_NOVELTY', 0.3)
            anti_circle_score = (w1 * self.metric_sr) + (w2 * self.metric_turn_smooth) + (w3 * self.metric_novelty)
            anti_circle_bonus = anti_circle_multiplier * anti_circle_score
        
        # Fitness total (sin limitaciones artificiales por generación)
        total_fitness = survival_fitness + food_fitness + exploration_fitness + obstacle_fitness + anti_circle_bonus
        
        # Sumar rewards del puzzle (llaves, puertas, cofre) - estos premian el éxito real
        total_fitness += self.puzzle_rewards
        
        # Restar penalizaciones acumuladas del entorno (fijo, no adaptativo)
        total_fitness -= min(self.fitness_env_penalty, penalty_max)
        
        # Normalizar a 0-100 (sin tope artificial por generación)
        unclamped = max(0, min(100, total_fitness))

        # Tope progresivo solo por TIEMPO VIVIDO (no por generación)
        # Agentes que viven más tiempo pueden alcanzar fitness más alto
        time_ratio = min(1.0, float(self.age) / float(getattr(SimulationConfig, 'BASE_TICKS', 600)))
        
        # Tope basado solo en tiempo: permite crecimiento natural
        # Agentes que viven el tiempo completo pueden llegar hasta 100
        # Ajustado a 50-100 para permitir que más agentes alcancen fitness alto
        base_cap = 50.0  # Base fija (reducida para permitir más agentes con fitness alto)
        cap_range = 50.0  # Rango fijo (aumentado para permitir más crecimiento)
        max_allowed = base_cap + cap_range * time_ratio  # 50-100 según tiempo vivido
        
        self.fitness = min(unclamped, max_allowed)
        
        return self.fitness

    def _update_movement_metrics(self, move_distance: float):
        """Actualiza ventanas y métricas anti-círculo después de cada movimiento."""
        # Registrar posición/ángulo y distancia de paso
        self.recent_positions.append((float(self.x), float(self.y)))
        self.recent_angles.append(float(self.angle))
        self.recent_step_distances.append(float(move_distance))

        cell_size = int(getattr(SimulationConfig, 'NOVELTY_CELL_SIZE', 16))
        cell = (int(self.x) // cell_size, int(self.y) // cell_size)
        self.recent_cells.append(cell)

        # Straightness ratio
        if len(self.recent_positions) >= 2:
            x0, y0 = self.recent_positions[0]
            xN, yN = self.recent_positions[-1]
            net_displacement = float(np.hypot(xN - x0, yN - y0))
            total_path = 0.0
            px, py = self.recent_positions[0]
            for (qx, qy) in list(self.recent_positions)[1:]:
                total_path += float(np.hypot(qx - px, qy - py))
                px, py = qx, qy
            self.metric_sr = 0.0 if total_path <= 1e-6 else max(0.0, min(1.0, net_displacement / total_path))
        else:
            self.metric_sr = 0.0

        # Giro medio absoluto normalizado (1 = muy recto, 0 = giro fuerte)
        if len(self.recent_angles) >= 2:
            deltas = []
            prev = self.recent_angles[0]
            for a in list(self.recent_angles)[1:]:
                d = a - prev
                # normalizar a [-pi, pi]
                while d > math.pi:
                    d -= 2 * math.pi
                while d < -math.pi:
                    d += 2 * math.pi
                deltas.append(abs(d))
                prev = a
            mean_abs = float(np.mean(deltas)) if deltas else 0.0
            tmax = float(getattr(SimulationConfig, 'TURN_MEAN_ABS_MAX', 0.2))
            self.metric_turn_smooth = 1.0 - max(0.0, min(1.0, mean_abs / max(tmax, 1e-6)))
        else:
            self.metric_turn_smooth = 1.0

        # Novedad espacial en la ventana
        denom = len(self.recent_cells)
        if denom > 0:
            self.metric_novelty = len(set(self.recent_cells)) / float(denom)
        else:
            self.metric_novelty = 0.0
    
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
        
        # Obtener sprite del agente escalado (con cache para mejor rendimiento)
        scaled_sprite = sprite_manager.get_scaled_agent_sprite(self.angle, tick, self.moving, (16, 16))
        
        if scaled_sprite:
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
    """Red neuronal."""
    
    def __init__(self, input_size=8, hidden_size=8, output_size=4):
        # Permitir int (1 capa) o lista (N capas)
        if isinstance(hidden_size, int):
            hidden_layers = [hidden_size]
        else:
            hidden_layers = list(hidden_size) if hidden_size else []

        self.input_size = int(input_size)
        self.hidden_layers = hidden_layers
        self.output_size = int(output_size)

        # Definir tamaños de capas encadenadas
        layer_dims = [self.input_size] + self.hidden_layers + [self.output_size]

        # Crear listas de pesos y sesgos para cada capa (i -> i+1)
        self.weights = []  # lista de matrices W
        self.biases = []   # lista de vectores b
        for layer_idx, (in_dim, out_dim) in enumerate(zip(layer_dims[:-1], layer_dims[1:])):
            W = np.random.randn(in_dim, out_dim) * 0.5
            b = np.random.randn(out_dim) * 0.1
            
            # Ajustar sesgos de la capa de salida para favorecer movimiento recto
            # Índices: 0=move_forward, 1=turn_left, 2=turn_right, 3=eat
            if layer_idx == len(layer_dims) - 2:  # Es la última capa (antes de la salida)
                # Sesgos negativos para turn_left (1) y turn_right (2) -> movimiento recto inicial
                if out_dim >= 3:  # Asegurar que hay al menos 3 salidas
                    b[1] = -0.3  # turn_left: sesgo negativo fuerte
                    b[2] = -0.3  # turn_right: sesgo negativo fuerte
            
            self.weights.append(W)
            self.biases.append(b)

        # Back-compat: exponer W1/b1 y W2/b2 (primera y última capa)
        # Esto evita romper accesos residuales en otros módulos
        self.W1 = self.weights[0]
        self.b1 = self.biases[0]
        self.W2 = self.weights[-1]
        self.b2 = self.biases[-1]

        # Debug: mostrar configuración de la red (solo una vez)
        if not hasattr(SimpleNeuralNetwork, '_debug_printed'):
            SimpleNeuralNetwork._debug_printed = True
            hidden_repr = "→".join(str(h) for h in self.hidden_layers) if self.hidden_layers else "0"
            print(f"🧠 Red neuronal: {self.input_size}→{hidden_repr}→{self.output_size}")
    
    def forward(self, x):
        """Propagación hacia adelante a través de todas las capas."""
        a = x
        # Todas las capas excepto la última con tanh
        for idx in range(len(self.weights) - 1):
            z = np.dot(a, self.weights[idx]) + self.biases[idx]
            a = np.tanh(z)
        # Última capa
        z_out = np.dot(a, self.weights[-1]) + self.biases[-1]
        a_out = np.tanh(z_out)
        
        return {
            'move_forward': float(a_out[0]),
            'turn_left': float(a_out[1]),
            'turn_right': float(a_out[2]),
            'eat': float(a_out[3])
        }
    
    def mutate(self, mutation_rate=0.1):
        """Mutación gaussiana en todas las capas."""
        for i in range(len(self.weights)):
            W = self.weights[i]
            b = self.biases[i]
            mask_W = np.random.random(W.shape) < mutation_rate
            W[mask_W] += np.random.randn(*W[mask_W].shape) * 0.1
            mask_b = np.random.random(b.shape) < mutation_rate
            b[mask_b] += np.random.randn(*b[mask_b].shape) * 0.1
        # Back-compat referencias
        self.W1 = self.weights[0]
        self.b1 = self.biases[0]
        self.W2 = self.weights[-1]
        self.b2 = self.biases[-1]
    
    def crossover(self, other):
        """Cruza uniforme capa a capa con otra red del mismo esquema."""
        child = SimpleNeuralNetwork(self.input_size, self.hidden_layers, self.output_size)
        for i in range(len(self.weights)):
            W_self, W_other = self.weights[i], other.weights[i]
            b_self, b_other = self.biases[i], other.biases[i]
            W_child = child.weights[i]
            b_child = child.biases[i]
            # Matrices
            mask_W = np.random.random(W_self.shape) < 0.5
            W_child[mask_W] = W_self[mask_W]
            W_child[~mask_W] = W_other[~mask_W]
            # Sesgos
            mask_b = np.random.random(b_self.shape) < 0.5
            b_child[mask_b] = b_self[mask_b]
            b_child[~mask_b] = b_other[~mask_b]
        # Back-compat referencias
        child.W1 = child.weights[0]
        child.b1 = child.biases[0]
        child.W2 = child.weights[-1]
        child.b2 = child.biases[-1]
        return child

    def copy_from(self, other):
        """Copia todos los pesos/sesgos desde otra red compatible."""
        # Ajustar estructura si hiciera falta
        if (self.input_size != other.input_size or 
            self.output_size != other.output_size or 
            self.hidden_layers != other.hidden_layers):
            # Re-crear con la misma arquitectura del otro
            self.__init__(other.input_size, other.hidden_layers, other.output_size)
        for i in range(len(self.weights)):
            self.weights[i] = other.weights[i].copy()
            self.biases[i] = other.biases[i].copy()
        # Back-compat referencias
        self.W1 = self.weights[0]
        self.b1 = self.biases[0]
        self.W2 = self.weights[-1]
        self.b2 = self.biases[-1]
