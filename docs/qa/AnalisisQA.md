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
>
> ✅ DIAG-27 (2026-11-14, spec *Limpieza*, bloque B): el reposicionamiento pasó a
> `_reposicionar_agentes` (`main.py`), que sortea la `y` con el alto del mundo
> (`world.screen_height`, 800), no con el de la ventana. Medido con el zoom inyectado (dos `+` en la
> generación 1; LIMPIEZA-13): antes y después del cambio, el CSV de 3 generaciones es igual a la
> línea base y ningún sorteo usó el alto agrandado. El control no dio distinto porque, en la
> práctica, ese sorteo no corre: `fix_agent_positions` ya saca antes a los agentes de fortalezas y
> obstáculos, y el reposicionamiento solo mueve a alguien si `find_safe_position` cayó a
> `(100, 100)`, cosa que no pasa en ninguna corrida de la línea base. Por eso la rama se ejercitó
> aparte, contra el bloque viejo: con alto 800, mismas posiciones, mismos sorteos y mismo estado del
> azar; con 867 (la ventana agrandada), el código viejo sorteaba distinto.
>
> ✅ DIAG-14 (2026-11-14, spec *Limpieza*, bloque C): `record_generation` guarda `total_agents` y la
> "Tasa:" divide por eso. `tests/test_reportes.py` lo prueba con 60 y con 45 vivos de 60 (100.0% y
> 75.0%); con el código de antes fallaba (120.0% y 90.0%). En los logs de la verificación, cada
> "Tasa:" vale `vivos` / 60 de la fila del CSV de esa generación (LIMPIEZA-14).
>
> ✅ DIAG-15 (2026-11-14, spec *Limpieza*, bloque C): el tiempo pasa a ser el simulado: `_simular`
> suma los ticks de cada generación (también la parcial del cofre), o sea, la columna `ticks` del
> CSV, y la consola y la pantalla dicen `Tiempo simulado`, con división real. Dos generaciones dan
> 0.5 minutos (antes 0.0); `test_humo.py` lo verifica, y fallaba con el código de antes. Con ventana,
> la pantalla final muestra el mismo número (LIMPIEZA-15).
>
> ✅ DIAG-16 (2026-11-14, spec *Limpieza*, bloque C): eran cuatro textos, no uno: "Resultado:
> Completado", "Cofre: SI" (fijo), "Primera vez con cofre abierto: Gen N" (salía con la generación
> actual) y el mensaje final. Ahora dependen de si se abrió el cofre; sin cofre dicen "Resultado: No
> logrado", "Cofre: NO", "El cofre no se abrió en ninguna generación" y "Los agentes no llegaron a
> abrir el cofre". Los textos se arman en `textos_del_cuadro` (`src/ui/pantalla_final.py`), sin
> dibujar, y `tests/test_reportes.py` la prueba con cofre y sin cofre. Control: la captura de la
> pantalla con ventana antes del cambio, con los cuatro textos (LIMPIEZA-16).
>
> ✅ DIAG-17 (2026-11-14, spec *Limpieza*, bloque C): con la pantalla final abierta, **56 s de CPU
> en 10 s** antes del cambio: no un núcleo sino más de cinco, porque el K-Means del clustering
> (multihilo) se recalculaba en cada cuadro. Ahora todo se calcula y se dibuja una vez, y el loop
> solo atiende eventos y muestra, con `clock.tick(30)`: **0,19 s en 10 s**. La pantalla queda quieta
> (dos capturas a un segundo de distancia, idénticas) y su fondo es el mundo con el dibujo del loop
> (LIMPIEZA-17, LIMPIEZA-18).

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
> *Corrección (2026-11-14, al arrancar el bloque A):* con el mismo comando y el mismo código dan 53:
> 37 en `main.py`, 12 en `src/` y 4 en el código muerto.
>
> ✅ DIAG-18 (2026-11-14, spec *Limpieza*, bloque A): se borraron `src/agents/brain/`,
> `src/analytics/metrics.py`, la rama de zonas `"safe"` (`obstacles.py` y los dos `elif` que la
> atendían en `advanced_agent.py`), `LearningMonitor.save_data` (con su llamada comentada en
> `main.py`) y `BehaviorClusterer.print_cluster_report`. CSV y log iguales a la línea base
> (LIMPIEZA-09).
>
> ✅ DIAG-19 (2026-11-14, spec *Limpieza*, bloque A): `requirements.txt` queda con `pygame`,
> `numpy`, `scikit-learn` y `pytest`; salen los diez que nada importa. Una instalación limpia en un
> entorno nuevo (Python 3.11.9) da `pytest` verde (11 tests) y el chequeo rápido con CSV y log
> idénticos a la línea base, aunque instaló versiones más nuevas que el `.venv`: numpy 2.4.6 (2.3.4),
> scikit-learn 1.9.1 (1.7.2), scipy 1.17.1 (1.16.2); pygame 2.6.1 y pytest 9.2.0 iguales
> (LIMPIEZA-07). Fijar versiones no hace falta por ahora.
>
> ✅ DIAG-20 (2026-11-14, spec *Limpieza*, bloque A): `git rm --cached` de los `.pyc` trackeados
> (eran 15, no 16); los de `brain/` se fueron con la carpeta. `.gitignore` ya los excluía
> (LIMPIEZA-08).
>
> ✅ DIAG-22 (2026-11-14, spec *Limpieza*, bloque A): `.env.example` borrado.
>
> ✅ DIAG-23 (2026-11-14, spec *Limpieza*, bloque A): `world.py` ya no importa `pygame`. Con él se
> fueron los otros imports y variables sin usar de `src/` (W0611, W0612 y W0404): el comando de
> Pylint del spec da 0 en `src/`. Quedan los 37 de `main.py`, para los bloques B y C.
>
> DIAG-21, parcial (2026-11-14, spec *Limpieza*, bloque B): en `genetic_algorithm.py`, la búsqueda
> de posición válida es un solo método (`_posicion_libre`, con `_choca` y `_posicion_de_respaldo`) y
> `random.randint(50, 900)` aparece 3 veces (eran 6); el archivo pasó de 443 a 299 líneas. En
> `main.py`, el reposicionamiento y el cálculo de ticks están una vez cada uno, y el reporte de fin
> de generación y los datos del cuadro de resumen salieron de `_simular`. CSV y log iguales a la
> línea base (LIMPIEZA-03, LIMPIEZA-11), también con los métodos de selección que la config no usa
> (`elitism`, `tournament` y uno desconocido), comparados antes y después. Falta el dibujo del mundo
> (bloque C).
>
> DIAG-26, parcial (2026-11-14, spec *Limpieza*, bloque B): salieron los 6 imports y variables sin
> usar de `main.py` que no están en la pantalla final. Quedan 31, todos en `show_final_screen`
> (bloque C).
>
> ✅ DIAG-21 (2026-11-14, spec *Limpieza*, bloque C): el mundo se dibuja con una sola función,
> `dibujar_mundo` (`src/ui/renderer.py`), que usan el loop y la pantalla final; el halo del hacha y
> el de la llave roja son una función. Comparada píxel por píxel contra el bloque viejo, sacado de
> `HEAD:main.py`, en ocho ticks y con comida comida y llave recogida: idéntica (control: el pasto
> corrido un píxel se detecta). La pantalla final se mudó a `src/ui/pantalla_final.py`; `main.py`
> pasó de 1.391 líneas (al arrancar el bloque C) a 725.
>
> ✅ DIAG-26 (2026-11-14, spec *Limpieza*, bloque C): los 31 de `show_final_screen` se fueron con su
> reescritura. El comando de Pylint del spec da 0 hallazgos (LIMPIEZA-10).

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

