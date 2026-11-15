"""
Ecosistema Evolutivo IA - Archivo principal simplificado.
"""

import pygame
import os
import time
import sys
import random
import statistics as _stats
import argparse
import csv

import numpy as np

from config import SimulationConfig
from src.world.world import World
from src.agents.advanced_agent import AdvancedAgent
from src.evolution.genetic_algorithm import GeneticAlgorithm
from src.ui.renderer import SpriteManager, ParticleSystem, dibujar_mundo
from src.ui.stats import StatsPanel
from src.ui.popup import SummaryPopup
from src.ui.pantalla_final import mostrar_pantalla_final
from src.analytics.learning_monitor import LearningMonitor

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Ubicación de los agentes (spec MODO_GUIADO_Y_AUTONOMO, decisión 23): los criterios que estaban
# repartidos entre el algoritmo genético y tres funciones de este archivo, juntos
RADIO_LIBRE = 35            # Distancia mínima a obstáculos, estanque, perímetro y manzanas
SEPARACION_AGENTES = 32     # Dos agentes no arrancan a menos de esto, en x y en y
PASO_DIRECCION = 20         # Una dirección está libre si a esta distancia no hay obstáculo
INTENTOS_POR_AGENTE = 500
GRILLA_DE_RESPALDO = [(x, y) for x in range(100, 801, 100) for y in range(100, 601, 100)]
    
    
def _lugar_libre(world, x, y, ubicados):
    """True si un agente puede arrancar en (x, y): fuera de fortalezas, obstáculos, perímetro y
    estanque, lejos de los agentes ya ubicados y de las manzanas, y con una dirección libre."""
    if world._is_inside_fortress(x, y):
        return False
    if any(obstacle.collides_with(x, y, RADIO_LIBRE) for obstacle in world.obstacles):
        return False
    # Caja centrada en el agente: la del genético iba de (x, y) hacia abajo y a la derecha, y dejaba
    # agentes con medio cuerpo en el estanque por arriba o por la izquierda
    if any(objeto.collides_with(x - RADIO_LIBRE, y - RADIO_LIBRE, 2 * RADIO_LIBRE, 2 * RADIO_LIBRE)
           for objeto in world.perimeter_obstacles + world.pond_obstacles):
        return False
    if any(abs(otro.x - x) < SEPARACION_AGENTES and abs(otro.y - y) < SEPARACION_AGENTES
           for otro in ubicados):
        return False
    if any(not food['eaten'] and ((x - food['x'])**2 + (y - food['y'])**2)**0.5 < RADIO_LIBRE
           for food in world.food_items):
        return False
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            test_x, test_y = x + dx * PASO_DIRECCION, y + dy * PASO_DIRECCION
            if (0 <= test_x < world.screen_width and 0 <= test_y < world.screen_height
                    and not any(obstacle.collides_with(test_x, test_y, PASO_DIRECCION)
                                for obstacle in world.obstacles)):
                return True
    return False


def _ubicar_agentes(world, agents):
    """Ubica a todos los agentes, con el mapa de la generación ya regenerado (DIAG-29).
    
    Para cada uno prueba posiciones al azar; si ninguna sirve, la grilla de respaldo; si tampoco,
    (100, 100). Las dos salidas de emergencia avisan por consola.
    """
    ubicados = []
    for agent in agents:
        lugar = None
        for _ in range(INTENTOS_POR_AGENTE):
            x, y = random.randint(50, 900), random.randint(50, 750)
            if _lugar_libre(world, x, y, ubicados):
                lugar = (x, y)
                break
        if lugar is None:
            lugar = next(((x, y) for x, y in GRILLA_DE_RESPALDO if _lugar_libre(world, x, y, ubicados)),
                         (100, 100))
            print(f"⚠️ No se encontró lugar al azar para el agente {agent.id}: va a {lugar}")
        agent.x, agent.y = float(lugar[0]), float(lugar[1])
        ubicados.append(agent)


