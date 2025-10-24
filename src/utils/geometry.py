"""
Utilidades geométricas para el ecosistema evolutivo.
Funciones para cálculos 2D y geometría.
"""

import numpy as np
from typing import Tuple, List


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula la distancia euclidiana entre dos puntos.
    
    Args:
        x1, y1: Coordenadas del primer punto
        x2, y2: Coordenadas del segundo punto
        
    Returns:
        Distancia entre los puntos
    """
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calculate_angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula el ángulo entre dos puntos.
    
    Args:
        x1, y1: Coordenadas del primer punto
        x2, y2: Coordenadas del segundo punto
        
    Returns:
        Ángulo en radianes
    """
    return np.arctan2(y2 - y1, x2 - x1)


def normalize_angle(angle: float) -> float:
    """
    Normaliza un ángulo al rango [0, 2π].
    
    Args:
        angle: Ángulo en radianes
        
    Returns:
        Ángulo normalizado
    """
    return angle % (2 * np.pi)


def point_in_circle(px: float, py: float, cx: float, cy: float, radius: float) -> bool:
    """
    Verifica si un punto está dentro de un círculo.
    
    Args:
        px, py: Coordenadas del punto
        cx, cy: Coordenadas del centro del círculo
        radius: Radio del círculo
        
    Returns:
        True si el punto está dentro del círculo
    """
    return calculate_distance(px, py, cx, cy) <= radius


def point_in_rectangle(px: float, py: float, rx: float, ry: float, 
                      width: float, height: float) -> bool:
    """
    Verifica si un punto está dentro de un rectángulo.
    
    Args:
        px, py: Coordenadas del punto
        rx, ry: Coordenadas de la esquina superior izquierda del rectángulo
        width: Ancho del rectángulo
        height: Alto del rectángulo
        
    Returns:
        True si el punto está dentro del rectángulo
    """
    return (rx <= px <= rx + width and ry <= py <= ry + height)


def line_intersects_circle(x1: float, y1: float, x2: float, y2: float,
                          cx: float, cy: float, radius: float) -> bool:
    """
    Verifica si una línea intersecta un círculo.
    
    Args:
        x1, y1: Coordenadas del primer punto de la línea
        x2, y2: Coordenadas del segundo punto de la línea
        cx, cy: Coordenadas del centro del círculo
        radius: Radio del círculo
        
    Returns:
        True si la línea intersecta el círculo
    """
    # Calcular distancia del punto a la línea
    A = y2 - y1
    B = x1 - x2
    C = x2 * y1 - x1 * y2
    
    distance = abs(A * cx + B * cy + C) / np.sqrt(A**2 + B**2)
    
    return distance <= radius


def calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
    """
    Calcula el área de un polígono usando la fórmula de Shoelace.
    
    Args:
        points: Lista de puntos (x, y) del polígono
        
    Returns:
        Área del polígono
    """
    if len(points) < 3:
        return 0.0
    
    area = 0.0
    n = len(points)
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0


def rotate_point(px: float, py: float, cx: float, cy: float, angle: float) -> Tuple[float, float]:
    """
    Rota un punto alrededor de un centro.
    
    Args:
        px, py: Coordenadas del punto a rotar
        cx, cy: Coordenadas del centro de rotación
        angle: Ángulo de rotación en radianes
        
    Returns:
        Coordenadas del punto rotado
    """
    # Trasladar al origen
    x = px - cx
    y = py - cy
    
    # Rotar
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    # Trasladar de vuelta
    return new_x + cx, new_y + cy


def calculate_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """
    Calcula el rectángulo delimitador de una lista de puntos.
    
    Args:
        points: Lista de puntos (x, y)
        
    Returns:
        Tupla (min_x, min_y, max_x, max_y)
    """
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    
    return min(x_coords), min(y_coords), max(x_coords), max(y_coords)
