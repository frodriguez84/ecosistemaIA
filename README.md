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
* *Dos modos para comparar* - **guiado** (la red más una conducción escrita a mano hacia la comida y el puzzle) y **autónomo** (solo la red)
* *Reproducibilidad* - La misma semilla da el mismo CSV byte a byte

---

## 🎯 Objetivo del Proyecto

Crear un **ecosistema digital autoevolutivo** donde criaturas simuladas:

1. **Perciben su entorno** - 11 sensores: energía, comida, obstáculos, posición, rumbo, su etapa del puzzle y una brújula a su próximo paso
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
├── main.py                  # Punto de entrada: flags, semilla, CSV y loop de simulación
├── config.py               # Configuración centralizada (SimulationConfig)
├── experimento.py          # Los dos modos, con evolución y sin ella, en varias semillas
├── requirements.txt        # Dependencias del proyecto
│
├── tests/                  # Tests (pytest)
│
├── src/
│   ├── agents/             # Sistema de agentes
│   │   └── advanced_agent.py    # AdvancedAgent y su red neuronal (SimpleNeuralNetwork)
│   │
│   ├── world/              # Mundo y entorno
│   │   ├── world.py       # Clase World (generación procedural, fortalezas, puzzle)
│   │   ├── obstacles.py   # Obstáculos (árboles, muros, agua, huts, etc.)
│   │   └── camino.py      # La brújula por el camino (BRUJULA_CAMINO)
│   │
│   ├── evolution/          # Algoritmo genético
│   │   └── genetic_algorithm.py  # Selección, cruce, mutación, evolución
│   │
│   ├── analytics/          # Análisis y métricas
│   │   ├── boletin.py           # Boletín final, formato de números y escala de los gráficos
│   │   ├── clustering.py        # Clustering de comportamientos (K-Means, PCA)
│   │   ├── learning_monitor.py  # Monitoreo de aprendizaje y mejoras
│   │   └── registro.py          # Registro de la corrida: historia, hitos, mejor agente, mapa de calor
│   │
│   └── ui/                 # Interfaz de usuario
│       ├── renderer.py     # Renderizado con pygame (sprites, partículas)
│       ├── stats.py        # Panel derecho: datos, gráficos de fitness y manzanas, puzzle y teclas
│       ├── graficos.py     # Gráfico de líneas con escala automática (panel y pantalla final)
│       ├── avisos.py       # Avisos arriba del mundo: fin de generación y primera vez de cada paso
│       ├── fuentes.py      # Fuentes de las pantallas (Pixelify Sans e Inter)
│       └── pantalla_final.py  # El boletín final: por consola y, con ventana, en una pantalla
│
├── assets/
│   ├── fonts/              # Fuentes de las pantallas (licencia OFL, ver LEEME.md)
│   └── sprites/            # Sprites del juego (agentes, objetos, entorno)
│
└── results/                # CSV y logs de las corridas (no se versionan)
```

---

## 🧱 Funcionalidades Implementadas (por módulos)

### 1. `src/agents/`

* **`advanced_agent.py`**: Clase `AdvancedAgent` con:

  * **Sensores**: 11 percepciones (energía, comida, obstáculos, posición, rumbo, etapa del puzzle y brújula al próximo paso)
  * **Red neuronal**: MLP con 2 capas ocultas [24, 16] y 5 salidas (avanzar, girar L/R, comer, golpear)
  * **Sistema de fitness**: Supervivencia + comida + exploración + anti-círculo + puzzle + cortes − agua, con los pesos en `config.py`
  * **Acciones**: Movimiento, alimentación y golpear (puertas, cofre, árboles y casitas)
  * **Puzzle propio**: cada agente tiene su etapa del puzzle y su hacha
  * **Dos modos** (`MODO` en `config.py`, `--modo`): en el **autónomo** decide solo la red; en el **guiado**, la red más una conducción escrita a mano (ver Notas Técnicas)
* **`SimpleNeuralNetwork`** (en `advanced_agent.py`):

  * Red neuronal MLP propia, con numpy (sin PyTorch)
  * Función de activación: `tanh`
  * Operaciones: forward pass, mutación gaussiana, cruce uniforme, clonación

### 2. `src/world/`

* **`world.py`**: Clase `World` que genera y gestiona:

  * **Generación procedural**: Pastos, árboles, muros, agua, estanques, perímetro
  * **Sistema de fortalezas**: Fortaleza pequeña (5x5 tiles) y grande (6x6 tiles) con muros y puertas
  * **Sistema de puzzle**: Llave roja, puerta de madera, llave dorada, puerta de hierro y cofre; el avance es de cada agente y se reinicia en cada generación
  * **Recursos**: Comida (manzanas), árboles que pueden cortarse, huts destructibles
  * **Estanque móvil**: Estanque que se regenera dinámicamente
* **`camino.py`**: la brújula por el camino (`BRUJULA_CAMINO`): por etapa del puzzle, una grilla con la distancia por el camino libre al próximo paso y su rumbo. La recompensa por acercarse por el camino (`ACERCARSE_CAMINO`) lee la misma distancia
* **`obstacles.py`**:

  * Tipos de obstáculos: `tree`, `wall`, `water`, `hut`
  * Efectos: pérdida de energía, reducción de velocidad, penalización de fitness (agua)
  * Sistema de corte: Árboles y huts pueden cortarse con hacha (requiere acción `hit`)

### 3. `src/evolution/`

* **`genetic_algorithm.py`**: Algoritmo genético completo:
  * **Selección**: Meeting pool (fracción superior por ranking) + elitismo opcional
  * **Cruce**: Uniforme entre genomas (pesos de red neuronal)
  * **Mutación**: Gaussiana con tasa configurable (30%)
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
* **`registro.py`**: Registro de la corrida, en memoria y sin azar (no cambia el CSV):

  * La fila del CSV de cada generación terminada
  * Los hitos: la primera vez en la corrida que un agente llega a cada paso del puzzle, con su línea en la consola (`🏆 ¡Primera llave roja! Agente 12, generación 2, segundo 8.3`)
  * El mejor agente de la corrida (el récord de fitness, no el de la última generación)
  * El mapa de calor de por dónde caminan: celdas de `HEATMAP_CELL_SIZE` (16 px), la generación 1 y la última
* **`boletin.py`**: El boletín final, que la consola imprime al terminar, con ventana y sin ella: la generación 1 contra el promedio de las últimas 5 (fitness, manzanas, edad y recorrido), hasta qué paso del puzzle llegaron, el cofre una sola vez, el mejor agente y cuánto del mapa recorrieron. Más el formato de los números (`31,2`, `2.220`) y la escala automática de los gráficos

### 5. `src/ui/`

* **`renderer.py`**:

  * Renderizado con pygame
  * Sistema de sprites (personajes, objetos, entorno)
  * Sistema de partículas para efectos visuales
  * Renderizado de agentes, mundo, HUD
* **`stats.py`**: Panel derecho, la columna entera: generación, modo, tiempo, vivos, muertos y comida; los gráficos de fitness (promedio y máximo) y de manzanas por agente de cada generación terminada; el puzzle de esta generación y de la anterior; las teclas
* **`graficos.py`**: Gráfico de líneas con la escala automática de `boletin.py` (nunca de 0 a 100 fijo); lo usan el panel y la pantalla final
* **`avisos.py`**: Avisos arriba del mundo, que no tapan ni frenan nada: el fin de cada generación (2,5 s, con la diferencia contra la anterior) y la primera vez que un agente llega a cada paso del puzzle (4 s, hasta 3 a la vez)
* **`fuentes.py`**: Carga las fuentes de `assets/fonts/` (Pixelify Sans para los títulos, Inter para el resto); si falta una, `main.py` con ventana se corta al arrancar
* **`pantalla_final.py`**: El boletín de la corrida: por consola, con ventana y sin ella; con ventana, además, en una pantalla sobre el último cuadro del mundo oscurecido, hasta ESC o ENTER: los cuatro números (la generación 1 contra las últimas 5), los gráficos con los pasos del puzzle marcados, el mapa de calor de la generación 1 y de la última, el embudo del puzzle y el mejor agente de la corrida

### 6. `config.py`

* **`SimulationConfig`**: Clase con todos los parámetros centralizados:
  * Población, generaciones máximas
  * Modo (`MODO`: `"guiado"` o `"autonomo"`)
  * Agente y energía (consumo, comida, radio, visión, costo de golpear)
  * Pesos del fitness
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
   * Fortalezas con puertas, llave dorada y cofre
   * Llave roja y hacha, en un lugar nuevo en cada generación
   * Perímetro del mapa
3. **Inicializa población** con redes neuronales aleatorias, ubicada con el mapa ya listo

### Loop de Simulación (por generación)

1. **Cada tick (960 ticks por generación al principio, 180 más cada 4 generaciones)**:

   * **Percepción**: Cada agente percibe su entorno (11 sensores)
   * **Decisión**: Red neuronal procesa percepciones → 5 acciones (en el modo guiado, más la guía escrita a mano)
   * **Acción**: Agente ejecuta acciones (mover, girar, comer, golpear)
   * **Efectos del entorno**: El agua resta energía, frena y penaliza el fitness; las pociones devuelven la energía
   * **Interacciones**: Recoger llaves y hacha por contacto; golpear puertas, cofre, árboles y huts
   * **Muerte**: Si energía ≤ 0, agente muere
2. **Al finalizar la generación**:

   * **Cálculo de fitness**: Supervivencia + comida + exploración + anti-círculo + puzzle + cortes − agua
   * **Ranking**: Ordenar agentes por fitness
   * **Clustering** (cada 3 generaciones): Análisis de comportamientos emergentes
   * **Algoritmo genético**:
     * Selección (meeting pool)
     * Cruce uniforme
     * Mutación gaussiana
     * Nueva población
   * **Resumen**: el reporte por consola y, con ventana, un aviso arriba del mundo con el fitness y las manzanas contra la generación anterior
   * **Reinicio**: Nuevo mapa, puzzle reiniciado, nueva población (evolucionada, o al azar en la línea base)
3. **Condición de fin**:

   * Alcanzar `MAX_GENERATIONS`. Abrir el cofre no termina la corrida: se cuenta cuántos agentes lo abrieron

---

## 🧠 Inteligencia Artificial (Detalles)

### Red Neuronal (Cerebro del Agente)

* **Tipo**: MLP (Multi-Layer Perceptron)
* **Arquitectura**:
  * Input: 11 sensores
  * Hidden: 2 capas [24, 16] neuronas
  * Output: 5 acciones (move_forward, turn_left, turn_right, eat, hit). Avanzar, comer y golpear se activan por encima de 0,5; el giro es (derecha − izquierda) × 0,12
* **Activación**: `tanh` (todas las capas)
* **Pesos**: Mutables por algoritmo genético
* **Sensores**, en orden: 1 energía; 2 distancia y 3 dirección a la manzana más cercana; 4 distancia al obstáculo más cercano; 5 x; 6 y; 7 rumbo; 8 etapa del puzzle / 5; 9 dirección al próximo paso del puzzle; 10 manzanas disponibles; 11 distancia al próximo paso del puzzle. Las distancias se miden contra el rango de visión (150 px, `VISION_RANGE`)
* **Quién decide**: en el modo autónomo, solo la red; en el guiado, la red más la guía escrita a mano (ver Notas Técnicas)

### Algoritmo Genético

* **Población**: 60 agentes (`POPULATION_SIZE`)
* **Fitness**, de 0 a 100, con los pesos en `config.py`:
  * Supervivencia: 0,010 × ticks vividos (`FITNESS_SURVIVAL`), con tope de 10 (`FITNESS_SURVIVAL_MAX`)
  * Comida: 10 × raíz de las manzanas comidas (`FITNESS_FOOD`)
  * Exploración: 10 × log(1 + distancia / 350) (`FITNESS_EXPLORATION`), con tope de 15 (`FITNESS_EXPLORATION_MAX`)
  * Anti-círculo (rectitud, giros suaves, lugares nuevos): 18 × su puntaje (`FITNESS_ANTI_CIRCLE`), si recorrió más de 100 px
  * Puzzle y cortes: la recompensa de cada paso, para el agente que lo dio (ver Sistema de Puzzle y Sistema de Corte)
  * Acercarse, solo con la recompensa prendida (`RECOMPENSA_ACERCARSE`, `--acercarse`): 10 × (pasos que dio + avance en el paso actual, de 0 a 1) (`FITNESS_ACERCARSE`). Ver Ayudas para aprender el puzzle
  * Agua: se resta la penalización acumulada, con tope de 10 (`WATER_PENALTY_MAX`)
  * Tope por tiempo vivido: de 50 al nacer a 100 desde los 960 ticks (`BASE_TICKS`)
* **Selección**: Meeting pool (60% superior por ranking) + élite de 1
* **Cruce**: Uniforme (95% tasa)
* **Mutación**: Gaussiana (30% tasa)
* **Inmigración**: 3 agentes nuevos al azar cada 6 generaciones

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

Cada agente hace su propio puzzle, en cinco pasos, y todo vuelve a cero en cada generación.

### Elementos del Puzzle

1. **Fortalezas**: Dos (pequeña 5x5, grande 6x6) con muros y una puerta cada una. Están siempre en el mismo lugar, en todas las semillas y generaciones: la pequeña arriba a la izquierda y la grande abajo a la derecha (con las fortalezas móviles, más abajo, cambian de lugar desde la generación 2)
2. **Llaves** (por contacto; quedan en el mapa para los demás):
   * **Llave roja**: En un lugar nuevo en cada generación, desde la generación 1 (`RED_KEY_SPAWN_GEN`). Recompensa: 10 (`RED_KEY_REWARD`)
   * **Llave dorada**: Dentro de la fortaleza pequeña. Recompensa: 25 (`GOLD_KEY_REWARD`)
3. **Puertas** (golpeando, a menos de 25 px de su centro, con una espera entre golpe y golpe):
   * **Puerta de madera** (fortaleza pequeña): 2 golpes (`DOOR_HITS_TO_OPEN`). Recompensa: 12 (`DOOR_OPEN_REWARD`)
   * **Puerta de hierro** (fortaleza grande): 3 golpes (`DOOR_IRON_HITS_TO_OPEN`). Recompensa: 35 (`DOOR_IRON_OPEN_REWARD`)
4. **Cofre** (golpeando, en contacto; dentro de la fortaleza grande): Recompensa: 50 (`CHEST_REWARD`)

### Flujo del Puzzle

1. **Etapa del agente**, de 0 a 5: llave roja → puerta de madera → llave dorada → puerta de hierro → cofre. Cada paso pide el anterior.
2. **Una puerta es pared para cada agente hasta que él la abre**: abrirla no la abre para los demás. Con ventana, se dibuja abierta si algún agente de la generación la abrió.
3. **Golpear** es la quinta salida de la red (> 0,5). Cuesta 0,05 de energía por tick (`HIT_ENERGY_COST`), golpee algo o no.
4. **Brújula**: los sensores 9 y 11 apuntan al próximo paso del agente, en línea recta (con la brújula por el camino, por el camino libre más corto); con el cofre abierto dan 0 y 1.
5. **Reinicio**: cada generación arranca con todos los agentes en la etapa 0 (con el currículo, en la 1 hasta la generación 15) y sin hacha, las puertas y el cofre cerrados, y la llave roja y el hacha en lugares nuevos (las fortalezas, solo con las fortalezas móviles).
6. **Abrir el cofre no termina la corrida**: la consola, el panel, la pantalla final y el CSV dicen cuántos agentes llegaron a cada paso.

### Mecánica de Aprendizaje

* **En el modo autónomo, sin guía**: la red tiene que descubrir el puzzle por prueba y error, con la brújula y golpear
* **En el modo guiado**: con fitness > 65, en el 40% de los ticks la guía lo empuja hacia su próximo paso y aprieta golpear al alinearse
* **Recompensas**: Fitness por cada paso, para el agente que lo dio

### Ayudas para aprender el puzzle

Tres switches en `config.py`, apagados por defecto e independientes, que valen para los dos modos, y un cuarto que cambia cómo mide la recompensa por acercarse. Apagados, la corrida es la de siempre.

* **Recompensa por acercarse** (`RECOMPENSA_ACERCARSE`, `--acercarse`): suma al fitness 10 × (pasos que dio + avance en el paso actual) (`FITNESS_ACERCARSE`). El avance va de 0 a 1 y cuenta lo más cerca que llegó al objetivo de la brújula, (distancia al empezar el paso − la más corta) / distancia al empezar; en las puertas, la mitad es ese camino y la otra mitad, los golpes que contaron sobre los necesarios. Quedarse cerca no suma más que pasar una vez, y alejarse después no resta
* **Acercarse por el camino** (`ACERCARSE_CAMINO`, `--acercarse-camino`, va con `--acercarse`): el avance mide la distancia por el camino libre, la de la brújula por el camino, no la recta; en el objetivo, sin camino o sin celda libre cerca, la recta. Usa la grilla de la brújula por el camino, pero no pide prenderla. Sin la recompensa por acercarse no hace nada. No es una columna del CSV: en el nombre del archivo, `_acercarse` pasa a ser `_acercarse_camino`, y el panel dice "acercarse por el camino"
* **Currículo** (`CURRICULO`, `--curriculo`): las generaciones 1 a 15 (`CURRICULO_HASTA_GENERACION`) nacen con la llave roja, sin su premio, y desde la 16 sin ella. El mapa no cambia: la brújula apunta a la puerta de madera, que sigue siendo pared hasta que el agente la abre
* **Deslizar contra lo que choca** (`DESLIZAR`, `--deslizar`): si el paso choca (una pared, un árbol, una casita, una puerta que no abrió, el perímetro o el estanque), el agente se mueve por el eje libre: primero solo en x y, si no, solo en y. Apagado, se queda donde está. Cambia todo el caminar, también hacia la comida. No es una columna del CSV: va en el nombre del archivo (`_deslizar`)
* **Lo dado al nacer no es un logro**: los avisos de hito, la primera vez del boletín y los pasos de la recompensa cuentan solo los pasos que el agente dio. Las columnas `agentes_*` del CSV cuentan quién llegó al menos a cada paso, también con la llave dada; la columna `etapa_inicial` dice con qué etapa nació la generación

**Fortalezas móviles** (`FORTALEZAS_MOVILES`, `--fortalezas-moviles`, apagado por defecto, en los dos modos). No es una ayuda: desde la generación 2, las dos fortalezas van a un lugar al azar en cada generación, con sus puertas, la llave dorada y el cofre, así la puerta se encuentra con la brújula y no con una ruta aprendida de memoria. La generación 1 queda como siempre. Cada fortaleza queda lejos del borde con el frente de su puerta, y las dos separadas; el estanque y el resto del mapa se generan después y las esquivan. No es una columna del CSV: va en el nombre del archivo (`_fortalezas_moviles`), y el panel lo dice en su renglón

**Brújula por el camino** (`BRUJULA_CAMINO`, `--brujula-camino`, apagado por defecto, en los dos modos). Los sensores 9 y 11 siguen el camino libre más corto al próximo paso, no la recta, que desde la llave dorada cruza las paredes de la fortaleza chica. Por etapa, una grilla de celdas de 5 px con lo que deja pasar el choque de esa etapa (las puertas que no abrió son pared) y la distancia por el camino, euclídea alrededor de las paredes; el sensor 9 apunta contra su gradiente y el 11 es esa distancia. En el objetivo y sin camino, la recta. La grilla se arma al empezar cada generación: un árbol talado después no la cambia. La recompensa por acercarse sigue midiendo la recta, salvo con acercarse por el camino. No es una columna del CSV: va en el nombre del archivo (`_brujula_camino`), y el panel lo dice en su renglón

---

## 🔋 Energía

* Cada agente arranca con 100 (`AGENT_ENERGY`, que también es el máximo) y gasta 0,10 por tick (`AGENT_ENERGY_CONSUMPTION`): sin comer, le alcanza para 1.000 ticks
* Comer suma 8 (`AGENT_ENERGY_GAIN_FOOD`), sin pasar del máximo. Se come con la salida `eat` > 0,5, a menos de 20 px de una manzana
* Golpear cuesta 0,05 por tick (`HIT_ENERGY_COST`); el agua, 0,05 más; una poción devuelve la energía al máximo
* Con energía 0, el agente muere. Las generaciones duran 960 ticks al principio y 180 más cada 4: desde la 5, el que no come no llega al final

---

## 🌊 Sistema de Agua

* **Efectos cuando un agente está en agua**:
  * **Energía**: Pierde 0,05 adicional por tick (`WATER_ENERGY_LOSS`), además del consumo normal (0,10)
  * **Velocidad**: Reducida al 80%
  * **Fitness**: Penalización de 5 puntos por tick (`WATER_FITNESS_PENALTY`), con tope de 10 (`WATER_PENALTY_MAX`)
* **Propósito**: Incentivar a los agentes a evitar el agua

---

## 🌳 Sistema de Corte

### Árboles

* **Activación**: Cuando quedan ≤30 manzanas en el mundo (`TREE_CUTTING_THRESHOLD`)
* **Mecánica**: Un agente con hacha propia (la agarra por contacto; queda en el mapa para los demás) corta golpeando (acción `hit` > 0,5)
* **Golpes requeridos**: 3 (fijo en el código: el `TREE_HITS_TO_CUT` de `config.py` no se lee)
* **Recompensas**:
  * Fitness: +15 (`TREE_CUT_REWARD`)
  * Comida: +20 manzanas generadas

### Huts (Casitas)

* **Activación**: Cuando quedan ≤20 manzanas en el mundo
* **Mecánica**: Un agente con hacha propia destruye la hut golpeando (acción `hit` > 0,5)
* **Golpes requeridos**: 4
* **Recompensas**:
  * Fitness: +15 (`HUT_CUT_REWARD`)
  * Comida: +30 manzanas generadas

---

## ⚙️ Configuración

El sistema usa `config.py` con la clase `SimulationConfig`:

```python
class SimulationConfig:
    # === SIMULACIÓN ===
    POPULATION_SIZE = 60
    MAX_GENERATIONS = 50
    HEADLESS_MODE = False  # True = sin ventana
    MODO = "guiado"        # "guiado" o "autonomo"
  
    # === ALGORITMO GENÉTICO ===
    MUTATION_RATE = 0.30
    CROSSOVER_RATE = 0.95
    MEETING_POOL_FRACTION = 0.60
  
    # === RED NEURONAL ===
    INPUT_SIZE = 11
    HIDDEN_SIZE = [24, 16]
    OUTPUT_SIZE = 5  # move_forward, turn_left, turn_right, eat, hit
  
    # === AGENTE ===
    AGENT_ENERGY = 100.0
    AGENT_ENERGY_CONSUMPTION = 0.10
    AGENT_ENERGY_GAIN_FOOD = 8
    HIT_ENERGY_COST = 0.05
  
    # === SISTEMA DE AGUA ===
    WATER_FITNESS_PENALTY = 5
    WATER_PENALTY_MAX = 10
    WATER_ENERGY_LOSS = 0.05

    # === FITNESS ===
    FITNESS_FOOD = 10.0
    FITNESS_EXPLORATION = 10.0
    FITNESS_SURVIVAL = 0.010
    FITNESS_ANTI_CIRCLE = 18.0

    # === SISTEMA DE PUZZLE ===
    RED_KEY_SPAWN_GEN = 1
    RED_KEY_REWARD = 10
    GOLD_KEY_REWARD = 25
    DOOR_OPEN_REWARD = 12
    DOOR_IRON_OPEN_REWARD = 35
    CHEST_REWARD = 50
  
    # ... más parámetros
