from dataclasses import dataclass

@dataclass(frozen=True)
class TrackingId:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("El ID de tracking no puede estar vacio")
        if len(self.value) > 50:
            raise ValueError("El ID de tracking no puede exceder 50 caracteres")


@dataclass(frozen=True)
class CheckpointId:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("El ID de checkpoint no puede estar vacio")
