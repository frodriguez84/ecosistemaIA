"""La brújula por el camino (BRUJULA_CAMINO; spec PUZZLE_SOLOS, sección "La brújula por el camino").

Para cada etapa del puzzle (0 a 4), una grilla de celdas de CELDA px con la distancia por el camino libre
más corto al objetivo de la etapa y el rumbo que sigue ese camino. Una celda es libre si un agente de esa
etapa puede tener el centro en el centro de la celda, con las cuentas de AdvancedAgent._choca. Las cinco
grillas se arman la primera vez que se pide una en la generación, y World.reset_food las borra. Solo
numpy: no consume azar.
"""

import math

import numpy as np

from config import SimulationConfig

# Tiene que ser de 7 px o menos: con el radio de 6, el hueco de una puerta de 20 px deja 8 px libres para
# el centro del agente, y con una celda más grande puede no caer ningún centro adentro
CELDA = 5

# Desde dónde se da el paso, como en world.py: una llave, a menos de su radio más 12 (check_key_pickup);
# una puerta, a menos de 25 de su centro (process_door_hit); el cofre, a menos de su radio más 8
# (check_chest_open)
MARGEN_LLAVE = 12
RADIO_GOLPE = 25
MARGEN_COFRE = 8

ETAPAS = range(5)

# Cuánto más alta que su vecina más alta queda una pared al interpolar el rumbo (_con_paredes), en px
PARED_MAS = 2 * CELDA

# Vecinas de una celda que no es libre, en el orden en que se prueban: primero las cuatro de los
# lados (a CELDA px del centro), después las diagonales
VECINAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))


