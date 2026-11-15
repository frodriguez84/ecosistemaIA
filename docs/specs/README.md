# Specs — manifiesto

Contratos de implementación. **No mezclar** con referencia (`../reference/`), ops
(`../operations/`) ni backlog (`../product/BACKLOG.md`).

**Regla de trabajo al implementar o cerrar un spec:** checklist en [`CLAUDE.md`](../../CLAUDE.md)
§ *Ciclo de vida de specs*. Formato del spec: [`../AGENTES.md`](../AGENTES.md).

| Estado | Significado |
|--------|-------------|
| 🟢 **Activo** | Normativo hoy — leer antes de tocar el código |
| 🔵 **Planned** | Decisiones cerradas — en cola de implementación |
| ⚫ **Done** | Implementado — resumen en [`../archive/SPECS_ARCHIVO.md`](../archive/SPECS_ARCHIVO.md) |

Un spec nuevo nace en `planned/` (usar [`/new-spec`](../../.claude/skills/new-spec/SKILL.md)).
Paths viejos tras un `git mv` llevan un stub con redirect.

---

## 🟢 Activos (`active/`)

| Spec | Cuándo leerlo |
|------|----------------|
| _(vacío)_ | |

## 🔵 Planned (`planned/`)

| Spec | Gate / nota |
|------|----------------|
| [Modo guiado y modo autónomo](planned/MODO_GUIADO_Y_AUTONOMO.md) — switch de la conducción escrita a mano, puzzle por agente, brújula, golpear, `config.py` que manda y medición por modo | Sin gate. Tres bloques (A reglas, B puzzle, C switch), con bitácora |

## ⚫ Done (`done/`)

| Spec | Resumen en SPECS_ARCHIVO |
|------|---------------------------|
| [Limpieza sin cambiar comportamiento](done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) — código muerto, dependencias, `.pyc`, duplicación y reportes, con el mismo CSV byte a byte | [§ Limpieza sin cambiar comportamiento](../archive/SPECS_ARCHIVO.md#limpieza-sin-cambiar-comportamiento) |
| [Medir antes de tocar](done/MEDIR_ANTES_DE_TOCAR.md) — flags, semilla, CSV por generación, `experimento.py`, tests | [§ Medir antes de tocar](../archive/SPECS_ARCHIVO.md#medir-antes-de-tocar) |
