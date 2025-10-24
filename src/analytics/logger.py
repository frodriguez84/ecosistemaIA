"""
Sistema de logging para el ecosistema evolutivo.
Registra eventos y métricas de la simulación.
"""

import logging
import json
import csv
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Niveles de logging disponibles."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Entrada de log."""
    timestamp: float
    level: LogLevel
    message: str
    module: str
    data: Dict[str, Any] = None


class SimulationLogger:
    """Logger principal de la simulación."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el logger.
        
        Args:
            config: Configuración del logger
        """
        self.config = config or {}
        self.logs = []
        self.metrics_logs = []
        
        # Configuración
        self.log_level = LogLevel(self.config.get('level', 'INFO'))
        self.log_format = self.config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_file = self.config.get('file', 'logs/runtime/simulation.log')
        self.metrics_file = self.config.get('metrics_file', 'logs/metrics/metrics.csv')
        
        # Configurar logging de Python
        self._setup_python_logging()
        
        # Crear directorios
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.metrics_file).parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_python_logging(self) -> None:
        """Configura el sistema de logging de Python."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.value),
            format=self.log_format,
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ecosistema')
    
    def log(self, level: LogLevel, message: str, module: str = "main", data: Dict[str, Any] = None) -> None:
        """
        Registra un mensaje de log.
        
        Args:
            level: Nivel del log
            message: Mensaje a registrar
            module: Módulo que genera el log
            data: Datos adicionales
        """
        # Crear entrada de log
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            module=module,
            data=data or {}
        )
        
        # Agregar a logs internos
        self.logs.append(entry)
        
        # Log con Python logging
        if level == LogLevel.DEBUG:
            self.logger.debug(f"[{module}] {message}")
        elif level == LogLevel.INFO:
            self.logger.info(f"[{module}] {message}")
        elif level == LogLevel.WARNING:
            self.logger.warning(f"[{module}] {message}")
        elif level == LogLevel.ERROR:
            self.logger.error(f"[{module}] {message}")
        elif level == LogLevel.CRITICAL:
            self.logger.critical(f"[{module}] {message}")
    
    def log_simulation_start(self, config: Dict[str, Any]) -> None:
        """
        Registra el inicio de la simulación.
        
        Args:
            config: Configuración de la simulación
        """
        self.log(LogLevel.INFO, "Simulación iniciada", "simulation", {
            'config': config,
            'timestamp': time.time()
        })
    
    def log_simulation_end(self, stats: Dict[str, Any]) -> None:
        """
        Registra el fin de la simulación.
        
        Args:
            stats: Estadísticas finales
        """
        self.log(LogLevel.INFO, "Simulación finalizada", "simulation", {
            'stats': stats,
            'timestamp': time.time()
        })
    
    def log_epoch_start(self, epoch: int) -> None:
        """
        Registra el inicio de una época.
        
        Args:
            epoch: Número de época
        """
        self.log(LogLevel.INFO, f"Época {epoch} iniciada", "epoch", {
            'epoch': epoch,
            'timestamp': time.time()
        })
    
    def log_epoch_end(self, epoch: int, stats: Dict[str, Any]) -> None:
        """
        Registra el fin de una época.
        
        Args:
            epoch: Número de época
            stats: Estadísticas de la época
        """
        self.log(LogLevel.INFO, f"Época {epoch} finalizada", "epoch", {
            'epoch': epoch,
            'stats': stats,
            'timestamp': time.time()
        })
    
    def log_generation_start(self, generation: int) -> None:
        """
        Registra el inicio de una generación.
        
        Args:
            generation: Número de generación
        """
        self.log(LogLevel.INFO, f"Generación {generation} iniciada", "generation", {
            'generation': generation,
            'timestamp': time.time()
        })
    
    def log_generation_end(self, generation: int, stats: Dict[str, Any]) -> None:
        """
        Registra el fin de una generación.
        
        Args:
            generation: Número de generación
            stats: Estadísticas de la generación
        """
        self.log(LogLevel.INFO, f"Generación {generation} finalizada", "generation", {
            'generation': generation,
            'stats': stats,
            'timestamp': time.time()
        })
    
    def log_agent_birth(self, agent_id: int, parent_ids: List[int] = None) -> None:
        """
        Registra el nacimiento de un agente.
        
        Args:
            agent_id: ID del agente
            parent_ids: IDs de los padres
        """
        self.log(LogLevel.DEBUG, f"Agente {agent_id} nacido", "agent", {
            'agent_id': agent_id,
            'parent_ids': parent_ids,
            'timestamp': time.time()
        })
    
    def log_agent_death(self, agent_id: int, cause: str, age: int) -> None:
        """
        Registra la muerte de un agente.
        
        Args:
            agent_id: ID del agente
            cause: Causa de la muerte
            age: Edad del agente
        """
        self.log(LogLevel.DEBUG, f"Agente {agent_id} murió", "agent", {
            'agent_id': agent_id,
            'cause': cause,
            'age': age,
            'timestamp': time.time()
        })
    
    def log_agent_action(self, agent_id: int, action: str, result: Dict[str, Any]) -> None:
        """
        Registra una acción de un agente.
        
        Args:
            agent_id: ID del agente
            action: Acción realizada
            result: Resultado de la acción
        """
        self.log(LogLevel.DEBUG, f"Agente {agent_id} realizó {action}", "agent", {
            'agent_id': agent_id,
            'action': action,
            'result': result,
            'timestamp': time.time()
        })
    
    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Registra métricas de la simulación.
        
        Args:
            metrics: Diccionario con métricas
        """
        # Agregar timestamp
        metrics['timestamp'] = time.time()
        
        # Agregar a logs de métricas
        self.metrics_logs.append(metrics)
        
        # Log con nivel INFO
        self.log(LogLevel.INFO, "Métricas registradas", "metrics", metrics)
    
    def log_error(self, error: Exception, module: str = "main") -> None:
        """
        Registra un error.
        
        Args:
            error: Excepción a registrar
            module: Módulo donde ocurrió el error
        """
        self.log(LogLevel.ERROR, f"Error: {str(error)}", module, {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': time.time()
        })
    
    def log_warning(self, message: str, module: str = "main", data: Dict[str, Any] = None) -> None:
        """
        Registra una advertencia.
        
        Args:
            message: Mensaje de advertencia
            module: Módulo que genera la advertencia
            data: Datos adicionales
        """
        self.log(LogLevel.WARNING, message, module, data)
    
    def log_info(self, message: str, module: str = "main", data: Dict[str, Any] = None) -> None:
        """
        Registra información.
        
        Args:
            message: Mensaje informativo
            module: Módulo que genera el mensaje
            data: Datos adicionales
        """
        self.log(LogLevel.INFO, message, module, data)
    
    def log_debug(self, message: str, module: str = "main", data: Dict[str, Any] = None) -> None:
        """
        Registra información de debug.
        
        Args:
            message: Mensaje de debug
            module: Módulo que genera el mensaje
            data: Datos adicionales
        """
        self.log(LogLevel.DEBUG, message, module, data)
    
    def save_metrics_to_csv(self) -> None:
        """Guarda métricas en archivo CSV."""
        if not self.metrics_logs:
            return
        
        try:
            with open(self.metrics_file, 'w', newline='', encoding='utf-8') as csvfile:
                if self.metrics_logs:
                    fieldnames = self.metrics_logs[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.metrics_logs)
        except Exception as e:
            self.log_error(e, "logger")
    
    def save_logs_to_json(self, filepath: str) -> None:
        """
        Guarda logs en archivo JSON.
        
        Args:
            filepath: Ruta del archivo
        """
        try:
            logs_data = [asdict(log) for log in self.logs]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(logs_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_error(e, "logger")
    
    def load_logs_from_json(self, filepath: str) -> None:
        """
        Carga logs desde archivo JSON.
        
        Args:
            filepath: Ruta del archivo
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
            
            self.logs.clear()
            for log_data in logs_data:
                entry = LogEntry(
                    timestamp=log_data['timestamp'],
                    level=LogLevel(log_data['level']),
                    message=log_data['message'],
                    module=log_data['module'],
                    data=log_data.get('data', {})
                )
                self.logs.append(entry)
        except Exception as e:
            self.log_error(e, "logger")
    
    def get_logs_by_level(self, level: LogLevel) -> List[LogEntry]:
        """
        Obtiene logs por nivel.
        
        Args:
            level: Nivel de log
            
        Returns:
            Lista de logs del nivel especificado
        """
        return [log for log in self.logs if log.level == level]
    
    def get_logs_by_module(self, module: str) -> List[LogEntry]:
        """
        Obtiene logs por módulo.
        
        Args:
            module: Nombre del módulo
            
        Returns:
            Lista de logs del módulo especificado
        """
        return [log for log in self.logs if log.module == module]
    
    def get_recent_logs(self, limit: int = 100) -> List[LogEntry]:
        """
        Obtiene logs recientes.
        
        Args:
            limit: Número máximo de logs
            
        Returns:
            Lista de logs más recientes
        """
        return self.logs[-limit:]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los logs.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.logs:
            return {}
        
        # Contar logs por nivel
        level_counts = {}
        for log in self.logs:
            level_counts[log.level.value] = level_counts.get(log.level.value, 0) + 1
        
        # Contar logs por módulo
        module_counts = {}
        for log in self.logs:
            module_counts[log.module] = module_counts.get(log.module, 0) + 1
        
        return {
            'total_logs': len(self.logs),
            'level_counts': level_counts,
            'module_counts': module_counts,
            'metrics_logs': len(self.metrics_logs),
            'oldest_log': min(log.timestamp for log in self.logs) if self.logs else 0,
            'newest_log': max(log.timestamp for log in self.logs) if self.logs else 0
        }
    
    def clear_logs(self) -> None:
        """Limpia todos los logs."""
        self.logs.clear()
        self.metrics_logs.clear()
    
    def export_logs(self, filepath: str, format: str = "json") -> None:
        """
        Exporta logs en diferentes formatos.
        
        Args:
            filepath: Ruta del archivo
            format: Formato de exportación (json, csv)
        """
        if format == "json":
            self.save_logs_to_json(filepath)
        elif format == "csv":
            self.save_metrics_to_csv()
        else:
            self.log_warning(f"Formato no soportado: {format}", "logger")
