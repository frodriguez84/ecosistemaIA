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
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork
from src.world.world import World
from src.world.obstacles import Obstacle, Axe
from src.evolution.genetic_algorithm import GeneticAlgorithm
from src.ui.renderer import SpriteManager, ParticleSystem
from src.ui.stats import StatsPanel
from src.ui.popup import SummaryPopup
from src.analytics.learning_monitor import LearningMonitor
from src.analytics.clustering import BehaviorClusterer

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def find_safe_position(world, agents, radius=16):
    """Encuentra una posición segura para un agente, evitando todos los obstáculos."""
    
    
    max_attempts = 100
    grass_area_width = 960  # Área de pasto válida
    
    for attempt in range(max_attempts):
        # Generar posición aleatoria en área de pasto
        x = random.randint(radius, grass_area_width - radius)
        y = random.randint(radius, 800 - radius)
        
        # Verificar colisiones con obstáculos
        collision = False
        
        # Verificar colisión con obstáculos normales
        for obstacle in world.obstacles:
            if obstacle.collides_with(x, y, radius):
                collision = True
                break
        
        # Verificar colisión con perímetro
        if not collision:
            for perimeter_obj in world.perimeter_obstacles:
                if perimeter_obj.collides_with(x, y, radius * 2, radius * 2):
                    collision = True
                    break
        
        # Verificar colisión con estanques
        if not collision:
            for pond_obj in world.pond_obstacles:
                if pond_obj.collides_with(x, y, radius * 2, radius * 2):
                    collision = True
                    break
        
        # Verificar colisión con fortalezas (IMPORTANTE!)
        if not collision and hasattr(world, '_is_inside_fortress'):
            if world._is_inside_fortress(x, y):
                collision = True
        
        # Verificar colisión con otros agentes
        if not collision:
            for agent in agents:
                if agent.alive and abs(agent.x - x) < radius * 2 and abs(agent.y - y) < radius * 2:
                    collision = True
                    break
        
        # Si no hay colisión, esta es una posición segura
        if not collision:
            return (x, y)
    
    # Si no se encuentra posición segura después de 100 intentos, usar posición por defecto
    print("⚠️ No se pudo encontrar posición segura, usando posición por defecto")
    return (100, 100)


def fix_agent_positions(world, agents):
    """Detecta y corrige agentes en posiciones inválidas."""
    fixed_count = 0
    
    for agent in agents:
        if not agent.alive:
            continue
            
        # Verificar si el agente está en posición inválida
        needs_fixing = False
        
        # Verificar colisión con obstáculos normales
        for obstacle in world.obstacles:
            if obstacle.collides_with(agent.x, agent.y, agent.radius):
                needs_fixing = True
                break
        
        # Verificar colisión con perímetro
        if not needs_fixing:
            for perimeter_obj in world.perimeter_obstacles:
                if perimeter_obj.collides_with(agent.x, agent.y, agent.radius * 2, agent.radius * 2):
                    needs_fixing = True
                    break
        
        # Verificar colisión con estanques
        if not needs_fixing:
            for pond_obj in world.pond_obstacles:
                if pond_obj.collides_with(agent.x, agent.y, agent.radius * 2, agent.radius * 2):
                    needs_fixing = True
                    break
        
        # Verificar colisión con fortalezas (IMPORTANTE!)
        if not needs_fixing and hasattr(world, '_is_inside_fortress'):
            if world._is_inside_fortress(agent.x, agent.y):
                needs_fixing = True
        
        # Si necesita corrección, mover a posición segura
        if needs_fixing:
            safe_x, safe_y = find_safe_position(world, agents, agent.radius)
            agent.x = safe_x
            agent.y = safe_y
            fixed_count += 1
            
    
    if fixed_count > 0:
        pass  # Se removió el print para reducir spam en consola
        


