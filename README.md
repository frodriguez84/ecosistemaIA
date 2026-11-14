# Ecosistema Evolutivo IA

**Contexto General**

Estás trabajando en el desarrollo de una aplicación completa de simulación llamada **"Ecosistema Evolutivo IA"**, un entorno 2D donde criaturas autónomas aprenden a sobrevivir, adaptarse y evolucionar utilizando múltiples técnicas de **Inteligencia Artificial**:

* **Algoritmos genéticos** - Evolución de poblaciones mediante selección, cruce y mutación
* **Redes neuronales artificiales** - Cerebro de los agentes que toma decisiones autónomas
* **Clustering no supervisado** - Análisis de comportamientos emergentes (K-Means, PCA)
* **Generación procedural del entorno** - Mundo dinámico con fortalezas, puzzle, recursos y obstáculos

El proyecto está desarrollado en **Python 3.11+** y mantiene una **arquitectura modular, extensible y limpia**, siguiendo principios de diseño como:

* *Separation of Concerns*
* *Single Responsibility Principle*
* *Aprendizaje puro* - Sin guía codificada, los agentes aprenden 100% mediante su red neuronal
* Soporte para logging estructurado, reproducibilidad y ejecución por fases

---

## 🎯 Objetivo del Proyecto

Crear un **ecosistema digital autoevolutivo** donde criaturas simuladas:

1. **Perciben su entorno** - Sensores de distancia, energía, comida, obstáculos, objetos del puzzle
2. **Toman decisiones mediante red neuronal** - 5 acciones: avanzar, girar izquierda/derecha, comer, golpear
3. **Son evaluadas por su desempeño** - Fitness basado en supervivencia, comida, exploración, eficiencia y puzzle
4. **Se reproducen mediante algoritmo genético** - Selección (meeting pool + elitismo), cruce, mutación
5. **Dan lugar a nuevas generaciones** - Poblaciones más adaptadas con comportamientos emergentes
6. **Son analizadas mediante clustering** - Identificación de estrategias emergentes (Exploradores, Recolectores, Exitosos)

El resultado es visual, con una interfaz completa que muestra:

* El mapa procedural (pastos, árboles, fortalezas, agua, estanques)
* Criaturas moviéndose y actuando de forma autónoma
* Sistema de puzzle (llaves, puertas, cofre)
* Métricas en tiempo real (generación, fitness promedio, supervivientes, diversidad)

---

## ⚙️ Stack Tecnológico

**Lenguaje:** Python 3.11+

**Librerías Principales:**

* `pygame` → Renderizado 2D, sprites y eventos
* `numpy` → Operaciones matemáticas y arrays
* `scikit-learn` → Clustering (K-Means), PCA, normalización
* `pytest` → Tests

**Entorno y herramientas:**

* Control de versiones con Git
* Requerimientos en `requirements.txt`
* Soporte para ejecución local con render o modo headless (sin visualización)

---

## 🧩 Estructura del Proyecto

```
EcosistemaEvolutivo/
├── main.py                  # Punto de entrada principal
├── config.py               # Configuración centralizada (SimulationConfig)
├── requirements.txt        # Dependencias del proyecto
│
├── src/
│   ├── agents/             # Sistema de agentes
│   │   └── advanced_agent.py    # AdvancedAgent y su red neuronal (SimpleNeuralNetwork)
│   │
│   ├── world/              # Mundo y entorno
│   │   ├── world.py       # Clase World (generación procedural, fortalezas, puzzle)
│   │   └── obstacles.py   # Obstáculos (árboles, muros, agua, huts, etc.)
│   │
│   ├── evolution/          # Algoritmo genético
│   │   └── genetic_algorithm.py  # Selección, cruce, mutación, evolución
│   │
│   ├── analytics/          # Análisis y métricas
│   │   ├── clustering.py        # Clustering de comportamientos (K-Means, PCA)
│   │   └── learning_monitor.py  # Monitoreo de aprendizaje y mejoras
│   │
│   └── ui/                 # Interfaz de usuario
│       ├── renderer.py     # Renderizado con pygame (sprites, partículas)
│       ├── stats.py        # Panel de estadísticas
│       ├── popup.py        # Popup de resumen generacional
│       └── pantalla_final.py  # Resumen final: por consola o en un cuadro
│
├── assets/
│   └── sprites/            # Sprites del juego (agentes, objetos, entorno)
│
├── logs/                   # Logs de métricas y runtime
├── checkpoints/            # Checkpoints de generaciones (opcional)
└── results/                # Resultados y reportes (opcional)
```

