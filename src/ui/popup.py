"""
Popup de resumen de generación.
"""

import pygame


class SummaryPopup:
    """Cuadro de resumen de generación."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = 800  # Más compacto
        self.height = 600  # Más compacto
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.visible = False
        self.generation_data = None
        self.fitness_history = []
        
        # Fuentes más pequeñas
        self.font = pygame.font.Font(None, 16)  # Más pequeña
        self.title_font = pygame.font.Font(None, 22)  # Más pequeña
        self.big_font = pygame.font.Font(None, 18)  # Más pequeña
    
    def show(self, generation_data, fitness_history):
        """Muestra el cuadro de resumen."""
        self.visible = True
        self.generation_data = generation_data
        self.fitness_history = fitness_history.copy()
    
    def hide(self):
        """Oculta el cuadro de resumen."""
        self.visible = False
        self.generation_data = None
    
    def handle_click(self, pos):
        """Maneja clicks en el cuadro."""
        if not self.visible:
            return False
            
        # Verificar click en botón cerrar (coordenadas fijas)
        close_button_x = self.x + self.width - 120
        close_button_y = self.y + self.height - 50
        close_button_width = 100
        close_button_height = 30
        
        if (close_button_x <= pos[0] <= close_button_x + close_button_width and 
            close_button_y <= pos[1] <= close_button_y + close_button_height):
            self.hide()
            return True
            
        # Verificar click en el cuadro (NO cerrar automáticamente)
        if (self.x <= pos[0] <= self.x + self.width and 
            self.y <= pos[1] <= self.y + self.height):
            return True  # Click detectado pero no cierra
            
        return False
    
    def add_object_at_coordinates(self, x, y, object_type, world):
        """Añade un objeto en las coordenadas especificadas (automáticamente alineado a tiles)."""
        # Alinear automáticamente a la grilla de tiles (16x16)
        tile_x = (x // 16) * 16
        tile_y = (y // 16) * 16
        
        if object_type == "tree":
            from ..world.obstacles import Obstacle
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "tree")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🌳 Árbol añadido en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "wall":
            from ..world.obstacles import Obstacle
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "wall")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🧱 Pared añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "water":
            from ..world.obstacles import Obstacle
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "water")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"💧 Agua añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "hut":
            from ..world.obstacles import Obstacle
            obstacle = Obstacle(tile_x, tile_y, 20, 20, "hut")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🏠 Casa añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "potion":
            from ..world.obstacles import Obstacle
            obstacle = Obstacle(tile_x, tile_y, 16, 16, "potion")
            world.obstacles.append(obstacle)
            world.manual_obstacles.append(obstacle)  # Guardar como manual
            print(f"🧪 Poción añadida en tile ({tile_x}, {tile_y}) - PERMANENTE")
        elif object_type == "apple":
            world.food_items.append({'x': tile_x, 'y': tile_y, 'eaten': False})
            print(f"🍎 Manzana añadida en tile ({tile_x}, {tile_y}) - TEMPORAL")
        else:
            print(f"❌ Tipo de objeto '{object_type}' no reconocido")
            print("💡 Tipos disponibles: tree, wall, water, hut, potion, apple")
    
    def draw(self, screen):
        """Dibuja el cuadro de resumen."""
        if not self.visible or not self.generation_data:
            return
        
        # Crear superficie semi-transparente
        popup_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        popup_surface.fill((0, 0, 0, 200))  # Fondo semi-transparente
        
        # Título
        title = self.title_font.render(f"GENERACIÓN {self.generation_data['generation']} COMPLETADA", True, (100, 255, 150))
        popup_surface.blit(title, (20, 20))
        
        # Línea separadora
        pygame.draw.line(popup_surface, (100, 255, 150), (20, 50), (self.width - 20, 50), 2)
        
        # Contenido más compacto - 2 columnas
        y_offset = 70
        
        # Columna izquierda
        left_x = 20
        right_x = self.width // 2 + 20
        
        # FITNESS
        fitness_title = self.big_font.render("FITNESS", True, (100, 255, 150))
        popup_surface.blit(fitness_title, (left_x, y_offset))
        y_offset += 25
        
        fitness_stats = [
            f"Promedio: {self.generation_data['avg_fitness']:.1f}/100",
            f"Máximo: {self.generation_data['max_fitness']:.1f}/100"
        ]
        
        for stat in fitness_stats:
            text = self.font.render(stat, True, (200, 200, 200))
            popup_surface.blit(text, (left_x + 10, y_offset))
            y_offset += 18
        
        # COMPORTAMIENTO
        behavior_title = self.big_font.render("COMPORTAMIENTO", True, (100, 255, 150))
        popup_surface.blit(behavior_title, (left_x, y_offset + 10))
        y_offset += 35
        
        behavior_stats = [
            f"Vida: {self.generation_data['avg_age']/60:.1f} min",
            f"Comida: {self.generation_data['avg_food']:.1f}"
        ]
        
        for stat in behavior_stats:
            text = self.font.render(stat, True, (200, 200, 200))
            popup_surface.blit(text, (left_x + 10, y_offset))
            y_offset += 18
        
        # Columna derecha
        y_offset = 70
        
        # EFICIENCIA
        efficiency_title = self.big_font.render("EFICIENCIA", True, (100, 255, 150))
        popup_surface.blit(efficiency_title, (right_x, y_offset))
        y_offset += 25
        
        efficiency_stats = [
            f"Exploración: {self.generation_data['avg_exploration']:.0f} px",
            f"Supervivencia: {self.generation_data['survival_rate']:.1f}%"
        ]
        
        for stat in efficiency_stats:
            text = self.font.render(stat, True, (200, 200, 200))
            popup_surface.blit(text, (right_x + 10, y_offset))
            y_offset += 18
        
        # HABILIDADES
        skills_title = self.big_font.render("HABILIDADES (%)", True, (100, 255, 150))
        popup_surface.blit(skills_title, (right_x, y_offset + 10))
        y_offset += 35
        
        # Contar árboles cortados
        trees_cut = self.generation_data.get('trees_cut', 0)
        
        skills_stats = [
            f"Movimiento: {self.generation_data['avg_movement_skill']:.1f}%",
            f"Comida: {self.generation_data['avg_food_skill']:.1f}%",
            f"Obstáculos: {self.generation_data['avg_obstacle_skill']:.1f}%",
            f"Árboles cortados: {trees_cut}"
        ]
        
        for stat in skills_stats:
            text = self.font.render(stat, True, (200, 200, 200))
            popup_surface.blit(text, (right_x + 10, y_offset))
            y_offset += 18
        
        # Gráfico de evolución (más alto y menos ancho)
        self._draw_fitness_graph(popup_surface, 280)  # Posición ajustada para el gráfico más alto
        
        # Botón cerrar
        close_button = pygame.Rect(self.width - 120, self.height - 50, 100, 30)
        pygame.draw.rect(popup_surface, (200, 50, 50), close_button)
        pygame.draw.rect(popup_surface, (255, 255, 255), close_button, 2)
        
        close_text = self.font.render("CERRAR", True, (255, 255, 255))
        text_rect = close_text.get_rect(center=close_button.center)
        popup_surface.blit(close_text, text_rect)
        
        # Dibujar en pantalla
        screen.blit(popup_surface, (self.x, self.y))
    
    def _draw_fitness_graph(self, surface, y_start):
        """Dibuja un gráfico con escalas del fitness por generación."""
        if len(self.fitness_history) < 2:
            return
            
        graph_width = self.width - 120  # Más corto (menos ancho)
        graph_height = 120  # Más alto (doble de altura)
        graph_x = 60  # Más espacio a la izquierda para etiquetas
        graph_y = y_start
        
        # Fondo del gráfico
        pygame.draw.rect(surface, (40, 40, 60), (graph_x, graph_y, graph_width, graph_height))
        pygame.draw.rect(surface, (100, 100, 100), (graph_x, graph_y, graph_width, graph_height), 1)
        
        # Escala fija del 0 al 100 para fitness
        min_fitness = 0
        max_fitness = 100
        
        # Dibujar líneas de cuadrícula
        for i in range(0, 101, 20):  # Líneas cada 20 puntos
            y = graph_y + graph_height - int((i / 100) * graph_height)
            color = (60, 60, 80) if i % 40 == 0 else (50, 50, 70)  # Líneas más marcadas cada 40
            pygame.draw.line(surface, color, (graph_x, y), (graph_x + graph_width, y), 1)
        
        # Dibujar línea de datos
        points = []
        for i, fitness in enumerate(self.fitness_history):
            x = graph_x + (i * graph_width) // (len(self.fitness_history) - 1)
            y = graph_y + graph_height - int((fitness / 100) * graph_height)
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, (100, 255, 150), False, points, 3)
            
        # Dibujar puntos en cada generación
        for i, (x, y) in enumerate(points):
            pygame.draw.circle(surface, (100, 255, 150), (x, y), 3)
            # Etiqueta de generación
            gen_text = self.font.render(f"G{i+1}", True, (150, 150, 150))
            surface.blit(gen_text, (x - 10, graph_y + graph_height + 5))
        
        # Etiquetas del eje Y (fitness) - más espacio
        for i in range(0, 101, 20):
            y = graph_y + graph_height - int((i / 100) * graph_height)
            fitness_text = self.font.render(f"{i}", True, (150, 150, 150))
            surface.blit(fitness_text, (graph_x - 35, y - 8))  # Más espacio a la izquierda
        
        # Título de los ejes
        y_label = self.font.render("FITNESS", True, (100, 255, 150))
        surface.blit(y_label, (10, graph_y + graph_height//2 - 20))  # Más espacio
        
        x_label = self.font.render("GENERACIONES", True, (100, 255, 150))
        surface.blit(x_label, (graph_x + graph_width//2 - 50, graph_y + graph_height + 15))  # Más cerca
