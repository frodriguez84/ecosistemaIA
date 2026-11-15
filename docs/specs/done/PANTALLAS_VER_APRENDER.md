# Spec: Pantallas para ver aprender

**Estado:** ✅ Implementado (2026-11-15)
**Prioridad:** Alta — es el ítem 4 del [BACKLOG](../../product/BACKLOG.md). Fer decidió hacerlo antes
que el puzzle aprendible (ítem 5), para que lo que sigue se disfrute mirando: lo que más le gusta es
mirar cómo aprenden.
**Gate:** Ninguno
**Bloquea:** nada. Conviene antes del ítem 5: el embudo del puzzle y los avisos de hito son la forma
de ver si el puzzle empieza a aprenderse.
**Depende de:** [Modo guiado y modo autónomo](../done/MODO_GUIADO_Y_AUTONOMO.md) (puzzle por agente,
`agentes_por_paso`, columnas del CSV) · [Medir antes de tocar](../done/MEDIR_ANTES_DE_TOCAR.md) (semilla,
mismo CSV byte a byte) · DIAG-32 en [AnalisisQA](../../qa/AnalisisQA.md) ·
[maqueta](https://claude.ai/artifact/SvXK3fB1Yv8zpSB3HBXE5Z) con datos reales (semilla 1, 30
generaciones, los dos modos), aprobada por Fer el 2026-11-15

---

## Problema

- **El popup de cada generación tapa el mundo.** Al terminar cada generación aparece un cuadro de
  800×600 (`src/ui/popup.py`) que queda abierto hasta hacer clic en "Cerrar", mientras la generación
  siguiente ya corre: dice "Generación 2 completada" con el panel en la 3. Tiene dos datos que valen
  siempre 0 ("Exploración: 0 m" y "Tiempo gen: 0.0s", DIAG-32) y un gráfico con la escala fija de 0 a
  100, aunque el fitness promedio no pasa de 40.
- **El panel no muestra la evolución.** Son seis renglones de texto, más los del puzzle cuando alguien
  llegó a un paso, en un recuadro de 300 px (`src/ui/stats.py`); el resto de la columna derecha queda
  vacía. Para ver si la población mejora hay
  que esperar el popup.
- **La pantalla final es una pared de texto** (`src/ui/pantalla_final.py`). Dice cuatro veces que no
  se abrió el cofre (subtítulo, "Resultado: No logrado", "El cofre no se abrió en ninguna generación" y
  el mensaje final), compara la generación 1 contra las últimas 3, muestra un "sello de movimiento"
  (`metric_sr` ≥ 0,5) que no explica nada, corre K-Means sobre la última generación y escribe `->`
  porque la fuente por defecto de pygame no tiene la `→`.
- **Lo más lindo de mirar no está:** por dónde caminan, hasta qué paso del puzzle llegan y cuándo
  pasó cada cosa por primera vez.
- **Las corridas sin ventana no guardan el mejor agente:** su resumen por consola solo dice el fitness
  máximo de la última generación.

## Objetivo

Ver aprender, mientras corre y al final, sin que nada tape el mundo, sin números que mientan y **sin
cambiar la simulación**: con la misma semilla, el mismo CSV byte a byte que antes de este spec, con
ventana y sin ella.

- **Durante la corrida:** el panel derecho con un gráfico en vivo (fitness promedio y máximo, y
  manzanas por agente, por generación terminada, con escala automática), un aviso corto arriba del
  mundo al cambiar de generación y un aviso la primera vez que pasa cada paso del puzzle.
- **Al final:** una sola pantalla, como boletín: cuatro números grandes, los gráficos con los hitos
  marcados, el mapa de calor de por dónde caminaron (generación 1 contra la última), el puzzle como
  embudo, el mejor agente de la corrida y el cofre una sola vez. Sin ventana, el mismo boletín en
  texto por consola.

La maqueta es la referencia visual (distribución, colores, tamaños). Donde difiere de este spec, manda
el spec: la tarjeta del mejor agente (decisión 6), las notas de edad y recorrido (decisión 14) y las
marcas de hitos en el gráfico (decisión 14).

## Qué NO es esta feature

- **No cambia la simulación:** reglas, fitness, sensores, algoritmo genético, mapa y azar quedan
  igual. El CSV tiene las mismas columnas y los mismos valores.
- **No escribe archivos nuevos:** el mapa de calor, los hitos y el mejor agente viven en memoria. Sin
  ventana, lo que queda es el log (el boletín por consola). Nada nuevo en `results/`, nada en el CSV.
- **No cambia `experimento.py`** ni su `resumen.md`.
- **No cambia el reporte por consola de cada generación** (fitness, comida, supervivencia, diversidad,
  puzzle), ni el clustering de cada 3 generaciones, ni los análisis de cada 5 y 10. El clustering sale
  de la pantalla final y queda donde ya está en la consola.
- **No muestra la pantalla final si la corrida se corta** con ESC o cerrando la ventana: como hoy.
- **No toca el dibujo del mundo:** pasto, obstáculos, agentes, tumbas y partículas quedan igual. Los
  rótulos de respaldo de `src/world/obstacles.py` (la "K" y la "C" cuando falta un sprite) siguen con la
  fuente de pygame. El "mapa más natural" es el ítem 7 del BACKLOG.
- **No hace pantallas interactivas:** sin clics, pestañas ni desplazamiento. La pantalla final se
  cierra con ESC o ENTER, como hoy.
- **No guarda capturas** ni exporta el boletín a imagen.

## Decisiones cerradas

### Qué sale y qué no cambia

| # | Decisión |
|---|----------|
| 1 | **Sale el popup de cada generación:** `src/ui/popup.py` entero, `SummaryPopup` (también de `src/ui/__init__.py`), `_datos_del_popup` y `fitness_history` de `main.py`, y el manejo del clic (`MOUSEBUTTONDOWN`). Sale lo que solo usaba el popup: `get_movement_skill`, `get_food_skill` y `get_energy_skill` (`src/agents/advanced_agent.py:819-838`), si `grep` confirma que nadie más los llama. DIAG-32 se resuelve sacándolo. |
| 2 | **Sale la pantalla final de hoy:** `textos_del_cuadro`, `_dibujar_cuadro`, `_grafico_de_fitness`, `_renglones_de_clustering` y las secciones OBJETIVO, PASOS CLAVE, LA CORRIDA, LÍNEA DE TIEMPO, TOP AGENTE, MOVIMIENTO y CLUSTERING. La reemplaza el boletín (decisiones 14 y 15). |
| 3 | **No cambia la simulación.** Con la misma semilla, el mismo CSV byte a byte que antes del spec, con ventana y sin ella, en los dos modos y con evolución y sin ella. Nada de lo nuevo consume azar (`random` ni `np.random`): contar posiciones, mirar hitos, guardar el mejor agente, armar el boletín, dibujar y los avisos. `COLUMNAS_CSV` y `_fila_csv` no cambian. |

### Los datos de la corrida

