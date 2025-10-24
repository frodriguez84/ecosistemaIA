#!/usr/bin/env python3
"""
Ecosistema Evolutivo IA - Versión Avanzada
Panel de estadísticas, comida limitada, barras de vida y mejoras visuales.
"""

import sys
import os
import random
import pygame
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import copy
import math
import time

# Agregar src al path
sys.path.insert(0, str(Path("src")))

class SpriteManager:
    """Gestor de sprites para el ecosistema."""
    
    def __init__(self):
        self.sprites = {}
        self.animations = {}
        self.load_all_sprites()
    
    def load_all_sprites(self):
        """Carga todos los sprites del juego."""
        try:
            # Cargar sprite sheet del personaje
            sprite_sheet = pygame.image.load("assets/sprites/characters/player.png")
            self.sprites['character_sheet'] = sprite_sheet
            
            # Cargar frames individuales del personaje
            directions = ['up', 'down', 'left', 'right']
            for direction in directions:
                self.sprites[f'character_{direction}_1'] = pygame.image.load(f"assets/sprites/characters/{direction}_1.png")
                self.sprites[f'character_{direction}_2'] = pygame.image.load(f"assets/sprites/characters/{direction}_2.png")
            
            # Cargar sprites de ambiente
            self.sprites['grass_1'] = pygame.image.load("assets/sprites/environment/001.png")
            self.sprites['grass_2'] = pygame.image.load("assets/sprites/environment/002.png")
            self.sprites['dirt_1'] = pygame.image.load("assets/sprites/environment/003.png")
            self.sprites['dirt_2'] = pygame.image.load("assets/sprites/environment/017.png")
            self.sprites['wall'] = pygame.image.load("assets/sprites/environment/032.png")
            self.sprites['tree'] = pygame.image.load("assets/sprites/environment/016.png")
            self.sprites['water_1'] = pygame.image.load("assets/sprites/environment/018.png")
            self.sprites['water_2'] = pygame.image.load("assets/sprites/environment/019.png")
            
            
            # Cargar nuevos sprites
            self.sprites['hut'] = pygame.image.load("assets/sprites/environment/033.png")
            self.sprites['potion'] = pygame.image.load("assets/sprites/environment/035.png")
            self.sprites['apple'] = pygame.image.load("assets/sprites/environment/034.png")
            
            # Crear animaciones
            self._create_animations()
            
            print("✅ Todos los sprites cargados correctamente")
            
        except Exception as e:
            print(f"❌ Error cargando sprites: {e}")
            # Crear sprites de fallback
            self._create_fallback_sprites()
    
    def _create_animations(self):
        """Crea las animaciones del personaje."""
        directions = ['up', 'down', 'left', 'right']
        for direction in directions:
            self.animations[f'walk_{direction}'] = [
                self.sprites[f'character_{direction}_1'],
                self.sprites[f'character_{direction}_2']
            ]
    
    def _create_fallback_sprites(self):
        """Crea sprites básicos si no se pueden cargar los archivos."""
        # Crear sprites de fallback
        self.sprites['character_up_1'] = pygame.Surface((16, 16))
        self.sprites['character_up_1'].fill((255, 100, 100))
        self.sprites['character_up_2'] = pygame.Surface((16, 16))
        self.sprites['character_up_2'].fill((255, 150, 150))
        
        # Crear animaciones de fallback
        self.animations['walk_up'] = [self.sprites['character_up_1'], self.sprites['character_up_2']]
    
    def get_character_sprite(self, direction, frame):
        """Obtiene el sprite del personaje según dirección y frame."""
        try:
            return self.sprites[f'character_{direction}_{frame}']
        except:
            return self.sprites.get('character_up_1', pygame.Surface((16, 16)))
    
    def get_environment_sprite(self, sprite_type, variant=1):
        """Obtiene sprite de ambiente."""
        try:
            if sprite_type == 'grass':
                return self.sprites[f'grass_{variant}']
            elif sprite_type == 'dirt':
                return self.sprites[f'dirt_{variant}']
            elif sprite_type == 'wall':
                return self.sprites['wall']
            elif sprite_type == 'tree':
                return self.sprites['tree']
            elif sprite_type == 'water':
                return self.sprites[f'water_{variant}']
            elif sprite_type == 'hut':
                return self.sprites['hut']
            elif sprite_type == 'potion':
                return self.sprites['potion']
            elif sprite_type == 'apple':
                return self.sprites['apple']
        except:
            return pygame.Surface((16, 16))

class ParticleSystem:
    """Sistema de partículas para efectos visuales."""
    
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x, y, color, velocity, lifetime):
        """Agrega una nueva partícula."""
        particle = {
            'x': x, 'y': y,
            'color': color,
            'vx': velocity[0], 'vy': velocity[1],
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'size': random.randint(2, 6)
        }
        self.particles.append(particle)
    
    def update(self):
        """Actualiza todas las partículas."""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['lifetime'] -= 1
            particle['vx'] *= 0.98  # Fricción
            particle['vy'] *= 0.98
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        """Dibuja todas las partículas."""
        for particle in self.particles:
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            color = (*particle['color'], alpha)
            size = int(particle['size'] * (particle['lifetime'] / particle['max_lifetime']))
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), max(1, size))
    
    def add_death_effect(self, x, y):
        """Agrega efecto de muerte."""
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.add_particle(x, y, (255, 100, 100), (vx, vy), 30)
    
    def add_food_effect(self, x, y):
        """Agrega efecto de comer comida."""
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.add_particle(x, y, (100, 255, 100), (vx, vy), 20)

class SimpleNeuralNetwork(nn.Module):
    """Red neuronal para los agentes."""
    
    def __init__(self, input_size=10, hidden_size=8, output_size=4):  # Parametros de la red neuronal
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
            nn.Tanh()
        )
    
    def forward(self, x):
        return self.network(x)
    
    def get_weights(self):
        """Obtiene todos los pesos de la red."""
        weights = []
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                weights.extend(layer.weight.data.flatten().tolist())
                weights.extend(layer.bias.data.flatten().tolist())
        return np.array(weights)
    
    def set_weights(self, weights):
        """Establece los pesos de la red."""
        idx = 0
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                weight_size = layer.weight.numel()
                bias_size = layer.bias.numel()
                
                layer.weight.data = torch.FloatTensor(
                    weights[idx:idx+weight_size]
                ).reshape(layer.weight.shape)
                idx += weight_size
                
                layer.bias.data = torch.FloatTensor(
                    weights[idx:idx+bias_size]
                ).reshape(layer.bias.shape)
                idx += bias_size

