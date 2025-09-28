from enum import Enum
from dataclasses import dataclass

class UnitStatus(Enum):
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    AT_FACILITY = "at_facility"
    
    def can_transition_to(self, new_status: 'UnitStatus') -> bool:
        transitions = {
            UnitStatus.CREATED: [UnitStatus.PICKED_UP, UnitStatus.EXCEPTION],
            UnitStatus.PICKED_UP: [UnitStatus.IN_TRANSIT, UnitStatus.EXCEPTION],
            UnitStatus.IN_TRANSIT: [UnitStatus.AT_FACILITY, UnitStatus.EXCEPTION],
            UnitStatus.AT_FACILITY: [UnitStatus.OUT_FOR_DELIVERY, UnitStatus.IN_TRANSIT, UnitStatus.EXCEPTION],
            UnitStatus.OUT_FOR_DELIVERY: [UnitStatus.DELIVERED, UnitStatus.EXCEPTION],
            UnitStatus.DELIVERED: [],
            UnitStatus.EXCEPTION: [UnitStatus.PICKED_UP, UnitStatus.IN_TRANSIT, UnitStatus.AT_FACILITY, UnitStatus.OUT_FOR_DELIVERY]
        }
        return new_status in transitions.get(self, [])
    
    @property
    def display_name(self) -> str:
        names = {
            UnitStatus.CREATED: "Creado",
            UnitStatus.PICKED_UP: "Recolectado",
            UnitStatus.IN_TRANSIT: "En Transito",
            UnitStatus.AT_FACILITY: "En Instalacion",
            UnitStatus.OUT_FOR_DELIVERY: "En Entrega",
            UnitStatus.DELIVERED: "Entregado",
            UnitStatus.EXCEPTION: "Excepcion",
            UnitStatus.RETURNED: "Devuelto",
            UnitStatus.CANCELLED: "Cancelado"
        }
        return names[self]