@echo off
echo 🔧 Instalando dependencias del Ecosistema Evolutivo IA...
echo ============================================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Instalar dependencias
echo 📦 Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install PyYAML numpy pandas matplotlib seaborn scikit-learn torch pygame deap noise rich tqdm psutil

if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

echo ✅ Dependencias instaladas

REM Verificar instalación
echo 🔍 Verificando instalación...
python check_installation.py

if errorlevel 1 (
    echo ⚠️  Hay problemas con la instalación
    pause
    exit /b 1
)

echo 🎉 Instalación completada!
echo.
echo 🚀 Para ejecutar la simulación:
echo    python start_simulation.py
echo    o
echo    python scripts/run_simulation.py
echo.
pause
