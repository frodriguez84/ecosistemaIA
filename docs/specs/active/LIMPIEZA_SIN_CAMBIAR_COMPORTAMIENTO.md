# Spec: Limpieza sin cambiar comportamiento

**Estado:** 🟢 Activo — en ejecución desde el 2026-11-14 (bloques A y B ✅; falta C); aprobado por Fer el 2026-11-14
**Prioridad:** Alta — el modo autónomo (ítem 3) va a tocar `main.py` y `genetic_algorithm.py`. Es la
última oportunidad de limpiarlos con una prueba objetiva de que no cambió nada: después del ítem 3,
la simulación cambia a propósito y la comparación byte a byte ya no sirve.
**Gate:** Ninguno
**Bloquea:** Modo guiado y modo autónomo (BACKLOG ítem 3), por orden: toca el mismo código.
**Depende de:** [Medir antes de tocar](../done/MEDIR_ANTES_DE_TOCAR.md) (semilla, CSV, `experimento.py`) ·
[diagnóstico inicial](../../qa/AnalisisQA.md#diagnostico-inicial): DIAG-14 a DIAG-21, DIAG-23, lo que
queda de DIAG-22, DIAG-26 y DIAG-27

---

## Problema

- **Código muerto que confunde (DIAG-18).** `src/agents/brain/` (PyTorch; ni siquiera importa),
  `src/analytics/metrics.py` (nadie lo importa), la rama de zonas `"safe"` (nunca se generan), y dos
  métodos que nadie llama: `LearningMonitor.save_data` y `BehaviorClusterer.print_cluster_report`. El
  README describe `brain/mlp.py` y `metrics.py` como partes del sistema.
- **`requirements.txt` pide diez paquetes que el código no usa (DIAG-19),** `torch` entre ellos (varios
  GB). Una instalación nueva tarda y pesa por nada.
- **15 `.pyc` commiteados (DIAG-20),** varios de módulos que ya no existen. El de `renderer` aparece
  modificado en `git status` después de cada corrida.
- **Duplicación (DIAG-21).** En `genetic_algorithm.py`, el bucle que busca una posición libre está
  copiado cuatro veces, con dos respaldos distintos. En `main.py`, el reposicionamiento de agentes y el
  cálculo de ticks están dos veces cada uno, y el mundo se dibuja dos veces (loop y pantalla final).
  `_simular` tiene ~620 líneas y `show_final_screen` ~570. El modo autónomo va a tocar justo esto.
- **Reportes que mienten.** "Supervivencia 118%" (DIAG-14). "Tiempo total: 0.0 minutos" (DIAG-15). La
  pantalla final dice que se completó la misión aunque el cofre siga cerrado (DIAG-16, en cuatro
  lugares). Mientras está abierta, la pantalla final usa un núcleo entero (DIAG-17).
- **Con ventana, el zoom cambia la simulación (DIAG-27).** El reposicionamiento sortea la `y` con el
  alto de la ventana, que cambia con `+` y `-`; el mundo mide 800 siempre.
- **54 imports y variables sin usar** según Pylint (DIAG-23, DIAG-26): 37 en `main.py`, 13 en el resto
  de `src/` y 4 en el código muerto.
- **`.env.example` vacío (DIAG-22):** no hay variables de entorno.

## Objetivo

Dejar el código más chico y legible, con los reportes diciendo la verdad, y probar que la simulación no
cambió: cada CSV de la verificación sale idéntico byte a byte al de la línea base, en varias semillas,
con evolución y sin ella. Al cierre, el experimento registrado en
[AnalisisQA § Experimento en cinco semillas](../../qa/AnalisisQA.md#experimento-cinco-semillas) se repite
idéntico.

## Qué NO es esta feature

- **No cambia la simulación:** ni el fitness, ni la guía escrita a mano, ni el mundo, ni el puzzle, ni el
  algoritmo genético. Los bugs de comportamiento (DIAG-01 a DIAG-05, DIAG-08 a DIAG-13) son del ítem 3.
- **No junta lo que se parece pero sortea distinto.** `find_safe_position` y el reposicionamiento de
  `main.py` usan otros rangos y radios. Los dos respaldos de `genetic_algorithm.py` (la grilla que evita
  el estanque y el `(100, 100)` fijo) quedan como están. `_create_random_population` y
  `_create_immigrant_agents` conservan su bucle: cuentan los intentos de otra forma y la primera verifica
  más cosas. Unificar cualquiera de estos cambia el azar: si hace falta, es del ítem 3.
- **No saca la segunda llamada a `fix_agent_positions`** (`main.py:711`). Parece repetida y no lo es: el
  reposicionamiento que corre entre las dos verifica el perímetro con `radius` y `fix_agent_positions`
  con `radius * 2`, así que la segunda puede mover agentes y consumir azar.
- **No resuelve los otros avisos de Pylint:** estilo, espacios al final, líneas largas, f-strings sin
  variables, llamadas a métodos `_privados`.
- **No fija versiones** en `requirements.txt`.
- **No toca la sección "¿APRENDIERON?" de la pantalla final.** Compara contra la generación 1, no contra
  la línea base (LEC-001): queda para el ítem 3, que va a poder comparar modos.
- **No cambia `experimento.py` ni las columnas del CSV.**
- **No muda a otros módulos nada de `main.py` salvo la pantalla final** (decisión 17).
- **No desinstala nada del `.venv` local.** Los paquetes que salen de `requirements.txt` pueden quedar
  instalados; la instalación limpia (decisión 25) prueba que no hacen falta.

## Decisiones cerradas

### Cómo se verifica

| # | Decisión |
|---|----------|
| 1 | **"Mismo comportamiento" quiere decir el mismo CSV byte a byte** que la línea base, sin ventana, con evolución y con `--sin-evolucion`. Con ventana, el CSV de 2 generaciones también tiene que ser igual: el dibujo no consume azar (MEDIR-06). |
| 2 | **Una sola línea base para todo el spec,** generada al arrancar el bloque A desde el commit anterior al primer cambio (el hash va a la bitácora): `experimento.py --semillas 1 2 3 4 5 --generaciones 20`, copiada a `results/linea_base_limpieza/` con sus CSV y sus logs (`results/` está en `.gitignore`). **Control:** si todavía existe `results/experimento_20261114-160055/` (el experimento registrado), sus 10 CSV tienen que ser idénticos a los nuevos. Si no lo son, el entorno cambió (versiones, por ejemplo) y la limpieza no arranca hasta explicarlo. |
| 3 | **Las corridas más cortas se comparan contra el comienzo de la línea base.** Las primeras N generaciones no dependen de cuántas vengan después: MEDIR-13 lo comprobó con 10 de 20, y el comparador de esta sesión de diseño lo volvió a confirmar con las semillas 1 y 2 (CSV y log iguales hasta la generación 10). Así una sola línea base de 20 generaciones sirve para los tres niveles de chequeo. |
| 4 | **Tres niveles de chequeo** (tiempos estimados; la sesión 1 anota los medidos): <br>**Rápido**, después de cada cambio: semillas 1 y 2 × dos modos × **7 generaciones**, 4 procesos en paralelo, ~1-2 min. Ejercita la evolución seis veces, la inmigración (se aplica al armar la generación 7: `IMMIGRATION_FREQUENCY = 6`; una corrida de 6 termina antes), el primer alargue de ticks (generación 5), el clustering (3 y 6) y el análisis detallado (5). <br>**Completo**, al final de cada bloque, antes del commit: `experimento.py --semillas 1 2 3 --generaciones 12`, 6 procesos, ~4 min. Suma la detección de patrones (10), el segundo alargue (9) y un tercer mundo. <br>**Cierre**, una vez, al final del bloque C: `experimento.py` con 5 semillas × 20 generaciones, ~9 min (523 s medidos en *Medir*). Es el experimento registrado entero. |
| 5 | **El log también se compara,** sin las dos líneas que cambian solas entre corridas iguales (`Tiempo real acumulado` y la ruta del CSV). Dice mucho más que el CSV: cada generación imprime fitness, comida, puzzle, clustering e inmigración. En una corrida más corta, el log se compara hasta la línea del 🏁, donde empieza el resumen final. Hasta los arreglos de reportes del bloque C, el log tiene que salir idéntico; después, solo cambian las líneas que lista la decisión 18. |
| 6 | **El comparador** (en Implementación) compara los CSV como bytes (el nuevo tiene que ser el comienzo exacto del de la línea base) y los logs normalizados. Si algo difiere, dice la primera generación del CSV y las primeras líneas del log que difieren. Se probó en esta sesión de diseño contra los dos experimentos existentes, con un control: un byte cambiado en un CSV y una línea cambiada en un log; los dos se detectaron. Cada sesión lo copia al scratchpad con `Write`. |
| 7 | **Igual CSV no prueba todo.** Las ramas raras (el respaldo después de 100 intentos de posición, el cofre abierto) casi nunca corren en las semillas de la verificación. Por eso, cada cambio en código que sortea se revisa además leyendo: mismas funciones de azar (`random.*`, `np.random.*`, crear, cruzar y mutar una `SimpleNeuralNetwork`), mismos argumentos, mismo orden, misma cantidad. Hay que suponer que sortea todo lo que está en `src/agents/`, `src/world/` y `src/evolution/`, y las funciones de `main.py` que reposicionan. El clustering no sortea: `KMeans` lleva `random_state=42`. El CSV atrapa los errores del camino común; la lectura, los de las ramas raras. |
| 8 | **Un cambio que cambia el CSV no entra, aunque sea correcto.** Se reescribe para que haga los mismos sorteos, o sale del spec: se anota en `AnalisisQA.md` con la semilla y la primera generación que difiere, y pasa al ítem 3, que cambia el comportamiento a propósito y arma su propia línea base. **En este spec no se regenera la línea base.** Por qué: con una sola línea base, cada cambio se mide contra el mismo punto y el experimento registrado se sigue repitiendo. Aceptar un CSV distinto deja sin control a todos los cambios que vienen después, porque ya no se puede separar la diferencia aceptada de un error nuevo. |
| 9 | **Si el rápido pasa y el completo falla,** la semilla y la primera generación distinta dicen dónde buscar (si diverge en la 7, la inmigración). Se deshace el cambio sospechoso, se repite el completo, y el cambio vuelve reescrito o sale por la decisión 8. |
| 10 | **`pytest` en cada commit** (el gate lo corre), y cada test nuevo se corre una vez contra el código de antes: tiene que fallar. Es su control. |

### Duplicación en la simulación (DIAG-21, DIAG-27)

| # | Decisión |
|---|----------|
| 11 | **`genetic_algorithm.py`:** las cuatro copias del bucle de 100 intentos (élite con `"elitism"`, élite con `"meeting_pool"`, élite con un método desconocido, hijos) pasan a un método que devuelve `(x, y)` o `None` y hace exactamente los mismos sorteos: dos `random.randint` por intento, `(50, 900)` y `(50, 750)`, hasta 100 intentos. **Cada llamador conserva su respaldo:** la grilla que evita el estanque (élite con `"elitism"` y con método desconocido) o `(100, 100)` (élite con `"meeting_pool"` e hijos). La verificación "obstáculo a radio 35 o estanque" pasa a otro método, que usan los seis lugares que la repiten, incluidos `_create_random_population` y `_create_immigrant_agents` (que conservan su bucle). Las ramas `"elitism"` y "método desconocido" son idénticas y se juntan en una. |
| 12 | **`main.py`:** el reposicionamiento copiado (`:311-361` y `:638-688`) pasa a una función, con los mismos sorteos. El cálculo de ticks de la generación (`:382-387` y `:700-705`), a otra. |
| 13 | **DIAG-27 se arregla al extraer el reposicionamiento:** la función sortea con el alto del mundo (`world.screen_height`, 800), no con el de la ventana. Sin ventana, o con ventana y sin zoom, es el mismo número y el CSV no cambia. Es el criterio de *Medir* (decisión 3): la ventana no cambia la simulación. |
| 14 | **Parecido no es igual:** solo se junta código que hace los mismos sorteos con los mismos argumentos (ver "Qué NO es"). |
| 15 | **En el código que se reescribe, lo que queda sin efecto se va con él** (el `if i < len(agents)` redundante de las élites, el `if fixed_count > 0: pass`). Fuera de eso no se sale a buscar más código muerto: lo que aparezca se anota en el BACKLOG. |

### Cuánto se parte `main.py`

| # | Decisión |
|---|----------|
| 16 | **Se parte lo que no es la simulación; el paso de la simulación queda a la vista en `_simular`.** Salen a funciones: el reposicionamiento y los ticks (decisión 12), el reporte por consola de fin de generación, los datos del popup y el dibujo del mundo. Quedan en `_simular`, en línea: el paso de cada agente (`decide`, `act`, los `_try_*` y el cofre), la actualización del mundo, el fin de generación en su orden (fitness de todos → reporte → fila del CSV → monitor → evolución → reposicionamiento → comida) y los eventos de teclado. Es lo que va a cambiar el modo autónomo (golpear en lugar de los `_try_*` por cercanía, puzzle por generación): tiene que leerse de corrido. Los eventos quedan en línea porque cambian cinco variables locales (pausa, corriendo, tamaño y pantalla); sacarlos pediría un objeto de estado. |
| 17 | **Funciones de módulo, sin clases nuevas ni objeto de estado:** lo que necesitan lo reciben por parámetro. Las de reporte solo leen. El `_calculate_fitness()` de todos los agentes y toda llamada que sortea quedan en `_simular`, en el mismo orden. **La pantalla final se muda a `src/ui/pantalla_final.py`,** y el dibujo del mundo a `src/ui/renderer.py`, donde está el resto del dibujo. La pantalla final se reescribe entera en el bloque C (DIAG-16, DIAG-17 y 27 de las 31 variables sin usar de `main.py` están ahí), así que mudarla no suma trabajo, y `main.py` queda con la simulación. |

### Reportes (DIAG-14 a DIAG-17): cómo se verifican

| # | Decisión |
|---|----------|
| 18 | **Cambian la consola o la pantalla, no el CSV.** El CSV tiene que seguir idéntico (prueba que el arreglo no tocó la simulación), y cada arreglo trae su propia prueba con su control: <br>**DIAG-14**, "Supervivencia 118%". `record_generation` guarda `total_agents` y el reporte divide por eso, sin el 50 por defecto. *Prueba:* un test que arma la generación con 60 agentes vivos y espera "Tasa: 100.0%". En el log, las únicas líneas que cambian son las "Tasa:" del análisis detallado (generaciones 5, 10, 15 y 20), y cada una vale `vivos` / 60 de la fila del CSV de esa generación. *Control:* el test falla con el código de antes. <br>**DIAG-15**, "Tiempo total: 0.0 minutos". Pasa a ser el tiempo simulado: la suma de los ticks de todas las generaciones, a 60 por segundo, con división real; el mismo número en la consola y en la pantalla. *Prueba:* `test_humo.py` verifica que el log de 2 generaciones diga `Tiempo simulado: 0.5 minutos` (1.920 ticks). *Control:* hoy dice 0.0. <br>**DIAG-16**, "misión completada" sin cofre. Cuatro textos pasan a depender de si se abrió el cofre: "Resultado: Completado" (`main.py:1286`), "Cofre: SI", que está fijo (`:1298`), "Primera vez con cofre abierto: Gen N", que sale aunque nunca se haya abierto (`:1343`; `generation_data` nunca tiene `chest_opened`, así que cae en la generación actual), y el mensaje final (`:1418`). *Prueba:* los textos del cuadro se arman en una función que no dibuja, y un test la llama con cofre y sin cofre: sin cofre, ninguno de los cuatro dice que se abrió o que se completó. *Control:* la pantalla mirada con ventana antes del cambio, con los cuatro textos. <br>**DIAG-17**, CPU al 100%. Las estadísticas y el clustering se calculan una vez, y el cuadro se arma una vez, ya escalado; el loop solo atiende eventos, muestra y espera con `clock.tick(30)`. *Prueba:* tiempo de CPU del proceso con la pantalla final abierta, durante 10 s: menos de 2 s. *Control:* la misma medición antes del cambio (se espera ~10 s, un núcleo entero). |
| 19 | **La pantalla final queda quieta:** se dibuja una vez (mundo, agentes vivos y cuadro), y las partículas dejan de moverse. |
| 20 | **El fondo de la pantalla final pasa a ser el último cuadro de la simulación,** con el dibujo del loop. Hoy la pantalla final redibuja el mundo con otra variante del pasto y otros halos; el cambio se ve detrás del cuadro y se acepta. |
| 21 | **Lo visual se mira una vez con ventana,** en el bloque C, antes y después: `main.py --generaciones 2 --semilla 1`. El CSV tiene que ser igual a las dos primeras generaciones de la línea base, y la simulación y la pantalla final tienen que verse como antes, salvo lo que dicen las decisiones 18 a 20. |

### Limpieza sin riesgo para el azar

| # | Decisión |
|---|----------|
| 22 | **Código muerto que se borra (DIAG-18):** `src/agents/brain/` (con sus `.pyc`); `src/analytics/metrics.py`; la rama de zonas `"safe"` (`obstacles.py:46-47`, y en `advanced_agent.py:500-517` el `"safe"` de la lista y los dos `elif` que la atienden); y dos métodos que nadie llama, encontrados al escribir este spec: `LearningMonitor.save_data` (con su llamada comentada en `main.py:866`) y `BehaviorClusterer.print_cluster_report` (que además se rompería: lee claves que no existen). Las pociones no se tocan: no son código muerto. |
| 23 | **`requirements.txt` queda con lo que el código importa:** `pygame`, `numpy`, `scikit-learn` y `pytest`, con las versiones mínimas de hoy. Salen los tres de DIAG-19 (`torch`, `deap`, `argparse`) y siete más que nada importa, encontrados al escribir este spec: `pandas` (solo lo usa `metrics.py`), `matplotlib` (solo un import sin uso en `learning_monitor.py`), `seaborn`, `PyYAML`, `rich`, `tqdm` y `pytest-cov`. |
| 24 | **`.pyc` (DIAG-20):** `git rm --cached` de todos los trackeados (15 hoy; los de `brain/` se van con la carpeta). `.gitignore` ya los excluye; los archivos quedan en disco. |
| 25 | **Instalación limpia:** un entorno nuevo en el scratchpad, `pip install -r requirements.txt` y, con ese Python, `pytest` y el chequeo rápido. Tiene que correr y dar verde. Su CSV se compara con la línea base y el resultado se anota: si difiere, se anotan las versiones instaladas y "fijar versiones" va al BACKLOG. No es una falla de la limpieza: las versiones nuevas no las trae este spec. |
| 26 | **`.env.example` se borra** (no hay variables de entorno); `CLAUDE.md` § Variables de entorno lo dice. |
| 27 | **Imports y variables sin usar (DIAG-23, DIAG-26):** el criterio es el Pylint de la extensión de VS Code, con el comando fijo de Implementación. Hoy da 54 hallazgos; al cerrar, 0. Si la parte derecha de una variable sin usar llama a algo que sortea o cambia estado, se queda la llamada y se va el nombre (`_`). Los `from config import SimulationConfig` repetidos adentro de una función que ya lo tiene arriba (W0404) se sacan. |

### Bloques

| # | Decisión |
|---|----------|
| 28 | **Tres bloques, en orden de riesgo, una sesión cada uno** (detalle en Esfuerzo). Cada bloque cierra con el chequeo completo y un commit, con confirmación de Fer. Lleva bitácora. |

## Criterios de done (DoD)

- [x] Línea base generada al arrancar el bloque A, con el hash de su commit en la bitácora. Si existía
  `results/experimento_20261114-160055/`, sus 10 CSV son idénticos a los de la línea base.
- [ ] Cada bloque cerró con el chequeo completo: 6 CSV idénticos al comienzo de los de la línea base, y
  logs idénticos salvo lo que lista la decisión 18.
- [ ] Chequeo de cierre: los 10 CSV del experimento 5 × 20 son idénticos a la línea base, y su
  `resumen.md` también (salvo la línea de la carpeta). En los logs solo cambian las líneas "Tasa:" del
  análisis detallado y la del tiempo en el resumen final.
- [ ] Con ventana, `--generaciones 2 --semilla 1` da un CSV igual a las dos primeras generaciones de la
  línea base.
- [x] No existen `src/agents/brain/`, `src/analytics/metrics.py`, `save_data` ni `print_cluster_report`,
  y `grep -rn "safe\"" src` no encuentra nada.
- [x] `requirements.txt` lista solo `pygame`, `numpy`, `scikit-learn` y `pytest`. Una instalación limpia
  da `pytest` verde y corre el chequeo rápido; la comparación de su CSV está anotada.
- [x] `git ls-files "*.pyc"` no devuelve nada, y una corrida ya no deja `.pyc` modificados en
  `git status`.
- [x] `.env.example` no existe.
- [ ] El comando de Pylint de Implementación da 0 hallazgos (hoy 54).
- [ ] En `genetic_algorithm.py` hay un solo bucle de 100 intentos, y `random.randint(50, 900)` aparece 3
  veces (hoy 6). En `main.py`, el reposicionamiento y el cálculo de ticks aparecen una vez cada uno. El
  mundo se dibuja con una sola función, que usan el loop y la pantalla final.
- [ ] El paso de la simulación y el orden del fin de generación siguen en `_simular`; no hay clases
  nuevas. La pantalla final está en `src/ui/pantalla_final.py`.
- [x] El reposicionamiento sortea con el alto del mundo, no con el de la ventana (DIAG-27).
- [ ] DIAG-14: test nuevo verde, que falla con el código de antes; las "Tasa:" del log de cierre valen
  `vivos` / 60.
- [ ] DIAG-15: `test_humo.py` verifica `Tiempo simulado: 0.5 minutos`; la pantalla final muestra el
  mismo número que la consola.
- [ ] DIAG-16: test nuevo verde sobre los textos de la pantalla final, con cofre y sin cofre; mirada con
  ventana.
- [ ] DIAG-17: con la pantalla final abierta, menos de 2 s de CPU en 10 s, con la medición de antes
  anotada.
- [ ] `python -m pytest -q` verde.
- [ ] Lo que salió del spec por la decisión 8 está anotado en `AnalisisQA.md` y en el ítem 3 del BACKLOG
  (o la bitácora dice que no salió nada).
- [ ] Docs al día: README (dependencias, estructura sin `brain/` ni `metrics.py`, con
  `pantalla_final.py`); `CLAUDE.md` (§ Stack, § Estructura, § Variables de entorno, y en § Notas lo de
  código muerto y `.pyc`); DIAG-14 a DIAG-21, DIAG-23, DIAG-26 y DIAG-27 ✅ en `AnalisisQA.md`.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| LIMPIEZA-01 | Línea base | 10 CSV y 10 logs en `results/linea_base_limpieza/`, hash anotado; idénticos a `experimento_20261114-160055/` si existe |
| LIMPIEZA-02 | Chequeo completo del bloque A | 6 CSV y 6 logs idénticos |
| LIMPIEZA-03 | Chequeo completo del bloque B | 6 CSV y 6 logs idénticos |
| LIMPIEZA-04 | Chequeo completo del bloque C | 6 CSV idénticos; en los logs solo cambian las "Tasa:" de las generaciones 5 y 10 |
| LIMPIEZA-05 | Chequeo de cierre, 5 × 20 | 10 CSV idénticos; `resumen.md` igual salvo la carpeta; logs: solo las "Tasa:" y la línea del tiempo |
| LIMPIEZA-06 | Con ventana, `--generaciones 2 --semilla 1` | CSV igual a las 2 primeras generaciones de la línea base |
| LIMPIEZA-07 | Instalación limpia | `pip list` sin los diez paquetes; `pytest` verde; chequeo rápido corrido y su comparación anotada |
| LIMPIEZA-08 | `.pyc` | `git ls-files "*.pyc"` vacío; después de una corrida, `git status` no muestra `.pyc` |
| LIMPIEZA-09 | Código muerto | Los archivos y métodos de la decisión 22 no existen; `grep -rn "safe\"" src` vacío |
| LIMPIEZA-10 | Pylint | El comando de Implementación da 0 hallazgos |
| LIMPIEZA-11 | `genetic_algorithm.py` | `random.randint(50, 900)` aparece 3 veces. Leyendo: mismos sorteos en el mismo orden, y cada llamador con su respaldo |
| LIMPIEZA-12 | Estructura de `main.py` | Reposicionamiento y ticks una vez cada uno; el paso de la simulación y el fin de generación en `_simular`; sin clases nuevas |
| LIMPIEZA-13 | DIAG-27, con ventana y zoom | `--generaciones 3 --semilla 1`, apretando `+` durante la generación 1: el CSV es igual a la línea base. *Control:* lo mismo antes del cambio da otro CSV desde la generación 2. Si el control no da distinto (ningún agente necesitó reposicionarse), se anota y vale la lectura |
| LIMPIEZA-14 | DIAG-14 | Test verde que falla con el código de antes; las "Tasa:" del log de cierre valen `vivos` / 60 |
| LIMPIEZA-15 | DIAG-15 | `test_humo.py` verifica 0.5 minutos; la pantalla final muestra el mismo número que la consola |
| LIMPIEZA-16 | DIAG-16 | Test verde con cofre y sin cofre; con ventana y sin cofre, ninguno de los cuatro textos dice que se completó |
| LIMPIEZA-17 | DIAG-17 | CPU con la pantalla final abierta, 10 s: antes ~10 s (control), después menos de 2 s |
| LIMPIEZA-18 | Pantalla final, a ojo | Fondo igual al último cuadro, quieta, textos correctos; ESC y ENTER cierran |
| LIMPIEZA-19 | `python -m pytest -q` | Verde |
| LIMPIEZA-20 | Lo que salió del spec | Cada cambio que salió por la decisión 8 está en `AnalisisQA.md` (semilla y generación) y en el ítem 3 del BACKLOG, o la bitácora dice "ninguno" |
| LIMPIEZA-21 | Docs | README, `CLAUDE.md` y los DIAG ✅, como dice el DoD |

## Implementación

### Comandos

Desde la raíz, en Git Bash. `S` es el scratchpad de la sesión.

```bash
PY=.venv/Scripts/python.exe

# Línea base (bloque A, lo primero; tarda ~9 min, en segundo plano)
git rev-parse --short HEAD                                    # a la bitácora
$PY experimento.py --semillas 1 2 3 4 5 --generaciones 20
mv results/experimento_<fecha-hora> results/linea_base_limpieza
$PY "$S/comparar.py" results/linea_base_limpieza results/experimento_20261114-160055   # control

# Chequeo rápido (después de cada cambio)
mkdir -p results/rapido
for s in 1 2; do
  $PY -u main.py --sin-ventana --generaciones 7 --semilla $s \
    --csv results/rapido/corrida_s${s}_evolucion.csv > results/rapido/corrida_s${s}_evolucion.log 2>&1 &
  $PY -u main.py --sin-ventana --generaciones 7 --semilla $s --sin-evolucion \
    --csv results/rapido/corrida_s${s}_sin_evolucion.csv > results/rapido/corrida_s${s}_sin_evolucion.log 2>&1 &
done; wait
$PY "$S/comparar.py" results/rapido

# Chequeo completo (fin de cada bloque) y de cierre (fin del bloque C)
$PY experimento.py --semillas 1 2 3 --generaciones 12
$PY experimento.py --semillas 1 2 3 4 5 --generaciones 20
$PY "$S/comparar.py" results/experimento_<fecha-hora>
diff <(tail -n +4 results/experimento_<fecha-hora>/resumen.md) <(tail -n +4 results/linea_base_limpieza/resumen.md)

# Con ventana (bloque C): el CSV va a una carpeta propia, con el nombre que espera el comparador
$PY main.py --generaciones 2 --semilla 1 --csv results/ventana/corrida_s1_evolucion.csv
$PY "$S/comparar.py" results/ventana

# Instalación limpia (bloque A)
$PY -m venv "$S/venv-limpio"
"$S/venv-limpio/Scripts/python.exe" -m pip install -r requirements.txt
"$S/venv-limpio/Scripts/python.exe" -m pip list
"$S/venv-limpio/Scripts/python.exe" -m pytest -q
# ...y el chequeo rápido con PY="$S/venv-limpio/Scripts/python.exe"

# Pylint de la extensión: imports y variables sin usar (hoy 54)
L=$(ls -d ~/.vscode/extensions/ms-python.pylint-*/bundled/libs | tail -1)
PYTHONPATH="$L" $PY -m pylint --disable=all --enable=W0611,W0612,W0404 \
  --extension-pkg-allow-list=pygame main.py config.py experimento.py src tests
```

CPU con la pantalla final abierta (DIAG-17), en PowerShell. El Python del `.venv` lanza un segundo
proceso: el de la ventana es el que tiene título.

```powershell
$p = Get-Process python | Where-Object { $_.MainWindowTitle -like "Ecosistema*" }
$antes = $p.CPU; Start-Sleep -Seconds 10; $p.Refresh(); $p.CPU - $antes
```

### El comparador

Se copia con `Write` a `$S/comparar.py` (lleva `$` y comillas: no por heredoc).

```python
"""Compara corridas nuevas contra la línea base de la limpieza: CSV y log.

Uso: python comparar.py CARPETA_NUEVA [CARPETA_BASE]   (base: results/linea_base_limpieza)
Una corrida más corta que la línea base se compara contra el comienzo de la línea base.
Sale con código 1 si algo difiere.
"""
import sys
from pathlib import Path

RUIDO = ("Tiempo real acumulado", "CSV de la corrida:")  # cambian solas entre dos corridas iguales
FIN = "Límite de generaciones"  # desde acá, una corrida más corta imprime su resumen final


def log_normalizado(ruta):
    lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    return [linea for linea in lineas if not any(r in linea for r in RUIDO)]


def comparar(nueva, base):
    iguales = True
    csvs = sorted(nueva.glob("corrida_s*.csv"))
    if not csvs:
        sys.exit(f"No hay CSV en {nueva}")
    for csv_nuevo in csvs:
        csv_base = base / csv_nuevo.name
        filas_n = csv_nuevo.read_bytes().splitlines(keepends=True)
        filas_b = csv_base.read_bytes().splitlines(keepends=True)
        distinta = next((i for i, fila in enumerate(filas_n)
                         if i >= len(filas_b) or fila != filas_b[i]), None)
        if distinta is None:
            print(f"CSV igual     {csv_nuevo.name} ({len(filas_n) - 1} generaciones)")
        else:
            iguales = False
            print(f"CSV DISTINTO  {csv_nuevo.name}: la primera fila distinta es la generación {distinta}")

        log_nuevo, log_base = csv_nuevo.with_suffix(".log"), csv_base.with_suffix(".log")
        if not log_nuevo.exists():
            print("   (sin log)")
            continue
        n, b = log_normalizado(log_nuevo), log_normalizado(log_base)
        if len(n) != len(b):
            corte = next((i for i, linea in enumerate(n) if FIN in linea), len(n))
            n, b = n[:corte], b[:corte]
        diferencias = [(i + 1, x, y) for i, (x, y) in enumerate(zip(n, b)) if x != y]
        if len(n) != len(b):
            diferencias.append((min(len(n), len(b)) + 1, f"<{len(n)} líneas>", f"<{len(b)} líneas>"))
        if not diferencias:
            print(f"log igual     {log_nuevo.name} ({len(n)} líneas comparadas)")
        else:
            iguales = False
            print(f"log DISTINTO  {log_nuevo.name}: {len(diferencias)} líneas")
            for numero, x, y in diferencias[:10]:
                print(f"   línea {numero}\n      nueva: {x}\n      base:  {y}")
    return iguales


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    nueva = Path(sys.argv[1])
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results/linea_base_limpieza")
    sys.exit(0 if comparar(nueva, base) else 1)
```

### Pistas de código (no normativas)

- **`genetic_algorithm.py`** (decisión 11). `any(...) or any(...)` corta igual que los `for` con
  `break` de hoy, y `collides_with` no sortea:

  ```python
  def _choca(self, x, y):
      """True si (x, y) cae sobre un obstáculo (radio 35) o sobre el estanque."""
      return (any(o.collides_with(x, y, 35) for o in self.world.obstacles)
              or any(p.collides_with(x, y, 35, 35) for p in self.world.pond_obstacles))

  def _posicion_libre(self):
      """Hasta 100 intentos al azar, dos randint por intento, como antes. None si ninguno sirve."""
      for _ in range(100):
          x = random.randint(50, 900)
          y = random.randint(50, 750)
          if not self._choca(x, y):
              return x, y
      return None
  ```

  Las élites con `"elitism"`: `self._posicion_libre() or self._posicion_de_respaldo()` (la grilla). Las
  élites con `"meeting_pool"` y los hijos: `self._posicion_libre() or (100, 100)`.
- **`main.py`:** `_ticks_de_generacion(config, generacion)`, `_reposicionar_agentes(world, agents,
  config)`, `_imprimir_fin_de_generacion(...)` y `_datos_del_popup(...)`. `_simular` suma los ticks de
  cada generación (también la parcial del cofre) para DIAG-15.
- **`src/ui/renderer.py`:** `dibujar_mundo(surface, world, sprite_manager, tick)`, con el halo del hacha
  y el de la llave roja en una función (hoy son el mismo código con otro color).
- **`src/ui/pantalla_final.py`:** el resumen por consola (sin ventana), la función que arma los textos
  del cuadro sin dibujar (la que prueba el test de DIAG-16) y la pantalla con su loop. Sigue leyendo
  `SimulationConfig.HEADLESS_MODE` de la clase, como hoy (`main.py:874`).
- **Tests:** `tests/test_reportes.py` (DIAG-14 y DIAG-16, con agentes y mundo de mentira) y una
  verificación más en `test_humo.py` (DIAG-15).

### Trampas conocidas

- **Líneas en blanco con espacios (LEC-002):** `main.py` y `genetic_algorithm.py` son CRLF y tienen
  muchas. Después de cada edición, `git diff` no tiene que mostrar líneas vacías cambiadas fuera del
  código que se reescribió.
- **En el bloque B no cambia ni un `print`:** el comparador compara el log, y un texto corregido de
  paso lo hace fallar. Los textos se tocan solo en el bloque C, y solo los de la decisión 18.
- **El `.pyc` de `renderer` aparece modificado** hasta el `git rm --cached` del bloque A: no stagearlo
  antes.
- **`main.py` necesita el `cwd` en la raíz** (sprites con ruta relativa). Con la salida a un archivo,
  `-u`, o el log aparece todo al final.
- **Cada `experimento.py` deja una carpeta nueva en `results/`:** se acumulan. `linea_base_limpieza/`
  no se borra hasta cerrar el spec.
- **El gate pre-commit corre solo si hay `.py` agregados o modificados:** un commit que solo borra
  archivos no lo dispara. Los tres bloques modifican `.py`, así que lo disparan.

## Edge cases

- **El control de la línea base falla** (sus CSV no son idénticos al experimento registrado): no se
  arranca la limpieza. Se anotan las versiones de `pip list` y se averigua qué cambió.
- **No existe `results/experimento_20261114-160055/`:** el control se saltea, y la bitácora lo dice.
- **Se abre el cofre en una corrida de la verificación:** la corrida termina antes y su CSV es más corto;
  el comparador la compara contra el comienzo de la línea base, igual que a las demás.
- **El zoom de LIMPIEZA-13 no mueve a nadie:** el control no da distinto; se anota y vale la lectura.
- **La instalación limpia da otro CSV:** decisión 25; no frena el spec.

## Esfuerzo

Tres sesiones, en secuencia. Cada bloque termina con el chequeo completo y un commit.

- **A — Línea base y limpieza sin riesgo.** La línea base, primero y en segundo plano. Después: `.pyc`,
  código muerto, `requirements.txt` y la instalación limpia, `.env.example`, y los imports y variables
  sin usar de `src/` (DIAG-23 incluido). Casi nada de esto toca código que sortea.
- **B — Duplicación de la simulación.** `genetic_algorithm.py`; en `main.py`, el reposicionamiento (con
  DIAG-27), los ticks, el reporte de fin de generación y los datos del popup fuera de `_simular`; los
  imports y variables sin usar de `main.py` que no están en la pantalla final. El CSV y el log tienen
  que salir idénticos.
- **C — Dibujo y reportes.** `dibujar_mundo`; la pantalla final a `src/ui/pantalla_final.py`, con
  DIAG-16 y DIAG-17; DIAG-14 y DIAG-15; el resto de Pylint; los tests; la mirada con ventana; el chequeo
  de cierre; las docs y `/close-spec`. Es el bloque más largo: si no entra en una sesión, el corte es
  después del commit de la pantalla final, y el chequeo de cierre, las docs y el cierre pasan a una
  cuarta.

## Relación con otros specs

- **Medir antes de tocar (cerrado):** la verificación usa sus piezas tal cual (`--semilla`, el CSV,
  `experimento.py`). Este spec no las cambia.
- **Modo guiado y modo autónomo (ítem 3):** recibe lo que salga de este spec por la decisión 8, y la
  sección "¿APRENDIERON?" de la pantalla final. Va a tocar el paso de la simulación en `_simular`, los
  `_try_*` de `advanced_agent.py`, `genetic_algorithm.py` y el puzzle de `world.py`, ya sin duplicación.
  Arma su propia línea base: desde ahí, comparar byte a byte contra esta ya no tiene sentido.

## Bitácora de ejecución

Formato: [`docs/AGENTES.md`](../../AGENTES.md) § "Specs de varias sesiones".

### Sesión 1 — 2026-11-14 — Bloque A
- **Hecho:**
  - Spec movido a `active/`, con el manifiesto, el BACKLOG y la memoria de proyecto
    (`spec-en-ejecucion`) al día.
  - **Línea base** desde `1ad83b9` (sin `.py` modificados): `experimento.py --semillas 1 2 3 4 5
    --generaciones 20`, en `results/linea_base_limpieza/` (10 CSV, 10 logs y `resumen.md`).
    **Control:** los 10 CSV, los 10 logs y el `resumen.md` (desde la línea 4) son idénticos a
    `results/experimento_20261114-160055/`. El comparador se copió del spec (verificado contra el
    bloque con `diff`) y se le volvió a hacer su control: un byte cambiado en la generación 7 de un
    CSV y una línea cambiada en un log; detectó los dos.
  - `.pyc`: `git rm --cached` de los 15 trackeados.
  - Código muerto (decisión 22): `src/agents/brain/`, `src/analytics/metrics.py`, la rama `"safe"`
    (`obstacles.py`; en `advanced_agent.py` queda `obstacle.type == "water"`, sin los dos `elif`),
    `save_data` (y `json`, que solo usaba él, y la llamada comentada en `main.py`) y
    `print_cluster_report`.
  - Imports y variables sin usar de `src/`: los 12 hallazgos, todos sin efecto (imports, dos
    constantes de `popup.py`, un `as e`). Pylint da 0 en `src/`.
  - `requirements.txt` con `pygame`, `numpy`, `scikit-learn` y `pytest`. **Instalación limpia**
    (Python 3.11.9, en el scratchpad): sin ninguno de los diez paquetes; `pytest` 11 de 11; chequeo
    rápido con ese Python, CSV y log idénticos. Instaló versiones más nuevas que el `.venv` (numpy
    2.4.6, scikit-learn 1.9.1, scipy 1.17.1) y el CSV no cambió.
  - `.env.example` borrado.
  - Docs: README (dependencias, estructura y módulos sin `brain/` ni `metrics.py`, obstáculos sin
    `safe`), `CLAUDE.md` (§ Stack, § Estructura, § Variables de entorno; las notas de código muerto
    y `.pyc` se fueron) y DIAG-18, DIAG-19, DIAG-20, DIAG-22 y DIAG-23 ✅ en `AnalisisQA.md`.
  - Commit: `limpieza: línea base y limpieza sin riesgo (bloque A)`.
- **Estados:**
  - DoD ✅: línea base, código muerto, `requirements.txt` con la instalación limpia, `.pyc` y
    `.env.example`. Parciales: chequeo completo por bloque (A ✅), Pylint (`src/` en 0; quedan los
    37 de `main.py`), `pytest` verde (hasta acá), docs (falta lo de B y C).
  - QA verificado: LIMPIEZA-01, LIMPIEZA-02 (6 CSV y 6 logs idénticos), LIMPIEZA-07, LIMPIEZA-08
    (después de las corridas, en `git status` los `.pyc` solo aparecen como borrados del índice) y
    LIMPIEZA-09. LIMPIEZA-10 parcial.
  - Decisión 8: no salió nada del spec.
  - **Tiempos medidos** (decisión 4): chequeo rápido 77 s; completo 2 min 49 s; 5 × 20 (línea base)
    8 min 27 s.
- **Desvíos del spec, y por qué:**
  - Pylint daba **53, no 54**, con el mismo comando y el mismo código que cuando se escribió el spec:
    37 en `main.py`, **12** en `src/` y 4 en el código muerto. Corrección anotada en `AnalisisQA.md`;
    el DoD (0 al cierre) no cambia.
  - README: también salió `src/analytics/logger.py`, que figuraba en la estructura y en los módulos y
    no existe (su `.pyc` era uno de los 15). Y `pytest` se sumó a la lista de librerías, como en
    `requirements.txt`. En `CLAUDE.md` § Stack salió "matplotlib: gráficos": ya nada lo importa.
  - En `popup.py`, el comentario "Escala fija del 0 al 100" se fue con las dos constantes que
    describía.
  - No quedó stub en `planned/`: Medir tampoco lo dejó al pasar a `active/`.
- **A medias o bloqueado:** nada bloqueado. Faltan los bloques B y C.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión — bloque B:**
  1. `git status -sb` y confirmar que `results/linea_base_limpieza/` tiene 10 CSV y 10 logs. Si
     falta, se regenera desde `1ad83b9` (con `git worktree`) y se vuelve a hacer el control de la
     decisión 2. Copiar el comparador de § El comparador al scratchpad con `Write`.
  2. **Antes de tocar el reposicionamiento, el control de LIMPIEZA-13, con Fer en la ventana:**
     `main.py --generaciones 3 --semilla 1 --csv results/zoom_antes/corrida_s1_evolucion.csv`,
     apretando `+` durante la generación 1, y comparar contra la línea base. Se espera otro CSV desde
     la generación 2; si da igual (nadie se reposicionó), se anota y vale la lectura. Este control se
     pierde si se hace después del cambio.
  3. `genetic_algorithm.py` (decisión 11 y la pista de código), chequeo rápido y lectura de los
     sorteos (decisión 7).
  4. `main.py`: el reposicionamiento con el alto del mundo (decisiones 12 y 13), los ticks, el
     reporte de fin de generación y los datos del popup, con un chequeo rápido después de cada uno.
     Después, LIMPIEZA-13 otra vez con Fer en la ventana (`results/zoom_despues/`): ahora el CSV
     tiene que ser igual a la línea base.
  5. Los 6 hallazgos de Pylint de `main.py` que no son de la pantalla final: líneas 17 (dos), 19
     (dos), 37 (`attempt`) y 257 (`population_size`; mirar que la parte derecha no sortee). Los 31
     de `show_final_screen` (líneas 873 a 1407) son del bloque C.
  6. Chequeo completo, bitácora y commit con confirmación.
  - **Trampas:** en el bloque B no cambia ni un `print`. LEC-002 en `main.py` y
    `genetic_algorithm.py` (CRLF, con muchas líneas en blanco con espacios). Los `.pyc` ya no están
    en el índice: no van a aparecer en `git status`.

### Sesión 2 — 2026-11-14 — Bloque B
- **Hecho:**
  - Línea base presente (10 CSV y 10 logs). Comparador copiado del spec y verificado con `diff`
    contra el bloque.
  - **Control de LIMPIEZA-13, antes del cambio.** Con Fer en la ventana, dos intentos: el `+` no
    llegó al juego (el log no tenía ningún `🔍 Zoom IN`; causa no determinada: teclado numérico, foco
    o distribución del teclado). Se hizo con las teclas inyectadas: un script del scratchpad
    envuelve `pygame.event.get`, mete dos `K_PLUS` en la generación 1 (1300×867 y 1400×934) y
    `K_RETURN` para cerrar la pantalla final, y cuenta los `randint(20, alto - 20)` con el alto
    agrandado. CSV de 3 generaciones igual a la línea base; log igual salvo las líneas del modo con
    ventana y las del zoom; **0 sorteos con el alto de la ventana**. El control no dio distinto,
    como preveía el spec: ese sorteo no corre. `fix_agent_positions` corre justo antes y ya saca a
    los agentes de fortalezas y obstáculos; el reposicionamiento solo mueve a alguien si
    `find_safe_position` cayó a `(100, 100)`, y eso no pasa en ninguna de las 10 corridas de la
    línea base.
  - **`genetic_algorithm.py`** (decisiones 11 y 15): `_choca`, `_posicion_libre` y
    `_posicion_de_respaldo`; las ramas `"elitism"` y método desconocido, juntas; sin los
    `if i < len(agents)`. 443 → 299 líneas, `randint(50, 900)` 3 veces, un solo bucle de 100.
    Chequeo rápido idéntico. Lectura de sorteos: mismas llamadas, mismos argumentos, mismo orden.
    **Prueba extra de las ramas que la config no usa** (usa `meeting_pool`): `elitism`,
    `tournament` y un método desconocido, semillas 1 y 2 × 7 generaciones, antes y después del
    cambio: CSV y log idénticos. Control: `elitism` da otro CSV que la línea base desde la
    generación 2, y el método desconocido da el mismo que `elitism`.
  - **`main.py`** (decisiones 12, 13, 15 y 16): `_reposicionar_agentes` (sortea con
    `world.screen_height`: DIAG-27), `_ticks_de_generacion`, `_imprimir_fin_de_generacion` y
    `_datos_del_popup`. En `_simular` quedan, en orden: fitness de todos → reporte → fila del CSV →
    datos del popup → monitor → evolución → reposicionamiento → comida. Salieron el
    `if fixed_count > 0: pass` con su contador, y el `if agents:`/`else` del reporte (con 0 agentes,
    `_fila_csv` ya dividía por cero: no era alcanzable). Chequeo rápido idéntico.
  - **El cuerpo de `_reposicionar_agentes` no corre en las semillas de la verificación,** así que se
    ejercitó aparte (script del scratchpad): mundo real, 5 agentes puestos sobre obstáculos, contra
    el bloque viejo sacado de `HEAD:main.py`; y forzando el respaldo (sin lugar libre: 500 intentos ×
    60 agentes y la grilla). Mismas posiciones, mismos sorteos, mismo estado final del azar y los
    mismos 60 avisos. Control: el bloque viejo con alto 867 da otros sorteos.
  - **Control de LIMPIEZA-13, después del cambio:** zoom inyectado, CSV igual, 0 sorteos con el
    alto de la ventana.
  - Pylint: los 6 hallazgos de `main.py` fuera de la pantalla final (imports de las líneas 17 y 19,
    `attempt`, `population_size`). Quedan los 31 de `show_final_screen`.
  - **Chequeo completo** (`experimento.py --semillas 1 2 3 --generaciones 12`): 6 CSV y 6 logs
    idénticos. `pytest` 11 de 11.
  - Docs: DIAG-27 ✅, DIAG-21 y DIAG-26 parciales en `AnalisisQA.md`; BACKLOG (ítem 2, y en el
    ítem 3 la nota del reposicionamiento que casi nunca mueve a nadie); LEC-004 y su regla en
    `CLAUDE.md` § Notas.
  - Commit: `limpieza: duplicación de la simulación (bloque B)`.
- **Estados:**
  - DoD ✅: DIAG-27. Parciales: chequeo completo por bloque (A y B ✅), Pylint (quedan 31, todos de
    la pantalla final), duplicación (falta el dibujo del mundo), estructura (falta mudar la
    pantalla final), `pytest` verde (hasta acá).
  - QA verificado: LIMPIEZA-03, LIMPIEZA-11 y LIMPIEZA-13 (el control no dio distinto: se anota y
    vale la lectura, con la medición y la prueba aparte de la rama). Parciales: LIMPIEZA-10 y
    LIMPIEZA-12 (reposicionamiento y ticks una vez cada uno, paso y fin de generación en
    `_simular`, sin clases nuevas; falta la pantalla final).
  - Decisión 8: no salió nada del spec.
  - **Tiempos medidos:** chequeo rápido 77-82 s; completo 3 min.
- **Desvíos del spec, y por qué:**
  - LIMPIEZA-13 con teclas inyectadas, no apretadas: el `+` de Fer no llegó dos veces (LEC-004).
    Las teclas inyectadas entran por el mismo manejador de eventos de `main.py`.
  - Los cuatro cambios de `main.py` entraron en una sola edición, con un chequeo rápido para todos y
    no uno por cambio. Dio idéntico, así que no hizo falta separar.
  - Más pruebas que las del spec (la decisión 7 pedía lectura para las ramas raras): las variantes
    de selección y la rama del reposicionamiento, ejercitadas aparte.
  - `genetic_algorithm.py` y `main.py` se editaron con scripts que reemplazan rangos de líneas
    verificados (extremos y unicidad), no con Edit: así no se tocan las líneas en blanco con espacios
    (LEC-002). `git diff` no muestra blancos cambiados fuera de lo reescrito.
- **A medias o bloqueado:** nada bloqueado. Falta el bloque C.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión — bloque C:**
  1. `git status -sb` y confirmar que `results/linea_base_limpieza/` tiene 10 CSV y 10 logs (si
     falta, se regenera desde `1ad83b9` con `git worktree` y se repite el control de la decisión 2).
     Copiar el comparador de § El comparador al scratchpad con `Write`.
  2. **Antes de tocar nada, los controles de antes, con Fer, en una sola corrida con ventana:**
     `main.py --generaciones 2 --semilla 1 --csv results/ventana_antes/corrida_s1_evolucion.csv`.
     Cuando el log muestre el `🏁` (la pantalla final abierta): (a) DIAG-17, CPU durante 10 s con el
     comando de PowerShell del spec (se espera ~10 s); (b) Fer mira la pantalla final: los cuatro
     textos de DIAG-16 sin cofre, el fondo y las partículas en movimiento (LIMPIEZA-18, antes);
     (c) Fer la cierra con ESC. El CSV, con el comparador contra la línea base. Estos controles se
     pierden si se hacen después del cambio.
  3. Los tests antes del código (decisión 10), corridos contra el código de hoy: el de DIAG-14 en
     `tests/test_reportes.py` y la verificación de `Tiempo simulado: 0.5 minutos` en `test_humo.py`.
     Los dos tienen que fallar. El de DIAG-16 llama a una función que todavía no existe: su control
     es la mirada del paso 2. Se commitean junto con los arreglos (el gate no deja commitear tests
     rojos).
  4. `dibujar_mundo` en `src/ui/renderer.py` (pista del spec), usado por el loop.
  5. La pantalla final a `src/ui/pantalla_final.py` (decisiones 17 a 20): el resumen por consola,
     la función que arma los textos sin dibujar (DIAG-16), la pantalla quieta, dibujada una vez con
     `dibujar_mundo`, y su loop con `clock.tick(30)` (DIAG-17), sin los 31 hallazgos de Pylint. DIAG-15:
     `_simular` suma los ticks de cada generación (también la parcial del cofre) y la consola y la
     pantalla muestran el mismo tiempo simulado. DIAG-14 en `learning_monitor.py`.
  6. Verificar: `pytest` (tests nuevos verdes), Pylint en 0, chequeo rápido. Después, con Fer, la
     misma corrida con ventana (`results/ventana_despues/`): CSV igual (LIMPIEZA-06), CPU menos de
     2 s (LIMPIEZA-17), los textos sin cofre (LIMPIEZA-16), fondo y quietud; ESC y ENTER cierran
     (LIMPIEZA-18).
  7. Chequeo completo (en los logs solo cambian las "Tasa:" de las generaciones 5 y 10:
     LIMPIEZA-04), bitácora y commit con confirmación. **Si el contexto no da para más, el corte es
     acá:** el cierre pasa a una cuarta sesión.
  8. Si da: chequeo de cierre 5 × 20 (LIMPIEZA-05, con el `diff` de `resumen.md` del spec), docs
     (README y `CLAUDE.md` § Estructura con `pantalla_final.py`; los DIAG ✅), `/close-spec`, y
     borrar la memoria `spec-en-ejecucion`.
  - **Trampas:** el chequeo rápido y el completo corren sin ventana: no ejercitan el dibujo ni la
    pantalla final con ventana; eso lo cubren las corridas de los pasos 2 y 6, y la lectura. Desde
    DIAG-14, el comparador va a mostrar las "Tasa:" como diferencias: cada una tiene que valer
    `vivos` / 60 de la fila del CSV de esa generación. La línea del tiempo del resumen final (DIAG-15)
    queda después del `🏁`: en las corridas cortas el comparador no la mira; en el 5 × 20, sí. En las
    corridas con ventana, mirar en el log que se llegó al `🏁` antes de medir, y que cada tecla dejó
    su `print` (LEC-004). Los scripts de esta sesión (teclas inyectadas, ramas raras) estaban en su
    scratchpad y se pierden: la técnica está en LEC-004 y en esta entrada.
