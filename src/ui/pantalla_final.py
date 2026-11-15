"""
Pantalla final: el resumen de la corrida. Sin ventana, por consola; con ventana, un cuadro sobre el
último cuadro de la simulación, hasta que se aprieta ESC o ENTER.
"""

import pygame

from config import SimulationConfig
from ..agents.advanced_agent import agentes_por_paso
from ..analytics.clustering import BehaviorClusterer
from .renderer import dibujar_mundo

VERDE = (100, 255, 150)
GRIS = (200, 200, 200)
GRIS_OSCURO = (150, 150, 150)


def minutos_simulados(ticks_totales):
    """Los ticks de todas las generaciones, a 60 por segundo, en minutos (DIAG-15)."""
    return ticks_totales / 60 / 60


def mostrar_pantalla_final(render_surface, generation, tick, agents, world, learning_monitor,
                           screen_width, screen_height, display_screen, sprite_manager,
                           particle_system, ticks_totales, primera_generacion_cofre, agentes_con_cofre):
    """Muestra el resumen final. Lee SimulationConfig.HEADLESS_MODE de la clase: main.py lo pisa ahí.

    primera_generacion_cofre es None si ningún agente abrió el cofre; agentes_con_cofre suma los de
    todas las generaciones (abrirlo no termina la corrida, decisión 11).
    """
    if SimulationConfig.HEADLESS_MODE:
        imprimir_resumen_final(generation, agents, learning_monitor, ticks_totales,
                               primera_generacion_cofre, agentes_con_cofre)
        return

    learning_monitor.create_learning_report()

    # Se calcula y se dibuja una sola vez: el mundo con el dibujo del loop, los agentes vivos,
    # las partículas quietas y el cuadro (DIAG-17)
    dibujar_mundo(render_surface, world, sprite_manager, tick)
    for agent in agents:
        if agent.alive:
            agent.draw(render_surface, tick, sprite_manager, particle_system)
    particle_system.draw(render_surface)

    textos = textos_del_cuadro(generation, agents, learning_monitor, ticks_totales,
                               primera_generacion_cofre, agentes_con_cofre)
    cuadro = _dibujar_cuadro(textos, learning_monitor, primera_generacion_cofre is not None)
    panel_x = (render_surface.get_width() - cuadro.get_width()) // 2 - 113
    panel_y = (render_surface.get_height() - cuadro.get_height()) // 2
    render_surface.blit(cuadro, (panel_x, panel_y))
    display_screen.blit(pygame.transform.scale(render_surface, (screen_width, screen_height)), (0, 0))

    # El loop solo atiende eventos y muestra lo ya dibujado
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                running = False
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def imprimir_resumen_final(generation, agents, learning_monitor, ticks_totales,
                           primera_generacion_cofre, agentes_con_cofre):
    """El resumen final por consola, para las corridas sin ventana."""
    cofre_abierto = primera_generacion_cofre is not None
    # Recalcular fitness de todos los agentes antes de mostrar estadísticas
    for agent in agents:
        agent._calculate_fitness()

    alive_agents = [a for a in agents if a.alive]
    max_fitness = max(agent.fitness for agent in agents) if agents else 0.0

    # Promedio de las últimas 3 generaciones (o de las que haya); sin historial, el de ahora
    ultimas = learning_monitor.generation_data[-3:]
    if ultimas:
        avg_fitness = sum(g.get('avg_fitness', 0) for g in ultimas) / len(ultimas)
    else:
        avg_fitness = sum(agent.fitness for agent in agents) / len(agents) if agents else 0.0

    if cofre_abierto:
        status_title = "¡MISIÓN COMPLETADA!"
        status_subtitle = "El cofre ha sido abierto por un agente evolutivo."
    else:
        status_title = "Simulación finalizada"
        status_subtitle = "Se alcanzó el límite de generaciones sin abrir el cofre."

    print(f"\n {status_title}")
    print(f"Generación: {generation}")
    print(f"Tiempo simulado: {minutos_simulados(ticks_totales):.1f} minutos")
    print(f"Agentes vivos: {len(alive_agents)}")
    print(status_subtitle)
    print(_texto_del_cofre(primera_generacion_cofre, agentes_con_cofre))
    print(f"Fitness promedio (últimas 3 gen): {avg_fitness:.1f}")
    print(f"Fitness máximo: {max_fitness:.1f}")