```

### Parámetros Clave

* **`POPULATION_SIZE`**: Tamaño de la población (60)
* **`MAX_GENERATIONS`**: Generaciones máximas (50)
* **`HEADLESS_MODE`**: `True` = sin render (rápido), `False` = con visualización
* **`MODO`**: `"guiado"` o `"autonomo"` (ver Notas Técnicas)
* **`MUTATION_RATE`**: Tasa de mutación (0.30 = 30%)
* **`BASE_TICKS`**: Ticks iniciales por generación (960)
* **`TICKS_INCREMENT_AMOUNT`**: Incremento de ticks (180)
* **`TICKS_INCREMENT_FREQUENCY`**: Cada cuántas generaciones incrementar (4)

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

Se puede correr con ventana o sin ella (aparte del modo guiado o autónomo):

* **Con ventana** (por defecto, `HEADLESS_MODE = False`):

  * Renderizado completo con pygame
  * Panel con los gráficos de fitness y manzanas en tiempo real
  * Avisos de fin de generación y de cada paso del puzzle, sin tapar el mundo
  * Más lento pero visualmente informativo
* **Sin ventana** (`--sin-ventana`, o `HEADLESS_MODE = True`):

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

# Modo autónomo: decide solo la red, sin la guía escrita a mano
python main.py --sin-ventana --generaciones 20 --semilla 7 --modo autonomo
```

