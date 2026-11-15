# Specs implementados — archivo

Resumen operativo de cada spec cerrado: qué hace, dónde está y dónde está su QA. El detalle de
diseño queda en el spec, en [`../specs/done/`](../specs/done/). El más nuevo arriba.

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
