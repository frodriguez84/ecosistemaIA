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
| [Limpieza sin cambiar comportamiento](active/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) — código muerto, dependencias, `.pyc`, duplicación y reportes, con el mismo CSV byte a byte | Antes de tocar `main.py`, `src/` o `requirements.txt`. En ejecución desde el 2026-11-14: bloques A, B y C ✅, con el chequeo de cierre; falta `/close-spec` (cuarta sesión); con bitácora |

## 🔵 Planned (`planned/`)

| Spec | Gate / nota |
|------|----------------|
| _(vacío)_ | |

## ⚫ Done (`done/`)

| Spec | Resumen en SPECS_ARCHIVO |
|------|---------------------------|
| [Medir antes de tocar](done/MEDIR_ANTES_DE_TOCAR.md) — flags, semilla, CSV por generación, `experimento.py`, tests | [§ Medir antes de tocar](../archive/SPECS_ARCHIVO.md#medir-antes-de-tocar) |