| # | Decisión |
|---|----------|
| 4 | **Un registro de la corrida, en memoria,** que alimenta `main.py` y del que leen las pantallas y la consola. Guarda: por cada generación terminada, **la fila del CSV tal cual** (por columna) más los ticks máximos de esa generación (`_ticks_de_generacion`); los hitos (decisión 5); el mejor agente (decisión 6) y el mapa de calor (decisión 7). Lo que muestran las pantallas son los números del CSV: el promedio de fitness del gráfico es `fitness_prom`, no una cuenta aparte. La primera generación en que pasó cada paso del puzzle es la primera fila con su columna `agentes_*` mayor que 0. Se alimenta igual con ventana y sin ella: un solo camino. `primera_generacion_cofre` y `agentes_con_cofre` salen de `main.py`: se derivan de la historia (la suma de `agentes_cofre` es la cantidad de agentes que abrieron el cofre en la corrida, porque cada agente lo abre una sola vez). |
| 5 | **Hitos: los cinco pasos del puzzle.** Un hito es la primera vez en la corrida que un agente llega a ese paso (su etapa llega a 1, 2, 3, 4 o 5). Se mira en cada tick, después de que actúan los agentes, y guarda generación, tick y id del agente. Si en un mismo tick pasan dos, se registran los dos, en el orden del puzzle. Cada hito imprime una línea en la consola, con ventana y sin ella, que generaliza la del cofre de hoy: `🏆 ¡Primera llave roja! Agente 12, generación 2, segundo 8.3`. Con ventana, además, un aviso (decisión 12). La generación de cada hito coincide con la primera fila del CSV con esa columna `agentes_*` mayor que 0. |
| 6 | **El mejor agente es el de la corrida,** no el de la última generación: el récord. Al terminar cada generación, con el fitness ya calculado (el mismo de la fila del CSV), el de más fitness de la generación reemplaza al récord solo si lo supera (un empate deja el anterior). Guarda id, generación, fitness, manzanas, recorrido (px), ticks vividos y etapa del puzzle. Su fitness es el máximo de `fitness_max` del CSV (a 4 decimales). |
| 7 | **Mapa de calor.** Grilla de celdas de `HEATMAP_CELL_SIZE` = 16 px (nuevo en `config.py`) sobre el área de juego de 960×800: 60×50 = 3.000 celdas. Después de cada tick simulado (después de `world.update()` y `tick += 1`), cada agente vivo suma 1 en la celda de su posición (`int(x) // 16`, `int(y) // 16`, recortado a la grilla). En pausa no se cuenta: el tick no avanza. Al terminar una generación se guarda su grilla si es la 1, queda como "la última" y se arranca una nueva en cero. Se guardan dos grillas, la de la generación 1 y la de la última, más la que está en curso. **Valor de una celda:** cuenta / ticks de su generación, es decir, cuántos agentes hubo en promedio en esa celda por tick; así se comparan generaciones de largos distintos. **Cobertura:** celdas con cuenta mayor que 0 / 3.000, en %. <br>**Costo** (medido al escribir el spec, 2026-11-15, esta máquina): contar 60 agentes en una lista de listas lleva ~16 µs por tick; un tick sin ventana lleva ~7,1 ms (semilla 1: 7,7 s una generación, 14,5 s dos). Es ~0,2 % del tiempo. Memoria: 3.000 enteros por grilla (12 KB como `int32`; ~30 KB como lista de listas), tres grillas: menos de 100 KB. El bloque A lo vuelve a medir y lo anota en la bitácora; si pasa del 1 % del tick, se para y se decide con Fer. |
| 8 | **Formato de los números del boletín y de las pantallas:** coma decimal y punto de miles (`31,2`, `2.220`), signos `+` y `−` (U+2212), porcentaje con espacio (`+73 %`), veces con `×` (`×1,9`). Lo usa también el boletín por consola. El reporte de consola de cada generación conserva su formato. |

### Durante la corrida (con ventana)

| # | Decisión |
|---|----------|
| 9 | **El panel derecho ocupa la columna entera** (x de 960 a 1200, los 800 px de alto), como la maqueta ("Durante la simulación"): <br>· título; <br>· datos: Generación *N de M* (M = generaciones de la corrida), Modo, Tiempo (mm:ss de la generación), Vivos, Muertos, Comida; <br>· **gráfico de fitness:** promedio y máximo por generación terminada, con leyenda y el último valor de cada serie rotulado; <br>· **gráfico de manzanas por agente**, igual; <br>· **puzzle:** "Esta generación:" con agentes con hacha y cada paso con alguien (lo de hoy), o "nadie todavía"; y la generación anterior: hasta qué paso llegaron y cuántos ("Gen 11: 2 agentes con llave roja"), o que nadie agarró la llave roja; <br>· abajo, las teclas: ESPACIO pausa, + − zoom, ESC salir. <br>Antes de que termine la generación 1, en el lugar de los gráficos: "Se dibuja al terminar la generación 1". El eje X tiene todas las generaciones terminadas a lo ancho, rotuladas G1 y G*n*. |
| 10 | **Escala automática** (la misma función para el panel y la pantalla final). Rango [*lo*, *hi*] con *lo* = mín(0, mínimo de las series) e *hi* = máx(0, máximo de las series); las series de un mismo gráfico comparten eje. El paso es el número más chico de la forma {1; 2; 2,5; 5} × 10ᵏ tal que ⌈*hi*/paso⌉ − ⌊*lo*/paso⌋ ≤ 5; el eje va de ⌊*lo*/paso⌋ × paso a ⌈*hi*/paso⌉ × paso. Si todo vale 0, el eje va de 0 a 1. Ejemplos (con *lo* = 0): máximo 75,1 → paso 20, tope 80; 39,7 → 10, 40; 66,0 → 20, 80; 1,42 → 0,5, 1,5; 0,94 → 0,2, 1,0; 100,5 → 25, 125. Nunca la escala fija de 0 a 100. |
| 11 | **Aviso de fin de generación,** arriba y al centro del mundo, de 440 px de ancho, semitransparente, durante 2,5 s, con una barra fina que muestra el tiempo que le queda: "Generación 11 terminada" y "Fitness promedio 31,2 +1,1 · Manzanas por agente 1,10 +0,18". La diferencia es contra la generación anterior, en verde si sube y en naranja si baja; la generación 1 va sin diferencias. Después de la última generación no hay aviso: aparece la pantalla final. |
| 12 | **Aviso de hito,** debajo del de fin de generación, en dorado, con el sprite del paso (32 px), durante 4 s: <br>· llave roja: "¡Primera llave roja!" / "Un agente la agarró en la generación N"; <br>· puerta de madera: "¡Primera puerta abierta!" / "Un agente abrió la de madera en la generación N"; <br>· llave dorada: "¡Primera llave dorada!" / "Un agente la agarró en la generación N"; <br>· puerta de hierro: "¡Puerta de hierro abierta!" / "Un agente la abrió en la generación N"; <br>· cofre: "¡Cofre abierto!" / "Un agente lo abrió en la generación N". <br>Se apilan hacia abajo, el más nuevo último; si hay más de 3 a la vez, se va el más viejo. **Los avisos no toman clics ni teclas y no frenan nada.** Duran tiempo de reloj (`pygame.time.get_ticks`), también en pausa. Las duraciones son constantes con nombre en el módulo de los avisos, como las medidas de pantalla, no parámetros de `config.py`: no cambian la simulación. |
| 13 | **Fuentes:** Pixelify Sans para los títulos e Inter para el resto, las dos con licencia OFL, en archivos TTF **estáticos** en `assets/fonts/` (pygame 2.6 no elige el peso de una fuente variable): Pixelify Sans Bold; Inter Regular, SemiBold y Bold. Con el `OFL.txt` de cada familia y un `LEEME.md` que dice de dónde salió cada archivo y su versión. El README dice que las fuentes de `assets/fonts/` son OFL (el código es MIT). Los textos del panel, de los avisos, de la pantalla final y el "PAUSADO" usan esas fuentes: ningún texto de pantalla usa `pygame.font.Font(None, …)`, salvo los rótulos de respaldo de `obstacles.py`. Si falta un TTF, `main.py` con ventana se corta al arrancar con el nombre del archivo: no cae a la fuente de pygame, que mostraría cuadrados. |

### Al final

