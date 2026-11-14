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
2. - [ ] **Limpieza sin cambiar comportamiento:** código muerto, dependencias sin uso, `.pyc` commiteados, duplicación, bugs de reportes, `.env.example` vacío. Se verifica con la misma semilla: mismos números antes y después. Cubre DIAG-14 a DIAG-21, DIAG-23, lo que queda de DIAG-22, los imports y variables sin usar que marca Pylint (DIAG-26) y DIAG-27. Depende de 1. → spec: [LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO](../specs/active/LIMPIEZA_SIN_CAMBIAR_COMPORTAMIENTO.md) (aprobado el 2026-11-14; en ejecución: bloques A y B ✅ el 2026-11-14, sigue C)
3. - [ ] **Modo guiado y modo autónomo:** switch en `config.py`. El guiado conserva la conducción escrita a mano (documentada como tal); el autónomo es neuroevolución real, con sensores del puzzle, acción de golpear y puzzle individual por generación. Incluye los bugs de fitness y la config ignorada. Cubre DIAG-01 a DIAG-05 y DIAG-08 a DIAG-13. Rumbo decidido por Fer el 2026-11-14 (opción "las dos, para comparar"). Al escribirlo, mirar el reposicionamiento que corre después de `evolve`: casi nunca mueve a nadie, porque `fix_agent_positions` corre antes ([DIAG-27](../qa/AnalisisQA.md#diagnostico-inicial)). Depende de 1. → spec: a escribir

## Decisiones pendientes de Fer

_(ninguna)_

## Hecho

- [x] 2026-11-14 — `LICENSE`: MIT, decidido por Fer (DIAG-22). El `.env.example` vacío pasa a la limpieza (ítem 2): no hay variables de entorno.
- [x] 2026-11-14 — Metodología sembrada (`/bootstrap-project`, plantilla + bitácora en specs) y diagnóstico inicial registrado en [AnalisisQA](../qa/AnalisisQA.md#diagnostico-inicial).
