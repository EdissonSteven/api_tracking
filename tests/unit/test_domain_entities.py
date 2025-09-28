import pytest
from datetime import datetime, timedelta
from src.domain.entities.checkpoint import Checkpoint
from src.domain.entities.unit import Unit
from src.domain.entities.tracking import Tracking
from src.domain.value_objects.tracking_id import TrackingId
from src.domain.value_objects.checkpoint_id import CheckpointId
from src.domain.value_objects.unit_status import UnitStatus

class TestCheckpoint:
    def test_create_checkpoint(self):
        """Test checkpoint creation"""
        tracking_id = TrackingId("TEST_001")
        checkpoint = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.CREATED,
            location="Test Location"
        )
        
        assert checkpoint.tracking_id == tracking_id
        assert checkpoint.status == UnitStatus.CREATED
        assert checkpoint.location == "Test Location"
        assert checkpoint.is_valid()

    def test_checkpoint_validation(self):
        """Test checkpoint validation"""
        tracking_id = TrackingId("TEST_001")
        
        # Valid checkpoint
        checkpoint = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.CREATED
        )
        assert checkpoint.is_valid()
        
        # Invalid checkpoint (future timestamp)
        future_time = datetime.utcnow() + timedelta(hours=1)
        invalid_checkpoint = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.CREATED,
            timestamp=future_time
        )
        assert not invalid_checkpoint.is_valid()

class TestUnit:
    def test_create_unit(self):
        """Test unit creation"""
        tracking_id = TrackingId("TEST_001")
        unit = Unit.create(
            tracking_id=tracking_id,
            guide_id="GUIDE_001"
        )
        
        assert unit.tracking_id == tracking_id
        assert unit.current_status == UnitStatus.CREATED
        assert unit.guide_id == "GUIDE_001"

    def test_unit_status_update(self):
        """Test unit status update"""
        tracking_id = TrackingId("TEST_001")
        unit = Unit.create(tracking_id=tracking_id)
        
        # Valid transition
        unit.update_status(UnitStatus.PICKED_UP)
        assert unit.current_status == UnitStatus.PICKED_UP
        
        # Invalid transition should raise error
        with pytest.raises(ValueError):
            unit.update_status(UnitStatus.DELIVERED)  # Can't go from PICKED_UP to DELIVERED

class TestTracking:
    def test_add_checkpoint(self):
        """Test adding checkpoint to tracking"""
        tracking_id = TrackingId("TEST_001")
        unit = Unit.create(tracking_id=tracking_id)
        tracking = Tracking(unit=unit)
        
        checkpoint = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.PICKED_UP
        )
        
        tracking.add_checkpoint(checkpoint)
        
        assert len(tracking.checkpoints) == 1
        assert tracking.get_current_status() == UnitStatus.PICKED_UP
        assert unit.current_status == UnitStatus.PICKED_UP

    def test_checkpoint_ordering(self):
        """Test checkpoint ordering"""
        tracking_id = TrackingId("TEST_001")
        unit = Unit.create(tracking_id=tracking_id)
        tracking = Tracking(unit=unit)
        
        now = datetime.utcnow()
        
        # Add checkpoints out of order
        checkpoint2 = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.IN_TRANSIT,
            timestamp=now + timedelta(minutes=10)
        )
        
        checkpoint1 = Checkpoint.create(
            tracking_id=tracking_id,
            status=UnitStatus.PICKED_UP,
            timestamp=now
        )
        
        tracking.add_checkpoint(checkpoint1)
        tracking.add_checkpoint(checkpoint2)
        
        history = tracking.get_history()
        assert len(history) == 2
        assert history[0].status == UnitStatus.PICKED_UP
        assert history[1].status == UnitStatus.IN_TRANSIT
