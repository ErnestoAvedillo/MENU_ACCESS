from pydantic import BaseModel, field_validator, model_validator
from .material import Material
import os
from pandas import read_csv

def get_wire_tolerance(diametero_hilo: float) -> float:
    """Obtiene la tolerancia del diámetro del hilo según el diámetro"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    material_dir = os.path.join(os.path.dirname(current_dir), 'material')
    file = os.path.join(material_dir, "DIAMETRO_TOLERANCIAS.csv")
    
    try:
        pd = read_csv(file)
        if pd.iloc[0]['diameter'] > diametero_hilo:
            return pd.iloc[0]['tolerance']
        if diametero_hilo > pd.iloc[len(pd) - 1]['diameter']:
            return pd.iloc[len(pd) - 1]['tolerance']
        for index, row in pd.iterrows():
            if row['diameter'] >= diametero_hilo:
                return last_row['tolerance']
            last_row = row
    except Exception as e:
        print(f"Error al obtener tolerancia: {e}")
        return 0.1  # Valor por defecto

def get_RMa_range(material, diametero_hilo: float) -> tuple:
    """Obtiene el rango de RMa para un material y diámetro de hilo dado"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        material_dir = os.path.join(os.path.dirname(current_dir), 'material')
        file = os.path.join(material_dir, material.RMa_file)
        
        if not os.path.exists(file):
            print(f"Archivo RMa no encontrado: {file}")
            return (1000.0, 1200.0)  # Valores por defecto
            
        df = read_csv(file)
        df.columns = df.columns.str.strip()  # Limpiar espacios en nombres de columnas
        
        # Si el diámetro es menor que el primer valor, usar el primero
        if diametero_hilo <= df.iloc[0]['diameter']:
            return (float(df.iloc[0]['RMa_min']), float(df.iloc[0]['RMa_max']))
        
        # Si el diámetro es mayor que el último valor, usar el último
        if diametero_hilo >= df.iloc[len(df) - 1]['diameter']:
            return (float(df.iloc[len(df) - 1]['RMa_min']), float(df.iloc[len(df) - 1]['RMa_max']))
        
        # Buscar entre qué valores está y retornar el valor inferior
        prev_row = df.iloc[0]
        for index, row in df.iterrows():
            if row['diameter'] >= diametero_hilo:
                return (float(row['RMa_min']), float(row['RMa_max']))
            prev_row = row

        return (1000.0, 1200.0)  # Valores por defecto
        
    except Exception as e:
        print(f"Error al obtener rango RMa: {e}")
        return (1000.0, 1200.0)  # Valores por defecto

class WireCharacteristics(BaseModel):
    material: Material
    diametero_hilo: float
    tolerancia_diametro: float = None
    RMa_min: float = None
    RMa_max: float = None

    @field_validator('diametero_hilo')
    @classmethod
    def validate_diametero_hilo(cls, v):
        """Valida que el diámetro del hilo sea positivo"""
        if v <= 0:
            raise ValueError("El diámetro del hilo debe ser positivo")
        return v
    
    @model_validator(mode='after')
    def assign_wire_characteristics(self):
        """Asigna automáticamente las características del hilo basándose en el material y diámetro"""
        if self.diametero_hilo is not None:
            self.tolerancia_diametro = get_wire_tolerance(self.diametero_hilo)
        
        if self.material and self.diametero_hilo and (self.RMa_min is None or self.RMa_max is None):
            self.RMa_min, self.RMa_max = get_RMa_range(self.material, self.diametero_hilo)
        
        return self
    
    def set_material(self, material:str, diametero_hilo:float):
        """Establece el material del muelle"""
        if not isinstance(material, Material):
            raise ValueError("El material debe ser una instancia de la clase Material")
        if diametero_hilo is None:
            raise ValueError("Debe proporcionar el diámetro del hilo para establecer el material")
        self.material = material
        self.diametero_hilo = diametero_hilo
        self.tolerancia_diametro = get_wire_tolerance(diametero_hilo)
        self.RMa_min, self.RMa_max = get_RMa_range(material, diametero_hilo)

        