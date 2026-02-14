from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import os
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para el servidor
import matplotlib.pyplot as plt
import numpy as np
from muelles.lineal.lineal import MuelleLineal
from muelles.pymodels.material import Material
from muelles.lineal.goodman import GoodmanData, GoodmanAnalyzer

# Create your views here.

def get_available_materials():
    """Obtiene la lista de materiales disponibles desde materials.csv"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        material_dir = os.path.join(current_dir, 'material')
        csv_path = os.path.join(material_dir, 'materials.csv')
        
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()  # Limpiar espacios en nombres de columnas
        
        materials = []
        for index, row in df.iterrows():
            denomination = str(row['denomination']).strip()
            # Usar la descripción del CSV, limpiando comillas si las hay
            description = str(row.get('descripcion', denomination)).strip().strip("'\"")
            
            materials.append({
                'code': denomination,
                'name': description,
                'shear_modulus': str(row.get('shear_modulus', '')).strip() if pd.notna(row.get('shear_modulus')) else '',
                'elastic_factor': str(row.get('factor_limite_elástico', '')).strip() if pd.notna(row.get('factor_limite_elástico')) else '',
            })
        
        return materials
    except Exception as e:
        print(f"Error al cargar materiales: {e}")
        # Materiales por defecto si falla la lectura del CSV
        return [
            {'code': 'SL', 'name': 'SL - Acero de alto carbono', 'shear_modulus': '81500', 'elastic_factor': '0.5'},
            {'code': 'SM', 'name': 'SM - Acero medio carbono', 'shear_modulus': '81500', 'elastic_factor': '0.5'},
            {'code': 'SH', 'name': 'SH - Acero duro', 'shear_modulus': '81500', 'elastic_factor': '0.5'},
        ]

def index(request):
    """Vista principal de la aplicación de muelles"""
    return render(request, 'muelles/index.html', {
        'titulo': 'Calculadora de Muelles',
        'descripcion': 'Herramienta para calcular especificaciones de muelles'
    })

def calculadora(request):
    """Vista de la calculadora de muelles"""
    resultado = None
    materiales = get_available_materials()
    muelle = None  # Inicializar la variable
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            material_code = request.POST.get('material')
            longitud_inicial = float(request.POST.get('longitud_inicial', 0)) if request.POST.get('longitud_inicial') else None
            longitud_final = float(request.POST.get('longitud_final', 0)) if request.POST.get('longitud_final') else None
            shot_peening = request.POST.get('shot_peening') == 'si'
            
            # Crear objeto Material desde el código
            material_obj = Material(nombre_material=material_code)
            
            muelle = MuelleLineal(
                material=material_obj,
                diametro_hilo=float(request.POST.get('diametero_hilo', 0))  # Usar el nombre correcto del HTML
            )
            
            diametro_exterior = float(request.POST.get('diametro_exterior', 0)) if request.POST.get('diametro_exterior') else None
            diametro_interior = float(request.POST.get('diametro_interior', 0)) if request.POST.get('diametro_interior') else None
            diametro_medio = float(request.POST.get('diametro_medio', 0)) if request.POST.get('diametro_medio') else None
            longitud_libre = float(request.POST.get('longitud_libre', 0))
            numero_espiras = float(request.POST.get('numero_espiras', 0))

            muelle.validate_diameters(diametro_exterior, diametro_interior, diametro_medio)
            muelle.calculate_spring_properties(
                numero_espiras=numero_espiras,
                pitch=None,
                longitud_libre=longitud_libre
            )
            muelle_data = muelle.get_spring_data()
            
            # Generar curva de esfuerzos si se proporcionan longitudes inicial y final
            curva_datos = None
            if longitud_inicial and longitud_final:
                curva_datos = generate_stress_curve(muelle, longitud_inicial, longitud_final, longitud_libre)
            
            # Generar diagrama de Goodman
            goodman_data = None
            if longitud_inicial and longitud_final:
                goodman_data = generate_goodman_diagram(muelle, longitud_inicial, longitud_final, shot_peening)
            
            # Obtener los datos calculados
            resultado = {
                'material_nombre': muelle.material.nombre_material,
                'modulo_corte': muelle.material.shear_modulus,
                'diametro_medio': round(muelle_data.get('diametro_medio', 0), 2),
                'diametero_hilo': round(muelle_data.get('diametro_hilo', 0), 2),
                'indice_muelle': round(muelle_data.get('indice_muelle', 0), 2),
                'constante_muelle': round(muelle_data.get('constante_muelle', 0), 2),
                'pitch': round(muelle_data.get('pitch', 0), 2),
                'numero_espiras_utiles': round(muelle_data.get('numero_espiras_utiles', 0), 1),
                'longitud_hilo': round(muelle_data.get('longitud_hilo', 0), 2),
                'factor_wahl': round(muelle_data.get('factor_wahl', 0), 3),
                'longitud_libre': longitud_libre,
                'numero_espiras': numero_espiras,
                'diametro_exterior': muelle_data.get('diametro_medio', 0) + muelle_data.get('diametro_hilo', 0),
                'diametro_interior': muelle_data.get('diametro_medio', 0) - muelle_data.get('diametro_hilo', 0),
                'longitud_bloqueo': round(muelle_data.get('longitud_bloqueo', 0), 2),
                'curva_esfuerzos': curva_datos,
                'diagrama_goodman': goodman_data,
            }
            
        except Exception as e:
            print(f"Error en cálculo de muelle: {e}")
            if muelle is not None:
                try:
                    muelle_data = muelle.get_spring_data()
                    for key, value in muelle_data.items():
                        print(f"{key}: {value}")
                except:
                    pass
            resultado = {'error': f'Error en los cálculos: {str(e)}'}
    
    return render(request, 'muelles/calculadora.html', {
        'resultado': resultado,
        'materiales': materiales
    })


def generate_stress_curve(muelle, longitud_inicial, longitud_final, longitud_libre):
    """Genera datos para la curva de esfuerzos y diámetros durante el recorrido"""
    try:
        # Crear array de posiciones desde longitud_libre hasta longitud_final
        posiciones = np.linspace(longitud_libre, longitud_inicial, 50)
        cargas = []
        tensiones = []
        diametros_externos = []
        
        for posicion in posiciones:
            if posicion >= longitud_libre:
                # Calcular carga solo si la posición es menor que la longitud libre
                carga = 0
                tension = 0
                diametro_externo = muelle.diametro_medio + muelle.diametero_hilo
            else:
                # Comprimir el muelle
                deformacion = longitud_libre - posicion
                carga = muelle.constante_muelle * deformacion
                
                # Calcular tensión de cortante (fórmula de Wahl)
                tension = (8 * carga * muelle.diametro_medio * muelle.factor_wahl) / (np.pi * muelle.diametero_hilo**3)
                
                # Calcular diámetro externo bajo carga
                # Aproximación: el diámetro aumenta ligeramente por la compresión
                diametro_externo = muelle.diametro_medio + muelle.diametero_hilo
            
            cargas.append(carga)
            tensiones.append(tension)
            diametros_externos.append(diametro_externo)
        
        # Generar gráfico de curva de esfuerzos
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Gráfico 1: Carga vs Posición
        ax1.plot(posiciones, cargas, 'b-', linewidth=2, label='Carga (N)')
        ax1.set_xlabel('Posición (mm)')
        ax1.set_ylabel('Carga (N)')
        ax1.set_title('Curva de Carga vs Posición')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Gráfico 2: Tensión vs Posición
        ax2.plot(posiciones, tensiones, 'r-', linewidth=2, label='Tensión de cortante (MPa)')
        ax2.set_xlabel('Posición (mm)')
        ax2.set_ylabel('Tensión (MPa)')
        ax2.set_title('Curva de Tensión vs Posición')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        
        # Guardar gráfico en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        curva_imagen = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            'imagen': curva_imagen,
            'datos': {
                'posiciones': posiciones.tolist(),
                'cargas': cargas,
                'tensiones': tensiones,
                'diametros_externos': diametros_externos
            }
        }
    except Exception as e:
        print(f"Error generando curva de esfuerzos: {e}")
        return None


def generate_goodman_diagram(muelle, longitud_inicial, longitud_final, shot_peening=False):
    """Genera el diagrama de Goodman para el muelle"""
    try:
        # Calcular tensiones máxima y mínima
        deformacion_max = muelle.longitud_libre - longitud_final
        deformacion_min = muelle.longitud_libre - longitud_inicial
        
        carga_max = muelle.constante_muelle * deformacion_max if deformacion_max > 0 else 0
        carga_min = muelle.constante_muelle * deformacion_min if deformacion_min > 0 else 0
        
        # Tensión de cortante usando fórmula de Wahl
        tension_max = (8 * carga_max * muelle.diametro_medio * muelle.factor_wahl) / (np.pi * muelle.diametero_hilo**3) if carga_max > 0 else 0
        tension_min = (8 * carga_min * muelle.diametro_medio * muelle.factor_wahl) / (np.pi * muelle.diametero_hilo**3) if carga_min > 0 else 0
        
        # Crear análisis de Goodman
        goodman_data = GoodmanData(
            material=muelle.material,
            diameter=muelle.diametero_hilo,
            carga="torsion"  # Para muelles helicoidales es carga de torsión
        )
        
        analyzer = GoodmanAnalyzer(goodman_data, shot_peening=shot_peening)
        
        # Generar diagrama
        fig = analyzer.plot_diagram(tension_max, tension_min, show_plot=False)
        
        # Guardar diagrama en base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        goodman_imagen = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Obtener resumen del análisis
        analisis = analyzer.get_analysis_summary(tension_max, tension_min)
        
        return {
            'imagen': goodman_imagen,
            'analisis': analisis,
            'tensiones': {
                'tension_max': round(tension_max, 2),
                'tension_min': round(tension_min, 2),
                'carga_max': round(carga_max, 2),
                'carga_min': round(carga_min, 2)
            }
        }
    except Exception as e:
        print(f"Error generando diagrama de Goodman: {e}")
        return None
