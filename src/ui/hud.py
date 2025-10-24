"""
Sistema de HUD (Heads-Up Display) para el ecosistema evolutivo.
Muestra información en tiempo real de la simulación.
"""

import pygame
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class HUDMode(Enum):
    """Modos de HUD disponibles."""
    MINIMAL = "minimal"
    DETAILED = "detailed"
    DEBUG = "debug"
    FULL = "full"


@dataclass
class HUDConfig:
    """Configuración del HUD."""
    position: Tuple[int, int] = (10, 10)
    width: int = 300
    height: int = 400
    background_color: Tuple[int, int, int] = (0, 0, 0, 128)  # Negro semi-transparente
    text_color: Tuple[int, int, int] = (255, 255, 255)
    border_color: Tuple[int, int, int] = (100, 100, 100)
    font_size: int = 18
    line_spacing: int = 20
    show_border: bool = True
    show_background: bool = True


class HUD:
    """Sistema de HUD para la simulación."""
    
    def __init__(self, config: HUDConfig):
        """
        Inicializa el HUD.
        
        Args:
            config: Configuración del HUD
        """
        self.config = config
        self.mode = HUDMode.DETAILED
        self.font = pygame.font.Font(None, config.font_size)
        self.small_font = pygame.font.Font(None, config.font_size - 4)
        self.large_font = pygame.font.Font(None, config.font_size + 8)
        
        # Datos del HUD
        self.simulation_data = {}
        self.agent_data = {}
        self.world_data = {}
        self.performance_data = {}
    
    def update_data(self, simulation_data: Dict[str, Any], 
                   agent_data: Dict[str, Any] = None,
                   world_data: Dict[str, Any] = None,
                   performance_data: Dict[str, Any] = None) -> None:
        """
        Actualiza los datos del HUD.
        
        Args:
            simulation_data: Datos de la simulación
            agent_data: Datos de los agentes
            world_data: Datos del mundo
            performance_data: Datos de rendimiento
        """
        self.simulation_data = simulation_data
        self.agent_data = agent_data or {}
        self.world_data = world_data or {}
        self.performance_data = performance_data or {}
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Renderiza el HUD.
        
        Args:
            screen: Superficie de pygame
        """
        if self.mode == HUDMode.MINIMAL:
            self._render_minimal(screen)
        elif self.mode == HUDMode.DETAILED:
            self._render_detailed(screen)
        elif self.mode == HUDMode.DEBUG:
            self._render_debug(screen)
        elif self.mode == HUDMode.FULL:
            self._render_full(screen)
    
    def _render_minimal(self, screen: pygame.Surface) -> None:
        """
        Renderiza HUD mínimo.
        
        Args:
            screen: Superficie de pygame
        """
        x, y = self.config.position
        lines = [
            f"Tick: {self.simulation_data.get('tick', 0)}",
            f"Agentes: {self.simulation_data.get('alive_agents', 0)}",
            f"Fitness: {self.simulation_data.get('average_fitness', 0):.3f}"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            screen.blit(text_surface, (x, y + i * self.config.line_spacing))
    
    def _render_detailed(self, screen: pygame.Surface) -> None:
        """
        Renderiza HUD detallado.
        
        Args:
            screen: Superficie de pygame
        """
        x, y = self.config.position
        
        # Crear superficie para el HUD
        hud_surface = pygame.Surface((self.config.width, self.config.height))
        hud_surface.set_alpha(128)
        
        if self.config.show_background:
            hud_surface.fill(self.config.background_color)
        
        if self.config.show_border:
            pygame.draw.rect(hud_surface, self.config.border_color, 
                           (0, 0, self.config.width, self.config.height), 2)
        
        # Renderizar contenido
        self._render_simulation_info(hud_surface, 10, 10)
        self._render_agent_info(hud_surface, 10, 120)
        self._render_world_info(hud_surface, 10, 220)
        
        # Blit a la pantalla principal
        screen.blit(hud_surface, (x, y))
    
    def _render_debug(self, screen: pygame.Surface) -> None:
        """
        Renderiza HUD de debug.
        
        Args:
            screen: Superficie de pygame
        """
        x, y = self.config.position
        
        # Información de debug
        debug_lines = [
            f"DEBUG MODE",
            f"Tick: {self.simulation_data.get('tick', 0)}",
            f"Época: {self.simulation_data.get('epoch', 0)}",
            f"Generación: {self.simulation_data.get('generation', 0)}",
            f"Agentes vivos: {self.simulation_data.get('alive_agents', 0)}",
            f"Agentes muertos: {self.simulation_data.get('dead_agents', 0)}",
            f"Fitness promedio: {self.simulation_data.get('average_fitness', 0):.4f}",
            f"Fitness mejor: {self.simulation_data.get('best_fitness', 0):.4f}",
            f"Energía promedio: {self.simulation_data.get('average_energy', 0):.2f}",
            f"Edad promedio: {self.simulation_data.get('average_age', 0):.1f}",
            f"Distancia total: {self.simulation_data.get('total_distance', 0):.1f}",
            f"Comida total: {self.simulation_data.get('total_food', 0)}",
            f"Colisiones total: {self.simulation_data.get('total_collisions', 0)}",
            f"Descendientes total: {self.simulation_data.get('total_offspring', 0)}"
        ]
        
        for i, line in enumerate(debug_lines):
            color = (255, 255, 0) if i == 0 else self.config.text_color
            text_surface = self.font.render(line, True, color)
            screen.blit(text_surface, (x, y + i * self.config.line_spacing))
    
    def _render_full(self, screen: pygame.Surface) -> None:
        """
        Renderiza HUD completo.
        
        Args:
            screen: Superficie de pygame
        """
        x, y = self.config.position
        
        # Crear superficie más grande
        full_width = self.config.width + 200
        full_height = self.config.height + 200
        hud_surface = pygame.Surface((full_width, full_height))
        hud_surface.set_alpha(128)
        
        if self.config.show_background:
            hud_surface.fill(self.config.background_color)
        
        if self.config.show_border:
            pygame.draw.rect(hud_surface, self.config.border_color, 
                           (0, 0, full_width, full_height), 2)
        
        # Renderizar todas las secciones
        self._render_simulation_info(hud_surface, 10, 10)
        self._render_agent_info(hud_surface, 10, 120)
        self._render_world_info(hud_surface, 10, 220)
        self._render_performance_info(hud_surface, 10, 320)
        self._render_evolution_info(hud_surface, 10, 420)
        
        # Blit a la pantalla principal
        screen.blit(hud_surface, (x, y))
    
    def _render_simulation_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Renderiza información de la simulación.
        
        Args:
            surface: Superficie de pygame
            x: Posición X
            y: Posición Y
        """
        title = self.large_font.render("SIMULACIÓN", True, self.config.text_color)
        surface.blit(title, (x, y))
        
        lines = [
            f"Tick: {self.simulation_data.get('tick', 0)}",
            f"Época: {self.simulation_data.get('epoch', 0)}",
            f"Generación: {self.simulation_data.get('generation', 0)}",
            f"Tiempo: {self.simulation_data.get('simulation_time', 0):.1f}s"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            surface.blit(text_surface, (x, y + 30 + i * self.config.line_spacing))
    
    def _render_agent_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Renderiza información de los agentes.
        
        Args:
            surface: Superficie de pygame
            x: Posición X
            y: Posición Y
        """
        title = self.large_font.render("AGENTES", True, self.config.text_color)
        surface.blit(title, (x, y))
        
        lines = [
            f"Vivos: {self.simulation_data.get('alive_agents', 0)}",
            f"Muertos: {self.simulation_data.get('dead_agents', 0)}",
            f"Fitness promedio: {self.simulation_data.get('average_fitness', 0):.3f}",
            f"Fitness mejor: {self.simulation_data.get('best_fitness', 0):.3f}",
            f"Energía promedio: {self.simulation_data.get('average_energy', 0):.1f}",
            f"Edad promedio: {self.simulation_data.get('average_age', 0):.1f}"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            surface.blit(text_surface, (x, y + 30 + i * self.config.line_spacing))
    
    def _render_world_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Renderiza información del mundo.
        
        Args:
            surface: Superficie de pygame
            x: Posición X
            y: Posición Y
        """
        title = self.large_font.render("MUNDO", True, self.config.text_color)
        surface.blit(title, (x, y))
        
        lines = [
            f"Comida: {self.simulation_data.get('total_food', 0)}",
            f"Obstáculos: {self.simulation_data.get('total_obstacles', 0)}",
            f"Distancia total: {self.simulation_data.get('total_distance', 0):.1f}",
            f"Colisiones: {self.simulation_data.get('total_collisions', 0)}",
            f"Descendientes: {self.simulation_data.get('total_offspring', 0)}"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            surface.blit(text_surface, (x, y + 30 + i * self.config.line_spacing))
    
    def _render_performance_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Renderiza información de rendimiento.
        
        Args:
            surface: Superficie de pygame
            x: Posición X
            y: Posición Y
        """
        title = self.large_font.render("RENDIMIENTO", True, self.config.text_color)
        surface.blit(title, (x, y))
        
        lines = [
            f"FPS: {self.performance_data.get('fps', 0):.1f}",
            f"Tiempo de tick: {self.performance_data.get('tick_time', 0):.3f}ms",
            f"Memoria: {self.performance_data.get('memory_usage', 0):.1f}MB",
            f"CPU: {self.performance_data.get('cpu_usage', 0):.1f}%"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            surface.blit(text_surface, (x, y + 30 + i * self.config.line_spacing))
    
    def _render_evolution_info(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Renderiza información de evolución.
        
        Args:
            surface: Superficie de pygame
            x: Posición X
            y: Posición Y
        """
        title = self.large_font.render("EVOLUCIÓN", True, self.config.text_color)
        surface.blit(title, (x, y))
        
        lines = [
            f"Diversidad: {self.simulation_data.get('diversity', 0):.3f}",
            f"Convergencia: {self.simulation_data.get('convergence', 0):.3f}",
            f"Tendencia fitness: {self.simulation_data.get('fitness_trend', 0):.3f}",
            f"Clusters: {self.simulation_data.get('n_clusters', 0)}"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.config.text_color)
            surface.blit(text_surface, (x, y + 30 + i * self.config.line_spacing))
    
    def set_mode(self, mode: HUDMode) -> None:
        """
        Establece el modo del HUD.
        
        Args:
            mode: Modo del HUD
        """
        self.mode = mode
    
    def toggle_mode(self) -> None:
        """Alterna entre modos del HUD."""
        modes = list(HUDMode)
        current_index = modes.index(self.mode)
        next_index = (current_index + 1) % len(modes)
        self.mode = modes[next_index]
    
    def get_mode(self) -> HUDMode:
        """
        Obtiene el modo actual del HUD.
        
        Returns:
            Modo actual del HUD
        """
        return self.mode
