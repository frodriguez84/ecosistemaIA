# Ecosistema Evolutivo IA — Prompt Maestro para Claude Code

> Lo **global** (SDD, modelo, git, registro obligatorio, seguridad, hábitos de sesión) está en
> `~/.claude/CLAUDE.md` y no se repite acá. Este archivo lleva lo que casi toda tarea de **este**
> proyecto necesita; el resto, en los archivos de la tabla del final. No duplicar: lo duplicado driftea.

## Idioma

**Responder siempre en español**, en todo momento — texto al usuario, mensajes de commit,
comentarios de PR, resúmenes de specs. Si una herramienta o el código está en inglés, está
bien citarlo tal cual, pero el texto propio va en español de principio a fin.

## Contexto del producto

Simulación 2D donde criaturas con una red neuronal propia evolucionan por algoritmo genético
para comer, sobrevivir y resolver un puzzle (llave roja → puerta de madera → llave dorada →
puerta de hierro → cofre). Nació en 2025 para el curso de Inteligencia Artificial de UCEMA.

**Es un proyecto lúdico:** sirve para aprender, jugar y ver hasta dónde llegan las distintas IAs
ayudando a evolucionarlo. No hay usuarios ni producción. Lo que importa es que la simulación sea
interesante y que lo que dice de sí misma (README, pantallas, reportes) sea verdad.

**Rumbo (decidido el 2026-11-14):** dos modos con un switch en `config.py`, para compararlos. El
modo **guiado** conserva la conducción escrita a mano que existe hoy, documentada como tal. El
modo **autónomo** es neuroevolución real: sin guía, con sensores del puzzle y acción de golpear.
Antes de tocar el aprendizaje se mide (orden de trabajo en
[docs/product/BACKLOG.md](docs/product/BACKLOG.md)).

## Stack y estructura

- **Python 3.11** con `.venv/` (Windows: `.venv/Scripts/python.exe`). `requirements.txt` lleva solo lo
  que el código importa: `pygame`, `numpy` (la red es propia, `SimpleNeuralNetwork`; sin PyTorch),
  `scikit-learn` (clustering) y `pytest`. Sin base de datos, web, deploy ni variables de entorno.
  Corre local con `python main.py`, con ventana o sin ella.
- **Dónde está cada cosa:** `main.py` (flags, semilla, CSV, loop), `config.py` (`SimulationConfig`),
  `experimento.py` (modos × evolución × semillas → `resumen.md`), `mediciones/` (miden una corrida
  sin cambiarla), `src/agents/advanced_agent.py` (sensores, decisión, acciones, fitness y la red),
  `src/evolution/genetic_algorithm.py`, `src/world/` (mundo, puzzle, obstáculos, la brújula por el camino), `src/analytics/`
  (registro, boletín, monitor, clustering), `src/ui/`, `tests/` y `results/` (en `.gitignore`). El
  árbol completo, en el README.

## Lógica de negocio crítica

El detalle de cada punto, con sus números, está en el README.
- **Dos modos** (`MODO`, `--modo`; por defecto `"guiado"`). Difieren **solo** en la conducción escrita
  a mano de `decide()` y `act()`: en el autónomo, `decide()` es la salida de la red recortada a [0, 1]
  y no consume azar. Guiado contra autónomo mide la guía; cada modo contra su línea base sin evolución
  mide el aprendizaje ([spec](docs/specs/done/MODO_GUIADO_Y_AUTONOMO.md)).
- **El puzzle es de cada agente:** etapa de 0 a 5 y hacha propias; una puerta es pared para cada uno
  hasta que él la abre; las llaves y el hacha se agarran por contacto y quedan en el mapa; puertas,
  cofre y árboles piden golpear (quinta salida, cuesta `HIT_ENERGY_COST`). Todo vuelve a 0 en cada
  generación (a 1 con el currículo), y abrir el cofre no termina la corrida.
- **La red tiene 11 entradas y 5 salidas.** Los sensores 9 y 11 son la brújula al próximo paso: en línea recta o, con
  `BRUJULA_CAMINO`, por el camino libre más corto.
