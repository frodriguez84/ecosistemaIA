"""
Módulo de interfaz de usuario para el ecosistema evolutivo.
Contiene sistemas de renderizado, estadísticas, avisos y la pantalla final.
"""

from .renderer import SpriteManager, ParticleSystem
from .stats import StatsPanel

__all__ = [
    'SpriteManager', 'ParticleSystem',
    'StatsPanel',
]
