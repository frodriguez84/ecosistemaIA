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

> ✅ DIAG-06 (2026-11-14, spec *Medir*): `--semilla S` siembra `random` y `numpy` al arrancar, y
> las partículas del dibujo usan su propio generador. La misma semilla da el mismo CSV byte a
> byte, con ventana o sin ella (MEDIR-04 a MEDIR-07). Sin `--semilla` se sortea una, se imprime y
> queda en el CSV.
>
> ✅ DIAG-07 (2026-11-14, spec *Medir*): `main.py` acepta `--sin-ventana`, `--generaciones N`,
> `--semilla S`, `--sin-evolucion` y `--csv RUTA`, que pisan los valores de `config.py` (MEDIR-01
> a MEDIR-03).

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
| DIAG-27 | Con ventana, el zoom (`+` y `-`) cambia la simulación. El reposicionamiento de agentes sortea la `y` entre 20 y `screen_height - 20`, y `screen_height` es el alto de la ventana, que cambia con el zoom; el mundo mide 800 siempre. Por lectura de código: con zoom, la misma semilla puede dar otro CSV que sin ventana. Encontrado el 2026-11-14 al escribir el spec *Limpieza*. | `main.py:326` y `:653`; el zoom en `:416-439` | Limpieza |

> ✅ DIAG-25 (2026-11-14, spec *Medir*): `main.py` y `experimento.py` reconfiguran `stdout` y
> `stderr` a UTF-8 antes del primer `print`. `python main.py --sin-ventana > corrida.log` termina
> sin error y el log tiene los emojis (MEDIR-12); el test de humo corre así.

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
| DIAG-26 | La extensión Pylint marcaba 29 errores en `main.py`, todos `E1101: Module 'pygame' has no '…' member` (`QUIT`, `SRCALPHA`, `KEYDOWN`, `init`…). pygame está compilado en C, y Pylint no carga módulos en C para ver sus miembros salvo que se le permita. No era un error del código: corre sin problemas. Además, el panel mostraba un análisis de `main.py` anterior al bloque A del spec *Medir* (las líneas no coincidían) hasta que Pylint volvió a analizar. Encontrado el 2026-11-14. | `.vscode/settings.json` | Resuelto |

> ✅ DIAG-22 (2026-11-14): `LICENSE` pasa a MIT, por decisión de Fer. El `.env.example` vacío se
> borra en la limpieza.
>
> ✅ DIAG-24 (2026-11-14): `.vscode/settings.json` apunta `python.defaultInterpreterPath` y
> `pylint.interpreter` al Python del `.venv`. Los errores de import desaparecieron del panel.
>
> ✅ DIAG-26 (2026-11-14): `.vscode/settings.json` le pasa a Pylint
> `--extension-pkg-allow-list=pygame`. Pylint volvió a analizar `main.py` y quedaron 0 errores.
> Los warnings que siguen son de estilo o restos: imports y variables sin usar (unas 35 en
> `main.py`), f-strings sin variables y llamadas a métodos `_privados`. Los restos van a la
> limpieza. El "fixme" de la línea 720 es falso: Pylint lee el "Todo" de "Todo el área" como `TODO`.
>
> Encontrado al escribir el spec *Limpieza* (2026-11-14) y sumado a su alcance: a DIAG-18,
> `LearningMonitor.save_data` y `BehaviorClusterer.print_cluster_report`, que nadie llama; a DIAG-19,
> `pandas`, `matplotlib`, `seaborn`, `PyYAML`, `rich`, `tqdm` y `pytest-cov`, que nada importa; a
> DIAG-26, los imports y variables sin usar del resto de `src/`. Con el comando de Pylint del spec,
> son 54 en total: 37 en `main.py`, 13 en `src/` y 4 en el código muerto.

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

<a id="experimento-cinco-semillas"></a>
### Experimento en cinco semillas — 2026-11-14 (MEDIR-18)

