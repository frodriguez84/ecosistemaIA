"""Mide dónde se traba la puerta de madera, sin cambiar la corrida (autónomo con --curriculo).

Envuelve, sin consumir azar:
- AdvancedAgent.act: después de moverse y con la llave (etapa 1), la distancia al centro de la
  puerta (al nacer y la mínima), los ticks a menos de 25 px, los ticks golpeando, y la distancia a
  un punto de control al que la brújula no apunta (la llave roja).
- AdvancedAgent.perceive y act: con la percepción que vio el agente y la llave, la sensibilidad de su
  red a la brújula (cuánto cambia el giro si el sensor 9 marca +90° contra −90°) y a la comida (el
  sensor 3, control positivo), sumada por tick (sens_brujula y sens_comida; promedio: / sens_ticks).
  Control: el forward en lote da las salidas de decide() y giro() el giro de act().
- AdvancedAgent._try_hit_door: cada golpe a menos de 25 px, si contó o qué lo frenó.
- main._fila_csv: fitness y sus términos (f_*; control: suman el fitness del agente), ranking,
  geometría de la puerta y un seguidor de brújula perfecto (como hoy y deslizando) sobre el mapa de
  cada generación.
- GeneticAlgorithm.evolve, SimpleNeuralNetwork.crossover y copy_from: qué aporta cada agente a la
  generación siguiente (élite y copia, 1; cruce, 0,5 por padre).

- GeneticAlgorithm.evolve: el origen de cada agente (elite, copia, cruce o inmigrante) y el id de sus
  padres en la generación anterior (padre1, padre2), para medir si heredan la sensibilidad.

- Con congelar=G, los cerebros de la generación G juegan las generaciones G + 1 a la última como
  episodios: el ruido del fitness (docs/qa/AnalisisQA.md#ruido-fitness).

Uso, desde la raíz del repo:
    python mediciones/medir_puerta.py . SALIDA SEMILLA {evolucion|sin_evolucion} GENERACIONES [acercarse] [deslizar] [fortalezas-moviles] [laboratorio] [curriculo30] [cruce=X] [pesos=NOMBRE:VALOR,...] [congelar=G]
acercarse, deslizar y fortalezas-moviles le pasan --acercarse, --deslizar y --fortalezas-moviles a
main.py (con las fortalezas móviles, la geometría y el seguidor miran la puerta de cada generación, y
geometria_*.csv dice dónde está, puerta_x y puerta_y). laboratorio es el laboratorio de la
brújula (docs/qa/AnalisisQA.md#laboratorio-brujula): antes de main.main() pone en 0 los pesos de la
comida, la exploración, el anti-círculo, la supervivencia, los cortes y el agua, así pagan solo
acercarse y el puzzle, y sube CURRICULO_HASTA_GENERACION a 30. curriculo30 sube solo el currículo, con
el fitness de siempre (el control del laboratorio). cruce=X fija CROSSOVER_RATE en X (el resto de los
hijos sale por copia de un padre; la mutación, igual). pesos= fija parámetros numéricos de config.py
antes de main.main(), por ejemplo pesos=FITNESS_ACERCARSE:40,FITNESS_ANTI_CIRCLE:9 (el rebalance del
fitness, docs/qa/AnalisisQA.md#rebalance-fitness); van después de los del laboratorio, y un nombre que
config.py no tiene corta la corrida. congelar=G (con evolucion; GENERACIONES mayor que G): desde la
generación G + 1, evolve() devuelve agentes nuevos con los cerebros de la G, sin selección, cruce,
mutación ni inmigrantes, en un orden barajado con un azar propio (el de la lista decide quién actúa
primero en cada tick); esas generaciones duran lo que la G y nacen con la etapa de la G (el currículo).
Cada una es un episodio: mapa, lugar de nacimiento y estado nuevos. agentes_*.csv suma pesos_hash (los
pesos: los clones repiten hash), orden (lugar en la lista) y cerebro (desde la G, el id de su agente en
la G); control: cada cerebro está una vez por episodio, con el hash de la G. Deja en SALIDA, por corrida:
corrida_*.csv (el CSV de main.py), agentes_*.csv (una fila por agente y generación) y
geometria_*.csv (una por generación). Al final imprime "MEDICION inconsistencias=0":
cada golpe se predice antes de llamar al original, y el ranking se compara con el de evolve.

Control: el corrida_*.csv tiene que ser byte a byte las primeras filas de la misma corrida sin el
script (results/experimento_*); si no, el envoltorio cambió la corrida y los números no valen. No
más de 10 corridas a la vez, y contar las líneas MEDICION de la tanda (LEC-017). El embudo lo arma
mediciones/analizar_puerta.py. Método y resultados: docs/qa/AnalisisQA.md#medicion-puerta-madera.
"""
import csv
import hashlib
import math
import os
import random
import sys

