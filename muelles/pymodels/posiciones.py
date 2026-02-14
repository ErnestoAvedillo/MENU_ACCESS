from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List

class PosicionCarga(BaseModel):
    posicion: float
    carga: Optional[float] = None
    tension: Optional[float] = None
    diametro_externo: Optional[float] = None

class PosicionesTable(BaseModel):
    posiciones: List[PosicionCarga] = []

    def add_posicion_carga(self, posicion: float, carga: Optional[float] = None,
                           tension: Optional[float] = None, diametro_externo: Optional[float] = None):
        """Agrega una nueva posición con sus características a la tabla"""
        nueva_posicion = PosicionCarga(
            posicion=posicion,
            carga=carga,
            tension=tension,
            diametro_externo=diametro_externo
        )
        self.posiciones.append(nueva_posicion)

    def clear_table(self):
        """Vacía la tabla de posiciones"""
        self.posiciones = []