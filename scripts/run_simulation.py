#!/usr/bin/env python3
"""
Script para ejecutar la simulación del ecosistema evolutivo.
"""

import sys
import os
import argparse
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.ecosistema.app import EcosistemaApp


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Ejecutar simulación del ecosistema evolutivo")
    parser.add_argument("--config", "-c", type=str, default="configs/default.yaml",
                       help="Archivo de configuración (por defecto: configs/default.yaml)")
    parser.add_argument("--headless", action="store_true",
                       help="Ejecutar en modo headless (sin interfaz gráfica)")
    parser.add_argument("--seed", "-s", type=int, default=42,
                       help="Semilla para reproducibilidad (por defecto: 42)")
    parser.add_argument("--output", "-o", type=str, default="results",
                       help="Directorio de salida para resultados (por defecto: results)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Modo verbose con más información")
    
    args = parser.parse_args()
    
    # Verificar que el archivo de configuración existe
    if not Path(args.config).exists():
        print(f"Error: Archivo de configuración no encontrado: {args.config}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logging si es verbose
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    try:
        print("Iniciando simulación del ecosistema evolutivo...")
        print(f"Configuración: {args.config}")
        print(f"Semilla: {args.seed}")
        print(f"Modo headless: {args.headless}")
        print(f"Directorio de salida: {args.output}")
        print("-" * 50)
        
        # Crear aplicación
        app = EcosistemaApp(args.config)
        
        # Configurar semilla si se especifica
        if args.seed:
            # from utils.rng import set_seed
            # set_seed(args.seed)
            print(f"Semilla establecida: {args.seed}")
        
        # Ejecutar simulación
        app.run()
        
        print("-" * 50)
        print("Simulación completada exitosamente")
        
    except KeyboardInterrupt:
        print("\nSimulación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error durante la simulación: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
