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
3. - [ ] **Modo guiado y modo autónomo:** switch en `config.py`. El guiado conserva la conducción escrita a mano (documentada como tal); el autónomo es neuroevolución real, con sensores del puzzle, acción de golpear y puzzle individual por generación. Incluye los bugs de fitness y la config ignorada. Cubre DIAG-01 a DIAG-05 y DIAG-08 a DIAG-13. Rumbo decidido por Fer el 2026-11-14 (opción "las dos, para comparar"). Al escribirlo, mirar el reposicionamiento que corre después de `evolve`: casi nunca mueve a nadie, porque `fix_agent_positions` corre antes ([DIAG-27](../qa/AnalisisQA.md#diagnostico-inicial)). Y en la pantalla final (encontrado en el bloque C de la limpieza): el `→` de "¿APRENDIERON?" sale como un cuadrado, porque la fuente por defecto de pygame no tiene el glifo; y el id del "TOP AGENTE" es `id(self)`, la dirección de memoria, así que cambia entre dos corridas iguales. Y del QA de cierre de la limpieza: `src/ui/popup.py:93` conserva un `.get('total_agents', 50)` cuyo 50 nunca se usa, y el README lista `logs/` y `checkpoints/`, que no existen. Depende de 1. → spec: a escribir

## Decisiones pendientes de Fer

_(ninguna)_

## Hecho

- [x] 2026-11-14 — `LICENSE`: MIT, decidido por Fer (DIAG-22). El `.env.example` vacío pasa a la limpieza (ítem 2): no hay variables de entorno.
- [x] 2026-11-14 — Metodología sembrada (`/bootstrap-project`, plantilla + bitácora en specs) y diagnóstico inicial registrado en [AnalisisQA](../qa/AnalisisQA.md#diagnostico-inicial).