---

## 🧱 Funcionalidades Implementadas (por módulos)

### 1. `src/agents/`

* **`advanced_agent.py`**: Clase `AdvancedAgent` con:

  * **Sensores**: 12 percepciones (distancia a comida, obstáculos, objetos del puzzle, energía, dirección)
  * **Red neuronal**: MLP con 2 capas ocultas [24, 18] y 5 salidas (avanzar, girar L/R, comer, golpear)
  * **Sistema de fitness**: Supervivencia + comida + exploración + evitar obstáculos + anti-círculo + puzzle
  * **Acciones**: Movimiento, alimentación, corte de árboles, interacción con puzzle
  * **Aprendizaje puro**: **100% autónomo** - Sin guía codificada, todo basado en decisiones de la red neuronal
* **`SimpleNeuralNetwork`** (en `advanced_agent.py`):

  * Red neuronal MLP propia, con numpy (sin PyTorch)
  * Función de activación: `tanh`
  * Operaciones: forward pass, mutación gaussiana, cruce uniforme, clonación

### 2. `src/world/`

* **`world.py`**: Clase `World` que genera y gestiona:

  * **Generación procedural**: Pastos, árboles, muros, agua, estanques, perímetro
  * **Sistema de fortalezas**: Fortaleza pequeña (4x5 tiles) y grande (6x6 tiles) con muros y puertas
  * **Sistema de puzzle**: Llaves rojas/doradas, puertas (wood/iron), cofre
  * **Recursos**: Comida (manzanas), árboles que pueden cortarse, huts destructibles
  * **Estanque móvil**: Estanque que se regenera dinámicamente
* **`obstacles.py`**:

  * Tipos de obstáculos: `tree`, `wall`, `water`, `hut`
  * Efectos: pérdida de energía, reducción de velocidad, penalización de fitness (agua)
  * Sistema de corte: Árboles y huts pueden cortarse con hacha (requiere acción `hit`)

### 3. `src/evolution/`

* **`genetic_algorithm.py`**: Algoritmo genético completo:
  * **Selección**: Meeting pool (fracción superior por ranking) + elitismo opcional
  * **Cruce**: Uniforme entre genomas (pesos de red neuronal)
  * **Mutación**: Gaussiana con tasa configurable (20%)
  * **Evolución**: Genera nueva población manteniendo mejores individuos

### 4. `src/analytics/`

* **`clustering.py`**: Análisis no supervisado:

  * **Features**: Fitness, comida, exploración, supervivencia
  * **Normalización**: StandardScaler
  * **Reducción de dimensión**: PCA (2 componentes)
  * **Clustering**: K-Means (k=3) - Identifica "Exploradores", "Recolectores", "Exitosos"
  * Ejecución cada 3 generaciones
* **`learning_monitor.py`**: Monitoreo de aprendizaje:

  * Detecta mejoras en comida (absoluta y relativa)
  * Detecta mejoras en fitness
  * Detecta cambios en diversidad genética
  * Reportes en consola con emojis

### 5. `src/ui/`

* **`renderer.py`**:

  * Renderizado con pygame
  * Sistema de sprites (personajes, objetos, entorno)
  * Sistema de partículas para efectos visuales
  * Renderizado de agentes, mundo, HUD
* **`stats.py`**: Panel lateral de estadísticas en tiempo real
* **`popup.py`**: Popup de resumen al final de cada generación
* **`pantalla_final.py`**: Resumen final de la corrida: por consola sin ventana; con ventana, un cuadro sobre el último cuadro de la simulación, hasta ESC o ENTER

### 6. `config.py`

* **`SimulationConfig`**: Clase con todos los parámetros centralizados:
  * Población, generaciones máximas
  * Parámetros del algoritmo genético
  * Arquitectura de red neuronal
  * Sistema de puzzle (recompensas, umbrales)
  * Sistema de agua (penalizaciones, energía)
  * Sistema de corte (árboles, huts)
  * Sistema adaptativo de tiempo (ticks por generación)

---

## 🧬 Flujo General del Sistema

### Inicialización

1. **Carga configuración** desde `config.py` (SimulationConfig)
2. **Genera mundo procedural**:
   * Pastos, árboles, muros, agua, estanques
   * Fortalezas con puertas
   * Llaves, cofre (spawn según generación)
   * Perímetro del mapa
