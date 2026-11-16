"""
Tests de las fortalezas móviles (FORTALEZAS_MOVILES, --fortalezas-moviles; sugerida por la medición de
acercarse 40 sin caminar, docs/qa/AnalisisQA.md#acercarse-sin-caminar).

Prendido, en cada generación desde la 2 las dos fortalezas van a un lugar al azar, con sus puertas, la
llave dorada y el cofre; la generación 1 queda como siempre. Apagado, no consume azar y el CSV es el de
antes del switch, byte a byte. La puerta queda accesible y el puzzle se puede completar: se mira con
las componentes conexas de una grilla de 3 px (lo que camina un agente en un tick), con las colisiones
de act() para cada etapa. Un camino en la grilla es un camino de verdad, así que el test no da por
alcanzable algo que no lo es.
"""

import csv
import hashlib
import io
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import ndimage

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402 (main importa pygame y todo el resto)
from config import SimulationConfig  # noqa: E402
from src.agents.advanced_agent import AdvancedAgent  # noqa: E402
from src.analytics.boletin import armar_boletin  # noqa: E402
from src.analytics.registro import RegistroDeLaCorrida  # noqa: E402
from src.ui.stats import datos_de_la_generacion  # noqa: E402
from src.world import world as modulo_world  # noqa: E402
from src.world.world import World  # noqa: E402

# Las de la generación 1, siempre (_generate_fortresses, con el mundo de 960 × 800)
CHICA_GEN1 = {"x": 50, "y": 50, "size": 5}
GRANDE_GEN1 = {"x": 718, "y": 558, "size": 6}

# El CSV de main._simular (semilla 7, 3 generaciones de 60 ticks), calculado con el código de antes del
# switch (349a43f) con scratchpad/hash_corto.py de la sesión; el de hoy, apagado, da lo mismo. Si un
# cambio de la simulación lo cambia a propósito, se recalcula y se anota por qué
CSV_DE_ANTES = {
    ("guiado", True): "9af1094f93fd8900759bfd24e8d51d9fc84c0c0e734027efbde2317649cde151",
    ("guiado", False): "1d2137478a846c3dd306ffcf732cd680184f449bb9312824348e8fe606d17a86",
    ("autonomo", True): "cbd4e32c95831cbe1694ea9b8bf28e609ce9e87f9dc2a08f9ece53bf51d497fb",
    ("autonomo", False): "9aeb4523730bbc23a45afd9d9ed8c10ef71482ce3f5d76c686d9c27b32897f99",
}

R = SimulationConfig.AGENT_RADIUS
PASO = 3  # lo que camina un agente en un tick (AGENT_SPEED)
RADIO_GOLPE = 25  # el de world.process_door_hit


def _mundo(monkeypatch, semilla, moviles=True):
    monkeypatch.setattr(SimulationConfig, "FORTALEZAS_MOVILES", moviles, raising=False)
    random.seed(semilla)
    np.random.seed(semilla)
    return World(SimulationConfig.get_game_area_width(), SimulationConfig.SCREEN_HEIGHT, SimulationConfig.FOOD_COUNT)


def _generaciones(monkeypatch, semilla, hasta):
    """El mundo de cada generación, de la 1 a `hasta`, con las fortalezas móviles y los agentes ubicados
    como en main.py. Devuelve el mismo mundo en cada vuelta: mirarlo antes de pedir la siguiente."""
    mundo = _mundo(monkeypatch, semilla)
    for generacion in range(1, hasta + 1):
        if generacion > 1:
            mundo.reset_food(generacion)
        agentes = [AdvancedAgent(0, 0) for _ in range(SimulationConfig.POPULATION_SIZE)]
        main._ubicar_agentes(mundo, agentes)
        yield generacion, mundo, agentes


def _lugares(mundo):
    return (dict(mundo.small_fortress_pos), dict(mundo.large_fortress_pos))


def _centro(objeto):
    return objeto.x + objeto.width // 2, objeto.y + objeto.height // 2


