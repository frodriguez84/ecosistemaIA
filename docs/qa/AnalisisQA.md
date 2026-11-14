# QA y hallazgos — Ecosistema Evolutivo IA

Evidencia de QA y bugs encontrados, con IDs trazables. **No se borra ni se condensa el
histórico.** Formato e IDs: [`../AGENTES.md`](../AGENTES.md). Cada hallazgo abierto tiene su
línea en [`../product/BACKLOG.md`](../product/BACKLOG.md) (a través del spec que lo resuelve).

---

<a id="diagnostico-inicial"></a>
## Diagnóstico inicial — 2026-11-14

Revisión al retomar el proyecto, un año después (último commit de código: `6efef30`,
2025-11-10). El código se leyó entero en sus partes centrales (`main.py`, `advanced_agent.py`,
`genetic_algorithm.py`, `world.py`). Se corrió sin ventana con el `.venv` existente
(Python 3.11.9, pygame 2.6.1, numpy 2.3.4). **Corre sin errores**, a ~10 s por generación con
60 agentes.

**Columna "Va a":** el spec que lo resuelve. *Medir* = medir antes de tocar · *Limpieza* =
limpieza sin cambiar comportamiento · *Aprendizaje* = modo guiado y modo autónomo. Orden y
estado en el BACKLOG.

### Lo que el README promete y el código no hace

| ID | Hallazgo | Evidencia | Va a |
|----|----------|-----------|------|
| DIAG-01 | **No es "aprendizaje puro".** `decide()` conduce a mano: con fitness > 30 gira al agente hacia la manzana más cercana y fuerza `eat = 0.9`; con fitness > 65, en el 40% de los ticks, lo empuja hacia puertas y llaves. | `src/agents/advanced_agent.py:168-317` | Aprendizaje |
| DIAG-02 | **La red no ve el puzzle.** Ningún sensor da dirección ni distancia a llave, puerta, cofre o hacha. Los sensores 8 y 9 son estado global del mundo (si *alguien* agarró una llave o abrió una puerta). El sensor 4 da distancia al obstáculo más cercano, sin dirección. | `advanced_agent.py:91-160` | Aprendizaje |
| DIAG-03 | **No existe la acción "golpear".** `OUTPUT_SIZE = 4` (avanzar, girar izq., girar der., comer). Agarrar hacha y llaves, golpear puertas y cortar árboles pasa solo, por cercanía, en cada tick. El README habla de 5 salidas. | `main.py:338-355`, `config.py:38` | Aprendizaje |
| DIAG-04 | **El puzzle es colectivo y persiste entre generaciones.** Llaves recogidas, puertas abiertas y hacha pasan a la generación siguiente. Cualquier agente abre la puerta si *otro* agarró la llave. | `src/world/world.py:431-458`, `world.py:986-1014` | Aprendizaje |
| DIAG-05 | **No hay presión de supervivencia.** El consumo es 0.05/tick fijo en el código (`AGENT_ENERGY_CONSUMPTION = 0.10` se ignora) y comer da +30 fijo (`AGENT_ENERGY_GAIN_FOOD = 8` se ignora). En 960 ticks se pierden 48 de 100 de energía: supervivencia 100% en todas las generaciones medidas. | `advanced_agent.py:353`, `advanced_agent.py:533` | Aprendizaje |
| DIAG-06 | **No es reproducible.** No hay semilla en ningún lado (el README dice "semillas y configuración determinística"). | búsqueda de `seed` en el código | Medir |
| DIAG-07 | **Para correr sin ventana hay que editar `config.py`.** No hay parámetros por línea de comando. | `config.py:11-12` | Medir |

### Bugs

| ID | Hallazgo | Evidencia | Va a |
|----|----------|-----------|------|
| DIAG-08 | La recompensa por cortar árbol o casita se suma a `self.fitness` y el siguiente `_calculate_fitness()` la pisa: **nunca cuenta**. Además el árbol suma 10 fijo, no `TREE_CUT_REWARD` (15). | `advanced_agent.py:554`, `advanced_agent.py:563` | Aprendizaje |
| DIAG-09 | `obstacles_avoided`, `obstacle_avoidance_count` y `total_obstacle_encounters` nunca se incrementan: el término de fitness por obstáculos y la "habilidad de obstáculos" valen siempre 0. | `advanced_agent.py:60-66`, `:749`, `:855` | Aprendizaje |
| DIAG-10 | El sensor de ángulo (`angle / 2π`) no se normaliza: el ángulo acumula giros y el valor sale de [0, 1] sin límite. | `advanced_agent.py:140` | Aprendizaje |
| DIAG-11 | La penalización por agua está topeada en 10 (`penalty_max`); el README dice "sin límite". | `advanced_agent.py:732`, `:768` | Aprendizaje |
| DIAG-12 | Más valores de `config.py` que se ignoran: `VISION_RANGE` (150 fijo), `AGENT_RADIUS` (8 fijo, config dice 6), `AGENT_ENERGY`, la pérdida de energía en el agua (0.05 fija). | `advanced_agent.py:30-50`, `src/world/obstacles.py:45` | Aprendizaje |
| DIAG-13 | El `else` de la "exploración para fitness bajo" cuelga del `if` de la guía de llaves: corre cada vez que esa guía no se activa, no cuando el fitness es bajo. | `advanced_agent.py:308` | Aprendizaje |
| DIAG-14 | El análisis detallado reporta "Supervivencia 120%": divide por `total_agents` con 50 por defecto cuando la clave falta. | `src/analytics/learning_monitor.py:175` | Limpieza |
| DIAG-15 | El resumen final sin ventana dice "Tiempo total: 0.0 minutos" (división entera de ticks). | `main.py:778` | Limpieza |
| DIAG-16 | La pantalla final dice "¡Los agentes evolutivos han completado su misión!" aunque no se haya abierto el cofre. | `main.py:1293` | Limpieza |
| DIAG-17 | La pantalla final recalcula K-Means y redibuja todo en cada vuelta del loop, sin `clock.tick`: CPU al 100% mientras está abierta. | `main.py:906-1308` | Limpieza |
| DIAG-25 | Con la salida redirigida a un archivo (`python main.py > corrida.log`), el primer `print` con emoji tira `UnicodeEncodeError`: en Windows la salida redirigida usa cp1252. Encontrado el 2026-11-14 al escribir el spec *Medir*. | `main.py:133`; prueba: `python -c "print('🎨')" > x.txt` falla con el Python del `.venv` | Medir |

