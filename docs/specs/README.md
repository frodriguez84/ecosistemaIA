# Specs — manifiesto

Contratos de implementación. **No mezclar** con referencia (`../reference/`), ops
(`../operations/`) ni backlog (`../product/BACKLOG.md`).

**Regla de trabajo al implementar o cerrar un spec:** abajo, § *Ciclo de vida de specs*. Formato del
spec: [`../AGENTES.md`](../AGENTES.md).

| Estado | Significado |
|--------|-------------|
| 🟢 **Activo** | Normativo hoy — leer antes de tocar el código |
| 🔵 **Planned** | Decisiones cerradas — en cola de implementación |
| ⚫ **Done** | Implementado — resumen en [`../archive/SPECS_ARCHIVO.md`](../archive/SPECS_ARCHIVO.md) |

Un spec nuevo nace en `planned/` (usar [`/new-spec`](../../.claude/skills/new-spec/SKILL.md)).
Paths viejos tras un `git mv` llevan un stub con redirect.

---

## Ciclo de vida de specs (regla de trabajo)

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

## 🟢 Activos (`active/`)

| Spec | Cuándo leerlo |
|------|----------------|
| _(vacío)_ | |

## 🔵 Planned (`planned/`)

| Spec | Gate / nota |
|------|----------------|
| [El hacha y los árboles](planned/HACHA_Y_ARBOLES.md) — que el modo autónomo aprenda a talar, contra la referencia final de Que aprendan el puzzle solos | Sin gate; decisiones cerradas con Fer el 2026-11-25 |

## ⚫ Done (`done/`)

| Spec | Resumen en SPECS_ARCHIVO |
|------|---------------------------|
| [Que aprendan el puzzle solos](done/PUZZLE_SOLOS.md) — en el autónomo y sin nada dado al nacer, la cadena del puzzle (de la llave roja al cofre) se aprende en 5 de 5 semillas contra la línea base, con cuatro switches nuevos apagados por defecto; comer, no; trece sesiones con bitácora | [§ Que aprendan el puzzle solos](../archive/SPECS_ARCHIVO.md#puzzle-solos) |
| [Que el puzzle se pueda aprender](done/PUZZLE_APRENDIBLE.md) — recompensa por acercarse al próximo paso y currículo (las primeras generaciones nacen con la llave roja), cada uno con su switch; en el autónomo, ninguno hace que aprenda la puerta de madera | [§ Que el puzzle se pueda aprender](../archive/SPECS_ARCHIVO.md#puzzle-aprendible) |
| [Pantallas para ver aprender](done/PANTALLAS_VER_APRENDER.md) — sin el popup de cada generación: gráfico en vivo en el panel, avisos que no tapan y una pantalla final como boletín, sin cambiar la simulación | [§ Pantallas para ver aprender](../archive/SPECS_ARCHIVO.md#pantallas-ver-aprender) |
| [Modo guiado y modo autónomo](done/MODO_GUIADO_Y_AUTONOMO.md) — switch de la conducción escrita a mano, puzzle por agente, brújula, golpear, `config.py` que manda y medición por modo | [§ Modo guiado y modo autónomo](../archive/SPECS_ARCHIVO.md#modo-guiado-y-autonomo) |
| [Limpieza sin cambiar comportamiento](done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) — código muerto, dependencias, `.pyc`, duplicación y reportes, con el mismo CSV byte a byte | [§ Limpieza sin cambiar comportamiento](../archive/SPECS_ARCHIVO.md#limpieza-sin-cambiar-comportamiento) |
| [Medir antes de tocar](done/MEDIR_ANTES_DE_TOCAR.md) — flags, semilla, CSV por generación, `experimento.py`, tests | [§ Medir antes de tocar](../archive/SPECS_ARCHIVO.md#medir-antes-de-tocar) |
