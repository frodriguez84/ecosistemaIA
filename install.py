#!/usr/bin/env python3
"""
Script simple para instalar dependencias.
"""

import subprocess
import sys

def install_package(package):
    """Instala un paquete."""
    try:
        print(f"📦 Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}: {e}")
        return False

def main():
    """Función principal."""
    print("🔧 Instalando dependencias del Ecosistema Evolutivo IA...")
    print("=" * 60)
    
    # Lista de dependencias (sin noise)
    packages = [
        "PyYAML",
        "numpy", 
        "pandas",
        "matplotlib",
        "seaborn",
        "scikit-learn",
        "torch",
        "pygame",
        "deap",
        "rich",
        "tqdm",
        "psutil"
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Resultado: {success_count}/{len(packages)} dependencias instaladas")
    
    if success_count == len(packages):
        print("🎉 ¡Todas las dependencias instaladas correctamente!")
        print("🚀 Ahora puedes ejecutar: python run_app.py")
    else:
        print("⚠️  Algunas dependencias no se pudieron instalar")
        print("💡 Intenta instalar manualmente las que fallaron")

if __name__ == "__main__":
    main()
