# Formato de specs — Ecosistema Evolutivo IA

**Fuente de verdad del formato de spec y de las convenciones de autoría.** El `CLAUDE.md`
global (genérico a todos los proyectos) referencia este archivo. El *ciclo de vida* (cómo se
**cierra** un spec) vive en [`../CLAUDE.md`](../CLAUDE.md) § "Ciclo de vida de specs"; acá va
el **formato** y la autoría. El scaffold lo automatiza [`/new-spec`](../.claude/skills/new-spec/SKILL.md).

## Dónde vive un spec
- `docs/specs/planned/` — decisión cerrada, en cola (o gateada). Sin código.
- `docs/specs/active/` — normativo hoy (leer antes de tocar el feature). Incluye specs parciales.
- `docs/specs/done/` — cerrado. Resumen operativo en `docs/archive/SPECS_ARCHIVO.md`.

Manifiesto: [`specs/README.md`](specs/README.md). Un spec nuevo nace en `planned/`.

## Header obligatorio
```
# Spec: <Título>

**Estado:** <🔵 Planned — en diseño | Parcial — §X ✅; §Y pendiente | ✅ Implementado (YYYY-MM-DD)>
**Prioridad:** <Alta/Media/Baja — por qué>
**Gate:** <Ninguno | condición de negocio que lo destraba>
**Bloquea:** <nada | qué>
**Depende de:** <specs/archivos>
```

## Cuerpo (secciones estándar)
- `## Problema` — qué duele hoy.
- `## Objetivo` — qué logra.
- `## Qué NO es esta feature` — fuera de scope explícito.
- `## Decisiones cerradas` — tabla numerada de decisiones de diseño.
- `## Criterios de done (DoD)` — checklist de criterios **verificables** (los verifica `/qa-spec`).
- `## QA manual (IDs propuestos)` — tabla `| ID | Caso | Criterio |`, prefijo `<SLUG>-NN`.

Opcionales según el spec: Implementación, Edge cases, Wireframes, Esfuerzo, Relación con
otros specs, v2 (fuera de scope).

**Obligatoria si la ejecución toma más de una sesión:** `## Bitácora de ejecución`, al final del
spec. Ver la sección siguiente.

## Specs de varias sesiones — la bitácora de ejecución

Cada sesión tiene que saber qué hizo la anterior, qué le toca y qué le deja a la siguiente. **El
estado vive en el spec, no en el chat**: un prompt que pasa de chat en chat se rompe si se saltea
una sesión, si se corren dos o si una se corta a mitad de camino.

**Formato.** Una entrada por sesión, al final del spec, escrita al cerrar (también si quedó a
medias):

```
### Sesión N — AAAA-MM-DD — <fase o bloque>
- Hecho: qué se cerró, con el commit.
- Estados: qué criterios del DoD o casos de QA cambiaron.
- Desvíos del spec, y por qué. Un texto o un valor que se aparta del que da una decisión es un desvío,
  aunque la decisión lo dé con una variable ("las últimas K"): se confirma con Fer (LEC-014).
- A medias o bloqueado: qué falta y qué lo destraba.
- Para verificar en producción después del deploy.
- Próxima sesión: fase o bloque, primer paso concreto, trampas que aparecieron.
```

**Protocolo de sesión.**
- **Al arrancar:** leer el spec y la **última entrada de la bitácora**; tomar su "Próxima sesión";
  `git status -sb`; si la entrada anterior dejó algo para verificar en producción, verificarlo
  antes de construir encima.
- **Al cerrar:** actualizar los estados del spec; escribir la entrada; lecciones, QA y backlog según
  corresponda; commit con confirmación; darle al usuario el prompt de la próxima sesión.

**El prompt de cada sesión es siempre el mismo:**

```
Ejecución de <spec>.
Seguí el protocolo de sesión de docs/specs/active/<SLUG>.md:
leé la última entrada de la Bitácora de ejecución y tomá su "Próxima sesión".
[Notas para esta sesión, si hay]
```

- Las sesiones de un mismo spec van **en secuencia**, nunca en paralelo.
- Una memoria de proyecto apunta al spec en ejecución; se borra al cerrarlo.
- Un trabajo de una sola sesión no lleva bitácora.

## Plantilla mínima (la usa `/new-spec`)
```
# Spec: <Título>

**Estado:** 🔵 Planned — en diseño
**Prioridad:** <Alta/Media/Baja — por qué>
**Gate:** <Ninguno | condición de negocio>
**Bloquea:** <nada | qué>
**Depende de:** <specs/archivos>

---

## Problema
<qué duele hoy>

## Objetivo
<qué logra>

## Qué NO es esta feature
- <fuera de scope>

## Decisiones cerradas
| # | Decisión |
|---|----------|
| 1 | <...> |

## Criterios de done (DoD)
- [ ] <criterio verificable>

## QA manual (IDs propuestos)
| ID | Caso | Criterio |
|----|------|----------|
| <SLUG>-01 | <...> | <...> |
```

## Convenciones de IDs de QA
- Prefijo `<SLUG>-NN` (SLUG = nombre corto del spec en mayúsculas), ej. `DASH-MG-01`.
- Resultados en `docs/qa/AnalisisQA.md`: header `## QA manual — …` (a mano) o
  `## QA /qa-spec — …` (automático, [`/qa-spec`](../.claude/skills/qa-spec/SKILL.md)). No
  reiniciar numeración existente.

## Cierre
Checklist de cierre (9 pasos) en [`../CLAUDE.md`](../CLAUDE.md) § "Ciclo de vida de specs".
Lo orquesta [`/close-spec`](../.claude/skills/close-spec/SKILL.md).
