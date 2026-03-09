from muelles.lineal.torsion import MuelleTorsion
from muelles.pymodels.material import Material
from math import pi

# Crear material primero
material = Material(nombre_material="SL")
# Crear muelle con la clase correcta
muelle = MuelleTorsion(material=material, wire_diameter=2.5)
# Configurar propiedades del muelle (usando nombres correctos de métodos)
muelle.calculate_spring_properties(
    diametro_medio=20.0,
    numero_espiras=10,
    pitch=5.0,
    angulo_libre=45.0,
    radious_leg_fija=10.0,
    radious_leg_movil=10.0
)
muelle.add_position(angle=40)
muelle.add_position(angle=10)
muelle.get_positions()
for pos in muelle.get_positions():
    print(f"Posición: Carga={pos.carga} N, Tensión={pos.tension:.2f} MPa")
    print(f"Posición: Carga={pos.carga} N, Deformación={pos.deformacion:.6f} mm/mm")
    print(f"Posición: Carga={pos.carga} N, Factor de seguridad={pos.factor_seguridad:.2f}")
    print("-" * 40)
