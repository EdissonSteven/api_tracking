import pytest
from src.infrastructure.database.repositories.unit_repository_impl import UnitRepositoryImpl
from src.infrastructure.database.repositories.checkpoint_repository_impl import CheckpointRepositoryImpl
from src.domain.entities.unit import Unit
from src.domain.entities.checkpoint import Checkpoint
from src.domain.value_objects.tracking_id import TrackingId
from src.domain.value_objects.unit_status import UnitStatus

class TestUnitRepository:
    @pytest.mark.asyncio
    async def test_save_and_find_unit(self, test_session):
        """Test unit repository save and find operations"""
        repo = UnitRepositoryImpl(test_session)
        tracking_id = TrackingId("TEST_REPO_001")
        
        # Create and save unit
        unit = Unit.create(
            tracking_id=tracking_id,
            guide_id="GUIDE_REPO_001"
        )
        
        saved_unit = await repo.save(unit)
        await test_session.commit()
        
        # Find unit
        found_unit = await repo.find_by_tracking_id(tracking_id)
        
        assert found_unit is not None
        assert found_unit.tracking_id == tracking_id
        assert found_unit.guide_id == "GUIDE_REPO_001"

    @pytest.mark.asyncio
    async def test_find_units_by_status(self, test_session):
        """Test finding units by status"""
        repo = UnitRepositoryImpl(test_session)
        
        # Create multiple units
        for i in range(3):
            tracking_id = TrackingId(f"TEST_STATUS_{i}")
            unit = Unit.create(tracking_id=tracking_id)
            await repo.save(unit)
        
        await test_session.commit()
        
        # Find units by status
        units = await repo.find_by_status(UnitStatus.CREATED, limit=10)
        
        assert len(units) >= 3