---

<a id="qa-limpieza-sin-cambiar-comportamiento"></a>
## QA /qa-spec — Limpieza sin cambiar comportamiento (2026-11-14)
**Veredicto:** APROBADO
**Verificación técnica:** sintaxis ✅ (`compileall` de `main.py`, `config.py`, `src`) · tests 17/17 en
20,4 s · build N/A (Python, sin build) · Pylint del spec: 0 hallazgos
**Método:** tres checkers independientes (Explore/haiku, solo lectura) contra el DoD de
`docs/specs/active/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md`: código y duplicación, reportes y tests,
docs y alcance. Los checkers no ejecutaban nada. Las corridas de las tres sesiones siguen en
`results/` (fuera de git) y se volvieron a comparar el mismo día con el comparador del spec
(verificado contra el bloque del spec con `diff`). Para las líneas de log que la decisión 18 deja
cambiar, un script del scratchpad verificó cada "Tasa:" del análisis detallado contra `vivos` / 60
de su fila del CSV, y el tiempo simulado contra la suma de `ticks` / 3.600. Su control: con los logs
del código viejo da MAL. Además, un chequeo rápido nuevo sobre `HEAD` (`results/rapido_cierre/`):
4 CSV iguales, y en cada log solo cambia la "Tasa:" de la generación 5. Lo que pide ventana (06,
16, 17 y 18) se verificó en vivo en la sesión 3, con Fer. El código no cambió desde entonces: el
último archivo de código se tocó a las 19:42, `ventana_despues/` es de las 19:45 a las 19:49, y el
árbol está limpio contra `HEAD`. Los IDs `LIMPIEZA-NN` son los del QA manual del spec.

