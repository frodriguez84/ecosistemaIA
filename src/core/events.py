"""
Sistema de eventos para el ecosistema evolutivo.
Define eventos internos del sistema de simulación.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time


class EventType(Enum):
    """Tipos de eventos del sistema."""
    SIMULATION_START = "simulation_start"
    SIMULATION_END = "simulation_end"
    EPOCH_START = "epoch_start"
    EPOCH_END = "epoch_end"
    TICK_START = "tick_start"
    TICK_END = "tick_end"
    AGENT_BORN = "agent_born"
    AGENT_DIED = "agent_died"
    AGENT_EAT = "agent_eat"
    AGENT_COLLISION = "agent_collision"
    GENERATION_START = "generation_start"
    GENERATION_END = "generation_end"
    CHECKPOINT_SAVE = "checkpoint_save"
    CHECKPOINT_LOAD = "checkpoint_load"


@dataclass
class Event:
    """Representa un evento del sistema."""
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    agent_id: Optional[int] = None
    
    def __post_init__(self):
        """Inicializa el timestamp si no se proporciona."""
        if self.timestamp is None:
            self.timestamp = time.time()


class EventManager:
    """Gestor de eventos del sistema."""
    
    def __init__(self):
        """Inicializa el gestor de eventos."""
        self._listeners: Dict[EventType, list] = {}
        self._event_history: list = []
        self._max_history: int = 10000
    
    def subscribe(self, event_type: EventType, callback) -> None:
        """
        Suscribe una función callback a un tipo de evento.
        
        Args:
            event_type: Tipo de evento al que suscribirse
            callback: Función a llamar cuando ocurra el evento
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback) -> None:
        """
        Desuscribe una función callback de un tipo de evento.
        
        Args:
            event_type: Tipo de evento del que desuscribirse
            callback: Función a remover
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass  # Callback no estaba suscrito
    
    def emit(self, event_type: EventType, data: Dict[str, Any] = None, agent_id: Optional[int] = None) -> None:
        """
        Emite un evento a todos los suscriptores.
        
        Args:
            event_type: Tipo de evento a emitir
            data: Datos adicionales del evento
            agent_id: ID del agente relacionado (opcional)
        """
        if data is None:
            data = {}
        
        event = Event(
            event_type=event_type,
            timestamp=time.time(),
            data=data,
            agent_id=agent_id
        )
        
        # Agregar a historial
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notificar a suscriptores
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error en callback de evento {event_type}: {e}")
    
    def get_events(self, event_type: Optional[EventType] = None, limit: Optional[int] = None) -> list:
        """
        Obtiene eventos del historial.
        
        Args:
            event_type: Filtrar por tipo de evento (opcional)
            limit: Límite de eventos a retornar (opcional)
            
        Returns:
            Lista de eventos
        """
        events = self._event_history
        
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        
        if limit is not None:
            events = events[-limit:]
        
        return events
    
    def clear_history(self) -> None:
        """Limpia el historial de eventos."""
        self._event_history.clear()
    
    def get_event_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Obtiene el número de eventos de un tipo específico.
        
        Args:
            event_type: Tipo de evento a contar (opcional)
            
        Returns:
            Número de eventos
        """
        if event_type is None:
            return len(self._event_history)
        
        return sum(1 for e in self._event_history if e.event_type == event_type)


# Instancia global del gestor de eventos
event_manager = EventManager()


def emit_event(event_type: EventType, data: Dict[str, Any] = None, agent_id: Optional[int] = None) -> None:
    """
    Función de conveniencia para emitir eventos.
    
    Args:
        event_type: Tipo de evento a emitir
        data: Datos adicionales del evento
        agent_id: ID del agente relacionado (opcional)
    """
    event_manager.emit(event_type, data, agent_id)


def subscribe_to_event(event_type: EventType, callback) -> None:
    """
    Función de conveniencia para suscribirse a eventos.
    
    Args:
        event_type: Tipo de evento al que suscribirse
        callback: Función a llamar cuando ocurra el evento
    """
    event_manager.subscribe(event_type, callback)
