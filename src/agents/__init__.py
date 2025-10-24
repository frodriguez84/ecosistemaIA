"""
Módulo de agentes para el ecosistema evolutivo.
Contiene la implementación de agentes autónomos con cerebro, sensores y actuadores.
"""

from .agent import Agent, AgentState, AgentStats
from .brain import Brain, MLP, create_random_brain, crossover_brains
from .brain.policy import Policy, ActionType, ActionExecutor
from .sensors import SensorArray, VisionSensor, EnergySensor, DistanceSensor, CollisionSensor
from .actuators import ActuatorArray, MovementActuator, RotationActuator, FeedingActuator, ReproductionActuator

__all__ = [
    'Agent', 'AgentState', 'AgentStats',
    'Brain', 'MLP', 'create_random_brain', 'crossover_brains',
    'Policy', 'ActionType', 'ActionExecutor',
    'SensorArray', 'VisionSensor', 'EnergySensor', 'DistanceSensor', 'CollisionSensor',
    'ActuatorArray', 'MovementActuator', 'RotationActuator', 'FeedingActuator', 'ReproductionActuator'
]
