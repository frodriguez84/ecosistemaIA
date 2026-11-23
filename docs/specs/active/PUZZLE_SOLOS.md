# Spec: Que aprendan el puzzle solos

**Estado:** Parcial — pasos 2 a 6 (llave roja, puerta de madera, llave dorada, puerta de hierro y cofre) ✅, 5 de 5 cada uno contra su línea base, con la brújula por el camino (`BRUJULA_CAMINO`) y la recompensa por acercarse medida por el camino (`ACERCARSE_CAMINO`), las dos apagadas por defecto: la puerta de hierro, 7,92 por generación, y el cofre, 4,80, con poco margen en dos semillas (1,2 y 1,4). Esa corrida (NA, Sesión 7) es la referencia desde el 2026-11-23 (Fer). Falta el paso 1 (comer), que se mide sobre la tanda de NA sin correr nada, y el 7 (todo junto). Decisiones cerradas con Fer el 2026-11-21 (la 6, cambiada el 2026-11-22; la referencia, sin costo de golpear desde el 2026-11-22, con la brújula por el camino desde el 2026-11-22 y con la recompensa por acercarse por el camino desde el 2026-11-23)
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
| 3 | **La referencia:** la condición de [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada), `medir_puerta.py . SALIDA S evolucion 150 acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`, semillas 1 a 5, con su línea base sin evolución. Sus CSV y SHA-256 están publicados. La referencia vigente se anota en la bitácora: cuando un cambio pasa su criterio y Fer decide quedárselo, la corrida con ese cambio pasa a ser la referencia nueva, con su comando. Desde el 2026-11-22, la vigente es sin costo de golpear (Sesión 3), con su línea base sin costo en `results/medicion_base_sin_costo_20261122/` (Sesión 4). **Desde el 2026-11-22 (Sesión 6), con la brújula por el camino:** `medir_puerta.py . SALIDA S evolucion 150 acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2 pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0 hierro brujula-camino` (NC), y su línea base, el mismo comando con `sin_evolucion` y sin `cruce=` (NCB0), los dos en `results/medicion_brujula_camino_20261122/` (sus SHA-256, en [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino)); `hierro`, `sens-etapa0` y `sens-golpe` solo miden. **Desde el 2026-11-23 (Sesión 7), con la recompensa por acercarse por el camino:** el comando de NC con `acercarse-camino` al final (NA), en `results/medicion_acercarse_camino_20261122/`, con NCB0 de línea base: sin evolución, el fitness no cambia lo que hacen (los SHA-256 de NA, en [la recompensa por acercarse, por el camino](../../qa/AnalisisQA.md#acercarse-camino)). |
| 4 | **Un cambio por vez** contra la referencia vigente (LEC-019). Si hace falta cambiar dos cosas, el diseño lleva el control que cambia una sola. |
| 5 | **El criterio común de "aprendido",** el mismo en cada paso: en las últimas 5 generaciones, en **4 de 5 semillas** el paso supera a la línea base sin evolución de la misma semilla; con un **tamaño mínimo**; y se lee junto con **un control o una medida independiente** (LEC-018). Para los pasos del puzzle, el tamaño mínimo por defecto es el del ítem 5: al menos 1 agente por generación, en promedio, que da el paso (`agentes_llave_roja`, `agentes_puerta_madera`, `agentes_llave_dorada`, `agentes_puerta_hierro`, `agentes_cofre` del CSV de `main.py`). Comer se mide aparte (decisión 6). La sesión del bloque escribe los números de su criterio en AnalisisQA **antes de correr**. |
| 6 | **Comer aprendido** no es comer más: el 16/11 comían más porque caminaban más, y la red no giraba hacia la comida ([brújula, deslizando](../../qa/AnalisisQA.md#brujula-c-deslizando)). Pide las dos cosas, que no dependen de cuánta comida queda: **la sensibilidad de la red a la comida** antes de abrir la puerta ((`sens_comida` + `sens_comida0`) / (`sens_ticks` + `sens_ticks0`)) ≥ 0,02 rad/tick (el umbral de la brújula) y por arriba de la línea base de la misma semilla, en 4 de 5 semillas; y, como medida independiente, que **dentro de cada generación los que giran más hacia la comida coman más** que los de su generación (el Spearman entre la sensibilidad y las manzanas de cada agente, mediana de las gens 121-150 de las 5 semillas, por arriba de la de la línea base). Las manzanas por 1.000 px se informan, sin criterio: con 70 manzanas sin reponer, la evolución se come del 80% al 90% y la medida queda sesgada en contra (LEC-022). Cambiada por Fer el 2026-11-22, con la [medición de comer](../../qa/AnalisisQA.md#comer); antes pedía más manzanas por 1.000 px en lugar de la medida de adentro de la generación. |
| 7 | **Cada bloque sigue el mismo ciclo:** medir el paso en la referencia → si pasa, se anota y se sigue con el próximo; si no, diagnosticar dónde se traba (una medición) → un cambio por vez → medirlo contra la referencia. Un cambio que toca la simulación entra con un switch apagado por defecto y con sus tests. Un cambio que se puede hacer con argumentos de `medir_puerta.py` (`pesos=`, `cruce=`, `curriculo=`) va sin código. |
| 8 | **Cada sesión deja lo de siempre:** su sección en AnalisisQA (criterio previo, resultados, lectura, qué sugiere y SHA-256), lo que aparezca fuera de alcance en mejoras futuras, su línea en el BACKLOG, y su entrada en la bitácora de este spec. El estado de cada paso, en la tabla de abajo. |
| 9 | **Lo que decide Fer:** qué cambio se prueba cuando hay más de uno, si un cambio que pasó queda en la referencia, y prender switches por defecto. La sesión sugiere; no elige sola. |

## La brújula por el camino

El cambio del paso 5 (Sesión 6, decidido por Fer en la Sesión 5): la brújula apunta por el camino libre más corto, no
en línea recta a través de las paredes. Va con el switch `BRUJULA_CAMINO`, apagado por defecto.

- **Qué cambia:** solo los sensores 9 y 11, en los dos modos. `_proximo_paso` sigue igual, y con él la recompensa por
  acercarse (`_medir_acercamiento`, en línea recta) y la guía del modo guiado.
- **La grilla:** celdas de 5 px; en el mapa de 960 × 800, 192 × 160. Una celda es libre si un agente de esa etapa puede
  tener el centro en el centro de la celda, con las cuentas de `_choca`: paredes, árboles y casitas sin talar, las
  puertas que no abrió, el perímetro y el estanque, con su caja corrida (DIAG-30). El agua no choca. Hay una grilla por
  etapa, de la 0 a la 4: la puerta de madera es pared hasta la 1 y la de hierro hasta la 3.
- **El tamaño de celda, 5 px:** tiene que ser de 7 o menos. Con el radio de 6, el hueco de una puerta de 20 px deja 8 px
  libres para el centro, y con una celda más grande puede no caer ningún centro adentro.
- **El objetivo de cada etapa:** las celdas libres desde donde se da el paso. Son las que están a menos de 27 px de una
  llave (el radio de la llave, 15, más los 12 de `check_key_pickup`), a menos de 25 del centro de una puerta
  (`process_door_hit`) y a menos de 18 del centro del cofre (10 + 8, `check_chest_open`). El centro de una puerta es
  pared. Cada celda del objetivo arranca con su distancia en línea recta al punto de `_proximo_paso`.
- **La distancia por el camino:** la distancia euclídea que rodea las paredes. Es la ecuación eikonal sobre la grilla,
  con el esquema de Godunov, resuelta con iteraciones de numpy hasta que no cambia; da lo mismo que *fast marching*. Una
  búsqueda en 8 direcciones no sirve: su distancia tiene forma de octógono y el rumbo saldría de a 45°.
- **El rumbo:** el contrario del gradiente de esa distancia, interpolado (bilineal) en la posición del agente entre los
  centros de las cuatro celdas que lo rodean. Para interpolar, una celda sin distancia (pared, o libre sin camino) vale
  lo de su vecina más alta más 10 px: cerca de una pared el rumbo se aleja de ella, y corrige el desvío del agente contra
  el centro de la celda. Si alguna de las cuatro sigue sin valor, el rumbo de la celda, con diferencias hacia el vecino
  más bajo de cada eje (*upwind*). En una celda del objetivo, la recta de hoy al punto de `_proximo_paso`. Sin camino (la
  distancia es infinita), también la recta de hoy. *Cambiado en la Sesión 6:* el rumbo de la celda solo dejaba al
  seguidor trabado en la entrada de los huecos angostos (llegaba en 13 de 20 mapas); interpolado, en 58 de 60, y los 2
  que faltan no tienen salida (DIAG-35).
- **El sensor 11:** la distancia por el camino de la celda, normalizada como hoy (`/ VISION_RANGE`, con tope 1). En el
  objetivo y sin camino, la de hoy. El esquema es de primer orden: en campo abierto, el rumbo se aparta de la recta hasta
  5,7° y la distancia hasta 10% cerca del objetivo, y desde 100 px, hasta 3,4° y 5,3%.
- **La celda del agente:** la que tiene su centro. Si esa celda no es libre (el agente no choca, pero el centro de la
  celda sí), se usa la libre más cercana entre sus 8 vecinas, primero las de los lados. Si no hay ninguna, la recta de
  hoy.
- **Cuándo se arma:** las 5 grillas, la primera vez que se pide una en la generación, que es en el primer tick. El mundo
  las borra en `reset_food`, donde se regeneran las fortalezas, el estanque y los obstáculos. Lo que cambia durante la
  generación (árboles y casitas talados) no se actualiza.
- **Sin azar:** armar las grillas y leerlas no consume `random` ni `np.random`.
- **Dónde vive:** un módulo nuevo, `src/world/camino.py`, con una función de rumbo que acepta un punto o arrays de puntos.
  El sensor 9 y el seguidor de `medir_puerta.py` llaman a la misma función.
- **Los nombres:** `BRUJULA_CAMINO = False` en `config.py`, `--brujula-camino` en `main.py` y `brujula-camino` en
  `medir_puerta.py`. Como `DESLIZAR`, va en el nombre del archivo, el panel, el boletín y el resumen del experimento, no
  en una columna del CSV.
- **El seguidor:** con `brujula-camino`, los dos seguidores de `medir_puerta.py` (el de la puerta de madera y el de la de
  hierro) siguen el rumbo nuevo. Sin el argumento, siguen la recta de hoy.

## La recompensa por acercarse, por el camino

El cambio siguiente del paso 5 (Sesión 7, decidido por Fer en la Sesión 6): la recompensa por acercarse mide la distancia
por el camino libre, la de la brújula por el camino, y no la recta. Va con el switch `ACERCARSE_CAMINO`, apagado por
defecto.

- **Qué cambia:** solo la distancia de `_medir_acercamiento`: d0, al empezar la etapa, y dmín. Con el switch, es la del
  sensor 11 de la brújula por el camino, antes de normalizar: la de la celda del agente y, en el objetivo, sin camino o
  sin celda libre cerca, la recta. No cambian la fórmula del avance (`_avance_en_el_paso`), los pasos dados,
  `FITNESS_ACERCARSE` ni cuándo se mide (una vez por tick, después de moverse). La brújula y la guía del modo guiado,
  tampoco.
- **Por qué:** con la recta, el agente que queda contra la pared de la fortaleza chica tiene el mejor avance que puede
  tener ahí. Desde el rincón donde queda el seguidor de la recta (Sesión 5), ir hasta la puerta de madera lo aleja en
  línea recta (de 784 a 793 px en el mapa de la semilla 5), y el avance no sube. Por el camino, lo acerca.
- **Con qué va:** sin `RECOMPENSA_ACERCARSE` no hace nada, y los tres comandos rechazan pedirlo sin `acercarse`. No pide
  `BRUJULA_CAMINO`: lee la misma grilla (`camino.campos`), y la arma aunque la brújula esté apagada. Así cada switch
  cambia una sola cosa (decisión 4), y acercarse por el camino con la brújula recta queda como control, si hace falta.
- **La lectura:** `camino.distancia(world, etapa, x, y)`, para un punto y con números de Python. `camino.rumbo`, con
  numpy, cuesta 34 µs por llamada con 5 corridas a la vez, y se llamaría otra vez por agente y por tick, ~15 min más por
  corrida de 150 generaciones; la distancia sola, 0,8 µs. Tiene que dar lo mismo que la distancia de `camino.rumbo`, y un
  test lo compara en una muestra de puntos de cada etapa.
- **La distancia va de a celda:** fuera del objetivo cambia de a 5 px, y dmín baja de a saltos. En el objetivo, la
  distancia por el camino arranca con la recta (la fuente de la eikonal): entrar al objetivo no salta.
- **Dónde puede saltar a la recta:** si el agente pasa de una celda con camino a una sin camino, o a una sin celda libre
  cerca (un árbol talado, que la grilla no actualiza, o un hueco que la grilla no ve), la distancia pasa a ser la recta,
  que puede ser más corta, y dmín baja sin acercarse. En la corrida corta se cuenta cuántas mediciones caen ahí; si no son
  casi ninguna, no se corrige.
- **Los nombres:** `ACERCARSE_CAMINO = False` en `config.py`, `--acercarse-camino` en `main.py` y `experimento.py`, y
  `acercarse-camino` en `medir_puerta.py`. Como los otros switches, no es una columna del CSV de `main.py`. En el nombre
  del archivo, `_acercarse` pasa a ser `_acercarse_camino`; en el panel y el boletín, la ayuda "acercarse" pasa a ser
  "acercarse por el camino"; en el resumen del experimento, "recompensa por acercarse, por el camino". En
  `medir_puerta.py`, `acercarse_` pasa a ser `acercarse_camino_` en el nombre, y `agentes_*.csv` y `geometria_*.csv`
  suman la columna `acercarse_camino`, solo con el argumento.
- **`medir_puerta.py`:** `terminos_fitness` recalcula `f_acercarse` desde el estado del agente (`_avance_en_el_paso`): no
  cambia, y su control (los términos suman el fitness) cubre el cambio.
- **Sin azar:** leer la distancia no consume `random` ni `np.random`.

## Estado por paso

| # | Paso | Estado | Dónde |
|---|------|--------|-------|
| 1 | Comer | 🔄 No aprendido en la referencia (2026-11-22): la sensibilidad a la comida, 3 de 5 (+0,014). Giraban hacia la comida hasta la 60 (+0,047) y lo pierden: desde ahí la selección casi no lo ve, aunque los que giran comen más que los de su generación. La larga sí gira (+0,046). **Con `FITNESS_FOOD` en 20 se aprende** (4 de 5, +0,045), **pero cuesta la llave roja** (28,9 por generación contra 44,5) **y la puerta** (0 de 5): no va a la referencia. Comer compite con la llave en el fitness. Se retoma después de la cadena, con la referencia nueva (Fer, 2026-11-22). **Lo próximo** (Fer, 2026-11-23): medirlo sobre la tanda de NA y NCB0, que ya tiene las columnas de la decisión 6 | [comer](../../qa/AnalisisQA.md#comer), [la comida al doble](../../qa/AnalisisQA.md#costo-chico-comida20) |
| 2 | Llave roja | ✅ En la referencia (2026-11-20): 44,5 de 60 por generación, 5 de 5 semillas, 38 veces la línea base y 9,8 veces por 1.000 px. Con la referencia sin costo sigue pasando (2026-11-22, sin criterio): 42,5 contra 1,24 de su línea base, 5 de 5. Con la brújula por el camino (2026-11-22, Sesión 6, sin cambiar la referencia): 52,2 contra 1,24 de su línea base, 5 de 5. Con la recompensa por acercarse por el camino (Sesión 7, la referencia desde el 2026-11-23): 54,8 contra 1,24, 5 de 5 | [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada), [la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo), [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino), [acercarse por el camino](../../qa/AnalisisQA.md#acercarse-camino) |
| 3 | Puerta de madera | ✅ En la referencia sin costo, contra su línea base sin costo (2026-11-22): 7,6 por generación contra 0,04, 5 de 5. **Lo aprendido es llegar con la llave y golpear siempre, no golpear en la puerta:** de los que tienen la llave llega el 29% (al azar, el 3%), y la red golpea casi el doble que al azar, pegada y lejos por igual (P lejos 0,61). Con ninguno de los costos medidos (0,05, 0,01 y 0) se condiciona el golpe. La medida independiente fijada no acompañó por un solo agente de la línea base (LEC-024): ✅ decidido por Fer. Con la brújula por el camino (Sesión 6): 33,0 por generación contra 0, 5 de 5, 4,3 veces N0; llega a la puerta el 74% de los que tienen la llave (N0, 34%). Con la recompensa por acercarse por el camino (Sesión 7, la referencia): 43,8 contra 0, 5 de 5; llega el 78% | [la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo), [golpear en la puerta](../../qa/AnalisisQA.md#sens-golpe), [el costo](../../qa/AnalisisQA.md#costo-golpe), [el costo en 0,01](../../qa/AnalisisQA.md#costo-chico-comida20), [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino), [acercarse por el camino](../../qa/AnalisisQA.md#acercarse-camino) |
| 4 | Llave dorada | ✅ En la referencia sin costo, contra su línea base sin costo (2026-11-22): 4,0 por generación contra 0, 5 de 5. Viene con la puerta: la agarra el 53% de los que la abren, en toda la corrida. Con la brújula por el camino (Sesión 6): 27,0 contra 0, 5 de 5, 6,7 veces N0. Con la recompensa por acercarse por el camino (Sesión 7, la referencia): 41,0 contra 0, 5 de 5 | [la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo), [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino), [acercarse por el camino](../../qa/AnalisisQA.md#acercarse-camino) |
| 5 | Puerta de hierro | ✅ **Pasa con la recompensa por acercarse por el camino** (2026-11-23, Sesión 7, la referencia): 5 de 5 (3,4 · 13,6 · 11,6 · 8,6 · 2,4 por generación, 7,92 en promedio; la línea base, 0). Llega el 43% de los que tienen la llave dorada (NC, 37%; más en las 5 semillas) y la abre el 21%. Sigue frenando llegar (el 71% de los que no la abren), y llega sin tiempo el 23%. **Antes:** no pasaba (2026-11-22): ninguna semilla llega a 1 por generación (0,16 en promedio; la línea base, 0). **La cadena se corta acá:** la abre el 1% de los que tienen la llave dorada (21 de 2.056 en las 31-150). Pide 3 golpes con 90 ticks entre golpe y golpe (la de madera, 2). **Se traba en llegar** (2026-11-22): el 99% de los que tienen la llave dorada nunca está a 25 px, y los que llegan la abren (21 de 29). La brújula y la recompensa por acercarse apuntan en línea recta, y desde la llave dorada, adentro de la fortaleza chica, esa recta cruza paredes en los 600 mapas: el seguidor perfecto no llega en 588, y los agentes quedan donde queda él. Fer decidió probar una brújula que siga el camino libre, con un switch. **Con la brújula por el camino** (2026-11-22, Sesión 6): **3 de 5, no pasa** (1,6 · 4,4 · 12,6 · 0,4 · 0 por generación; de 0,16 a 3,80 en promedio). Llega el 37% de los que tienen la llave dorada (N0, 1%) y la abre el 14%. Las semillas 4 y 5 van atrasadas en toda la cadena. Sigue trabándose en llegar (el 73% de los que no la abren), y el 19% llega sin tiempo; la recompensa por acercarse todavía mide la recta | [la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo), [dónde se traba](../../qa/AnalisisQA.md#medicion-puerta-hierro), [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino), [acercarse por el camino](../../qa/AnalisisQA.md#acercarse-camino) |
| 6 | Cofre | ✅ **Pasa con la recompensa por acercarse por el camino** (2026-11-23, Sesión 7, la referencia): 5 de 5 (1,2 · 9,2 · 6,0 · 6,2 · 1,4 por generación, 4,80 en promedio; la línea base, 0), con poco margen en las semillas 1 y 5; en las 116-120 hubiera sido 4 de 5. Lo abre el 68% de los que abren la puerta de hierro (gens 31-150). **Antes:** no pasaba (2026-11-22): 0,08 por generación, detrás de la puerta de hierro (7 agentes en las 31-150, en las semillas 1 y 4). Se vuelve a medir cuando pase el paso 5. Con la brújula por el camino (Sesión 6): 1 de 5 (la semilla 3, 9,4 por generación; 2,12 en promedio), 856 agentes en las 31-150; en las 116-120 hubieran sido 3 de 5 | [la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo), [la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino), [acercarse por el camino](../../qa/AnalisisQA.md#acercarse-camino) |
| 7 | Todo junto | ⏳ Una corrida final con los 6 pasos. Si comer pasa en la tanda de NA, esa tanda puede serlo (lo decide Fer) | — |

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

### Sesión 3 — 2026-11-22 — Pasos 3 y 1: el costo de golpear en 0,01 y la comida al doble
- **Hecho:** una tanda de 10 corridas a la vez (1 h 48 min), dos experimentos de un cambio cada uno contra la referencia
  con costo 0,05, con sus criterios escritos en AnalisisQA antes de lanzar ([AnalisisQA](../../qa/AnalisisQA.md#costo-chico-comida20)):
  (a) `HIT_ENERGY_COST:0.01` y (b) `FITNESS_FOOD:20`, con `pesos=`, sin código. Dos scripts nuevos,
  `mediciones/analizar_costo_chico.py` y `mediciones/analizar_comida20.py`, probados contra lo publicado antes de lanzar.
  La lección LEC-023, con su regla en OPERACIONES: un control de la gen 1 comparaba manzanas que salen de un CSV
  redondeado con tolerancia 1e-9, y la prueba con la misma corrida en los dos lados no podía verlo. Commit: el de esta
  sesión, confirmado por Fer.
- **Estados:**
  - (a) Con 0,01 pasa la puerta (4 de 5, 3,56 por generación), pero en 3 de 5 semillas golpean en todos lados (P lejos
    0,39), y el golpe condicionado no sube (2 de 5). Con ninguno de los tres costos medidos se condiciona el golpe.
  - (b) Con 20, comer queda aprendido (4 de 5, +0,045), pero la llave roja cae a 28,9 por generación (pide 40,0) y la
    puerta, a 0,08 (0 de 5). No va a la referencia.
  - **La referencia vigente cambia (Fer, 2026-11-22): sin costo de golpear.** Es `medir_puerta.py . SALIDA S evolucion 150
    acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2
    pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0`, semillas 1 a 5, ya corrida
    en `results/medicion_costo_golpe_20261121/` (sus SHA-256, en [el costo](../../qa/AnalisisQA.md#costo-golpe)). El valor
    por defecto de `config.py` no cambia.
  - El paso 3 pasa con ella (7,6 por generación, 5 de 5) contra la línea base publicada, que es con costo, y queda ✅
    cuando lo confirme su línea base sin costo. El paso 1 sigue 🔄.
- **Desvíos del spec:** el orden de trabajo. Comer, el paso 1, se retoma después de la cadena (Fer, 2026-11-22): compite
  con la llave en el fitness y se ajusta mirando todos los pasos juntos. El orden de la decisión 1, lo que aprenden, no
  cambia.
- **A medias o bloqueado:** la referencia nueva no tiene su línea base sin evolución. La publicada es con costo, y sin
  costo los agentes al azar viven más y pueden llegar a más.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** los pasos 3 a 6 con la referencia sin costo, contra su línea base sin costo.
  - **Primer paso, la línea base:** 5 corridas a la vez (~1 h 30 min; contar las 5 líneas `MEDICION`, LEC-017):
    `medir_puerta.py . results/medicion_base_sin_costo_AAAAMMDD S sin_evolucion 150 acercarse deslizar
    fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe
    pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0`, semillas 1 a 5, con la
    fecha de la sesión. Es la línea base publicada (`results/medicion_sin_llave_20261120/`) con `HIT_ENERGY_COST:0` y
    `sens-golpe`, que solo suma columnas. Sin evolución, los pesos del fitness no cambian lo que hacen, y sin selección no
    hay cruce. Control: `ENERGIA_GOLPE` da 0 golpeando.
  - **Mientras corre:** controlar los SHA-256 de los 10 CSV de la referencia (`python mediciones/analizar_comida.py
    results/medicion_sin_llave_20261120 results/medicion_corridas_largas_20261120 results/medicion_costo_golpe_20261121
    prueba` da "errores: 0") y escribir en AnalisisQA, antes de calcular, el criterio de los pasos 3 a 6. Es la
    decisión 5, en las gens 146-150, con `agentes_puerta_madera`, `agentes_llave_dorada`, `agentes_puerta_hierro` y
    `agentes_cofre` del `corrida_*.csv`, contra la línea base nueva de la misma semilla. La medida independiente: para la
    puerta, "En la puerta", la de [el costo](../../qa/AnalisisQA.md#costo-golpe); para los pasos 4 a 6, por 1.000 px,
    como la llave roja en [sin la llave dada](../../qa/AnalisisQA.md#sin-la-llave-dada).
  - **Al terminar:** un script nuevo para la cadena, probado primero contra lo publicado (la puerta de la referencia,
    9,8 · 10,2 · 3,2 · 6,0 · 8,8 por generación; la llave dorada, 2.056 en las 31-150). Cada paso que no pase sigue la
    decisión 7: una medición de dónde se traba antes de cambiar nada.
  - **Trampas:** `medir_puerta.py` mide la sensibilidad y el golpe solo en las etapas 0 y 1, así que para los pasos 4 a 6
    no hay medidas de la red. Un paso con menos de 1 agente por generación no pasa, sea cual sea la línea base. La puerta
    sin costo no es estable al final (13,5 y 7,6 por generación en las dos últimas ventanas): leerla por ventana. Los
    archivos de la línea base terminan en `..._HIT_ENERGY_COST0_sin_evolucion.csv` y van en su propia carpeta.

### Sesión 4 — 2026-11-22 — Pasos 3 a 6: la línea base sin costo
- **Hecho:** la línea base sin evolución de la referencia sin costo, 5 corridas a la vez (44 min), en
  `results/medicion_base_sin_costo_20261122/` (sus SHA-256, en AnalisisQA), con el criterio de los pasos 3 a 6 escrito
  antes de leerla ([la cadena sin costo](../../qa/AnalisisQA.md#cadena-sin-costo)). Un script nuevo,
  `mediciones/analizar_cadena.py`, probado contra lo publicado antes de leer la corrida: controla solo los números
  publicados, y dio 0 errores. La lección LEC-024, con su regla en OPERACIONES. Commit: el de esta sesión, confirmado por
  Fer.
- **Estados:**
  - **El paso 3 pasa de 🔄 a ✅** (decidido por Fer): 5 de 5, 7,6 por generación contra 0,04. La medida independiente
    fijada, la parte que la abre de los que llegan, no acompañó: 61% contra 100%, pero ese 100% es un solo agente de la
    línea base. Las comparaciones que sí se pueden hacer acompañan: llegan el 29% contra el 3%, y la red golpea casi el
    doble que al azar.
  - **El paso 4 pasa de ⏳ a ✅:** 5 de 5, 4,0 contra 0. La medida por 1.000 px acompaña sin agregar (la línea base, en 0).
  - **El paso 5 pasa de ⏳ a 🔄:** no pasa, ninguna semilla llega a 1 por generación. La cadena se corta ahí: la abre el 1%
    de los que tienen la llave dorada.
  - **El paso 6 sigue ⏳:** no pasa, está detrás.
  - La llave roja sigue pasando con la referencia nueva (5 de 5, sin criterio).
- **Desvíos del spec:** ninguno. La línea base de la referencia quedó anotada en la decisión 3.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** el paso 5, la puerta de hierro. Toca medir dónde se traba (decisión 7), sin cambiar la simulación.
  - **Primer paso, un argumento nuevo en `medir_puerta.py`** (por ejemplo `hierro`). Que mida en la etapa 3 (con la llave
    dorada, hacia la puerta de hierro) lo que hoy mide en la etapa 1 para la de madera, en columnas propias de
    `agentes_*.csv`, como `sens-etapa0` y `sens-golpe`. Hoy lo de la etapa 1 está en el envoltorio de `act` (desde
    `if not vivo or self.etapa != 1`) y en `try_hit_door`. Lo que tiene que medir:
    - la distancia al centro de `world.door_iron` al empezar la etapa, y la mínima;
    - los ticks en la etapa 3, los ticks a menos de 25 px y los ticks golpeando ahí;
    - cada golpe a menos de 25 px: si contó o qué lo frenó. Lo pueden frenar el cooldown del agente o el de la puerta,
      90 ticks entre golpes a la misma puerta, y la de hierro pide 3 golpes (`golpes_puerta['door_iron']`). La predicción
      del golpe va contra `MEDICION inconsistencias`, como en la etapa 1;
    - el tick en que el agente agarró la llave dorada, para saber cuánto le queda de la generación (`ticks_gen`).
  - **Control del argumento:**
    - sin el argumento, las tres corridas cortas de siempre dan los mismos SHA-256 que con el `medir_puerta.py` del commit
      de esta sesión (la lista, en [el costo](../../qa/AnalisisQA.md#costo-golpe), "Probado");
    - con el argumento, una corrida corta que llegue a la etapa 3: la semilla 5 con el comando de la referencia y 6
      generaciones (en la referencia, en la gen 5 un agente agarra la llave dorada). Su `corrida_*.csv` da el prefijo
      publicado de N0 (`sha_prefijo` de `analizar_largas.py`), y su `agentes_*.csv` sin las columnas nuevas, el de sin
      el argumento.
  - **Después, la tanda:** la referencia otra vez, con el argumento, 5 corridas a la vez (~1 h 20 min; contar las 5
    líneas `MEDICION`, LEC-017): `medir_puerta.py . results/medicion_hierro_AAAAMMDD S evolucion 150 acercarse deslizar
    fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2
    pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0 hierro`, con la fecha de la
    sesión. Control: los `corrida_*.csv` dan el SHA-256 publicado de N0 (medir no cambia la corrida), y los
    `agentes_*.csv` sin las columnas nuevas, el suyo.
  - **Antes de lanzar,** escribir en AnalisisQA qué se mira y qué diría cada resultado: no llegan (la distancia mínima),
    llegan sin tiempo (lo que les queda al llegar, contra los 181 ticks que piden 3 golpes con 90 entre golpe y golpe),
    llegan y no golpean, o golpean y no completan los 3 golpes (se van entre golpe y golpe). Comparado con la puerta de
    madera en la misma corrida y con la misma cuenta.
  - **Trampas:**
    - es un diagnóstico dentro de N0, sin contraste con la línea base: la línea base sin costo tiene 3 llaves doradas en
      las 31-150 (LEC-024);
    - en la ventana 146-150 hay ~100 agentes con la llave dorada; leer también las 31-150 (2.056);
    - un golpe frenado por el cooldown no es un golpe perdido: con 3 golpes, se cuentan los ticks entre golpes;
    - la puerta de hierro cambia de lugar con las fortalezas móviles: el centro se lee de `world.door_iron` en cada tick.

### Sesión 5 — 2026-11-22 — Paso 5: dónde se traba la puerta de hierro
- **Hecho:**
  - el argumento `hierro` de `medir_puerta.py`. Mide en la etapa 3 lo que se mide en la 1, en 17 columnas `h_` de
    `agentes_*.csv`, y suma a `geometria_*.csv` la puerta de hierro, con un seguidor de brújula perfecto desde la llave
    dorada (8 columnas);
  - lo probé antes de lanzar. Sin el argumento, los 12 CSV de las corridas cortas dan los SHA-256 de ca43455. Con él,
    dan lo mismo sin las columnas nuevas, y la semilla 5 da el prefijo de N0;
  - el criterio, escrito en AnalisisQA antes de lanzar
    ([dónde se traba la puerta de hierro](../../qa/AnalisisQA.md#medicion-puerta-hierro));
  - la tanda: la referencia otra vez con el argumento, 5 a la vez (1 h 22 min), en `results/medicion_hierro_20261122/`.
    Medir no cambió la corrida (los `corrida_*.csv` dan el SHA-256 de N0), con 0 inconsistencias;
  - un script nuevo, `mediciones/analizar_hierro.py`, probado con N0 antes de leer la tanda (0 errores);
  - la lección LEC-025, con su regla en OPERACIONES.

  Commit: el de esta sesión, confirmado por Fer.
- **Estados:**
  - **El paso 5 sigue 🔄, con el diagnóstico: se traba en llegar.** El 99% de los que tienen la llave dorada nunca está
    a 25 px, en las 5 semillas y en la ventana. Los que llegan la abren (21 de 29).
  - **La causa:** la brújula y la recompensa por acercarse apuntan en línea recta. Desde la llave dorada, adentro de la
    fortaleza chica, esa recta cruza las paredes en los 600 mapas. El seguidor perfecto no llega en 588, y los agentes
    quedan donde queda él (el 75%, a menos de 10 px).
  - **Afuera de la chica tampoco alcanza:** en 326 de 600 mapas, la fortaleza grande queda en el medio.
  - El paso 6 sigue ⏳.
- **Decidido por Fer:** probar una brújula que siga el camino libre, con un switch apagado por defecto (decisión 9). La
  recompensa por acercarse no cambia (decisión 4).
- **Desvíos del spec:**
  - la geometría de la puerta de hierro y el seguidor no estaban en la lista de la Sesión 4. Los sumé al diseño antes de
    lanzar, porque "no llegan" se lee con ellos;
  - la prueba corta mostró, antes de escribir el criterio, que el seguidor no llegaba en sus 6 mapas. Quedó anotado en
    AnalisisQA, y el criterio no depende de eso;
  - después de leer la tanda le sumé a `analizar_hierro.py` dos cuentas sin criterio: el avance de los que no llegan y la
    recta a la puerta, contra las paredes de las fortalezas.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** el paso 5, con la brújula que sigue el camino libre. Es un cambio en la simulación: va con un switch
  apagado por defecto y sus tests (decisión 7). Puede llevar dos sesiones: esta implementa y controla, y la tanda va en la
  siguiente si no entra.
  - **Primer paso, antes de tocar el código: las 4 corridas cortas con el código del commit de esta sesión.** Sus CSV, al
    scratchpad, para el control de "apagado no cambia nada". Con `P=pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0`,
    las 4 a la vez:
    - `medir_puerta.py . SALIDA/c1 1 evolucion 3 acercarse deslizar fortalezas-moviles curriculo=150 cruce=0.2 $P`;
    - `medir_puerta.py . SALIDA/c2 2 sin_evolucion 3 acercarse deslizar fortalezas-moviles curriculo=1`;
    - `medir_puerta.py . SALIDA/c3 3 evolucion 4 acercarse deslizar fortalezas-moviles curriculo=2 sens-etapa0 sens-golpe cruce=0.2 $P`;
    - `medir_puerta.py . SALIDA/c5 5 evolucion 6 acercarse deslizar fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2 $P,HIT_ENERGY_COST:0 hierro`.

    Control: las 4 líneas `MEDICION inconsistencias=0`.
  - **Después, el diseño en este spec, antes del código** (una sección "La brújula por el camino", debajo de las
    decisiones). Lo que tiene que fijar:
    - **qué cambia:** solo los sensores 9 y 11. `_proximo_paso` también lo usan la recompensa (`_medir_acercamiento`) y la
      guía del modo guiado, y esas no cambian. El 9 apunta por el camino más corto al objetivo de `_proximo_paso`, y el 11
      es la distancia por ese camino, normalizada como hoy. Sin camino, la recta de hoy;
    - **la grilla:** qué es pared tiene que ser lo de `_choca` para un agente de esa etapa. Son las paredes, los árboles y
      las casitas, las puertas que no abrió, el perímetro y el estanque (con su caja corrida, DIAG-30); el agua no choca;
    - **el tamaño de celda: 5 px.** Tiene que ser de 7 o menos: con el radio de 6, el hueco de una puerta de 20 px deja
      libres 8 px de centros, y una celda más grande puede no tener centro adentro;
    - **el objetivo de cada etapa:** en una puerta (etapas 1 y 3), las celdas libres a menos de 25 px de su centro, desde
      donde cuenta el golpe; el centro es pared. En una llave o el cofre, su celda;
    - **cuándo se arma:** al empezar cada generación, una vez por etapa (0 a 4), porque ahí se regeneran las
      fortalezas, el estanque y los obstáculos. Los árboles talados durante la generación no se actualizan, y eso se
      anota;
    - **sin azar:** armar la grilla y leerla no consume `random` ni `np.random`;
    - **los nombres:** el switch en `config.py` (`BRUJULA_CAMINO = False`), el flag de `main.py` (`--brujula-camino`) y el
      argumento de `medir_puerta.py` (`brujula-camino`). Como `DESLIZAR`, va en el nombre del archivo, el panel, el
      boletín y el resumen del experimento, no en una columna del CSV. La lista de dónde tocar: los 9 archivos que
      nombran `DESLIZAR`.
  - **Los tests,** en `tests/`, como `test_deslizar.py`:
    - con el switch apagado, las 4 corridas cortas dan los mismos SHA-256 que en el primer paso, y
      `python -m pytest -q` pasa;
    - prendido, un agente en la etapa 3 adentro de la fortaleza chica tiene la brújula hacia la puerta de madera, no
      contra la pared;
    - la grilla coincide con `_choca` en una muestra de puntos.
  - **El control de LEC-025:** con `hierro brujula-camino`, el seguidor de `medir_puerta.py` sigue la brújula nueva (la
    misma función que el sensor 9, no una copia). En la corrida corta de la semilla 5 (la c5 de arriba, con
    `brujula-camino`) tiene que llegar a la puerta de hierro desde la llave dorada en los 6 mapas; hoy no llega en
    ninguno. Sin `brujula-camino`, el seguidor es el de hoy.
  - **El criterio en AnalisisQA, antes de lanzar.** Los pasos 2 a 6 con la brújula nueva van contra su propia línea base
    sin evolución, también con la brújula nueva: si la línea base mejora igual, no es aprendizaje (LEC-001). Se usa el
    criterio de la decisión 5, y se compara con N0: los pasos 2 a 4, que pasan, no tienen que perder.
  - **La tanda: 10 a la vez,** con evolución y `sin_evolucion`, semillas 1 a 5 (en la Sesión 3, 10 a la vez tardaron 1 h
    48 min). El comando: `medir_puerta.py . results/medicion_brujula_camino_AAAAMMDD S evolucion 150 acercarse deslizar
    fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2
    pesos=FITNESS_ACERCARSE:40,FITNESS_EXPLORATION:0,FITNESS_ANTI_CIRCLE:0,HIT_ENERGY_COST:0 hierro brujula-camino`, con
    la fecha de la sesión. Contar las 10 líneas `MEDICION` (LEC-017).
  - **Trampas:**
    - la grilla con `_choca` celda por celda puede ser lenta: con celdas de 5 px son 38.400 celdas por etapa, 5 etapas
      por generación, y cada `_choca` recorre los obstáculos. Medir el tiempo en la corrida corta. Si pesa, rasterizar
      los rectángulos con numpy, con las mismas reglas, y el test que la compara con `_choca`;
    - el centro del agente puede caer en una celda marcada como pared, aunque el agente no choque: usar la celda libre
      más cercana;
    - la brújula nueva cambia el sensor en todos los pasos, también en la llave roja y la puerta de madera;
    - un camino que rodea es más largo: ya hoy, al 19% no le alcanza el tiempo desde la llave dorada;
    - el cofre todavía no se probó con su seguidor (LEC-025).

### Sesión 6 — 2026-11-22 — Paso 5: la brújula por el camino
- **Hecho:**
  - el switch `BRUJULA_CAMINO`, apagado por defecto (`--brujula-camino` en `main.py` y `experimento.py`; `brujula-camino`
    en `medir_puerta.py`). El código está en `src/world/camino.py`, con el diseño en la sección "La brújula por el camino".
    El switch va en el nombre del archivo, el panel, el boletín y el resumen, y lo dicen el README, `CLAUDE.md` y
    OPERACIONES. `_proximo_paso` usa ahora `camino.punto_del_paso`: es la misma cuenta;
  - 12 tests en `tests/test_brujula_camino.py`; la suite completa (202) pasa;
  - apagado no cambia nada: las 4 corridas cortas de la Sesión 5 dan en sus 12 CSV los mismos SHA-256 que con 90471f9,
    antes y después de tocar `medir_puerta.py`;
  - el control de LEC-025: con `brujula-camino`, los dos seguidores de `medir_puerta.py` siguen `camino.rumbo`. En la
    corrida corta de la semilla 5, el que desliza llega de la llave dorada a la puerta de hierro en los 6 mapas; con la
    recta, en ninguno;
  - el criterio, escrito en AnalisisQA antes de lanzar ([la brújula por el camino](../../qa/AnalisisQA.md#brujula-camino));
  - la tanda de 10 (NC y NCB0): 2 h 18 min, con 0 inconsistencias;
  - un script nuevo, `mediciones/analizar_brujula_camino.py`, probado con lo publicado antes de lanzar (0 errores);
  - DIAG-35 (un árbol o una casita tapa la puerta de madera) y tres ítems en mejoras futuras;
  - dos lecciones con su regla en OPERACIONES: LEC-026 (una ruta de más de 260 caracteres) y LEC-027 (`write_text` deja
    en CRLF un archivo LF).

  Commit: el de esta sesión, confirmado por Fer.
- **Estados:**
  - **los pasos 2 a 4 siguen ✅, y ganan.** Con la brújula, 52,2 · 33,0 · 27,0 por generación, contra 1,2 · 0 · 0 de su
    línea base (5 de 5 cada uno). Contra N0, la puerta de madera sube 4,3 veces y la llave dorada 6,7;
  - **el paso 5 sigue 🔄: 3 de 5** (1,6 · 4,4 · 12,6 · 0,4 · 0), de 0,16 a 3,80 por generación en promedio. Llega a la
    puerta el 37% de los que tienen la llave dorada (N0, el 1%), y la abre el 14%. Las semillas 4 y 5 van atrasadas en
    toda la cadena. Sigue trabándose en llegar (el 73% de los que no la abren), y crece "llegan sin tiempo" (el 19%);
  - **el paso 6 pasa de ⏳ a 🔄:** 1 de 5 (la semilla 3). En las 31-150 abren el cofre 856 agentes (N0, 7).
- **Decidido por Fer:**
  - la brújula por el camino pasa a la referencia (decisión 3, con su comando);
  - lo próximo es la recompensa por acercarse medida por el camino, con un switch.
- **Desvíos del spec:**
  - **el rumbo.** El diseño decía el rumbo de la celda (*upwind*), y con él el seguidor se trababa en la entrada de los
    huecos angostos (llegaba en 13 de 20 mapas). Pasó a ser interpolado entre las cuatro celdas, con las paredes más
    altas (58 de 60). El diseño quedó corregido en el spec;
  - **el objetivo de las llaves y el cofre:** las celdas libres desde donde se da el paso, como en las puertas, y no "su
    celda", que puede no ser libre;
  - **la distancia es eikonal, no un BFS** como sugería la Sesión 5: con un BFS en 8 direcciones, el rumbo sale de a 45°;
  - NCB0 se corrió sin `cruce=`, como NB0; el prompt de la Sesión 5 lo ponía en las 10;
  - en `medir_puerta.py`, el control del sensor 11 compara con `camino.rumbo` cuando va `brujula-camino`. Sin ese
    arreglo, la corrida corta daba 27.915 inconsistencias;
  - después de leer la tanda sumé una cuenta sin criterio: la puerta de hierro por semilla y por ventana, y la semilla 5.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** el paso 5, con la recompensa por acercarse medida por el camino. Es código: va con un switch apagado
  por defecto y sus tests (decisión 7). Puede llevar dos sesiones: una implementa y controla, y la tanda va en la
  siguiente si no entra.
  - **Primer paso, antes de tocar el código: las 5 corridas cortas con el código del commit de esta sesión,** las 5 a la
    vez, con la salida en `results/sesion7_antes/`: en el scratchpad, la ruta pasa los 260 caracteres (LEC-026).
    - c1, c2, c3 y c5 son las cuatro de la "Próxima sesión" de la Sesión 5, con `results/sesion7_antes/cN` de salida;
    - c6 es la c5 con la brújula: `medir_puerta.py . results/sesion7_antes/c6 5 evolucion 6 acercarse deslizar
      fortalezas-moviles curriculo=30 sens-etapa0 sens-golpe cruce=0.2 $P,HIT_ENERGY_COST:0 hierro brujula-camino`.

    Control: las 5 líneas `MEDICION inconsistencias=0`. El `corrida_*.csv` de c5 da `3db0df62…` y el de c6, `2e484f8f…`,
    los de esta sesión.
  - **Después, el diseño en este spec, antes del código** (una sección debajo de "La brújula por el camino"). Lo que
    tiene que fijar:
    - **qué cambia:** solo `_medir_acercamiento` de `advanced_agent.py` (d0 y dmín, de donde sale el avance del paso). Con
      el switch, la distancia es `camino.rumbo(world, etapa, x, y)[1]`, la del sensor 11 de la brújula por el camino; en
      el objetivo y sin camino, la recta. La fórmula del avance y `FITNESS_ACERCARSE` no cambian;
    - **con qué va:** no hace nada sin `RECOMPENSA_ACERCARSE`. Decidir si además pide `BRUJULA_CAMINO` o usa la grilla
      igual (es la misma);
    - **los nombres:** `ACERCARSE_CAMINO = False`, `--acercarse-camino` y `acercarse-camino` en `medir_puerta.py`. Como
      los otros switches, va en el nombre del archivo, el panel, el boletín y el resumen del experimento;
    - `terminos_fitness` de `medir_puerta.py` recalcula `f_acercarse` desde el estado del agente (`_avance_en_el_paso`):
      no cambia, y su control (los términos suman el fitness) cubre el cambio.
  - **Los tests,** como `tests/test_brujula_camino.py`:
    - apagado no cambia nada: las corridas cortas, y `python -m pytest -q` pasa;
    - prendido, salir de la fortaleza chica por la puerta de madera con la llave dorada sube el avance, y con la recta no
      sube;
    - no consume azar.
  - **El criterio en AnalisisQA, antes de lanzar,** contra la referencia nueva (NC):
    - la decisión 5 en los pasos 2 a 6, contra NCB0;
    - los pasos 2 a 4 no pierden;
    - la medida independiente del paso 5, la parte que llega a 25 px de la puerta de hierro, contra NC (37%).
  - **La tanda: 5 corridas, no 10.** Sin evolución, el fitness no cambia lo que hacen: la línea base sigue siendo NCB0, y
    no se corre otra vez. El comando es el de NC con `acercarse-camino`, en
    `results/medicion_acercarse_camino_AAAAMMDD/` con la fecha de la sesión (~2 h las 5 a la vez). Contar las 5
    líneas `MEDICION` (LEC-017).
    Control: la gen 1 de cada corrida nueva es la de NC salvo el fitness y sus términos.
  - **Trampas:**
    - `_medir_acercamiento` corre una vez por agente y por tick, después de moverse: es otra lectura de `camino.rumbo`
      (~78 µs con la máquina cargada), aparte de la del sensor. Medir el tiempo en la corrida corta;
    - desde la gen 2 la selección cambia: el único control byte a byte es el de la gen 1;
    - las semillas 4 y 5 van atrasadas en toda la cadena: mirar el embudo, no solo la puerta de hierro;
    - los scripts que editan archivos leen y escriben bytes (LEC-027). Qué archivos son CRLF está en OPERACIONES.

### Sesión 7 — 2026-11-22 — Paso 5: la recompensa por acercarse por el camino
- **Hecho:**
  - el switch `ACERCARSE_CAMINO`, apagado por defecto (`--acercarse-camino` en `main.py` y `experimento.py`,
    `acercarse-camino` en `medir_puerta.py`; los tres lo rechazan sin `acercarse`). La distancia sale de
    `camino.distancia`, nueva en `src/world/camino.py`; el diseño, en la sección "La recompensa por acercarse, por el
    camino". Va en el nombre del archivo, el panel, el boletín y el resumen, y lo dicen el README, `CLAUDE.md` y
    OPERACIONES;
  - 7 tests en `tests/test_acercarse_camino.py` y dos líneas en `tests/test_resumen.py`; la suite completa (209) pasa;
  - apagado no cambia nada: las 5 corridas cortas (c1, c2, c3, c5 y c6) dan en sus 15 CSV los mismos SHA-256 con el
    código de 7c2075b y con el switch; c5 da `3db0df62…` y c6, `2e484f8f…`;
  - los controles con el switch prendido:
    - c7, la c6 con `acercarse-camino`: en la gen 1 cambia solo el fitness;
    - los saltos a la recta fuera del objetivo: 7 de 353.922 mediciones, y ninguno baja dmín;
    - sin evolución cambia solo el fitness: por eso NCB0 no se corrió otra vez;
    - el tiempo: ~1% más;
  - el criterio, escrito en AnalisisQA antes de lanzar ([la recompensa por acercarse, por el
    camino](../../qa/AnalisisQA.md#acercarse-camino));
  - la tanda de 5 (NA), del 2026-11-22 a las 23:38 al 2026-11-23 a la 1:19, con 0 inconsistencias;
  - un script nuevo, `mediciones/analizar_acercarse_camino.py`, probado antes de lanzar con NC en el lugar de NA (da lo
    publicado, 0 errores).

  Commit: el de esta sesión, confirmado por Fer.
- **Estados:**
  - **los pasos 5 y 6 pasan a ✅, 5 de 5 cada uno:**
    - la puerta de hierro, 3,4 · 13,6 · 11,6 · 8,6 · 2,4 por generación; con NC pasaba en 3 de 5. La medida independiente
      acompaña: llega el 43% de los que tienen la llave dorada (NC, 37%), y por semilla es más alta en las 5;
    - el cofre, 1,2 · 9,2 · 6,0 · 6,2 · 1,4; con NC pasaba en 1 de 5. Tiene poco margen en las semillas 1 y 5;
  - **los pasos 2 a 4 siguen ✅, y ganan:** 54,8 · 43,8 · 41,0 por generación (NC, 52,2 · 33,0 · 27,0). Las semillas 4 y
    5, atrasadas con NC, se pusieron al día;
  - el paso 1 sigue 🔄 y el 7, ⏳.
- **Decidido por Fer (2026-11-23):**
  - NA pasa a la referencia (decisión 3, con su comando). `ACERCARSE_CAMINO` sigue apagado por defecto;
  - lo próximo es el paso 1, comer, medido sobre la tanda de NA y NCB0.
- **Desvíos del spec:**
  - **el test del avance.** La Sesión 6 pedía que salir de la fortaleza chica por la puerta de madera subiera el avance, y
    que con la recta no lo subiera. En el mapa de la semilla 5, saliendo, la recta también baja, y el test no distinguía.
    Quedó desde el rincón donde se traba el seguidor de la recta (122, 123): de ahí a la puerta de madera, con la recta el
    avance no sube, y por el camino sí;
  - **la lectura de la distancia:** `camino.distancia`, para un punto y con números de Python, en lugar de
    `camino.rumbo(...)[1]`, como decía el prompt: `rumbo` habría sumado ~15 min por corrida. Un test las compara;
  - **dos controles que el prompt no pedía:** sin evolución, con el switch y sin él, para no correr NCB0 otra vez; y los
    saltos a la recta;
  - el control de la gen 1 compara `agentes_*.csv` con las filas alineadas por `id`, porque el orden de las filas sale del
    fitness;
  - la aserción del resumen del experimento fue a `tests/test_resumen.py`, que arma corridas completas;
  - después de leer la tanda sumé dos cuentas sin criterio: la puerta de hierro y el cofre por semilla en las 116-120, y
    la llegada a la puerta de hierro por semilla.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A.
- **Próxima sesión:** el paso 1, comer, sobre la tanda de la referencia (NA) y de su línea base (NCB0). No toca la
  simulación ni corre nada: es un script en `mediciones/`.
  - **Primer paso: los datos.** `git status -sb`. Después, los SHA-256 de los 15 CSV de NA, en
    `results/medicion_acercarse_camino_20261122/` (publicados en [la recompensa por acercarse, por el
    camino](../../qa/AnalisisQA.md#acercarse-camino)), y los de los 15 de NCB0, los `*_sin_evolucion.csv` de
    `results/medicion_brujula_camino_20261122/` (publicados en [la brújula por el
    camino](../../qa/AnalisisQA.md#brujula-camino)), con `sha256sum`.

    Control: los 30 dan lo publicado, y los 10 logs (`log_s*_evolucion.txt` de NA y `log_s*_sin_evolucion.txt` de NCB0)
    terminan con `MEDICION inconsistencias=0`. Si falta alguno o no da, se regenera desde el commit de esta sesión con
    los comandos de la decisión 3: NA, ~1 h 40 las 5 a la vez; NCB0, el de NC con `sin_evolucion` y sin `cruce=`.
  - **El criterio en AnalisisQA, antes de leer** (decisiones 5 y 6; gens 146-150; por semilla, NA contra NCB0 de la misma
    semilla):
    - **la sensibilidad a la comida antes de abrir la puerta:** (`sens_comida` + `sens_comida0`) / (`sens_ticks` +
      `sens_ticks0`) por fila, promedio de las filas de la ventana. Pide ≥ 0,02 rad/tick y más que NCB0, en 4 de 5;
    - **la medida independiente:** dentro de cada generación con 10 agentes medidos o más, el Spearman entre la
      sensibilidad y las manzanas de cada agente (de `f_comida` = 10 × √manzanas). Pide que la mediana de las gens 121-150,
      con las 5 semillas, quede por arriba de la de NCB0;
    - sin criterio: las manzanas por 1.000 px (LEC-022), la comida que queda, el control positivo (la sensibilidad a la
      brújula en las mismas filas), las ventanas, y NC con la misma cuenta.
  - **El script,** con las cuentas de `analizar_comida20.py`, que es la decisión 6 como quedó. Los nombres de los
    archivos están en `NA_NOMBRE`, de `analizar_acercarse_camino.py`, y en `NC_NOMBRE` y `NCB0_NOMBRE`, de
    `analizar_brujula_camino.py`. Antes de leer nada nuevo, se prueba con lo publicado: N contra NB
    (`results/medicion_golpe_20261121` y `results/medicion_sin_llave_20261120`) da la sensibilidad +0,0138 con 3 de 5, y
    el Spearman de las 121-150, +0,102 contra +0,041.
  - **Qué diría cada resultado:**
    - **si pasa,** NA cumple los seis pasos en la misma tanda. Si es la corrida final del paso 7 lo decide Fer; después
      van el README (SOLOS-08) y el cierre del spec;
    - **si no pasa,** se mira por ventana dónde se pierde la sensibilidad, como en la Sesión 2, y se sugiere un cambio, uno
      por vez contra NA.
  - **Trampas:**
    - con NA, en las 146-150, el 80% de los que tienen la llave roja abre la puerta de madera (en la referencia de la
      Sesión 2, el 4%), y la sensibilidad se mide solo antes de abrirla: se mide en menos ticks por agente. Antes de leer,
      contar en NA y en NCB0 las filas de la ventana con ticks medidos y su mediana de ticks, y anotarlas;
    - `f_comida` va redondeada en el CSV: las manzanas que salen de ahí se comparan con la tolerancia del redondeo
      (LEC-023);
    - NCB0 no tiene `acercarse-camino`: sin evolución, el fitness no cambia lo que hacen (el control de esta sesión).