raiz, salida, semilla, tipo, generaciones = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
acercarse = "acercarse" in sys.argv[6:]
deslizar = "deslizar" in sys.argv[6:]
moviles = "fortalezas-moviles" in sys.argv[6:]
laboratorio = "laboratorio" in sys.argv[6:]
curriculo30 = "curriculo30" in sys.argv[6:]
cruce = next((float(a[len("cruce="):]) for a in sys.argv[6:] if a.startswith("cruce=")), None)
pesos = next((a[len("pesos="):] for a in sys.argv[6:] if a.startswith("pesos=")), "")
congelar = next((int(a[len("congelar="):]) for a in sys.argv[6:] if a.startswith("congelar=")), None)
if congelar is not None and (tipo != "evolucion" or int(generaciones) <= congelar):
    sys.exit("congelar=G va con evolucion y con GENERACIONES mayor que G")  # sin evolución no se llama a evolve
os.chdir(raiz)  # main.py carga los sprites con ruta relativa
sys.path.insert(0, raiz)

import numpy as np  # noqa: E402
import main  # noqa: E402
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork  # noqa: E402
from src.evolution.genetic_algorithm import GeneticAlgorithm  # noqa: E402

RADIO_GOLPE = 25  # el de world.process_door_hit


def centro_puerta(world):
    d = world.door
    return d.x + d.width // 2, d.y + d.height // 2


MED = {}          # agente -> medición de la generación en curso
FILAS = []        # una por agente y generación
FILA_DE = {}      # agente de la última generación cerrada -> su fila (para el aporte)
GEOM = []         # geometría por generación
CRUCES = {}       # id(cerebro hijo) -> (padre1, padre2) o (padre, None) en la copia
ORIGEN = {}       # agente de la generación nueva -> (origen, id padre1, id padre2)
INCONS = [0]      # predicción del golpe distinta de lo que pasó
SLOT = {}         # con congelar=G: cerebro -> id de su agente en la generación G
HASH_G = {}       # id del agente de la generación G -> hash de los pesos de su cerebro
CONGELADO = [False]
LLAMADAS_AG = [0]  # cruces, copias o mutaciones después de congelar: tiene que quedar en 0


def hash_pesos(cerebro):
    """Los primeros 16 hex del SHA-256 de los pesos y sesgos. Dos cerebros con el mismo son clones."""
    h = hashlib.sha256()
    for w in cerebro.weights + cerebro.biases:
        h.update(np.ascontiguousarray(w).tobytes())
    return h.hexdigest()[:16]

# Laboratorio de la brújula: los pesos que van a 0, así pagan solo acercarse y el puzzle
PESOS_LABORATORIO = dict(FITNESS_FOOD=0.0, FITNESS_EXPLORATION=0.0, FITNESS_ANTI_CIRCLE=0.0, FITNESS_SURVIVAL=0.0,
                         TREE_CUT_REWARD=0, HUT_CUT_REWARD=0, WATER_PENALTY_MAX=0)
SIN_PAGA = ("f_supervivencia", "f_comida", "f_exploracion", "f_anticirculo", "f_agua")


