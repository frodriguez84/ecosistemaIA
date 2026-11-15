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
| DIAG-28 | **La conducción escrita a mano es más que la de DIAG-01.** En el 2% de los ticks, `decide()` sortea de nuevo el rumbo del agente, sea cual sea su fitness (un rumbo al azar cada ~50 ticks); el temporizador de exploración lo gira cada 100 ticks a casi todos (DIAG-13); en `act()`, un reflejo anula los giros cuando el agente giró mucho en los últimos 20 movimientos, y se suma ruido al girar. Es probable que la red maneje poco el rumbo: cuadra con que lo que más cambia con la evolución sea la distancia (×4,3). Encontrado el 2026-11-14 al escribir el spec *Aprendizaje*. | `advanced_agent.py:324-329`, `:307-316`, `:363-383`, `:392` | Aprendizaje |

> ✅ DIAG-06 (2026-11-14, spec *Medir*): `--semilla S` siembra `random` y `numpy` al arrancar, y
> las partículas del dibujo usan su propio generador. La misma semilla da el mismo CSV byte a
> byte, con ventana o sin ella (MEDIR-04 a MEDIR-07). Sin `--semilla` se sortea una, se imprime y
> queda en el CSV.
>
> ✅ DIAG-07 (2026-11-14, spec *Medir*): `main.py` acepta `--sin-ventana`, `--generaciones N`,
> `--semilla S`, `--sin-evolucion` y `--csv RUTA`, que pisan los valores de `config.py` (MEDIR-01
> a MEDIR-03).
>
> ✅ DIAG-05 (2026-11-14, spec *Aprendizaje*, bloque A): el consumo (`AGENT_ENERGY_CONSUMPTION`,
> 0,10 por tick) y lo que suma comer (`AGENT_ENERGY_GAIN_FOOD`, 8) se leen de `config.py`; la energía
> alcanza para 1.000 ticks sin comer. En el [experimento del bloque A](#experimento-modos-a), desde
> la generación 5 quedan vivos entre 0 y 16 de 60 al final de cada generación.
> `tests/test_reglas.py` lo prueba con otros valores, y fallaba con el código de antes.
>
> ✅ DIAG-02, DIAG-03 y DIAG-04 (2026-11-15, spec *Aprendizaje*, bloque B). `tests/test_puzzle.py`
> los prueba, y sus 12 tests fallaron con el código de antes:
> - DIAG-02: la red tiene 11 sensores. El 8 es la etapa del puzzle del propio agente (0 a 5); el 9 y
>   el 11 son la brújula, dirección y distancia a su próximo paso (la llave roja, la puerta de madera,
>   la llave dorada, la puerta de hierro o el cofre), calculadas como las de la comida. El hacha y los
>   árboles no tienen brújula.
> - DIAG-03: golpear es la quinta salida, y cuesta `HIT_ENERGY_COST` (0,05) por tick, golpee algo o
>   no. Las puertas, el cofre, los árboles y las casitas piden golpear; las llaves y el hacha siguen
>   por contacto.
> - DIAG-04: cada agente tiene su etapa y su hacha, y arranca en la etapa 0 y sin hacha. La puerta es
>   pared para cada uno hasta que él la abre, y la recompensa es del que dio el paso. En cada
>   generación se cierran puertas y cofre, y la llave roja y el hacha se sortean en un lugar nuevo.
>
> ✅ DIAG-01 y DIAG-28 (2026-11-15, spec *Aprendizaje*, bloque C). La conducción escrita a mano queda
> como es, pero solo en el modo guiado (`MODO = "guiado"`, el de por defecto), y el README la describe
> como guía, no como aprendizaje. En el modo autónomo (`--modo autonomo`), `decide()` es la salida de
> la red recortada a [0, 1], y `decide()` + `act()` no consumen azar: no corren las ramas de comida y
> árboles, el temporizador de exploración, las dos ramas del puzzle, el ruido de las salidas, el rumbo
> al azar del 2%, el reflejo que recorta los giros ni el ruido al girar. `tests/test_modos.py` lo
> prueba, y sus 4 tests fallaron con el código de antes. Cuánto pone la guía lo mide el
> [experimento de cierre](#experimento-modos-cierre).

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
| DIAG-29 | Al final de cada generación, los agentes se ubican contra el mapa viejo: `evolve` (con `_posicion_libre`), `fix_agent_positions` y `_reposicionar_agentes` corren antes de que `reset_food()` regenere obstáculos y estanque. El único chequeo que sirve es el segundo `fix_agent_positions`, contra el mapa nuevo. Explica por qué el reposicionamiento casi nunca mueve a nadie (DIAG-27). Encontrado el 2026-11-14 al escribir el spec *Aprendizaje*. | `main.py:641-668` | Aprendizaje |
| DIAG-30 | La colisión con el estanque y con el perímetro mira una caja que arranca en la posición del agente y va hacia abajo y a la derecha (`collides_with(x, y, radio, radio)`), no una centrada en él: un agente que entra por la derecha o por abajo se mete en el estanque hasta la mitad del cuerpo. La ubicación de agentes del algoritmo genético usaba la misma caja; con ella, la ubicación nueva del bloque A del spec *Aprendizaje* dejaba 10 de 1.260 agentes arrancando con medio cuerpo en el agua (3 semillas × 7 generaciones). El bloque A la centró en la ubicación (0 de 1.260), pero el movimiento sigue igual. Encontrado el 2026-11-14 al verificar MODOS-08. | `advanced_agent.py:420` y `:435`; `obstacles.py:396` y `:428` | Mejoras futuras |
| DIAG-32 | El popup de cada generación muestra dos datos que siempre valen 0: "Exploración: 0 m" lee la clave `avg_distance`, que `_datos_del_popup` no manda (manda `avg_exploration`), y "Tiempo gen: 0.0s" lee `generation_time`, fijo en 0. Además, queda abierto hasta hacer clic en "Cerrar", tapa casi todo el mundo mientras la generación siguiente ya corre (su título dice "Generación 2 completada" con el panel en la 3), y su gráfico tiene la escala fija de 0 a 100. Encontrado el 2026-11-15, en una captura. | `src/ui/popup.py:114` y `:180`; `main.py:247` y `:258` | Pantallas, bloque B |

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
>
> ✅ DIAG-08, DIAG-09, DIAG-10, DIAG-12, DIAG-13 y DIAG-29 (2026-11-14, spec *Aprendizaje*,
> bloque A). Cada uno tiene su test en `tests/test_reglas.py`, y los 11 tests fallaron con el código
> de antes:
> - DIAG-08: las recompensas por árbol y por casita van a `cut_rewards`, que `_calculate_fitness()`
>   suma, como `puzzle_rewards`. El árbol vale `TREE_CUT_REWARD` (15).
> - DIAG-09: salen los tres contadores, el término de fitness por obstáculos, `get_obstacle_skill`,
>   `avg_obstacle_skill` del popup y el comportamiento `obstacle_avoiders`. Valían siempre 0: sumar
>   un 0 entero al fitness no cambia el resultado.
> - DIAG-10: el sensor 7 es `(ángulo mod 2π) / 2π`, en [0, 1).
> - DIAG-12: `VISION_RANGE`, `AGENT_RADIUS`, `AGENT_ENERGY` (energía inicial y máxima, también para
>   la poción) y `WATER_ENERGY_LOSS` se leen de `config.py`.
> - DIAG-13: la exploración extra cuelga del `if fitness > 30`: corre solo con fitness ≤ 30.
> - DIAG-29: una sola función, `_ubicar_agentes` (`main.py`), ubica a todos después de
>   `reset_food()`, con todos los criterios juntos; el algoritmo genético ya no ubica. En 3 semillas
>   × 7 generaciones (1.260 ubicaciones), ningún agente arrancó en una fortaleza, sobre un obstáculo
>   o en el estanque del mapa de su generación. Al verificarlo apareció DIAG-30.
>
> ✅ DIAG-11 (bloque A el código, 2026-11-14; bloque C el README, 2026-11-15): el tope de la
> penalización por agua es `WATER_PENALTY_MAX` (10), con su test, y el README dice que tiene tope.
>
> ✅ DIAG-32 (2026-11-15, spec *Pantallas para ver aprender*, bloque B): sale el popup entero
> (`src/ui/popup.py`, `SummaryPopup`, `_datos_del_popup`, el clic y los `get_*_skill` que solo
> usaba él), y con él los dos ceros. El fin de cada generación es un aviso arriba del mundo que
> dura 2,5 s, no toma clics ni frena nada y no aparece después de la última; el gráfico pasó al
> panel, con la escala automática. `tests/test_pantallas.py` lo prueba, con su control, y la
> corrida con ventana llega a la pantalla final sin ningún clic (PANTALLAS-11, PANTALLAS-13 y
> PANTALLAS-16).

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
| DIAG-31 | La extensión Pylint marcaba 4 errores `E0402: Attempted relative import beyond top-level package`, en `pantalla_final.py` (2), `popup.py` y `stats.py`: las importaciones `from ..agents…` y `from ..analytics…`. `src/` no tenía `__init__.py` (sus subcarpetas sí): al correr, Python lo toma como paquete implícito y la importación anda, pero Pylint toma como raíz la última carpeta con `__init__.py` (`ui`). No era un error del código. En el mismo archivo, un "fixme" falso: Pylint lee el "Todo se calcula…" de un comentario como `TODO` (como en DIAG-26). Encontrado el 2026-11-15. | `src/ui/pantalla_final.py:9-10`, `popup.py:7`, `stats.py:8` | Resuelto |

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
> ✅ DIAG-31 (2026-11-15): `src/__init__.py`, con solo un docstring, y el comentario de
> `pantalla_final.py:38` pasa a decir "Se calcula…". Con el Pylint de la extensión corrido desde la
> terminal, 0 E0402 y 0 fixme en `src/`; los 53 tests, verdes, y la misma semilla da el mismo CSV.
> Lo que sigue en `pantalla_final.py` es de diseño (`_calculate_fitness` llamado desde afuera, dos
> `except Exception`) y de estilo (líneas de más de 100), y queda como está.
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

---

<a id="experimento-modos-a"></a>
## Modo guiado y modo autónomo — experimento del bloque A (2026-11-14, MODOS-10)

**Qué cambió** (bloque A del [spec](../specs/active/MODO_GUIADO_Y_AUTONOMO.md)): `config.py` manda
con sus números: el consumo es 0,10 por tick (corría 0,05), comer suma 8 (sumaba 30), el radio es 6
(era 8), el árbol suma 15 (sumaba 10 y no contaba, DIAG-08) y el agua resta `WATER_ENERGY_LOSS`. Los
pesos del fitness pasan a `config.py` con los mismos valores. DIAG-08 a DIAG-11 y DIAG-13 quedan
arreglados; los agentes se ubican una vez por generación, con el mapa nuevo (DIAG-29), y el id es un
contador. El modo es el de siempre, con la guía (el switch es del bloque C). La simulación cambia a
propósito: no se compara byte a byte contra la de antes (decisión 27).

**Cómo se corrió:** las 10 corridas a la vez, en 12 núcleos: 370 s. Carpeta
`results/experimento_20261114-224205`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 20`

**Por modo** (promedio ± desvío muestral entre semillas):

| Modo | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Etapa del puzzle (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Con evolución | 5 | 23.61 ± 0.71 | 39.99 ± 3.23 | 16.39 ± 3.86 | 0.61 ± 0.07 | 2.50 ± 0.66 | 1.88 ± 0.71 | 1169 ± 43 | 2.2 ± 0.8 | 0 de 5 |
| Sin evolución | 5 | 21.18 ± 0.44 | 21.80 ± 0.72 | 0.62 ± 0.97 | 0.55 ± 0.10 | 0.66 ± 0.08 | 0.11 ± 0.11 | 1052 ± 5 | 2.6 ± 1.5 | 1 de 5 (gen. 6.0) |

**Comparación pareada por semilla:** la evolución subió más que la línea base en 4 de 4 semillas en fitness, y en 4 de 4 en manzanas por agente.

**Por corrida:**

| Semilla | Modo | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Etapa del puzzle | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Con evolución | 20 | 22.43 | 45.30 | 22.87 | 0.51 | 3.55 | 3.05 | 1238 | 1 | — |
| 1 | Sin evolución | 6 | — | — | — | — | — | — | — | 5 | 6 |
| 2 | Con evolución | 20 | 24.35 | 38.43 | 14.08 | 0.69 | 2.24 | 1.54 | 1151 | 2 | — |
| 2 | Sin evolución | 20 | 21.05 | 20.89 | -0.16 | 0.44 | 0.56 | 0.12 | 1045 | 2 | — |
| 3 | Con evolución | 20 | 23.92 | 39.35 | 15.43 | 0.64 | 2.20 | 1.55 | 1158 | 3 | — |
| 3 | Sin evolución | 20 | 21.66 | 21.63 | -0.02 | 0.69 | 0.65 | -0.04 | 1052 | 3 | — |
| 4 | Con evolución | 20 | 23.69 | 36.73 | 13.04 | 0.62 | 1.85 | 1.22 | 1121 | 2 | — |
| 4 | Sin evolución | 20 | 20.64 | 22.60 | 1.96 | 0.53 | 0.69 | 0.16 | 1057 | 2 | — |
| 5 | Con evolución | 20 | 23.64 | 40.17 | 16.53 | 0.61 | 2.65 | 2.04 | 1177 | 3 | — |
| 5 | Sin evolución | 20 | 21.36 | 22.09 | 0.72 | 0.53 | 0.75 | 0.21 | 1055 | 1 | — |

Las corridas de menos de 10 generaciones (abrieron el cofre antes) quedan fuera de los promedios de fitness y manzanas: semilla 1 sin evolución.

**Lectura, contra el [experimento de cinco semillas](#experimento-cinco-semillas):**
- **Ahora hay presión de supervivencia, como preveía la decisión 15.** En las generaciones 1 a 4
  (960 ticks) mueren a lo sumo dos agentes, por la energía extra que resta el agua. Desde la 5
  (1.140 ticks) la energía no alcanza sin comer: al final de cada generación quedan vivos entre 0 y
  16 de 60. En las últimas 5 quedan 4,1 vivos en promedio con evolución y 1,4 sin ella.
- **Con evolución viven más, y lo aprenden:** la edad promedio de las últimas 5 es 1.169 ± 43 ticks
  con evolución y 1.052 ± 5 sin ella. Sin evolución apenas pasa los 1.000 ticks que da la energía
  inicial (cada manzana suma ~80). Con evolución sube de ~1.035 en las generaciones 5 a 8 a entre
  1.121 y 1.238 en las últimas 5.
- **Sigue aprendiendo algo, en todas las semillas comparables:** subió más que la línea base en 4 de
  4, en fitness y en manzanas. La peor semilla con evolución (+13,0 de fitness) sube más que la mejor
  sin evolución (+2,0).
- **Los números absolutos bajan, y era esperable:** con evolución, el fitness de las últimas 5 pasa
  de 42,6 a 40,0 y las manzanas por agente de 3,60 a 2,50. Comer suma 8 de energía en lugar de 30 y
  el que no come muere: vive menos ticks para comer, explorar y sumar supervivencia. El fitness
  máximo, en cambio, sube más que antes: de ~58 a ~75 con evolución (antes, a ~67) y a ~64 sin ella.
- **La distancia sube menos que antes:** de ~470 a ~1.280 con evolución (×2,7; antes ×4,3) y de ~360
  a ~440 sin ella (×1,2).
- **Todavía no separa aprendizaje de guía.** El fitness promedio con evolución termina en 40,0, por
  encima del umbral de 30 desde el que la guía lleva a la comida (DIAG-01). Lo mide el bloque C.
- **El puzzle sigue sin mostrar aprendizaje, y una línea base lo resolvió:** la semilla 1 sin
  evolución abrió el cofre en la generación 6 y la corrida terminó ahí; por eso la comparación
  pareada es sobre 4 semillas. El puzzle todavía es colectivo y persistente (DIAG-03, DIAG-04): con
  cerebros al azar y el mapa de esa semilla, alcanzó. Etapa 2,2 ± 0,8 con evolución contra
  2,6 ± 1,5 sin ella. Lo cambia el bloque B.
- **La población converge igual que antes:** diversidad en la generación 20 entre 0,097 y 0,117 con
  evolución (antes, 0,087 a 0,111); la línea base se queda en 0,23.

**Parada de la decisión 22: no se dispara.** Con evolución, ninguna semilla corrió sin muertes: hay
muertes en 17 o 18 de las 20 generaciones de cada una. Las generaciones cortadas porque murieron
todos antes del final son 4 de 80 desde la generación 5 (semilla 2: la 18; semilla 3: la 17;
semilla 4: la 17 y la 19), y ninguna semilla tiene la mayoría cortada. Los valores de energía quedan
como están. Para tener en cuenta: la presión es fuerte, y las generaciones cortadas aparecen desde
la 17, cuando duran 1.680 ticks.

---

<a id="experimento-modos-b"></a>
## Modo guiado y modo autónomo — experimento del bloque B (2026-11-15, MODOS-19)

**Qué cambió** (bloque B del [spec](../specs/active/MODO_GUIADO_Y_AUTONOMO.md)): el puzzle es de
cada agente y se reinicia en cada generación (DIAG-04); la red tiene 11 sensores, con la etapa propia
y una brújula a su próximo paso (DIAG-02), y 5 salidas: golpear, que cuesta 0,05 de energía por tick
(DIAG-03). Las puertas, el cofre, los árboles y las casitas piden golpear; las llaves y el hacha
siguen por contacto y quedan en el mapa. La guía apunta al próximo paso del agente y golpea al
alinearse. Abrir el cofre ya no termina la corrida. El modo sigue siendo el guiado (el switch es del
bloque C). La ubicación evita la llave roja y el hacha a 35 px, como las manzanas (decidido con Fer
en la sesión: ver la nota del final).

**Cómo se corrió:** las 10 corridas a la vez, en 12 núcleos: 327 s. Carpeta
`results/experimento_20261115-102446`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 20`

**Por modo** (promedio ± desvío muestral entre semillas):

| Modo | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Con evolución | 5 | 23.87 ± 0.80 | 34.81 ± 0.60 | 10.94 ± 0.92 | 0.67 ± 0.05 | 1.11 ± 0.04 | 0.44 ± 0.06 | 992 ± 23 | 4.24 ± 1.38 | 1.0 ± 0.0 | 0 de 5 |
| Sin evolución | 5 | 20.81 ± 1.02 | 21.39 ± 0.65 | 0.58 ± 1.41 | 0.54 ± 0.06 | 0.59 ± 0.05 | 0.05 ± 0.11 | 914 ± 8 | 1.44 ± 0.65 | 1.4 ± 0.5 | 0 de 5 |

**Comparación pareada por semilla:** la evolución subió más que la línea base en 5 de 5 semillas en fitness, y en 5 de 5 en manzanas por agente.

**Por corrida:**

| Semilla | Modo | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Con evolución | 20 | 24.71 | 35.11 | 10.40 | 0.73 | 1.15 | 0.42 | 1017 | 4.40 | 1 | — |
| 1 | Sin evolución | 20 | 21.57 | 21.12 | -0.45 | 0.58 | 0.59 | 0.01 | 925 | 2.40 | 1 | — |
| 2 | Con evolución | 20 | 23.34 | 34.13 | 10.79 | 0.65 | 1.06 | 0.41 | 979 | 4.00 | 1 | — |
| 2 | Sin evolución | 20 | 20.07 | 22.04 | 1.97 | 0.51 | 0.62 | 0.11 | 914 | 1.60 | 2 | — |
| 3 | Con evolución | 20 | 24.01 | 35.59 | 11.58 | 0.64 | 1.11 | 0.47 | 1016 | 6.40 | 1 | — |
| 3 | Sin evolución | 20 | 22.15 | 21.35 | -0.81 | 0.62 | 0.52 | -0.10 | 905 | 0.60 | 1 | — |
| 4 | Con evolución | 20 | 24.49 | 34.30 | 9.81 | 0.73 | 1.08 | 0.36 | 975 | 2.60 | 1 | — |
| 4 | Sin evolución | 20 | 20.49 | 20.47 | -0.01 | 0.52 | 0.55 | 0.03 | 919 | 1.20 | 1 | — |
| 5 | Con evolución | 20 | 22.78 | 34.91 | 12.13 | 0.62 | 1.13 | 0.51 | 971 | 3.80 | 1 | — |
| 5 | Sin evolución | 20 | 19.75 | 21.98 | 2.23 | 0.46 | 0.65 | 0.19 | 909 | 1.40 | 2 | — |

**Lectura, contra el [experimento del bloque A](#experimento-modos-a):**
- **Primera señal en el puzzle: con evolución, más agentes llegan a la llave roja.** Con evolución
  pasan de 1,9 agentes por generación en las generaciones 1 a 5 a 4,2 en las últimas 5; sin
  evolución se quedan igual (1,6 y 1,4). En las últimas 5, la evolución tiene más agentes con llave
  roja que la línea base en las 5 semillas (de 2,6 contra 1,2 a 6,4 contra 0,6). Todavía no se sabe
  cuánto es de la red y cuánto de la guía: la rama de llaves pide fitness > 65 y el fitness máximo de
  las últimas 5 está en ~62, así que la guía del puzzle corre poco, pero la de la comida puede pasar
  cerca de la llave. Lo separa el bloque C.
- **Nadie de la evolución pasa la puerta de madera; la línea base, tres veces.** Con evolución la
  etapa máxima es 1 en las 5 semillas. Sin evolución, un agente abrió la puerta de madera en la
  semilla 2 (generaciones 9 y 11) y en la 5 (generación 18): un cerebro al azar que golpea seguido y
  pasa por la puerta con la llave. Ninguno siguió a la llave dorada. El cofre no se abrió.
- **Sigue aprendiendo a comer más que la línea base, en todas las semillas:** subió más en 5 de 5,
  en fitness y en manzanas. La peor semilla con evolución (+9,8 de fitness) sube más que la mejor sin
  ella (+2,2).
- **Golpear rompe la premisa de la decisión 15.** La decisión 15 calculaba que nadie muere en las
  generaciones 1 a 4 (la energía alcanza para 1.000 ticks). Con el costo de golpear no es así: entre
  60 cerebros al azar, la mitad casi no golpea, pero 19 golpean en más de la mitad de los ticks
  (medido en 300 ticks, semilla 3), y golpeando siempre se gastan 0,15 por tick, que alcanzan para
  667. En las generaciones 1 a 4 quedan vivos entre 21 y 37 de 60 (en el A, 58 o más). Desde la 5 quedan entre 0 y 11, y en las
  últimas 5, 0,6 en promedio en los dos modos. La edad de las últimas 5 baja de 1.169 a 992 con
  evolución y de 1.052 a 914 sin ella.
- **Los números absolutos bajan otra vez:** con evolución, el fitness de las últimas 5 pasa de 40,0 a
  34,8 y las manzanas por agente de 2,50 a 1,11. Viven menos ticks, y la red ahora tiene que manejar
  una quinta salida que cuesta.
- **La distancia sube como en el A:** de ~465 a ~1.110 con evolución (×2,4; en el A, ×2,7) y de ~360 a
  ~400 sin ella. Se cortaron 1,2 árboles por corrida con evolución y ninguno sin ella.
- **La población converge igual:** diversidad en la generación 20 entre 0,083 y 0,133 con evolución;
  la línea base, en 0,23.

**La parada de la decisión 22 no se dispara,** aunque era para el bloque A: ninguna semilla corrió sin
muertes, y las generaciones cortadas desde la 5 son entre 2 y 7 de 16 por corrida (la que más, la
semilla 4 con evolución), ninguna con la mayoría. Sobre la premisa rota de la decisión 15, Fer
decidió el 2026-11-15 dejar `HIT_ENERGY_COST` en 0,05: es lo que pide la decisión 14 ("golpear
siempre acorta la vida"), y el bloque C compara los dos modos con los mismos valores.

**Primera corrida, antes de corregir la ubicación** (`results/experimento_20261115-101003`): con los
agentes arrancando a veces sobre la llave roja o el hacha (LEC-008). Mismas conclusiones: 5 de 5 en
fitness y en manzanas, etapa máxima 1 en todas. Los agentes con llave roja de las generaciones 1 a 5
eran 2,8 con evolución y 2,0 sin ella: la suerte de arrancar encima ponía entre medio agente y uno
por generación.

<a id="experimento-modos-cierre"></a>

## Modo guiado y modo autónomo — experimento de cierre (2026-11-15, MODOS-27)

**Qué cambió** (bloque C del [spec](../specs/active/MODO_GUIADO_Y_AUTONOMO.md)): el switch. Con
`--modo autonomo`, `decide()` es solo la salida de la red y no corre nada de la guía (DIAG-01,
DIAG-28); con `--modo guiado` (el de por defecto) todo sigue como en el bloque B. **El guiado no
cambió:** sus 20 primeras generaciones son, byte a byte, las del [experimento del bloque
B](#experimento-modos-b) en las 10 corridas (sin la columna `modo`).

**Cómo se corrió:** 20 corridas, 11 a la vez, en 12 núcleos: 16,5 min (a ratos con corridas de
verificación en paralelo). Carpeta `results/experimento_20261115-112804`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos guiado autonomo`

**Por grupo** (promedio ± desvío muestral entre semillas):

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| guiado | Con evolución | 5 | 23.87 ± 0.80 | 36.74 ± 0.89 | 12.87 ± 0.44 | 0.67 ± 0.05 | 1.19 ± 0.04 | 0.52 ± 0.04 | 998 ± 34 | 5.20 ± 1.21 | 1.2 ± 0.4 | 0 de 5 |
| guiado | Sin evolución | 5 | 20.81 ± 1.02 | 21.28 ± 0.97 | 0.48 ± 1.10 | 0.54 ± 0.06 | 0.60 ± 0.02 | 0.06 ± 0.05 | 906 ± 11 | 1.68 ± 0.66 | 1.4 ± 0.5 | 0 de 5 |
| autonomo | Con evolución | 5 | 17.49 ± 0.27 | 31.39 ± 2.32 | 13.90 ± 2.38 | 0.24 ± 0.03 | 0.83 ± 0.14 | 0.58 ± 0.12 | 990 ± 36 | 3.16 ± 1.37 | 1.2 ± 0.4 | 0 de 5 |
| autonomo | Sin evolución | 5 | 16.37 ± 0.36 | 16.58 ± 0.87 | 0.21 ± 0.73 | 0.21 ± 0.05 | 0.20 ± 0.07 | -0.00 ± 0.04 | 884 ± 9 | 0.72 ± 0.36 | 1.2 ± 0.4 | 0 de 5 |

**Comparaciones pareadas por semilla** (un empate no cuenta como más):

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5.
- **Guiado, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5.
- **Guiado contra autónomo, en las últimas 5:** con evolución, el guiado tuvo más manzanas por agente en 5 de 5 semillas y más agentes con llave roja en 4 de 5; sin evolución, más manzanas en 5 de 5 y más agentes con llave roja en 5 de 5.

**Por corrida:**

| Semilla | Modo | Evolución | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | guiado | Con evolución | 30 | 24.71 | 37.84 | 13.13 | 0.73 | 1.23 | 0.50 | 1028 | 5.60 | 1 | — |
| 1 | guiado | Sin evolución | 30 | 21.57 | 22.59 | 1.02 | 0.58 | 0.61 | 0.03 | 918 | 1.20 | 1 | — |
| 1 | autonomo | Con evolución | 30 | 17.48 | 33.62 | 16.13 | 0.26 | 0.94 | 0.68 | 1045 | 3.00 | 1 | — |
| 1 | autonomo | Sin evolución | 30 | 16.55 | 17.15 | 0.59 | 0.22 | 0.26 | 0.04 | 883 | 0.60 | 1 | — |
| 2 | guiado | Con evolución | 30 | 23.34 | 36.61 | 13.27 | 0.65 | 1.20 | 0.56 | 984 | 6.00 | 2 | — |
| 2 | guiado | Sin evolución | 30 | 20.07 | 20.52 | 0.44 | 0.51 | 0.61 | 0.10 | 907 | 1.20 | 2 | — |
| 2 | autonomo | Con evolución | 30 | 17.45 | 28.73 | 11.28 | 0.24 | 0.77 | 0.53 | 949 | 1.00 | 1 | — |
| 2 | autonomo | Sin evolución | 30 | 16.00 | 15.03 | -0.97 | 0.16 | 0.10 | -0.06 | 886 | 0.40 | 1 | — |
| 3 | guiado | Con evolución | 30 | 24.01 | 37.13 | 13.12 | 0.64 | 1.12 | 0.49 | 1025 | 6.40 | 1 | — |
| 3 | guiado | Sin evolución | 30 | 22.15 | 21.37 | -0.79 | 0.62 | 0.61 | -0.01 | 909 | 1.60 | 1 | — |
| 3 | autonomo | Con evolución | 30 | 17.10 | 33.16 | 16.06 | 0.27 | 0.93 | 0.66 | 998 | 4.00 | 1 | — |
| 3 | autonomo | Sin evolución | 30 | 16.74 | 16.88 | 0.13 | 0.19 | 0.18 | -0.02 | 891 | 1.20 | 1 | — |
| 4 | guiado | Con evolución | 30 | 24.49 | 36.70 | 12.21 | 0.73 | 1.21 | 0.49 | 1007 | 4.60 | 1 | — |
| 4 | guiado | Sin evolución | 30 | 20.49 | 20.19 | -0.30 | 0.52 | 0.59 | 0.07 | 907 | 1.60 | 1 | — |
| 4 | autonomo | Con evolución | 30 | 17.85 | 32.37 | 14.51 | 0.25 | 0.90 | 0.66 | 989 | 3.20 | 1 | — |
| 4 | autonomo | Sin evolución | 30 | 16.58 | 16.92 | 0.34 | 0.29 | 0.27 | -0.02 | 890 | 0.40 | 1 | — |
| 5 | guiado | Con evolución | 30 | 22.78 | 35.40 | 12.62 | 0.62 | 1.18 | 0.56 | 945 | 3.40 | 1 | — |
| 5 | guiado | Sin evolución | 30 | 19.75 | 21.75 | 2.00 | 0.46 | 0.57 | 0.11 | 888 | 2.80 | 2 | — |
| 5 | autonomo | Con evolución | 30 | 17.57 | 29.06 | 11.49 | 0.20 | 0.60 | 0.40 | 968 | 4.60 | 2 | — |
| 5 | autonomo | Sin evolución | 30 | 15.95 | 16.91 | 0.96 | 0.17 | 0.21 | 0.04 | 868 | 1.00 | 2 | — |

**Lectura: las tres preguntas del Objetivo.**

1. **¿El modo autónomo aprende? Sí: a comer y a caminar.** Contra su línea base subió más en
   fitness y en manzanas por agente en 5 de 5 semillas. Las manzanas por agente pasan de 0,24 en las
   generaciones 1 a 5 a 0,83 en las últimas 5 (×3,4); sin evolución, de 0,21 a 0,20. La peor semilla
   con evolución (+11,3 de fitness) sube más que la mejor sin ella (+1,0). La distancia recorrida
   pasa de ~205 a ~1.090 px por agente (×5,3); sin evolución, ~190 las dos. Sin ninguna conducción
   escrita a mano, la red aprende a avanzar y a comer.
2. **¿La guía es la que hace comer? En parte: pone un piso, y la evolución suma encima lo mismo en
   los dos modos.** Sin evolución, la guía sola triplica lo que comen los cerebros al azar (0,60
   contra 0,20 manzanas por agente en las últimas 5; el guiado tiene más en 5 de 5). Con evolución,
   el guiado sigue comiendo más (1,19 contra 0,83, 5 de 5), pero lo que suma la evolución es
   parecido: +0,52 en el guiado y +0,58 en el autónomo. La diferencia entre los modos es de ~0,4
   manzanas por agente al principio (0,67 contra 0,24) y al final (1,19 contra 0,83): eso es lo que
   pone la guía; el resto es aprendizaje, en los dos. Es lo que el experimento de cinco semillas no
   podía separar (DIAG-01).
3. **¿Alguno aprende el puzzle? Solo el primer paso, y por caminar más.** Con evolución hay más
   agentes con llave roja en las últimas 5 que en la línea base en 5 de 5 semillas, en los dos modos
   (guiado 5,2 contra 1,7; autónomo 3,2 contra 0,7). Pero por distancia recorrida no la encuentran
   más: en las últimas 5, el autónomo con evolución tiene 2,9 agentes con llave roja por cada 1.000
   px de recorrido promedio, contra 3,8 de su línea base; el guiado, 4,0 contra 4,3. No hay señal de
   que usen la brújula. Más allá de la llave roja, casi nada: la puerta de madera se abrió en 6 de
   las 600 generaciones, siempre un agente solo (guiado con evolución, semilla 2, generación 29;
   guiado sin evolución, semilla 2, generaciones 9 y 11, y semilla 5, generación 18; autónomo,
   semilla 5, generación 1, que es la misma con evolución y sin ella). Nadie llegó a la llave
   dorada; el cofre no se abrió.

**Además:**
- **En las generaciones largas no sobrevive nadie.** En las últimas 5 (2.040 a 2.220 ticks) no queda
  ningún agente vivo al final, en ningún grupo; la edad promedio está entre 870 y 1.050 ticks. Desde
  la generación 5, las generaciones que terminan porque murieron todos son de 11 a 16 de 26 en el
  guiado con evolución y de 18 a 22 en el autónomo sin evolución (la mayoría). La parada de la
  decisión 22 era del bloque A; acá queda como dato para cuando se juegue con la energía.
- **Contra el B, el guiado sigue subiendo con más generaciones:** el fitness de las últimas 5 pasa de
  34,8 (generaciones 16 a 20) a 36,7 (26 a 30), y las manzanas por agente de 1,11 a 1,19.
- **La población converge igual en los dos modos:** diversidad en la generación 30 entre 0,057 y
  0,103 con evolución; la línea base, 0,23.
- **Árboles cortados:** 16 en el guiado con evolución (entre las 5 corridas), 1 en el autónomo con
  evolución, ninguno sin evolución.

**En corto:** sin guía, la evolución aprende a comer (5 de 5 semillas contra la línea base); la guía
suma ~0,4 manzanas por agente encima del aprendizaje, no lo reemplaza; el puzzle no se aprende más
allá de la llave roja, que sube porque caminan más.

---

<a id="qa-modo-guiado-y-autonomo"></a>
## QA /qa-spec — Modo guiado y modo autónomo (2026-11-15)
**Veredicto:** APROBADO (la primera pasada dio BLOQUEADO por MODOS-29; se arregló en la sesión y se
re-verificó)
**Verificación técnica:** sintaxis ✅ (`compileall` de `main.py`, `config.py`, `src`, `experimento.py`
y `tests`) · tests 53/53 en 22,8 s · build N/A (Python, sin build)
**Método:** cuatro checkers independientes (Explore/haiku, solo lectura) contra el DoD y el QA manual
de `docs/specs/active/MODO_GUIADO_Y_AUTONOMO.md`: bloque A (MODOS-01 a 09), bloque B (11 a 17),
bloque C (20, 21 y 23 a 26) y docs (06, 26 y 29). Los checkers no ejecutaban nada: lo que pide
corridas se volvió a correr en la sesión desde `05078e5`, con el árbol limpio, y los experimentos
registrados se leyeron de este archivo y de `results/`. Cada `archivo:línea` de la tabla se imprimió
antes de copiarlo (LEC-006). **Primera pasada: BLOQUEADO** por MODOS-29: el README decía que el
árbol pide 2 golpes, que es el `TREE_HITS_TO_CUT` de `config.py`; pero nadie lo lee y el código pide
3. Además, `CLAUDE.md:51` remitía a § Notas por los parámetros que se ignoran, y § Notas ya no los
nombraba. Se arregló en la sesión, en el README y en `CLAUDE.md`, sin tocar código. Dos checkers
nuevos re-verificaron MODOS-29: el primero encontró que la fortaleza chica del README era 4x5 (es
5x5) y que dos de los parámetros "que no se leen" se imprimen al arrancar; se corrigió, y el segundo
dio todo PASS. Los IDs `MODOS-NN` son los del QA manual del spec.

| ID | Criterio | Resultado | Evidencia / Gap |
|----|----------|-----------|-----------------|
| MODOS-QA-01 | Config manda | ✅ | `advanced_agent.py:46` (`AGENT_RADIUS`), `:50-51` (`AGENT_ENERGY`), `:66` (`VISION_RANGE`), `:408` (consumo), `:586` (ganancia, con tope en el máximo). `test_reglas.py:54`, `:62` y `:86` pisan los valores con otros distintos de los fijos de antes (0,37; 70 y 13; 11 y 222). Verde (MODOS-01) |
| MODOS-QA-02 | Números fijos | ✅ | `grep` en `src/` sin `self.energy -= 0.05`, `self.energy + 30`, `self.radius = 8`, `self.vision_range = 150`, `self.fitness += 10`, `penalty_max` ni `*_multiplier`; `obstacles.py:44` lee `WATER_ENERGY_LOSS`. Los `FITNESS_*` se leen en `advanced_agent.py:719-736` (MODOS-02) |
| MODOS-QA-03 | DIAG-08 | ✅ | Acumulador `cut_rewards` (`advanced_agent.py:98`): suma `TREE_CUT_REWARD` y `HUT_CUT_REWARD` (`:610`, `:618`), y `_calculate_fitness` lo suma (`:745`). `test_reglas.py:106`; falló contra el código de antes (bitácora, sesión 1) (MODOS-03) |
| MODOS-QA-04 | DIAG-09 | ✅ | No quedan `obstacles_avoided`, `obstacle_avoidance_count`, `total_obstacle_encounters`, `get_obstacle_skill` ni `obstacle_avoiders` en el código; `test_reglas.py:128-131` lo prueba. Valían 0: el fitness no cambió por sacarlos (bitácora, sesión 1) (MODOS-04) |
| MODOS-QA-05 | DIAG-10 | ✅ | `advanced_agent.py:160`: `(ángulo mod 2π) / 2π`; `test_reglas.py:134`, con muchas vueltas en los dos sentidos (MODOS-05) |
| MODOS-QA-06 | DIAG-11 | ✅ | `advanced_agent.py:748` topea en `WATER_PENALTY_MAX`; `test_reglas.py:145`. El README no dice "sin límite" y da el tope en `README.md:248` (MODOS-06) |
| MODOS-QA-07 | DIAG-13 | ✅ | La exploración extra está en el `else` del `if self.fitness > 30` (`advanced_agent.py:218`, `:300-310`), después del `return` del autónomo (`:212-214`). `test_reglas.py:155` (fitness 50 y 20) (MODOS-07) |
| MODOS-QA-08 | Ubicación (DIAG-29) | ✅ | `_ubicar_agentes` (`main.py:75`), con su criterio `_lugar_libre` (`:38`, que solo llama ella), después de crear el mundo (`:371`) y de `reset_food()` (`:548-549`); las funciones viejas no existen. En vivo, en esta sesión: un script envolvió `_ubicar_agentes` en una corrida de 5 generaciones (semilla 3), con 0 de 60 agentes en fortaleza, obstáculo, perímetro o estanque en las 5 ubicaciones, en el orden ubicar y después `reset_food` → ubicar. Su control: el centro de un obstáculo, del estanque y de cada fortaleza da adentro (MODOS-08) |
| MODOS-QA-09 | Id | ✅ | Contador de clase (`advanced_agent.py:29-39`), reiniciado al empezar `_simular` (`main.py:311`), sin azar; la pantalla final muestra `top_agent.id` (`pantalla_final.py:177`). `test_reglas.py:168`: dos corridas con la misma semilla dan ids 1 a 60 en la generación 1 (MODOS-09) |
| MODOS-QA-10 | Experimento A | ✅ | [Registrado](#experimento-modos-a), con su lectura contra el de cinco semillas; la parada de la decisión 22, evaluada en la bitácora (sesión 1: no se dispara) (MODOS-10) |
| MODOS-QA-11 | Puzzle por agente | ✅ | La puerta es pared según la etapa de cada agente (`advanced_agent.py:545`, `:549`); el golpe que la completa sube la etapa de quien golpea (`world.py:930-936`), con golpes y cooldown por agente (`obstacles.py:256-259`), y la recompensa va a su acumulador. `test_puzzle.py:68` (MODOS-11) |
| MODOS-QA-12 | Golpear | ✅ | Golpear (`hit` > 0,5) cuesta `HIT_ENERGY_COST` (`advanced_agent.py:412-414`); puerta, cofre y corte piden golpear (`:601-602`, `:638-639`, `:658-659`). `test_puzzle.py:90` y `:155` (MODOS-12) |
| MODOS-QA-13 | Reinicio por generación | ✅ | Agente nuevo en etapa 0 y sin hacha (`advanced_agent.py:75-76`), también las élites; `reset_food` cierra puertas y cofre y sortea hacha y llave roja después de regenerar el mapa (`world.py:430-443`). `test_puzzle.py:182` y `:219` (MODOS-13) |
| MODOS-QA-14 | Cofre | ✅ | Abrirlo se cuenta y la corrida sigue (`main.py:478-484`); el CSV se escribe solo al cerrar cada generación (`:511`). `test_puzzle.py:231` (MODOS-14) |
| MODOS-QA-15 | Brújula | ✅ | `_proximo_paso` por etapa (`advanced_agent.py:192-204`); con etapa 5, 0 y 1 (`:178-180`). `test_puzzle.py:165` (MODOS-15) |
| MODOS-QA-16 | Guía adaptada | ✅ | Umbrales 65 y probabilidad 0,4 (`advanced_agent.py:315-320`), apuntando a `_proximo_paso` (`:323`): puertas con etapa 1 o 3 (`:326-327`; al alinearse, 0,6 y golpear 0,9, `:338-340`), llaves y cofre con etapa 0, 2 o 4 (`:350-351`; 0,7 y golpear 0,9, `:362-364`). El checker comparó los valores contra `cc9126b`: iguales. `test_puzzle.py:263` (MODOS-16) |
| MODOS-QA-17 | Pantallas del puzzle | ✅ | Consola (`main.py:226-228`), popup (`popup.py:126-133`), panel (`stats.py:77-84`) y pantalla final (`pantalla_final.py:138-143`) cuentan agentes por paso (MODOS-17) |
| MODOS-QA-18 | Con ventana, bloque B | ✅ | Lo visual (puertas abiertas, llave y hacha en el mapa) se miró con ventana en la sesión 2; `renderer.py` y `world.py` no cambiaron desde `e8cb600`. Mismo CSV que sin ventana: vuelto a correr en esta sesión, en los dos modos (MODOS-QA-22) (MODOS-18) |
| MODOS-QA-19 | Experimento B | ✅ | [Registrado](#experimento-modos-b), con su lectura contra el A (MODOS-19) |
| MODOS-QA-20 | `--modo` | ✅ | `MODO = "guiado"` (`config.py:15`); `--modo` con la ayuda en español (`main.py:126-128`). `test_modos.py:106` (MODOS-20) |
| MODOS-QA-21 | Sin guía | ✅ | En autónomo, `decide()` devuelve la red recortada antes de toda la guía (`advanced_agent.py:212-214`); en `act()`, el reflejo y el ruido corren solo en el guiado (`:428-429`). `test_modos.py:66`, `:78` (el estado de `random` y de `np.random`, igual después de 50 ticks) y `:90` (MODOS-21) |
| MODOS-QA-22 | Reproducible por modo | ✅ | En esta sesión, semilla 7 y 2 generaciones, en los dos modos: dos corridas sin ventana, el mismo CSV; con ventana (ESC inyectado en la pantalla final, que el log muestra: LEC-004), el mismo; la generación 1, igual con y sin evolución, con su control (la 2 difiere) (MODOS-22) |
| MODOS-QA-23 | CSV final | ✅ | `COLUMNAS_CSV` en el orden de la decisión 28 (`main.py:99-105`); la ruta con el modo (`:287-288`) (MODOS-23) |
| MODOS-QA-24 | `experimento.py` por modo | ✅ | Semillas × modos × {con, sin} (`experimento.py:311-312`); `resumir_corrida` (`:54`), `resumir_grupo` (`:90`), `comparar_evolucion` (`:125`) y `comparar_modos` (`:137-144`). En esta sesión, `--semillas 1 2 --generaciones 10` (`results/experimento_20261115-120912`): 8 CSV, 8 logs y `resumen.md`; tres corridas y las cinco comparaciones K de N, recalculadas con un script que no usa `experimento.py`, coinciden (MODOS-24) |
| MODOS-QA-25 | Pantalla final | ✅ | "LA CORRIDA" con la línea de LEC-001 y `->` (`pantalla_final.py:154-159`); el cofre por agentes y la primera generación (`:161-166`). `test_reportes.py:106` (MODOS-25) |
| MODOS-QA-26 | Sueltos | ✅ | `popup.py:95` sin el 50; el README sin `logs/` ni `checkpoints/` (MODOS-26) |
| MODOS-QA-27 | Experimento de cierre | ✅ | [Registrado](#experimento-modos-cierre), con la respuesta a las tres preguntas; su tabla y sus comparaciones son, línea por línea, las de `results/experimento_20261115-112804/resumen.md`. Corrió antes del commit `05078e5`: las 8 corridas de MODOS-QA-24, hechas desde ese commit, son byte a byte sus 10 primeras generaciones en las semillas 1 y 2 (MODOS-27) |
| MODOS-QA-28 | `python -m pytest -q` | ✅ | 53 passed en 22,8 s (MODOS-28) |
| MODOS-QA-29 | Docs | ✅ | Después del arreglo de esta sesión. README: modos, flags, 11 sensores, 5 salidas, puzzle, golpear, fitness, agua y energía, cada número contra lo que usa el código (40 revisados); sin "aprendizaje puro", `logs/` ni `checkpoints/`. `CLAUDE.md`: § Notas (sin las tres diferencias; qué manda `config.py` y qué no), § Lógica de negocio crítica y el árbol. DIAG-01 a DIAG-05, DIAG-08 a DIAG-13, DIAG-28 y DIAG-29 ✅ en este archivo (MODOS-29) |

**Observaciones que no cambian el veredicto:**
- **La primera pasada de MODOS-29.** `README.md:331` decía "Golpes requeridos: 2" para el árbol:
  coincidía con el `TREE_HITS_TO_CUT` de `config.py`, pero nadie lo lee y `world.py:29` pide 3. El
  DoD pedía que cada número coincidiera "con `config.py` o con el código", y la sesión 3 lo dio por
  bueno contra `config.py` (LEC-010). `CLAUDE.md:51` decía "varios se ignoran, ver Notas", y § Notas
  ya no los nombraba. Sigue siendo cierto para tres parámetros (`TREE_HITS_TO_CUT`,
  `STATS_UPDATE_FREQUENCY` y `PARTICLE_UPDATE_FREQUENCY`); `PERIMETER_MARGIN` y `BASE_SPRITE_SIZE`
  solo se imprimen. Ninguno estaba en las decisiones 15 y 16: van a
  [mejoras futuras](../product/mejoras_futuras.md). La fortaleza chica: el README decía 4x5 (`:123` y
  `:280`), como los comentarios de `config.py:111` y de `world.py`, y los muros son de 5x5.
- **Comparación 3:** el spec la titula "autónomo contra guiado" sin decir qué lado se cuenta;
  `comparar_modos` cuenta en cuántas semillas el guiado tuvo más (`experimento.py:138`), que es
  "cuánto pone la guía", lo que la decisión 29 dice que mide. El checker la dio PARCIAL por analogía
  con las comparaciones 1 y 2.
- **Decisión 11 en el popup:** muestra cuántos agentes de la generación abrieron el cofre, no la
  primera generación de la corrida; el resumen final de la consola, la pantalla final y el resumen de
  `experimento.py` sí la dicen. No es parte del DoD ni del QA manual.
- **Cooldown compartido:** `_try_hit_door` (`advanced_agent.py:642`) mira el mismo
  `last_tree_hit_tick` (120 ticks) que el corte, que se pone al cortar y al abrir una puerta. Ya
  estaba antes del bloque B (`cc9126b`); entre golpes a una misma puerta manda `DOOR_HIT_COOLDOWN`.
- `advanced_agent.py:418-423` (si se piden los dos giros, gana el más fuerte) corre en los dos modos:
  es del cuerpo común (decisión 4), no de la guía.
- **Borde numérico del sensor 7:** con un ángulo negativo del orden de −1e-20, `%` da 2π en punto
  flotante y el sensor sale 1,0. Es improbable y el test no lo cubre.
- **Fuera de las secciones del DoD:** el README dice "Mutación: Gaussiana (30% tasa)"
  (`README.md:252`), y `genetic_algorithm.py:113-114` la sube a 50% cuando la diversidad del fitness
  baja de 0,15. Los pesos del anti-círculo se leen con `getattr` y un valor por defecto distinto del
  de `config.py` (`advanced_agent.py:732-734`): hoy no pesa, porque `config.py` los define.

---

<a id="qa-pantallas-ver-aprender"></a>
## QA /qa-spec — Pantallas para ver aprender (2026-11-15)
**Veredicto:** APROBADO
**Verificación técnica:** sintaxis ✅ (`compileall` de `main.py`, `config.py` y `src`) · tests 123/123 en
26,4 s · build N/A (Python, sin build)
**Método:** cuatro checkers independientes (Explore/haiku, solo lectura) contra las decisiones, el DoD
y el QA manual de `docs/specs/active/PANTALLAS_VER_APRENDER.md`, sin leer su bitácora: datos
(PANTALLAS-02 a 05), boletín (06 a 10), pantallas (11 a 15) y docs (18). Los checkers no ejecutaban
nada: lo que pide corridas o capturas se volvió a correr en la sesión desde `f62a7f0`, con el árbol
limpio: las 4 corridas de referencia, tres con ventana y eventos inyectados (LEC-004), una medición
del costo del mapa de calor y del récord dentro de 4 corridas reales, y el control del azar. Cada
`archivo:línea` de la tabla se imprimió antes de copiarlo (LEC-006). Los checkers dieron PARCIAL en
03, 04, 05, 06, 08 y 15: en cada caso faltaba una corrida o una captura, que se hizo en la sesión, o
era un texto que el spec no fijaba o un desvío anotado (ver las observaciones). Los IDs
`PANTALLAS-NN` son los del QA manual del spec.

| ID | Criterio | Resultado | Evidencia / Gap |
|----|----------|-----------|-----------------|
| PANTALLAS-QA-01 | La simulación no cambia | ✅ | Las 4 corridas de referencia (semilla 7, 3 generaciones, guiado y autónomo, con evolución y sin ella) dan los 4 SHA-256 de la bitácora del spec. Con ventana, semilla 7 y 2 generaciones en los dos modos, y semilla 1 y 5 generaciones en el guiado: el mismo CSV que sin ventana (`cmp`) (PANTALLAS-01) |
| PANTALLAS-QA-02 | Sin azar nuevo | ✅ | `test_registro.py:171` compara el estado de `random` y de `np.random` antes y después de contar, mirar hitos, cerrar generaciones y armar el boletín: verde. Su control, vuelto a correr en esta sesión (un plugin de pytest del scratchpad agrega un `random.random()` al conteo): falla. Ningún módulo nuevo llama a `random` ni a `np.random` (PANTALLAS-02) |
| PANTALLAS-QA-03 | Mapa de calor | ✅ | Celda `int(x) // 16` e `int(y) // 16`, recortada a la grilla, solo los vivos (`registro.py:43-49`); después de `world.update()` y `tick += 1`, dentro del `if not paused` (`main.py:465-468`); valor por los ticks de su generación (`registro.py:94-97`); grillas de la generación 1 y de la última (`registro.py:88-92`); `HEATMAP_CELL_SIZE = 16` (`config.py:60`). Tests: `test_registro.py:55` (bordes), `:74` (solo vivos), `:81` (normalización) y `:95` (gen 1, última y arranque en cero). Costo, medido en esta sesión dentro de 4 corridas reales (semillas 7 y 1, los dos modos): de 28 a 36 µs por tick contra ticks de 4,9 a 7,1 ms, de 0,41 a 0,62 % (PANTALLAS-03) |
| PANTALLAS-QA-04 | Hitos | ✅ | Se miran en cada tick, después de que actúan los agentes (`main.py:447-451`); solo la primera vez, con generación, tick e id, en el orden del puzzle (`registro.py:51-64`); la línea de consola (`boletin.py:93`), con ventana y sin ella. Tests: `test_registro.py:116` y `:127`, y `test_humo.py:142` (el log contra el CSV, sin ventana). En esta sesión, en 7 logs (4 sin ventana y 3 con ventana), cada línea de hito coincide con la primera generación del CSV con esa columna `agentes_*` > 0 (PANTALLAS-04) |
| PANTALLAS-QA-05 | Mejor agente | ✅ | El récord cambia solo si se lo supera (`registro.py:76-77`, con `>`); `test_registro.py:138` (el empate no lo cambia). En esta sesión, en 4 corridas (semillas 7 y 1, los dos modos), su fitness redondeado a 4 decimales es el máximo de `fitness_max` del CSV; en las dos del autónomo el récord es de una generación anterior a la última (53,3098 contra 53,0123; 58,6046 contra 51,7472), así que el control "el mejor de la última" daría distinto. Sale en el log sin ventana ("Mejor agente de la corrida: #168 · generación 3") (PANTALLAS-05) |
| PANTALLAS-QA-06 | Los cuatro números | ✅ | K = mín(5, G − 1), sin la generación 1 (`boletin.py:104-108`); % para fitness y edad, × para manzanas y recorrido, "—" si la generación 1 vale 0, "una sola generación" con G = 1; la nota "se alargan" solo si es verdad (desvío confirmado por Fer en la sesión 1). Tests: `test_boletin.py:101` (K = 5) y los de K = 2, K = 1 y G = 1. Con G = 2, la nota dice "gen 1 → gen 2" (`boletin.py:110`): ver observaciones (PANTALLAS-06) |
| PANTALLAS-QA-07 | Embudo y cofre | ✅ | Embudo de la última generación con la primera vez de cada paso; una sola frase del cofre (`boletin.py:166`); "murieron todos" solo con `vivos` = 0 (`boletin.py:176-177`). Tests desde `test_boletin.py:196`. En los 7 logs de esta sesión la frase del cofre sale una vez y "murieron todos" no sale (ninguna última generación terminó con `vivos` = 0); en la captura de la pantalla final, la frase sale una vez (PANTALLAS-07) |
| PANTALLAS-QA-08 | Consola sin ventana | ✅ | `imprimir_resumen_final(registro)` va antes del `return` sin ventana (`pantalla_final.py:68-70`). En los logs sin ventana de esta sesión: encabezado con "0,8 min simulados" (3 × 960 ticks), los cuatro números con sus notas, el embudo, el mejor agente, la cobertura de la generación 1 y de la última, y la frase del cofre una vez; "últimas 3" no está en el código. `test_humo.py:126` (DIAG-15) (PANTALLAS-08) |
| PANTALLAS-QA-09 | Escala automática | ✅ | `escala` (`boletin.py:70`), con la tolerancia de la trampa de coma flotante del spec; los seis ejemplos de la decisión 10 en `test_boletin.py:76`, más todo 0, series que comparten eje y negativos; el formato de la decisión 8, con sus tests. Ningún gráfico usa la escala fija de 0 a 100. El control (la escala del popup), en la bitácora de la sesión 1 (PANTALLAS-09) |
| PANTALLAS-QA-10 | Fuentes | ✅ | `assets/fonts/`: Pixelify Sans Bold e Inter Regular, SemiBold y Bold, un `OFL.txt` por familia y `LEEME.md`. `fuentes.verificar()` (`fuentes.py:26`) corta con el nombre del archivo, antes de abrir la ventana (`main.py:302`). `test_fuentes.py:121` (archivos), `:139` (el control: la fuente de pygame no tiene la `→`) y los que recorren cada carácter de los textos de pantalla en su fuente. La `→` se ve en la captura de la pantalla final (PANTALLAS-10) |
| PANTALLAS-QA-11 | Sin popup | ✅ | `grep` no encuentra `popup`, `SummaryPopup`, `_datos_del_popup`, `MOUSEBUTTONDOWN` ni los `get_*_skill` en `main.py`, `src/`, `tests/` ni `experimento.py`; `src/ui/popup.py` no existe. Las 3 corridas con ventana de esta sesión llegaron al final con 0 clics. DIAG-32 ✅ (PANTALLAS-11) |
| PANTALLAS-QA-12 | Panel | ✅ | La columna entera (`main.py:349`: x 960, 240×800); datos con "N de M" (`stats.py:51-52`), gráficos de fitness y manzanas con la escala automática, puzzle, "Se dibuja al terminar la generación 1" (`stats.py:29`) y teclas (`stats.py:32`). Captura (semilla 1, generación 5): "5 de 5", ejes de 0 a 80 y de 0 a 0,8, el último valor de cada serie rotulado ("58,3" y "24,7"), G1 y G4, "Gen 4: 2 agentes con llave roja" (PANTALLAS-12) |
| PANTALLAS-QA-13 | Aviso de fin de generación | ✅ | 2,5 s y 440 px (`avisos.py:16` y `:19`); después de la última generación no hay: el `return` de `main.py:502` va antes del aviso. `test_pantallas.py:129` (a los 2,4 s está, a los 2,6 s no) y `:203` (una corrida con ventana en el driver dummy). Captura: "Generación 2 terminada · Fitness promedio 24,5 +2,6 · Manzanas por agente 0,75 +0,12", con las diferencias en verde y la barra por la mitad (PANTALLAS-13) |
| PANTALLAS-QA-14 | Aviso de hito | ✅ | 4 s y no más de 3 (`avisos.py:17-18`), con el reloj como parámetro; los cinco títulos (`boletin.py:18-19`) y subtítulos (`test_pantallas.py:165`). `test_pantallas.py:141` (4 s, apilados en orden, tope de 3). Captura: "¡Primera llave roja!" en dorado, con el sprite de la llave, y "Un agente la agarró en la generación 2" (PANTALLAS-14) |
| PANTALLAS-QA-15 | Pantalla final | ✅ | `dibujar_boletin` en `pantalla_final.py`: encabezado, cuatro números, gráficos con las marcas, mapas con la raíz cuadrada (`:124`) y el contorno de las fortalezas (`:128`), embudo, mejor agente y pie; se cierra con ESC o ENTER (`:91`). `textos_del_cuadro`, `_dibujar_cuadro`, `_grafico_de_fitness` y `_renglones_de_clustering` no existen. Captura (semilla 1, 5 generaciones): todo lo de la decisión 14, la marca "1ª llave roja · gen 2", el cofre una vez, el mejor agente #285 con fitness 69,7 (el máximo de `fitness_max`), sin MOVIMIENTO ni CLUSTERING (PANTALLAS-15) |
| PANTALLAS-QA-16 | Ventana con eventos inyectados | ✅ | `ventana.py` del scratchpad (envuelve `mostrar_pantalla_final`, `pygame.event.get` y `pygame.display.flip`; `TARGET_FPS` = 100.000): 3 corridas, código 0, un solo ESC inyectado, recién después de capturar la pantalla final, y 0 clics; el log de cada una tiene la línea del hito y el boletín. 34, 33 y 88 s (PANTALLAS-16) |
| PANTALLAS-QA-17 | Tests | ✅ | 123 passed en 26,4 s. Cada test nuevo, con su control en la bitácora del spec: 9 del bloque A y 7 del B; el del azar, vuelto a correr en esta sesión (PANTALLAS-17) |
| PANTALLAS-QA-18 | Docs | ✅ | README: el árbol de `src/ui/` es la carpeta, sin el popup (`README.md:89-94`); el panel (`:177`), la pantalla final (`:181`) y la licencia de las fuentes (`:663-665`). `CLAUDE.md:71`, sin el popup. DIAG-32 ✅ (`AnalisisQA.md:153`) (PANTALLAS-18) |

**Observaciones que no cambian el veredicto:**
- **Con 2 generaciones, la nota de los cuatro números dice "gen 1 → gen 2"** (`boletin.py:110`), y no
  "gen 1 → promedio de las últimas 1", como da el texto literal de la decisión 14 b. Dice lo mismo. La
  sesión 1 lo anotó entre los textos que el spec no fijaba, pero la decisión sí lo fija: es un desvío
  del texto. Fer lo confirmó el 2026-11-15 y queda así (LEC-014).
- **El fondo del aviso de fin de generación tiene alfa 230 de 255** (`avisos.py:27`, ~90 % opaco): es
  semitransparente, como pide la decisión 11, pero el mundo apenas se ve detrás.
- **Con ventana, después del boletín sale el "REPORTE COMPLETO DE APRENDIZAJE"** de
  `create_learning_report` (`pantalla_final.py:72`); sin ventana no sale. Era igual antes del spec
  (`4212fad`), y el spec no lo toca.
- **El costo del mapa de calor da más que en la sesión 1** (0,41 a 0,62 % contra 0,27 %): la sesión 1
  lo midió con `timeit` fuera de la corrida, y esta lo mide adentro, con el envoltorio incluido. Las
  dos quedan por debajo del 1 %.
- **`test_humo.py` corre sin ventana:** la coincidencia de las líneas de hito con el CSV con ventana
  no tiene test; se verificó en las corridas de esta sesión.
- En `src/ui/__pycache__/` queda un `popup.cpython-311.pyc` viejo, fuera de git: Python no lo importa
  sin su `.py`.

---

<a id="experimento-puzzle-a"></a>

## Que el puzzle se pueda aprender — experimento A, la recompensa por acercarse (2026-11-15, PUZZLE-12)

**Qué cambió** (bloque A del [spec](../specs/active/PUZZLE_APRENDIBLE.md)): con `--acercarse`, el
fitness suma `FITNESS_ACERCARSE` (10) × (pasos que dio + avance en el paso actual). El avance va de 0 a
1: lo más cerca que llegó al objetivo de la brújula desde que empezó el paso, y en las puertas, mitad
eso y mitad los golpes que contaron. Vale para los dos modos; el experimento es del autónomo.

**Antes de correr, los controles** (detalle en la bitácora del spec): apagado, las 8 corridas del
autónomo y del guiado, semillas 1 y 2, con evolución y sin ella, 10 generaciones, son byte a byte las
del [experimento de cierre](#experimento-modos-cierre) sin la columna `acercarse` (PUZZLE-07);
prendido, la misma semilla da el mismo CSV, con ventana y sin ella (PUZZLE-09).

**Cómo se corrió:** 10 corridas, 11 a la vez, en 12 núcleos: 451 s. Carpeta
`results/experimento_20261115-200451`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --acercarse`

**Ayudas prendidas:** recompensa por acercarse.

**Por grupo** (promedio ± desvío muestral entre semillas):

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| autonomo | Con evolución | 5 | 19.05 ± 0.73 | 34.50 ± 1.98 | 15.45 ± 1.36 | 0.30 ± 0.07 | 0.88 ± 0.15 | 0.58 ± 0.15 | 919 ± 103 | 3.52 ± 1.00 | 1.4 ± 0.5 | 0 de 5 |
| autonomo | Sin evolución | 5 | 17.05 ± 0.44 | 17.29 ± 0.90 | 0.24 ± 0.77 | 0.21 ± 0.05 | 0.20 ± 0.07 | -0.00 ± 0.04 | 884 ± 9 | 0.72 ± 0.36 | 1.2 ± 0.4 | 0 de 5 |

**Comparaciones pareadas por semilla** (un empate no cuenta como más):

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5, más con la puerta de madera abierta en 1 de 5 y más llave roja por 1.000 px en 2 de 5.
- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 0 de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 2 de 5. Cada uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no.

**Por corrida:**

| Semilla | Modo | Evolución | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Agentes con llave roja, últimas 5 | Puerta de madera, últimas 5 | Llave roja por 1.000 px | Etapa máxima | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | autonomo | Con evolución | 30 | 18.80 | 34.72 | 15.93 | 0.26 | 0.97 | 0.71 | 778 | 3.20 | 0.20 | 3.18 | 2 | — |
| 1 | autonomo | Sin evolución | 30 | 17.23 | 17.86 | 0.62 | 0.22 | 0.26 | 0.04 | 883 | 0.60 | 0.00 | 2.82 | 1 | — |
| 2 | autonomo | Con evolución | 30 | 18.44 | 32.74 | 14.31 | 0.27 | 0.79 | 0.52 | 963 | 2.00 | 0.00 | 2.14 | 1 | — |
| 2 | autonomo | Sin evolución | 30 | 16.64 | 15.68 | -0.96 | 0.16 | 0.10 | -0.06 | 886 | 0.40 | 0.00 | 2.73 | 1 | — |
| 3 | autonomo | Con evolución | 30 | 18.35 | 32.58 | 14.23 | 0.25 | 0.68 | 0.43 | 842 | 3.60 | 0.00 | 3.09 | 1 | — |
| 3 | autonomo | Sin evolución | 30 | 17.43 | 17.66 | 0.23 | 0.19 | 0.18 | -0.02 | 891 | 1.20 | 0.00 | 5.82 | 1 | — |
| 4 | autonomo | Con evolución | 30 | 19.74 | 35.01 | 15.27 | 0.41 | 0.89 | 0.48 | 1010 | 4.40 | 0.00 | 3.19 | 1 | — |
| 4 | autonomo | Sin evolución | 30 | 17.42 | 17.60 | 0.18 | 0.29 | 0.27 | -0.02 | 890 | 0.40 | 0.00 | 1.97 | 1 | — |
| 5 | autonomo | Con evolución | 30 | 19.91 | 37.43 | 17.52 | 0.29 | 1.07 | 0.78 | 1000 | 4.40 | 0.00 | 2.89 | 2 | — |
| 5 | autonomo | Sin evolución | 30 | 16.50 | 17.64 | 1.14 | 0.17 | 0.21 | 0.04 | 868 | 1.00 | 0.00 | 5.63 | 2 | — |

**Lectura, contra el experimento de cierre** (mismas semillas y generaciones, sin la ayuda). El
fitness no se compara entre los dos: este tiene un término más.

1. **Criterio de la decisión 13: no.** Con evolución, la puerta de madera de las últimas 5 vale 0 en
   cuatro semillas y 0,2 en la semilla 1 (un agente, en la generación 26): 0 de 5 semillas llegan a 1
   por generación. En el cierre, también 0 de 5. Sin contar la generación 1, que es la misma con
   evolución y sin ella y en la semilla 5 tiene un agente con la puerta abierta en los dos
   experimentos, es la única vez que se abrió en las 145 generaciones evolucionadas; en el cierre,
   ninguna.
2. **Secundario, usar la brújula: no.** Llave roja por 1.000 px con evolución: 2,90 contra 2,87 en el
   cierre, y más que la línea base en 2 de 5 semillas (en el cierre, 1 de 5). Hay algunos agentes más
   con llave roja en las últimas 5 (3,52 contra 3,16), pero también caminan más (1.201 contra 1.087 px
   por agente): por distancia recorrida la encuentran igual que antes.
3. **Parada de la decisión 14: no salta.** Las manzanas por agente con evolución en las últimas 5 van
   de 0,68 a 1,07 (promedio 0,88; en el cierre, 0,83): ninguna semilla por debajo de 0,42. La
   recompensa no le gana a la comida.

**Además:**
- **La línea base es la del cierre:** en las 5 semillas y las 30 generaciones, el CSV sin evolución es
  igual al del cierre salvo `fitness_*` y `acercarse` (PUZZLE-08, a escala). En cerebros al azar, el
  término suma entre 0,60 y 0,71 al fitness promedio de cada generación, cuyo desvío entre agentes es
  de ~11: avanzan poco hacia su paso. La generación 1 con evolución también es la del cierre, salvo el
  fitness, en 5 de 5.
- **En dos semillas viven bastante menos:** edad promedio de las últimas 5, 778 contra 1.045 ticks en
  la semilla 1 y 842 contra 998 en la 3; en las otras tres, parecida. En el grupo, 919 contra 990.
- **La población converge igual:** diversidad en la generación 30 entre 0,059 y 0,087 (cierre: 0,060 a
  0,103).

**En corto:** la recompensa por acercarse sola no hace que el autónomo pase la puerta de madera (0 de
5, igual que sin ella), ni que encuentre la llave roja por la brújula en lugar de por caminar. Tampoco
le quita comida. Siguen el experimento B (el currículo: nacer con la llave roja) y el C (las dos
juntas).
