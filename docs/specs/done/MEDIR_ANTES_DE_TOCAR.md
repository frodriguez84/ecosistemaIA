# Spec: Medir antes de tocar

**Estado:** ✅ Implementado (2026-11-14)
**Prioridad:** Alta — sin medición, cada cambio al aprendizaje se evalúa a ojo (LEC-001), y la
limpieza no tiene cómo probar que no cambió nada.
**Gate:** Ninguno
**Bloquea:** Limpieza sin cambiar comportamiento (BACKLOG ítem 2) · Modo guiado y modo autónomo (ítem 3)
**Depende de:** [diagnóstico inicial](../../qa/AnalisisQA.md#diagnostico-inicial) (DIAG-06, DIAG-07,
DIAG-25 y el experimento)

---

## Problema

- **No hay semilla (DIAG-06).** Dos corridas iguales dan números distintos, así que no se puede
  saber si un cambio movió algo o si fue el azar. El README dice "semillas y configuración
  determinística" y no es verdad.
- **Para correr sin ventana hay que editar `config.py` (DIAG-07).** No hay parámetros por línea de
  comando, y esos cambios de prueba quedan sueltos en el árbol de trabajo.
- **Con la salida redirigida a un archivo, `main.py` se cae (DIAG-25).** En Windows, la salida
  redirigida usa cp1252 y el primer `print` con emoji tira `UnicodeEncodeError`. Correr varias
  simulaciones en tanda y guardar su log hoy es imposible.
- **Las métricas solo salen por consola.** Para comparar dos corridas hay que copiar números a mano.
- **El experimento del diagnóstico es una sola corrida con una semilla:** un indicio, no una
  conclusión. El script que lo corrió vivió en el scratchpad y no quedó en el repo.
- **Sin semilla no hay forma de verificar la limpieza** (ítem 2): "mismos números antes y después"
  necesita corridas que se puedan repetir.

## Objetivo

Correr la simulación desde la línea de comando, con semilla, y obtener un CSV por corrida que se
pueda repetir byte a byte. Con eso, un comando corre el experimento "con evolución contra sin
evolución" en varias semillas y devuelve una tabla que dice si la evolución aprende más que el
azar. Un test de humo cuida que todo esto siga andando.

## Qué NO es esta feature

- **No cambia la simulación.** Ni el aprendizaje, ni la guía escrita a mano, ni el fitness, ni el
  mundo, ni el puzzle. Lo único nuevo adentro de la simulación es que el azar se siembra.
- **No apaga la guía.** La hipótesis "lo que evoluciona es caminar derecho y la guía hace comer" se
  mide cuando exista el switch guiado/autónomo (ítem 3).
- **No limpia ni arregla reportes.** La duplicación de `main.py` y DIAG-14 a DIAG-17 son de la
  limpieza (ítem 2).
- **No expone otros parámetros de `config.py`** por línea de comando (población, ticks, mutación).
  Se suman cuando un experimento los necesite.
- **No hace gráficos ni pruebas estadísticas formales.** El resumen es una tabla con promedio,
  desvío y conteo por semilla.
- **No toca `LearningMonitor`** ni sus reportes por consola, ni guarda cerebros o checkpoints.

## Decisiones cerradas