### Limpieza y deuda

| ID | Hallazgo | Evidencia | Va a |
|----|----------|-----------|------|
| DIAG-18 | Código muerto: `src/agents/brain/` (PyTorch; ni siquiera importa porque falta `policy.py`), `src/analytics/metrics.py` (no se importa), la rama de zonas `"safe"` (nunca se generan). Las pociones **no** son código muerto: se generan 3-5 por mundo y curan al 100%, pero el README no las menciona. | `src/agents/brain/__init__.py:7`, `obstacles.py:46`, `world.py:206-220` | Limpieza |
| DIAG-19 | Dependencias sin uso en `requirements.txt`: `torch` (varios GB), `deap`, `argparse` (es de la librería estándar). `pytest` figuraba pero no estaba instalado en el `.venv` (se instaló el 2026-11-14 para el gate). | `requirements.txt` | Limpieza |
| DIAG-20 | 16 `.pyc` commiteados, varios de módulos que ya no existen (`actuators`, `sensors`, `policy`, `hud`…), aunque `.gitignore` los excluye. | `git ls-files \| grep pyc` | Limpieza |
| DIAG-21 | Duplicación: el reposicionamiento de agentes está copiado dos veces en `main.py`; la búsqueda de posición válida, cinco veces en `genetic_algorithm.py`; el dibujo del mundo, dos veces (loop y pantalla final). `main()` es un loop de ~600 líneas. | `main.py:196-247` y `:512-563`; `genetic_algorithm.py:136-337` | Limpieza |
| DIAG-22 | `LICENSE` y `.env.example` existen pero están vacíos. | — | Decisión de Fer |
| DIAG-23 | `world.py` importa `pygame` y no lo usa. | `src/world/world.py:6` | Limpieza |
| DIAG-24 | La extensión Pylint de VS Code marcaba "Unable to import 'pygame'" en `advanced_agent.py` y `world.py`: corría con el Python global de la Microsoft Store, que no tiene `pygame`. No era un error del código. | `.vscode/settings.json` | Resuelto |

> ✅ DIAG-22 (2026-11-14): `LICENSE` pasa a MIT, por decisión de Fer. El `.env.example` vacío se
> borra en la limpieza.
>
> ✅ DIAG-24 (2026-11-14): `.vscode/settings.json` apunta `python.defaultInterpreterPath` y
> `pylint.interpreter` al Python del `.venv`. Los errores de import desaparecieron del panel.

### Experimento: con evolución contra sin evolución

**Pregunta:** ¿la evolución aprende algo, o lo que se ve sale de la guía escrita a mano y del
puzzle que se acumula?

**Cómo se corrió:** 20 generaciones, semilla 7 (`random` y `numpy`), sin ventana (nota¹). La
línea base reemplaza `GeneticAlgorithm.evolve` por
`_create_random_population()`: cada generación arranca con cerebros al azar, así que nada se
hereda. Todo lo demás (mundo, guía, puzzle persistente, tiempo adaptativo) es igual.

| | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Puzzle en la gen 20 |
|---|---|---|---|---|---|
| Con evolución | 21.4 | 33.7 | 0.56 | 1.62 | llave roja, puerta de madera, llave dorada, puerta de hierro |
| Sin evolución | 21.2 | 24.5 | 0.52 | 0.92 | llave roja, puerta de madera, llave dorada |

**Lectura:**
- La evolución **sí aprende algo**: +12 de fitness contra +3. El +3 sin evolución sale de que las
  generaciones se alargan (+180 ticks cada 4 generaciones).
- El avance del puzzle **no prueba aprendizaje**: con cerebros al azar llegó casi igual de lejos,
  porque el puzzle se acumula entre generaciones y se activa por cercanía (DIAG-03, DIAG-04).
- El fitness máximo no muestra tendencia en ninguna de las dos (~55-74).
- Comen muy poco: menos de 2 manzanas por agente por generación, con 70 en el mapa.
- **Es una sola corrida con una semilla:** indicio, no conclusión. Medirlo bien (varias semillas)
  es parte del spec *Medir*.
- **Hipótesis a medir:** lo que evoluciona es sobre todo "caminar derecho y explorar" (el bonus
  anti-círculo y la exploración llevan rápido el fitness por encima de 30) y desde ahí la guía
  escrita a mano hace comer. Se prueba repitiendo el experimento con la guía apagada.

¹ La config usada es la del commit `6efef30` con `MAX_GENERATIONS` sobrescrito por el script de
la corrida. El script vivió en el scratchpad de la sesión y no quedó en el repo: el spec *Medir*
lo reemplaza con parámetros por línea de comando.