Los flags pisan los valores de `config.py` (`python main.py --help` los lista):

| Flag | Qué hace |
|------|----------|
| `--sin-ventana` | Corre sin abrir ventana. Pisa `HEADLESS_MODE`. |
| `--generaciones N` | Cantidad de generaciones. Pisa `MAX_GENERATIONS`. |
| `--semilla S` | Semilla del azar. Sin ella se sortea una y se imprime al arrancar. |
| `--sin-evolucion` | Línea base: cada generación arranca con cerebros al azar y no hereda nada. |
| `--modo guiado\|autonomo` | `guiado`: la red más la conducción escrita a mano; `autonomo`: solo la red. Pisa `MODO`. |
| `--acercarse` | Prende la recompensa por acercarse al próximo paso del puzzle. Pisa `RECOMPENSA_ACERCARSE`. |
| `--curriculo` | Prende el currículo: las primeras generaciones nacen con la llave roja. Pisa `CURRICULO`. |
| `--deslizar` | Si el paso choca, el agente se mueve por el eje libre. Pisa `DESLIZAR`. |
| `--fortalezas-moviles` | Desde la generación 2, las fortalezas cambian de lugar en cada generación. Pisa `FORTALEZAS_MOVILES`. |
| `--brujula-camino` | La brújula sigue el camino libre más corto al próximo paso, no la recta. Pisa `BRUJULA_CAMINO`. |
| `--acercarse-camino` | La recompensa por acercarse mide la distancia por el camino libre, no la recta. Va con `--acercarse`. Pisa `ACERCARSE_CAMINO`. |
| `--csv RUTA` | Dónde escribir el CSV. Por defecto, `results/corrida_s<semilla>_<modo>[_acercarse[_camino]][_curriculo][_deslizar][_fortalezas_moviles][_brujula_camino]_<evolucion\|sin_evolucion>.csv`. |

