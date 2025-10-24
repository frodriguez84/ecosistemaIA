"""
Controlador de tiempo para el ecosistema evolutivo.
Maneja ticks, épocas y duración de la simulación.
"""

import time
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class TimeConfig:
    """Configuración de tiempo para la simulación."""
    ticks_per_epoch: int = 2000
    max_epochs: int = 200
    tick_duration_ms: float = 16.67  # ~60 FPS
    epoch_timeout_seconds: Optional[float] = None


class TimeKeeper:
    """Controlador de tiempo de la simulación."""
    
    def __init__(self, config: TimeConfig):
        """
        Inicializa el controlador de tiempo.
        
        Args:
            config: Configuración de tiempo
        """
        self.config = config
        self.current_tick = 0
        self.current_epoch = 0
        self.start_time = None
        self.epoch_start_time = None
        self.tick_start_time = None
        
        # Callbacks
        self.on_tick_start: Optional[Callable] = None
        self.on_tick_end: Optional[Callable] = None
        self.on_epoch_start: Optional[Callable] = None
        self.on_epoch_end: Optional[Callable] = None
    
    def start_simulation(self) -> None:
        """Inicia la simulación."""
        self.start_time = time.time()
        self.current_tick = 0
        self.current_epoch = 0
        self._start_epoch()
    
    def _start_epoch(self) -> None:
        """Inicia una nueva época."""
        self.epoch_start_time = time.time()
        self.current_tick = 0
        
        if self.on_epoch_start:
            self.on_epoch_start(self.current_epoch)
    
    def _end_epoch(self) -> bool:
        """
        Finaliza la época actual.
        
        Returns:
            True si la simulación debe continuar, False si debe terminar
        """
        if self.on_epoch_end:
            self.on_epoch_end(self.current_epoch)
        
        self.current_epoch += 1
        
        # Verificar si hemos alcanzado el máximo de épocas
        if self.current_epoch >= self.config.max_epochs:
            return False
        
        # Verificar timeout de época si está configurado
        if self.config.epoch_timeout_seconds:
            epoch_duration = time.time() - self.epoch_start_time
            if epoch_duration > self.config.epoch_timeout_seconds:
                return False
        
        self._start_epoch()
        return True
    
    def start_tick(self) -> bool:
        """
        Inicia un nuevo tick.
        
        Returns:
            True si el tick puede continuar, False si la época debe terminar
        """
        # Verificar si hemos alcanzado el máximo de ticks por época
        if self.current_tick >= self.config.ticks_per_epoch:
            return self._end_epoch()
        
        self.tick_start_time = time.time()
        self.current_tick += 1
        
        if self.on_tick_start:
            self.on_tick_start(self.current_tick, self.current_epoch)
        
        return True
    
    def end_tick(self) -> None:
        """Finaliza el tick actual."""
        if self.on_tick_end:
            self.on_tick_end(self.current_tick, self.current_epoch)
        
        # Control de velocidad (si está habilitado)
        if self.config.tick_duration_ms > 0:
            self._wait_for_tick_duration()
    
    def _wait_for_tick_duration(self) -> None:
        """Espera el tiempo necesario para mantener la velocidad de tick."""
        if self.tick_start_time is None:
            return
        
        elapsed = time.time() - self.tick_start_time
        target_duration = self.config.tick_duration_ms / 1000.0
        
        if elapsed < target_duration:
            time.sleep(target_duration - elapsed)
    
    def get_simulation_time(self) -> float:
        """
        Obtiene el tiempo total de simulación en segundos.
        
        Returns:
            Tiempo transcurrido desde el inicio
        """
        if self.start_time is None:
            return 0.0
        
        return time.time() - self.start_time
    
    def get_epoch_time(self) -> float:
        """
        Obtiene el tiempo transcurrido en la época actual.
        
        Returns:
            Tiempo transcurrido en la época actual
        """
        if self.epoch_start_time is None:
            return 0.0
        
        return time.time() - self.epoch_start_time
    
    def get_tick_time(self) -> float:
        """
        Obtiene el tiempo transcurrido en el tick actual.
        
        Returns:
            Tiempo transcurrido en el tick actual
        """
        if self.tick_start_time is None:
            return 0.0
        
        return time.time() - self.tick_start_time
    
    def get_progress(self) -> dict:
        """
        Obtiene el progreso actual de la simulación.
        
        Returns:
            Diccionario con información de progreso
        """
        total_ticks = self.config.max_epochs * self.config.ticks_per_epoch
        current_total_ticks = (self.current_epoch * self.config.ticks_per_epoch) + self.current_tick
        
        return {
            'current_epoch': self.current_epoch,
            'current_tick': self.current_tick,
            'max_epochs': self.config.max_epochs,
            'ticks_per_epoch': self.config.ticks_per_epoch,
            'epoch_progress': self.current_tick / self.config.ticks_per_epoch,
            'simulation_progress': current_total_ticks / total_ticks,
            'simulation_time': self.get_simulation_time(),
            'epoch_time': self.get_epoch_time(),
            'tick_time': self.get_tick_time()
        }
    
    def is_simulation_complete(self) -> bool:
        """
        Verifica si la simulación ha terminado.
        
        Returns:
            True si la simulación ha terminado
        """
        return self.current_epoch >= self.config.max_epochs
    
    def reset(self) -> None:
        """Reinicia el controlador de tiempo."""
        self.current_tick = 0
        self.current_epoch = 0
        self.start_time = None
        self.epoch_start_time = None
        self.tick_start_time = None
