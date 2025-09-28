import pytest
from unittest.mock import Mock, AsyncMock
from src.application.use_cases.create_checkpoint_use_case import CreateCheckpointUseCase
from src.application.dtos.checkpoint_dto import CreateCheckpointRequest
from src.domain.value_objects.tracking_id import TrackingId
from src.domain.value_objects.unit_status import UnitStatus

class TestCreateCheckpointUseCase:
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        checkpoint_repo = Mock()
        unit_repo = Mock()
        validation_service = Mock()
        
        return checkpoint_repo, unit_repo, validation_service
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mocked dependencies"""
        checkpoint_repo, unit_repo, validation_service = mock_repositories
        return CreateCheckpointUseCase(checkpoint_repo, unit_repo, validation_service)
    
    @pytest.mark.asyncio
    async def test_create_checkpoint_success(self, use_case, mock_repositories):
        """Test successful checkpoint creation"""
        checkpoint_repo, unit_repo, validation_service = mock_repositories
        
        # Setup mocks
        validation_service.ensure_idempotency = AsyncMock(return_value=False)
        validation_service.validate_checkpoint_creation = AsyncMock(return_value=True)
        checkpoint_repo.save = AsyncMock()
        unit_repo.update_status = AsyncMock()
        
        # Create request
        request = CreateCheckpointRequest(
            tracking_id="TEST_001",
            status="CREATED",
            location="Test Location"
        )
        
        # Execute
        result = await use_case.execute(request)
        
        # Verify
        assert result.tracking_id == "TEST_001"
        assert result.status == "CREATED"
        validation_service.validate_checkpoint_creation.assert_called_once()
        checkpoint_repo.save.assert_called_once()
        unit_repo.update_status.assert_called_once()
