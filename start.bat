@echo off
echo 🚀 Ecosistema Evolutivo IA - Inicio Rápido
echo ==========================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar dependencias
echo 🔍 Verificando dependencias...
python -c "import yaml, numpy, pandas, matplotlib, seaborn, sklearn, torch, pygame, deap, noise, rich, tqdm, psutil" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencias faltantes. Ejecutando instalación automática...
    call install.bat
    if errorlevel 1 (
        echo ❌ Error en la instalación
        pause
        exit /b 1
    )
)

echo ✅ Dependencias verificadas

REM Crear directorios necesarios
if not exist "logs" mkdir logs
if not exist "logs\runtime" mkdir logs\runtime
if not exist "logs\metrics" mkdir logs\metrics
if not exist "results" mkdir results
if not exist "results\figures" mkdir results\figures
if not exist "results\reports" mkdir results\reports
if not exist "checkpoints" mkdir checkpoints
if not exist "checkpoints\latest" mkdir checkpoints\latest
if not exist "checkpoints\archive" mkdir checkpoints\archive

echo 📁 Directorios creados

REM Ejecutar simulación
echo 🎮 Iniciando simulación...
echo ==========================================
python start_simulation.py

if errorlevel 1 (
    echo ❌ Error durante la simulación
    echo 💡 Para más información, ejecuta:
    echo    python scripts/run_simulation.py --verbose
    pause
    exit /b 1
)

echo ✅ Simulación completada
pause
