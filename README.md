# API de Tracking Logistico

API RESTful para gestion de checkpoints y seguimiento de paquetes logisticos.

## Inicio Rapido

### Opcion 1: Docker (Recomendado)
`powershell
.\dev.ps1 -Docker
`

### Opcion 2: Desarrollo Local
`powershell
.\dev.ps1 -API
`

### Opcion 3: Manual
`powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m uvicorn src.main:app --reload
`

## URLs

- API: http://localhost:8000
- Documentacion: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Caracteristicas

- Clean Architecture con SOLID
- FastAPI con Swagger en espaÃ±ol
- Validacion robusta con Pydantic
- Docker Compose listo
- Logging estructurado

## Estructura

`
src/
â”œâ”€â”€ domain/           # Logica de negocio
â”œâ”€â”€ application/      # Casos de uso
â”œâ”€â”€ infrastructure/   # Infraestructura
â”œâ”€â”€ interfaces/       # API REST
â””â”€â”€ config/           # Configuracion
`

## Estados de Unidades

- CREATED (Creado)
- PICKED_UP (Recolectado)
- IN_TRANSIT (En Transito)
- AT_FACILITY (En Instalacion)
- OUT_FOR_DELIVERY (En Entrega)
- DELIVERED (Entregado)
- EXCEPTION (Excepcion)

## Ejemplo de Uso

`http
POST /api/v1/checkpoints
{
  "tracking_id": "TRK001234567",
  "status": "PICKED_UP",
  "location": "Centro de Distribucion Bogota",
  "description": "Paquete recolectado sin novedad"
}
`

## TODOs

- [ ] Implementar repositorios con PostgreSQL
- [ ] Agregar autenticacion JWT
- [ ] Tests unitarios e integracion
- [ ] Cache con Redis
- [ ] Rate limiting

---

Construido con Clean Architecture y principios SOLID