def punto_del_paso(world, etapa):
    """Dónde está el próximo paso del puzzle para un agente de esa etapa (decisión 13): la llave roja
    (etapa 0), la puerta de madera (1), la llave dorada (2), la puerta de hierro (3) o el cofre (4). Las
    puertas y el cofre, por su centro, que es desde donde se mide el golpe. None con etapa 5, o si el paso
    no está en el mapa."""
    if etapa == 0 and world.red_key:
        return (world.red_key.x, world.red_key.y)
    if etapa == 2 and world.gold_key:
        return (world.gold_key.x, world.gold_key.y)
    objeto = {1: world.door, 3: world.door_iron, 4: world.chest}.get(etapa)
    if objeto:
        return (objeto.x + objeto.width // 2, objeto.y + objeto.height // 2)
    return None


def _alcance(world, etapa):
    """A cuánto del punto del paso se da el paso (estrictamente menos)."""
    if etapa == 0:
        return world.red_key.radius + MARGEN_LLAVE
    if etapa == 2:
        return world.gold_key.radius + MARGEN_LLAVE
    if etapa == 4:
        return world.chest.radius + MARGEN_COFRE
    return RADIO_GOLPE


def centros(world):
    """Los centros de las celdas: xs (columnas) e ys (filas)."""
    nx = int(math.ceil(world.screen_width / CELDA))
    ny = int(math.ceil(world.screen_height / CELDA))
    return (np.arange(nx) + 0.5) * CELDA, (np.arange(ny) + 0.5) * CELDA


def _chocan(cajas, xs, ys, r):
    """Las celdas cuyo centro choca con alguna caja centrada, con la cuenta de Obstacle.collides_with y
    Door.collides_with: choca si la distancia en x es a lo sumo el medio ancho más el radio, y en y igual."""
    choca = np.zeros((len(ys), len(xs)), dtype=bool)
    for o in cajas:
        en_x = np.abs(xs - (o.x + o.width // 2)) <= o.width // 2 + r
        en_y = np.abs(ys - (o.y + o.height // 2)) <= o.height // 2 + r
        choca |= en_y[:, None] & en_x[None, :]
    return choca


def libres(world, etapa):
    """Qué celdas son libres para el centro de un agente de esa etapa: las cuentas de _choca. Paredes,
    árboles y casitas sin talar, las puertas que no abrió (la de madera hasta la etapa 1, la de hierro
    hasta la 3), el perímetro y el estanque, con la caja que va de (x, y) hacia abajo y a la derecha
    (DIAG-30). El agua no choca."""
    xs, ys = centros(world)
    r = SimulationConfig.AGENT_RADIUS
    cajas = [o for o in world.obstacles if o.type in ("wall", "tree", "hut")
             and not (o.type in ("tree", "hut") and o.is_cut)]
    if world.door and etapa < 2:
        cajas.append(world.door)
    if world.door_iron and etapa < 4:
        cajas.append(world.door_iron)
    choca = _chocan(cajas, xs, ys, r)
    for o in list(world.perimeter_obstacles) + list(world.pond_obstacles):
        en_x = (o.x < xs + r) & (o.x + o.width > xs)
        en_y = (o.y < ys + r) & (o.y + o.height > ys)
        choca |= en_y[:, None] & en_x[None, :]
    return ~choca


def _vecinos(T):
    """Los cuatro vecinos de cada celda (izquierda, derecha, arriba, abajo), con infinito afuera."""
    marco = np.full((T.shape[0] + 2, T.shape[1] + 2), np.inf)
    marco[1:-1, 1:-1] = T
    return marco[1:-1, :-2], marco[1:-1, 2:], marco[:-2, 1:-1], marco[2:, 1:-1]


def distancias(libre, fuente, valor0, maximo_iteraciones=100_000):
    """La distancia por el camino desde las celdas fuente (que arrancan con valor0) a cada celda libre:
    la ecuación eikonal con el esquema de Godunov, con iteraciones hasta que no cambia (el mismo punto
    fijo que fast marching). Infinito en las celdas que no son libres y en las que no tienen camino."""
    h = float(CELDA)
    T = np.where(fuente & libre, valor0, np.inf)
    for _ in range(maximo_iteraciones):
        izq, der, arr, aba = _vecinos(T)
        a, b = np.minimum(izq, der), np.minimum(arr, aba)
        menor = np.minimum(a, b)
        with np.errstate(invalid="ignore"):
            d = np.abs(a - b)
            nuevo = np.where(d >= h, menor + h, (a + b + np.sqrt(np.maximum(2 * h * h - d * d, 0.0))) / 2)
        nuevo[np.isinf(menor)] = np.inf
        nuevo = np.where(libre, np.minimum(nuevo, T), np.inf)
        if np.array_equal(nuevo, T):
            return T
        T = nuevo
    raise RuntimeError("la distancia por el camino no convergió")


def _rumbos(T):
    """El rumbo en cada celda: el contrario del gradiente de T, con la diferencia hacia el vecino más bajo
    de cada eje si es más bajo que la celda (upwind), en el ángulo de la pantalla (y crece hacia abajo)."""
    izq, der, arr, aba = _vecinos(T)
    with np.errstate(invalid="ignore"):
        gx = np.where(np.minimum(izq, der) < T, np.where(izq <= der, T - izq, der - T), 0.0)
        gy = np.where(np.minimum(arr, aba) < T, np.where(arr <= aba, T - arr, aba - T), 0.0)
    gx = np.where(np.isfinite(gx), gx, 0.0)
    gy = np.where(np.isfinite(gy), gy, 0.0)
    return np.arctan2(-gy, -gx), (gx == 0) & (gy == 0)


def _representante(libre):
    """Para cada celda, la celda que se lee: ella misma si es libre; si no, la primera vecina libre en el
    orden de VECINAS; si no hay ninguna, ella misma. Devuelve las filas y las columnas."""
    ny, nx = libre.shape
    fi, co = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    fila, col = fi.copy(), co.copy()
    falta = ~libre
    for df, dc in VECINAS:
        f2, c2 = fi + df, co + dc
        dentro = (f2 >= 0) & (f2 < ny) & (c2 >= 0) & (c2 < nx)
        ok = falta & dentro
        ok[ok] = libre[f2[ok], c2[ok]]
        fila[ok], col[ok] = f2[ok], c2[ok]
        falta &= ~ok
    return fila, col


def _con_paredes(T):
    """T para interpolar: en una celda sin distancia (pared, o libre sin camino), la mayor de sus cuatro
    vecinas con distancia más PARED_MAS. Así, cerca de una pared el rumbo se aleja de ella y corrige el
    desvío del agente contra el centro de la celda. Infinito si ninguna vecina tiene distancia."""
    izq, der, arr, aba = _vecinos(np.where(np.isfinite(T), T, -np.inf))
    mayor = np.maximum.reduce([izq, der, arr, aba])
    return np.where(np.isfinite(T), T, np.where(np.isfinite(mayor), mayor + PARED_MAS, np.inf))


class CampoCamino:
    """La grilla de una etapa. Por celda, ya con la celda que se lee: la distancia por el camino, el rumbo
    de la celda (para cuando no se puede interpolar) y si va la recta de hoy (una celda del objetivo, sin
    camino, o sin celda libre cerca). Y T con las paredes, para interpolar el rumbo."""

    def __init__(self, world, etapa):
        xs, ys = centros(world)
        self.nx, self.ny = len(xs), len(ys)
        punto = punto_del_paso(world, etapa)
        if punto is None:
            self.angulo = np.zeros((self.ny, self.nx))
            self.distancia = self.interpolable = np.full((self.ny, self.nx), np.inf)
            self.recta = np.ones((self.ny, self.nx), dtype=bool)
            return
        libre = libres(world, etapa)
        valor0 = np.hypot(xs[None, :] - punto[0], ys[:, None] - punto[1])
        fuente = libre & (valor0 < _alcance(world, etapa))
        T = distancias(libre, fuente, valor0)
        angulo, plano = _rumbos(T)
        recta = fuente | np.isinf(T) | ~libre | plano
        fila, col = _representante(libre)
        self.angulo, self.distancia, self.recta = angulo[fila, col], T[fila, col], recta[fila, col]
        self.interpolable = _con_paredes(T)


def campos(world):
    """Las grillas de las etapas 0 a 4 del mapa de la generación: se arman la primera vez que se piden y
    quedan en el mundo hasta que World.reset_food las borra."""
    armados = getattr(world, "campos_camino", None)
    if armados is None:
        armados = [CampoCamino(world, etapa) for etapa in ETAPAS]
        world.campos_camino = armados
    return armados


def rumbo(world, etapa, x, y):
    """El rumbo (el ángulo de np.arctan2 en la pantalla) y la distancia al próximo paso por el camino,
    desde (x, y), que pueden ser números o arrays. Lo usan los sensores 9 y 11 y el seguidor de
    medir_puerta.py. Llamarla sin próximo paso (etapa 5, o el paso fuera del mapa) es un error.

    - En una celda del objetivo, sin camino o sin celda libre cerca: la recta de hoy al punto del paso.
    - Si no: el contrario del gradiente de T interpolado (bilineal) entre los centros de las cuatro celdas
      que rodean el punto, con las paredes más altas (_con_paredes). Si alguna de las cuatro no tiene
      valor, o el gradiente da 0, el rumbo de la celda.
    - La distancia, la de la celda."""
    px, py = punto_del_paso(world, etapa)
    campo = campos(world)[etapa]
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dx, dy = px - x, py - y
    j = np.clip((x // CELDA).astype(np.intp), 0, campo.nx - 1)
    i = np.clip((y // CELDA).astype(np.intp), 0, campo.ny - 1)
    recta = campo.recta[i, j]
    # Las cuatro celdas alrededor: la columna j0 y la j0 + 1, la fila i0 y la i0 + 1
    fx, fy = x / CELDA - 0.5, y / CELDA - 0.5
    j0 = np.clip(np.floor(fx).astype(np.intp), 0, campo.nx - 2)
    i0 = np.clip(np.floor(fy).astype(np.intp), 0, campo.ny - 2)
    tx, ty = np.clip(fx - j0, 0.0, 1.0), np.clip(fy - i0, 0.0, 1.0)
    T = campo.interpolable
    t00, t01, t10, t11 = T[i0, j0], T[i0, j0 + 1], T[i0 + 1, j0], T[i0 + 1, j0 + 1]
    with np.errstate(invalid="ignore"):
        gx = (1 - ty) * (t01 - t00) + ty * (t11 - t10)
        gy = (1 - tx) * (t10 - t00) + tx * (t11 - t01)
    ok = np.isfinite(gx) & np.isfinite(gy) & ((gx != 0) | (gy != 0))
    angulo = np.where(ok, np.arctan2(-np.where(ok, gy, 0.0), -np.where(ok, gx, 0.0)), campo.angulo[i, j])
    return (np.where(recta, np.arctan2(dy, dx), angulo),
            np.where(recta, np.sqrt(dx * dx + dy * dy), campo.distancia[i, j]))