Toda corrida, con ventana o sin ella, deja un CSV con una fila por generación: modo, si la
recompensa por acercarse estaba prendida, la etapa con la que nació la generación, fitness,
manzanas, vivos, edad, distancia, diversidad y cuántos agentes llegaron a cada paso del puzzle. **La
misma semilla da el mismo CSV byte a byte.**

### Experimento: los dos modos, con evolución y sin ella

```bash
# Semillas 1 a 5, 20 generaciones, los dos modos, tantas corridas a la vez como núcleos menos uno
python experimento.py

# Más chico: un solo modo
python experimento.py --semillas 1 2 --generaciones 10 --modos autonomo --paralelo 2
```

Corre cada semilla en cada modo, con evolución y sin evolución (línea base), y deja en
`results/experimento_<AAAAMMDD-HHMMSS>/` el CSV y el log de cada corrida, más un `resumen.md`. Por
grupo (modo × evolución): fitness y manzanas por agente en las primeras y las últimas 5
generaciones, supervivencia, agentes con llave roja, etapa máxima del puzzle y cofre. Y tres
comparaciones pareadas por semilla: en cada modo, si la evolución supera a la línea base; y si el
guiado tiene más que el autónomo. Con 5 semillas y 30 generaciones (20 corridas) tardó 16,5
minutos en una máquina de 12 núcleos. `--acercarse`, `--curriculo`, `--deslizar`, `--fortalezas-moviles`, `--brujula-camino` y `--acercarse-camino` pasan a todas las
corridas; el resumen dice cuáles estaban prendidas, suma por corrida la puerta de madera y la llave roja por
1.000 px de recorrido, y en el autónomo aplica el criterio del ítem 5 del BACKLOG (¿aprende a pasar
la puerta de madera?).

