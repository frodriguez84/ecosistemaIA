# Ecosistema Evolutivo IA — Prompt Maestro para Claude Code

> Las reglas **globales** (SDD, selección de modelo, git, registro obligatorio, seguridad,
> hábitos de sesión) están en `~/.claude/CLAUDE.md` y NO se repiten acá. Este archivo lleva
> solo lo específico de **este** proyecto. Si algo ya está en el global, referencialo — no
> lo dupliques (la duplicación es lo que después driftea).

## Idioma

**Responder siempre en español**, en todo momento — texto al usuario, mensajes de commit,
comentarios de PR, resúmenes de specs. Si una herramienta o el código está en inglés, está
bien citarlo tal cual, pero el texto propio va en español de principio a fin.

## Contexto del producto

Simulación 2D donde criaturas con una red neuronal propia evolucionan por algoritmo genético
para comer, sobrevivir y resolver un puzzle (llave roja → puerta de madera → llave dorada →
puerta de hierro → cofre). Nació en 2025 para el curso de Inteligencia Artificial de UCEMA.

**Es un proyecto lúdico:** sirve para aprender, jugar y ver hasta dónde llegan las distintas IAs
ayudando a evolucionarlo. No hay usuarios ni producción. Lo que importa es que la simulación sea
interesante y que lo que dice de sí misma (README, pantallas, reportes) sea verdad.

**Rumbo (decidido el 2026-11-14):** dos modos con un switch en `config.py`, para compararlos. El
modo **guiado** conserva la conducción escrita a mano que existe hoy, documentada como tal. El
modo **autónomo** es neuroevolución real: sin guía, con sensores del puzzle y acción de golpear.
Antes de tocar el aprendizaje se mide (orden de trabajo en
[docs/product/BACKLOG.md](docs/product/BACKLOG.md)).

---

## Stack tecnológico

- **Python 3.11** con entorno virtual en `.venv/` (Windows: `.venv/Scripts/python.exe`).
  Dependencias en `requirements.txt`: solo las que el código importa (`pygame`, `numpy`,
  `scikit-learn` y `pytest`), con versión mínima y sin fijar.
- **pygame 2.6:** ventana, sprites y eventos.
- **numpy:** la red neuronal es propia (`SimpleNeuralNetwork`, en `src/agents/advanced_agent.py`);
  no usa PyTorch.
- **scikit-learn:** clustering de comportamientos (K-Means + PCA). **pytest:** los tests.
- **Sin base de datos, sin web, sin deploy.** Corre local con `python main.py`, con ventana o sin
  ella (`--sin-ventana`, o `HEADLESS_MODE` en `config.py`).

---

## Estructura de carpetas

```
EcosistemaEvolutivo/
├── main.py              ← punto de entrada: flags, semilla, CSV; loop de simulación y render
├── config.py            ← SimulationConfig: parámetros centralizados (tres no se leen, ver Notas)
├── experimento.py       ← los dos modos, con evolución y sin ella, en varias semillas → resumen.md
├── requirements.txt
├── mediciones/          ← scripts que miden una corrida sin cambiarla (envuelven sin consumir azar; control byte a byte)
├── tests/               ← pytest: humo de main.py (los dos modos y las ayudas), reglas, puzzle, modos, acercarse, currículo, deslizar, reportes, resumen, registro, boletín, fuentes y pantallas
├── results/             ← CSV y logs de las corridas (en .gitignore)
├── assets/sprites/      ← sprites de personajes y entorno
├── assets/fonts/        ← Pixelify Sans e Inter, TTF estáticos con licencia OFL (origen en su LEEME.md)
├── src/
│   ├── agents/
│   │   └── advanced_agent.py      ← AdvancedAgent (sensores, decisión, acciones, fitness) + SimpleNeuralNetwork
│   ├── evolution/
│   │   └── genetic_algorithm.py   ← selección (meeting pool / torneo / élite), cruce, mutación, inmigración
│   ├── world/
│   │   ├── world.py               ← mundo procedural, fortalezas, llaves, puertas, cofre, hacha, comida
│   │   └── obstacles.py           ← obstáculos y sus efectos (agua, árboles, casitas)
│   ├── analytics/
│   │   ├── learning_monitor.py    ← métricas por generación, diversidad, reportes por consola
│   │   ├── clustering.py          ← K-Means + PCA sobre comportamientos
│   │   ├── registro.py            ← registro de la corrida: filas del CSV, hitos, mejor agente, mapa de calor (sin azar)
│   │   └── boletin.py             ← boletín final (datos y texto de consola), formato de números, escala de gráficos
│   └── ui/                        ← renderer (sprites, partículas, dibujar_mundo), panel con gráficos, avisos, gráficos, fuentes y pantalla final (el boletín)
├── docs/                ← metodología: specs, backlog, QA (índice en docs/README.md)
└── .claude/             ← skills del proyecto y hook pre-commit
```

