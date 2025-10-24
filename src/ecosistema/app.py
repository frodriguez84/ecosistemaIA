"""
Aplicación principal del ecosistema evolutivo.
Integra todos los componentes del sistema.
"""

import sys
import time
import random
from typing import Dict, Any, Optional
from pathlib import Path

# Importar módulos del sistema
from .config.loader import load_config
from core.loop import SimulationLoop
from core.events import EventType
from env.world import World
from agents.agent import Agent
from ai.ga.evolve import GeneticAlgorithm
from ai.fitness import FitnessEvaluator
from analytics.metrics import MetricsCollector
from ui.renderer import SimulationRenderer
from ui.hud import HUD
from ui.controls import SimulationControls


class EcosistemaApp:
    """Aplicación principal del ecosistema evolutivo."""
    
    def __init__(self, config_path: str = "configs/default.yaml"):
        """
        Inicializa la aplicación.
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config = load_config(config_path)
        self.world = None
        self.agents = []
        self.running = False
        
        # Inicializar componentes
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema."""
        # Crear mundo
        self.world = World(self.config)
        
        # Crear agentes
        self._create_agents()
    
    def _create_agents(self):
        """Crea la población inicial de agentes."""
        population_size = self.config['ga']['population_size']
        
        for i in range(population_size):
            agent = Agent(
                agent_id=i,
                x=random.randint(0, self.config['simulation']['map_size'][0]-1),
                y=random.randint(0, self.config['simulation']['map_size'][1]-1),
                config=self.config['agent']
            )
            self.agents.append(agent)
    
    def run(self):
        """Ejecuta la simulación principal."""
        print("🚀 Iniciando simulación del ecosistema evolutivo...")
        print(f"📊 Configuración:")
        print(f"   - Mapa: {self.config['simulation']['map_size']}")
        print(f"   - Población: {len(self.agents)} agentes")
        print(f"   - Épocas: {self.config['simulation']['max_epochs']}")
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running:
                # Actualizar simulación
                self._update_simulation()
                
                # Controlar FPS
                time.sleep(1.0 / 60)  # 60 FPS
                
        except KeyboardInterrupt:
            print("\n⏹️ Simulación interrumpida por el usuario")
        except Exception as e:
            print(f"\n❌ Error durante la simulación: {e}")
        finally:
            self._cleanup()
    
    def _update_simulation(self):
        """Actualiza el estado de la simulación."""
        # Actualizar agentes
        for agent in self.agents:
            agent.update(self.world)
        
        # Actualizar mundo
        self.world.update()
    
    def _cleanup(self):
        """Limpia recursos al finalizar."""
        print("🧹 Limpiando recursos...")
        print("✅ Simulación finalizada")


def main():
    """Función principal."""
    print("🎯 Ecosistema Evolutivo IA")
    print("=" * 40)
    
    # Crear y ejecutar aplicación
    app = EcosistemaApp()
    app.run()


if __name__ == "__main__":
    main()