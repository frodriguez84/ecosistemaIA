# Specs implementados — archivo

Resumen operativo de cada spec cerrado: qué hace, dónde está y dónde está su QA. El detalle de
diseño queda en el spec, en [`../specs/done/`](../specs/done/). El más nuevo arriba.

---

## Que aprendan el puzzle solos {#puzzle-solos}

**Spec:** [PUZZLE_SOLOS](../specs/done/PUZZLE_SOLOS.md) · cerrado el 2026-11-25, en catorce sesiones con
bitácora (trece de mediciones y cambios, del 2026-11-21 al 2026-11-24, y el cierre).

**Qué hace:** lleva al modo autónomo, sin nada dado al nacer en la ventana que se mide, por la cadena del
puzzle, un paso por vez y con el mismo criterio contra la línea base sin evolución (4 de 5 semillas, al
menos 1 agente por generación, leído junto con una medida independiente). Cada cambio a la simulación entró
con un switch en `config.py`, apagado por defecto y común a los dos modos: la **brújula por el camino**
(`BRUJULA_CAMINO`, `--brujula-camino`: los sensores 9 y 11 apuntan por el camino libre más corto, no en
línea recta), la **recompensa por acercarse medida por el camino** (`ACERCARSE_CAMINO`,
`--acercarse-camino`, va con `--acercarse`), el **fitness sin tope** (`FITNESS_SIN_TOPE`,
`--fitness-sin-tope`: la selección ordena por la suma de los términos; la mutación adaptativa y la guía
siguen con el de 0 a 100) y la **comida que rebrota** (`COMIDA_REBROTA`, `--comida-rebrota`: cada manzana
comida vuelve a los `COMIDA_REBROTA_TICKS`, 250, al azar y lejos de los vivos). Apagados, la corrida es la
de antes byte a byte; ninguno va por defecto (Fer, 2026-11-24). Lo demás se probó sin código, con los
argumentos de `mediciones/medir_puerta.py` (`pesos=`, `cruce=`, `curriculo=`).

**Alcance:** `config.py`, `main.py` y `experimento.py` (los cuatro flags, el nombre del CSV, el panel, el
boletín y el resumen); `src/world/camino.py` (nuevo: por etapa, una grilla con la distancia y el rumbo por
el camino libre), `src/world/world.py`, `src/agents/advanced_agent.py` y `src/evolution/genetic_algorithm.py`
(la mutación adaptativa lee `fitness_con_tope`); `mediciones/medir_puerta.py` (los cuatro switches y la
medida `hierro`) y un script `mediciones/analizar_*.py` por medición. Tests: `test_brujula_camino.py` (12),
`test_acercarse_camino.py` (7), `test_fitness_sin_tope.py` (11) y `test_comida_rebrota.py` (11), nuevos; 231
en ~85 s. No cambia la red (11 entradas, 5 salidas), el modo guiado por defecto ni el mapa.

