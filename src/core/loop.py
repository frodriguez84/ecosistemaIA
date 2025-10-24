"""
Loop principal de simulación del ecosistema evolutivo.
Coordina todos los componentes del sistema.
"""

import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from .events import EventManager, EventType, emit_event
from .timekeeper import TimeKeeper, TimeConfig


@dataclass
class SimulationState:
    """Estado actual de la simulación."""
    is_running: bool = False
    is_paused: bool = False
    current_generation: int = 0
    total_agents: int = 0
    alive_agents: int = 0
    average_fitness: float = 0.0
    best_fitness: float = 0.0


class SimulationLoop:
    """Loop principal de la simulación."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el loop de simulación.
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.state = SimulationState()
        self.event_manager = EventManager()
        
        # Configurar timekeeper
        time_config = TimeConfig(
            ticks_per_epoch=config['simulation']['ticks_per_epoch'],
            max_epochs=config['simulation']['max_epochs'],
            tick_duration_ms=1000.0 / config['ui'].get('fps', 60)
        )
        self.timekeeper = TimeKeeper(time_config)
        
        # Componentes del sistema (se inicializarán después)
        self.environment = None
        self.agent_manager = None
        self.genetic_algorithm = None
        self.analytics = None
        self.renderer = None
        
        # Callbacks
        self.on_tick: Optional[Callable] = None
        self.on_epoch: Optional[Callable] = None
        self.on_generation: Optional[Callable] = None
        
        # Configurar callbacks del timekeeper
        self._setup_timekeeper_callbacks()
    
    def _setup_timekeeper_callbacks(self) -> None:
        """Configura los callbacks del timekeeper."""
        self.timekeeper.on_tick_start = self._on_tick_start
        self.timekeeper.on_tick_end = self._on_tick_end
        self.timekeeper.on_epoch_start = self._on_epoch_start
        self.timekeeper.on_epoch_end = self._on_epoch_end
    
    def set_components(self, environment, agent_manager, genetic_algorithm, analytics, renderer=None):
        """
        Establece los componentes del sistema.
        
        Args:
            environment: Gestor del entorno
            agent_manager: Gestor de agentes
            genetic_algorithm: Algoritmo genético
            analytics: Sistema de análisis
            renderer: Renderizador (opcional)
        """
        self.environment = environment
        self.agent_manager = agent_manager
        self.genetic_algorithm = genetic_algorithm
        self.analytics = analytics
        self.renderer = renderer
    
    def start(self) -> None:
        """Inicia la simulación."""
        if self.state.is_running:
            return
        
        self.state.is_running = True
        self.state.is_paused = False
        
        emit_event(EventType.SIMULATION_START, {
            'config': self.config,
            'timestamp': time.time()
        })
        
        self.timekeeper.start_simulation()
        self._main_loop()
    
    def pause(self) -> None:
        """Pausa la simulación."""
        self.state.is_paused = True
    
    def resume(self) -> None:
        """Reanuda la simulación."""
        self.state.is_paused = False
    
    def stop(self) -> None:
        """Detiene la simulación."""
        self.state.is_running = False
        self.state.is_paused = False
        
        emit_event(EventType.SIMULATION_END, {
            'final_state': self.state.__dict__,
            'timestamp': time.time()
        })
    
    def _main_loop(self) -> None:
        """Loop principal de la simulación."""
        try:
            while self.state.is_running and not self.timekeeper.is_simulation_complete():
                # Manejar pausa
                if self.state.is_paused:
                    time.sleep(0.1)
                    continue
                
                # Iniciar tick
                if not self.timekeeper.start_tick():
                    break
                
                # Ejecutar tick
                self._execute_tick()
                
                # Finalizar tick
                self.timekeeper.end_tick()
                
                # Renderizar si está disponible
                if self.renderer:
                    self.renderer.render()
                
                # Verificar si necesitamos nueva generación
                if self._should_evolve():
                    self._evolve_generation()
        
        except KeyboardInterrupt:
            print("Simulación interrumpida por el usuario")
        except Exception as e:
            print(f"Error en el loop principal: {e}")
            raise
        finally:
            self.stop()
    
    def _execute_tick(self) -> None:
        """Ejecuta un tick de la simulación."""
        # Actualizar entorno
        if self.environment:
            self.environment.update()
        
        # Actualizar agentes
        if self.agent_manager:
            self.agent_manager.update_agents()
        
        # Actualizar métricas
        if self.analytics:
            self.analytics.update_metrics()
        
        # Callback personalizado
        if self.on_tick:
            self.on_tick(self.timekeeper.current_tick, self.timekeeper.current_epoch)
    
    def _should_evolve(self) -> bool:
        """
        Determina si es momento de evolucionar.
        
        Returns:
            True si debe evolucionar
        """
        # Evolucionar al final de cada época
        return (self.timekeeper.current_tick >= self.config['simulation']['ticks_per_epoch'] and
                self.agent_manager and
                self.agent_manager.get_alive_count() > 0)
    
    def _evolve_generation(self) -> None:
        """Evoluciona a la siguiente generación."""
        if not self.genetic_algorithm or not self.agent_manager:
            return
        
        self.state.current_generation += 1
        
        emit_event(EventType.GENERATION_START, {
            'generation': self.state.current_generation,
            'timestamp': time.time()
        })
        
        # Calcular fitness de agentes actuales
        fitness_scores = self.agent_manager.calculate_fitness()
        
        # Evolucionar población
        new_population = self.genetic_algorithm.evolve(
            self.agent_manager.get_agents(),
            fitness_scores
        )
        
        # Reemplazar población
        self.agent_manager.replace_population(new_population)
        
        # Actualizar estado
        self.state.total_agents = len(new_population)
        self.state.alive_agents = self.agent_manager.get_alive_count()
        
        # Callback personalizado
        if self.on_generation:
            self.on_generation(self.state.current_generation)
        
        emit_event(EventType.GENERATION_END, {
            'generation': self.state.current_generation,
            'population_size': self.state.total_agents,
            'timestamp': time.time()
        })
    
    def _on_tick_start(self, tick: int, epoch: int) -> None:
        """Callback cuando inicia un tick."""
        emit_event(EventType.TICK_START, {
            'tick': tick,
            'epoch': epoch,
            'timestamp': time.time()
        })
    
    def _on_tick_end(self, tick: int, epoch: int) -> None:
        """Callback cuando termina un tick."""
        emit_event(EventType.TICK_END, {
            'tick': tick,
            'epoch': epoch,
            'timestamp': time.time()
        })
    
    def _on_epoch_start(self, epoch: int) -> None:
        """Callback cuando inicia una época."""
        emit_event(EventType.EPOCH_START, {
            'epoch': epoch,
            'timestamp': time.time()
        })
        
        # Reiniciar entorno si es necesario
        if self.environment:
            self.environment.reset_epoch()
    
    def _on_epoch_end(self, epoch: int) -> None:
        """Callback cuando termina una época."""
        emit_event(EventType.EPOCH_END, {
            'epoch': epoch,
            'timestamp': time.time()
        })
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la simulación.
        
        Returns:
            Diccionario con el estado actual
        """
        progress = self.timekeeper.get_progress()
        
        return {
            'state': self.state.__dict__,
            'progress': progress,
            'timekeeper': {
                'current_tick': self.timekeeper.current_tick,
                'current_epoch': self.timekeeper.current_epoch,
                'simulation_time': self.timekeeper.get_simulation_time()
            }
        }
    
    def set_callback(self, event_type: str, callback: Callable) -> None:
        """
        Establece un callback personalizado.
        
        Args:
            event_type: Tipo de evento ('tick', 'epoch', 'generation')
            callback: Función callback
        """
        if event_type == 'tick':
            self.on_tick = callback
        elif event_type == 'epoch':
            self.on_epoch = callback
        elif event_type == 'generation':
            self.on_generation = callback
