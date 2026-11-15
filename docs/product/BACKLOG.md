# Backlog — Ecosistema Evolutivo IA

Cola de trabajo. Una línea por ítem + link al spec cuando exista. El **detalle de diseño**
vive en `docs/specs/`, no acá. Las ideas que todavía no se decidieron viven en
[mejoras_futuras.md](mejoras_futuras.md).

Convención: `- [ ]` pendiente · `- [x]` hecho (con fecha) · `→ spec:` link si tiene spec.

---

## Próximo

En este orden: sin medición, cada cambio al aprendizaje se evalúa a ojo; y la limpieza se
verifica comparando corridas con la misma semilla. Todo sale del
[diagnóstico inicial](../qa/AnalisisQA.md#diagnostico-inicial) del 2026-11-14.

1. - [x] 2026-11-14 — **Medir antes de tocar:** parámetros por línea de comando (sin ventana, generaciones, semilla), corridas reproducibles, métricas por generación a CSV, comparación entre corridas con varias semillas, línea base sin evolución y test de humo. Cubre DIAG-06, DIAG-07 y DIAG-25. Resultado: la evolución sube más que la línea base en 5 de 5 semillas ([experimento](../qa/AnalisisQA.md#experimento-cinco-semillas)). → spec: [MEDIR_ANTES_DE_TOCAR](../specs/done/MEDIR_ANTES_DE_TOCAR.md) (QA APROBADO)
2. - [x] 2026-11-14 — **Limpieza sin cambiar comportamiento:** código muerto, dependencias sin uso, `.pyc` commiteados, duplicación, bugs de reportes, `.env.example` vacío. Se verifica con la misma semilla: mismos números antes y después. Cubre DIAG-14 a DIAG-21, DIAG-23, lo que queda de DIAG-22, los imports y variables sin usar que marca Pylint (DIAG-26) y DIAG-27. Resultado: los CSV de 5 semillas × 20 generaciones, idénticos byte a byte a la línea base; `main.py` de 1.391 a 725 líneas. → spec: [LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO](../specs/done/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) (QA APROBADO)
3. - [ ] **Modo guiado y modo autónomo:** switch en `config.py` que cambia solo la conducción escrita a mano; mundo, puzzle (por agente y por generación), brújula al próximo paso, acción de golpear y fitness son comunes a los dos modos. Los valores de `config.py` que hoy se ignoran pasan a mandar, con los pesos del fitness. `experimento.py` compara cada modo contra su línea base sin evolución, y los modos entre sí. Cubre DIAG-01 a DIAG-05, DIAG-08 a DIAG-13, DIAG-28 y DIAG-29, y los sueltos de la limpieza (la ubicación de agentes de DIAG-27, el `→` y el `id(self)` de la pantalla final, el 50 de `popup.py:93`, `logs/` y `checkpoints/` en el README). Rumbo decidido por Fer el 2026-11-14 (opción "las dos, para comparar"); decisiones del spec cerradas con Fer el mismo día. Depende de 1. → spec: [MODO_GUIADO_Y_AUTONOMO](../specs/active/MODO_GUIADO_Y_AUTONOMO.md) (active: bloque A ✅ 2026-11-14 y bloque B ✅ 2026-11-15, con sus experimentos: [A](../qa/AnalisisQA.md#experimento-modos-a), [B](../qa/AnalisisQA.md#experimento-modos-b); sigue C)

## Decisiones pendientes de Fer

_(ninguna)_

## Hecho

- [x] 2026-11-14 — `LICENSE`: MIT, decidido por Fer (DIAG-22). El `.env.example` vacío pasa a la limpieza (ítem 2): no hay variables de entorno.
- [x] 2026-11-14 — Metodología sembrada (`/bootstrap-project`, plantilla + bitácora en specs) y diagnóstico inicial registrado en [AnalisisQA](../qa/AnalisisQA.md#diagnostico-inicial).
