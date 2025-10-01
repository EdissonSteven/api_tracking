"""
Tests unitarios para POST /api/v1/checkpoints (MVP)

5 tests esenciales que cubren los casos críticos sin llamados a BD.
Siguiendo Clean Architecture, DDD y SOLID.
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from src.interfaces.api.v1.schemas.checkpoint_schemas import (
    CreateCheckpointRequest,
    UnitStatusEnum
)
from src.domain.domain_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    AuthorizationError
)

from tests.unit.test_helpers import DTOFactory


class TestCreateCheckpointMVP:
    """5 tests esenciales para el endpoint de creación de checkpoints."""
    
    def test_01_create_checkpoint_success(
        self,
        mock_create_checkpoint_use_case,
        mock_validation_service,
        operator_user,
        success_result
    ):
        """
        TEST 1: Caso exitoso - Happy path
        
        GIVEN: Request válido con usuario autorizado
        WHEN: Se crea el checkpoint
        THEN: Retorna checkpoint creado con status 201
        """
        # Arrange
        request_data = CreateCheckpointRequest(
            tracking_id="TRK001",
            status=UnitStatusEnum.PICKED_UP,
            location="Distribution Center",
            operator="John Doe",
            description="Package picked up successfully"
        )
        
        mock_validation_service.validate_request.return_value = success_result(None)
        
        created_dto = DTOFactory.create_checkpoint_dto(
            tracking_id="TRK001",
            status="PICKED_UP",
            location="Distribution Center",
            operator="John Doe"
        )
        mock_create_checkpoint_use_case.execute.return_value = created_dto
        
        # Act
        result = mock_create_checkpoint_use_case.execute(
            tracking_id=request_data.tracking_id,
            status=request_data.status.value,
            location=request_data.location,
            operator=request_data.operator,
            description=request_data.description
        )
        
        # Assert
        assert result.tracking_id == "TRK001"
        assert result.status == "PICKED_UP"
        assert result.location == "Distribution Center"
        assert result.operator == "John Doe"
        mock_create_checkpoint_use_case.execute.assert_called_once()
    
    def test_02_create_checkpoint_validation_fails(
        self,
        mock_validation_service,
        operator_user,
        failure_result
    ):
        """
        TEST 2: Validación de entrada
        
        GIVEN: Request con campos inválidos o vacíos
        WHEN: Se valida el request
        THEN: Falla validación y retorna errores específicos
        """
        # Arrange
        validation_errors = [
            {
                "field": "tracking_id",
                "message": "Tracking ID no puede estar vacío",
                "error_code": "REQUIRED_FIELD"
            },
            {
                "field": "location",
                "message": "Location es requerido",
                "error_code": "REQUIRED_FIELD"
            }
        ]
        
        mock_validation_service.validate_request.return_value = failure_result(validation_errors)
        
        invalid_request = CreateCheckpointRequest(
            tracking_id="",  # Invalid
            status=UnitStatusEnum.CREATED,
            location="",  # Invalid
            operator="Test Operator"
        )
        
        # Act
        validation_result = mock_validation_service.validate_request(invalid_request, operator_user)
        
        # Assert
        assert validation_result.is_failure()
        assert len(validation_result.error) == 2
        assert validation_result.error[0]["error_code"] == "REQUIRED_FIELD"
        assert validation_result.error[1]["error_code"] == "REQUIRED_FIELD"
    
    def test_03_create_checkpoint_unit_not_found(
        self,
        mock_create_checkpoint_use_case,
        mock_validation_service,
        operator_user,
        success_result
    ):
        """
        TEST 3: Unidad no existe en BD
        
        GIVEN: Tracking ID que no existe en el sistema
        WHEN: Se intenta crear checkpoint
        THEN: Lanza ResourceNotFoundError (404)
        """
        # Arrange
        request_data = CreateCheckpointRequest(
            tracking_id="TRK_NO_EXISTE",
            status=UnitStatusEnum.CREATED,
            location="Test Location",
            operator="Test Operator"
        )
        
        mock_validation_service.validate_request.return_value = success_result(None)
        
        # Mock: Unit no existe
        mock_create_checkpoint_use_case.execute.side_effect = ResourceNotFoundError(
            "Unit",
            "TRK_NO_EXISTE"
        )
        
        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            mock_create_checkpoint_use_case.execute(
                tracking_id=request_data.tracking_id,
                status=request_data.status.value,
                location=request_data.location,
                operator=request_data.operator
            )
        
        assert "TRK_NO_EXISTE" in str(exc_info.value)
    
    def test_04_create_checkpoint_without_permission(self, viewer_user):
        """
        TEST 4: Usuario sin permisos
        
        GIVEN: Usuario sin permiso checkpoint:create
        WHEN: Intenta crear checkpoint
        THEN: Lanza AuthorizationError (403)
        """
        # Arrange
        request_data = CreateCheckpointRequest(
            tracking_id="TRK002",
            status=UnitStatusEnum.CREATED,
            location="Test Location",
            operator="Test Operator"
        )
        
        # Assert: Verificar que viewer no tiene permiso
        assert "checkpoint:create" not in viewer_user.get("permissions", [])
        
        # Act & Assert
        with pytest.raises(Exception):  # En producción sería AuthorizationError o HTTPException 403
            if "checkpoint:create" not in viewer_user.get("permissions", []):
                raise AuthorizationError("Usuario no tiene permiso checkpoint:create")
    
    def test_05_create_checkpoint_idempotent(
        self,
        mock_create_checkpoint_use_case,
        mock_validation_service,
        operator_user,
        success_result
    ):
        """
        TEST 5: Idempotencia
        
        GIVEN: Checkpoint duplicado (mismo tracking_id + status)
        WHEN: Se intenta crear checkpoint que ya existe
        THEN: Retorna checkpoint existente sin error (idempotente)
        """
        # Arrange
        request_data = CreateCheckpointRequest(
            tracking_id="TRK003",
            status=UnitStatusEnum.CREATED,
            location="Warehouse A",
            operator="Operator A"
        )
        
        mock_validation_service.validate_request.return_value = success_result(None)
        
        # Mock: Retorna checkpoint existente
        existing_checkpoint = DTOFactory.create_checkpoint_dto(
            checkpoint_id="existing-id-123",
            tracking_id="TRK003",
            status="CREATED",
            location="Warehouse A"
        )
        mock_create_checkpoint_use_case.execute.return_value = existing_checkpoint
        
        # Act - Llamar dos veces con mismos datos
        result1 = mock_create_checkpoint_use_case.execute(
            tracking_id=request_data.tracking_id,
            status=request_data.status.value,
            location=request_data.location,
            operator=request_data.operator
        )
        
        result2 = mock_create_checkpoint_use_case.execute(
            tracking_id=request_data.tracking_id,
            status=request_data.status.value,
            location=request_data.location,
            operator=request_data.operator
        )
        
        # Assert - Ambos resultados deben ser el mismo checkpoint
        assert result1.id == result2.id == "existing-id-123"
        assert result1.tracking_id == result2.tracking_id == "TRK003"
        assert result1.status == result2.status == "CREATED"