### Tests

```bash
python -m pytest -q
```

Un test de humo corre `main.py` con sus flags reales, en los dos modos (y verifica que la misma
semilla dé el mismo CSV). Los demás prueban que las reglas de `config.py` mandan, el puzzle por
agente, el switch de modos, los reportes y las cuentas del resumen del experimento.

---

## 📊 Resultados y Análisis

### Métricas Generadas

Cada corrida genera:

* **Métricas por consola**:

  * Fitness promedio/máximo/mínimo por generación
  * Supervivientes, comida total, distancia recorrida
  * Análisis de clustering (cada 3 generaciones)
  * Monitoreo de aprendizaje (mejoras detectadas)
* **CSV de la corrida** en `results/`, con una fila por generación

### Análisis de Comportamiento

El sistema incluye análisis automático:

1. **Clustering**: Identifica 3 tipos de estrategias emergentes
2. **Monitoreo de aprendizaje**: Detecta mejoras en comida y fitness
3. **Diversidad genética**: Monitorea convergencia prematura

### Resultados

Los experimentos, con su lectura, están en [`docs/qa/AnalisisQA.md`](docs/qa/AnalisisQA.md). Lo
que se mide es cada modo contra su línea base sin evolución, con la misma semilla y en varias
semillas: que el fitness suba con las generaciones no alcanza, porque la línea base también sube.

