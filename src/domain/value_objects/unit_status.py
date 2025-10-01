from enum import Enum
from typing import List

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
            UnitStatus.CREATED: [UnitStatus.PICKED_UP, UnitStatus.CANCELLED],
            UnitStatus.PICKED_UP: [UnitStatus.IN_TRANSIT, UnitStatus.EXCEPTION],
            UnitStatus.IN_TRANSIT: [UnitStatus.AT_FACILITY, UnitStatus.EXCEPTION],
            UnitStatus.AT_FACILITY: [UnitStatus.OUT_FOR_DELIVERY, UnitStatus.IN_TRANSIT, UnitStatus.EXCEPTION],
            UnitStatus.OUT_FOR_DELIVERY: [UnitStatus.DELIVERED, UnitStatus.EXCEPTION, UnitStatus.RETURNED],
            UnitStatus.DELIVERED: [UnitStatus.RETURNED],
            UnitStatus.EXCEPTION: [UnitStatus.IN_TRANSIT, UnitStatus.AT_FACILITY, UnitStatus.OUT_FOR_DELIVERY, UnitStatus.RETURNED],
            UnitStatus.RETURNED: [UnitStatus.AT_FACILITY, UnitStatus.CANCELLED],
            UnitStatus.CANCELLED: []
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
    
    def get_allowed_transitions(self) -> List[str]:
        """Retorna lista de estados permitidos para transición"""
        transitions = {
            "created": ["picked_up"],
            "picked_up": ["in_transit"],
            "in_transit": ["at_facility", "out_for_delivery"],
            "at_facility": ["in_transit", "out_for_delivery"],
            "out_for_delivery": ["delivered", "exception"],
            "delivered": [],
            "exception": ["in_transit", "out_for_delivery"]
        }
        return transitions.get(self.value, [])