class AdvancedAgent:
    """Agente con animación, barra de vida y mejoras visuales."""
    
    def __init__(self, agent_id, x, y, config, brain=None):
        self.id = agent_id
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * np.pi)
        self.energy = config.get('energy_max', 100)
        self.max_energy = config.get('energy_max', 100)
        self.vision_range = config.get('vision_range', 80)
        self.speed = 3.0  # Aumentar velocidad base
        self.radius = 8
        
        # Red neuronal
        if brain is None:
            self.brain = SimpleNeuralNetwork()
        else:
            self.brain = brain
        
        # Estado
        self.alive = True
        self.age = 0
        self.fitness = 0
        self.food_eaten = 0
        self.distance_traveled = 0
        self.obstacles_avoided = 0
        self.last_x = x
        self.last_y = y
        
        # Efectos visuales
        self.death_effect = None
        self.death_timer = 0
        
        # Sistema de sprites
        self.animation_frame = 0
        self.animation_timer = 0
        self.direction = 'down'  # Dirección actual del personaje
        self.last_direction = 'down'
        
        # Estadísticas de habilidades
        self.movement_distance = 0
        self.food_found_count = 0
        self.obstacle_avoidance_count = 0
        self.energy_management_score = 0
        self.total_moves = 0
        self.total_food_attempts = 0
        self.total_obstacle_encounters = 0
        
        # Animación
        self.animation_frame = 0
        self.walk_cycle = 0
        self.last_move_time = 0
        
    def draw(self, screen, tick, sprite_manager=None, particle_system=None):
        """Dibuja el agente con sprites animados."""
        if not self.alive:
            # Dibujar efecto de muerte
            if self.death_effect and particle_system:
                particle_system.add_death_effect(self.x, self.y)
                self._draw_death_effect(screen, tick)
            return
        
        # Determinar dirección del personaje
        self._update_direction()
        
        # Actualizar animación
        self._update_animation(tick)
        
        # Dibujar sprite del personaje
        if sprite_manager:
            self._draw_sprite_character(screen, sprite_manager)
        else:
            # Fallback a círculo si no hay sprite manager
            self._draw_fallback_character(screen)
        
        # Dibujar barra de vida
        self._draw_health_bar(screen)
        
        # Efecto de comer
        if hasattr(self, 'eating') and self.eating and particle_system:
            particle_system.add_food_effect(self.x, self.y)
    
    def _update_direction(self):
        """Actualiza la dirección del personaje según el ángulo."""
        # Convertir ángulo a dirección
        angle_deg = math.degrees(self.angle) % 360
        
        if 315 <= angle_deg or angle_deg < 45:
            self.direction = 'right'
        elif 45 <= angle_deg < 135:
            self.direction = 'down'
        elif 135 <= angle_deg < 225:
            self.direction = 'left'
        elif 225 <= angle_deg < 315:
            self.direction = 'up'
    
    def _update_animation(self, tick):
        """Actualiza la animación del personaje."""
        self.animation_timer += 1
        
        # Cambiar frame cada 10 ticks
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % 2
            self.animation_timer = 0
    
    def _draw_sprite_character(self, screen, sprite_manager):
        """Dibuja el personaje usando sprites."""
        try:
            # Obtener sprite según dirección y frame
            sprite = sprite_manager.get_character_sprite(
                self.direction, 
                self.animation_frame + 1
            )
            
            # Aplicar color basado en fitness
            fitness_color = self.get_fitness_color()
            
            # Crear superficie con color modificado
            colored_sprite = sprite.copy()
            colored_sprite.fill(fitness_color, special_flags=pygame.BLEND_MULT)
            
            # Dibujar sprite centrado
            sprite_rect = colored_sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(colored_sprite, sprite_rect)
            
        except Exception as e:
            # Fallback a círculo si hay error
            self._draw_fallback_character(screen)
    
    def _draw_fallback_character(self, screen):
        """Dibuja personaje básico como fallback."""
        # Calcular color basado en fitness
        fitness_ratio = min(self.fitness / 100, 1.0)
        base_color = (255, int(255 * fitness_ratio), 100)
        
        # Dibujar círculo
        pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.radius)
        
        # Dibujar dirección
        end_x = self.x + math.cos(self.angle) * (self.radius + 5)
        end_y = self.y + math.sin(self.angle) * (self.radius + 5)
        pygame.draw.line(screen, (255, 255, 255), 
                        (int(self.x), int(self.y)), 
                        (int(end_x), int(end_y)), 2)
    
    def _draw_health_bar(self, screen):
        """Dibuja la barra de vida del agente."""
        bar_width = 20
        bar_height = 4
        bar_x = int(self.x - bar_width // 2)
        bar_y = int(self.y - self.radius - 10)
        
        # Color de la barra según energía
        energy_ratio = self.energy / self.max_energy
        if energy_ratio > 0.6:
            bar_color = (0, 255, 0)  # Verde
        elif energy_ratio > 0.3:
            bar_color = (255, 255, 0)  # Amarillo
        else:
            bar_color = (255, 0, 0)  # Rojo
        
        # Fondo de la barra
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Barra de energía
        energy_width = int(bar_width * energy_ratio)
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, energy_width, bar_height))
    
    def get_fitness_color(self):
        """Obtiene el color basado en el fitness del agente."""
        # Calcular fitness relativo (0-1)
        fitness_ratio = min(1.0, self.fitness / 100.0)  # Normalizar a 0-1
        
        # Mapear fitness a colores
        if fitness_ratio < 0.2:
            return (255, 0, 0)      # Rojo - fitness bajo
        elif fitness_ratio < 0.4:
            return (255, 100, 0)     # Naranja - fitness medio-bajo
        elif fitness_ratio < 0.6:
            return (255, 255, 0)    # Amarillo - fitness medio
        elif fitness_ratio < 0.8:
            return (100, 255, 0)    # Verde claro - fitness bueno
        else:
            return (0, 255, 0)       # Verde - fitness excelente
        
        # Borde de la barra
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _draw_death_effect(self, screen, tick):
        """Dibuja el efecto visual de muerte."""
        if not self.death_effect:
            return
        
        # Efecto muy simple: solo un pequeño círculo rojo
        radius = 5
        color = (255, 100, 100)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius)
        
        # X pequeña en el centro
        if self.death_timer < 3:
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x - 3), int(self.y - 3)), 
                           (int(self.x + 3), int(self.y + 3)), 2)
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x + 3), int(self.y - 3)), 
                           (int(self.x - 3), int(self.y + 3)), 2)
        
        self.death_timer += 1
        if self.death_timer > 10:  # Efecto dura solo 10 frames
            self.death_effect = None
    
    def perceive(self, world, other_agents):
        """Percepción del entorno."""
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
        food_direction = self._get_food_direction(world.food_items)
        perceptions.append(food_direction)
        
        # 4. Distancia a otros agentes
        nearest_agent_dist = self._find_nearest_agent(other_agents)
        perceptions.append(min(nearest_agent_dist / self.vision_range, 1.0))
        
        # 5. Dirección a otros agentes
        agent_direction = self._get_agent_direction(other_agents)
        perceptions.append(agent_direction)
        
        # 6. Posición relativa (normalizada)
        screen_width = world.screen_width
        screen_height = world.screen_height
        perceptions.append(self.x / screen_width)
        perceptions.append(self.y / screen_height)
        
        # 7. Ángulo actual
        perceptions.append(self.angle / (2 * np.pi))
        
        # 8. Distancia al obstáculo más cercano
        nearest_obstacle_dist = self._find_nearest_obstacle(world.obstacles)
        perceptions.append(min(nearest_obstacle_dist / self.vision_range, 1.0))
        
        # 9. Dirección al obstáculo más cercano
        obstacle_direction = self._get_obstacle_direction(world.obstacles)
        perceptions.append(obstacle_direction)
        
        return np.array(perceptions, dtype=np.float32)
    
    def _find_nearest_food(self, food_items):
        """Encuentra la comida más cercana."""
        if not food_items:
            return self.vision_range
        
        min_dist = float('inf')
        for food in food_items:
            if not food['eaten']:
                dist = float(np.sqrt((float(self.x) - food['x'])**2 + (float(self.y) - food['y'])**2))
                min_dist = min(min_dist, dist)
        
        return min_dist if min_dist != float('inf') else self.vision_range
    
    def _get_food_direction(self, food_items):
        """Obtiene la dirección hacia la comida más cercana."""
        if not food_items:
            return 0.0
        
        nearest_food = None
        min_dist = float('inf')
        
        for food in food_items:
            if not food['eaten']:
                dist = float(np.sqrt((float(self.x) - food['x'])**2 + (float(self.y) - food['y'])**2))
                if dist < min_dist:
                    min_dist = dist
                    nearest_food = food
        
        if nearest_food:
            dx = nearest_food['x'] - float(self.x)
            dy = nearest_food['y'] - float(self.y)
            target_angle = float(np.arctan2(dy, dx))
            return (target_angle - self.angle) / np.pi
        
        return 0.0
    
    def _find_nearest_agent(self, other_agents):
        """Encuentra el agente más cercano."""
        if not other_agents:
            return self.vision_range
        
        min_dist = float('inf')
        for agent in other_agents:
            if agent.id != self.id and agent.alive:
                dist = float(np.sqrt((float(self.x) - float(agent.x))**2 + (float(self.y) - float(agent.y))**2))
                min_dist = min(min_dist, dist)
        
        return min_dist if min_dist != float('inf') else self.vision_range
    
    def _get_agent_direction(self, other_agents):
        """Obtiene la dirección hacia otros agentes."""
        if not other_agents:
            return 0.0
        
        nearest_agent = None
        min_dist = float('inf')
        
        for agent in other_agents:
            if agent.id != self.id and agent.alive:
                dist = float(np.sqrt((float(self.x) - float(agent.x))**2 + (float(self.y) - float(agent.y))**2))
                if dist < min_dist:
                    min_dist = dist
                    nearest_agent = agent
        
        if nearest_agent:
            dx = nearest_agent.x - self.x
            dy = nearest_agent.y - self.y
            target_angle = float(np.arctan2(dy, dx))
            return (target_angle - self.angle) / np.pi
        
        return 0.0
    
    def _find_nearest_obstacle(self, obstacles):
        """Encuentra el obstáculo más cercano."""
        if not obstacles:
            return self.vision_range
        
        min_dist = float('inf')
        for obstacle in obstacles:
            center_x = obstacle.x + obstacle.width / 2
            center_y = obstacle.y + obstacle.height / 2
            dist = float(np.sqrt((float(self.x) - float(center_x))**2 + (float(self.y) - float(center_y))**2))
            min_dist = min(min_dist, dist)
        
        return min_dist if min_dist != float('inf') else self.vision_range
    
    def _get_obstacle_direction(self, obstacles):
        """Obtiene la dirección hacia el obstáculo más cercano."""
        if not obstacles:
            return 0.0
        
        nearest_obstacle = None
        min_dist = float('inf')
        
        for obstacle in obstacles:
            center_x = obstacle.x + obstacle.width / 2
            center_y = obstacle.y + obstacle.height / 2
            dist = float(np.sqrt((float(self.x) - float(center_x))**2 + (float(self.y) - float(center_y))**2))
            if dist < min_dist:
                min_dist = dist
                nearest_obstacle = obstacle
        
        if nearest_obstacle:
            center_x = nearest_obstacle.x + nearest_obstacle.width / 2
            center_y = nearest_obstacle.y + nearest_obstacle.height / 2
            dx = center_x - self.x
            dy = center_y - self.y
            target_angle = float(np.arctan2(dy, dx))
            return (target_angle - self.angle) / np.pi
        
        return 0.0
    
    def _find_nearest_food(self, world):
        """Encuentra la comida más cercana en el mundo."""
        min_distance = float('inf')
        nearest_food = None
        
        for food in world.food_items:
            if not food['eaten']:
                distance = float(np.sqrt((float(self.x) - food['x'])**2 + (float(self.y) - food['y'])**2))
                if distance < min_distance:
                    min_distance = distance
                    nearest_food = (food['x'], food['y'])
        
        return nearest_food
    
    def decide(self, perceptions, world=None):
        """Toma decisiones basadas en la percepción."""
        with torch.no_grad():
            input_tensor = torch.FloatTensor(perceptions).unsqueeze(0)
            outputs = self.brain(input_tensor).squeeze(0)
            
            # Mejorar la interpretación de las salidas
            move_forward = max(0, min(1, outputs[0]))  # Normalizar entre 0 y 1
            turn_left = max(0, min(1, outputs[1]))     # Normalizar entre 0 y 1
            turn_right = max(0, min(1, outputs[2]))   # Normalizar entre 0 y 1
            eat = max(0, min(1, outputs[3]))          # Normalizar entre 0 y 1
            
            # Agregar exploración continua pero reducida
            exploration_factor = 0.08  # Más exploración para evitar patrones circulares
            move_forward += random.uniform(-exploration_factor, exploration_factor)
            turn_left += random.uniform(-exploration_factor, exploration_factor)
            turn_right += random.uniform(-exploration_factor, exploration_factor)
            
            # Agregar movimiento aleatorio ocasional para romper patrones
            if random.random() < 0.1:  # 10% de las veces
                # Movimiento en línea recta aleatoria
                random_direction = random.uniform(0, 2 * np.pi)
                self.angle = random_direction
                move_forward += 0.3
            
            # Agregar objetivo direccional más frecuente y variado
            if random.random() < 0.6 and world:  # 60% de las veces (más frecuente)
                # Dirigirse hacia comida cercana
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
                        move_forward += 0.4
                    elif angle_diff > 0:
                        turn_right += 0.5
                    else:
                        turn_left += 0.5
                else:
                    self.target_food = None
                eat += random.uniform(-exploration_factor, exploration_factor)
            else:
                self.target_food = None
            
            return {
                'move_forward': max(0, min(1, move_forward)),
                'turn_left': max(0, min(1, turn_left)),
                'turn_right': max(0, min(1, turn_right)),
                'eat': max(0, min(1, eat))
            }
    
    def act(self, decisions, world, other_agents, tick):
        """Ejecuta las acciones decididas."""
        # Girar
        turn_amount = (decisions['turn_right'] - decisions['turn_left']) * 0.1
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
            if not self._check_obstacle_collision(new_x, new_y, world.obstacles):
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
                
                # Gastar energía por moverse
                self.energy -= 0.1
            else:
                # Evitar obstáculo (solo si tiene buen fitness = aprendió)
                if self.fitness > 30:  # Solo cuenta si ya aprendió algo
                    self.obstacles_avoided += 1
                self.obstacle_avoidance_count += 1
                self.total_obstacle_encounters += 1
        
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
        self._check_zone_effects(world.obstacles)
        
        # Gastar energía por estar vivo
        self.energy -= 0.05
        self.age += 1
        
        # Calcular score de gestión de energía
        if self.energy < self.max_energy * 0.3:  # Si está bajo de energía
            self.energy_management_score += 1
        
        # Morir si no tiene energía
        if self.energy <= 0 and self.alive:
            self.alive = False
            self.death_effect = True
            self.death_timer = 0
            self.target_food = None  # Limpiar objetivo al morir
            self._calculate_fitness()
    
    def _check_obstacle_collision(self, x, y, obstacles):
        """Verifica colisión con obstáculos (paredes, árboles y casitas). El agua NO tiene colisión."""
        for obstacle in obstacles:
            if obstacle.type in ["wall", "tree", "hut"] and obstacle.collides_with(x, y, self.radius):
                return True
        return False
    
    def _check_zone_effects(self, obstacles):
        """Verifica efectos de zonas especiales."""
        for obstacle in obstacles:
            if obstacle.type in ["water", "safe"] and obstacle.collides_with(self.x, self.y, self.radius):
                effect = obstacle.get_effect()
                self.energy += effect.get("energy_gain", 0)
                self.energy -= effect.get("energy_loss", 0)
                self.energy = max(0, min(self.max_energy, self.energy))
                
                # Aplicar efectos de velocidad
                if effect.get("speed_reduction", 1.0) != 1.0:
                    self.speed = max(1.0, self.speed * effect["speed_reduction"])
                elif effect.get("speed_boost", 1.0) != 1.0:
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
                
                if dist < 20:  # Rango más grande para comer
                    food['eaten'] = True
                    self.energy = min(self.max_energy, self.energy + 30)
                    self.food_eaten += 1
                    self.fitness += 10
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
    
    def _calculate_fitness(self):
        """Calcula el fitness final del agente (normalizado 0-100)."""
        # Puntuaciones base
        survival_score = min(self.age * 0.5, 25)  # Máximo 25 puntos por supervivencia
        food_score = min(self.food_eaten * 20, 35)  # Máximo 35 puntos por comida (más importante)
        exploration_score = min(self.distance_traveled * 0.08, 25)  # Máximo 25 puntos por exploración (más importante)
        avoidance_score = min(self.obstacles_avoided * 3, 15)  # Máximo 15 puntos por evitar obstáculos
        
        # Penalización por movimiento circular (detección simple)
        circular_penalty = 0
        if self.total_moves > 100:  # Solo si se movió significativamente
            # Calcular si se movió principalmente en círculos
            if self.movement_distance < self.age * 0.5:  # Se movió poco para su edad
                circular_penalty = 5  # Penalización por estar estático
            elif self.movement_distance > self.age * 2.0:  # Se movió demasiado (posible círculo)
                circular_penalty = 3  # Penalización por movimiento excesivo
        
        # Fitness total normalizado
        raw_fitness = survival_score + food_score + exploration_score + avoidance_score - circular_penalty
        self.fitness = max(0.0, min(100.0, raw_fitness))  # Entre 0 y 100
    
    def get_movement_skill(self):
        """Calcula el % de habilidad de desplazamiento."""
        if self.total_moves == 0:
            return 0.0
        # Normalizar distancia total de movimiento
        max_possible_distance = self.age * 2.0  # Máximo posible si se moviera constantemente
        return min(100.0, (self.movement_distance / max_possible_distance) * 100) if max_possible_distance > 0 else 0.0
    
    def get_food_skill(self):
        """Calcula el % de habilidad para encontrar comida."""
        if self.total_food_attempts == 0:
            return 0.0
        return (self.food_found_count / self.total_food_attempts) * 100
    
    def get_obstacle_skill(self):
        """Calcula el % de habilidad para esquivar obstáculos."""
        if self.total_obstacle_encounters == 0:
            return 0.0  # Si no encontró obstáculos, no se puede evaluar
        return (self.obstacle_avoidance_count / self.total_obstacle_encounters) * 100
    
    def get_energy_skill(self):
        """Calcula el % de habilidad para gestionar energía."""
        if self.age == 0:
            return 0.0
        # Menos tiempo con energía baja = mejor habilidad
        energy_management_ratio = 1.0 - (self.energy_management_score / self.age)
        return max(0.0, energy_management_ratio * 100)

