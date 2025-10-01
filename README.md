 Inicio Rápido (5 minutos)
Prerequisitos

Docker instalado (versión 20.10+)
Docker Compose instalado (versión 2.0+)
Puerto 8000 disponible

⚡ Instalación en 3 Pasos
bash# 1. Clonar el repositorio
git clone <repo-url>
cd mi-api-tracking

# 2. Levantar todos los servicios con Docker
docker-compose up -d

# 3. Verificar que todo esté funcionando
curl http://localhost:8000/health
✅ ¡Listo! La API está corriendo en: http://localhost:8000

📖 Documentación Interactiva con Swagger
Una vez levantado el servicio, accede a la documentación interactiva:
🔗 http://localhost:8000/docs
Aquí podrás:

✅ Ver todos los endpoints disponibles
✅ Probar la API directamente desde el navegador
✅ Ver ejemplos de peticiones y respuestas
✅ Autenticarte con JWT de forma visual
✅ Explorar los esquemas de datos

Documentación alternativa (ReDoc):

http://localhost:8000/redoc - Formato más limpio para lectura


🔐 Autenticación (JWT Bearer Token)
Paso 1: Obtener Token
Ve a Swagger: http://localhost:8000/docs y expande el endpoint:
POST /api/v1/auth/login
Usa uno de estos usuarios de prueba:
UsuarioContraseñaRolPermisosadminadmin123AdministradorTodos los permisosoperatoroperator123OperadorLectura y escrituraviewerviewer123VisualizadorSolo lectura
Ejemplo en Swagger:

Click en "Try it out"
Ingresa las credenciales:

json{
  "username": "admin",
  "password": "admin123"
}

Click en "Execute"
Copia el access_token de la respuesta

Paso 2: Autenticarte en Swagger

Click en el botón 🔒 Authorize (arriba a la derecha)
Ingresa el token en este formato:

Bearer <tu_token_aquí>

Click en "Authorize"
¡Ahora puedes usar todos los endpoints protegidos!


🧪 Datos de Prueba Precargados
El sistema viene con 12 unidades de tracking y 26 checkpoints para probar:
Tracking IDs Recomendados para Pruebas
Tracking IDEstadoCheckpointsDescripciónTRK001in_transit2Bogotá → Medellín (en camino)TRK003delivered3Entregado (ciclo completo)TRK004out_for_delivery3Último tramo de entregaTRK008exception3Con problema (dirección incorrecta)TRK009created1Recién creado
Probar en Swagger

Ve a: GET /api/v1/tracking/{tracking_id}
Click en "Try it out"
Ingresa: TRK001
Click en "Execute"
¡Verás el tracking completo con todos sus checkpoints!


🎯 Casos de Uso Principales
1️⃣ Consultar Tracking Completo
bashGET /api/v1/tracking/TRK001
Respuesta:
json{
  "tracking_id": "TRK001",
  "unit": {
    "tracking_id": "TRK001",
    "guide_id": "guid-uuid-here",
    "origin": "Bogotá",
    "destination": "Medellín",
    "status": "in_transit",
    "weight_kg": 2.5
  },
  "checkpoints": [
    {
      "status": "picked_up",
      "location": "Centro de Distribución Bogotá",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "status": "in_transit",
      "location": "Terminal de Transporte",
      "timestamp": "2025-01-15T12:00:00Z"
    }
  ],
  "total_checkpoints": 2
}
2️⃣ Crear Nuevo Checkpoint
bashPOST /api/v1/checkpoints
Body:
json{
  "tracking_id": "TRK001",
  "status": "at_facility",
  "location": "Centro de Distribución Medellín",
  "description": "Paquete llegó a ciudad destino"
}
3️⃣ Listar Unidades por Estado
bashGET /api/v1/shipments/status/in_transit?limit=10&offset=0

📊 Estados del Ciclo Logístico
El sistema maneja 7 estados en el ciclo de vida de un paquete:
EstadoCódigoDescripción✨ CreadoCREATEDGuía generada, esperando recolección📦 RecolectadoPICKED_UPPaquete recogido del remitente🚛 En TránsitoIN_TRANSITEn camino hacia destino🏢 En InstalaciónAT_FACILITYEn bodega/centro de distribución🚚 En EntregaOUT_FOR_DELIVERYÚltimo tramo hacia el cliente✅ EntregadoDELIVEREDRecibido por el destinatario⚠️ ExcepciónEXCEPTIONRequiere atención/problema

🏗️ Arquitectura del Proyecto
Este proyecto implementa Clean Architecture con separación clara de responsabilidades:
src/
├── domain/              # 🎯 Capa de Dominio (Entidades, Value Objects, Reglas de Negocio)
│   ├── entities/        # Unit, Checkpoint, Tracking
│   ├── value_objects/   # TrackingId, UnitStatus
│   └── repositories/    # Interfaces (contratos)
│
├── application/         # 📋 Capa de Aplicación (Casos de Uso, DTOs)
│   ├── use_cases/       # CreateCheckpoint, GetTracking, ListUnits
│   └── dtos/            # Data Transfer Objects
│
├── infrastructure/      # ⚙️ Capa de Infraestructura (Implementaciones)
│   ├── database/        # PostgreSQL con SQLModel
│   ├── cache/           # Redis para cache y rate limiting
│   └── security/        # JWT, autenticación, validación
│
└── interfaces/          # 🌐 Capa de Interfaces (API REST)
    └── api/
        └── v1/          # Controllers, Schemas, Middlewares
