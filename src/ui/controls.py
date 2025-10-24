"""
Sistema de controles para el ecosistema evolutivo.
Maneja entrada del usuario y controles de la simulación.
"""

import pygame
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ControlAction(Enum):
    """Acciones de control disponibles."""
    PAUSE = "pause"
    RESUME = "resume"
    RESET = "reset"
    SPEED_UP = "speed_up"
    SLOW_DOWN = "slow_down"
    TOGGLE_GRID = "toggle_grid"
    TOGGLE_VISION = "toggle_vision"
    TOGGLE_METRICS = "toggle_metrics"
    TOGGLE_DEBUG = "toggle_debug"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    CAMERA_UP = "camera_up"
    CAMERA_DOWN = "camera_down"
    CAMERA_LEFT = "camera_left"
    CAMERA_RIGHT = "camera_right"
    SAVE_STATE = "save_state"
    LOAD_STATE = "load_state"
    EXPORT_DATA = "export_data"
    QUIT = "quit"


@dataclass
class ControlConfig:
    """Configuración de controles."""
    # Teclas de control
    pause_key: int = pygame.K_SPACE
    reset_key: int = pygame.K_r
    speed_up_key: int = pygame.K_PLUS
    slow_down_key: int = pygame.K_MINUS
    grid_key: int = pygame.K_g
    vision_key: int = pygame.K_v
    metrics_key: int = pygame.K_m
    debug_key: int = pygame.K_d
    save_key: int = pygame.K_s
    load_key: int = pygame.K_l
    export_key: int = pygame.K_e
    quit_key: int = pygame.K_ESCAPE
    
    # Teclas de cámara
    camera_up_key: int = pygame.K_UP
    camera_down_key: int = pygame.K_DOWN
    camera_left_key: int = pygame.K_LEFT
    camera_right_key: int = pygame.K_RIGHT
    zoom_in_key: int = pygame.K_EQUALS
    zoom_out_key: int = pygame.K_0
    
    # Configuración de movimiento
    camera_speed: float = 5.0
    zoom_speed: float = 0.1
    speed_multiplier: float = 0.1


