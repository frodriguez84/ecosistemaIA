"""
Tests para el cargador de configuración.
"""

import pytest
import yaml
from pathlib import Path
from src.ecosistema.config.loader import ConfigLoader, load_config


class TestConfigLoader:
    """Tests para el cargador de configuración."""
    
    def test_config_loader_creation(self):
        """Test de creación del cargador."""
        loader = ConfigLoader()
        assert loader is not None
    
    def test_load_default_config(self):
        """Test de carga de configuración por defecto."""
        # Crear archivo de configuración de prueba
        test_config = {
            'simulation': {
                'map_size': [100, 100],
                'population': 50,
                'ticks_per_epoch': 1000
            },
            'agent': {
                'energy_max': 100.0,
                'energy_move_cost': 1.0
            },
            'ga': {
                'population_size': 50,
                'mutation_rate': 0.1
            }
        }
        
        # Guardar configuración de prueba
        test_file = Path("test_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            # Cargar configuración
            loader = ConfigLoader(str(test_file))
            config = loader.load_config()
            
            assert config['simulation']['map_size'] == [100, 100]
            assert config['simulation']['population'] == 50
            assert config['agent']['energy_max'] == 100.0
            
        finally:
            # Limpiar archivo de prueba
            if test_file.exists():
                test_file.unlink()
    
    def test_config_validation(self):
        """Test de validación de configuración."""
        # Configuración inválida (falta sección requerida)
        invalid_config = {
            'simulation': {
                'map_size': [100, 100]
            }
            # Falta sección 'agent'
        }
        
        test_file = Path("test_invalid_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        try:
            loader = ConfigLoader(str(test_file))
            
            # Debe lanzar excepción
            with pytest.raises(ValueError):
                loader.load_config()
                
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_get_section(self):
        """Test de obtención de sección."""
        test_config = {
            'simulation': {'map_size': [100, 100]},
            'agent': {'energy_max': 100.0}
        }
        
        test_file = Path("test_section_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            loader = ConfigLoader(str(test_file))
            config = loader.load_config()
            
            simulation_section = loader.get_section('simulation')
            assert simulation_section['map_size'] == [100, 100]
            
            agent_section = loader.get_section('agent')
            assert agent_section['energy_max'] == 100.0
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_get_value(self):
        """Test de obtención de valor."""
        test_config = {
            'simulation': {'map_size': [100, 100]},
            'agent': {'energy_max': 100.0}
        }
        
        test_file = Path("test_value_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            loader = ConfigLoader(str(test_file))
            config = loader.load_config()
            
            # Obtener valor existente
            map_size = loader.get_value('simulation', 'map_size')
            assert map_size == [100, 100]
            
            # Obtener valor con valor por defecto
            default_value = loader.get_value('simulation', 'non_existent', 'default')
            assert default_value == 'default'
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_update_config(self):
        """Test de actualización de configuración."""
        test_config = {
            'simulation': {'map_size': [100, 100]},
            'agent': {'energy_max': 100.0}
        }
        
        test_file = Path("test_update_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            loader = ConfigLoader(str(test_file))
            config = loader.load_config()
            
            # Actualizar valor
            loader.update_config('simulation', 'map_size', [200, 200])
            
            # Verificar actualización
            updated_value = loader.get_value('simulation', 'map_size')
            assert updated_value == [200, 200]
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_save_config(self):
        """Test de guardado de configuración."""
        test_config = {
            'simulation': {'map_size': [100, 100]},
            'agent': {'energy_max': 100.0}
        }
        
        test_file = Path("test_save_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            loader = ConfigLoader(str(test_file))
            config = loader.load_config()
            
            # Modificar configuración
            loader.update_config('simulation', 'map_size', [300, 300])
            
            # Guardar en nuevo archivo
            output_file = Path("test_output_config.yaml")
            loader.save_config(str(output_file))
            
            # Verificar que se guardó correctamente
            assert output_file.exists()
            
            # Cargar y verificar
            with open(output_file, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert saved_config['simulation']['map_size'] == [300, 300]
            
        finally:
            if test_file.exists():
                test_file.unlink()
            if output_file.exists():
                output_file.unlink()
    
    def test_load_config_function(self):
        """Test de función de conveniencia load_config."""
        test_config = {
            'simulation': {'map_size': [100, 100]},
            'agent': {'energy_max': 100.0}
        }
        
        test_file = Path("test_function_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
        
        try:
            config = load_config(str(test_file))
            
            assert config['simulation']['map_size'] == [100, 100]
            assert config['agent']['energy_max'] == 100.0
            
        finally:
            if test_file.exists():
                test_file.unlink()
