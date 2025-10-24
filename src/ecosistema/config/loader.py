"""
Cargador de configuración YAML para el ecosistema evolutivo.
Maneja la carga y validación de parámetros del sistema.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Cargador y validador de configuración YAML."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el cargador de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, usa default.yaml
        """
        if config_path is None:
            config_path = "configs/default.yaml"
        
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo YAML.
        
        Returns:
            Diccionario con la configuración cargada
            
        Raises:
            FileNotFoundError: Si el archivo de configuración no existe
            yaml.YAMLError: Si hay error al parsear el YAML
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            # Validar configuración
            self._validate_config()
            return self._config.copy()
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error al parsear YAML: {e}")
    
    def _validate_config(self) -> None:
        """Valida que la configuración tenga las secciones requeridas."""
        required_sections = [
            'simulation', 'agent', 'ga', 'neural_net', 
            'environment', 'fitness', 'analytics', 'ui', 'logging'
        ]
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Sección requerida '{section}' no encontrada en configuración")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtiene una sección específica de la configuración.
        
        Args:
            section: Nombre de la sección
            
        Returns:
            Diccionario con la configuración de la sección
        """
        if self._config is None:
            self.load_config()
        
        if section not in self._config:
            raise KeyError(f"Sección '{section}' no encontrada en configuración")
        
        return self._config[section]
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor específico de la configuración.
        
        Args:
            section: Nombre de la sección
            key: Clave del valor
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor de la configuración o valor por defecto
        """
        try:
            section_config = self.get_section(section)
            return section_config.get(key, default)
        except KeyError:
            return default
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        Actualiza un valor en la configuración.
        
        Args:
            section: Nombre de la sección
            key: Clave del valor
            value: Nuevo valor
        """
        if self._config is None:
            self.load_config()
        
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Guarda la configuración actual en un archivo.
        
        Args:
            output_path: Ruta de salida. Si es None, sobrescribe el archivo original
        """
        if self._config is None:
            raise ValueError("No hay configuración cargada para guardar")
        
        save_path = Path(output_path) if output_path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as file:
            yaml.dump(self._config, file, default_flow_style=False, indent=2)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Función de conveniencia para cargar configuración.
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Diccionario con la configuración cargada
    """
    loader = ConfigLoader(config_path)
    return loader.load_config()


if __name__ == "__main__":
    # Test del cargador
    try:
        config = load_config()
        print("Configuración cargada exitosamente:")
        print(f"- Tamaño del mapa: {config['simulation']['map_size']}")
        print(f"- Población: {config['simulation']['population']}")
        print(f"- Generaciones máximas: {config['ga']['max_generations']}")
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
