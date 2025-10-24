"""
Módulo core del ecosistema evolutivo.
Contiene el loop principal, eventos y control de tiempo.
"""

from .events import EventType, Event, EventManager, event_manager, emit_event, subscribe_to_event
from .timekeeper import TimeKeeper, TimeConfig
from .loop import SimulationLoop, SimulationState

__all__ = [
    'EventType', 'Event', 'EventManager', 'event_manager',
    'emit_event', 'subscribe_to_event',
    'TimeKeeper', 'TimeConfig',
    'SimulationLoop', 'SimulationState'
]