| # | Decisión |
|---|----------|
| 1 | **Flags en español, con `argparse`:** `--sin-ventana`, `--generaciones N`, `--semilla S`, `--sin-evolucion`, `--csv RUTA`. Sin flags, `python main.py` corre como hoy, con los valores de `config.py` (y además escribe el CSV). Los flags pisan los atributos **de la clase** `SimulationConfig` antes de que nada los lea. |
| 2 | **Semilla:** `random.seed(s)` y `np.random.seed(s)` al arrancar `main()`, antes de crear el mundo. Sin `--semilla`, se sortea una con `random.SystemRandom`, se imprime y queda en el CSV: cualquier corrida se puede repetir. |
| 3 | **Las partículas usan su propio `random.Random()`.** Hoy `ParticleSystem.add_food_effect` (`src/ui/renderer.py:241-257`) usa el `random` global, y solo corre con ventana: con la misma semilla, la corrida con ventana se desviaría de la sin ventana. Con un generador propio, el dibujo no consume el azar de la simulación. |
| 4 | **"Reproducible" quiere decir CSV idéntico byte a byte.** El CSV no lleva hora, fecha, duración real ni nada que cambie entre dos corridas iguales. Los decimales van redondeados a 4. |
| 5 | **Un CSV por corrida, una fila por generación,** escrita y vaciada (`flush`) al terminar cada generación: una corrida cortada deja sus generaciones completas. Se escribe siempre, con ventana o sin ella. UTF-8, separador coma. |
| 6 | **Columnas, en este orden:** `semilla, evolucion, generacion, ticks, fitness_prom, fitness_max, fitness_min, fitness_desvio, manzanas_prom, manzanas_max, vivos, distancia_prom, diversidad, arboles_cortados, llave_roja, puerta_madera, llave_dorada, puerta_hierro, cofre`. `evolucion` y las cinco del puzzle valen 0 o 1. |
| 7 | **Las columnas del puzzle son el estado del mundo al final de la generación,** no lo que logró esa generación: el puzzle se acumula entre generaciones (DIAG-04). |
| 8 | **Ruta por defecto:** `results/corrida_s<semilla>_<evolucion\|sin_evolucion>.csv` (`results/` ya está en `.gitignore`). Si el archivo existe, se pisa y se avisa por consola. `--csv` elige otra ruta. |
| 9 | **Si se abre el cofre,** la corrida termina como hoy, pero antes escribe la fila de esa generación (parcial) con `cofre = 1`. |
| 10 | **Línea base:** `--sin-evolucion` reemplaza `ga.evolve(agents, generation)` (`main.py:506`) por `ga._create_random_population()`: cada generación arranca con cerebros al azar y no hereda nada. Todo lo demás (mundo, guía, puzzle persistente, tiempo adaptativo) queda igual. Es el experimento del diagnóstico. Con la misma semilla, la generación 1 sale idéntica en los dos modos. |
| 11 | **Salida en UTF-8:** `main.py` reconfigura `stdout` y `stderr` a UTF-8 al arrancar, antes del primer `print` (DIAG-25). Así `python main.py --sin-ventana > corrida.log` funciona. |
| 12 | **`experimento.py` en la raíz** corre semillas × {con evolución, sin evolución} como subprocesos de `main.py --sin-ventana`, en paralelo. Flags: `--semillas` (por defecto 1 a 5), `--generaciones` (por defecto 20, mínimo 10), `--paralelo K` (por defecto, núcleos − 1). Cada corrida deja su CSV y su log en `results/experimento_<AAAAMMDD-HHMMSS>/`. |
| 13 | **Resumen por corrida:** fitness promedio de las generaciones 1-5 y de las últimas 5, y su diferencia; lo mismo para manzanas por agente; etapa del puzzle en la última generación (0 a 5, la suma de las cinco columnas); generación en que se abrió el cofre, si se abrió. |
| 14 | **Resumen por modo:** promedio y desvío entre semillas de cada número de la decisión 13. **Comparación pareada por semilla:** "la evolución subió más que la línea base en K de N semillas", para fitness y para manzanas. Sale como tabla Markdown por consola y en `resumen.md`, para pegar tal cual en `AnalisisQA.md`. |
| 15 | **Test de humo:** `tests/test_humo.py` corre `main.py` como subproceso, con sus flags reales, 2 generaciones y semilla fija. Verifica: (a) sale con código 0; (b) el CSV tiene el encabezado de la decisión 6 y 2 filas; (c) dos corridas con la misma semilla dan CSV idénticos; (d) `--sin-evolucion` corre y su generación 1 es igual a la de la corrida con evolución. Las corridas se lanzan en paralelo. |
| 16 | **Test del resumen:** `tests/test_resumen.py` le pasa al resumen CSV armados a mano y verifica sus números. Es lo que produce las conclusiones: si cuenta mal, la conclusión es falsa. |
| 17 | **El gate pre-commit** deja de aceptar el código 5 de pytest ("no hay tests") y compila también `experimento.py` y `tests/`. |
| 18 | **El resumen usa solo la librería estándar** (`csv`, `statistics`), sin pandas: la limpieza va a revisar qué dependencias sobran. |

## Criterios de done (DoD)

- [x] `python main.py --sin-ventana --generaciones 2 --semilla 7` corre sin editar `config.py`, sin
  abrir ventana, y termina después de 2 generaciones.
- [x] `python main.py` sin flags abre la ventana con los valores de `config.py`, como hoy.
- [x] `python main.py --help` lista los cinco flags con su descripción en español.
- [x] Toda corrida imprime su semilla al arrancar y la ruta del CSV al terminar. Sin `--semilla`, la
  semilla se sortea y aparece en el CSV.
