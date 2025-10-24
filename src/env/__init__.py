"""
Módulo de entorno para el ecosistema evolutivo.
Contiene el mundo, física y generación procedural.
"""

from .world import World, WorldState
from .physics import PhysicsEngine, CollisionType, CollisionResult
from .procedural import ProceduralGenerator, WorldConfig, TerrainGenerator, ResourceManager
from .resources import ResourceManager as BaseResourceManager, ResourceConfig

__all__ = [
    'World', 'WorldState',
    'PhysicsEngine', 'CollisionType', 'CollisionResult',
    'ProceduralGenerator', 'WorldConfig', 'TerrainGenerator', 'ResourceManager',
    'BaseResourceManager', 'ResourceConfig'
]
