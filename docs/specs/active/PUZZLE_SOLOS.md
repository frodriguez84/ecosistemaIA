# Spec: Que aprendan el puzzle solos

**Estado:** Parcial — paso 2 (llave roja) ✅; pasos 1 (comer) y 3 (puerta de madera) en curso; el resto pendiente. Decisiones cerradas con Fer el 2026-11-21 (la 6, cambiada el 2026-11-22)
**Prioridad:** Alta — es el rumbo del modo autónomo, pedido por Fer el 2026-11-21
**Gate:** Ninguno
**Bloquea:** el ítem 6 del [BACKLOG](../../product/BACKLOG.md) (mecánicas nuevas) y el hacha y los árboles: entran cuando el puzzle esté aprendido
**Depende de:** [Que el puzzle se pueda aprender](../done/PUZZLE_APRENDIBLE.md) (recompensa por acercarse, currículo), los switches `DESLIZAR` y `FORTALEZAS_MOVILES`, `mediciones/medir_puerta.py` y las mediciones del 16 al 21 de noviembre en [AnalisisQA](../../qa/AnalisisQA.md)

---

## Problema

Desde el 2026-11-16, cada sesión fue una medición suelta: medía una cosa, escribía su "Qué sugiere" y Fer elegía la
siguiente. El hilo vivía en la memoria y en el chat. Funcionó (la llave roja ya se aprende sola y se sabe dónde se traba
la puerta de madera), pero no hay un orden escrito de lo que falta, ni una definición común de cuándo un paso está
aprendido, ni un lugar donde una sesión nueva vea qué hizo la anterior y qué le toca.

## Objetivo

Que en el modo autónomo, sin nada dado al nacer, los agentes aprendan en orden: **comer, la llave roja, la puerta de
madera, la llave dorada, la puerta de hierro y el cofre**. Cada paso, medido con el mismo criterio contra la línea base
sin evolución. Al final, una corrida donde se aprende todo junto.

Después de este spec (no en él): el hacha y los árboles, y las mecánicas nuevas.

## Qué NO es esta feature

