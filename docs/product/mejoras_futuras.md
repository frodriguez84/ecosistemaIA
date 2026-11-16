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
- [ ] **Sueltos del QA de cierre** (2026-11-15, detalle en [AnalisisQA](../qa/AnalisisQA.md#qa-modo-guiado-y-autonomo)): el popup decía cuántos agentes de la generación abrieron el cofre, pero no la primera generación de la corrida (la decisión 11 la pide): resuelto el 2026-11-15, el popup salió y el boletín final la dice (spec *Pantallas para ver aprender*); `_try_hit_door` comparte con el corte el cooldown de 120 ticks del agente, así que después de cortar un árbol o de abrir una puerta no puede golpear la siguiente por 120 ticks (ya era así antes del spec; cambiarlo cambia la simulación; en la [medición de la puerta](../qa/AnalisisQA.md#medicion-puerta-madera), con el currículo, después de cortar no frenó ningún golpe, y el de los primeros 120 ticks de cada generación solo demora a los que nacen cerca); el README dice que la mutación es del 30% y el genético la sube a 50% cuando la diversidad baja de 0,15.

## Fuera de alcance del spec Que el puzzle se pueda aprender — 2026-11-15

Aparecido al escribir el [spec](../specs/done/PUZZLE_APRENDIBLE.md) con Fer, con la medición de su § Problema.

- [ ] **Más presión selectiva en el genético:** el meeting pool elige al azar dentro del 60% de arriba, más una élite, así que un término del fitness solo pesa si cambia quién queda adentro de ese 60%. Cambiarlo cambia todo lo aprendido hasta ahora: va con una medición propia.
- [x] 2026-11-16 — **Una medida de "usa la brújula":** el coseno entre el rumbo y la brújula da negativo también con cerebros al azar (−0,09 a −0,19), probablemente porque el que camina derecho pasa cerca y se aleja. Una alternativa: si gira hacia el lado que marca la brújula más seguido que al azar. **Resuelto con un punto de control** en la [medición de la puerta](../qa/AnalisisQA.md#medicion-puerta-madera): el camino hecho hacia el objetivo de la brújula contra el camino hecho hacia un punto al que no apunta (la llave roja, con la etapa 1). Si la evolución los sube igual, caminan más; si sube solo el del objetivo, la usan.
- [ ] **Medir las dos ayudas en el modo guiado:** valen para los dos modos, pero el spec mide solo el autónomo.
- [ ] **Variantes descartadas, por si el resultado las vuelve a poner en juego:** un currículo que avanza cuando se aprende (la línea base no lo destraba nunca, y al final cada una corre en otro mundo); la llave roja sorteada cerca de la puerta (enseñaría "ir arriba a la izquierda" en lugar de seguir la brújula); una recompensa basada en potencial, por dónde termina el agente (castiga a los que caminan: −0,15 medido).

## Aparecido al ejecutar el spec Que el puzzle se pueda aprender — 2026-11-15

- [x] 2026-11-16 — **Dónde se traba la puerta de madera:** con la llave dada a los 60 agentes durante 15 generaciones, la evolución la abre lo mismo que el azar (8 veces contra 9 en el [experimento B](../qa/AnalisisQA.md#experimento-puzzle-b); 6 contra 9 en el C, con la recompensa por acercarse). Medir en el currículo, con evolución y sin ella, cuántos llegan a menos de 25 px del centro de la puerta, cuántos golpean ahí y cuántos golpes cuentan, sin consumir azar (como la medición del § Problema del spec). Es lo que diría si el paso siguiente es el camino, golpear o la selección. **Resultado:** el camino, por dos órdenes de magnitud (el 99,4% nunca llega a menos de 25 px, y los que llegan nacieron cerca); no usan la brújula (con evolución, el camino hacia la puerta sube lo mismo que hacia un punto de control); y aunque la usaran, chocar no desliza y un seguidor de brújula perfecto llega solo en el 12% de los arranques (50% deslizando). Golpear pierde ~la mitad de los que llegan y el segundo golpe ~un tercio; la selección sí elige a los que abren ([medición](../qa/AnalisisQA.md#medicion-puerta-madera)).
- [x] 2026-11-16 — **Que chocar deslice** (sugerido por la [medición de la puerta](../qa/AnalisisQA.md#medicion-puerta-madera), 2026-11-16): hoy, si el paso choca, el agente no se mueve, y queda trabado contra lo primero que encuentra en línea recta. Deslizando (moverse por el eje libre), un seguidor de brújula perfecto llega a la puerta en el 50% de los arranques, contra 12% hoy, y entra a la franja de la puerta por la pared sur. Cambia la simulación en los dos modos (también comer y caminar): con un switch, y medido como las ayudas (el B con y sin deslizar: la puerta, y el camino hacia la puerta contra el punto de control). Se cruza con DIAG-30 (la caja descentrada contra el estanque y el perímetro). **Hecho:** switch `DESLIZAR` (`--deslizar`), apagado por defecto; con las mismas colisiones de `act()`, DIAG-30 incluido; apagado, el CSV es el de antes byte a byte. **Resultado:** abre el camino para todos (con la llave dada, llegan a la puerta 3 veces más con evolución y 2,4 sin ella; comen más y agarran más la llave, 5 de 5 semillas), y la evolución abre la puerta más que el azar en las 15 generaciones del currículo (17 contra 10, 4 de 5 semillas), pero no lo aprende: no crece con las generaciones y el criterio del ítem 5 da 0 de 5. Siguen sin usar la brújula: el camino hacia la puerta y hacia el punto de control suben lo mismo ([medición y experimento](../qa/AnalisisQA.md#deslizar-al-chocar)).
- [ ] **Los tests de humo lanzan 12 corridas a la vez, y a veces una se cae:** pasó 2 veces en unas 12 corridas del humo del 2026-11-15. La primera, importando scipy, antes de simular, con la memoria virtual de la máquina al 72%; de la segunda no quedó el mensaje. Repetido, pasa. Si vuelve, guardar el log (`--basetemp`) y, según el error, limitar las corridas simultáneas del fixture u `OPENBLAS_NUM_THREADS=1` (controlando que el CSV no cambie). **Volvió el 2026-11-16, con el mensaje:** en la medición de la puerta, con 15 corridas a la vez (fuera del humo), una se cayó importando scipy con "DLL load failed while importing _lsoda: El archivo de paginación es demasiado pequeño para completar la operación". Es memoria virtual de Windows; con 10 a la vez no pasó (LEC-017). **Y otra vez el 2026-11-16, en el humo,** al terminar el experimento de deslizar: 2 de las 12 corridas se cayeron importando scipy con el mismo mensaje (`cython_blas` y `_matfuncs_expm`), y fallaron 10 tests; repetido, 15 de 15. Los logs quedaron en la carpeta temporal de pytest (`pytest-60/humo0`, fuera del repo). Tres veces en dos días: limitar las corridas simultáneas del fixture ya vale la pena.

## Aparecido al medir deslizar — 2026-11-16

Con la [medición y el experimento](../qa/AnalisisQA.md#deslizar-al-chocar) de deslizar.

- [x] 2026-11-16 — **Deslizar prendido por defecto** (decisión de Fer): mejora comer, la llave y llegar a la puerta, con evolución y sin ella, y la evolución sigue sumando encima (5 de 5 en fitness, manzanas y llave). Prenderlo cambia todas las corridas: los experimentos anteriores dejan de ser la línea base de los nuevos, y las corridas tardan ~1,5 veces. **Decidido por Fer: queda apagado por defecto;** se prende con `--deslizar`.
- [ ] **Que la brújula se aprenda:** deslizando, un seguidor de brújula perfecto llega a la puerta en el 50% de los arranques y los agentes en el 1,7%; la evolución sube igual el camino hacia la puerta y hacia un punto de control. Es el cuello que queda para la puerta de madera. Candidatos ya anotados: más presión selectiva y el sensor de obstáculos con dirección.
