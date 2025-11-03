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
        # Si el árbol o hut está cortado/destruido, no hay colisión
        if (self.type == "tree" or self.type == "hut") and self.is_cut:
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
            from config import SimulationConfig
            return {"energy_loss": 0.05, "speed_reduction": 0.8, "fitness_loss": SimulationConfig.WATER_FITNESS_PENALTY}
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
            # Escalar sprite si es necesario para que coincida con el tamaño del obstáculo
            if sprite.get_width() != self.width or sprite.get_height() != self.height:
                sprite = pygame.transform.scale(sprite, (self.width, self.height))
            screen.blit(sprite, (self.x, self.y))
        else:
            # Fallback: dibujar rectángulo de color
            color = self._get_color()
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
        # NO dibujar barra de vida para árboles y huts (solo para puertas)
    
    # MÉTODO COMENTADO - Ya no se usa para árboles y huts
    # def _draw_hit_counter(self, screen):
    #     """Dibuja la barra de vida del obstáculo (árbol o hut)."""
    #     from config import SimulationConfig
    #     
    #     # Determinar golpes necesarios según el tipo
    #     if self.type == "tree":
    #         max_hits = SimulationConfig.TREE_HITS_TO_CUT
    #         hits_remaining = max_hits - self.collision_count
    #     elif self.type == "hut":
    #         max_hits = SimulationConfig.HUT_HITS_TO_CUT  # Usar config
    #         hits_remaining = max_hits - self.collision_count
    #     else:
    #         return
    #     
    #     if hits_remaining > 0:
    #         # Calcular progreso de vida
    #         health_ratio = hits_remaining / max_hits
    #         
    #         # Dimensiones de la barra
    #         bar_width = 20
    #         bar_height = 4
    #         bar_x = self.x + self.width // 2 - bar_width // 2
    #         bar_y = self.y - 10
    #         
    #         # Fondo de la barra (rojo)
    #         bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    #         pygame.draw.rect(screen, (255, 0, 0), bg_rect)
    #         
    #         # Barra de vida (verde)
    #         health_width = int(bar_width * health_ratio)
    #         if health_width > 0:
    #             health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
    #             pygame.draw.rect(screen, (0, 255, 0), health_rect)
    #         
    #         # Borde de la barra
    #         pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)
    
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
        """Registra un golpe al obstáculo (para sistema de cortar árboles y huts)."""
        from config import SimulationConfig
        
        if self.type == "tree" and self.can_be_cut and not self.is_cut:
            self.collision_count += 1
            if self.collision_count >= 3:  # 3 golpes para árboles
                self.is_cut = True
                return True  # Árbol cortado
        elif self.type == "hut" and not self.is_cut:
            self.collision_count += 1
            if self.collision_count >= SimulationConfig.HUT_HITS_TO_CUT:  # Usar config
                self.is_cut = True
                return True  # Hut destruido
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


