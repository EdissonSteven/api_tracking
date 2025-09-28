import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.encoders import jsonable_encoder
from ..v1.schemas.error_schemas import ErrorResponse, ValidationErrorResponse, ErrorDetail

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


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
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
    """Handler corregido para errores de validación."""
    try:
        logger.warning(f"Validation Error: {exc.errors()}")
        validation_errors: List[Dict[str, Any]] = []
        
        for error in exc.errors():
            # ✅ CORREGIDO: Crear objeto con estructura correcta
            validation_error = {
                "field": ".".join(str(x) for x in error.get("loc", [])),  # Convertir loc a string
                "message": error.get("msg", "Error de validación"),       # ✅ Usar "message" no "msg"
                "type": error.get("type", "validation_error"),
                "input": str(error.get("input", "")),
                "context": error.get("ctx", {})
            }
            validation_errors.append(validation_error)

        # Crear respuesta usando el schema existente
        validation_response = ValidationErrorResponse(
            error=True,
            message="Error de validación en los datos enviados",
            validation_errors=validation_errors,
            timestamp=datetime.utcnow()
        )
        
        content = jsonable_encoder(validation_response)
        return JSONResponse(status_code=422, content=content)
        
    except Exception as handler_error:
        # Si hay error en el handler, devolver respuesta simple
        logger.error(f"Error en validation_exception_handler: {str(handler_error)}")
        
        simple_response = {
            "error": True,
            "message": "Error de validación",
            "details": "Error procesando detalles de validación",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(status_code=422, content=simple_response)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # Normalizar detalles a tipos serializables
    details = [{"type": type(exc).__name__, "message": str(exc)}]
    error_response = ErrorResponse(
        error=True,
        message="Error interno del servidor",
        details=details
    )
    content = jsonable_encoder(error_response)
    return JSONResponse(status_code=500, content=content)


async def starlette_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    logger.warning(f"Starlette HTTP Exception: {getattr(exc, 'status_code', 500)} - {getattr(exc, 'detail', '')}")
    error_response = ErrorResponse(
        error=True,
        message=str(getattr(exc, "detail", "")),
        details=[]
    )
    content = jsonable_encoder(error_response)
    return JSONResponse(status_code=getattr(exc, "status_code", 500), content=content)


def setup_error_handlers(app):
    # Registrar handlers en la app FastAPI/Starlette
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


# Funciones utilitarias para crear respuestas de error consistentes

def create_error_response(
    message: str, 
    status_code: int = 400,
    details: Dict[str, Any] = None
) -> JSONResponse:
    error = ErrorResponse(error=True, message=message, details=[details] if details else [])
    content = jsonable_encoder(error)
    return JSONResponse(status_code=status_code, content=content)


def create_validation_error_response(
    errors: list,
    message: str = "Error de validación"
) -> JSONResponse:
    validation_response = ValidationErrorResponse(
        error=True,
        message=message,
        validation_errors=errors,
        timestamp=datetime.utcnow()
    )
    content = jsonable_encoder(validation_response)
    return JSONResponse(status_code=422, content=content)