# Columnas del CSV de cada corrida, en este orden (spec MEDIR_ANTES_DE_TOCAR, decisión 6;
# edad_prom: spec MODO_GUIADO_Y_AUTONOMO, decisión 28)
COLUMNAS_CSV = [
    "semilla", "evolucion", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "edad_prom", "distancia_prom", "diversidad",
    "arboles_cortados", "llave_roja", "puerta_madera", "llave_dorada", "puerta_hierro", "cofre",
]


def _leer_argumentos(argv):
    """Lee los flags de la línea de comando. Sin flags, mandan los valores de config.py."""
    parser = argparse.ArgumentParser(
        description="Ecosistema Evolutivo IA: corre la simulación y deja un CSV con una fila por generación.",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="Muestra esta ayuda y sale.")
    parser.add_argument("--sin-ventana", action="store_true",
                        help="Corre sin abrir ventana (más rápido). Pisa HEADLESS_MODE de config.py.")
    parser.add_argument("--generaciones", type=int, metavar="N",
                        help="Cantidad de generaciones. Pisa MAX_GENERATIONS de config.py.")
    parser.add_argument("--semilla", type=int, metavar="S",
                        help="Semilla del azar, para repetir una corrida. Sin ella se sortea una y se imprime.")
    parser.add_argument("--sin-evolucion", action="store_true",
                        help="Línea base: cada generación arranca con cerebros al azar y no hereda nada.")
    parser.add_argument("--csv", metavar="RUTA",
                        help="Dónde escribir el CSV. Por defecto, results/corrida_s<semilla>_<evolucion|sin_evolucion>.csv.")
    args = parser.parse_args(argv)
    if args.generaciones is not None and args.generaciones < 1:
        parser.error("--generaciones tiene que ser 1 o más")
    if args.semilla is not None and not 0 <= args.semilla < 2**32:
        parser.error("--semilla tiene que estar entre 0 y 4294967295")
    return args


def _fila_csv(semilla, evolucion, generacion, ticks, agents, world, learning_monitor):
    """Arma la fila del CSV de una generación. Espera el fitness ya calculado en cada agente.

    Hace las mismas cuentas que el reporte por consola del final de generación. Los decimales van
    redondeados a 4 para que dos corridas con la misma semilla den el mismo archivo byte a byte.
    Las columnas del puzzle son el estado del mundo, que se acumula entre generaciones.
    """
    fitness = [float(agent.fitness) for agent in agents]
    manzanas = [agent.food_eaten for agent in agents]
    arboles_cortados = len([tree for tree in world.trees if tree.is_cut]) if hasattr(world, 'trees') else 0
    fila = [
        semilla,
        int(evolucion),
        generacion,
        ticks,
        sum(fitness) / len(fitness),
        max(fitness),
        min(fitness),
        _stats.pstdev(fitness),
        sum(manzanas) / len(manzanas),
        max(manzanas),
        len([agent for agent in agents if agent.alive]),
        sum(agent.age for agent in agents) / len(agents),
        sum(agent.distance_traveled for agent in agents) / len(agents),
        learning_monitor.calculate_diversity(agents),
        arboles_cortados,
        int(bool(world.red_key_collected)),
        int(bool(world.door and world.door.is_open)),
        int(bool(world.gold_key_collected)),
        int(bool(world.door_iron and world.door_iron.is_open)),
        int(bool(world.chest and world.chest.is_open)),
    ]
    return [round(float(valor), 4) if isinstance(valor, float) else valor for valor in fila]


def _ticks_de_generacion(config, generacion):
    """Ticks que dura una generación: con tiempo adaptativo, se alarga cada TICKS_INCREMENT_FREQUENCY generaciones."""
    if not config.ADAPTIVE_TIME_ENABLED:
        return config.BASE_TICKS
    incrementos_aplicados = (generacion - 1) // config.TICKS_INCREMENT_FREQUENCY
    return config.BASE_TICKS + (config.TICKS_INCREMENT_AMOUNT * incrementos_aplicados)


