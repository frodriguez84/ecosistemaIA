# Operaciones — correr, medir y editar archivos

Lo que no hace falta en toda tarea; el [`CLAUDE.md`](../../CLAUDE.md) apunta acá. Cada regla sale de una
lección: la historia, en [LECCIONES_APRENDIDAS.md](LECCIONES_APRENDIDAS.md).

## Correr

- **Para correr sin ventana, flags, no `config.py`:** `python main.py --sin-ventana --generaciones N
  --semilla S` (`--help` los lista; `--sin-evolucion` es la línea base, `--modo autonomo` el modo
  sin guía, `--acercarse` y `--curriculo` prenden las ayudas, `--deslizar` el deslizamiento y
  `--fortalezas-moviles`, las fortalezas móviles). El
  experimento con los dos modos, con evolución y sin ella, en varias semillas es `python experimento.py`
  (`--modos` elige los modos; `--acercarse`, `--curriculo`, `--deslizar` y `--fortalezas-moviles` pasan a
  todas las corridas).
- **`mediciones/`:** scripts que miden una corrida sin cambiarla (envuelven sin consumir azar; control
  byte a byte).
- **Una corrida sin ventana tarda ~6 s por generación de 960 ticks** con 60 agentes (máquina de 12
  núcleos), más unos 3 s de arranque; las generaciones se alargan 180 ticks cada 4 (con `--deslizar`,
  ~1,5 veces: caminan más ticks). Redirigida a
  archivo, la salida sale con buffer y aparece toda al final: para leer un log mientras corre,
  `python -u` (así lanza las corridas `experimento.py`). Más de 10 corridas a la vez se quedan sin
  memoria virtual y alguna se cae al arrancar; el `wait` de una tanda en segundo plano igual da 0: se
  cuentan las salidas de cada corrida (LEC-017).
- **Un control con ventana que depende de una tecla se verifica en el log:** cada tecla de
  `main.py` deja su `print` (`🔍 Zoom IN`…); si no está, la tecla no llegó y el resultado no dice
  nada. Para hacerlo repetible, el evento se inyecta envolviendo `pygame.event.get` desde un script
  (LEC-004).

## Medir

La regla de base, que una mejora del aprendizaje se demuestra contra la línea base sin evolución
(LEC-001), está en el `CLAUDE.md`.
- **Una corrida que se quiera comparar con otra lleva semilla fija** (`--semilla`): la misma semilla da
  el mismo CSV byte a byte. Un test de una propiedad del mundo (que algo se alcanza, que nada se pisa) se
  corre también contra el código de antes del cambio: lo que falla allá es de antes, va como bug y el
  test lo deja afuera con su ID (LEC-020).
- **Una tabla que compara experimentos se llena con la misma cuenta en cada fila,** sobre los CSV,
  también donde el razonamiento dice que da 0 (LEC-016). Una proyección de lo que hace un cambio
  cambia solo lo que el cambio toca: si promedia también la variable con que se mide, sobreestima (LEC-021).
- **Un criterio fijado antes de medir lleva un tamaño mínimo, no solo "K de N semillas",** y se lee con
  un control o una medida independiente: 4 de 5 sale por azar el 19% de las veces (LEC-018).
- **Un experimento que cambia más de una cosa contra su comparación lleva el control que cambia una
  sola:** si el efecto aparece donde difieren las dos, sin ese control no se atribuye (LEC-019).
- **El scratchpad es de una sola sesión.** Un CSV de referencia que otra sesión tiene que comparar
  deja su SHA-256 en la bitácora, con el commit desde el que se regenera (LEC-011).

## Editar archivos

- **Después de editar código, revisar `git diff` por líneas que eran solo espacios.** El Edit vacía
  las líneas en blanco con espacios que van en el texto nuevo, y muchos archivos (CRLF) las tienen.
  Devolverlas para que el diff muestre solo lo que se quiso cambiar (LEC-002). Para mirar finales
  de línea, el `grep` de Git Bash quita los CR salvo con `-U`: contar bytes con Python (LEC-003);
  y `git show HEAD:archivo` da el blob en LF (`core.autocrlf`): para comparar contra HEAD, sin los
  CR de los dos lados (LEC-009).
  En un archivo CRLF, nunca `sed -i`: lo deja entero en LF y `git diff` no lo muestra (LEC-005).
  Un script de edición escrito con Write pierde los espacios de sus líneas en blanco: que compare
  contra el archivo con los espacios finales recortados y devuelva las líneas que no cambió (LEC-007).

## El editor

- **El editor tiene que usar el Python del `.venv`.** Con el Python global (Microsoft Store), la
  extensión Pylint marca "Unable to import 'pygame'" aunque el código corra bien.
  `.vscode/settings.json` lo fija; si vuelve a aparecer: `Ctrl+Shift+P` → *Python: Select
  Interpreter* → `.venv` (DIAG-24). Los `E1101: Module 'pygame' has no … member` de Pylint son
  falsos: `pylint.args` en ese mismo archivo le deja ver los miembros de pygame (DIAG-26).
