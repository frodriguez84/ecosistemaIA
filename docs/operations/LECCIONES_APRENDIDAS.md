# Lecciones aprendidas — Ecosistema Evolutivo IA

Qué salió mal, cómo se descubrió y qué regla deja. Una entrada por lección, la más nueva arriba.
La regla, además, va donde se aplica (CLAUDE.md, el spec o el código).

---

## LEC-003 — 2026-11-14 — En Git Bash, `grep` no ve los CR de un archivo CRLF

**Qué pasó.** En el bloque B de [Medir antes de tocar](../specs/done/MEDIR_ANTES_DE_TOCAR.md), para
controlar que las líneas nuevas del README (que es CRLF) no hubieran quedado con LF, se contaron
con `grep -c` las líneas que terminan en CR. Dio 0, como si el archivo fuera LF, mientras `file`
decía CRLF. El `grep` de Git Bash quita el CR del final de cada línea antes de comparar, salvo con
`-U` (`--binary`): con `-U` dio las 631 líneas. Se confirmó contando `\r\n` en los bytes con Python.

**Regla.** Para controlar finales de línea, contar bytes (en Python,
`open(ruta, "rb").read().count(b"\r\n")`) o usar `grep -U`. Un 0 de `grep` sin `-U` no quiere decir
que el archivo sea LF. Aplicada en [`CLAUDE.md`](../../CLAUDE.md) § Notas, junto a la de LEC-002.

## LEC-002 — 2026-11-14 — El Edit vacía las líneas en blanco que tienen espacios

**Qué pasó.** En el bloque A de [Medir antes de tocar](../specs/active/MEDIR_ANTES_DE_TOCAR.md),
dos reemplazos con la herramienta Edit (en `main.py` y `src/ui/renderer.py`) llevaban en el texto
nuevo una línea en blanco con espacios, copiada tal cual del original. Quedó vacía, sin los
espacios. El código andaba igual, pero el diff mostraba líneas cambiadas que nadie quiso tocar. Se
vio al revisar `git diff` antes del commit y se devolvió con un script que reemplaza una sola vez.

**Regla.** Después de editar código de este repo, revisar `git diff` buscando líneas quitadas que
eran solo espacios, y devolverlas. Muchos archivos son CRLF y tienen líneas en blanco con espacios.
Importa sobre todo en la limpieza, donde el diff tiene que mostrar solo lo que se quiso cambiar.
Aplicada en [`CLAUDE.md`](../../CLAUDE.md) § Notas.

## LEC-001 — 2026-11-14 — Lo que se ve en pantalla no prueba que aprendan

**Qué pasó.** En 2025 los parámetros se ajustaron mirando la simulación y la curva de fitness (el
código lo dice: "ajustados para mejorar curva de fitness promedio (presentación)"). Al retomar el
proyecto, una corrida con cerebros al azar en cada generación, sin heredar nada, llegó en el puzzle
casi tan lejos como la corrida con evolución: el puzzle se acumula entre generaciones y se activa
por cercanía. Parte de lo que parecía aprendizaje era la mecánica del mundo y la guía escrita a
mano. Detalle: [AnalisisQA, diagnóstico inicial](../qa/AnalisisQA.md#diagnostico-inicial).

**Regla.** Un cambio que dice mejorar el aprendizaje se demuestra contra una línea base sin
evolución, con la misma semilla y con más de una semilla. Si la línea base mejora igual, no es
aprendizaje. Aplicada en [`CLAUDE.md`](../../CLAUDE.md) § Convenciones de código.