def _imprimir_fin_de_generacion(generation, tick, agents, alive_agents, world, learning_monitor,
                                simulation_start_time):
    """Reporte por consola del fin de una generación. Solo lee: espera el fitness ya calculado.

    alive_agents son los vivos al empezar el último tick; la tasa de supervivencia los vuelve a contar.
    """
    # Calcular tiempo acumulado desde el inicio de la simulación
    elapsed_time = time.time() - simulation_start_time
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    print(f"\n🧬 Generación {generation} terminada")
    print(f"   - Agentes vivos: {len(alive_agents)}")
    print(f"   - Segundos: {tick/60:.1f}")

    # Contar árboles cortados (estado del mundo, que se acumula entre generaciones)
    trees_cut_this_generation = 0
    if hasattr(world, 'trees'):
        trees_cut_this_generation = len([tree for tree in world.trees if tree.is_cut])

    # Estadísticas de puzzle (llaves, puertas, cofre)
    red_key_status = "LLAVE RECOGIDA" if world.red_key_collected else "NO RECOGIDA"
    gold_key_status = "LLAVE RECOGIDA" if world.gold_key_collected else "NO RECOGIDA"

    door_status = "PUERTA ABIERTA" if world.door and world.door.is_open else "PUERTA CERRADA"
    iron_door_status = "PUERTA ABIERTA" if world.door_iron and world.door_iron.is_open else "PUERTA CERRADA"

    chest_status = "COFRE ABIERTO" if world.chest and world.chest.is_open else "COFRE CERRADO"

    alive_agents_for_stats = [a for a in agents if a.alive]
    avg_fitness = sum(agent.fitness for agent in agents) / len(agents)
    max_fitness = max(agent.fitness for agent in agents)
    min_fitness = min(agent.fitness for agent in agents)
    avg_age = sum(agent.age for agent in agents) / len(agents)
    avg_food = sum(agent.food_eaten for agent in agents) / len(agents)
    max_food = max(agent.food_eaten for agent in agents)

    # Calcular diversidad genética
    diversity = learning_monitor.calculate_diversity(agents)

    # ESTANDARIZAR LOGS - Siempre el mismo formato y orden
    print(f"   📊 FITNESS:")
    print(f"      - Promedio: {avg_fitness:.1f}/100")
    print(f"      - Máximo: {max_fitness:.1f}/100")
    print(f"      - Mínimo: {min_fitness:.1f}/100")
    print(f"   🍎 COMIDA:")
    print(f"      - Promedio: {avg_food:.1f}")
    print(f"      - Máximo: {max_food}")
    print(f"   ⏱️ SUPERVIVENCIA:")
    print(f"      - Tasa: {len(alive_agents_for_stats)/len(agents)*100:.1f}%")
    print(f"      - Tiempo promedio: {avg_age/60/60:.1f} min")
    print(f"   🧬 DIVERSIDAD GENÉTICA: {diversity:.4f}")
    print(f"   🧩 PUZZLE:")
    print(f"      - Llave roja: {red_key_status}")
    print(f"      - Llave dorada: {gold_key_status}")
    print(f"      - Puerta madera: {door_status}")
    print(f"      - Puerta hierro: {iron_door_status}")
    print(f"      - Cofre: {chest_status}")
    print(f"      - Árboles cortados: {trees_cut_this_generation}")
    print(f"   - ⏱️ Tiempo real acumulado: {elapsed_minutes}m {elapsed_seconds}s")