def nueva():
    return dict(d0_llave=None, dmin_llave=math.inf, d0=None, dmin=math.inf, ticks_etapa1=0, ticks_25=0, ticks_golpe=0, ticks_golpe_25=0,
                bloq_agente_inicio=0, bloq_agente_corte=0, bloq_puerta=0, golpes=0,
                t_llega25=None, t_golpe1=None, t_golpe2=None, ticks_25_post90=0, golpe_25_post90=0,
                sens_ticks=0, sens_brujula=0.0, sens_comida=0.0, ticks_avanza=0, ticks_gira=0, giro_abs=0.0)


def terminos_fitness(a):
    """Los términos de _calculate_fitness del agente, con los mismos pesos de config.py, sin el recorte
    a [0, 100] ni el tope por tiempo vivido. Lee el estado del agente, sin azar."""
    c = SimulationConfig
    anti = 0.0
    if a.distance_traveled > 100:
        anti = c.FITNESS_ANTI_CIRCLE * (c.ANTI_CIRCLE_W1_SR * a.metric_sr + c.ANTI_CIRCLE_W2_TURN * a.metric_turn_smooth
                                        + c.ANTI_CIRCLE_W3_NOVELTY * a.metric_novelty)
    t = dict(f_supervivencia=min(a.age * c.FITNESS_SURVIVAL, c.FITNESS_SURVIVAL_MAX),
             f_comida=c.FITNESS_FOOD * math.sqrt(max(0.0, float(a.food_eaten))),
             f_exploracion=min(c.FITNESS_EXPLORATION * math.log1p(max(0.0, a.distance_traveled) / 350.0),
                               c.FITNESS_EXPLORATION_MAX),
             f_anticirculo=anti, f_puzzle=a.puzzle_rewards + a.cut_rewards,
             f_acercarse=(c.FITNESS_ACERCARSE * (a.etapa - a.etapa_inicial + a._avance_en_el_paso())
                          if c.RECOMPENSA_ACERCARSE else 0.0),
             f_agua=-min(a.fitness_env_penalty, c.WATER_PENALTY_MAX))
    total = sum(t.values())
    tope = 50.0 + 50.0 * min(1.0, float(a.age) / float(c.BASE_TICKS))
    if abs(min(max(0, min(100, total)), tope) - a.fitness) > 1e-6:
        INCONS[0] += 1  # los términos no suman el fitness del agente
    if laboratorio and (any(t[k] != 0 for k in SIN_PAGA) or a.cut_rewards != 0):
        INCONS[0] += 1  # en el laboratorio paga algo más que acercarse y el puzzle
    return t


_perceive = AdvancedAgent.perceive


def perceive(self, world, other_agents):
    p = _perceive(self, world, other_agents)
    self._med_percepcion = p  # la que va a usar decide(); main.py llama a act() justo después
    return p


def giro(salidas):
    """El giro en radianes que hace act() en el autónomo con esas salidas de la red (una por fila):
    recortadas a [0, 1], si las dos pasan 0,3 se anula la más débil, × 0,12 y, arriba de 0,08, × 0,6."""
    izq, der = np.clip(salidas[:, 1], 0, 1), np.clip(salidas[:, 2], 0, 1)
    ambos, gana_izq = (izq > 0.3) & (der > 0.3), izq > der
    der = np.where(ambos & gana_izq, 0.0, der)
    izq = np.where(ambos & ~gana_izq, 0.0, izq)
    g = (der - izq) * 0.12
    return np.where(np.abs(g) > 0.08, g * 0.6, g)


def sensibilidad(cerebro, p):
    """Con la percepción p que vio el agente, cuánto cambia su giro si la brújula (sensor 9) marca el
    objetivo 90° a un lado o al otro (+0,5 contra −0,5), y lo mismo con la comida (sensor 3), el control
    positivo: un ángulo que se aprende. Positivo: gira hacia donde marca. Solo numpy, sin azar."""
    x = np.repeat(p[None, :], 5, axis=0)  # la quinta fila, sin tocar: control contra decide()
    x[0, 8], x[1, 8], x[2, 2], x[3, 2] = 0.5, -0.5, 0.5, -0.5
    a = x
    for i in range(len(cerebro.weights) - 1):
        a = np.tanh(np.dot(a, cerebro.weights[i]) + cerebro.biases[i])
    salidas = np.tanh(np.dot(a, cerebro.weights[-1]) + cerebro.biases[-1])
    g = giro(salidas)
    return g[0] - g[1], g[2] - g[3], salidas[4]


