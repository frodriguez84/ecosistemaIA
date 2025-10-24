"""
Módulo principal del ecosistema evolutivo.
Contiene la aplicación principal y configuración.
"""

from .app import EcosistemaApp, main
from .config import ConfigLoader, load_config

__all__ = ['EcosistemaApp', 'main', 'ConfigLoader', 'load_config']