3. **Inicializa población** con redes neuronales aleatorias

### Loop de Simulación (por generación)

1. **Cada tick (600-2000 ticks/generación, adaptativo)**:

   * **Percepción**: Cada agente percibe su entorno (10 sensores)
   * **Decisión**: Red neuronal procesa percepciones → 5 acciones
   * **Acción**: Agente ejecuta acciones (mover, girar, comer, golpear)
   * **Efectos del entorno**: Agua reduce energía/fitness, estanques restauran energía
   * **Interacciones**: Cortar árboles/huts, recoger llaves, abrir puertas, abrir cofre
   * **Muerte**: Si energía ≤ 0, agente muere
2. **Al finalizar la generación**:

   * **Cálculo de fitness**: Supervivencia + comida + exploración + obstáculos + anti-círculo + puzzle
   * **Ranking**: Ordenar agentes por fitness
   * **Clustering** (cada 3 generaciones): Análisis de comportamientos emergentes
   * **Algoritmo genético**:
     * Selección (meeting pool)
     * Cruce uniforme
     * Mutación gaussiana
     * Nueva población
   * **Resumen**: Popup con estadísticas de la generación
   * **Reinicio**: Nuevo mundo, nueva población evolucionada
3. **Condición de fin**:

   * Alcanzar `MAX_GENERATIONS` O
   * Abrir el cofre (objetivo principal)

---

## 🧠 Inteligencia Artificial (Detalles)

### Red Neuronal (Cerebro del Agente)

* **Tipo**: MLP (Multi-Layer Perceptron)
* **Arquitectura**:
  * Input: 10 sensores (distancia comida, obstáculos, puzzle, energía, dirección)
  * Hidden: 2 capas [24, 18] neuronas
  * Output: 5 acciones (move_forward, turn_left, turn_right, eat, hit)
* **Activación**: `tanh` (todas las capas)
* **Pesos**: Mutables por algoritmo genético
* **Aprendizaje**: **100% puro** - Sin guía codificada, decisiones completamente autónomas

### Algoritmo Genético

* **Población**: 60 agentes (configurable)
* **Fitness**: Combinación de:
  * Supervivencia (edad) - Cap: 23
  * Comida (sqrt) - Multiplicador: 12.0
  * Exploración (log) - Multiplicador: 12.0, Cap: 15.0
  * Evitar obstáculos - Multiplicador: 0.20
  * Anti-círculo (movimiento eficiente) - Multiplicador: 10.0
  * Puzzle (llaves, puertas, cofre) - Recompensas acumuladas
  * Penalizaciones (agua) - Sin límite, proporcional al tiempo
* **Selección**: Meeting pool (90% superior) + elitismo opcional
* **Cruce**: Uniforme (90% tasa)
* **Mutación**: Gaussiana (20% tasa)
* **Elitismo**: 0 (se puede configurar)

### Clustering (Análisis No Supervisado)

* **Features extraídas**:
  * Fitness total
  * Comida consumida
  * Distancia recorrida
  * Edad (supervivencia)
* **Preprocesamiento**:
  * Normalización: `StandardScaler`
  * Reducción de dimensión: `PCA` (2 componentes, 95% varianza)
* **Algoritmo**: K-Means con k=3
* **Clusters identificados**:
  * **Exploradores**: Alta exploración, fitness medio
  * **Recolectores**: Alta comida, exploración media
  * **Exitosos**: Alto fitness en todas las métricas
* **Frecuencia**: Cada 3 generaciones

---

## 🎮 Sistema de Puzzle

El ecosistema incluye un sistema complejo de puzzle que los agentes deben aprender a resolver:

### Elementos del Puzzle

1. **Fortalezas**: Dos tipos (pequeña 4x5, grande 6x6) con muros y puertas
2. **Llaves**:
   * **Red Key**: Aparece desde gen 5 (configurable), recompensa: 2 fitness
   * **Gold Key**: Dentro de fortaleza grande, recompensa: 10 fitness
3. **Puertas**:
   * **Wood Door**: Requiere 3 golpes, recompensa: 10 fitness
   * **Iron Door**: Requiere 3 golpes, recompensa: 20 fitness
4. **Cofre**: Objetivo final, recompensa: 85 fitness (alto para garantizar fitness 60+ al completar)

### Flujo del Puzzle

