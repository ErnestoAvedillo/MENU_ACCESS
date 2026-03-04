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
from muelles.lineal.compresion import MuelleCompresion
from muelles.lineal.traccion import MuelleTraccion
from muelles.pymodels.material import Material
from muelles.lineal.goodman import GoodmanData, GoodmanAnalyzer
import traceback

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


def calculadora_compresion(request):
    """Vista de la calculadora de muelles de compresión"""
    resultado = None
    materials = get_available_materials()
    muelle = None  # Inicializar la variable
    if request.method == 'POST':
        try:
            datos_entrada_muelle = get_data_spring(request)
            # Crear objeto Material desde el código
            material_obj = Material(nombre_material=datos_entrada_muelle['material'])

            muelle = MuelleCompresion(
                material=material_obj,  
                diametro_hilo=float(request.POST.get('diametero_hilo', 0))  # Usar el nombre correcto del HTML
            )
            muelle.validate_diameters(datos_entrada_muelle['diametro_exterior'], None, None)
            muelle.calculate_spring_properties(
                numero_espiras=datos_entrada_muelle['numero_espiras'],
                pitch=None,
                longitud_libre=datos_entrada_muelle['longitud_libre']
            )
            muelle_data = muelle.get_spring_data()
            
            # Generar curva de esfuerzos si se proporcionan longitudes inicial y final
            muelle.add_posicion_carga(datos_entrada_muelle['longitud_inicial'])
            muelle.add_posicion_carga(datos_entrada_muelle['longitud_final'])

            # Generar curva de esfuerzos vs recorrido
            curva_esfuerzo_vs_travel = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_travel_graph()
                curva_esfuerzo_vs_travel = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_travels()
                }
            except Exception:
                curva_esfuerzo_vs_travel = None

            curva_esfuerzo_vs_position = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_position_graph()
                curva_esfuerzo_vs_position = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_esfuerzo_vs_position = None

            #Generar curva de diametros vs posición
            curva_diametros_vs_posicion = None
            try:
                curva_imagen_b64 = muelle.get_diameter_vs_position_graph()
                curva_diametros_vs_posicion = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_diametros_vs_posicion = None

            # Generar diagrama de Goodman usando método del objeto MuelleLineal
            goodman_data = None
            muelle.shot_peening = datos_entrada_muelle['shot_peening'] == 'si'
            muelle.numero_ciclos = datos_entrada_muelle['numero_ciclos']
            try:
                # Si el usuario envió longitudes, pasar esas; si no, el método usará valores por defecto
                goodman_data = muelle.create_goodman_diagram()
            except Exception:
                goodman_data = None
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
                    'longitud_libre': muelle.longitud_libre,
                    'numero_espiras': muelle.numero_espiras,
                    'diametro_exterior': muelle_data.get('diametro_medio', 0) + muelle_data.get('diametro_hilo', 0),
                    'diametro_interior': muelle_data.get('diametro_medio', 0) - muelle_data.get('diametro_hilo', 0),
                    'longitud_bloqueo': round(muelle_data.get('longitud_bloqueo', 0), 2),
                    'curva_esfuerzos': curva_esfuerzo_vs_position,
                    'curva_recorrido': curva_esfuerzo_vs_travel,
                    'curva_diametros': curva_diametros_vs_posicion,
                    'diagrama_goodman': goodman_data,
                    'numero_ciclos': muelle.numero_ciclos,
                    'shot_peening': muelle.shot_peening,
                    'tension_inicial': round(muelle_data.get('tension_inicial', 0), 2)
                }
        except Exception as e:
            print(f"Error en cálculo de muelle: {e}")
            tb = traceback.format_exc()
            if muelle is not None:
                try:
                    muelle_data = muelle.get_spring_data()
                    for key, value in muelle_data.items():
                        print(f"{key}: {value}")
                except:
                    pass
            resultado = {'error': f'Error en los cálculos: {str(e)}', 'traceback': tb}
    return render(request, 'muelles/calculadora_compresion.html', {
        'resultado': resultado,
        'materiales': materials,
    })


