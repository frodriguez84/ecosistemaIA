# Makefile para el Ecosistema Evolutivo IA

.PHONY: help install test run clean setup-dev

# Variables
PYTHON = python3
PIP = pip3
VENV = venv
SRC_DIR = src
TESTS_DIR = tests
SCRIPTS_DIR = scripts
CONFIG_DIR = configs
RESULTS_DIR = results
LOGS_DIR = logs

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostrar ayuda
	@echo "$(GREEN)Ecosistema Evolutivo IA$(NC)"
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

setup-dev: ## Configurar entorno de desarrollo
	@echo "$(GREEN)Configurando entorno de desarrollo...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/$(PIP) install --upgrade pip
	$(VENV)/bin/$(PIP) install -r requirements.txt
	$(VENV)/bin/$(PIP) install -e .
	@echo "$(GREEN)Entorno configurado. Activar con: source $(VENV)/bin/activate$(NC)"

install: ## Instalar dependencias
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

test: ## Ejecutar tests
	@echo "$(GREEN)Ejecutando tests...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v --tb=short

test-coverage: ## Ejecutar tests con cobertura
	@echo "$(GREEN)Ejecutando tests con cobertura...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term

run: ## Ejecutar simulación
	@echo "$(GREEN)Ejecutando simulación...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py

run-headless: ## Ejecutar simulación en modo headless
	@echo "$(GREEN)Ejecutando simulación en modo headless...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --headless

run-custom: ## Ejecutar simulación con configuración personalizada
	@echo "$(GREEN)Ejecutando simulación con configuración personalizada...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/custom.yaml

run-seed: ## Ejecutar simulación con semilla específica
	@echo "$(GREEN)Ejecutando simulación con semilla específica...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --seed 12345

run-verbose: ## Ejecutar simulación en modo verbose
	@echo "$(GREEN)Ejecutando simulación en modo verbose...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --verbose