def _datos_del_popup(generation, tick, agents, alive_agents, world, learning_monitor):
    """Datos del cuadro de resumen de una generación. Solo lee: espera el fitness ya calculado."""
    alive_agents_for_stats = [a for a in agents if a.alive]
    trees_cut_this_generation = 0
    if hasattr(world, 'trees'):
        trees_cut_this_generation = len([tree for tree in world.trees if tree.is_cut])
    return {
        'generation': generation,
        'avg_fitness': sum(agent.fitness for agent in agents) / len(agents),
        'max_fitness': max(agent.fitness for agent in agents),
        'avg_age': sum(agent.age for agent in agents) / len(agents),
        'avg_food': sum(agent.food_eaten for agent in agents) / len(agents),
        'avg_energy': (sum(agent.energy for agent in alive_agents_for_stats) / len(alive_agents_for_stats)
                       if alive_agents_for_stats else 0),
        'avg_exploration': sum(agent.distance_traveled for agent in agents) / len(agents),
        'survival_rate': len(alive_agents) / len(agents) * 100,
        'avg_movement_skill': sum(agent.get_movement_skill() for agent in agents) / len(agents),
        'avg_food_skill': sum(agent.get_food_skill() for agent in agents) / len(agents),
        'avg_energy_skill': sum(agent.get_energy_skill() for agent in agents) / len(agents),
        'trees_cut': trees_cut_this_generation,
        # Datos del puzzle
        'red_key_collected': world.red_key_collected,
        'gold_key_collected': world.gold_key_collected,
        'doors_opened': (1 if world.door and world.door.is_open else 0) + (1 if world.door_iron and world.door_iron.is_open else 0),
        'chest_opened': world.chest.is_open if world.chest else False,
        'total_agents': len(agents),
        'alive_count': len(alive_agents_for_stats),
        'diversity': learning_monitor.calculate_diversity(agents),
        'generation_time': 0,  # Se puede calcular si es necesario
        'generation_time_ticks': tick  # Tiempo en ticks de esta generación
    }


def main(argv=None):
    """Punto de entrada: lee los flags, siembra el azar y corre la simulación escribiendo el CSV."""
    # Antes del primer print: con la salida redirigida a un archivo, Windows usa cp1252 y el
    # primer emoji tira UnicodeEncodeError (DIAG-25)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    args = _leer_argumentos(argv)
    # Se pisan en la clase, no en una instancia: la pantalla final lee SimulationConfig directo
    if args.sin_ventana:
        SimulationConfig.HEADLESS_MODE = True
    if args.generaciones is not None:
        SimulationConfig.MAX_GENERATIONS = args.generaciones

    # Sin --semilla se sortea una, se imprime y queda en el CSV: cualquier corrida se puede repetir
    semilla = args.semilla if args.semilla is not None else random.SystemRandom().randrange(1_000_000)
    random.seed(semilla)
    np.random.seed(semilla)
    evolucion = not args.sin_evolucion
    print(f"🎲 Semilla: {semilla} ({'con' if evolucion else 'sin'} evolución)")

    ruta_csv = args.csv or os.path.join(
        "results", f"corrida_s{semilla}_{'evolucion' if evolucion else 'sin_evolucion'}.csv")
    if os.path.exists(ruta_csv):
        print(f"⚠️ El CSV ya existe y se va a pisar: {ruta_csv}")
    os.makedirs(os.path.dirname(ruta_csv) or ".", exist_ok=True)

    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.writer(archivo_csv)
        escritor.writerow(COLUMNAS_CSV)

        def escribir_fila(fila):
            # Se vacía en cada generación: una corrida cortada deja sus generaciones completas
            escritor.writerow(fila)
            archivo_csv.flush()

        try:
            _simular(semilla, evolucion, escribir_fila)
        finally:
            print(f"📄 CSV de la corrida: {ruta_csv}")