| ID | Criterio | Resultado | Evidencia / Gap |
|----|----------|-----------|-----------------|
| LIMPIEZA-QA-01 | Línea base desde el commit anterior al primer cambio, con su control | ✅ | Hash `1ad83b9` en la bitácora, y es el padre del primer commit del spec (`076ffa3`). Comparador: los 10 CSV y los 10 logs de `results/linea_base_limpieza/` son iguales a los de `experimento_20261114-160055/` (LIMPIEZA-01) |
| LIMPIEZA-QA-02 | Chequeo completo del bloque A | ✅ | `results/experimento_20261114-171106/`: 6 CSV y 6 logs iguales (LIMPIEZA-02) |
| LIMPIEZA-QA-03 | Chequeo completo del bloque B | ✅ | `results/experimento_20261114-191956/`: 6 CSV y 6 logs iguales (LIMPIEZA-03) |
| LIMPIEZA-QA-04 | Chequeo completo del bloque C | ✅ | `results/experimento_20261114-194553/`: 6 CSV iguales; en cada log, 2 líneas distintas, las "Tasa:" de las generaciones 5 y 10, cada una igual a `vivos` / 60 (LIMPIEZA-04) |
| LIMPIEZA-QA-05 | Chequeo de cierre, 5 × 20 | ✅ | `results/experimento_20261114-195055/`: 10 CSV iguales; `resumen.md` igual desde la línea 4; en cada log, 5 líneas: las 4 "Tasa:" (`vivos` / 60) y la del tiempo (suma de `ticks` / 3.600; 7,3 minutos en la semilla 1) (LIMPIEZA-05) |
| LIMPIEZA-QA-06 | Con ventana, `--generaciones 2 --semilla 1` | ✅ | `results/ventana_despues/`: CSV igual a las 2 primeras generaciones; el log solo difiere en las 3 líneas del modo con ventana (LIMPIEZA-06) |
| LIMPIEZA-QA-07 | `requirements.txt` e instalación limpia | ✅ | Solo `pygame`, `numpy`, `scikit-learn` y `pytest`, con `>=`; ningún import de terceros fuera de esos cuatro. La instalación limpia es de la sesión 1 (bitácora): `pytest` verde y chequeo rápido idéntico. `requirements.txt` no cambió desde entonces (LIMPIEZA-07) |
| LIMPIEZA-QA-08 | `.pyc` | ✅ | `git ls-files "*.pyc"` vacío; `.gitignore:6-7`. Después del chequeo rápido nuevo, `git status` limpio (LIMPIEZA-08) |
| LIMPIEZA-QA-09 | Código muerto | ✅ | No existen `src/agents/brain/`, `src/analytics/metrics.py`, `save_data` ni `print_cluster_report`; `grep -rn 'safe"' src` vacío (LIMPIEZA-09) |
| LIMPIEZA-QA-10 | Pylint | ✅ | El comando de Implementación da 0 hallazgos (antes 53) (LIMPIEZA-10) |
| LIMPIEZA-QA-11 | `genetic_algorithm.py` | ✅ | `random.randint(50, 900)` 3 veces (`:44`, `:111`, `:239`); un solo bucle de 100, en `_posicion_libre` (`:108-115`); respaldos: `(100, 100)` en `:149` y `:200`, la grilla en `:156`. Comparado camino por camino contra `1ad83b9` (élites, hijos, población al azar, inmigrantes): mismos sorteos, mismos argumentos, mismo orden (LIMPIEZA-11) |
| LIMPIEZA-QA-12 | Estructura de `main.py` | ✅ | `_reposicionar_agentes` (`main.py:125`) y `_ticks_de_generacion` (`:251`), una vez cada una. En `_simular`, el paso del agente (`:546-566`) y el fin de generación en orden (`:603-652`). Sin clases nuevas. `mostrar_pantalla_final` en `src/ui/pantalla_final.py:22`; `dibujar_mundo` (`src/ui/renderer.py:284`) la usan `main.py:672` y `pantalla_final.py:34` (LIMPIEZA-12) |
| LIMPIEZA-QA-13 | DIAG-27 | ✅ | `main.py:145` sortea la `y` con `world.screen_height`. El control con zoom no dio distinto porque ese sorteo no corre en las semillas de la verificación: vale la lectura, como dice el spec, y la sesión 2 ejercitó la rama aparte (bitácora) (LIMPIEZA-13) |
| LIMPIEZA-QA-14 | DIAG-14 | ✅ | `learning_monitor.py:47` guarda `total_agents` y `:172` divide por él. `tests/test_reportes.py:35-43` (60 y 45 vivos), que falló con el código de antes (sesión 3: 120.0% y 90.0%). Las "Tasa:" del cierre valen `vivos` / 60 (LIMPIEZA-14) |
| LIMPIEZA-QA-15 | DIAG-15 | ✅ | `minutos_simulados` (`pantalla_final.py:17-19`), con división real; `main.py:571` y `:610` suman los ticks, también los de la generación parcial del cofre; la consola y el cuadro usan la misma función. `test_humo.py:104-108`; antes decía 0.0 (LIMPIEZA-15) |
| LIMPIEZA-QA-16 | DIAG-16 | ✅ | `textos_del_cuadro` (`pantalla_final.py:94-201`) no dibuja; `test_reportes.py:67-79`, con cofre y sin cofre. Con ventana y sin cofre, mirado por Fer y en capturas en la sesión 3 (LIMPIEZA-16) |
| LIMPIEZA-QA-17 | DIAG-17 | ✅ | En vivo, sesión 3: 56 s de CPU en 10 s antes, 0,19 s después. Todo se calcula y se dibuja una vez antes del loop (`pantalla_final.py:30-45`); el loop solo atiende eventos, hace `flip` y espera con `clock.tick(30)` (`:50-57`) (LIMPIEZA-17) |
| LIMPIEZA-QA-18 | Pantalla final, a ojo | ✅ | En vivo, sesión 3: las capturas de los cuadros 1 y 30 son idénticas (quieta), el fondo es el último cuadro, y ESC (Fer) y ENTER (inyectada) la cierran. Sin `particle_system.update()` (`pantalla_final.py:34-38`); `K_ESCAPE` y `K_RETURN` en `:54` (LIMPIEZA-18) |
| LIMPIEZA-QA-19 | `python -m pytest -q` | ✅ | 17 passed en 20,4 s (LIMPIEZA-19) |
| LIMPIEZA-QA-20 | Lo que salió del spec por la decisión 8 | ✅ | Las tres entradas de la bitácora dicen que no salió nada (LIMPIEZA-20) |
| LIMPIEZA-QA-21 | Docs | ✅ | README: dependencias (`:47-50`), estructura sin `brain/` ni `metrics.py`, con `pantalla_final.py` (`:87`). `CLAUDE.md` § Stack, § Estructura (la pantalla final en `src/ui/`, `:70`) y § Variables de entorno. DIAG-14 a DIAG-21, DIAG-23, DIAG-26 y DIAG-27 ✅ en este archivo (LIMPIEZA-21) |
| LIMPIEZA-QA-22 | § "Qué NO es": no cambia la simulación, `experimento.py`, las columnas del CSV ni la lógica de "¿APRENDIERON?" | ✅ | `git diff 1ad83b9 HEAD -- src/agents src/world`: solo `brain/`, la rama `"safe"`, imports sin usar y `.pyc`. `experimento.py` sin diff; `COLUMNAS_CSV` igual. "¿APRENDIERON?": mismas ramas y umbrales (`pantalla_final.py:132-155` contra `1ad83b9:main.py:1307-1334`) |

**Observaciones de los checkers que no cambian el veredicto:**
- El checker de docs dio dos PARCIAL por criterios que se le escribieron más estrictos que el DoD:
  `pantalla_final.py` literal en `CLAUDE.md` § Estructura (el DoD pide la sección al día, y la línea
  de `src/ui/` nombra los módulos por lo que hacen), y una lista de lo permitido en `src/agents` sin
  los `.pyc` que saca la decisión 24.
- `find_safe_position` (`main.py:38`) sortea la `y` con el 800 literal: es el alto del mundo, no el
  de la ventana, y el spec la deja como está. `fix_agent_positions` corre dos veces, también a
  propósito (§ "Qué NO es").
- Con ventana, la consola no imprime el resumen final (igual que antes): el tiempo simulado se ve
  solo en el cuadro, calculado con la misma función.
- Fuera de alcance, al ítem 3 del BACKLOG (decisión 15): `src/ui/popup.py:93` conserva un
  `.get('total_agents', 50)` cuyo 50 nunca se usa (la clave siempre llega), y el README lista
  `logs/` y `checkpoints/` (`README.md:92-93` y `:493-497`), que no existen.