- [x] Dos corridas con la misma semilla dan CSV idénticos byte a byte, con evolución y sin evolución.
- [x] La misma semilla con ventana y sin ventana da el mismo CSV (2 generaciones).
- [x] El CSV tiene exactamente las columnas de la decisión 6, una fila por generación, y cortar la
  corrida con Ctrl+C deja las generaciones terminadas escritas.
- [x] Si se abre el cofre, el CSV tiene la fila de esa generación con `cofre = 1`.
- [x] Con `--sin-evolucion`, cada generación arranca con cerebros al azar, y la generación 1 es igual
  a la de la corrida con evolución de la misma semilla (salvo la columna `evolucion`).
- [x] `python main.py --sin-ventana --generaciones 1 > corrida.log` termina sin error de encoding.
- [x] `python experimento.py --semillas 1 2 --generaciones 10 --paralelo 2` deja 4 CSV, 4 logs y
  `resumen.md` en su carpeta, y el resumen trae lo de las decisiones 13 y 14.
- [x] `python -m pytest -q` pasa (`test_humo.py` y `test_resumen.py`) en menos de 90 segundos.
- [x] El gate pre-commit ya no acepta el código 5 y compila `experimento.py` y `tests/`.
- [x] El diff no toca `src/agents/`, `src/world/` ni `src/evolution/`: la simulación no cambió.
- [x] El experimento completo (5 semillas × 20 generaciones × 2 modos) está corrido y registrado en
  `AnalisisQA.md`, con su lectura, junto al experimento de una semilla del diagnóstico.
- [x] Docs al día: README § "Instalación y Uso" con los flags y `experimento.py`; la línea
  "Reproducibilidad: semillas y configuración determinística" pasa a ser verdad; `CLAUDE.md`
  § Notas ("Para correr sin ventana hoy hay que editar `config.py`") y § Convenciones
  ("Todavía no hay suite") actualizados; DIAG-06, DIAG-07 y DIAG-25 marcados ✅ en `AnalisisQA.md`.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| MEDIR-01 | `python main.py --sin-ventana --generaciones 2 --semilla 7` | Sin ventana, 2 generaciones, sale con código 0, imprime la semilla y la ruta del CSV |
| MEDIR-02 | `python main.py` sin flags | Abre la ventana con los valores de `config.py` y escribe el CSV |
| MEDIR-03 | `python main.py --help` | Lista los cinco flags, en español |
| MEDIR-04 | Misma semilla dos veces, con evolución | CSV idénticos byte a byte |
| MEDIR-05 | Misma semilla dos veces, `--sin-evolucion` | CSV idénticos byte a byte |
| MEDIR-06 | Misma semilla con ventana y sin ventana, 2 generaciones | Mismo CSV |
| MEDIR-07 | Corrida sin `--semilla` | Imprime una semilla sorteada; repetirla con esa semilla da el mismo CSV |
| MEDIR-08 | Encabezado y filas del CSV | Columnas de la decisión 6, en orden; una fila por generación |
| MEDIR-09 | Cortar con Ctrl+C en la generación 3 | El CSV tiene las filas de las generaciones 1 y 2, completas |
| MEDIR-10 | Generación 1, con evolución y `--sin-evolucion`, misma semilla | Filas iguales salvo `evolucion` |
| MEDIR-11 | `--sin-evolucion`, generaciones 2 en adelante | La diversidad queda cerca de la de la generación 1: cada generación es una población al azar |
| MEDIR-12 | Salida redirigida a archivo | Sin `UnicodeEncodeError`; el log tiene los emojis |
| MEDIR-13 | `python experimento.py --semillas 1 2 --generaciones 10 --paralelo 2` | 4 CSV, 4 logs y `resumen.md` |
| MEDIR-14 | `python experimento.py --generaciones 5` | Error claro: el mínimo es 10 |
| MEDIR-15 | Números del resumen | Coinciden con un cálculo a mano sobre los CSV de MEDIR-13 |
| MEDIR-16 | `python -m pytest -q` | Verde, en menos de 90 s |
| MEDIR-17 | Gate pre-commit con un test roto | Bloquea el commit |
| MEDIR-18 | Experimento completo: 5 semillas × 20 generaciones | Corrido y registrado en `AnalisisQA.md` con su lectura |
| MEDIR-19 | Diff del spec | No toca `src/agents/`, `src/world/` ni `src/evolution/` |
| MEDIR-20 | Corrida en la que se abre el cofre | La última fila es la de esa generación, con `cofre = 1`. Si ninguna corrida del QA lo abre, se verifica leyendo el código |

