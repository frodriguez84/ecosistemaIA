# Lecciones aprendidas — Ecosistema Evolutivo IA

Qué salió mal, cómo se descubrió y qué regla deja. Una entrada por lección, la más nueva arriba.
La regla, además, va donde se aplica (CLAUDE.md, el spec o el código).

---

## LEC-007 — 2026-11-14 — Un script de edición escrito con Write pierde los espacios de sus líneas en blanco

**Qué pasó.** En el bloque A de [Modo guiado y modo autónomo](../specs/active/MODO_GUIADO_Y_AUTONOMO.md),
los archivos CRLF se editaron con un script de Python, como pide LEC-005: textos viejos exactos,
unicidad verificada, escritura en CRLF. El primer reemplazo no encontró su texto. El script se había
escrito con la herramienta Write, que deja vacías las líneas que solo tienen espacios, y en el
código esas líneas llevan la sangría (`'    '`): todo texto viejo con una línea en blanco adentro
dejaba de coincidir. Escribirlo de nuevo con los espacios no sirve, porque la herramienta los vuelve
a quitar. Pasa lo mismo con una línea de código que termina en espacios.

**Regla.** El script compara contra el archivo con los espacios finales recortados y, al escribir,
devuelve la línea original en todo lo que no cambió (con `difflib.SequenceMatcher` entre las líneas
recortadas y las nuevas); una línea en blanco nueva toma la sangría de la que le sigue. Así el diff
muestra solo lo que se quiso cambiar y no toca los blancos (LEC-002). Aplicada en
[`CLAUDE.md`](../../CLAUDE.md) § Notas.

## LEC-006 — 2026-11-14 — Lo que cita un checker de QA se verifica antes de copiarlo

**Qué pasó.** En el cierre de [Limpieza](../specs/done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md),
`/qa-spec` lanzó tres checkers (Explore, haiku). Uno citó `genetic_algorithm.py:240` como una de
las tres apariciones de `random.randint(50, 900)`. La 240 es el `randint(50, 750)`: la tercera está
en la 239. El veredicto era correcto (`grep -c` daba 3), pero la tabla de QA es la evidencia que
queda, y habría quedado con una cita falsa. Se encontró imprimiendo cada línea citada antes de
cerrar la tabla. En la misma corrida, otro checker dio dos PARCIAL porque su prompt pedía más que el
DoD: un nombre de archivo literal en `CLAUDE.md` que el DoD no exige. El checker verifica lo que se
le escribe, no el spec.

**Regla.** Antes de escribir la tabla de QA, se imprime cada `archivo:línea` que citaron los
checkers (`sed -n`) y se corrige lo que no coincide. Al checker se le pasa el texto del DoD tal
cual. Si se le agrega algo, un FAIL o PARCIAL sobre lo agregado no cuenta contra el spec, y se
explica en las observaciones. Aplicada en
[`.claude/skills/qa-spec/SKILL.md`](../../.claude/skills/qa-spec/SKILL.md) § 3 y § 4.

## LEC-005 — 2026-11-14 — `sed -i` en Git Bash deja en LF un archivo CRLF entero

**Qué pasó.** En el bloque C de [Limpieza](../specs/active/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md),
para cambiar una línea de imports de `main.py` (CRLF) se usó `sed -i` con un patrón que terminaba
en `\r$`. El patrón no encontró nada (el `sed` de Git Bash, como su `grep`, ve las líneas sin el
CR: LEC-003) y aun así reescribió el archivo: las 1.292 líneas quedaron en LF. `git diff` no lo
mostró, porque `core.autocrlf` compara sin los CR; lo delató el aviso "LF will be replaced by CRLF"
de Git, y se confirmó contando bytes con Python. Se volvió a CRLF con Python (el archivo era CRLF
puro) y el diff quedó en lo que se quería cambiar.

**Regla.** En un archivo CRLF no se usa `sed -i`. Se edita con un script de Python que lee y
escribe bytes, verifica el texto viejo y su unicidad, y escribe CRLF; o con Edit, revisando después
los blancos (LEC-002). Después de editar, se cuentan los finales de línea con Python: el aviso
"LF will be replaced by CRLF" sobre un archivo que era CRLF es la señal. Aplicada en
[`CLAUDE.md`](../../CLAUDE.md) § Notas.

## LEC-004 — 2026-11-14 — Un control que depende de una tecla puede no haber pasado

**Qué pasó.** En el bloque B de [Limpieza](../specs/active/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md),
el control de LIMPIEZA-13 pedía apretar `+` en la ventana durante la generación 1 y comparar el CSV
contra la línea base. Fer lo hizo dos veces y el CSV dio igual: habría quedado anotado como "el
control no dio distinto". Pero el log no tenía ninguna línea `🔍 Zoom IN`: la tecla no había llegado
al juego (no se supo por qué: teclado numérico, foco o distribución del teclado), y un CSV igual no
decía nada del zoom. Se resolvió inyectando las teclas: un script envuelve `pygame.event.get` y
agrega los eventos, que entran por el mismo manejador de `main.py`. El script además contó los
sorteos que usaban el alto agrandado, que era lo que el control quería saber: 0.

**Regla.** Un control que depende de una acción manual verifica en el log que la acción pasó (cada
tecla de `main.py` deja su `print`) antes de leer el resultado. Si no pasó, o si se quiere
repetible, el evento se inyecta envolviendo `pygame.event.get`. Y cuando un resultado igual puede
deberse a que el código no corrió, se mide si corrió. Aplicada en [`CLAUDE.md`](../../CLAUDE.md)
§ Notas.

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
