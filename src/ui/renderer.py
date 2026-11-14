"""
Sistema de renderizado con sprites y partículas.
"""

import pygame
import os
import random
import numpy as np

from config import SimulationConfig


class SpriteManager:
    """Gestor de sprites del juego."""
    
    def __init__(self):
        self.sprites = {}
        self.sprite_paths = {}  # Almacenar rutas para recarga
        self.scaled_sprites_cache = {}  # Cache de sprites escalados (clave: sprite_key_size)
        self._load_sprites()

    def _make_white_transparent(self, surface, tolerance=40):
        """Convierte en transparente los píxeles casi blancos (para eliminar halos).
        tolerance: 0-255, mayor = más agresivo.
        """
        if surface is None:
            return surface
        surface = surface.convert_alpha()
        width, height = surface.get_size()
        for x in range(width):
            for y in range(height):
                r, g, b, a = surface.get_at((x, y))
                if a == 0:
                    continue
                # Condición de casi blanco (alto brillo y poca saturación)
                if r > 255 - tolerance and g > 255 - tolerance and b > 255 - tolerance:
                    surface.set_at((x, y), (r, g, b, 0))
        return surface
    
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
        self.sprites['grave'] = self._load_sprite(f"{sprite_dir}/environment/grave.png")
        
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
                sprite = pygame.image.load(path).convert_alpha()
                # Escalar sprite según el factor de escalado actual
                scale_factor = SimulationConfig.SPRITE_SCALE_FACTOR
                if scale_factor != 1.0:
                    original_size = sprite.get_size()
                    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                    sprite = pygame.transform.scale(sprite, new_size)
                
                # Limpiar fondo casi blanco en la tumba
                if 'grave' in path.lower():
                    sprite = self._make_white_transparent(sprite, tolerance=60)
                
                # Almacenar ruta para recarga
                if sprite_key:
                    self.sprite_paths[sprite_key] = path
                
                return sprite
            else:
                print(f"⚠️ Sprite no encontrado: {path}")
                return None
        except Exception:
            #print(f"❌ Error cargando sprite {path}: {e}")
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
    
    def get_scaled_agent_sprite(self, angle=0, tick=0, moving=False, size=(16, 16)):
        """Obtiene sprite del agente escalado con cache para mejor rendimiento."""
        # Obtener sprite base (sin escalar)
        base_sprite = self.get_agent_sprite(angle, tick, moving)
        if not base_sprite:
            return None
        
        # Crear clave de cache: sprite_key + tamaño
        direction = 'right' if -np.pi/4 <= angle <= np.pi/4 else \
                  'down' if np.pi/4 < angle <= 3*np.pi/4 else \
                  'left' if 3*np.pi/4 < angle <= 5*np.pi/4 else 'up'
        frame = 1 if (tick // 8) % 2 == 0 else 2 if moving else 1
        sprite_key = f'agent_{direction}_{frame}'
        cache_key = f"{sprite_key}_{size[0]}x{size[1]}"
        
        # Verificar cache
        if cache_key in self.scaled_sprites_cache:
            return self.scaled_sprites_cache[cache_key]
        
        # Escalar y guardar en cache
        scaled_sprite = pygame.transform.scale(base_sprite, size)
        self.scaled_sprites_cache[cache_key] = scaled_sprite
        return scaled_sprite
    
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
        elif sprite_type == 'grave':
            return self.sprites.get('grave')
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
        # Generador propio: el dibujo (que solo corre con ventana) no consume el azar de la
        # simulación, así la misma semilla da lo mismo con ventana y sin ella
        self.rng = random.Random()
    
    def add_death_effect(self, x, y):
        """Agrega efecto de muerte."""
        for _ in range(5):
            particle = {
                'x': x + self.rng.randint(-10, 10),
                'y': y + self.rng.randint(-10, 10),
                'vx': self.rng.uniform(-2, 2),
                'vy': self.rng.uniform(-2, 2),
                'life': 30,
                'color': (255, 0, 0)
            }
            self.particles.append(particle)
    
    def add_food_effect(self, x, y):
        """Agrega efecto de comer comida."""
        for _ in range(3):
            particle = {
                'x': x + self.rng.randint(-5, 5),
                'y': y + self.rng.randint(-5, 5),
                'vx': self.rng.uniform(-1, 1),
                'vy': self.rng.uniform(-1, 1),
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


def dibujar_mundo(surface, world, sprite_manager, tick):
    """Dibuja el mundo: fondo, pasto, obstáculos, perímetro, estanque, hacha, comida, puertas, cofre
    y llaves. Lo usan el loop de main.py y la pantalla final; los agentes, las tumbas, las
    partículas y los paneles los dibuja cada uno."""
    surface.fill((40, 40, 60))  # Fondo azul oscuro

    # Pasto en el área de juego (1200 de ancho menos los 240 del panel), en damero de dos variantes
    for x in range(0, 960, 16):
        for y in range(0, 800, 16):
            variante = 1 if (x // 16 + y // 16) % 2 == 0 else 2
            surface.blit(sprite_manager.get_environment_sprite('grass', variante), (x, y))

    for obstacle in world.obstacles:
        obstacle.draw(surface, sprite_manager, tick)
    for perimeter_obj in world.perimeter_obstacles:  # Perímetro decorativo
        perimeter_obj.draw(surface, sprite_manager)
    for pond_obj in world.pond_obstacles:  # Estanque móvil
        pond_obj.draw(surface, sprite_manager, tick)

    # Hacha, si nadie la agarró
    if SimulationConfig.TREE_CUTTING_ENABLED and world.axe and not world.axe['picked_up']:
        axe_sprite = sprite_manager.get_environment_sprite('axe')
        if axe_sprite:
            x, y = world.axe['x'], world.axe['y']
            _dibujar_con_halo(surface, axe_sprite, x, y, (255, 255), tick,
                              lambda: surface.blit(axe_sprite, (x - 10, y - 10)))

    # Manzanas
    apple_sprite = sprite_manager.get_environment_sprite('apple')
    for food in world.food_items:
        if not food['eaten']:
            surface.blit(apple_sprite, (int(food['x'] - 8), int(food['y'] - 8)))

    # Fortalezas: puertas (encima de los muros), cofre y llaves
    if SimulationConfig.FORTRESSES_ENABLED:
        if world.door:
            world.door.draw(surface, sprite_manager, tick)
        if world.door_iron:
            world.door_iron.draw(surface, sprite_manager, tick)
        if world.chest:
            world.chest.draw(surface, sprite_manager, tick)
        if world.red_key and not world.red_key.collected:
            red_key_sprite = sprite_manager.get_environment_sprite('red_key')
            if red_key_sprite:
                _dibujar_con_halo(surface, red_key_sprite, world.red_key.x, world.red_key.y, (255, 100), tick,
                                  lambda: world.red_key.draw(surface, sprite_manager, tick))
            else:
                world.red_key.draw(surface, sprite_manager, tick)
        if world.gold_key and not world.gold_key.collected:
            world.gold_key.draw(surface, sprite_manager, tick)


def _dibujar_con_halo(surface, sprite, x, y, rojo_verde, tick, dibujar_objeto):
    """Halo pulsante, el objeto (lo dibuja dibujar_objeto) y un brillo suave encima: el hacha y la
    llave roja. El azul del color pulsa con el tick."""
    intensidad = int(50 + 30 * abs(pygame.math.Vector2(1, 1).length() * 0.1 * tick % 1 - 0.5))
    color = (*rojo_verde, 100 + intensidad)
    for i in range(3):
        radio = 15 + i * 5
        halo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*color, 30 - i * 8), (radio, radio), radio)
        surface.blit(halo, (x - radio, y - radio))
    dibujar_objeto()
    brillo = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    brillo.fill((*color, 30))
    brillo.blit(sprite, (0, 0), special_flags=pygame.BLEND_ADD)
    surface.blit(brillo, (x - 10, y - 10))