---

## Variables de entorno

<!-- TODO: documentar cada var con un comentario de para qué es. Nunca pegar valores reales
     de secrets — solo el nombre y el propósito. -->

```env
# No usa ninguna. No hay .env.example: estaba vacío y se borró en la limpieza.
```

---

## Lógica de negocio crítica

- **Dos modos** (`MODO` en `config.py`, `--modo`; por defecto `"guiado"`). Difieren **solo** en la
  conducción escrita a mano de `decide()` y `act()`: en el autónomo, `decide()` es la salida de la red
  recortada a [0, 1] y no consume azar. Mundo, puzzle, sensores, golpear, fitness y valores de
  `config.py` son los mismos. Guiado contra autónomo mide la guía; cada modo contra su línea base sin
  evolución mide el aprendizaje (spec [Modo guiado y modo autónomo](docs/specs/done/MODO_GUIADO_Y_AUTONOMO.md)).
- **El puzzle es de cada agente:** etapa de 0 a 5 y hacha propias; una puerta es pared para cada uno
  hasta que él la abre; las llaves y el hacha se agarran por contacto y quedan en el mapa; puertas,
  cofre y árboles piden golpear (quinta salida, cuesta `HIT_ENERGY_COST`). Todo vuelve a 0 en cada
  generación (a 1 con el currículo, hasta la 15), y abrir el cofre no termina la corrida.
- **Dos ayudas para aprender el puzzle,** comunes a los dos modos, cada una con su switch en
  `config.py`, apagadas por defecto: la recompensa por acercarse (`RECOMPENSA_ACERCARSE`: suma
  `FITNESS_ACERCARSE` = 10 × (pasos que dio + avance en el paso actual)) y el currículo (`CURRICULO`:
  las generaciones 1 a `CURRICULO_HASTA_GENERACION` = 15 nacen con la llave roja, sin su premio).
  Apagadas, la corrida es la de antes. Lo dado al nacer no es un logro: hitos, primera vez del boletín
  y pasos de la recompensa cuentan solo los pasos dados (`etapa_inicial` del agente y del CSV). Spec
  [Que el puzzle se pueda aprender](docs/specs/done/PUZZLE_APRENDIBLE.md).