| # | Decisión |
|---|----------|
| 14 | **Una sola pantalla final, como boletín,** sobre el último cuadro del mundo oscurecido, hasta ESC o ENTER (como hoy). En este orden (ver Wireframes): <br>**a. Encabezado.** "Corrida terminada"; debajo, "Modo guiado · con evolución · semilla 1 · 30 generaciones · 9,6 min simulados" (en la línea base, "sin evolución (línea base)"). A la derecha, "Hasta dónde llegaron:" y el paso más lejano de la corrida ("llave roja"; "nadie agarró la llave roja" si nadie), seguido de **la única frase sobre el cofre:** "el cofre no se abrió", o "el cofre se abrió por primera vez en la generación X; lo abrieron N agentes en la corrida". <br>**b. Cuatro números:** fitness promedio, manzanas por agente, edad promedio (ticks vividos) y recorrido promedio (píxeles), de la generación 1 al promedio de las últimas K = mín(5, G − 1) generaciones (G = generaciones de la corrida; las últimas K no incluyen la 1). El cambio va en % para fitness y edad, y en × para manzanas y recorrido; en verde si sube, en naranja si baja; "—" si el valor de la generación 1 es 0. La nota de cada uno dice "gen 1 → promedio de las últimas K"; **la de edad y la de recorrido dicen además que suben también porque las generaciones se alargan.** Con G = 1, solo el valor y la nota "una sola generación". <br>**c. Gráficos:** fitness promedio y máximo por generación, con escala automática, el último valor de cada serie rotulado y **cada paso del puzzle que se alcanzó marcado** con una línea punteada en su generación y la etiqueta "1ª llave roja · gen 2"; las etiquetas se apilan, una por renglón, para que no se pisen. Debajo, manzanas por agente. <br>**d. Por dónde caminaron:** el mapa de calor de la generación 1 y el de la última, lado a lado, con la misma escala de color; sobre fondo liso, con solo el contorno gris de las dos fortalezas (los recuadros de `_is_inside_fortress`: tamaño × 20 px desde `small_fortress_pos` y `large_fortress_pos`, que no cambian entre generaciones; el resto del mapa se regenera en cada una). Color de una celda: raíz cuadrada de valor / máximo de los dos mapas, de ocre oscuro a ámbar (los de la maqueta); una celda sin visitas queda del fondo. Debajo de cada uno, "Generación N · X % del mapa"; la leyenda "poco tiempo — mucho" y la nota de la maqueta (qué es el calor, por qué solo las fortalezas). Con G = 1, un solo mapa. <br>**e. Embudo del puzzle** de la última generación: los cinco pasos, cada uno con su sprite, una barra (agentes / `POPULATION_SIZE`) y "5 de 60 · 1ª vez: gen 2", "0 de 60 · 1ª vez: gen 29" o "nadie, en ninguna generación". Debajo, **solo si la última generación terminó con `vivos` = 0:** "La generación 30 terminó en el tick 1.335 de 2.220: murieron todos". <br>**f. Mejor agente de la corrida:** su sprite, "#id · generación g", fitness, manzanas, recorrido, ticks vividos y hasta qué paso del puzzle llegó (por su nombre, como paso). <br>**g. Pie:** "¿Aprendieron de verdad? Se mide contra la línea base sin evolución: python experimento.py" (en la línea base: "Esta corrida es la línea base: cada generación arranca con cerebros al azar"), y "ESC o ENTER para salir". <br>Fuera del encabezado, el cofre aparece solo como nombre de paso (la fila del embudo, el paso del mejor agente). |
| 15 | **El boletín por consola.** El boletín es una función que no dibuja: arma los datos de la decisión 14 (sin gráficos ni mapas) a partir del registro. Sin ventana, `imprimir_resumen_final` imprime ese boletín en texto: encabezado (con el tiempo simulado, DIAG-15), los cuatro números con sus notas, el embudo, "murieron todos" si corresponde, el mejor agente, la frase del cofre una sola vez y la cobertura del mapa de la generación 1 y de la última. Así las corridas sin ventana dejan el mejor agente en su log. Con ventana se imprime también, antes de mostrar la pantalla. Deja de existir el promedio de "las últimas 3". |

### Cómo se verifica

| # | Decisión |
|---|----------|
| 16 | **CSV de referencia, antes de tocar código** (primer paso del bloque A): semilla 7, 3 generaciones, sin ventana, guiado y autónomo, con evolución y sin ella: 4 CSV, guardados fuera del repo (scratchpad), con el comando en la bitácora. Al cerrar cada bloque, las mismas 4 corridas dan los mismos 4 CSV byte a byte (`cmp`), y con ventana (2 generaciones, en los dos modos) el mismo CSV que sin ventana. |
| 17 | **Tests, cada uno con su control:** se corre una vez contra una versión rota a propósito y tiene que fallar; el control queda en la bitácora. <br>· **A, `tests/test_registro.py`:** el mapa de calor cuenta en la celda correcta (también en los bordes: x 0 y 959, y 0 y 799), solo agentes vivos, normaliza por los ticks de su generación, guarda la de la generación 1 y arranca la siguiente en cero (control: contar los muertos o normalizar por los ticks de la corrida); los hitos se registran la primera vez y no la segunda, con generación, tick e id, dos en un mismo tick en orden (control: registrar cada vez); el récord del mejor agente cambia solo si se supera (control: `>=`); nada consume azar: el estado de `random` y de `np.random` es igual antes y después de contar, mirar hitos, cerrar una generación y armar el boletín (control: una llamada a `random.random()`). <br>· **A, `tests/test_boletin.py`:** los cuatro números (gen 1 contra las últimas 5; con 3 generaciones, las últimas 2; con 1, sin comparación), sus formatos y sus notas; el embudo y la primera generación de cada paso; "hasta dónde llegaron"; la frase del cofre una sola vez, con cofre y sin él; "murieron todos" solo con `vivos` = 0; la consola imprime los mismos números; el pie de la línea base. Control: las mismas preguntas contra la pantalla y la consola de hoy (cuatro frases del cofre, "últimas 3"). <br>· **A, escala y formato** (en `test_boletin.py` o aparte): los ejemplos de la decisión 10 y de la 8. Control: la escala fija de 0 a 100 del popup (39,7 no da 40). <br>· **A, fuentes:** están los cuatro TTF, los `OFL.txt` y el `LEEME.md`; cada carácter de los textos de pantalla (los del boletín de varias corridas de mentira, los de los avisos y los del panel) existe en la fuente que lo dibuja, con `→`, `×`, `−`, `·`, `¡` y las tildes. Control: la fuente por defecto de pygame con `→`. <br>· **A, al día:** `test_reportes.py` pierde los tests de `textos_del_cuadro` (la función sale) y conserva el de DIAG-14; `test_humo.py` adapta la línea del tiempo simulado al texto nuevo y sigue probando DIAG-15 (2 × 960 ticks = 0,5 min); además, en cada log de humo, cada línea de hito coincide con la primera generación con esa columna `agentes_*` mayor que 0, y cada paso con agentes tiene su línea. <br>· **B, `tests/test_pantallas.py`,** con `SDL_VIDEODRIVER=dummy` (sin ventana visible): el panel, los avisos y la pantalla final se dibujan sobre la superficie de 1200×800 sin error, con 0, 1 y 30 generaciones, con cofre y sin él, y en la línea base; los avisos, con un reloj inyectado: el de generación está a los 2,4 s y no a los 2,6 s, el de hito dura 4 s, se apilan en orden y no hay más de 3. Control: una división por cero con G = 1, o el aviso sin vencer. <br>`python -m pytest -q` sigue en menos de 90 s. |
| 18 | **La ventana se verifica con eventos inyectados** (LEC-004): un script envuelve `pygame.event.get` para mandar ESC en la pantalla final y `pygame.display.flip` para guardar capturas (aviso de fin de generación, aviso de hito, panel con gráficos, pantalla final). Una corrida con ventana llega al final sin ningún clic, ESC la cierra con código 0 y el CSV completo, el log tiene el boletín y las líneas de hito, y la sesión mira las capturas (y Fer, si quiere). Las capturas quedan en el scratchpad, no en el repo. Para que no tarde, el script sube `TARGET_FPS`: solo cambia cuánto espera cada cuadro, no la simulación (lo confirma el CSV). |

### Bloques

| # | Decisión |
|---|----------|
| 19 | **Dos bloques, una sesión cada uno, en este orden,** con bitácora. Cada uno cierra con el control de la decisión 16 y un commit con la confirmación de Fer. <br>**A — Los datos:** decisiones 3 a 8, 13 y 15: CSV de referencia, registro (historia, hitos, mejor agente, mapa de calor), costo medido, boletín y consola nueva, escala y formato, fuentes en el repo, tests de A. <br>**B — Las pantallas:** decisiones 1, 2, 9 a 12 y 14: sale el popup, panel, avisos, pantalla final, `test_pantallas.py`, la verificación con ventana de la decisión 18 y los docs. El cierre (`/close-spec`) entra en la sesión del bloque B si alcanza el contexto; si no, una tercera sesión. |

