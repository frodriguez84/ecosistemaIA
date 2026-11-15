# Spec: Pantallas para ver aprender

**Estado:** 🔵 Planned — en diseño
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

**Bloque A — Los datos**
- [ ] Los 4 CSV de referencia existen desde antes del primer cambio de código, con su comando en la
  bitácora.
- [ ] El registro guarda la historia (fila del CSV más ticks máximos), los hitos, el mejor agente de la
  corrida y el mapa de calor como dicen las decisiones 4 a 7, alimentado por un solo camino en
  `main.py`. `primera_generacion_cofre` y `agentes_con_cofre` ya no existen en `main.py`.
- [ ] Cada hito imprime su línea en la consola (decisión 5); la del cofre de hoy es una de ellas.
- [ ] `HEATMAP_CELL_SIZE = 16` en `config.py`. El costo de contar está medido de nuevo y anotado en la
  bitácora (µs por tick contra ms por tick, y memoria), por debajo del 1 % del tick.
- [ ] El boletín es una función que no dibuja; sin ventana, la consola lo imprime como dice la
  decisión 15, con la frase del cofre una sola vez y sin "últimas 3".
- [ ] Escala automática y formato de números como dicen las decisiones 10 y 8.
- [ ] `assets/fonts/` tiene Pixelify Sans Bold e Inter Regular, SemiBold y Bold (TTF estáticos), los
  `OFL.txt` y el `LEEME.md` con origen y versión; el README dice que son OFL.
- [ ] Los tests de A (decisión 17) verdes, cada uno con su control anotado en la bitácora;
  `test_reportes.py` y `test_humo.py` al día.
- [ ] Las 4 corridas dan los 4 CSV de referencia byte a byte; con ventana (2 generaciones, los dos
  modos), el mismo CSV que sin ventana.
- [ ] `python -m pytest -q` verde en menos de 90 s.

**Bloque B — Las pantallas**
- [ ] `grep` no encuentra `popup.py`, `SummaryPopup`, `_datos_del_popup`, `MOUSEBUTTONDOWN`,
  `get_movement_skill`, `get_food_skill` ni `get_energy_skill` en el código.
- [ ] El panel sigue la decisión 9, con los dos gráficos en vivo y la escala de la decisión 10.
- [ ] Los avisos siguen las decisiones 11 y 12.
- [ ] La pantalla final sigue la decisión 14: no tiene MOVIMIENTO ni CLUSTERING, y la frase del cofre
  está una sola vez.
- [ ] `grep "font.Font(None"` solo encuentra los rótulos de respaldo de `src/world/obstacles.py`.
- [ ] `tests/test_pantallas.py` verde, con su control anotado en la bitácora.
- [ ] La verificación con ventana de la decisión 18 está hecha y anotada: corrida hasta el final sin
  clics, ESC cierra, capturas miradas, log con el boletín y los hitos, CSV igual que sin ventana en los
  dos modos.
- [ ] Las 4 corridas dan los 4 CSV de referencia byte a byte.
- [ ] `python -m pytest -q` verde en menos de 90 s.
- [ ] Docs al día: README (árbol de `src/ui/`, las líneas que nombran el popup, la pantalla final y el
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

_(vacía: el spec está en `planned/`)_. La primera sesión mueve el spec a `active/`, actualiza el
manifiesto y arranca el bloque A por los CSV de referencia (decisión 16), antes de tocar código.