ORDEN_SALIDAS = ('move_forward', 'turn_left', 'turn_right', 'eat', 'hit')
_act = AdvancedAgent.act


def act(self, decisions, world, other_agents, tick):
    vivo = self.alive
    angulo, predicho = self.angle, None
    if vivo and self.etapa == 1 and world.door and getattr(self, "_med_percepcion", None) is not None:
        m = MED.setdefault(self, nueva())
        sb, sc, salida = sensibilidad(self.brain, self._med_percepcion)
        m['sens_ticks'] += 1
        m['sens_brujula'] += float(sb)
        m['sens_comida'] += float(sc)
        tomadas = np.array([decisions[k] for k in ORDEN_SALIDAS])
        if np.abs(np.clip(salida, 0, 1) - tomadas).max() > 1e-6:
            INCONS[0] += 1  # el forward en lote no es el de la red
        predicho = float(giro(tomadas[None, :])[0])
        m['ticks_avanza'] += int(decisions['move_forward'] > 0.5)
        m['ticks_gira'] += int(predicho != 0.0)
        m['giro_abs'] += abs(predicho)
    self._med_percepcion = None
    _act(self, decisions, world, other_agents, tick)
    if predicho is not None and abs((self.angle - angulo) - predicho) > 1e-9:
        INCONS[0] += 1  # giro() no es el de act()
    if not vivo or self.etapa != 1 or not world.door:
        return
    m = MED.setdefault(self, nueva())
    cx, cy = centro_puerta(world)
    d = math.hypot(self.x - cx, self.y - cy)
    m['ticks_etapa1'] += 1
    if m['d0'] is None:
        m['d0'] = d  # después del primer tick: casi donde nació
    if world.red_key:  # control: un punto al que la brújula no apunta (con etapa 1 no se agarra)
        dl = math.hypot(self.x - world.red_key.x, self.y - world.red_key.y)
        if m['d0_llave'] is None:
            m['d0_llave'] = dl
        if dl < m['dmin_llave']:
            m['dmin_llave'] = dl
    if d < m['dmin']:
        m['dmin'] = d
    if self.golpeando:
        m['ticks_golpe'] += 1
    if d < RADIO_GOLPE:
        m['ticks_25'] += 1
        if m['t_llega25'] is None:
            m['t_llega25'] = tick
        if self.golpeando:
            m['ticks_golpe_25'] += 1
        if m['t_golpe1'] is not None and tick - m['t_golpe1'] >= SimulationConfig.DOOR_HIT_COOLDOWN:
            m['ticks_25_post90'] += 1
            if self.golpeando:
                m['golpe_25_post90'] += 1


_hit = AdvancedAgent._try_hit_door


def try_hit_door(self, world, current_tick):
    prediccion = None
    m = MED.setdefault(self, nueva())
    if self.golpeando and self.etapa == 1 and world.door:
        cx, cy = centro_puerta(world)
        if math.hypot(self.x - cx, self.y - cy) < RADIO_GOLPE:
            if current_tick - self.last_tree_hit_tick < self.tree_hit_cooldown:
                if self.last_tree_hit_tick == 0:
                    m['bloq_agente_inicio'] += 1  # los primeros 120 ticks de la generación
                else:
                    m['bloq_agente_corte'] += 1   # después de cortar un árbol
                prediccion = False
            else:
                ultimo = self.golpes_puerta.get('door', (0, 0))[1]
                if current_tick - ultimo < SimulationConfig.DOOR_HIT_COOLDOWN:
                    m['bloq_puerta'] += 1
                    prediccion = False
                else:
                    prediccion = True
        else:
            prediccion = False
    elif self.etapa == 1:
        prediccion = False
    antes = self.golpes_puerta.get('door', (0, 0))[0]
    resultado = _hit(self, world, current_tick)
    despues = self.golpes_puerta.get('door', (0, 0))[0]
    if despues > antes:
        m['golpes'] += despues - antes
        if m['t_golpe1'] is None:
            m['t_golpe1'] = current_tick
        else:
            m['t_golpe2'] = current_tick
    if prediccion is not None and prediccion != (despues > antes):
        INCONS[0] += 1
    return resultado


