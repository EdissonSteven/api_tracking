Tests Unitarios - POST /api/v1/checkpoints
Tests unitarios para el endpoint de creación de checkpoints siguiendo Clean Architecture, DDD y SOLID.

1. tests/unit/conftest.py
Fixtures específicas para tests unitarios:

Mocks de Use Cases
Mocks de Validation Service
Usuarios de prueba (admin, operator, viewer)
Result objects (success/failure)
2. tests/unit/test_helpers.py
Factories para crear objetos de prueba:

DTOFactory: Crea CheckpointDTOs
UserFactory: Crea usuarios con diferentes roles y permisos
3. tests/unit/test_checkpoint_controller.py
5 tests esenciales del MVP para POST /api/v1/checkpoints

🧪 Cobertura de Tests
5 Tests Esenciales
test_01_create_checkpoint_success
✅ Caso exitoso (happy path)
Usuario autorizado crea checkpoint válido
Retorna 201 con checkpoint creado
test_02_create_checkpoint_validation_fails
✅ Validación de campos requeridos
Tracking ID y location vacíos
Retorna errores de validación
test_03_create_checkpoint_unit_not_found
✅ Unidad no existe en sistema
Retorna 404 ResourceNotFoundError
test_04_create_checkpoint_without_permission
✅ Usuario sin permiso checkpoint:create
Retorna 403 AuthorizationError
test_05_create_checkpoint_idempotent
✅ Checkpoint duplicado (mismo tracking_id + status)
Retorna checkpoint existente sin error
🚀 Ejecución
Ejecutar solo tests unitarios de checkpoint controller
bash
pytest tests/unit/test_checkpoint_controller.py -v
Ejecutar todos los tests unitarios
bash
pytest tests/unit/ -v
Ejecutar un test específico
bash
pytest tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_01_create_checkpoint_success -v
Con cobertura
bash
pytest tests/unit/test_checkpoint_controller.py --cov=src.interfaces.api.v1.controllers --cov-report=html
Ejecutar solo tests marcados como unit
bash
pytest -m unit -v
📊 Output Esperado
tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_01_create_checkpoint_success PASSED
tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_02_create_checkpoint_validation_fails PASSED
tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_03_create_checkpoint_unit_not_found PASSED
tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_04_create_checkpoint_without_permission PASSED
tests/unit/test_checkpoint_controller.py::TestCreateCheckpointMVP::test_05_create_checkpoint_idempotent PASSED

========================== 5 passed in 0.23s ==========================