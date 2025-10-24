"""
Política de decisión para agentes.
Convierte percepciones en acciones usando la red neuronal.
"""

import numpy as np
from typing import List, Dict, Any
from enum import Enum


class ActionType(Enum):
    """Tipos de acciones disponibles para los agentes."""
    MOVE_FORWARD = "move_forward"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    EAT = "eat"
    REPRODUCE = "reproduce"
    IDLE = "idle"


class Policy:
    """Política de decisión para agentes."""
    
    def __init__(self, brain, action_mapping: Dict[int, ActionType] = None):
        """
        Inicializa la política.
        
        Args:
            brain: Cerebro del agente
            action_mapping: Mapeo de índices de salida a acciones
        """
        self.brain = brain
        self.action_mapping = action_mapping or self._default_action_mapping()
    
    def _default_action_mapping(self) -> Dict[int, ActionType]:
        """Mapeo por defecto de salidas a acciones."""
        return {
            0: ActionType.MOVE_FORWARD,
            1: ActionType.TURN_LEFT,
            2: ActionType.TURN_RIGHT,
            3: ActionType.EAT
        }
    
    def decide(self, perceptions: np.ndarray) -> ActionType:
        """
        Toma una decisión basada en las percepciones.
        
        Args:
            perceptions: Array de percepciones del agente
            
        Returns:
            Acción a realizar
        """
        # Obtener salida de la red neuronal
        outputs = self.brain.think(perceptions)
        
        # Seleccionar acción con mayor activación
        action_index = np.argmax(outputs)
        
        # Mapear a acción
        if action_index in self.action_mapping:
            return self.action_mapping[action_index]
        else:
            return ActionType.IDLE
    
    def get_action_probabilities(self, perceptions: np.ndarray) -> Dict[ActionType, float]:
        """
        Obtiene las probabilidades de cada acción.
        
        Args:
            perceptions: Array de percepciones del agente
            
        Returns:
            Diccionario con probabilidades de cada acción
        """
        outputs = self.brain.think(perceptions)
        
        # Aplicar softmax para obtener probabilidades
        exp_outputs = np.exp(outputs - np.max(outputs))
        probabilities = exp_outputs / np.sum(exp_outputs)
        
        # Mapear a acciones
        action_probs = {}
        for i, prob in enumerate(probabilities):
            if i in self.action_mapping:
                action_probs[self.action_mapping[i]] = prob
        
        return action_probs
    
    def get_action_strength(self, perceptions: np.ndarray, action: ActionType) -> float:
        """
        Obtiene la fuerza/intensidad de una acción específica.
        
        Args:
            perceptions: Array de percepciones del agente
            action: Acción de la cual obtener la fuerza
            
        Returns:
            Fuerza de la acción (0.0 a 1.0)
        """
        outputs = self.brain.think(perceptions)
        
        # Encontrar el índice de la acción
        action_index = None
        for idx, act in self.action_mapping.items():
            if act == action:
                action_index = idx
                break
        
        if action_index is None:
            return 0.0
        
        # Normalizar la salida
        max_output = np.max(outputs)
        if max_output == 0:
            return 0.0
        
        return float(outputs[action_index] / max_output)
    
    def set_action_mapping(self, action_mapping: Dict[int, ActionType]) -> None:
        """
        Establece un nuevo mapeo de acciones.
        
        Args:
            action_mapping: Nuevo mapeo de índices a acciones
        """
        self.action_mapping = action_mapping
    
    def clone(self) -> 'Policy':
        """
        Crea una copia de la política.
        
        Returns:
            Nueva instancia de Policy
        """
        return Policy(self.brain.clone(), self.action_mapping.copy())


class ActionExecutor:
    """Ejecutor de acciones para agentes."""
    
    def __init__(self):
        """Inicializa el ejecutor de acciones."""
        self.action_effects = {
            ActionType.MOVE_FORWARD: self._execute_move_forward,
            ActionType.TURN_LEFT: self._execute_turn_left,
            ActionType.TURN_RIGHT: self._execute_turn_right,
            ActionType.EAT: self._execute_eat,
            ActionType.REPRODUCE: self._execute_reproduce,
            ActionType.IDLE: self._execute_idle
        }
    
    def execute_action(self, agent, action: ActionType, environment=None) -> Dict[str, Any]:
        """
        Ejecuta una acción para un agente.
        
        Args:
            agent: Agente que ejecuta la acción
            action: Acción a ejecutar
            environment: Entorno donde se ejecuta la acción
            
        Returns:
            Diccionario con resultados de la acción
        """
        if action in self.action_effects:
            return self.action_effects[action](agent, environment)
        else:
            return self._execute_idle(agent, environment)
    
    def _execute_move_forward(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta movimiento hacia adelante."""
        # Calcular nueva posición
        dx = np.cos(agent.angle) * agent.speed
        dy = np.sin(agent.angle) * agent.speed
        
        new_x = agent.x + dx
        new_y = agent.y + dy
        
        # Verificar colisiones con el entorno
        collision = False
        if environment:
            collision = environment.check_collision(new_x, new_y)
        
        if not collision:
            agent.x = new_x
            agent.y = new_y
            agent.energy -= agent.energy_move_cost
        
        return {
            'success': not collision,
            'energy_cost': agent.energy_move_cost,
            'new_position': (new_x, new_y) if not collision else (agent.x, agent.y)
        }
    
    def _execute_turn_left(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta giro a la izquierda."""
        agent.angle -= agent.turn_speed
        agent.energy -= agent.energy_turn_cost
        
        return {
            'success': True,
            'energy_cost': agent.energy_turn_cost,
            'new_angle': agent.angle
        }
    
    def _execute_turn_right(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta giro a la derecha."""
        agent.angle += agent.turn_speed
        agent.energy -= agent.energy_turn_cost
        
        return {
            'success': True,
            'energy_cost': agent.energy_turn_cost,
            'new_angle': agent.angle
        }
    
    def _execute_eat(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta acción de comer."""
        food_eaten = 0
        energy_gained = 0
        
        if environment:
            # Buscar comida en la posición actual
            food_eaten = environment.get_food_at_position(agent.x, agent.y)
            if food_eaten > 0:
                energy_gained = food_eaten * agent.energy_eat_gain
                agent.energy = min(agent.energy + energy_gained, agent.energy_max)
                environment.remove_food_at_position(agent.x, agent.y, food_eaten)
        
        return {
            'success': food_eaten > 0,
            'food_eaten': food_eaten,
            'energy_gained': energy_gained
        }
    
    def _execute_reproduce(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta reproducción."""
        if agent.energy >= agent.reproduction_threshold:
            agent.energy -= agent.reproduction_cost
            return {
                'success': True,
                'energy_cost': agent.reproduction_cost,
                'can_reproduce': True
            }
        else:
            return {
                'success': False,
                'energy_cost': 0,
                'can_reproduce': False
            }
    
    def _execute_idle(self, agent, environment=None) -> Dict[str, Any]:
        """Ejecuta inactividad."""
        return {
            'success': True,
            'energy_cost': 0
        }
