"""Cálculo de muelles de torsión."""
from math import pi
from math import sqrt, atan
from muelles.pymodels.material import Material
from muelles.pymodels.wire_characteristics import WireCharacteristics
from typing import Optional
from muelles.pymodels.posiciones import PosicionesTable


class MuelleTorsion(WireCharacteristics):
    diametro_medio: float = 0.0  # en mm
    diametro_interior: float = 0.0  # en mm
    diametro_exterior: float = 0.0  # en mm
    angulo_libre: float = 0.0  # en grados
    angulo_tangencias: float = 0.0  # en grados
    pitch: float = 0.0  # en mm
    shot_peening: bool = False
    # Número de ciclos para análisis de fatiga, por defecto 1 millón
    numero_ciclos: int = 1e6  
    numero_espiras_utiles: float = 0.0
    numero_espiras: int = 0
    ancho_muelle: float = 0.0  # en mm
    radious_leg_fija: float = 0.0  # en mm
    long_leg_fija: float = 0.0  # en mm
    radious_leg_movil: float = 0.0  # en mm
    long_leg_movil: float = 0.0  # en mm
    indice_muelle: float = 0.0  # factor_wahl: float = 0.0  # factor de Wahl
    factor_wahl_category: Optional[str] = None  # categoría del factor de Wahl
    factor_wahl_eval: Optional[float] = None  # factor de Wahl evaluado
    factor_wahl: float = 0.0  # factor de Wahl
    longitud_hilo_total: float = 0.0  # en mm
    longitud_hilo_cuerpo: float = 0.0  # en mm
    constante_muelle: float = 0.0  # en Nmm/rad
    momento_resistente: float = 0.0  # en Nmm
    # Lista de posiciones para análisis de fatiga
    positions: PosicionesTable = PosicionesTable()

    def __init__(self, material: Material, wire_diameter: float, **data):
        data.update({
            'material': material,
            'diametero_hilo': wire_diameter,
        })
        super().__init__(**data)
        self.numero_ciclos = 1e6  # Valor por defecto de 1 millón de ciclos
        self.shot_peening = False  # Valor por defecto sin shot peening
        self.diametro_medio = 0.0  # en mm
        self.pitch = 0.0  # en mm
        self.numero_espiras_utiles = 0.0
        self.numero_espiras = 0
        self.ancho_muelle = 0.0  # en mm
        self.radious_leg_fija = 0.0  # en mm
        self.long_leg_fija = 0.0  # en mm
        self.radious_leg_movil = 0.0  # en mm
        self.long_leg_movil = 0.0  # en mm
        self.indice_muelle = 0.0  # factor_wahl: float = 0.0  # factor de Wahl
        self.factor_wahl_category = None  # categoría del factor de Wahl
        self.factor_wahl_eval = None  # factor de Wahl evaluado
        self.factor_wahl = 0.0  # factor de Wahl
        self.longitud_hilo_total = 0.0  # en mm
        self.longitud_hilo_cuerpo = 0.0  # en mm
        self.constante_muelle = 0.0  # en Nmm/rad
        self.momento_resistente = 0.0  # en Nmm
        # Lista de posiciones para análisis de fatiga
        self.positions = PosicionesTable()

    def calculate_spring_properties(self,
                                    diametro_medio: float,
                                    numero_espiras: int,
                                    pitch: float,
                                    angulo_libre: float,
                                    radious_leg_fija: float,
                                    radious_leg_movil: float
                                    ):
        """Calcula todas las propiedades del muelle de torsión basándose en los parámetros proporcionados"""
        self.set_diametro_medio(diametro_medio)
        self.set_ancho_muelle(numero_espiras, pitch, angulo_libre)
        self.set_angulo_tangencias(angulo_libre, radious_leg_fija, radious_leg_movil)
        self.set_longitud_hilo(numero_espiras, pitch, angulo_libre, radious_leg_fija, radious_leg_movil)
        self.calcular_indice_muelle()
        self.calcular_factor_de_wahl()
        self.calculate_length_legs(radious_leg_fija, radious_leg_movil)
        self.set_momento_resistente()
        self.calcula_constante_muelle()
        return self.get_spring_properties()

    def set_material(self, material: str, diametero_hilo: float):
        """Establece el material del muelle de torsión"""
        super().set_material(material, diametero_hilo)
        if not isinstance(material, Material):
            raise ValueError("""El material debe ser una instancia de la clase
                             Material""")
        if diametero_hilo is None:
            raise ValueError("""Debe proporcionar el diámetro del hilo para
                            establecer el material""")

    def set_diametro_medio(self, diametro_medio):
        """Establece el diámetro medio del muelle de torsión"""
        if diametro_medio <= 0:
            raise ValueError("El diámetro medio debe ser un valor positivo")
        self.diametro_medio = diametro_medio
        return

    def calcular_indice_muelle(self):
        """Calcula el índice del muelle de torsión"""
        self.indice_muelle = self.diametro_medio / self.diametero_hilo
        return self.indice_muelle

    def calcular_factor_de_wahl(self):
        """Calcula el factor de Wahl para muelles de torsión"""
        if self.indice_muelle is None:
            self.calcular_indice_muelle()

        self.factor_wahl = ((4*self.indice_muelle**2 - self.indice_muelle - 1)
                            /
                            (4 * self.indice_muelle * (self.indice_muelle - 1))
                            )
        if self.indice_muelle < 4:
            self.factor_wahl_category = 'Bajo'
            self.factor_wahl_eval = 1 + 0.5 / self.indice_muelle
        elif 4 <= self.indice_muelle < 8:
            self.factor_wahl_category = 'Medio'
            self.factor_wahl_eval = 1 + 0.75 / self.indice_muelle
        else:
            self.factor_wahl_category = 'Alto'
            self.factor_wahl_eval = 1 + 1.0 / self.indice_muelle

        return self.factor_wahl_eval

    def set_ancho_muelle(self, numero_espiras, pitch, angulo_libre):
        """Establece el ancho del muelle de torsión"""
        if numero_espiras is None or pitch is None or angulo_libre is None:
            raise ValueError("""Debe proporcionar número de espiras útiles,
                             pitch y ángulo libre para establecer el ancho del
                             muelle""")
        self.pitch = pitch
        self.angulo_libre = angulo_libre
        self.ancho_muelle = (numero_espiras + angulo_libre / 360) * pitch
        self.numero_espiras_utiles = (numero_espiras +
                                      angulo_libre / 360 )

        return self.ancho_muelle

    def set_longitud_hilo(self,
                          numero_espiras: int,
                          pitch: float,
                          angulo_libre: float,
                          radious_leg_fija: float,
                          radious_leg_movil: float):
        """Calcula la longitud del hilo del muelle de torsión"""
        parameters_provided = [numero_espiras,
                               pitch,
                               angulo_libre,
                               radious_leg_fija,
                               radious_leg_movil]
        if sum(1 for var in parameters_provided if var is None) > 0:
            raise ValueError("""Debe proporcionar número de espiras útiles,
                             pitch, ángulo libre, y radios de las patas para
                             calcular la longitud del hilo""")
        if self.diametro_medio <= 0:
            raise ValueError("""El diámetro medio debe ser un valor positivo
                             para calcular la longitud del hilo""")
        self.numero_espiras = numero_espiras
        self.pitch = pitch
        self.angulo_libre = angulo_libre
        self.radious_leg_fija = radious_leg_fija
        self.radious_leg_movil = radious_leg_movil
        longitud_una_vuelta = sqrt((pi * self.diametro_medio) ** 2 +
                                   (pitch / (2 * pi)) ** 2) 
        self.longitud_hilo_cuerpo = ((numero_espiras + angulo_libre / 2 / pi) *
                                     longitud_una_vuelta)
        self.calculate_length_legs(radious_leg_fija, radious_leg_movil)
        self.longitud_hilo_total = (self.longitud_hilo_cuerpo +
                                    (self.long_leg_fija + self.long_leg_fija))
        return self.longitud_hilo_total

    def set_angulo_tangencias(self,
                              angulo_libre,
                              radious_leg_fija,
                              radious_leg_movil):
        """Calcula el ángulo de tangencias del muelle de torsión"""
        parameters_provided = [angulo_libre,
                               radious_leg_fija,
                               radious_leg_movil]
        if sum(1 for var in parameters_provided if var is None) > 0:
            raise ValueError("""Debe proporcionar ángulo libre y radios de las
                             patas para calcular el ángulo de tangencias""")
        angulo_cero_equivalente = (2 * pi -
                                   atan(radious_leg_fija / self.diametro_medio) -
                                   atan(radious_leg_movil / self.diametro_medio))
        self.angulo_libre = angulo_libre
        self.radious_leg_fija = radious_leg_fija
        self.radious_leg_movil = radious_leg_movil
        if angulo_cero_equivalente >= angulo_libre:
            self.angulo_tangencias = angulo_cero_equivalente - angulo_libre
        else:
            self.angulo_tangencias = 360 - (angulo_cero_equivalente - angulo_libre)
        self.numero_espiras_utiles = self.numero_espiras + self.angulo_tangencias / 2 / pi
        return self.angulo_tangencias

    def calculate_length_legs(self,
                              radious_leg_fija=None,
                              radious_leg_movil=None):
        """Calcula la longitud de las patas del muelle de torsión"""
        if radious_leg_fija is None :
            self.radious_leg_fija = self.diametro_medio / 2
        if radious_leg_movil is None:

            self.radious_leg_movil = self.diametro_medio / 2
        if radious_leg_fija < self.diametro_medio / 2:
            self.radious_leg_fija = self.diametro_medio / 2
        if radious_leg_movil < self.diametro_medio / 2:
            self.radious_leg_movil = self.diametro_medio / 2
        self.radious_leg_fija = radious_leg_fija
        self.radious_leg_movil = radious_leg_movil
        self.long_leg_fija = sqrt(self.diametro_medio**2 / 4 + radious_leg_fija**2)
        self.long_leg_movil = sqrt(self.diametro_medio**2 / 4 + radious_leg_movil**2)
        return self.long_leg_fija, self.long_leg_movil

    def set_numero_ciclos(self, numero_ciclos):
        """Establece el número de ciclos para el análisis de fatiga del muelle de torsión"""
        self.numero_ciclos = numero_ciclos
        return self.numero_ciclos

    def set_shot_peening(self, shot_peening: bool):
        """Establece si el muelle de torsión ha sido tratado con shot peening"""
        self.shot_peening = shot_peening
        return self.shot_peening

    def calcula_constante_muelle(self):
        """Calcula la constante del muelle de torsión"""
        if self.momento_resistente <= 0:
            self.set_momento_resistente()
        self.constante_muelle = (self.material.young_modulus *
                                 self.momento_resistente /
                                 self.longitud_hilo_total)
        return self.constante_muelle

    def calcular_torque(self, angulo_giro):
        """Calcula el torque aplicado al muelle de torsión para un ángulo de
        giro dado en grados"""
        if angulo_giro <= 0:
            raise ValueError("El ángulo de giro debe ser un valor positivo")
        # Convertir ángulo a radianes
        torque = self.constante_muelle * (angulo_giro * pi / 180)
        return torque

    def set_momento_resistente(self):
        """Calcula el momento resistente del muelle de torsión para un torque
        máximo dado"""
        self.momento_resistente = pi * pow(self.diametro_medio, 4) / 64
        return self.momento_resistente

    def calcular_tension(self, torque):
        """Calcula la tensión máxima en el muelle de torsión para un torque
        dado"""
        if torque <= 0:
            raise ValueError("El torque debe ser un valor positivo para \
            calcular la tensión")
        tension = ((32 * torque * self.factor_wahl) /
                   (pi * pow(self.diametro_medio, 3)))
        return tension

    def add_position(self, angle=None, torque=None):
        """Agrega una posición de ángulo y torque para análisis de fatiga"""
        if angle is None and torque is None:
            raise ValueError("Debe proporcionar un ángulo o un torque solo")
        if angle is not None and torque is not None:
            raise ValueError("Debe proporcionar solo un ángulo o un torque")
        if angle is not None and angle <= 0:
            raise ValueError("El ángulo debe ser un valor positivo")
        if torque is not None and torque <= 0:
            raise ValueError("El torque debe ser un valor positivo")
        if self.constante_muelle <= 0:
            self.calcula_constante_muelle()
        if angle is not None:
            # Convertir ángulo a radianes
            torque = self.constante_muelle * (angle * pi / 180)  
            tension = self.calcular_tension(torque)
        else:
            # Convertir torque a ángulo en grados
            angle = (torque / self.constante_muelle) * (180 / pi)
            tension = self.calcular_tension(torque)
        if not hasattr(self, 'positions'):
            self.positions = PosicionesTable()
        self.positions.add_posicion_carga(angle, torque, tension, self.diametro_exterior, self.diametro_interior)
        return self.positions

    def clean_positions(self):
        """Limpia la lista de posiciones para análisis de fatiga"""
        self.positions.clear_table()
        
        return self.positions.posiciones

    def get_positions(self):
        """Obtiene la lista de posiciones para análisis de fatiga"""
        return self.positions.posiciones
    
    def get_spring_properties(self):
        """Obtiene un diccionario con todas las propiedades del muelle de torsión"""
        return {
            'diametro_medio': self.diametro_medio,
            'diametro_interior': self.diametro_interior,
            'diametro_exterior': self.diametro_exterior,
            'angulo_libre': self.angulo_libre,
            'angulo_tangencias': self.angulo_tangencias,
            'pitch': self.pitch,
            'shot_peening': self.shot_peening,
            'numero_ciclos': self.numero_ciclos,
            'numero_espiras_utiles': self.numero_espiras_utiles,
            'numero_espiras': self.numero_espiras,
            'ancho_muelle': self.ancho_muelle,
            'radious_leg_fija': self.radious_leg_fija,
            'long_leg_fija': self.long_leg_fija,
            'radious_leg_movil': self.radious_leg_movil,
            'long_leg_movil': self.long_leg_movil,
            'indice_muelle': self.indice_muelle,
            'factor_wahl_category': self.factor_wahl_category,
            'factor_wahl_eval': self.factor_wahl_eval,
            'longitud_hilo_total': self.longitud_hilo_total,
            'longitud_hilo_cuerpo': self.longitud_hilo_cuerpo,
            'constante_muelle': self.constante_muelle,
            'momento_resistente': self.momento_resistente
        }