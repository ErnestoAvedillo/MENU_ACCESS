/**
 * Calculadora de Muelles - JavaScript
 * Sistema de validación, formateo y detección automática para formularios
 * Autor: Sistema de Calculadora de Muelles
 * Fecha: 2026
 */

// Detección y formateo automático para inputs numéricos
function setupFormatDetection() {
    // Detectar todos los inputs numéricos
    const numericInputs = document.querySelectorAll('input[type="number"]');

    numericInputs.forEach(input => {
        // Auto-formateo mientras se escribe
        input.addEventListener('input', function (e) {
            let value = e.target.value;

            // Detectar separador decimal (punto o coma)
            if (value.includes(',')) {
                // Convertir coma a punto para compatibilidad
                value = value.replace(',', '.');
                e.target.value = value;
            }

            // Validar formato numérico
            const isValidNumber = /^-?\d*\.?\d*$/.test(value);

            // Aplicar estilos según validación
            if (value && !isValidNumber) {
                e.target.style.borderColor = '#dc3545';
                e.target.style.backgroundColor = '#fff5f5';
            } else {
                e.target.style.borderColor = '#28a745';
                e.target.style.backgroundColor = '#f8fff8';
            }
        });

        // Formatear al perder el foco
        input.addEventListener('blur', function (e) {
            let value = parseFloat(e.target.value);
            if (!isNaN(value)) {
                // Formatear a 3 decimales si es necesario
                if (value % 1 !== 0) {
                    e.target.value = value.toFixed(3).replace(/\.?0+$/, '');
                }
            }
            // Resetear estilos
            e.target.style.borderColor = '#ced4da';
            e.target.style.backgroundColor = 'white';
        });
    });
}

// Detectar formato de material y auto-completar propiedades
function setupMaterialDetection() {
    const materialSelect = document.getElementById('material');
    const moduloInput = document.querySelector('input[name="modulo_corte"]');

    if (materialSelect && moduloInput) {
        materialSelect.addEventListener('change', function () {
            const selected = this.options[this.selectedIndex];
            const shearModulus = selected.getAttribute('data-shear-modulus');
            const elasticFactor = selected.getAttribute('data-elastic-factor');

            // Auto-completar módulo de corte si está disponible
            if (shearModulus && !moduloInput.value) {
                moduloInput.value = shearModulus;
                moduloInput.style.backgroundColor = '#e7f3ff';
                setTimeout(() => {
                    moduloInput.style.backgroundColor = 'white';
                }, 2000);
            }

            // Mostrar información del material
            showMaterialInfo(selected, shearModulus, elasticFactor);
        });
    }
}

// Mostrar información del material seleccionado
function showMaterialInfo(selectedOption, shearModulus, elasticFactor) {
    let materialInfo = document.getElementById('material-info');
    if (!materialInfo) {
        materialInfo = document.createElement('div');
        materialInfo.id = 'material-info';
        materialInfo.style.cssText = `
            display: block; 
            margin-top: 10px; 
            padding: 8px; 
            background: #e7f3ff; 
            border-left: 4px solid #007bff; 
            border-radius: 4px;
            font-size: 13px;
        `;
        document.getElementById('material').parentNode.appendChild(materialInfo);
    }

    if (shearModulus && elasticFactor) {
        materialInfo.innerHTML = `
            <strong>📊 Propiedades del Material:</strong><br>
            <span style="color: #0056b3;">• Módulo de corte: <strong>${formatNumber(shearModulus)} N/mm²</strong></span><br>
            <span style="color: #0056b3;">• Factor límite elástico: <strong>${formatNumber(elasticFactor)}</strong></span>
        `;
        materialInfo.style.display = 'block';
    } else {
        materialInfo.style.display = 'none';
    }
}

// Formatear números para mostrar
function formatNumber(num) {
    const number = parseFloat(num);
    if (isNaN(number)) return num;

    // Detectar si es entero o decimal
    if (number % 1 === 0) {
        return number.toLocaleString('es-ES');
    } else {
        return number.toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 3 });
    }
}

// Validación de formulario antes del envío
function setupFormValidation() {
    const form = document.querySelector('form');
    form.addEventListener('submit', function (e) {
        const requiredInputs = form.querySelectorAll('input[required], select[required]');
        let hasErrors = false;

        requiredInputs.forEach(input => {
            if (!input.value) {
                input.style.borderColor = '#dc3545';
                input.style.backgroundColor = '#fff5f5';
                hasErrors = true;
            }
        });

        if (hasErrors) {
            e.preventDefault();
            alert('⚠️ Por favor complete todos los campos obligatorios');
        }
    });
}

// Configurar selector visual de extremos de muelle
function setupSpringEndSelector() {
    const endOptions = document.querySelectorAll('.end-option');
    const hiddenInput = document.querySelector('input[name="tipo_final"]');

    endOptions.forEach(option => {
        option.addEventListener('click', function () {
            // Remover selección anterior
            endOptions.forEach(opt => opt.classList.remove('selected'));

            // Seleccionar nueva opción
            this.classList.add('selected');

            // Actualizar valor en input oculto
            const value = this.getAttribute('data-value');
            hiddenInput.value = value;

            // Animación de confirmación
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'translateY(-2px)';
            }, 150);

            // Log para depuración
            console.log('🌀 Tipo de extremo seleccionado:', value);
        });

        // Efecto hover mejorado
        option.addEventListener('mouseenter', function () {
            if (!this.classList.contains('selected')) {
                this.style.transform = 'translateY(-1px)';
            }
        });

        option.addEventListener('mouseleave', function () {
            if (!this.classList.contains('selected')) {
                this.style.transform = 'none';
            }
        });
    });
}

// Configurar auto-detección de propiedades del material (compatibilidad)
function setupMaterialPropertyDetection() {
    const materialSelect = document.getElementById('material');
    if (materialSelect) {
        materialSelect.addEventListener('change', function () {
            const selected = this.options[this.selectedIndex];
            const shearModulus = selected.getAttribute('data-shear-modulus');
            const elasticFactor = selected.getAttribute('data-elastic-factor');

            // Integración con el sistema de detección de formato
            showMaterialInfo(selected, shearModulus, elasticFactor);
        });
    }
}

// Inicialización del sistema cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    setupFormatDetection();
    setupMaterialDetection();
    setupFormValidation();
    setupSpringEndSelector();
    setupMaterialPropertyDetection();

    // Mostrar mensaje de carga en consola
    console.log('🔧 Sistema de detección de formato HTML activado');
    console.log('🌀 Calculadora de Muelles initialized');
});