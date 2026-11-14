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
  Dependencias en `requirements.txt`, que incluye `torch` y `deap` aunque hoy no se usan.
- **pygame 2.6:** ventana, sprites y eventos.
- **numpy:** la red neuronal es propia (`SimpleNeuralNetwork`, en `src/agents/advanced_agent.py`);
  no usa PyTorch.
- **scikit-learn:** clustering de comportamientos (K-Means + PCA). **matplotlib:** gráficos.
- **Sin base de datos, sin web, sin deploy.** Corre local con `python main.py`, con ventana o sin
  ella (`--sin-ventana`, o `HEADLESS_MODE` en `config.py`).

---

## Estructura de carpetas

```
EcosistemaEvolutivo/
├── main.py              ← punto de entrada: flags, semilla, CSV; loop de simulación, render y pantalla final
├── config.py            ← SimulationConfig: parámetros centralizados (varios se ignoran, ver Notas)
├── experimento.py       ← con evolución contra sin evolución, en varias semillas → resumen.md
├── requirements.txt
├── tests/               ← pytest: humo de main.py y cuentas del resumen de experimento.py
├── results/             ← CSV y logs de las corridas (en .gitignore)
├── assets/sprites/      ← sprites de personajes y entorno
├── src/
│   ├── agents/
│   │   ├── advanced_agent.py      ← AdvancedAgent (sensores, decisión, acciones, fitness) + SimpleNeuralNetwork
│   │   └── brain/                 ← código muerto (PyTorch); ni siquiera importa
│   ├── evolution/
│   │   └── genetic_algorithm.py   ← selección (meeting pool / torneo / élite), cruce, mutación, inmigración
│   ├── world/
│   │   ├── world.py               ← mundo procedural, fortalezas, llaves, puertas, cofre, hacha, comida
│   │   └── obstacles.py           ← obstáculos y sus efectos (agua, árboles, casitas)
│   ├── analytics/
│   │   ├── learning_monitor.py    ← métricas por generación, diversidad, reportes por consola
│   │   ├── clustering.py          ← K-Means + PCA sobre comportamientos
│   │   └── metrics.py             ← código muerto (no se importa)
│   └── ui/                        ← renderer (sprites, partículas), panel de stats, popup de resumen
├── docs/                ← metodología: specs, backlog, QA (índice en docs/README.md)
└── .claude/             ← skills del proyecto y hook pre-commit
```

---

## Variables de entorno

<!-- TODO: documentar cada var con un comentario de para qué es. Nunca pegar valores reales
     de secrets — solo el nombre y el propósito. -->

```env
# Hoy no usa ninguna. .env.example existe pero está vacío.
```

---

## Lógica de negocio crítica

<!-- TODO — SE LLENA CON EL PRIMER FEATURE REAL, NO AHORA.
     Acá va la lógica que un agente DEBE conocer y que no es obvia del código: reglas de
     negocio, límites por plan, invariantes del dominio, funciones puras centrales. Cada
     entrada trazable a un spec en docs/specs/. Vacío hasta que exista el primer feature. -->

_(vacío — se llena con el primer feature)_

---

## Convenciones de código

- **Español** en comentarios, docstrings, mensajes de consola y textos de pantalla (así está todo
  el código).
- **Los parámetros van en `config.py`** (`SimulationConfig`), no como números sueltos en el
  código. Hoy no se cumple del todo (ver Notas).
- **Sin formateador ni linter configurados.** No correr black, ruff ni similares con
  `--fix`/`--write` (regla global): reformatearían archivos enteros.
- **Tests con pytest,** en `tests/`: `python -m pytest -q` (el gate pre-commit los corre). Una
  corrida que se quiera comparar con otra lleva semilla fija (`--semilla`): la misma semilla da el
  mismo CSV byte a byte.
- **Una mejora del aprendizaje se demuestra contra la línea base sin evolución,** con la misma
  semilla y con varias semillas. Si la línea base mejora igual, no es aprendizaje (LEC-001 en
  [docs/operations/LECCIONES_APRENDIDAS.md](docs/operations/LECCIONES_APRENDIDAS.md)).

<!-- TODO: ajustar a medida que se fijen (p. ej. type hints, estructura de tests). -->

---

## Notas importantes para Claude Code

<!-- Se gana con el uso: cada nota sale de algo que pasó. Las de abajo salen del diagnóstico
     inicial del 2026-11-14 (docs/qa/AnalisisQA.md#diagnostico-inicial). -->

- **El README describe más de lo que hace el código.** Ante la duda, manda el código. Diferencias
  conocidas (detalle en [docs/qa/AnalisisQA.md](docs/qa/AnalisisQA.md#diagnostico-inicial)):
  - `decide()` lleva a mano a los agentes con fitness alto hacia comida, puertas y llaves: no es
    "aprendizaje puro".
  - La red tiene 4 salidas, no 5: no existe la acción "golpear". Llaves, puertas y árboles se
    activan por cercanía.
  - El estado del puzzle (llaves, puertas, hacha) es del mundo, no de un agente, y persiste entre
    generaciones.
- **`config.py` no manda en todo:** el consumo de energía, la energía por comida, el rango de
  visión, el radio del agente y la recompensa por árbol están fijos en el código.
- **Código muerto:** `src/agents/brain/` y `src/analytics/metrics.py`. No importarlos ni
  arreglarlos: se borran en la limpieza.
- **Hay `.pyc` commiteados** en `src/**/__pycache__/`, aunque `.gitignore` los excluye. Si aparecen
  modificados en `git status`, no stagearlos.
- **Después de editar código, revisar `git diff` por líneas que eran solo espacios.** El Edit vacía
  las líneas en blanco con espacios que van en el texto nuevo, y muchos archivos (CRLF) las tienen.
  Devolverlas para que el diff muestre solo lo que se quiso cambiar (LEC-002). Para mirar finales
  de línea, el `grep` de Git Bash quita los CR salvo con `-U`: contar bytes con Python (LEC-003).
- **Para correr sin ventana, flags, no `config.py`:** `python main.py --sin-ventana --generaciones N
  --semilla S` (`--help` los lista; `--sin-evolucion` es la línea base). El experimento con
  evolución contra sin evolución en varias semillas es `python experimento.py`.
- **El editor tiene que usar el Python del `.venv`.** Con el Python global (Microsoft Store), la
  extensión Pylint marca "Unable to import 'pygame'" aunque el código corra bien.
  `.vscode/settings.json` lo fija; si vuelve a aparecer: `Ctrl+Shift+P` → *Python: Select
  Interpreter* → `.venv` (DIAG-24).
- **No hay producción.** En la bitácora de un spec, "Para verificar en producción" es N/A: lo que
  se verifica es una corrida.
- **Una corrida sin ventana tarda ~6 s por generación de 960 ticks** con 60 agentes (máquina de 12
  núcleos), más unos 3 s de arranque; las generaciones se alargan 180 ticks cada 4. Redirigida a
  archivo, la salida sale con buffer y aparece toda al final: para leer un log mientras corre,
  `python -u` (así lanza las corridas `experimento.py`).

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
| Pendientes | `docs/product/BACKLOG.md` |