def _texto_del_cofre(primera_generacion_cofre, agentes_con_cofre):
    """Cuántos agentes abrieron el cofre en la corrida y cuándo pasó la primera vez (decisión 11)."""
    if primera_generacion_cofre is None:
        return "Ningún agente abrió el cofre"
    return (f"Cofre: lo abrieron {agentes_con_cofre} agentes en la corrida; la primera vez, en la "
            f"generación {primera_generacion_cofre}")


def textos_del_cuadro(generation, agents, learning_monitor, ticks_totales, primera_generacion_cofre,
                      agentes_con_cofre):
    """Arma los textos del cuadro final sin dibujar nada, así se pueden probar (DIAG-16).

    Devuelve un dict con titulo, subtitulo, encabezado (generación y tiempo), secciones (lista de
    (título, [(texto, color), ...])) y mensaje_final.
    """
    cofre_abierto = primera_generacion_cofre is not None
    datos = learning_monitor.generation_data
    minutos = minutos_simulados(ticks_totales)

    if cofre_abierto:
        titulo = "¡MISIÓN COMPLETADA!"
        subtitulo = "El cofre ha sido abierto por un agente evolutivo"
    else:
        titulo = "Simulación finalizada"
        subtitulo = "Se alcanzó el límite de generaciones sin abrir el cofre"

    secciones = []

    # 1) Objetivo y resultado
    secciones.append(("OBJETIVO", [
        ("Objetivo: Abrir el cofre", GRIS),
        ("Resultado: Completado", (200, 255, 200)) if cofre_abierto else ("Resultado: No logrado", GRIS),
    ]))

    # 2) Pasos clave del reto: cuántos agentes de la última generación llegaron a cada uno
    roja, madera, dorada, hierro, cofre = agentes_por_paso(agents)
    secciones.append(("PASOS CLAVE", [
        ("Agentes de la última generación que llegaron a cada paso:", GRIS),
        (f"Llave roja: {roja}   Puerta madera: {madera}   Llave dorada: {dorada}", GRIS),
        (f"Puerta hierro: {hierro}   Cofre: {cofre}", GRIS),
    ]))

    # 3) La corrida: la generación 1 contra las últimas 3 (o las que haya; main.py registra cada
    # generación antes de llegar acá). Si aprendieron no se ve acá: la línea base sin evolución sube
    # también (LEC-001, decisión 25)
    ultimas = datos[-3:]
    fitness_inicio, manzanas_inicio = datos[0].get('avg_fitness', 0), datos[0].get('avg_food', 0)
    fitness_final = sum(g.get('avg_fitness', 0) for g in ultimas) / len(ultimas)
    manzanas_final = sum(g.get('avg_food', 0) for g in ultimas) / len(ultimas)
    # La fuente de pygame no tiene el glifo de la flecha: en pantalla va "->"
    secciones.append(("LA CORRIDA", [
        (f"Fitness prom.: gen 1 {fitness_inicio:.1f} -> últimas {len(ultimas)} {fitness_final:.1f}", GRIS),
        (f"Manzanas por agente: gen 1 {manzanas_inicio:.1f} -> últimas {len(ultimas)} "
         f"{manzanas_final:.1f}", GRIS),
        ("Si aprendieron se mide contra la línea base: python experimento.py", GRIS),
    ]))

    # 4) Línea de tiempo. Abrir el cofre no termina la corrida (decisión 11): la primera vez y cuántos
    if cofre_abierto:
        renglones_cofre = [(f"Primera vez con cofre abierto: Gen {primera_generacion_cofre}", GRIS),
                           (f"Agentes que abrieron el cofre en la corrida: {agentes_con_cofre}", GRIS)]
    else:
        renglones_cofre = [("El cofre no se abrió en ninguna generación", GRIS)]
    secciones.append(("LÍNEA DE TIEMPO", renglones_cofre + [
        (f"Tiempo simulado: {minutos:.1f} min", GRIS),
    ]))

    # 5) Top agente, con el id por contador de la corrida (decisión 24): entero, sin recortar
    renglones_top = []
    top_agent = max(agents, key=lambda a: a.fitness) if agents else None
    if top_agent:
        top_km = top_agent.distance_traveled / 100 / 1000  # px -> m -> km (1px=1cm)
        top_fitness_capped = min(100.0, getattr(top_agent, 'fitness', 0.0))
        renglones_top.append((f"Agente #{top_agent.id}: fitness {top_fitness_capped:.1f}, comida "
                              f"{top_agent.food_eaten} manzanas, recorrio {top_km:.2f} km", GRIS))
    secciones.append(("TOP AGENTE", renglones_top))

    # 6) Sello de movimiento
    try:
        avg_sr = sum(getattr(a, 'metric_sr', 0.0) for a in agents) / len(agents) if agents else 0.0
        movement_flag = "Mas recto y con menos vueltas" if avg_sr >= 0.5 else "Aun con vueltas"
    except Exception:
        movement_flag = "Aun con vueltas"
    secciones.append(("MOVIMIENTO", [(movement_flag, GRIS)]))

    # 7) Clustering de la última generación
    secciones.append(("CLUSTERING", _renglones_de_clustering(agents)))

    if cofre_abierto:
        mensaje_final = "¡Los agentes evolutivos han completado su misión!"
    else:
        mensaje_final = "Los agentes no llegaron a abrir el cofre"

    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "encabezado": [f"Generación: {generation}", f"Tiempo simulado: {minutos:.1f} min"],
        "secciones": secciones,
        "mensaje_final": mensaje_final,
    }