## Implementación

**`main.py`**
- `main(argv=None)` con `argparse`; `if __name__ == "__main__": main()`.
- Lo primero de `main()`: reconfigurar `sys.stdout` y `sys.stderr` a UTF-8, leer los flags, pisar
  `SimulationConfig.HEADLESS_MODE` y `SimulationConfig.MAX_GENERATIONS` **en la clase**, y sembrar.
  `show_final_screen` lee `SimulationConfig.HEADLESS_MODE` directo de la clase (`main.py:749`): si se
  pisa en la instancia, la pantalla final sin ventana intenta dibujar.
- La fila del CSV sale de los mismos valores que hoy se imprimen al final de la generación
  (`main.py:409-477`), más `fitness_desvio` y `distancia_prom`. Conviene una función que arme la fila,
  porque se usa en dos lugares: al final de cada generación y al abrirse el cofre (`main.py:355-361`,
  que hoy hace `return` sin registrar nada). En ese segundo lugar hay que llamar antes a
  `_calculate_fitness()` en todos los agentes, como hace el final de generación.
- `main()` sale por varios `return`: el archivo del CSV se abre con `with` (o `try/finally`) para que
  se cierre en todos.

**`src/ui/renderer.py`**
- `ParticleSystem` guarda un `random.Random()` propio y lo usa en lugar del módulo `random`.

**`experimento.py`**
- Lanza `[sys.executable, "main.py", "--sin-ventana", ...]` con `cwd` en la raíz, la salida a un log
  por corrida, desde un `ThreadPoolExecutor(max_workers=K)` (alcanza con hilos: el trabajo lo hacen
  los subprocesos). `sys.executable` hace que use el Python del `.venv`.
- Una corrida que falla queda marcada en el resumen con la ruta a su log; no frena las demás.

**`tests/`**
- `test_humo.py`: los CSV van a `tmp_path` con `--csv`. Las tres corridas (dos con evolución y una
  sin) se lanzan juntas con `subprocess.Popen` y se esperan con timeout.
- `test_resumen.py`: CSV de 10 generaciones armados a mano, con números redondos.

**Trampas conocidas**
- Una corrida sin ventana tarda ~10 s por generación con 60 agentes, y las generaciones se alargan
  (+180 ticks cada 4). El experimento completo (10 corridas de 20 generaciones) tarda del orden de
  10 a 15 minutos con 4 en paralelo: correrlo en segundo plano.
- Las generaciones más largas suben el fitness y las manzanas aunque no haya aprendizaje: por eso la
  comparación es contra la línea base, nunca contra el número inicial.
- `results/` está en `.gitignore`: los CSV no se commitean. Lo que queda en el repo es el resumen
  pegado en `AnalisisQA.md`.

## Edge cases

- **Cofre antes de la última generación:** la corrida queda más corta. Si terminó en 10 generaciones
  o más, las ventanas se toman sobre las que tiene; si terminó antes de 10, queda fuera de las
  ventanas y el resumen lo dice. La generación del cofre se informa siempre.
- **Corrida que falla en el experimento:** el resumen se arma con las que terminaron y lista las que
  no, con su log.
- **Dos experimentos a la vez:** no chocan, cada uno tiene su carpeta con fecha y hora.
- **Con ventana y `--generaciones`:** al terminar se ve la pantalla final, como hoy.

## Esfuerzo

Dos sesiones, en secuencia:
- **A:** `main.py` (flags, semilla, CSV, UTF-8), partículas, `test_humo.py`, gate.
- **B:** `experimento.py` y el resumen, `test_resumen.py`, correr el experimento completo, registrarlo
  y actualizar las docs.

## Relación con otros specs

- **Limpieza (ítem 2):** la verifica con `--semilla` y CSV idénticos byte a byte antes y después del
  cambio. Esa comparación ya funciona con estas piezas: no necesita nada más de este spec.
- **Modo guiado y modo autónomo (ítem 3):** va a sumar un flag de modo y una columna en el CSV, y el
  resumen va a comparar por esa columna. Este spec no lo anticipa.

## Bitácora de ejecución

Formato: [`docs/AGENTES.md`](../../AGENTES.md) § "Specs de varias sesiones".

