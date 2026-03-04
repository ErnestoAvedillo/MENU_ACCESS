"""Cálculo de muelles de torsión."""
from math import pi
from math import sqrt, atan
from muelles.pymodels.material import Material
from muelles.pymodels.wire_characteristics import WireCharacteristics
from typing import Optional


class MuelleTorsion(WireCharacteristics):
    diametro_medio: float = 0.0  # en mm
    diametro_interior: float = 0.0  # en mm
    diametro_exterior: float = 0.0  # en mm
    angulo_libre: float = 0.0  # en grados
    angulo_tangencias: float = 0.0  # en grados
    pitch: float = 0.0  # en mm
    shot_peening: bool = False
    numero_ciclos: int = 1e6  # Número de ciclos para análisis de fatiga, por defecto 1 millón
    numero_espiras_utiles: float = 0.0
    numero_espiras: int = 0
    ancho_muelle: float = 0.0  # en mm
    radious_leg_fija: float = 0.0  # en mm
    radious_leg_movil: float = 0.0  # en mm
    indice_muelle: float = 0.0  # factor_wahl: float = 0.0  # factor de Wahl
    factor_wahl_category: Optional[str] = None  # categoría del factor de Wahl
    factor_wahl_eval: Optional[float] = None  # factor de Wahl evaluado

    def __init__(self, material: Material, wire_diameter: float, **data):
        data.update({
            'material': material,
            'diametero_hilo': wire_diameter,
        })
        super().__init__(material=material, diametero_hilo=wire_diameter, **data)
        self.numero_ciclos = 1e6  # Valor por defecto de 1 millón de ciclos
        self.shot_peening = False  # Valor por defecto sin shot peening
        self.diametro_medio = 0.0  # en mm
        self.pitch = 0.0  # en mm

    def set_material(self, material:str, diametero_hilo:float):
        """Establece el material del muelle de torsión"""
        super().set_material(material, diametero_hilo)
        if not isinstance(material, Material):
            raise ValueError("El material debe ser una instancia de la clase Material")
        if diametero_hilo is None:
            raise ValueError("Debe proporcionar el diámetro del hilo para establecer el material")
    
    def set_diametro_medio(self, diametro_medio):
        """Establece el diámetro medio del muelle de torsión"""
        if diametro_medio <= 0:
            raise ValueError("El diámetro medio debe ser un valor positivo")
        self.diametro_medio = diametro_medio
        return
    
    def calcular_diametro_medio(self, diametro_exterior, diametro_interior):
        """Calcula el diámetro medio del muelle"""
        none_variables = sum(1 for var in [diametro_exterior, diametro_interior] if var is not None)
        if none_variables != 1:
            self.diametro_medio = (diametro_exterior + diametro_interior) / 2
            self.diametero_hilo = diametro_exterior - self.diametro_medio
            return self.diametro_medio
        
        if self.diametero_hilo <= 0 or self.diametero_hilo is None:
            raise ValueError("El diámetro del hilo debe ser un valor positivo y no nulo para calcular el diámetro medio")
        if not diametro_exterior:
            return (diametro_interior + self.diametero_hilo)
        if not diametro_interior:
            diametro_medio = diametro_exterior - self.diametero_hilo
        numero_espiras: int = 0
        if diametro_medio <= 0:
            raise ValueError("El diámetro medio calculado debe ser un valor positivo")
        self.set_diametro_medio(diametro_medio)
        return self.diametro_medio
    
    def calcular_indice_muelle(self):
        """Calcula el índice del muelle de torsión"""
        self.indice_muelle = self.diametro_medio / self.diametero_hilo
        return self.indice_muelle
    
    def calcular_factor_de_wahl(self):
        """Calcula el factor de Wahl para muelles de torsión"""
        if self.indice_muelle is None:
            self.calcular_indice_muelle()
        
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
    
    def set_ancho_muelle(self, numero_espiras_utiles, pitch, angulo_libre):
        """Establece el ancho del muelle de torsión"""
        if numero_espiras_utiles is None or pitch is None or angulo_libre is None:
            raise ValueError("Debe proporcionar número de espiras útiles, pitch y ángulo libre para establecer el ancho del muelle")
        self.numero_espiras_utiles = numero_espiras_utiles
        self.pitch = pitch
        self.angulo_libre = angulo_libre
        self.ancho_muelle = (numero_espiras_utiles + angulo_libre / 360) * pitch
        return self.ancho_muelle
    
    def set_longitud_hilo(self):
        """Calcula la longitud del hilo del muelle de torsión"""
        if self.numero_espiras_utiles is None or self.pitch is None or self.angulo_libre is None:
            raise ValueError("Debe proporcionar número de espiras útiles, pitch y ángulo libre para calcular la longitud del hilo")
        longitud_hilo = (self.numero_espiras_utiles) * pi() * self.diametro_medio
        longitud_hilo += sqrt(self.diametro_medio**2 / 4 + self.radious_leg_movil**2)  # Añadir longitud de las patas
        longitud_hilo += sqrt(self.diametro_medio**2 / 4 + self.radious_leg_fija**2)  # Añadir longitud de las patas
        return self.longitud_hilo
    
    def set_angulo_tangencias(self,angulo_libre, radious_leg_fija, radious_leg_movil):
        """Calcula el ángulo de tangencias del muelle de torsión"""
        if angulo_libre is None or radious_leg_fija is None or radious_leg_movil is None:
            raise ValueError("Debe proporcionar ángulo libre y radios de las patas para calcular el ángulo de tangencias")
        angulo_cero_equivalente = 2* pi - atan (radious_leg_fija / self.diametro_medio) - atan (radious_leg_movil / self.diametro_medio)
        self.angulo_libre = angulo_libre
        self.radious_leg_fija = radious_leg_fija
        self.radious_leg_movil = radious_leg_movil
        if angulo_cero_equivalente >= angulo_libre:
            self.angulo_tangencias = angulo_cero_equivalente - angulo_libre
        else:
            self.angulo_tangencias = 360 - (angulo_cero_equivalente - angulo_libre)
        self.numero_espiras_utiles = self.numero_espiras + self.angulo_tangencias / 2 / pi
        return self.angulo_tangencias
    
    def set_numero_ciclos(self, numero_ciclos):
        """Establece el número de ciclos para el análisis de fatiga del muelle de torsión"""
        self.numero_ciclos = numero_ciclos
        return self.numero_ciclos
    
    def set_shot_peening(self, shot_peening: bool):
        """Establece si el muelle de torsión ha sido tratado con shot peening"""
        self.shot_peening = shot_peening
        return self.shot_peening
    
    def calcula_constante_muelle(self, torque_aplicado, angulo_giro):
        """Calcula la constante del muelle de torsión"""
        if angulo_giro <= 0:
            raise ValueError("El ángulo de giro debe ser un valor positivo")
        self.constante_muelle = torque_aplicado / (angulo_giro * pi / 180)  # Convertir ángulo a radianes
        return self.constante_muelle