def geometria(world):
    """La distancia más corta al centro de la puerta a la que puede estar el centro de un agente con
    etapa 1, y el área libre a menos de 25 px, con las mismas colisiones que act()."""
    cx, cy = centro_puerta(world)
    r = SimulationConfig.AGENT_RADIUS
    cerca = [o for o in world.obstacles if o.type in ("wall", "tree", "hut")
             and abs(o.x + o.width / 2 - cx) < 80 and abs(o.y + o.height / 2 - cy) < 80]
    perim = [o for o in world.perimeter_obstacles + world.pond_obstacles
             if abs(o.x + o.width / 2 - cx) < 80 and abs(o.y + o.height / 2 - cy) < 80]
    paso = 0.25
    dmin, libres = math.inf, 0
    n = int(RADIO_GOLPE / paso)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * paso, cy + j * paso
            d = math.hypot(x - cx, y - cy)
            if d >= RADIO_GOLPE:
                continue
            if world._is_inside_fortress(x, y):
                continue
            if any(o.collides_with(x, y, r) for o in cerca):
                continue
            if world.door.collides_with(x, y, r):
                continue
            if any(o.collides_with(x, y, r, r) for o in perim):
                continue
            libres += 1
            dmin = min(dmin, d)
    return dmin, libres * paso * paso


