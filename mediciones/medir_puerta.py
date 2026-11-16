"""Mide dónde se traba la puerta de madera, sin cambiar la corrida (autónomo con --curriculo).

Envuelve, sin consumir azar:
- AdvancedAgent.act: después de moverse y con la llave (etapa 1), la distancia al centro de la
  puerta (al nacer y la mínima), los ticks a menos de 25 px, los ticks golpeando, y la distancia a
  un punto de control al que la brújula no apunta (la llave roja).
- AdvancedAgent._try_hit_door: cada golpe a menos de 25 px, si contó o qué lo frenó.
- main._fila_csv: fitness, ranking, geometría de la puerta y un seguidor de brújula perfecto (como
  hoy y deslizando) sobre el mapa de cada generación.
- GeneticAlgorithm.evolve, SimpleNeuralNetwork.crossover y copy_from: qué aporta cada agente a la
  generación siguiente (élite y copia, 1; cruce, 0,5 por padre).

Uso, desde la raíz del repo:
    python mediciones/medir_puerta.py . SALIDA SEMILLA {evolucion|sin_evolucion} GENERACIONES [acercarse] [deslizar]
acercarse y deslizar le pasan --acercarse y --deslizar a main.py. Deja en SALIDA, por corrida:
corrida_*.csv (el CSV de main.py), agentes_*.csv (una fila por agente y generación) y
geometria_*.csv (una por generación). Al final imprime "MEDICION inconsistencias=0":
cada golpe se predice antes de llamar al original, y el ranking se compara con el de evolve.

Control: el corrida_*.csv tiene que ser byte a byte las primeras filas de la misma corrida sin el
script (results/experimento_*); si no, el envoltorio cambió la corrida y los números no valen. No
más de 10 corridas a la vez, y contar las líneas MEDICION de la tanda (LEC-017). El embudo lo arma
mediciones/analizar_puerta.py. Método y resultados: docs/qa/AnalisisQA.md#medicion-puerta-madera.
"""
import csv
import math
import os
import sys

raiz, salida, semilla, tipo, generaciones = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
acercarse = "acercarse" in sys.argv[6:]
deslizar = "deslizar" in sys.argv[6:]
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
INCONS = [0]      # predicción del golpe distinta de lo que pasó


def nueva():
    return dict(d0_llave=None, dmin_llave=math.inf, d0=None, dmin=math.inf, ticks_etapa1=0, ticks_25=0, ticks_golpe=0, ticks_golpe_25=0,
                bloq_agente_inicio=0, bloq_agente_corte=0, bloq_puerta=0, golpes=0,
                t_llega25=None, t_golpe1=None, t_golpe2=None, ticks_25_post90=0, golpe_25_post90=0)


_act = AdvancedAgent.act


def act(self, decisions, world, other_agents, tick):
    vivo = self.alive
    _act(self, decisions, world, other_agents, tick)
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
    FILA_DE.clear()
    for lugar, a in enumerate(orden, start=1):
        m = MED.get(a, nueva())
        f = dict(semilla=semilla_, evolucion=int(evolucion), generacion=generacion, ticks_gen=ticks,
                 id=a.id, etapa_inicial=a.etapa_inicial, etapa=a.etapa, vivo=int(a.alive), edad=a.age,
                 fitness=round(float(a.fitness), 4), lugar=lugar, en_pool=int(lugar <= k),
                 elite=int(lugar <= SimulationConfig.ELITISM), golpes_puerta=a.golpes_puerta.get('door', (0, 0))[0],
                 abrio=int(a.etapa >= 2 and a.etapa_inicial < 2), aporte='')
        f.update({k2: ('' if v is None else (round(v, 3) if isinstance(v, float) else v)) for k2, v in m.items()})
        FILAS.append(f)
        FILA_DE[a] = f
    dmin, area = geometria(world)
    fin, fin_desliza = seguidor(world)
    GEOM.append(dict(semilla=semilla_, evolucion=int(evolucion), generacion=generacion,
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
    hijo = _cross(self, other)
    CRUCES[id(hijo)] = (self, other)
    return hijo


def copy_from(self, other):
    resultado = _copy(self, other)
    CRUCES[id(self)] = (other, None)
    return resultado


def evolve(self, agents, generation=1):
    CRUCES.clear()
    nuevos = _evolve(self, agents, generation)
    # agents ya quedó ordenado por evolve: control del lugar que se anotó en _fila_csv
    for lugar, a in enumerate(agents, start=1):
        if a in FILA_DE and FILA_DE[a]['lugar'] != lugar:
            INCONS[0] += 1000
    por_cerebro = {id(a.brain): a for a in agents}
    aporte = {a: 0.0 for a in agents}
    for hijo in nuevos:
        b = hijo.brain
        padre = por_cerebro.get(id(b))
        if padre is not None and padre.brain is b:
            aporte[padre] += 1.0  # élite: el mismo cerebro
            continue
        par = CRUCES.get(id(b))
        if par is None:
            continue  # inmigrante: cerebro nuevo
        p1, p2 = par
        a1, a2 = por_cerebro.get(id(p1)), (por_cerebro.get(id(p2)) if p2 is not None else None)
        if p2 is None:
            aporte[a1] += 1.0
        else:
            aporte[a1] += 0.5
            aporte[a2] += 0.5
    for a, v in aporte.items():
        if a in FILA_DE:
            FILA_DE[a]['aporte'] = v
    CRUCES.clear()
    return nuevos


AdvancedAgent.act = act
AdvancedAgent._try_hit_door = try_hit_door
main._fila_csv = fila_csv
GeneticAlgorithm.evolve = evolve
SimpleNeuralNetwork.crossover = crossover
SimpleNeuralNetwork.copy_from = copy_from

os.makedirs(salida, exist_ok=True)
nombre = f"s{semilla}_{'acercarse_' if acercarse else ''}{'deslizar_' if deslizar else ''}{tipo}"
ruta_csv = os.path.join(salida, f"corrida_{nombre}.csv")
argv = ["--sin-ventana", "--generaciones", generaciones, "--semilla", str(semilla), "--modo", "autonomo",
        "--curriculo", "--csv", ruta_csv]
if acercarse:
    argv.append("--acercarse")
if deslizar:
    argv.append("--deslizar")
if tipo == "sin_evolucion":
    argv.append("--sin-evolucion")
main.main(argv)

for f in FILAS:
    f["acercarse"] = int(acercarse)
    f["deslizar"] = int(deslizar)
for g in GEOM:
    g["deslizar"] = int(deslizar)
with open(os.path.join(salida, f"agentes_{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(FILAS[0].keys()))
    w.writeheader()
    w.writerows(FILAS)
with open(os.path.join(salida, f"geometria_{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(GEOM[0].keys()))
    w.writeheader()
    w.writerows(GEOM)
print(f"MEDICION inconsistencias={INCONS[0]} filas={len(FILAS)}")
