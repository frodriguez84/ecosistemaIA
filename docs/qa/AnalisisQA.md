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
| DIAG-33 | Si `_ubicar_agentes` no encuentra lugar al azar (500 intentos) ni en la grilla de respaldo, el agente va a (100, 100) sin mirar nada: con las fortalezas fijas es adentro de la chica, y el agente nace encerrado (la puerta es pared hasta que la abre, y la abre desde afuera). Pasa en corridas reales: 49 agentes en 30 de los 130 logs de `results/`, y en una de las 6 referencias de la sesión. En 20 semillas × 30 generaciones de mapas (sin simular: el mapa y la ubicación de los agentes), 11 agentes nacen adentro con las fijas y 0 con las móviles, que casi nunca cubren ese punto. Arreglarlo cambia el CSV de las corridas donde pasa. Encontrado el 2026-11-16 con las [fortalezas móviles](#fortalezas-moviles). | `main.py:92-95` | Mejoras futuras |
| DIAG-34 | `_generate_red_key` sortea la llave roja lejos de los obstáculos y fuera de las fortalezas, pero no mira el estanque (va en otra lista, `pond_obstacles`): la llave puede caer en el agua. En 20 semillas × 30 generaciones de mapas, en 3 de 600 no queda ningún lugar donde un agente pueda estar a menos de 27 px (el radio para agarrarla): esa generación nadie la puede agarrar, con las fortalezas fijas y con las móviles por igual. En otras 600 (sin ubicar agentes), cae sobre una baldosa del estanque en 13. Con el currículo pesa solo después del corte (antes nacen con ella). Arreglarlo cambia el CSV de las corridas donde pasa. Encontrado el 2026-11-16 con los tests de las [fortalezas móviles](#fortalezas-moviles). | `src/world/world.py:1008` (`_generate_red_key`) | Mejoras futuras |

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

**Qué cambió** (bloque A del [spec](../specs/done/PUZZLE_APRENDIBLE.md)): con `--acercarse`, el
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

---

<a id="experimento-puzzle-b"></a>

## Que el puzzle se pueda aprender — experimento B, el currículo (2026-11-15, PUZZLE-16)

**Qué cambió** (bloque B del [spec](../specs/done/PUZZLE_APRENDIBLE.md)): con `--curriculo`, las
generaciones 1 a 15 (`CURRICULO_HASTA_GENERACION`) nacen con la llave roja, élites incluidas y sin su
premio; desde la 16, sin ella. El mapa no cambia: la brújula apunta a la puerta de madera, que es pared
para cada agente hasta que la abre. Sin la recompensa por acercarse. En las generaciones 1 a 15,
`agentes_llave_roja` vale 60: es la llave dada, y `etapa_inicial` vale 1.

**Antes de correr, los controles** (detalle en la bitácora del spec): apagados los dos switches, las 8
corridas del autónomo y del guiado, semillas 1 y 2, con evolución y sin ella, 10 generaciones, son
byte a byte las del [experimento de cierre](#experimento-modos-cierre) sin `acercarse` ni
`etapa_inicial` (PUZZLE-07), y con `--acercarse` sola, semillas 1 y 2, las 10 primeras generaciones
del [experimento A](#experimento-puzzle-a) sin `etapa_inicial`. Con `--curriculo`, la misma semilla da
el mismo CSV, con ventana y sin ella (PUZZLE-09).

**Cómo se corrió:** 10 corridas, 11 a la vez, en 12 núcleos: 429 s la más lenta. Carpeta
`results/experimento_20261115-205826`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --curriculo`

**Ayudas prendidas:** currículo.

**Por grupo** (promedio ± desvío muestral entre semillas):

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| autonomo | Con evolución | 5 | 17.86 ± 0.90 | 31.00 ± 1.90 | 13.15 ± 1.76 | 0.30 ± 0.05 | 0.77 ± 0.17 | 0.47 ± 0.19 | 954 ± 60 | 2.88 ± 1.28 | 2.2 ± 0.4 | 0 de 5 |
| autonomo | Sin evolución | 5 | 16.46 ± 0.98 | 16.58 ± 0.87 | 0.11 ± 0.98 | 0.23 ± 0.06 | 0.20 ± 0.07 | -0.02 ± 0.05 | 884 ± 9 | 0.72 ± 0.36 | 2.0 ± 0.7 | 0 de 5 |

**Comparaciones pareadas por semilla** (un empate no cuenta como más):

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5, más con la puerta de madera abierta en 0 de 5 y más llave roja por 1.000 px en 1 de 5.
- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 0 de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 1 de 5. Cada uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no.

**Por corrida:**

| Semilla | Modo | Evolución | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Agentes con llave roja, últimas 5 | Puerta de madera, últimas 5 | Llave roja por 1.000 px | Etapa máxima | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | autonomo | Con evolución | 30 | 17.59 | 28.99 | 11.40 | 0.33 | 0.59 | 0.27 | 942 | 1.80 | 0.00 | 2.46 | 2 | — |
| 1 | autonomo | Sin evolución | 30 | 17.35 | 17.15 | -0.21 | 0.24 | 0.26 | 0.02 | 883 | 0.60 | 0.00 | 2.82 | 3 | — |
| 2 | autonomo | Con evolución | 30 | 16.65 | 30.83 | 14.18 | 0.22 | 0.79 | 0.57 | 988 | 1.40 | 0.00 | 1.47 | 2 | — |
| 2 | autonomo | Sin evolución | 30 | 15.76 | 15.03 | -0.73 | 0.18 | 0.10 | -0.08 | 886 | 0.40 | 0.00 | 2.73 | 2 | — |
| 3 | autonomo | Con evolución | 30 | 17.68 | 29.90 | 12.23 | 0.32 | 0.60 | 0.28 | 854 | 4.40 | 0.00 | 3.76 | 2 | — |
| 3 | autonomo | Sin evolución | 30 | 17.35 | 16.88 | -0.47 | 0.24 | 0.18 | -0.07 | 891 | 1.20 | 0.00 | 5.82 | 2 | — |
| 4 | autonomo | Con evolución | 30 | 19.07 | 31.29 | 12.22 | 0.36 | 0.90 | 0.54 | 996 | 3.00 | 0.00 | 2.14 | 2 | — |
| 4 | autonomo | Sin evolución | 30 | 16.70 | 16.92 | 0.22 | 0.31 | 0.27 | -0.04 | 890 | 0.40 | 0.00 | 1.97 | 1 | — |
| 5 | autonomo | Con evolución | 30 | 18.30 | 34.01 | 15.70 | 0.28 | 0.98 | 0.70 | 988 | 3.80 | 0.00 | 2.46 | 3 | — |
| 5 | autonomo | Sin evolución | 30 | 15.15 | 16.91 | 1.76 | 0.17 | 0.21 | 0.04 | 868 | 1.00 | 0.00 | 5.63 | 2 | — |


**Lectura, contra el experimento de cierre y el A** (mismas semillas y generaciones). El fitness no se
compara entre experimentos; las manzanas y las columnas `agentes_*` de las últimas 5, sí.

1. **Criterio de la decisión 13: no.** La puerta de madera vale 0 en las últimas 5 de las 5 semillas,
   con evolución y sin ella: 0 de 5, como en el cierre y en el A. Después del corte (generaciones 16 a
   30) se abrió una sola vez en las 75 generaciones evolucionadas (semilla 5, generación 22).
2. **Con la llave dada, la evolución tampoco aprende a abrir la puerta.** En las 15 generaciones del
   currículo, con los 60 agentes de cada generación con la llave, la puerta se abrió 8 veces en las 5
   semillas con evolución y 9 sin ella; en las generaciones 11 a 15, 0,16 agentes por generación en
   promedio en las dos. Con la llave en la mano, llegar a la puerta y golpearla dos veces no sale más
   seguido que con cerebros al azar.
3. **Secundario, usar la brújula: no.** Llave roja por 1.000 px con evolución en las últimas 5: 2,46
   (cierre 2,87, A 2,90); más que la línea base en 1 de 5 semillas.
4. **La línea base de las generaciones 16 a 30 es la del cierre:** byte a byte, salvo `etapa_inicial`,
   en las 5 semillas. El currículo cambia solo las generaciones en que se da la llave, y las últimas 5
   se comparan contra lo mismo que en el cierre y en el A.

**Además:** manzanas por agente con evolución en las últimas 5, 0,77 (cierre 0,83), de 0,59 a 0,98 por
semilla; edad promedio 954 ticks (cierre 990); diversidad en la generación 30 entre 0,070 y 0,084. La
etapa máxima (2 o 3) sale de las generaciones del currículo, que cuentan la llave dada: con ella, alguno
abrió la puerta, y en dos corridas uno agarró la llave dorada.

---

<a id="experimento-puzzle-c"></a>

## Que el puzzle se pueda aprender — experimento C, las dos ayudas (2026-11-15, PUZZLE-16)

**Qué cambió:** `--acercarse --curriculo`. Las generaciones 1 a 15 nacen con la llave roja, y la
recompensa por acercarse mide desde el primer tick el camino a la puerta de madera y los golpes que
contaron; la llave dada no cuenta como paso (decisión 10), así que el término arranca en 0.

**Cómo se corrió:** 10 corridas, 11 a la vez, en 12 núcleos: 396 s la más lenta. Carpeta
`results/experimento_20261115-210549`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --acercarse --curriculo`

**Ayudas prendidas:** recompensa por acercarse y currículo.

**Por grupo** (promedio ± desvío muestral entre semillas):

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| autonomo | Con evolución | 5 | 18.87 ± 0.50 | 32.88 ± 3.41 | 14.01 ± 3.14 | 0.30 ± 0.05 | 0.72 ± 0.21 | 0.42 ± 0.19 | 951 ± 89 | 3.52 ± 1.99 | 1.8 ± 0.4 | 0 de 5 |
| autonomo | Sin evolución | 5 | 16.69 ± 0.97 | 17.29 ± 0.90 | 0.60 ± 1.01 | 0.23 ± 0.06 | 0.20 ± 0.07 | -0.02 ± 0.05 | 884 ± 9 | 0.72 ± 0.36 | 2.0 ± 0.7 | 0 de 5 |

**Comparaciones pareadas por semilla** (un empate no cuenta como más):

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5, más con la puerta de madera abierta en 0 de 5 y más llave roja por 1.000 px en 1 de 5.
- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 0 de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 1 de 5. Cada uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no.

**Por corrida:**

| Semilla | Modo | Evolución | Generaciones | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom., últimas 5 | Agentes con llave roja, últimas 5 | Puerta de madera, últimas 5 | Llave roja por 1.000 px | Etapa máxima | Cofre en la gen. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | autonomo | Con evolución | 30 | 18.74 | 28.12 | 9.38 | 0.27 | 0.37 | 0.10 | 954 | 0.80 | 0.00 | 1.70 | 2 | — |
| 1 | autonomo | Sin evolución | 30 | 17.57 | 17.86 | 0.29 | 0.24 | 0.26 | 0.02 | 883 | 0.60 | 0.00 | 2.82 | 3 | — |
| 2 | autonomo | Con evolución | 30 | 19.24 | 33.31 | 14.07 | 0.37 | 0.79 | 0.42 | 1018 | 3.20 | 0.00 | 2.36 | 1 | — |
| 2 | autonomo | Sin evolución | 30 | 16.04 | 15.68 | -0.36 | 0.18 | 0.10 | -0.08 | 886 | 0.40 | 0.00 | 2.73 | 2 | — |
| 3 | autonomo | Con evolución | 30 | 19.26 | 37.00 | 17.74 | 0.28 | 0.89 | 0.61 | 1029 | 6.40 | 0.00 | 4.51 | 2 | — |
| 3 | autonomo | Sin evolución | 30 | 17.60 | 17.66 | 0.07 | 0.24 | 0.18 | -0.07 | 891 | 1.20 | 0.00 | 5.82 | 2 | — |
| 4 | autonomo | Con evolución | 30 | 19.04 | 34.82 | 15.78 | 0.34 | 0.84 | 0.49 | 949 | 3.60 | 0.00 | 3.16 | 2 | — |
| 4 | autonomo | Sin evolución | 30 | 16.88 | 17.60 | 0.72 | 0.31 | 0.27 | -0.04 | 890 | 0.40 | 0.00 | 1.97 | 1 | — |
| 5 | autonomo | Con evolución | 30 | 18.07 | 31.17 | 13.10 | 0.24 | 0.72 | 0.48 | 806 | 3.60 | 0.00 | 3.03 | 2 | — |
| 5 | autonomo | Sin evolución | 30 | 15.38 | 17.64 | 2.26 | 0.17 | 0.21 | 0.04 | 868 | 1.00 | 0.00 | 5.63 | 2 | — |


**Lectura, contra el cierre, el A y el B:**

1. **Criterio de la decisión 13: no.** La puerta de madera vale 0 en las últimas 5 de las 5 semillas: 0
   de 5. Después del corte no se abrió ninguna vez en las 75 generaciones evolucionadas.
2. **Con la llave dada y la recompensa hacia la puerta, tampoco aprenden a abrirla.** En las 15
   generaciones del currículo, la puerta se abrió 6 veces en las 5 semillas con evolución y 9 sin ella.
3. **Secundario: no.** Llave roja por 1.000 px con evolución: 2,95 (cierre 2,87); más que la línea base
   en 1 de 5.
4. **La semilla 1 come y camina menos:** 0,37 manzanas por agente en las últimas 5, debajo del 0,42 de
   la parada de la decisión 14 (que se evaluaba después del A; acá sería 1 semilla de 5, no 3), con 472
   px de recorrido (cierre 1.257) y 0,8 agentes con llave roja. En el grupo, 0,72 manzanas (cierre 0,83).
5. **La línea base es la del B:** en las 5 semillas y las 30 generaciones, el CSV sin evolución es igual
   al del B salvo `fitness_*` y `acercarse` (PUZZLE-08, con el currículo).

<a id="puzzle-respuesta-item-5"></a>

### La respuesta al ítem 5, con los tres experimentos

Autónomo, semillas 1 a 5, 30 generaciones; con evolución, promedio entre semillas de las últimas 5
generaciones, salvo la última columna.

| | Puerta de madera | Criterio (4 de 5) | Llave roja | Llave roja por 1.000 px | Manzanas por agente | Puertas abiertas en las gens 1-15, con / sin evolución |
|---|---|---|---|---|---|---|
| Cierre, sin ayuda | 0 | 0 de 5 | 3,16 | 2,87 | 0,83 | 1 / 1 (sin llave; la generación 1 de la semilla 5, la misma en los dos) |
| A, acercarse | 0,04 | 0 de 5 | 3,52 | 2,90 | 0,88 | 1 / 1 (sin llave; la misma generación 1 de la semilla 5) |
| B, currículo | 0 | 0 de 5 | 2,88 | 2,46 | 0,77 | 8 / 9 |
| C, las dos | 0 | 0 de 5 | 3,52 | 2,95 | 0,72 | 6 / 9 |

- **Ninguna de las dos ayudas, ni las dos juntas, hace que el autónomo aprenda a pasar la puerta de
  madera:** 0 de 5 en A, B y C, como sin ayuda. Tampoco encuentra la llave roja por la brújula en lugar
  de por caminar: la llave roja por 1.000 px queda entre 2,46 y 2,95 con evolución, contra 2,87 sin
  ayuda, y supera a la línea base en 1 o 2 semillas de 5.
- **El cuello no es solo encontrar la llave.** Con la llave dada a los 60 agentes durante 15
  generaciones, la evolución abre la puerta lo mismo que cerebros al azar: 14 veces entre B y C, contra
  18 de sus líneas base. Por qué no se midió. Dos candidatos, de la medición del § Problema del spec: la
  puerta pide llegar a menos de 25 px de su centro y golpear dos veces con espera entre golpes, y la
  evolución deja de golpear porque golpear cuesta energía.
- **La evolución sigue aprendiendo a comer y a caminar:** en los tres, sube más que su línea base en
  fitness y en manzanas por agente en 5 de 5 semillas.

**En corto:** el ítem 5 se cierra con un resultado negativo. Ni la recompensa por acercarse ni el
currículo de nacer con la llave hacen que el autónomo aprenda la puerta de madera; con la llave dada,
la evolución la abre tanto como el azar. Lo que sigue es una decisión de Fer (en
[mejoras futuras](../product/mejoras_futuras.md), la medición que diría dónde se traba).

---

<a id="qa-puzzle-aprendible"></a>
## QA /qa-spec — Que el puzzle se pueda aprender (2026-11-15)
**Veredicto:** APROBADO (la primera pasada dio PARCIAL en PUZZLE-16 por dos celdas de la tabla de la
respuesta al ítem 5; se corrigieron en la sesión y se re-verificaron)
**Verificación técnica:** sintaxis ✅ (`compileall` de `main.py`, `config.py`, `src`, `experimento.py`
y `tests`) · tests 155/155 en 35,2 s · build N/A (Python, sin build)
**Método:** cuatro checkers independientes (Explore/haiku, solo lectura) contra las decisiones, el DoD
y el QA manual de `docs/specs/active/PUZZLE_APRENDIBLE.md`, sin leer su bitácora (salvo el de los
experimentos, solo la frase de la parada de la decisión 14): la recompensa (PUZZLE-01 a 06 y 10), el
currículo (01, 10, 13 a 15), el resumen y los experimentos (11, 12 y 16) y los docs (18). Los checkers
no ejecutaban nada: lo que pide corridas se volvió a correr en la sesión desde `a5759fd` (el árbol
tenía solo el cambio local de Fer en `config.py`, dos comentarios): las 12 corridas de PUZZLE-07 y 08,
las 9 de PUZZLE-09 (3 con ventana, con ESC inyectado y capturas, LEC-004) y el control de los tests
nuevos en dos worktrees. Cada `archivo:línea` de la tabla se imprimió antes de copiarlo (LEC-006). Los
checkers dieron PARCIAL en tres criterios: el de la recompensa, por el tope de los golpes de la
decisión 6 (se cumple por construcción, ver PUZZLE-QA-04); el del currículo, porque no leyó la brújula
ni la pared (evidencia de código en PUZZLE-QA-13); y el de los experimentos, por la tabla de la
respuesta al ítem 5 (PUZZLE-QA-16, corregida). Los IDs `PUZZLE-NN` son los del QA manual del spec.

| ID | Criterio | Resultado | Evidencia / Gap |
|----|----------|-----------|-----------------|
| PUZZLE-QA-01 | Switches en `config.py` | ✅ | `config.py:112-113` (`RECOMPENSA_ACERCARSE = False`, `FITNESS_ACERCARSE = 10.0`) y `:116-117` (`CURRICULO = False`, `CURRICULO_HASTA_GENERACION = 15`). `--acercarse` y `--curriculo` en `main.py:145-151` y en `experimento.py:337-342`, con la ayuda en español; `experimento.py:369-372` los pasa a cada corrida. `test_acercarse.py:176` y `:187`, `test_curriculo.py:72` (PUZZLE-01) |
| PUZZLE-QA-02 | Avance en una llave | ✅ | `_medir_acercamiento` (`advanced_agent.py:214-225`): d0 en el primer tick de la etapa y dmín con `min`, en línea recta (`math.hypot`) al objetivo de `_proximo_paso` (`:200-212`), sin el tope de `VISION_RANGE`. `_avance_en_el_paso` (`:227-239`): `(d0 − dmin) / d0`, 1 si d0 es 0. `test_acercarse.py:100`: de 200 a 50 px, 0,75 × `FITNESS_ACERCARSE` (PUZZLE-02) |
| PUZZLE-QA-03 | Avance en una puerta | ✅ | `advanced_agent.py:235-238`: `(camino + golpes / necesarios) / 2`, con `DOOR_HITS_TO_OPEN` o `DOOR_IRON_HITS_TO_OPEN`. Los golpes son los de `golpes_puerta`, que `obstacles.py:262-266` suma solo fuera del cooldown del agente y `world.py:930-934` solo con la llave y a menos de 25 px. `test_acercarse.py:129` (PUZZLE-03) |
| PUZZLE-QA-04 | Sin trampa | ✅ | dmín solo baja (`advanced_agent.py:225`): quedarse cerca no suma y alejarse no resta. El tope de los golpes en los necesarios menos uno (decisión 6) sale por construcción: el golpe que los completa devuelve `True` (`obstacles.py:272-274`) y `world.py:934-935` pasa al agente a la etapa 2 en la misma llamada. Dar el paso: `pasos_que_dio` sube 1 y el avance del paso nuevo arranca en 0 (`advanced_agent.py:231-232`). `test_acercarse.py:107` y `:145` (PUZZLE-04) |
| PUZZLE-QA-05 | Sin azar | ✅ | La medición usa `math.hypot`, sin `random` (`advanced_agent.py:214-225`), y corre una vez por tick, después de moverse (`:547-549`). `test_acercarse.py:239`: el estado de `random` y de `np.random`, igual después de `decide()` + `act()` en el autónomo con el switch (PUZZLE-05) |
| PUZZLE-QA-06 | Común a los modos | ✅ | Ni el término (`advanced_agent.py:786-790`) ni la medición (`:547-549`) miran `MODO`. `test_acercarse.py:260`: la misma trayectoria da el mismo término en guiado y autónomo (PUZZLE-06) |
| PUZZLE-QA-07 | Apagado = hoy | ✅ | En esta sesión, autónomo y guiado, semillas 1 y 2, con evolución y sin ella, 10 generaciones: las 8, sin `acercarse` ni `etapa_inicial` (que valen 0), son las 10 primeras filas del cierre (`results/experimento_20261115-112804`). Además, autónomo con `--acercarse`, semillas 1 y 2, con evolución y sin ella: las 10 primeras del experimento A, sin `etapa_inicial` (PUZZLE-07) |
| PUZZLE-QA-08 | Línea base intacta | ✅ | En esta sesión, autónomo sin evolución con `--acercarse`, semillas 1 y 2: igual al cierre salvo `fitness_*`, `acercarse` y `etapa_inicial`; `fitness_*` cambia y `fitness_prom` es más alto en las 10 generaciones, así que la comparación ve diferencias. Con el currículo, desde los CSV: la línea base del C es la del B salvo `fitness_*` y `acercarse`, en las 5 semillas y las 30 generaciones. `test_humo.py:135` (PUZZLE-08) |
| PUZZLE-QA-09 | Reproducible | ✅ | En esta sesión, semilla 7, 2 generaciones, autónomo, con cada switch: dos corridas sin ventana y una con ventana (un solo ESC, inyectado después de capturar la pantalla final) dan el mismo CSV. Con `--curriculo`, `54ab394b…`, y con los dos, `b2b65538…`: los SHA-256 de la bitácora. Con `--acercarse`, `5a6d88a1…` (el de la sesión 1 era de antes de la columna `etapa_inicial`). `test_humo.py:106` (PUZZLE-09) |
| PUZZLE-QA-10 | CSV y ruta | ✅ | `COLUMNAS_CSV` con `acercarse` después de `modo` y `etapa_inicial` después de `generacion` (`main.py:114`), y `_fila_csv` las llena en ese orden (`:180-183`); `_ruta_csv_por_defecto` con `_acercarse` y `_curriculo` (`:201-207`). `test_acercarse.py:199`, `test_curriculo.py:260` y `:277` (PUZZLE-10) |
| PUZZLE-QA-11 | Resumen | ✅ | `experimento.py:98-103` (puerta de madera y llave roja por 1.000 px de las últimas 5), `:241-245` (K de N y la línea del criterio, `_linea_del_criterio` en `:216-228`), `:259-263` (las ayudas) y `:306-312` (la marca del currículo). El checker recalculó desde los CSV la puerta, la llave roja y la llave roja por 1.000 px de las 30 corridas de A, B y C y de las 10 del autónomo del cierre: coinciden con cada `resumen.md` a dos decimales (semilla 1 del A: 0,20 y 0,00; 3,18 y 2,82). `test_resumen.py:85`, `:273`, `:303`, `:310` y `:330` (PUZZLE-11) |
| PUZZLE-QA-12 | Experimento A | ✅ | [Registrado](#experimento-puzzle-a), con su lectura contra el cierre y el criterio aplicado: 0 de 5, secundario 2 de 5, como su `resumen.md`. La parada de la decisión 14, evaluada en la bitácora (sesión 1); el checker recalculó las manzanas por agente con evolución de las últimas 5 desde los CSV: de 0,68 a 1,07, ninguna debajo de 0,42 (PUZZLE-12) |
| PUZZLE-QA-13 | Nacen con la llave | ✅ | `_fijar_etapa_inicial` (`main.py:100-107`): etapa 1 hasta `CURRICULO_HASTA_GENERACION` para toda la población, sin azar ni premio; después de `_ubicar_agentes`, al arrancar (`:379-380`) y al final de cada generación (`:550-551`), con evolución y sin ella (`:543-546`). `RED_KEY_REWARD` se suma solo al agarrar la llave (`advanced_agent.py:667-668`), y en la etapa 1 no se puede (`world.py:910`). La brújula de la etapa 1 apunta a la puerta (`advanced_agent.py:209`), y la puerta es pared mientras la etapa sea menor que 2 (`:584`). `test_curriculo.py:86`, `:101`, `:111`, `:118` y `:124`; `test_humo.py:154` (PUZZLE-13) |
| PUZZLE-QA-14 | Lo dado no es logro | ✅ | `mirar_hitos` cuenta solo a quien dio el paso (`registro.py:62-63`: `etapa_inicial < paso <= etapa`); la primera vez del boletín, solo generaciones con `etapa_inicial < paso` (`boletin.py:117-118`); el "llegó a" del mejor agente, sin lo dado (`:204-208`); el término cuenta `etapa − etapa_inicial` (`advanced_agent.py:789`). En esta sesión, con `--curriculo` el log con ventana no tiene ninguna línea de hito; con `--acercarse`, en la misma semilla, sale "¡Primera llave roja! Agente 4, generación 1". `test_curriculo.py:159`, `:175`, `:193`, `:216` y `:260` (PUZZLE-14) |
| PUZZLE-QA-15 | Pantallas | ✅ | El panel tiene el renglón "Ayudas" solo si hay alguna (`stats.py:53-57`); el boletín, "Modo autónomo + …" (`boletin.py:58-70` y `:163-164`). Capturas de esta sesión (semilla 7): en la generación 1 con los dos switches, "Ayudas: acercarse + currículo", "Llave roja: 60" y ningún aviso sobre el mundo; el boletín del currículo, "Modo autónomo + currículo", "60 de 60 · dada al nacer" y "llegó a: ningún paso (nació con la llave roja)" (PUZZLE-15) |
| PUZZLE-QA-16 | Experimentos B y C | ✅ | Registrados ([B](#experimento-puzzle-b), [C](#experimento-puzzle-c)) con la [respuesta al ítem 5](#puzzle-respuesta-item-5): 0 de 5 en los dos y secundario 1 de 5, como sus `resumen.md`; la respuesta aplica el 4 de 5 de la decisión 13. **Primera pasada PARCIAL:** la tabla de la respuesta decía 0 / 0 puertas abiertas en las generaciones 1 a 15 del cierre y del A, y son 1 / 1 (semilla 5, generación 1, la misma con evolución y sin ella; el texto del A ya lo contaba). Corregida en la sesión, con la cuenta del checker y la de la sesión, que coinciden; la respuesta no cambia (PUZZLE-16) |
| PUZZLE-QA-17 | `python -m pytest -q` | ✅ | 155 passed en 35,2 s. Control vuelto a correr en esta sesión: `test_acercarse.py` en un worktree de `c9b8983` (antes del bloque A), 10 de 10 fallan; `test_curriculo.py` en uno de `7390ed3` (antes del B), 12 de 12 fallan. Los de `test_humo.py` y `test_resumen.py`, en la bitácora del spec (PUZZLE-17) |
| PUZZLE-QA-18 | Docs | ✅ | README: el término con su peso (`README.md:262`), las ayudas (`:320-326`), los flags y la ruta (`:496-498`), el CSV (`:500-502`) y `experimento.py` (`:521-523`). `CLAUDE.md:98-105` (los dos switches, comunes a los dos modos, con 10 y 15) y `:157-160` (los flags de `main.py` y de `experimento.py`). Cada número, contra `config.py` y el código que lo lee (PUZZLE-18) |

**Observaciones que no cambian el veredicto:**
- **Las listas de términos del fitness del README** (`README.md:113` y `:223`) no nombran el de
  acercarse. Con el switch apagado, que es el valor por defecto, son ciertas; el término está en `:262`
  y en § Ayudas. El DoD no las pide.
- **El tope de los golpes de la decisión 6 no tiene un `min` ni un test:** sale de que el golpe que
  completa los necesarios cambia la etapa en la misma llamada. Tampoco hay test de la etapa 5 (sin paso
  actual: `_proximo_paso` da `None` y el avance, 0); la decisión 16 no lo pide.
- **El encabezado del boletín deduce el currículo** de la `etapa_inicial` de la generación 1
  (`boletin.py:164`), no del switch. Con el flujo de `main.py` es lo mismo, salvo con
  `CURRICULO_HASTA_GENERACION` = 0, donde nadie nace con la llave y el boletín no lo nombra.
- **Con el currículo, "Hasta dónde llegaron: nadie agarró la llave roja"** aunque los 60 la tengan: es
  cierto (nadie la agarró) y es la decisión 10; el embudo dice "dada al nacer".
- **Los CSV del experimento A no tienen `etapa_inicial`:** corrieron antes del bloque B.

---

<a id="medicion-puerta-madera"></a>

## Dónde se traba la puerta de madera — medición (2026-11-16)

**La pregunta** (ítem de [mejoras futuras](../product/mejoras_futuras.md), decidido por Fer el
2026-11-15, antes del ítem 6 del BACKLOG): con la llave roja dada a los 60 agentes durante 15
generaciones, la evolución abre la puerta de madera lo mismo que cerebros al azar (8 contra 9 en el
[experimento B](#experimento-puzzle-b)). ¿El cuello es el camino (no llegan a menos de 25 px del
centro), golpear (llegan y no golpean), los golpes que no cuentan (cooldown, distancia) o la selección
(los que la abren no pasan sus genes)?

**Método.** Sin cambios en `src/`, `main.py` ni `config.py`. El script
[`mediciones/medir_puerta.py`](../../mediciones/medir_puerta.py) corre `main.main()` con los flags del
experimento y envuelve, sin consumir azar (el embudo lo arma
[`mediciones/analizar_puerta.py`](../../mediciones/analizar_puerta.py)):
- `AdvancedAgent.act`: con la posición después de moverse (la que mira el golpe) y la llave (etapa 1),
  la distancia al centro de la puerta, (100, 140), la del primer tick (dónde nació), los ticks a menos
  de 25 px y los ticks con golpear > 0,5, en total y a menos de 25 px. Además, la distancia a un **punto
  de control**: la llave roja, que está en el mapa, a la que la brújula no apunta y que con la etapa 1
  no se agarra.
- `AdvancedAgent._try_hit_door`: cada golpe a menos de 25 px, si contó o qué lo frenó: el cooldown de
  120 ticks del agente (que al empezar la generación corre desde el tick 0) o el de 90 de la puerta.
- `main._fila_csv`: fitness, lugar en el ranking (el mismo orden estable que `evolve`) y si entra en
  los 36 del meeting pool; la geometría de la puerta en el mapa de la generación.
- `GeneticAlgorithm.evolve`, `SimpleNeuralNetwork.crossover` y `copy_from`: el aporte de cada agente a
  la generación siguiente (élite y copia, 1; cada padre de un cruce, 0,5).
- Un **seguidor de brújula perfecto**, sobre el mapa de cada generación: desde una grilla de arranques
  cada 25 px en la zona donde nacen los agentes, avanza 3 px por tick derecho al centro de la puerta,
  con las colisiones de `act()`. Dos variantes: como hoy (si el paso choca, no se mueve) y deslizando
  (si choca, prueba moverse solo en x y, si no, solo en y).

Autónomo con `--curriculo`, semillas 1 a 5, 15 generaciones: con evolución y sin ella (la configuración
del B) y con evolución y `--acercarse` (la del C, cuya línea base es la del B salvo el fitness). 4.500
agentes × generación en cada una, todos con la llave.

**Control.** Los 15 CSV son byte a byte las 15 primeras filas de sus corridas en
`results/experimento_20261115-205826` (B) y `results/experimento_20261115-210549` (C), fuera de git: el
envoltorio no cambió la corrida. Cada golpe a menos de 25 px se predijo (cuenta o no, y por qué) antes
de llamar al original: 0 diferencias. El ranking coincide con el orden de `evolve`, y el aporte suma 60
por generación (57 en la 6 y la 12, por los 3 inmigrantes).

**Geometría.** La puerta (20 × 20) y los muros de la pared sur frenan el centro de un agente (radio 6)
a 16 px del centro de la puerta, de frente y por abajo. Lo libre a menos de 25 px es una franja de unos
9 px de alto debajo de la puerta: 235 px² (mediana de 225 mapas; 29 px² en uno, con un obstáculo
enfrente). En línea recta se entra a la franja solo desde un cono de ~50° por debajo; desde el costado,
la pared frena a más de 25 px.

**El embudo** (agentes × generación con la llave):

| | Agentes × gen. | < 100 px | < 50 px | < 25 px | Golpearon a < 25 px | ≥ 1 golpe que contó | Abrieron |
|---|---|---|---|---|---|---|---|
| B con evolución, gens 1-15 | 4.500 | 237 (5,3%) | 60 (1,3%) | 25 (0,6%) | 12 | 10 | 8 |
| B sin evolución, gens 1-15 | 4.500 | 187 (4,2%) | 54 (1,2%) | 19 (0,4%) | 11 | 11 | 9 |
| C con evolución, gens 1-15 | 4.500 | 248 (5,5%) | 67 (1,5%) | 27 (0,6%) | 14 | 12 | 6 |
| B con evolución, gens 1-5 | 1.500 | 69 (4,6%) | 14 (0,9%) | 4 (0,3%) | 4 | 4 | 2 |
| B con evolución, gens 11-15 | 1.500 | 83 (5,5%) | 23 (1,5%) | 10 (0,7%) | 4 | 4 | 4 |
| B sin evolución, gens 1-5 | 1.500 | 58 (3,9%) | 12 (0,8%) | 2 (0,1%) | 1 | 1 | 1 |
| B sin evolución, gens 11-15 | 1.500 | 72 (4,8%) | 22 (1,5%) | 10 (0,7%) | 6 | 6 | 4 |
| C con evolución, gens 1-5 | 1.500 | 68 (4,5%) | 13 (0,9%) | 5 (0,3%) | 1 | 1 | 1 |
| C con evolución, gens 11-15 | 1.500 | 96 (6,4%) | 27 (1,8%) | 13 (0,9%) | 7 | 6 | 4 |

Las 8 y 9 aperturas son las del experimento B; las 6, las del C.

| | B con evolución | B sin evolución | C con evolución |
|---|---|---|---|
| Distancia mínima a la puerta, mediana (al nacer, ~540 px) | 496 px | 517 px | 498 px |
| Llegan a < 25 px: de los que nacen a menos de 100 px / a más de 400 px | 12 de 131 / 2 de 3.103 | 13 de 123 / 0 de 3.140 | 17 de 131 / 1 de 3.103 |
| Camino hecho, gens 11-15, (al nacer − mínima) / al nacer: hacia la puerta / hacia el punto de control | 0,103 / 0,127 | 0,057 / 0,071 | 0,107 / 0,121 |
| Ticks golpeando con la llave: gen 1 → gens 11-15 | 29,6% → 21,6% | 29,6% → 27,0% | 29,6% → 29,9% |
| Los que abrieron: en el pool / aporte a la gen. siguiente, promedio (el de todos, 0,99) | 8 de 8 / 2,38 | 9 de 9 / — | 6 de 6 / 1,70 (5; el sexto abrió en la 15) |

**Seguidor de brújula perfecto** (225 mapas: 15 corridas × 15 generaciones; la generación 1 se repite
entre las corridas de una semilla):

| | Llega a < 25 px | Lo más cerca (mediana de cada mapa; la del medio entre mapas) |
|---|---|---|
| Como hoy: si el paso choca, no se mueve | 11,8% de los arranques (de 0% a 32% según el mapa) | 354 px |
| Deslizando contra lo que choca | 50,1% (de 16% a 75%) | 19 px |

**Lectura.**

1. **El cuello es el camino, por dos órdenes de magnitud.** El 99,4% de los agentes con la llave nunca
   llega a menos de 25 px; lo más cerca que llegan tiene una mediana de ~500 px, con evolución y sin
   ella. Después del camino, los factores son chicos: de los que llegan, golpea ahí la mitad; de los que
   golpean ahí, casi todos cuentan un golpe; de los que cuentan uno, 7 de cada 10 dan el segundo.
2. **Los que llegan, nacieron cerca.** De los que nacen a menos de 100 px de la puerta, llega 1 de cada
   10; de los que nacen a más de 400 px (dos de cada tres), 3 en 9.346 entre las tres condiciones.
   Ninguno de los 23 que abrieron nació a más de 400 px.
3. **No usan la brújula.** Con evolución, el camino hecho hacia la puerta casi se duplica (0,057 →
   0,103 en las generaciones 11 a 15, más que la línea base en 5 de 5 semillas), pero hacia el punto de
   control sube lo mismo (0,071 → 0,127; ×1,8 en los dos): caminan más, no van hacia la puerta. Con
   evolución, en las 5 semillas del B, el camino hacia el control es mayor que hacia la puerta. Con la
   recompensa por acercarse (C), igual: 0,107 hacia la puerta y 0,121 hacia el control, los dos 0,050
   arriba de la línea base.
4. **Aunque la usaran, el mapa no la deja pagar.** Un seguidor de brújula perfecto llega en el 12% de
   los arranques: la línea recta choca con un muro, un árbol, una casita o el estanque, y como chocar no
   desliza, queda trabado ahí (mediana: 354 px de la puerta). Deslizando, llega en el 50%, y entra a la
   franja de la puerta por la pared sur. Con la mecánica de hoy, seguir la brújula casi nunca paga, así
   que la selección no tiene con qué empujar a aprenderla.
5. **Golpear pierde la mitad, y la evolución golpea menos.** De los que llegan a < 25 px, golpean ahí
   entre el 48% y el 58%. Con evolución, en el B, golpear baja de 30% a 22% de los ticks (cuesta
   energía; dentro de cada generación, golpear más y el fitness tienen una correlación de −0,14, la
   mediana); en el C no baja (~29%): los golpes que cuentan suman al término de acercarse.
6. **Los golpes que no cuentan casi no pierden a nadie.** Los frenan el cooldown de 120 ticks del
   agente al empezar la generación (los que nacen cerca llegan antes del tick 120 y esperan empujando
   la puerta: varios la abrieron con golpes en los ticks 120 y 210) y los 90 de la puerta entre golpes.
   El corte de árboles no frenó ninguno. Lo que se pierde es el segundo golpe: de 33 que contaron uno,
   10 se fueron antes del segundo (6 en el C), y solo 2 volvieron a estar a < 25 px cuando ya podían
   darlo, sin golpear.
7. **La selección sí elige a los que abren, pero no hay qué heredar.** Los 23 quedaron en el pool
   (lugar mediano entre 5 y 7) y, con evolución, dejaron 2,4 (B) y 1,7 (C) hijos-equivalentes, contra
   0,99 del promedio. Abrieron porque nacieron cerca, y la generación siguiente nace en otro lugar.

**Qué sugiere** (para decidir el paso siguiente; esta medición no tocó código):
- **El cambio que más abre el camino es que chocar deslice:** si el paso choca, moverse por el eje
  libre. Lleva al seguidor perfecto del 12% al 50% y lo mete en la franja de la puerta. Cambia la
  simulación en los dos modos (también comer y caminar); con un switch, se mide como las ayudas: el B
  con y sin deslizar, la puerta y el camino hacia la puerta contra el punto de control.
- **Si con deslizamiento siguen sin usar la brújula,** el problema pasa a ser aprenderla: la presión
  de selección (ya en mejoras futuras) o un sensor de contra qué chocan.
- **Golpear (pierde ~la mitad de los que llegan) y el segundo golpe (~un tercio) son factores chicos:**
  bajar `DOOR_HITS_TO_OPEN` a 1 o achicar el cooldown ayudaría a los que llegan, pero hoy llegan 25 de
  4.500.

---

<a id="deslizar-al-chocar"></a>

## Deslizar contra lo que choca — switch, medición y experimento B (2026-11-16)

**Qué cambió** (sugerido por la [medición de la puerta](#medicion-puerta-madera); pedido por Fer, con
vía libre para cambiar el proyecto): un switch `DESLIZAR` en `config.py`, apagado por defecto, con
`--deslizar` en `main.py`, `experimento.py` y `mediciones/medir_puerta.py`. Prendido, si el paso
choca, el agente prueba moverse solo en x y, si no, solo en y (`act()` en
`src/agents/advanced_agent.py`). Las tres pruebas usan la misma función, `_choca`, que es la
verificación de siempre sacada de `act()`: obstáculos, las puertas que el agente no abrió, el perímetro
y el estanque. Vale para los dos modos. No es una columna del CSV (cambiaría el CSV apagado): va en el
nombre del archivo (`_deslizar`), en el renglón de ayudas del panel, en el encabezado del boletín y en
"Ayudas prendidas" del resumen del experimento.

**DIAG-30.** El estanque y el perímetro siguen con la caja que va de (x, y) hacia abajo y a la derecha:
deslizar usa la misma, a propósito (centrarla cambiaría la corrida apagada, y mezclaría dos cambios en
una medición). Por la derecha o por abajo, el agente desliza a lo largo del estanque con el centro en
el borde, 5 px del cuerpo encima del agua, lo mismo que deja hoy un paso derecho; nunca más adentro
(test: desde una grilla de 792 arranques alrededor de una pared y del estanque, en 8 rumbos, ninguno
termina donde el paso entero chocaría). El estanque no es zona de agua (esas no tienen colisión): lo de
DIAG-30 es solo visual.

**Controles.**
- **Apagado, el CSV es el de antes, byte a byte.** Seis corridas de 10 generaciones (guiado semilla 1
  con evolución y 2 sin; autónomo semilla 1 con y 2 sin; autónomo semilla 3 con `--acercarse
  --curriculo`; guiado semilla 3 con `--curriculo`), en `f5f2375` antes de tocar el código y después:
  6 de 6 iguales. Con los mismos tiempos (±3 s): sacar `_choca` no hizo más lenta la corrida.
- **La medición sin deslizar, con el código nuevo,** da byte a byte las 15 primeras filas de las 10
  corridas del [experimento B](#experimento-puzzle-b) (`results/experimento_20261115-205826`), y
  deslizando, las del experimento B con `--deslizar` (`results/experimento_20261116-101649`): el
  envoltorio no cambió ninguna corrida. Las 20 terminaron con `MEDICION inconsistencias=0`.
- **Tests** (`tests/test_deslizar.py`, 12): corridos contra el código de antes del switch, 10 fallan
  y 2 pasan (en una esquina no se mueve; sin choque, el paso es el mismo: valen también sin el
  switch). Con el código nuevo, 12 de 12.

**La medición** (`mediciones/medir_puerta.py` con y sin `deslizar`, el B: autónomo con `--curriculo`,
semillas 1 a 5, 15 generaciones, con evolución y sin ella; el embudo, de
`mediciones/analizar_puerta.py`, sobre los agentes × generación con la llave):

| | Agentes × gen. | < 100 px | < 50 px | < 25 px | Golpearon a < 25 px | ≥ 1 golpe que contó | Abrieron |
|---|---|---|---|---|---|---|---|
| B con evolución, gens 1-15 | 4.500 | 237 (5,3%) | 60 (1,3%) | 25 (0,6%) | 12 | 10 | 8 |
| B sin evolución, gens 1-15 | 4.500 | 187 (4,2%) | 54 (1,2%) | 19 (0,4%) | 11 | 11 | 9 |
| B deslizando, con evolución, gens 1-15 | 4.500 | 408 (9,1%) | 137 (3,0%) | 76 (1,7%) | 32 | 29 | 17 |
| B deslizando, sin evolución, gens 1-15 | 4.500 | 253 (5,6%) | 79 (1,8%) | 45 (1,0%) | 22 | 19 | 10 |
| B con evolución, gens 11-15 | 1.500 | 83 (5,5%) | 23 (1,5%) | 10 (0,7%) | 4 | 4 | 4 |
| B sin evolución, gens 11-15 | 1.500 | 72 (4,8%) | 22 (1,5%) | 10 (0,7%) | 6 | 6 | 4 |
| B deslizando, con evolución, gens 11-15 | 1.500 | 170 (11,3%) | 55 (3,7%) | 28 (1,9%) | 10 | 10 | 7 |
| B deslizando, sin evolución, gens 11-15 | 1.500 | 96 (6,4%) | 32 (2,1%) | 18 (1,2%) | 11 | 10 | 5 |

Las dos primeras filas de cada bloque son las de la [medición de la puerta](#medicion-puerta-madera),
vueltas a contar con el mismo script (dan lo mismo).

| | B con evolución | B sin evolución | B deslizando, con evolución | B deslizando, sin evolución |
|---|---|---|---|---|
| Abrieron, gens 1-15, por semilla | 1/3/2/1/1 | 3/3/1/0/2 | 3/1/4/4/5 | 2/3/3/1/1 |
| Con evolución abrieron más que su línea base | 2 de 5 semillas | | 4 de 5 | |
| Ídem, solo gens 11-15 (abrieron) | 3 de 5 (4 contra 4) | | 1 de 5 (7 contra 5) | |
| Llegan a < 25 px de los que nacen a más de 400 px | 2 de 3.103 | 0 de 3.140 | 27 de 3.105 (abrieron 6) | 5 de 3.140 (1) |
| Camino hecho, gen 1 (los mismos cerebros), hacia la puerta / el control | 0,031 / 0,059 | 0,031 / 0,059 | 0,058 / 0,099 | 0,058 / 0,099 |
| Camino hecho, gens 11-15, hacia la puerta / el control | 0,103 / 0,127 | 0,057 / 0,071 | 0,186 / 0,197 | 0,085 / 0,097 |
| Los que abrieron (gens 1-14): lugar mediano / aporte a la gen. siguiente | 5 / 2,38 | — | 1 / 2,50 | — |
| Ticks golpeando con la llave: gen 1 → gen 15 | 29,6% → 22,4% | 29,6% → 24,5% | 31,1% → 23,4% | 31,1% → 25,4% |

El seguidor de brújula perfecto, sobre los 300 mapas de las 20 corridas, llega a < 25 px en el 11,5%
de los arranques sin deslizar y en el 49,7% deslizando (como en la medición de la puerta).

**El experimento B completo con `--deslizar`** (10 corridas, 10 a la vez, en 12 núcleos: 621 s la más
lenta; el B sin deslizar, 429 s: deslizando, los agentes caminan más ticks y la corrida tarda ~1,5
veces). Carpeta `results/experimento_20261116-101649`.

`python experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --curriculo --deslizar`

**Ayudas prendidas:** currículo y deslizar al chocar.

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| autonomo | Con evolución | 5 | 21.89 ± 0.68 | 39.67 ± 1.47 | 17.78 ± 1.97 | 0.44 ± 0.04 | 1.06 ± 0.07 | 0.62 ± 0.05 | 982 ± 45 | 5.04 ± 3.18 | 2.8 ± 0.4 | 0 de 5 |
| autonomo | Sin evolución | 5 | 19.44 ± 0.87 | 19.47 ± 0.78 | 0.02 ± 0.92 | 0.34 ± 0.03 | 0.33 ± 0.06 | -0.02 ± 0.04 | 893 ± 8 | 1.24 ± 0.73 | 2.6 ± 0.5 | 0 de 5 |

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5, más con la puerta de madera abierta en 1 de 5 y más llave roja por 1.000 px en 3 de 5.
- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 0 de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 3 de 5. Cada uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no.

Por corrida, en el `resumen.md` de la carpeta. **Contra el B sin deslizar**, la misma cuenta sobre los
CSV de las dos carpetas (suma de las 5 semillas, y por semilla):

| | Puerta abierta, gens 1-15 (llave dada) | Puerta abierta, gens 16-30 | Llave roja agarrada, gens 16-30 | Manzanas por agente, últimas 5 | Fitness, diferencia | Etapa máxima |
|---|---|---|---|---|---|---|
| B con evolución | 8 (1/3/2/1/1) | 1 (0/0/0/0/1) | 167 (20/32/46/30/39) | 0,77 | 13,15 | 2,2 |
| B sin evolución | 9 (3/3/1/0/2) | 0 | 53 (6/8/10/12/17) | 0,20 | 0,11 | 2,0 |
| B deslizando, con evolución | 17 (3/1/4/4/5) | 2 (0/0/1/0/1) | 270 (47/53/48/44/78) | 1,06 | 17,78 | 2,8 |
| B deslizando, sin evolución | 10 (2/3/3/1/1) | 0 | 82 (11/10/22/14/25) | 0,33 | 0,02 | 2,6 |

Deslizando contra sin deslizar, por semilla: más llave roja en las gens 16-30 en 5 de 5, con evolución
y sin ella; más manzanas por agente en las últimas 5 en 5 de 5, con y sin; más aperturas de la puerta
con la llave dada en 4 de 5 con evolución y en 2 de 5 sin.

**Lectura.**

1. **Deslizar abre el camino, para todos.** Con la llave dada, llegan a < 25 px de la puerta 3 veces
   más con evolución (76 contra 25) y 2,4 veces más sin ella (45 contra 19); desde más de 400 px, 27
   contra 2. Con los mismos cerebros (gen 1), el camino hecho hacia la puerta casi se duplica: es la
   mecánica, sin aprender nada. También come más (0,33 contra 0,20 manzanas por agente sin evolución)
   y agarra más la llave roja (5 de 5 semillas, con evolución y sin ella).
2. **Con deslizamiento, la evolución abre la puerta más que el azar, pero no aprende a abrirla.** En las
   15 generaciones del currículo, 17 contra 10 (más en 4 de 5 semillas), cuando sin deslizar era 8
   contra 9. Pero no crece con las generaciones: en las 11 a 15, 7 contra 5 (más en 1 de 5); y en las
   16 a 30, con el puzzle entero, 2 contra 0. El criterio del ítem 5 da 0 de 5, como sin deslizar.
3. **Siguen sin usar la brújula.** Con deslizamiento, la evolución sube el camino hacia la puerta y
   hacia el punto de control lo mismo (+0,101 y +0,100 sobre su línea base en las gens 11 a 15; en 2 de
   5 semillas el de la puerta supera al del control, por 0,003 o menos). Lo que aprende es a caminar
   más, y deslizar hace que caminar pague (llega más lejos sin trabarse). Un seguidor perfecto llega en
   el 50% de los arranques; los agentes, en el 1,7%.
4. **Golpear y el segundo golpe, igual que antes:** de los que llegan, golpean ahí entre el 36% y el
   61%; de los 29 que contaron un golpe con evolución, 12 no dieron el segundo. La evolución sigue
   golpeando menos (31% → 23% de los ticks).
5. **La selección elige todavía más a los que abren:** el lugar mediano de los que abrieron es el 1
   (antes, el 5), y dejan 2,5 hijos-equivalentes contra 0,99 del promedio. Igual que antes, la
   generación siguiente nace en otro lugar de otro mapa.

**Qué sugiere** (para decidir; deslizar queda apagado por defecto):
- **Deslizar es una mejora de la mecánica, no del aprendizaje del puzzle.** Mejora comer, la llave y
  llegar a la puerta en las dos condiciones, y la evolución sigue sumando encima (5 de 5 en fitness,
  manzanas y llave). Si Fer quiere, puede quedar prendido por defecto; cambiaría todas las corridas de
  referencia (en [mejoras futuras](../product/mejoras_futuras.md)).
- **El cuello pasa a ser aprender la brújula,** como anticipaba la medición de la puerta: la presión de
  selección o un sensor de contra qué chocan (los dos ya en mejoras futuras).

---

<a id="brujula-c-deslizando"></a>

## La brújula, deslizando y con la recompensa por acercarse — experimento C y medición (2026-11-16)

**La pregunta** (ítem "Que la brújula se aprenda" de [mejoras futuras](../product/mejoras_futuras.md)):
ahora que chocar desliza, ¿la recompensa por acercarse hace que el autónomo aprenda a seguir la brújula
y a pasar la puerta de madera? Si no, medir por qué antes de cambiar nada. Sin cambios en `src/`,
`main.py` ni `config.py`.

**Criterio, fijado antes de medir:**
- **Aprende la puerta:** el criterio del ítem 5 (al menos 1 agente por generación con la puerta de
  madera abierta en las últimas 5 y más que la línea base, en 4 de 5 semillas). Lo calcula
  `experimento.py`.
- **Usa la brújula:** en las generaciones 11 a 15, (camino hacia la puerta − camino hacia el punto de
  control) con evolución, mayor que en su línea base, en 4 de 5 semillas. El camino es el de la
  [medición de la puerta](#medicion-puerta-madera): (al nacer − mínima) / al nacer; el control, la
  llave roja, a la que la brújula no apunta con la etapa 1.

**Cómo se corrió.**
1. **El experimento C deslizando:** `python experimento.py --semillas 1 2 3 4 5 --generaciones 30
   --modos autonomo --acercarse --curriculo --deslizar`, 10 corridas, 10 a la vez: 665 s la más lenta.
   Carpeta `results/experimento_20261116-105457`.
2. **La medición del C deslizando:** `mediciones/medir_puerta.py` con `acercarse deslizar`, semillas 1
   a 5, con evolución y sin ella, 15 generaciones, 10 a la vez; el embudo con
   `mediciones/analizar_puerta.py` (con las condiciones (1, 1, 1) y (1, 1, 0) sumadas a `CONDS`) y lo
   nuevo con [`mediciones/analizar_brujula.py`](../../mediciones/analizar_brujula.py).
3. **Lo mismo con el B deslizando** (`deslizar` solo, sin la recompensa), para tener el control del
   criterio de la brújula y los términos del fitness, que se sumaron a la medición después del paso 2.

Los `agentes_*.csv` de las dos mediciones quedaron en el scratchpad de la sesión, que no sobrevive: se
regeneran con `medir_puerta.py` desde el commit de esta sesión (las corridas son las mismas: lo
comprueba el control byte a byte contra las carpetas de `results/`). Las del C deslizando no traen los
términos del fitness ni el giro, que se sumaron después.

**Qué se sumó a la medición** (`medir_puerta.py`, sin consumir azar):
- **La sensibilidad de la red a la brújula:** con la percepción que vio el agente en cada tick con la
  llave, cuánto cambia el giro que haría `act()` si el sensor 9 marca el objetivo 90° a un lado o al
  otro (+0,5 contra −0,5), en rad/tick. Positivo: gira hacia donde marca. Lo mismo con el sensor 3 (la
  comida) como control positivo. Una red armada a mano que sigue la brújula da +0,143 (el máximo es
  ~0,144), la que huye −0,143, y las dos dan 0 a la comida.
- **El giro:** % de ticks girando, giro medio |rad/tick| y % de ticks avanzando.
- **Los términos del fitness** por agente al final de la generación (supervivencia, comida, exploración,
  anti-círculo, puzzle, acercarse y agua), con los pesos de `config.py`.

**Controles.**
- **La tabla de abajo, rehecha** (el script de la sesión anterior ya no existía): da las 4 filas
  publicadas en [deslizar](#deslizar-al-chocar) (B y B deslizando) y, en el C, las aperturas y la
  diferencia de fitness de su `resumen.md`.
- **La línea base del C deslizando es la del B deslizando** salvo `fitness_*` y `acercarse`, en las 5
  semillas y las 30 generaciones (`fitness_prom` más alto con la recompensa en las 150).
- **La medición no cambió ninguna corrida:** los 20 `corrida_*.csv` (10 del C deslizando y 10 del B
  deslizando) son byte a byte el encabezado y las 15 primeras filas de sus corridas en
  `results/experimento_20261116-105457` y `results/experimento_20261116-101649`. Las 20 terminaron con
  `MEDICION inconsistencias=0`, que cuenta, además de los golpes y el ranking: que el forward en lote
  de la sensibilidad dé las salidas de `decide()`, que el giro calculado sea el que hizo `act()` y que
  los términos sumen el fitness de cada agente.
- **El embudo del B deslizando da el publicado** (76 y 17 aperturas en las gens 1-15 con evolución; 45
  y 10 sin ella; 28 y 7, 18 y 5 en las 11-15) y el camino puerta / control también (0,186 / 0,197 y
  0,085 / 0,097).

### El experimento C deslizando

**Ayudas prendidas:** recompensa por acercarse y currículo y deslizar al chocar.

| Modo | Evolución | Corridas | Fitness prom., gens 1-5 | Fitness prom., últimas 5 | Diferencia | Manzanas por agente, gens 1-5 | Manzanas por agente, últimas 5 | Diferencia | Edad prom. (ticks), últimas 5 | Agentes con llave roja, últimas 5 | Etapa máxima (0-5) | Cofre abierto |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| autonomo | Con evolución | 5 | 22.18 ± 0.88 | 41.76 ± 1.83 | 19.58 ± 1.93 | 0.41 ± 0.06 | 0.93 ± 0.12 | 0.51 ± 0.09 | 953 ± 50 | 4.44 ± 2.33 | 2.2 ± 0.4 | 0 de 5 |
| autonomo | Sin evolución | 5 | 19.81 ± 0.90 | 20.47 ± 0.82 | 0.66 ± 0.92 | 0.34 ± 0.03 | 0.33 ± 0.06 | -0.02 ± 0.04 | 893 ± 8 | 1.24 ± 0.73 | 2.6 ± 0.5 | 0 de 5 |

- **Autónomo, con evolución contra sin:** la evolución subió más en fitness en 5 de 5 semillas, en manzanas por agente en 5 de 5, y tuvo más agentes con llave roja en las últimas 5 en 5 de 5, más con la puerta de madera abierta en 2 de 5 y más llave roja por 1.000 px en 3 de 5.
- **Criterio del ítem 5 (puerta de madera):** con evolución, al menos 1 agente por generación con la puerta de madera abierta en las últimas 5 y más que la línea base, en 0 de 5 semillas; secundario, más llave roja por 1.000 px que la línea base, en 3 de 5. Cada uno pide 4 de 5. **El autónomo aprende a pasar la puerta de madera: no.** Secundario: no.

Por corrida, en el `resumen.md` de la carpeta. **Contra el B deslizando y el C sin deslizar**, la misma
cuenta sobre los CSV de las cuatro carpetas (suma de las 5 semillas, y por semilla):

| | Puerta abierta, gens 1-15 (llave dada) | Puerta abierta, gens 16-30 | Llave roja agarrada, gens 16-30 | Manzanas por agente, últimas 5 | Fitness, diferencia | Etapa máxima |
|---|---|---|---|---|---|---|
| B con evolución | 8 (1/3/2/1/1) | 1 (0/0/0/0/1) | 167 (20/32/46/30/39) | 0,77 | 13,15 | 2,2 |
| B sin evolución | 9 (3/3/1/0/2) | 0 | 53 (6/8/10/12/17) | 0,20 | 0,11 | 2,0 |
| B deslizando, con evolución | 17 (3/1/4/4/5) | 2 (0/0/1/0/1) | 270 (47/53/48/44/78) | 1,06 | 17,78 | 2,8 |
| B deslizando, sin evolución | 10 (2/3/3/1/1) | 0 | 82 (11/10/22/14/25) | 0,33 | 0,02 | 2,6 |
| C con evolución | 6 (1/0/2/1/2) | 0 | 188 (12/31/71/37/37) | 0,72 | 14,01 | 1,8 |
| C sin evolución | 9 (3/3/1/0/2) | 0 | 53 (6/8/10/12/17) | 0,20 | 0,60 | 2,0 |
| C deslizando, con evolución | 11 (4/3/2/1/1) | 3 (0/0/2/1/0) | 282 (33/83/47/47/72) | 0,93 | 19,58 | 2,2 |
| C deslizando, sin evolución | 10 (2/3/3/1/1) | 0 | 82 (11/10/22/14/25) | 0,33 | 0,66 | 2,6 |

| Criterio del ítem 5 / puerta abierta | B | B deslizando | C | C deslizando |
|---|---|---|---|---|
| Criterio del ítem 5 | 0 de 5 | 0 de 5 | 0 de 5 | 0 de 5 |
| Con evolución abrió más que su línea base, gens 1-15 / 16-30 | 2 / 1 de 5 | 4 / 2 de 5 | 2 / 0 de 5 | 1 / 2 de 5 |
| Puerta abierta en las gens 11-15, con / sin evolución | 4 / 4 | 7 / 5 | 4 / 4 | 3 / 5 |

### La medición: la puerta y la brújula

**El embudo** (agentes × generación con la llave; las filas del B deslizando son las de
[deslizar](#deslizar-al-chocar), repetidas por esta medición):

| | Agentes × gen. | < 100 px | < 50 px | < 25 px | Golpearon a < 25 px | ≥ 1 golpe que contó | Abrieron |
|---|---|---|---|---|---|---|---|
| B deslizando, con evolución, gens 1-15 | 4.500 | 408 (9,1%) | 137 (3,0%) | 76 (1,7%) | 32 | 29 | 17 |
| C deslizando, con evolución, gens 1-15 | 4.500 | 392 (8,7%) | 130 (2,9%) | 53 (1,2%) | 26 | 26 | 11 |
| C deslizando, sin evolución, gens 1-15 | 4.500 | 253 (5,6%) | 79 (1,8%) | 45 (1,0%) | 22 | 19 | 10 |
| B deslizando, con evolución, gens 11-15 | 1.500 | 170 (11,3%) | 55 (3,7%) | 28 (1,9%) | 10 | 10 | 7 |
| C deslizando, con evolución, gens 11-15 | 1.500 | 159 (10,6%) | 53 (3,5%) | 21 (1,4%) | 10 | 10 | 3 |
| C deslizando, sin evolución, gens 11-15 | 1.500 | 96 (6,4%) | 32 (2,1%) | 18 (1,2%) | 11 | 10 | 5 |

Los 11 que abrieron con evolución quedaron en el pool (lugar mediano 1) y dejaron 2,27
hijos-equivalentes, contra 0,99 del promedio. Desde más de 400 px llegan a < 25 px 15 de 3.102 con
evolución (abrieron 2) y 5 de 3.140 sin ella (1).

**El criterio de la brújula** (generaciones 11 a 15, camino hacia la puerta − hacia el control, con
evolución / sin ella; "sí" si con evolución es mayor):

| Semilla | C deslizando | | B deslizando (control, sin recompensa) | |
|---|---|---|---|---|
| 1 | −0,038 / −0,012 | no | −0,025 / −0,012 | no |
| 2 | +0,013 / +0,004 | sí | +0,002 / +0,004 | no |
| 3 | −0,014 / −0,034 | sí | −0,019 / −0,034 | sí |
| 4 | +0,012 / −0,004 | sí | +0,004 / −0,004 | sí |
| 5 | −0,014 / −0,017 | sí | −0,015 / −0,017 | sí |
| **Criterio** | **4 de 5** | | **3 de 5** | |
| Grupo: puerta / control, con evolución | 0,172 / 0,180 | | 0,186 / 0,197 | |
| Grupo: puerta / control, sin evolución | 0,085 / 0,097 | | 0,085 / 0,097 | |

**La sensibilidad del giro** (rad/tick; un seguidor de brújula, 0,143), promedio por agente:

| | Brújula, gens 1-5 | Brújula, gens 11-15 | Comida, gens 1-5 | Comida, gens 11-15 | Agentes con > 0,02 a la brújula, gens 11-15 |
|---|---|---|---|---|---|
| C deslizando, con evolución | +0,0018 | +0,0045 | +0,0013 | +0,0028 | 23% |
| B deslizando, con evolución | +0,0004 | +0,0013 | +0,0015 | +0,0026 | 18% |
| Sin evolución (la misma en los dos) | +0,0000 | +0,0014 | +0,0008 | +0,0010 | 20% |

Con evolución, más que su línea base en las gens 11-15: a la brújula, 3 de 5 semillas en los dos; a la
comida, 2 de 5 (C) y 4 de 5 (B). Por agente, la sensibilidad a la brújula va de −0,055 a +0,057 (p5 a
p95; |promedio| 0,021), igual con evolución y sin ella, en las gens 1-5 y en las 11-15.

**La selección** (dentro de cada generación, correlación de rangos con el fitness: mediana entre las
75 generaciones, y % con r > 0):

| | C deslizando, con evolución | C deslizando, sin evolución | B deslizando, con evolución |
|---|---|---|---|
| Sensibilidad a la brújula | +0,032 (63%) | −0,027 (43%) | −0,009 (49%) |
| Sensibilidad a la comida | +0,041 (64%) | −0,009 (45%) | +0,032 (61%) |
| Camino hacia la puerta | +0,566 (100%) | +0,621 (100%) | +0,517 (100%) |
| Camino hacia el control | +0,567 (100%) | +0,586 (100%) | — |
| Sensibilidad a la brújula → camino hacia la puerta / el control | +0,152 / +0,047 | +0,056 / +0,005 | — |

Por quintil de sensibilidad a la brújula dentro de la generación (con evolución, gens 1 a 14), el
aporte a la generación siguiente va de 0,90 a 1,11 en el C deslizando y de 0,89 a 1,07 en el B
deslizando, sin orden (el quintil más alto, 0,97 y 0,91), y el % en el pool de 52% a 67%.

**Qué mueve el fitness** (B deslizando, con evolución; por término: promedio, desvío dentro de la
generación y correlación de rangos con el fitness, medianas):

| Término | Gens 1-5 | Gens 11-15 | Sin evolución, gens 11-15 |
|---|---|---|---|
| Supervivencia | 8,7 · 1,2 · +0,39 | 9,1 · 1,2 · +0,29 | 8,9 · 1,4 · +0,36 |
| Comida | 2,7 · 6,0 · +0,64 | 4,6 · 7,0 · +0,73 | 2,0 · 5,2 · +0,59 |
| Exploración | 5,1 · 5,5 · +0,85 | 8,7 · 5,3 · +0,64 | 4,1 · 5,1 · +0,86 |
| Anti-círculo | 5,9 · 6,6 · +0,83 | 9,2 · 6,4 · +0,57 | 5,0 · 6,6 · +0,84 |
| Agua | −0,7 · 2,2 · −0,12 | −1,4 · 3,4 · +0,03 | −0,5 · 2,2 · −0,15 |

El puzzle (abrir la puerta, 12) vale 0 en casi todos. En el C deslizando, el término de acercarse
suma 0,69 en promedio con evolución (desvío dentro de la generación, 1,16; sin evolución, 0,40 y 0,94),
en un fitness con un desvío de ~15. Los que llegan a < 50 px sin abrir tienen +13,4 de fitness sobre el
resto de su generación en el C deslizando y +10,9 en el B (mediana entre generaciones; lugar mediano 14
y 16 de 60).

**El giro** (B deslizando): giran en el 48% de los ticks, 0,024 rad/tick en promedio, con evolución y
sin ella (0,023), en las gens 1-5 y en las 11-15. Lo que la evolución cambia es avanzar: de 30% a 58% de
los ticks (sin evolución, 24%). En las gens 11-15 con evolución, el que más gira tiene menos
anti-círculo (−0,33) y apenas más fitness (+0,09).

**Si el término de acercarse pesara más** (sobre los datos del C deslizando, con el mismo
comportamiento: solo cambia el fitness; el término se reconstruye con su fórmula, con el camino y los
golpes de la medición):

| Peso de acercarse | 10 (hoy) | 20 | 40 | 60 | 100 |
|---|---|---|---|---|---|
| Sensibilidad a la brújula ↔ fitness | +0,032 | +0,040 | +0,047 | +0,060 | +0,075 |
| Uso (puerta − control) ↔ fitness | −0,023 | −0,014 | +0,010 | +0,030 | +0,050 |

**Lectura.**

1. **La puerta: no.** Criterio del ítem 5, 0 de 5. Con la llave dada, la evolución la abre como el
   azar (11 contra 10; en las gens 11-15, 3 contra 5). Sumarle la recompensa al B deslizando no ayudó:
   abre 11 en lugar de 17, llegan menos a < 25 px (53 contra 76) y comen menos (0,93 contra 1,06
   manzanas por agente). Con 5 semillas, que reste no está probado; que no suma, sí.
2. **La brújula, por el criterio fijado: sí, en el mínimo, 4 de 5; pero no la aprenden.** Los márgenes
   van de 0,003 a 0,020, y en el grupo es +0,004, cuando el camino hecho subió +0,087. Sin la
   recompensa (B deslizando), la misma cuenta da 3 de 5: la recompensa cambió una semilla. Si la
   evolución no usara la brújula para nada, 4 o más de 5 sale por azar 6 veces de 32 (19%). La medida
   directa no lo acompaña: con evolución, la sensibilidad a la brújula es +0,0045 rad/tick en las gens
   11-15, el 3% de un seguidor, más que la línea base en 3 de 5 semillas; y los agentes que giran hacia
   ella con más de 0,02 siguen siendo 1 de cada 5, como en cerebros al azar.
3. **No aprenden a girar hacia nada, tampoco hacia la comida.** La sensibilidad a la comida queda en
   +0,003 con evolución, como la de la brújula. Lo que la evolución aprende es a avanzar más (de 30% a
   58% de los ticks) y a caminar más y más derecho: comen más porque recorren más, no porque giren hacia
   las manzanas. "Aprende a comer", en los experimentos, quiere decir que come más.
4. **Hay variación para seleccionar, y sirve un poco, pero la selección no la ve.** En cada generación
   hay agentes que giran hacia la brújula y agentes que giran al revés (±0,055), y los que giran hacia
   ella se acercan más a la puerta (+0,15 con evolución; hacia el control, +0,05). Pero acercarse a la
   puerta no paga más que acercarse a cualquier lado: el camino hacia la puerta y hacia el control se
   correlacionan igual con el fitness (+0,57). La sensibilidad a la brújula y el fitness, +0,03 (C) y
   −0,01 (B); por quintil, el mismo aporte y el mismo pool.
5. **Por qué no paga: el fitness premia caminar y comer, y la brújula pesa 0,7.** El desvío del
   fitness dentro de la generación (~15) lo hacen la comida (7), el anti-círculo (6) y la exploración
   (5), y los dos últimos pagan caminar hacia cualquier lado. El término de acercarse da como mucho 5
   por recorrer todo el camino a la puerta y en promedio 0,7. Aun con peso 100 en lugar de 10, con el
   comportamiento de hoy, la sensibilidad a la brújula se correlacionaría +0,075 con el fitness: la
   brújula mueve poco dónde termina cada agente, que depende sobre todo de dónde nace y cuánto camina.
6. **Girar ya tiene un costo:** giran casi la mitad de los ticks, con un sesgo propio (0,024 rad/tick)
   del tamaño de lo que la brújula cambia el giro (±0,02). Girar más baja el anti-círculo, que premia
   la rectitud: el término juega en contra de doblar hacia cualquier objetivo.

**Qué sugiere** (para decidir; esta sesión no tocó código de la simulación):
- **Más presión selectiva, sola, no:** el gradiente de la brújula sobre el fitness es ~0; más presión
  empujaría más fuerte lo que hoy se selecciona, caminar y comer.
- **Un sensor de obstáculos, tampoco por ahora:** el cuello no es esquivar (deslizando, un seguidor
  llega en el 50%), es que nadie gira hacia la brújula.
- **Dos causas posibles, que estos datos no separan:** que el fitness no lo pida (lo de arriba) o que el
  aprendiz no lo encuentre (en un cerebro al azar la brújula es 1 de 11 entradas con la misma escala
  de pesos; su efecto en el giro es del tamaño del sesgo; la mutación mueve 0,1 por peso; son 15 a 30
  generaciones). El paso siguiente que propongo es un **laboratorio de la brújula** que las separe: el C
  deslizando con solo acercarse pagando (comida, exploración, anti-círculo y supervivencia en 0), desde
  un script de `mediciones/` que fija esos pesos antes de llamar a `main.main()`, sin tocar `src/`. Si
  ahí la sensibilidad sube clara sobre la línea base, el aprendiz puede y lo que falta es rebalancear el
  fitness (medido); si ni así sube, lo que falta está en el aprendiz (la mutación, la población, las
  generaciones o cómo entra la brújula a la red). Con un criterio con tamaño mínimo, no solo K de N
  ([LEC-018](../operations/LECCIONES_APRENDIDAS.md)).

---

<a id="laboratorio-brujula"></a>

## Laboratorio de la brújula: si solo paga acercarse, ¿aprenden a girar hacia ella? (2026-11-16)

**La pregunta** (sugerida por la [medición de la brújula](#brujula-c-deslizando)): si seguir la brújula
es lo único que paga, ¿la evolución aprende a girar hacia ella? Separa dos causas posibles: que el
fitness no lo pida (hoy pagan la comida, el anti-círculo y la exploración, y acercarse pesa 0,7) o
que el aprendiz (la red y el genético) no lo encuentre. Sin cambios en `src/`, `main.py` ni
`config.py`.

**Diseño.** [`mediciones/medir_puerta.py`](../../mediciones/medir_puerta.py) con el argumento
`laboratorio`: antes de `main.main()` pone en 0 `FITNESS_FOOD`, `FITNESS_EXPLORATION`,
`FITNESS_ANTI_CIRCLE`, `FITNESS_SURVIVAL`, `TREE_CUT_REWARD`, `HUT_CUT_REWARD` y `WATER_PENALTY_MAX`, y
sube `CURRICULO_HASTA_GENERACION` a 30, así la brújula apunta a la puerta las 30 generaciones. Pagan
solo acercarse y el puzzle. Comer sigue dando energía: deja de pagar, no de servir.

**Criterio, fijado antes de medir** ([LEC-018](../operations/LECCIONES_APRENDIDAS.md): tamaño mínimo y
K de N):
- **Aprende a girar hacia la brújula:** en las últimas 5 generaciones, la sensibilidad promedio a la
  brújula con evolución es ≥ 0,02 rad/tick (1/7 de un seguidor) y mayor que su línea base, en 4 de 5
  semillas.
- **Secundario:** (camino a la puerta − camino al control) con evolución supera al de la línea base por
  al menos 0,05, en 4 de 5 semillas.
- **Lectura acordada:** si se cumple, el aprendiz puede y falta rebalancear el fitness; si no, lo que
  falta está en el aprendiz, y se mide antes de proponer (¿la sensibilidad sube algo?, ¿la selección
  elige a los que más giran hacia la brújula?, ¿los hijos la heredan?).

**Salvedad, declarada antes de medir:** la puerta no se mueve en toda la corrida (`world.reset_food`
regenera los obstáculos y guarda las fortalezas), la llave roja (el control) se sortea en cada
generación, y la red ve x, y y el rumbo absoluto (sensores 5 a 7). Una ruta aprendida de memoria
subiría el secundario sin usar la brújula. El principal no tiene ese problema: mide solo el sensor 9.

**Cómo se corrió.**
1. **El laboratorio:** `medir_puerta.py` con `acercarse deslizar laboratorio`, semillas 1 a 5, con
   evolución y sin ella, 30 generaciones, 10 a la vez: 15 min.
2. **El control C30, agregado después de ver el laboratorio** (desvío del diseño, abajo): lo mismo con
   `acercarse deslizar curriculo30`, el C deslizando con su fitness de siempre y el currículo hasta la
   30. 15 min.
3. El análisis, con [`mediciones/analizar_brujula.py`](../../mediciones/analizar_brujula.py) sobre cada
   carpeta: ahora toma las generaciones de la carpeta y mide en las 1-5, las 11-15 y las últimas 5;
   imprime el criterio del laboratorio, cuántos agentes cobran algo y la herencia.

**Qué se sumó a la medición** (sin consumir azar): el origen de cada agente (élite, copia, cruce o
inmigrante) y el id de sus padres, para medir si los hijos heredan la sensibilidad; el argumento
`curriculo30`; y la columna `curriculo_hasta`.

**Desvío del diseño: el control C30.** En las generaciones 1-15 el laboratorio difiere del C deslizando
solo en el fitness, y ahí la sensibilidad no subió (0,0033 contra 0,0045). Subió en las 16-30, donde
difiere en dos cosas: el fitness y el currículo extendido. Para separarlas, el C30 cambia solo el
currículo. Su criterio, fijado antes de correrlo: la subida es por el fitness si en las gens 26-30 la
sensibilidad con evolución del laboratorio supera a la del C30 en 4 de 5 semillas y el promedio del C30
queda por debajo de la mitad del laboratorio; si llega a la mitad o más, las generaciones de más explican
una parte o todo.

**Controles.**
- **Las 20 corridas terminaron con `MEDICION inconsistencias=0`** (las 20 líneas contadas, LEC-017).
  En el laboratorio eso incluye que los términos `f_*` sumen el fitness con los pesos del laboratorio y
  que supervivencia, comida, exploración, anti-círculo, agua y cortes den 0 en cada agente.
- **El laboratorio sin evolución, gens 1-15, es el C deslizando sin evolución**
  (`results/experimento_20261116-105457`) salvo `fitness_*`: 0 celdas distintas en las 5 semillas. La
  gen 1 con evolución, también (los mismos cerebros al azar en el mismo mapa).
- **El C30, gens 1-15, es byte a byte el C deslizando,** con evolución y sin ella (10 de 10): hasta la 15
  no cambia nada. Sin evolución, en las 30 generaciones, es el laboratorio salvo `fitness_*` (0 celdas) y
  con la misma sensibilidad agente por agente: el fitness no cambia lo que hacen los cerebros al azar, y
  la línea base sirve para los dos.
- **La medición reproduce la publicada:** la sensibilidad del C30 en las gens 1-5 y 11-15 (+0,0018 y
  +0,0045) y la de sin evolución (+0,0000 y +0,0014) son las de la [medición de la
  brújula](#brujula-c-deslizando).

Los `agentes_*.csv` quedaron en el scratchpad de la sesión, que no sobrevive: se regeneran con
`medir_puerta.py` desde el commit de esta sesión. Los SHA-256 de los `corrida_*.csv`, para comprobar que
la regeneración da las mismas corridas (LEC-011):

<details><summary>SHA-256 de las 20 corridas</summary>

| Semilla | Laboratorio, con evolución | Laboratorio, sin evolución | C30, con evolución | C30, sin evolución |
|---|---|---|---|---|
| 1 | `1d55ba5a82e1dd84737b822113d800a2c6836cc58df662e7be9e0e125ecac900` | `145912a0f0d78c67e9ec84a88497781440644571a450e092b1eade22adfc1c2f` | `32778f807eb7476309385053c34e891c2b93e48a4299e173c19498f167224874` | `80d0e840e2be8ca9e8956080f069d6dd339fadc2c3b22ca5dce7fdbdd09c5074` |
| 2 | `3e7e8127d9090187550d4597d7ce2bf475879936de2cd2612cd478e6ff63fc4b` | `a7913b8e66542343cdb12281573ec3aa75fad95f9d4348617080db5458b1b1c2` | `f57eb9cb92efdf9567885dd59340b778ac65508540aecb8ca8b110529fb11615` | `92a0294bf736b6bc3d40d102dfedaded37d24857d661ea49ec30c9803589a501` |
| 3 | `bd53a4078b2baf3db22960624321f3e365608a6fabbb3d270545d00a4802096a` | `850417627045a5717b0967e8e9289cbd4772b7d600c1f573cf0b154be2e7913e` | `a5582519e5c4616037d35bda7182312c1eb31fe450b8d87b53b9041a10a6bc69` | `089f47c36078ddde9ad534983992eff7ae287b0789f6389ab0c787b06e20ba31` |
| 4 | `fa312fde94f350fd8aa262517c5137ccb4953b95bb05df46e2ecbe49569b6ad3` | `2450d60c8aaa2afdf983bffa1654cdebd5e7e7b7da4b14dc19188a76259c5608` | `279af2cf22cf07766c7e48a4e96cc6aaa18c49cb46197277e10162063a037055` | `5550064f5dcb6df4ead6063d7f742213c55c9cf543b4278a7f6637a64eda0098` |
| 5 | `29cd62a9eda1b8faecf2dbca26fe80114319037576061d2baaa003fc98f0a4a0` | `3b1d94feea5626eaed6be8752803d668a0e2543967fe666ca0d66779f4aa26d4` | `2f6d72004ee54927481d1b8c3cbd75ef7320e6842faf145cc58fff163d8fe112` | `6d4ea3695b84fa67a205039610de7880bd369c7e38a2ce50e077c29acba37541` |

</details>

### El criterio

Gens 26-30, por semilla (rad/tick; "sí" si cumple):

| Semilla | Sensibilidad con / sin evolución | Principal | Uso con − sin | Secundario | C30: sensibilidad con evolución | C30: uso con − sin |
|---|---|---|---|---|---|---|
| 1 | +0,0099 / +0,0022 | no | −0,017 | no | −0,0063 | −0,108 |
| 2 | +0,0058 / +0,0001 | no | +0,008 | no | +0,0044 | +0,088 |
| 3 | +0,0297 / +0,0017 | sí | +0,122 | sí | +0,0033 | +0,035 |
| 4 | +0,0277 / +0,0012 | sí | +0,090 | sí | −0,0013 | +0,032 |
| 5 | +0,0197 / −0,0025 | no (0,0197) | +0,057 | sí | +0,0121 | +0,044 |
| **Criterio** | | **2 de 5** | | **3 de 5** | | |

**Aprende a girar hacia la brújula: no, por el criterio fijado** (pide 4 de 5 en los dos). Con evolución,
la sensibilidad supera a su línea base en las 5 semillas, pero en 3 no llega al tamaño mínimo.

**El control C30, por su criterio: la subida es por el fitness.** El laboratorio supera al C30 en 5 de 5
semillas, y el C30 queda en +0,0024 de promedio, por debajo de la mitad del laboratorio (+0,0093 de
+0,0186), y cerca de la línea base (+0,0005).

### Cuánto sube, y cuándo

Sensibilidad a la brújula, promedio por agente | a la comida (el control) | % de agentes con más de 0,02
a la brújula:

| | Gens 1-5 | Gens 11-15 | Gens 16-20 | Gens 21-25 | Gens 26-30 |
|---|---|---|---|---|---|
| Laboratorio, con evolución | +0,0040 · +0,0019 · 21% | +0,0033 · +0,0015 · 22% | +0,0066 · −0,0050 · 24% | +0,0092 · −0,0004 · 27% | **+0,0186** · +0,0042 · **39%** |
| C30, con evolución | +0,0018 · +0,0013 · 21% | +0,0045 · +0,0028 · 23% | +0,0076 · +0,0027 · 26% | +0,0065 · +0,0028 · 23% | +0,0024 · +0,0023 · 18% |
| Sin evolución (la misma en los dos) | +0,0000 · +0,0008 · 18% | +0,0014 · +0,0010 · 20% | +0,0011 · −0,0007 · 19% | +0,0033 · −0,0000 · 22% | +0,0005 · +0,0004 · 19% |

Por generación, el laboratorio sube desde la 16 y sigue subiendo al final: +0,0140 en la 24, +0,0164 en
la 28, +0,0228 en la 29 y **+0,0277 en la 30** (1/5 de un seguidor). En las gens 11-15, para comparar con
el C deslizando: +0,0033 contra +0,0045, más que la línea base en 4 de 5 semillas; el criterio "usa la
brújula" de la medición anterior da 2 de 5 (el C deslizando, 4 de 5).

### Por qué sube en uno y no en el otro

| | Laboratorio | C30 |
|---|---|---|
| Selección: sensibilidad a la brújula ↔ fitness dentro de la generación (Spearman, mediana; % con r > 0), gens 1-15 | +0,122 (80%) | +0,032 (63%) |
| Ídem, gens 16-30 | **+0,245 (92%)** | +0,019 (52%) |
| Aporte a la generación siguiente por quintil de sensibilidad, Q1 → Q5, gens 16-29 | 0,80 · 0,91 · 1,01 · 1,08 · 1,17 | 1,02 · 1,06 · 0,93 · 0,97 · 0,99 |
| Herencia en el cruce: pendiente hijo ↔ promedio de los padres, gens 1-15 / 16-30 | 0,20 / 0,45 | 0,22 / 0,43 |
| Herencia en la copia (un padre, con mutación o no), gens 1-15 / 16-30 | 0,67 / 0,79 | 0,65 / 0,69 |
| Élite (el mismo cerebro, en otro mapa): el techo de lo que se puede heredar, gens 1-15 / 16-30 | 0,54 / 0,72 | 0,57 / 0,62 |

Sin evolución, la correlación sensibilidad ↔ fitness es +0,056 y +0,067 en el laboratorio: los cerebros
al azar que giran hacia la brújula se acercan más, y con solo acercarse pagando eso se ve en el fitness.
En el cruce entran el 95% de los hijos (`CROSSOVER_RATE`), y la copia el 5%.

### Qué más cambia

| | Laboratorio, con evolución | C30, con evolución | Sin evolución |
|---|---|---|---|
| Agentes que cobran algo (fitness > 0), gens 1-5 / 11-15 / 26-30 | 43% / 59% / 82% | 100% (cobran todos) | 33% / 36% / 35% (laboratorio) |
| Giran (% de ticks) · giro medio · avanzan, gens 26-30 | 68% · 0,035 · 74% | 42% · 0,021 · 88% | 47% · 0,023 · 24% |
| Llegan a < 25 px de la puerta / la abren, gens 16-30 | 161 / 22 | 185 / 28 | 44 / 9 |
| Ídem, gens 26-30 | 85 / 13 | 56 / 8 | 21 / 2 |
| Criterio del ítem 5 (la puerta) en las 26-30 | 1 de 5 | 1 de 5 | — |

En el C30, en las gens 26-30, el que más gira tiene menos anti-círculo (−0,64), y giran menos que al
principio; en el laboratorio, sin ese término, giran más.

### Lectura

1. **El criterio fijado no se cumple:** principal 2 de 5 y secundario 3 de 5. Por la lectura acordada,
   lo que falta está en el aprendiz; lo de abajo dice que falta también en el fitness.
2. **El fitness es el primer bloqueo.** Con el fitness de hoy y las mismas 30 generaciones (C30), la
   selección no ve la brújula (+0,02 a +0,03) y la sensibilidad no sube (+0,0024, como la línea base).
   Con solo acercarse pagando, la selección la ve (+0,12 y +0,25; el quintil que más gira deja 1,17
   hijos contra 0,80 del que menos) y la sensibilidad sube en las 5 semillas, a +0,0186 en las 26-30 y
   +0,0277 en la 30, el doble de agentes que la línea base con más de 0,02 (39% contra 19%).
3. **El aprendiz puede, pero lento.** En 30 generaciones llega al 13% de un seguidor en promedio
   (19% en la 30) y sigue subiendo; arranca recién después de la 15, aunque la selección ya la veía
   (+0,12). Lo que lo frena se ve en la herencia, que es la misma con los dos fitness: el cruce uniforme
   peso a peso, en el 95% de los hijos, pasa al hijo 0,2 de la sensibilidad de los padres al principio y
   0,45 al final, cuando la población ya se parece; una copia pasa ~0,65 a 0,8, cerca del techo (la élite,
   el mismo cerebro en otro mapa, 0,54 a 0,72). Y la señal llega por pocos: en las gens 1-5 cobra algo el
   43% de los agentes; el resto empata en 0 y entra al pool por el orden de la lista.
4. **La comida, el control, casi no se mueve** (+0,0042 en el laboratorio, +0,0023 en el C30): lo que
   sube en el laboratorio es la brújula, cuatro veces más.
5. **La puerta, no:** el criterio del ítem 5 da 1 de 5 en los dos. En las 26-30 el laboratorio llega
   (85) y abre (13) más que el C30 (56 y 8) y que la línea base (21 y 2); en las 16-30, el C30 llega más
   (185 contra 161) sin girar hacia la brújula: camina más (avanza el 88% de los ticks).
6. **El secundario no mide la brújula solo, como advertía la salvedad.** En el laboratorio el uso sube
   en las semillas donde sube la sensibilidad (3, 4 y 5); pero en el C30 sube en 4 de 5 (+0,03 a +0,09)
   con la sensibilidad en ~0. La puerta fija y la llave roja que se mueve dejan subir el uso por otro
   camino (una ruta de memoria con x, y y el rumbo, o caminar más hacia el lado de la fortaleza). Se lee
   junto con la sensibilidad.

**Qué sugiere** (para decidir; esta sesión no tocó la simulación):
- **Rebalancear el fitness solo no alcanza:** aun con acercarse como única paga, 30 generaciones no
  llegan al criterio. Tiene sentido junto con un aprendiz más rápido.
- **Primero, medir el freno del aprendiz** con el laboratorio, desde `mediciones/` y sin tocar `src/`:
  (a) **menos cruce** (`CROSSOVER_RATE` 0,5 o 0,2: más hijos por copia y mutación, que heredan ~0,7 en
  lugar de ~0,2 a 0,45); si sube más rápido que el laboratorio, el freno es el cruce. (b) **Más
  generaciones** (60): si sigue subiendo y pasa el criterio, el aprendiz llega, lento. (a) es otra tanda
  de 15 min; (b), de ~1 h.
- **Después, el rebalance, medido como este laboratorio:** el C deslizando con el currículo hasta la 30,
  contra el C30, con el cambio del aprendiz que haya salido de (a) o (b). Dos niveles: el chico,
  acercarse más pesado (40 en lugar de 10) y el anti-círculo más liviano (9 en lugar de 18); y el grande,
  exploración y anti-círculo en 0 con la comida como está (sale lo que paga caminar hacia cualquier
  lado). El chico probablemente no alcance: la [reconstrucción de la medición
  anterior](#brujula-c-deslizando) da, con acercarse a 100, una correlación sensibilidad ↔ fitness de
  +0,075, menos que la del laboratorio en sus gens 1-15 (+0,12). Criterio a fijar antes, por ejemplo:
  sensibilidad en las 26-30 por encima de la mitad del laboratorio y del C30 en 4 de 5 semillas, sin
  perder manzanas por agente contra el C30.
- **La puerta fija** se anota aparte ([mejoras futuras](../product/mejoras_futuras.md)): una medida de
  "usa la brújula" que compara caminos sirve con un control que también quede fijo, o con fortalezas que
  se muevan.

---

<a id="laboratorio-menos-cruce"></a>

## El laboratorio de la brújula con menos cruce (2026-11-16)

**La pregunta** (sugerida por el [laboratorio](#laboratorio-brujula)): con solo acercarse pagando, la
sensibilidad a la brújula sube, pero lento, y la herencia apunta al cruce uniforme peso a peso (95% de
los hijos), que le pasa al hijo 0,2 a 0,45 de la sensibilidad de los padres, contra ~0,7 de una copia.
¿Es el cruce lo que frena? Sin cambios en `src/`, `main.py` ni `config.py`.

**Diseño.** El laboratorio igual, cambiando una sola cosa ([LEC-019](../operations/LECCIONES_APRENDIDAS.md)):
`CROSSOVER_RATE`, fijado desde [`medir_puerta.py`](../../mediciones/medir_puerta.py) con `cruce=X` antes
de `main.main()` (los demás hijos salen por copia de un padre; la mutación, igual). Dos niveles, 0,2 y
0,5, con evolución, semillas 1 a 5: 10 corridas, 10 a la vez, 19,5 min. La línea base sin evolución es la
del laboratorio: sin evolución nunca se cruza. El análisis, `analizar_brujula.py` con las dos carpetas
(ahora lee varias; el cruce es parte de la condición, y la línea base lo ignora).

**Criterio, fijado antes de medir** (LEC-018):
- **El cruce frena:** con cruce 0,2, la sensibilidad a la brújula con evolución en las gens 26-30 supera
  a la del laboratorio (0,95) en 4 de 5 semillas, y su promedio es al menos 1,5 veces el del laboratorio
  (≥ 0,028).
- El 0,5 se informa como punto intermedio, sin criterio propio. Aparte, el criterio del laboratorio
  (≥ 0,02 y más que la línea base, 4 de 5) para cada nivel.
- **Control de la manipulación:** los hijos por cruce tienen que dar ~20% y ~50%, y la herencia promedio
  tiene que subir; si no, el resultado no dice nada del cruce.

**Controles.**
- Las 10 corridas terminaron con `MEDICION inconsistencias=0` (las 10 líneas contadas), y los términos
  que no pagan dieron 0 en cada agente.
- El log de cada corrida dice "Cruce: 20.0%" o "Cruce: 50.0%": el cambio llegó al genético.
- La gen 1 de las 10 es byte a byte la del laboratorio, con su fitness (los mismos cerebros al azar en el
  mismo mapa y con los mismos pesos); la 2 ya difiere, porque el cruce actúa recién en `evolve`.
- El análisis sobre las carpetas del laboratorio y del C30 da lo publicado, más la herencia de todos los
  hijos juntos.
- **La manipulación se cumplió:** hijos por cruce, 19% y 20% con 0,2 y 50% y 49% con 0,5 (gens 1-15 y
  16-30; el laboratorio, 93%); la herencia de todos los hijos juntos sube con menos cruce (tabla de
  abajo).

<details><summary>SHA-256 de las 10 corridas (se regeneran con medir_puerta.py desde el commit de esta sesión)</summary>

| Semilla | Cruce 0,2 | Cruce 0,5 |
|---|---|---|
| 1 | `a4acd120fd230a3174241f41c382900807b3ceb2567a7984b215950878406a61` | `ed5d78672615ef995c63ba143e5c22a99a145bf6e465d4d789efc9c02d29af4b` |
| 2 | `f1a659b70e70bb882e4368c1192d57c55544b3ad8629997a15e48b6939739328` | `7282cf063458d0ce15993995d9886aaee7090a88aeb6bf7d97f8a108c4e31336` |
| 3 | `2e592d2a0decbe223d6344abac1b994d57e2c37719b2c15b53f0c05226ff18dc` | `480aba988720427b881d427f0ba7ace83e112250a8b50a088d1137965189edd2` |
| 4 | `6909f46556b6b4ae5798dabdf16a5551411648a69059cfe62c871c25c9381f44` | `95b44f28aa482e235a319e40cf36cbe3dff14b641326b43a6b421aeb798224c7` |
| 5 | `ff11c1f4243b19dc43e9bee4542bda12d5dbb2437b3c387b6cb937f020917cc5` | `8c674bda325daae79eab0ed4d3efa5db4eae26bd838884393f0ce12df600aef9` |

</details>

### El criterio

Sensibilidad a la brújula con evolución, gens 26-30, por semilla (rad/tick):

| Semilla | Laboratorio (cruce 0,95) | Cruce 0,5 | Cruce 0,2 | Sin evolución |
|---|---|---|---|---|
| 1 | +0,0099 | +0,0720 | +0,1109 | +0,0022 |
| 2 | +0,0058 | +0,0192 | +0,0715 | +0,0001 |
| 3 | +0,0297 | +0,0159 | +0,0535 | +0,0017 |
| 4 | +0,0277 | +0,0051 | +0,0496 | +0,0012 |
| 5 | +0,0197 | +0,0480 | +0,0235 | −0,0025 |
| **Promedio** | +0,0186 | +0,0321 (1,7 veces) | **+0,0618 (3,3 veces)** | +0,0005 |
| Mayor que el laboratorio | — | 3 de 5 | **5 de 5** | |
| Criterio del laboratorio (≥ 0,02 y más que la línea base) | 2 de 5 | 2 de 5 | **5 de 5** | |
| Secundario (uso con − sin ≥ 0,05) | 3 de 5 | 5 de 5 | 5 de 5 | |

**El cruce frena: sí, por el criterio fijado** (5 de 5 y 3,3 veces). Con 0,2, además, se cumple el
criterio del laboratorio, en las 5 semillas. El 0,5 queda en el medio.

### Cuánto sube, y cuándo

Sensibilidad a la brújula, promedio por agente | a la comida | % de agentes con más de 0,02 a la brújula:

| | Gens 1-5 | Gens 11-15 | Gens 16-20 | Gens 21-25 | Gens 26-30 | Gen 30 |
|---|---|---|---|---|---|---|
| Laboratorio (0,95) | +0,0040 · +0,0019 · 21% | +0,0033 · +0,0015 · 22% | +0,0066 · −0,0050 · 24% | +0,0092 · −0,0004 · 27% | +0,0186 · +0,0042 · 39% | +0,0277 |
| Cruce 0,5 | +0,0055 · +0,0035 · 23% | +0,0119 · +0,0032 · 32% | +0,0121 · +0,0072 · 31% | +0,0177 · +0,0143 · 36% | +0,0321 · +0,0187 · 47% | +0,0421 |
| Cruce 0,2 | +0,0071 · +0,0031 · 23% | **+0,0261** · +0,0035 · 43% | +0,0401 · +0,0056 · 58% | +0,0497 · +0,0096 · 70% | **+0,0618** · +0,0159 · **80%** | +0,0657 |
| Sin evolución | +0,0000 · +0,0008 · 18% | +0,0014 · +0,0010 · 20% | +0,0011 · −0,0007 · 19% | +0,0033 · −0,0000 · 22% | +0,0005 · +0,0004 · 19% | −0,0048 |

Con 0,2 arranca temprano: en las gens 11-15 ya es +0,026, más que la línea base en 5 de 5 semillas.

### Por qué

| | Laboratorio (0,95) | Cruce 0,5 | Cruce 0,2 |
|---|---|---|---|
| Hijos por cruce, gens 1-15 / 16-30 | 93% / 93% | 50% / 49% | 19% / 20% |
| Herencia de la sensibilidad, todos los hijos (pendiente hijo ↔ padres), gens 1-15 / 16-30 | 0,26 / 0,48 | 0,54 / 0,68 | **0,70 / 0,76** |
| Ídem, solo los hijos por cruce | 0,20 / 0,45 | 0,24 / 0,57 | 0,64 / 0,82 |
| Selección: sensibilidad ↔ fitness (Spearman, mediana), gens 1-15 / 16-30 | +0,122 / +0,245 | +0,165 / +0,353 | +0,250 / +0,269 |
| Agentes que cobran algo, gens 1-5 / 11-15 / 26-30 | 43% / 59% / 82% | 44% / 70% / 94% | 53% / 86% / 94% |

### La puerta

Gens 16-30, con evolución (sin evolución, la línea base del laboratorio):

| | Llegan a < 25 px | Golpean ahí | ≥ 1 golpe que contó | La abren | Ticks a < 25 px (mediana) | % de ticks golpeando (todos) | Criterio del ítem 5, gens 26-30 |
|---|---|---|---|---|---|---|---|
| Laboratorio (0,95) | 161 | 84 | 75 | 22 | 29 | 32% | 1 de 5 |
| Cruce 0,5 | 334 | 152 | 143 | 77 | 42 | 20% | **3 de 5** |
| Cruce 0,2 | **910** | 104 | 102 | 48 | 116 | 15% | 1 de 5 |
| Sin evolución | 44 | 24 | 22 | 9 | 53 | 35% | — |

### Lectura

1. **El cruce era el freno del aprendiz.** Con cruce 0,2, la sensibilidad a la brújula es 3,3 veces la del
   laboratorio en las gens 26-30, mayor en las 5 semillas, y pasa el criterio del laboratorio en las 5:
   gira hacia la brújula el 43% de lo que gira un seguidor, y el 80% de los agentes lo hace con más de 0,02
   (sin evolución, el 19%). Con 0,5 queda en el medio: hay dosis-respuesta.
2. **El mecanismo es la herencia.** Con menos cruce, los hijos heredan 0,70 de la sensibilidad en las gens
   1-15, contra 0,26; hasta los hijos por cruce heredan más (0,64), porque la población sale casi toda de
   copias y los padres se parecen. Con la herencia alta, la misma selección (+0,12 a +0,25) mueve la
   población desde temprano.
3. **La comida, el control, sube también, menos:** +0,0159 con 0,2 (un cuarto de la brújula) y +0,0187
   con 0,5. La comida no paga en el laboratorio, pero comer da energía para seguir acercándose, o la red
   generaliza (los sensores 3 y 9 tienen el mismo formato). Lo que más sube es la brújula.
4. **El cuello de la puerta pasa a ser golpear.** Con 0,2 llegan a la puerta 20 veces más que sin
   evolución y se quedan más (116 ticks de mediana), pero golpean ahí 104 de 910 y la abren 48. La
   evolución bajó el golpe en todo el recorrido (15% de los ticks, contra 35% sin evolución): golpear
   cuesta energía (`HIT_ENERGY_COST`) y paga solo al lado de la puerta, y la red no aprendió todavía a
   golpear solo ahí. Con 0,5 llegan menos y golpean más: la abren más (77) y el criterio del ítem 5 da 3 de
   5, el mejor hasta ahora, sin ser 4.
5. **Todo esto es el laboratorio:** solo acercarse y el puzzle pagan. Con el fitness del juego (el C30),
   la selección no ve la brújula (+0,02); menos cruce sube la herencia, pero sin selección no hay qué
   heredar. Falta medirlo.

**Qué sugiere** (para decidir; esta sesión no tocó la simulación):
- **El laboratorio de 60 generaciones ya no hace falta:** con menos cruce, el aprendiz llega en 30.
- **Lo siguiente, menos cruce en el juego, medido en dos pasos** (una cosa por vez, LEC-019): (a) el C30
  con cruce 0,2 y el fitness de siempre, contra el C30: si la sensibilidad no sube, el fitness sigue siendo
  el bloqueo; (b) el rebalance de [mejoras futuras](../product/mejoras_futuras.md) con cruce 0,2. Cada uno,
  una tanda de 15 min, solo con evolución (la línea base es la del laboratorio).
- **`CROSSOVER_RATE` por defecto:** bajarlo en `config.py` cambia todas las corridas y deja atrás las de
  referencia, como deslizar. Lo decide Fer, con una medición en el juego (comer, caminar, la llave) como la
  de deslizar.
- **Golpear en la puerta, el cuello nuevo:** medir antes de cambiar nada por qué baja el golpe (su costo
  de energía contra lo que paga) y si la red lo condiciona a la distancia al paso (sensor 11), con una
  sensibilidad como la de la brújula.

---

<a id="menos-cruce-juego"></a>

## Menos cruce en el juego, con su fitness (2026-11-16)

**La pregunta** (sugerida por el [laboratorio con menos cruce](#laboratorio-menos-cruce)): en el
laboratorio, bajar el cruce hizo que la red aprendiera la brújula. ¿Alcanza con eso en el juego, con el
fitness de siempre, o el fitness sigue siendo el bloqueo? Sin cambios en `src/`, `main.py` ni
`config.py`.

**Diseño.** El C30 (C deslizando con el currículo hasta la 30, el control del
[laboratorio](#laboratorio-brujula)) cambiando una sola cosa (LEC-019): `cruce=0.2`. 5 corridas con
evolución, semillas 1 a 5, 5 a la vez: 12 min. La línea base sin evolución es la del C30 (nunca se cruza).
El análisis, `analizar_brujula.py` con las carpetas del C30 y de esta tanda.

**Criterio, fijado antes de medir** (gens 26-30):
- **Aprende en el juego con menos cruce:** sensibilidad a la brújula con evolución ≥ 0,02 y mayor que la
  línea base, en 4 de 5 semillas.
- **Sube algo:** mayor que el C30 (cruce 0,95) en 4 de 5 semillas y promedio ≥ 0,0093 (la mitad del
  laboratorio, el umbral del control C30).
- Si ninguno, el fitness sigue siendo el bloqueo y menos cruce solo no alcanza.
- Control de la manipulación: ~20% de hijos por cruce y más herencia que el C30.

**Controles.** Las 5 corridas terminaron con `MEDICION inconsistencias=0` (las 5 líneas contadas) y su log
dice "Cruce: 20.0%". La gen 1 de las 5 es byte a byte la del C30; la 2 ya difiere. Hijos por cruce: 19% y
20% (gens 1-15 y 16-30). SHA-256 de las corridas, de la semilla 1 a la 5 (se regeneran con
`medir_puerta.py ... curriculo30 cruce=0.2` desde el commit de esta sesión):
`54ab8cc3df1227884247a29b3ba079108b122959b710c0387ab3ce59fc3d9c15`,
`431d73fbdf7b05c973c94f5550fba79ad520329ad66df25ab4110f6d05605a9e`,
`0339ec31df26de4975371f54da01f238e3148f10613036a248435c6f6a3134e5`,
`b3e981907c57b665cdb47cd1d28366d089f48b4de68cb13116920c5b6f39b003`,
`3161db730a8245c94a8f3a07d4cfba8d0882fa8198522c45d3c71de1c72dc832`.

**El criterio** (sensibilidad a la brújula con evolución, gens 26-30, rad/tick):

| Semilla | C30 (cruce 0,95) | C30, cruce 0,2 | Sin evolución |
|---|---|---|---|
| 1 | −0,0063 | +0,0179 | +0,0022 |
| 2 | +0,0044 | −0,0117 | +0,0001 |
| 3 | +0,0033 | +0,0200 (apenas por debajo de 0,02) | +0,0017 |
| 4 | −0,0013 | −0,0115 | +0,0012 |
| 5 | +0,0121 | +0,0304 | −0,0025 |
| **Promedio** | +0,0024 | +0,0090 | +0,0005 |
| Aprende (≥ 0,02 y más que la línea base) | 0 de 5 | **1 de 5** | |
| Sube algo (más que el C30, 4 de 5, y promedio ≥ 0,0093) | | **3 de 5, 0,0090** | |

**Aprende en el juego con menos cruce: no. Sube algo: no** (3 de 5 y 0,0090, por poco).

**Por qué** (con evolución):

| | C30 (cruce 0,95) | C30, cruce 0,2 | Laboratorio, cruce 0,2 |
|---|---|---|---|
| Selección: sensibilidad ↔ fitness (Spearman, mediana), gens 1-15 / 16-30 | +0,032 / +0,019 | −0,027 / +0,025 | +0,250 / +0,269 |
| Herencia de la sensibilidad, todos los hijos, gens 1-15 / 16-30 | 0,27 / 0,46 | 0,62 / 0,64 | 0,70 / 0,76 |

**El juego** (gens 26-30, promedio de las 5 semillas; entre paréntesis, en cuántas el cruce 0,2 supera al
C30):

| | C30 (cruce 0,95) | C30, cruce 0,2 | Sin evolución |
|---|---|---|---|
| Fitness promedio | 40,0 | 41,5 (4 de 5) | 19,6 |
| Manzanas por agente | 1,04 | 1,04 (2 de 5) | 0,30 |
| Distancia recorrida (px) | 1.221 | 1.077 | 328 |
| Edad (ticks) | 974 | 987 | 891 |
| Criterio del ítem 5 (la puerta) | 1 de 5 | 1 de 5 | — |

**Lectura.**
1. **Con el fitness del juego, menos cruce no alcanza:** la herencia sube como en el laboratorio (de 0,27
   a 0,62), pero la selección no ve la brújula (−0,03 y +0,03, como el C30), así que no hay nada que
   heredar hacia ese lado. Sin selección, la sensibilidad se mueve para los dos lados: dos semillas
   terminan en −0,012, girando al revés de la brújula, y tres por arriba; el promedio queda en +0,009.
2. **El fitness es el bloqueo,** como decía el [laboratorio](#laboratorio-brujula); el cruce era el freno
   cuando el fitness sí la pedía. Hacen falta las dos cosas.
3. **En el juego, menos cruce no empeora nada visible:** el mismo fitness (+1,5) y las mismas manzanas,
   camina un 12% menos y vive un poco más. No mide la llave roja (con el currículo hasta la 30 nacen con
   ella), y es una sola variante: para la decisión de `CROSSOVER_RATE` por defecto, falta la medición del
   juego completo.

**Qué sugiere** (para decidir; esta sesión no tocó la simulación):
- **Lo siguiente es el rebalance con cruce 0,2,** contra este C30 con cruce 0,2 (una sola cosa cambiada):
  los dos niveles de [mejoras futuras](../product/mejoras_futuras.md), el chico (acercarse 40,
  anti-círculo 9) y el grande (exploración y anti-círculo en 0, la comida como está). `medir_puerta.py`
  todavía no tiene cómo fijar esos pesos sueltos: un argumento más, como `cruce=X`.

---

<a id="rebalance-fitness"></a>

## El rebalance del fitness para la brújula, con menos cruce (2026-11-16)

**La pregunta** (sugerida por [menos cruce en el juego](#menos-cruce-juego)): con cruce 0,2 los hijos heredan la
sensibilidad a la brújula, pero con el fitness del juego la selección no la ve. ¿Alcanza con cambiar los pesos del
fitness para que la vea, sin dejar de comer? Sin cambios en `src/`, `main.py` ni `config.py`.

**Diseño.** El C30 con cruce 0,2 (el C deslizando con el currículo hasta la 30 y `CROSSOVER_RATE` 0,2, la tanda de
[menos cruce en el juego](#menos-cruce-juego)) cambiando una sola cosa (LEC-019): los pesos del fitness, con el
argumento nuevo de [`medir_puerta.py`](../../mediciones/medir_puerta.py), `pesos=NOMBRE:VALOR,...`, que los fija en
`SimulationConfig` antes de `main.main()` (un nombre que `config.py` no tiene corta la corrida). Los dos niveles de
[mejoras futuras](../product/mejoras_futuras.md#aparecido-en-el-laboratorio-de-la-brújula--2026-11-16):
- **Chico,** `pesos=FITNESS_ACERCARSE:40,FITNESS_ANTI_CIRCLE:9`: acercarse de 10 a 40 y anti-círculo de 18 a 9.
- **Grande,** `pesos=FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`: sale lo que paga caminar hacia cualquier lado;
  comida, supervivencia, acercarse y el puzzle quedan como están.

Cada nivel con evolución, semillas 1 a 5. El control (el C30 con cruce 0,2) y la línea base sin evolución (la del
C30: sin evolución nunca se cruza, y el fitness no cambia lo que hacen los cerebros) se regeneran, y sus SHA-256 se
comparan con los publicados (LEC-011): 20 corridas de 30 generaciones, en dos tandas de 10. El análisis,
`analizar_brujula.py`, ahora con los pesos en la condición; las manzanas, del CSV de `main.py`.

**Criterio, fijado antes de medir** (gens 26-30, con evolución; como referencia, el control dio +0,0090 de
sensibilidad promedio, y el laboratorio con cruce 0,2, donde solo paga acercarse, +0,0618):
1. **Aprende la brújula por el rebalance:** en 4 de 5 semillas, la sensibilidad a la brújula es ≥ 0,02 rad/tick
   (el tamaño mínimo del laboratorio), mayor que la línea base y mayor que el control de la misma semilla.
2. **Sin dejar de comer:** manzanas por agente (`manzanas_prom`), promedio de las 5 semillas, al menos el 90% de las
   del control.
3. Un nivel pasa si cumple 1 y 2. Si cumple 1 y no 2, aprende la brújula a costa de comer: se informa así, y no se
   propone para el juego tal cual.
- **Se lee con la selección** (la medida independiente, LEC-018): la correlación sensibilidad ↔ fitness con
  evolución tiene que subir desde la del control (−0,03 y +0,03 en las gens 1-15 y 16-30) hacia la del laboratorio
  (+0,25 y +0,27). Si 1 se cumple sin que suba, no se atribuye al rebalance. La sensibilidad a la comida, al lado.
- **Control de la manipulación:** el log de cada corrida imprime los pesos; en la gen 1 (los mismos cerebros en el
  mismo mapa que el control), el comportamiento es el del control celda a celda, y cada término del fitness es el
  del control por el peso nuevo sobre el viejo, agente por agente; la gen 2 ya difiere.
- La puerta (el criterio del ítem 5) se informa, sin criterio propio: su cuello es golpear.
- **Lo esperado,** por la [reconstrucción](#brujula-c-deslizando): el chico probablemente no alcance.

**Cómo se corrió.** Primero el control y la línea base (10 corridas, 17 min), para comprobar que el script con el
argumento nuevo da lo publicado; después los dos niveles (10 corridas, 17 min). El criterio 1, el 2 y el juego, con un
script de la sesión sobre los CSV, y cruzados con `analizar_brujula.py` (dan lo mismo).

**Controles.**
- **Las 20 corridas terminaron con `MEDICION inconsistencias=0`** (las 20 líneas contadas). Los logs de los niveles
  dicen `PESOS {...}` (5 y 5) y "Cruce: 20.0%" (10); los del control, "Cruce: 20.0%" (5).
- **El control y la línea base son byte a byte los publicados:** 10 de 10 SHA-256 (los de [menos cruce en el
  juego](#menos-cruce-juego) y los del [laboratorio](#laboratorio-brujula)). La medición da lo mismo: el control,
  +0,0090 con las mismas 5 semillas, 41,5 de fitness y 1,04 manzanas; la línea base, la fila sin evolución del
  laboratorio.
- **La manipulación llegó, y solo al fitness:** en la gen 1 de las 10 corridas, el CSV de `main.py` es el del control
  salvo las 4 columnas de fitness, el comportamiento de los 60 agentes es el del control celda a celda, y cada término
  del fitness es el del control por el peso nuevo sobre el viejo, agente por agente (acercarse × 4 y anti-círculo × 0,5
  en el chico; exploración y anti-círculo en 0 en el grande). La gen 2 ya difiere en las 10.
- Un nombre que `config.py` no tiene (`FITNES_ANTI_CIRCLE`) corta la corrida antes de empezar.

<details><summary>SHA-256 de las 10 corridas nuevas (se regeneran con medir_puerta.py desde el commit de esta sesión)</summary>

| Semilla | Chico | Grande |
|---|---|---|
| 1 | `9b287f7de1cf36a8d42658e392214cc70234faa020156934e6410c90e190e341` | `9354fbd0727227fbf6a9504b3a769ec2f9ca737d5881704011eacffadd7d6f60` |
| 2 | `097edc5929995a1b8b227973ff15f76fe62b0982528a3b57e4a8757003737011` | `a155c37676f6aafbcad3511c649c36dc1717ee5f73b1723425a50cc577b14938` |
| 3 | `f65a6350ec07e504d1955808b0e6484ddc68fb17ecccc76899ccc367edb3716a` | `68fd92479019ec5962dc4585ed3f3faf38349b49dc022bd98074326487e2575e` |
| 4 | `fa08a7a14c4aa0d9c0ff42fe5a9b720d0c34407a3876a70cff3dce6708a3a04d` | `0787f0f7b3a7324e770758a9396454bbae1c64bd9a34e93996f04c816e47ccd5` |
| 5 | `cdcd79101754f459b46c971cf25d3d6425fe9a97d7922b192a5c7a250a3d4090` | `498eb3dd37bc3026482986a138698c935d38fda6310af22f941d81bc4dc44c23` |

</details>

### El criterio

Sensibilidad a la brújula con evolución, gens 26-30, por semilla (rad/tick):

| Semilla | Control (C30, cruce 0,2) | Chico | Grande | Sin evolución |
|---|---|---|---|---|
| 1 | +0,0179 | −0,0222 | +0,0166 | +0,0022 |
| 2 | −0,0117 | +0,0027 | **+0,0270** | +0,0001 |
| 3 | +0,0200 | +0,0149 | +0,0127 | +0,0017 |
| 4 | −0,0115 | **+0,0561** | −0,0042 | +0,0012 |
| 5 | +0,0304 | +0,0192 | −0,0483 | −0,0025 |
| **Promedio** | +0,0090 | +0,0141 (1,6 veces el control) | +0,0008 | +0,0005 |
| 1. ≥ 0,02, más que la línea base y más que el control | | **1 de 5** | **1 de 5** | |
| Sin pedir más que el control (el criterio del laboratorio) | 1 de 5 | 1 de 5 | 1 de 5 | |
| Más que el control | | 2 de 5 | 2 de 5 | |
| 2. Manzanas por agente (% del control) | 1,04 | 0,92 (**88%**) | 1,04 (100%) | 0,30 |

**Ninguno de los dos niveles pasa.** El chico no cumple el 1 (1 de 5) ni el 2 (88%, pedía 90%: menos manzanas que el
control en las 5 semillas); el grande cumple el 2, pero no el 1 (1 de 5).

### Cuánto sube, y cuándo

Sensibilidad a la brújula, promedio por agente | a la comida | % de agentes con más de 0,02 a la brújula:

| | Gens 1-5 | Gens 11-15 | Gens 16-20 | Gens 21-25 | Gens 26-30 |
|---|---|---|---|---|---|
| Control | −0,0027 · +0,0037 · 17% | +0,0014 · +0,0084 · 17% | −0,0002 · +0,0153 · 17% | +0,0049 · +0,0167 · 24% | +0,0090 · +0,0229 · 33% |
| Chico | +0,0015 · −0,0002 · 18% | −0,0018 · +0,0032 · 14% | +0,0058 · +0,0083 · 23% | **+0,0137** · +0,0161 · 33% | **+0,0141** · +0,0158 · 36% |
| Grande | +0,0013 · +0,0037 · 18% | +0,0011 · +0,0090 · 18% | −0,0014 · +0,0180 · 23% | −0,0026 · +0,0194 · 20% | +0,0008 · +0,0201 · 22% |
| Sin evolución | +0,0000 · +0,0008 · 18% | +0,0014 · +0,0010 · 20% | +0,0011 · −0,0007 · 19% | +0,0033 · −0,0000 · 22% | +0,0005 · +0,0004 · 19% |

El chico sube desde la 16 y se estanca desde la 22, entre +0,012 y +0,017 por generación (el laboratorio con cruce 0,2,
+0,0618 en las 26-30, seguía subiendo). La comida sube en los tres: en el chico, tanto como la brújula; en el control y
el grande, más.

### Por qué

| | Control | Chico | Grande | Laboratorio, cruce 0,2 |
|---|---|---|---|---|
| Selección: sensibilidad a la brújula ↔ fitness (Spearman, mediana), gens 1-15 / 16-30 | −0,027 / +0,025 | +0,050 / **+0,143** | +0,054 / +0,004 | +0,250 / +0,269 |
| Ídem, a la comida | +0,103 / +0,107 | +0,069 / +0,098 | +0,146 / +0,123 | |
| Aporte a la generación siguiente por quintil de sensibilidad a la brújula, Q1 → Q5, gens 16-29 | 0,92 · 0,99 · 1,01 · 0,96 · 1,09 | 0,81 · 1,07 · 0,92 · 1,05 · 1,11 | 1,02 · 1,05 · 0,95 · 0,97 · 0,98 | |
| Herencia de la sensibilidad, todos los hijos (pendiente), gens 1-15 / 16-30 | 0,62 / 0,64 | 0,66 / 0,84 | 0,59 / 0,78 | 0,70 / 0,76 |
| Acercarse en el fitness, gens 26-30: promedio · desvío dentro de la generación (mediana) · Spearman con el fitness | 1,9 · 1,5 · +0,32 | 9,4 · **6,9** · +0,65 | 1,6 · 1,6 · +0,31 | |
| La comida, ídem | 7,3 · 7,0 · +0,80 | 6,5 · 6,9 · +0,70 | 7,3 · 7,1 · **+0,85** | |
| Giran (% de ticks con la llave) · giro medio (rad/tick), gens 26-30 | 46% · 0,020 | 47% · 0,019 | **73% · 0,042** | |

Sin evolución, el giro es 47% · 0,023.

### La puerta y el juego

Gens 16-30, con evolución (sin evolución, la línea base):

| | Llegan a < 25 px | Golpean ahí | ≥ 1 golpe que contó | La abren (por semilla) | Ticks a < 25 px (mediana) | % de ticks golpeando (promedio por agente) |
|---|---|---|---|---|---|---|
| Control | 162 | 42 | 40 | 12 (0, 2, 0, 1, 9) | 28,5 | 17% |
| Chico | **333** | 105 | 97 | 28 (2, 3, 0, 20, 3) | 32 | 23% |
| Grande | 162 | **89** | 85 | **32** (5, 20, 1, 6, 0) | 29 | 17% |
| Sin evolución | 44 | 24 | 22 | 9 (4, 1, 3, 0, 1) | 52,5 | 35% |

Gens 26-30, promedio de las 5 semillas (entre paréntesis, en cuántas el nivel supera al control):

| | Control | Chico | Grande | Sin evolución |
|---|---|---|---|---|
| Fitness promedio | 41,5 | 41,4 (2 de 5) | 17,0 (0 de 5; sin dos términos, otra escala) | 19,6 |
| Manzanas por agente | 1,04 | 0,92 (0 de 5) | 1,04 (2 de 5) | 0,30 |
| Distancia recorrida (px) | 1.077 | 1.079 (2 de 5) | 1.315 (3 de 5) | 328 |
| Edad (ticks) | 987 | 969 (2 de 5) | 989 (2 de 5) | 891 |
| Agentes con la puerta abierta, por generación | 0,36 | 0,52 (3 de 5) | 1,16 (4 de 5) | 0,08 |
| Criterio del ítem 5 (la puerta) | 1 de 5 | 1 de 5 | 2 de 5 | — |

### Lectura

1. **Ninguno de los dos niveles hace que la brújula se aprenda en el juego,** por el criterio fijado: 1 de 5 cada uno,
   como el control. Lo esperado era que el chico no alcanzara; no alcanza, pero queda más cerca que el grande.
2. **El chico va en la dirección, sin llegar, y paga con comida.** La selección empieza a ver la brújula (+0,14 en las
   gens 16-30, la mitad del laboratorio; el control, +0,03) y el quintil que más gira hacia ella deja 1,11 hijos contra
   0,81 del que menos. La sensibilidad sube desde la 16 y se estanca en ~+0,014 desde la 22: 1,6 veces el control, un
   cuarto del laboratorio. Una semilla aprende como el laboratorio (la 4: +0,056, y abre la puerta 20 veces en las gens
   16-30) y dos quedan cerca del umbral (la 3, +0,015; la 5, +0,019). Acercarse pesa ahora en el fitness como la comida
   (desvío 6,9 cada uno; en el control, 1,5 contra 7,0), y las dos tiran para lados distintos: 12% menos manzanas,
   menos en las 5 semillas. Llegan a la puerta el doble que el control.
3. **El grande no hace que la selección vea la brújula** (+0,05 y +0,00). Sacar lo que paga caminar deja el fitness en
   manos de la comida (Spearman +0,85), y acercarse sigue chico (desvío 1,6). Sin el anti-círculo giran más (73% de los
   ticks, el doble de giro medio), pero no hacia la brújula. No pierde manzanas, y camina más aunque caminar ya no
   pague.
4. **El grande abre la puerta más que el control sin girar hacia la brújula** (32 contra 12 en las gens 16-30; 4 de 5
   semillas en las 26-30; criterio del ítem 5, 2 de 5): llegan los mismos (162), pero golpean ahí más de la mitad (89,
   contra 42). Una semilla pone 20 de las 32. Sin medir por qué; una posibilidad es que, sin el anti-círculo, quedarse
   dando vueltas al lado de la puerta ya no cueste.
5. **Lo que separa al chico del laboratorio es cuánto pesa acercarse contra lo demás.** La selección ve la brújula en
   proporción: el laboratorio (paga solo acercarse) +0,27; el chico (acercarse como la comida) +0,14; el control y el
   grande (acercarse con un desvío de 1,5) ~0. Sacar términos no alcanza si lo que queda no es acercarse.
6. **El camino a la puerta sube más que la sensibilidad, como advertía la salvedad del
   [laboratorio](#laboratorio-brujula).** En el chico, el uso (camino a la puerta − al control) con evolución supera al
   de la línea base en 5 de 5 semillas en las 26-30, también donde la sensibilidad no llega (la 3: +0,20 de uso con
   +0,015). Con la puerta fija, acercarse también se puede cobrar con una ruta (la red ve x, y y el rumbo). Cuanto más
   paga acercarse, más pesa.

**Qué sugiere** (para decidir; esta sesión no tocó la simulación):
- **Ninguno de los dos niveles va a `config.py`:** no pasan.
- **Si se sigue por el fitness, el paso que falta es juntar los dos:** acercarse 40 sin lo que paga caminar,
  `pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`, contra el grande (cambia solo acercarse,
  LEC-019). Quedarían la comida y acercarse, con el mismo peso en el fitness; por lo de arriba, la selección vería la
  brújula más que en el chico. Una tanda de 17 min, solo con evolución, con este mismo criterio.
- **El costo en comida es parte de la pregunta, no un ruido:** en el chico, subir acercarse subió la brújula y bajó las
  manzanas. Si el próximo nivel aprende la brújula comiendo menos, el criterio 2 choca con el 1, y cuánta comida vale
  la puerta lo decide Fer.
- **Las fortalezas fijas pesan más con acercarse más pesado** (lectura 6): si el próximo nivel sube el camino a la puerta
  sin la sensibilidad, sortearlas en cada generación va antes que seguir con los pesos
  ([mejoras futuras](../product/mejoras_futuras.md#aparecido-en-el-laboratorio-de-la-brújula--2026-11-16)).
- **El golpe del grande:** si sin el anti-círculo golpean más al lado de la puerta, se ve en la medición del golpe que
  ya está anotada.

---

<a id="acercarse-sin-caminar"></a>

## Acercarse 40 sin lo que paga caminar (2026-11-16)

**La pregunta** (sugerida por el [rebalance](#rebalance-fitness)): la selección ve la brújula en proporción a cuánto
pesa acercarse contra lo demás. Si quedan solo la comida y acercarse, con el mismo peso, ¿se aprende la brújula? Sin
cambios en `src/`, `main.py` ni `config.py`.

**Diseño.** El grande del [rebalance](#rebalance-fitness) (el C30 con cruce 0,2, exploración y anti-círculo en 0)
cambiando una sola cosa (LEC-019): acercarse de 10 a 40,
`pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`. 5 corridas con evolución, semillas 1 a 5, 5 a
la vez. El grande, el C30 con cruce 0,2 y la línea base sin evolución son las corridas del rebalance, de la misma
sesión (sus SHA-256, ahí).

**Criterio, fijado antes de medir** (el del rebalance, con el grande como control; gens 26-30, con evolución):
1. **Aprende la brújula:** en 4 de 5 semillas, la sensibilidad a la brújula es ≥ 0,02 rad/tick, mayor que la línea
   base y mayor que el grande de la misma semilla.
2. **Sin dejar de comer:** manzanas por agente, promedio de las 5 semillas, al menos el 90% de las del grande (1,04,
   las mismas que el C30 con cruce 0,2).
3. Pasa si cumple 1 y 2. Si cumple 1 y no 2, aprende la brújula a costa de comer: cuánta comida vale la puerta lo
   decide Fer.
- **Se lee con la selección:** la correlación sensibilidad ↔ fitness con evolución tiene que subir desde la del grande
  (+0,05 y +0,00 en las gens 1-15 y 16-30). **Lo esperado,** por la lectura 5 del rebalance: más que el chico (+0,05 y
  +0,14). Si 1 se cumple sin que suba, no se atribuye al cambio.
- **La ruta:** si el camino a la puerta contra el control sube y la sensibilidad no (como en la semilla 3 del chico),
  lo que paga acercarse se cobra por otro lado, y las fortalezas fijas van antes que seguir con los pesos.
- **Control de la manipulación:** los logs imprimen los pesos; en la gen 1, el comportamiento es el del C30 con cruce
  0,2 celda a celda, con acercarse × 4 y exploración y anti-círculo en 0, agente por agente.

**Controles.** Las 5 corridas terminaron con `MEDICION inconsistencias=0` (las 5 líneas contadas, 12 min), y sus logs
dicen `PESOS {'FITNESS_ACERCARSE': 40.0, 'FITNESS_EXPLORATION': 0.0, 'FITNESS_ANTI_CIRCLE': 0.0}` y "Cruce: 20.0%". En
la gen 1 de las 5, el comportamiento es el del C30 con cruce 0,2 celda a celda, el CSV de `main.py` también salvo el
fitness, y los términos son los esperados agente por agente; la gen 2 ya difiere. SHA-256, de la semilla 1 a la 5 (se
regeneran con `medir_puerta.py ... curriculo30 cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`
desde el commit de esta sesión): `bce521baee9badff2b590221ab3e15b4abcb72a36263c3e4a7949907733ead49`,
`5d5b9ec7e084f4c929b6bd2478a65fb4f35229b51cc52fa1f9f0bd4fb03c6610`,
`8dabd31423e286dd5943ea971764c9f8305711e8f274a8c59cce3e268de35215`,
`c5289ed9f9d01184a5a37170c788829aa4b2ba22a54fa6259d8248ebc2c04130`,
`1405b53488e5d6c9daa786bb99606c0f7d9bceab4ec05ed7c616806ba72a95d4`.

**El criterio** (sensibilidad a la brújula con evolución, gens 26-30, rad/tick):

| Semilla | Grande (el control) | Acercarse 40 sin caminar | Chico (referencia) | Sin evolución |
|---|---|---|---|---|
| 1 | +0,0166 | +0,0108 | −0,0222 | +0,0022 |
| 2 | +0,0270 | **+0,0390** | +0,0027 | +0,0001 |
| 3 | +0,0127 | **+0,0202** | +0,0149 | +0,0017 |
| 4 | −0,0042 | +0,0012 | +0,0561 | +0,0012 |
| 5 | −0,0483 | +0,0152 | +0,0192 | −0,0025 |
| **Promedio** | +0,0008 | **+0,0173** | +0,0141 | +0,0005 |
| 1. ≥ 0,02, más que la línea base y más que el grande | | **2 de 5** | | |
| Más que el grande | | 4 de 5 | | |
| 2. Manzanas por agente (% del grande) | 1,04 | 1,07 (**102%**; 4 de 5 por encima) | 0,92 | 0,30 |

**No pasa:** cumple el 2, pero el 1 da 2 de 5 (pedía 4). Es lo más cerca que llegó el juego: supera al grande en 4 de 5
semillas, el promedio es el más alto medido fuera del laboratorio (1,9 veces el C30 con cruce 0,2) y no pierde
comida. Queda en el 28% del laboratorio con cruce 0,2 (+0,0618).

**Cuánto sube, y cuándo** (sensibilidad a la brújula | a la comida | % de agentes con más de 0,02):

| | Gens 1-5 | Gens 11-15 | Gens 16-20 | Gens 21-25 | Gens 26-30 |
|---|---|---|---|---|---|
| Acercarse 40 sin caminar | +0,0023 · −0,0006 · 19% | **+0,0094** · +0,0059 · 23% | +0,0070 · +0,0065 · 23% | +0,0132 · +0,0091 · 29% | **+0,0173** · +0,0100 · 34% |
| Grande | +0,0013 · +0,0037 · 18% | +0,0011 · +0,0090 · 18% | −0,0014 · +0,0180 · 23% | −0,0026 · +0,0194 · 20% | +0,0008 · +0,0201 · 22% |
| Chico | +0,0015 · −0,0002 · 18% | −0,0018 · +0,0032 · 14% | +0,0058 · +0,0083 · 23% | +0,0137 · +0,0161 · 33% | +0,0141 · +0,0158 · 36% |

Sube antes que el chico (en las 11-15 ya es +0,009) y sigue subiendo despacio al final (+0,0205 en la 28, +0,0178 en la
30). Es el primero en que la brújula sube más que la comida (+0,017 contra +0,010; en el chico, parejas; en el grande y
el C30, la comida el doble).

**Por qué** (con evolución):

| | Grande | Acercarse 40 sin caminar | Chico | Laboratorio, cruce 0,2 |
|---|---|---|---|---|
| Selección: sensibilidad a la brújula ↔ fitness (Spearman, mediana), gens 1-15 / 16-30 | +0,054 / +0,004 | +0,048 / **+0,110** | +0,050 / +0,143 | +0,250 / +0,269 |
| Ídem, a la comida | +0,146 / +0,123 | +0,101 / +0,167 | +0,069 / +0,098 | |
| Aporte por quintil de sensibilidad a la brújula, Q1 → Q5, gens 16-29 | 1,02 · 1,05 · 0,95 · 0,97 · 0,98 | 0,82 · 1,06 · 0,97 · 1,07 · 1,05 | 0,81 · 1,07 · 0,92 · 1,05 · 1,11 | |
| Herencia de la sensibilidad, todos los hijos (pendiente), gens 1-15 / 16-30 | 0,59 / 0,78 | 0,59 / 0,65 | 0,66 / 0,84 | 0,70 / 0,76 |
| Acercarse en el fitness, gens 26-30: promedio · desvío · Spearman con el fitness | 1,6 · 1,6 · +0,31 | 8,1 · 6,7 · +0,66 | 9,4 · 6,9 · +0,65 | |
| La comida, ídem | 7,3 · 7,1 · +0,85 | 7,6 · 6,9 · +0,73 | 6,5 · 6,9 · +0,70 | |
| Giran (% de ticks con la llave) · giro medio, gens 26-30 | 73% · 0,042 | 67% · 0,035 | 47% · 0,019 | |

**La puerta y el juego** (gens 16-30 para la puerta; 26-30 para el resto):

| | Grande | Acercarse 40 sin caminar | Chico |
|---|---|---|---|
| Llegan a < 25 px · golpean ahí · la abren (por semilla) | 162 · 89 · 32 (5, 20, 1, 6, 0) | 167 · 44 · 20 (0, 20, 0, 0, 0) | 333 · 105 · 28 (2, 3, 0, 20, 3) |
| % de ticks golpeando (promedio por agente) | 17% | 23% | 23% |
| Criterio del ítem 5 | 2 de 5 | 1 de 5 | 1 de 5 |
| Fitness · manzanas · distancia (px) · edad | 17,0 · 1,04 · 1.315 · 989 | 23,0 · 1,07 · 1.327 · 964 | 41,4 · 0,92 · 1.079 · 969 |
| Uso (camino a la puerta − al control), con evolución menos sin, ≥ 0,05 | 1 de 5 | 4 de 5 | 3 de 5 |

**Lectura.**
1. **No pasa** (2 de 5), pero es el mejor resultado fuera del laboratorio: más brújula que el grande en 4 de 5, el
   promedio más alto (+0,017), sube antes, más que la comida, y sin perder manzanas. Sacar lo que paga caminar le
   devolvió a la comida lo que el chico le quitaba (102% contra 88%).
2. **Lo esperado no se cumplió:** la selección no ve la brújula más que en el chico (+0,11 contra +0,14 en las gens
   16-30). Con la comida y acercarse pesando lo mismo, la selección se reparte entre las dos (la comida, +0,17), como en
   el chico. La lectura 5 del rebalance se ajusta: lo que importa es cuánto pesa acercarse contra la comida, no contra
   todo lo demás; con los dos parejos, la selección ve la brújula a la mitad que en el laboratorio, en los dos casos.
3. **La ruta aparece de nuevo:** el uso (camino a la puerta contra el control) sube en las 5 semillas y pasa 0,05 en 4,
   también donde la sensibilidad no se mueve (la semilla 4: +0,12 de uso con +0,001). Con la puerta fija, una semilla
   puede cobrar acercarse sin la brújula; pasó en el chico (la 3) y pasa acá.
4. **Donde se aprende la brújula, se abre la puerta.** En las cuatro condiciones con cruce 0,2 (el C30, el chico, el
   grande y esta), la semilla con más sensibilidad en las gens 26-30 es la que más abre la puerta en las 16-30 (la 5, la
   4, la 2 y la 2, con 9, 20, 20 y 20 aperturas). Por azar, 1 en 625 si fueran independientes; no lo son del todo
   (comparten semillas y mapas), así que es una observación, no una prueba. Acá, las 20 aperturas son de la semilla 2.

**Qué sugiere** (para decidir; esta sesión no tocó la simulación):
- **No va a `config.py` todavía:** no pasa el criterio. Si hubiera que elegir unos pesos para el juego con cruce 0,2,
  estos son los mejores medidos (más brújula, la misma comida).
- **Lo siguiente, las fortalezas que se mueven** ([mejoras futuras](../product/mejoras_futuras.md#aparecido-en-el-laboratorio-de-la-brújula--2026-11-16)):
  con la puerta fija, acercarse se cobra también con una ruta (lectura 3), y la selección no distingue la ruta de la
  brújula. Sortearlas en cada generación deja la brújula como la única forma de cobrar acercarse, y es lo que pide el
  ítem 7 del BACKLOG ("aprender reglas, no un mapa"). Cambia la simulación: un switch apagado por defecto, con el CSV de
  antes byte a byte apagado, y medido con estos mismos pesos, contra estos mismos pesos con la puerta fija.
- **La alternativa, más barata y sin código:** acercarse más pesado que la comida (80, sin lo que paga caminar), contra
  esta tanda. Por la lectura 2 debería subir la selección de la brújula; el chico dice que el costo puede ser comida.

---

<a id="fortalezas-moviles"></a>

## Fortalezas móviles: el switch y la medición con acercarse 40 sin caminar (2026-11-16)

**La pregunta** (sugerida por [acercarse 40 sin caminar](#acercarse-sin-caminar), lectura 3): con la puerta fija,
acercarse se cobra también con una ruta (la red ve x, y y el rumbo absoluto), y la selección no distingue la ruta de la
brújula. Si las fortalezas cambian de lugar en cada generación, la brújula queda como la única forma de cobrar acercarse
a la puerta. ¿Se aprende?

**Las fortalezas eran más fijas de lo que decían los docs.** `_generate_fortresses` las pone en las mismas esquinas en
todas las semillas: la chica en (50, 50) y la grande en (718, 558), abajo a la derecha (su lugar se calcula con
`TILE_SIZE`, 32, aunque sus muros son de 20 px). `reset_food` las guarda al regenerar el mapa. La puerta de madera
estuvo en (90, 130) en todas las corridas medidas hasta hoy.

**El switch.** `FORTALEZAS_MOVILES` en `config.py` (`:128`), apagado por defecto, y `--fortalezas-moviles` en `main.py`
y `experimento.py`; en `medir_puerta.py`, la palabra `fortalezas-moviles`. Prendido, `reset_food` sortea un lugar para
las dos fortalezas antes de regenerar el estanque y el resto del mapa, que las esquivan (`world.py:393` y
`_sortear_fortalezas`, `:569`). Las dos puertas, la llave dorada y el cofre van con ellas (`:427`). La generación 1
queda como siempre: con el switch prendido, la gen 1 es la del control celda a celda.
- **Dónde pueden ir.** La zona de cada fortaleza son sus muros y el frente de su puerta que despeja
  `_clear_area_around_doors`: abajo de la chica y arriba de la grande, 3 tiles de 32 desde la fila de la puerta, de 2
  tiles a la izquierda a 3 a la derecha. Muros y frente quedan a 50 px del borde (`MARGEN_FORTALEZAS`, lo que tienen en
  la gen 1): el perímetro no tapa la puerta. Las dos zonas quedan a 40 px una de otra (`SEPARACION_FORTALEZAS`): el
  despeje de una puerta borra todo lo que encuentra, muros incluidos, y no puede tocar los de la otra.
- **Apagado no consume azar,** y no es columna del CSV: va en el nombre del archivo (`_fortalezas_moviles`), en el
  panel, en el subtítulo del boletín y en el resumen del experimento. En el panel va en un renglón propio
  ("Fortalezas: móviles"): en el de las ayudas, con las tres prendidas, no entra. El mapa de calor de la pantalla final
  dibuja las fortalezas de su generación (el registro las guarda con cada grilla), y su nota lo dice.
- **Qué más usa esas posiciones, y las lee de la generación en curso:** `_is_inside_fortress` (comida, árboles, llave
  roja, ubicación de los agentes), `_clear_area_around_doors`, `_is_pond_position_valid`, la brújula y la guía
  (`_proximo_paso` lee los objetos en cada tick), el renderer (dibuja los objetos), y la geometría y el seguidor de
  `medir_puerta.py` (leen `world.door` al cerrar cada generación; `geometria_*.csv` ahora dice dónde está la puerta,
  `puerta_x` y `puerta_y`). Nada guarda la posición vieja.

**Cómo se verificó el switch.**
- **Apagado, el CSV es el de antes byte a byte.** Antes de tocar el código, 6 corridas de 3 generaciones con semilla 1
  desde 349a43f: guiado y autónomo con y sin evolución, y el autónomo con las tres ayudas, con y sin evolución. Después
  del cambio, los 6 SHA-256 iguales. En el test, 4 SHA-256 de una corrida corta en proceso (semilla 7, 3 generaciones de
  60 ticks, los dos modos con y sin evolución), calculados con el código de 349a43f. El control más fuerte, los 5 SHA-256
  publicados de acercarse 40 sin caminar, va en la medición.
- **Prendido,** `tests/test_fortalezas_moviles.py` (22 tests): la gen 1 es la de siempre y después cambian, con las
  puertas, la llave dorada y el cofre en su lugar relativo; muros enteros, dentro de los márgenes y con las zonas
  separadas; nada adentro (estanque, obstáculos, comida, llave roja, hacha, agentes); la puerta de madera alcanzable
  desde donde nace cada agente, y el puzzle completable desde ahí con la llave roja, con los métodos del mundo, en 3
  semillas. Lo alcanzable se mira con las componentes conexas de una grilla de 3 px con las colisiones de `act()` de
  cada etapa: un camino en la grilla es un camino de verdad. Su control: con tres muros pegados al frente de la puerta,
  ningún agente llega. Contra el código de 349a43f fallan los 8 tests que dependen del switch y pasan los 14 de
  propiedades, que con las fortalezas fijas también se cumplen.
- **El mundo, sin correr la simulación** (un script de la sesión: el mapa y la ubicación de los agentes, 10 semillas × 30
  generaciones por condición): prendido, cambian de lugar en las 290 generaciones desde la 2, con los muros enteros y
  nada encima; el 100% de los agentes puede llegar a menos de 25 px de la puerta de madera en los 300 mundos, igual que
  con las fijas.
- **Dos bugs de antes aparecieron al probarlo,** DIAG-33 y DIAG-34 (en la [tabla de bugs](#diagnostico-inicial)). No se
  arreglan acá: cambiarían el CSV con el switch apagado.

**La medición. Diseño** (cambia una sola cosa, LEC-019): acercarse 40 sin caminar, con evolución (`medir_puerta.py ...
acercarse deslizar curriculo30 cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`), con
las fortalezas móviles (`fortalezas-moviles`) contra las fijas. La línea base sin evolución va con las móviles
(`sin_evolucion ... acercarse deslizar curriculo30 fortalezas-moviles`): el switch cambia lo que hacen los agentes, así
que la de la puerta fija no sirve. Sin evolución, el cruce y los pesos no cambian lo que hacen, como en las anteriores.
15 corridas de 30 generaciones, semillas 1 a 5: las 5 fijas (regeneran el control: el scratchpad de la sesión anterior
ya no está), 5 móviles y 5 de línea base con las móviles, en dos tandas (10 y 5). `analizar_brujula.py` ahora tiene las
fortalezas móviles en la condición, también en la línea base, y compara una condición con móviles contra la misma con
fijas.

**Criterio, fijado antes de medir** (el del rebalance; gens 26-30, con evolución):
1. **Aprende la brújula:** en 4 de 5 semillas, la sensibilidad a la brújula es ≥ 0,02 rad/tick, mayor que la línea base
   (móviles, sin evolución) y mayor que las fijas de la misma semilla.
2. **Sin dejar de comer:** manzanas por agente, promedio de las 5 semillas, al menos el 90% de las de las fijas (1,07 en
   la tanda publicada).
3. Pasa si cumple 1 y 2.
- **Se lee con la selección** (LEC-018): la correlación sensibilidad ↔ fitness con evolución, gens 16-30, tiene que
  subir desde la de las fijas (+0,110 en la tanda publicada). Si 1 se cumple sin que suba, no se atribuye al switch.
- **Lo esperado:** sin la ruta, lo que paga acercarse a la puerta pasa por la brújula, y la selección debería verla más.
  Pero la puerta en cualquier lado puede quedar más cerca o más lejos que en la esquina: no se sabe hacia dónde va lo que
  se cobra acercándose.
- **La ruta:** con las fijas, el uso (camino a la puerta − al control, con evolución menos sin) pasó 0,05 en una semilla
  con sensibilidad < 0,02 (la 4: +0,12 con +0,001). Con las móviles no debería pasar en ninguna; si pasa, acercarse se
  cobra por otro lado que todavía no se ve. Y el uso y la sensibilidad deberían ir juntos: dentro de cada generación, la
  correlación (Spearman) entre el uso y la sensibilidad de cada agente, más alta con las móviles que con las fijas.
- **Controles:**
  - Las 5 fijas son byte a byte las publicadas (los 5 SHA-256 de [acercarse 40 sin caminar](#acercarse-sin-caminar)).
  - La manipulación llegó: en la gen 1, el CSV de `main.py` y lo que mide `medir_puerta.py` de cada agente son los de
    las fijas, celda a celda; desde la 2 difieren, y la puerta (`puerta_x`, `puerta_y` de `geometria_*.csv`) cambia de
    lugar en cada generación con las móviles y queda en (100, 140) con las fijas.
  - El seguidor de brújula perfecto sigue llegando: deslizando (la condición desliza), llega a menos de 25 px de la
    puerta en todas las generaciones con las móviles, y en promedio desde al menos la mitad de los arranques que con las
    fijas.
  - Las 15 corridas terminan con `MEDICION inconsistencias=0` (contadas, LEC-017).
- La puerta (el criterio del ítem 5) se informa, sin criterio propio.

**Cómo se corrió.** Primero las 5 fijas y las 5 móviles, a la vez; después las 5 de línea base. La salida, en
`results/medicion_fortalezas_moviles_20261116/` (fuera del repo). El criterio, los controles y las tablas, con un
script de la sesión sobre los CSV, cruzados con `analizar_brujula.py`: dan lo mismo (principal 3 de 5; contra las fijas,
mayor en 4 de 5 y 1,55 veces el promedio).

**Controles.**
- **Las 15 corridas terminaron con `MEDICION inconsistencias=0`** (las 15 líneas contadas). Los logs con evolución dicen
  `PESOS {'FITNESS_ACERCARSE': 40.0, 'FITNESS_EXPLORATION': 0.0, 'FITNESS_ANTI_CIRCLE': 0.0}` y `CROSSOVER_RATE=0.2`
  (10 de 10).
- **Las 5 fijas son byte a byte las publicadas** (5 de 5 SHA-256), y su sensibilidad es la de la tabla publicada.
- **La manipulación llegó.** En la gen 1, el CSV de `main.py` y las 60 filas de agentes de las móviles son los de las
  fijas, en las 5 semillas; en la gen 2 difieren las 5. La puerta tiene 30 lugares distintos por semilla con las móviles
  (en la gen 1, (100, 140)) y uno solo con las fijas.
- **El seguidor de brújula perfecto sigue llegando:** deslizando, a menos de 25 px en 150 de 150 generaciones con las
  móviles, desde el 32,5% de los arranques en promedio (mínimo 3,5%); con las fijas, desde el 51,3%. Pedía al menos la
  mitad (25,7%): cumple. Sin medir por qué llega desde menos arranques.
- **La línea base no aprende:** +0,0007 de sensibilidad en las gens 26-30 (la de la puerta fija daba +0,0005).

<details><summary>SHA-256 de las 10 corridas nuevas (se regeneran con medir_puerta.py desde el commit de esta sesión)</summary>

| Semilla | Móviles, con evolución | Sin evolución (móviles) |
|---|---|---|
| 1 | `890c5d6d5536b0f376ce73cf6e1bcf88fc945e9f2b21de417f91e0587da707c2` | `7f01aa73b02f4fb5b9b1e6cf24ce504d543e17f92f4e1a610684eed5b0ce73d7` |
| 2 | `2efaf6aa7256366d531ca996c10e8893839157555444c1d7dbd52fd01464d88e` | `54526ead9f67586e8222220e9c9d410d9b6c5c7cbe34a8cb8f6f1da9a2e51466` |
| 3 | `5fd564a476731c6ede926dcfc6f65be2838d7bef87c155c001a08d3a9101fb1c` | `49843bc3ec74d8b5afc6af0aed91128bd3f7542a86dd68a1c0d3a0a0cdb918f4` |
| 4 | `702cfc867ebdcb20741ef65095615a7f317e1fc974c5214c1df809e69ff723a2` | `29d675daa87ff162dc370e5d6d447fca789c2de999e69fd2bfc2248b89ca8d00` |
| 5 | `971ed3e97ef86ce0a1183a8bd8a71b421b67aeb46f89111f4ce02ad5034cec66` | `00690daed1a49075971f8a6d7f3282e9b5722aca13a7adb45ed5c99376aff02c` |

</details>

**El criterio** (sensibilidad a la brújula con evolución, gens 26-30, rad/tick):

| Semilla | Fijas | Móviles | Sin evolución (móviles) |
|---|---|---|---|
| 1 | +0,0108 | +0,0123 | +0,0010 |
| 2 | +0,0390 | **+0,0620** | −0,0023 |
| 3 | +0,0202 | **+0,0265** | +0,0034 |
| 4 | +0,0012 | −0,0064 | +0,0015 |
| 5 | +0,0152 | **+0,0398** | −0,0004 |
| **Promedio** | +0,0173 | **+0,0268** (1,55 veces las fijas) | +0,0007 |
| 1. ≥ 0,02, más que la línea base y más que las fijas | | **3 de 5** | |
| Más que las fijas | | 4 de 5 | |
| 2. Manzanas por agente (% de las fijas) | 1,07 | 1,09 (**102%**; 2 de 5 por encima) | 0,31 |

**No pasa:** cumple el 2, pero el 1 da 3 de 5 (pedía 4). Es lo más alto medido en el juego: promedio +0,027 (el 43% del
laboratorio con cruce 0,2, +0,0618), la mitad de los agentes por encima de 0,02 en las 26-30 (51%; con las fijas, 34%),
y sin perder comida. La semilla 1 queda abajo del umbral (+0,012, 12 veces su línea base) y la 4 no aprende (−0,006).

**Cuánto sube, y cuándo** (sensibilidad a la brújula | a la comida | % de agentes con más de 0,02 a la brújula):

| | Gens 1-5 | Gens 11-15 | Gens 16-20 | Gens 21-25 | Gens 26-30 |
|---|---|---|---|---|---|
| Móviles | +0,0005 · −0,0006 · 19% | +0,0058 · +0,0118 · 24% | +0,0154 · +0,0169 · 36% | +0,0218 · +0,0216 · 45% | **+0,0268** · +0,0263 · 51% |
| Fijas | +0,0023 · −0,0006 · 19% | +0,0094 · +0,0059 · 23% | +0,0070 · +0,0065 · 23% | +0,0132 · +0,0091 · 29% | +0,0173 · +0,0100 · 34% |
| Sin evolución (móviles) | +0,0005 · +0,0014 · 19% | −0,0000 · +0,0006 · 18% | +0,0012 · −0,0003 · 17% | +0,0017 · −0,0004 · 20% | +0,0007 · +0,0009 · 19% |

Con las móviles arranca más tarde (en las 11-15, +0,006 contra +0,009) y después sube más rápido, sin estancarse:
+0,0246 en la 26 y +0,0299 en la 30. La sensibilidad a la comida sube a la par (+0,026; con las fijas, +0,010). Sin
medir por qué; una posibilidad es que la red aprenda a girar hacia donde marca un sensor de dirección, cualquiera.

**Por qué** (con evolución; sin evolución, la selección no ve la brújula: −0,02 en los dos tramos):

| | Fijas | Móviles |
|---|---|---|
| Selección: sensibilidad a la brújula ↔ fitness (Spearman, mediana), gens 1-15 / 16-30 | +0,048 / +0,110 | +0,073 / **+0,132** |
| Ídem, a la comida | +0,101 / +0,167 | +0,139 / +0,164 |
| Ídem, el uso (camino a la puerta − al control) | +0,152 / +0,376 | +0,191 / +0,336 |
| Acercarse en el fitness, gens 26-30: promedio · desvío dentro de la generación (mediana) · Spearman con el fitness | 8,1 · 6,7 · +0,66 | 9,0 · 6,3 · +0,61 |
| La comida, ídem | 7,6 · 6,9 · +0,73 | 7,4 · 7,4 · +0,76 |
| Distancia a la puerta al nacer (mediana), gens 26-30 | 544 px | 419 px |

La selección ve la brújula un poco más con las móviles (+0,13 contra +0,11 en las 16-30; el laboratorio, +0,27), y el uso
pesa un poco menos en el fitness (+0,34 contra +0,38): con las fijas, parte de lo que se cobraba acercándose era la ruta.

**La ruta.**
- Uso con evolución menos sin y sensibilidad, gens 26-30, por semilla: la 1, +0,068 y +0,012; la 2, +0,168 y +0,062; la
  3, +0,079 y +0,027; la 4, −0,026 y −0,006; la 5, +0,078 y +0,040. **La semilla 4, la que con las fijas se acercaba sin
  la brújula** (+0,12 de uso con +0,001), con las móviles no se acerca ni gira hacia la brújula: su ruta no sobrevive a
  la puerta que se mueve. Entre las 5 semillas, el uso y la sensibilidad van en el mismo orden (Spearman 0,9; con las
  fijas, 0,5, con el uso sin restar la línea base, porque la de la puerta fija no se corrió en esta sesión).
- **El control fijado marca la semilla 1:** uso +0,068 (≥ 0,05) con sensibilidad +0,012 (< 0,02). No puede ser una ruta
  de memoria (la puerta cambia de lugar), y su sensibilidad es 12 veces la de su línea base: lo más probable es la
  brújula por debajo del umbral, pero no está probado.
- **Por agente, lo esperado no se cumplió:** dentro de cada generación, la correlación entre el uso y la sensibilidad de
  cada agente no sube con las móviles (mediana +0,11 contra +0,13 en las 16-30; la línea base, +0,06). El uso de un
  agente depende también de dónde nace y de qué tiene en el camino.

**La puerta y el juego** (gens 16-30 para la puerta; 26-30 para el resto):

| | Fijas | Móviles | Sin evolución (móviles) |
|---|---|---|---|
| Llegan a < 25 px · golpean ahí · la abren (por semilla) | 167 · 44 · 20 (0, 20, 0, 0, 0) | **277 · 94 · 46** (10, 35, 0, 0, 1) | 48 · 29 · 11 (4, 0, 2, 4, 1) |
| Agentes con la puerta abierta, por generación | 0,40 | **1,20** | 0,28 |
| Criterio del ítem 5 | 1 de 5 | 2 de 5 | — |
| Fitness · manzanas · distancia (px) · edad | 23,0 · 1,07 · 1.327 · 964 | 22,8 · 1,09 · 1.288 · 942 | 20,1 · 0,31 · 327 · 894 |

Con las móviles llegan más a la puerta y la abren más del doble, otra vez sobre todo donde más se aprende la brújula (la
semilla 2: +0,062 y 35 de las 46 aperturas; es la quinta condición con cruce 0,2 en que la semilla con más sensibilidad
es la que más abre). La puerta queda más cerca al nacer (419 px contra 544), pero la cercanía sola suma poco: sin
evolución, a 375 px de mediana, llegan 48 (con la puerta fija, 44).

**Lectura.**
1. **No pasa** (3 de 5), pero es el mejor resultado del juego: la sensibilidad más alta fuera del laboratorio (+0,027,
   1,55 veces las fijas, mayor en 4 de 5 semillas), la mitad de los agentes por encima del umbral, sigue subiendo en la
   30, y sin perder comida (102%).
2. **La ruta no sobrevive:** la semilla 4 se acercaba a la puerta fija sin la brújula y con la puerta que se mueve no se
   acerca. Entre semillas, el uso y la sensibilidad ahora van juntos. Por agente, no se ve.
3. **La selección ve la brújula un poco más** (+0,13 contra +0,11): sacar la ruta no la duplica. Acercarse y la comida
   siguen pesando parejo en el fitness; lo que separa al juego del laboratorio (+0,27) sigue siendo cuánto pesa acercarse
   contra la comida (lectura 2 de [acercarse 40 sin caminar](#acercarse-sin-caminar)).
4. **La puerta se abre más del doble** (46 contra 20; criterio del ítem 5, 2 de 5), con la semilla que más aprende la
   brújula poniendo la mayoría.

**Qué sugiere** (para decidir):
- **El switch queda apagado por defecto hasta que lo decida Fer.** Prenderlo cambia todas las corridas y deja atrás las
  de referencia, como deslizar. A favor: es lo que pide el ítem 7 del BACKLOG ("aprender reglas, no un mapa"), saca la
  ruta, y con los pesos de acercarse 40 sin caminar da lo mejor medido en el juego.
- **Lo siguiente para la brújula, con las móviles:** acercarse más pesado que la comida (80, sin lo que paga caminar; ya
  en [mejoras futuras](../product/mejoras_futuras.md#aparecido-en-el-laboratorio-de-la-brújula--2026-11-16)), contra
  esta tanda: sin la ruta, lo que suba acercarse solo se cobra con la brújula. 5 corridas, unos 15 min.
- **O más generaciones:** con las móviles la sensibilidad sigue subiendo en la 30; 60 generaciones dirían si llega al
  umbral en 4 de 5. Más de 1 h.
- **DIAG-33 y DIAG-34**, a mejoras futuras: arreglarlos cambia las corridas donde pasan, así que van con su propio control.