Principios Aplicados

✅ Single Responsibility Principle (SRP): Cada clase tiene una única razón para cambiar
✅ Open/Closed Principle (OCP): Abierto a extensión, cerrado a modificación
✅ Liskov Substitution Principle (LSP): Las abstracciones son intercambiables
✅ Interface Segregation Principle (ISP): Interfaces específicas por cliente
✅ Dependency Inversion Principle (DIP): Dependemos de abstracciones, no de concreciones


🛠️ Stack Tecnológico
TecnologíaVersiónPropósitoPython3.11+Lenguaje baseFastAPI0.110+Framework web moderno y rápidoSQLModel0.0.14ORM basado en Pydantic y SQLAlchemyPostgreSQL15Base de datos principalRedis7Cache y rate limitingPydantic2.6+Validación de datosDocker-ContainerizaciónUvicorn0.27+ASGI server

📦 Servicios Docker
El docker-compose.yml levanta 3 servicios:
ServicioPuertoDescripciónapi8000API FastAPI principalpostgres5432Base de datos PostgreSQLredis6379Cache y rate limiting
Comandos Docker Útiles
bash# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs solo de la API
docker-compose logs -f api

# Reiniciar un servicio específico
docker-compose restart api

# Ver estado de servicios
docker-compose ps

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker-compose down -v

# Reconstruir la imagen
docker-compose up -d --build

🧪 Testing
Tests Unitarios y de Integración
bash# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/unit/
pytest tests/integration/
Cargar Más Datos de Prueba
bash# Conectar a PostgreSQL
docker exec -it mi-api-tracking-postgres-1 psql -U trackinguser -d tracking_db

# Ejecutar el script de datos de prueba
\i /docker-entrypoint-initdb.d/test_data.sql

# O desde fuera del contenedor
docker exec -i mi-api-tracking-postgres-1 psql -U trackinguser -d tracking_db < scripts/test_data.sql

🔧 Configuración Avanzada
Variables de Entorno
Crea un archivo .env basado en .env.example:
bash# Base de datos
DATABASE_URL=postgresql://trackinguser:trackingpass@postgres:5432/tracking_db

# Redis
REDIS_URL=redis://redis:6379/0

# Seguridad
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# API
DEBUG=true
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

📈 Monitoreo y Observabilidad
Health Check
bashcurl http://localhost:8000/health
Respuesta esperada:
json{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-15T10:30:00Z"
}
Métricas

Logs estructurados en JSON
Trazabilidad de requests con request_id
Métricas de performance por endpoint


🚦 Endpoints Principales
MétodoEndpointDescripciónAutenticaciónPOST/api/v1/auth/loginObtener token JWT❌ NoGET/api/v1/tracking/{tracking_id}Consultar tracking completo✅ SíPOST/api/v1/checkpointsCrear nuevo checkpoint✅ SíGET/api/v1/shipments/status/{status}Listar unidades por estado✅ SíGET/healthHealth check del sistema❌ NoGET/docsDocumentación Swagger❌ No

🎓 Características Destacadas
✨ Clean Architecture

Separación clara entre capas
Independencia de frameworks
Testeable y mantenible

🔒 Seguridad

Autenticación JWT con roles y permisos
Rate limiting por usuario
Validación de inputs
Headers de seguridad (CORS, CSRF protection)

⚡ Performance

Cache con Redis
Pool de conexiones a BD
Queries optimizados con índices
Lazy loading de relaciones

📊 Observabilidad

Logs estructurados
Métricas por endpoint
Health checks
Trazabilidad de requests


🐛 Troubleshooting
Error: "Port 8000 already in use"
bash# Ver qué está usando el puerto
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Cambiar el puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usa puerto 8001 en tu máquina
Error: "Database connection failed"
bash# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Reiniciar PostgreSQL
docker-compose restart postgres

# Ver logs de PostgreSQL
docker-compose logs postgres
Error: "Redis connection failed"
bash# Verificar Redis
docker-compose ps redis

# Reiniciar Redis
docker-compose restart redis

📞 Contacto y Documentación Adicional

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json


📝 Licencia
Este proyecto es parte de una prueba técnica.

🙏 Agradecimientos
Construido con ❤️ siguiendo las mejores prácticas de:

Clean Architecture (Robert C. Martin)
Domain-Driven Design (Eric Evans)
SOLID Principles
RESTful API Design
12 Factor App


¿Listo para empezar? 🚀
bashdocker-compose up -d
Luego visita: http://localhost:8000/docs