class Obstacle:
    """Obstáculo en el mundo."""
    
    def __init__(self, x, y, width, height, obstacle_type="wall"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.color = self._get_color()
    
    def _get_color(self):
        """Obtiene el color según el tipo."""
        if self.type == "wall":
            return (100, 100, 100)  # Gris
        elif self.type == "tree":
            return (50, 150, 50)    # Verde oscuro
        elif self.type == "water":
            return (50, 150, 255)   # Azul
        elif self.type == "safe":
            return (100, 255, 100)  # Verde
        return (150, 150, 150)
    
    def collides_with(self, x, y, radius):
        """Verifica colisión con un punto."""
        return (self.x - radius <= x <= self.x + self.width + radius and
                self.y - radius <= y <= self.y + self.height + radius)
    
    def get_effect(self):
        """Obtiene el efecto del obstáculo."""
        if self.type == "water":
            return {"energy_loss": 2, "speed_reduction": 0.7}  # Agua ralentiza
        elif self.type == "safe":
            return {"energy_gain": 2, "speed_boost": 1.2}
        return {"energy_loss": 0, "speed_reduction": 1.0}
    
    def draw(self, screen, sprite_manager=None, tick=0):
        """Dibuja el obstáculo con sprites mejorados."""
        if sprite_manager:
            self._draw_with_sprites(screen, sprite_manager, tick)
        else:
            self._draw_fallback(screen, tick)
    
    def _draw_with_sprites(self, screen, sprite_manager, tick):
        """Dibuja usando sprites."""
        try:
            if self.type == "wall":
                # Usar sprite de pared
                wall_sprite = sprite_manager.get_environment_sprite('wall')
                self._draw_tiled_sprite(screen, wall_sprite)
                
            elif self.type == "tree":
                # Árbol con sprite
                tree_sprite = sprite_manager.get_environment_sprite('tree')
                # Centrar el árbol
                center_x = self.x + self.width // 2 - tree_sprite.get_width() // 2
                center_y = self.y + self.height // 2 - tree_sprite.get_height() // 2
                screen.blit(tree_sprite, (center_x, center_y))
                
            elif self.type == "water":
                # Agua con sprite animado
                water_variant = 1 if (tick // 10) % 2 == 0 else 2
                water_sprite = sprite_manager.get_environment_sprite('water', water_variant)
                self._draw_tiled_sprite(screen, water_sprite)
                
                
                
            elif self.type == "hut":
                # Casita con sprite
                hut_sprite = sprite_manager.get_environment_sprite('hut')
                screen.blit(hut_sprite, (self.x, self.y))
                
            elif self.type == "potion":
                # Poción con sprite
                potion_sprite = sprite_manager.get_environment_sprite('potion')
                screen.blit(potion_sprite, (self.x, self.y))
                
        except Exception as e:
            # Fallback si hay error con sprites
            self._draw_fallback(screen, tick)
    
    def _draw_tiled_sprite(self, screen, sprite):
        """Dibuja un sprite repetido para llenar el área."""
        sprite_width = sprite.get_width()
        sprite_height = sprite.get_height()
        
        for x in range(0, self.width, sprite_width):
            for y in range(0, self.height, sprite_height):
                screen.blit(sprite, (self.x + x, self.y + y))
    
    def _draw_fire_zone(self, screen, tick):
        """Dibuja zona de fuego con animación."""
        # Fondo rojo
        pygame.draw.rect(screen, (200, 50, 50), 
                       (self.x, self.y, self.width, self.height))
        
        # Llamas animadas
        for i in range(8):
            flame_x = self.x + (i * self.width // 8)
            flame_height = random.randint(10, 20) + int(5 * math.sin(tick * 0.1 + i))
            flame_points = [
                (flame_x, self.y + self.height),
                (flame_x + 5, self.y + self.height - flame_height),
                (flame_x + 10, self.y + self.height)
            ]
            pygame.draw.polygon(screen, (255, 100, 0), flame_points)
            pygame.draw.polygon(screen, (255, 200, 0), 
                              [(flame_x + 1, self.y + self.height),
                               (flame_x + 5, self.y + self.height - flame_height + 5),
                               (flame_x + 9, self.y + self.height)])
        
        # Borde
        pygame.draw.rect(screen, (150, 0, 0), 
                       (self.x, self.y, self.width, self.height), 3)
    
    def _draw_fallback(self, screen, tick):
        """Dibuja obstáculo básico como fallback."""
        if self.type == "wall":
            pygame.draw.rect(screen, (100, 100, 100), 
                           (self.x, self.y, self.width, self.height))
        elif self.type == "tree":
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = self.width // 2
            pygame.draw.circle(screen, (50, 150, 50), (center_x, center_y), radius)
        elif self.type == "water":
            pygame.draw.rect(screen, (50, 150, 255), 
                           (self.x, self.y, self.width, self.height))
        elif self.type == "safe":
            pygame.draw.rect(screen, (50, 150, 50), 
                           (self.x, self.y, self.width, self.height))

class GeneticAlgorithm:
    """Algoritmo genético para evolución."""
    
    def __init__(self, population_size, mutation_rate=0.1, crossover_rate=0.7):
        self.population_size = population_size
        self.mutation_rate = mutation_rate  # Reducido para mejor rendimiento
        self.crossover_rate = crossover_rate  # Reducido para mejor rendimiento
        self.world = None
        self.generation = 0
    
    def evolve(self, agents):
        """Evoluciona la población."""
        fitness_scores = [agent.fitness for agent in agents]
        total_fitness = sum(fitness_scores)
        
        if total_fitness == 0:
            return self._create_random_population()
        
        parents = self._selection(agents, fitness_scores)
        new_agents = []
        
        for i in range(self.population_size):
            if i < len(parents):
                parent1 = parents[i]
                parent2 = parents[(i + 1) % len(parents)]
                child_brain = self._crossover(parent1.brain, parent2.brain)
                child_brain = self._mutate(child_brain)
                
                # Encontrar posición válida para el nuevo agente
                valid_position = False
                attempts = 0
                max_attempts = 50  # Reducir intentos para mejor rendimiento
                x, y = 0, 0
                
                while not valid_position and attempts < max_attempts:
                    x = random.randint(50, 950)
                    y = random.randint(50, 750)
                    
                    # Verificar que no esté sobre obstáculos y que tenga espacio para moverse
                    valid_position = True
                    if self.world:
                        for obstacle in self.world.obstacles:
                            if obstacle.collides_with(x, y, 25):  # Radio de seguridad más grande
                                valid_position = False
                                break
                        
                        # Verificar que no esté en una esquina sin salida
                        if valid_position:
                            # Verificar que tenga al menos 2 direcciones libres
                            free_directions = 0
                            test_positions = [
                                (x + 20, y), (x, y + 20)
                            ]
                            for test_x, test_y in test_positions:
                                can_move = True
                                for obstacle in self.world.obstacles:
                                    if obstacle.collides_with(test_x, test_y, 10):
                                        can_move = False
                                        break
                                if can_move:
                                    free_directions += 1
                            
                            if free_directions < 1:  # Necesita al menos 1 dirección libre
                                valid_position = False
                    
                    attempts += 1
                
                # Si no se encuentra posición válida, usar posición aleatoria dentro del mapa
                if not valid_position:
                    x = random.randint(50, screen_width - 50)
                    y = random.randint(50, screen_height - 50)
                
                new_agent = AdvancedAgent(
                    agent_id=i,
                    x=x,
                    y=y,
                    config={'energy_max': 100, 'vision_range': 80},
                    brain=child_brain
                )
                new_agents.append(new_agent)
            else:
                # Encontrar posición válida para el nuevo agente
                valid_position = False
                attempts = 0
                max_attempts = 50  # Reducir intentos para mejor rendimiento
                x, y = 0, 0
                
                while not valid_position and attempts < max_attempts:
                    x = random.randint(50, 950)
                    y = random.randint(50, 750)
                    
                    # Verificar que no esté sobre obstáculos y que tenga espacio para moverse
                    valid_position = True
                    if self.world:
                        for obstacle in self.world.obstacles:
                            if obstacle.collides_with(x, y, 25):  # Radio de seguridad más grande
                                valid_position = False
                                break
                        
                        # Verificar que no esté en una esquina sin salida
                        if valid_position:
                            # Verificar que tenga al menos 2 direcciones libres
                            free_directions = 0
                            test_positions = [
                                (x + 20, y), (x, y + 20)
                            ]
                            for test_x, test_y in test_positions:
                                can_move = True
                                for obstacle in self.world.obstacles:
                                    if obstacle.collides_with(test_x, test_y, 10):
                                        can_move = False
                                        break
                                if can_move:
                                    free_directions += 1
                            
                            if free_directions < 1:  # Necesita al menos 1 dirección libre
                                valid_position = False
                    
                    attempts += 1
                
                # Si no se encuentra posición válida, usar posición aleatoria dentro del mapa
                if not valid_position:
                    x = random.randint(50, screen_width - 50)
                    y = random.randint(50, screen_height - 50)
                
                new_agent = AdvancedAgent(
                    agent_id=i,
                    x=x,
                    y=y,
                    config={'energy_max': 100, 'vision_range': 80}
                )
                new_agents.append(new_agent)
        
        return new_agents
    
    def _selection(self, agents, fitness_scores):
        """Selección por torneo mejorada."""
        parents = []
        
        # Elitismo: mantener los mejores agentes (más élite)
        elite_count = max(2, self.population_size // 5)  # 20% de élite
        sorted_agents = sorted(zip(agents, fitness_scores), key=lambda x: x[1], reverse=True)
        elite_agents = [agent for agent, _ in sorted_agents[:elite_count]]
        
        # Agregar élite a los padres
        parents.extend(elite_agents)
        
        # Selección por torneo para el resto (más selectivo)
        for _ in range(self.population_size - elite_count):
            tournament = random.sample(list(zip(agents, fitness_scores)), 7)  # Torneo más grande
            winner = max(tournament, key=lambda x: x[1])[0]
            parents.append(winner)
        
        return parents
    
    def _crossover(self, brain1, brain2):
        """Cruza dos redes neuronales."""
        weights1 = brain1.get_weights()
        weights2 = brain2.get_weights()
        
        if random.random() < self.crossover_rate:
            child_weights = []
            for w1, w2 in zip(weights1, weights2):
                if random.random() < 0.5:
                    child_weights.append(w1)
                else:
                    child_weights.append(w2)
            
            child_brain = SimpleNeuralNetwork()
            child_brain.set_weights(np.array(child_weights))
            return child_brain
        else:
            return copy.deepcopy(brain1)
    
    def _mutate(self, brain):
        """Muta una red neuronal con mutación adaptativa."""
        weights = brain.get_weights()
        
        for i in range(len(weights)):
            if random.random() < self.mutation_rate:
                # Mutación adaptativa: más pequeña para pesos grandes
                mutation_strength = 0.1 * (1.0 - abs(weights[i]) / 10.0)  # Menos mutación para pesos grandes
                weights[i] += random.gauss(0, mutation_strength)
        
        brain.set_weights(weights)
        return brain
    
    def _create_random_population(self):
        """Crea una población aleatoria."""
        agents = []
        for i in range(self.population_size):
            # Encontrar posición válida (solo en pasto, no sobre obstáculos)
            valid_position = False
            attempts = 0
            max_attempts = 200  # Más intentos para encontrar pasto
            
            while not valid_position and attempts < max_attempts:
                # Limitar spawn al área del juego (no debajo del panel)
                x = random.randint(50, 900)  # Área del juego, no del panel
                y = random.randint(50, 750)
                
                # Verificar que no esté sobre obstáculos sólidos
                valid_position = True
                if self.world:
                    # Verificar colisiones con obstáculos sólidos
                    for obstacle in self.world.obstacles:
                        if obstacle.type in ["wall", "tree", "hut"] and obstacle.collides_with(x, y, 35):
                            valid_position = False
                            break
                    
                    # Verificar que no esté sobre comida
                    if valid_position:
                        for food in self.world.food_items:
                            distance = ((x - food['x'])**2 + (y - food['y'])**2)**0.5
                            if distance < 25:
                                valid_position = False
                                break
                    
                    # Verificar que no esté en una esquina sin salida
                    if valid_position:
                        # Verificar que tenga al menos 2 direcciones libres
                        free_directions = 0
                        test_positions = [
                            (x + 30, y), (x - 30, y), (x, y + 30), (x, y - 30)
                        ]
                        for test_x, test_y in test_positions:
                            can_move = True
                            for obstacle in self.world.obstacles:
                                if obstacle.collides_with(test_x, test_y, 15):
                                    can_move = False
                                    break
                            if can_move:
                                free_directions += 1
                        
                        if free_directions < 2:  # Necesita al menos 2 direcciones libres
                            valid_position = False
                        
                        # Preferir posiciones en caminos (más alejadas de árboles)
                        if valid_position:
                            min_distance_to_tree = float('inf')
                            for obstacle in self.world.obstacles:
                                if obstacle.type == "tree":
                                    distance = ((x - obstacle.x)**2 + (y - obstacle.y)**2)**0.5
                                    min_distance_to_tree = min(min_distance_to_tree, distance)
                            
                            # Si está muy cerca de un árbol, no es ideal
                            if min_distance_to_tree < 40:
                                valid_position = False
                        
                        # Preferir posiciones en caminos (más alejadas de árboles)
                        if valid_position:
                            min_distance_to_tree = float('inf')
                            for obstacle in self.world.obstacles:
                                if obstacle.type == "tree":
                                    distance = ((x - obstacle.x)**2 + (y - obstacle.y)**2)**0.5
                                    min_distance_to_tree = min(min_distance_to_tree, distance)
                            
                            # Si está muy cerca de un árbol, no es ideal
                            if min_distance_to_tree < 40:
                                valid_position = False
                
                attempts += 1
            
            # Si no se encuentra posición válida, usar posición aleatoria
            if not valid_position:
                x = random.randint(50, 950)
                y = random.randint(50, 750)
            
            agent = AdvancedAgent(
                agent_id=i,
                x=x,
                y=y,
                config={'energy_max': 100, 'vision_range': 80}
            )
            agents.append(agent)
        return agents

class World:
    """Mundo del ecosistema con obstáculos."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.food_items = []
        self.obstacles = []
        self.manual_obstacles = []  # Obstáculos creados manualmente
        self.tick = 0
        
        # Generar obstáculos automáticamente
        self._generate_obstacles()
        
        # Generar comida inicial (solo una vez por generación)
        self._generate_food(40)  # Cantidad de comida inicial
    
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
        for _ in range(random.randint(12, 20)):  # Más árboles
            attempts = 0
            max_attempts = 50
            placed = False
            
            while not placed and attempts < max_attempts:
                x = random.randint(30, self.screen_width - 30)
                y = random.randint(30, self.screen_height - 30)
                
                # Verificar que no se superponga con otros obstáculos
                if not self._check_collision_with_objects(x, y, 35, self.obstacles):
                    tree_size = random.randint(18, 25)
                    self.obstacles.append(Obstacle(x, y, tree_size, tree_size, "tree"))
                    placed = True
                attempts += 1
    
    def _generate_connected_walls(self):
        """Genera paredes conectadas (líneas, L, cuadrado 2x2)."""
        # Generar líneas horizontales (4 paredes juntas)
        for _ in range(random.randint(2, 4)):
            x = random.randint(50, self.screen_width - 200)
            y = random.randint(50, self.screen_height - 50)
            for i in range(4):
                self.obstacles.append(Obstacle(x + i * 20, y, 20, 20, "wall"))
        
        # Generar líneas verticales (4 paredes juntas)
        for _ in range(random.randint(2, 4)):
            x = random.randint(50, self.screen_width - 50)
            y = random.randint(50, self.screen_height - 200)
            for i in range(4):
                self.obstacles.append(Obstacle(x, y + i * 20, 20, 20, "wall"))
        
        # Generar formas L
        for _ in range(random.randint(2, 3)):
            x = random.randint(50, self.screen_width - 100)
            y = random.randint(50, self.screen_height - 100)
            # L horizontal
            for i in range(3):
                self.obstacles.append(Obstacle(x + i * 20, y, 20, 20, "wall"))
            for i in range(2):
                self.obstacles.append(Obstacle(x, y + (i+1) * 20, 20, 20, "wall"))
        
        # Generar cuadrados 2x2
        for _ in range(random.randint(1, 2)):
            x = random.randint(50, self.screen_width - 100)
            y = random.randint(50, self.screen_height - 100)
            for i in range(2):
                for j in range(2):
                    self.obstacles.append(Obstacle(x + i * 20, y + j * 20, 20, 20, "wall"))
    
    def _generate_connected_water(self):
        """Genera agua conectada (líneas, L, cuadrado 2x2)."""
        # Generar líneas de agua horizontales
        for _ in range(random.randint(1, 2)):
            x = random.randint(50, self.screen_width - 200)
            y = random.randint(50, self.screen_height - 50)
            for i in range(3):
                self.obstacles.append(Obstacle(x + i * 30, y, 30, 20, "water"))
        
        # Generar líneas de agua verticales
        for _ in range(random.randint(1, 2)):
            x = random.randint(50, self.screen_width - 50)
            y = random.randint(50, self.screen_height - 200)
            for i in range(3):
                self.obstacles.append(Obstacle(x, y + i * 30, 20, 30, "water"))
    
    def _generate_connected_trees(self):
        """Genera grupos de árboles conectados."""
        # Generar grupos de 2-3 árboles juntos
        for _ in range(random.randint(3, 5)):
            base_x = random.randint(50, self.screen_width - 100)
            base_y = random.randint(50, self.screen_height - 100)
            
            # Grupo de 2-3 árboles
            for i in range(random.randint(2, 3)):
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-30, 30)
                x = base_x + offset_x
                y = base_y + offset_y
                
                if 30 <= x <= self.screen_width - 30 and 30 <= y <= self.screen_height - 30:
                    tree_size = random.randint(18, 25)
                    self.obstacles.append(Obstacle(x, y, tree_size, tree_size, "tree"))
    
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
        self._generate_food(40)

class StatsPanel:
    """Panel de estadísticas en tiempo real."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 24)
    
    def draw_background(self, screen):
        """Dibuja solo el fondo del panel sin actualizar datos."""
        # Fondo del panel con gradiente
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (25, 25, 40), panel_rect)
        pygame.draw.rect(screen, (60, 60, 90), panel_rect, 3)
        
        # Borde interno más sutil
        inner_rect = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)
        pygame.draw.rect(screen, (40, 40, 60), inner_rect, 1)
        
        # Título con efecto
        title = self.title_font.render("* ECOSISTEMA EVOLUTIVO *", True, (100, 255, 150))
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Línea separadora
        pygame.draw.line(screen, (100, 255, 150), (self.x + 10, self.y + 35), (self.x + self.width - 10, self.y + 35), 2)
    
    def draw(self, screen, generation, agents, world, tick):
        """Dibuja el panel de estadísticas simplificado."""
        # Fondo del panel
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (25, 25, 40), panel_rect)
        pygame.draw.rect(screen, (60, 60, 90), panel_rect, 3)
        
        # Título
        title = self.title_font.render("* ECOSISTEMA *", True, (100, 255, 150))
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Línea separadora
        pygame.draw.line(screen, (100, 255, 150), (self.x + 10, self.y + 35), (self.x + self.width - 10, self.y + 35), 2)
        
        # Calcular estadísticas básicas
        alive_agents = [a for a in agents if a.alive]
        dead_agents = [a for a in agents if not a.alive]
        
        # Mostrar minutos de simulación
        minutes = tick // 60
        time_str = f"{minutes} min"
        
        # Solo 5 datos básicos
        stats = [
            f"Generación: {generation}",
            f"Tiempo: {time_str}",
            f"Vivos: {len(alive_agents)}",
            f"Muertos: {len(dead_agents)}",
            f"Comida: {len([f for f in world.food_items if not f['eaten']])}"
        ]
        
        # Dibujar estadísticas
        y_offset = 50
        for stat in stats:
            text = self.font.render(stat, True, (200, 200, 200))
            screen.blit(text, (self.x + 10, self.y + y_offset))
            y_offset += 25

class SummaryPopup:
    """Cuadro de resumen que aparece al final de cada generación."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = 900  # Casi como la pantalla del juego
        self.height = 700
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.visible = False
        self.generation_data = None
        self.fitness_history = []  # Para el gráfico de evolución
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 28)
        self.close_button_rect = None
        
    def show(self, generation_data, fitness_history):
        """Muestra el cuadro de resumen."""
        self.visible = True
        self.generation_data = generation_data
        self.fitness_history = fitness_history.copy()
        
    def hide(self):
        """Oculta el cuadro de resumen."""
        self.visible = False
        
    def handle_click(self, pos):
        """Maneja clicks en el cuadro."""
        if not self.visible:
            return False
            
        # Verificar click en botón cerrar (coordenadas fijas)
        close_button_x = self.x + self.width - 120
        close_button_y = self.y + self.height - 50
        close_button_width = 100
        close_button_height = 30
        
        if (close_button_x <= pos[0] <= close_button_x + close_button_width and 
            close_button_y <= pos[1] <= close_button_y + close_button_height):
            self.hide()
            return True
            
        # Verificar click en el cuadro (NO cerrar automáticamente)
        if (self.x <= pos[0] <= self.x + self.width and 
            self.y <= pos[1] <= self.y + self.height):
            return True  # Click detectado pero no cierra
            
        return False
    
    def add_object_at_coordinates(self, x, y, object_type, world):
        """Añade un objeto en las coordenadas especificadas (automáticamente alineado a tiles)."""
        # Alinear automáticamente a la grilla de tiles (16x16)
        tile_x = (x // 16) * 16
        tile_y = (y // 16) * 16
        
        if object_type == "tree":
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "tree")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🌳 Árbol añadido en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "wall":
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "wall")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🧱 Pared añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "water":
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "water")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"💧 Agua añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "hut":
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "hut")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🏠 Casa añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "potion":
            obstacle = Obstacle(tile_x, tile_y, 16, 16, "potion")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🧪 Poción añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "apple":
            world.food_items.append({'x': tile_x, 'y': tile_y, 'eaten': False})
            print(f"🍎 Manzana añadida en tile ({tile_x}, {tile_y}) - TEMPORAL")
        else:
            print(f"❌ Tipo de objeto '{object_type}' no reconocido")
            print("💡 Tipos disponibles: tree, wall, water, hut, potion, apple")
    
    def draw(self, screen):
        """Dibuja el cuadro de resumen."""
        if not self.visible or not self.generation_data:
            return
            
        # Crear superficie con transparencia
        popup_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        popup_surface.fill((20, 20, 40, 220))  # Fondo semi-transparente
        
        # Borde
        pygame.draw.rect(popup_surface, (100, 255, 150, 255), (0, 0, self.width, self.height), 3)
        
        # Título
        title = self.title_font.render(f"GENERACIÓN {self.generation_data['generation']} COMPLETADA", True, (100, 255, 150))
        title_rect = title.get_rect(center=(self.width//2, 30))
        popup_surface.blit(title, title_rect)
        
        # Línea separadora
        pygame.draw.line(popup_surface, (100, 255, 150), (20, 50), (self.width - 20, 50), 2)
        
        # Datos de la generación
        y_offset = 70
        data = self.generation_data
        
        sections = [
            ("FITNESS:", [
                f"Promedio: {data.get('avg_fitness', 0):.1f}/100",
                f"Máximo: {data.get('max_fitness', 0):.1f}/100"
            ]),
            ("COMPORTAMIENTO:", [
                f"Tiempo de vida: {data.get('avg_age', 0)/60:.1f} min",
                f"Comida promedio: {data.get('avg_food', 0):.1f}",
                f"Esquives exitosos: {data.get('avg_avoidance', 0):.0f}",
                f"Energía promedio: {data.get('avg_energy', 0):.1f}"
            ]),
            ("EFICIENCIA:", [
                f"Exploración: {data.get('avg_exploration', 0):.0f} px",
                f"Supervivencia: {data.get('survival_rate', 0):.1f}%"
            ]),
            ("HABILIDADES (%):", [
                f"Desplazamiento: {data.get('avg_movement_skill', 0):.1f}%",
                f"Búsqueda comida: {data.get('avg_food_skill', 0):.1f}%",
                f"Esquivar obstáculos: {data.get('avg_obstacle_skill', 0):.1f}%",
                f"Gestión energía: {data.get('avg_energy_skill', 0):.1f}%"
            ])
        ]
        
        for section_title, items in sections:
            # Título de sección
            section_text = self.font.render(section_title, True, (100, 255, 150))
            popup_surface.blit(section_text, (20, y_offset))
            y_offset += 25
            
            # Items de la sección
            for item in items:
                item_text = self.font.render(item, True, (220, 220, 220))
                popup_surface.blit(item_text, (30, y_offset))
                y_offset += 20
            y_offset += 10
        
        # Gráfico de evolución (si hay datos históricos)
        if len(self.fitness_history) > 1:
            y_offset += 10
            graph_text = self.font.render("EVOLUCIÓN DEL FITNESS:", True, (100, 255, 150))
            popup_surface.blit(graph_text, (20, y_offset))
            y_offset += 25
            
            # Dibujar gráfico simple
            self._draw_fitness_graph(popup_surface, y_offset)
            y_offset += 100
        
        # Botón cerrar
        close_y = self.height - 50
        self.close_button_rect = pygame.Rect(self.width - 120, close_y, 100, 30)
        pygame.draw.rect(popup_surface, (200, 50, 50), self.close_button_rect)
        pygame.draw.rect(popup_surface, (255, 255, 255), self.close_button_rect, 2)
        
        close_text = self.font.render("CERRAR", True, (255, 255, 255))
        close_rect = close_text.get_rect(center=self.close_button_rect.center)
        popup_surface.blit(close_text, close_rect)
        
        # Dibujar en la pantalla principal
        screen.blit(popup_surface, (self.x, self.y))
        
    def _draw_fitness_graph(self, surface, y_start):
        """Dibuja un gráfico con escalas del fitness por generación."""
        if len(self.fitness_history) < 2:
            return
            
        graph_width = self.width - 60  # Más espacio para etiquetas
        graph_height = 120  # Más alto para mejor visualización
        graph_x = 40  # Más espacio a la izquierda para etiquetas Y
        graph_y = y_start
        
        # Fondo del gráfico
        pygame.draw.rect(surface, (40, 40, 60), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(surface, (100, 100, 100), (graph_x, graph_y, graph_width, graph_height), 1)
        
        # Escala fija del 0 al 100 para fitness
        min_fitness = 0
        max_fitness = 100
        
        # Dibujar líneas de cuadrícula
        for i in range(0, 101, 20):  # Líneas cada 20 puntos
            y = graph_y + graph_height - int((i / 100) * graph_height)
            color = (60, 60, 80) if i % 40 == 0 else (50, 50, 70)  # Líneas más marcadas cada 40
            pygame.draw.line(surface, color, (graph_x, y), (graph_x + graph_width, y), 1)
        
        # Dibujar línea de datos
        points = []
        for i, fitness in enumerate(self.fitness_history):
            x = graph_x + (i * graph_width) // (len(self.fitness_history) - 1)
            y = graph_y + graph_height - int((fitness / 100) * graph_height)
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, (100, 255, 150), False, points, 3)
            
        # Dibujar puntos en cada generación
        for i, (x, y) in enumerate(points):
            pygame.draw.circle(surface, (100, 255, 150), (x, y), 3)
            # Etiqueta de generación
            gen_text = self.font.render(f"G{i+1}", True, (150, 150, 150))
            surface.blit(gen_text, (x - 10, graph_y + graph_height + 5))
        
        # Etiquetas del eje Y (fitness)
        for i in range(0, 101, 20):
            y = graph_y + graph_height - int((i / 100) * graph_height)
            fitness_text = self.font.render(f"{i}", True, (150, 150, 150))
            surface.blit(fitness_text, (graph_x - 25, y - 8))
        
        # Título de los ejes
        y_label = self.font.render("FITNESS", True, (100, 255, 150))
        surface.blit(y_label, (5, graph_y + graph_height//2 - 20))
        
        x_label = self.font.render("GENERACIONES", True, (100, 255, 150))
        surface.blit(x_label, (graph_x + graph_width//2 - 50, graph_y + graph_height + 25))

def main():
    """Función principal."""
    print("🎨 Ecosistema Evolutivo IA")
    print("=" * 70)
    print("💡 FUNCIONES DISPONIBLES:")
    print("   - Presiona 'C' para activar modo comando")
    print("   - Escribe: tree, wall, water, hut, potion, apple")
    print("   - Haz click en el mapa donde quieres colocar el objeto")
    print("   - Presiona ENTER para colocar el objeto")
    print("   - Presiona 'C' nuevamente para salir del modo comando")
    print("=" * 70)
    
    # Configuración
    screen_width = 1200  # Pantalla original
    screen_height = 800
    population_size = 20  # Reducir población para mejor rendimiento
    max_generations = 50
    target_fps = 60  # Aumentar FPS para mayor velocidad
    
    # Inicializar Pygame
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Ecosistema Evolutivo IA - Avanzado con Sprites")
    clock = pygame.time.Clock()
    
    # Crear sistemas de sprites y partículas
    sprite_manager = SpriteManager()
    particle_system = ParticleSystem()
    
    # Crear cuadro de resumen
    summary_popup = SummaryPopup(screen_width, screen_height)
    fitness_history = []  # Historial de fitness para el gráfico
    
    # Crear mundo (sistema original)
    world = World(screen_width - 250, screen_height)  # Dejar espacio para el panel
    
    # Crear algoritmo genético
    ga = GeneticAlgorithm(population_size)
    ga.world = world  # Pasar referencia al mundo
    
    # Crear población inicial
    agents = ga._create_random_population()
    
    # Crear panel de estadísticas (más alto)
    stats_panel = StatsPanel(screen_width - 240, 10, 230, 300)  # Panel más corto
    
    print(f"✅ {len(agents)} agentes avanzados creados")
    print(f"✅ {len(world.food_items)} piezas de comida generadas")
    print(f"✅ {len(world.obstacles)} obstáculos generados")
    print(f"✅ Sistema de sprites inicializado")
    print(f"✅ Sistema de partículas activado")
    
    # Bucle principal
    running = True
    paused = False
    generation = 1
    max_ticks_per_generation = 10000  # Más tiempo para buscar comida
    tick = 0
    stats_update_counter = 0  # Contador para actualizar estadísticas
    
    # Sistema de comandos
    command_mode = False
    current_command = ""
    last_click_coords = None
    
    # Optimizaciones de rendimiento
    print(f"⚡ Optimizaciones de rendimiento activadas:")
    print(f"   - FPS objetivo: {target_fps}")
    print(f"   - Velocidad de agentes: 3.0 (aumentada)")
    print(f"   - Estadísticas actualizadas cada 5 frames")
    print(f"   - Partículas actualizadas cada 2 frames")
    print(f"   - Redes neuronales optimizadas")
    print(f"   - Menos agentes por generación")
    
    while running and generation <= max_generations:
        # Manejar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_c:
                    # Activar modo comando
                    command_mode = not command_mode
                    current_command = ""
                    if command_mode:
                        print("🎯 MODO COMANDO ACTIVADO")
                        print("💡 Escribe: tree, wall, water, hut, potion, apple")
                        print("💡 Luego haz click en el mapa para colocar el objeto")
                    else:
                        print("❌ Modo comando desactivado")
                elif command_mode:
                    # Manejar comandos
                    if event.key == pygame.K_RETURN:
                        # Ejecutar comando
                        if current_command and last_click_coords:
                            x, y = last_click_coords
                            summary_popup.add_object_at_coordinates(x, y, current_command, world)
                            command_mode = False
                            current_command = ""
                        else:
                            print("❌ Primero haz click en el mapa")
                    elif event.key == pygame.K_BACKSPACE:
                        # Borrar último carácter
                        current_command = current_command[:-1]
                    else:
                        # Añadir carácter
                        char = event.unicode.lower()
                        if char.isalpha():
                            current_command += char
                            print(f"📝 Comando: {current_command}")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Manejar clicks en el cuadro de resumen
                if summary_popup.handle_click(event.pos):
                    pass  # El cuadro se cierra automáticamente
                else:
                    # Mostrar coordenadas del click
                    x, y = event.pos
                    if x < screen_width - 250:  # Solo en el área del juego
                        # Convertir a coordenadas de tile (16x16)
                        tile_x = (x // 16) * 16
                        tile_y = (y // 16) * 16
                        tile_coord_x = x // 16
                        tile_coord_y = y // 16
                        
                        # Guardar coordenadas para comandos
                        last_click_coords = (tile_x, tile_y)
                        
                        print(f"📍 Click en píxeles: ({x}, {y})")
                        print(f"🎯 Coordenadas de tile: ({tile_x}, {tile_y})")
                        print(f"📐 Tile número: ({tile_coord_x}, {tile_coord_y})")
                        
                        if command_mode:
                            print(f"✅ Coordenadas guardadas para comando: {current_command}")
                            print("💡 Presiona ENTER para colocar el objeto")
                        else:
                            print("💡 Presiona 'C' para activar modo comando")
        
        if not paused:
            # Actualizar agentes (optimizado)
            alive_agents = [a for a in agents if a.alive]
            
            # Solo actualizar si hay agentes vivos
            if alive_agents:
                for agent in alive_agents:
                    perceptions = agent.perceive(world, alive_agents)
                    decisions = agent.decide(perceptions, world)
                    agent.act(decisions, world, alive_agents, tick)
            
            world.update()
            tick += 1
            
            # Verificar si todos murieron o se acabó el tiempo
            if len(alive_agents) == 0 or tick >= max_ticks_per_generation:
                print(f"\n🧬 Generación {generation} terminada")
                print(f"   - Agentes vivos: {len(alive_agents)}")
                print(f"   - Ticks: {tick}")
                
                if agents:
                    avg_fitness = sum(agent.fitness for agent in agents) / len(agents)
                    max_fitness = max(agent.fitness for agent in agents)
                    avg_age = sum(agent.age for agent in agents) / len(agents)
                    avg_food = sum(agent.food_eaten for agent in agents) / len(agents)
                    avg_avoidance = sum(agent.obstacles_avoided for agent in agents) / len(agents)
                    avg_energy = sum(agent.energy for agent in alive_agents) / len(alive_agents) if alive_agents else 0
                    
                    print(f"   - Fitness promedio: {avg_fitness:.1f}/100")
                    print(f"   - Fitness máximo: {max_fitness:.1f}/100")
                    print(f"   - Tiempo de vida: {avg_age/60:.1f} min")
                    print(f"   - Comida promedio: {avg_food:.1f}")
                    print(f"   - Esquives exitosos: {avg_avoidance:.0f}")
                    print(f"   - Supervivencia: {len(alive_agents)/len(agents)*100:.1f}%")
                else:
                    avg_fitness = max_fitness = avg_age = avg_food = avg_avoidance = avg_energy = 0
                
                # Preparar datos para el cuadro de resumen
                generation_data = {
                    'generation': generation,
                    'avg_fitness': avg_fitness,
                    'max_fitness': max_fitness,
                    'avg_age': avg_age,
                    'avg_food': avg_food,
                    'avg_avoidance': avg_avoidance,
                    'avg_energy': avg_energy,
                    'avg_exploration': sum(agent.distance_traveled for agent in agents)/len(agents) if agents else 0,
                    'survival_rate': len(alive_agents)/len(agents)*100 if agents else 0,
                    'avg_movement_skill': sum(agent.get_movement_skill() for agent in agents) / len(agents) if agents else 0,
                    'avg_food_skill': sum(agent.get_food_skill() for agent in agents) / len(agents) if agents else 0,
                    'avg_obstacle_skill': sum(agent.get_obstacle_skill() for agent in agents) / len(agents) if agents else 0,
                    'avg_energy_skill': sum(agent.get_energy_skill() for agent in agents) / len(agents) if agents else 0
                }
                
                # Añadir fitness promedio al historial
                fitness_history.append(avg_fitness)
                
                # Mostrar cuadro de resumen
                summary_popup.show(generation_data, fitness_history)
                
                # Evolucionar
                agents = ga.evolve(agents)
                world.reset_food()
                world.tick = 0
                tick = 0
                generation += 1
                
                print(f"✅ Nueva generación {generation} creada")
        
        # Renderizar
        screen.fill((40, 40, 60))  # Fondo azul oscuro
        
        # Dibujar fondo solo con pasto
        for x in range(0, screen_width - 250, 16):
            for y in range(0, screen_height, 16):
                # Solo pasto con variación
                grass_variant = 1 if (x // 16 + y // 16) % 2 == 0 else 2
                grass_sprite = sprite_manager.get_environment_sprite('grass', grass_variant)
                screen.blit(grass_sprite, (x, y))
        
        # Dibujar obstáculos con sprites
        for obstacle in world.obstacles:
            obstacle.draw(screen, sprite_manager, tick)
        
        # Dibujar manzanas (comida)
        for food in world.food_items:
            if not food['eaten']:
                # Dibujar manzana con sprite
                apple_sprite = sprite_manager.get_environment_sprite('apple')
                screen.blit(apple_sprite, (int(food['x'] - 8), int(food['y'] - 8)))
        
        # Actualizar sistema de partículas (cada 2 frames para mejor rendimiento)
        if tick % 2 == 0:
            particle_system.update()
        
        # Limpiar objetivos de agentes muertos para mejor rendimiento
        for agent in agents:
            if not agent.alive and hasattr(agent, 'target_food'):
                agent.target_food = None
        
        # Dibujar agentes con sprites animados
        for agent in agents:
            agent.draw(screen, tick, sprite_manager, particle_system)
            
            # Dibujar indicador de comportamiento inteligente
            if agent.fitness > 50 and agent.alive:  # Solo agentes vivos con buen fitness
                # Dibujar línea hacia comida cercana si la está buscando
                if hasattr(agent, 'target_food') and agent.target_food:
                    # Solo dibujar si el agente está dentro del mapa visible
                    if 0 <= agent.x < screen_width - 250 and 0 <= agent.y < screen_height:
                        pygame.draw.line(screen, (255, 255, 0), 
                                       (int(agent.x), int(agent.y)), 
                                       (int(agent.target_food[0]), int(agent.target_food[1])), 2)
        
        # Dibujar partículas
        particle_system.draw(screen)
        
        # Dibujar panel de estadísticas simplificado
        stats_panel.draw(screen, generation, agents, world, tick)
        
        # Dibujar cuadro de resumen (si está visible)
        summary_popup.draw(screen)
        
        # Información básica en la esquina
        font = pygame.font.Font(None, 24)
        alive_count = len([a for a in agents if a.alive])
        food_count = len([f for f in world.food_items if not f['eaten']])
        
        # Mostrar modo comando
        if command_mode:
            command_text = f"MODO COMANDO: {current_command}"
            command_surface = font.render(command_text, True, (255, 255, 0))
            screen.blit(command_surface, (10, 10))
            
            help_text = "Escribe: tree, wall, water, hut, potion, apple"
            help_surface = font.render(help_text, True, (200, 200, 200))
            screen.blit(help_surface, (10, 35))
            
            if last_click_coords:
                coords_text = f"Click en: {last_click_coords}"
                coords_surface = font.render(coords_text, True, (0, 255, 0))
                screen.blit(coords_surface, (10, 60))
        
        #info_text = f"Gen: {generation}/{max_generations} | Vivos: {alive_count} | Comida: {food_count}"
        #text_surface = font.render(info_text, True, (255, 255, 255))
        #screen.blit(text_surface, (10, 10))
        
        if paused:
            pause_text = font.render("PAUSADO - Presiona ESPACIO", True, (255, 0, 0))
            screen.blit(pause_text, (10, 40))
        
        pygame.display.flip()
        clock.tick(target_fps)  # Usar FPS objetivo
    
    pygame.quit()
    print(f"\n🎉 Simulación completada - {generation-1} generaciones evolucionadas")

if __name__ == "__main__":
    main()
