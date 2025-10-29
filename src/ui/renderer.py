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
        self.sprite_paths = {}  # Almacenar rutas para recarga
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
        
        # Sprites de fortalezas
        self.sprites['door'] = self._load_sprite(f"{sprite_dir}/environment/door.png")
        self.sprites['door_iron'] = self._load_sprite(f"{sprite_dir}/environment/door_iron.png")
        self.sprites['chest'] = self._load_sprite(f"{sprite_dir}/environment/chest.png")
        self.sprites['chest_opened'] = self._load_sprite(f"{sprite_dir}/environment/chest_opened.png")
        self.sprites['gold_key'] = self._load_sprite(f"{sprite_dir}/environment/gold_key.png")
        self.sprites['red_key'] = self._load_sprite(f"{sprite_dir}/environment/red_key.png")
        
        # Sprites del perímetro decorativo
        self.sprites['perimeter_021'] = self._load_sprite(f"{sprite_dir}/environment/021.png")  # Lado inferior
        self.sprites['perimeter_023'] = self._load_sprite(f"{sprite_dir}/environment/023.png")  # Lado derecho
        self.sprites['perimeter_024'] = self._load_sprite(f"{sprite_dir}/environment/024.png")  # Lado izquierdo
        self.sprites['perimeter_026'] = self._load_sprite(f"{sprite_dir}/environment/026.png")  # Lado superior
        self.sprites['perimeter_028'] = self._load_sprite(f"{sprite_dir}/environment/028.png")  # Esquina superior izquierda
        self.sprites['perimeter_029'] = self._load_sprite(f"{sprite_dir}/environment/029.png")  # Esquina superior derecha
        self.sprites['perimeter_030'] = self._load_sprite(f"{sprite_dir}/environment/030.png")  # Esquina inferior izquierda
        self.sprites['perimeter_031'] = self._load_sprite(f"{sprite_dir}/environment/031.png")  # Esquina inferior derecha
        
        # Sprites del estanque móvil (3x3)
        self.sprites['pond_020'] = self._load_sprite(f"{sprite_dir}/environment/020.png")  # Esquina superior izquierda
        self.sprites['pond_021'] = self._load_sprite(f"{sprite_dir}/environment/021.png")  # Lado superior
        self.sprites['pond_022'] = self._load_sprite(f"{sprite_dir}/environment/022.png")  # Esquina superior derecha
        self.sprites['pond_023'] = self._load_sprite(f"{sprite_dir}/environment/023.png")  # Lado izquierdo
        self.sprites['pond_019'] = self._load_sprite(f"{sprite_dir}/environment/019.png")  # Agua central
        self.sprites['pond_024'] = self._load_sprite(f"{sprite_dir}/environment/024.png")  # Lado derecho
        self.sprites['pond_025'] = self._load_sprite(f"{sprite_dir}/environment/025.png")  # Esquina inferior izquierda
        self.sprites['pond_026'] = self._load_sprite(f"{sprite_dir}/environment/026.png")  # Lado inferior
        self.sprites['pond_027'] = self._load_sprite(f"{sprite_dir}/environment/027.png")  # Esquina inferior derecha
    
    def _load_sprite(self, path, sprite_key=None):
        """Carga un sprite desde archivo."""
        try:
            if os.path.exists(path):
                sprite = pygame.image.load(path)
                # Escalar sprite según el factor de escalado actual
                from config import SimulationConfig
                scale_factor = SimulationConfig.SPRITE_SCALE_FACTOR
                if scale_factor != 1.0:
                    original_size = sprite.get_size()
                    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                    sprite = pygame.transform.scale(sprite, new_size)
                
                # Almacenar ruta para recarga
                if sprite_key:
                    self.sprite_paths[sprite_key] = path
                
                return sprite
            else:
                print(f"⚠️ Sprite no encontrado: {path}")
                return None
        except Exception as e:
            print(f"❌ Error cargando sprite {path}: {e}")
            return None
    
    def reload_sprites(self):
        """Recarga todos los sprites con el nuevo factor de escalado."""
        print(f"🔄 Recargando sprites con factor {SimulationConfig.SPRITE_SCALE_FACTOR:.2f}x")
        for sprite_key, path in self.sprite_paths.items():
            self.sprites[sprite_key] = self._load_sprite(path, sprite_key)
    
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
        elif sprite_type == 'door':
            return self.sprites.get('door')
        elif sprite_type == 'door_iron':
            return self.sprites.get('door_iron')
        elif sprite_type == 'chest':
            return self.sprites.get('chest')
        elif sprite_type == 'chest_opened':
            return self.sprites.get('chest_opened')
        elif sprite_type == 'gold_key':
            return self.sprites.get('gold_key')
        elif sprite_type == 'red_key':
            return self.sprites.get('red_key')
        elif sprite_type == 'perimeter':
            return self.sprites.get(f'perimeter_{variant}')
        elif sprite_type == 'pond':
            return self.sprites.get(f'pond_{variant}')
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