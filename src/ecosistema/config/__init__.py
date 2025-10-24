"""
Módulo de configuración del ecosistema evolutivo.
Maneja la carga y validación de configuraciones YAML.
"""

from .loader import ConfigLoader, load_config

__all__ = ['ConfigLoader', 'load_config']