## Criterios de done (DoD)

**Bloque A — Los datos** (✅ 2026-11-15, sesión 1)
- [x] Los 4 CSV de referencia existen desde antes del primer cambio de código, con su comando en la
  bitácora.
- [x] El registro guarda la historia (fila del CSV más ticks máximos), los hitos, el mejor agente de la
  corrida y el mapa de calor como dicen las decisiones 4 a 7, alimentado por un solo camino en
  `main.py`. `primera_generacion_cofre` y `agentes_con_cofre` ya no existen en `main.py`.
- [x] Cada hito imprime su línea en la consola (decisión 5); la del cofre de hoy es una de ellas.
- [x] `HEATMAP_CELL_SIZE = 16` en `config.py`. El costo de contar está medido de nuevo y anotado en la
  bitácora (µs por tick contra ms por tick, y memoria), por debajo del 1 % del tick.
- [x] El boletín es una función que no dibuja; sin ventana, la consola lo imprime como dice la
  decisión 15, con la frase del cofre una sola vez y sin "últimas 3".
- [x] Escala automática y formato de números como dicen las decisiones 10 y 8.
- [x] `assets/fonts/` tiene Pixelify Sans Bold e Inter Regular, SemiBold y Bold (TTF estáticos), los
  `OFL.txt` y el `LEEME.md` con origen y versión; el README dice que son OFL.
- [x] Los tests de A (decisión 17) verdes, cada uno con su control anotado en la bitácora;
  `test_reportes.py` y `test_humo.py` al día (`test_reportes.py` conserva los de `textos_del_cuadro`
  hasta el B: ver desvíos de la sesión 1).
- [x] Las 4 corridas dan los 4 CSV de referencia byte a byte; con ventana (2 generaciones, los dos
  modos), el mismo CSV que sin ventana.
- [x] `python -m pytest -q` verde en menos de 90 s.

**Bloque B — Las pantallas** (✅ 2026-11-15, sesión 2)
- [x] `grep` no encuentra `popup.py`, `SummaryPopup`, `_datos_del_popup`, `MOUSEBUTTONDOWN`,
  `get_movement_skill`, `get_food_skill` ni `get_energy_skill` en el código.
- [x] El panel sigue la decisión 9, con los dos gráficos en vivo y la escala de la decisión 10.
- [x] Los avisos siguen las decisiones 11 y 12.
- [x] La pantalla final sigue la decisión 14: no tiene MOVIMIENTO ni CLUSTERING, y la frase del cofre
  está una sola vez.
- [x] `grep "font.Font(None"` solo encuentra los rótulos de respaldo de `src/world/obstacles.py`.
- [x] `tests/test_pantallas.py` verde, con su control anotado en la bitácora.
- [x] La verificación con ventana de la decisión 18 está hecha y anotada: corrida hasta el final sin
  clics, ESC cierra, capturas miradas, log con el boletín y los hitos, CSV igual que sin ventana en los
  dos modos.
- [x] Las 4 corridas dan los 4 CSV de referencia byte a byte.
- [x] `python -m pytest -q` verde en menos de 90 s.
- [x] Docs al día: README (árbol de `src/ui/`, las líneas que nombran el popup, la pantalla final y el
  panel, y la licencia de las fuentes), `CLAUDE.md` (árbol: `ui/` sin el popup) y DIAG-32 ✅ en
  `AnalisisQA.md`.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| PANTALLAS-01 | La simulación no cambia | Los 4 CSV de referencia, byte a byte, al cerrar cada bloque; con ventana igual que sin ventana, en los dos modos |
| PANTALLAS-02 | Sin azar nuevo | El test de estado de `random` y `np.random` verde; su control (una llamada a `random.random()`) falla |
| PANTALLAS-03 | Mapa de calor | Celda correcta en los bordes, solo vivos, valor por tick, generación 1 guardada; costo medido por debajo del 1 % del tick |
| PANTALLAS-04 | Hitos | Primera vez, con generación, tick e id; línea en la consola; coincide con la primera generación con `agentes_*` > 0 del CSV |
| PANTALLAS-05 | Mejor agente | Es el récord de la corrida; su fitness es el máximo de `fitness_max` del CSV; sale en el log sin ventana |
| PANTALLAS-06 | Los cuatro números | Gen 1 contra las últimas K (5, menos si la corrida es corta); % y ×; notas de edad y recorrido |
| PANTALLAS-07 | Embudo y cofre | Embudo de la última generación con la 1ª vez de cada paso; la frase del cofre, una sola vez; "murieron todos" solo con `vivos` = 0 |
| PANTALLAS-08 | Consola sin ventana | Imprime el boletín (mejor agente y cobertura incluidos) y el tiempo simulado correcto (DIAG-15) |
| PANTALLAS-09 | Escala automática | Los ejemplos de la decisión 10; nunca 0 a 100 fijo |
| PANTALLAS-10 | Fuentes | 4 TTF, `OFL.txt`, `LEEME.md`; todos los caracteres de pantalla existen; la `→` se ve |
| PANTALLAS-11 | Sin popup | No existe nada de lo de la decisión 1; la corrida con ventana no pide clics; DIAG-32 ✅ |
| PANTALLAS-12 | Panel | Datos, gráficos de fitness y manzanas con escala automática, puzzle y teclas (captura) |
| PANTALLAS-13 | Aviso de fin de generación | Arriba, 2,5 s, diferencias contra la anterior; no aparece después de la última (test y captura) |
| PANTALLAS-14 | Aviso de hito | Dorado, 4 s, apilados, no más de 3 (test y captura) |
| PANTALLAS-15 | Pantalla final | Todo lo de la decisión 14, sin MOVIMIENTO ni CLUSTERING (captura) |
| PANTALLAS-16 | Ventana con eventos inyectados | Llega al final sin clics, ESC cierra con código 0, el log tiene el boletín y los hitos |
| PANTALLAS-17 | Tests | `python -m pytest -q` verde en menos de 90 s; cada test nuevo con su control en la bitácora |
| PANTALLAS-18 | Docs | README, `CLAUDE.md` y `AnalisisQA.md` como dice el DoD |

## Wireframes