class SimulationControls:
    """Sistema de controles de la simulación."""
    
    def __init__(self, config: ControlConfig):
        """
        Inicializa el sistema de controles.
        
        Args:
            config: Configuración de controles
        """
        self.config = config
        self.callbacks = {}
        self.pressed_keys = set()
        self.key_repeat_delay = 0.1  # Segundos
        self.last_key_time = {}
        
        # Estado de controles
        self.is_paused = False
        self.speed_multiplier = 1.0
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
        
        # Configurar callbacks por defecto
        self._setup_default_callbacks()
    
    def _setup_default_callbacks(self) -> None:
        """Configura callbacks por defecto."""
        self.callbacks[ControlAction.PAUSE] = self._toggle_pause
        self.callbacks[ControlAction.RESET] = self._reset_simulation
        self.callbacks[ControlAction.SPEED_UP] = self._speed_up
        self.callbacks[ControlAction.SLOW_DOWN] = self._slow_down
        self.callbacks[ControlAction.TOGGLE_GRID] = self._toggle_grid
        self.callbacks[ControlAction.TOGGLE_VISION] = self._toggle_vision
        self.callbacks[ControlAction.TOGGLE_METRICS] = self._toggle_metrics
        self.callbacks[ControlAction.TOGGLE_DEBUG] = self._toggle_debug
        self.callbacks[ControlAction.ZOOM_IN] = self._zoom_in
        self.callbacks[ControlAction.ZOOM_OUT] = self._zoom_out
        self.callbacks[ControlAction.CAMERA_UP] = self._camera_up
        self.callbacks[ControlAction.CAMERA_DOWN] = self._camera_down
        self.callbacks[ControlAction.CAMERA_LEFT] = self._camera_left
        self.callbacks[ControlAction.CAMERA_RIGHT] = self._camera_right
        self.callbacks[ControlAction.SAVE_STATE] = self._save_state
        self.callbacks[ControlAction.LOAD_STATE] = self._load_state
        self.callbacks[ControlAction.EXPORT_DATA] = self._export_data
        self.callbacks[ControlAction.QUIT] = self._quit_simulation
    
    def register_callback(self, action: ControlAction, callback: Callable) -> None:
        """
        Registra un callback para una acción.
        
        Args:
            action: Acción de control
            callback: Función callback
        """
        self.callbacks[action] = callback
    
    def handle_events(self, events: List[pygame.event.Event]) -> List[ControlAction]:
        """
        Maneja eventos de pygame.
        
        Args:
            events: Lista de eventos de pygame
            
        Returns:
            Lista de acciones ejecutadas
        """
        actions = []
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                action = self._handle_keydown(event.key)
                if action:
                    actions.append(action)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = self._handle_mouse_click(event)
                if action:
                    actions.append(action)
            elif event.type == pygame.MOUSEWHEEL:
                action = self._handle_mouse_wheel(event)
                if action:
                    actions.append(action)
        
        # Manejar teclas presionadas continuamente
        actions.extend(self._handle_continuous_keys())
        
        return actions
    
    def _handle_keydown(self, key: int) -> Optional[ControlAction]:
        """
        Maneja teclas presionadas.
        
        Args:
            key: Código de tecla
            
        Returns:
            Acción ejecutada
        """
        self.pressed_keys.add(key)
        
        # Mapear teclas a acciones
        key_mapping = {
            self.config.pause_key: ControlAction.PAUSE,
            self.config.reset_key: ControlAction.RESET,
            self.config.speed_up_key: ControlAction.SPEED_UP,
            self.config.slow_down_key: ControlAction.SLOW_DOWN,
            self.config.grid_key: ControlAction.TOGGLE_GRID,
            self.config.vision_key: ControlAction.TOGGLE_VISION,
            self.config.metrics_key: ControlAction.TOGGLE_METRICS,
            self.config.debug_key: ControlAction.TOGGLE_DEBUG,
            self.config.save_key: ControlAction.SAVE_STATE,
            self.config.load_key: ControlAction.LOAD_STATE,
            self.config.export_key: ControlAction.EXPORT_DATA,
            self.config.quit_key: ControlAction.QUIT,
            self.config.camera_up_key: ControlAction.CAMERA_UP,
            self.config.camera_down_key: ControlAction.CAMERA_DOWN,
            self.config.camera_left_key: ControlAction.CAMERA_LEFT,
            self.config.camera_right_key: ControlAction.CAMERA_RIGHT,
            self.config.zoom_in_key: ControlAction.ZOOM_IN,
            self.config.zoom_out_key: ControlAction.ZOOM_OUT
        }
        
        action = key_mapping.get(key)
        if action:
            self._execute_action(action)
            return action
        
        return None
    
    def _handle_keyup(self, key: int) -> None:
        """
        Maneja teclas liberadas.
        
        Args:
            key: Código de tecla
        """
        self.pressed_keys.discard(key)
    
    def _handle_mouse_click(self, event: pygame.event.Event) -> Optional[ControlAction]:
        """
        Maneja clics del mouse.
        
        Args:
            event: Evento del mouse
            
        Returns:
            Acción ejecutada
        """
        if event.button == 1:  # Clic izquierdo
            # Implementar lógica de selección de agente
            pass
        elif event.button == 3:  # Clic derecho
            # Implementar lógica de menú contextual
            pass
        
        return None
    
    def _handle_mouse_wheel(self, event: pygame.event.Event) -> Optional[ControlAction]:
        """
        Maneja rueda del mouse.
        
        Args:
            event: Evento del mouse
            
        Returns:
            Acción ejecutada
        """
        if event.y > 0:
            return self._execute_action(ControlAction.ZOOM_IN)
        else:
            return self._execute_action(ControlAction.ZOOM_OUT)
    
    def _handle_continuous_keys(self) -> List[ControlAction]:
        """
        Maneja teclas presionadas continuamente.
        
        Returns:
            Lista de acciones ejecutadas
        """
        actions = []
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Teclas de cámara
        camera_actions = {
            self.config.camera_up_key: ControlAction.CAMERA_UP,
            self.config.camera_down_key: ControlAction.CAMERA_DOWN,
            self.config.camera_left_key: ControlAction.CAMERA_LEFT,
            self.config.camera_right_key: ControlAction.CAMERA_RIGHT
        }
        
        for key, action in camera_actions.items():
            if key in self.pressed_keys:
                # Verificar delay de repetición
                if (action not in self.last_key_time or 
                    current_time - self.last_key_time[action] > self.key_repeat_delay):
                    self._execute_action(action)
                    self.last_key_time[action] = current_time
                    actions.append(action)
        
        return actions
    
    def _execute_action(self, action: ControlAction) -> None:
        """
        Ejecuta una acción de control.
        
        Args:
            action: Acción a ejecutar
        """
        if action in self.callbacks:
            self.callbacks[action]()
    
    # Callbacks por defecto
    def _toggle_pause(self) -> None:
        """Alterna pausa de la simulación."""
        self.is_paused = not self.is_paused
        print(f"Simulación {'pausada' if self.is_paused else 'reanudada'}")
    
    def _reset_simulation(self) -> None:
        """Reinicia la simulación."""
        print("Reiniciando simulación...")
        # Implementar lógica de reinicio
    
    def _speed_up(self) -> None:
        """Aumenta la velocidad de la simulación."""
        self.speed_multiplier = min(5.0, self.speed_multiplier + self.config.speed_multiplier)
        print(f"Velocidad: {self.speed_multiplier:.1f}x")
    
    def _slow_down(self) -> None:
        """Reduce la velocidad de la simulación."""
        self.speed_multiplier = max(0.1, self.speed_multiplier - self.config.speed_multiplier)
        print(f"Velocidad: {self.speed_multiplier:.1f}x")
    
    def _toggle_grid(self) -> None:
        """Alterna visualización de grilla."""
        print("Grilla alternada")
    
    def _toggle_vision(self) -> None:
        """Alterna visualización de visión."""
        print("Visión alternada")
    
    def _toggle_metrics(self) -> None:
        """Alterna visualización de métricas."""
        print("Métricas alternadas")
    
    def _toggle_debug(self) -> None:
        """Alterna modo debug."""
        print("Modo debug alternado")
    
    def _zoom_in(self) -> None:
        """Aumenta el zoom."""
        self.zoom = min(5.0, self.zoom + self.config.zoom_speed)
        print(f"Zoom: {self.zoom:.2f}")
    
    def _zoom_out(self) -> None:
        """Reduce el zoom."""
        self.zoom = max(0.1, self.zoom - self.config.zoom_speed)
        print(f"Zoom: {self.zoom:.2f}")
    
    def _camera_up(self) -> None:
        """Mueve la cámara hacia arriba."""
        self.camera_y -= self.config.camera_speed
        print(f"Cámara: ({self.camera_x:.1f}, {self.camera_y:.1f})")
    
    def _camera_down(self) -> None:
        """Mueve la cámara hacia abajo."""
        self.camera_y += self.config.camera_speed
        print(f"Cámara: ({self.camera_x:.1f}, {self.camera_y:.1f})")
    
    def _camera_left(self) -> None:
        """Mueve la cámara hacia la izquierda."""
        self.camera_x -= self.config.camera_speed
        print(f"Cámara: ({self.camera_x:.1f}, {self.camera_y:.1f})")
    
    def _camera_right(self) -> None:
        """Mueve la cámara hacia la derecha."""
        self.camera_x += self.config.camera_speed
        print(f"Cámara: ({self.camera_x:.1f}, {self.camera_y:.1f})")
    
    def _save_state(self) -> None:
        """Guarda el estado de la simulación."""
        print("Guardando estado...")
        # Implementar lógica de guardado
    
    def _load_state(self) -> None:
        """Carga el estado de la simulación."""
        print("Cargando estado...")
        # Implementar lógica de carga
    
    def _export_data(self) -> None:
        """Exporta datos de la simulación."""
        print("Exportando datos...")
        # Implementar lógica de exportación
    
    def _quit_simulation(self) -> None:
        """Sale de la simulación."""
        print("Saliendo de la simulación...")
        # Implementar lógica de salida
    
    def get_camera_position(self) -> tuple:
        """
        Obtiene la posición de la cámara.
        
        Returns:
            Tupla (x, y) con la posición de la cámara
        """
        return (self.camera_x, self.camera_y)
    
    def get_zoom(self) -> float:
        """
        Obtiene el nivel de zoom.
        
        Returns:
            Nivel de zoom
        """
        return self.zoom
    
    def get_speed_multiplier(self) -> float:
        """
        Obtiene el multiplicador de velocidad.
        
        Returns:
            Multiplicador de velocidad
        """
        return self.speed_multiplier
    
    def is_simulation_paused(self) -> bool:
        """
        Verifica si la simulación está pausada.
        
        Returns:
            True si está pausada
        """
        return self.is_paused
    
    def set_camera_position(self, x: float, y: float) -> None:
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
    
    def set_speed_multiplier(self, speed: float) -> None:
        """
        Establece el multiplicador de velocidad.
        
        Args:
            speed: Multiplicador de velocidad
        """
        self.speed_multiplier = max(0.1, min(5.0, speed))
    
    def get_control_info(self) -> Dict[str, Any]:
        """
        Obtiene información de los controles.
        
        Returns:
            Diccionario con información de controles
        """
        return {
            'is_paused': self.is_paused,
            'speed_multiplier': self.speed_multiplier,
            'camera_position': (self.camera_x, self.camera_y),
            'zoom': self.zoom,
            'pressed_keys': list(self.pressed_keys)
        }