- **El hacha y los árboles:** van después del cofre (decisión 1). Lo que se sabe del código, en
  [mejoras futuras](../../product/mejoras_futuras.md#el-hacha-y-los-árboles-después-del-cofre--2026-11-21).
- **Las mecánicas nuevas** (enemigos, objetos; ítem 6 del BACKLOG): cuando el puzzle esté aprendido.
- **El modo guiado:** no se toca.
- **Prender switches por defecto:** cada uno lo decide Fer, como hasta hoy.
- **Un cambio sin medir:** todo cambio se mide contra la referencia, con su criterio escrito antes de correr.

## Decisiones cerradas

| # | Decisión |
|---|----------|
| 1 | **El orden:** comer → llave roja → puerta de madera → llave dorada → puerta de hierro → cofre. El hacha y los árboles, después del cofre (Fer, 2026-11-21): la cadena está más cerca, y la red no ve ni el hacha ni los árboles, así que talar probablemente pida un sensor nuevo, que cambia la red y cortaría las comparaciones a mitad de camino. |
| 2 | **"Solos"** (Fer, 2026-11-21): modo autónomo y nada dado al nacer **en la ventana que se mide** (las últimas 5 generaciones). Valen la brújula (es un sensor: igual tienen que aprender a usarla), la recompensa por acercarse, los switches del mundo (deslizar, fortalezas móviles) y un currículo que se corta antes de esa ventana, como el de la referencia (hasta la 30): es una ayuda de arranque, como acercarse (confirmado por Fer). Lo dado al nacer no cuenta como logro (`etapa_inicial`). |
| 3 | **La referencia:** la condición de [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada), `medir_puerta.py . SALIDA S evolucion 150 acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`, semillas 1 a 5, con su línea base sin evolución. Sus CSV y SHA-256 están publicados. La referencia vigente se anota en la bitácora: cuando un cambio pasa su criterio y Fer decide quedárselo, la corrida con ese cambio pasa a ser la referencia nueva, con su comando. |
| 4 | **Un cambio por vez** contra la referencia vigente (LEC-019). Si hace falta cambiar dos cosas, el diseño lleva el control que cambia una sola. |
| 5 | **El criterio común de "aprendido",** el mismo en cada paso: en las últimas 5 generaciones, en **4 de 5 semillas** el paso supera a la línea base sin evolución de la misma semilla; con un **tamaño mínimo**; y se lee junto con **un control o una medida independiente** (LEC-018). Para los pasos del puzzle, el tamaño mínimo por defecto es el del ítem 5: al menos 1 agente por generación, en promedio, que da el paso (`agentes_llave_roja`, `agentes_puerta_madera`, `agentes_llave_dorada`, `agentes_puerta_hierro`, `agentes_cofre` del CSV de `main.py`). Comer se mide aparte (decisión 6). La sesión del bloque escribe los números de su criterio en AnalisisQA **antes de correr**. |
| 6 | **Comer aprendido** no es comer más: el 16/11 comían más porque caminaban más, y la red no giraba hacia la comida ([brújula, deslizando](../../qa/AnalisisQA.md#brujula-c-deslizando)). Pide las dos cosas, que no dependen de cuánta comida queda: **la sensibilidad de la red a la comida** antes de abrir la puerta ((`sens_comida` + `sens_comida0`) / (`sens_ticks` + `sens_ticks0`)) ≥ 0,02 rad/tick (el umbral de la brújula) y por arriba de la línea base de la misma semilla, en 4 de 5 semillas; y, como medida independiente, que **dentro de cada generación los que giran más hacia la comida coman más** que los de su generación (el Spearman entre la sensibilidad y las manzanas de cada agente, mediana de las gens 121-150 de las 5 semillas, por arriba de la de la línea base). Las manzanas por 1.000 px se informan, sin criterio: con 70 manzanas sin reponer, la evolución se come del 80% al 90% y la medida queda sesgada en contra (LEC-022). Cambiada por Fer el 2026-11-22, con la [medición de comer](../../qa/AnalisisQA.md#comer); antes pedía más manzanas por 1.000 px en lugar de la medida de adentro de la generación. |
| 7 | **Cada bloque sigue el mismo ciclo:** medir el paso en la referencia → si pasa, se anota y se sigue con el próximo; si no, diagnosticar dónde se traba (una medición) → un cambio por vez → medirlo contra la referencia. Un cambio que toca la simulación entra con un switch apagado por defecto y con sus tests. Un cambio que se puede hacer con argumentos de `medir_puerta.py` (`pesos=`, `cruce=`, `curriculo=`) va sin código. |
| 8 | **Cada sesión deja lo de siempre:** su sección en AnalisisQA (criterio previo, resultados, lectura, qué sugiere y SHA-256), lo que aparezca fuera de alcance en mejoras futuras, su línea en el BACKLOG, y su entrada en la bitácora de este spec. El estado de cada paso, en la tabla de abajo. |
| 9 | **Lo que decide Fer:** qué cambio se prueba cuando hay más de uno, si un cambio que pasó queda en la referencia, y prender switches por defecto. La sesión sugiere; no elige sola. |

## Estado por paso

| # | Paso | Estado | Dónde |
|---|------|--------|-------|
| 1 | Comer | 🔄 No aprendido en la referencia (2026-11-22): la sensibilidad a la comida, 3 de 5 (+0,014). Giraban hacia la comida hasta la 60 (+0,047) y lo pierden: desde ahí la selección casi no lo ve, aunque los que giran comen más que los de su generación. La larga sí gira (+0,046). Lo que se prueba: `FITNESS_FOOD` en 20 (Fer, 2026-11-22) | [comer](../../qa/AnalisisQA.md#comer) |
| 2 | Llave roja | ✅ En la referencia (2026-11-20): 44,5 de 60 por generación, 5 de 5 semillas, 38 veces la línea base y 9,8 veces por 1.000 px | [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada) |
| 3 | Puerta de madera | 🔄 2 de 5 en la referencia (2,5 por generación). El cuello es golpear: el golpe en general (57%) y el condicionado a la distancia (43%). **El costo de golpear es lo que frena** (2026-11-21): sin `HIT_ENERGY_COST`, 7,6 por generación y el umbral del ítem 5 en 5 de 5, pero golpeando en todos lados. La referencia, con o sin costo, la decide Fer: antes, se mide el costo en 0,01 (Fer, 2026-11-22) | [golpear en la puerta](../../qa/AnalisisQA.md#sens-golpe), [el costo](../../qa/AnalisisQA.md#costo-golpe) |
| 4 | Llave dorada | ⏳ Llegan las 5 semillas, pero pocos: 351 agentes en las gens 31-150. Sin costo de golpear, 2.056, como la larga | [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada), [el costo](../../qa/AnalisisQA.md#costo-golpe) |
| 5 | Puerta de hierro | ⏳ Nadie en la referencia (en la larga, con la llave dada, 8 agentes en la semilla 4). Sin costo de golpear, 21 agentes en 4 semillas | ídem |
| 6 | Cofre | ⏳ Nadie en la referencia (en la larga, 6 en la semilla 4). Sin costo de golpear, 7 agentes en las semillas 1 y 4 | ídem |
| 7 | Todo junto | ⏳ Una corrida final con los 6 pasos | — |

Un paso ✅ se vuelve a mirar en la corrida final: un cambio para un paso posterior puede romper uno anterior.

## Criterios de done (DoD)

- [ ] Cada paso (comer, llave roja, puerta de madera, llave dorada, puerta de hierro, cofre) cumple el criterio común en
      la referencia vigente, con su sección en AnalisisQA.
- [ ] La corrida final: la referencia vigente, 5 semillas, con los 6 pasos cumpliendo el criterio común en la misma
      tanda, y nada dado al nacer en la ventana que se mide.
- [ ] La referencia final escrita en este spec (comando, switches y pesos), con los SHA-256 de sus CSV.
- [ ] Cada cambio a la simulación que hizo falta, con su switch, sus tests, y la decisión de Fer sobre si va por defecto.
- [ ] El README dice lo que aprende el modo autónomo, y es verdad (con los números de la corrida final).
- [ ] El hacha y los árboles, anotados en el BACKLOG como el paso que sigue.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| SOLOS-01 | Comer | Decisión 6, en las 5 semillas de la referencia vigente |
| SOLOS-02 | Llave roja | Decisión 5 |
| SOLOS-03 | Puerta de madera | Decisión 5 (es el criterio del ítem 5) |
| SOLOS-04 | Llave dorada | Decisión 5 |
| SOLOS-05 | Puerta de hierro | Decisión 5 |
| SOLOS-06 | Cofre | Decisión 5 |
| SOLOS-07 | Todo junto | Los 6 en la misma tanda, nada dado al nacer en la ventana |
| SOLOS-08 | Lo que dice el README | Los números del README sobre el autónomo son los de la corrida final |

## Herramientas y tiempos

- **Medir:** `mediciones/medir_puerta.py` (sus argumentos, en su docstring) y un script de análisis por medición en
  `mediciones/`. Las reglas para medir y comparar, en [OPERACIONES](../../operations/OPERACIONES.md#medir).
- **Tiempos:** una tanda de 150 generaciones tarda ~1 h 30 min con 5 a 10 corridas a la vez; no más de 10 a la vez, y se
  cuentan las líneas `MEDICION` (LEC-017). Las 300 generaciones duplican el tiempo.
- **Los CSV** quedan en `results/` (fuera del repo): lo que otra sesión necesita comparar deja su SHA-256 en AnalisisQA.

## Prompt de cada sesión

```
Ejecución de Que aprendan el puzzle solos.
Seguí el protocolo de sesión de docs/specs/active/PUZZLE_SOLOS.md:
leé la última entrada de la Bitácora de ejecución y tomá su "Próxima sesión".
```

## Bitácora de ejecución

### Sesión 1 — 2026-11-21 — Paso 3, puerta de madera: el costo de golpear
- **Hecho:** el spec, escrito con Fer (las decisiones 1 y 2; el currículo de arranque, confirmado). La medición del costo
  de golpear ([AnalisisQA](../../qa/AnalisisQA.md#costo-golpe)): la referencia con `HIT_ENERGY_COST:0` (vía `pesos=`, sin
  código), 5 semillas, contra la referencia publicada. `medir_puerta.py` suma `ENERGIA_GOLPE`, lo que cobró golpear medido
  en la energía (no cambia ningún CSV), y hay un script nuevo, `mediciones/analizar_costo_golpe.py`. Commit: el de esta
  sesión, confirmado por Fer.
- **Estados:** el paso 3 sigue 🔄. Veredicto: el costo frena la puerta sin la llave, por el golpe en general. Sin costo,
  la puerta pasa de 2,5 a 7,6 por generación (4 de 5; el umbral del ítem 5, 5 de 5), pero golpean en todos lados (61% de
  los ticks lejos de la puerta) y el golpe condicionado sube en 3 de 5 semillas, no en 4. La cadena avanza: la llave
  dorada como en la larga, la puerta de hierro en 4 semillas, el cofre en 2.
- **Desvíos del spec:** ninguno. La medición se diseñó antes de que existiera el spec y sigue sus decisiones 3 a 5.
- **A medias o bloqueado:** la referencia sigue siendo la de la decisión 3 (con costo) hasta que Fer decida entre el costo
  en 0, un costo más chico o seguir así ([BACKLOG](../../product/BACKLOG.md), "Decisiones pendientes de Fer").
- **Para verificar en producción:** N/A.
- **Próxima sesión:** el paso 1, comer (decisión 6), sobre la referencia de la decisión 3 y su línea base, con los CSV
  publicados de `results/medicion_sin_llave_20261120/`, sin corridas. Si Fer ya cambió la referencia, comer se mide igual
  sobre estos CSV: la referencia nueva se vuelve a mirar en la corrida final. Primer paso: controlar los 20 `corrida_*.csv` y
  `agentes_*.csv` de esa carpeta contra su SHA-256 publicado ([sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada)) y escribir en
  AnalisisQA los números del criterio antes de calcular. Las dos medidas: manzanas por 1.000 px (`manzanas_prom` /
  `distancia_prom` × 1.000, del CSV de `main.py`) y la sensibilidad a la comida ((`sens_comida` + `sens_comida0`) /
  (`sens_ticks` + `sens_ticks0`) por fila de agente, la cuenta de la brújula antes de abrir la puerta). **Trampas:** la
  sensibilidad se mide solo en las etapas 0 y 1 (después de abrir la puerta, no); el script nuevo se prueba primero
  contra números publicados (manzanas 0,987 y 0,382 en la línea base; la brújula, +0,1105).

### Sesión 2 — 2026-11-22 — Paso 1, comer, en la referencia
- **Hecho:** comer, medido sobre los CSV publicados, sin corridas ([AnalisisQA](../../qa/AnalisisQA.md#comer)), con un
  script nuevo, `mediciones/analizar_comida.py`, probado contra lo publicado con `prueba` antes de leer nada nuevo (0
  errores en los controles). Antes de usarlos, los 20 CSV de la referencia, los 20 de la larga y su línea base y los 10
  de sin costo dieron su SHA-256 publicado. La lección LEC-022, con su regla en OPERACIONES. Commit: el de esta sesión,
  confirmado por Fer.
- **Estados:** el paso 1 pasa de ⏳ a 🔄: comer no está aprendido. Las manzanas por 1.000 px dan 0 de 5 (0,65 veces la
  línea base) y la sensibilidad a la comida, 3 de 5 (+0,014). Giraban hacia la comida hasta la 60 (+0,047) y lo pierden:
  desde ahí la selección casi no lo ve (de +0,02 a +0,05, contra +0,18), aunque los que giran comen más que los de su
  generación (+0,10). La larga sí gira (+0,046, 5 de 5 contra su línea base). Sin costo de golpear, +0,035, 3 de 5.
- **Desvíos del spec:** la decisión 6, cambiada por Fer. Las manzanas por 1.000 px no sirven con 70 manzanas sin
  reponer: con evolución se come del 80% al 90%, y la larga, que gira hacia la comida, da menos que su línea base en las
  5. Ahora piden la sensibilidad a la comida y, como medida independiente, el Spearman de adentro de cada generación
  (LEC-022). Con la decisión nueva, la referencia tampoco pasa (la sensibilidad, 3 de 5; el Spearman con las manzanas en
  las 121-150, +0,102 contra +0,041 de la línea base, sí). La línea base larga y la corrida sin costo se sumaron sin
  criterio, después de leer el criterio.
- **A medias o bloqueado:** la referencia sigue con costo 0,05: Fer decidió medir antes el costo en 0,01.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** una tanda de 10 corridas a la vez (~1 h 30 min), dos experimentos, cada uno con un solo cambio
  contra la referencia vigente (decisiones 3 y 4: la de costo 0,05), y con su criterio escrito en AnalisisQA antes de
  lanzar:
  - **(a) Paso 3, el costo en 0,01:** `medir_puerta.py . SALIDA S evolucion 150 acercarse deslizar fortalezas-moviles
    curriculo=30 sens-etapa0 sens-golpe cruce=0.2
    pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0.01`, semillas 1 a 5. Se
    compara con la referencia con `sens-golpe` (`results/medicion_golpe_20261121/`) y con sin costo
    (`results/medicion_costo_golpe_20261121/`), con las medidas de [el costo](../../qa/AnalisisQA.md#costo-golpe). La
    pregunta: si con un costo chico pasa la puerta (el criterio del ítem 5, 4 de 5) y golpean en la puerta y no en todos
    lados (el golpe condicionado, S, sube en 4 de 5, y P lejos queda lejos del 0,61 de sin costo). Con eso, Fer decide la
    referencia.
  - **(b) Paso 1, `FITNESS_FOOD` en 20:** el mismo comando con
    `pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,FITNESS_FOOD:20`, semillas 1 a 5. Comer, con
    la decisión 6 nueva, contra la línea base de la referencia (`results/medicion_sin_llave_20261120/`: sin evolución,
    los pesos del fitness no cambian lo que hacen); y contra la referencia, que la llave roja y la puerta no caigan.
  - **Primer paso:** controlar el SHA-256 de las tres carpetas de comparación (`python mediciones/analizar_comida.py
    results/medicion_sin_llave_20261120 results/medicion_corridas_largas_20261120 results/medicion_costo_golpe_20261121
    prueba` lo hace con la referencia y sin costo; `python mediciones/analizar_costo_golpe.py
    results/medicion_golpe_20261121 results/medicion_golpe_20261121`, su prueba, con los de `sens-golpe`: "errores: 0" en
    los dos) y escribir los dos criterios, con sus números, antes de lanzar.
  - **Trampas:** los pesos van en el nombre de los archivos (`...ANTI_CIRCLE0-HIT_ENERGY_COST0.01_evolucion.csv` y
    `...ANTI_CIRCLE0-FOOD20_evolucion.csv`): en una misma carpeta, los patrones de `analizar_comida.py` y
    `analizar_costo_golpe.py` agarran más de un archivo, así que van en dos carpetas o con patrones nuevos. Contar las 10
    líneas `MEDICION` (LEC-017), y en (a), que `ENERGIA_GOLPE` dé 0,01 por tick golpeando. Cuando Fer decida la
    referencia con lo de (a), la (b) se vuelve a mirar en la corrida final.
