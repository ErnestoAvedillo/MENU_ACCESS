from math import sqrt, pi
from .constants import WAHL_FACTOR_CONSTANTS, TIPOS_FINAL_MUELLE
from ..pymodels.wire_characteristics import WireCharacteristics
from ..pymodels.material import Material
from ..pymodels.posiciones import PosicionesTable
from typing import List, Optional
import os
from matplotlib import pyplot as plt
import io
import base64
"""Clase para el cálculo de un muelle lineal"""


class MuelleLineal(WireCharacteristics):
    # Campos adicionales de MuelleLineal
    diametro_medio: float = 0.0  # en mm
    longitud_libre: float = 0.0  # en mm
    numero_espiras: int = 0
    numero_espiras_utiles: float = 0.0
    tipo_final: str = "rectificado"  # por defecto rectificado
    pitch: float = 0.0  # en mm 
    shot_peening: bool = False
    revestimiento: Optional[str] = None
    longitud_hilo: float = 0.0  # en mm
    indice_muelle: float = 0.0
    longitud_bloqueo: float = 0.0  # Longitud con carga máxima en mm
    posiciones: PosicionesTable = PosicionesTable()
    constante_muelle: float = 0.0  # en N/mm
    factor_wahl: float = 0.0  # factor de Wahl
    factor_wahl_category: Optional[str] = None  # categoría del factor de Wahl
    factor_wahl_eval: Optional[float] = None  # factor de Wahl evaluado
    
    def __init__(self, material, diametro_hilo: float, **data):
        """inicializo las variables del muelle a 0"""
        # Inicializar con valores por defecto
        data.update({
            'material': material,
            'diametero_hilo': diametro_hilo,
            'tipo_final': TIPOS_FINAL_MUELLE[4] if len(TIPOS_FINAL_MUELLE) > 4 else "rectificado",
            'posiciones': PosicionesTable()
        })
        super().__init__(**data)
    
    def set_material(self, material:str, diametro_hilo:float):
        """Primera parte: Establece el material del muelle"""
        super().set_material(material, diametro_hilo)
        if not isinstance(material, Material):
            raise ValueError("El material debe ser una instancia de la clase Material")
        if diametro_hilo is None:
            raise ValueError("Debe proporcionar el diámetro del hilo para establecer el material")
    
    def validate_diameters(self, diametro_exterior:float=None, diametro_interior:float=None, diametro_medio:float=None):
        """Segunda parte: Valida y establece los diámetros del muelle"""
        if sum(1 for var in [diametro_exterior, diametro_interior, diametro_medio] if var is not None) != 1:
            raise ValueError("Debe proporcionar exactamente uno de los tres diámetros: exterior, interior, medio")
        if diametro_medio is not None:
            self.set_diametro_medio(diametro_medio)
        else:
            self.calcular_diametro_medio(diametro_exterior, diametro_interior)
        self.calcular_factor_de_wahl()

    def calculate_spring_properties(self,numero_espiras:float=None, pitch:float=None, longitud_libre:float=None):
        """Tercera parte: Calcula todas las propiedades del muelle"""
        self.set_numero_espiras(numero_espiras=numero_espiras, pitch=pitch, longitud_libre=longitud_libre)
        self.calcular_constante_muelle()
        self.calcular_longitud_bloqueo()
        self.calcular_longitud_hilo()
        self.calacula_tension_en_posicion(self.longitud_bloqueo)
        self.calcular_diametro_externo_en_posicion(self.longitud_bloqueo)
    
    def calculate_positions_table(self, step:List):
        """Cuarta parte: Calcula la tabla de posiciones, cargas, tensiones y diámetros externos"""
        for posicion in step:
            self.add_posicion_carga(posicion)

    def set_diametro_medio(self, diametro_medio):
        """Establece el diámetro medio del muelle"""
        self.diametro_medio = diametro_medio
        return
    
    def calcular_diametro_medio(self, diametro_exterior, diametro_interior):
        """Calcula el diámetro medio del muelle"""
        none_variables = sum(1 for var in [diametro_exterior, diametro_interior] if var is not None)
        if none_variables != 1:
            raise ValueError("Debe proporcionar exactamente dos de los tres diámetros")
        if not diametro_exterior:
            return (diametro_interior + self.diametero_hilo)
        if not diametro_interior:
            return (diametro_exterior - self.diametero_hilo)

    def calcular_indice_muelle(self):
        """Calcula el índice del muelle"""
        self.indice_muelle = self.diametro_medio / self.diametero_hilo
        return self.indice_muelle
    
    def calculo_espiras_utiles(self):
        """Calcula el número de espiras útiles del muelle según el tipo de final"""
        print(f"numero de espiras antes de calculo espiras utiles: {self.numero_espiras}")
        if self.tipo_final == 'abierto':
            self.numero_espiras_utiles = self.numero_espiras - 0.5
        elif self.tipo_final == 'cerrado':
            self.numero_espiras_utiles = self.numero_espiras - 1
        elif self.tipo_final == 'semi-cerrado':
            self.numero_espiras_utiles = self.numero_espiras - 0.75
        elif self.tipo_final == 'rectificado':
            self.numero_espiras_utiles = self.numero_espiras - 1
        print(f"numero de espiras utiles despues de calculo espiras utiles: {self.numero_espiras_utiles}")
        return self.numero_espiras_utiles
    
    def set_numero_espiras(self, numero_espiras=None, pitch=None, longitud_libre=None):
        """Establece el número de espiras del muelle"""
        numero_variables = sum(1 for var in [numero_espiras, pitch, longitud_libre] if var is not None) 
        if numero_variables != 2:
            raise ValueError("Debe proporcionar exactamente dos de las tres variables: numero_espiras, pitch, longitud_libre")
        if not pitch:
            self.pitch = longitud_libre / numero_espiras
            self.numero_espiras = numero_espiras
            self.longitud_libre = longitud_libre
        elif not numero_espiras:
            self.numero_espiras = longitud_libre / pitch
            self.pitch = pitch
            self.longitud_libre = longitud_libre
        elif not longitud_libre:
            self.longitud_libre = numero_espiras * pitch
            self.numero_espiras = numero_espiras
            self.pitch = pitch
        self.calculo_espiras_utiles()
    
    def calculo_pitch(self, longitud: float):
        """Calcula el pitch del muelle"""
        self.pitch = longitud / self.numero_espiras
        return self.pitch

    def calcular_longitud_hilo(self):
        """Calcula la longitud del hilo del muelle"""
        self.longitud_hilo = self.numero_espiras * sqrt((pi * self.diametro_medio)**2 + self.pitch**2)
        return self.longitud_hilo

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

    def calcular_constante_muelle(self):
        """Calcula la constante del muelle (N/mm)"""
        try:
            print(f"Calculando constante del muelle con shear_modulus: {self.material.shear_modulus}, diametero_hilo: {self.diametero_hilo}, diametro_medio: {self.diametro_medio}, numero_espiras_utiles: {self.numero_espiras_utiles}")
            self.constante_muelle = (self.material.shear_modulus * self.diametero_hilo**4) / (8 * self.diametro_medio**3 * self.numero_espiras_utiles)
        except ValueError:
            raise ValueError("No se puede calcular la constante del muelle sin el diámetro medio")
        return self.constante_muelle

    def calcular_paso(self):
        """Calcula el paso del muelle"""
        return self.longitud_libre / self.numero_espiras

    def calcular_longitud_bloqueo(self):
        """Calcula la longitud de bloqueo del muelle"""
        self.longitud_bloqueo = self.numero_espiras_utiles * self.diametero_hilo
        return self.longitud_bloqueo

    def calcula_carga_en_posicion(self, posicion: float):
        """Calcula la carga en una posición dada usando la constante del muelle"""
        if self.constante_muelle == 0:
            self.calcular_constante_muelle()
        carga = self.constante_muelle * posicion
        return carga

    def calacula_tension_en_posicion(self, posicion: float):
        """Calcula la tensión en el hilo del muelle en una posición dada"""
        carga = self.calcula_carga_en_posicion(posicion)
        tension = (8 * self.diametro_medio * carga) / (3.1416 * self.diametero_hilo**3) * self.factor_wahl
        return tension
    
    def calcular_diametro_externo_en_posicion(self, longitud:float):
        """Calcula el diámetro externo del muelle"""
        
        diametro_externo = self.diametro_medio + self.diametero_hilo + \
                            self.diametro_medio * self.material.poisson_coef * (self.longitud_libre - longitud) / self.longitud_libre
        return diametro_externo

    def add_posicion_carga(self, longitud: float):
        """Agrega una posición de carga a la tabla de posiciones"""
        self.posiciones.add_posicion_carga(
            posicion=longitud,
            carga=self.calcula_carga_en_posicion(longitud),
            tension=self.calacula_tension_en_posicion(longitud),
            diametro_externo=self.calcular_diametro_externo_en_posicion(longitud)
        )
    
    def vaciar_tablas(self):
        """Vacía las tablas de posiciones, cargas, tensiones y diámetros externos"""
        self.posiciones.clear_table()

    def get_spring_data(self):
        """Retorna un diccionario con los datos principales del muelle"""
        return {
            "material": self.material.nombre_material,
            "young_modulus": self.material.young_modulus,
            "shear_modulus": self.material.shear_modulus,
            "elastic_limit_factor": self.material.elastic_limit_factor,
            "poisson_coef": self.material.poisson_coef,
            "RMa_file": self.material.RMa_file,
            "diametro_hilo": self.diametero_hilo,
            "diametro_medio": self.diametro_medio,
            "longitud_libre": self.longitud_libre,
            "numero_espiras": self.numero_espiras,
            "numero_espiras_utiles": self.numero_espiras_utiles,
            "constante_muelle": self.constante_muelle,
            "factor_wahl": self.factor_wahl,
            "factor_wahl_category": self.factor_wahl_category,
            "longitud_bloqueo": self.longitud_bloqueo,
            "longitud_hilo": self.longitud_hilo
        
        }

    def get_data_positions(self):
        """Retorna la tabla de posiciones, cargas, tensiones y diámetros externos"""
        return self.posiciones.posiciones

    def get_forces_graph(self):
        tabla_posiciones = self.posiciones.posiciones
        posiciones = [pc.posicion for pc in tabla_posiciones]
        cargas = [pc.carga for pc in tabla_posiciones]
        plot = plt.figure()
        plt.plot(posiciones, cargas, marker='o')
        plt.title('Curva de Carga vs Posición')
        plt.xlabel('Posición (mm)')
        plt.ylabel('Carga (N)')
        plt.grid(True)
        # Save the plot to a BytesIO object

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plot_data = base64.b64encode(buf.read()).decode()
        buf.close()
        plt.close()

        return plot_data

    def get_diameter_graph(self):
        tabla_posiciones = self.posiciones.posiciones
        posiciones = [pc.posicion for pc in tabla_posiciones]
        diametros = [pc.diametro_externo for pc in tabla_posiciones]
        plot = plt.figure()
        plt.plot(posiciones, diametros, marker='o', color='orange')
        plt.title('Diámetro Externo vs Posición')
        plt.xlabel('Posición (mm)')
        plt.ylabel('Diámetro Externo (mm)')
        plt.grid(True)
        # Save the plot to a BytesIO object

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plot_data = base64.b64encode(buf.read()).decode()
        buf.close()
        plt.close()

        return plot_data
    
    def create_goodman_diagram(self):
        """Crea el diagrama de Goodman para el muelle"""
        # Placeholder implementation
        # Aquí se implementaría la lógica para crear el diagrama de Goodman
        pass

    