def calculadora_traccion(request):
    """Vista de la calculadora de muelles de tracción"""
    resultado = None
    materials = get_available_materials()
    muelle = None  # Inicializar la variable
    if request.method == 'POST':
        try:
            datos_entrada_muelle = get_data_spring(request)
                    # Crear objeto Material desde el código
            material_obj = Material(nombre_material=datos_entrada_muelle['material'])

            muelle = MuelleTraccion(
                material=material_obj,  
                diametro_hilo=float(request.POST.get('diametero_hilo', 0))  # Usar el nombre correcto del HTML
            )
            muelle.validate_diameters(datos_entrada_muelle['diametro_exterior'], None, None)
            muelle.calculate_spring_properties(
                numero_espiras=datos_entrada_muelle['numero_espiras'],
                pitch=None,
                longitud_libre=datos_entrada_muelle['longitud_libre']
            )
            muelle.set_tension_inicial(float(request.POST.get('tension_inicial', 0)) if request.POST.get('tension_inicial') else 0.0)
            muelle_data = muelle.get_spring_data()

            tension_inicial = float(request.POST.get('tension_inicial', 0)) if request.POST.get('tension_inicial') else 0.0
            muelle.set_tension_inicial(tension_inicial)
            
            diametro_exterior = float(request.POST.get('diametro_exterior', 0)) if request.POST.get('diametro_exterior') else None
            longitud_libre = float(request.POST.get('longitud_libre', 0))
            numero_espiras = float(request.POST.get('numero_espiras', 0))
            numero_ciclos = float(request.POST.get('numero_ciclos', 1e6))  # Valor por defecto de 1 millón de ciclos

            # Asignar el número de ciclos al objeto muelle (ya leído desde el formulario)
            muelle.numero_ciclos = numero_ciclos
            muelle.shot_peening = request.POST.get('shot_peening') == 'si'

            muelle.validate_diameters(diametro_exterior, None, None)
            muelle.calculate_spring_properties(
                numero_espiras=numero_espiras,
                pitch=None,
                longitud_libre=longitud_libre
            )
            muelle_data = muelle.get_spring_data()
            
            # Generar curva de esfuerzos si se proporcionan longitudes inicial y final
            longitud_inicial = float(request.POST.get('longitud_inicial', 0))
            longitud_final = float(request.POST.get('longitud_final', 0))
            muelle.add_posicion_carga(longitud_inicial)
            muelle.add_posicion_carga(longitud_final)

            # Generar curva de esfuerzos usando método del objeto MuelleLineal
            curva_esfuerzo_vs_position = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_position_graph()
                curva_esfuerzo_vs_position = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_esfuerzo_vs_position = None

            # Generar curva de esfuerzos vs recorrido
            curva_esfuerzo_vs_travel = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_travel_graph()
                curva_esfuerzo_vs_travel = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_travels()
                }
            except Exception:
                curva_esfuerzo_vs_travel = None

            # Generar curva de esfuerzos vs posición
            curva_esfuerzo_vs_position = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_position_graph()
                curva_esfuerzo_vs_position = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_esfuerzo_vs_position = None

            #Generar curva de diametros vs posición
            curva_diametros_vs_posicion = None
            try:
                curva_imagen_b64 = muelle.get_diameter_vs_position_graph()
                curva_diametros_vs_posicion = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_diametros_vs_posicion = None

            # Generar diagrama de Goodman usando método del objeto MuelleLineal
            goodman_data = None
            try:
                # Si el usuario envió longitudes, pasar esas; si no, el método usará valores por defecto
                goodman_data = muelle.create_goodman_diagram()
            except Exception:
                goodman_data = None

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
                    'longitud_libre': muelle.longitud_libre,
                    'numero_espiras': muelle.numero_espiras,
                    'diametro_exterior': muelle_data.get('diametro_medio', 0) + muelle_data.get('diametro_hilo', 0),
                    'diametro_interior': muelle_data.get('diametro_medio', 0) - muelle_data.get('diametro_hilo', 0),
                    'shot_peening': muelle.shot_peening,
                    'tension_inicial': round(muelle_data.get('tension_inicial', 0), 2),
                    'curva_esfuerzos': curva_esfuerzo_vs_position,
                    'curva_recorrido': curva_esfuerzo_vs_travel,
                    'curva_diametros': curva_diametros_vs_posicion,
                    'diagrama_goodman': goodman_data,
                    'numero_ciclos': muelle.numero_ciclos,
                    'shot_peening': muelle.shot_peening,
                    'tension_inicial': round(muelle_data.get('tension_inicial', 0), 2)
                }
        except Exception as e:
            print(f"Error en cálculo de muelle: {e}")
            tb = traceback.format_exc()
            if muelle is not None:
                try:
                    muelle_data = muelle.get_spring_data()
                    for key, value in muelle_data.items():
                        print(f"{key}: {value}")
                except:
                    pass
            resultado = {'error': f'Error en los cálculos: {str(e)}', 'traceback': tb}
        return render(request, 'muelles/calculadora_traccion.html', {
            'resultado': resultado,
            'materiales': materials,
        })

