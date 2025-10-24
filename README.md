**Contexto General**

Estás trabajando en el desarrollo de una aplicación completa de simulación llamada  **“Ecosistema Evolutivo IA”** , un entorno 2D donde criaturas autónomas aprenden a sobrevivir, adaptarse y evolucionar utilizando múltiples técnicas de  **Inteligencia Artificial** :

* Algoritmos genéticos
* Redes neuronales artificiales
* Clustering no supervisado
* Generación procedural del entorno

El proyecto está desarrollado en  **Python 3.11+** , y debe mantener una  **arquitectura modular, extensible y limpia** , siguiendo principios de diseño como:

* *Separation of Concerns*
* *Single Responsibility Principle*
* *Dependency Injection* ligera (configuración YAML)
* Soporte para logging estructurado, reproducibilidad por seeds y ejecución por fases.


## 🎯 Objetivo del Proyecto

Crear un **ecosistema digital autoevolutivo** donde criaturas simuladas:

1. Perciban su entorno (posición de comida, obstáculos, energía).
2. Tomen decisiones mediante una red neuronal (movimiento, alimentación, evasión).
3. Sean evaluadas por su desempeño ( *fitness* ).
4. Se reproduzcan mediante un **algoritmo genético** (selección, cruce, mutación).
5. Den lugar a nuevas generaciones más adaptadas.
6. Sean analizadas mediante técnicas **no supervisadas** para detectar patrones emergentes.

El resultado debe ser visual, con una interfaz mínima que muestre:

* El mapa (entorno 2D).
* Criaturas moviéndose y actuando.
* Métricas en tiempo real (generación, fitness promedio, supervivientes, diversidad).

---

## ⚙️ Stack Tecnológico

**Lenguaje:** Python 3.11+

**Librerías Principales:**

* `pygame` o `arcade` → Renderizado 2D y eventos.
* `torch` o `tensorflow.keras` → Redes neuronales.
* `deap` → Algoritmos genéticos.
* `scikit-learn` → Clustering, PCA, normalización.
* `noise` o `perlin-noise` → Generación procedural del entorno.
* `matplotlib` / `seaborn` → Visualización de métricas.
* `pandas`, `numpy` → Manipulación de datos.
* `yaml`, `argparse` → Configuración y CLI.
* `logging`, `rich` → Logging estructurado y visual.

**Entorno y herramientas:**

* Control de versiones con Git.
* Requerimientos en `requirements.txt` o `pyproject.toml`.
* Soporte para ejecución local o notebook (modo headless opcional).

---

## 🧩 Estructura del Proyecto

*(ya creada en Cursor, pero Cursor debe comprenderla)*

La raíz contiene:

<pre class="overflow-visible!" data-start="2993" data-end="3590"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>src/ecosistema/
├── app.py                  </span><span># punto de entrada principal</span><span>
├── core/                   </span><span># loop principal, eventos, tiempo</span><span>
├── </span><span>env</span><span>/                    </span><span># entorno 2D y generación procedural</span><span>
├── agents/                 </span><span># criaturas: sensores, actuadores y cerebros</span><span>
├── ai/                     </span><span># algoritmos genéticos y cálculo de fitness</span><span>
├── analytics/              </span><span># métricas, clustering y análisis</span><span>
├── ui/                     </span><span># render y HUD</span><span>
├── persistence/            </span><span># checkpoints, IO, seeds</span><span>
├── utils/                  </span><span># helpers varios</span><span>
└── config/                 </span><span># loader YAML</span><span>
</span></span></code></div></div></pre>

---

## 🧱 Funcionalidades Esperadas (por módulos)

### 1. `core/`

* `loop.py`: ciclo principal de simulación (ticks, eventos, reinicio de época).
* `events.py`: define eventos internos (inicio, fin de época, colisión, muerte).
* `timekeeper.py`: controla duración de ticks y tiempos totales.

### 2. `env/`