- **Deslizar contra lo que choca** (`DESLIZAR`, `--deslizar`; apagado por defecto, en los dos modos):
  si el paso choca, el agente prueba moverse solo en x y, si no, solo en y, con las mismas colisiones
  del paso entero (`_choca`, con la caja descentrada del estanque y el perímetro de DIAG-30). No es
  columna del CSV, así que apagado el CSV es el de antes byte a byte: va en el nombre del archivo, el
  panel, el boletín y el resumen del experimento ([medición](docs/qa/AnalisisQA.md#deslizar-al-chocar)).
- **La red tiene 11 entradas y 5 salidas.** Los sensores 9 y 11 son la brújula al próximo paso del
  agente.

---

## Convenciones de código

- **Español** en comentarios, docstrings, mensajes de consola y textos de pantalla (así está todo
  el código).
- **Los parámetros van en `config.py`** (`SimulationConfig`), no como números sueltos en el
  código. Quedan en el código, a propósito, los umbrales de la guía (ver Notas).
- **Sin formateador ni linter configurados.** No correr black, ruff ni similares con
  `--fix`/`--write` (regla global): reformatearían archivos enteros.
- **Tests con pytest,** en `tests/`: `python -m pytest -q` (el gate pre-commit los corre). Una
  corrida que se quiera comparar con otra lleva semilla fija (`--semilla`): la misma semilla da el
  mismo CSV byte a byte.
- **Una mejora del aprendizaje se demuestra contra la línea base sin evolución,** con la misma
  semilla y con varias semillas. Si la línea base mejora igual, no es aprendizaje (LEC-001 en
  [docs/operations/LECCIONES_APRENDIDAS.md](docs/operations/LECCIONES_APRENDIDAS.md)).
- **Una tabla que compara experimentos se llena con la misma cuenta en cada fila,** sobre los CSV,
  también donde el razonamiento dice que da 0 (LEC-016).

<!-- TODO: ajustar a medida que se fijen (p. ej. type hints, estructura de tests). -->

---

## Notas importantes para Claude Code

<!-- Se gana con el uso: cada nota sale de algo que pasó. Las de abajo salen del diagnóstico
     inicial del 2026-11-14 (docs/qa/AnalisisQA.md#diagnostico-inicial). -->

- **Ante la duda, manda el código.** El README se puso al día en el bloque C del spec de los modos
  (agente, puzzle, fitness, agua, energía y modos, con los números de `config.py`); las secciones
  de clustering, monitor y UI no se revisaron número por número. Un número de los docs se compara
  con lo que usa el código: un valor de `config.py` que nadie lee no verifica nada (LEC-010).
- **`config.py` manda** en energía, consumo, comida, visión, radio, agua, costo de golpear y pesos
  del fitness. Quedan en el código, a propósito: los umbrales de la guía (30, 65, 40%), el radio de
  comer (20 px) y los cooldowns de golpear (el de entre golpes a una puerta es `DOOR_HIT_COOLDOWN`).
  Tres parámetros de `config.py` no los lee nadie: `TREE_HITS_TO_CUT` (dice 2; el árbol pide 3, fijo
  en `src/world/world.py:29`), `STATS_UPDATE_FREQUENCY` y `PARTICLE_UPDATE_FREQUENCY`; y
  `PERIMETER_MARGIN` y `BASE_SPRITE_SIZE` solo se imprimen al arrancar (en
  [mejoras futuras](docs/product/mejoras_futuras.md)).
- **Después de editar código, revisar `git diff` por líneas que eran solo espacios.** El Edit vacía
  las líneas en blanco con espacios que van en el texto nuevo, y muchos archivos (CRLF) las tienen.
  Devolverlas para que el diff muestre solo lo que se quiso cambiar (LEC-002). Para mirar finales
  de línea, el `grep` de Git Bash quita los CR salvo con `-U`: contar bytes con Python (LEC-003);
  y `git show HEAD:archivo` da el blob en LF (`core.autocrlf`): para comparar contra HEAD, sin los
  CR de los dos lados (LEC-009).
  En un archivo CRLF, nunca `sed -i`: lo deja entero en LF y `git diff` no lo muestra (LEC-005).
  Un script de edición escrito con Write pierde los espacios de sus líneas en blanco: que compare
  contra el archivo con los espacios finales recortados y devuelva las líneas que no cambió (LEC-007).
- **Para correr sin ventana, flags, no `config.py`:** `python main.py --sin-ventana --generaciones N
  --semilla S` (`--help` los lista; `--sin-evolucion` es la línea base, `--modo autonomo` el modo
  sin guía, `--acercarse` y `--curriculo` prenden las ayudas y `--deslizar`, el deslizamiento). El
  experimento con los dos modos, con evolución y sin ella, en varias semillas es `python experimento.py`
  (`--modos` elige los modos; `--acercarse`, `--curriculo` y `--deslizar` pasan a todas las corridas).
- **El editor tiene que usar el Python del `.venv`.** Con el Python global (Microsoft Store), la
  extensión Pylint marca "Unable to import 'pygame'" aunque el código corra bien.
  `.vscode/settings.json` lo fija; si vuelve a aparecer: `Ctrl+Shift+P` → *Python: Select
  Interpreter* → `.venv` (DIAG-24). Los `E1101: Module 'pygame' has no … member` de Pylint son
  falsos: `pylint.args` en ese mismo archivo le deja ver los miembros de pygame (DIAG-26).
- **No hay producción.** En la bitácora de un spec, "Para verificar en producción" es N/A: lo que
  se verifica es una corrida.
- **El scratchpad es de una sola sesión.** Un CSV de referencia que otra sesión tiene que comparar
  deja su SHA-256 en la bitácora, con el commit desde el que se regenera (LEC-011).
- **Un control con ventana que depende de una tecla se verifica en el log:** cada tecla de
  `main.py` deja su `print` (`🔍 Zoom IN`…); si no está, la tecla no llegó y el resultado no dice
  nada. Para hacerlo repetible, el evento se inyecta envolviendo `pygame.event.get` desde un script
  (LEC-004).
- **Una corrida sin ventana tarda ~6 s por generación de 960 ticks** con 60 agentes (máquina de 12
  núcleos), más unos 3 s de arranque; las generaciones se alargan 180 ticks cada 4 (con `--deslizar`,
  ~1,5 veces: caminan más ticks). Redirigida a
  archivo, la salida sale con buffer y aparece toda al final: para leer un log mientras corre,
  `python -u` (así lanza las corridas `experimento.py`). Más de 10 corridas a la vez se quedan sin
  memoria virtual y alguna se cae al arrancar; el `wait` de una tanda en segundo plano igual da 0: se
  cuentan las salidas de cada corrida (LEC-017).

---

## Ciclo de vida de specs (regla de trabajo)

Manifiesto completo: `docs/specs/README.md`. Formato: `docs/AGENTES.md`. **Cada spec vive en
una sola carpeta según su estado.**

| Carpeta | Cuándo usar |
|---------|-------------|
| `docs/specs/planned/` | Decisiones cerradas — en cola, aún sin código (o con gate de negocio) |
| `docs/specs/active/` | **Normativo hoy** — leer antes de tocar el feature. Incluye specs parciales |
| `docs/specs/done/` | **Cerrado** — resumen operativo en `docs/archive/SPECS_ARCHIVO.md` |

### Al empezar a implementar
1. Leer el spec. Si está en `planned/` y el trabajo toma más de una sesión, **moverlo a
   `active/`** (`git mv`) y actualizar `docs/specs/README.md`.
   - **Si toma más de una sesión, lleva `## Bitácora de ejecución`**: cada sesión arranca leyendo
     la última entrada y cierra escribiendo la suya, con el prompt de la siguiente. Formato y
     protocolo: `docs/AGENTES.md` § "Specs de varias sesiones".
2. Implementar contra el DoD — no improvisar fuera de scope sin anotar en `BACKLOG.md`.
3. Si el spec tiene fases, cerrar **fase por fase**; no mover a `done/` hasta que esté completo.

### Al cerrar (checklist obligatorio — lo orquesta `/close-spec`)

| # | Qué | Dónde |
|---|-----|-------|
| 1 | Código + verificación técnica | typecheck · tests · build |
| 2 | QA con IDs trazables | `docs/qa/AnalisisQA.md` — sección nueva, IDs `FEATURE-NN`, ✅/❌. No condensar histórico |
| 3 | Resumen condensado | `docs/archive/SPECS_ARCHIVO.md` — anchor `{#slug}`, rutas, archivos clave, link al spec y al QA |
| 4 | Estado en el spec | Primera línea: `**Estado:** ✅ Implementado (YYYY-MM-DD)` o `Parcial — §X ✅; §Y pendiente` |
| 5 | Mover el spec | 100% cerrado → `git mv active/FOO.md done/`. Parcial → queda en `active/` |
| 6 | Manifiesto | `docs/specs/README.md` — mover fila a la tabla correcta |
| 7 | Cola de trabajo | `docs/product/BACKLOG.md` — ítem ✅ con fecha |
| 8 | Stub de redirect | Si moviste el archivo: stub de 5 líneas en la ruta vieja |
| 9 | Lecciones (si aplica) | `docs/operations/LECCIONES_APRENDIDAS.md` |

**El spec es el árbitro. QA bloqueado = no PR.**

---

## Loops con corte verificable (stop-conditions)

Solo automatizar (`/loop`) loops cuyo criterio de "listo" sea **objetivo**. Lo subjetivo
(autoría de spec, decisiones de producto/pricing) queda **manual**.

| Loop | Corte verificable |
|------|-------------------|
| **Fix → re-verify** (tras gaps de QA) | typecheck + tests verdes **y** `/qa-spec` = APROBADO (PARCIAL en vivo NO cierra) |
| **Coherencia memoria/docs** | `/consistency-check` = cero hallazgos ALTO |

**NO automatizar:** autoría/diseño de specs; decisiones de producto; cualquier loop sin
criterio objetivo.

Skills que dan el criterio: `/qa-spec`, `/close-spec`, `/consistency-check`, `/check` y el
hook pre-commit (`.claude/hooks/pre-commit-gate.sh`).

---

## Documentación — dónde está cada cosa

| Necesitás… | Leé… |
|------------|------|
| Implementar features / convenciones | Este archivo (`CLAUDE.md`) |
| Reglas globales (SDD, git, modelo) | `~/.claude/CLAUDE.md` |
| Regla de trabajo specs | `docs/specs/README.md` |
| Formato de spec / autoría | `docs/AGENTES.md` |
| Índice de docs por rol | `docs/README.md` |
| Specs implementados (resumen) | `docs/archive/SPECS_ARCHIVO.md` (cuando exista) |
| QA + IDs trazables | `docs/qa/AnalisisQA.md` |
| Pendientes | `docs/product/BACKLOG.md` (no hay `PENDIENTES.md`: el BACKLOG es el tablero) |
| Ideas sin decidir y lo que aparece fuera de alcance | `docs/product/mejoras_futuras.md` (acá, no en `docs/specs/` como dice la guía global) |
