"""
Sistema de actuadores para agentes del ecosistema evolutivo.
Permite a los agentes realizar acciones en el entorno.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from enum import Enum
from .brain.policy import ActionType, ActionExecutor


class ActuatorType(Enum):
    """Tipos de actuadores disponibles."""
    MOVEMENT = "movement"
    ROTATION = "rotation"
    FEEDING = "feeding"
    REPRODUCTION = "reproduction"


class MovementActuator:
    """Actuador de movimiento para agentes."""
    
    def __init__(self, max_speed: float = 2.0, acceleration: float = 0.5):
        """
        Inicializa el actuador de movimiento.
        
        Args:
            max_speed: Velocidad máxima del agente
            acceleration: Aceleración del agente
        """
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.current_speed = 0.0
    
    def move_forward(self, agent, distance: float = None) -> Dict[str, Any]:
        """
        Mueve el agente hacia adelante.
        
        Args:
            agent: Agente a mover
            distance: Distancia a mover (opcional)
            
        Returns:
            Resultado del movimiento
        """
        if distance is None:
            distance = self.max_speed
        
        # Calcular nueva posición
        dx = np.cos(agent.angle) * distance
        dy = np.sin(agent.angle) * distance
        
        new_x = agent.x + dx
        new_y = agent.y + dy
        
        # Verificar límites del mundo
        world_width = getattr(agent, 'world_width', 100)
        world_height = getattr(agent, 'world_height', 100)
        
        # Mantener dentro de los límites
        new_x = max(0, min(new_x, world_width))
        new_y = max(0, min(new_y, world_height))
        
        # Actualizar posición
        old_x, old_y = agent.x, agent.y
        agent.x = new_x
        agent.y = new_y
        
        # Calcular distancia real movida
        actual_distance = np.sqrt((new_x - old_x)**2 + (new_y - old_y)**2)
        
        return {
            'success': True,
            'old_position': (old_x, old_y),
            'new_position': (new_x, new_y),
            'distance_moved': actual_distance,
            'energy_cost': actual_distance * agent.energy_move_cost
        }
    
    def move_to_position(self, agent, target_x: float, target_y: float) -> Dict[str, Any]:
        """
        Mueve el agente hacia una posición específica.
        
        Args:
            agent: Agente a mover
            target_x: Posición X objetivo
            target_y: Posición Y objetivo
            
        Returns:
            Resultado del movimiento
        """
        # Calcular dirección hacia el objetivo
        dx = target_x - agent.x
        dy = target_y - agent.y
        distance = np.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            return {'success': True, 'distance_moved': 0, 'energy_cost': 0}
        
        # Normalizar dirección
        dx /= distance
        dy /= distance
        
        # Calcular ángulo hacia el objetivo
        target_angle = np.arctan2(dy, dx)
        
        # Actualizar ángulo del agente
        agent.angle = target_angle
        
        # Mover hacia el objetivo
        move_distance = min(distance, self.max_speed)
        return self.move_forward(agent, move_distance)


class RotationActuator:
    """Actuador de rotación para agentes."""
    
    def __init__(self, max_turn_speed: float = 0.1):
        """
        Inicializa el actuador de rotación.
        
        Args:
            max_turn_speed: Velocidad máxima de giro en radianes por tick
        """
        self.max_turn_speed = max_turn_speed
    
    def turn_left(self, agent, angle: float = None) -> Dict[str, Any]:
        """
        Gira el agente a la izquierda.
        
        Args:
            agent: Agente a girar
            angle: Ángulo a girar (opcional)
            
        Returns:
            Resultado del giro
        """
        if angle is None:
            angle = self.max_turn_speed
        
        old_angle = agent.angle
        agent.angle -= angle
        
        # Normalizar ángulo
        agent.angle = agent.angle % (2 * np.pi)
        
        return {
            'success': True,
            'old_angle': old_angle,
            'new_angle': agent.angle,
            'angle_turned': angle,
            'energy_cost': angle * agent.energy_turn_cost
        }
    
    def turn_right(self, agent, angle: float = None) -> Dict[str, Any]:
        """
        Gira el agente a la derecha.
        
        Args:
            agent: Agente a girar
            angle: Ángulo a girar (opcional)
            
        Returns:
            Resultado del giro
        """
        if angle is None:
            angle = self.max_turn_speed
        
        old_angle = agent.angle
        agent.angle += angle
        
        # Normalizar ángulo
        agent.angle = agent.angle % (2 * np.pi)
        
        return {
            'success': True,
            'old_angle': old_angle,
            'new_angle': agent.angle,
            'angle_turned': angle,
            'energy_cost': angle * agent.energy_turn_cost
        }
    
    def turn_to_angle(self, agent, target_angle: float) -> Dict[str, Any]:
        """
        Gira el agente hacia un ángulo específico.
        
        Args:
            agent: Agente a girar
            target_angle: Ángulo objetivo
            
        Returns:
            Resultado del giro
        """
        # Calcular diferencia de ángulo
        angle_diff = target_angle - agent.angle
        
        # Normalizar diferencia
        while angle_diff > np.pi:
            angle_diff -= 2 * np.pi
        while angle_diff < -np.pi:
            angle_diff += 2 * np.pi
        
        # Determinar dirección de giro
        if abs(angle_diff) < self.max_turn_speed:
            # Giro directo
            agent.angle = target_angle
            return {
                'success': True,
                'angle_turned': abs(angle_diff),
                'energy_cost': abs(angle_diff) * agent.energy_turn_cost
            }
        elif angle_diff > 0:
            # Girar a la derecha
            return self.turn_right(agent, self.max_turn_speed)
        else:
            # Girar a la izquierda
            return self.turn_left(agent, self.max_turn_speed)


class FeedingActuator:
    """Actuador de alimentación para agentes."""
    
    def __init__(self, eating_range: float = 2.0, energy_gain_per_food: float = 20.0):
        """
        Inicializa el actuador de alimentación.
        
        Args:
            eating_range: Rango de alimentación
            energy_gain_per_food: Energía ganada por unidad de comida
        """
        self.eating_range = eating_range
        self.energy_gain_per_food = energy_gain_per_food
    
    def eat(self, agent, environment) -> Dict[str, Any]:
        """
        Intenta comer comida en la posición actual.
        
        Args:
            agent: Agente que come
            environment: Entorno donde buscar comida
            
        Returns:
            Resultado de la alimentación
        """
        # Buscar comida en el rango de alimentación
        food_positions = environment.get_food_positions()
        food_eaten = 0
        energy_gained = 0
        
        for food_x, food_y in food_positions:
            distance = np.sqrt((agent.x - food_x)**2 + (agent.y - food_y)**2)
            
            if distance <= self.eating_range:
                # Comer comida
                food_amount = environment.remove_food_at_position(food_x, food_y)
                if food_amount > 0:
                    food_eaten += food_amount
                    energy_gained += food_amount * self.energy_gain_per_food
        
        # Aplicar energía ganada
        if energy_gained > 0:
            agent.energy = min(agent.energy + energy_gained, agent.energy_max)
        
        return {
            'success': food_eaten > 0,
            'food_eaten': food_eaten,
            'energy_gained': energy_gained,
            'energy_cost': 0  # Comer no cuesta energía
        }


class ReproductionActuator:
    """Actuador de reproducción para agentes."""
    
    def __init__(self, reproduction_threshold: float = 80.0, reproduction_cost: float = 30.0):
        """
        Inicializa el actuador de reproducción.
        
        Args:
            reproduction_threshold: Energía mínima para reproducirse
            reproduction_cost: Costo de energía para reproducirse
        """
        self.reproduction_threshold = reproduction_threshold
        self.reproduction_cost = reproduction_cost
    
    def reproduce(self, agent, partner=None) -> Dict[str, Any]:
        """
        Intenta reproducirse.
        
        Args:
            agent: Agente que se reproduce
            partner: Pareja reproductiva (opcional)
            
        Returns:
            Resultado de la reproducción
        """
        if agent.energy < self.reproduction_threshold:
            return {
                'success': False,
                'reason': 'insufficient_energy',
                'energy_cost': 0
            }
        
        # Verificar si hay pareja cerca (si se requiere)
        if partner is not None:
            distance = np.sqrt((agent.x - partner.x)**2 + (agent.y - partner.y)**2)
            if distance > 5.0:  # Rango de reproducción
                return {
                    'success': False,
                    'reason': 'partner_too_far',
                    'energy_cost': 0
                }
        
        # Realizar reproducción
        agent.energy -= self.reproduction_cost
        
        return {
            'success': True,
            'energy_cost': self.reproduction_cost,
            'offspring_ready': True
        }


class ActuatorArray:
    """Array de actuadores para un agente."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el array de actuadores.
        
        Args:
            config: Configuración de actuadores
        """
        self.actuators = {}
        self.action_executor = ActionExecutor()
        
        # Crear actuadores según configuración
        if config.get('movement', {}).get('enabled', True):
            movement_config = config['movement']
            self.actuators['movement'] = MovementActuator(
                max_speed=movement_config.get('max_speed', 2.0),
                acceleration=movement_config.get('acceleration', 0.5)
            )
        
        if config.get('rotation', {}).get('enabled', True):
            rotation_config = config['rotation']
            self.actuators['rotation'] = RotationActuator(
                max_turn_speed=rotation_config.get('max_turn_speed', 0.1)
            )
        
        if config.get('feeding', {}).get('enabled', True):
            feeding_config = config['feeding']
            self.actuators['feeding'] = FeedingActuator(
                eating_range=feeding_config.get('eating_range', 2.0),
                energy_gain_per_food=feeding_config.get('energy_gain_per_food', 20.0)
            )
        
        if config.get('reproduction', {}).get('enabled', True):
            reproduction_config = config['reproduction']
            self.actuators['reproduction'] = ReproductionActuator(
                reproduction_threshold=reproduction_config.get('threshold', 80.0),
                reproduction_cost=reproduction_config.get('cost', 30.0)
            )
    
    def execute_action(self, agent, action: ActionType, environment=None) -> Dict[str, Any]:
        """
        Ejecuta una acción usando el actuador apropiado.
        
        Args:
            agent: Agente que ejecuta la acción
            action: Acción a ejecutar
            environment: Entorno donde ejecutar la acción
            
        Returns:
            Resultado de la acción
        """
        return self.action_executor.execute_action(agent, action, environment)
    
    def get_actuator_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre los actuadores.
        
        Returns:
            Diccionario con información de actuadores
        """
        info = {
            'actuators': list(self.actuators.keys()),
            'actuator_details': {}
        }
        
        for actuator_name, actuator in self.actuators.items():
            if actuator_name == 'movement':
                info['actuator_details'][actuator_name] = {
                    'type': 'movement',
                    'max_speed': actuator.max_speed,
                    'acceleration': actuator.acceleration
                }
            elif actuator_name == 'rotation':
                info['actuator_details'][actuator_name] = {
                    'type': 'rotation',
                    'max_turn_speed': actuator.max_turn_speed
                }
            elif actuator_name == 'feeding':
                info['actuator_details'][actuator_name] = {
                    'type': 'feeding',
                    'eating_range': actuator.eating_range,
                    'energy_gain_per_food': actuator.energy_gain_per_food
                }
            elif actuator_name == 'reproduction':
                info['actuator_details'][actuator_name] = {
                    'type': 'reproduction',
                    'reproduction_threshold': actuator.reproduction_threshold,
                    'reproduction_cost': actuator.reproduction_cost
                }
        
        return info
