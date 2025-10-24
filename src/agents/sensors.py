"""
Sistema de sensores para agentes del ecosistema evolutivo.
Permite a los agentes percibir su entorno.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class SensorType(Enum):
    """Tipos de sensores disponibles."""
    VISION = "vision"
    ENERGY = "energy"
    DISTANCE = "distance"
    COLLISION = "collision"
    FOOD_DETECTION = "food_detection"
    AGENT_DETECTION = "agent_detection"


class VisionSensor:
    """Sensor de visión que detecta objetos en un radio."""
    
    def __init__(self, vision_range: float, vision_angle: float = 360.0, resolution: int = 8):
        """
        Inicializa el sensor de visión.
        
        Args:
            vision_range: Radio de visión
            vision_angle: Ángulo de visión en grados
            resolution: Número de rayos de visión
        """
        self.vision_range = vision_range
        self.vision_angle = np.radians(vision_angle)
        self.resolution = resolution
        self.ray_angles = np.linspace(0, self.vision_angle, resolution)
    
    def sense(self, agent_x: float, agent_y: float, agent_angle: float, 
              environment) -> np.ndarray:
        """
        Realiza la detección visual.
        
        Args:
            agent_x: Posición X del agente
            agent_y: Posición Y del agente
            agent_angle: Ángulo del agente
            environment: Entorno donde buscar
            
        Returns:
            Array con distancias detectadas
        """
        distances = np.zeros(self.resolution)
        
        for i, ray_angle in enumerate(self.ray_angles):
            # Ángulo absoluto del rayo
            absolute_angle = agent_angle + ray_angle
            
            # Calcular punto final del rayo
            end_x = agent_x + np.cos(absolute_angle) * self.vision_range
            end_y = agent_y + np.sin(absolute_angle) * self.vision_range
            
            # Buscar colisión en el rayo
            distance = environment.raycast(agent_x, agent_y, end_x, end_y)
            distances[i] = distance / self.vision_range  # Normalizar
        
        return distances


class EnergySensor:
    """Sensor que detecta el nivel de energía del agente."""
    
    def __init__(self, energy_max: float = 100.0):
        """
        Inicializa el sensor de energía.
        
        Args:
            energy_max: Energía máxima del agente
        """
        self.energy_max = energy_max
    
    def sense(self, agent_energy: float) -> float:
        """
        Detecta el nivel de energía.
        
        Args:
            agent_energy: Energía actual del agente
            
        Returns:
            Nivel de energía normalizado (0.0 a 1.0)
        """
        return agent_energy / self.energy_max


class DistanceSensor:
    """Sensor que detecta la distancia a objetos específicos."""
    
    def __init__(self, max_distance: float = 50.0):
        """
        Inicializa el sensor de distancia.
        
        Args:
            max_distance: Distancia máxima a detectar
        """
        self.max_distance = max_distance
    
    def sense_distance_to_food(self, agent_x: float, agent_y: float, 
                              food_positions: List[Tuple[float, float]]) -> float:
        """
        Detecta la distancia a la comida más cercana.
        
        Args:
            agent_x: Posición X del agente
            agent_y: Posición Y del agente
            food_positions: Lista de posiciones de comida
            
        Returns:
            Distancia normalizada a la comida más cercana
        """
        if not food_positions:
            return 1.0  # No hay comida
        
        min_distance = float('inf')
        for food_x, food_y in food_positions:
            distance = np.sqrt((agent_x - food_x)**2 + (agent_y - food_y)**2)
            min_distance = min(min_distance, distance)
        
        return min(min_distance / self.max_distance, 1.0)
    
    def sense_distance_to_agents(self, agent_x: float, agent_y: float, 
                                 other_agents: List[Dict[str, Any]]) -> float:
        """
        Detecta la distancia al agente más cercano.
        
        Args:
            agent_x: Posición X del agente
            agent_y: Posición Y del agente
            other_agents: Lista de otros agentes
            
        Returns:
            Distancia normalizada al agente más cercano
        """
        if not other_agents:
            return 1.0  # No hay otros agentes
        
        min_distance = float('inf')
        for agent in other_agents:
            distance = np.sqrt((agent_x - agent['x'])**2 + (agent_y - agent['y'])**2)
            min_distance = min(min_distance, distance)
        
        return min(min_distance / self.max_distance, 1.0)


class CollisionSensor:
    """Sensor que detecta colisiones inminentes."""
    
    def __init__(self, collision_threshold: float = 5.0):
        """
        Inicializa el sensor de colisión.
        
        Args:
            collision_threshold: Distancia de detección de colisión
        """
        self.collision_threshold = collision_threshold
    
    def sense(self, agent_x: float, agent_y: float, agent_angle: float,
              environment) -> float:
        """
        Detecta colisiones inminentes.
        
        Args:
            agent_x: Posición X del agente
            agent_y: Posición Y del agente
            agent_angle: Ángulo del agente
            environment: Entorno donde verificar
            
        Returns:
            Probabilidad de colisión (0.0 a 1.0)
        """
        # Verificar colisión en la dirección del movimiento
        future_x = agent_x + np.cos(agent_angle) * self.collision_threshold
        future_y = agent_y + np.sin(agent_angle) * self.collision_threshold
        
        if environment.check_collision(future_x, future_y):
            return 1.0
        else:
            return 0.0


class SensorArray:
    """Array de sensores para un agente."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el array de sensores.
        
        Args:
            config: Configuración de sensores
        """
        self.sensors = {}
        self.sensor_order = []
        
        # Crear sensores según configuración
        if config.get('vision', {}).get('enabled', True):
            vision_config = config['vision']
            self.sensors['vision'] = VisionSensor(
                vision_range=vision_config.get('range', 5.0),
                vision_angle=vision_config.get('angle', 360.0),
                resolution=vision_config.get('resolution', 8)
            )
            self.sensor_order.append('vision')
        
        if config.get('energy', {}).get('enabled', True):
            energy_config = config['energy']
            self.sensors['energy'] = EnergySensor(
                energy_max=energy_config.get('max', 100.0)
            )
            self.sensor_order.append('energy')
        
        if config.get('distance', {}).get('enabled', True):
            distance_config = config['distance']
            self.sensors['distance'] = DistanceSensor(
                max_distance=distance_config.get('max', 50.0)
            )
            self.sensor_order.append('distance')
        
        if config.get('collision', {}).get('enabled', True):
            collision_config = config['collision']
            self.sensors['collision'] = CollisionSensor(
                collision_threshold=collision_config.get('threshold', 5.0)
            )
            self.sensor_order.append('collision')
    
    def sense_all(self, agent, environment) -> np.ndarray:
        """
        Ejecuta todos los sensores y retorna percepciones.
        
        Args:
            agent: Agente que percibe
            environment: Entorno a percibir
            
        Returns:
            Array con todas las percepciones
        """
        perceptions = []
        
        for sensor_name in self.sensor_order:
            sensor = self.sensors[sensor_name]
            
            if sensor_name == 'vision':
                vision_data = sensor.sense(agent.x, agent.y, agent.angle, environment)
                perceptions.extend(vision_data)
            
            elif sensor_name == 'energy':
                energy_data = sensor.sense(agent.energy)
                perceptions.append(energy_data)
            
            elif sensor_name == 'distance':
                food_positions = environment.get_food_positions()
                distance_to_food = sensor.sense_distance_to_food(
                    agent.x, agent.y, food_positions
                )
                perceptions.append(distance_to_food)
                
                other_agents = environment.get_other_agents(agent)
                distance_to_agents = sensor.sense_distance_to_agents(
                    agent.x, agent.y, other_agents
                )
                perceptions.append(distance_to_agents)
            
            elif sensor_name == 'collision':
                collision_data = sensor.sense(agent.x, agent.y, agent.angle, environment)
                perceptions.append(collision_data)
        
        return np.array(perceptions, dtype=np.float32)
    
    def get_sensor_count(self) -> int:
        """
        Obtiene el número total de percepciones.
        
        Returns:
            Número de percepciones
        """
        total = 0
        for sensor_name in self.sensor_order:
            sensor = self.sensors[sensor_name]
            if sensor_name == 'vision':
                total += sensor.resolution
            elif sensor_name == 'energy':
                total += 1
            elif sensor_name == 'distance':
                total += 2  # Distancia a comida y a otros agentes
            elif sensor_name == 'collision':
                total += 1
        
        return total
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre los sensores.
        
        Returns:
            Diccionario con información de sensores
        """
        info = {
            'sensors': list(self.sensors.keys()),
            'total_perceptions': self.get_sensor_count(),
            'sensor_details': {}
        }
        
        for sensor_name, sensor in self.sensors.items():
            if sensor_name == 'vision':
                info['sensor_details'][sensor_name] = {
                    'type': 'vision',
                    'range': sensor.vision_range,
                    'angle': sensor.vision_angle,
                    'resolution': sensor.resolution
                }
            elif sensor_name == 'energy':
                info['sensor_details'][sensor_name] = {
                    'type': 'energy',
                    'max_energy': sensor.energy_max
                }
            elif sensor_name == 'distance':
                info['sensor_details'][sensor_name] = {
                    'type': 'distance',
                    'max_distance': sensor.max_distance
                }
            elif sensor_name == 'collision':
                info['sensor_details'][sensor_name] = {
                    'type': 'collision',
                    'threshold': sensor.collision_threshold
                }
        
        return info