* `world.py`: define el mapa, grilla y límites.
* `resources.py`: administra comida, obstáculos, regeneración.
* `physics.py`: calcula costos de movimiento, energía, colisiones.
* `procedural.py`: genera mundos usando ruido Perlin o semillas reproducibles.

### 3. `agents/`

* `agent.py`: clase principal `Agent` con estado (energía, edad, pos).
* `sensors.py`: percepción del entorno (radio de visión, energía, obstáculos).
* `actuators.py`: acciones posibles (mover, girar, comer).
* `brain/`:
  * `mlp.py`: red neuronal (PyTorch o Keras) con pesos inicializables.
  * `policy.py`: lógica para convertir percepciones → acciones.

### 4. `ai/`

* `fitness.py`: define función de evaluación (vida + comida + distancia).
* `ga/`:
  * `selection.py`, `crossover.py`, `mutation.py`: operadores genéticos.
  * `evolve.py`: maneja el ciclo GA (selección, cruce, mutación, elitismo).

### 5. `analytics/`

* `metrics.py`: registra métricas por tick y época.
* `logger.py`: guarda logs estructurados (JSON/CSV).
* `features.py`: transforma logs en features numéricas.
* `clustering.py`: aplica KMeans/DBSCAN para clasificar comportamientos.
* `dimensionality.py`: reduce dimensión (PCA o UMAP).

### 6. `ui/`

* `renderer.py`: dibuja mapa y agentes.
* `hud.py`: panel de métricas (texto o barra).
* `controls.py`: lectura de input (pausa, velocidad, seed).

### 7. `persistence/`

* `checkpoints.py`: guarda/carga pesos, generaciones y configuraciones.
* `io_utils.py`: funciones genéricas de lectura/escritura.
* `seeds.py`: control de reproducibilidad.

### 8. `utils/`

* Funciones auxiliares: geometría 2D, RNG, profiling y timers.

---

## 🧬 Flujo General del Sistema

1. Se cargan configuraciones (tamaño del mapa, población, parámetros del GA).
2. Se genera un entorno procedural con comida y obstáculos.
3. Se inicializan agentes con redes neuronales aleatorias.
4. Se ejecuta el  **loop de simulación** :
   * Cada tick: los agentes perciben → deciden → actúan.
   * Se actualiza energía, posición y estado.
   * Se registran métricas.
5. Al finalizar una época:
   * Se calcula fitness de cada agente.
   * El módulo GA genera la nueva población (cruce + mutación).
   * Se guarda un checkpoint.
6. Cada cierto número de generaciones:
   * Se corre el análisis de clustering.
   * Se generan reportes o gráficos.

---

## 📊 Datos, Logs y Resultados

* Cada corrida debe producir:
  * `logs/metrics/epoch_X.csv` con fitness, energía y distancia promedio.
  * `checkpoints/gen_X.pkl` con pesos de redes neuronales.
  * `results/figures/` con gráficos de evolución.
  * `results/reports/` con análisis generacional y clustering.

---

## 🧠 Inteligencia Artificial (detalles)

### Algoritmo Genético

* Población inicial: 50–200 individuos.
* Fitness: ponderación de supervivencia + comida + eficiencia.
* Selección: torneo o ruleta.
* Crossover: uniforme o por secciones de pesos.
* Mutación: gaussiana, 2–10% tasa.
* Elitismo: 1–2 mejores individuos se preservan.

### Red Neuronal (cerebro del agente)

* Tipo: MLP con 1–2 capas ocultas.
* Entradas: percepciones + estado (energía, dirección, entorno).
* Salidas: 3–4 acciones posibles (rotar, avanzar, comer).
* Activaciones: ReLU o tanh.
* Pesos mutables por el GA.

### Clustering (Análisis no supervisado)

* Features: distancia recorrida, energía gastada, colisiones, vida útil.
* Algoritmo: K-Means (k=3–5) o DBSCAN.
* Propósito: identificar “estilos” de comportamiento emergentes.

---

## 🧭 Parámetros configurables (YAML)

Ejemplo de `configs/default.yaml`:

<pre class="overflow-visible!" data-start="7526" data-end="7964"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-yaml"><span><span>simulation:</span><span>
  </span><span>map_size:</span><span> [</span><span>80</span><span>, </span><span>80</span><span>]
  </span><span>ticks_per_epoch:</span><span></span><span>2000</span><span>
  </span><span>population:</span><span></span><span>100</span><span>
  </span><span>food_density:</span><span></span><span>0.1</span><span>
  </span><span>obstacle_density:</span><span></span><span>0.05</span><span>
  </span><span>random_seed:</span><span></span><span>42</span><span>

</span><span>agent:</span><span>
  </span><span>vision_range:</span><span></span><span>5</span><span>
  </span><span>energy_max:</span><span></span><span>100</span><span>
  </span><span>energy_move_cost:</span><span></span><span>1.2</span><span>
  </span><span>energy_eat_gain:</span><span></span><span>20</span><span>

</span><span>ga:</span><span>
  </span><span>population_size:</span><span></span><span>100</span><span>
  </span><span>mutation_rate:</span><span></span><span>0.08</span><span>
  </span><span>crossover_rate:</span><span></span><span>0.7</span><span>
  </span><span>elitism:</span><span></span><span>2</span><span>
  </span><span>max_generations:</span><span></span><span>200</span><span>

</span><span>neural_net:</span><span>
  </span><span>input_size:</span><span></span><span>10</span><span>
  </span><span>hidden_layers:</span><span> [</span><span>16</span><span>, </span><span>8</span><span>]
  </span><span>output_size:</span><span></span><span>4</span><span>
  </span><span>activation:</span><span></span><span>relu</span><span>
</span></span></code></div></div></pre>

---

## 🎮 Interfaz y visualización

* `pygame` muestra mapa top-down.
* Los agentes son círculos con color según especie/generación.
* HUD lateral con:
  * Generación actual
  * Fitness promedio
  * Diversidad genética
  * Controles: pausa, velocidad, reinicio
* Soporte para modo *headless* (sin render) para correr experimentos más rápido.

---

## 🧩 Testing y Validación

* Unit tests con `pytest`.
* Tests mínimos:
  * Carga de configuración.
  * Generación procedural del mapa.
  * Movimiento y colisiones de agentes.
  * Correcto cálculo de fitness.
  * GA produce nueva población válida.
  * Checkpoints y reproducibilidad.

---

## 📦 Entregables Finales Esperados

1. Código fuente completo modularizado (src/).
2. Documentación técnica (docs/arquitectura.md + diagramas Mermaid).
3. Logs y resultados de 3–5 corridas experimentales.
4. Notebook con análisis de clustering.
5. README con instrucciones para ejecutar, reproducir y visualizar.

---

## 🚀 Instalación y Uso

### Requisitos Previos

- Python 3.11+
- pip
- make (opcional, para usar comandos del Makefile)

### Instalación Rápida

```bash
# 1. Instalar dependencias
python install.py

# 2. Probar que todo funciona
python test_simple.py

# 3. Ejecutar aplicación
python run_final.py
```

### Instalación con Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
python install_dependencies.py

# Verificar instalación
python check_installation.py

# Ejecutar simulación
python scripts/run_simulation.py
```

### Instalación Manual

```bash
# Instalar dependencias una por una
pip install PyYAML numpy pandas matplotlib seaborn scikit-learn torch pygame deap noise rich tqdm psutil

# Verificar instalación
python check_installation.py

# Ejecutar simulación
python scripts/run_simulation.py
```

### Comandos Principales

```bash
# Ejecutar aplicación
python run_app.py

# Instalar dependencias
python install.py

# Ejecutar simulación
python scripts/run_simulation.py

# Tests
make test                  # Tests básicos
make test-coverage         # Tests con cobertura

# Desarrollo
make dev-setup             # Configurar entorno completo
make dev-test              # Todas las verificaciones
make lint                  # Linter
make format                # Formatear código

