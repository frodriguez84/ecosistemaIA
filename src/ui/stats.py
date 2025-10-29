"""
Panel de estadísticas en tiempo real.
"""

import pygame


class StatsPanel:
    """Panel de estadísticas en tiempo real."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 24)
    
    def draw_background(self, screen):
        """Dibuja solo el fondo del panel sin actualizar datos."""
        # Fondo del panel con gradiente
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (25, 25, 40), panel_rect)
        pygame.draw.rect(screen, (60, 60, 90), panel_rect, 3)
        
        # Borde interno más sutil
        inner_rect = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)
        pygame.draw.rect(screen, (40, 40, 60), inner_rect, 1)
        
        # Título con efecto
        title = self.title_font.render("* ECOSISTEMA EVOLUTIVO *", True, (100, 255, 150))
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Línea separadora
        pygame.draw.line(screen, (100, 255, 150), (self.x + 10, self.y + 35), (self.x + self.width - 10, self.y + 35), 2)
    
    def draw(self, screen, generation, agents, world, tick):
        """Dibuja el panel de estadísticas simplificado."""
        # Fondo del panel
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (25, 25, 40), panel_rect)
        pygame.draw.rect(screen, (60, 60, 90), panel_rect, 3)
        
        # Título
        title = self.title_font.render("* ECOSISTEMA *", True, (100, 255, 150))
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Línea separadora
        pygame.draw.line(screen, (100, 255, 150), (self.x + 10, self.y + 35), (self.x + self.width - 10, self.y + 35), 2)
        
        # Calcular estadísticas básicas
        alive_agents = [a for a in agents if a.alive]
        dead_agents = [a for a in agents if not a.alive]
        
        # Mostrar tiempo en formato mm:ss
        total_seconds = tick // 60
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Solo 5 datos básicos
        stats = [
            f"Generación: {generation}",
            f"Tiempo: {time_str}",
            f"Vivos: {len(alive_agents)}",
            f"Muertos: {len(dead_agents)}",
            f"Comida: {len([f for f in world.food_items if not f['eaten']])}"
        ]
        
        # Añadir texto de corte de árboles si está activo
        if hasattr(world, 'axe_picked_up') and world.axe_picked_up:
            stats.append("* Pueden cortar árboles!")
        
        # Añadir texto de llaves recogidas
        if hasattr(world, 'red_key_collected') and world.red_key_collected:
            stats.append("* Pueden abrir puerta madera!")
        if hasattr(world, 'gold_key_collected') and world.gold_key_collected:
            stats.append("* Pueden abrir puerta hierro!")
        
        # Dibujar estadísticas
        y_offset = 50
        for stat in stats:
            text = self.font.render(stat, True, (200, 200, 200))
            screen.blit(text, (self.x + 10, self.y + y_offset))
            y_offset += 25