1. **Gen 1-4**: Agentes aprenden tareas básicas (comer, sobrevivir, explorar)
2. **Gen 5+**: Aparecen llaves rojas en el mundo
3. **Aprendizaje emergente**: Los agentes aprenden a:
   * Recoger llave roja
   * Golpear puerta de madera (acción `hit` > 0.5)
   * Entrar a fortaleza pequeña
   * Recoger llave dorada
   * Golpear puerta de hierro
   * Entrar a fortaleza grande
   * Abrir cofre
4. **Fin del juego**: Al abrir el cofre, la simulación termina

### Mecánica de Aprendizaje

* **Sin guía codificada**: Los agentes descubren el puzzle mediante prueba y error
* **Recompensas**: Fitness positivo por cada acción exitosa del puzzle
* **Penalizaciones**: Agua penaliza fitness si pasan mucho tiempo en ella
* **Red neuronal**: Debe aprender a usar la acción `hit` cuando está cerca de puertas/árboles

---

## 🌊 Sistema de Agua

* **Efectos cuando un agente está en agua**:
  * **Energía**: Pierde 0.05 adicional por tick (además del consumo normal 0.05)
  * **Velocidad**: Reducida a 50% (SPEED_REDUCTION = 0.5)
  * **Fitness**: Penalización de 5 puntos por tick (sin límite máximo)
* **Propósito**: Incentivar a los agentes a evitar el agua
* **Aprendizaje**: Los agentes evolucionan para minimizar tiempo en agua

---

## 🌳 Sistema de Corte

### Árboles

* **Activación**: Cuando quedan ≤30 manzanas en el mundo
* **Mecánica**: Agente con hacha puede cortar árbol (acción `hit` > 0.5)
* **Golpes requeridos**: 2
* **Recompensas**:
  * Fitness: +7
  * Comida: +20 manzanas generadas

### Huts (Casitas)

* **Activación**: Cuando quedan ≤20 manzanas en el mundo
* **Mecánica**: Agente con hacha puede destruir hut (acción `hit` > 0.5)
* **Golpes requeridos**: 4
* **Recompensas**:
  * Fitness: +15
  * Comida: +30 manzanas generadas

---

## ⚙️ Configuración

El sistema usa `config.py` con la clase `SimulationConfig`:

```python
class SimulationConfig:
    # === SIMULACIÓN ===
    POPULATION_SIZE = 60
    MAX_GENERATIONS = 50
    HEADLESS_MODE = True  # False para visualización
  
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.20
    CROSSOVER_RATE = 0.90
    MEETING_POOL_FRACTION = 0.90
  
    # === RED NEURONAL ===
    INPUT_SIZE = 10
    HIDDEN_SIZE = [24, 18]
    OUTPUT_SIZE = 5  # move_forward, turn_left, turn_right, eat, hit
  
    # === SISTEMA DE PUZZLE ===
    RED_KEY_SPAWN_GEN = 5
    RED_KEY_REWARD = 2
    GOLD_KEY_REWARD = 10
    DOOR_OPEN_REWARD = 10
    DOOR_IRON_OPEN_REWARD = 20
    CHEST_REWARD = 85
  
    # === SISTEMA DE AGUA ===
    WATER_FITNESS_PENALTY = 5
    WATER_ENERGY_LOSS = 0.05
  
    # ... más parámetros
```

### Parámetros Clave

* **`POPULATION_SIZE`**: Tamaño de la población (60)
* **`MAX_GENERATIONS`**: Generaciones máximas (50)
* **`HEADLESS_MODE`**: `True` = sin render (rápido), `False` = con visualización
* **`MUTATION_RATE`**: Tasa de mutación (0.20 = 20%)
* **`BASE_TICKS`**: Ticks iniciales por generación (600)
* **`TICKS_INCREMENT_AMOUNT`**: Incremento de ticks (200)
* **`TICKS_INCREMENT_FREQUENCY`**: Cada cuántas generaciones incrementar (2)

---

## 🚀 Instalación y Uso

### Requisitos Previos

- Python 3.11+
- pip

### Instalación

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd EcosistemaEvolutivo

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar simulación
python main.py
```

### Modo de Ejecución

El sistema puede ejecutarse en dos modos:

* **Modo visual** (por defecto, `HEADLESS_MODE = False`):

  * Renderizado completo con pygame
  * Panel de estadísticas en tiempo real
  * Popups de resumen generacional
  * Más lento pero visualmente informativo
* **Modo headless** (`--sin-ventana`, o `HEADLESS_MODE = True`):

  * Sin renderizado visual
  * Solo output por consola
  * Mucho más rápido para experimentos
  * Ideal para múltiples corridas

### Ejecutar Simulación

```bash
# Modo visual, con los valores de config.py
python main.py

