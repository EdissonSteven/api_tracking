"""
Fixtures específicas para tests unitarios.

Fixtures que mockean dependencias sin llamar a BD ni infraestructura.
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from tests.unit.test_helper import UserFactory


# =====================
# Use Case Mocks
# =====================

@pytest.fixture
def mock_create_checkpoint_use_case():
    """Mock del CreateCheckpointUseCase."""
    mock = Mock()
    mock.execute = Mock()
    return mock


@pytest.fixture
def mock_validation_service():
    """Mock del ValidationService."""
    mock = Mock()
    mock.validate_request = Mock()
    return mock


@pytest.fixture
def mock_event_dispatcher():
    """Mock del DomainEventDispatcher."""
    mock = Mock()
    mock.dispatch = Mock()
    mock.subscribe = Mock()
    return mock


# =====================
# User Fixtures
# =====================

@pytest.fixture
def admin_user():
    """Usuario administrador de prueba."""
    return UserFactory.create_admin_user()


@pytest.fixture
def operator_user():
    """Usuario operador de prueba con permisos de escritura."""
    return UserFactory.create_operator_user()


@pytest.fixture
def viewer_user():
    """Usuario visualizador (solo lectura, SIN permiso checkpoint:create)."""
    return UserFactory.create_viewer_user()


# =====================
# Result Objects
# =====================

@pytest.fixture
def success_result():
    """Mock de Result exitoso."""
    from src.application.result import Result
    
    def create_success(value=None):
        result = Mock(spec=Result)
        result.is_success = Mock(return_value=True)
        result.is_failure = Mock(return_value=False)
        result.value = value
        result.error = None
        return result
    
    return create_success


@pytest.fixture
def failure_result():
    """Mock de Result fallido."""
    from src.application.result import Result
    
    def create_failure(error="Test Error"):
        result = Mock(spec=Result)
        result.is_success = Mock(return_value=False)
        result.is_failure = Mock(return_value=True)
        result.value = None
        result.error = error
        return result
    
    return create_failure