# Columnas del CSV de cada corrida, en este orden (spec MEDIR_ANTES_DE_TOCAR, decisión 6)
COLUMNAS_CSV = [
    "semilla", "evolucion", "generacion", "ticks",
    "fitness_prom", "fitness_max", "fitness_min", "fitness_desvio",
    "manzanas_prom", "manzanas_max", "vivos", "distancia_prom", "diversidad",
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


def main(argv=None):
    """Punto de entrada: lee los flags, siembra el azar y corre la simulación escribiendo el CSV."""
    # Antes del primer print: con la salida redirigida a un archivo, Windows usa cp1252 y el
    # primer emoji tira UnicodeEncodeError (DIAG-25)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    args = _leer_argumentos(argv)
    # Se pisan en la clase, no en una instancia: show_final_screen lee SimulationConfig directo
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
    
    
    # Configuración centralizada
    config = SimulationConfig()
    config.print_config()  # Mostrar configuración actual
    
    # Obtener parámetros de la configuración
    screen_width = config.SCREEN_WIDTH
    screen_height = config.SCREEN_HEIGHT
    population_size = config.POPULATION_SIZE
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
    ga.world = world  # Pasar referencia al mundo
    
    # Crear población inicial
    agents = ga._create_random_population()
    
    # Reposicionar agentes que spawnearon dentro de fortalezas O sobre obstáculos
    if config.FORTRESSES_ENABLED:
        
        for agent in agents:
            # Verificar si está dentro de fortalezas O sobre obstáculos
            needs_repositioning = (world._is_inside_fortress(agent.x, agent.y) or 
                                  any(obstacle.collides_with(agent.x, agent.y, agent.radius) 
                                      for obstacle in world.obstacles))
            
            if needs_repositioning:
                # Reposicionar fuera de fortalezas, obstáculos Y zona de estadísticas
                attempts = 0
                while attempts < 500:  # Más intentos para mayor seguridad
                    # Área de juego válida: solo pasto, excluyendo perímetro y panel de estadísticas
                    # Usar dimensiones escaladas dinámicamente
                    new_x = random.randint(20, config.get_grass_area_width() - 20)  # Solo área de pasto, evitando perímetro
                    new_y = random.randint(20, screen_height - 20)  # Evitando perímetro superior e inferior
                    
                    # Verificar que no esté en fortaleza Y no colisione con obstáculos Y no esté en perímetro Y no esté en estanque
                    if (not world._is_inside_fortress(new_x, new_y) and
                        not any(obstacle.collides_with(new_x, new_y, agent.radius) 
                               for obstacle in world.obstacles) and
                        not any(perimeter_obj.collides_with(new_x, new_y, agent.radius, agent.radius)
                               for perimeter_obj in world.perimeter_obstacles) and
                        not any(pond_obj.collides_with(new_x, new_y, agent.radius, agent.radius)
                               for pond_obj in world.pond_obstacles)):
                        agent.x = new_x
                        agent.y = new_y
                        break
                    attempts += 1
                
                # Si no se pudo reposicionar después de 500 intentos, usar posición segura
                if attempts >= 500:
                    # Buscar posición segura que no esté en estanque
                    safe_x, safe_y = 100, 100  # Posición por defecto
                    for test_x in [100, 200, 300, 400, 500, 600, 700, 800]:
                        for test_y in [100, 200, 300, 400, 500, 600]:
                            # Verificar que no esté en estanque
                            safe_position = True
                            for pond_obj in world.pond_obstacles:
                                if pond_obj.collides_with(test_x, test_y, agent.radius, agent.radius):
                                    safe_position = False
                                    break
                            if safe_position:
                                safe_x, safe_y = test_x, test_y
                                break
                        if safe_position:
                            break
                    
                    agent.x = safe_x
                    agent.y = safe_y
                    print(f"⚠️ Agente {agent.id} reposicionado a posición segura ({safe_x}, {safe_y})")
    
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
    if config.ADAPTIVE_TIME_ENABLED:
        # Calcular cuántos incrementos aplicar: cada TICKS_INCREMENT_FREQUENCY generaciones
        incrementos_aplicados = (generation - 1) // config.TICKS_INCREMENT_FREQUENCY
        max_ticks_per_generation = config.BASE_TICKS + (config.TICKS_INCREMENT_AMOUNT * incrementos_aplicados)
    else:
        max_ticks_per_generation = config.BASE_TICKS
    print(f"🎮 Generación {generation} iniciada ⏱️ {max_ticks_per_generation} ticks")
    tick = 0
    
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

                        # ¡COFRE ABIERTO! Mostrar pantalla de FIN
                        print(f"\n🏆 ¡¡¡COFRE ABIERTO!!! 🏆")
                        print(f"🎯 Agente {agent.id} ha completado la misión en la generación {generation}")
                        print(f"⏱️ Segundos: {tick/60:.1f}")
                        show_final_screen(render_surface, generation, tick, agents, world, learning_monitor, screen_width, screen_height, display_screen, sprite_manager, particle_system)
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
            # Calcular tiempo acumulado desde el inicio de la simulación
            elapsed_time = time.time() - simulation_start_time
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)
            
            print(f"\n🧬 Generación {generation} terminada")
            print(f"   - Agentes vivos: {len(alive_agents)}")
            print(f"   - Segundos: {tick/60:.1f}")
            
            
            # Contar árboles cortados en esta generación
            trees_cut_this_generation = 0
            if hasattr(world, 'trees'):
                trees_cut_this_generation = len([tree for tree in world.trees if tree.is_cut])
            
            # Estadísticas de puzzle (llaves, puertas, cofre)
            red_key_status = "LLAVE RECOGIDA" if world.red_key_collected else "NO RECOGIDA"
            gold_key_status = "LLAVE RECOGIDA" if world.gold_key_collected else "NO RECOGIDA"
            
            door_status = "PUERTA ABIERTA" if world.door and world.door.is_open else "PUERTA CERRADA"
            iron_door_status = "PUERTA ABIERTA" if world.door_iron and world.door_iron.is_open else "PUERTA CERRADA"
            
            chest_status = "COFRE ABIERTO" if world.chest and world.chest.is_open else "COFRE CERRADO"
            
            if agents:
                # Recalcular agentes vivos para las estadísticas
                alive_agents_for_stats = [a for a in agents if a.alive]
                
                # Calcular fitness de todos los agentes antes de las estadísticas
                for agent in agents:
                    agent._calculate_fitness()
                
                avg_fitness = sum(agent.fitness for agent in agents) / len(agents)
                max_fitness = max(agent.fitness for agent in agents)
                min_fitness = min(agent.fitness for agent in agents)
                avg_age = sum(agent.age for agent in agents) / len(agents)
                avg_food = sum(agent.food_eaten for agent in agents) / len(agents)
                max_food = max(agent.food_eaten for agent in agents)
                avg_energy = sum(agent.energy for agent in alive_agents_for_stats) / len(alive_agents_for_stats) if alive_agents_for_stats else 0
                
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
            else:
                avg_fitness = max_fitness = avg_age = avg_food = avg_energy = 0
                alive_agents_for_stats = []  # Lista vacía si no hay agentes
            
            # Fila del CSV, antes de la pantalla final (que con ventana espera una tecla)
            escribir_fila(_fila_csv(semilla, evolucion, generation, tick, agents, world, learning_monitor))

            # Preparar datos para el cuadro de resumen
            generation_data = {
                'generation': generation,
                'avg_fitness': avg_fitness,
                'max_fitness': max_fitness,
                'avg_age': avg_age,
                'avg_food': avg_food,
                'avg_energy': avg_energy,
                'avg_exploration': sum(agent.distance_traveled for agent in agents)/len(agents) if agents else 0,
                'survival_rate': len(alive_agents)/len(agents)*100 if agents else 0,
                'avg_movement_skill': sum(agent.get_movement_skill() for agent in agents) / len(agents) if agents else 0,
                'avg_food_skill': sum(agent.get_food_skill() for agent in agents) / len(agents) if agents else 0,
                'avg_obstacle_skill': sum(agent.get_obstacle_skill() for agent in agents) / len(agents) if agents else 0,
                'avg_energy_skill': sum(agent.get_energy_skill() for agent in agents) / len(agents) if agents else 0,
                'trees_cut': trees_cut_this_generation,
                # Datos del puzzle
                'red_key_collected': world.red_key_collected,
                'gold_key_collected': world.gold_key_collected,
                'doors_opened': (1 if world.door and world.door.is_open else 0) + (1 if world.door_iron and world.door_iron.is_open else 0),
                'chest_opened': world.chest.is_open if world.chest else False,
                'total_agents': len(agents),
                'alive_count': len(alive_agents_for_stats),
                'diversity': learning_monitor.calculate_diversity(agents) if hasattr(learning_monitor, 'calculate_diversity') else 0,
                'generation_time': 0,  # Se puede calcular si es necesario
                'generation_time_ticks': tick  # Tiempo en ticks de esta generación
            }
            
            # Añadir fitness promedio al historial
            fitness_history.append(avg_fitness)
            
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
                show_final_screen(render_surface, generation, tick, agents, world, learning_monitor, screen_width, screen_height, display_screen, sprite_manager, particle_system, mission_completed=False)
                return

            # Evolucionar. La línea base (--sin-evolucion) arranca de cero: cerebros al azar, sin herencia
            if evolucion:
                agents = ga.evolve(agents, generation)
            else:
                agents = ga._create_random_population()
            
            # SISTEMA DE DETECCIÓN Y CORRECCIÓN DE POSICIONES INVÁLIDAS
            print("🔍 Verificando posiciones de agentes...")
            fix_agent_positions(world, agents)
            
            # Reposicionar agentes que spawnearon dentro de fortalezas O sobre obstáculos (después de evolucionar)
            if config.FORTRESSES_ENABLED:
                
                for agent in agents:
                    # Verificar si está dentro de fortalezas O sobre obstáculos
                    needs_repositioning = (world._is_inside_fortress(agent.x, agent.y) or 
                                          any(obstacle.collides_with(agent.x, agent.y, agent.radius) 
                                              for obstacle in world.obstacles))
                    
                    if needs_repositioning:
                        # Reposicionar fuera de fortalezas, obstáculos Y zona de estadísticas
                        attempts = 0
                        while attempts < 500:  # Más intentos para mayor seguridad
                            # Área de juego válida: solo pasto, excluyendo perímetro y panel de estadísticas
                            # Usar dimensiones escaladas dinámicamente
                            new_x = random.randint(20, config.get_grass_area_width() - 20)  # Solo área de pasto, evitando perímetro
                            new_y = random.randint(20, screen_height - 20)  # Evitando perímetro superior e inferior
                            
                            # Verificar que no esté en fortaleza Y no colisione con obstáculos Y no esté en perímetro Y no esté en estanque
                            if (not world._is_inside_fortress(new_x, new_y) and
                                not any(obstacle.collides_with(new_x, new_y, agent.radius) 
                                       for obstacle in world.obstacles) and
                                not any(perimeter_obj.collides_with(new_x, new_y, agent.radius, agent.radius)
                                       for perimeter_obj in world.perimeter_obstacles) and
                                not any(pond_obj.collides_with(new_x, new_y, agent.radius, agent.radius)
                                       for pond_obj in world.pond_obstacles)):
                                agent.x = new_x
                                agent.y = new_y
                                break
                            attempts += 1
                        
                        # Si no se pudo reposicionar después de 500 intentos, usar posición segura
                        if attempts >= 500:
                            # Buscar posición segura que no esté en estanque
                            safe_x, safe_y = 100, 100  # Posición por defecto
                            for test_x in [100, 200, 300, 400, 500, 600, 700, 800]:
                                for test_y in [100, 200, 300, 400, 500, 600]:
                                    # Verificar que no esté en estanque
                                    safe_position = True
                                    for pond_obj in world.pond_obstacles:
                                        if pond_obj.collides_with(test_x, test_y, agent.radius, agent.radius):
                                            safe_position = False
                                            break
                                    if safe_position:
                                        safe_x, safe_y = test_x, test_y
                                        break
                                if safe_position:
                                    break
                            
                            agent.x = safe_x
                            agent.y = safe_y
                            print(f"⚠️ Agente {agent.id} reposicionado a posición segura ({safe_x}, {safe_y})")
            
            world.reset_food()
            world.tick = 0
            tick = 0
            generation += 1

            # Limpiar tumbas al iniciar nueva generación
            graves.clear()
            dead_ids.clear()
            
            # Recalcular tiempo máximo para la nueva generación con incremento gradual
            if config.ADAPTIVE_TIME_ENABLED:
                # Calcular cuántos incrementos aplicar: cada TICKS_INCREMENT_FREQUENCY generaciones
                incrementos_aplicados = (generation - 1) // config.TICKS_INCREMENT_FREQUENCY
                max_ticks_per_generation = config.BASE_TICKS + (config.TICKS_INCREMENT_AMOUNT * incrementos_aplicados)
            else:
                max_ticks_per_generation = config.BASE_TICKS
            
            print(f"✅ Nueva generación {generation} creada ⏱️ {max_ticks_per_generation/60} seg")
            
            # SISTEMA DE DETECCIÓN Y CORRECCIÓN DE POSICIONES INVÁLIDAS
            
            fix_agent_positions(world, agents)
        
        # Renderizar (solo si no está en modo headless)
        if not config.HEADLESS_MODE:
            render_surface.fill((40, 40, 60))  # Fondo azul oscuro
            
            # Dibujar fondo: pasto hasta el perímetro, agua después
            for x in range(0, 960, 16):  # Área de juego fija (1200 - 240 panel)
                for y in range(0, 800, 16):  # Alto fijo
                    if x < 1200:  # Todo el área de juego debe ser pasto
                        # Solo pasto con variación
                        grass_variant = 1 if (x // 16 + y // 16) % 2 == 0 else 2
                        grass_sprite = sprite_manager.get_environment_sprite('grass', grass_variant)
                        render_surface.blit(grass_sprite, (x, y))
            
            # Dibujar obstáculos con sprites
            for obstacle in world.obstacles:
                obstacle.draw(render_surface, sprite_manager, tick)
            
            # Dibujar perímetro decorativo
            for perimeter_obj in world.perimeter_obstacles:
                perimeter_obj.draw(render_surface, sprite_manager)
            
            # Dibujar estanque móvil
            for pond_obj in world.pond_obstacles:
                pond_obj.draw(render_surface, sprite_manager, tick)
            
            # Dibujar hacha si existe y no fue agarrada
            if config.TREE_CUTTING_ENABLED and world.axe and not world.axe['picked_up']:
                axe_sprite = sprite_manager.get_environment_sprite('axe')
                if axe_sprite:
                    # Efecto de brillo pulsante
                    glow_intensity = int(50 + 30 * abs(pygame.math.Vector2(1, 1).length() * 0.1 * tick % 1 - 0.5))
                    glow_color = (255, 255, 100 + glow_intensity)  # Amarillo brillante
                    
                    # Dibujar halo de brillo suave (sin fondo)
                    for i in range(3):
                        glow_radius = 15 + i * 5
                        glow_alpha = 30 - i * 8  # Más transparente
                        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surface, (*glow_color[:3], glow_alpha), 
                                        (glow_radius, glow_radius), glow_radius)
                        render_surface.blit(glow_surface, (world.axe['x'] - glow_radius, world.axe['y'] - glow_radius))
                    
                    # Dibujar hacha original con brillo sutil
                    render_surface.blit(axe_sprite, (world.axe['x'] - 10, world.axe['y'] - 10))
                    
                    # Añadir brillo sutil encima (sin fondo)
                    bright_overlay = pygame.Surface(axe_sprite.get_size(), pygame.SRCALPHA)
                    bright_overlay.fill((*glow_color[:3], 30))  # Muy transparente
                    bright_overlay.blit(axe_sprite, (0, 0), special_flags=pygame.BLEND_ADD)
                    render_surface.blit(bright_overlay, (world.axe['x'] - 10, world.axe['y'] - 10))
            
            # Dibujar manzanas (comida)
            for food in world.food_items:
                if not food['eaten']:
                    # Dibujar manzana con sprite
                    apple_sprite = sprite_manager.get_environment_sprite('apple')
                    render_surface.blit(apple_sprite, (int(food['x'] - 8), int(food['y'] - 8)))
            
            # Dibujar fortalezas, llaves, puertas y cofre (DESPUÉS de obstáculos para que se vean)
            if config.FORTRESSES_ENABLED:
                # Dibujar puertas (encima de los muros)
                if world.door:
                    world.door.draw(render_surface, sprite_manager, tick)
                if world.door_iron:
                    world.door_iron.draw(render_surface, sprite_manager, tick)
                
                # Dibujar cofre
                if world.chest:
                    world.chest.draw(render_surface, sprite_manager, tick)
                
                # Dibujar llaves
                if world.red_key and not world.red_key.collected:
                    # Efecto de halo brillante para red_key (igual que el hacha)
                    red_key_sprite = sprite_manager.get_environment_sprite('red_key')
                    if red_key_sprite:
                        # Efecto de brillo pulsante
                        glow_intensity = int(50 + 30 * abs(pygame.math.Vector2(1, 1).length() * 0.1 * tick % 1 - 0.5))
                        glow_color = (255, 100, 100 + glow_intensity)  # Rojo brillante
                        
                        # Dibujar halo de brillo suave (sin fondo)
                        for i in range(3):
                            glow_radius = 15 + i * 5
                            glow_alpha = 30 - i * 8  # Más transparente
                            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                            pygame.draw.circle(glow_surface, (*glow_color[:3], glow_alpha), 
                                            (glow_radius, glow_radius), glow_radius)
                            render_surface.blit(glow_surface, (world.red_key.x - glow_radius, world.red_key.y - glow_radius))
                        
                        # Dibujar red_key original con brillo sutil
                        world.red_key.draw(render_surface, sprite_manager, tick)
                        
                        # Añadir brillo sutil encima (sin fondo)
                        bright_overlay = pygame.Surface(red_key_sprite.get_size(), pygame.SRCALPHA)
                        bright_overlay.fill((*glow_color[:3], 30))  # Muy transparente
                        bright_overlay.blit(red_key_sprite, (0, 0), special_flags=pygame.BLEND_ADD)
                        render_surface.blit(bright_overlay, (world.red_key.x - 10, world.red_key.y - 10))
                    else:
                        # Fallback si no hay sprite
                        world.red_key.draw(render_surface, sprite_manager, tick)
                
                if world.gold_key and not world.gold_key.collected:
                    world.gold_key.draw(render_surface, sprite_manager, tick)
            
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
    
    # Guardar datos para análisis posterior (DESHABILITADO)
    # learning_monitor.save_data(f"learning_data_gen_{generation-1}.json")