class Grilla:
    """Los lugares de la grilla de 3 px donde un agente con esa etapa puede estar, y sus componentes
    conexas (4-conexas), con las colisiones de act(): obstáculos, las puertas que no abrió, el
    perímetro y el estanque (con su caja descentrada, DIAG-30)."""

    def __init__(self, mundo, etapa):
        xs = np.arange(R, mundo.screen_width - R + 1, PASO, dtype=float)
        ys = np.arange(R, mundo.screen_height - R + 1, PASO, dtype=float)
        self.X, self.Y = np.meshgrid(xs, ys)
        choca = np.zeros(self.X.shape, dtype=bool)
        cajas = [o for o in mundo.obstacles if o.type in ("wall", "tree", "hut") and not o.is_cut]
        cajas += [mundo.door] if etapa < 2 else []
        cajas += [mundo.door_iron] if etapa < 4 else []
        for o in cajas:
            cx, cy = _centro(o)
            choca |= (np.abs(self.X - cx) <= o.width // 2 + R) & (np.abs(self.Y - cy) <= o.height // 2 + R)
        for o in mundo.perimeter_obstacles + mundo.pond_obstacles:
            choca |= ((o.x < self.X + R) & (o.x + o.width > self.X)
                      & (o.y < self.Y + R) & (o.y + o.height > self.Y))
        self.libre = ~choca
        self.componentes, _ = ndimage.label(self.libre)

    def componente(self, x, y):
        """La componente del lugar libre de la grilla más cercano a (x, y)."""
        d = np.where(self.libre, np.hypot(self.X - x, self.Y - y), np.inf)
        i = np.unravel_index(np.argmin(d), d.shape)
        assert d[i] <= PASO, (x, y)
        return self.componentes[i]

    def lugares_de(self, componente):
        return self.X[self.componentes == componente], self.Y[self.componentes == componente]


# --- Apagado ---

def test_apagado_por_defecto_y_los_flags(capsys):
    import experimento  # noqa: E402
    assert SimulationConfig.FORTALEZAS_MOVILES is False
    for modulo in (main, experimento):
        assert modulo._leer_argumentos([]).fortalezas_moviles is False
        assert modulo._leer_argumentos(["--fortalezas-moviles"]).fortalezas_moviles is True
        capsys.readouterr()
        with pytest.raises(SystemExit):
            modulo._leer_argumentos(["--help"])
        assert "--fortalezas-moviles" in capsys.readouterr().out, modulo.__name__


def _correr_adentro(monkeypatch, capsys, modo, evolucion, moviles):
    """main._simular sin ventana, semilla 7, 3 generaciones de 60 ticks. Devuelve las filas del CSV."""
    for nombre, valor in (("HEADLESS_MODE", True), ("MAX_GENERATIONS", 3), ("BASE_TICKS", 60), ("MODO", modo),
                          ("RECOMPENSA_ACERCARSE", False), ("CURRICULO", False), ("DESLIZAR", False),
                          ("FORTALEZAS_MOVILES", moviles)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    random.seed(7)
    np.random.seed(7)
    filas = []
    capsys.readouterr()
    main._simular(7, evolucion, filas.append)
    capsys.readouterr()
    return filas


def _sha256_del_csv(filas):
    texto = io.StringIO()
    escritor = csv.writer(texto)
    escritor.writerow(main.COLUMNAS_CSV)
    escritor.writerows(filas)
    return hashlib.sha256(texto.getvalue().encode("utf-8")).hexdigest()


@pytest.mark.parametrize("modo, evolucion", list(CSV_DE_ANTES))
def test_apagado_el_csv_es_el_de_antes_del_switch(monkeypatch, capsys, modo, evolucion):
    filas = _correr_adentro(monkeypatch, capsys, modo, evolucion, moviles=False)
    assert _sha256_del_csv(filas) == CSV_DE_ANTES[(modo, evolucion)]
    # No es una columna del CSV: va solo en el nombre del archivo
    assert not any("fortaleza" in columna or "movil" in columna for columna in main.COLUMNAS_CSV)


def test_apagado_no_sortea_y_las_fortalezas_quedan_donde_estan(monkeypatch):
    def no_deberia(self):
        raise AssertionError("con el switch apagado no se sortean las fortalezas")

    monkeypatch.setattr(World, "_sortear_fortalezas", no_deberia)
    mundo = _mundo(monkeypatch, 3, moviles=False)
    puertas = [(o.x, o.y) for o in (mundo.door, mundo.door_iron, mundo.gold_key, mundo.chest)]
    for generacion in range(2, 6):
        mundo.reset_food(generacion)
        assert _lugares(mundo) == (CHICA_GEN1, GRANDE_GEN1)
        assert [(o.x, o.y) for o in (mundo.door, mundo.door_iron, mundo.gold_key, mundo.chest)] == puertas


# --- Prendido: dónde van ---

def test_prendido_la_gen_1_es_la_de_siempre_y_despues_cambian_con_su_contenido(monkeypatch):
    vistos = []
    for generacion, mundo, _ in _generaciones(monkeypatch, 5, 8):
        chica, grande = _lugares(mundo)
        if generacion == 1:
            assert (chica, grande) == (CHICA_GEN1, GRANDE_GEN1)
        assert (chica, grande) not in vistos
        vistos.append((chica, grande))
        # Las puertas, la llave dorada y el cofre, en el lugar de _generate_fortresses
        assert (mundo.door.x, mundo.door.y) == (chica["x"] + 40, chica["y"] + 80)
        assert (mundo.gold_key.x, mundo.gold_key.y) == (chica["x"] + 60, chica["y"] + 40)
        assert (mundo.door_iron.x, mundo.door_iron.y) == (grande["x"] + 40, grande["y"])
        assert (mundo.chest.x, mundo.chest.y) == (grande["x"] + 60, grande["y"] + 60)


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_prendido_no_se_pisan_con_nada(monkeypatch, semilla):
    t = SimulationConfig.TILE_SIZE
    for generacion, mundo, agentes in _generaciones(monkeypatch, semilla, 10):
        chica, grande = _lugares(mundo)
        # Muros enteros: cada baldosa del borde, salvo la de la puerta
        paredes = {(o.x, o.y) for o in mundo.obstacles if o.type == "wall"}
        for pos, puerta in ((chica, mundo.door), (grande, mundo.door_iron)):
            n = pos["size"]
            borde = {(pos["x"] + 20 * i, pos["y"] + 20 * j) for i in range(n) for j in range(n)
                     if i in (0, n - 1) or j in (0, n - 1)}
            assert borde - paredes == {(puerta.x, puerta.y)}, generacion
            # A MARGEN_FORTALEZAS del borde del mapa, con el frente de la puerta
            lado = 20 * n
            assert 50 <= pos["x"] and pos["x"] + lado <= mundo.screen_width - 50
        assert chica["y"] >= 50 and mundo.door.y + 3 * t <= mundo.screen_height - 50
        assert mundo.door_iron.y - 3 * t >= 50 and grande["y"] + 120 <= mundo.screen_height - 50
        # Ni el estanque, ni otro obstáculo, ni la comida, la llave roja, el hacha o un agente adentro
        for pos in (chica, grande):
            lado = 20 * pos["size"]
            for p in mundo.pond_obstacles:
                assert not (p.x < pos["x"] + lado and p.x + p.width > pos["x"]
                            and p.y < pos["y"] + lado and p.y + p.height > pos["y"]), generacion
        assert not any(o.type != "wall" and mundo._is_inside_fortress(*_centro(o)) for o in mundo.obstacles)
        assert not any(mundo._is_inside_fortress(f["x"], f["y"]) for f in mundo.food_items)
        assert not mundo._is_inside_fortress(mundo.red_key.x, mundo.red_key.y)
        assert not mundo._is_inside_fortress(mundo.axe["x"], mundo.axe["y"])
        # Menos el que no encontró lugar y fue a (100, 100), que no mira nada: con las fijas cae adentro
        # de la chica (DIAG-33, de antes del switch)
        assert not any(mundo._is_inside_fortress(a.x, a.y) for a in agentes if (a.x, a.y) != (100, 100)), generacion


def test_las_zonas_quedan_separadas_y_adentro_es_donde_estan_ahora(monkeypatch):
    """La zona de cada fortaleza (muros y el despeje de su puerta) no toca la de la otra: si no, el despeje
    borraría muros de la otra (lo mira el test de arriba). Y "adentro" sigue a las fortalezas: el centro
    de la chica de la generación 1 es adentro solo si una fortaleza de ahora lo cubre."""
    t = SimulationConfig.TILE_SIZE
    g = modulo_world.SEPARACION_FORTALEZAS
    for _, mundo, _ in _generaciones(monkeypatch, 4, 12):
        chica, grande = _lugares(mundo)
        zona_chica = (chica["x"] - 24, chica["y"], chica["x"] + 136, mundo.door.y + 3 * t)
        zona_grande = (grande["x"] - 24, mundo.door_iron.y - 3 * t, grande["x"] + 136, grande["y"] + 120)
        assert (zona_chica[2] + g <= zona_grande[0] or zona_grande[2] + g <= zona_chica[0]
                or zona_chica[3] + g <= zona_grande[1] or zona_grande[3] + g <= zona_chica[1])
        cubre = any(p["x"] <= 100 <= p["x"] + 20 * p["size"] and p["y"] <= 100 <= p["y"] + 20 * p["size"]
                    for p in (chica, grande))
        assert mundo._is_inside_fortress(100, 100) == cubre


# --- Prendido: la puerta y el puzzle ---

@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_prendido_la_puerta_queda_accesible_desde_donde_nacen(monkeypatch, semilla):
    for generacion, mundo, agentes in _generaciones(monkeypatch, semilla, 6):
        grilla = Grilla(mundo, etapa=1)
        cx, cy = _centro(mundo.door)
        cerca = grilla.libre & (np.hypot(grilla.X - cx, grilla.Y - cy) < RADIO_GOLPE)
        al_lado = set(np.unique(grilla.componentes[cerca])) - {0}
        assert al_lado, generacion
        assert all(grilla.componente(a.x, a.y) in al_lado for a in agentes), generacion


def test_control_la_grilla_ve_una_puerta_tapada(monkeypatch):
    """El control del test de arriba: con tres muros pegados abajo de la puerta de madera, ningún agente
    llega a menos de 25 px (la única componente al lado es el interior de la fortaleza, cerrada)."""
    from src.world.obstacles import Obstacle
    for generacion, mundo, agentes in _generaciones(monkeypatch, 1, 2):
        dx, dy = mundo.door.x, mundo.door.y
        mundo.obstacles += [Obstacle(dx + i, dy + 20, 20, 20, "wall") for i in (-20, 0, 20)]
        grilla = Grilla(mundo, etapa=1)
        cx, cy = _centro(mundo.door)
        cerca = grilla.libre & (np.hypot(grilla.X - cx, grilla.Y - cy) < RADIO_GOLPE)
        al_lado = set(np.unique(grilla.componentes[cerca])) - {0}
        assert not any(grilla.componente(a.x, a.y) in al_lado for a in agentes), generacion


def _ir(mundo, agente, etapa, cerca_de):
    """Lleva al agente a un lugar libre de su componente (con las colisiones de su etapa) donde
    cerca_de(xs, ys) es verdad (con arrays). Falla si no hay ninguno: el paso no se puede alcanzar."""
    grilla = Grilla(mundo, etapa)
    xs, ys = grilla.lugares_de(grilla.componente(agente.x, agente.y))
    sirven = np.flatnonzero(cerca_de(xs, ys))
    assert len(sirven), f"etapa {etapa}: el paso no se alcanza"
    agente.x, agente.y = float(xs[sirven[0]]), float(ys[sirven[0]])


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_prendido_el_puzzle_se_puede_completar(monkeypatch, semilla):
    """Desde donde nace un agente con la llave roja (como en el currículo), paso por paso: camina por su
    componente hasta el próximo paso y lo da con los métodos del mundo (la llave dorada por contacto, las
    puertas y el cofre golpeando). La llave roja queda afuera: no depende de las fortalezas, y en el 0,5%
    de las generaciones cae en el medio del estanque, con las fijas igual que con las móviles (DIAG-34)."""
    for generacion, mundo, agentes in _generaciones(monkeypatch, semilla, 6):
        agente = agentes[0]
        agente.etapa, tick = 1, 1000

        for etapa, puerta, golpes in ((1, mundo.door, SimulationConfig.DOOR_HITS_TO_OPEN),
                                      (3, mundo.door_iron, SimulationConfig.DOOR_IRON_HITS_TO_OPEN)):
            if etapa == 3:
                _ir(mundo, agente, 2, lambda x, y: mundo.gold_key.collides_with(x, y, 12))
                assert mundo.check_key_pickup(agente) == "gold_key" and agente.etapa == 3
            cx, cy = _centro(puerta)
            _ir(mundo, agente, etapa, lambda x, y: np.hypot(x - cx, y - cy) < RADIO_GOLPE)
            abierta = None
            for _ in range(golpes):
                abierta = mundo.process_door_hit(agente, tick)
                tick += SimulationConfig.DOOR_HIT_COOLDOWN
            assert abierta == puerta.door_type and agente.etapa == etapa + 1, generacion

        _ir(mundo, agente, 4, lambda x, y: mundo.chest.collides_with(x, y, 8))
        assert mundo.check_chest_open(agente) and agente.etapa == 5, generacion


# --- La corrida, la ruta, el panel, el boletín, el experimento y el mapa de calor ---

def test_prendido_la_gen_1_es_la_del_apagado_despues_cambia_y_la_misma_semilla_da_lo_mismo(monkeypatch, capsys):
    apagado = _correr_adentro(monkeypatch, capsys, "autonomo", True, moviles=False)
    prendido = _correr_adentro(monkeypatch, capsys, "autonomo", True, moviles=True)
    assert prendido[0] == apagado[0]  # la generación 1, celda a celda
    assert prendido[1:] != apagado[1:]
    assert _correr_adentro(monkeypatch, capsys, "autonomo", True, moviles=True) == prendido


def test_la_ruta_el_panel_y_el_boletin_nombran_las_fortalezas_moviles(monkeypatch):
    for nombre, valor in (("MODO", "autonomo"), ("RECOMPENSA_ACERCARSE", False), ("CURRICULO", False),
                          ("DESLIZAR", True), ("FORTALEZAS_MOVILES", True)):
        monkeypatch.setattr(SimulationConfig, nombre, valor, raising=False)
    assert main._ruta_csv_por_defecto(3, True) == str(
        Path("results") / "corrida_s3_autonomo_deslizar_fortalezas_moviles_evolucion.csv")
    datos = dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert (datos["Ayudas"], datos["Fortalezas"]) == ("deslizar", "móviles")

    registro = RegistroDeLaCorrida(960, 800, 16)
    mejor = SimpleNamespace(id=1, x=50.0, y=50.0, alive=True, etapa=0, etapa_inicial=0, fitness=20.0,
                            food_eaten=1, distance_traveled=100.0, age=960)
    fila = dict.fromkeys(main.COLUMNAS_CSV, 0)
    fila.update(semilla=7, evolucion=1, modo="autonomo", generacion=1, ticks=960)
    registro.cerrar_generacion(fila, 960, [mejor])
    assert armar_boletin(registro)["subtitulo"].startswith(
        "Modo autónomo + deslizar · fortalezas móviles · con evolución")

    monkeypatch.setattr(SimulationConfig, "FORTALEZAS_MOVILES", False)
    assert main._ruta_csv_por_defecto(3, True) == str(Path("results") / "corrida_s3_autonomo_deslizar_evolucion.csv")
    assert "Fortalezas" not in dict(datos_de_la_generacion(1, [], SimpleNamespace(food_items=[]), 0))
    assert "fortalezas" not in armar_boletin(registro)["subtitulo"]


def test_experimento_pasa_el_flag_y_lo_nombra(monkeypatch, tmp_path):
    import experimento  # noqa: E402
    comandos = []

    def correr(comando, **_):
        comandos.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(experimento.subprocess, "run", correr)
    resultado = experimento._correr(1, "autonomo", True, 10, tmp_path, deslizar=True, moviles=True)
    assert "--fortalezas-moviles" in comandos[0]
    assert resultado["csv"].name == "corrida_s1_autonomo_deslizar_fortalezas_moviles_evolucion.csv"
    experimento._correr(1, "autonomo", False, 10, tmp_path)
    assert "--fortalezas-moviles" not in comandos[1]

    assert "**Fortalezas móviles:**" in experimento.resumen_markdown([], [], "", moviles=True)
    assert "Fortalezas móviles" not in experimento.resumen_markdown([], [], "")


def test_cada_mapa_de_calor_guarda_las_fortalezas_de_su_generacion(monkeypatch, capsys):
    finales = []
    monkeypatch.setattr(main, "mostrar_pantalla_final", lambda *args: finales.append(args))
    _correr_adentro(monkeypatch, capsys, "autonomo", True, moviles=True)
    world, registro = finales[0][4], finales[0][-1]
    assert registro.calor_gen1["fortalezas"] == [CHICA_GEN1, GRANDE_GEN1]
    assert registro.calor_ultima["fortalezas"] == [world.small_fortress_pos, world.large_fortress_pos]
    assert registro.calor_ultima["fortalezas"] != registro.calor_gen1["fortalezas"]
    # Son copias: lo que haga el mundo después no las cambia
    assert registro.calor_ultima["fortalezas"][0] is not world.small_fortress_pos