Referencia visual: la [maqueta](https://claude.ai/artifact/SvXK3fB1Yv8zpSB3HBXE5Z). Estos dibujos fijan
qué va y dónde; los números son los de la maqueta (guiado, semilla 1); los del mejor agente, marcadores.

**Panel derecho, durante la corrida** (240×800):
```
┌──────────────────────────┐
│ Ecosistema               │
│ Generación      12 de 30 │
│ Modo              guiado │
│ Tiempo             00:00 │
│ Vivos                 60 │
│ Muertos                0 │
│ Comida                70 │
│ FITNESS POR GENERACIÓN   │
│ ─ Promedio  ─ Máximo     │
│ 80┤     /\    /‾● 66,0   │
│ 40┤ _/‾‾  ‾‾‾‾  ● 31,2   │
│  0┼─────────────         │
│   G1          G11        │
│ MANZANAS POR AGENTE      │
│1,5┤                      │
│  0┼__/‾‾‾‾‾‾‾‾● 1,10     │
│ PUZZLE                   │
│ Esta generación:         │
│   nadie todavía          │
│ Gen 11: 2 agentes con    │
│   llave roja             │
│                          │
│ ESPACIO pausa            │
│ + − zoom   ESC salir     │
└──────────────────────────┘
```

**Avisos, arriba del mundo:**
```
        ┌──────────────────────────────────────────────────────────┐
        │ Generación 11 terminada                                   │
        │ Fitness promedio 31,2 +1,1 · Manzanas por agente 1,10 +0,18│
        │ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬                      │
        └──────────────────────────────────────────────────────────┘
        ┌──────────────────────────────────────────────────────────┐
        │ [llave] ¡Primera llave roja!                              │
        │         Un agente la agarró en la generación 2            │
        └──────────────────────────────────────────────────────────┘
```

**Pantalla final** (cuadro de 1144×744 sobre el mundo oscurecido):
```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Corrida terminada                                 Hasta dónde llegaron: llave roja · │
│ Modo guiado · con evolución · semilla 1 ·         el cofre no se abrió               │
│ 30 generaciones · 9,6 min simulados                                                  │
│ ┌ FITNESS PROMEDIO ──┐ ┌ MANZANAS POR AGENTE ┐ ┌ EDAD PROMEDIO ────┐ ┌ RECORRIDO ─────┐ │
│ │ 21,8 → 37,8  +73 % │ │ 0,63 → 1,23  ×2,0   │ │ 863 → 1.028 +19 % │ │ 365 → 1.372 ×3,8│ │
│ │ gen 1 → últimas 5  │ │ gen 1 → últimas 5   │ │ ticks vividos;    │ │ píxeles; sube   │ │
│ │                    │ │                     │ │ sube también...   │ │ también...      │ │
│ └────────────────────┘ └─────────────────────┘ └───────────────────┘ └─────────────────┘ │
│ FITNESS POR GENERACIÓN  ─Promedio ─Máximo         POR DÓNDE CAMINARON                 │
│ 80┤ ┊1ª llave roja · gen 2                        ┌──────────┐ ┌──────────┐          │
│   ┤ ┊ /\/‾\/‾‾\/‾‾‾\/‾‾\  Máx. 64,7               │  gen 1   │ │  gen 30  │          │
│  0┼_┊/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾  Prom. 39,7              └──────────┘ └──────────┘          │
│ MANZANAS POR AGENTE                               Gen 1 · 36 %  Gen 30 · 77 % del mapa│
│1,5┤        ___/‾‾‾‾‾‾‾‾‾‾  1,37                   poco tiempo ░▒▓█ mucho · nota      │
│ PUZZLE: CUÁNTOS LLEGARON A CADA PASO EN LA ÚLTIMA GENERACIÓN  ┌ MEJOR AGENTE ───────┐ │
│ [ ] Llave roja        ███░░░░░░  5 de 60 · 1ª vez: gen 2       │ [sprite] #id · gen g│ │
│ [ ] Puerta de madera  ░░░░░░░░░  nadie, en ninguna generación  │ Fitness f           │ │
│ [ ] Llave dorada      ░░░░░░░░░  nadie, en ninguna generación  │ m manzanas · d px   │ │
│ [ ] Puerta de hierro  ░░░░░░░░░  nadie, en ninguna generación  │ vivió t ticks       │ │
│ [ ] Cofre             ░░░░░░░░░  nadie, en ninguna generación  │ llegó a: <paso>     │ │
│ La generación 30 terminó en el tick 1.335 de 2.220: murieron todos  └─────────────────┘ │
│ ¿Aprendieron de verdad? Se mide contra la línea base…: python experimento.py  ESC/ENTER│
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Implementación (pistas, no normativas)

### Archivos

- **`src/analytics/registro.py`** (sin pygame): el registro de la decisión 4, por ejemplo
  `RegistroDeLaCorrida` con `contar_posiciones(agents)`, `mirar_hitos(agents, generacion, tick)` (devuelve
  los nuevos), `cerrar_generacion(fila, ticks_max, agents)`; y la historia, los hitos, el mejor agente y
  las grillas. Para los hitos alcanza con comparar la etapa máxima de los agentes contra la del registro.
- **`src/analytics/boletin.py`** (sin pygame): arma el boletín (decisiones 14 y 15) y su texto de
  consola; y las funciones puras de formato (decisión 8) y de escala (decisión 10), que usan también las
  pantallas. Así se prueban sin abrir nada.
- **`src/ui/fuentes.py`:** carga y guarda en caché las fuentes por papel y tamaño.
- **`src/ui/graficos.py`:** dibuja un gráfico de líneas con la escala de la decisión 10 (lo usan el panel
  y la pantalla final). Conviene dibujar el gráfico del panel una vez por generación en una `Surface` y
  copiarla en cada cuadro.
- **`src/ui/avisos.py`:** la pila de avisos, con el reloj como parámetro (para el test).
- **`src/ui/stats.py`** (panel), **`src/ui/pantalla_final.py`** (boletín en pantalla y en consola).
- **`main.py`:** crea el registro; después de `tick += 1`, `registro.contar_posiciones(agents)`; después de
  los `_try_*` del puzzle, los hitos (consola y, con ventana, aviso); en el fin de generación, la fila del
  CSV se arma una vez, se escribe y se pasa a `cerrar_generacion` como
  `dict(zip(COLUMNAS_CSV, fila))`. Hoy el popup está en `:22`, `:233-260`, `:357-358`, `:412-417`,
  `:514-516`, `:534` y `:595`; el cofre en `:396-397` y `:479-484`; el panel en `:374` y `:592`; la pausa en
  `:348` y `:597-599`.
- **`config.py`:** `HEATMAP_CELL_SIZE`, junto a la configuración de pantalla.
- **`assets/fonts/`:** los TTF, los `OFL.txt` y el `LEEME.md`.
- **Colores:** los de la maqueta (fondo `#11131c`, panel `#161826`, cuadro `#1a1a19`, texto `#f0efec`,
  secundario `#c3c2b7`, apagado `#a19f96`, promedio `#3987e5`, máximo `#d95926`, sube `#0ca30c`, hito
  `#2a2416` / `#6b5420` / `#ffd27a`, calor `#3a3418` → `#ffb020`).

### Comandos

```bash
S=<scratchpad>
# Referencia (bloque A, antes de tocar código) y control al cerrar cada bloque
for m in guiado autonomo; do
  .venv/Scripts/python.exe main.py --sin-ventana --generaciones 3 --semilla 7 --modo $m --csv "$S/ref_${m}_evo.csv"
  .venv/Scripts/python.exe main.py --sin-ventana --generaciones 3 --semilla 7 --modo $m --sin-evolucion --csv "$S/ref_${m}_sin.csv"
done
# ...las mismas corridas con --csv "$S/nuevo_*.csv", y cmp contra la referencia

# Tests
.venv/Scripts/python.exe -m pytest -q
```

### Trampas conocidas

- **CRLF:** `main.py`, `config.py`, `README.md`, `src/ui/__init__.py`, `stats.py`, `renderer.py`,
  `src/analytics/__init__.py`, `learning_monitor.py` y `advanced_agent.py` son CRLF; `pantalla_final.py`,
  `CLAUDE.md`, los tests y los docs son LF. Después de editar, revisar `git diff` por líneas en blanco
  vaciadas (LEC-002), contar finales de línea con Python (LEC-003), nunca `sed -i` (LEC-005). Los archivos
  nuevos, LF.
- **Contar con `agent.alive` al final del tick,** no con la lista `alive_agents`, que se arma al empezar.
- **Nada al azar en lo nuevo:** ni un `random.choice` para un color. Las partículas ya tienen su propio
  generador (`ParticleSystem.rng`).
- **`SimulationConfig` se pisa en la clase,** no en una instancia: el panel y la pantalla final leen las
  generaciones de la corrida de ahí (`MAX_GENERATIONS`, que pisa `--generaciones`).
- **Fuentes:** pygame 2.6.1 (SDL_ttf 2.20) carga la instancia por defecto de una fuente variable; hacen
  falta los TTF estáticos. Google Fonts publica Inter y Pixelify Sans como variables en su repo, y las
  estáticas en la descarga de la familia; Inter también en las releases de su autor. Si alguna estática
  no se consigue, se arma en el scratchpad con `fontTools` (no entra a `requirements.txt`). Si Pixelify
  Sans no tiene un carácter de un título, se para y se decide con Fer.
- **Glifo faltante:** ver en la sesión qué API de pygame distingue un carácter que la fuente no tiene
  (por ejemplo, comparar su dibujo con el de un carácter que seguro no está); el control es la `→` con la
  fuente por defecto.
- **Escala y coma flotante:** un 0,3 que viene de una cuenta puede ser 0,30000000000000004; dividido
  por 0,1 da 3,0000000000000004 y ⌈⌉ da 4 (eje hasta 0,4). Usar una tolerancia o `Decimal` en la escala
  (los ejemplos de la decisión 10 se verificaron así al escribir el spec).