def _renglones_de_clustering(agents):
    """Hasta tres renglones: cada estrategia con su porcentaje, cantidad y fitness."""
    try:
        if not agents or len(agents) < 3:
            return [("No disponible (pocos agentes)", GRIS_OSCURO)]
        clusterer = BehaviorClusterer(n_clusters=3)
        _, cluster_stats = clusterer.cluster_agents(agents)
        interpretations = clusterer.get_cluster_interpretation(cluster_stats)

        # Ordenar clusters por tipo
        cluster_order = ["Exploradores", "Recolectores", "Exitosos"]
        sorted_clusters = []
        for cluster_id, count in cluster_stats['cluster_counts'].items():
            if count > 0:
                strategy = interpretations.get(cluster_id, f"C{cluster_id}")
                fitness = cluster_stats['cluster_fitness'][cluster_id]['promedio']
                percentage = (count / len(agents)) * 100
                sorted_clusters.append((strategy, count, percentage, fitness))
        sorted_clusters.sort(key=lambda x: (cluster_order.index(x[0]) if x[0] in cluster_order else 999, -x[1]))

        return [(f"{strategy}: {percentage:.1f}% ({count} agentes, fit {fitness:.1f})", GRIS)
                for strategy, count, percentage, fitness in sorted_clusters[:3]]
    except Exception:
        return [("Error en clustering", GRIS_OSCURO)]


