from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class CheckpointId:
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("CheckpointId cannot be empty")
    
    @classmethod
    def generate(cls):
        return cls(str(uuid.uuid4()))