def _simular(semilla, evolucion, escribir_fila):
    """Corre la simulación. Con evolucion=False, cada generación arranca con cerebros al azar."""
    print("🎨 Ecosistema Evolutivo IA")
    AdvancedAgent.reiniciar_ids()  # los ids van de 1 en cada corrida (decisión 24)
    
    
    # Configuración centralizada
    config = SimulationConfig()
    config.print_config()  # Mostrar configuración actual
    
    # Obtener parámetros de la configuración
    screen_width = config.SCREEN_WIDTH
    screen_height = config.SCREEN_HEIGHT
    max_generations = config.MAX_GENERATIONS
    target_fps = 999999 if config.HEADLESS_MODE else config.TARGET_FPS
    
    # Inicializar Pygame
    pygame.init()
    if not config.HEADLESS_MODE:
        # Crear ventana de visualización (tamaño deseado)
        display_screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Ecosistema Evolutivo IA")
        
        # Crear superficie de renderizado (tamaño base fijo)
        render_surface = pygame.Surface((1200, 800))
        
        # Calcular factor de escalado
        scale_x = screen_width / 1200.0
        scale_y = screen_height / 800.0
        scale_factor = min(scale_x, scale_y)  # Usar el menor para mantener proporciones
        
        print(f"🎨 Factor de escalado: {scale_factor:.2f}x")
    else:
        display_screen = None
        render_surface = None
        scale_factor = 1.0
        print("🚀 MODO HEADLESS ACTIVADO - Sin render")
    clock = pygame.time.Clock()
    
    # Crear fuentes una vez (cache para mejor rendimiento)
    pause_font = pygame.font.Font(None, 24) if not config.HEADLESS_MODE else None
    
    # Crear sistemas de sprites y partículas
    sprite_manager = SpriteManager()
    particle_system = ParticleSystem()
    graves = []  # Tumbas persistentes hasta la próxima generación
    dead_ids = set()  # Para detectar muertes nuevas sin duplicar tumbas
    
    # Crear cuadro de resumen
    summary_popup = SummaryPopup(screen_width, screen_height)
    fitness_history = []  # Historial de fitness para el gráfico
    
    # Crear monitor de aprendizaje
    learning_monitor = LearningMonitor()
    
    # Crear mundo (sistema original) con cantidad de comida configurable
    world = World(config.get_game_area_width(), screen_height, config.FOOD_COUNT)  # Usar área de juego dinámica
    
    # Crear algoritmo genético con configuración
    ga = GeneticAlgorithm(**config.get_genetic_params())
    
    # Crear población inicial y ubicarla en el mundo
    agents = ga._create_random_population()
    _ubicar_agentes(world, agents)
    
    # Crear panel de estadísticas (más alto)
    stats_panel = StatsPanel(screen_width - config.get_stats_panel_width(), 10, config.get_stats_panel_width() - 10, 300)  # Panel dinámico
    
    print(f"✅ {len(agents)} agentes avanzados creados")
    print(f"✅ {len(world.food_items)} piezas de comida generadas")
    print("🎮 CONTROLES:")
    print("   ESC - Salir")
    print("   ESPACIO - Pausar/Reanudar")
    print("   +/= - Zoom IN (agrandar ventana)")
    print("   - - Zoom OUT (achicar ventana)")
    
    # Tiempo de inicio de la simulación
    simulation_start_time = time.time()
    
    # Bucle principal
    running = True
    paused = False
    generation = 1
    # Calcular tiempo máximo adaptativo con incremento gradual
    max_ticks_per_generation = _ticks_de_generacion(config, generation)
    print(f"🎮 Generación {generation} iniciada ⏱️ {max_ticks_per_generation} ticks")
    tick = 0
    ticks_totales = 0  # Tiempo simulado: los ticks de todas las generaciones (DIAG-15)
    
    # Sistema de comandos
    
    
    # Optimizaciones de rendimiento
    print(f"⚡ Optimizaciones de rendimiento activadas:")
    print(f"   - FPS objetivo: {target_fps}")
    
    while running and generation <= max_generations:
        # Manejar eventos (solo si no está en modo headless)
        if not config.HEADLESS_MODE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Manejar clicks en el popup de resumen
                    if event.button == 1:  # Click izquierdo
                        mouse_pos = event.pos
                        if summary_popup.handle_click(mouse_pos):
                            pass  # El popup se cerró automáticamente
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        # Zoom in
                        screen_width = min(screen_width + 100, 1600)
                        screen_height = min(screen_height + 67, 1067)
                        display_screen = pygame.display.set_mode((screen_width, screen_height))
                        
                        # Recalcular factor de escalado
                        scale_x = screen_width / 1200.0
                        scale_y = screen_height / 800.0
                        scale_factor = min(scale_x, scale_y)
                        
                        print(f"🔍 Zoom IN: {screen_width}x{screen_height} (factor: {scale_factor:.2f}x)")
                    elif event.key == pygame.K_MINUS:
                        # Zoom out
                        screen_width = max(screen_width - 100, 800)
                        screen_height = max(screen_height - 67, 533)
                        display_screen = pygame.display.set_mode((screen_width, screen_height))
                        
                        # Recalcular factor de escalado
                        scale_x = screen_width / 1200.0
                        scale_y = screen_height / 800.0
                        scale_factor = min(scale_x, scale_y)
                        
                        print(f"🔍 Zoom OUT: {screen_width}x{screen_height} (factor: {scale_factor:.2f}x)")
        else:
            # En modo headless, avanzar automáticamente
            paused = False
        
        if not paused:
            # Actualizar agentes (optimizado)
            alive_agents = [a for a in agents if a.alive]
            
            for agent in alive_agents:
                decisions = agent.decide(world, alive_agents, sprite_manager)
                agent.act(decisions, world, alive_agents, tick)
                
                # Sistema de corte de árboles
                if config.TREE_CUTTING_ENABLED:
                    # Intentar agarrar hacha
                    agent._try_pickup_axe(world)
                    
                    # Intentar cortar árbol
                    agent._try_cut_tree(world, tick)
                
                # Sistema de fortalezas/llaves/puertas/cofre
                if config.FORTRESSES_ENABLED:
                    # Intentar recoger llaves
                    agent._try_pickup_key(world, generation)
                    
                    # Intentar golpear puertas
                    agent._try_hit_door(world, tick)
                    
                    # Intentar abrir cofre
                    if agent._try_open_chest(world):
                        # Antes de salir, la fila de esta generación (parcial), con cofre = 1
                        for otro in agents:
                            otro._calculate_fitness()
                        escribir_fila(_fila_csv(semilla, evolucion, generation, tick, agents, world, learning_monitor))
                        ticks_totales += tick  # La generación parcial también cuenta (DIAG-15)

                        # ¡COFRE ABIERTO! Mostrar pantalla de FIN
                        print(f"\n🏆 ¡¡¡COFRE ABIERTO!!! 🏆")
                        print(f"🎯 Agente {agent.id} ha completado la misión en la generación {generation}")
                        print(f"⏱️ Segundos: {tick/60:.1f}")
                        mostrar_pantalla_final(render_surface, generation, tick, agents, world, learning_monitor, screen_width, screen_height, display_screen, sprite_manager, particle_system, ticks_totales, cofre_abierto=True)
                        return
        
        # Registrar tumbas para agentes que acaban de morir (sin colisión)
        if not paused:
            for agent in agents:
                if not agent.alive and agent.id not in dead_ids:
                    graves.append({'x': int(agent.x), 'y': int(agent.y)})
                    dead_ids.add(agent.id)

        # Actualizar sistema de corte de árboles (solo si no está pausado)
        if not paused and config.TREE_CUTTING_ENABLED:
            world.update_tree_cutting_status()
        
        # Generar red_key en gen 11+ si no existe (solo una vez por generación)
        if config.FORTRESSES_ENABLED and generation >= config.RED_KEY_SPAWN_GEN and not world.red_key:
            world._generate_red_key(generation)
        
        # Actualizar mundo (solo si no está pausado)
        if not paused:
            world.update()
            tick += 1
        
        # Verificar si todos murieron o se acabó el tiempo
        if len(alive_agents) == 0 or tick >= max_ticks_per_generation:
            # Fitness de todos los agentes, antes del reporte, la fila del CSV y la evolución
            for agent in agents:
                agent._calculate_fitness()
            _imprimir_fin_de_generacion(generation, tick, agents, alive_agents, world, learning_monitor,
                                        simulation_start_time)

            # Fila del CSV, antes de la pantalla final (que con ventana espera una tecla)
            escribir_fila(_fila_csv(semilla, evolucion, generation, tick, agents, world, learning_monitor))
            ticks_totales += tick  # Al tiempo simulado (DIAG-15)

            # Datos del cuadro de resumen, y el fitness promedio al historial del gráfico
            generation_data = _datos_del_popup(generation, tick, agents, alive_agents, world, learning_monitor)
            fitness_history.append(generation_data['avg_fitness'])
            
            # Registrar datos en el monitor de aprendizaje
            gen_data = learning_monitor.record_generation(generation, agents, world)
            
            # Clustering (después de crear gen_data)
            if gen_data and gen_data.get('cluster_stats'):
                learning_monitor._print_cluster_summary(gen_data['cluster_stats'])
            
            # Mostrar análisis detallado cada 5 generaciones (sin gen 1 para evitar duplicados)
            if generation % 5 == 0 and generation != 1:
                learning_monitor.print_generation_summary(gen_data)
            
            # Detectar patrones de aprendizaje cada 10 generaciones
            if generation % 10 == 0:
                learning_monitor.detect_learning_patterns()
            
            # Mostrar cuadro de resumen
            summary_popup.show(generation_data, fitness_history)
            
            if generation >= max_generations:
                print("🏁 Límite de generaciones alcanzado sin abrir el cofre. Mostrando resumen final...")
                mostrar_pantalla_final(render_surface, generation, tick, agents, world, learning_monitor, screen_width, screen_height, display_screen, sprite_manager, particle_system, ticks_totales, cofre_abierto=False)
                return

            # Evolucionar. La línea base (--sin-evolucion) arranca de cero: cerebros al azar, sin herencia
            if evolucion:
                agents = ga.evolve(agents, generation)
            else:
                agents = ga._create_random_population()
            
            # El mapa se regenera y recién ahí se ubican los agentes (DIAG-29)
            world.reset_food()
            _ubicar_agentes(world, agents)
            world.tick = 0
            tick = 0
            generation += 1

            # Limpiar tumbas al iniciar nueva generación
            graves.clear()
            dead_ids.clear()
            
            # Recalcular tiempo máximo para la nueva generación con incremento gradual
            max_ticks_per_generation = _ticks_de_generacion(config, generation)
            
            print(f"✅ Nueva generación {generation} creada ⏱️ {max_ticks_per_generation/60} seg")
        
        # Renderizar (solo si no está en modo headless)
        if not config.HEADLESS_MODE:
            dibujar_mundo(render_surface, world, sprite_manager, tick)
            
            # Actualizar sistema de partículas (cada 2 frames para mejor rendimiento)
            if tick % 2 == 0:
                particle_system.update()
            
            # Limpiar objetivos de agentes muertos para mejor rendimiento
            for agent in agents:
                if not agent.alive and hasattr(agent, 'target_food'):
                    agent.target_food = None
            
            # Dibujar tumbas antes de los agentes (decoración sin colisión)
            if graves:
                grave_sprite = sprite_manager.get_environment_sprite('grave')
                if grave_sprite:
                    for g in graves:
                        rect = grave_sprite.get_rect(center=(g['x'], g['y']))
                        render_surface.blit(grave_sprite, rect)

            # Dibujar agentes
            for agent in agents:
                agent.draw(render_surface, tick, sprite_manager, particle_system)
            
            # Dibujar partículas
            particle_system.draw(render_surface)
            
            # Dibujar panel de estadísticas simplificado
            stats_panel.draw(render_surface, generation, agents, world, tick)
            
            # Dibujar cuadro de resumen (si está visible)
            summary_popup.draw(render_surface)
                        
            if paused and pause_font:
                pause_text = pause_font.render("PAUSADO - Presiona ESPACIO", True, (255, 0, 0))
                render_surface.blit(pause_text, (10, 40))
            
            # Escalar y mostrar la superficie renderizada
            scaled_surface = pygame.transform.scale(render_surface, (screen_width, screen_height))
            display_screen.blit(scaled_surface, (0, 0))
            
            # Actualizar pantalla
            pygame.display.flip()
        
        clock.tick(target_fps)  # Usar FPS objetivo
    
    pygame.quit()
    
    # Crear reporte final de aprendizaje
    print(f"\nSimulación completada - {generation-1} generaciones evolucionadas")
    learning_monitor.create_learning_report()


if __name__ == "__main__":
    main()
