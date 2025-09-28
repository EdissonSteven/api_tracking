from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

EXEMPT_PATHS = ("/docs", "/redoc", "/openapi.json", "/openapi.yaml", "/static")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # No alterar headers ni aplicar CSP en rutas de documentación/estáticos
        if any(request.url.path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        response: Response = await call_next(request)

        # Eliminar header Server de forma segura
        try:
            del response.headers["server"]
        except KeyError:
            pass

        # Añadir o ajustar CSP (ejemplo mínimo; ajusta según políticas de seguridad)
        csp = "default-src 'self'; frame-ancestors 'none';"
        response.headers["Content-Security-Policy"] = csp

        # Otros headers de seguridad (siempre con claves en minúscula)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware"""
    
    def __init__(self, app: ASGIApp, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["https://tracking.company.com"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers if origin is allowed
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Request-ID"
            response.headers["Access-Control-Max-Age"] = "86400"
        
        return response