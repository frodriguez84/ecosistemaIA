"""
Utilidades de generación de números aleatorios para el ecosistema evolutivo.
Maneja semillas y estados de RNG para reproducibilidad.
"""

import random
import numpy as np
import pickle
from typing import Optional, Dict, Any
from pathlib import Path


def set_seed(seed: int) -> None:
    """
    Establece la semilla para todos los generadores de números aleatorios.
    
    Args:
        seed: Semilla a establecer
    """
    random.seed(seed)
    np.random.seed(seed)


def get_random_state() -> Dict[str, Any]:
    """
    Obtiene el estado actual de todos los generadores de números aleatorios.
    
    Returns:
        Diccionario con el estado de los generadores
    """
    return {
        'python_random': random.getstate(),
        'numpy_random': np.random.get_state()
    }


def set_random_state(state: Dict[str, Any]) -> None:
    """
    Establece el estado de todos los generadores de números aleatorios.
    
    Args:
        state: Diccionario con el estado de los generadores
    """
    if 'python_random' in state:
        random.setstate(state['python_random'])
    
    if 'numpy_random' in state:
        np.random.set_state(state['numpy_random'])


def save_random_state(filepath: str) -> None:
    """
    Guarda el estado de los generadores de números aleatorios.
    
    Args:
        filepath: Ruta del archivo donde guardar
    """
    state = get_random_state()
    
    with open(filepath, 'wb') as f:
        pickle.dump(state, f)


def load_random_state(filepath: str) -> None:
    """
    Carga el estado de los generadores de números aleatorios.
    
    Args:
        filepath: Ruta del archivo a cargar
    """
    with open(filepath, 'rb') as f:
        state = pickle.load(f)
    
    set_random_state(state)


def get_random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Obtiene un número flotante aleatorio.
    
    Args:
        min_val: Valor mínimo
        max_val: Valor máximo
        
    Returns:
        Número flotante aleatorio
    """
    return random.uniform(min_val, max_val)


def get_random_int(min_val: int = 0, max_val: int = 100) -> int:
    """
    Obtiene un número entero aleatorio.
    
    Args:
        min_val: Valor mínimo
        max_val: Valor máximo
        
    Returns:
        Número entero aleatorio
    """
    return random.randint(min_val, max_val)


def get_random_choice(choices: list) -> Any:
    """
    Obtiene una elección aleatoria de una lista.
    
    Args:
        choices: Lista de opciones
        
    Returns:
        Elemento aleatorio de la lista
    """
    return random.choice(choices)


def get_random_sample(population: list, k: int) -> list:
    """
    Obtiene una muestra aleatoria de una población.
    
    Args:
        population: Lista de elementos
        k: Tamaño de la muestra
        
    Returns:
        Lista con la muestra aleatoria
    """
    return random.sample(population, k)


def get_random_shuffle(lst: list) -> list:
    """
    Obtiene una copia aleatoria de una lista.
    
    Args:
        lst: Lista a mezclar
        
    Returns:
        Lista mezclada
    """
    shuffled = lst.copy()
    random.shuffle(shuffled)
    return shuffled


def get_gaussian_random(mean: float = 0.0, std: float = 1.0) -> float:
    """
    Obtiene un número aleatorio con distribución gaussiana.
    
    Args:
        mean: Media de la distribución
        std: Desviación estándar
        
    Returns:
        Número aleatorio gaussiano
    """
    return np.random.normal(mean, std)


def get_multivariate_gaussian(mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Obtiene un vector aleatorio con distribución gaussiana multivariada.
    
    Args:
        mean: Vector de medias
        cov: Matriz de covarianza
        
    Returns:
        Vector aleatorio gaussiano
    """
    return np.random.multivariate_normal(mean, cov)


def get_beta_random(alpha: float, beta: float) -> float:
    """
    Obtiene un número aleatorio con distribución beta.
    
    Args:
        alpha: Parámetro alpha
        beta: Parámetro beta
        
    Returns:
        Número aleatorio beta
    """
    return np.random.beta(alpha, beta)


def get_gamma_random(shape: float, scale: float = 1.0) -> float:
    """
    Obtiene un número aleatorio con distribución gamma.
    
    Args:
        shape: Parámetro de forma
        scale: Parámetro de escala
        
    Returns:
        Número aleatorio gamma
    """
    return np.random.gamma(shape, scale)


def get_exponential_random(scale: float = 1.0) -> float:
    """
    Obtiene un número aleatorio con distribución exponencial.
    
    Args:
        scale: Parámetro de escala
        
    Returns:
        Número aleatorio exponencial
    """
    return np.random.exponential(scale)


def get_poisson_random(lam: float) -> int:
    """
    Obtiene un número aleatorio con distribución de Poisson.
    
    Args:
        lam: Parámetro lambda
        
    Returns:
        Número aleatorio de Poisson
    """
    return np.random.poisson(lam)


def get_binomial_random(n: int, p: float) -> int:
    """
    Obtiene un número aleatorio con distribución binomial.
    
    Args:
        n: Número de ensayos
        p: Probabilidad de éxito
        
    Returns:
        Número aleatorio binomial
    """
    return np.random.binomial(n, p)


def get_geometric_random(p: float) -> int:
    """
    Obtiene un número aleatorio con distribución geométrica.
    
    Args:
        p: Probabilidad de éxito
        
    Returns:
        Número aleatorio geométrico
    """
    return np.random.geometric(p)


def get_hypergeometric_random(ngood: int, nbad: int, nsample: int) -> int:
    """
    Obtiene un número aleatorio con distribución hipergeométrica.
    
    Args:
        ngood: Número de elementos buenos
        nbad: Número de elementos malos
        nsample: Tamaño de la muestra
        
    Returns:
        Número aleatorio hipergeométrico
    """
    return np.random.hypergeometric(ngood, nbad, nsample)
