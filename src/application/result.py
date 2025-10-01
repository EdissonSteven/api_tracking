"""
Result Pattern para manejo robusto de errores sin excepciones.

Este patrón permite manejar errores de forma funcional y explícita,
siguiendo principios de Clean Architecture y programación defensiva.
"""

from typing import TypeVar, Generic, Union, Callable, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

T = TypeVar('T')  # Tipo de dato exitoso
E = TypeVar('E')  # Tipo de error


class Result(Generic[T, E], ABC):
    """Clase base abstracta para el Result Pattern."""
    
    @abstractmethod
    def is_success(self) -> bool:
        """Verifica si el resultado es exitoso."""
        pass
    
    @abstractmethod
    def is_failure(self) -> bool:
        """Verifica si el resultado es un error."""
        pass
    
    @abstractmethod
    def unwrap(self) -> T:
        """Extrae el valor exitoso o lanza excepción si es error."""
        pass
    
    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Extrae el valor exitoso o retorna valor por defecto."""
        pass
    
    @abstractmethod
    def map(self, func: Callable[[T], Any]) -> 'Result':
        """Aplica función al valor si es exitoso."""
        pass
    
    @abstractmethod
    def map_error(self, func: Callable[[E], Any]) -> 'Result':
        """Aplica función al error si es falla."""
        pass


@dataclass(frozen=True)
class Success(Result[T, E]):
    """Resultado exitoso."""
    
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def map(self, func: Callable[[T], Any]) -> 'Result':
        try:
            return Success(func(self.value))
        except Exception as e:
            return Failure(e)
    
    def map_error(self, func: Callable[[E], Any]) -> 'Result':
        return self
    
    def __str__(self) -> str:
        return f"Success({self.value})"


@dataclass(frozen=True)
class Failure(Result[T, E]):
    """Resultado de error."""
    
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        if isinstance(self.error, Exception):
            raise self.error
        else:
            raise ValueError(f"Result is a failure: {self.error}")
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def map(self, func: Callable[[T], Any]) -> 'Result':
        return self
    
    def map_error(self, func: Callable[[E], Any]) -> 'Result':
        try:
            return Failure(func(self.error))
        except Exception as e:
            return Failure(e)
    
    def __str__(self) -> str:
        return f"Failure({self.error})"


# Type aliases para uso común
CheckpointResult = Result[Any, Exception]
ValidationResult = Result[bool, str]


class ResultBuilder:
    """Builder para crear Results de forma fluente."""
    
    @staticmethod
    def success(value: T) -> Success[T, Any]:
        """Crear resultado exitoso."""
        return Success(value)
    
    @staticmethod
    def failure(error: E) -> Failure[Any, E]:
        """Crear resultado de error."""
        return Failure(error)
    
    @staticmethod
    def from_exception(func: Callable[[], T]) -> Result[T, Exception]:
        """Ejecutar función y capturar excepción como Result."""
        try:
            return Success(func())
        except Exception as e:
            return Failure(e)
    
    @staticmethod
    def from_optional(value: Optional[T], error_message: str = "Value is None") -> Result[T, str]:
        """Convertir Optional a Result."""
        if value is not None:
            return Success(value)
        else:
            return Failure(error_message)


class ResultUtils:
    """Utilidades para trabajar con Results."""
    
    @staticmethod
    def combine(*results: Result) -> Result[list, Any]:
        """
        Combina múltiples results. Si todos son exitosos, retorna lista de valores.
        Si alguno falla, retorna el primer error.
        """
        values = []
        for result in results:
            if result.is_failure():
                return result
            values.append(result.unwrap())
        
        return Success(values)
    
    @staticmethod
    def sequence(results: list[Result[T, E]]) -> Result[list[T], E]:
        """
        Convierte lista de Results en Result de lista.
        Si todos son exitosos, retorna Success con lista de valores.
        Si alguno falla, retorna el primer Failure.
        """
        values = []
        for result in results:
            if result.is_failure():
                return result
            values.append(result.unwrap())
        
        return Success(values)
    
    @staticmethod
    def partition(results: list[Result[T, E]]) -> tuple[list[T], list[E]]:
        """
        Separa lista de Results en listas de valores exitosos y errores.
        """
        successes = []
        failures = []
        
        for result in results:
            if result.is_success():
                successes.append(result.unwrap())
            else:
                failures.append(result.error)
        
        return successes, failures


# Decorador para convertir funciones que lanzan excepciones a Result
def to_result(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """
    Decorador que convierte una función que lanza excepciones a una que retorna Result.
    """
    def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            return Success(func(*args, **kwargs))
        except Exception as e:
            return Failure(e)
    
    return wrapper


# Context manager para manejo de Results
class ResultContext:
    """Context manager para ejecutar código que retorna Results."""
    
    def __init__(self):
        self.results = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.results.append(Failure(exc_val))
            return True  # Suprimir excepción
        return False
    
    def add_result(self, result: Result):
        """Agregar resultado al contexto."""
        self.results.append(result)
    
    def get_combined_result(self) -> Result[list, Any]:
        """Obtener resultado combinado de todas las operaciones."""
        return ResultUtils.sequence(self.results)


# Ejemplos de uso específicos para el dominio de tracking
class CheckpointResultFactory:
    """Factory para crear Results específicos del dominio de checkpoints."""
    
    @staticmethod
    def validation_success() -> Result[bool, str]:
        """Resultado exitoso de validación."""
        return Success(True)
    
    @staticmethod
    def validation_failure(message: str) -> Result[bool, str]:
        """Resultado fallido de validación."""
        return Failure(message)
    
    @staticmethod
    def checkpoint_created(checkpoint_id: str) -> Result[str, str]:
        """Resultado exitoso de creación de checkpoint."""
        return Success(checkpoint_id)
    
    @staticmethod
    def checkpoint_creation_failed(reason: str) -> Result[str, str]:
        """Resultado fallido de creación de checkpoint."""
        return Failure(reason)


# Alias de conveniencia
Ok = Success
Err = Failure

# Funciones de conveniencia
def ok(value: T) -> Success[T, Any]:
    """Crear resultado exitoso (alias de Success)."""
    return Success(value)

def err(error: E) -> Failure[Any, E]:
    """Crear resultado de error (alias de Failure)."""
    return Failure(error)


# Async Result para operaciones asíncronas
class AsyncResult:
    """Wrapper para trabajar con Results en operaciones asíncronas."""
    
    @staticmethod
    async def from_coroutine(coro) -> Result:
        """Ejecutar corrutina y capturar excepción como Result."""
        try:
            result = await coro
            return Success(result)
        except Exception as e:
            return Failure(e)
    
    @staticmethod
    async def map_async(result: Result[T, E], async_func: Callable[[T], Any]) -> Result:
        """Aplicar función asíncrona a Result."""
        if result.is_success():
            try:
                new_value = await async_func(result.unwrap())
                return Success(new_value)
            except Exception as e:
                return Failure(e)
        else:
            return result