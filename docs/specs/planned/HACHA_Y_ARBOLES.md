# Spec: El hacha y los árboles

**Estado:** 🔵 Planned — decisiones cerradas con Fer el 2026-11-25
**Prioridad:** Alta — es el ítem que sigue en el [BACKLOG](../../product/BACKLOG.md), decidido con Fer el 2026-11-21
**Gate:** Ninguno (el spec anterior, [Que aprendan el puzzle solos](../done/PUZZLE_SOLOS.md), cerró el 2026-11-25)
**Bloquea:** nada
**Depende de:** [Que aprendan el puzzle solos](../done/PUZZLE_SOLOS.md) y su [referencia final](../done/PUZZLE_SOLOS.md#la-referencia-final) (NT, con su línea base NCB0), `mediciones/medir_puerta.py` y lo anotado en [mejoras futuras](../../product/mejoras_futuras.md#el-hacha-y-los-árboles-después-del-cofre--2026-11-21)

---

## Problema

La referencia final del spec anterior (NT) ya tala: de 30 a 96 árboles por semilla en las 150 generaciones (30 · 64 ·
96 · 91 · 80), y en las últimas 5, 0,6 · 0,8 · 1,0 · 0 · 0,6 por generación. Su línea base (NCB0), ninguno.

Ese cero no dice que la línea base no sepa talar. Los árboles se cortan solo cuando quedan 30 manzanas o menos sin comer
(`TREE_CUTTING_THRESHOLD`), y NCB0 come unas 0,4 manzanas por agente (24 de 70): el umbral nunca se abre. NT come una por
agente y lo abre, y cada corte suelta 20 manzanas que lo vuelven a cerrar. Hoy los árboles cortados miden sobre todo
cuánto come la población, y comer no se aprendió ([decisión 10](../done/PUZZLE_SOLOS.md#decisiones-cerradas) del spec
anterior).

Además, la red no ve ni el hacha ni los árboles: la brújula apunta a los pasos del puzzle, y el sensor 4 es la distancia
al obstáculo más cercano (paredes, árboles y casitas), sin dirección.

## Objetivo

Que el modo autónomo aprenda a talar, medido contra una línea base que también puede talar, sin que se rompa la cadena
del puzzle que ya se aprende (de la llave roja al cofre).

## Lo que pide talar hoy

Lo que dice el código el 2026-11-25, igual en los dos modos (lo llama `main.py` en cada tick, después de `act()`):

- **El hacha propia:** una por mapa, en un lugar nuevo en cada generación; se agarra por contacto, a menos de 30 px, y
  queda en el mapa para los demás (`world.check_axe_pickup`).
- **Golpear** (la quinta salida, > 0,5) a menos de 25 px de un árbol. La distancia se mide contra la **esquina de arriba
  a la izquierda** del árbol, no contra su centro (`world.process_tree_hit`): con el radio del agente (6 px), un árbol se
  golpea solo desde arriba o desde la izquierda. A las casitas se les mide el centro.
- **El umbral:** quedan 30 manzanas o menos sin comer (`world.update_tree_cutting_status`).
- **3 golpes,** con 120 ticks entre golpes al mismo árbol: más de 240 ticks contra el mismo árbol (la puerta de hierro
  pide 3 golpes con 90 entre uno y otro). El 3 es fijo en `world.py:35`: el `TREE_HITS_TO_CUT` de `config.py` (2) no lo
  lee nadie. Los golpes de varios agentes al mismo árbol se suman, y el corte es del que da el tercero.
- **Un corte frena a todos:** 30 ticks sin golpes a ningún árbol en todo el mapa. Y al que corta, 120 ticks sin poder
  golpear la puerta (y al que abre una puerta, sin poder golpear un árbol): comparten `last_tree_hit_tick`.
- **El pago:** 15 al fitness del que corta (`TREE_CUT_REWARD`, en `cut_rewards`) y 20 manzanas al azar en el mapa, para
  todos (`TREE_CUT_FOOD_REWARD`). En NT, con el fitness sin tope, el que abre el cofre suma 342 en total.
- **Lo que mide el CSV:** `arboles_cortados` por generación (el de `main.py`). No dice quién tiene el hacha, quién golpea
  un árbol ni quién corta.

## Qué NO es esta feature

- **Un paso más de la cadena:** talar va aparte (decisión 1). La brújula no apunta al hacha ni a los árboles.
- **Las casitas:** también piden el hacha, pero tienen su umbral (20), 4 golpes y su pago, y `arboles_cortados` no las
  cuenta. Se informan si aparecen.
- **Comer:** cerrado como no aprendido en el spec anterior. Se informa, sin criterio.
- **El modo guiado:** no se toca (su conducción ya lleva al árbol, con el hacha y poca comida).
- **Prender switches por defecto:** lo decide Fer, como siempre. `python main.py` sigue siendo la corrida de antes.
- **Las mecánicas nuevas** (ítem 6 del BACKLOG): no esperan a este spec ni entran en él.

## Decisiones cerradas

Con Fer, el 2026-11-25.

| # | Decisión |
|---|----------|
| 1 | **Talar va aparte de la cadena,** como hoy en el código: con el hacha propia y en cualquier etapa. Prueba algo nuevo: un segundo comportamiento que la brújula no guía. Si hace falta un sensor nuevo, cambia la red (hoy, 11 entradas). |
| 2 | **Sin el umbral de comida, sin código:** `TREE_CUTTING_THRESHOLD:9999` en el `pesos=` de la referencia y de su línea base. Los árboles se pueden cortar siempre: la línea base también puede talar, y talar deja de depender de cuánto se come. `config.py` no cambia: por defecto, el umbral sigue en 30. Las casitas mantienen el suyo. |
| 3 | **La referencia del spec,** NU: el comando de NT con el umbral fuera. Por semilla S, de 1 a 5: `python mediciones/medir_puerta.py . SALIDA S evolucion 150 acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0,TREE_CUTTING_THRESHOLD:9999 hierro brujula-camino acercarse-camino fitness-sin-tope`, más el argumento que mide el hacha (decisión 6). **Su línea base, NUB0:** el comando de NCB0 con el mismo `pesos=`, es decir, `sin_evolucion`, sin `cruce=` ni `acercarse-camino` ni `fitness-sin-tope` (sin evolución no cambian lo que hacen). NCB0 no sirve: con el umbral fuera, los agentes sin evolución también hacen otra cosa. Es un cambio contra NT (decisión 8). Cuando un cambio pasa su criterio y Fer decide quedárselo, la corrida con ese cambio pasa a ser la referencia, con su comando en la bitácora. |
| 4 | **La cadena no se rompe:** en la tanda de la referencia y en la tanda donde talar pase, los pasos 2 a 6 (llave roja, puerta de madera, llave dorada, puerta de hierro y cofre) cumplen el criterio común contra la línea base de esa tanda. Un cambio que hace pasar talar y rompe la cadena no va a la referencia (le pasó a comer con la comida al doble). Si la cadena no pasa en NU, la sesión lo informa y Fer decide. |
| 5 | **"Talar aprendido"** es el criterio común ([decisión 5](../done/PUZZLE_SOLOS.md#decisiones-cerradas) del spec anterior) sobre `arboles_cortados`: en las generaciones 146 a 150, en **4 de 5 semillas** más árboles por generación que la línea base de la misma semilla, con un **tamaño mínimo** de 1 árbol por generación en promedio. **La medida independiente** (LEC-018): de los agentes que agarran el hacha, la proporción que corta al menos un árbol, en las mismas generaciones, por arriba de la de la línea base en 4 de 5 semillas. Separa cortar de agarrar el hacha: si talan más solo porque más agentes pasan por el hacha, no acompaña. Si la línea base no tiene agentes con hacha en la ventana, la medida se informa sin comparar (LEC-024). La sesión escribe los números en AnalisisQA **antes de correr**. |
| 6 | **El hacha se informa, sin criterio:** en cada tanda, cuántos la agarran por generación y cuándo. Sirve para diagnosticar dónde se traba talar; no bloquea. Lo mide `medir_puerta.py` con un argumento nuevo que solo mide, como `hierro` y `sens-golpe`: por agente, cuándo agarra el hacha, los golpes que le contaron a un árbol, los árboles que cortó y los ticks con el hacha a distancia de golpe de un árbol. Con y sin el argumento, el CSV de `main.py` sale igual byte a byte. |
| 7 | **Las rarezas del árbol quedan como reglas del mundo** (el golpe medido a la esquina, los golpes compartidos con el corte para el tercero, la espera compartida con la puerta): se anotan, y cambian solo si el diagnóstico muestra que traban talar, de a una y con su switch. Lo único que se arregla de entrada: el código lee `TREE_HITS_TO_CUT`, puesto en 3, y el CSV sale igual byte a byte (LEC-010). |
| 8 | **Un cambio por vez** contra la referencia vigente (LEC-019), con el ciclo del spec anterior ([decisión 7](../done/PUZZLE_SOLOS.md#decisiones-cerradas)): medir en la referencia → si pasa, se anota; si no, diagnosticar dónde se traba (una medición) → un cambio → medirlo contra la referencia, con su criterio escrito antes. Un cambio que toca la simulación entra con un switch apagado por defecto y sus tests. Si cambia lo que hacen los agentes sin evolución (un sensor nuevo, por ejemplo: cambia la red), lleva su línea base propia, como NRB0. Lo que se puede hacer con argumentos de `medir_puerta.py` (`pesos=`, como el pago de talar), sin código. Candidatos, sin elegir: un sensor nuevo (al hacha, al árbol más cercano, si tiene el hacha), el pago de talar y las rarezas de la decisión 7. |
| 9 | **Lo que decide Fer:** qué cambio se prueba cuando hay más de uno, si un cambio que pasó queda en la referencia, prender switches por defecto y **cuándo se cierra el spec.** Si talar no pasa, cada vuelta termina con Fer decidiendo si sigue con otro cambio o cierra el paso como no aprendido, como con comer. Sin tope fijo de intentos. La sesión sugiere; no elige sola. |
| 10 | **Cada sesión deja lo de siempre:** su sección en AnalisisQA (criterio previo, resultados, lectura, qué sugiere y SHA-256 de los CSV), lo que aparezca fuera de alcance en mejoras futuras, su línea en el BACKLOG, el estado en la tabla de abajo y su entrada en la bitácora. |

## Estado por paso

| Qué | Estado | Dónde |
|-----|--------|-------|
| La referencia (NU y NUB0) | ⏳ Sin correr | |
| La cadena en NU (pasos 2 a 6, decisión 4) | ⏳ Sin medir | |
| El hacha (se informa, decisión 6) | ⏳ Sin medir | |
| Talar (decisión 5) | ⏳ Sin medir | |

## Criterios de done (DoD)

- [ ] La medición del hacha en `medir_puerta.py`, con un argumento que solo mide: el CSV de `main.py` sale igual byte a
      byte con y sin él.
- [ ] `TREE_HITS_TO_CUT` leído por el código, en 3, con el mismo CSV byte a byte.
- [ ] La referencia (NU) y su línea base (NUB0), corridas en las 5 semillas, con sus comandos en la bitácora y los SHA-256
      de sus CSV en AnalisisQA; la cadena (decisión 4) y el hacha (decisión 6), medidos en ellas.
- [ ] Talar cumple la decisión 5 en la referencia vigente, con la cadena cumpliendo la decisión 4 en la misma tanda; o
      Fer lo cierra como no aprendido (decisión 9), con sus mediciones en AnalisisQA.
- [ ] Cada cambio a la simulación que hizo falta, con su switch apagado por defecto, sus tests y la decisión de Fer sobre
      si va por defecto.
- [ ] El README dice lo que hace el modo autónomo con el hacha y los árboles, con los números de la última tanda, y es
      verdad (incluido `TREE_HITS_TO_CUT`).
- [ ] Las rarezas que no se tocaron, anotadas en mejoras futuras.

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| HACHA-01 | La medición solo mide | El CSV de `main.py`, igual byte a byte con y sin el argumento nuevo de `medir_puerta.py` |
| HACHA-02 | `TREE_HITS_TO_CUT` | El código lo lee, en 3, y el CSV sale igual byte a byte |
| HACHA-03 | La referencia | NU y NUB0 en las 5 semillas, con sus SHA-256 en AnalisisQA |
| HACHA-04 | La cadena | Decisión 4: los pasos 2 a 6 en la tanda de la referencia y en la de talar |
| HACHA-05 | El hacha | Decisión 6: se informa, sin criterio |
| HACHA-06 | Talar | Decisión 5 en la referencia vigente, o cerrado por Fer (decisión 9) |
| HACHA-07 | Lo que dice el README | Los números del README sobre el hacha y los árboles son los de la última tanda |

## Herramientas y tiempos

- **Medir:** `mediciones/medir_puerta.py` (sus argumentos, en su docstring) y un script de análisis por medición en
  `mediciones/`. Las reglas para medir y comparar, en [OPERACIONES](../../operations/OPERACIONES.md#medir).
- **Tiempos:** una tanda de 150 generaciones tarda ~1 h 30 min con 5 a 10 corridas a la vez; no más de 10 a la vez, y se
  cuentan las líneas `MEDICION` (LEC-017).
- **Los CSV** quedan en `results/` (fuera del repo): lo que otra sesión necesita comparar deja su SHA-256 en AnalisisQA.

## Prompt de cada sesión

```
Ejecución de El hacha y los árboles.
Seguí el protocolo de sesión de docs/specs/active/HACHA_Y_ARBOLES.md:
leé la última entrada de la Bitácora de ejecución y tomá su "Próxima sesión".
```

## Bitácora de ejecución

### Sesión 0 — 2026-11-25 — El diseño

- **Hecho:** el spec, con las decisiones 1 a 10 cerradas con Fer. Dato que cambió el diseño: NT ya tala, y NCB0 no,
  porque nunca abre el umbral de comida (decisión 2).
- **Estados:** todo ⏳.
- **Desvíos del spec:** ninguno.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A (no hay producción).
- **Próxima sesión:** el bloque 1, la referencia.
  1. Mover el spec a `active/` (`git mv`) y su fila en el manifiesto.
  2. Que el código lea `TREE_HITS_TO_CUT` en 3 (decisión 7) y el argumento que mide el hacha en `medir_puerta.py`
     (decisión 6). Se prueban con NT en una semilla y pocas generaciones: el CSV de `main.py` igual byte a byte antes y
     después del cambio, y con y sin el argumento. Tests de los dos.
  3. El criterio de la decisión 5 y el de la cadena (decisión 4), con sus números, en AnalisisQA, antes de correr.
  4. La tanda: NU y NUB0, 5 semillas cada una (10 corridas, ~1 h 30 min).
  5. Leer la cadena, el hacha y talar; los SHA-256 en AnalisisQA; Fer decide si NU es la referencia y qué sigue.

  **Trampas:** la línea base es NUB0, no NCB0 (sin el umbral, los agentes sin evolución también hacen otra cosa).
  `pesos=` pone el umbral en 9999.0 y el nombre del CSV lo lleva. Las casitas mantienen su umbral (20). Los golpes a
  un árbol se suman entre agentes: "cortó" es del que da el tercero, y la medición tiene que contar los dos.
