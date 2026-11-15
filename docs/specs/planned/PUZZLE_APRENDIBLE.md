# Spec: Que el puzzle se pueda aprender

**Estado:** 🔵 Planned — decisiones cerradas con Fer (2026-11-15), sin código
**Prioridad:** Alta — es el ítem 5 del [BACKLOG](../../product/BACKLOG.md): en el modo autónomo, la
evolución aprende a comer y a caminar, pero el puzzle no pasa de la llave roja.
**Gate:** Ninguno
**Bloquea:** el ítem 6 del BACKLOG (mecánicas nuevas): cada mecánica suma algo para aprender, y
conviene saber antes si se puede aprender algo más que comer.
**Depende de:** [Modo guiado y modo autónomo](../done/MODO_GUIADO_Y_AUTONOMO.md) (puzzle por agente,
brújula, golpear, fitness común a los dos modos, `experimento.py` por modo) ·
[Pantallas para ver aprender](../done/PANTALLAS_VER_APRENDER.md) (avisos de hito, panel, boletín) ·
[experimento de cierre](../../qa/AnalisisQA.md#experimento-modos-cierre) (el "sin la ayuda")

---

## Problema

- **El autónomo no aprende el puzzle.** Contra su línea base aprende a comer y a caminar (5 de 5
  semillas), pero la llave roja sube solo porque caminan más: por cada 1.000 px de recorrido promedio,
  el autónomo con evolución tiene 2,9 agentes con llave roja y su línea base, 3,8. La puerta de madera
  se abrió una sola vez en las 150 generaciones del autónomo (semilla 5, generación 1, que es la misma
  con evolución y sin ella) ([experimento de cierre](../../qa/AnalisisQA.md#experimento-modos-cierre)).
- **La recompensa es escasa.** El fitness premia cada paso solo cuando se completa, y eso casi nunca
  pasa: no hay nada que distinga a un agente que fue hacia la puerta de uno que fue para el otro lado.

### Lo que se midió para decidir (2026-11-15)

Autónomo, semillas 1 a 3, 30 generaciones, con evolución y sin ella, desde `255c4ed`. Un script del
scratchpad envolvió `act()` y `_fila_csv` sin consumir azar; control: los 6 CSV salieron byte a byte
iguales a los del experimento de cierre. En las últimas 5 generaciones:

| | Con evolución | Sin evolución |
|---|---|---|
| Camino hecho hacia la llave roja: (distancia al empezar − la más corta que alcanzó) / distancia al empezar, promedio | 0,15 a 0,27 | 0,07 a 0,08 |
| Agentes que hacen más del 80% de ese camino | 2 a 8% | 1 a 2% |
| (Distancia al empezar − distancia al terminar) / distancia al empezar, promedio | −0,16 a +0,03 | −0,07 a −0,03 |
| Ticks en que golpean (semillas 1, 2 y 3) | 4%, 25% y 14% | 34 a 37% |
| Agentes con llave roja (5 generaciones × 3 semillas) | 40 | 11 |
| De ellos, los que llegaron a menos de 25 px de la puerta de madera | 2 (uno golpeó una vez; ninguno la abrió) | 0 |

- **Primer cuello, el camino.** Con la llave, lo más cerca que llegan a la puerta tiene una mediana de
  290 a 490 px según la semilla; de la llave a la puerta hay ~540 px de mediana.
- **Segundo cuello, golpear.** Los cerebros al azar golpean en ~30% de los ticks; la evolución deja de
  golpear, porque cuesta `HIT_ENERGY_COST`. La puerta pide `DOOR_HITS_TO_OPEN` golpes, con
  `DOOR_HIT_COOLDOWN` entre golpes, a menos de 25 px: el primer golpe no da nada.
- **Premiar dónde termina el agente castiga a los que caminan.** Una recompensa basada en potencial,
  sumada sobre la generación, se reduce a "distancia al empezar − distancia al terminar", y con
  evolución da negativa en dos de tres semillas: terminan más lejos de la llave que donde arrancaron.
- **El currículo del BACKLOG hoy no cambia la corrida.** "Primero llave roja y puerta de madera, el
  resto cuando eso se aprenda": nadie pasa la puerta de madera, así que los pasos 3 a 5 ya no pagan
  nunca. Para servir, el currículo tiene que hacer más fácil el paso 2.
- **La selección es débil.** Meeting pool: el 60% de arriba por ranking, elegido al azar adentro, más
  una élite. Un término nuevo del fitness actúa solo si cambia quién queda adentro de ese 60%. El
  fitness tiene un desvío de ~11 dentro de cada generación. Sobre las mismas generaciones, un peso de
  10 por el camino hecho hacia la llave mete en el pool entre 1,4 y 2,2 agentes por generación que
  antes quedaban afuera; uno de 20, entre 2,6 y 3,2.
- **Sin evolución, el fitness no elige a nadie:** cada generación son cerebros al azar, y el clustering
  usa `random_state=42`. Una recompensa nueva no cambia lo que hace la línea base, solo su columna de
  fitness.

## Objetivo

Dos ayudas para que el puzzle se pueda aprender en el modo autónomo, cada una con su switch, apagadas
por defecto:
1. **Recompensa por acercarse** al próximo paso del agente.
2. **Currículo:** las primeras 15 generaciones nacen con la llave roja.

Tres experimentos (A, la recompensa; B, el currículo; C, las dos), cada uno contra su línea base sin
evolución y contra el experimento de cierre, con un criterio fijado antes de medir. Responden: **¿alguna
hace que el autónomo aprenda a pasar la puerta de madera?**

## Qué NO es esta feature

- **No cambia el algoritmo genético** (selección, cruce, mutación, inmigración), aunque la selección sea
  débil (Problema). Queda en [mejoras futuras](../../product/mejoras_futuras.md).
- **No cambia los sensores, la red ni golpear.** La brújula es la de hoy.
- **No cambia el mapa, los premios del puzzle (`*_REWARD`) ni la energía.**
- **No ajusta el peso ni el calendario para que aprendan** (decisión 14). Un resultado negativo es un
  resultado y se registra.
- **No mide el guiado.** Las dos ayudas valen para los dos modos (decisión 3), pero los experimentos son
  del autónomo, que es la pregunta del ítem.
- **No premia acercarse al hacha ni a los árboles:** no tienen brújula.
- **No suma una medida de "usa la brújula".** El coseno entre el rumbo y la brújula salió negativo
  también en cerebros al azar (−0,09 a −0,19), probablemente porque un agente que camina en línea recta
  pasa cerca del objetivo y después se aleja: no sirve como está. Queda en mejoras futuras; para separar
  la brújula de caminar más alcanza la llave roja por 1.000 px (decisión 13).

## Decisiones cerradas

Fer eligió las siete recomendaciones de la sesión de autoría (bitácora, sesión 0).

### Qué se prueba

| # | Decisión |
|---|----------|
| 1 | **Los dos caminos, en tres experimentos separados y en este orden:** A, la recompensa por acercarse sola; B, el currículo solo; C, los dos juntos. La recompensa va primero: cambia un término del fitness y no el mundo, y ataca el primer cuello (el camino). C no pide código nuevo: son los dos switches prendidos. |
| 2 | **Dos switches independientes en `config.py`, apagados por defecto:** `RECOMPENSA_ACERCARSE = False` y `CURRICULO = False`. `--acercarse` y `--curriculo`, en `main.py` y en `experimento.py`, los prenden pisando la clase, como `--modo`. Apagados, la corrida es la de hoy: el CSV, sin las columnas nuevas, es byte a byte el de antes del spec. |
| 3 | **Las dos ayudas valen para los dos modos.** Los modos siguen difiriendo solo en la guía (decisión 2 del spec de los modos), así que guiado contra autónomo sigue midiendo la guía si los dos corren con los mismos switches. En el guiado, la recompensa sube el fitness, y la guía del puzzle (fitness > 65) corre más seguido. |

### La recompensa por acercarse

| # | Decisión |
|---|----------|
| 4 | **Avance en el paso actual, de 0 a 1.** **Camino hecho** = (d0 − dmín) / d0, nunca negativo: d0 es la distancia al objetivo del paso en el primer tick del agente en esa etapa, y dmín la más corta que alcanzó en esa etapa (si d0 es 0, el camino está hecho). El objetivo es el de la brújula (`_proximo_paso`: las llaves, y el centro de las puertas y del cofre), y la distancia, en línea recta y sin el tope de `VISION_RANGE` del sensor 11. <br>· **Llaves y cofre:** avance = camino hecho. <br>· **Puertas:** avance = (camino hecho + golpes que contaron / golpes necesarios) / 2. Los golpes que contaron son los de la decisión 8 del spec de los modos (con la llave, a menos de 25 px, respetando el cooldown); los necesarios, `DOOR_HITS_TO_OPEN` o `DOOR_IRON_HITS_TO_OPEN`. <br>· **Etapa 5:** no hay paso actual. |
| 5 | **El término del fitness:** `FITNESS_ACERCARSE` × (pasos que dio el agente + avance en el paso actual), con `FITNESS_ACERCARSE = 10` en `config.py` (lo mismo que la llave roja y que la primera manzana). Dar un paso vale su premio de hoy más 10, y el término nunca baja al darlo. Pasos que dio = etapa − etapa con la que nació (decisión 10; hasta el bloque B todos nacen en la 0, así que en el A son la etapa). Se suma en `_calculate_fitness` con los demás términos, antes de los topes de hoy (0 a 100 y el tope por tiempo vivido). Con `RECOMPENSA_ACERCARSE = False` el término no existe. |
| 6 | **Dar vueltas no suma.** Cuenta lo más cerca que llegó, no los ticks que pasó cerca: volver a acercarse no suma, y alejarse después (por ejemplo, para comer) no resta. Los golpes a la puerta topean en los necesarios menos uno: el último la abre y el agente pasa al paso siguiente. La suerte de nacer cerca del objetivo la achica la división por d0. |
| 7 | **Sin azar:** se actualiza una vez por tick, con la posición después de moverse, y no consume `random` ni `np.random`. En el autónomo, `decide()` + `act()` siguen sin consumir azar (decisión 5 del spec de los modos). |

### El currículo

| # | Decisión |
|---|----------|
| 8 | **Nacen con la llave roja.** Con `CURRICULO` prendido, los agentes de las generaciones 1 a `CURRICULO_HASTA_GENERACION` (15, en `config.py`) nacen en la etapa 1, élites incluidas, sin el premio de la llave: no la agarraron. Desde la 16 nacen en la etapa 0, como hoy. El mapa no cambia: la llave roja sigue ahí (en la etapa 1 nadie la puede agarrar), la puerta de madera es pared para cada uno hasta que la abre, y la brújula apunta a la puerta. Son 60 intentos por generación con la puerta, en lugar de ~3. |
| 9 | **Por calendario, no por desempeño.** La línea base sin evolución ve los mismos mundos, y las últimas 5 generaciones (26 a 30) son del puzzle de hoy en las dos, que es donde se mide (decisión 13). Pasar de nivel "cuando se aprende" dejaría a la línea base, que no lo destraba nunca, en otro mundo al final. |
| 10 | **Lo que se da al nacer no es un logro.** El agente guarda la etapa con la que nació. Los avisos y los hitos (decisión 5 del spec de las pantallas) cuentan solo los pasos que el agente dio, y la recompensa por acercarse también (decisión 5). Las columnas `agentes_*` siguen contando "llegaron al menos a esa etapa": en las generaciones del currículo, `agentes_llave_roja` vale 60, y la columna `etapa_inicial` lo explica (decisión 11). |

### CSV, pantallas y `experimento.py`

| # | Decisión |
|---|----------|
| 11 | **Columnas nuevas:** `acercarse` (0 o 1, de la corrida) después de `modo`, y `etapa_inicial` (0 o 1, de cada generación) después de `generacion`. **Ruta por defecto:** `results/corrida_s<semilla>_<modo>[_acercarse][_curriculo]_<evolucion\|sin_evolucion>.csv`. El renglón "Modo" del panel y el encabezado del boletín nombran los switches prendidos. |
| 12 | **`experimento.py`:** `--acercarse` y `--curriculo` pasan a cada corrida, y el resumen dice cuáles estaban prendidos. Por corrida suma **puerta de madera** (promedio de `agentes_puerta_madera` en las últimas 5) y **llave roja por 1.000 px** (promedio de `agentes_llave_roja` en las últimas 5 / promedio de `distancia_prom` en las últimas 5 × 1.000). La comparación con evolución contra sin evolución suma esas dos, como "K de N", y una línea con el criterio de la decisión 13. Si las últimas 5 de una corrida no son todas del puzzle de hoy (`etapa_inicial` > 0), el resumen la marca. |

### Cómo se mide

| # | Decisión |
|---|----------|
| 13 | **Criterio de éxito, fijado antes de medir.** Autónomo, semillas 1 a 5, 30 generaciones, con evolución y sin ella, con los mismos switches. **El autónomo aprende a pasar la puerta de madera** si, en 4 o más de las 5 semillas, la corrida con evolución tiene en las últimas 5 generaciones al menos 1 agente por generación con la puerta de madera abierta en promedio (`agentes_puerta_madera`) **y** más que su línea base sin evolución (un empate no cuenta como más). **Secundario,** que separa usar la brújula de caminar más: llave roja por 1.000 px mayor que la de la línea base en 4 o más de 5. **"Sin la ayuda"** es el experimento de cierre del spec de los modos (mismas semillas, mismas generaciones): ahí la puerta de madera vale 0 en las últimas 5 de las 5 semillas del autónomo. |
| 14 | **No se ajusta nada para que aprendan:** el peso (10) y el calendario (15) quedan, como la decisión 22 del spec de los modos. **Parada prevista,** después del experimento A: si con evolución las manzanas por agente de las últimas 5 quedan por debajo de 0,42 en 3 o más semillas (la mitad del promedio del autónomo con evolución en el experimento de cierre, 0,83), la recompensa le está ganando a la comida: se para y se decide con Fer antes del bloque B. |
| 15 | **Experimentos,** cada uno de 10 corridas (~8 min con las 10 a la vez; en la medición, 6 a la vez tardaron 356 s): <br>· **A:** `experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --acercarse` <br>· **B:** lo mismo con `--curriculo` <br>· **C:** lo mismo con `--acercarse --curriculo` <br>Cada uno se registra en `AnalisisQA.md` con su lectura contra el experimento de cierre y contra los anteriores de este spec. |
| 16 | **Tests,** cada uno corrido una vez contra el código de antes de su cambio: tiene que fallar, y es su control (decisión 31 del spec de los modos). <br>· **A**, `tests/test_acercarse.py`: un agente que empieza a 200 px de la llave y llega a 50 suma `FITNESS_ACERCARSE` × 0,75; quedarse muchos ticks a 50 px suma lo mismo que pasar una vez, y alejarse después no resta; en la puerta, con 1 de 2 golpes, el avance es (camino hecho + 0,5) / 2; agarrar la llave no baja el término y suma su premio más `FITNESS_ACERCARSE`; con otro `FITNESS_ACERCARSE` el término cambia; apagado, el fitness es el de hoy; prendido, en el autónomo, `decide()` + `act()` no consumen azar; la misma trayectoria da el mismo término en los dos modos. `test_humo.py`: una corrida con `--acercarse` dice `acercarse` = 1 en el CSV, la misma semilla da el mismo CSV, y sin evolución, con el switch y sin él, el CSV es igual salvo `fitness_*` y `acercarse`. `test_resumen.py`: puerta de madera, llave roja por 1.000 px, los K de N y la línea del criterio, contra un cálculo a mano. <br>· **B**, `tests/test_curriculo.py`: prendido, en las generaciones del currículo todos nacen en la etapa 1, élites incluidas, sin `RED_KEY_REWARD`, y después en la 0 (con otro `CURRICULO_HASTA_GENERACION`, el corte se mueve); apagado, siempre en la 0; el que nace en la etapa 1 tiene la brújula a la puerta y la puerta como pared hasta que la abre; un paso dado al nacer no es hito; con los dos switches, los pasos que dio no cuentan el dado al nacer; `etapa_inicial` en el CSV, 1 en el currículo y 0 después, y 0 apagado. <br>`python -m pytest -q` sigue en menos de 90 s. |

### Bloques

| # | Decisión |
|---|----------|
| 17 | **Dos bloques, una sesión cada uno, más el cierre.** Lleva bitácora. Cada bloque cierra con su experimento registrado y un commit con la confirmación de Fer. <br>**A — La recompensa:** decisiones 2 a 7, lo de la recompensa en 11 y 12, `tests/test_acercarse.py`, el experimento A y la parada de la decisión 14. <br>**B — El currículo:** decisiones 8 a 10, lo del currículo en 11 y 12, `tests/test_curriculo.py`, los experimentos B y C, la lectura de los tres con la respuesta al ítem 5, y los docs. <br>**Cierre:** `/close-spec`, en la sesión del B si alcanza el contexto; si no, una tercera. |

## Criterios de done (DoD)

**Bloque A — La recompensa**
- [ ] `RECOMPENSA_ACERCARSE` (`False`) y `FITNESS_ACERCARSE` (10) en `config.py`; `--acercarse` en `main.py`
  y en `experimento.py`, en `--help` en español.
- [ ] El término sigue las decisiones 4 a 7, y `tests/test_acercarse.py` está verde, con su control.
- [ ] Apagado, la corrida es la de hoy: autónomo y guiado, semillas 1 y 2, 10 generaciones; el CSV, sin
  las columnas nuevas, es byte a byte las 10 primeras generaciones del experimento de cierre.
- [ ] Prendido: la misma semilla da el mismo CSV, con ventana el mismo que sin ventana; sin evolución,
  el CSV es igual que sin el switch salvo `fitness_*` y `acercarse`.
- [ ] El CSV tiene `acercarse` después de `modo`, la ruta por defecto lleva `_acercarse`, y el panel y
  el boletín lo nombran cuando está prendido.
- [ ] El resumen de `experimento.py` trae puerta de madera, llave roja por 1.000 px, sus K de N y la línea
  del criterio; `tests/test_resumen.py` lo cubre.
- [ ] Experimento A corrido y registrado en `AnalisisQA.md`, con su lectura contra el experimento de
  cierre y el criterio de la decisión 13 aplicado. La parada de la decisión 14, evaluada en la bitácora.

**Bloque B — El currículo**
- [ ] `CURRICULO` (`False`) y `CURRICULO_HASTA_GENERACION` (15) en `config.py`; `--curriculo` en `main.py` y
  en `experimento.py`, en `--help` en español.
- [ ] El currículo sigue las decisiones 8 a 10, y `tests/test_curriculo.py` está verde, con su control.
- [ ] El CSV tiene `etapa_inicial` después de `generacion`, la ruta lleva `_curriculo`, y el panel y el
  boletín lo nombran cuando está prendido.
- [ ] Apagados los dos switches, la corrida sigue siendo la de hoy (el mismo control que en el A).
  Prendido: la misma semilla da el mismo CSV, con ventana el mismo que sin ventana.
- [ ] Mirado con ventana, con `--curriculo`: en la generación 1 todos arrancan con la llave roja y no
  sale el aviso de hito de la llave roja.
- [ ] Experimentos B y C corridos y registrados en `AnalisisQA.md`, y la lectura de los tres responde
  el ítem 5 con el criterio de la decisión 13.
- [ ] `python -m pytest -q` verde en menos de 90 s.
- [ ] Docs al día: README (el término del fitness con su peso en `config.py`, el currículo, los dos
  flags) y `CLAUDE.md` (§ Lógica de negocio crítica: los dos switches, comunes a los dos modos; § Notas:
  los flags). Cada número de esas secciones coincide con `config.py` o con el código (LEC-010).

## QA manual (IDs propuestos)

| ID | Caso | Criterio |
|----|------|----------|
| PUZZLE-01 | Switches en `config.py` | Los cuatro valores con sus números, apagados por defecto; `--acercarse` y `--curriculo` en `--help` |
| PUZZLE-02 | Avance en una llave | Camino hecho = (d0 − dmín) / d0; el test con 200 → 50 px da 0,75 × `FITNESS_ACERCARSE` |
| PUZZLE-03 | Avance en una puerta | (camino hecho + golpes / necesarios) / 2; los golpes son los que contaron |
| PUZZLE-04 | Sin trampa | Dar vueltas no suma; alejarse no resta; dar el paso no baja el término |
| PUZZLE-05 | Sin azar | Prendido, en el autónomo, `decide()` + `act()` no consumen azar |
| PUZZLE-06 | Común a los modos | La misma trayectoria da el mismo término en guiado y autónomo |
| PUZZLE-07 | Apagado = hoy | Autónomo y guiado, semillas 1 y 2, 10 generaciones: sin las columnas nuevas, byte a byte las del experimento de cierre |
| PUZZLE-08 | Línea base intacta | Sin evolución, con `--acercarse` y sin él: el CSV igual salvo `fitness_*` y `acercarse` |
| PUZZLE-09 | Reproducible | Con cada switch: misma semilla, mismo CSV; con ventana, igual que sin ventana |
| PUZZLE-10 | CSV y ruta | `acercarse` después de `modo`, `etapa_inicial` después de `generacion`; ruta con los sufijos |
| PUZZLE-11 | Resumen | Puerta de madera, llave roja por 1.000 px, K de N y la línea del criterio coinciden con un cálculo a mano |
| PUZZLE-12 | Experimento A | Registrado con su lectura y el criterio aplicado; parada de la decisión 14 evaluada |
| PUZZLE-13 | Nacen con la llave | Generaciones 1 a 15 en la etapa 1, élites incluidas, sin `RED_KEY_REWARD`; desde la 16, en la 0 |
| PUZZLE-14 | Lo dado no es logro | Ni hito ni aviso por la llave dada al nacer; la recompensa no la cuenta |
| PUZZLE-15 | Pantallas | Panel y boletín nombran los switches prendidos; con ventana, sin aviso de llave roja en la generación 1 con `--curriculo` |
| PUZZLE-16 | Experimentos B y C | Registrados, con la respuesta al ítem 5 según la decisión 13 |
| PUZZLE-17 | `python -m pytest -q` | Verde, en menos de 90 s; cada test nuevo falló contra el código de antes |
| PUZZLE-18 | Docs | README y `CLAUDE.md` como dice el DoD; los números coinciden con lo que lee el código |

## Implementación (pistas, no normativas)

### Comandos

```bash
# Tests
.venv/Scripts/python.exe -m pytest -q

# Experimentos (en segundo plano, ~8 min cada uno)
.venv/Scripts/python.exe experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --acercarse
.venv/Scripts/python.exe experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --curriculo
.venv/Scripts/python.exe experimento.py --semillas 1 2 3 4 5 --generaciones 30 --modos autonomo --acercarse --curriculo

# Apagado = hoy (PUZZLE-07): las 10 primeras filas del experimento de cierre, sin las columnas nuevas
.venv/Scripts/python.exe main.py --sin-ventana --generaciones 10 --semilla 1 --modo autonomo --csv "$S/a1.csv"
```

### Por bloque

**A.**
- `config.py`: `RECOMPENSA_ACERCARSE` y `FITNESS_ACERCARSE`, junto a los pesos `FITNESS_*`.
- `src/agents/advanced_agent.py`: en `__init__`, el estado del paso actual (su etapa, d0 y dmín); una
  función que lo actualiza una vez por tick; `_calculate_fitness` suma el término. Los golpes que
  contaron ya están en `golpes_puerta`.
- `main.py`: `--acercarse`, la columna y la ruta. `src/ui/stats.py` y `src/analytics/boletin.py`: el
  nombre del switch.
- `experimento.py`: los flags, el nombre de cada CSV y log, el resumen, las comparaciones y la línea del
  criterio.

**B.**
- `config.py`: `CURRICULO` y `CURRICULO_HASTA_GENERACION`.
- `main.py`: la etapa con la que nacen, en una sola función, después de `_ubicar_agentes` (al arrancar y
  al final de cada generación); `--curriculo`; la columna `etapa_inicial` y la ruta.
- `src/agents/advanced_agent.py`: la etapa con la que nació el agente.
- `src/analytics/registro.py`: `mirar_hitos` cuenta solo los pasos dados. Hoy recorre las etapas en
  orden desde la última alcanzada; con el currículo, el primer hito puede ser la puerta de madera antes
  que la llave roja.

### Trampas conocidas

- **CRLF:** `main.py`, `config.py`, `src/agents/advanced_agent.py`, `src/ui/stats.py` y `README.md` son
  CRLF; `experimento.py`, `src/analytics/boletin.py`, `src/analytics/registro.py`, `CLAUDE.md` y los tests,
  LF. Después de editar, `git diff` por líneas en blanco vaciadas (LEC-002), los finales de línea
  contados con Python (LEC-003) y nunca `sed -i` (LEC-005).
- **La etapa cambia después de `act()`:** las llaves y las puertas se prueban en los `_try_*` que
  `main.py` llama después de moverse. El estado del paso actual tiene que darse cuenta del cambio de
  etapa en el tick siguiente, con d0 medido ahí.
- **El fitness de una corrida con `--acercarse` no se compara con el de una sin él:** tiene un término
  más. Entre experimentos se comparan las manzanas y las columnas `agentes_*`; adentro de un
  experimento, las comparaciones de fitness siguen valiendo, porque la línea base también lo calcula.
- **`config.py` se pisa en la clase,** no en una instancia; los tests que cambian un valor lo devuelven
  (`monkeypatch.setattr`). Un test de "config manda" cambia el valor a uno distinto del de hoy.
- **Los tests de humo cuestan ~15 s por corrida.** Con las corridas nuevas, `pytest` puede pasar de los
  90 s: lo del currículo se prueba con `CURRICULO_HASTA_GENERACION` chico y pocas generaciones, o sin
  correr `main.py`. Si no entra, se decide con Fer.
- **Los tests nuevos tienen de dónde partir:** `tests/test_puzzle.py` arma un mundo real
  (`mundo`), un agente en una etapa (`_agente_en`), un tick (`_tick`) y golpes a la puerta
  (`_golpear_puerta`); `tests/test_reglas.py` pisa valores de `config.py` (`_pisar`).
- **Con ventana, la pantalla final espera ESC o ENTER** (`src/ui/pantalla_final.py`): para el control
  con ventana sin intervención, un script envuelve `pygame.event.get` y agrega un `KEYDOWN` de ESC desde
  que se entra a la pantalla final (LEC-004). El de las sesiones anteriores quedó en su scratchpad: se
  rearma.
- **La salida redirigida sale con buffer:** para leer un log mientras corre, `python -u` (así lanza
  `experimento.py` sus corridas).
- **Los checkers de `/qa-spec` no pueden correr `main.py`** (LEC-006): lo que pide corridas se vuelve a
  correr en la sesión, y cada `archivo:línea` citado se imprime antes de copiarlo.

## Edge cases

- **El objetivo del paso no está en el mapa** (antes de `RED_KEY_SPAWN_GEN`, o sin fortalezas): avance 0
  y no hay d0; se mide desde el primer tick en que aparece.
- **El agente muere:** su término queda con el dmín y los golpes que tenía.
- **Etapa 5:** solo cuentan los cinco pasos dados.
- **Nadie abre la puerta de madera:** `agentes_puerta_madera` vale 0, y en las comparaciones el empate no
  cuenta como más. Es el resultado de hoy.
- **`--curriculo` con menos de 21 generaciones:** las últimas 5 incluyen generaciones del currículo; el
  resumen marca la corrida (decisión 12).
- **Con ventana y un switch prendido:** el mismo CSV que sin ventana, con la misma semilla.

## Esfuerzo

Dos sesiones en secuencia, una por bloque (decisión 17), cada una con su experimento en segundo plano
(~8 min; el B corre dos). El cierre entra en la sesión del B si alcanza el contexto.

## Relación con otros specs

- **[Modo guiado y modo autónomo](../done/MODO_GUIADO_Y_AUTONOMO.md):** se mantiene su decisión 2 (los
  modos difieren solo en la guía). Cambian su decisión 28 (dos columnas nuevas y la ruta) y su decisión
  29 (el resumen suma la puerta de madera y la llave roja por 1.000 px). Sus decisiones 22 (no ajustar) y
  31 (tests con control) se aplican igual.
- **[Pantallas para ver aprender](../done/PANTALLAS_VER_APRENDER.md):** cambia su decisión 5 (los hitos
  cuentan solo los pasos dados); el panel y el boletín suman el nombre de los switches.

## Bitácora de ejecución

Formato: [`docs/AGENTES.md`](../../AGENTES.md) § "Specs de varias sesiones".

### Sesión 0 — 2026-11-15 — Autoría
- **Hecho:** medición en el scratchpad (§ Lo que se midió para decidir), con su control: los 6 CSV,
  byte a byte los del experimento de cierre. Spec escrito con Fer, que eligió las siete
  recomendaciones: los dos caminos en tres experimentos (recompensa, currículo, los dos), comunes a los
  dos modos, la recompensa por lo más cerca que llegó más los golpes a la puerta, el currículo de nacer
  con la llave roja por calendario (generaciones 1 a 15), el criterio de la decisión 13, dos switches
  apagados y el peso 10. Lo que quedó afuera, en
  [mejoras futuras](../../product/mejoras_futuras.md). Commit: `docs: spec Que el puzzle se pueda
  aprender (ítem 5 del BACKLOG)`.
- **Estados:** spec en `planned/`, sin código. DoD y QA sin empezar.
- **Desvíos del spec, y por qué:** ninguno. Lo decidió la sesión sin consultar, y Fer puede cambiarlo
  antes del bloque que lo usa: los nombres de `config.py` y de los flags; las columnas `acercarse` y
  `etapa_inicial`, su lugar y los sufijos de la ruta; el umbral de la parada de la decisión 14 (la
  mitad de las manzanas del cierre); el cofre como las llaves, solo camino, aunque pide un golpe; que el
  panel y el boletín nombren los switches, y que los hitos no cuenten lo dado al nacer.
- **A medias o bloqueado:** nada.
- **Para verificar en producción:** N/A, no hay producción.
- **Próxima sesión:** bloque A (decisión 17).
  - **Primer paso:** `git status -sb` (al escribir el spec, `config.py` tenía un cambio local de Fer, dos
    comentarios con comandos: no es de este spec y no se commitea sin preguntarle). `git mv` del spec a
    `active/`, con el manifiesto (`docs/specs/README.md`) y el link del ítem 5 del BACKLOG al día.
    Después, `tests/test_acercarse.py` (decisión 16, A) contra el código de hoy: cada test tiene que
    fallar; los que usan algo que no existe (el switch, el peso) fallan por `AttributeError`, y se anota
    cuáles.
  - **Después, en orden:** `config.py`; el estado del paso actual y el término en el agente (decisiones
    4 a 7); `--acercarse`, la columna y la ruta en `main.py`; el panel y el boletín; `experimento.py`
    (flags, resumen, K de N, línea del criterio) con `test_resumen.py`; `test_humo.py`; el control
    "apagado = hoy" (PUZZLE-07) y "línea base intacta" (PUZZLE-08); el determinismo con ventana y sin
    ella; el experimento A en segundo plano, registrado en `AnalisisQA.md` con su lectura contra el
    experimento de cierre; la parada de la decisión 14, evaluada en la entrada de la bitácora.
  - **Trampa:** la etapa cambia en los `_try_*`, después de `act()` (Trampas conocidas).
  - **Trampa:** `main.py`, `config.py`, `advanced_agent.py` y `stats.py` son CRLF (LEC-002, LEC-003,
    LEC-005).
  - **Trampa:** el experimento de cierre es la referencia de "apagado = hoy" y de "sin la ayuda". Está
    en `results/experimento_20261115-112804` (fuera de git); si no está, se regeneran sus 10 primeras
    generaciones desde `255c4ed` con `--semillas 1 2 --generaciones 10` (LEC-011).