### Sesión 1 — 2026-11-14 — Bloque A
- **Hecho:**
  - `main.py`: `main(argv=None)` reconfigura `stdout` y `stderr` a UTF-8, lee los flags con
    `argparse` (también `-h` en español), pisa `HEADLESS_MODE` y `MAX_GENERATIONS` en la clase y
    siembra `random` y `np.random`. El cuerpo de la simulación pasó a
    `_simular(semilla, evolucion, escribir_fila)`. Sus únicos cambios son la fila del CSV, al final
    de cada generación y al abrirse el cofre, y el switch de `--sin-evolucion` (decisión 10). La
    fila la arma `_fila_csv()`.
  - `src/ui/renderer.py`: `ParticleSystem` usa su propio `random.Random()`.
  - `tests/test_humo.py`: 4 tests sobre 3 corridas en paralelo; tarda unos 18 s.
  - Gate pre-commit: el código 5 de pytest ya bloquea, y compila también `tests/`.
  - Spec movido a `active/`, con el manifiesto, el BACKLOG y la memoria de proyecto al día.
  - LEC-002 (el Edit vacía las líneas en blanco con espacios) y su regla en `CLAUDE.md` § Notas.
  - Commit: `medir: flags, semilla, CSV por generación y test de humo (bloque A)`.
- **Estados:**
  - DoD: los diez primeros criterios ✅. Quedan parciales tres: `pytest` (falta
    `test_resumen.py`), el gate (falta compilar `experimento.py`) y "el diff no toca `src/agents/`,
    `src/world/` ni `src/evolution/`" (✅ hasta acá, vale para el spec entero).
  - QA verificado con corridas: MEDIR-01 a MEDIR-10, MEDIR-12, MEDIR-17 y MEDIR-19. MEDIR-16 vale
    solo para `test_humo.py`. MEDIR-20 se verificó leyendo el código, porque ninguna corrida abrió el
    cofre: ni las de 2 generaciones ni una de 13 con ventana.
  - MEDIR-11 tiene un indicio con 2 generaciones, semilla 7: sin evolución, la diversidad pasa de
    0,2283 a 0,2288; con evolución baja a 0,2204. Se confirma en B, con 10 generaciones o más.
  - Para B: MEDIR-13, MEDIR-14, MEDIR-15 y MEDIR-18.
- **Desvíos del spec, y por qué:**
  - Gate (decisión 17): `experimento.py` todavía no está en el `compileall` porque no existe.
    `compileall` con una ruta que no existe falla, y bloquearía todo commit de código. Lo suma B.
  - MEDIR-09: el Ctrl+C se simuló con `_thread.interrupt_main()`, que levanta `KeyboardInterrupt` en
    el hilo principal, igual que Ctrl+C. Cortada en la generación 3, la corrida dejó las
    generaciones 1 y 2, iguales byte a byte a las de la corrida completa. El script quedó en el
    scratchpad, no en el repo.
  - Detalles que el spec no fijaba: la semilla sorteada va de 0 a 999.999, para que sea cómoda de
    tipear. `--generaciones` menor que 1 y `--semilla` fuera de 0 a 2³² − 1 (el rango de numpy) dan
    error de `argparse`. Los encabezados `usage:` y `options:` de `argparse` quedan en inglés.
- **A medias o bloqueado:** nada bloqueado. Falta todo el bloque B.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión:** bloque B.
  - **Primer paso:** el resumen como función pura, con `tests/test_resumen.py` primero (decisión 16,
    CSV armados a mano con números redondos).
  - **Después, en orden:** `experimento.py` (lanzador y `resumen.md`); MEDIR-13, MEDIR-14 y
    MEDIR-15; sumar `experimento.py` al `compileall` de `.claude/hooks/pre-commit-gate.sh`; el
    experimento completo en segundo plano (MEDIR-18), registrado en `AnalisisQA.md` junto al de una
    semilla del diagnóstico; y el último ítem del DoD (README, `CLAUDE.md` § Notas y
    § Convenciones, DIAG-06, DIAG-07 y DIAG-25 ✅). B es el último bloque: con el DoD completo, se
    cierra con `/close-spec docs/specs/active/MEDIR_ANTES_DE_TOCAR.md` (corre `/qa-spec`), y se
    borra la memoria de proyecto `spec-en-ejecucion`.
  - **Trampa:** la salida redirigida a archivo sale con buffer. Si una corrida se mata, su log
    pierde la cola, y un script que lee el log de otra corrida mientras corre necesita `python -u`
    o `PYTHONUNBUFFERED=1`. En esta sesión eso dejó abierta 5 minutos la ventana de MEDIR-02.
  - **Trampa:** tiempos medidos en esta máquina (12 núcleos): 2 generaciones sin ventana tardan
    unos 15 s con el arranque, unos 6 s por generación de 960 ticks; 3 corridas en paralelo, unos
    18 s. La nota de `CLAUDE.md` ("~10 s por generación") queda vieja: corregirla con las docs.
  - **Trampa:** `main.py` necesita el `cwd` en la raíz, porque los sprites se cargan con la ruta
    relativa `assets/sprites`.
  - **Trampa:** después de editar código, revisar `git diff` por líneas en blanco vaciadas (LEC-002).
    El `.pyc` de `src/ui/__pycache__/renderer` aparece modificado: no stagearlo.

