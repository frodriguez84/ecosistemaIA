"""
Utilidades de profiling para el ecosistema evolutivo.
Mide rendimiento y tiempos de ejecución.
"""

import time
import psutil
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento."""
    cpu_percent: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    timestamp: float


class Timer:
    """Timer simple para medir tiempos de ejecución."""
    
    def __init__(self, name: str = "Timer"):
        """
        Inicializa el timer.
        
        Args:
            name: Nombre del timer
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_time = 0.0
    
    def start(self) -> None:
        """Inicia el timer."""
        self.start_time = time.time()
    
    def stop(self) -> None:
        """Detiene el timer."""
        self.end_time = time.time()
        if self.start_time is not None:
            self.elapsed_time = self.end_time - self.start_time
    
    def reset(self) -> None:
        """Reinicia el timer."""
        self.start_time = None
        self.end_time = None
        self.elapsed_time = 0.0
    
    def get_elapsed_time(self) -> float:
        """
        Obtiene el tiempo transcurrido.
        
        Returns:
            Tiempo transcurrido en segundos
        """
        if self.start_time is not None and self.end_time is not None:
            return self.elapsed_time
        elif self.start_time is not None:
            return time.time() - self.start_time
        else:
            return 0.0
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class Profiler:
    """Profiler para medir rendimiento del sistema."""
    
    def __init__(self):
        """Inicializa el profiler."""
        self.timers = {}
        self.metrics_history = []
        self.process = psutil.Process(os.getpid())
    
    def start_timer(self, name: str) -> Timer:
        """
        Inicia un timer con nombre.
        
        Args:
            name: Nombre del timer
            
        Returns:
            Timer iniciado
        """
        timer = Timer(name)
        timer.start()
        self.timers[name] = timer
        return timer
    
    def stop_timer(self, name: str) -> float:
        """
        Detiene un timer y retorna el tiempo transcurrido.
        
        Args:
            name: Nombre del timer
            
        Returns:
            Tiempo transcurrido en segundos
        """
        if name in self.timers:
            self.timers[name].stop()
            return self.timers[name].get_elapsed_time()
        return 0.0
    
    def get_timer(self, name: str) -> Optional[Timer]:
        """
        Obtiene un timer por nombre.
        
        Args:
            name: Nombre del timer
            
        Returns:
            Timer o None si no existe
        """
        return self.timers.get(name)
    
    def get_all_timers(self) -> Dict[str, Timer]:
        """
        Obtiene todos los timers.
        
        Returns:
            Diccionario con todos los timers
        """
        return self.timers.copy()
    
    def measure_performance(self) -> PerformanceMetrics:
        """
        Mide el rendimiento actual del sistema.
        
        Returns:
            Métricas de rendimiento
        """
        # CPU
        cpu_percent = self.process.cpu_percent()
        
        # Memoria
        memory_info = self.process.memory_info()
        memory_usage = memory_info.rss / 1024 / 1024  # MB
        
        # Memoria disponible
        memory_available = psutil.virtual_memory().available / 1024 / 1024  # MB
        
        # Uso de disco
        disk_usage = psutil.disk_usage('/').percent
        
        metrics = PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_usage=memory_usage,
            memory_available=memory_available,
            disk_usage=disk_usage,
            timestamp=time.time()
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del rendimiento.
        
        Returns:
            Diccionario con resumen de rendimiento
        """
        if not self.metrics_history:
            return {}
        
        # Calcular estadísticas
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_usage for m in self.metrics_history]
        
        return {
            'total_measurements': len(self.metrics_history),
            'cpu': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'timers': {
                name: timer.get_elapsed_time() 
                for name, timer in self.timers.items()
            }
        }
    
    def clear_history(self) -> None:
        """Limpia el historial de métricas."""
        self.metrics_history.clear()
    
    def clear_timers(self) -> None:
        """Limpia todos los timers."""
        self.timers.clear()
    
    def reset(self) -> None:
        """Reinicia el profiler."""
        self.clear_history()
        self.clear_timers()


@contextmanager
def profile_function(name: str, profiler: Optional[Profiler] = None):
    """
    Context manager para perfilar una función.
    
    Args:
        name: Nombre de la función
        profiler: Profiler a usar (opcional)
    """
    if profiler is None:
        profiler = Profiler()
    
    timer = profiler.start_timer(name)
    try:
        yield timer
    finally:
        profiler.stop_timer(name)


def measure_execution_time(func):
    """
    Decorator para medir el tiempo de ejecución de una función.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} ejecutada en {end_time - start_time:.4f} segundos")
        return result
    
    return wrapper


def measure_memory_usage(func):
    """
    Decorator para medir el uso de memoria de una función.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_after - memory_before
        
        print(f"{func.__name__} usó {memory_diff:.2f} MB de memoria")
        return result
    
    return wrapper


class PerformanceMonitor:
    """Monitor de rendimiento en tiempo real."""
    
    def __init__(self, interval: float = 1.0):
        """
        Inicializa el monitor.
        
        Args:
            interval: Intervalo de medición en segundos
        """
        self.interval = interval
        self.profiler = Profiler()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self) -> None:
        """Inicia el monitoreo."""
        self.monitoring = True
        # Implementar monitoreo en hilo separado
        # Por simplicidad, se omite la implementación del hilo
    
    def stop_monitoring(self) -> None:
        """Detiene el monitoreo."""
        self.monitoring = False
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """
        Obtiene las métricas actuales.
        
        Returns:
            Métricas de rendimiento actuales
        """
        return self.profiler.measure_performance()
    
    def get_metrics_history(self) -> List[PerformanceMetrics]:
        """
        Obtiene el historial de métricas.
        
        Returns:
            Lista de métricas históricas
        """
        return self.profiler.metrics_history.copy()