def show_final_screen(render_surface, generation, tick, agents, world, learning_monitor, screen_width, screen_height, display_screen, sprite_manager, particle_system, mission_completed=True):
    """Muestra la pantalla de FIN con el resumen de resultados."""
    
       
    # Si estamos en modo headless, solo mostrar estadísticas por consola
    if SimulationConfig.HEADLESS_MODE:
        # Recalcular fitness de todos los agentes antes de mostrar estadísticas
        from config import SimulationConfig as Config
        for agent in agents:
            agent._calculate_fitness()
        
        alive_agents = [a for a in agents if a.alive]
        max_fitness = max(agent.fitness for agent in agents) if agents else 0.0
        
        # Calcular promedio de las últimas 3 generaciones (más representativo)
        if learning_monitor.generation_data and len(learning_monitor.generation_data) >= 3:
            last_gens = learning_monitor.generation_data[-3:]
            avg_fitness = sum(g.get('avg_fitness', 0) for g in last_gens) / len(last_gens)
        elif learning_monitor.generation_data:
            # Si hay menos de 3 generaciones, usar todas las disponibles
            avg_fitness = sum(g.get('avg_fitness', 0) for g in learning_monitor.generation_data) / len(learning_monitor.generation_data)
        else:
            # Fallback: usar promedio de la generación actual
            avg_fitness = sum(agent.fitness for agent in agents) / len(agents) if agents else 0.0
        
        if mission_completed:
            status_title = "¡MISIÓN COMPLETADA!"
            status_subtitle = "El cofre ha sido abierto por un agente evolutivo."
        else:
            status_title = "Simulación finalizada"
            status_subtitle = "Se alcanzó el límite de generaciones sin abrir el cofre."

        print(f"\n {status_title}")
        print(f"Generación: {generation}")
        print(f"Tiempo total: {tick // 60 // 60:.1f} minutos")
        print(f"Agentes vivos: {len(alive_agents)}")
        print(status_subtitle)
        print(f"Fitness promedio (últimas 3 gen): {avg_fitness:.1f}")
        print(f"Fitness máximo: {max_fitness:.1f}")
        return
    
    # Crear reporte final de aprendizaje
    learning_monitor.create_learning_report()
    
    # Calcular estadísticas finales
    alive_agents = [a for a in agents if a.alive]
    total_agents = len(agents)
    
    # Estadísticas de fitness
    fitness_values = [a.fitness for a in agents]
    max_fitness = max(fitness_values) if fitness_values else 0
    avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0
    
    # Estadísticas de comida
    food_eaten_values = [a.food_eaten for a in agents]
    max_food = max(food_eaten_values) if food_eaten_values else 0
    avg_food = sum(food_eaten_values) / len(food_eaten_values) if food_eaten_values else 0
    
    # Estadísticas de supervivencia
    survival_times = [a.age for a in agents]
    max_survival = max(survival_times) if survival_times else 0
    avg_survival = sum(survival_times) / len(survival_times) if survival_times else 0
    
    # Estadísticas de exploración
    exploration_values = [a.distance_traveled for a in agents]
    max_exploration = max(exploration_values) if exploration_values else 0
    avg_exploration = sum(exploration_values) / len(exploration_values) if exploration_values else 0
    
    # Estadísticas históricas de TODAS las generaciones
    if learning_monitor.generation_data:
        # Estadísticas de comida totales (solo promedio, no total)
        avg_food_all_gens = sum(gen_data['avg_food'] for gen_data in learning_monitor.generation_data) / len(learning_monitor.generation_data)
        
        # Estadísticas de supervivencia totales (convertir ticks a minutos)
        total_survival_all_gens = sum(gen_data['avg_age'] for gen_data in learning_monitor.generation_data) / 60 / 60  # ticks a minutos
        avg_survival_all_gens = sum(gen_data['avg_age'] for gen_data in learning_monitor.generation_data) / len(learning_monitor.generation_data) / 60 / 60
        
        # Estadísticas de exploración totales (convertir píxeles a metros/km)
        total_exploration_all_gens = sum(gen_data['avg_distance'] for gen_data in learning_monitor.generation_data)
        avg_exploration_all_gens = sum(gen_data['avg_distance'] for gen_data in learning_monitor.generation_data) / len(learning_monitor.generation_data)
        
        # Convertir exploración a metros (asumiendo 1 píxel = 1 cm)
        total_exploration_meters = total_exploration_all_gens / 100
        avg_exploration_meters = avg_exploration_all_gens / 100
    else:
        avg_food_all_gens = 0
        total_survival_all_gens = 0
        avg_survival_all_gens = 0
        total_exploration_meters = 0
        avg_exploration_meters = 0

    # Datos para Modo Compacto
    
    # Trayectoria de fitness: delta vs gen 1
    if learning_monitor.generation_data:
        initial_avg_fitness = learning_monitor.generation_data[0].get('avg_fitness', avg_fitness)
        fitness_delta = avg_fitness - initial_avg_fitness
        fitness_stdev = _stats.pstdev(fitness_values) if len(fitness_values) > 1 else 0.0
    else:
        initial_avg_fitness = avg_fitness
        fitness_delta = 0.0
        fitness_stdev = 0.0

    # Diversidad: inicial → mínima → final
    if learning_monitor.generation_data and any('diversity' in d for d in learning_monitor.generation_data):
        diversities = [d.get('diversity', 0) for d in learning_monitor.generation_data]
        diversity_initial = diversities[0]
        diversity_min = min(diversities)
        diversity_final = diversities[-1]
        convergence_flag = 'Sí' if diversity_min < (diversity_initial * 0.6) else 'No'
    else:
        diversity_initial = diversity_min = diversity_final = 0
        convergence_flag = 'N/A'

    # Hitos del puzzle (sobre historial)
    if learning_monitor.generation_data:
        total_gens = len(learning_monitor.generation_data)
        pct_red = int(100 * sum(1 for d in learning_monitor.generation_data if d.get('red_key_collected', False)) / total_gens)
        pct_gold = int(100 * sum(1 for d in learning_monitor.generation_data if d.get('gold_key_collected', False)) / total_gens)
        pct_doors = int(100 * sum(1 for d in learning_monitor.generation_data if d.get('doors_opened', 0) > 0) / total_gens)
        pct_chest = int(100 * sum(1 for d in learning_monitor.generation_data if d.get('chest_opened', False)) / total_gens)
        first_chest_gen = next((d.get('generation') for d in learning_monitor.generation_data if d.get('chest_opened', False)), generation)
        trees_cut_total = sum(d.get('trees_cut', 0) for d in learning_monitor.generation_data)
    else:
        pct_red = pct_gold = pct_doors = pct_chest = 0
        first_chest_gen = generation
        trees_cut_total = 0

    # Movimiento (compacto)
    avg_distance_this_gen_m = (avg_exploration / 100) if avg_exploration else 0

    # Penalizaciones ambientales acumuladas (esta generación)
    total_env_penalty = sum(getattr(a, 'fitness_env_penalty', 0.0) for a in agents)
    
    # Estadísticas de habilidades
    trees_cut = 0  # No se rastrea individualmente por agente
    obstacles_avoided = sum(a.obstacles_avoided for a in agents)
    
    # Estadísticas de fortalezas (usar atributos del mundo, no de agentes individuales)
    red_keys_collected = 1 if world.red_key_collected else 0
    gold_keys_collected = 1 if world.gold_key_collected else 0
    doors_opened = 0
    if world.door and world.door.is_open:
        doors_opened += 1
    if world.door_iron and world.door_iron.is_open:
        doors_opened += 1
    
    # Configurar fuentes (más pequeñas, como el popup de generación)
    font_large = pygame.font.Font(None, 48)   # Título principal
    font_title = pygame.font.Font(None, 22)   # Secciones
    font_medium = pygame.font.Font(None, 18)  # Subtítulos/ítems destacados
    font_small = pygame.font.Font(None, 16)   # Texto
    
    # Colores
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 100, 255)
    RED = (255, 0, 0)
    
    # Pantalla de FIN
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    running = False
        
        # Renderizar la simulación de fondo primero
        # Dibujar fondo de pasto
        grass_sprite = sprite_manager.get_environment_sprite('grass')
        if grass_sprite:
            for x in range(0, render_surface.get_width(), grass_sprite.get_width()):
                for y in range(0, render_surface.get_height(), grass_sprite.get_height()):
                    render_surface.blit(grass_sprite, (x, y))
        
        # Dibujar obstáculos
        for obstacle in world.obstacles:
            obstacle.draw(render_surface, sprite_manager, tick)
        
        # Dibujar perímetro decorativo
        for perimeter_obj in world.perimeter_obstacles:
            perimeter_obj.draw(render_surface, sprite_manager)
        
        # Dibujar estanque móvil
        for pond_obj in world.pond_obstacles:
            pond_obj.draw(render_surface, sprite_manager, tick)
        
        # Dibujar comida
        for food in world.food_items:
            if not food['eaten']:
                apple_sprite = sprite_manager.get_environment_sprite('apple')
                render_surface.blit(apple_sprite, (int(food['x'] - 8), int(food['y'] - 8)))
        
        # Dibujar fortalezas, llaves, puertas y cofre
        if world.door:
            world.door.draw(render_surface, sprite_manager, tick)
        if world.door_iron:
            world.door_iron.draw(render_surface, sprite_manager, tick)
        if world.chest:
            world.chest.draw(render_surface, sprite_manager, tick)
        if world.red_key and not world.red_key.collected:
            # Efecto de halo brillante para red_key (igual que el hacha)
            red_key_sprite = sprite_manager.get_environment_sprite('red_key')
            if red_key_sprite:
                # Efecto de brillo pulsante
                glow_intensity = int(50 + 30 * abs(pygame.math.Vector2(1, 0).rotate(tick * 2).x))
                glow_radius = 20
                
                # Crear superficie de brillo
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 0, 0, glow_intensity),
                                (glow_radius, glow_radius), glow_radius)
                render_surface.blit(glow_surface, (world.red_key.x - glow_radius, world.red_key.y - glow_radius))
                
                # Dibujar red_key original con brillo sutil
                world.red_key.draw(render_surface, sprite_manager, tick)
                
                # Añadir brillo sutil encima (sin fondo)
                bright_overlay = pygame.Surface(red_key_sprite.get_size(), pygame.SRCALPHA)
                bright_overlay.fill((255, 0, 0, 30))
                bright_overlay.blit(red_key_sprite, (0, 0), special_flags=pygame.BLEND_ADD)
                render_surface.blit(bright_overlay, (world.red_key.x - 10, world.red_key.y - 10))
            else:
                # Fallback si no hay sprite
                world.red_key.draw(render_surface, sprite_manager, tick)
        if world.gold_key and not world.gold_key.collected:
            world.gold_key.draw(render_surface, sprite_manager, tick)
        
        # Dibujar hacha si existe y no fue agarrada (con efectos de brillo)
        if SimulationConfig.TREE_CUTTING_ENABLED and world.axe and not world.axe['picked_up']:
            axe_sprite = sprite_manager.get_environment_sprite('axe')
            if axe_sprite:
                # Efecto de brillo pulsante
                glow_intensity = int(50 + 30 * abs(pygame.math.Vector2(1, 0).rotate(tick * 2).x))
                glow_radius = 20
                
                # Crear superficie de brillo
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 255, 0, glow_intensity),
                                (glow_radius, glow_radius), glow_radius)
                render_surface.blit(glow_surface, (world.axe['x'] - glow_radius, world.axe['y'] - glow_radius))
                
                # Dibujar hacha original con brillo sutil
                render_surface.blit(axe_sprite, (world.axe['x'] - 10, world.axe['y'] - 10))
                
                # Añadir brillo sutil encima (sin fondo)
                bright_overlay = pygame.Surface(axe_sprite.get_size(), pygame.SRCALPHA)
                bright_overlay.fill((255, 255, 0, 30))
                bright_overlay.blit(axe_sprite, (0, 0), special_flags=pygame.BLEND_ADD)
                render_surface.blit(bright_overlay, (world.axe['x'] - 10, world.axe['y'] - 10))
        
        # Dibujar agentes
        for agent in agents:
            if agent.alive:
                agent.draw(render_surface, tick, sprite_manager, particle_system)
        
        # Actualizar y dibujar sistema de partículas
        particle_system.update()
        particle_system.draw(render_surface)
        
        # Crear panel semi-transparente como el popup de generación
        panel_width, panel_height = 800, 600
        panel_x = (render_surface.get_width() - panel_width) // 2 - 113
        panel_y = (render_surface.get_height() - panel_height) // 2
        final_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        final_surface.fill((0, 0, 0, 200))

        if mission_completed:
            title_label = "¡MISIÓN COMPLETADA!"
            subtitle_label = "El cofre ha sido abierto por un agente evolutivo"
            title_color = GOLD
        else:
            title_label = "Simulación finalizada"
            subtitle_label = "Se alcanzó el límite de generaciones sin abrir el cofre"
            title_color = BLUE

        # Título principal
        title_text = font_large.render(title_label, True, title_color)
        title_rect = title_text.get_rect(center=(panel_width // 2, 40))
        final_surface.blit(title_text, title_rect)

        # Subtítulo
        subtitle_text = font_medium.render(subtitle_label, True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(panel_width // 2, 70))
        final_surface.blit(subtitle_text, subtitle_rect)

        # Línea separadora
        pygame.draw.line(final_surface, (100, 255, 150), (20, 90), (panel_width - 20, 90), 2)

        # --- Gráfico histórico de fitness (promedio y máximo) ---
        chart_width, chart_height = 340, 220
        chart_x = panel_width - chart_width - 30
        chart_y = 110

        chart_surface = pygame.Surface((chart_width, chart_height), pygame.SRCALPHA)
        chart_surface.fill((20, 20, 20, 180))

        axis_color = (80, 200, 120)
        grid_color = (70, 70, 70)
        avg_color = (120, 255, 180)
        max_color = (255, 215, 0)

        padding_left = 50
        padding_right = 20
        padding_top = 20
        padding_bottom = 40
        inner_width = chart_width - padding_left - padding_right
        inner_height = chart_height - padding_top - padding_bottom
        inner_left = padding_left
        inner_top = padding_top

        # Marco y ejes
        pygame.draw.rect(chart_surface, (90, 90, 90), (0, 0, chart_width, chart_height), 1)
        pygame.draw.line(chart_surface, axis_color,
                         (inner_left, inner_top + inner_height),
                         (inner_left + inner_width, inner_top + inner_height), 2)
        pygame.draw.line(chart_surface, axis_color,
                         (inner_left, inner_top),
                         (inner_left, inner_top + inner_height), 2)

        # Etiquetas del eje Y (0-100)
        for level in range(0, 101, 25):
            if inner_height <= 0:
                break
            level_ratio = level / 100.0
            y = inner_top + inner_height - int(level_ratio * inner_height)
            pygame.draw.line(chart_surface, grid_color,
                             (inner_left, y),
                             (inner_left + inner_width, y), 1)
            label = font_small.render(f"{level}", True, (180, 180, 180))
            chart_surface.blit(label, (10, y - 8))

        avg_history = [d.get('avg_fitness', 0.0) for d in learning_monitor.generation_data] if learning_monitor.generation_data else []
        max_history = [d.get('max_fitness', d.get('avg_fitness', 0.0)) for d in learning_monitor.generation_data] if learning_monitor.generation_data else []
        gen_count = len(avg_history)

        def _map_point(idx, value):
            if inner_width <= 0:
                return inner_left, inner_top + inner_height
            if gen_count <= 1:
                x = inner_left + inner_width // 2
            else:
                x = inner_left + int(idx * inner_width / (gen_count - 1))
            value_clamped = max(0.0, min(100.0, float(value)))
            if inner_height <= 0:
                y = inner_top
            else:
                y = inner_top + inner_height - int((value_clamped / 100.0) * inner_height)
            return x, y

        # Dibujar líneas de historia
        if gen_count:
            avg_points = [_map_point(i, val) for i, val in enumerate(avg_history)]
            max_points = [_map_point(i, val) for i, val in enumerate(max_history)]

            if len(avg_points) >= 2:
                pygame.draw.lines(chart_surface, avg_color, False, avg_points, 2)
            elif avg_points:
                pygame.draw.circle(chart_surface, avg_color, avg_points[0], 3)

            if len(max_points) >= 2:
                pygame.draw.lines(chart_surface, max_color, False, max_points, 2)
            elif max_points:
                pygame.draw.circle(chart_surface, max_color, max_points[0], 3)

            # Puntos finales resaltados
            pygame.draw.circle(chart_surface, avg_color, avg_points[-1], 4)
            pygame.draw.circle(chart_surface, max_color, max_points[-1], 4, 1)

            # Etiquetas de generaciones (inicio y fin)
            if gen_count >= 1:
                start_label = font_small.render("Gen 1", True, (180, 180, 180))
                chart_surface.blit(start_label, (inner_left - start_label.get_width() // 2, inner_top + inner_height + 10))
                end_label = font_small.render(f"Gen {gen_count}", True, (180, 180, 180))
                chart_surface.blit(end_label, (inner_left + inner_width - end_label.get_width() // 2, inner_top + inner_height + 10))

        # Leyenda
        legend_y = 5
        legend_avg = font_small.render("Promedio", True, avg_color)
        legend_max = font_small.render("Máximo", True, max_color)
        chart_surface.blit(legend_avg, (inner_left + 10, legend_y))
        chart_surface.blit(legend_max, (inner_left + 120, legend_y))

        final_surface.blit(chart_surface, (chart_x, chart_y))

        # Estadísticas principales (Modo compacto)
        y_pos = 110

        # Encabezado corto
        gen_text = font_medium.render(f"Generación: {generation}", True, (100, 255, 150))
        final_surface.blit(gen_text, (30, y_pos))
        
        # Tiempo total acumulado (minutos) estimado a partir del historial
        total_ticks = 0
        if learning_monitor.generation_data:
            for gen_data in learning_monitor.generation_data:
                if 'generation_time_ticks' in gen_data:
                    total_ticks += gen_data['generation_time_ticks']
                else:
                    total_ticks += gen_data.get('avg_age', 0)
        if total_ticks == 0:
            total_ticks = tick
        total_minutes = total_ticks // 60 // 60
        time_text = font_medium.render(f"Tiempo total: {total_minutes:.1f} min", True, (100, 255, 150))
        final_surface.blit(time_text, (260, y_pos))

        y_pos += 28

        # 1) Objetivo y resultado
        goal_title = font_title.render("OBJETIVO", True, (100, 255, 150))
        final_surface.blit(goal_title, (30, y_pos))
        y_pos += 18
        goal_line_1 = font_small.render("Objetivo: Abrir el cofre", True, (200, 200, 200))
        goal_line_2 = font_small.render("Resultado: Completado", True, (200, 255, 200))
        final_surface.blit(goal_line_1, (40, y_pos)); y_pos += 18
        final_surface.blit(goal_line_2, (40, y_pos)); y_pos += 20

        # 2) Pasos clave del reto (checklist)
        steps_title = font_title.render("PASOS CLAVE", True, (100, 255, 150))
        final_surface.blit(steps_title, (30, y_pos))
        y_pos += 18
        step_red = "SI" if world.red_key_collected else "NO"
        step_gold = "SI" if world.gold_key_collected else "NO"
        step_door_wood = "SI" if (world.door and world.door.is_open) else "NO"
        step_door_iron = "SI" if (world.door_iron and world.door_iron.is_open) else "NO"
        step_chest = "SI"  # Estamos en pantalla de FIN
        steps_line_1 = font_small.render(f"Llave roja: {step_red}   Llave dorada: {step_gold}", True, (200, 200, 200))
        steps_line_2 = font_small.render(f"Puerta madera: {step_door_wood}   Puerta hierro: {step_door_iron}", True, (200, 200, 200))
        steps_line_3 = font_small.render(f"Cofre: {step_chest}", True, (200, 200, 200))
        final_surface.blit(steps_line_1, (40, y_pos)); y_pos += 18
        final_surface.blit(steps_line_2, (40, y_pos)); y_pos += 18
        final_surface.blit(steps_line_3, (40, y_pos)); y_pos += 20

        # 3) ¿Aprendieron?
        learned_title = font_title.render("¿APRENDIERON?", True, (100, 255, 150))
        final_surface.blit(learned_title, (30, y_pos))
        y_pos += 18
        
        # Mejora más robusta: al menos 5 puntos de diferencia O al menos 10% de mejora
        if learning_monitor.generation_data and len(learning_monitor.generation_data) > 1:
            initial_avg_fitness = learning_monitor.generation_data[0].get('avg_fitness', 0)
            # Usar el promedio de las últimas 3 generaciones para evitar fluctuaciones
            last_gens = learning_monitor.generation_data[-3:]
            final_avg_fitness = sum(g.get('avg_fitness', 0) for g in last_gens) / len(last_gens)
            fitness_delta = final_avg_fitness - initial_avg_fitness
            # Mejora significativa: al menos 5 puntos Y al menos 10% de mejora relativa
            improvement_threshold = max(5.0, initial_avg_fitness * 0.10)  # 5 puntos o 10% del inicial
            improved_flag = "SI" if fitness_delta > improvement_threshold else "NO"
            
            # Explorar más: comparar distancia promedio gen1 vs últimas 3
            first_avg_dist = learning_monitor.generation_data[0].get('avg_distance', 0)
            last_avg_dist = sum(g.get('avg_distance', 0) for g in last_gens) / len(last_gens)
            explored_more_flag = "SI" if last_avg_dist > first_avg_dist * 1.05 else "NO"  # Al menos 5% más exploración
        else:
            improved_flag = "SI" if fitness_delta > 5.0 else "NO"  # Fallback: umbral de 5 puntos
            explored_more_flag = "N/A"
            initial_avg_fitness = avg_fitness
            final_avg_fitness = avg_fitness
        
        learn_line_1 = font_small.render(f"Mejoraron con el tiempo: {improved_flag}", True, (200, 200, 200))
        learn_line_2 = font_small.render(f"Antes vs ahora (fitness prom): {initial_avg_fitness:.1f} → {final_avg_fitness:.1f}", True, (200, 200, 200))
        learn_line_3 = font_small.render(f"Exploraron más: {explored_more_flag}", True, (200, 200, 200))
        final_surface.blit(learn_line_1, (40, y_pos)); y_pos += 18
        final_surface.blit(learn_line_2, (40, y_pos)); y_pos += 18
        final_surface.blit(learn_line_3, (40, y_pos)); y_pos += 20

        # 4) Línea de tiempo mínima
        timeline_title = font_title.render("LÍNEA DE TIEMPO", True, (100, 255, 150))
        final_surface.blit(timeline_title, (30, y_pos))
        y_pos += 18
        timeline_line_1 = font_small.render(f"Primera vez con cofre abierto: Gen {first_chest_gen}", True, (200, 200, 200))
        timeline_line_2 = font_small.render(f"Tiempo total de simulación: {total_minutes:.1f} min", True, (200, 200, 200))
        final_surface.blit(timeline_line_1, (40, y_pos)); y_pos += 18
        final_surface.blit(timeline_line_2, (40, y_pos)); y_pos += 20

        # 5) Top agente (ID corto)
        top_title = font_title.render("TOP AGENTE", True, (100, 255, 150))
        final_surface.blit(top_title, (30, y_pos))
        y_pos += 18
        top_agent = max(agents, key=lambda a: a.fitness) if agents else None
        if top_agent:
            raw_id = str(top_agent.id)
            short_id = f"#{raw_id[-4:]}" if len(raw_id) > 4 else f"#{raw_id}"
            top_km = top_agent.distance_traveled/100/1000  # px -> m -> km (1px=1cm)
            top_fitness_capped = min(100.0, getattr(top_agent, 'fitness', 0.0))
            top_line = font_small.render(
                f"Agente {short_id}: fitness {top_fitness_capped:.1f}, comida {top_agent.food_eaten} manzanas, recorrio {top_km:.2f} km",
                True, (200, 200, 200)
            )
            final_surface.blit(top_line, (40, y_pos)); y_pos += 20

        # 6) Sello de movimiento
        move_title = font_title.render("MOVIMIENTO", True, (100, 255, 150))
        final_surface.blit(move_title, (30, y_pos))
        y_pos += 18
        try:
            avg_sr = sum(getattr(a, 'metric_sr', 0.0) for a in agents) / len(agents) if agents else 0.0
            movement_flag = "Mas recto y con menos vueltas" if avg_sr >= 0.5 else "Aun con vueltas"
        except Exception:
            movement_flag = "Aun con vueltas"
        move_line = font_small.render(movement_flag, True, (200, 200, 200))
        final_surface.blit(move_line, (40, y_pos)); y_pos += 20

        # 7) Clustering (última generación)
        cluster_title = font_title.render("CLUSTERING", True, (100, 255, 150))
        final_surface.blit(cluster_title, (30, y_pos))
        y_pos += 18
        
        # Calcular clustering de la última generación
        try:
            if agents and len(agents) >= 3:
                total_agents = len(agents)
                clusterer = BehaviorClusterer(n_clusters=3)
                clusters, cluster_stats = clusterer.cluster_agents(agents)
                interpretations = clusterer.get_cluster_interpretation(cluster_stats)
                
                # Ordenar clusters por tipo
                cluster_order = ["Exploradores", "Recolectores", "Exitosos"]
                sorted_clusters = []
                for cluster_id in cluster_stats['cluster_counts'].keys():
                    count = cluster_stats['cluster_counts'][cluster_id]
                    if count > 0:
                        strategy = interpretations.get(cluster_id, f"C{cluster_id}")
                        fitness = cluster_stats['cluster_fitness'][cluster_id]['promedio']
                        percentage = (count / total_agents) * 100  # Calcular porcentaje
                        sorted_clusters.append((strategy, count, percentage, fitness))
                sorted_clusters.sort(key=lambda x: (cluster_order.index(x[0]) if x[0] in cluster_order else 999, -x[1]))
                
                for strategy, count, percentage, fitness in sorted_clusters[:3]:
                    cluster_text = f"{strategy}: {percentage:.1f}% ({count} agentes, fit {fitness:.1f})"
                    cluster_line = font_small.render(cluster_text, True, (200, 200, 200))
                    final_surface.blit(cluster_line, (40, y_pos))
                    y_pos += 18
            else:
                no_cluster_line = font_small.render("No disponible (pocos agentes)", True, (150, 150, 150))
                final_surface.blit(no_cluster_line, (40, y_pos))
                y_pos += 18
        except Exception as e:
            error_line = font_small.render("Error en clustering", True, (150, 150, 150))
            final_surface.blit(error_line, (40, y_pos))
            y_pos += 18
        
        y_pos += 8

        # Mensaje final + instrucciones
        final_text = font_medium.render("¡Los agentes evolutivos han completado su misión!", True, (100, 255, 150))
        final_rect = final_text.get_rect(center=(panel_width // 2, y_pos))
        final_surface.blit(final_text, final_rect)
        y_pos += 26
        instructions_text = font_small.render("Presiona ESC o ENTER para salir", True, (220, 220, 220))
        instructions_rect = instructions_text.get_rect(center=(panel_width // 2, y_pos))
        final_surface.blit(instructions_text, instructions_rect)

        # Dibujar el panel sobre la simulación
        render_surface.blit(final_surface, (panel_x, panel_y))
        
        # Escalar y mostrar la superficie renderizada
        scaled_surface = pygame.transform.scale(render_surface, (screen_width, screen_height))
        display_screen.blit(scaled_surface, (0, 0))
        
        pygame.display.flip()
    
    # Cerrar pygame
    pygame.quit()


if __name__ == "__main__":
    main()