# Limpieza
make clean                 # Limpiar todo
make clean-logs            # Solo logs
make clean-results         # Solo resultados
```

### Configuración

El sistema usa archivos YAML para configuración. El archivo principal es `configs/default.yaml`:

```yaml
simulation:
  map_size: [80, 80]
  population: 100
  ticks_per_epoch: 2000

agent:
  energy_max: 100
  vision_range: 5

ga:
  population_size: 100
  mutation_rate: 0.08
  crossover_rate: 0.7
```

### Experimentos

```bash
# Experimentos predefinidos
make exp-baseline          # Configuración baseline
make exp-high-mutation     # Alta tasa de mutación
make exp-small-world       # Mundo pequeño
make exp-medium-world      # Mundo mediano
make exp-hard-world        # Mundo difícil
```

### Análisis de Resultados

```bash
# Análisis interactivo
make analyze               # Análisis general
make cluster-analysis      # Análisis de clustering
make ablation-study        # Estudio de ablación

# Exportar datos
make export-metrics        # Exportar métricas
make make-gif              # Crear GIF de simulación
```

## 🧩 Arquitectura Implementada

El sistema está completamente implementado con los siguientes módulos:

### ✅ Módulos Completados

- **`src/core/`** - Loop principal, eventos y control de tiempo
- **`src/agents/`** - Sistema de agentes con cerebro neural, sensores y actuadores
- **`src/env/`** - Entorno 2D con física y generación procedural
- **`src/ai/`** - Algoritmos genéticos y evaluación de fitness
- **`src/analytics/`** - Métricas, clustering y logging
- **`src/ui/`** - Interfaz visual con pygame, HUD y controles
- **`src/ecosistema/`** - Aplicación principal integrada
- **`src/utils/`** - Utilidades geométricas, RNG y profiling

### 🔧 Características Implementadas

- **Agentes Autónomos**: Redes neuronales MLP con sensores y actuadores
- **Algoritmo Genético**: Selección, cruce, mutación y elitismo
- **Entorno 2D**: Física, colisiones y generación procedural
- **Análisis**: Clustering, métricas y logging estructurado
- **Interfaz Visual**: Renderizado con pygame, HUD y controles
- **Configuración**: Sistema YAML flexible y reproducible
- **Testing**: Suite de tests con pytest
- **Documentación**: Docstrings y documentación técnica

### 📊 Flujo del Sistema

1. **Inicialización**: Carga configuración, crea mundo y población inicial
2. **Simulación**: Loop principal con ticks, percepción, decisión y acción
3. **Evolución**: Algoritmo genético para mejorar población
4. **Análisis**: Clustering y métricas en tiempo real
5. **Visualización**: Renderizado con pygame y HUD informativo

### 🎯 Resultados Esperados

- **Evolución**: Agentes que aprenden a sobrevivir y reproducirse
- **Emergencia**: Comportamientos complejos emergentes
- **Diversidad**: Múltiples estrategias de supervivencia
- **Adaptación**: Mejora continua del fitness
- **Análisis**: Insights sobre evolución y comportamiento

## 🧭 Lineamientos de Desarrollo

El código sigue estos principios:

- **Arquitectura Modular**: Separación clara de responsabilidades
- **Tipado Fuerte**: Uso de type hints en todo el código
- **Documentación**: Docstrings claros y concisos
- **Testing**: Tests unitarios para cada módulo
- **Reproducibilidad**: Semillas y configuración determinística
- **Performance**: Optimización para simulaciones largas
- **Extensibilidad**: Fácil agregar nuevos componentes

## 🧩 Misión Completada

> **El proyecto `Ecosistema Evolutivo IA` está completamente implementado y funcional.**
>
> ✅ Todos los módulos están implementados
> ✅ Arquitectura modular y extensible
> ✅ Sistema de configuración flexible
> ✅ Interfaz visual completa
> ✅ Análisis y métricas
> ✅ Testing y documentación
> ✅ Scripts de ejecución y Makefile
>
> **El sistema está listo para ejecutar simulaciones y experimentos.**
>
