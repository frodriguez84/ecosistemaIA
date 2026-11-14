# Spec: Medir antes de tocar

**Estado:** 🔵 Planned — en diseño
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

- [ ] `python main.py --sin-ventana --generaciones 2 --semilla 7` corre sin editar `config.py`, sin
  abrir ventana, y termina después de 2 generaciones.
- [ ] `python main.py` sin flags abre la ventana con los valores de `config.py`, como hoy.
- [ ] `python main.py --help` lista los cinco flags con su descripción en español.
- [ ] Toda corrida imprime su semilla al arrancar y la ruta del CSV al terminar. Sin `--semilla`, la
  semilla se sortea y aparece en el CSV.
- [ ] Dos corridas con la misma semilla dan CSV idénticos byte a byte, con evolución y sin evolución.
- [ ] La misma semilla con ventana y sin ventana da el mismo CSV (2 generaciones).
- [ ] El CSV tiene exactamente las columnas de la decisión 6, una fila por generación, y cortar la
  corrida con Ctrl+C deja las generaciones terminadas escritas.
- [ ] Si se abre el cofre, el CSV tiene la fila de esa generación con `cofre = 1`.
- [ ] Con `--sin-evolucion`, cada generación arranca con cerebros al azar, y la generación 1 es igual
  a la de la corrida con evolución de la misma semilla (salvo la columna `evolucion`).
- [ ] `python main.py --sin-ventana --generaciones 1 > corrida.log` termina sin error de encoding.
- [ ] `python experimento.py --semillas 1 2 --generaciones 10 --paralelo 2` deja 4 CSV, 4 logs y
  `resumen.md` en su carpeta, y el resumen trae lo de las decisiones 13 y 14.
- [ ] `python -m pytest -q` pasa (`test_humo.py` y `test_resumen.py`) en menos de 90 segundos.
- [ ] El gate pre-commit ya no acepta el código 5 y compila `experimento.py` y `tests/`.
- [ ] El diff no toca `src/agents/`, `src/world/` ni `src/evolution/`: la simulación no cambió.
- [ ] El experimento completo (5 semillas × 20 generaciones × 2 modos) está corrido y registrado en
  `AnalisisQA.md`, con su lectura, junto al experimento de una semilla del diagnóstico.
- [ ] Docs al día: README § "Instalación y Uso" con los flags y `experimento.py`; la línea
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

_(vacía — la primera sesión agrega su entrada al cerrar, con el formato de
[`docs/AGENTES.md`](../../AGENTES.md) § "Specs de varias sesiones")_
