# Specs implementados — archivo

Resumen operativo de cada spec cerrado: qué hace, dónde está y dónde está su QA. El detalle de
diseño queda en el spec, en [`../specs/done/`](../specs/done/). El más nuevo arriba.

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