clean: ## Limpiar archivos generados
	@echo "$(GREEN)Limpiando archivos generados...$(NC)"
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TESTS_DIR)/__pycache__
	rm -rf $(SRC_DIR)/**/__pycache__
	rm -rf $(TESTS_DIR)/**/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf $(RESULTS_DIR)/*
	rm -rf $(LOGS_DIR)/*
	@echo "$(GREEN)Limpieza completada$(NC)"

clean-logs: ## Limpiar solo logs
	@echo "$(GREEN)Limpiando logs...$(NC)"
	rm -rf $(LOGS_DIR)/*

clean-results: ## Limpiar solo resultados
	@echo "$(GREEN)Limpiando resultados...$(NC)"
	rm -rf $(RESULTS_DIR)/*

setup-dirs: ## Crear directorios necesarios
	@echo "$(GREEN)Creando directorios necesarios...$(NC)"
	mkdir -p $(LOGS_DIR)/runtime
	mkdir -p $(LOGS_DIR)/metrics
	mkdir -p $(RESULTS_DIR)/figures
	mkdir -p $(RESULTS_DIR)/reports
	mkdir -p $(CONFIG_DIR)/env_presets
	mkdir -p $(CONFIG_DIR)/ga_presets
	mkdir -p $(CONFIG_DIR)/experiment_templates
	mkdir -p checkpoints/latest
	mkdir -p checkpoints/archive
	@echo "$(GREEN)Directorios creados$(NC)"

lint: ## Ejecutar linter
	@echo "$(GREEN)Ejecutando linter...$(NC)"
	$(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR) --max-line-length=88 --ignore=E203,W503

format: ## Formatear código
	@echo "$(GREEN)Formateando código...$(NC)"
	$(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR) --line-length=88

type-check: ## Verificar tipos
	@echo "$(GREEN)Verificando tipos...$(NC)"
	$(PYTHON) -m mypy $(SRC_DIR) --ignore-missing-imports

docs: ## Generar documentación
	@echo "$(GREEN)Generando documentación...$(NC)"
	$(PYTHON) -m pydoc -w $(SRC_DIR)/ecosistema/app.py
	$(PYTHON) -m pydoc -w $(SRC_DIR)/agents/agent.py
	$(PYTHON) -m pydoc -w $(SRC_DIR)/ai/ga/evolve.py
	@echo "$(GREEN)Documentación generada$(NC)"

benchmark: ## Ejecutar benchmark de rendimiento
	@echo "$(GREEN)Ejecutando benchmark...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR)/test_benchmark.py -v

profile: ## Ejecutar profiling
	@echo "$(GREEN)Ejecutando profiling...$(NC)"
	$(PYTHON) -m cProfile -o profile.prof $(SCRIPTS_DIR)/run_simulation.py
	$(PYTHON) -m pstats profile.prof

check-deps: ## Verificar dependencias
	@echo "$(GREEN)Verificando dependencias...$(NC)"
	$(PYTHON) -m pip check

update-deps: ## Actualizar dependencias
	@echo "$(GREEN)Actualizando dependencias...$(NC)"
	$(PIP) install --upgrade -r requirements.txt

build: ## Construir paquete
	@echo "$(GREEN)Construyendo paquete...$(NC)"
	$(PYTHON) -m build

install-dev: setup-dirs install ## Configurar entorno completo de desarrollo

# Comandos de experimentación
exp-baseline: ## Ejecutar experimento baseline
	@echo "$(GREEN)Ejecutando experimento baseline...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/ga_presets/baseline.yaml

exp-high-mutation: ## Ejecutar experimento con alta mutación
	@echo "$(GREEN)Ejecutando experimento con alta mutación...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/ga_presets/high_mutation.yaml

exp-small-world: ## Ejecutar experimento en mundo pequeño
	@echo "$(GREEN)Ejecutando experimento en mundo pequeño...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/env_presets/small_world.yaml

exp-medium-world: ## Ejecutar experimento en mundo mediano
	@echo "$(GREEN)Ejecutando experimento en mundo mediano...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/env_presets/medium_world.yaml

exp-hard-world: ## Ejecutar experimento en mundo difícil
	@echo "$(GREEN)Ejecutando experimento en mundo difícil...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/run_simulation.py --config $(CONFIG_DIR)/env_presets/hard_world.yaml

# Comandos de análisis
analyze: ## Ejecutar análisis de resultados
	@echo "$(GREEN)Ejecutando análisis...$(NC)"
	$(PYTHON) -m jupyter notebook notebooks/EDA_metrics.ipynb

cluster-analysis: ## Ejecutar análisis de clustering
	@echo "$(GREEN)Ejecutando análisis de clustering...$(NC)"
	$(PYTHON) -m jupyter notebook notebooks/clustering_analysis.ipynb

ablation-study: ## Ejecutar estudio de ablación
	@echo "$(GREEN)Ejecutando estudio de ablación...$(NC)"
	$(PYTHON) -m jupyter notebook notebooks/ablation_ga.ipynb

# Comandos de utilidades
export-metrics: ## Exportar métricas
	@echo "$(GREEN)Exportando métricas...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/export_metrics.py

make-gif: ## Crear GIF de la simulación
	@echo "$(GREEN)Creando GIF...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/make_gif_from_frames.py

resume-checkpoint: ## Reanudar desde checkpoint
	@echo "$(GREEN)Reanudando desde checkpoint...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/resume_from_checkpoint.py

seed-replay: ## Reproducir simulación con semilla
	@echo "$(GREEN)Reproduciendo simulación...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/seed_replay.py

# Comandos de desarrollo
dev-setup: setup-dirs install-dev ## Configurar entorno de desarrollo completo

dev-test: test lint type-check ## Ejecutar todas las verificaciones de desarrollo

dev-clean: clean clean-logs clean-results ## Limpieza completa de desarrollo

# Comandos de producción
prod-install: install setup-dirs ## Instalación para producción

prod-run: run-headless ## Ejecutar en modo producción

# Comandos de CI/CD
ci-test: test lint type-check ## Ejecutar tests de CI

ci-build: build ## Construir para CI

# Comandos de monitoreo
monitor: ## Monitorear simulación en ejecución
	@echo "$(GREEN)Monitoreando simulación...$(NC)"
	tail -f $(LOGS_DIR)/runtime/simulation.log

monitor-metrics: ## Monitorear métricas
	@echo "$(GREEN)Monitoreando métricas...$(NC)"
	tail -f $(LOGS_DIR)/metrics/metrics.csv

# Comandos de backup
backup: ## Crear backup de resultados
	@echo "$(GREEN)Creando backup...$(NC)"
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz $(RESULTS_DIR) $(LOGS_DIR) checkpoints

restore: ## Restaurar desde backup
	@echo "$(GREEN)Restaurando desde backup...$(NC)"
	@echo "Especificar archivo de backup: make restore BACKUP_FILE=backup_YYYYMMDD_HHMMSS.tar.gz"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "$(RED)Error: Especificar BACKUP_FILE$(NC)"; exit 1; fi
	tar -xzf $(BACKUP_FILE)

# Comandos de información
info: ## Mostrar información del sistema
	@echo "$(GREEN)Información del sistema:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Directorio actual: $(shell pwd)"
	@echo "Archivos de configuración: $(shell ls $(CONFIG_DIR)/*.yaml 2>/dev/null || echo 'Ninguno')"
	@echo "Resultados: $(shell ls $(RESULTS_DIR)/ 2>/dev/null || echo 'Ninguno')"
	@echo "Logs: $(shell ls $(LOGS_DIR)/ 2>/dev/null || echo 'Ninguno')"

status: ## Mostrar estado de la simulación
	@echo "$(GREEN)Estado de la simulación:$(NC)"
	@if [ -f "$(LOGS_DIR)/runtime/simulation.log" ]; then \
		echo "Log de simulación: $(shell tail -1 $(LOGS_DIR)/runtime/simulation.log)"; \
	else \
		echo "No hay log de simulación"; \
	fi
	@if [ -f "$(LOGS_DIR)/metrics/metrics.csv" ]; then \
		echo "Métricas: $(shell wc -l < $(LOGS_DIR)/metrics/metrics.csv) líneas"; \
	else \
		echo "No hay métricas"; \
	fi

# Comandos de ayuda específicos
help-run: ## Ayuda para ejecutar simulación
	@echo "$(GREEN)Comandos para ejecutar simulación:$(NC)"
	@echo "  make run              - Ejecutar simulación normal"
	@echo "  make run-headless     - Ejecutar sin interfaz gráfica"
	@echo "  make run-verbose      - Ejecutar con información detallada"
	@echo "  make run-seed         - Ejecutar con semilla específica"
	@echo "  make run-custom       - Ejecutar con configuración personalizada"

help-exp: ## Ayuda para experimentos
	@echo "$(GREEN)Comandos para experimentos:$(NC)"
	@echo "  make exp-baseline     - Experimento baseline"
	@echo "  make exp-high-mutation - Experimento con alta mutación"
	@echo "  make exp-small-world  - Experimento en mundo pequeño"
	@echo "  make exp-medium-world - Experimento en mundo mediano"
	@echo "  make exp-hard-world   - Experimento en mundo difícil"

help-dev: ## Ayuda para desarrollo
	@echo "$(GREEN)Comandos para desarrollo:$(NC)"
	@echo "  make dev-setup        - Configurar entorno de desarrollo"
	@echo "  make dev-test         - Ejecutar todas las verificaciones"
	@echo "  make dev-clean        - Limpieza completa"
	@echo "  make test             - Ejecutar tests"
	@echo "  make lint             - Ejecutar linter"
	@echo "  make format           - Formatear código"
	@echo "  make type-check       - Verificar tipos"

# Comando por defecto
.DEFAULT_GOAL := help
