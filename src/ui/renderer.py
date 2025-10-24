"""
Sistema de renderizado para el ecosistema evolutivo.
Visualiza la simulación usando pygame.
"""

import pygame
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RenderMode(Enum):
    """Modos de renderizado disponibles."""
    NORMAL = "normal"
    DEBUG = "debug"
    HEATMAP = "heatmap"
    CLUSTER = "cluster"


@dataclass
class RenderConfig:
    """Configuración del renderizado."""
    window_size: Tuple[int, int] = (1000, 800)
    fps: int = 60
    show_grid: bool = True
    show_vision: bool = False
    show_metrics: bool = True
    background_color: Tuple[int, int, int] = (50, 50, 50)
    agent_color: Tuple[int, int, int] = (255, 100, 100)
    food_color: Tuple[int, int, int] = (100, 255, 100)
    obstacle_color: Tuple[int, int, int] = (100, 100, 100)
    grid_color: Tuple[int, int, int] = (80, 80, 80)
    text_color: Tuple[int, int, int] = (255, 255, 255)


class SimulationRenderer:
    """Renderizador principal de la simulación."""
    
    def __init__(self, config: RenderConfig):
        """
        Inicializa el renderizador.
        
        Args:
            config: Configuración del renderizado
        """
        self.config = config
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        
        # Estado del renderizado
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.render_mode = RenderMode.NORMAL
        
        # Colores por cluster
        self.cluster_colors = [
            (255, 100, 100),  # Rojo
            (100, 255, 100),  # Verde
            (100, 100, 255),  # Azul
            (255, 255, 100),  # Amarillo
            (255, 100, 255),  # Magenta
            (100, 255, 255),  # Cian
            (255, 150, 100),  # Naranja
            (150, 100, 255),  # Púrpura
        ]
        
        # Inicializar pygame
        self._initialize_pygame()
    
    def _initialize_pygame(self) -> None:
        """Inicializa pygame."""
        pygame.init()
        
        # Crear ventana
        self.screen = pygame.display.set_mode(self.config.window_size)
        pygame.display.set_caption("Ecosistema Evolutivo IA")
        
        # Configurar reloj
        self.clock = pygame.time.Clock()
        
        # Configurar fuentes
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
    
    def render(self, world, agents: List[Any], metrics: Dict[str, Any] = None) -> None:
        """
        Renderiza la simulación.
        
        Args:
            world: Mundo de la simulación
            agents: Lista de agentes
            metrics: Métricas de la simulación
        """
        # Limpiar pantalla
        self.screen.fill(self.config.background_color)
        
        # Renderizar mundo
        self._render_world(world)
        
        # Renderizar agentes
        self._render_agents(agents)
        
        # Renderizar métricas
        if self.config.show_metrics and metrics:
            self._render_metrics(metrics)
        
        # Renderizar información de debug
        if self.render_mode == RenderMode.DEBUG:
            self._render_debug_info(world, agents)
        
        # Actualizar pantalla
        pygame.display.flip()
        self.clock.tick(self.config.fps)
    
    def _render_world(self, world) -> None:
        """
        Renderiza el mundo.
        
        Args:
            world: Mundo a renderizar
        """
        if not world:
            return
        
        # Obtener información del mundo
        world_info = world.get_world_info()
        
        # Renderizar obstáculos
        self._render_obstacles(world)
        
        # Renderizar comida
        self._render_food(world)
        
        # Renderizar grilla
        if self.config.show_grid:
            self._render_grid(world)
    
    def _render_obstacles(self, world) -> None:
        """
        Renderiza obstáculos del mundo.
        
        Args:
            world: Mundo con obstáculos
        """
        # Obtener obstáculos del mundo
        # Asumiendo que el mundo tiene un método para obtener obstáculos
        if hasattr(world, 'physics') and hasattr(world.physics, 'obstacles'):
            for obstacle in world.physics.obstacles:
                x = int(obstacle['x'] * self.zoom - self.camera_x)
                y = int(obstacle['y'] * self.zoom - self.camera_y)
                width = int(obstacle['width'] * self.zoom)
                height = int(obstacle['height'] * self.zoom)
                
                pygame.draw.rect(self.screen, self.config.obstacle_color, 
                               (x, y, width, height))
    
    def _render_food(self, world) -> None:
        """
        Renderiza comida del mundo.
        
        Args:
            world: Mundo con comida
        """
        # Obtener comida del mundo
        if hasattr(world, 'physics') and hasattr(world.physics, 'food_items'):
            for food in world.physics.food_items:
                x = int(food['x'] * self.zoom - self.camera_x)
                y = int(food['y'] * self.zoom - self.camera_y)
                amount = food['amount']
                
                # Tamaño del círculo basado en la cantidad
                radius = max(2, min(8, int(amount * 2)))
                
                pygame.draw.circle(self.screen, self.config.food_color, (x, y), radius)
    
    def _render_grid(self, world) -> None:
        """
        Renderiza la grilla del mundo.
        
        Args:
            world: Mundo con grilla
        """
        if not hasattr(world, 'config'):
            return
        
        # Obtener tamaño del mundo
        world_width = world.config.get('simulation', {}).get('map_size', [100, 100])[0]
        world_height = world.config.get('simulation', {}).get('map_size', [100, 100])[1]
        
        # Calcular espaciado de la grilla
        grid_spacing = 20 * self.zoom
        
        # Líneas verticales
        for x in range(0, world_width, int(grid_spacing)):
            screen_x = int(x * self.zoom - self.camera_x)
            if 0 <= screen_x <= self.config.window_size[0]:
                pygame.draw.line(self.screen, self.config.grid_color, 
                               (screen_x, 0), (screen_x, self.config.window_size[1]))
        
        # Líneas horizontales
        for y in range(0, world_height, int(grid_spacing)):
            screen_y = int(y * self.zoom - self.camera_y)
            if 0 <= screen_y <= self.config.window_size[1]:
                pygame.draw.line(self.screen, self.config.grid_color, 
                               (0, screen_y), (self.config.window_size[0], screen_y))
    
    def _render_agents(self, agents: List[Any]) -> None:
        """
        Renderiza los agentes.
        
        Args:
            agents: Lista de agentes
        """
        for agent in agents:
            if agent.state.value != 'alive':
                continue
            
            # Calcular posición en pantalla
            screen_x = int(agent.x * self.zoom - self.camera_x)
            screen_y = int(agent.y * self.zoom - self.camera_y)
            
            # Verificar si está en pantalla
            if not (0 <= screen_x <= self.config.window_size[0] and 
                    0 <= screen_y <= self.config.window_size[1]):
                continue
            
            # Determinar color del agente
            agent_color = self._get_agent_color(agent)
            
            # Renderizar agente
            radius = max(3, int(5 * self.zoom))
            pygame.draw.circle(self.screen, agent_color, (screen_x, screen_y), radius)
            
            # Renderizar dirección
            if self.render_mode == RenderMode.DEBUG:
                direction_length = 10 * self.zoom
                end_x = screen_x + int(np.cos(agent.angle) * direction_length)
                end_y = screen_y + int(np.sin(agent.angle) * direction_length)
                pygame.draw.line(self.screen, (255, 255, 255), 
                               (screen_x, screen_y), (end_x, end_y), 2)
            
            # Renderizar visión
            if self.config.show_vision:
                self._render_agent_vision(agent, screen_x, screen_y)
            
            # Renderizar información del agente
            if self.render_mode == RenderMode.DEBUG:
                self._render_agent_info(agent, screen_x, screen_y)
    
    def _get_agent_color(self, agent) -> Tuple[int, int, int]:
        """
        Obtiene el color de un agente.
        
        Args:
            agent: Agente a colorear
            
        Returns:
            Color RGB del agente
        """
        # Si hay información de cluster, usar color del cluster
        if hasattr(agent, 'cluster_id') and agent.cluster_id is not None:
            cluster_id = agent.cluster_id % len(self.cluster_colors)
            return self.cluster_colors[cluster_id]
        
        # Color basado en energía
        energy_ratio = agent.energy / 100.0  # Asumiendo energía máxima de 100
        if energy_ratio > 0.8:
            return (100, 255, 100)  # Verde para alta energía
        elif energy_ratio > 0.5:
            return (255, 255, 100)  # Amarillo para energía media
        else:
            return (255, 100, 100)  # Rojo para baja energía
    
    def _render_agent_vision(self, agent, screen_x: int, screen_y: int) -> None:
        """
        Renderiza el campo de visión de un agente.
        
        Args:
            agent: Agente
            screen_x: Posición X en pantalla
            screen_y: Posición Y en pantalla
        """
        if not hasattr(agent, 'sensors'):
            return
        
        # Obtener información de visión
        vision_sensor = getattr(agent.sensors, 'sensors', {}).get('vision')
        if not vision_sensor:
            return
        
        # Renderizar rayos de visión
        vision_range = vision_sensor.vision_range * self.zoom
        for i, ray_angle in enumerate(vision_sensor.ray_angles):
            absolute_angle = agent.angle + ray_angle
            end_x = screen_x + int(np.cos(absolute_angle) * vision_range)
            end_y = screen_y + int(np.sin(absolute_angle) * vision_range)
            
            pygame.draw.line(self.screen, (200, 200, 200), 
                           (screen_x, screen_y), (end_x, end_y), 1)
    
    def _render_agent_info(self, agent, screen_x: int, screen_y: int) -> None:
        """
        Renderiza información de un agente.
        
        Args:
            agent: Agente
            screen_x: Posición X en pantalla
            screen_y: Posición Y en pantalla
        """
        # Información básica
        info_text = f"ID: {agent.id}\nE: {agent.energy:.1f}\nA: {agent.stats.age}"
        
        # Renderizar texto
        lines = info_text.split('\n')
        for i, line in enumerate(lines):
            text_surface = self.small_font.render(line, True, self.config.text_color)
            self.screen.blit(text_surface, (screen_x + 10, screen_y + 10 + i * 15))
    
    def _render_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Renderiza métricas en pantalla.
        
        Args:
            metrics: Diccionario con métricas
        """
        y_offset = 10
        
        # Métricas principales
        main_metrics = [
            f"Tick: {metrics.get('tick', 0)}",
            f"Época: {metrics.get('epoch', 0)}",
            f"Generación: {metrics.get('generation', 0)}",
            f"Agentes: {metrics.get('alive_agents', 0)}",
            f"Fitness: {metrics.get('average_fitness', 0):.3f}",
            f"Energía: {metrics.get('average_energy', 0):.1f}"
        ]
        
        for metric in main_metrics:
            text_surface = self.font.render(metric, True, self.config.text_color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25
    
    def _render_debug_info(self, world, agents: List[Any]) -> None:
        """
        Renderiza información de debug.
        
        Args:
            world: Mundo de la simulación
            agents: Lista de agentes
        """
        # Información de cámara
        camera_info = f"Cámara: ({self.camera_x}, {self.camera_y}) Zoom: {self.zoom:.2f}"
        text_surface = self.small_font.render(camera_info, True, self.config.text_color)
        self.screen.blit(text_surface, (10, self.config.window_size[1] - 50))
        
        # Información del mundo
        if world:
            world_info = world.get_world_info()
            world_text = f"Mundo: {world_info.get('agents', {}).get('total', 0)} agentes"
            text_surface = self.small_font.render(world_text, True, self.config.text_color)
            self.screen.blit(text_surface, (10, self.config.window_size[1] - 30))
    
    def set_camera(self, x: float, y: float) -> None:
        """
        Establece la posición de la cámara.
        
        Args:
            x: Posición X de la cámara
            y: Posición Y de la cámara
        """
        self.camera_x = x
        self.camera_y = y
    
    def set_zoom(self, zoom: float) -> None:
        """
        Establece el nivel de zoom.
        
        Args:
            zoom: Nivel de zoom
        """
        self.zoom = max(0.1, min(5.0, zoom))
    
    def set_render_mode(self, mode: RenderMode) -> None:
        """
        Establece el modo de renderizado.
        
        Args:
            mode: Modo de renderizado
        """
        self.render_mode = mode
    
    def get_screen_coordinates(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """
        Convierte coordenadas del mundo a coordenadas de pantalla.
        
        Args:
            world_x: Posición X en el mundo
            world_y: Posición Y en el mundo
            
        Returns:
            Coordenadas de pantalla
        """
        screen_x = int(world_x * self.zoom - self.camera_x)
        screen_y = int(world_y * self.zoom - self.camera_y)
        return screen_x, screen_y
    
    def get_world_coordinates(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convierte coordenadas de pantalla a coordenadas del mundo.
        
        Args:
            screen_x: Posición X en pantalla
            screen_y: Posición Y en pantalla
            
        Returns:
            Coordenadas del mundo
        """
        world_x = (screen_x + self.camera_x) / self.zoom
        world_y = (screen_y + self.camera_y) / self.zoom
        return world_x, world_y
    
    def handle_events(self) -> List[pygame.event.Event]:
        """
        Maneja eventos de pygame.
        
        Returns:
            Lista de eventos procesados
        """
        events = []
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    events.append(event)
                elif event.key == pygame.K_g:
                    self.config.show_grid = not self.config.show_grid
                elif event.key == pygame.K_v:
                    self.config.show_vision = not self.config.show_vision
                elif event.key == pygame.K_m:
                    self.config.show_metrics = not self.config.show_metrics
                elif event.key == pygame.K_d:
                    if self.render_mode == RenderMode.NORMAL:
                        self.render_mode = RenderMode.DEBUG
                    else:
                        self.render_mode = RenderMode.NORMAL
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom con rueda del mouse
                if event.y > 0:
                    self.set_zoom(self.zoom * 1.1)
                else:
                    self.set_zoom(self.zoom / 1.1)
        
        return events
    
    def cleanup(self) -> None:
        """Limpia recursos del renderizador."""
        if self.screen:
            pygame.quit()