---

## 🧩 Arquitectura Implementada

### ✅ Módulos Completados

- **`src/agents/`** - Sistema de agentes con red neuronal, en modo guiado o autónomo
- **`src/world/`** - Mundo procedural con puzzle y recursos
- **`src/evolution/`** - Algoritmo genético completo (selección, cruce, mutación)
- **`src/analytics/`** - Métricas, clustering y monitoreo de aprendizaje
- **`src/ui/`** - Interfaz visual con pygame: panel, avisos y pantalla final

### 🔧 Características Implementadas

- **Dos modos**: guiado (la red más una guía escrita a mano) y autónomo (solo la red)
- **Red neuronal MLP**: 2 capas ocultas, 5 salidas (incluye acción `hit`)
- **Sistema de puzzle**: Fortalezas, llaves, puertas, cofre; el avance es de cada agente
- **Sistema de corte**: Árboles y huts destructibles
- **Sistema de agua**: Penalización con tope
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
- **Dos modos comparables**: El switch cambia solo la guía escrita a mano; todo lo demás es igual
- **Configuración Centralizada**: Los parámetros en `config.py` (SimulationConfig); los umbrales de la guía quedan en el código
- **Reproducibilidad**: `--semilla S` siembra todo el azar; la misma semilla da el mismo CSV byte a byte
- **Performance**: Optimizado para simulaciones largas
- **Extensibilidad**: Fácil agregar nuevos elementos (obstáculos, recompensas, etc.)

