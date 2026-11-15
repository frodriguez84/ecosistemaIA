# Mejoras futuras — Ecosistema Evolutivo IA

Ideas que todavía no son trabajo decidido: sin priorizar y sin spec. Cuando una se decide, pasa al
[BACKLOG](BACKLOG.md) como ítem (y de ahí a un spec), y acá se marca con la fecha y el link.
También viene acá lo que aparece fuera de alcance mientras se ejecuta un spec, con de dónde salió.

Convención: `- [ ]` abierta · `- [x]` pasó al BACKLOG o se descartó (con fecha y por qué).

---

## Ideas de Fer — 2026-11-14

- [ ] **Assets:** revisar la carpeta `C:\Users\usuario\eclipse-workspace\2DGame\res` (fuera del repo): hay de todo para usar.
- [ ] **Enemigos.**
- [ ] **Más objetos.**
- [ ] **Transición de mapa, historia, storytelling.**
- [ ] **Mecánicas nuevas para que aprendan otras cosas.** Se cruza con el modo autónomo (BACKLOG ítem 3): mirarla al escribir ese spec. *Mirada el 2026-11-14:* el spec [MODO_GUIADO_Y_AUTONOMO](../specs/active/MODO_GUIADO_Y_AUTONOMO.md) suma golpear y el puzzle por agente, pero ninguna mecánica nueva; esta idea sigue abierta para después.

## Fuera de alcance del spec Modo guiado y modo autónomo — 2026-11-14

Decidido con Fer al escribir el [spec](../specs/active/MODO_GUIADO_Y_AUTONOMO.md): primero la versión simple, y estas cuando haya una medición con qué compararlas.

- [ ] **Un par de sensores (dirección y distancia) por objeto del puzzle,** más el inventario, en lugar de la brújula al próximo paso. La red tendría que aprender el orden del puzzle; es mucho más difícil.
- [ ] **Visión por rayos:** N rayos con la distancia y el tipo de lo que tocan.
- [ ] **Sensor de obstáculos con dirección:** hoy el sensor 4 da la distancia al obstáculo más cercano, sin dirección (DIAG-02).
- [ ] **Brújula al hacha y a los árboles:** en el spec quedan sin brújula.
- [ ] **Que comer cueste** (energía o quedarse quieto): hoy una red que siempre come no pierde nada, así que "aprender a comer" es aprender a llegar a la manzana.
- [ ] **Los umbrales de la guía a `config.py`** (30, 65 y 40%): en el spec quedan en el código, comentados como guía.

## Aparecido al ejecutar el spec Modo guiado y modo autónomo

- [ ] **Colisión centrada con el estanque y el perímetro (DIAG-30):** al moverse, el agente mira una caja que va de su posición hacia abajo y a la derecha, y puede meterse medio cuerpo en el estanque. Apareció el 2026-11-14 en el bloque A, al verificar la ubicación de agentes (que ya usa una caja centrada). Cambiarlo cambia la simulación: va con una medición.
- [ ] **Código sin uso en `obstacles.py`:** la clase `Axe` (el hacha es un dict de `world.py`) y, desde el bloque B (2026-11-15), `Key.collect` y `Key.collected`: las llaves quedan en el mapa y nadie las recoge. El dibujo todavía mira `collected`. Sacarlo no cambia la simulación.
