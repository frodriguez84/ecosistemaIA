# Specs implementados — archivo

Resumen operativo de cada spec cerrado: qué hace, dónde está y dónde está su QA. El detalle de
diseño queda en el spec, en [`../specs/done/`](../specs/done/). El más nuevo arriba.

---

## Modo guiado y modo autónomo {#modo-guiado-y-autonomo}

**Spec:** [MODO_GUIADO_Y_AUTONOMO](../specs/done/MODO_GUIADO_Y_AUTONOMO.md) · cerrado el 2026-11-15,
en cinco sesiones (autoría, los bloques A, B y C, y el cierre).

**Qué hace:** dos modos con un switch (`MODO` en `config.py`, `--modo`) que difieren solo en la
conducción escrita a mano. En el autónomo, `decide()` es la salida de la red recortada a [0, 1] y no
consume azar. Mundo, puzzle, sensores, golpear y fitness son los mismos en los dos. El puzzle pasa a
ser de cada agente y de cada generación: la red lo ve con una brújula y lo acciona golpeando.
`config.py` manda en energía, consumo, comida, visión, radio, agua, costo de golpear y pesos del
fitness. `experimento.py` compara cada modo contra su línea base sin evolución, y los modos entre sí.

**Alcance:**
- Bloque A, las reglas mandan: `AGENT_ENERGY`, `AGENT_ENERGY_CONSUMPTION` (0,10), `AGENT_ENERGY_GAIN_FOOD`
  (8), `VISION_RANGE`, `AGENT_RADIUS` (6), `TREE_CUT_REWARD`, `WATER_ENERGY_LOSS`, `WATER_PENALTY_MAX` y
  los `FITNESS_*` se leen de `config.py`. Arreglados DIAG-08 (el acumulador `cut_rewards`), DIAG-09 (sin
  contadores de obstáculos), DIAG-10 (sensor 7 en [0, 1)), DIAG-11 (tope del agua) y DIAG-13. Una sola
  ubicación de agentes por generación, después de `reset_food()` (`_ubicar_agentes` y `_lugar_libre`,
  en `main.py`); el genético ya no ubica. Ids por contador de corrida. `edad_prom` en el CSV.
- Bloque B, el puzzle por agente: etapa (0 a 5) y hacha de cada agente; una puerta es pared para cada
  uno hasta que él la abre; las llaves y el hacha se agarran por contacto y quedan en el mapa;
  puertas, cofre, árboles y casitas piden golpear (quinta salida, `HIT_ENERGY_COST`). Todo vuelve a 0
  en cada generación, y abrir el cofre no termina la corrida. 11 entradas (la etapa y la brújula al
  próximo paso) y 5 salidas. La guía apunta al próximo paso del agente. Columnas `agentes_*` en el
  CSV; consola, popup, panel y pantalla final cuentan agentes por paso.
- Bloque C, el switch: `MODO` y `--modo`; la columna `modo` y la ruta
  `results/corrida_s<semilla>_<modo>_<evolucion|sin_evolucion>.csv`; `experimento.py --modos`, con
  grupos modo × evolución y tres comparaciones K de N (`comparar_evolucion`, `comparar_modos`). La
  pantalla final con "LA CORRIDA" y la línea de LEC-001, sin `→`; `popup.py` sin el 50; el panel
  muestra el modo.
- Tests: `test_reglas.py`, `test_puzzle.py` y `test_modos.py`, nuevos, y `test_humo.py`,
  `test_resumen.py` y `test_reportes.py` al día: 53 en ~23 s.
- No cambia el algoritmo genético ni el mapa (salvo que la llave roja y el hacha se sortean en cada
  generación).