---

## 🧩 Estado del Proyecto

> **El proyecto `Ecosistema Evolutivo IA` está completamente implementado y funcional.**

✅ **Todos los módulos están implementados**✅ **Arquitectura modular y extensible**✅ **Sistema de configuración centralizado**✅ **Interfaz visual completa**✅ **Análisis y métricas**✅ **Modo guiado y modo autónomo**✅ **Sistema de puzzle complejo**✅ **Clustering de comportamientos emergentes**

> **El sistema está listo para ejecutar simulaciones y experimentos.**

---

## 📝 Notas Técnicas

### Modo guiado y modo autónomo

* **Autónomo** (`--modo autonomo`): `decide()` devuelve la salida de la red recortada a [0, 1], sin nada más y sin consumir azar
* **Guiado** (`--modo guiado`, el de por defecto): la red más una conducción escrita a mano, que **no es aprendizaje**:
  * Con fitness > 30, lleva al agente hacia la manzana más cercana (o hacia un árbol, si tiene hacha y queda menos del 60% de la comida) y aprieta comer o golpear al alinearse
  * Con fitness ≤ 30, cada 100 ticks le cambia el rumbo al azar
  * Con fitness > 65, en el 40% de los ticks, lo empuja hacia su próximo paso del puzzle y aprieta golpear al alinearse
  * Siempre: ruido de ±0,02 en las salidas, un rumbo al azar en el 2% de los ticks, un reflejo que recorta los giros cuando gira sin parar y ruido al girar
