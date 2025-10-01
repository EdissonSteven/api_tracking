import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.encoders import jsonable_encoder

from ..v1.schemas.error_schemas import ErrorResponse, ValidationErrorResponse, ErrorDetail
from ....domain.domain_exceptions import (
    BusinessRuleViolationError,
    DomainValidationError,
    UnitNotFoundError
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """Middleware para manejo centralizado de errores."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            request = Request(scope, receive=receive)
            response = await general_exception_handler(request, exc)
            await response(scope, receive, send)


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para excepciones de dominio."""
    
    # Obtener request_id si existe
    request_id = getattr(request.state, "request_id", "unknown")
    
    # BusinessRuleViolationError
    if isinstance(exc, BusinessRuleViolationError):
        context = exc.context or {}
        
        # Construir mensaje con transiciones permitidas
        message = exc.message
        if "allowed_transitions" in context and context["allowed_transitions"]:
            transitions_str = ", ".join(context["allowed_transitions"])
            message = f"{exc.message}. Estados permitidos: [{transitions_str}]"
        elif "allowed_transitions" in context:
            message = f"{exc.message}. Este es un estado final, no permite transiciones."
        
        logger.warning(
            f"Business rule violation - request_id={request_id}, "
            f"error_code=BUSINESS_RULE_VIOLATION, rule={exc.rule_name}"
        )
        
        return JSONResponse(
            status_code=409,
            content={
                "error": True,
                "error_code": "BUSINESS_RULE_VIOLATION",
                "message": message,
                "rule_violation": exc.rule_name,
                "details": {
                    **context,
                    "violated_rule": exc.rule_name
                },
                "request_id": request_id
            }
        )
    
    # DomainValidationError
    elif isinstance(exc, DomainValidationError):
        logger.warning(
            f"Domain validation error - request_id={request_id}, "
            f"error_code=DOMAIN_VALIDATION_ERROR"
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "error_code": "DOMAIN_VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details or {},
                "request_id": request_id
            }
        )
    
    # UnitNotFoundError
    elif isinstance(exc, UnitNotFoundError):
        logger.warning(
            f"Unit not found - request_id={request_id}, "
            f"tracking_id={exc.tracking_id}"
        )
        
        return JSONResponse(
            status_code=404,
            content={
                "error": True,
                "error_code": "UNIT_NOT_FOUND",
                "message": f"Unidad no encontrada: {exc.tracking_id}",
                "details": {"tracking_id": exc.tracking_id},
                "request_id": request_id
            }
        )
    
    # Fallback para otras excepciones de dominio
    logger.error(f"Unexpected domain exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "request_id": request_id
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler para excepciones HTTP de FastAPI."""
    logger.warning(f"HTTP Exception: {getattr(exc, 'status_code', 500)} - {getattr(exc, 'detail', '')}")
    
    error_response = ErrorResponse(
        error=True,
        message=str(getattr(exc, "detail", "")),
        details=[]
    )
    
    content = jsonable_encoder(error_response)
    return JSONResponse(status_code=getattr(exc, "status_code", 500), content=content)


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handler para errores de validación de Pydantic."""
    try:
        logger.warning(f"Validation Error: {exc.errors()}")
        validation_errors: List[Dict[str, Any]] = []
        
        for error in exc.errors():
            validation_error = {
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", "Error de validación"),
                "type": error.get("type", "validation_error"),
                "input": str(error.get("input", "")),
                "context": error.get("ctx", {})
            }
            validation_errors.append(validation_error)

        validation_response = ValidationErrorResponse(
            error=True,
            message="Error de validación en los datos enviados",
            validation_errors=validation_errors,
            timestamp=datetime.utcnow()
        )
        
        content = jsonable_encoder(validation_response)
        return JSONResponse(status_code=422, content=content)
        
    except Exception as handler_error:
        logger.error(f"Error en validation_exception_handler: {str(handler_error)}")
        
        simple_response = {
            "error": True,
            "message": "Error de validación",
            "details": "Error procesando detalles de validación",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(status_code=422, content=simple_response)


async def starlette_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handler para excepciones HTTP de Starlette."""
    logger.warning(f"Starlette HTTP Exception: {getattr(exc, 'status_code', 500)} - {getattr(exc, 'detail', '')}")
    
    error_response = ErrorResponse(
        error=True,
        message=str(getattr(exc, "detail", "")),
        details=[]
    )
    
    content = jsonable_encoder(error_response)
    return JSONResponse(status_code=getattr(exc, "status_code", 500), content=content)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para excepciones no manejadas."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    details = [{"type": type(exc).__name__, "message": str(exc)}]
    error_response = ErrorResponse(
        error=True,
        message="Error interno del servidor",
        details=details
    )
    
    content = jsonable_encoder(error_response)
    return JSONResponse(status_code=500, content=content)


def setup_error_handlers(app):
    """
    Registrar handlers de excepciones en la aplicación FastAPI.
    
    IMPORTANTE: El orden importa - los handlers más específicos primero.
    """
    # Middleware general
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Handlers específicos de dominio (PRIMERO para que tengan prioridad)
    app.add_exception_handler(BusinessRuleViolationError, domain_exception_handler)
    app.add_exception_handler(DomainValidationError, domain_exception_handler)
    app.add_exception_handler(UnitNotFoundError, domain_exception_handler)
    
    # Handlers de validación y HTTP
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Handler catch-all para excepciones no manejadas
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers configured successfully")


# Funciones utilitarias para crear respuestas de error consistentes

def create_error_response(
    message: str, 
    status_code: int = 400,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Crear respuesta de error estandarizada.
    
    Args:
        message: Mensaje de error
        status_code: Código HTTP
        details: Detalles adicionales del error
        
    Returns:
        JSONResponse con formato estandarizado
    """
    error = ErrorResponse(
        error=True, 
        message=message, 
        details=[details] if details else []
    )
    content = jsonable_encoder(error)
    return JSONResponse(status_code=status_code, content=content)


def create_validation_error_response(
    errors: list,
    message: str = "Error de validación"
) -> JSONResponse:
    """
    Crear respuesta de error de validación estandarizada.
    
    Args:
        errors: Lista de errores de validación
        message: Mensaje general del error
        
    Returns:
        JSONResponse con formato estandarizado
    """
    validation_response = ValidationErrorResponse(
        error=True,
        message=message,
        validation_errors=errors,
        timestamp=datetime.utcnow()
    )
    content = jsonable_encoder(validation_response)
    return JSONResponse(status_code=422, content=content)