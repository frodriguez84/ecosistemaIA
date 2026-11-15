# Spec: Modo guiado y modo autónomo

**Estado:** 🟢 Activo — Parcial: bloque A ✅ (2026-11-14); bloques B y C pendientes
**Prioridad:** Alta — es el rumbo del proyecto: que los agentes aprendan de verdad y medir ese
aprendizaje. Hoy no se sabe si aprenden a comer (puede ser la guía escrita a mano), y el puzzle no lo
pueden aprender: no lo ven ni lo pueden accionar.
**Gate:** Ninguno
**Bloquea:** jugar con los parámetros de `config.py` (lo que Fer quiere hacer después) y las ideas de
[mejoras futuras](../../product/mejoras_futuras.md) que suman mecánicas.
**Depende de:** [Medir antes de tocar](../done/MEDIR_ANTES_DE_TOCAR.md) (semilla, CSV, `experimento.py`) ·
[Limpieza sin cambiar comportamiento](../done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) ·
[diagnóstico inicial](../../qa/AnalisisQA.md#diagnostico-inicial): DIAG-01 a DIAG-05, DIAG-08 a DIAG-13,
DIAG-28 y DIAG-29

---

## Problema

- **No se sabe si aprenden a comer.** La evolución sube más que la línea base en 5 de 5 semillas
  ([experimento](../../qa/AnalisisQA.md#experimento-cinco-semillas)), pero su fitness promedio termina en
  42,6, por encima del umbral de 30 desde el que `decide()` lleva a mano a cada agente hacia la manzana
  más cercana (DIAG-01). Parte de las manzanas pueden ser de la guía.
- **La guía es más grande que la de DIAG-01 (DIAG-28).** En el 2% de los ticks el rumbo se sortea de
  nuevo, para todos y con cualquier fitness: un rumbo al azar cada ~50 ticks. Se suman el temporizador de
  exploración (DIAG-13), un reflejo que anula los giros cuando el agente gira mucho y ruido al girar. Lo
  más probable es que la red maneje poco el rumbo y decida sobre todo si avanza. Cuadra con que lo que
  más cambia con la evolución sea la distancia recorrida (×4,3).
- **El puzzle no se puede aprender.** La red no lo ve (DIAG-02), no lo puede accionar (DIAG-03: todo se
  activa por cercanía) y es colectivo y persistente (DIAG-04): un agente abre la puerta porque otro
  agarró la llave, y lo logrado pasa a la generación siguiente. Con cerebros al azar se llega casi igual
  de lejos.
- **Nadie muere (DIAG-05)** y **`config.py` no manda (DIAG-12):** el consumo, la ganancia por comida, la
  energía, la visión, el radio y la pérdida en el agua están fijos en el código. Cambiar esos valores en
  `config.py` hoy no hace nada.
- **El fitness tiene bugs:** el árbol y la casita nunca cuentan (DIAG-08), el término por obstáculos vale
  siempre 0 (DIAG-09), el sensor de ángulo sale de [0, 1] (DIAG-10), el tope de la penalización por agua
  contradice al README (DIAG-11) y la exploración "para fitness bajo" cuelga del `if` equivocado
  (DIAG-13).
- **Los agentes se ubican contra el mapa viejo (DIAG-29).** Al final de cada generación se ubican y
  después `reset_food()` regenera obstáculos y estanque. Es por qué el reposicionamiento casi nunca mueve
  a nadie (lo que encontró DIAG-27).
- **Sueltos** (del ítem 3 del BACKLOG): en la pantalla final el `→` sale como un cuadrado y el "TOP
  AGENTE" muestra `id(self)`, que cambia entre dos corridas iguales; `popup.py:93` conserva un 50 por
  defecto que nunca se usa; el README lista `logs/` y `checkpoints/`, que no existen. Y la sección
  "¿APRENDIERON?" compara contra la generación 1, que es justo lo que LEC-001 dice que no prueba nada.

## Objetivo

Dos modos con un switch (`MODO` en `config.py`, `--modo` por línea de comando) que difieren **solo en
la conducción escrita a mano**. Mundo, puzzle, sensores, acción de golpear y fitness son los mismos en
los dos. El puzzle pasa a ser por agente y por generación, la red lo ve con una brújula y lo acciona
golpeando.

Con eso, `experimento.py` responde tres preguntas con varias semillas y contra la línea base sin
evolución (LEC-001):
1. ¿El modo autónomo aprende?
2. ¿La guía es la que hace comer?
3. ¿Alguno de los dos aprende el puzzle?

Y los parámetros de `config.py` que hoy se ignoran pasan a mandar, junto con los pesos del fitness,
para jugar con ellos después.

## Qué NO es esta feature

- **No cambia el algoritmo genético:** selección, cruce, mutación e inmigración quedan como están. Lo
  único que pierde es la ubicación de los agentes (decisión 23).
- **No cambia el mapa:** la generación de obstáculos, fortalezas, estanque, comida y pociones queda
  igual. Lo nuevo es que la llave roja y el hacha se sortean en cada generación (decisión 10).
- **No hace que comer cueste** ni cambia el radio de comer (20 px, fijo en el código).
- **No pasa a `config.py` los umbrales de la guía** (30, 65, 40%): quedan en el código, comentados como
  guía.
- **No suma sensores más allá de la brújula:** nada de un par de sensores por objeto, rayos de visión ni
  sensor de obstáculos con dirección. Van a [mejoras futuras](../../product/mejoras_futuras.md).
- **No ajusta parámetros para que aprendan** (decisión 22). Un resultado negativo se registra como
  resultado.
- **No suma enemigos, objetos ni mecánicas nuevas** (ideas de Fer en mejoras futuras).
- **No guarda cerebros ni checkpoints,** no hace gráficos ni pruebas estadísticas formales: el resumen
  sigue siendo promedio, desvío y conteo por semilla.
- **No reescribe el README entero:** pone al día las secciones que describen el agente, el puzzle, el
  fitness, el agua y los modos (DoD, bloque C).

## Decisiones cerradas

### El switch y la guía

| # | Decisión |
|---|----------|
| 1 | **`MODO = "guiado"` o `"autonomo"` en `config.py`; `--modo guiado\|autonomo` lo pisa en la clase**, como los flags de *Medir* (su decisión 1). Por defecto, `"guiado"`: `python main.py` sin flags sigue mostrando agentes que comen y van al puzzle. |
| 2 | **El switch cambia solo la conducción escrita a mano.** Mundo, puzzle por agente, sensores, golpear, fitness y valores de `config.py` son los mismos en los dos modos. Así, guiado contra autónomo mide la guía, y cada modo contra su línea base sin evolución mide el aprendizaje. El mundo de antes de este spec (puzzle colectivo, todo por cercanía) no se conserva: queda en git (`5e73d9c`) y en el experimento de cinco semillas. |
| 3 | **Qué es la guía (solo en el modo guiado),** en `src/agents/advanced_agent.py` de hoy: en `decide()`, la conducción hacia árboles y comida con fitness > 30 (`:167-247`), la de puertas y llaves con fitness > 65 en el 40% de los ticks (`:252-305`), el temporizador de exploración (`:307-316`, con DIAG-13 arreglado: decisión 21), el ruido de ±0,02 sobre las salidas (`:318-322`) y el rumbo al azar del 2% (`:324-329`); en `act()`, el reflejo que anula los giros (`:363-383`) y el ruido al girar (`:392`). |
| 4 | **El cuerpo es común a los dos modos:** velocidad; giro = (derecha − izquierda) × 0,12, reducido × 0,6 si pasa de 0,08 (sin ruido en el autónomo); si se piden los dos giros por encima de 0,3, gana el más fuerte; avanza con > 0,5; colisiones; comer y golpear con > 0,5; consumo de energía y costo de golpear. Los sesgos iniciales de la red (−0,3 en los giros) quedan: son la inicialización, y la evolución los cambia. |
| 5 | **Criterio de "sin guía":** en el modo autónomo, `decide()` devuelve exactamente la salida de la red recortada a [0, 1], y `decide()` + `act()` no consumen azar (ni `random` ni `np.random`). Lo prueba un test (decisión 31). |
| 6 | **La guía se adapta al puzzle nuevo, sin cambiar su intensidad.** Apunta al próximo paso del agente (el mismo objetivo de la brújula, decisión 13), no al estado del mundo. La rama de puertas corre cuando el próximo paso es una puerta; la de llaves, cuando es una llave o el cofre. Mismos umbrales (65), misma probabilidad (0,4), mismos empujes (0,6 y 0,2 en puertas; 0,7 y 0,3 en llaves). Cuando está alineada (\|Δángulo\| < 0,3), además aprieta `golpear = 0,9`, como la rama de comida aprieta `eat = 0,9`. La rama de árboles requiere el hacha del agente, no la de cualquiera, y también aprieta golpear al alinearse. |

### El puzzle por agente

| # | Decisión |
|---|----------|
| 7 | **Cada agente tiene su etapa, de 0 a 5:** 0 nada; 1 tiene la llave roja; 2 abrió la puerta de madera; 3 tiene la llave dorada; 4 abrió la puerta de hierro; 5 abrió el cofre. Y su propio hacha (sí o no). Todo agente nuevo arranca en la etapa 0 y sin hacha, también las élites. |
| 8 | **Cómo se avanza** (distancias y radios, los de hoy): <br>· **Llave roja:** por contacto, con etapa 0 → 1. La llave queda en el mapa para los demás. <br>· **Puerta de madera:** golpeando con etapa 1, a menos de 25 px del centro de la puerta; `DOOR_HITS_TO_OPEN` golpes con `DOOR_HIT_COOLDOWN` entre golpes, contados por agente → 2. <br>· **Llave dorada:** por contacto, con etapa 2 → 3. <br>· **Puerta de hierro:** golpeando con etapa 3; `DOOR_IRON_HITS_TO_OPEN` golpes → 4. <br>· **Cofre:** golpeando con etapa 4, en contacto con el cofre → 5. <br>· **Hacha:** por contacto (30 px); queda en el mapa. <br>· **Árbol y casita:** golpeando con hacha propia, con las condiciones de hoy (umbral de manzanas disponibles, cooldowns por agente, por árbol y global). <br>Cada recompensa (`RED_KEY_REWARD`, `DOOR_OPEN_REWARD`, `GOLD_KEY_REWARD`, `DOOR_IRON_OPEN_REWARD`, `CHEST_REWARD`, `TREE_CUT_REWARD`, `HUT_CUT_REWARD`) es para el agente que dio el paso. |
| 9 | **Una puerta es pared para cada agente hasta que él la abre.** Los demás siguen chocando. Con ventana, la puerta se dibuja abierta si algún agente de la generación la abrió; el dibujo no consume azar. |
| 10 | **Todo se reinicia en cada generación:** puertas y cofre cerrados; llave roja y hacha en una posición nueva, sorteada después de regenerar el mapa; llave dorada en su lugar. Nada del puzzle pasa a la generación siguiente (DIAG-04). |
| 11 | **Abrir el cofre no termina la corrida.** La consola, el popup, la pantalla final y el resumen dicen cuántos agentes lo abrieron y la primera generación en que pasó. Deja de existir la fila parcial del cofre (decisión 9 de *Medir*): todas las filas del CSV son generaciones completas. |

### Sensores y golpear

| # | Decisión |
|---|----------|
| 12 | **11 entradas** (`INPUT_SIZE = 11`), en este orden: 1 energía; 2 distancia a la comida; 3 dirección a la comida; 4 distancia al obstáculo más cercano; 5 x; 6 y; 7 ángulo (decisión 20); **8 etapa del agente / 5** (antes: llaves del mundo); **9 dirección al próximo paso** (antes: puertas del mundo); 10 manzanas disponibles; **11 distancia al próximo paso** (nueva). El ratio de comida sigue siendo el sensor 10, que es el que lee la guía. |
| 13 | **La brújula:** el próximo paso es la llave roja (etapa 0), la puerta de madera (1), la llave dorada (2), la puerta de hierro (3) o el cofre (4). La dirección se calcula como el sensor 3 (ángulo relativo, normalizado a [−1, 1]) y la distancia como el sensor 2 (distancia / `VISION_RANGE`, con tope 1). Con etapa 5, dirección 0 y distancia 1, como cuando no hay comida. El hacha y los árboles no tienen brújula. |
| 14 | **Golpear es la quinta salida** (`OUTPUT_SIZE = 5`). Con golpear > 0,5, el agente golpea ese tick lo que tenga a su alcance (decisión 8) y gasta `HIT_ENERGY_COST` (0,05) de energía extra, golpee algo o no. Golpear siempre acorta la vida. Comer sigue sin costo. |

### Las reglas mandan (DIAG-05, DIAG-08 a DIAG-13)

| # | Decisión |
|---|----------|
| 15 | **Mandan los valores de `config.py`, con los números que declara hoy:** `AGENT_ENERGY` (100, también es el máximo), `AGENT_ENERGY_CONSUMPTION` (0,10 por tick; hoy corre 0,05), `AGENT_ENERGY_GAIN_FOOD` (8; hoy corre 30), `VISION_RANGE` (150), `AGENT_RADIUS` (6; hoy corre 8), `TREE_CUT_REWARD` (15; hoy suma 10). Nuevos: `WATER_ENERGY_LOSS` (0,05, hoy fijo en `src/world/obstacles.py:44`), `WATER_PENALTY_MAX` (10, hoy `penalty_max`) y `HIT_ENERGY_COST` (0,05). La poción cura hasta `AGENT_ENERGY`. Con estos números, la energía alcanza para 1.000 ticks sin comer: nadie muere en las generaciones 1 a 4 (960 ticks) y desde la 5 muere el que no come. La presión crece a medida que las generaciones se alargan. |
| 16 | **Los pesos del fitness pasan a `config.py`,** con los valores de hoy: `FITNESS_FOOD` (10), `FITNESS_EXPLORATION` (10), `FITNESS_EXPLORATION_MAX` (15), `FITNESS_SURVIVAL` (0,010), `FITNESS_SURVIVAL_MAX` (10) y `FITNESS_ANTI_CIRCLE` (18). La forma de la fórmula (raíz de las manzanas, logaritmo de la distancia, tope por tiempo vivido) no cambia. |
| 17 | **DIAG-11:** el tope de la penalización por agua es `WATER_PENALTY_MAX`, y el README se corrige: hoy dice "sin límite". |
| 18 | **DIAG-08:** las recompensas por árbol y casita van a un acumulador que `_calculate_fitness()` suma, como `puzzle_rewards`, con `TREE_CUT_REWARD` y `HUT_CUT_REWARD`. |
| 19 | **DIAG-09:** se sacan `obstacles_avoided`, `obstacle_avoidance_count`, `total_obstacle_encounters`, el término de fitness por obstáculos, `get_obstacle_skill`, la "habilidad de obstáculos" que muestran el popup y la consola, y el comportamiento `obstacle_avoiders` de `LearningMonitor`. Hoy valen siempre 0, así que el fitness no cambia por esto. |
| 20 | **DIAG-10:** el sensor 7 es `(ángulo mod 2π) / 2π`, siempre en [0, 1). |
| 21 | **DIAG-13:** el `else` del temporizador de exploración pasa al `if fitness > 30`, que es lo que dice su comentario: la exploración extra es para fitness ≤ 30. Es guía: corre solo en el modo guiado. |
| 22 | **No se ajustan valores para que aprendan.** Un resultado negativo es un resultado y se registra. Si un bloque muestra que hay que cambiar un valor, se para y se decide con Fer, y queda en la bitácora. **Parada prevista,** después del experimento del bloque A, en las corridas con evolución: si en 3 o más semillas **no muere nadie** en ninguna generación (`vivos` = 60 siempre: no hay presión), o si **mueren todos antes del final** en la mayoría de las generaciones desde la 5 (`ticks` menor que el máximo de esa generación: la generación se corta), se consultan los valores de energía con Fer antes de arrancar el bloque B. |

### Ubicación de agentes y sueltos

| # | Decisión |
|---|----------|
| 23 | **DIAG-29: una sola ubicación por generación, con el mundo ya listo.** Al arrancar, después de crear el mundo; al final de cada generación, después de `reset_food()`. Es una sola función de `main.py` con todos los criterios de hoy juntos: fuera de obstáculos, fortalezas, perímetro y estanque; no encima de otro agente; no a menos de 35 px de una manzana; con al menos una dirección libre. Si no encuentra lugar, recorre la grilla fija de respaldo; si tampoco, usa `(100, 100)` y avisa por consola. El algoritmo genético deja de ubicar: crea los agentes y nada más. Se van `find_safe_position`, `fix_agent_positions` y `_reposicionar_agentes` (`main.py`), y `_posicion_libre`, `_posicion_de_respaldo`, `_choca` y los bucles de posición de `_create_random_population` y `_create_immigrant_agents` (`genetic_algorithm.py`). |
| 24 | **El id del agente es un contador por corrida** (1, 2, 3…), que se reinicia al empezar `_simular` y no consume azar. Lo muestran la pantalla final y los logs. |
| 25 | **Pantalla final.** "¿APRENDIERON?" pasa a llamarse "LA CORRIDA": fitness y manzanas de la generación 1 contra las últimas, y la línea "Si aprendieron se mide contra la línea base: python experimento.py" (LEC-001). Los textos del cofre dicen cuántos agentes lo abrieron y en qué generación pasó la primera vez, o que ningún agente lo abrió. En la pantalla, el `→` pasa a `->`: la fuente por defecto de pygame no tiene el glifo. La consola lo conserva. |
| 26 | **`popup.py:93` sin el 50 por defecto** (`total_agents` siempre viene) y **el README sin `logs/` ni `checkpoints/`**. |

### Cómo se mide

| # | Decisión |
|---|----------|
| 27 | **Línea base propia.** Este spec cambia la simulación a propósito: no hay comparación byte a byte contra lo anterior. El "antes" es el experimento de cinco semillas, que el cierre de la limpieza reprodujo byte a byte en `5e73d9c`: no se vuelve a correr. Cada bloque cierra con su experimento registrado en `AnalisisQA.md`, con su lectura, y el bloque siguiente lo toma como referencia. Dentro de cada bloque siguen valiendo los controles de *Medir*: la misma semilla da el mismo CSV byte a byte, y con ventana el mismo que sin ventana. |
| 28 | **Columnas del CSV al cierre,** en este orden: `semilla, evolucion, modo, generacion, ticks, fitness_prom, fitness_max, fitness_min, fitness_desvio, manzanas_prom, manzanas_max, vivos, edad_prom, distancia_prom, diversidad, arboles_cortados, agentes_llave_roja, agentes_puerta_madera, agentes_llave_dorada, agentes_puerta_hierro, agentes_cofre`. <br>· `edad_prom` (bloque A): ticks vividos en promedio. Con presión de supervivencia, `vivos` al final no alcanza. <br>· `agentes_*` (bloque B): cuántos agentes de la generación llegaron *al menos* a esa etapa. Reemplazan las cinco columnas del estado del mundo, que ya no existe. <br>· `modo` (bloque C): `guiado` o `autonomo`. Ruta por defecto: `results/corrida_s<semilla>_<modo>_<evolucion\|sin_evolucion>.csv`. |
| 29 | **`experimento.py` corre por modo (bloque C):** `--modos` (por defecto `guiado autonomo`) × semillas × {con evolución, sin evolución}. <br>**Resumen por corrida:** lo de hoy (fitness y manzanas por agente: generaciones 1-5, últimas 5 y diferencia), más supervivencia (`edad_prom` de las últimas 5), agentes con llave roja (promedio de las últimas 5), etapa máxima de la corrida y primera generación con cofre. **Por grupo** (modo × evolución): promedio ± desvío entre semillas. <br>**Comparaciones pareadas por semilla,** como "K de N": <br>1. Autónomo con evolución contra sin: ¿subió más en fitness y en manzanas, y tiene más agentes con llave roja en las últimas 5? Es la pregunta 1. <br>2. Guiado con evolución contra sin: lo mismo. <br>3. Autónomo contra guiado, por nivel en las últimas 5 (manzanas y agentes con llave roja), con evolución y sin ella. Con evolución dice cuánto pone la guía a una población que evolucionó; sin evolución, cuánto pone la guía sola. Es la pregunta 2. <br>Un empate no cuenta como "más" (*Medir*). El bloque A suma la supervivencia al resumen; el B adapta el resumen del puzzle a las columnas `agentes_*`; el C suma los modos y las comparaciones. |
| 30 | **Experimentos:** bloques A y B, `experimento.py --semillas 1 2 3 4 5 --generaciones 20` (hasta el bloque C solo existe el guiado): 10 corridas, ~9 min, comparables en largo con el experimento de cinco semillas. Cierre, en el bloque C: `--semillas 1 2 3 4 5 --generaciones 30`, 20 corridas, ~30 min estimados, en segundo plano. La sesión anota el tiempo medido. |
| 31 | **Tests,** cada uno corrido una vez contra el código de antes de su cambio: tiene que fallar (es su control, como la decisión 10 de *Limpieza*). <br>· **A**, `tests/test_reglas.py`: con otro `AGENT_ENERGY_CONSUMPTION`, un tick consume ese valor; comer suma `AGENT_ENERGY_GAIN_FOOD` sin pasar de `AGENT_ENERGY`; el agente usa `AGENT_RADIUS` y `VISION_RANGE`; el agua resta `WATER_ENERGY_LOSS`; la recompensa por árbol sigue después de `_calculate_fitness()` y vale `TREE_CUT_REWARD` (DIAG-08); el sensor 7 queda en [0, 1) después de muchas vueltas (DIAG-10); la penalización por agua se topea en `WATER_PENALTY_MAX` (DIAG-11); con fitness 50 no corre la exploración extra y con 20 sí (DIAG-13); los agentes de la generación 1 tienen ids 1 a 60. <br>· **B**, `tests/test_puzzle.py`: el agente A con llave roja que golpea abre la puerta para él, y el agente B sigue chocando; sin golpear o sin llave no hay golpe; la llave dorada pide etapa 2 y el cofre etapa 4 y golpear; la recompensa es para quien dio el paso; golpear gasta `HIT_ENERGY_COST`; la brújula apunta al paso de cada etapa, y con etapa 5 da 0 y 1; un agente nuevo arranca en etapa 0 y sin hacha; el hacha de un agente no habilita a otro a cortar. <br>· **C**, `tests/test_modos.py`: en autónomo, `decide()` es la salida de la red recortada, y el estado de `random` y de `np.random` es igual antes y después de `decide()` + `act()`; en guiado, un agente con fitness > 65, alineado con su puerta y con la rama activa, aprieta golpear. `test_humo.py` suma corridas `--modo autonomo` (misma semilla, mismo CSV; generación 1 igual con y sin evolución) y `test_resumen.py` cubre los modos y las tres comparaciones. <br>`python -m pytest -q` sigue en menos de 90 s. |

### Bloques

| # | Decisión |
|---|----------|
| 32 | **Tres bloques, una sesión cada uno, en este orden.** Cada uno cierra con su experimento registrado y un commit con la confirmación de Fer. Lleva bitácora. <br>**A — Las reglas mandan:** decisiones 15 a 24 y `edad_prom`. <br>**B — El puzzle por agente:** decisiones 6 a 14 y las columnas `agentes_*`. <br>**C — El switch:** decisiones 1 a 5, `modo` en el CSV, `experimento.py` por modo, decisiones 25 y 26, docs y el experimento de cierre. |

## Criterios de done (DoD)

**Bloque A — Las reglas mandan** (✅ 2026-11-14, sesión 1)
- [x] `AGENT_ENERGY`, `AGENT_ENERGY_CONSUMPTION`, `AGENT_ENERGY_GAIN_FOOD`, `VISION_RANGE`, `AGENT_RADIUS`,
  `TREE_CUT_REWARD`, `WATER_ENERGY_LOSS`, `WATER_PENALTY_MAX` y los pesos del fitness (decisión 16) se
  leen de `config.py`. `grep` en `src/` no encuentra `self.energy -= 0.05`, `self.energy + 30`,
  `self.radius = 8`, `self.vision_range = 150`, `self.fitness += 10`, `penalty_max` ni los
  `*_multiplier` de `_calculate_fitness`, y `obstacles.py` ya no tiene el `"energy_loss": 0.05` del agua.
- [x] DIAG-08, DIAG-09, DIAG-10, DIAG-11 y DIAG-13 arreglados como dicen las decisiones 17 a 21, cada uno
  con su test, que falla contra el código de antes. *(El README de DIAG-11 va con los docs del bloque C.)*
- [x] Los agentes se ubican una vez por generación, después de `reset_food()`, con una sola función; no
  existen `find_safe_position`, `fix_agent_positions`, `_reposicionar_agentes`, `_posicion_libre`,
  `_posicion_de_respaldo` ni `_choca`.
- [x] El id de los agentes es un contador por corrida: en la generación 1 van de 1 a 60.
- [x] El CSV tiene `edad_prom` después de `vivos`, y el resumen de `experimento.py` trae la
  supervivencia (`edad_prom` de las últimas 5), cubierta por `test_resumen.py`. La misma semilla da el
  mismo CSV byte a byte, y con ventana el mismo que sin ventana (2 generaciones).
- [x] Experimento A corrido (5 semillas × 20 generaciones) y registrado en `AnalisisQA.md`, con su
  lectura contra el experimento de cinco semillas. La parada de la decisión 22 está evaluada en la
  bitácora.

**Bloque B — El puzzle por agente**
- [ ] El puzzle es por agente (decisiones 7 a 10): etapa y hacha propias; la puerta, pared para cada uno
  hasta que la abre; todo vuelve a 0 en cada generación.
- [ ] Abrir el cofre no termina la corrida; no hay filas parciales en el CSV.
- [ ] La red tiene 11 entradas y 5 salidas; la brújula sigue la decisión 13; golpear gasta
  `HIT_ENERGY_COST`.
- [ ] La guía apunta al próximo paso del agente y aprieta golpear al alinearse, con sus umbrales,
  probabilidades y empujes de hoy (decisión 6).
- [ ] El CSV tiene las cinco columnas `agentes_*` en lugar de las del estado del mundo; el resumen de
  `experimento.py` usa esas columnas.
- [ ] La consola, el popup, el panel y la pantalla final muestran cuántos agentes llegaron a cada etapa,
  no el estado del mundo.
- [ ] `tests/test_puzzle.py` verde, con su control. Misma semilla, mismo CSV; con ventana, el mismo que
  sin ventana.
- [ ] Mirado con ventana: las puertas se dibujan abiertas cuando algún agente las abrió, la llave roja y el
  hacha quedan en el mapa.
- [ ] Experimento B corrido (5 × 20, guiado) y registrado en `AnalisisQA.md`, con su lectura contra el A.

**Bloque C — El switch**
- [ ] `MODO` en `config.py` (por defecto `"guiado"`) y `--modo guiado|autonomo` en `main.py`, que aparece
  en `--help` en español.
- [ ] En autónomo no corre nada de la guía (decisión 3), y `tests/test_modos.py` prueba la decisión 5.
- [ ] El CSV tiene `modo`, con las columnas en el orden de la decisión 28, y la ruta por defecto incluye
  el modo. En los dos modos, la misma semilla da el mismo CSV, con ventana el mismo que sin ventana, y la
  generación 1 es igual con y sin evolución.
- [ ] `experimento.py --modos ...` corre semillas × modos × {con, sin} y el resumen trae lo de la
  decisión 29, con las tres comparaciones; `tests/test_resumen.py` lo cubre.
- [ ] La pantalla final sigue la decisión 25 (sin `→`, id por contador, "LA CORRIDA", textos del cofre);
  `test_reportes.py` al día. `popup.py` sin el 50 por defecto.
- [ ] Experimento de cierre corrido (5 semillas × 30 generaciones × 2 modos × 2) y registrado en
  `AnalisisQA.md`, con su lectura: qué responde a cada una de las tres preguntas del Objetivo.
- [ ] `python -m pytest -q` verde en menos de 90 s.
- [ ] Docs al día: README (modos, flags, 11 sensores, 5 salidas, puzzle por agente, golpear, fitness con
  sus pesos en `config.py`, agua con tope, energía; sin "aprendizaje puro" para el modo guiado; sin `logs/`
  ni `checkpoints/`), y cada número de esas secciones coincide con `config.py` o con el código.
  `CLAUDE.md`: § Notas (las tres diferencias del README y "`config.py` no manda en todo" dejan de ser
  ciertas), § Lógica de negocio crítica (los dos modos y el puzzle por agente, en pocas líneas) y el árbol
  si cambió. DIAG-01 a DIAG-05, DIAG-08 a DIAG-13, DIAG-28 y DIAG-29 ✅ en `AnalisisQA.md`.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| MODOS-01 | Config manda | Cambiar `AGENT_ENERGY_CONSUMPTION`, `AGENT_ENERGY_GAIN_FOOD` y `AGENT_RADIUS` cambia la corrida; `test_reglas.py` verde |
| MODOS-02 | Números fijos | El `grep` del DoD (bloque A) no encuentra nada |
| MODOS-03 | DIAG-08 | La recompensa por árbol sobrevive a `_calculate_fitness()` y vale `TREE_CUT_REWARD`; el test falla con el código de antes |
| MODOS-04 | DIAG-09 | No existen los contadores de obstáculos ni su habilidad; el fitness de una corrida no cambia por sacarlos (valían 0) |
| MODOS-05 | DIAG-10 | Sensor 7 en [0, 1) después de muchas vueltas |
| MODOS-06 | DIAG-11 | Penalización por agua topeada en `WATER_PENALTY_MAX`; README sin "sin límite" |
| MODOS-07 | DIAG-13 | Exploración extra solo con fitness ≤ 30, solo en guiado |
| MODOS-08 | Ubicación (DIAG-29) | Una función, después de `reset_food()`; las funciones viejas no existen; ningún agente arranca adentro de una fortaleza ni sobre un obstáculo del mapa nuevo |
| MODOS-09 | Id | Generación 1 con ids 1 a 60; dos corridas iguales muestran el mismo TOP AGENTE |
| MODOS-10 | Experimento A | Registrado con lectura; parada de la decisión 22 evaluada |
| MODOS-11 | Puzzle por agente | La puerta abierta por A sigue siendo pared para B; la recompensa es de quien dio el paso |
| MODOS-12 | Golpear | Sin golpear no se abre ni se corta nada; golpear gasta `HIT_ENERGY_COST` |
| MODOS-13 | Reinicio por generación | Agentes nuevos en etapa 0 y sin hacha; llave roja y hacha en posición nueva; puertas y cofre cerrados |
| MODOS-14 | Cofre | Abrirlo no termina la corrida; el CSV no tiene filas parciales |
| MODOS-15 | Brújula | Apunta al paso de cada etapa; con etapa 5, 0 y 1 |
| MODOS-16 | Guía adaptada | Apunta al próximo paso del agente y aprieta golpear al alinearse; umbrales, probabilidad y empujes iguales a hoy |
| MODOS-17 | Pantallas del puzzle | Consola, popup, panel y pantalla final muestran agentes por etapa |
| MODOS-18 | Con ventana, bloque B | Puertas dibujadas abiertas si alguien las abrió; llave y hacha en el mapa; mismo CSV que sin ventana |
| MODOS-19 | Experimento B | Registrado con lectura contra el A |
| MODOS-20 | `--modo` | `--help` lo lista en español; sin flag corre el guiado |
| MODOS-21 | Sin guía | En autónomo, `decide()` es la salida de la red recortada y `decide()` + `act()` no consumen azar |
| MODOS-22 | Reproducible por modo | Misma semilla, mismo CSV en los dos modos; con ventana igual que sin ventana; generación 1 igual con y sin evolución |
| MODOS-23 | CSV final | Columnas y orden de la decisión 28; ruta con el modo |
| MODOS-24 | `experimento.py` por modo | `--semillas 1 2 --generaciones 10` deja 8 CSV, 8 logs y `resumen.md` con las tres comparaciones; los números coinciden con un cálculo a mano |
| MODOS-25 | Pantalla final | "LA CORRIDA" con la línea de LEC-001; sin `→` en pantalla; textos del cofre por agentes |
| MODOS-26 | Sueltos | `popup.py` sin el 50; README sin `logs/` ni `checkpoints/` |
| MODOS-27 | Experimento de cierre | 5 × 30 × 4 corrido y registrado, con la respuesta a las tres preguntas |
| MODOS-28 | `python -m pytest -q` | Verde, en menos de 90 s |
| MODOS-29 | Docs | README, `CLAUDE.md` y los DIAG ✅, como dice el DoD |

## Implementación (pistas, no normativas)

### Comandos

```bash
# Tests
.venv/Scripts/python.exe -m pytest -q

# Experimento de los bloques A y B (solo guiado hasta C; ~9 min, en segundo plano)
.venv/Scripts/python.exe experimento.py --semillas 1 2 3 4 5 --generaciones 20

# Experimento de cierre (bloque C; ~30 min estimados, en segundo plano)
.venv/Scripts/python.exe experimento.py --semillas 1 2 3 4 5 --generaciones 30

# Determinismo y ventana (en cada bloque; con --modo desde el C)
.venv/Scripts/python.exe main.py --sin-ventana --generaciones 2 --semilla 7 --csv "$S/a.csv"
.venv/Scripts/python.exe main.py --sin-ventana --generaciones 2 --semilla 7 --csv "$S/b.csv"
.venv/Scripts/python.exe main.py --generaciones 2 --semilla 7 --csv "$S/v.csv"   # con ventana
cmp "$S/a.csv" "$S/b.csv" && cmp "$S/a.csv" "$S/v.csv"
```

### Por bloque

**A.**
- `config.py`: los valores nuevos (decisiones 15 y 16) junto a los de su sección.
- `src/agents/advanced_agent.py`: `__init__` (radio, visión, energía), `act` (consumo), `_try_eat`
  (ganancia), `_try_heal` (cura hasta `AGENT_ENERGY`), `_try_cut_tree` (acumulador),
  `_calculate_fitness` (pesos, tope del agua, sin término de obstáculos), sensor 7, el `else` de
  `decide`.
- `src/world/obstacles.py:44`: `WATER_ENERGY_LOSS`.
- `main.py`: la función de ubicación, llamada después de `World(...)` y después de `reset_food()`; sale
  la ubicación de antes de `reset_food()`; `edad_prom` en `_fila_csv` y `COLUMNAS_CSV`; el contador de ids
  se reinicia al empezar `_simular`; sale `avg_obstacle_skill` de `_datos_del_popup`.
- `src/evolution/genetic_algorithm.py`: los agentes se crean sin buscar posición (por ejemplo, en
  `(0, 0)` hasta que `main.py` los ubica).
- `src/analytics/learning_monitor.py`: sale `obstacle_avoiders`. Revisar si `clustering.py` usa algo de
  lo que sale.
- `tests/test_reglas.py`; `test_humo.py` y `test_resumen.py` con el encabezado nuevo.

**B.**
- `src/agents/advanced_agent.py`: etapa, hacha y golpes por puerta del agente; brújula
  (`perceive`); golpear en `act` (costo) y en los `_try_*`; colisión con puertas según la etapa del
  agente (hoy `_check_door_collision` y el bloque repetido de `act`, `:418-424`); la guía adaptada.
- `src/world/world.py`: `check_key_pickup`, `process_door_hit`, `check_chest_open`,
  `check_axe_pickup`, `process_tree_hit`, `process_hut_hit` y `update_tree_cutting_status` pasan a
  recibir al agente (o su estado) en lugar de cambiar el estado global; `reset_food()` reinicia el
  puzzle entero y sortea llave roja y hacha después de regenerar el mapa. `Door.is_open` queda solo para
  el dibujo ("algún agente la abrió").
- `main.py`: los `_try_*` dependen de golpear; sale la salida por el cofre; `_fila_csv`,
  `_imprimir_fin_de_generacion` y `_datos_del_popup` cuentan agentes por etapa.
- `src/ui/stats.py`, `popup.py`, `pantalla_final.py`: agentes por etapa.
- `experimento.py`: `COLUMNAS_PUZZLE` y el resumen del puzzle (decisión 29).
- `config.py`: `INPUT_SIZE = 11`, `OUTPUT_SIZE = 5`, `HIT_ENERGY_COST`.

**C.**
- `config.py`: `MODO`. `main.py`: `--modo`, columna `modo`, ruta del CSV.
- `src/agents/advanced_agent.py`: `decide()` y `act()` consultan el modo; en autónomo no corre nada de
  la decisión 3.
- `experimento.py`: `--modos`, grupos por modo y las tres comparaciones.
- `src/ui/pantalla_final.py` (decisión 25), `src/ui/popup.py` (decisión 26), README, `CLAUDE.md`.

### Trampas conocidas

- **CRLF:** `main.py`, `config.py`, `advanced_agent.py`, `world.py`, `obstacles.py`,
  `genetic_algorithm.py`, `learning_monitor.py`, `popup.py`, `stats.py`, `renderer.py` y `README.md` son
  CRLF. Después de editar, revisar `git diff` por líneas en blanco vaciadas (LEC-002), contar los
  finales de línea con Python (LEC-003) y nunca `sed -i` (LEC-005). `experimento.py`,
  `pantalla_final.py` y los tests son LF.
- **`config.py` se pisa en la clase,** no en una instancia (*Medir*, Implementación): la pantalla final y
  varias funciones leen `SimulationConfig` directo. Los tests que cambian un valor lo devuelven al
  terminar (`monkeypatch.setattr`).
- **Un test de "config manda" tiene que cambiar el valor** a uno distinto del fijo de hoy. `VISION_RANGE`
  (150) y `AGENT_ENERGY` (100) coinciden con los números del código: un test que solo compara contra el
  valor de `config.py` pasa también con el código viejo, y su control no controla nada.
- **Con presión de supervivencia, una generación puede terminar antes** (todos muertos): `ticks` lo
  muestra, y la parada de la decisión 22 lo vigila.
- **Las corridas con evolución tardan más** que las de la línea base (los agentes caminan y comen más):
  el experimento tarda lo que tarda la corrida más lenta.
- **La salida redirigida sale con buffer:** para leer un log mientras corre, `python -u` (así lanza las
  corridas `experimento.py`).
- **Los checkers de `/qa-spec` no pueden correr `main.py`:** lo que pida corridas se vuelve a correr
  fresco en la sesión, y cada `archivo:línea` citado se imprime antes de copiarlo (LEC-006).

## Edge cases

- **Toda la población muere antes del final:** la generación termina, como hoy; `ticks` y `edad_prom` lo
  muestran.
- **Ningún agente llega a la llave roja:** las columnas `agentes_*` valen 0, y en las comparaciones el
  empate no cuenta como "más".
- **Varios agentes golpean la misma puerta en el mismo tick:** cada uno cuenta sus golpes; la puerta se
  dibuja abierta en cuanto la abre el primero.
- **Un agente con hacha y más manzanas que el umbral:** golpear no corta nada, y paga el costo.
- **Etapa 5:** la brújula da 0 y 1; el agente sigue comiendo y explorando hasta el final de la
  generación.
- **Con ventana y `--modo autonomo`:** igual que sin ventana, con la misma semilla.
- **Una corrida falla en el experimento:** el resumen se arma con las que terminaron y lista las que no,
  con su log (*Medir*).

## Esfuerzo

Tres sesiones en secuencia, una por bloque (decisión 32). El B es el más grande (siete funciones de
`world.py`, el agente, las tres pantallas, el CSV y el resumen): si no entra en una sesión, se corta
donde quede verde y la bitácora dice qué falta. El cierre (`/close-spec`) entra en la sesión del bloque
C si alcanza el contexto; si no, una cuarta sesión.

## Relación con otros specs

- **[Medir antes de tocar](../done/MEDIR_ANTES_DE_TOCAR.md):** cambian sus decisiones 6 (columnas), 7 (el
  puzzle deja de ser estado del mundo), 8 (la ruta suma el modo), 9 (sin fila parcial del cofre) y 13 (la
  etapa del puzzle del resumen). El resto queda: semilla, CSV byte a byte, flags, comparación pareada.
- **[Limpieza sin cambiar comportamiento](../done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md):** lo que dejó
  para el ítem 3 en su "Qué NO es" se resuelve acá. "¿APRENDIERON?" (decisión 25). Juntar
  `find_safe_position` con el reposicionamiento y la segunda llamada a `fix_agent_positions` (decisión
  23: se van todas).

## Bitácora de ejecución

Formato: [`docs/AGENTES.md`](../../AGENTES.md) § "Specs de varias sesiones".

### Sesión 0 — 2026-11-14 — Autoría
- **Hecho:** spec escrito con Fer, que eligió todas las recomendaciones: el switch cambia solo la guía;
  el puzzle es por agente y se reinicia en cada generación; brújula al próximo paso; golpear con costo de
  energía; `config.py` manda con los números que declara; pesos del fitness a `config.py`; un spec con
  tres bloques. Registrados DIAG-28 (la guía escondida) y DIAG-29 (la ubicación contra el mapa viejo) en
  `AnalisisQA.md`, y lo que quedó afuera en `mejoras_futuras.md`. Commit:
  `docs: spec del modo guiado y modo autónomo`.
- **Estados:** spec en `planned/`, sin código. DoD y QA sin empezar.
- **Desvíos del spec, y por qué:** ninguno. Dos detalles los decidió la sesión sin consultar, y Fer
  puede cambiarlos antes del bloque C: el modo por defecto es `"guiado"` (decisión 1) y los nombres
  nuevos de `config.py` van en inglés, como el resto del archivo, salvo `MODO`.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión:** bloque A (decisión 32).
  - **Primer paso:** `git mv` del spec a `active/`, con el manifiesto (`docs/specs/README.md`) y el link
    del ítem 3 del BACKLOG al día. Después, `tests/test_reglas.py` (decisión 31, bloque A) contra el
    código de hoy: cada test tiene que fallar.
  - **Después, en orden:** `config.py` (decisiones 15 y 16); el agente (DIAG-05, DIAG-08 a DIAG-13);
    `obstacles.py`; la ubicación única y el contador de ids (decisiones 23 y 24); `edad_prom` en el CSV
    y la supervivencia en el resumen; el `grep` del DoD; el determinismo con ventana y sin ella; el
    experimento A en segundo plano, registrado en `AnalisisQA.md` con su lectura contra el experimento
    de cinco semillas; la parada de la decisión 22, evaluada en la entrada de la bitácora.
  - **Trampa:** los tests de "config manda" cambian el valor (Trampas conocidas).
  - **Trampa:** casi todo lo que toca el bloque A es CRLF (LEC-002, LEC-003, LEC-005).

### Sesión 1 — 2026-11-14 — Bloque A
- **Hecho:** spec movido a `active/`, con el manifiesto, el BACKLOG y los links de mejoras futuras al
  día. Primero `tests/test_reglas.py`, contra el código de antes: los 10 tests de la decisión 31
  fallaron, todos por su aserción. Después: `config.py` con `WATER_PENALTY_MAX`, `WATER_ENERGY_LOSS` y
  los pesos `FITNESS_*`; el agente lee de `config.py` energía, consumo, comida, radio, visión y
  recompensas por cortar, que van a `cut_rewards` (DIAG-08); DIAG-09, DIAG-10, DIAG-11 y DIAG-13;
  `obstacles.py` con `WATER_ENERGY_LOSS`; `_ubicar_agentes` en `main.py`, llamada después de
  `World(...)` y después de `reset_food()`, y el genético crea los agentes en (0, 0) sin ubicarlos;
  ids por contador (`AdvancedAgent.reiniciar_ids()` al empezar `_simular`); `edad_prom` en el CSV y
  `supervivencia` en el resumen de `experimento.py` (`test_resumen.py`, que falló antes del cambio).
  Experimento A registrado en [AnalisisQA § experimento del bloque A](../../qa/AnalisisQA.md#experimento-modos-a),
  DIAG-30 registrado y LEC-007 escrita. Commit: `modos: las reglas mandan, ubicación única e ids por
  contador (bloque A)`.
- **Estados:** DoD del bloque A completo. DIAG-05, DIAG-08, DIAG-09, DIAG-10, DIAG-12, DIAG-13 y
  DIAG-29 ✅; DIAG-11 a medias (falta el README, bloque C). `python -m pytest -q`: 28 passed en 19 s.
  Determinismo: semilla 7, 2 generaciones, el mismo CSV dos veces sin ventana y una con ventana.
  Experimento A: 370 s (10 corridas a la vez; la semilla 1 sin evolución terminó en la generación 6,
  con el cofre).
- **Parada de la decisión 22: no se dispara.** Con evolución, ninguna semilla corrió sin muertes (hay
  muertes en 17 o 18 de las 20 generaciones de cada una), y las generaciones cortadas desde la 5 son 4
  de 80, ninguna semilla con la mayoría. Los valores de energía quedan. La presión es fuerte: desde la
  generación 5 quedan vivos entre 0 y 16 de 60, y las cortadas aparecen desde la 17 (1.680 ticks).
- **Desvíos del spec, y por qué:**
  - Un test más que los de la decisión 31: `test_no_quedan_los_contadores_de_obstaculos` (DIAG-09),
    porque el DoD pide un test por DIAG. Su control corrió contra `22caa39` en un worktree aparte: los
    11 tests fallan ahí.
  - La ubicación mide estanque y perímetro con una caja centrada en el agente, no con la del genético
    (`collides_with(x, y, 35, 35)`, que solo mira hacia abajo y a la derecha): con la heredada, 10 de
    1.260 agentes arrancaban con medio cuerpo en el agua. Es más estricta que la de antes, en la
    dirección de "fuera del estanque" de la decisión 23. El movimiento usa la misma caja corrida:
    DIAG-30, a mejoras futuras (cambiarlo cambia la simulación).
  - La grilla de respaldo de la ubicación aplica todos los criterios (antes, solo el estanque). No
    corrió en ninguna verificación.
- **A medias o bloqueado:** nada del bloque A. El README de DIAG-11 queda para los docs del bloque C,
  como dice su DoD.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión:** bloque B (decisión 32).
  - **Primer paso:** `tests/test_puzzle.py` (decisión 31, bloque B) contra el código de hoy. Los tests
    de comportamiento tienen que fallar por su aserción: la puerta que abre A sigue frenando a B, sin
    golpear no se abre nada, la recompensa es de quien dio el paso. Los que usan algo que todavía no
    existe (la etapa, golpear, la brújula) fallan por `AttributeError` o `KeyError`: se anota cuáles.
  - **Después, en orden:** `config.py` (`INPUT_SIZE = 11`, `OUTPUT_SIZE = 5`, `HIT_ENERGY_COST`);
    etapa, hacha y golpes por puerta en el agente; las siete funciones de `world.py` reciben al agente,
    y `reset_food()` reinicia el puzzle y sortea llave roja y hacha después de regenerar el mapa; la
    puerta, pared para cada agente según su etapa; brújula (sensores 8, 9 y 11); golpear (quinta
    salida, `HIT_ENERGY_COST`); la guía adaptada (decisión 6); `main.py` (los `_try_*` dependen de
    golpear, sale la salida por el cofre, columnas `agentes_*`); consola, popup, panel y pantalla
    final; el resumen del puzzle en `experimento.py`; determinismo con ventana y sin ella; mirarlo con
    ventana (MODOS-18); el experimento B en segundo plano, registrado contra el A.
  - **Trampa:** `tests/test_reglas.py` llama a `decide()` y `perceive()` reales con un mundo de mentira
    (`_mundo()`) sin llaves, puertas ni cofre, y `QUIETO` tiene 4 salidas. Con la brújula y golpear,
    hay que sumarle al `_mundo()` lo que lea la brújula y a `QUIETO` la quinta salida, y los 11 tienen
    que seguir verdes.
  - **Trampa:** la llave roja hoy la genera el loop de `main.py` (`world._generate_red_key(generation)`
    cuando no hay llave), no `reset_food()`. Con la decisión 10 se sortea en `reset_food()`, y como
    queda en el mapa para los demás (decisión 8), recogerla ya no la saca.
  - **Trampa:** `tests/test_reportes.py` arma un mundo con `red_key_collected` y puertas abiertas para
    la pantalla final; con agentes por etapa (MODOS-17), cambia.
  - **Trampa:** CRLF en casi todo lo que toca el bloque. Las ediciones por script, como en esta sesión:
    texto viejo único, finales de línea conservados y las líneas que no cambian devueltas tal cual
    (LEC-005, LEC-007).