**Pregunta:** la misma del experimento anterior, medida con varias semillas: ¿la evolución sube
más que la línea base, semilla por semilla?

**Cómo se corrió:** `python experimento.py` (spec *Medir*): semillas 1 a 5, 20 generaciones, cada
una con evolución y con `--sin-evolucion` (la misma línea base de antes: cerebros al azar en cada
generación). Las 10 corridas a la vez, en 12 núcleos: 523 s. Se repite con el mismo comando: la
misma semilla da el mismo CSV (MEDIR-04 y MEDIR-05). Las semillas 1 y 2 también corrieron en el
experimento chico de MEDIR-13, y sus 10 primeras generaciones son idénticas byte a byte a las de
este.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 20`

**Por modo** (promedio ± desvío muestral entre semillas):

| Modo | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Etapa del puzzle (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Con evolución | 5 | 22.88 ± 1.13 | 42.63 ± 3.27 | 19.74 ± 3.91 | 0.66 ± 0.04 | 3.60 ± 1.22 | 2.94 ± 1.22 | 3.0 ± 1.2 | 0 de 5 |
| Sin evolución | 5 | 21.02 ± 0.57 | 23.30 ± 0.95 | 2.27 ± 1.36 | 0.56 ± 0.04 | 0.82 ± 0.08 | 0.26 ± 0.07 | 1.8 ± 0.4 | 0 de 5 |

**Comparación pareada por semilla:** la evolución subió más que la línea base en 5 de 5 semillas en fitness, y en 5 de 5 en manzanas por agente.

**Por corrida:**

| Semilla | Modo | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Etapa del puzzle | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Con evolución | 20 | 24.18 | 39.69 | 15.51 | 0.71 | 2.13 | 1.42 | 4 | — |
| 1 | Sin evolución | 20 | 21.39 | 22.20 | 0.80 | 0.58 | 0.75 | 0.17 | 1 | — |
| 2 | Con evolución | 20 | 23.37 | 41.45 | 18.09 | 0.64 | 3.46 | 2.82 | 3 | — |
| 2 | Sin evolución | 20 | 21.74 | 22.73 | 0.99 | 0.57 | 0.81 | 0.24 | 2 | — |
| 3 | Con evolución | 20 | 21.38 | 46.69 | 25.31 | 0.65 | 4.99 | 4.34 | 1 | — |
| 3 | Sin evolución | 20 | 21.02 | 24.55 | 3.52 | 0.61 | 0.96 | 0.35 | 2 | — |
| 4 | Con evolución | 20 | 23.42 | 45.50 | 22.08 | 0.68 | 4.65 | 3.97 | 4 | — |
| 4 | Sin evolución | 20 | 20.30 | 23.98 | 3.67 | 0.53 | 0.83 | 0.31 | 2 | — |
| 5 | Con evolución | 20 | 22.08 | 39.80 | 17.72 | 0.61 | 2.76 | 2.15 | 3 | — |
| 5 | Sin evolución | 20 | 20.66 | 23.04 | 2.37 | 0.51 | 0.76 | 0.25 | 2 | — |

**Lectura:**
- **La evolución aprende algo, y no es suerte de una semilla:** subió más que la línea base en las
  cinco, en fitness y en manzanas. La peor semilla con evolución (+15,5 de fitness) sube más de
  cuatro veces que la mejor sin evolución (+3,7). Las manzanas por agente pasan de 0,66 a 3,60 con
  evolución y de 0,56 a 0,82 sin ella.
- **Lo que sube sin evolución es el tiempo:** las generaciones se alargan (+180 ticks cada 4), y
  eso solo da +2,3 de fitness y +0,26 manzanas (LEC-001).
- **Lo que más cambia es cuánto caminan:** la distancia promedio por agente pasa de ~440 a ~1.890
  con evolución (×4,3) y de ~360 a ~590 sin ella (×1,6, por el tiempo).
- **La hipótesis del diagnóstico sigue abierta y este experimento no la puede separar.** La guía
  escrita a mano lleva a la comida a los agentes con fitness > 30 (DIAG-01). El fitness promedio de
  fin de generación termina en 42,6 con evolución, por encima de ese umbral, y en 23,3 sin ella, por
  debajo. Puede ser que la evolución aprenda a caminar y explorar, y que parte de las manzanas las
  ponga la guía. Lo separa el switch guiado/autónomo (ítem 3 del BACKLOG).
- **El puzzle no muestra aprendizaje:** etapa 3,0 ± 1,2 con evolución contra 1,8 ± 0,4 sin ella,
  con mucha dispersión. La semilla 3 con evolución quedó en la etapa 1, por debajo de su línea base.
  Ninguna corrida abrió el cofre. Con un puzzle colectivo que se activa por cercanía (DIAG-03,
  DIAG-04), caminar más alcanza para avanzar más.
- **El fitness máximo sube poco en los dos modos:** de ~58 a ~67 con evolución y de ~58 a ~62 sin
  ella (promedio de las gens 1-5 contra las últimas 5). Lo que sube es el promedio, no el techo.
- **La línea base no hereda nada, como debe (MEDIR-11):** su diversidad se queda en 0,23 las 20
  generaciones. Con evolución baja de 0,23 a ~0,10 en la generación 20 (0,087 a 0,111): la
  población converge rápido. Hay que tenerlo en cuenta para el modo autónomo.
- **Contra la corrida de una semilla del diagnóstico:** aquella dio +12 de fitness con evolución y
  +3 sin ella. Las de ahora van de +15,5 a +25,3 con evolución y de +0,8 a +3,7 sin ella. La
  conclusión es la misma, ahora sin excepciones en cinco semillas. El +12 queda por debajo del
  rango: con una semilla sola no había forma de saber cuánto varía. Aquella corrida no se puede
  repetir, porque la sembró un script que no quedó en el repo.

---

<a id="qa-medir-antes-de-tocar"></a>
## QA /qa-spec — Medir antes de tocar (2026-11-14)
**Veredicto:** APROBADO
**Verificación técnica:** sintaxis ✅ (`compileall` de `main.py`, `config.py`, `experimento.py`,
`src`, `tests`) · tests 11/11 en 17,7 s · build N/A (Python, sin build)
**Método:** tres checkers independientes (Explore/haiku, solo lectura) contra el DoD de
`docs/specs/active/MEDIR_ANTES_DE_TOCAR.md`. Los checkers no podían ejecutar `main.py`. Lo que
pedía una corrida se corrió el mismo día, sin ventana, en el scratchpad: C1, C3, C4, C5 y C10.
Lo que necesita ventana (02 y 06) y el Ctrl+C (07) se verificaron en vivo en la sesión 1 del spec
(bitácora). `main.py` y `renderer.py` no cambiaron desde entonces. Los IDs `MEDIR-NN` son los del
QA manual del spec.

| ID | Criterio | Resultado | Evidencia / Gap |
|----|----------|-----------|-----------------|
| MEDIR-QA-01 | `--sin-ventana --generaciones 2 --semilla 7` corre sin editar `config.py`, sin ventana, y termina tras 2 generaciones | ✅ | Corrida fresca: código 0, 2 filas. Los flags pisan la clase en `main.py:212-215`; `config.py` sin cambios (MEDIR-01) |
| MEDIR-QA-02 | `python main.py` sin flags abre la ventana con los valores de `config.py` | ✅ | En vivo en la sesión 1 (MEDIR-02). Sin flags no hay override (`main.py:212-215`); `config.py:11-12` |
| MEDIR-QA-03 | `--help` lista los cinco flags en español | ✅ | Salida fresca de `--help`; `main.py:146-160`. `usage:` y `options:` quedan en inglés (argparse) (MEDIR-03) |
| MEDIR-QA-04 | Imprime la semilla y la ruta del CSV; sin `--semilla` la sortea y queda en el CSV | ✅ | Corrida fresca sin `--semilla`: sorteó 155792, la imprimió y la escribió en el CSV; repetida con esa semilla, el mismo CSV (MEDIR-07). `main.py:218-242` |
| MEDIR-QA-05 | Misma semilla, CSV idénticos byte a byte, con y sin evolución | ✅ | Corridas frescas: `cmp` idénticos en los dos modos. `test_humo.py:89-90`. Las semillas 1 y 2 de MEDIR-13 y MEDIR-18 dan las mismas 10 primeras generaciones (MEDIR-04, MEDIR-05) |
| MEDIR-QA-06 | Misma semilla con ventana y sin ventana, mismo CSV | ✅ | En vivo en la sesión 1 (MEDIR-06). Las partículas usan su propio generador (`renderer.py:238`); ningún otro código del dibujo consume azar |
| MEDIR-QA-07 | Columnas de la decisión 6, una fila por generación; Ctrl+C deja las generaciones terminadas | ✅ | `main.py:136-141` y `:179-199`; `flush` por fila en `:234-237`. Ctrl+C simulado en la sesión 1 con `_thread.interrupt_main()` (desvío anotado en la bitácora) (MEDIR-08, MEDIR-09) |
| MEDIR-QA-08 | Si se abre el cofre, la fila de esa generación con `cofre = 1` | ✅ | Por lectura de código, como permite MEDIR-20: `main.py:469-480` calcula el fitness, escribe la fila y recién después hace `return`. Ninguna corrida abrió el cofre |
| MEDIR-QA-09 | `--sin-evolucion`: cerebros al azar en cada generación; gen 1 igual a la de con evolución | ✅ | `main.py:627-631`; `test_humo.py:93-100`. La diversidad de la línea base se queda en 0,23 durante 20 generaciones (MEDIR-10, MEDIR-11) |
| MEDIR-QA-10 | Salida redirigida a archivo sin error de encoding | ✅ | Corrida fresca `> r.log`: sin `UnicodeEncodeError` y con emojis. `main.py:207-208` (MEDIR-12) |
| MEDIR-QA-11 | `experimento.py --semillas 1 2 --generaciones 10 --paralelo 2`: 4 CSV, 4 logs y `resumen.md` con las decisiones 13 y 14 | ✅ | `results/experimento_20261114-155725/`. Números recalculados con `awk` (MEDIR-13, MEDIR-15). `--generaciones 5` da un error claro (MEDIR-14) |
| MEDIR-QA-12 | `pytest` pasa (`test_humo.py` y `test_resumen.py`) en menos de 90 s | ✅ | 11 passed en 17,7 s (MEDIR-16) |
| MEDIR-QA-13 | El gate no acepta el código 5 y compila `experimento.py` y `tests/` | ✅ | `.claude/hooks/pre-commit-gate.sh:32` y `:43` (MEDIR-17) |
| MEDIR-QA-14 | El diff no toca `src/agents/`, `src/world/` ni `src/evolution/` | ✅ | `git diff 810d738`: en `src/` solo cambia `src/ui/renderer.py`, que la decisión 3 permite (MEDIR-19) |
| MEDIR-QA-15 | Experimento completo corrido y registrado con su lectura, junto al de una semilla | ✅ | [§ Experimento en cinco semillas](#experimento-cinco-semillas); `results/experimento_20261114-160055/` (MEDIR-18) |
| MEDIR-QA-16 | Docs al día; DIAG-06, DIAG-07 y DIAG-25 ✅ | ✅ | README § Instalación y Uso y § Principios de Diseño; `CLAUDE.md` § Stack, Estructura, Convenciones y Notas; las notas ✅ debajo de las tablas del diagnóstico |

**Observaciones de los checkers que no cambian el veredicto:**
- `_fila_csv` divide por `len(agents)`. No puede valer 0: la lista `agents` es la población entera
  de cada generación (60) y los muertos solo se filtran para los reportes.
- El comando que registra `resumen.md` no lleva `--paralelo`, a propósito: no cambia los resultados.
