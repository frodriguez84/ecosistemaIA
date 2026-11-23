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
- Con evaluaciones=K, cada cerebro juega K episodios por generación y la selección usa el promedio de su
  fitness; con reloj=R, el control de igual costo (docs/qa/AnalisisQA.md#varias-evaluaciones).

Uso, desde la raíz del repo:
    python mediciones/medir_puerta.py . SALIDA SEMILLA {evolucion|sin_evolucion} GENERACIONES [acercarse] [deslizar] [fortalezas-moviles] [laboratorio] [curriculo30] [curriculo=N] [sens-etapa0] [sens-golpe] [hierro] [brujula-camino] [acercarse-camino] [fitness-sin-tope] [cruce=X] [pesos=NOMBRE:VALOR,...] [congelar=G] [evaluaciones=K] [reloj=R]
acercarse, deslizar y fortalezas-moviles le pasan --acercarse, --deslizar y --fortalezas-moviles a
main.py (con las fortalezas móviles, la geometría y el seguidor miran la puerta de cada generación, y
geometria_*.csv dice dónde está, puerta_x y puerta_y). laboratorio es el laboratorio de la
brújula (docs/qa/AnalisisQA.md#laboratorio-brujula): antes de main.main() pone en 0 los pesos de la
comida, la exploración, el anti-círculo, la supervivencia, los cortes y el agua, así pagan solo
acercarse y el puzzle, y sube CURRICULO_HASTA_GENERACION a 30. curriculo30 sube solo el currículo, con
el fitness de siempre (el control del laboratorio). curriculo=N fija CURRICULO_HASTA_GENERACION en N (va
sin curriculo30; con laboratorio, pisa el 30): con N = 30 es curriculo30, y una corrida larga con N igual
a sus generaciones nace con la llave hasta el final (docs/qa/AnalisisQA.md#corridas-largas).
sens-etapa0 mide la sensibilidad también en la etapa 0, cuando la brújula apunta a la llave roja (sin la llave
dada, docs/qa/AnalisisQA.md#sin-la-llave-dada), en tres columnas más: sens_ticks0, sens_brujula0 y
sens_comida0; las de la etapa 1 no cambian, y sin el argumento agentes_*.csv es el de antes.
sens-golpe mide, en los mismos ticks, la salida 'hit' de la red antes del tanh (z; golpea si tanh(z) > 0,5, o sea z >
atanh(0,5)) con el sensor 11, la distancia al próximo paso, en "pegado" (RADIO_GOLPE / visión) y en "lejos" (1,0), con el
resto de la percepción como la vio el agente (docs/qa/AnalisisQA.md#sens-golpe), en cuatro columnas más: zgolpe_pegado y
zgolpe_lejos (la suma de z) y golpea_pegado y golpea_lejos (los ticks en que golpearía); con sens-etapa0, también en la
etapa 0, con un 0 al final. Se divide por sens_ticks (o sens_ticks0). Un forward aparte: las demás columnas no cambian.
hierro mide en la etapa 3 (con la llave dorada, hacia la puerta de hierro) lo que se mide en la 1 para la de madera
(docs/qa/AnalisisQA.md#medicion-puerta-hierro), en columnas propias de agentes_*.csv que empiezan con h_: h_t_dorada (el
tick del primer act con la llave dorada; la agarró en el anterior), h_d0 (la distancia al centro de la puerta de hierro
después de ese act) y h_dmin (la mínima), h_ticks (los ticks en la etapa 3), h_ticks_25, h_t_llega25, h_ticks_golpe y
h_ticks_golpe_25 (como los de la etapa 1), cada golpe a menos de 25 px, si contó (h_golpes, con el tick de cada uno en
h_t_golpe1 a h_t_golpe3) o qué lo frenó (h_bloq_agente, el cooldown del agente, que ponen abrir la puerta de madera y
cortar; h_bloq_puerta, los DOOR_HIT_COOLDOWN ticks entre golpes a la misma puerta), y entre golpe y golpe:
h_ticks_25_listo (a menos de 25 px, con un golpe ya dado y el cooldown de la puerta cumplido), h_golpe_25_listo (de
esos, golpeando) y h_ticks_fuera_entre (a 25 px o más, con un golpe ya dado). La predicción de cada golpe va contra
MEDICION inconsistencias, como en la etapa 1, y h_golpes contra los golpes del agente. geometria_*.csv suma la puerta de
hierro: h_puerta_x y h_puerta_y, h_dmin_libre y h_area_libre_25 (la cuenta de la de madera) y un seguidor de brújula
perfecto que arranca en la llave dorada, con la puerta de madera abierta y la de hierro cerrada, H_PASOS pasos, como hoy y
deslizando (h_seguidor_dmin y h_seguidor_t25, h_desliza_dmin y h_desliza_t25: la distancia mínima y el primer paso a menos
de 25 px; vacío si no llega). Sin el argumento, los tres CSV son los de antes.
brujula-camino le pasa --brujula-camino a main.py (la brújula por el camino, spec PUZZLE_SOLOS) y suma la columna
brujula_camino a agentes_*.csv y a geometria_*.csv; los dos seguidores (el de la puerta de madera y, con hierro, el de la
de hierro) siguen el rumbo de src/world/camino.py, la misma función que el sensor 9, con la etapa 1 y la 3. Sin el
argumento, siguen la recta y los tres CSV son los de antes.
acercarse-camino (va con acercarse) le pasa --acercarse-camino a main.py (la recompensa por acercarse medida por el
camino, spec PUZZLE_SOLOS), suma camino_ al nombre después de acercarse_ y la columna acercarse_camino a agentes_*.csv y a
geometria_*.csv. f_acercarse sale del estado del agente: no cambia. Sin el argumento, los tres CSV son los de antes.
fitness-sin-tope le pasa --fitness-sin-tope a main.py (la selección ordena por la suma de los términos, sin el tope de
100, spec PUZZLE_SOLOS), suma sin_tope_ al nombre después de brujula_camino_ y la columna fitness_sin_tope a
agentes_*.csv y a geometria_*.csv, y a agentes_*.csv la columna fitness_con_tope (el de 0 a 100, el que leen la mutación
adaptativa y la guía). El control de los términos compara su suma con piso en 0 con el fitness, y la cuenta con los
topes con fitness_con_tope. No va con evaluaciones=K. Sin el argumento, los tres CSV son los de antes.
cruce=X fija CROSSOVER_RATE en X (el resto de los
hijos sale por copia de un padre; la mutación, igual). pesos= fija parámetros numéricos de config.py
antes de main.main(), por ejemplo pesos=FITNESS_ACERCARSE:40,FITNESS_ANTI_CIRCLE:9 (el rebalance del
fitness, docs/qa/AnalisisQA.md#rebalance-fitness); van después de los del laboratorio, y un nombre que
config.py no tiene corta la corrida. congelar=G (con evolucion; GENERACIONES mayor que G): desde la
generación G + 1, evolve() devuelve agentes nuevos con los cerebros de la G, sin selección, cruce,
mutación ni inmigrantes, en un orden barajado con un azar propio (el de la lista decide quién actúa
primero en cada tick); esas generaciones duran lo que la G y nacen con la etapa de la G (el currículo).
Cada una es un episodio: mapa, lugar de nacimiento y estado nuevos. agentes_*.csv suma pesos_hash (los
pesos: los clones repiten hash), orden (lugar en la lista) y cerebro (desde la G, el id de su agente en
la G); control: cada cerebro está una vez por episodio, con el hash de la G.
evaluaciones=K (con evolucion, sin congelar ni reloj; GENERACIONES son las generaciones del AG, y main.py
corre K × GENERACIONES, una fila del CSV por episodio): después de los episodios 1 a K − 1 de cada
generación, evolve() devuelve agentes nuevos con los mismos cerebros, como congelar, en un orden barajado
con un azar propio (el primer episodio queda en el orden de evolve); después del K-ésimo llama al evolve
real con la generación del AG, y adentro el fitness de cada agente es el promedio de su cerebro en los K
episodios (evolve lo recalcula: se envuelve _calculate_fitness solo durante esa llamada). La duración y
el currículo de cada episodio son los de su generación del AG. agentes_*.csv suma gen_real, episodio,
pesos_hash, orden, cerebro (el id de su agente en el episodio 1) y, en el episodio K, fitness_prom y el
lugar, el pool y la élite con el promedio (lugar_prom, en_pool_prom, elite_prom); controles: cada cerebro
juega una vez cada episodio con el mismo hash, el orden de evolve es el del promedio, evolve corre solo
después del K-ésimo y nada cruza, copia ni muta afuera de él. reloj=R (el control de igual costo, con una
evaluación): la generación n dura y nace como la ⌈n/R⌉, el mismo reloj que con evaluaciones=R; desde la
TOPE_RELOJ·R + 1, como la TOPE_RELOJ (así el currículo no se corta si el control sigue). Deja en SALIDA, por corrida:
corrida_*.csv (el CSV de main.py), agentes_*.csv (una fila por agente y generación) y
geometria_*.csv (una por generación). Al final imprime "MEDICION inconsistencias=0":
cada golpe se predice antes de llamar al original, y el ranking se compara con el de evolve. Antes, "ENERGIA_GOLPE": lo
que cobró golpear por tick, medido en la energía en los ticks en que nada más la mueve (golpeando tiene que dar
HIT_ENERGY_COST, y sin golpear, 0; si no, suma inconsistencias): el costo que se cobró, no el de config.py (LEC-010).

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
sens_etapa0 = "sens-etapa0" in sys.argv[6:]
sens_golpe = "sens-golpe" in sys.argv[6:]
hierro = "hierro" in sys.argv[6:]
brujula = "brujula-camino" in sys.argv[6:]
acercarse_camino = "acercarse-camino" in sys.argv[6:]
if acercarse_camino and not acercarse:
    sys.exit("acercarse-camino va con acercarse: sin la recompensa por acercarse no hace nada")
sin_tope = "fitness-sin-tope" in sys.argv[6:]
curriculo30 = "curriculo30" in sys.argv[6:]
curriculo = next((int(a[len("curriculo="):]) for a in sys.argv[6:] if a.startswith("curriculo=")), None)
if curriculo is not None and (curriculo30 or curriculo < 1):
    sys.exit("curriculo=N va sin curriculo30, con N de 1 en adelante")
cruce = next((float(a[len("cruce="):]) for a in sys.argv[6:] if a.startswith("cruce=")), None)
pesos = next((a[len("pesos="):] for a in sys.argv[6:] if a.startswith("pesos=")), "")
congelar = next((int(a[len("congelar="):]) for a in sys.argv[6:] if a.startswith("congelar=")), None)
if congelar is not None and (tipo != "evolucion" or int(generaciones) <= congelar):
    sys.exit("congelar=G va con evolucion y con GENERACIONES mayor que G")  # sin evolución no se llama a evolve
evaluaciones = next((int(a[len("evaluaciones="):]) for a in sys.argv[6:] if a.startswith("evaluaciones=")), 1)
reloj = next((int(a[len("reloj="):]) for a in sys.argv[6:] if a.startswith("reloj=")), None)
if evaluaciones < 1 or (reloj is not None and reloj < 2):
    sys.exit("evaluaciones=K va con K de 1 en adelante, y reloj=R con R de 2 en adelante")
if evaluaciones > 1 and (tipo != "evolucion" or congelar is not None or reloj is not None):
    sys.exit("evaluaciones=K (K > 1) va con evolucion, sin congelar ni reloj")  # sin evolución no hay selección
if evaluaciones > 1 and sin_tope:
    sys.exit("evaluaciones=K (K > 1) va sin fitness-sin-tope")  # el promedio con tope de la mutación no se lleva
if reloj is not None and congelar is not None:
    sys.exit("reloj=R va sin congelar")
TOPE_RELOJ = 30  # con reloj=R: la última generación de la tanda con evaluaciones=R que controla
RELOJ = evaluaciones if evaluaciones > 1 else reloj  # None: el reloj de siempre
os.chdir(raiz)  # main.py carga los sprites con ruta relativa
sys.path.insert(0, raiz)

import numpy as np  # noqa: E402
import main  # noqa: E402
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork  # noqa: E402
from src.evolution.genetic_algorithm import GeneticAlgorithm  # noqa: E402
from src.world import camino  # noqa: E402

RADIO_GOLPE = 25  # el de world.process_door_hit
H_PASOS = 1000    # con hierro: los pasos del seguidor desde la llave dorada (3 px por paso; el mapa es de 1200 px)


def centro_puerta(world, puerta=None):
    d = world.door if puerta is None else puerta
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
LLAMADAS_AG = [0]  # cruces, copias o mutaciones después de congelar o, con evaluaciones=K, afuera del evolve real: 0
SUMA = {}         # con evaluaciones=K: cerebro -> suma de su fitness en los episodios de la generación
CUENTA = {}       # cerebro -> episodios que jugó en la generación
PROMEDIO = {}     # cerebro -> su fitness promedio, después del episodio K (lo que ve el evolve real)
DENTRO_AG = [False]  # adentro del evolve real
LLAMADAS_DENTRO = [0]  # cruces, copias y mutaciones adentro del evolve real
EVOLVE_EN = []    # los episodios después de los que corrió el evolve real


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
    m = dict(d0_llave=None, dmin_llave=math.inf, d0=None, dmin=math.inf, ticks_etapa1=0, ticks_25=0, ticks_golpe=0, ticks_golpe_25=0,
             bloq_agente_inicio=0, bloq_agente_corte=0, bloq_puerta=0, golpes=0,
             t_llega25=None, t_golpe1=None, t_golpe2=None, ticks_25_post90=0, golpe_25_post90=0,
             sens_ticks=0, sens_brujula=0.0, sens_comida=0.0, ticks_avanza=0, ticks_gira=0, giro_abs=0.0)
    if sens_etapa0:  # sin el argumento, las columnas de antes
        m.update(sens_ticks0=0, sens_brujula0=0.0, sens_comida0=0.0)
    for suf in ('', '0') if sens_golpe else ():  # sin el argumento, tampoco estas
        if suf == '' or sens_etapa0:
            m.update({'zgolpe_pegado' + suf: 0.0, 'zgolpe_lejos' + suf: 0.0, 'golpea_pegado' + suf: 0, 'golpea_lejos' + suf: 0})
    if hierro:  # sin el argumento, tampoco estas
        m.update(h_t_dorada=None, h_d0=None, h_dmin=math.inf, h_ticks=0, h_ticks_25=0, h_t_llega25=None, h_ticks_golpe=0,
                 h_ticks_golpe_25=0, h_bloq_agente=0, h_bloq_puerta=0, h_golpes=0, h_t_golpe1=None, h_t_golpe2=None,
                 h_t_golpe3=None, h_ticks_25_listo=0, h_golpe_25_listo=0, h_ticks_fuera_entre=0)
    return m


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
    if sin_tope:  # la selección ve la suma con piso en 0; la mutación y la guía, la de 0 a 100
        if abs(max(0, total) - a.fitness) > 1e-6 or abs(min(max(0, min(100, total)), tope) - a.fitness_con_tope) > 1e-6:
            INCONS[0] += 1  # los términos no suman el fitness del agente
    elif abs(min(max(0, min(100, total)), tope) - a.fitness) > 1e-6:
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


def golpe(cerebro, p, pegado):
    """Con la percepción p que vio el agente, la salida 'hit' de su red antes del tanh (z) con el sensor 11 en pegado
    y en 1,0 (lejos). En z, un corrimiento parejo del golpe mueve las dos igual y no cambia su diferencia; con el tanh o
    con la decisión, achicaría también la diferencia. Forward aparte del de sensibilidad(). Solo numpy, sin azar."""
    x = np.repeat(p[None, :], 2, axis=0)
    x[0, 10], x[1, 10] = pegado, 1.0
    a = x
    for i in range(len(cerebro.weights) - 1):
        a = np.tanh(np.dot(a, cerebro.weights[i]) + cerebro.biases[i])
    z = np.dot(a, cerebro.weights[-1]) + cerebro.biases[-1]
    return z[:, ORDEN_SALIDAS.index('hit')]


ENERGIA = dict(golpe_ticks=0, golpe_extra=0.0, sin_ticks=0, sin_extra=0.0)  # lo que cobró golpear, medido en la energía


def energia_de_golpear(agente, world, antes):
    """Lo que el tick le restó al agente además del consumo, en los ticks en que nada más mueve la energía (no comió, no
    tomó una poción, no está en el agua): golpeando tiene que ser HIT_ENERGY_COST, y sin golpear, 0. Mide el costo que se
    cobró, no el que dice config.py (LEC-010). Solo lee el estado, sin azar."""
    if agente.eating or agente.energy >= agente.max_energy or any(
            o.type == "water" and o.collides_with(agente.x, agente.y, agente.radius) for o in world.obstacles):
        return
    extra = antes - agente.energy - SimulationConfig.AGENT_ENERGY_CONSUMPTION
    k = "golpe" if agente.golpeando else "sin"
    ENERGIA[k + "_ticks"] += 1
    ENERGIA[k + "_extra"] += extra
    if abs(extra - (SimulationConfig.HIT_ENERGY_COST if agente.golpeando else 0.0)) > 1e-9:
        INCONS[0] += 1  # el tick cobró otra cosa que el costo de config.py


_act = AdvancedAgent.act


def act(self, decisions, world, other_agents, tick):
    vivo = self.alive
    angulo, predicho = self.angle, None
    if vivo and getattr(self, "_med_percepcion", None) is not None and (
            (self.etapa == 1 and world.door) or (sens_etapa0 and self.etapa == 0 and world.red_key)):
        m = MED.setdefault(self, nueva())
        sb, sc, salida = sensibilidad(self.brain, self._med_percepcion)
        suf = '' if self.etapa == 1 else '0'  # con sens-etapa0, la etapa 0 va a sus propias columnas
        m['sens_ticks' + suf] += 1
        m['sens_brujula' + suf] += float(sb)
        m['sens_comida' + suf] += float(sc)
        tomadas = np.array([decisions[k] for k in ORDEN_SALIDAS])
        if np.abs(np.clip(salida, 0, 1) - tomadas).max() > 1e-6:
            INCONS[0] += 1  # el forward en lote no es el de la red
        if sens_golpe:
            p = self._med_percepcion
            zp, zl = golpe(self.brain, p, RADIO_GOLPE / self.vision_range)
            m['zgolpe_pegado' + suf] += float(zp)
            m['zgolpe_lejos' + suf] += float(zl)
            m['golpea_pegado' + suf] += int(np.tanh(zp) > 0.5)
            m['golpea_lejos' + suf] += int(np.tanh(zl) > 0.5)
            paso = self._proximo_paso(world)
            # Con brujula-camino, el sensor 11 es la distancia por el camino (camino.rumbo); si no, la recta
            distancia = (float(camino.rumbo(world, self.etapa, self.x, self.y)[1]) if brujula
                         else math.hypot(paso[0] - float(self.x), paso[1] - float(self.y)))
            if abs(p[10] - min(distancia / self.vision_range, 1.0)) > 1e-5:
                INCONS[0] += 1  # el sensor 11 no es la distancia al próximo paso
            if p[10] == 1.0 and (np.tanh(zl) > 0.5) != (decisions['hit'] > 0.5):
                INCONS[0] += 1  # lejos de verdad, la decisión no es la que tomó: no es la salida 'hit'
        predicho = float(giro(tomadas[None, :])[0])
        if self.etapa == 1:
            m['ticks_avanza'] += int(decisions['move_forward'] > 0.5)
            m['ticks_gira'] += int(predicho != 0.0)
            m['giro_abs'] += abs(predicho)
    self._med_percepcion = None
    energia = self.energy
    _act(self, decisions, world, other_agents, tick)
    if vivo:
        energia_de_golpear(self, world, energia)
    if predicho is not None and abs((self.angle - angulo) - predicho) > 1e-9:
        INCONS[0] += 1  # giro() no es el de act()
    if hierro and vivo and self.etapa == 3 and world.door_iron:
        medir_hierro(self, world, tick)
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


def medir_hierro(agente, world, tick):
    """Con hierro, después de moverse y con la llave dorada (etapa 3): lo que act() mide en la etapa 1 para la puerta de
    madera, con la puerta de hierro, y entre golpe y golpe. Los golpes del agente son los de hasta el tick anterior: el de
    este tick lo prueba _try_hit_door después. Solo lee el estado, sin azar."""
    m = MED.setdefault(agente, nueva())
    cx, cy = centro_puerta(world, world.door_iron)
    d = math.hypot(agente.x - cx, agente.y - cy)
    m['h_ticks'] += 1
    if m['h_t_dorada'] is None:
        m['h_t_dorada'], m['h_d0'] = tick, d  # el primer act con la llave dorada: casi donde la agarró
    if d < m['h_dmin']:
        m['h_dmin'] = d
    if agente.golpeando:
        m['h_ticks_golpe'] += 1
    golpes, ultimo = agente.golpes_puerta.get('door_iron', (0, 0))
    if d < RADIO_GOLPE:
        m['h_ticks_25'] += 1
        if m['h_t_llega25'] is None:
            m['h_t_llega25'] = tick
        if agente.golpeando:
            m['h_ticks_golpe_25'] += 1
        if golpes >= 1 and tick - ultimo >= SimulationConfig.DOOR_HIT_COOLDOWN:
            m['h_ticks_25_listo'] += 1
            if agente.golpeando:
                m['h_golpe_25_listo'] += 1
    elif golpes >= 1:
        m['h_ticks_fuera_entre'] += 1


def prediccion_hierro(agente, world, current_tick, m):
    """Con hierro y la llave dorada: si el golpe de este tick a la puerta de hierro va a contar y, si no, qué lo frena.
    None si no corresponde predecir (sin el argumento o en otra etapa)."""
    if not (hierro and agente.etapa == 3 and world.door_iron):
        return None
    if not agente.golpeando:
        return False
    cx, cy = centro_puerta(world, world.door_iron)
    if math.hypot(agente.x - cx, agente.y - cy) >= RADIO_GOLPE:
        return False
    if current_tick - agente.last_tree_hit_tick < agente.tree_hit_cooldown:
        m['h_bloq_agente'] += 1  # el cooldown del agente: lo ponen abrir la puerta de madera y cortar
        return False
    if current_tick - agente.golpes_puerta.get('door_iron', (0, 0))[1] < SimulationConfig.DOOR_HIT_COOLDOWN:
        m['h_bloq_puerta'] += 1
        return False
    return True


_hit = AdvancedAgent._try_hit_door


def try_hit_door(self, world, current_tick):
    prediccion = None
    m = MED.setdefault(self, nueva())
    prediccion_h = prediccion_hierro(self, world, current_tick, m)
    antes_h = self.golpes_puerta.get('door_iron', (0, 0))[0]
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
    despues_h = self.golpes_puerta.get('door_iron', (0, 0))[0]
    if prediccion_h is not None:
        if despues_h > antes_h:
            m['h_golpes'] += despues_h - antes_h
            m['h_t_golpe' + str(min(despues_h, 3))] = current_tick
        if prediccion_h != (despues_h > antes_h):
            INCONS[0] += 1  # el golpe a la puerta de hierro no fue el que se predijo
    return resultado


def geometria(world, puerta=None):
    """La distancia más corta al centro de la puerta a la que puede estar el centro de un agente con
    etapa 1, y el área libre a menos de 25 px, con las mismas colisiones que act(). Con puerta, la de
    hierro (etapa 3), con la misma cuenta."""
    puerta = world.door if puerta is None else puerta
    cx, cy = centro_puerta(world, puerta)
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
            if puerta.collides_with(x, y, r):
                continue
            if any(o.collides_with(x, y, r, r) for o in perim):
                continue
            libres += 1
            dmin = min(dmin, d)
    return dmin, libres * paso * paso


def colisiones(world, puerta):
    """Las colisiones de act() para el seguidor, con una sola puerta cerrada: la que busca."""
    r = SimulationConfig.AGENT_RADIUS
    cajas = [(o.x + o.width // 2, o.y + o.height // 2, o.width // 2 + r, o.height // 2 + r)
             for o in world.obstacles if o.type in ("wall", "tree", "hut")
             and not (o.type in ("tree", "hut") and o.is_cut)]
    d = puerta
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

    return choca


def seguir(world, puerta, choca, x0, y0, pasos, etapa):
    """Desde cada arranque, avanza 3 px por tick derecho al centro de la puerta, con las colisiones de act(), como hoy (si
    el paso choca, queda trabado) y deslizando. Con brujula-camino, con el rumbo de camino.rumbo para un agente de esa
    etapa, en lugar de derecho. Devuelve, en los dos, la distancia mínima de cada arranque y el primer paso a menos de 25
    px (−1 si no llega). Solo numpy, sin azar."""
    cx, cy = centro_puerta(world, puerta)
    r = SimulationConfig.AGENT_RADIUS
    resultados = []
    for desliza in (False, True):
        x, y = x0.copy(), y0.copy()
        dmin = np.hypot(x - cx, y - cy)
        t25 = np.where(dmin < RADIO_GOLPE, 0, -1)
        for paso in range(1, pasos + 1):
            ang = np.asarray(camino.rumbo(world, etapa, x, y)[0]) if brujula else np.arctan2(cy - y, cx - x)
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
            dist = np.hypot(x - cx, y - cy)
            dmin = np.minimum(dmin, dist)
            t25 = np.where((t25 < 0) & (dist < RADIO_GOLPE), paso, t25)
        resultados.append((dmin, t25))
    return resultados


def seguidor(world):
    """Un seguidor de brújula perfecto, sobre el mapa de la generación: desde una grilla de puntos de
    arranque (cada 25 px en la zona donde nacen los agentes, los que act() deja ocupar), avanza 3 px
    por tick derecho al centro de la puerta, con las colisiones de act(); si el paso choca, queda
    trabado (no hay deslizamiento). Devuelve la distancia final de cada arranque. Solo numpy, sin azar."""
    choca = colisiones(world, world.door)
    gx, gy = np.meshgrid(np.arange(50, 901, 25, dtype=float), np.arange(50, 751, 25, dtype=float))
    x0, y0 = gx.ravel(), gy.ravel()
    adentro = np.array([world._is_inside_fortress(a, b) for a, b in zip(x0, y0)])
    ok = ~adentro & ~choca(x0, y0)
    x0, y0 = x0[ok], y0[ok]
    return [dmin for dmin, _ in seguir(world, world.door, choca, x0, y0, 450, 1)]


def seguidor_hierro(world):
    """Con hierro: el seguidor de brújula perfecto desde la llave dorada, donde empieza la etapa 3, hacia la puerta de
    hierro, con la de madera abierta (el agente ya la abrió) y la de hierro cerrada, H_PASOS pasos. Devuelve, como hoy y
    deslizando, la distancia mínima y el primer paso a menos de 25 px (−1 si no llega)."""
    x0 = np.array([float(world.gold_key.x)])
    y0 = np.array([float(world.gold_key.y)])
    return [(float(dmin[0]), int(t25[0])) for dmin, t25 in
            seguir(world, world.door_iron, colisiones(world, world.door_iron), x0, y0, H_PASOS, 3)]


_fila = main._fila_csv


def fila_csv(semilla_, evolucion, generacion, ticks, agents, world, learning_monitor):
    fila = _fila(semilla_, evolucion, generacion, ticks, agents, world, learning_monitor)
    orden = sorted(agents, key=lambda a: a.fitness, reverse=True)  # el mismo orden estable que evolve
    k = max(2, int(len(agents) * max(0.05, min(0.95, SimulationConfig.MEETING_POOL_FRACTION))))
    posicion = {a: i for i, a in enumerate(agents)}  # quién actúa primero en cada tick
    FILA_DE.clear()
    ep = (generacion - 1) % evaluaciones + 1  # con evaluaciones=K, el episodio dentro de la generación del AG
    if evaluaciones > 1 and ep == 1:
        SLOT.clear()
        HASH_G.clear()
        SUMA.clear()
        CUENTA.clear()
    for lugar, a in enumerate(orden, start=1):
        m = MED.get(a, nueva())
        f = dict(semilla=semilla_, evolucion=int(evolucion), generacion=generacion, ticks_gen=ticks,
                 id=a.id, etapa_inicial=a.etapa_inicial, etapa=a.etapa, vivo=int(a.alive), edad=a.age,
                 fitness=round(float(a.fitness), 4), lugar=lugar, en_pool=int(lugar <= k),
                 elite=int(lugar <= SimulationConfig.ELITISM), golpes_puerta=a.golpes_puerta.get('door', (0, 0))[0],
                 abrio=int(a.etapa >= 2 and a.etapa_inicial < 2), aporte='')
        f['origen'], f['padre1'], f['padre2'] = ORIGEN.get(a, ('', '', ''))
        if sin_tope:  # el de 0 a 100, el que leen la mutación adaptativa y la guía; sin el argumento, no está
            f['fitness_con_tope'] = round(float(a.fitness_con_tope), 4)
        f.update({k2: round(v, 4) for k2, v in terminos_fitness(a).items()})
        f.update({k2: ('' if v is None else (round(v, 3) if isinstance(v, float) else v)) for k2, v in m.items()})
        if hierro and m['h_golpes'] != a.golpes_puerta.get('door_iron', (0, 0))[0]:
            INCONS[0] += 1  # los golpes contados no son los que el agente le dio a la puerta de hierro
        if congelar is not None:
            f['pesos_hash'], f['orden'], f['cerebro'] = hash_pesos(a.brain), posicion[a], ''
            if generacion == congelar:
                SLOT[a.brain] = a.id
                HASH_G[a.id] = f['pesos_hash']
            if generacion >= congelar:
                f['cerebro'] = SLOT.get(a.brain, '')
                if HASH_G.get(f['cerebro']) != f['pesos_hash']:
                    INCONS[0] += 1  # no es un cerebro de la generación G, o le cambiaron los pesos
        if evaluaciones > 1:
            f['gen_real'], f['episodio'] = (generacion - 1) // evaluaciones + 1, ep
            f['pesos_hash'], f['orden'] = hash_pesos(a.brain), posicion[a]
            if ep == 1:
                SLOT[a.brain] = a.id
                HASH_G[a.id] = f['pesos_hash']
            f['cerebro'] = SLOT.get(a.brain, '')
            if HASH_G.get(f['cerebro']) != f['pesos_hash']:
                INCONS[0] += 1  # no es un cerebro del episodio 1, o le cambiaron los pesos
            SUMA[a.brain] = SUMA.get(a.brain, 0.0) + float(a.fitness)
            CUENTA[a.brain] = CUENTA.get(a.brain, 0) + 1
            if CUENTA[a.brain] != ep:
                INCONS[0] += 1  # el cerebro jugó más o menos episodios que este
            f.update(fitness_prom='', lugar_prom='', en_pool_prom='', elite_prom='')
        FILAS.append(f)
        FILA_DE[a] = f
    if (congelar is not None and generacion > congelar) or evaluaciones > 1:
        cerebros = [FILA_DE[a]['cerebro'] for a in agents]
        if set(cerebros) != set(HASH_G) or len(set(cerebros)) != len(agents):
            INCONS[0] += 1  # cada cerebro de la G (o del episodio 1), una vez por episodio
    if evaluaciones > 1 and ep == evaluaciones:
        # El ranking que va a usar el evolve real: el promedio, con el mismo orden estable
        PROMEDIO.clear()
        PROMEDIO.update({b: s / evaluaciones for b, s in SUMA.items()})
        por_promedio = sorted(agents, key=lambda a: PROMEDIO[a.brain], reverse=True)
        for lugar, a in enumerate(por_promedio, start=1):
            FILA_DE[a].update(fitness_prom=round(PROMEDIO[a.brain], 4), lugar_prom=lugar, en_pool_prom=int(lugar <= k),
                              elite_prom=int(lugar <= SimulationConfig.ELITISM))
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
    if hierro:
        hd, harea = geometria(world, world.door_iron)
        (sd, st), (dd, dt) = seguidor_hierro(world)
        hx, hy = centro_puerta(world, world.door_iron)
        GEOM[-1].update(h_puerta_x=hx, h_puerta_y=hy, h_dmin_libre=round(hd, 3), h_area_libre_25=round(harea, 1),
                        h_seguidor_dmin=round(sd, 1), h_seguidor_t25='' if st < 0 else st,
                        h_desliza_dmin=round(dd, 1), h_desliza_t25='' if dt < 0 else dt)
    MED.clear()
    return fila


_evolve = GeneticAlgorithm.evolve
_cross = SimpleNeuralNetwork.crossover
_copy = SimpleNeuralNetwork.copy_from


def prohibida():
    """Una llamada de cruce, copia o mutación donde no tiene que haber: después de congelar o, con
    evaluaciones=K, afuera del evolve real. Y cuenta las de adentro."""
    LLAMADAS_DENTRO[0] += int(DENTRO_AG[0])
    return int(CONGELADO[0] or (evaluaciones > 1 and not DENTRO_AG[0]))


def crossover(self, other):
    LLAMADAS_AG[0] += prohibida()
    hijo = _cross(self, other)
    CRUCES[id(hijo)] = (self, other)
    return hijo


def copy_from(self, other):
    LLAMADAS_AG[0] += prohibida()
    resultado = _copy(self, other)
    CRUCES[id(self)] = (other, None)
    return resultado


_mutate = SimpleNeuralNetwork.mutate


def mutate(self, mutation_rate=0.1):
    LLAMADAS_AG[0] += prohibida()
    return _mutate(self, mutation_rate)


def clones(agents, generation, origen):
    """Agentes nuevos (estado en cero) con los mismos cerebros, sin selección, cruce, mutación ni
    inmigrantes. El orden de la lista, quién actúa primero en cada tick, se baraja con un azar propio
    que no toca el de la corrida: si quedara fijo, la ventaja de actuar primero se repetiría entre
    episodios y se contaría como del cerebro."""
    ORIGEN.clear()
    nuevos = []
    for a in agents:
        hijo = AdvancedAgent(0, 0, a.brain)
        ORIGEN[hijo] = (origen, a.id, '')
        nuevos.append(hijo)
    random.Random(semilla * 1000 + generation).shuffle(nuevos)
    return nuevos


def congelados(agents, generation):
    """Con congelar=G, desde la generación G + 1: los cerebros de la G, en clones()."""
    CONGELADO[0] = True
    return clones(agents, generation, 'congelado')


_calc = AdvancedAgent._calculate_fitness


def fitness_promedio(self):
    """Con evaluaciones=K, solo adentro del evolve real: el fitness del agente es el promedio de su
    cerebro en los K episodios de la generación. Llama al original antes, por si algo depende de eso."""
    _calc(self)
    self.fitness = PROMEDIO[self.brain]
    self.fitness_con_tope = self.fitness  # la mutación adaptativa lo lee; sin fitness-sin-tope son el mismo
    return self.fitness


def evolve(self, agents, generation=1):
    if congelar is not None and generation >= congelar:
        return congelados(agents, generation)
    if evaluaciones > 1 and generation % evaluaciones:
        return clones(agents, generation, 'episodio')  # el episodio siguiente de la misma generación
    CRUCES.clear()
    if evaluaciones > 1:
        EVOLVE_EN.append(generation)
        DENTRO_AG[0] = True
        AdvancedAgent._calculate_fitness = fitness_promedio
        try:
            nuevos = _evolve(self, agents, generation // evaluaciones)  # la generación del AG: los inmigrantes
        finally:
            AdvancedAgent._calculate_fitness = _calc
            DENTRO_AG[0] = False
    else:
        nuevos = _evolve(self, agents, generation)
    # agents ya quedó ordenado por evolve: control del lugar que se anotó en _fila_csv (con el promedio)
    clave = 'lugar_prom' if evaluaciones > 1 else 'lugar'
    for lugar, a in enumerate(agents, start=1):
        if a in FILA_DE and FILA_DE[a][clave] != lugar:
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
if RELOJ is not None:
    _ticks_r = main._ticks_de_generacion
    _etapa_r = main._fijar_etapa_inicial
    tope = int(generaciones) if evaluaciones > 1 else TOPE_RELOJ

    def gen_de_reloj(n):
        """La generación cuya duración y currículo usa la n de main.py: la ⌈n/R⌉, hasta el tope."""
        return min(-(-n // RELOJ), tope)

    def ticks_de_generacion_r(config, generacion):
        return _ticks_r(config, gen_de_reloj(generacion))

    def fijar_etapa_inicial_r(agents, generacion):
        _etapa_r(agents, gen_de_reloj(generacion))

    main._ticks_de_generacion = ticks_de_generacion_r
    main._fijar_etapa_inicial = fijar_etapa_inicial_r
    if evaluaciones > 1:
        SimpleNeuralNetwork.mutate = mutate
        print(f"EVALUACIONES={evaluaciones}: {generaciones} generaciones de {evaluaciones} episodios"
              f" ({int(generaciones) * evaluaciones} en main.py)")
    else:
        print(f"RELOJ={reloj}: la generación n dura y nace como la n/{reloj} redondeada para arriba,"
              f" hasta la {TOPE_RELOJ}")

os.makedirs(salida, exist_ok=True)
if laboratorio:
    for k, v in PESOS_LABORATORIO.items():
        setattr(SimulationConfig, k, v)
    print(f"LABORATORIO {PESOS_LABORATORIO}")
if laboratorio or curriculo30:
    SimulationConfig.CURRICULO_HASTA_GENERACION = 30  # la brújula apunta a la puerta las 30 generaciones
    print("CURRICULO_HASTA_GENERACION=30")
if curriculo is not None:
    SimulationConfig.CURRICULO_HASTA_GENERACION = curriculo  # con laboratorio, pisa el 30
    print(f"CURRICULO_HASTA_GENERACION={curriculo}")
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
nombre = (f"s{semilla}_{'acercarse_' if acercarse else ''}{'camino_' if acercarse_camino else ''}"
          f"{'deslizar_' if deslizar else ''}"
          f"{'moviles_' if moviles else ''}{'brujula_camino_' if brujula else ''}{'sin_tope_' if sin_tope else ''}"
          f"{'laboratorio_' if laboratorio else ''}{'curriculo30_' if curriculo30 else ''}"
          f"{f'curriculo{curriculo}_' if curriculo is not None else ''}"
          f"{f'cruce{cruce}_' if cruce is not None else ''}{etiqueta_pesos}"
          f"{f'congelar{congelar}_' if congelar is not None else ''}"
          f"{f'evaluaciones{evaluaciones}_' if evaluaciones > 1 else ''}{f'reloj{reloj}_' if reloj else ''}{tipo}")
ruta_csv = os.path.join(salida, f"corrida_{nombre}.csv")
argv = ["--sin-ventana", "--generaciones", str(int(generaciones) * evaluaciones), "--semilla", str(semilla), "--modo", "autonomo",
        "--curriculo", "--csv", ruta_csv]
if acercarse:
    argv.append("--acercarse")
if deslizar:
    argv.append("--deslizar")
if moviles:
    argv.append("--fortalezas-moviles")
if brujula:
    argv.append("--brujula-camino")
if acercarse_camino:
    argv.append("--acercarse-camino")
if sin_tope:
    argv.append("--fitness-sin-tope")
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
    if evaluaciones > 1:
        f["evaluaciones"] = evaluaciones
    if reloj:
        f["reloj"] = reloj
    if brujula:  # sin el argumento, la columna no está: el CSV es el de antes
        f["brujula_camino"] = 1
    if acercarse_camino:  # igual
        f["acercarse_camino"] = 1
    if sin_tope:  # igual
        f["fitness_sin_tope"] = 1
for g in GEOM:
    g["deslizar"] = int(deslizar)
    g["fortalezas_moviles"] = int(moviles)
    g["laboratorio"] = int(laboratorio)
    if brujula:
        g["brujula_camino"] = 1
    if acercarse_camino:
        g["acercarse_camino"] = 1
    if sin_tope:
        g["fitness_sin_tope"] = 1
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
if evaluaciones > 1:
    INCONS[0] += LLAMADAS_AG[0]
    esperado = list(range(evaluaciones, evaluaciones * int(generaciones), evaluaciones))
    if EVOLVE_EN != esperado:
        INCONS[0] += 1  # el evolve real corre solo después del episodio K de cada generación, menos la última
    print(f"EVALUACIONES episodios={len({f['generacion'] for f in FILAS})} evolve={len(EVOLVE_EN)}"
          f" (despues de los episodios {EVOLVE_EN[:2]}...{EVOLVE_EN[-1:]}) llamadas_ag_afuera={LLAMADAS_AG[0]}"
          f" adentro={LLAMADAS_DENTRO[0]}")
print(f"ENERGIA_GOLPE golpeando: {ENERGIA['golpe_ticks']} ticks, {ENERGIA['golpe_extra'] / max(1, ENERGIA['golpe_ticks']):.6f}"
      f" por tick | sin golpear: {ENERGIA['sin_ticks']} ticks, {ENERGIA['sin_extra'] / max(1, ENERGIA['sin_ticks']):.6f} por tick"
      f" (HIT_ENERGY_COST={SimulationConfig.HIT_ENERGY_COST})")
print(f"MEDICION inconsistencias={INCONS[0]} filas={len(FILAS)}")
