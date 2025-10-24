"""
Módulo de interfaz de usuario para el ecosistema evolutivo.
Contiene sistemas de renderizado, estadísticas y popups.
"""

from .renderer import SpriteManager, ParticleSystem
from .stats import StatsPanel
from .popup import SummaryPopup

__all__ = [
    'SpriteManager', 'ParticleSystem',
    'StatsPanel',
    'SummaryPopup'
]