# Sin ventana (rápido), 20 generaciones, semilla fija
python main.py --sin-ventana --generaciones 20 --semilla 7

# Línea base: cada generación arranca con cerebros al azar, sin heredar nada
python main.py --sin-ventana --generaciones 20 --semilla 7 --sin-evolucion
```

Los flags pisan los valores de `config.py` (`python main.py --help` los lista):

| Flag | Qué hace |
|------|----------|
| `--sin-ventana` | Corre sin abrir ventana. Pisa `HEADLESS_MODE`. |
| `--generaciones N` | Cantidad de generaciones. Pisa `MAX_GENERATIONS`. |
| `--semilla S` | Semilla del azar. Sin ella se sortea una y se imprime al arrancar. |
| `--sin-evolucion` | Línea base: cada generación arranca con cerebros al azar y no hereda nada. |
| `--csv RUTA` | Dónde escribir el CSV. Por defecto, `results/corrida_s<semilla>_<evolucion\|sin_evolucion>.csv`. |

Toda corrida, con ventana o sin ella, deja un CSV con una fila por generación: fitness, manzanas,
vivos, distancia, diversidad y estado del puzzle. **La misma semilla da el mismo CSV byte a byte.**

### Experimento: con evolución contra sin evolución

```bash
# Semillas 1 a 5, 20 generaciones, tantas corridas a la vez como núcleos menos uno
python experimento.py