**Resultado:** la cadena entera, sí. En la referencia final (NT: el autónomo con el currículo hasta la 30,
acercarse por el camino, deslizar, fortalezas móviles, la brújula por el camino, el fitness sin tope, el
cruce en 0,2, golpear sin costo y tres pesos del fitness), en las gens 146-150 la llave roja, la puerta de
madera, la llave dorada, la puerta de hierro y el cofre pasan 5 de 5 (55,0 · 43,9 · 42,4 · 13,1 · 9,6
agentes por generación; sin evolución, 1,2 y 0), y corrida otra vez desde el commit de la Sesión 12 da sus
30 CSV byte a byte. Lo que destrabó cada paso: golpear sin costo, la puerta de madera; la brújula y la
recompensa por acercarse medidas por el camino, la puerta de hierro (la recta cruzaba las paredes de la
fortaleza chica); y el fitness sin tope subió la puerta de hierro y el cofre (la selección distingue la
cadena entera). **Comer, no:** se cerró como no aprendido (decisión 10); compite con la cadena por el giro,
y ni más peso a la comida ni la comida que rebrota lo sumaron. El comando, los valores y los SHA-256, en
[§ La referencia final](../specs/done/PUZZLE_SOLOS.md#la-referencia-final) del spec; la lectura, en
[AnalisisQA § La corrida final](../qa/AnalisisQA.md#corrida-final).

**QA:** [AnalisisQA § QA /qa-spec — Que aprendan el puzzle solos](../qa/AnalisisQA.md#qa-puzzle-solos),
APROBADO 11/11 (los checkers dieron PARCIAL en tres criterios; ninguno se sostiene contra el texto del
spec).

---

## Que el puzzle se pueda aprender {#puzzle-aprendible}

**Spec:** [PUZZLE_APRENDIBLE](../specs/done/PUZZLE_APRENDIBLE.md) · cerrado el 2026-11-15, en cuatro
sesiones (autoría con una medición previa, los bloques A y B, y el cierre).

**Qué hace:** dos ayudas para aprender el puzzle, cada una con su switch en `config.py`, apagadas por
defecto y comunes a los dos modos. La **recompensa por acercarse** (`RECOMPENSA_ACERCARSE`,
`--acercarse`) suma `FITNESS_ACERCARSE` (10) × (pasos que dio + avance en el paso actual). El avance es
lo más cerca que llegó del objetivo de la brújula desde donde empezó el paso; en las puertas suma
además los golpes que contaron. El **currículo** (`CURRICULO`, `--curriculo`) hace que las generaciones
1 a `CURRICULO_HASTA_GENERACION` (15) nazcan con la llave roja, sin su premio. Lo que se da al nacer no
cuenta como logro. Apagadas, la corrida es la de antes.

**Alcance:** el bloque A, la recompensa (`_medir_acercamiento` y `_avance_en_el_paso` en el agente, la
columna `acercarse`, la ruta con `_acercarse`); el bloque B, el currículo (`etapa_inicial`,
`_fijar_etapa_inicial` en `main.py`, los hitos que cuentan solo los pasos dados, la columna
`etapa_inicial`, la ruta con `_curriculo` y el renglón "Ayudas" del panel); `experimento.py`, con los
dos flags, la puerta de madera, la llave roja por 1.000 px y la línea del criterio. Tests:
`test_acercarse.py` (10) y `test_curriculo.py` (12), nuevos; 155 en ~35 s. No cambia el genético, los
sensores, la red, el mapa, los premios ni la energía.

**Resultado:** no. Ninguna ayuda, ni las dos juntas, hace que el autónomo aprenda a pasar la puerta de
madera: 0 de 5 semillas en los tres experimentos. Con la llave dada, la evolución abre la puerta lo
mismo que cerebros al azar. Sigue aprendiendo a comer y a caminar (5 de 5). Detalle en
[AnalisisQA § La respuesta al ítem 5](../qa/AnalisisQA.md#puzzle-respuesta-item-5).

**QA:** [AnalisisQA § QA /qa-spec — Que el puzzle se pueda aprender](../qa/AnalisisQA.md#qa-puzzle-aprendible),
APROBADO 18/18 (la primera pasada dio PARCIAL por la tabla del ítem 5; se corrigió en la sesión).

---

## Pantallas para ver aprender {#pantallas-ver-aprender}

**Spec:** [PANTALLAS_VER_APRENDER](../specs/done/PANTALLAS_VER_APRENDER.md) · cerrado el 2026-11-15: autoría
con una [maqueta](https://claude.ai/artifact/SvXK3fB1Yv8zpSB3HBXE5Z), dos bloques (los datos y las
pantallas) y el cierre.

**Qué hace:** ver aprender sin cambiar la simulación (el mismo CSV byte a byte). Sale el popup de cada
generación (DIAG-32). Durante la corrida, el panel derecho ocupa la columna entera, con gráficos en vivo
de fitness y de manzanas por agente (escala automática), y arriba del mundo hay avisos que no toman
clics ni frenan nada: el fin de cada generación (2,5 s, con la diferencia contra la anterior) y la
primera vez de cada paso del puzzle (4 s, en dorado). Al final, una sola pantalla como boletín: cuatro
números (la generación 1 contra el promedio de las últimas 5), los gráficos con los pasos del puzzle
marcados, el mapa de calor de por dónde caminaron (la generación 1 contra la última), el puzzle como
embudo, el mejor agente de la corrida y el cofre una sola vez. Sin ventana, el mismo boletín por
consola.

**Alcance:**
- Bloque A, los datos: `src/analytics/registro.py` (`RegistroDeLaCorrida`: la fila del CSV de cada
  generación, los hitos, el récord del mejor agente y el mapa de calor, en celdas de
  `HEATMAP_CELL_SIZE` = 16 px), alimentado por un solo camino en `main.py`, con ventana y sin ella;
  `src/analytics/boletin.py` (formato de números, escala automática, `armar_boletin`,
  `texto_de_consola`, `linea_de_hito`). Cada hito imprime su línea en la consola. Fuentes Pixelify Sans
  e Inter (TTF estáticos, OFL) en `assets/fonts/`, con `src/ui/fuentes.py`.
- Bloque B, las pantallas: salen `src/ui/popup.py`, el cuadro final de antes y los `get_*_skill`.
  Nuevos `src/ui/graficos.py` y `src/ui/avisos.py` (`PilaDeAvisos`, con el reloj como parámetro);
  reescritos `src/ui/stats.py` (el panel) y `src/ui/pantalla_final.py` (`dibujar_boletin`). Ningún
  texto de pantalla usa la fuente de pygame, salvo los rótulos de respaldo de `obstacles.py`.
- Tests: `test_registro.py`, `test_boletin.py`, `test_fuentes.py` y `test_pantallas.py` (con
  `SDL_VIDEODRIVER=dummy`), nuevos; `test_humo.py` y `test_reportes.py` al día: 123 en ~26 s.
- No cambian la simulación, el CSV, `experimento.py` ni el reporte de consola de cada generación. Nada
  nuevo consume azar ni escribe archivos.

**QA:** [AnalisisQA § QA /qa-spec — Pantallas para ver aprender](../qa/AnalisisQA.md#qa-pantallas-ver-aprender),
APROBADO 18/18. Resuelve DIAG-32.

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
