# Lecciones aprendidas — Ecosistema Evolutivo IA

Qué salió mal, cómo se descubrió y qué regla deja. Una entrada por lección, la más nueva arriba.
La regla, además, va donde se aplica (CLAUDE.md, el spec o el código).

---

## LEC-021 — 2026-11-16 — Una proyección que promedia más de lo que toca el cambio lo sobreestima

**Qué pasó.** En el [ruido del fitness](../qa/AnalisisQA.md#ruido-fitness), la selección veía la brújula +0,15 con un
episodio y +0,27 con el promedio de 5. Ese +0,27 promediaba las dos variables, el fitness y la sensibilidad a la
brújula, y varias evaluaciones solo promedian el fitness. La sensibilidad también es ruidosa (se repite 0,44 entre
episodios), y promediarla sube la correlación por sí sola. La sugerencia y el pedido de la sesión siguiente se armaron
sobre el +0,27. Se vio al fijar el criterio de [varias evaluaciones](../qa/AnalisisQA.md#varias-evaluaciones), antes de
correr: había que llenar las filas con una evaluación y con cinco con la misma cuenta, y con la sensibilidad de un
episodio la proyección daba +0,14. Medido: +0,145.

**Regla.** Una proyección de lo que hace un cambio cambia solo lo que el cambio toca; la variable con que se lo mide
queda con la misma cuenta que en la comparación. Aplicada en [`OPERACIONES.md`](OPERACIONES.md) § Medir,
junto a la de LEC-016.

## LEC-020 — 2026-11-16 — Un test de una propiedad del mundo puede pasar de suerte

**Qué pasó.** Con las [fortalezas móviles](../qa/AnalisisQA.md#fortalezas-moviles), los tests de "nada nace
adentro de una fortaleza" y "el puzzle se puede completar" pasaban con el switch prendido en las 3 semillas
elegidas. Corridos contra el código de antes del switch (su control), fallaban en la semilla 3, por dos bugs
que no tienen que ver con el cambio: el agente que no encuentra lugar va a (100, 100), adentro de la chica
fija (DIAG-33), y la llave roja puede caer en el medio del estanque (DIAG-34). Con el switch pasaban porque
esas semillas no los pisaban: un cambio que moviera el azar los habría hecho fallar, y la culpa habría ido
al switch.

**Regla.** Un test de una propiedad del mundo (que algo se alcanza, que nada se pisa) se corre también
contra el código de antes del cambio. Lo que falla allá es de antes: se registra como bug y el test lo deja
afuera con su ID, así prueba solo lo que depende del cambio. Aplicada en [`OPERACIONES.md`](OPERACIONES.md) §
Medir.

## LEC-019 — 2026-11-16 — Un experimento que cambia dos cosas contra su comparación no dice cuál pesó

**Qué pasó.** El [laboratorio de la brújula](../qa/AnalisisQA.md#laboratorio-brujula) cambiaba dos cosas
respecto del C deslizando: el fitness (solo acercarse pagando) y el currículo, extendido de la
generación 15 a la 30. La sensibilidad a la brújula subió solo en las generaciones 16 a 30, donde
difieren las dos; en las 1 a 15, donde difiere solo el fitness, fue la misma. Contra el C deslizando, el
resultado no decía si la subida era por el fitness o por las generaciones de más. Se vio al mirar en qué
ventana aparecía la subida, antes de escribir la lectura. Se resolvió con un control que cambia una sola
cosa (el currículo hasta la 30, con el fitness de siempre), con su criterio fijado antes de correrlo: era
el fitness.

**Regla.** Un experimento que cambia más de una cosa respecto de la corrida con que se compara lleva,
desde el diseño, el control que cambia una sola. Si el efecto aparece solo donde difieren las dos, sin
ese control no se atribuye. Aplicada en [`OPERACIONES.md`](OPERACIONES.md) § Medir.

## LEC-018 — 2026-11-16 — Un criterio "más que la línea base en K de N" pasa con márgenes de ruido

**Qué pasó.** En la [medición de la brújula](../qa/AnalisisQA.md#brujula-c-deslizando), el criterio
"usa la brújula", fijado antes de medir, era: (camino hacia la puerta − hacia un punto de control) con
evolución, mayor que en la línea base, en 4 de 5 semillas. Dio 4 de 5, con márgenes de 0,003 a 0,020
cuando el camino había subido 0,087. La misma cuenta sin la recompensa dio 3 de 5, y la medida directa
(cuánto gira la red hacia donde marca la brújula) quedó en el 3% de un seguidor, como sin evolución.
Sin efecto ninguno, 4 o más de 5 sale por azar el 19% de las veces. Se vio porque la sesión había sumado
una medida independiente y un control antes de leer el resultado.

**Regla.** Un criterio fijado antes de medir lleva, además del K de N, un tamaño mínimo del efecto, y
se lee junto con una condición de control o una medida independiente. Si pasa en el mínimo y lo demás no
lo acompaña, se informa que pasó y por qué no se lee como aprendizaje. Aplicada en
[`OPERACIONES.md`](OPERACIONES.md) § Medir.

## LEC-017 — 2026-11-16 — Una tanda en segundo plano termina con 0 aunque se caiga una corrida

**Qué pasó.** En la [medición de dónde se traba la puerta de madera](../qa/AnalisisQA.md#medicion-puerta-madera),
15 corridas a la vez en segundo plano (`for …; do python … & done; wait`). La tanda terminó con código
0, pero una (semilla 3, con evolución) se había caído al arrancar, importando scipy: "DLL load failed
while importing _lsoda: El archivo de paginación es demasiado pequeño". `wait` sin argumentos devuelve
0 aunque un proceso falle. Se vio porque había 14 líneas finales del script en lugar de 15, y el control
byte a byte de esa corrida no encontró su CSV. Corrida sola, salió bien. Con 10 a la vez no pasó.

**Regla.** De una tanda en paralelo se cuentan las salidas (una línea final por corrida, un CSV por
corrida), no el código de salida de la tanda. En esta máquina, no más de 10 corridas a la vez. Aplicada
en [`OPERACIONES.md`](OPERACIONES.md) § Correr, junto al tiempo de una corrida sin ventana, y en el ítem de
[mejoras futuras](../product/mejoras_futuras.md) sobre las corridas del humo que se caen.

## LEC-016 — 2026-11-15 — Una celda que obviamente vale 0 se cuenta igual

**Qué pasó.** En el bloque B de [Que el puzzle se pueda aprender](../specs/done/PUZZLE_APRENDIBLE.md),
la tabla de la respuesta al ítem 5 compara las puertas abiertas en las generaciones 1 a 15 de los
cuatro experimentos. Las del B y el C se contaron en los CSV; las del experimento sin ayuda y del de la
recompensa se llenaron con "0 / 0 (sin llave)" por razonamiento: sin el currículo, nadie nace con la
llave. Pero en la semilla 5 un agente abrió la puerta en la generación 1, la misma con evolución y sin
ella, y el texto del experimento A, en el mismo archivo, ya lo contaba. Lo encontró el checker
independiente del QA de cierre, que recalculó cada celda desde los CSV.

**Regla.** En una tabla que compara experimentos, cada celda de una columna sale de la misma cuenta
sobre los datos, también las filas donde el razonamiento dice que da 0. Aplicada en `OPERACIONES.md`
(§ Medir) y en la tabla corregida (PUZZLE-QA-16).

## LEC-015 — 2026-11-15 — Separar dos cosas que eran una deja textos que todavía las juntan

**Qué pasó.** En el bloque B de [Que el puzzle se pueda aprender](../specs/done/PUZZLE_APRENDIBLE.md),
con el currículo los agentes nacen con la llave roja, y "llegar a un paso" dejó de ser lo mismo que
"darlo". La primera vez de cada paso en el boletín pasó a contar solo los pasos dados, y los tests
(filas armadas a mano, con generaciones del currículo y después sin él) daban bien. Mirando la
pantalla final de una corrida de 2 generaciones, las dos del currículo, la barra de la llave roja
estaba llena (60 de 60) y al lado decía "nadie, en ninguna generación"; el mejor agente "llegó a: llave
roja", que le habían dado. La barra cuenta quién llegó; el texto, quién la dio: cada uno estaba bien y
juntos se contradecían.

**Regla.** Cuando un cambio separa dos cosas que antes eran la misma, buscar cada lugar donde se
muestran una al lado de la otra y probar el caso en que difieren del todo (acá, una corrida que
termina adentro del currículo), mirándolo en pantalla. Aplicada en el boletín: "60 de 60 · dada al
nacer" y "llegó a: ningún paso (nació con la llave roja)", con su test en `tests/test_curriculo.py`.

## LEC-014 — 2026-11-15 — Un texto distinto del de una decisión es un desvío, aunque la decisión lo dé con una variable

**Qué pasó.** En el bloque A de [Pantallas para ver aprender](../specs/done/PANTALLAS_VER_APRENDER.md),
la nota de los cuatro números con 2 generaciones quedó "gen 1 → gen 2". La decisión 14 b dice "gen 1 →
promedio de las últimas K", que con K = 1 da "promedio de las últimas 1". La bitácora lo anotó entre
los "textos que el spec no fijaba", junto con otros que de verdad no fijaba, y no entre los desvíos,
que son los que se confirman con Fer. Lo encontró el checker independiente del QA de cierre, que leyó
la decisión sin leer la bitácora.

**Regla.** Antes de anotar un texto como "que el spec no fijaba", buscarlo en las decisiones: si una lo
da, aunque sea con una variable o como plantilla, apartarse es un desvío y se confirma con Fer. Aplicada
en `docs/AGENTES.md`, en el formato de la bitácora ("Desvíos del spec, y por qué").

## LEC-013 — 2026-11-15 — Una fuente de pygame guardada en caché deja de servir cuando se cierra `pygame.font`

**Qué pasó.** En el bloque B de [Pantallas para ver aprender](../specs/active/PANTALLAS_VER_APRENDER.md),
`src/ui/fuentes.py` carga cada fuente una sola vez y la guarda en un diccionario del módulo. Los tests
de pantallas cierran pygame al terminar (`pygame.quit()`) y los de fuentes cierran `pygame.font`; el
módulo siguiente volvía a abrirlo, pero la caché seguía devolviendo las fuentes viejas, y dibujar con
una de ellas colgó el proceso entero ("Windows fatal exception: access violation"), sin un error de
Python que dijera cuál. Pasaba en los dos órdenes de los módulos. `pygame.register_quit` no sirvió
para vaciarla: su lista se vacía con el primer `pygame.quit()` y `pygame.font.quit()` no la llama.

**Regla.** Un objeto de pygame guardado en un módulo vale mientras pygame siga abierto. Quien lo cierra
y lo vuelve a abrir (en este repo, solo los tests) vacía la caché: `fuentes.olvidar()`, al abrir y al
cerrar el fixture. Aplicada en el docstring de `fuentes.olvidar` y en los fixtures de
`tests/test_fuentes.py` y `tests/test_pantallas.py`.

## LEC-012 — 2026-11-15 — Una fuente de píxeles se mira dibujada por pygame, al tamaño en que se usa

**Qué pasó.** La maqueta aprobada de [Pantallas para ver aprender](../specs/active/PANTALLAS_VER_APRENDER.md)
usaba Pixelify Sans a 22 y 34 px, y en el navegador se veía bien. Dibujada por pygame, la "C" y la
"c" salían cerradas, iguales a la "O" y la "o": "Eoosistema", "Oorrida terminada". La abertura mide
unas 35 de 1.000 unidades, menos de medio "píxel" de diseño, y a 21, 22, 30, 33, 34 y 35 px el
rasterizador la cierra. Se vio en la primera captura de la pantalla final; el test de caracteres
faltantes no lo podía ver, porque el glifo existe.

**Regla.** Un tamaño de fuente que viene de una maqueta se confirma en una captura de pygame, no en el
navegador; y con Pixelify Sans, un título va en un tamaño donde la "C" queda abierta (16, 18, 20,
23, 24, 26, 28, 32, 36 o 40 px). Aplicada en `tests/test_fuentes.py`
(`test_la_c_de_los_titulos_queda_abierta`, sobre los tamaños que usan los módulos) y en las trampas
de la bitácora del spec.

## LEC-011 — 2026-11-15 — El scratchpad es de una sola sesión: una referencia para otra sesión no puede vivir ahí

**Qué pasó.** El spec de [Pantallas para ver aprender](../specs/active/PANTALLAS_VER_APRENDER.md)
(decisión 16) pedía guardar los 4 CSV de referencia "fuera del repo (scratchpad)" y compararlos con
`cmp` al cerrar cada bloque. Pero cada bloque es una sesión, y el scratchpad de una sesión es una
carpeta propia que la siguiente no ve (y que una limpieza puede borrar). El bloque B no habría
encontrado contra qué comparar. Se vio al generar las referencias, en la sesión 1, antes de que
fallara.

**Regla.** Lo que una sesión deja para que otra lo compare (CSV de control, salidas esperadas) no
queda solo en el scratchpad: su SHA-256 va a la bitácora del spec, con el commit desde el que se
regenera. La sesión siguiente corre lo mismo y compara hashes, sin depender del archivo. Aplicada en
[`OPERACIONES.md`](OPERACIONES.md) § Medir.

## LEC-010 — 2026-11-15 — Un número de los docs que coincide con `config.py` no está verificado si nadie lee ese parámetro

**Qué pasó.** En el cierre de [Modo guiado y modo autónomo](../specs/done/MODO_GUIADO_Y_AUTONOMO.md),
el checker de docs de `/qa-spec` encontró que el README decía que el árbol pide 2 golpes. El 2 es el
`TREE_HITS_TO_CUT` de `config.py`, pero nadie lo lee: `world.py:29` pide 3. El DoD pedía que cada
número del README coincidiera "con `config.py` o con el código", y la sesión 3 lo había dado por
bueno contra `config.py`. Lo mismo con la fortaleza chica: el README decía 4x5, como el comentario
de `config.py`, y los muros son de 5x5. Al arreglarlo, el inventario de qué parámetros no lee nadie
se equivocó dos veces: primero dejó afuera `config.py` y no vio que `get_genetic_params()` lee los
del genético (dio 14 en lugar de 3); después no siguió a `print_config()`, que imprime dos más. Los
dos errores los encontraron checkers nuevos.

**Regla.** Un número de la documentación se compara con lo que usa el programa. Si sale de
`config.py`, primero se confirma que el código lee ese parámetro: el nombre en `main.py`, `src/` y en
los métodos de `config.py`, siguiendo quién llama a esos métodos. Un valor de `config.py` que nadie
lee no verifica nada. Aplicada en [`CLAUDE.md`](../../CLAUDE.md) § Notas; los parámetros que
no mandan, en [mejoras futuras](../product/mejoras_futuras.md).

## LEC-009 — 2026-11-15 — `git show HEAD:archivo` da el archivo en LF aunque en disco sea CRLF

**Qué pasó.** En el bloque C de [Modo guiado y modo autónomo](../specs/active/MODO_GUIADO_Y_AUTONOMO.md),
un script de control comparaba cada archivo editado contra `git show HEAD:<archivo>` para encontrar
líneas que solo cambiaron en blancos (LEC-002) y para ver si el final de línea había cambiado.
Marcó todas las líneas de `main.py`, `config.py` y el agente, y dijo que habían pasado de LF a CRLF.
No habían cambiado: con `core.autocrlf`, Git guarda los archivos en LF y los pone en CRLF al
sacarlos al disco, y `git show` devuelve lo guardado. Se vio porque el archivo en disco era CRLF
puro, igual que antes de editarlo.

**Regla.** Para comparar un archivo en disco con su versión de HEAD, se sacan los CR de los dos
lados antes de comparar líneas; el final de línea esperado se toma de la lista de archivos CRLF del
spec o de `CLAUDE.md`, no del blob de Git. Aplicada en [`OPERACIONES.md`](OPERACIONES.md) § Editar archivos,
junto a la de LEC-003.

## LEC-008 — 2026-11-15 — Lo que se agarra por contacto no puede estar donde arranca un agente

**Qué pasó.** En el bloque B de [Modo guiado y modo autónomo](../specs/active/MODO_GUIADO_Y_AUTONOMO.md),
la llave roja y el hacha pasaron a sortearse en `reset_food()`, antes de ubicar a los agentes (antes,
la llave aparecía después del primer tick). La ubicación evitaba las manzanas a 35 px, pero no la
llave ni el hacha, que se agarran por contacto: en la primera captura con ventana, en el tick 1, el
panel ya decía "Con hacha: 1" y "Llave roja: 1". Un agente que arranca encima se lleva el premio sin
buscarlo, en ~25% de las generaciones; los tests verdes y el CSV byte a byte no lo mostraban. Se
decidió con Fer evitarlas a 35 px, como las manzanas, con un test cuyo control usa la ubicación vieja.

**Regla.** Cuando un cambio mueve un objeto a antes de ubicar a los agentes, revisar todo lo que ese
objeto da por contacto: la ubicación tiene que evitarlo. Se controla mirando el tick 1 (el panel con
ventana, o las etapas de los agentes): nadie tiene que haber avanzado sin moverse. Aplicada en
`_lugar_libre` (`main.py`) y en `tests/test_puzzle.py`.

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
[`OPERACIONES.md`](OPERACIONES.md) § Editar archivos.

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
deberse a que el código no corrió, se mide si corrió. Aplicada en [`OPERACIONES.md`](OPERACIONES.md)
§ Correr.

## LEC-003 — 2026-11-14 — En Git Bash, `grep` no ve los CR de un archivo CRLF

**Qué pasó.** En el bloque B de [Medir antes de tocar](../specs/done/MEDIR_ANTES_DE_TOCAR.md), para
controlar que las líneas nuevas del README (que es CRLF) no hubieran quedado con LF, se contaron
con `grep -c` las líneas que terminan en CR. Dio 0, como si el archivo fuera LF, mientras `file`
decía CRLF. El `grep` de Git Bash quita el CR del final de cada línea antes de comparar, salvo con
`-U` (`--binary`): con `-U` dio las 631 líneas. Se confirmó contando `\r\n` en los bytes con Python.

**Regla.** Para controlar finales de línea, contar bytes (en Python,
`open(ruta, "rb").read().count(b"\r\n")`) o usar `grep -U`. Un 0 de `grep` sin `-U` no quiere decir
que el archivo sea LF. Aplicada en [`OPERACIONES.md`](OPERACIONES.md) § Editar archivos, junto a la
de LEC-002.

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