def seguidor(world):
    """Un seguidor de brújula perfecto, sobre el mapa de la generación: desde una grilla de puntos de
    arranque (cada 25 px en la zona donde nacen los agentes, los que act() deja ocupar), avanza 3 px
    por tick derecho al centro de la puerta, con las colisiones de act(); si el paso choca, queda
    trabado (no hay deslizamiento). Devuelve la distancia final de cada arranque. Solo numpy, sin azar."""
    cx, cy = centro_puerta(world)
    r = SimulationConfig.AGENT_RADIUS
    cajas = [(o.x + o.width // 2, o.y + o.height // 2, o.width // 2 + r, o.height // 2 + r)
             for o in world.obstacles if o.type in ("wall", "tree", "hut")
             and not (o.type in ("tree", "hut") and o.is_cut)]
    d = world.door
    cajas.append((d.x + d.width // 2, d.y + d.height // 2, d.width // 2 + r, d.height // 2 + r))
    ox, oy, hx, hy = (np.array(c, dtype=float) for c in zip(*cajas))
    aabb = world.perimeter_obstacles + world.pond_obstacles
    ax = np.array([o.x for o in aabb], dtype=float)
    ay = np.array([o.y for o in aabb], dtype=float)
    aw = np.array([o.width for o in aabb], dtype=float)
    ah = np.array([o.height for o in aabb], dtype=float)

    def choca(x, y):
        c1 = ((np.abs(x[:, None] - ox) <= hx) & (np.abs(y[:, None] - oy) <= hy)).any(axis=1)
        if len(ax):
            c2 = ((ax < x[:, None] + r) & (ax + aw > x[:, None]) & (ay < y[:, None] + r)
                  & (ay + ah > y[:, None])).any(axis=1)
            return c1 | c2
        return c1

    gx, gy = np.meshgrid(np.arange(50, 901, 25, dtype=float), np.arange(50, 751, 25, dtype=float))
    x0, y0 = gx.ravel(), gy.ravel()
    adentro = np.array([world._is_inside_fortress(a, b) for a, b in zip(x0, y0)])
    ok = ~adentro & ~choca(x0, y0)
    x0, y0 = x0[ok], y0[ok]
    finales = []
    for desliza in (False, True):
        x, y = x0.copy(), y0.copy()
        dmin = np.hypot(x - cx, y - cy)
        for _ in range(450):
            ang = np.arctan2(cy - y, cx - x)
            nx = np.clip(x + np.cos(ang) * SimulationConfig.AGENT_SPEED, r, world.screen_width - r)
            ny = np.clip(y + np.sin(ang) * SimulationConfig.AGENT_SPEED, r, world.screen_height - r)
            libre = ~choca(nx, ny)
            px, py = np.where(libre, nx, x), np.where(libre, ny, y)
            if desliza:  # si el paso choca, solo en x; si no, solo en y
                solo_x = ~libre & ~choca(nx, y)
                px = np.where(solo_x, nx, px)
                solo_y = ~libre & ~solo_x & ~choca(x, ny)
                py = np.where(solo_y, ny, py)
            x, y = px, py
            dmin = np.minimum(dmin, np.hypot(x - cx, y - cy))
        finales.append(dmin)
    return finales


_fila = main._fila_csv


def fila_csv(semilla_, evolucion, generacion, ticks, agents, world, learning_monitor):
    fila = _fila(semilla_, evolucion, generacion, ticks, agents, world, learning_monitor)
    orden = sorted(agents, key=lambda a: a.fitness, reverse=True)  # el mismo orden estable que evolve
    k = max(2, int(len(agents) * max(0.05, min(0.95, SimulationConfig.MEETING_POOL_FRACTION))))
    posicion = {a: i for i, a in enumerate(agents)}  # quién actúa primero en cada tick
    FILA_DE.clear()
    for lugar, a in enumerate(orden, start=1):
        m = MED.get(a, nueva())
        f = dict(semilla=semilla_, evolucion=int(evolucion), generacion=generacion, ticks_gen=ticks,
                 id=a.id, etapa_inicial=a.etapa_inicial, etapa=a.etapa, vivo=int(a.alive), edad=a.age,
                 fitness=round(float(a.fitness), 4), lugar=lugar, en_pool=int(lugar <= k),
                 elite=int(lugar <= SimulationConfig.ELITISM), golpes_puerta=a.golpes_puerta.get('door', (0, 0))[0],
                 abrio=int(a.etapa >= 2 and a.etapa_inicial < 2), aporte='')
        f['origen'], f['padre1'], f['padre2'] = ORIGEN.get(a, ('', '', ''))
        f.update({k2: round(v, 4) for k2, v in terminos_fitness(a).items()})
        f.update({k2: ('' if v is None else (round(v, 3) if isinstance(v, float) else v)) for k2, v in m.items()})
        if congelar is not None:
            f['pesos_hash'], f['orden'], f['cerebro'] = hash_pesos(a.brain), posicion[a], ''
            if generacion == congelar:
                SLOT[a.brain] = a.id
                HASH_G[a.id] = f['pesos_hash']
            if generacion >= congelar:
                f['cerebro'] = SLOT.get(a.brain, '')
                if HASH_G.get(f['cerebro']) != f['pesos_hash']:
                    INCONS[0] += 1  # no es un cerebro de la generación G, o le cambiaron los pesos
        FILAS.append(f)
        FILA_DE[a] = f
    if congelar is not None and generacion > congelar:
        cerebros = [FILA_DE[a]['cerebro'] for a in agents]
        if set(cerebros) != set(HASH_G) or len(set(cerebros)) != len(agents):
            INCONS[0] += 1  # cada cerebro de la G, una vez por episodio
    dmin, area = geometria(world)
    fin, fin_desliza = seguidor(world)
    cx, cy = centro_puerta(world)
    GEOM.append(dict(semilla=semilla_, evolucion=int(evolucion), generacion=generacion, puerta_x=cx, puerta_y=cy,
                     dmin_libre=round(dmin, 3), area_libre_25=round(area, 1), arranques=len(fin),
                     seguidor_25=int((fin < 25).sum()), seguidor_50=int((fin < 50).sum()),
                     seguidor_100=int((fin < 100).sum()), seguidor_mediana=round(float(np.median(fin)), 1),
                     desliza_25=int((fin_desliza < 25).sum()), desliza_50=int((fin_desliza < 50).sum()),
                     desliza_100=int((fin_desliza < 100).sum()),
                     desliza_mediana=round(float(np.median(fin_desliza)), 1)))
    MED.clear()
    return fila


_evolve = GeneticAlgorithm.evolve
_cross = SimpleNeuralNetwork.crossover
_copy = SimpleNeuralNetwork.copy_from


def crossover(self, other):
    LLAMADAS_AG[0] += int(CONGELADO[0])
    hijo = _cross(self, other)
    CRUCES[id(hijo)] = (self, other)
    return hijo


def copy_from(self, other):
    LLAMADAS_AG[0] += int(CONGELADO[0])
    resultado = _copy(self, other)
    CRUCES[id(self)] = (other, None)
    return resultado


_mutate = SimpleNeuralNetwork.mutate


def mutate(self, mutation_rate=0.1):
    LLAMADAS_AG[0] += int(CONGELADO[0])
    return _mutate(self, mutation_rate)


def congelados(agents, generation):
    """Con congelar=G, desde la generación G + 1: agentes nuevos (estado en cero) con los mismos
    cerebros, sin selección, cruce, mutación ni inmigrantes. El orden de la lista, quién actúa primero
    en cada tick, se baraja con un azar propio que no toca el de la corrida: si quedara fijo, la
    ventaja de actuar primero se repetiría entre episodios y se contaría como del cerebro."""
    CONGELADO[0] = True
    ORIGEN.clear()
    nuevos = []
    for a in agents:
        hijo = AdvancedAgent(0, 0, a.brain)
        ORIGEN[hijo] = ('congelado', a.id, '')
        nuevos.append(hijo)
    random.Random(semilla * 1000 + generation).shuffle(nuevos)
    return nuevos


def evolve(self, agents, generation=1):
    if congelar is not None and generation >= congelar:
        return congelados(agents, generation)
    CRUCES.clear()
    nuevos = _evolve(self, agents, generation)
    # agents ya quedó ordenado por evolve: control del lugar que se anotó en _fila_csv
    for lugar, a in enumerate(agents, start=1):
        if a in FILA_DE and FILA_DE[a]['lugar'] != lugar:
            INCONS[0] += 1000
    por_cerebro = {id(a.brain): a for a in agents}
    aporte = {a: 0.0 for a in agents}
    ORIGEN.clear()
    for hijo in nuevos:
        b = hijo.brain
        padre = por_cerebro.get(id(b))
        if padre is not None and padre.brain is b:
            aporte[padre] += 1.0  # élite: el mismo cerebro
            ORIGEN[hijo] = ('elite', padre.id, '')
            continue
        par = CRUCES.get(id(b))
        if par is None:
            ORIGEN[hijo] = ('inmigrante', '', '')  # cerebro nuevo
            continue
        p1, p2 = par
        a1, a2 = por_cerebro.get(id(p1)), (por_cerebro.get(id(p2)) if p2 is not None else None)
        if p2 is None:
            aporte[a1] += 1.0
            ORIGEN[hijo] = ('copia', a1.id, '')
        else:
            aporte[a1] += 0.5
            aporte[a2] += 0.5
            ORIGEN[hijo] = ('cruce', a1.id, a2.id)
    for a, v in aporte.items():
        if a in FILA_DE:
            FILA_DE[a]['aporte'] = v
    CRUCES.clear()
    return nuevos


AdvancedAgent.perceive = perceive
AdvancedAgent.act = act
AdvancedAgent._try_hit_door = try_hit_door
main._fila_csv = fila_csv
GeneticAlgorithm.evolve = evolve
SimpleNeuralNetwork.crossover = crossover
SimpleNeuralNetwork.copy_from = copy_from
if congelar is not None:
    _ticks = main._ticks_de_generacion
    _etapa = main._fijar_etapa_inicial

    def ticks_de_generacion(config, generacion):
        return _ticks(config, min(generacion, congelar))  # los episodios duran lo que la generación G

    def fijar_etapa_inicial(agents, generacion):
        _etapa(agents, min(generacion, congelar))  # y nacen con su etapa (el currículo)

    main._ticks_de_generacion = ticks_de_generacion
    main._fijar_etapa_inicial = fijar_etapa_inicial
    SimpleNeuralNetwork.mutate = mutate
    print(f"CONGELAR={congelar}: los cerebros de la generación {congelar} juegan de la {congelar + 1} a la {generaciones}")

os.makedirs(salida, exist_ok=True)
if laboratorio:
    for k, v in PESOS_LABORATORIO.items():
        setattr(SimulationConfig, k, v)
    print(f"LABORATORIO {PESOS_LABORATORIO}")
if laboratorio or curriculo30:
    SimulationConfig.CURRICULO_HASTA_GENERACION = 30  # la brújula apunta a la puerta las 30 generaciones
    print("CURRICULO_HASTA_GENERACION=30")
if cruce is not None:
    SimulationConfig.CROSSOVER_RATE = cruce
    print(f"CROSSOVER_RATE={cruce}")
PESOS = {}
for par in filter(None, pesos.split(",")):
    k, v = par.split(":")
    actual = getattr(SimulationConfig, k, None)
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        sys.exit(f"pesos: {k} no es un parámetro numérico de config.py")  # si no, nadie lo leería
    PESOS[k] = float(v)
    setattr(SimulationConfig, k, PESOS[k])
if PESOS:
    print(f"PESOS {PESOS}")
etiqueta_pesos = "pesos-" + "-".join(f"{k.replace('FITNESS_', '')}{v:g}" for k, v in PESOS.items()) + "_" if PESOS else ""
nombre = (f"s{semilla}_{'acercarse_' if acercarse else ''}{'deslizar_' if deslizar else ''}"
          f"{'moviles_' if moviles else ''}"
          f"{'laboratorio_' if laboratorio else ''}{'curriculo30_' if curriculo30 else ''}"
          f"{f'cruce{cruce}_' if cruce is not None else ''}{etiqueta_pesos}"
          f"{f'congelar{congelar}_' if congelar is not None else ''}{tipo}")
ruta_csv = os.path.join(salida, f"corrida_{nombre}.csv")
argv = ["--sin-ventana", "--generaciones", generaciones, "--semilla", str(semilla), "--modo", "autonomo",
        "--curriculo", "--csv", ruta_csv]
if acercarse:
    argv.append("--acercarse")
if deslizar:
    argv.append("--deslizar")
if moviles:
    argv.append("--fortalezas-moviles")
if tipo == "sin_evolucion":
    argv.append("--sin-evolucion")
main.main(argv)

for f in FILAS:
    f["acercarse"] = int(acercarse)
    f["deslizar"] = int(deslizar)
    f["fortalezas_moviles"] = int(moviles)
    f["laboratorio"] = int(laboratorio)
    f["curriculo_hasta"] = SimulationConfig.CURRICULO_HASTA_GENERACION
    f["cruce"] = SimulationConfig.CROSSOVER_RATE
    f["pesos"] = pesos
    if congelar is not None:
        f["congelar"] = congelar
for g in GEOM:
    g["deslizar"] = int(deslizar)
    g["fortalezas_moviles"] = int(moviles)
    g["laboratorio"] = int(laboratorio)
with open(os.path.join(salida, f"agentes_{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(FILAS[0].keys()))
    w.writeheader()
    w.writerows(FILAS)
with open(os.path.join(salida, f"geometria_{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(GEOM[0].keys()))
    w.writeheader()
    w.writerows(GEOM)
if congelar is not None:
    INCONS[0] += LLAMADAS_AG[0]
    episodios = len({f["generacion"] for f in FILAS if f["generacion"] > congelar})
    print(f"CONGELADO episodios={episodios} cerebros={len(HASH_G)} distintos={len(set(HASH_G.values()))}"
          f" llamadas_ag={LLAMADAS_AG[0]}")
print(f"MEDICION inconsistencias={INCONS[0]} filas={len(FILAS)}")
