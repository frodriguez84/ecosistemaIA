"""
Ecosistema Evolutivo IA - Archivo principal simplificado.
"""

import pygame
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import SimulationConfig
from src.agents.advanced_agent import AdvancedAgent, SimpleNeuralNetwork
from src.world.world import World
from src.world.obstacles import Obstacle, Axe
from src.evolution.genetic_algorithm import GeneticAlgorithm
from src.ui.renderer import SpriteManager, ParticleSystem
from src.ui.stats import StatsPanel
from src.ui.popup import SummaryPopup
from src.analytics.learning_monitor import LearningMonitor


def main():
    """Función principal."""
    print("🎨 Ecosistema Evolutivo IA")
    print("=" * 70)
    print("💡 FUNCIONES DISPONIBLES:")
    print("   - Presiona 'C' para activar modo comando")
    print("   - Escribe: tree, wall, water, hut, potion, apple")
    print("   - Haz click en el mapa donde quieres colocar el objeto")
    print("   - Presiona ENTER para colocar el objeto")
    print("   - Presiona 'C' nuevamente para salir del modo comando")
    print("=" * 70)
    
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
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Ecosistema Evolutivo IA")
    else:
        screen = None
        print("🚀 MODO HEADLESS ACTIVADO - Sin render")
    clock = pygame.time.Clock()
    
    # Crear sistemas de sprites y partículas
    sprite_manager = SpriteManager()
    particle_system = ParticleSystem()
    
    # Crear cuadro de resumen
    summary_popup = SummaryPopup(screen_width, screen_height)
    fitness_history = []  # Historial de fitness para el gráfico
    
    # Crear monitor de aprendizaje
    learning_monitor = LearningMonitor()
    
    # Crear mundo (sistema original) con cantidad de comida configurable
    world = World(screen_width - 250, screen_height, config.FOOD_COUNT)  # Usar config
    
    # Crear algoritmo genético con configuración
    ga = GeneticAlgorithm(**config.get_genetic_params())
    ga.world = world  # Pasar referencia al mundo
    
    # Crear población inicial
    agents = ga._create_random_population()
    
    # Reposicionar agentes que spawnearon dentro de fortalezas O sobre obstáculos
    if config.FORTRESSES_ENABLED:
        import random
        for agent in agents:
            # Verificar si está dentro de fortalezas O sobre obstáculos
            needs_repositioning = (world._is_inside_fortress(agent.x, agent.y) or 
                                  any(obstacle.collides_with(agent.x, agent.y, agent.radius) 
                                      for obstacle in world.obstacles))
            
            if needs_repositioning:
                # Reposicionar fuera de fortalezas, obstáculos Y zona de estadísticas
                attempts = 0
                while attempts < 500:  # Más intentos para mayor seguridad
                    # Excluir zona del panel de estadísticas (panel_width = 240, panel_height = 300)
                    new_x = random.randint(250, screen_width - 50)  # Evitar zona de estadísticas
                    new_y = random.randint(320, screen_height - 50)  # Evitar zona de estadísticas
                    
                    # Verificar que no esté en fortaleza Y no colisione con obstáculos
                    if (not world._is_inside_fortress(new_x, new_y) and
                        not any(obstacle.collides_with(new_x, new_y, agent.radius) 
                               for obstacle in world.obstacles)):
                        agent.x = new_x
                        agent.y = new_y
                        break
                    attempts += 1
                
                # Si no se pudo reposicionar después de 500 intentos, usar posición segura
                if attempts >= 500:
                    # Posición segura en el centro del área de juego
                    agent.x = screen_width // 2
                    agent.y = screen_height // 2
                    print(f"⚠️ Agente {agent.id} reposicionado a posición segura")
    
    # Crear panel de estadísticas (más alto)
    stats_panel = StatsPanel(screen_width - 240, 10, 230, 300)  # Panel más corto
    
    print(f"✅ {len(agents)} agentes avanzados creados")
    print(f"✅ {len(world.food_items)} piezas de comida generadas")
    print(f"✅ {len(world.obstacles)} obstáculos generados")
    print("✅ Sistema de sprites inicializado")
    print("✅ Sistema de partículas activado")
    
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
    command_mode = False
    current_command = ""
    last_click_coords = None
    
    # Optimizaciones de rendimiento
    print(f"⚡ Optimizaciones de rendimiento activadas:")
    print(f"   - FPS objetivo: {target_fps}")
    print(f"   - Velocidad de agentes: 3.0 (aumentada)")
    print(f"   - Estadísticas actualizadas cada 5 frames")
    print(f"   - Partículas actualizadas cada 2 frames")
    print(f"   - Redes neuronales optimizadas")
    print(f"   - Menos agentes por generación")
    
    while running and generation <= max_generations:
        # Manejar eventos (solo si no está en modo headless)
        if not config.HEADLESS_MODE:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_c:
                        # Activar modo comando
                        command_mode = not command_mode
                        current_command = ""
                        if command_mode:
                            print("🎯 MODO COMANDO ACTIVADO")
                            print("💡 Escribe: tree, wall, water, hut, potion, apple")
                            print("💡 Luego haz click en el mapa para colocar el objeto")
                        else:
                            print("❌ Modo comando desactivado")
                    elif command_mode:
                        # Manejar comandos
                        if event.key == pygame.K_RETURN:
                            # Ejecutar comando
                            if current_command and last_click_coords:
                                x, y = last_click_coords
                                summary_popup.add_object_at_coordinates(x, y, current_command, world)
                                command_mode = False
                                current_command = ""
                            else:
                                print("❌ Primero haz click en el mapa")
                        elif event.key == pygame.K_BACKSPACE:
                            # Borrar último carácter
                            current_command = current_command[:-1]
                        else:
                            # Añadir carácter
                            char = event.unicode.lower()
                            if char.isalpha():
                                current_command += char
                                print(f"📝 Comando: {current_command}")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Manejar clicks en el cuadro de resumen
                    if summary_popup.handle_click(event.pos):
                        pass  # El cuadro se cierra automáticamente
                    else:
                        # Mostrar coordenadas del click
                        x, y = event.pos
                        if x < screen_width - 250:  # Solo en el área del juego
                            # Convertir a coordenadas de tile (16x16)
                            tile_x = (x // 16) * 16
                            tile_y = (y // 16) * 16
                            tile_coord_x = x // 16
                            tile_coord_y = y // 16
                            
                            # Guardar coordenadas para comandos
                            last_click_coords = (tile_x, tile_y)
                            
                            print(f"📍 Click en píxeles: ({x}, {y})")
                            print(f"🎯 Coordenadas de tile: ({tile_x}, {tile_y})")
                            print(f"📐 Tile número: ({tile_coord_x}, {tile_coord_y})")
                            
                            if command_mode:
                                print(f"✅ Coordenadas guardadas para comando: {current_command}")
                                print("💡 Presiona ENTER para colocar el objeto")
                            else:
                                print("💡 Presiona 'C' para activar modo comando")
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
                        # ¡COFRE ABIERTO! Mostrar pantalla de FIN
                        print(f"\n🏆 ¡¡¡COFRE ABIERTO!!! 🏆")
                        print(f"🎯 Agente {agent.id} ha completado la misión en la generación {generation}")
                        print(f"⏱️ Tick: {tick}")
                        print(f"🎉 ¡MISIÓN COMPLETADA! 🎉")
                        show_final_screen(screen, generation, tick, agents, world, learning_monitor)
                        return
        
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
            print(f"\n🧬 Generación {generation} terminada")
            print(f"   - Agentes vivos: {len(alive_agents)}")
            print(f"   - Ticks: {tick}")
            
            # Contar árboles cortados en esta generación
            trees_cut_this_generation = 0
            if hasattr(world, 'trees'):
                trees_cut_this_generation = len([tree for tree in world.trees if tree.is_cut])
            
            # Estadísticas de puzzle (llaves, puertas, cofre)
            red_key_status = "🔑 RECOGIDA" if world.red_key_collected else "❌ NO RECOGIDA"
            gold_key_status = "🔑 RECOGIDA" if world.gold_key_collected else "❌ NO RECOGIDA"
            
            door_status = "🚪 ABIERTA" if world.door and world.door.is_open else "🔒 CERRADA"
            iron_door_status = "🚪 ABIERTA" if world.door_iron and world.door_iron.is_open else "🔒 CERRADA"
            
            chest_status = "📦 ABIERTO" if world.chest and world.chest.is_open else "🔒 CERRADO"
            
            if agents:
                # Calcular fitness de todos los agentes antes de las estadísticas
                for agent in agents:
                    agent._calculate_fitness()
                
                avg_fitness = sum(agent.fitness for agent in agents) / len(agents)
                max_fitness = max(agent.fitness for agent in agents)
                avg_age = sum(agent.age for agent in agents) / len(agents)
                avg_food = sum(agent.food_eaten for agent in agents) / len(agents)
                avg_energy = sum(agent.energy for agent in alive_agents) / len(alive_agents) if alive_agents else 0
                
                print(f"   - Fitness promedio: {avg_fitness:.1f}/100")
                print(f"   - Fitness máximo: {max_fitness:.1f}/100")
                print(f"   - Tiempo de vida: {avg_age/60:.1f} min")
                print(f"   - Comida promedio: {avg_food:.1f}")
                print(f"   - Supervivencia: {len(alive_agents)/len(agents)*100:.1f}%")
                
                # Estadísticas de puzzle
                print(f"   🧩 PUZZLE:")
                print(f"      - Llave roja: {red_key_status}")
                print(f"      - Llave dorada: {gold_key_status}")
                print(f"      - Puerta madera: {door_status}")
                print(f"      - Puerta hierro: {iron_door_status}")
                print(f"      - Cofre: {chest_status}")
                print(f"      - Árboles cortados: {trees_cut_this_generation}")
            else:
                avg_fitness = max_fitness = avg_age = avg_food = avg_energy = 0
            
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
                'trees_cut': trees_cut_this_generation
            }
            
            # Añadir fitness promedio al historial
            fitness_history.append(avg_fitness)
            
            # Registrar datos en el monitor de aprendizaje
            gen_data = learning_monitor.record_generation(generation, agents, world)
            
            # Mostrar análisis detallado cada 5 generaciones
            if generation % 5 == 0 or generation == 1:
                learning_monitor.print_generation_summary(gen_data)
            
            # Detectar patrones de aprendizaje cada 10 generaciones
            if generation % 10 == 0:
                learning_monitor.detect_learning_patterns()
            
            # Mostrar cuadro de resumen
            summary_popup.show(generation_data, fitness_history)
            
            # Evolucionar
            agents = ga.evolve(agents)
            
            # Reposicionar agentes que spawnearon dentro de fortalezas O sobre obstáculos (después de evolucionar)
            if config.FORTRESSES_ENABLED:
                import random
                for agent in agents:
                    # Verificar si está dentro de fortalezas O sobre obstáculos
                    needs_repositioning = (world._is_inside_fortress(agent.x, agent.y) or 
                                          any(obstacle.collides_with(agent.x, agent.y, agent.radius) 
                                              for obstacle in world.obstacles))
                    
                    if needs_repositioning:
                        # Reposicionar fuera de fortalezas, obstáculos Y zona de estadísticas
                        attempts = 0
                        while attempts < 500:  # Más intentos para mayor seguridad
                            # Excluir zona del panel de estadísticas (panel_width = 240, panel_height = 300)
                            new_x = random.randint(250, screen_width - 50)  # Evitar zona de estadísticas
                            new_y = random.randint(320, screen_height - 50)  # Evitar zona de estadísticas
                            
                            # Verificar que no esté en fortaleza Y no colisione con obstáculos
                            if (not world._is_inside_fortress(new_x, new_y) and
                                not any(obstacle.collides_with(new_x, new_y, agent.radius) 
                                       for obstacle in world.obstacles)):
                                agent.x = new_x
                                agent.y = new_y
                                break
                            attempts += 1
                        
                        # Si no se pudo reposicionar después de 500 intentos, usar posición segura
                        if attempts >= 500:
                            # Posición segura en el centro del área de juego
                            agent.x = screen_width // 2
                            agent.y = screen_height // 2
                            print(f"⚠️ Agente {agent.id} reposicionado a posición segura")
            
            world.reset_food()
            world.tick = 0
            tick = 0
            generation += 1
            
            # Recalcular tiempo máximo para la nueva generación con incremento gradual
            if config.ADAPTIVE_TIME_ENABLED:
                # Calcular cuántos incrementos aplicar: cada TICKS_INCREMENT_FREQUENCY generaciones
                incrementos_aplicados = (generation - 1) // config.TICKS_INCREMENT_FREQUENCY
                max_ticks_per_generation = config.BASE_TICKS + (config.TICKS_INCREMENT_AMOUNT * incrementos_aplicados)
            else:
                max_ticks_per_generation = config.BASE_TICKS
            
            print(f"✅ Nueva generación {generation} creada ⏱️ {max_ticks_per_generation} ticks")
        
        # Renderizar (solo si no está en modo headless)
        if not config.HEADLESS_MODE:
            screen.fill((40, 40, 60))  # Fondo azul oscuro
            
            # Dibujar fondo solo con pasto
            for x in range(0, screen_width - 250, 16):
                for y in range(0, screen_height, 16):
                    # Solo pasto con variación
                    grass_variant = 1 if (x // 16 + y // 16) % 2 == 0 else 2
                    grass_sprite = sprite_manager.get_environment_sprite('grass', grass_variant)
                    screen.blit(grass_sprite, (x, y))
            
            # Dibujar obstáculos con sprites
            for obstacle in world.obstacles:
                obstacle.draw(screen, sprite_manager, tick)
            
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
                        screen.blit(glow_surface, (world.axe['x'] - glow_radius, world.axe['y'] - glow_radius))
                    
                    # Dibujar hacha original con brillo sutil
                    screen.blit(axe_sprite, (world.axe['x'] - 10, world.axe['y'] - 10))
                    
                    # Añadir brillo sutil encima (sin fondo)
                    bright_overlay = pygame.Surface(axe_sprite.get_size(), pygame.SRCALPHA)
                    bright_overlay.fill((*glow_color[:3], 30))  # Muy transparente
                    bright_overlay.blit(axe_sprite, (0, 0), special_flags=pygame.BLEND_ADD)
                    screen.blit(bright_overlay, (world.axe['x'] - 10, world.axe['y'] - 10))
            
            # Dibujar manzanas (comida)
            for food in world.food_items:
                if not food['eaten']:
                    # Dibujar manzana con sprite
                    apple_sprite = sprite_manager.get_environment_sprite('apple')
                    screen.blit(apple_sprite, (int(food['x'] - 8), int(food['y'] - 8)))
            
            # Dibujar fortalezas, llaves, puertas y cofre (DESPUÉS de obstáculos para que se vean)
            if config.FORTRESSES_ENABLED:
                # Dibujar puertas (encima de los muros)
                if world.door:
                    world.door.draw(screen, sprite_manager, tick)
                if world.door_iron:
                    world.door_iron.draw(screen, sprite_manager, tick)
                
                # Dibujar cofre
                if world.chest:
                    world.chest.draw(screen, sprite_manager, tick)
                
                # Dibujar llaves
                if world.red_key and not world.red_key.collected:
                    world.red_key.draw(screen, sprite_manager, tick)
                if world.gold_key and not world.gold_key.collected:
                    world.gold_key.draw(screen, sprite_manager, tick)
            
            # Actualizar sistema de partículas (cada 2 frames para mejor rendimiento)
            if tick % 2 == 0:
                particle_system.update()
            
            # Limpiar objetivos de agentes muertos para mejor rendimiento
            for agent in agents:
                if not agent.alive and hasattr(agent, 'target_food'):
                    agent.target_food = None
            
            # Dibujar agentes
            for agent in agents:
                agent.draw(screen, tick, sprite_manager, particle_system)
            
            # Dibujar partículas
            particle_system.draw(screen)
            
            # Dibujar panel de estadísticas simplificado
            stats_panel.draw(screen, generation, agents, world, tick)
            
            # Dibujar cuadro de resumen (si está visible)
            summary_popup.draw(screen)
            
            # Mostrar modo comando
            if command_mode:
                font = pygame.font.Font(None, 24)
                command_text = f"MODO COMANDO: {current_command}"
                command_surface = font.render(command_text, True, (255, 255, 0))
                screen.blit(command_surface, (10, 10))
                
                help_text = "Escribe: tree, wall, water, hut, potion, apple"
                help_surface = font.render(help_text, True, (200, 200, 200))
                screen.blit(help_surface, (10, 35))
                
                if last_click_coords:
                    coords_text = f"Click en: {last_click_coords}"
                    coords_surface = font.render(coords_text, True, (0, 255, 0))
                    screen.blit(coords_surface, (10, 60))
            
            if paused:
                font = pygame.font.Font(None, 24)
                pause_text = font.render("PAUSADO - Presiona ESPACIO", True, (255, 0, 0))
                screen.blit(pause_text, (10, 40))
            
            pygame.display.flip()
        
        clock.tick(target_fps)  # Usar FPS objetivo
    
    pygame.quit()
    
    # Crear reporte final de aprendizaje
    print(f"\n🎉 Simulación completada - {generation-1} generaciones evolucionadas")
    learning_monitor.create_learning_report()
    
    # Guardar datos para análisis posterior (DESHABILITADO)
    # learning_monitor.save_data(f"learning_data_gen_{generation-1}.json")


def show_final_screen(screen, generation, tick, agents, world, learning_monitor):
    """Muestra la pantalla de FIN cuando se abre el cofre."""
    import pygame
    from config import SimulationConfig
    
    # Si estamos en modo headless, solo mostrar estadísticas por consola
    if SimulationConfig.HEADLESS_MODE:
        print(f"\n🎉 ¡MISIÓN COMPLETADA! 🎉")
        print(f"📊 Generación: {generation}")
        print(f"⏱️ Tick: {tick}")
        print(f"🎯 Agentes vivos: {len([a for a in agents if a.alive])}")
        print(f"🏆 ¡El cofre ha sido abierto por un agente evolutivo!")
        print(f"📈 Fitness promedio: {sum(a.fitness for a in agents) / len(agents):.1f}")
        print(f"📈 Fitness máximo: {max(a.fitness for a in agents):.1f}")
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
    
    # Configurar fuente
    font_large = pygame.font.Font(None, 72)
    font_title = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 28)
    
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
        
        # Fondo negro
        screen.fill(BLACK)
        
        # Título principal
        title_text = font_large.render("🎉 ¡MISIÓN COMPLETADA! 🎉", True, GOLD)
        title_rect = title_text.get_rect(center=(screen.get_width()//2, 80))
        screen.blit(title_text, title_rect)
        
        # Subtítulo
        subtitle_text = font_title.render("El cofre ha sido abierto por un agente evolutivo", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(screen.get_width()//2, 130))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Estadísticas principales
        y_pos = 200
        
        # Generación y tick
        gen_text = font_medium.render(f"Generación: {generation}", True, GREEN)
        screen.blit(gen_text, (50, y_pos))
        
        tick_text = font_medium.render(f"Tick: {tick}", True, GREEN)
        screen.blit(tick_text, (300, y_pos))
        
        y_pos += 50
        
        # Estadísticas de fitness
        fitness_title = font_title.render("📊 ESTADÍSTICAS DE FITNESS", True, GOLD)
        screen.blit(fitness_title, (50, y_pos))
        y_pos += 40
        
        fitness_texts = [
            f"Fitness máximo: {max_fitness:.1f}",
            f"Fitness promedio: {avg_fitness:.1f}",
            f"Agentes vivos: {len(alive_agents)}/{total_agents}"
        ]
        
        for text in fitness_texts:
            fitness_text = font_small.render(text, True, WHITE)
            screen.blit(fitness_text, (70, y_pos))
            y_pos += 30
        
        y_pos += 20
        
        # Estadísticas de comida
        food_title = font_title.render("🍎 ESTADÍSTICAS DE COMIDA", True, GOLD)
        screen.blit(food_title, (50, y_pos))
        y_pos += 40
        
        food_texts = [
            f"Manzanas máximas comidas: {max_food}",
            f"Manzanas promedio comidas: {avg_food:.1f}",
            f"Árboles cortados: {trees_cut}"
        ]
        
        for text in food_texts:
            food_text = font_small.render(text, True, WHITE)
            screen.blit(food_text, (70, y_pos))
            y_pos += 30
        
        y_pos += 20
        
        # Estadísticas de supervivencia
        survival_title = font_title.render("⏱️ ESTADÍSTICAS DE SUPERVIVENCIA", True, GOLD)
        screen.blit(survival_title, (50, y_pos))
        y_pos += 40
        
        survival_texts = [
            f"Tiempo máximo de supervivencia: {max_survival:.1f} min",
            f"Tiempo promedio de supervivencia: {avg_survival:.1f} min",
            f"Obstáculos evitados: {obstacles_avoided}"
        ]
        
        for text in survival_texts:
            survival_text = font_small.render(text, True, WHITE)
            screen.blit(survival_text, (70, y_pos))
            y_pos += 30
        
        y_pos += 20
        
        # Estadísticas de exploración
        exploration_title = font_title.render("🗺️ ESTADÍSTICAS DE EXPLORACIÓN", True, GOLD)
        screen.blit(exploration_title, (50, y_pos))
        y_pos += 40
        
        exploration_texts = [
            f"Distancia máxima recorrida: {max_exploration:.0f} píxeles",
            f"Distancia promedio recorrida: {avg_exploration:.0f} píxeles"
        ]
        
        for text in exploration_texts:
            exploration_text = font_small.render(text, True, WHITE)
            screen.blit(exploration_text, (70, y_pos))
            y_pos += 30
        
        y_pos += 20
        
        # Estadísticas de fortalezas
        fortress_title = font_title.render("🏰 ESTADÍSTICAS DE FORTALEZAS", True, GOLD)
        screen.blit(fortress_title, (50, y_pos))
        y_pos += 40
        
        fortress_texts = [
            f"Llaves rojas recogidas: {red_keys_collected}",
            f"Llaves doradas recogidas: {gold_keys_collected}",
            f"Puertas abiertas: {doors_opened}"
        ]
        
        for text in fortress_texts:
            fortress_text = font_small.render(text, True, WHITE)
            screen.blit(fortress_text, (70, y_pos))
            y_pos += 30
        
        y_pos += 40
        
        # Mensaje final
        final_text = font_medium.render("🎯 ¡Los agentes evolutivos han completado su misión!", True, GREEN)
        final_rect = final_text.get_rect(center=(screen.get_width()//2, y_pos))
        screen.blit(final_text, final_rect)
        
        y_pos += 50
        
        # Instrucciones
        instructions_text = font_small.render("Presiona ESC o ENTER para salir", True, WHITE)
        instructions_rect = instructions_text.get_rect(center=(screen.get_width()//2, y_pos))
        screen.blit(instructions_text, instructions_rect)
        
        pygame.display.flip()
    
    # Cerrar pygame
    pygame.quit()


if __name__ == "__main__":
    main()
