"""
Obstáculos del mundo: paredes, árboles, agua, casitas, pociones.
"""

import pygame
import random


class Obstacle:
    """Obstáculo del mundo."""
    
    def __init__(self, x, y, width, height, obstacle_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.collision_count = 0  # Para sistema de cortar árboles
        self.is_cut = False  # Si el árbol fue cortado
        self.can_be_cut = False  # Si puede ser cortado (cuando hay ≤5 manzanas)
    
    def collides_with(self, x, y, radius):
        """Verifica si hay colisión con el obstáculo."""
        # Si el árbol está cortado, no hay colisión
        if self.type == "tree" and self.is_cut:
            return False
        
        # Calcular distancia desde el centro del obstáculo
        dx = abs(x - (self.x + self.width // 2))
        dy = abs(y - (self.y + self.height // 2))
        
        # Si está fuera del rectángulo expandido, no hay colisión
        if dx > (self.width // 2 + radius):
            return False
        if dy > (self.height // 2 + radius):
            return False
        
        # Si está dentro del rectángulo expandido, hay colisión
        return True
    
    def get_effect(self):
        """Obtiene el efecto del obstáculo."""
        if self.type == "water":
            return {"energy_loss": 0.25, "speed_reduction": 0.8, "fitness_loss": 2}  # Agua más suave
        elif self.type == "safe":
            return {"energy_gain": 2, "speed_boost": 1.2}
        return {"energy_loss": 0, "speed_reduction": 1.0}
    
    def draw(self, screen, sprite_manager, tick):
        """Dibuja el obstáculo."""
        if self.type == "wall":
            sprite = sprite_manager.get_environment_sprite('wall')
        elif self.type == "tree":
            if self.is_cut:
                sprite = sprite_manager.get_environment_sprite('stump')  # Tronco cortado
            else:
                sprite = sprite_manager.get_environment_sprite('tree')
        elif self.type == "water":
            # Alternar entre dos sprites de agua para efecto animado
            water_variant = 1 if (tick // 10) % 2 == 0 else 2
            sprite = sprite_manager.get_environment_sprite('water', water_variant)
        elif self.type == "hut":
            sprite = sprite_manager.get_environment_sprite('hut')
        elif self.type == "potion":
            sprite = sprite_manager.get_environment_sprite('potion')
        else:
            sprite = None
        
        if sprite:
            screen.blit(sprite, (self.x, self.y))
        else:
            # Fallback: dibujar rectángulo de color
            color = self._get_color()
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
    
    def _draw_hit_counter(self, screen):
        """Dibuja la barra de vida del árbol."""
        from config import SimulationConfig
        
        # Obtener golpes restantes
        hits_remaining = SimulationConfig.TREE_HITS_TO_CUT - self.collision_count
        
        if hits_remaining > 0:
            # Calcular progreso de vida
            max_hits = SimulationConfig.TREE_HITS_TO_CUT
            health_ratio = hits_remaining / max_hits
            
            # Dimensiones de la barra
            bar_width = 20
            bar_height = 4
            bar_x = self.x + self.width // 2 - bar_width // 2
            bar_y = self.y - 10
            
            # Fondo de la barra (rojo)
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (255, 0, 0), bg_rect)
            
            # Barra de vida (verde)
            health_width = int(bar_width * health_ratio)
            if health_width > 0:
                health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
                pygame.draw.rect(screen, (0, 255, 0), health_rect)
            
            # Borde de la barra
            pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)
    
    def _get_color(self):
        """Obtiene el color del obstáculo."""
        colors = {
            "wall": (100, 100, 100),
            "tree": (34, 139, 34),
            "water": (0, 100, 200),
            "hut": (139, 69, 19),
            "potion": (255, 0, 0)
        }
        return colors.get(self.type, (128, 128, 128))
    
    def hit(self):
        """Registra un golpe al obstáculo (para sistema de cortar árboles)."""
        if self.type == "tree" and self.can_be_cut and not self.is_cut:
            self.collision_count += 1
            if self.collision_count >= 5:
                self.is_cut = True
                return True  # Árbol cortado
        return False


class Axe:
    """Hacha que permite cortar árboles."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.collected_by = None
        self.radius = 15
    
    def collides_with(self, x, y, radius):
        """Verifica si hay colisión con el hacha."""
        dx = abs(x - self.x)
        dy = abs(y - self.y)
        distance = (dx**2 + dy**2)**0.5
        return distance < (self.radius + radius)
    
    def collect(self, agent):
        """Recoge el hacha."""
        if not self.collected:
            self.collected = True
            self.collected_by = agent
            return True
        return False
    
    def draw(self, screen, sprite_manager, tick):
        """Dibuja el hacha."""
        if not self.collected:
            sprite = sprite_manager.get_environment_sprite('axe')
            if sprite:
                screen.blit(sprite, (self.x - 8, self.y - 8))
            else:
                # Fallback: dibujar hacha simple
                pygame.draw.circle(screen, (139, 69, 19), (int(self.x), int(self.y)), 8)
                pygame.draw.rect(screen, (100, 100, 100), (self.x - 2, self.y - 10, 4, 8))