# Más chico
python experimento.py --semillas 1 2 --generaciones 10 --paralelo 2
```

Corre cada semilla con evolución y sin evolución (línea base) y deja en
`results/experimento_<AAAAMMDD-HHMMSS>/` el CSV y el log de cada corrida, más un `resumen.md`:
fitness y manzanas por agente en las primeras y las últimas 5 generaciones, la etapa del puzzle, y
en cuántas semillas la evolución subió más que la línea base. El completo tarda unos 9 minutos
en una máquina de 12 núcleos.

### Tests

```bash
python -m pytest -q
```

Un test de humo corre `main.py` con sus flags reales (y verifica que la misma semilla dé el mismo
CSV), y otro verifica las cuentas del resumen del experimento.

---

## 📊 Resultados y Análisis

### Métricas Generadas

Cada corrida genera:

* **Métricas por consola**:

  * Fitness promedio/máximo/mínimo por generación
  * Supervivientes, comida total, distancia recorrida
  * Análisis de clustering (cada 3 generaciones)
  * Monitoreo de aprendizaje (mejoras detectadas)
* **Logs estructurados** (opcional):

  * `logs/metrics/` - Métricas por generación
  * `logs/runtime/` - Logs de runtime
* **Checkpoints** (opcional):

  * `checkpoints/` - Estados de generaciones

### Análisis de Comportamiento

El sistema incluye análisis automático:

1. **Clustering**: Identifica 3 tipos de estrategias emergentes
2. **Monitoreo de aprendizaje**: Detecta mejoras en comida y fitness
3. **Diversidad genética**: Monitorea convergencia prematura

### Resultados Esperados

* **Evolución natural**: Fitness promedio aumenta gradualmente
* **Comportamientos emergentes**: Agentes aprenden a comer, explorar, resolver puzzle
* **Diversidad**: Múltiples estrategias coexisten
* **Resolución del puzzle**: Agentes eventualmente abren el cofre (fitness 60+)
* **Adaptación**: Evitan agua, cortan árboles cuando hay poca comida

---

## 🧩 Arquitectura Implementada

### ✅ Módulos Completados

- **`src/agents/`** - Sistema de agentes con red neuronal y aprendizaje puro
- **`src/world/`** - Mundo procedural con puzzle y recursos
- **`src/evolution/`** - Algoritmo genético completo (selección, cruce, mutación)
- **`src/analytics/`** - Métricas, clustering y monitoreo de aprendizaje
- **`src/ui/`** - Interfaz visual con pygame, estadísticas y popups

### 🔧 Características Implementadas

- **Aprendizaje puro**: 100% autónomo, sin guía codificada
- **Red neuronal MLP**: 2 capas ocultas, 5 salidas (incluye acción `hit`)
- **Sistema de puzzle**: Fortalezas, llaves, puertas, cofre
- **Sistema de corte**: Árboles y huts destructibles
- **Sistema de agua**: Penalizaciones proporcionales
- **Algoritmo genético**: Meeting pool, cruce uniforme, mutación gaussiana
- **Clustering**: K-Means con PCA para identificar estrategias
- **Tiempo adaptativo**: Ticks por generación aumentan progresivamente
- **Fitness natural**: Sin dependencia de generación, basado en rendimiento real

### 📊 Flujo del Sistema

1. **Inicialización**: Carga `config.py`, genera mundo procedural, crea población inicial
2. **Simulación**: Loop con ticks, percepción → decisión → acción
3. **Fitness**: Cálculo basado en rendimiento real (supervivencia, comida, exploración, puzzle)
4. **Evolución**: Algoritmo genético mejora población
5. **Análisis**: Clustering y monitoreo de aprendizaje (cada 3 generaciones)
6. **Visualización**: Renderizado con pygame y HUD informativo (si no está en headless)

---

## 🧭 Principios de Diseño

El código sigue estos principios:

- **Arquitectura Modular**: Separación clara de responsabilidades
- **Aprendizaje Puro**: Sin guía codificada, agentes aprenden 100% autónomamente
- **Configuración Centralizada**: Todo en `config.py` (SimulationConfig)
- **Reproducibilidad**: `--semilla S` siembra todo el azar; la misma semilla da el mismo CSV byte a byte
- **Performance**: Optimizado para simulaciones largas
- **Extensibilidad**: Fácil agregar nuevos elementos (obstáculos, recompensas, etc.)

---

## 🧩 Estado del Proyecto

> **El proyecto `Ecosistema Evolutivo IA` está completamente implementado y funcional.**

✅ **Todos los módulos están implementados**✅ **Arquitectura modular y extensible**✅ **Sistema de configuración centralizado**✅ **Interfaz visual completa**✅ **Análisis y métricas**✅ **Aprendizaje puro sin guía codificada**✅ **Sistema de puzzle complejo**✅ **Clustering de comportamientos emergentes**

> **El sistema está listo para ejecutar simulaciones y experimentos.**

---

## 📝 Notas Técnicas

### Aprendizaje Puro

* Los agentes **NO reciben guía codificada** hacia comida, árboles o puzzle
* Todas las decisiones son tomadas por la red neuronal basándose en percepciones
* El fitness recompensa comportamientos exitosos, pero no "dirige" el comportamiento
* Única excepción: Limitación física de giro excesivo para evitar círculos infinitos

### Sistema de Fitness

* **Sin dependencia de generación**: El fitness no aumenta artificialmente con las generaciones
* **Basado en rendimiento real**: Supervivencia, comida, exploración, eficiencia, puzzle
* **Penalizaciones proporcionales**: Agua penaliza según tiempo transcurrido (sin límite)
* **Recompensas del puzzle**: Acumuladas durante la generación, sumadas al fitness final

### Sistema Adaptativo de Tiempo

* **BASE_TICKS**: 600 ticks iniciales
* **Incremento**: +200 ticks cada 2 generaciones
* **Propósito**: Permitir más tiempo para tareas complejas en generaciones avanzadas
* **Efecto**: Fitness puede aumentar naturalmente con más tiempo disponible

---

## 🎯 Objetivo del Puzzle

El objetivo principal del ecosistema es que los agentes aprendan a resolver el puzzle:

1. **Aprendizaje básico** (Gen 1-4): Comer, sobrevivir, explorar
2. **Descubrimiento del puzzle** (Gen 5+): Aparecen llaves, agentes empiezan a interactuar
3. **Resolución completa**: Agentes aprenden secuencia completa (llave → puerta → cofre)
4. **Fitness final**: Cuando abren el cofre, fitness promedio debe ser ≥60

La simulación termina cuando el cofre es abierto, independientemente de la generación.

---

## 📚 Referencias y Conceptos

- **Algoritmos Genéticos**: Selección, cruce, mutación, elitismo
- **Redes Neuronales**: MLP, forward pass, backpropagation (implícito vía GA)
- **Clustering**: K-Means, PCA, normalización
- **Aprendizaje por Refuerzo Evolutivo**: Fitness como señal de recompensa
- **Emergencia**: Comportamientos complejos emergentes de reglas simples

---

**Desarrollado para el curso de Inteligencia Artificial - UCEMA**
