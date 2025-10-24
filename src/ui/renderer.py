"""
Sistema de renderizado con sprites y partículas.
"""

import pygame
import os
import random
import numpy as np


class SpriteManager:
    """Gestor de sprites del juego."""
    
    def __init__(self):
        self.sprites = {}
        self._load_sprites()
    
    def _load_sprites(self):
        """Carga todos los sprites del juego."""
        sprite_dir = "assets/sprites"
        
        # Sprites de agentes (animados)
        self.sprites['agent_down_1'] = self._load_sprite(f"{sprite_dir}/characters/down_1.png")
        self.sprites['agent_down_2'] = self._load_sprite(f"{sprite_dir}/characters/down_2.png")
        self.sprites['agent_up_1'] = self._load_sprite(f"{sprite_dir}/characters/up_1.png")
        self.sprites['agent_up_2'] = self._load_sprite(f"{sprite_dir}/characters/up_2.png")
        self.sprites['agent_left_1'] = self._load_sprite(f"{sprite_dir}/characters/left_1.png")
        self.sprites['agent_left_2'] = self._load_sprite(f"{sprite_dir}/characters/left_2.png")
        self.sprites['agent_right_1'] = self._load_sprite(f"{sprite_dir}/characters/right_1.png")
        self.sprites['agent_right_2'] = self._load_sprite(f"{sprite_dir}/characters/right_2.png")
        self.sprites['agent'] = self._load_sprite(f"{sprite_dir}/characters/player.png")
        
        # Sprites de entorno
        self.sprites['grass_1'] = self._load_sprite(f"{sprite_dir}/environment/001.png")
        self.sprites['grass_2'] = self._load_sprite(f"{sprite_dir}/environment/002.png")
        self.sprites['dirt_1'] = self._load_sprite(f"{sprite_dir}/environment/003.png")
        self.sprites['dirt_2'] = self._load_sprite(f"{sprite_dir}/environment/017.png")
        self.sprites['wall'] = self._load_sprite(f"{sprite_dir}/environment/032.png")
        self.sprites['tree'] = self._load_sprite(f"{sprite_dir}/environment/016.png")
        self.sprites['stump'] = self._load_sprite(f"{sprite_dir}/environment/036.png")
        self.sprites['water_1'] = self._load_sprite(f"{sprite_dir}/environment/018.png")
        self.sprites['water_2'] = self._load_sprite(f"{sprite_dir}/environment/019.png")
        self.sprites['hut'] = self._load_sprite(f"{sprite_dir}/environment/033.png")
        self.sprites['potion'] = self._load_sprite(f"{sprite_dir}/environment/035.png")
        self.sprites['apple'] = self._load_sprite(f"{sprite_dir}/environment/034.png")
        self.sprites['axe'] = self._load_sprite(f"{sprite_dir}/environment/axe.png")
    
    def _load_sprite(self, path):
        """Carga un sprite desde archivo."""
        try:
            if os.path.exists(path):
                sprite = pygame.image.load(path)
                # No escalar automáticamente, mantener tamaño original
                return sprite
            else:
                print(f"⚠️ Sprite no encontrado: {path}")
                return None
        except Exception as e:
            print(f"❌ Error cargando sprite {path}: {e}")
            return None
    
    def get_agent_sprite(self, angle=0, tick=0, moving=False):
        """Obtiene sprite del agente según dirección y animación."""
        # Normalizar ángulo a 0-2π
        angle = angle % (2 * np.pi)
        
        # Determinar dirección basada en ángulo (más preciso)
        if -np.pi/4 <= angle <= np.pi/4:
            direction = 'right'
        elif np.pi/4 < angle <= 3*np.pi/4:
            direction = 'down'
        elif 3*np.pi/4 < angle <= 5*np.pi/4:
            direction = 'left'
        else:
            direction = 'up'
        
        # Animación solo si está moviéndose
        if moving:
            frame = 1 if (tick // 8) % 2 == 0 else 2  # Animación más rápida
        else:
            frame = 1  # Frame estático cuando no se mueve
        
        sprite_key = f'agent_{direction}_{frame}'
        sprite = self.sprites.get(sprite_key)
        
        # Fallback al sprite base
        if not sprite:
            sprite = self.sprites.get('agent')
        
        return sprite
    
    def get_environment_sprite(self, sprite_type, variant=1):
        """Obtiene sprite del entorno."""
        if sprite_type == 'grass':
            return self.sprites.get(f'grass_{variant}')
        elif sprite_type == 'dirt':
            return self.sprites.get(f'dirt_{variant}')
        elif sprite_type == 'wall':
            return self.sprites.get('wall')
        elif sprite_type == 'tree':
            return self.sprites.get('tree')
        elif sprite_type == 'stump':
            return self.sprites.get('stump')
        elif sprite_type == 'water':
            return self.sprites.get(f'water_{variant}')
        elif sprite_type == 'hut':
            return self.sprites.get('hut')
        elif sprite_type == 'potion':
            return self.sprites.get('potion')
        elif sprite_type == 'apple':
            return self.sprites.get('apple')
        elif sprite_type == 'axe':
            return self.sprites.get('axe')
        else:
            return None


class ParticleSystem:
    """Sistema de partículas para efectos visuales."""
    
    def __init__(self):
        self.particles = []
    
    def add_death_effect(self, x, y):
        """Agrega efecto de muerte."""
        for _ in range(5):
            particle = {
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-10, 10),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'life': 30,
                'color': (255, 0, 0)
            }
            self.particles.append(particle)
    
    def add_food_effect(self, x, y):
        """Agrega efecto de comer comida."""
        for _ in range(3):
            particle = {
                'x': x + random.randint(-5, 5),
                'y': y + random.randint(-5, 5),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'life': 20,
                'color': (0, 255, 0)
            }
            self.particles.append(particle)
    
    def update(self):
        """Actualiza todas las partículas."""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        """Dibuja todas las partículas."""
        for particle in self.particles:
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 2)