* **Lo demás es igual en los dos**: mundo, puzzle, sensores, golpear, fitness y los valores de `config.py`. El giro (× 0,12, reducido × 0,6 si pasa de 0,08) es del cuerpo, común a los dos. Así, guiado contra autónomo mide la guía, y cada modo contra su línea base sin evolución mide el aprendizaje

### Sistema de Fitness

* **Sin dependencia de generación**: El fitness no aumenta artificialmente con las generaciones
* **Basado en rendimiento real**: Supervivencia, comida, exploración, eficiencia, puzzle
* **Pesos en `config.py`**: `FITNESS_*`, con la forma de la fórmula fija (raíz, logaritmo, topes)
* **Agua**: La penalización se acumula por tick, con tope de 10 (`WATER_PENALTY_MAX`)
* **Recompensas del puzzle**: Acumuladas durante la generación, sumadas al fitness final

### Sistema Adaptativo de Tiempo

* **BASE_TICKS**: 960 ticks iniciales
* **Incremento**: +180 ticks cada 4 generaciones
* **Propósito**: Permitir más tiempo para tareas complejas en generaciones avanzadas
* **Efecto**: Fitness puede aumentar naturalmente con más tiempo disponible

---

## 🎯 Objetivo del Puzzle

El objetivo principal del ecosistema es que los agentes aprendan a resolver el puzzle:

1. **Comer y sobrevivir**: La energía alcanza para 1.000 ticks sin comer; desde la generación 5, el que no come no llega al final
2. **El puzzle**: La llave roja está desde la generación 1, y cada agente avanza su propia etapa
3. **Resolución completa**: llave roja → puerta de madera → llave dorada → puerta de hierro → cofre
4. **Medición**: `experimento.py` dice en cuántas semillas cada modo supera a su línea base

Abrir el cofre no termina la simulación: se cuenta cuántos agentes lo abrieron y en qué generación pasó la primera vez.

---

## 📚 Referencias y Conceptos

- **Algoritmos Genéticos**: Selección, cruce, mutación, elitismo
- **Redes Neuronales**: MLP, forward pass, backpropagation (implícito vía GA)
- **Clustering**: K-Means, PCA, normalización
- **Aprendizaje por Refuerzo Evolutivo**: Fitness como señal de recompensa
- **Emergencia**: Comportamientos complejos emergentes de reglas simples

---

## 📄 Licencia

El código es MIT ([LICENSE](LICENSE)). Las fuentes de `assets/fonts/` (Pixelify Sans e Inter) no:
tienen la SIL Open Font License 1.1, con su texto y su origen en
[assets/fonts/LEEME.md](assets/fonts/LEEME.md).

---

**Desarrollado para el curso de Inteligencia Artificial - UCEMA**