**Resultado** (5 semillas × 30 generaciones, los dos modos, con evolución y sin ella): sin guía, la
evolución aprende a comer y a caminar (5 de 5 semillas contra su línea base); la guía suma ~0,4
manzanas por agente encima del aprendizaje, no lo reemplaza; el puzzle no se aprende más allá de la
llave roja, que sube porque caminan más. Detalle en
[AnalisisQA § experimento de cierre](../qa/AnalisisQA.md#experimento-modos-cierre).

**QA:** [AnalisisQA § QA /qa-spec — Modo guiado y modo autónomo](../qa/AnalisisQA.md#qa-modo-guiado-y-autonomo),
APROBADO 29/29 (la primera pasada dio BLOQUEADO por dos números del README; se arregló en la sesión).
Resuelve DIAG-01 a DIAG-05, DIAG-08 a DIAG-13, DIAG-28 y DIAG-29.

---

## Limpieza sin cambiar comportamiento {#limpieza-sin-cambiar-comportamiento}

**Spec:** [LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO](../specs/done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) ·
cerrado el 2026-11-14, en cuatro sesiones.

**Qué hace:** deja el código más chico y los reportes diciendo la verdad, sin cambiar la
simulación. Con la misma semilla, cada CSV sale idéntico byte a byte al de la línea base
(generada desde `1ad83b9`), con evolución y sin ella, y el experimento registrado de 5 semillas ×
20 generaciones se repite idéntico.

**Alcance:**
- Fuera: `src/agents/brain/`, `src/analytics/metrics.py`, la rama de zonas `"safe"`, `save_data`,
  `print_cluster_report`, los 15 `.pyc` del índice, `.env.example` y los 53 imports y variables sin
  usar que marcaba Pylint (`W0611`, `W0612`, `W0404`).
- `requirements.txt`: solo `pygame`, `numpy`, `scikit-learn` y `pytest` (salieron diez paquetes,
  `torch` entre ellos).
- `src/evolution/genetic_algorithm.py` (443 → 299 líneas): `_choca`, `_posicion_libre` (el único
  bucle de 100 intentos) y `_posicion_de_respaldo`. Cada llamador conserva su respaldo.
- `main.py` (1.391 → 725 líneas): `_reposicionar_agentes` (sortea con el alto del mundo, no con el
  de la ventana: DIAG-27), `_ticks_de_generacion`, `_imprimir_fin_de_generacion` y
  `_datos_del_popup`. El paso de la simulación y el fin de generación siguen en línea en `_simular`.
- `src/ui/renderer.py`: `dibujar_mundo`, que usan el loop y la pantalla final.
- `src/ui/pantalla_final.py`: la pantalla final, que se dibuja una vez y queda quieta.
  `textos_del_cuadro` arma los textos sin dibujar. Dice si se abrió el cofre (DIAG-16), muestra el
  tiempo simulado (DIAG-15) y gasta 0,19 s de CPU cada 10 s, contra 56 s antes (DIAG-17).
- `src/analytics/learning_monitor.py`: la "Tasa:" de supervivencia divide por los agentes de la
  generación (DIAG-14).
- Tests: `tests/test_reportes.py` (DIAG-14 y DIAG-16) y el tiempo simulado en `tests/test_humo.py`;
  17 en total.
- No cambia la simulación, ni `experimento.py`, ni las columnas del CSV.

**Cómo se verificó:** el comparador del spec (CSV byte a byte y log normalizado) contra una sola
línea base: después de cada cambio (semillas 1 y 2 × 7 generaciones), al cierre de cada bloque
(3 × 12) y al final (5 × 20). En los logs solo cambian las líneas de DIAG-14 y DIAG-15.

**QA:** [AnalisisQA § QA /qa-spec — Limpieza sin cambiar comportamiento](../qa/AnalisisQA.md#qa-limpieza-sin-cambiar-comportamiento),
APROBADO 22/22. Resuelve DIAG-14 a DIAG-21, DIAG-23, DIAG-26, DIAG-27 y lo que quedaba de DIAG-22.

---

## Medir antes de tocar {#medir-antes-de-tocar}

**Spec:** [MEDIR_ANTES_DE_TOCAR](../specs/done/MEDIR_ANTES_DE_TOCAR.md) · cerrado el 2026-11-14,
en dos sesiones.

**Qué hace:** la simulación corre desde la línea de comando, con semilla, y cada corrida deja un
CSV con una fila por generación que se repite byte a byte con la misma semilla. `experimento.py`
corre "con evolución contra sin evolución" en varias semillas y resume la comparación en tablas
Markdown. Un test de humo y un test del resumen cuidan que siga andando.

**Alcance:**
- `main.py`: flags `--sin-ventana`, `--generaciones N`, `--semilla S`, `--sin-evolucion` (línea
  base: cerebros al azar en cada generación) y `--csv RUTA`. Siembra `random` y `numpy`, escribe la
  salida en UTF-8 y deja el CSV en `results/corrida_s<semilla>_<modo>.csv` (`COLUMNAS_CSV`,
  `_fila_csv`).
- `src/ui/renderer.py`: las partículas usan su propio generador, así el dibujo no consume el azar
  de la simulación.
- `experimento.py`: lanzador en paralelo y resumen (`resumir_corrida`, `resumir_modo`,
  `comparar_por_semilla`, `resumen_markdown`), solo con la librería estándar.
- `tests/test_humo.py` y `tests/test_resumen.py`. El gate pre-commit compila `experimento.py` y
  `tests/`, y bloquea si pytest no encuentra tests.
- No cambia la simulación: no toca `src/agents/`, `src/world/` ni `src/evolution/`.

**Resultado:** con 5 semillas × 20 generaciones, la evolución sube más que la línea base en 5 de
5 semillas, en fitness y en manzanas. El puzzle no muestra aprendizaje. Detalle en
[AnalisisQA § Experimento en cinco semillas](../qa/AnalisisQA.md#experimento-cinco-semillas).

**QA:** [AnalisisQA § QA /qa-spec — Medir antes de tocar](../qa/AnalisisQA.md#qa-medir-antes-de-tocar),
APROBADO 16/16. Resuelve DIAG-06, DIAG-07 y DIAG-25.