### Sesión 2 — 2026-11-14 — Bloque B
- **Hecho:**
  - `experimento.py`: el resumen son funciones puras (`resumir_corrida`, `resumir_modo`,
    `comparar_por_semilla`, `resumen_markdown`) que usan solo `csv` y `statistics`. El lanzador
    corre `main.py --sin-ventana` por semilla y modo desde un `ThreadPoolExecutor`, y escribe
    `resumen.md`.
  - `tests/test_resumen.py`, escrito antes que el resumen: 7 tests con CSV armados a mano. Cubren
    las ventanas (con 12 generaciones, para que se note si "las últimas 5" están mal), el cofre antes
    y después de 10 generaciones, promedio y desvío, la comparación pareada (con un empate y una
    semilla sin línea base) y el Markdown. Suite completa: 11 tests en 18 s.
  - Gate pre-commit: compila también `experimento.py`.
  - Experimento completo corrido y registrado en `AnalisisQA.md` § "Experimento en cinco
    semillas", con su lectura: la evolución sube más que la línea base en 5 de 5 semillas.
  - Docs: README (flags, experimento, tests, la línea de reproducibilidad), `CLAUDE.md` (stack,
    árbol de carpetas, § Convenciones, § Notas con el tiempo medido); DIAG-06, DIAG-07 y DIAG-25 ✅.
- **Estados:**
  - DoD completo.
  - QA verificado con corridas: MEDIR-13; MEDIR-14 (sale con código 2 y no crea carpeta);
    MEDIR-15 (recalculado con `awk` sobre los CSV de MEDIR-13, sin usar `experimento.py`);
    MEDIR-16 (11 tests, 18 s); MEDIR-18; MEDIR-19 (el diff del spec entero solo toca
    `src/ui/renderer.py` dentro de `src/`).
  - MEDIR-11 confirmado: sin evolución, la diversidad se queda en 0,23 en 10 y en 20 generaciones;
    con evolución baja a ~0,10 en la 20.
  - MEDIR-20 sigue verificado leyendo el código: ninguna corrida abrió el cofre.
  - `/qa-spec`: APROBADO, 16/16 (`AnalisisQA.md` § "QA /qa-spec — Medir antes de tocar"). Los
    checkers no podían ejecutar `main.py`, así que C1, C3, C4, C5 y C10 se volvieron a correr
    frescos, sin ventana.
- **Desvíos del spec, y por qué:**
  - El resumen vive en `experimento.py`, no en un módulo aparte: es el único que lo usa, y el test
    lo importa de ahí.
  - Detalles que el spec no fijaba: el desvío es muestral (`statistics.stdev`), y con una sola
    semilla se muestra solo el promedio. Un empate no cuenta como "la evolución subió más".
    `experimento.py` lanza `main.py` con `python -u`, para que el log se escriba mientras corre y
    una corrida cortada no pierda la cola. Sale con código 1 si falló alguna corrida, descarta las
    semillas repetidas (pisarían su propio CSV) y valida el rango de la semilla igual que `main.py`.
- **A medias o bloqueado:** nada. **Cerrado** el 2026-11-14 con `/close-spec`: movido a `done/`,
  con su resumen en `docs/archive/SPECS_ARCHIVO.md`.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión:** ninguna de este spec. Lo que sigue es el ítem 2 del BACKLOG (limpieza sin
  cambiar comportamiento). Esa limpieza se verifica con `--semilla` y CSV idénticos byte a byte antes
  y después de cada cambio.
  - **Trampa:** las corridas con evolución tardan más que las de la línea base (515 s contra 375 s
    con 20 generaciones, 10 corridas a la vez), porque los agentes caminan y comen más. El
    experimento completo tarda lo que tarda la corrida con evolución más lenta.
  - **Trampa:** cada `experimento.py` deja una carpeta nueva en `results/` (en `.gitignore`): se
    acumulan.
