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
- [x] 2026-11-15 — pasó al [BACKLOG](BACKLOG.md), ítem 6. **Mecánicas nuevas para que aprendan otras cosas.** Se cruza con el modo autónomo (BACKLOG ítem 3): mirarla al escribir ese spec. *Mirada el 2026-11-14:* el spec [MODO_GUIADO_Y_AUTONOMO](../specs/active/MODO_GUIADO_Y_AUTONOMO.md) suma golpear y el puzzle por agente, pero ninguna mecánica nueva; esta idea sigue abierta para después.

## Para ver aprender y para jugar — 2026-11-15

Charladas con Fer al cerrar el spec de los modos. Fer prefiere mirar cómo aprenden antes que jugarlo: lo de jugar (el sandbox) va para más adelante.

- [ ] **Ver qué piensa un agente:** clic en un agente y se ven sus 11 sensores y sus 5 salidas como barras en vivo, con la flecha de la brújula.
- [ ] **Colores por linaje:** cada familia de un color, para ver cómo un linaje exitoso toma la población. Pide que el genético guarde de qué padres viene cada agente.
- [ ] **La estela del mejor:** al arrancar cada generación, el recorrido del mejor de la anterior, tenue.
- [ ] **Sandbox (más adelante):** cambiar parámetros en vivo desde la ventana, guardar el mejor cerebro y volver a verlo, guiado y autónomo lado a lado.
- [ ] **Publicar:** repo público con un GIF y la historia del experimento; después, quizás itch.io (PyInstaller o pygbag). Antes, revisar la licencia de los sprites de `assets/sprites/` (no hay archivo de licencia).

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
- [ ] **Parámetros de `config.py` que no mandan:** `TREE_HITS_TO_CUT` (dice 2; el árbol pide 3, fijo en `src/world/world.py:29`), `STATS_UPDATE_FREQUENCY` y `PARTICLE_UPDATE_FREQUENCY` no los lee nadie; `PERIMETER_MARGIN` y `BASE_SPRITE_SIZE` solo los usan métodos que `print_config()` imprime al arrancar. Apareció el 2026-11-15 en el QA de cierre. Que el árbol lea `TREE_HITS_TO_CUT` puesto en 3 no cambia la simulación; en 2, sí (va con una medición). Los otros cuatro son del dibujo o de la consola: sacarlos o conectarlos no toca la simulación. De paso: los comentarios de `config.py:111` y de `_generate_fortresses` (`world.py`) dicen que la fortaleza chica es de 4x5, y los muros la arman de 5x5.
- [ ] **Sueltos del QA de cierre** (2026-11-15, detalle en [AnalisisQA](../qa/AnalisisQA.md#qa-modo-guiado-y-autonomo)): el popup dice cuántos agentes de la generación abrieron el cofre, pero no la primera generación de la corrida (la decisión 11 la pide); `_try_hit_door` comparte con el corte el cooldown de 120 ticks del agente, así que después de cortar un árbol o de abrir una puerta no puede golpear la siguiente por 120 ticks (ya era así antes del spec; cambiarlo cambia la simulación); el README dice que la mutación es del 30% y el genético la sube a 50% cuando la diversidad baja de 0,15.