class Key:
    """Llave que permite abrir puertas."""
    
    def __init__(self, x, y, key_type):
        self.x = x
        self.y = y
        self.key_type = key_type  # "red_key" o "gold_key"
        self.collected = False
        self.collected_by = None
        self.radius = 15
    
    def collides_with(self, x, y, radius):
        """Verifica si hay colisión con la llave."""
        dx = abs(x - self.x)
        dy = abs(y - self.y)
        distance = (dx**2 + dy**2)**0.5
        return distance < (self.radius + radius)
    
    def collect(self, agent):
        """Recoge la llave."""
        if not self.collected:
            self.collected = True
            self.collected_by = agent
            return True
        return False
    
    def draw(self, screen, sprite_manager, tick):
        """Dibuja la llave."""
        if not self.collected:
            sprite = sprite_manager.get_environment_sprite(self.key_type)
            if sprite:
                # Las llaves se dibujan centradas (self.x y self.y son el centro)
                sprite_width, sprite_height = sprite.get_size()
                screen.blit(sprite, (self.x - sprite_width // 2, self.y - sprite_height // 2))
            else:
                # Fallback: dibujar llave simple (más visible)
                color = (255, 0, 0) if self.key_type == "red_key" else (255, 215, 0)
                # Círculo exterior de color
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 10)
                # Círculo interior más oscuro
                pygame.draw.circle(screen, (200, 0, 0) if self.key_type == "red_key" else (200, 170, 0), 
                                 (int(self.x), int(self.y)), 6)
                # Texto "K" para identificar
                font = pygame.font.Font(None, 16)
                text = font.render("K", True, (255, 255, 255))
                text_rect = text.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(text, text_rect)


class Door:
    """Puerta que requiere llave para abrir."""
    
    def __init__(self, x, y, door_type):
        self.x = x
        self.y = y
        self.door_type = door_type  # "door" o "door_iron"
        self.is_open = False
        self.hit_count = 0
        self.last_hit_tick = 0
        self.width = 20  # Mismo tamaño que otros elementos
        self.height = 20
    
    def collides_with(self, x, y, radius):
        """Verifica si hay colisión con la puerta."""
        if self.is_open:
            # Cuando la puerta está abierta, NO hay colisión - los agentes pueden pasar libremente
            return False
        
        # Puerta cerrada: colisión normal
        dx = abs(x - (self.x + self.width // 2))
        dy = abs(y - (self.y + self.height // 2))
        
        if dx > (self.width // 2 + radius):
            return False
        if dy > (self.height // 2 + radius):
            return False
        
        return True
    
    def hit(self, current_tick, cooldown):
        """Registra un golpe a la puerta."""
        if self.is_open:
            return False
        
        # Cooldown entre golpes
        if current_tick - self.last_hit_tick < cooldown:
            return False
        
        self.hit_count += 1
        self.last_hit_tick = current_tick
        
        from config import SimulationConfig
        max_hits = SimulationConfig.DOOR_HITS_TO_OPEN if self.door_type == "door" else SimulationConfig.DOOR_IRON_HITS_TO_OPEN
        
        if self.hit_count >= max_hits:
            self.is_open = True
            return True  # Puerta abierta
        
        return False
    
    def _draw_hit_counter(self, screen):
        """Dibuja la barra de vida de la puerta."""
        from config import SimulationConfig
        
        max_hits = SimulationConfig.DOOR_HITS_TO_OPEN if self.door_type == "door" else SimulationConfig.DOOR_IRON_HITS_TO_OPEN
        hits_remaining = max_hits - self.hit_count
        
        if hits_remaining > 0 and not self.is_open:
            health_ratio = hits_remaining / max_hits
            
            bar_width = 20
            bar_height = 4
            bar_x = self.x + self.width // 2 - bar_width // 2
            bar_y = self.y - 10
            
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (255, 0, 0), bg_rect)
            
            health_width = int(bar_width * health_ratio)
            if health_width > 0:
                health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
                pygame.draw.rect(screen, (0, 255, 0), health_rect)
            
            pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)
    
    def draw(self, screen, sprite_manager, tick):
        """Dibuja la puerta."""
        if not self.is_open:
            sprite = sprite_manager.get_environment_sprite(self.door_type)
            if sprite:
                # Escalar sprite si es necesario
                if sprite.get_width() != self.width or sprite.get_height() != self.height:
                    sprite = pygame.transform.scale(sprite, (self.width, self.height))
                screen.blit(sprite, (self.x, self.y))
            else:
                # Fallback: dibujar puerta simple
                color = (139, 69, 19) if self.door_type == "door" else (70, 70, 70)
                pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
                # Dibujar bordes
                pygame.draw.rect(screen, (100, 100, 100), (self.x, self.y, self.width, self.height), 2)
            
            # Dibujar contador de golpes
            self._draw_hit_counter(screen)


class Chest:
    """Cofre que se abre al contacto."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_open = False
        self.opened_by = None
        self.width = 20  # Mismo tamaño que otros elementos
        self.height = 20
        self.radius = 10
    
    def collides_with(self, x, y, radius):
        """Verifica si hay colisión con el cofre."""
        dx = abs(x - (self.x + self.width // 2))
        dy = abs(y - (self.y + self.height // 2))
        distance = (dx**2 + dy**2)**0.5
        return distance < (self.radius + radius)
    
    def open(self, agent):
        """Abre el cofre."""
        if not self.is_open:
            self.is_open = True
            self.opened_by = agent
            return True
        return False
    
    def draw(self, screen, sprite_manager, tick):
        """Dibuja el cofre."""
        if self.is_open:
            sprite = sprite_manager.get_environment_sprite('chest_opened')
        else:
            sprite = sprite_manager.get_environment_sprite('chest')
        
        if sprite:
            # Escalar sprite si es necesario
            if sprite.get_width() != self.width or sprite.get_height() != self.height:
                sprite = pygame.transform.scale(sprite, (self.width, self.height))
            screen.blit(sprite, (self.x, self.y))
        else:
            # Fallback: dibujar cofre simple (más visible)
            if not self.is_open:
                # Cofre cerrado - dorado
                pygame.draw.rect(screen, (184, 134, 11), (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, (255, 215, 0), (self.x + 2, self.y + 2, self.width - 4, self.height - 4))
                # Cerradura
                pygame.draw.circle(screen, (139, 69, 19), (self.x + self.width // 2, self.y + self.height // 2), 4)
                # Texto "C" para identificar
                font = pygame.font.Font(None, 18)
                text = font.render("C", True, (139, 69, 19))
                text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
                screen.blit(text, text_rect)
            else:
                # Cofre abierto - gris
                pygame.draw.rect(screen, (192, 192, 192), (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, (128, 128, 128), (self.x + 2, self.y + 2, self.width - 4, self.height - 4))


class PerimeterObstacle:
    """Obstáculo decorativo del perímetro del mapa."""
    
    def __init__(self, x, y, sprite_type):
        self.x = x
        self.y = y
        self.width = 20  # TILE_SIZE
        self.height = 20  # TILE_SIZE
        self.type = 'perimeter'
        self.sprite_type = sprite_type  # '021', '023', '024', '026', '028', '029', '030', '031'
    
    def collides_with(self, other_x, other_y, other_width, other_height):
        """Verifica colisión con otro objeto."""
        return (self.x < other_x + other_width and
                self.x + self.width > other_x and
                self.y < other_y + other_height and
                self.y + self.height > other_y)
    
    def draw(self, screen, sprite_manager):
        """Dibuja el obstáculo del perímetro."""
        sprite = sprite_manager.get_environment_sprite('perimeter', self.sprite_type)
        
        if sprite:
            # Escalar sprite al tamaño correcto
            sprite_scaled = pygame.transform.scale(sprite, (self.width, self.height))
            screen.blit(sprite_scaled, (self.x, self.y))
        else:
            # Fallback visual si no se encuentra el sprite
            pygame.draw.rect(screen, (100, 100, 100), (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (80, 80, 80), (self.x + 1, self.y + 1, self.width - 2, self.height - 2))


class PondObstacle:
    """Estanque móvil de 3x3 tiles."""
    
    def __init__(self, x, y, sprite_type):
        self.x = x
        self.y = y
        self.width = 20  # TILE_SIZE
        self.height = 20  # TILE_SIZE
        self.type = 'pond'
        self.sprite_type = sprite_type  # '020', '021', '022', '023', '019', '024', '025', '026', '027'
    
    def collides_with(self, other_x, other_y, other_width, other_height):
        """Verifica colisión con otro objeto."""
        return (self.x < other_x + other_width and
                self.x + self.width > other_x and
                self.y < other_y + other_height and
                self.y + self.height > other_y)
    
    def draw(self, screen, sprite_manager, tick=0):
        """Dibuja el elemento del estanque con animación de agua."""
        # Para elementos de agua (019/018), usar el mismo sistema que el agua suelta
        if self.sprite_type in ['019', '018']:
            # Usar el mismo sistema de animación que el agua suelta (cada 10 ticks)
            water_variant = 1 if (tick // 10) % 2 == 0 else 2
            sprite = sprite_manager.get_environment_sprite('water', water_variant)
        else:
            sprite = sprite_manager.get_environment_sprite('pond', self.sprite_type)
        
        if sprite:
            # Escalar sprite al tamaño correcto
            sprite_scaled = pygame.transform.scale(sprite, (self.width, self.height))
            screen.blit(sprite_scaled, (self.x, self.y))
        else:
            # Fallback visual si no se encuentra el sprite
            pygame.draw.rect(screen, (100, 150, 200), (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (80, 120, 180), (self.x + 1, self.y + 1, self.width - 2, self.height - 2))