- **Ocho switches en `config.py`, apagados por defecto y comunes a los dos modos.** Apagados, la
  corrida es la de antes:
  - la recompensa por acercarse (`RECOMPENSA_ACERCARSE`, `--acercarse`) y el currículo (`CURRICULO`,
    `--curriculo`: hasta la generación 15 nacen con la llave roja, sin su premio). Lo dado al nacer
    no es un logro: cuenta solo lo hecho (`etapa_inicial`) ([spec](docs/specs/done/PUZZLE_APRENDIBLE.md));
  - deslizar contra lo que choca (`DESLIZAR`, `--deslizar`), las fortalezas móviles
    (`FORTALEZAS_MOVILES`, `--fortalezas-moviles`), la brújula por el camino (`BRUJULA_CAMINO`,
    `--brujula-camino`), la recompensa por acercarse medida por el camino (`ACERCARSE_CAMINO`,
    `--acercarse-camino`, va con `--acercarse`), el fitness sin tope (`FITNESS_SIN_TOPE`,
    `--fitness-sin-tope`: la selección ordena por la suma de los términos; la mutación adaptativa y
    la guía siguen leyendo `fitness_con_tope`, de 0 a 100) y la comida que rebrota (`COMIDA_REBROTA`,
    `--comida-rebrota`: cada manzana comida vuelve a los `COMIDA_REBROTA_TICKS` ticks, al azar y lejos
    de los vivos; prendida consume azar) ([spec](docs/specs/active/PUZZLE_SOLOS.md)).
    No son columnas del CSV: van en el nombre del archivo, el panel, el boletín y el resumen del
    experimento.

## Convenciones de código

- **Español** en comentarios, docstrings, mensajes de consola y textos de pantalla.
- **Los parámetros van en `config.py`** (`SimulationConfig`), no como números sueltos. Quedan en el
  código, a propósito, los umbrales de la guía (30, 65, 40%), el radio de comer (20 px) y los
  cooldowns de golpear (el de entre golpes a una puerta es `DOOR_HIT_COOLDOWN`).
- **Sin formateador ni linter configurados.** No correr black, ruff ni similares con
  `--fix`/`--write` (regla global): reformatearían archivos enteros.
- **Tests con pytest,** en `tests/`: `python -m pytest -q` (el gate pre-commit los corre). La misma
  semilla (`--semilla`) da el mismo CSV byte a byte.
- **Una mejora del aprendizaje se demuestra contra la línea base sin evolución,** con la misma
  semilla y con varias semillas. Si la línea base mejora igual, no es aprendizaje (LEC-001). Las
  reglas para medir y comparar experimentos, en [OPERACIONES](docs/operations/OPERACIONES.md#medir).

## Notas importantes para Claude Code

- **Ante la duda, manda el código.** Un número de los docs se compara con lo que usa el código: un
  valor de `config.py` que nadie lee no verifica nada (LEC-010; cuáles son, en
  [mejoras futuras](docs/product/mejoras_futuras.md)). Del README, las secciones de clustering,
  monitor y UI no se revisaron número por número.
- **Después de editar, revisar `git diff` por líneas que eran solo espacios** y devolverlas (LEC-002).
  En un archivo CRLF, nunca `sed -i` (LEC-005). El resto de los finales de línea, en
  [OPERACIONES](docs/operations/OPERACIONES.md#editar-archivos).
- **Para correr sin ventana, flags, no `config.py`:** `python main.py --sin-ventana --generaciones N
  --semilla S` (`--help` los lista). Los tiempos, las tandas y `experimento.py`, en
  [OPERACIONES](docs/operations/OPERACIONES.md#correr).

## Specs

Cada spec vive en una sola carpeta según su estado (`docs/specs/planned/`, `active/` o `done/`). Qué
hacer al empezar y al cerrar, en [docs/specs/README.md](docs/specs/README.md) (el cierre lo orquesta
`/close-spec`); el formato y la bitácora de los specs de varias sesiones, en
[docs/AGENTES.md](docs/AGENTES.md). **El spec es el árbitro. QA bloqueado = no PR.**

## Documentación — dónde está cada cosa

| Necesitás… | Leé… |
|------------|------|
| Correr, medir, editar archivos, el editor | `docs/operations/OPERACIONES.md` |
| Cómo funciona la simulación, con sus números | `README.md` |
| Reglas globales (SDD, git, modelo) | `~/.claude/CLAUDE.md` |
| Ciclo de vida de specs y qué loops se automatizan | `docs/specs/README.md` |
| Formato de spec / autoría | `docs/AGENTES.md` |
| Índice de docs por rol | `docs/README.md` |
| QA + IDs trazables | `docs/qa/AnalisisQA.md` |
| Lecciones aprendidas | `docs/operations/LECCIONES_APRENDIDAS.md` |
| Pendientes | `docs/product/BACKLOG.md` (no hay `PENDIENTES.md`: el BACKLOG es el tablero) |
| Ideas sin decidir y lo que aparece fuera de alcance | `docs/product/mejoras_futuras.md` (acá, no en `docs/specs/` como dice la guía global) |
