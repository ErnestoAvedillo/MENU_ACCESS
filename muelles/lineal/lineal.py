from math import sqrt, pi
from .constants import WAHL_FACTOR_CONSTANTS, TIPOS_FINAL_MUELLE_COMPRESION
from ..pymodels.wire_characteristics import WireCharacteristics
from ..pymodels.material import Material
from ..pymodels.posiciones import PosicionesTable
from .goodman import Goodman
import traceback
from typing import List, Optional
import os
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
import io
import base64
import numpy as np
from .goodman import GoodmanData, GoodmanAnalyzer
"""Clase para el cálculo de un muelle lineal"""


class MuelleLineal(WireCharacteristics):
    # Campos adicionales de MuelleLineal
    diametro_medio: float = 0.0  # en mm
    longitud_libre: float = 0.0  # en mm
    numero_espiras_utiles: float = 0.0
    pitch: float = 0.0  # en mm 
    shot_peening: bool = False
    revestimiento: Optional[str] = None
    indice_muelle: float = 0.0
    posiciones: PosicionesTable = PosicionesTable()
    constante_muelle: float = 0.0  # en N/mm
    factor_wahl: float = 0.0  # factor de Wahl
    factor_wahl_category: Optional[str] = None  # categoría del factor de Wahl
    factor_wahl_eval: Optional[float] = None  # factor de Wahl evaluadoSS
    numero_ciclos: int = 1e6  # Número de ciclos para análisis de fatiga, por defecto 1 millón
    
    def __init__(self, material:Material, diametro_hilo: float, **data):
        """inicializo las variables del muelle a 0"""
        # Inicializar con valores por defecto

        data.update({
            'material': material,
            'diametero_hilo': diametro_hilo,
            'posiciones': PosicionesTable()
        })
        super().__init__(**data)
        self.numero_ciclos = 1e6  # Valor por defecto de 1 millón de ciclos para análisis de fatiga
        self.shot_peening = False  # Valor por defecto sin shot peening
    
    def set_material(self, material:str, diametro_hilo:float):
        """Primera parte: Establece el material del muelle"""
        super().set_material(material, diametro_hilo)
        if not isinstance(material, Material):
            raise ValueError("El material debe ser una instancia de la clase Material")
        if diametro_hilo is None:
            raise ValueError("Debe proporcionar el diámetro del hilo para establecer el material")
    
    def validate_diameters(
            self,
            diametro_exterior:float=None,
            diametro_interior:float=None,
            diametro_medio:float=None
            ):
        """Segunda parte: Valida y establece los diámetros del muelle"""
        numero_espiras: int = 0
        if sum(1 for var in [diametro_exterior, diametro_interior, diametro_medio] if var is not None) != 1:
            raise ValueError("Debe proporcionar exactamente uno de los tres diámetros: exterior, interior, medio")
        if diametro_medio is not None:
            self.set_diametro_medio(diametro_medio)
        else:
            self.calcular_diametro_medio(diametro_exterior, diametro_interior)
        self.calcular_factor_de_wahl()

    def set_diametro_medio(self, diametro_medio):
        """Establece el diámetro medio del muelle"""
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
        """Calcula el índice del muelle"""
        self.indice_muelle = self.diametro_medio / self.diametero_hilo
        return self.indice_muelle
    
    def set_numero_espiras(self, numero_espiras_utiles=None, pitch=None, longitud_libre=None):
        """Establece el número de espiras del muelle"""
        numero_variables = sum(1 for var in [numero_espiras_utiles, pitch, longitud_libre] if var is not None) 
        if numero_variables != 2:
            raise ValueError("Debe proporcionar exactamente dos de las tres variables: numero_espiras_utiles, pitch, longitud_libre")
        if not pitch:
            self.pitch = longitud_libre / numero_espiras_utiles
            self.longitud_libre = longitud_libre
        elif not numero_espiras_utiles:
            self.numero_espiras_utiles = longitud_libre / pitch
            self.pitch = pitch
            self.longitud_libre = longitud_libre
        elif not longitud_libre:
            self.longitud_libre = numero_espiras_utiles * pitch
            self.pitch = pitch
    
    def set_numero_ciclos(self, numero_ciclos):
        """Establece el número de ciclos para el análisis de fatiga"""
        self.numero_ciclos = numero_ciclos
        return self.numero_ciclos

    def calculo_pitch(self, longitud: float):
        """Calcula el pitch del muelle"""
        self.pitch = longitud / self.numero_espiras
        return self.pitch

    def calcular_factor_de_wahl(self):
        """Calcula el factor de Wahl"""
        if self.indice_muelle == 0:
            self.calcular_indice_muelle()
        self.factor_wahl = (4 * self.indice_muelle - 1) / (4 * self.indice_muelle - 4) + 0.615 / self.indice_muelle
        """Evalúa el factor de Wahl y lo clasifica en categorías"""
        if self.factor_wahl < WAHL_FACTOR_CONSTANTS['red'][1]:
            self.factor_wahl_category = 'red'
        elif WAHL_FACTOR_CONSTANTS['orange'][0] <= self.factor_wahl < WAHL_FACTOR_CONSTANTS['orange'][1]:
            self.factor_wahl_category = 'orange'
        else:
            self.factor_wahl_category = 'green'
        return self.factor_wahl, self.factor_wahl_category

    def calcular_constante_muelle(self):
        """Calcula la constante del muelle (N/mm)"""
        try:
            print(f"Calculando constante del muelle con shear_modulus: {self.material.shear_modulus}, diametero_hilo: {self.diametero_hilo}, diametro_medio: {self.diametro_medio}, numero_espiras_utiles: {self.numero_espiras_utiles}")
            self.constante_muelle = (self.material.shear_modulus * self.diametero_hilo**4) / (8 * self.diametro_medio**3 * self.numero_espiras_utiles)
        except ValueError:
            raise ValueError("No se puede calcular la constante del muelle sin el diámetro medio")
        return self.constante_muelle

    def calcula_carga_en_posicion(self, longitud: float):
        """Calcula la carga en una posición dada usando la constante del muelle"""
        if self.constante_muelle == 0:
            self.calcular_constante_muelle()
        carga = self.constante_muelle * (self.longitud_libre - longitud)
        return carga

    def calacula_tension_en_posicion(self, longitud: float):
        """Calcula la tensión en el hilo del muelle en una posición dada"""
        try:
            carga = self.calcula_carga_en_posicion(longitud)
            tension = (8 * self.diametro_medio * carga) / (3.1416 * self.diametero_hilo**3) * self.factor_wahl
            return tension
        except ValueError as e:
            raise ValueError(f"Error al calcular la tensión en posición {longitud}: {e}")