def _dibujar_cuadro(textos, learning_monitor, cofre_abierto):
    """El cuadro semitransparente de 800×600 con los textos y el gráfico de fitness."""
    font_large = pygame.font.Font(None, 48)   # Título principal
    font_title = pygame.font.Font(None, 22)   # Secciones
    font_medium = pygame.font.Font(None, 18)  # Subtítulos/ítems destacados
    font_small = pygame.font.Font(None, 16)   # Texto

    panel_width, panel_height = 800, 600
    final_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    final_surface.fill((0, 0, 0, 200))

    # Título (dorado si se abrió el cofre, azul si no), subtítulo y línea separadora
    title_color = (255, 215, 0) if cofre_abierto else (0, 100, 255)
    title_text = font_large.render(textos["titulo"], True, title_color)
    final_surface.blit(title_text, title_text.get_rect(center=(panel_width // 2, 40)))
    subtitle_text = font_medium.render(textos["subtitulo"], True, (255, 255, 255))
    final_surface.blit(subtitle_text, subtitle_text.get_rect(center=(panel_width // 2, 70)))
    pygame.draw.line(final_surface, VERDE, (20, 90), (panel_width - 20, 90), 2)

    grafico = _grafico_de_fitness(learning_monitor, font_small)
    final_surface.blit(grafico, (panel_width - grafico.get_width() - 30, 110))

    # Encabezado: generación y tiempo simulado
    y_pos = 110
    generacion, tiempo = textos["encabezado"]
    final_surface.blit(font_medium.render(generacion, True, VERDE), (30, y_pos))
    final_surface.blit(font_medium.render(tiempo, True, VERDE), (260, y_pos))
    y_pos += 28

    for titulo, renglones in textos["secciones"]:
        final_surface.blit(font_title.render(titulo, True, VERDE), (30, y_pos))
        y_pos += 18
        for texto, color in renglones:
            final_surface.blit(font_small.render(texto, True, color), (40, y_pos))
            y_pos += 18
        y_pos += 2
    y_pos += 6  # Aire antes del mensaje final

    final_text = font_medium.render(textos["mensaje_final"], True, VERDE)
    final_surface.blit(final_text, final_text.get_rect(center=(panel_width // 2, y_pos)))
    y_pos += 26
    instructions_text = font_small.render("Presiona ESC o ENTER para salir", True, (220, 220, 220))
    final_surface.blit(instructions_text, instructions_text.get_rect(center=(panel_width // 2, y_pos)))
    return final_surface


def _grafico_de_fitness(learning_monitor, font_small):
    """Gráfico de 340×220 con el fitness promedio y el máximo de cada generación."""
    chart_width, chart_height = 340, 220
    chart_surface = pygame.Surface((chart_width, chart_height), pygame.SRCALPHA)
    chart_surface.fill((20, 20, 20, 180))

    axis_color = (80, 200, 120)
    grid_color = (70, 70, 70)
    avg_color = (120, 255, 180)
    max_color = (255, 215, 0)

    inner_left, inner_top = 50, 20  # Márgenes: 50 a la izquierda, 20 arriba, 20 a la derecha, 40 abajo
    inner_width = chart_width - inner_left - 20
    inner_height = chart_height - inner_top - 40

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
        y = inner_top + inner_height - int(level / 100.0 * inner_height)
        pygame.draw.line(chart_surface, grid_color, (inner_left, y), (inner_left + inner_width, y), 1)
        chart_surface.blit(font_small.render(f"{level}", True, (180, 180, 180)), (10, y - 8))

    datos = learning_monitor.generation_data
    avg_history = [d.get('avg_fitness', 0.0) for d in datos]
    max_history = [d.get('max_fitness', d.get('avg_fitness', 0.0)) for d in datos]
    gen_count = len(avg_history)

    def _map_point(idx, value):
        if gen_count <= 1:
            x = inner_left + inner_width // 2
        else:
            x = inner_left + int(idx * inner_width / (gen_count - 1))
        value_clamped = max(0.0, min(100.0, float(value)))
        return x, inner_top + inner_height - int((value_clamped / 100.0) * inner_height)

    # Líneas de historia
    if gen_count:
        avg_points = [_map_point(i, val) for i, val in enumerate(avg_history)]
        max_points = [_map_point(i, val) for i, val in enumerate(max_history)]

        if len(avg_points) >= 2:
            pygame.draw.lines(chart_surface, avg_color, False, avg_points, 2)
        else:
            pygame.draw.circle(chart_surface, avg_color, avg_points[0], 3)

        if len(max_points) >= 2:
            pygame.draw.lines(chart_surface, max_color, False, max_points, 2)
        else:
            pygame.draw.circle(chart_surface, max_color, max_points[0], 3)

        # Puntos finales resaltados
        pygame.draw.circle(chart_surface, avg_color, avg_points[-1], 4)
        pygame.draw.circle(chart_surface, max_color, max_points[-1], 4, 1)

        # Etiquetas de generaciones (inicio y fin)
        start_label = font_small.render("Gen 1", True, (180, 180, 180))
        chart_surface.blit(start_label, (inner_left - start_label.get_width() // 2, inner_top + inner_height + 10))
        end_label = font_small.render(f"Gen {gen_count}", True, (180, 180, 180))
        chart_surface.blit(end_label, (inner_left + inner_width - end_label.get_width() // 2,
                                       inner_top + inner_height + 10))

    # Leyenda
    chart_surface.blit(font_small.render("Promedio", True, avg_color), (inner_left + 10, 5))
    chart_surface.blit(font_small.render("Máximo", True, max_color), (inner_left + 120, 5))

    return chart_surface