- **`SDL_VIDEODRIVER=dummy`** permite `set_mode` y `convert_alpha` sin ventana visible; los sprites
  necesitan una pantalla creada antes de cargarse.
- **Los checkers de `/qa-spec` no pueden correr `main.py`:** lo que pida corridas se vuelve a correr
  fresco en la sesión, y cada `archivo:línea` citado se imprime antes de copiarlo (LEC-006).

## Edge cases

- **Corrida de una generación:** los cuatro números sin comparación, un solo mapa de calor, gráficos de
  un punto, sin aviso de fin de generación.
- **Nadie agarra la llave roja en toda la corrida:** "Hasta dónde llegaron: nadie agarró la llave roja",
  el embudo con "nadie, en ninguna generación" en los cinco pasos, el gráfico sin marcas.
- **Varios hitos en la misma generación o el mismo tick:** sus etiquetas se apilan en el gráfico; los
  avisos se apilan, hasta 3.
- **Mueren todos antes del final de una generación:** termina antes, como hoy; si es la última, lo dice
  el boletín (decisión 14 e).
- **Mueren todos justo en el último tick:** `vivos` = 0, y el boletín lo dice igual ("terminó en el
  tick 2.220 de 2.220: murieron todos").
- **El valor de la generación 1 es 0** (por ejemplo, manzanas en la línea base): el cambio es "—".
- **Un fitness negativo:** el eje baja hasta el múltiplo del paso que lo cubre (decisión 10).
- **Pausa:** la simulación y el conteo se frenan; los avisos siguen su reloj.
- **Zoom:** todo se dibuja en la superficie de 1200×800 y se escala, como hoy.
- **`POPULATION_SIZE` distinto de 60:** las barras del embudo y el "de N" lo leen de `config.py`.
- **Un agente sentado siempre en la misma celda:** el color usa la raíz cuadrada para que esa celda no
  apague el resto del mapa.

## Esfuerzo

Dos sesiones en secuencia, una por bloque (decisión 19). El B es el más grande (panel, avisos,
pantalla final y la verificación con ventana): si no entra, se corta donde quede verde y la bitácora
dice qué falta. El cierre entra en la sesión del B si alcanza el contexto; si no, una tercera.

## Relación con otros specs

- **[Modo guiado y modo autónomo](../done/MODO_GUIADO_Y_AUTONOMO.md):** su decisión 11 (consola, popup y
  pantalla final dicen cuántos abrieron el cofre) queda en el boletín, una sola vez; la 25 (pantalla final
  con "LA CORRIDA" y `->`) la reemplaza el boletín, con la `→` de vuelta; la 26 (`popup.py:93`) se va con el
  popup. El id por contador (decisión 24) es el que muestra el mejor agente.
- **[Medir antes de tocar](../done/MEDIR_ANTES_DE_TOCAR.md):** la semilla y el CSV byte a byte son el
  control de este spec; el CSV no cambia.
- **Ítem 7 del BACKLOG (mapa más natural):** el mapa de calor usa fondo liso, así que no depende de cómo
  se dibuje el mapa.

## Bitácora de ejecución

### CSV de referencia (decisión 16)

Generados el 2026-11-15 con el código del commit `4212fad`, antes del primer cambio de código, con los
comandos de "Comandos" (semilla 7, 3 generaciones, sin ventana). El control de cada bloque compara contra
estos SHA-256, así no depende de que el scratchpad de una sesión vieja siga existiendo; si hace falta el
archivo, se regenera desde `4212fad` con `git worktree add`.

| CSV | SHA-256 |
|-----|---------|
| `ref_guiado_evo.csv` | `d40735791309abc8ed764eba2553420eb696b2fdba644c899102768fe769b2dd` |
| `ref_guiado_sin.csv` | `897b1bfcb029646556c8bb900f5a1a9fc71d015fedc4a901d72e07c130f53379` |
| `ref_autonomo_evo.csv` | `4b442886c6ca699c1cfeed939e96fbe0d8084ab6ebe4fe463c6a8bef1d47a954` |
| `ref_autonomo_sin.csv` | `6359234df93d2df64800b825930c4ce7208ee1fe6341a501a4dfe5ffca39c54d` |

```bash
S=<scratchpad>
for m in guiado autonomo; do for e in evo sin; do
  f=""; [ $e = sin ] && f="--sin-evolucion"
  .venv/Scripts/python.exe main.py --sin-ventana --generaciones 3 --semilla 7 --modo $m $f --csv "$S/nuevo_${m}_${e}.csv"
done; done
sha256sum "$S"/nuevo_*.csv   # contra la tabla
```

### Sesión 1 — 2026-11-15 — Bloque A (los datos)

- **Hecho** (commit `pantallas: bloque A, los datos`): spec a `active/`, manifiesto y BACKLOG al día.
  CSV de referencia antes de tocar código (tabla de arriba). `src/analytics/registro.py`
  (`RegistroDeLaCorrida`: historia, hitos, mejor agente, mapa de calor), `src/analytics/boletin.py`
  (formato, escala, `armar_boletin`, `texto_de_consola`, `linea_de_hito`), `src/ui/fuentes.py`
  (`verificar` y `fuente(papel, tamaño)`), `HEATMAP_CELL_SIZE = 16` en `config.py`. `main.py`: el registro
  se alimenta por un solo camino (cuenta después de `tick += 1`, hitos después de que actúan los
  agentes, `cerrar_generacion` con la misma fila del CSV); salen `primera_generacion_cofre`,
  `agentes_con_cofre` y también `ticks_totales` (sale del registro); con ventana, `fuentes.verificar()`
  antes de abrirla. `imprimir_resumen_final(registro)` imprime el boletín, con ventana y sin ella.
  Fuentes en `assets/fonts/` con `LEEME.md`; README (árbol, `registro`, `boletin`, `fuentes`, sección
  Licencia) y `CLAUDE.md` (árbol) al día.
- **Verificación:** las 4 corridas dan los 4 SHA-256 de referencia (dos veces: a mitad del bloque y con
  el código final). Con ventana (`ventana.py` del scratchpad: envuelve `main.mostrar_pantalla_final`
  para prender una bandera y `pygame.event.get` para mandar ESC desde ahí; `TARGET_FPS` = 100.000),
  semilla 7, 2 generaciones: sale con código 0, el CSV es igual al de sin ventana en los dos modos y el
  log tiene el boletín y la línea del hito. `python -m pytest -q`: 109 verdes en 24 s.
- **Costo del mapa de calor** (decisión 7, esta máquina): contar 60 agentes, 18,3 µs por tick
  (`timeit`, mejor de 5); el tick sin ventana, 6,69 ms (semilla 1: 7,8 s una generación, 14,3 s dos).
  **0,27 % del tick.** Memoria: cada grilla es una lista de 3.000 enteros, 24 KB de punteros (los
  enteros hasta 256 son compartidos; en una prueba, 45 celdas pasaban de 256): tres grillas, menos de
  100 KB.
- **Controles de la decisión 17** (cada uno, con monkeypatch desde `controles.py` del scratchpad, sin
  tocar el código; los 9 fallan, como tienen que fallar):
  contar también los muertos → `test_solo_cuentan_los_vivos` falla (2 ≠ 1) · normalizar por los ticks de
  la corrida → falla (0,33 ≠ 1,0) · registrar el hito cada vez → falla · récord con `>=` → falla (el
  empate cambia al 4) · una llamada a `random.random()` al contar → falla el test del azar · escala fija
  de 0 a 100 (la del popup) → falla (39,7 da 100, no 40) · las preguntas de `test_boletin` (una sola
  frase del cofre, sin "últimas 3") contra la pantalla y la consola de antes, guardadas antes de tocar
  `pantalla_final.py` → fallan las tres (cuadro: 5 renglones con el cofre; consola: 2, y "últimas 3")
  · la fuente de pygame en lugar de Inter → falla por la `→` · el test de hitos de `test_humo` contra
  un log con otra generación y contra uno sin la línea → falla en los dos.
- **Estados:** DoD del bloque A completo. QA (para `/qa-spec` al cerrar): PANTALLAS-01 (bloque A),
  02, 03, 04, 05, 06, 07, 08, 09 y 10 cubiertos por tests y corridas; 17 en parte (falta
  `test_pantallas.py`, del B). Del 11 al 16 y el 18, del B.
- **Desvíos del spec, y por qué:**
  - **Las notas de edad y recorrido dicen "sube también porque las generaciones se alargan" solo si
    se alargan:** si alguna de las últimas K generaciones podía durar más ticks que la 1. Con 4
    generaciones o menos duran todas 960 ticks, y la frase sería falsa. Fer lo confirmó el 2026-11-15.
  - **El cuadro final de antes sigue en la ventana hasta el B:** la decisión 2 (sale la pantalla de
    hoy) es del bloque B (decisión 19). `mostrar_pantalla_final` recibe el registro y saca de ahí lo del
    cofre y el tiempo para el cuadro viejo; `test_reportes.py` conserva los tests de `textos_del_cuadro`
    hasta que la función salga en el B (la decisión 17 los sacaba en el A).
  - **`tests/test_puzzle.py::test_abrir_el_cofre_no_termina_la_corrida` cambió** (no estaba en la
    decisión 17): miraba los dos argumentos del cofre de `mostrar_pantalla_final`. Su mock ahora hace
    lo que el cofre real (`etapa = 5`, `world.py:954`) y el test mira la frase del cofre del boletín.
  - **Fuentes en dos carpetas,** `assets/fonts/pixelify-sans/` y `assets/fonts/inter/`, cada una con su
    `OFL.txt` (el de Inter es su `LICENSE.txt`, renombrado). Pixelify Sans Bold sale del repo de la
    autora (Google Fonts solo publica la variable); Inter, de la release v4.1 (`extras/ttf/`).
  - **A Pixelify Sans le falta la `→`.** Ningún título la lleva (va en los números y las notas, en
    Inter), así que no hizo falta parar; `test_fuentes.py` lo vigila.
  - **Textos que el spec no fijaba:** el mejor agente en etapa 0 dice "llegó a: ningún paso del
    puzzle"; con 2 generaciones la nota es "gen 1 → gen 2"; "1 manzana" y "lo abrió 1 agente" en
    singular; el boletín por consola arranca con "📋 Corrida terminada".
  - **`minutos_simulados` pasó a `boletin.py`** (sin pygame); `pantalla_final.py` lo importa de ahí.
- **A medias o bloqueado:** nada del A. El "PAUSADO" sigue con la fuente de pygame: dibujar con las
  fuentes nuevas es del B (DoD del B, `grep "font.Font(None"`).
- **Para verificar en producción:** N/A (no hay producción).
- **Próxima sesión — Bloque B (las pantallas):**
  1. Leer la maqueta (`Artifact` action `read` sobre el link del encabezado) para distribución, tamaños y
     colores; los colores ya están en "Implementación".
  2. Sacar el popup (decisión 1): `grep -n "popup\|SummaryPopup\|_datos_del_popup\|fitness_history\|MOUSEBUTTONDOWN\|get_movement_skill\|get_food_skill\|get_energy_skill"`
     en todo el código; las líneas de `main.py` que da el spec ya se corrieron. `src/ui/__init__.py`
     importa `SummaryPopup`.
  3. Panel (decisión 9), avisos (11 y 12, con el reloj inyectable), pantalla final (14) leyendo
     `armar_boletin(registro)` y `registro` (series de la historia, `registro.hitos`, `registro.valores`
     de `calor_gen1` y `calor_ultima`), y el "PAUSADO", todo con `fuentes.fuente(...)`. Los avisos de
     hito salen del mismo `for hito in registro.mirar_hitos(...)` de `main.py`.
  4. Al sacar el cuadro viejo: sale el bloque de `mostrar_pantalla_final` que saca el cofre del
     registro, `textos_del_cuadro` y compañía, y los tests de `textos_del_cuadro` de `test_reportes.py`
     (queda el de DIAG-14). En `test_fuentes.py`, `TITULOS` y `TEXTOS_FIJOS` pasan a ser los textos de
     los módulos nuevos.
  5. `tests/test_pantallas.py` con `SDL_VIDEODRIVER=dummy`, y su control.
  6. Verificación con ventana (decisión 18): el patrón de `ventana.py` está en "Verificación", arriba;
     para las capturas, envolver también `pygame.display.flip`. El scratchpad de esta sesión no lo ve
     la próxima: se rearma.
  7. Cierre: las 4 corridas contra los SHA-256 de la tabla, `pytest` en menos de 90 s, docs del DoD
     del B (README: las líneas del popup, `CLAUDE.md`: `ui/` sin el popup, DIAG-32 ✅), y `/close-spec`
     si alcanza el contexto.
  - **Trampas:** Pixelify Sans no tiene la `→` (ningún título puede llevarla). Los títulos de los hitos
    están en `boletin.TITULOS_DE_HITOS`; los subtítulos de los avisos (decisión 12) todavía no existen.
    Las notas de edad y recorrido dicen "se alargan" solo si es verdad (desvío confirmado por Fer).

### Sesión 2 — 2026-11-15 — Bloque B (las pantallas)

- **Hecho** (commit `pantallas: bloque B, las pantallas`): sale el popup (decisión 1): `src/ui/popup.py`,
  `SummaryPopup` (también de `src/ui/__init__.py`), `_datos_del_popup`, `fitness_history` y el clic de
  `main.py`, y `get_movement_skill`, `get_food_skill` y `get_energy_skill` (`grep`: nadie más los llamaba).
  Sale el cuadro final de antes (decisión 2): `textos_del_cuadro`, `_dibujar_cuadro`, `_grafico_de_fitness`
  y `_renglones_de_clustering`. Nuevos: `src/ui/graficos.py` (`dibujar_grafico` con la escala de la
  decisión 10, `x_de`, `rotulo_del_eje`), `src/ui/avisos.py` (`PilaDeAvisos` con el reloj como parámetro,
  `textos_de_generacion`, `textos_de_hito`; duraciones y medidas como constantes del módulo). Reescritos:
  `src/ui/stats.py` (el panel de la decisión 9; los gráficos se dibujan una vez por generación en una
  `Surface`) y `src/ui/pantalla_final.py` (`dibujar_boletin`, la decisión 14). `fuentes.py` suma
  `renglones` (partir texto) y `olvidar` (vaciar la caché). `main.py`: el panel ocupa la columna entera
  (x 960, 240×800), los avisos de hito salen del mismo `for` que la línea de consola, el de fin de
  generación va después del `return` de la última, y el "PAUSADO" usa Inter Bold. Tests:
  `tests/test_pantallas.py` (nuevo, 20), `test_fuentes.py` (los textos salen de los módulos nuevos, más
  el test de la "C" abierta) y `test_reportes.py` (queda el de DIAG-14). Docs: README (árbol de
  `src/ui/` y las líneas del popup, el panel y la pantalla final), `CLAUDE.md` (árbol), DIAG-32 ✅ en
  `AnalisisQA.md` y el sub-ítem del popup en `mejoras_futuras.md`.
- **Verificación:** las 4 corridas dan los 4 SHA-256 de la tabla de arriba. `python -m pytest -q`:
  123 verdes en 24 s. Con ventana (`ventana.py` del scratchpad: envuelve `main.mostrar_pantalla_final`
  para prender una bandera, `pygame.event.get` para mandar ESC cuando la pantalla final ya se capturó,
  `pygame.display.flip` para las capturas y `PilaDeAvisos` para saber cuándo hay avisos;
  `TARGET_FPS` = 100.000): semilla 1, 5 generaciones, guiado, 124 s, código 0, un solo ESC, sin ningún
  clic; el log tiene la línea del hito (llave roja, generación 2, la primera fila con
  `agentes_llave_roja` > 0) y el boletín. Semilla 7, 2 generaciones, en los dos modos: código 0 (32 s cada una), el boletín y la línea del hito en el log; el CSV con ventana es igual al de sin ventana (`cmp`) en las tres corridas, también la de la semilla 1. Capturas miradas (en el scratchpad, no en el
  repo): aviso de fin de generación con datos reales ("Generación 2 terminada · Fitness promedio 24,5
  +2,6 · Manzanas por agente 0,75 +0,12", los de la maqueta), aviso de la primera llave roja, panel con
  los dos gráficos y el puzzle, y la pantalla final (gen 1: 36 % del mapa, como la maqueta; mejor
  agente con fitness 69,7, el máximo de `fitness_max`).
- **Controles de `test_pantallas.py` y del test nuevo de `test_fuentes.py`** (cada uno con un plugin de
  pytest del scratchpad, `controles_b.py`, que rompe una cosa sin tocar el código; los 7 fallan, como
  tienen que fallar): `x_de` sin la guarda de una generación (la división por cero con G = 1) → fallan el
  panel y la pantalla final con 1 generación y el test con ventana · el aviso de generación sin vencer
  (duración 10⁹ ms) → falla el de 2,5 s · el de hito sin vencer → falla el de 4 s · sin tope de 3
  hitos → falla el de la pila · `main.py` con el aviso de fin de generación antes de la pantalla final
  (cargado desde una copia) → falla el test con ventana (avisa 1, 2 y 3) · el gráfico de fitness de
  170 px → falla "sin pisar el pie" con murieron todos · el título final a 34 px → falla el de la "C".
- **Estados:** DoD del bloque B completo. QA (para `/qa-spec` al cerrar): PANTALLAS-11 a 18 cubiertos
  por tests, corridas y capturas; 01 cerrado en los dos bloques; 17 completo.
- **Desvíos del spec, y por qué:**
  - **Los títulos en Pixelify van a 24 px (panel) y 32 px (pantalla final), no a 22 y 34 como la
    maqueta:** Pixelify Sans Bold cierra la abertura de la "C" y de la "c" a 21, 22, 30, 33, 34 y 35 px
    (mide ~35 de 1.000 unidades, menos de medio "píxel" de diseño), y se leía "Eoosistema" y "Oorrida
    terminada". `test_fuentes.py` lo vigila en los cuatro tamaños de títulos que se usan.
  - **Los títulos de sección ("FITNESS POR GENERACIÓN", "PUZZLE"…) van en Inter SemiBold,** como en la
    maqueta, no en Pixelify: en Pixelify van "Ecosistema", "Corrida terminada" y los títulos de los
    avisos. La lista `TITULOS` del bloque A los tenía como títulos.
  - **`fuentes.olvidar()`, que el spec no tenía:** una fuente cargada deja de servir cuando se cierra
    `pygame.font`, y dibujar con ella cuelga el proceso (access violation). Pasaba entre
    `test_fuentes.py` y `test_pantallas.py`, en cualquier orden; los dos fixtures la llaman al abrir y
    al cerrar. `pygame.register_quit` no sirve: se vacía con el primer `pygame.quit()`.
  - **Las marcas del gráfico salen del embudo** (la primera fila del CSV con el paso), no de
    `registro.hitos`: por la decisión 5 dan la misma generación, y así el gráfico y el embudo no pueden
    decir cosas distintas.
  - **`mostrar_pantalla_final` conserva `generation` en la firma,** aunque ya no la usa: los tests de
    `test_reglas.py` y `test_pantallas.py` la reemplazan leyendo los argumentos por posición.
  - **Textos que el spec no fijaba:** en el panel, "Con hacha: 3" y "Llave roja: 2" (lo de antes, sin
    el asterisco); la generación anterior dice "con llave roja", "con llave dorada" o "abrieron la
    puerta de madera / de hierro / el cofre", en singular con 1; la marca del cofre es "1er cofre · gen
    N"; la tarjeta es "MEJOR AGENTE DE LA CORRIDA"; una diferencia de 0 en el aviso va en gris, y la que
    baja, en naranja `#e88a3c`; "murieron todos" va debajo del embudo; antes de la generación 1, los
    títulos de los gráficos quedan y el aviso va debajo del primero.
- **A medias o bloqueado:** nada del B. Falta el cierre: no entró en esta sesión por contexto.
- **Para verificar en producción:** N/A (no hay producción).
- **Próxima sesión — Cierre:**
  1. `git status -sb` limpio, en `main`, con el commit del bloque B.
  2. `/close-spec docs/specs/active/PANTALLAS_VER_APRENDER.md`. Los checkers de `/qa-spec` no pueden
     correr `main.py` (LEC-006): las corridas que pide el QA se rehacen frescas en la sesión. Las 4 de
     referencia, con el bloque de comandos de arriba contra los SHA-256 de la tabla. Con ventana, con el
     patrón de `ventana.py` que describe "Verificación" (el scratchpad de esta sesión no lo ve la
     próxima: se rearma): semilla 7, 2 generaciones, en los dos modos, contra el CSV sin ventana; y
     semilla 1, 5 generaciones, guiado, para las capturas (~2 minutos).
  3. Los IDs PANTALLAS-01 a 18 van a una sección nueva de `docs/qa/AnalisisQA.md`; PANTALLAS-12, 13, 14
     y 15 piden captura: se miran las de la semilla 1. Con 2 generaciones no alcanza: el aviso de la
     generación 1 va sin diferencias, después de la última no hay aviso y el panel tiene un solo punto.
  4. Después del cierre, borrar la memoria `spec-en-ejecucion` (el spec deja de estar en ejecución).
  - **Trampas:** Pixelify Sans Bold cierra la "C" en algunos tamaños (ver desvíos): un título nuevo
    va en 16, 18, 20, 23, 24, 26, 28, 32, 36 o 40 px. Un test que cierra pygame llama a
    `fuentes.olvidar()`. Las capturas con ventana tardan: 5 generaciones, ~2 minutos.

### Sesión 3 — 2026-11-15 — Cierre

- **Hecho:** `/close-spec`. QA APROBADO 18/18
  ([AnalisisQA § QA /qa-spec — Pantallas para ver aprender](../../qa/AnalisisQA.md#qa-pantallas-ver-aprender)),
  resumen en [SPECS_ARCHIVO](../../archive/SPECS_ARCHIVO.md#pantallas-ver-aprender), el spec a `done/` con
  su stub, el manifiesto y el BACKLOG al día, y LEC-014. Sin cambios de código.
- **Verificación** (fresca, desde `f62a7f0`, con el árbol limpio): `compileall` y 123 tests en 26,4 s.
  Las 4 corridas dan los 4 SHA-256 de la tabla. Con ventana (`ventana.py` rearmado en el scratchpad,
  con el patrón de la sesión 2): semilla 7 y 2 generaciones en los dos modos, y semilla 1 y 5
  generaciones en el guiado; código 0, un solo ESC, 0 clics, el CSV igual al de sin ventana, y las
  capturas del panel, de los dos avisos y de la pantalla final, miradas. En 7 logs, cada línea de hito
  coincide con la primera generación del CSV con ese paso. En 4 corridas, el récord es el máximo de
  `fitness_max`, y contar posiciones lleva de 0,41 a 0,62 % del tiempo de la corrida (`medir.py` del
  scratchpad, medido adentro de la corrida). El control del azar, vuelto a correr: falla.
- **Estados:** el spec, ✅ Implementado. PANTALLAS-01 a 18, ✅.
- **Desvíos del spec, y por qué:** con 2 generaciones, la nota de los cuatro números dice "gen 1 → gen
  2", y la decisión 14 b da "gen 1 → promedio de las últimas 1". La sesión 1 lo anotó entre los textos
  que el spec no fijaba; lo encontró el checker del QA. Dice lo mismo: Fer lo confirmó el 2026-11-15
  y queda así (LEC-014).
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A (no hay producción).
- **Próxima sesión:** ninguna: el spec está cerrado. Lo que sigue es el ítem 5 del BACKLOG (que el
  puzzle se pueda aprender en el modo autónomo), que todavía no tiene spec.