def get_data_spring(request):
    datos_muelle = {
        'material': request.POST.get('material'),
        'shot_peening': request.POST.get('shot_peening') == 'si',
        'diametro_exterior': float(request.POST.get('diametro_exterior', 0)) if request.POST.get('diametro_exterior') else None,
        'longitud_libre': float(request.POST.get('longitud_libre', 0)),
        'numero_espiras': float(request.POST.get('numero_espiras', 0)),
        'numero_ciclos': float(request.POST.get('numero_ciclos', 1e6)),
        'longitud_inicial': float(request.POST.get('longitud_inicial', 0)) if request.POST.get('longitud_inicial') else None,
        'longitud_final': float(request.POST.get('longitud_final', 0)) if request.POST.get('longitud_final') else None,
    }
    return datos_muelle

def get_curves(muelle):
    """Función para generar las curvas de esfuerzos vs posición y esfuerzos vs recorrido"""
    # Esta función se puede implementar para generar las curvas usando los métodos del objeto MuelleLineal
    # Generar curva de esfuerzos vs posición


def calculadora(request, template_name='muelles/calculadora_compresion.html', default_tipo='lineal'):
    """Vista de la calculadora de muelles"""
    resultado = None
    materiales = get_available_materials()
    muelle = None  # Inicializar la variable
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            tipo_muelle = str(request.POST.get('tipo_muelle', default_tipo)).strip().lower()
            material_code = request.POST.get('material')
            longitud_inicial = float(request.POST.get('longitud_inicial', 0)) if request.POST.get('longitud_inicial') else None
            longitud_final = float(request.POST.get('longitud_final', 0)) if request.POST.get('longitud_final') else None
            shot_peening = request.POST.get('shot_peening') == 'si'
            
            # Crear objeto Material desde el código
            material_obj = Material(nombre_material=material_code)

            spring_class = MuelleTraccion if tipo_muelle == 'traccion' else MuelleCompresion
            
            muelle = spring_class(
                material=material_obj,  
                diametro_hilo=float(request.POST.get('diametero_hilo', 0))  # Usar el nombre correcto del HTML
            )
            # Propiedades adicionales desde el formulario
            muelle.shot_peening = shot_peening

            if isinstance(muelle, MuelleTraccion):
                tension_inicial = float(request.POST.get('tension_inicial', 0)) if request.POST.get('tension_inicial') else 0.0
                muelle.set_tension_inicial(tension_inicial)
            
            diametro_exterior = float(request.POST.get('diametro_exterior', 0)) if request.POST.get('diametro_exterior') else None
            diametro_interior = float(request.POST.get('diametro_interior', 0)) if request.POST.get('diametro_interior') else None
            diametro_medio = float(request.POST.get('diametro_medio', 0)) if request.POST.get('diametro_medio') else None
            longitud_libre = float(request.POST.get('longitud_libre', 0))
            numero_espiras = float(request.POST.get('numero_espiras', 0))
            numero_ciclos = float(request.POST.get('numero_ciclos', 1e6))  # Valor por defecto de 1 millón de ciclos

            # Asignar el número de ciclos al objeto muelle (ya leído desde el formulario)
            muelle.numero_ciclos = numero_ciclos

            muelle.validate_diameters(diametro_exterior, diametro_interior, diametro_medio)
            muelle.calculate_spring_properties(
                numero_espiras=numero_espiras,
                pitch=None,
                longitud_libre=longitud_libre
            )
            muelle_data = muelle.get_spring_data()
            
            # Generar curva de esfuerzos si se proporcionan longitudes inicial y final
            muelle.add_posicion_carga(longitud_inicial)
            muelle.add_posicion_carga(longitud_final)

            # Generar curva de esfuerzos usando método del objeto MuelleLineal
            curva_esfuerzo_vs_position = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_position_graph()
                curva_esfuerzo_vs_position = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_esfuerzo_vs_position = None

            # Generar curva de esfuerzos vs recorrido
            curva_esfuerzo_vs_travel = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_travel_graph()
                curva_esfuerzo_vs_travel = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_travels()
                }
            except Exception:
                curva_esfuerzo_vs_travel = None

            # Generar curva de esfuerzos vs posición
            curva_esfuerzo_vs_position = None
            try:
                curva_imagen_b64 = muelle.get_forces_vs_position_graph()
                curva_esfuerzo_vs_position = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_esfuerzo_vs_position = None

            #Generar curva de diametros vs posición
            curva_diametros_vs_posicion = None
            try:
                curva_imagen_b64 = muelle.get_diameter_vs_position_graph()
                curva_diametros_vs_posicion = {
                    'imagen': curva_imagen_b64,
                    'datos': muelle.get_data_positions()
                }
            except Exception:
                curva_diametros_vs_posicion = None

            # Generar diagrama de Goodman usando método del objeto MuelleLineal
            goodman_data = None
            try:
                # Si el usuario envió longitudes, pasar esas; si no, el método usará valores por defecto
                goodman_data = muelle.create_goodman_diagram()
            except Exception:
                goodman_data = None
            # if longitud_inicial and longitud_final:
            #     curva_esfuerzo_vs_position = generate_stress_curve(muelle, longitud_inicial, longitud_final, longitud_libre)
            
            # Generar diagrama de Goodman
            # goodman_data = None
            # if longitud_inicial and longitud_final:
                # goodman_data = generate_goodman_diagram(muelle, longitud_inicial, longitud_final, shot_peening, numero_ciclos)
            
            # Obtener los datos calculados
            resultado = {
                'tipo_muelle': tipo_muelle,
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
                'curva_esfuerzos': curva_esfuerzo_vs_position,
                'curva_recorrido': curva_esfuerzo_vs_travel,
                'curva_diametros': curva_diametros_vs_posicion,
                'diagrama_goodman': goodman_data,
                'numero_ciclos': muelle.numero_ciclos,
                'shot_peening': muelle.shot_peening,
                'tension_inicial': round(muelle_data.get('tension_inicial', 0), 2)
            }
            
        except Exception as e:
            print(f"Error en cálculo de muelle: {e}")
            tb = traceback.format_exc()
            if muelle is not None:
                try:
                    muelle_data = muelle.get_spring_data()
                    for key, value in muelle_data.items():
                        print(f"{key}: {value}")
                except:
                    pass
            resultado = {'error': f'Error en los cálculos: {str(e)}', 'traceback': tb}
    
    return render(request, template_name, {
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


def generate_goodman_diagram(muelle, longitud_inicial, longitud_final, shot_peening=False,numero_ciclos=1e6):
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
            carga="torsion",  # Para muelles helicoidales es carga de torsión
            numero_ciclos=numero_ciclos
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
