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
            const isHidden = input.offsetParent === null;
            if (isHidden) {
                return;
            }
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

function setupSpringTypeSelector() {
    const typeSelect = document.getElementById('tipo_muelle');
    const tensionGroup = document.getElementById('traccion_tension_group');
    const tensionInput = document.getElementById('tension_inicial');
    const initialLabel = document.querySelector('label[for="longitud_inicial"]');
    const finalLabel = document.querySelector('label[for="longitud_final"]');
    const compresionEndOptions = document.querySelectorAll('.compresion-end-option');
    const traccionEndOptions = document.querySelectorAll('.traccion-end-option');
    const endOptions = document.querySelectorAll('.end-option');
    const endHiddenInput = document.getElementById('tipo_final');

    if (!typeSelect) {
        return;
    }

    const updateByType = () => {
        const isTraccion = typeSelect.value === 'traccion';

        if (tensionGroup) {
            tensionGroup.style.display = isTraccion ? 'block' : 'none';
        }

        if (tensionInput) {
            tensionInput.required = isTraccion;
        }

        if (initialLabel) {
            initialLabel.textContent = isTraccion ? 'Longitud inicial estirada (mm):' : 'Longitud inicial (mm):';
        }

        if (finalLabel) {
            finalLabel.textContent = isTraccion ? 'Longitud final estirada (mm):' : 'Longitud final (mm):';
        }

        compresionEndOptions.forEach(option => {
            option.style.display = isTraccion ? 'none' : '';
        });

        traccionEndOptions.forEach(option => {
            option.style.display = isTraccion ? '' : 'none';
        });

        if (endHiddenInput) {
            const compresionValues = ['abierto', 'cerrado', 'semi-cerrado', 'rectificado'];
            const traccionValues = [
                'anillo_doble_aleman_entero_centrado',
                'anillo_doble_aleman_entero_lateral',
                'anillo_simple_aleman_centrado',
                'static/img/anillo_simple_aleman_entero_lateral.png',
                'static/img/anillo_simple_aleman_entero_centrado.png',
                'anillo_especial'
            ];

            const validValues = isTraccion ? traccionValues : compresionValues;
            const defaultValue = isTraccion ? 'anillo_doble_aleman_entero_centrado' : 'rectificado';

            if (!validValues.includes(endHiddenInput.value)) {
                const defaultOption = document.querySelector(`.end-option[data-value="${defaultValue}"]`);
                if (defaultOption) {
                    endOptions.forEach(option => option.classList.remove('selected'));
                    defaultOption.classList.add('selected');
                    endHiddenInput.value = defaultValue;
                }
            }
        }
    };

    typeSelect.addEventListener('change', updateByType);
    updateByType();
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

function setupGeometryFieldControlAndDiameterSync() {
    const materialSelect = document.getElementById('material');
    const wireDiameterInput = document.getElementById('diametro_hilo');
    const diametroMedioInput = document.getElementById('diametro_medio');
    const diametroExteriorInput = document.getElementById('diametro_exterior');
    const diametroInteriorInput = document.getElementById('diametro_interior');

    if (!materialSelect || !wireDiameterInput) {
        return;
    }

    const form = materialSelect.closest('form');
    if (!form) {
        return;
    }

    const geometryFields = Array.from(
        form.querySelectorAll('input[type="number"], select')
    ).filter(field => {
        const fieldId = field.id || '';
        const fieldName = field.name || '';
        if (!fieldId && !fieldName) {
            return false;
        }
        if (field === materialSelect || field === wireDiameterInput) {
            return false;
        }
        if (fieldId === 'numero_ciclos' || fieldId === 'shot_peening') {
            return false;
        }
        if (fieldName === 'csrfmiddlewaretoken') {
            return false;
        }
        return true;
    });

    let blockedNotice = null;
    let blockedNoticeTimer = null;

    function showGeometryBlockedMessage() {
        if (!blockedNotice) {
            blockedNotice = document.createElement('div');
            blockedNotice.textContent = 'Geometría bloqueada: selecciona material y diámetro de hilo';
            blockedNotice.style.cssText = [
                'position: fixed',
                'left: 50%',
                'top: 50%',
                'transform: translate(-50%, -50%)',
                'z-index: 9999',
                'padding: 16px 20px',
                'border-radius: 8px',
                'background: #1f2937',
                'color: #fff',
                'font-size: 14px',
                'box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3)',
                'opacity: 0',
                'transition: opacity 0.2s ease'
            ].join(';');
            document.body.appendChild(blockedNotice);
        }

        if (blockedNoticeTimer) {
            clearTimeout(blockedNoticeTimer);
        }

        blockedNotice.style.opacity = '1';
        blockedNoticeTimer = setTimeout(() => {
            blockedNotice.style.opacity = '0';
        }, 1800);
    }

    function toNumber(value) {
        if (value === null || value === undefined || value === '') {
            return null;
        }
        const parsed = Number(String(value).replace(',', '.'));
        return Number.isFinite(parsed) ? parsed : null;
    }

    function formatNumber(value) {
        if (!Number.isFinite(value)) {
            return '';
        }
        return value.toFixed(3).replace(/\.?0+$/, '');
    }

    function isGeometryEnabled() {
        const hasMaterial = Boolean(materialSelect.value);
        const wireDiameter = toNumber(wireDiameterInput.value);
        return hasMaterial && wireDiameter !== null && wireDiameter > 0;
    }

    function updateGeometryAvailability() {
        const enabled = isGeometryEnabled();
        geometryFields.forEach(field => {
            field.disabled = !enabled;
        });
    }

    function setupBlockedGeometryHandlers() {
        // Wrap each disabled field with visual layer that captures clicks
        geometryFields.forEach(field => {
            // Listener directo en pointerdown (más confiable que click para disabled)
            field.addEventListener('pointerdown', function (event) {
                console.log('🔒 Pointerdown en campo:', field.id, 'Disabled:', field.disabled);
                if (field.disabled) {
                    event.preventDefault();
                    event.stopPropagation();
                    console.log('✋ Mostrando mensaje de bloqueado');
                    showGeometryBlockedMessage();
                }
            }, true);

            // También mousedown como fallback
            field.addEventListener('mousedown', function (event) {
                console.log('🔒 Mousedown en campo:', field.id, 'Disabled:', field.disabled);
                if (field.disabled) {
                    event.preventDefault();
                    event.stopPropagation();
                    console.log('✋ Mostrando mensaje de bloqueado (mousedown)');
                    showGeometryBlockedMessage();
                }
            }, true);

            // Keydown para prevenir entrada por teclado
            field.addEventListener('keydown', function (event) {
                if (field.disabled) {
                    event.preventDefault();
                    showGeometryBlockedMessage();
                }
            });
        });

        // Listener global como respaldo
        document.addEventListener('pointerdown', function (event) {
            const target = event.target;
            if (target.disabled && geometryFields.includes(target)) {
                console.log('Global: Campo deshabilitado detectado');
                event.preventDefault();
                event.stopPropagation();
                showGeometryBlockedMessage();
            }
        }, true);
    }

    let isSyncing = false;

    function syncDiameterFields(changedInput) {
        if (isSyncing) {
            return;
        }
        if (!diametroMedioInput || !diametroExteriorInput || !diametroInteriorInput) {
            return;
        }

        const wireDiameter = toNumber(wireDiameterInput.value);
        if (wireDiameter === null || wireDiameter <= 0) {
            return;
        }

        const medio = toNumber(diametroMedioInput.value);
        const exterior = toNumber(diametroExteriorInput.value);
        const interior = toNumber(diametroInteriorInput.value);

        isSyncing = true;
        try {
            if (changedInput === diametroMedioInput && medio !== null) {
                diametroExteriorInput.value = formatNumber(medio + wireDiameter);
                diametroInteriorInput.value = formatNumber(medio - wireDiameter);
            } else if (changedInput === diametroExteriorInput && exterior !== null) {
                diametroMedioInput.value = formatNumber(exterior - wireDiameter);
                diametroInteriorInput.value = formatNumber(exterior - 2 * wireDiameter);
            } else if (changedInput === diametroInteriorInput && interior !== null) {
                diametroMedioInput.value = formatNumber(interior + wireDiameter);
                diametroExteriorInput.value = formatNumber(interior + 2 * wireDiameter);
            }
        } finally {
            isSyncing = false;
        }
    }

    materialSelect.addEventListener('change', updateGeometryAvailability);
    wireDiameterInput.addEventListener('input', function () {
        updateGeometryAvailability();
        // Cuando cambia el diámetro de hilo, recalcular basándose en diámetro medio si existe
        if (diametroMedioInput && diametroMedioInput.value) {
            syncDiameterFields(diametroMedioInput);
        } else if (diametroExteriorInput && diametroExteriorInput.value) {
            syncDiameterFields(diametroExteriorInput);
        } else if (diametroInteriorInput && diametroInteriorInput.value) {
            syncDiameterFields(diametroInteriorInput);
        }
    });

    if (diametroMedioInput) {
        diametroMedioInput.addEventListener('input', function () {
            syncDiameterFields(diametroMedioInput);
        });
    }
    if (diametroExteriorInput) {
        diametroExteriorInput.addEventListener('input', function () {
            syncDiameterFields(diametroExteriorInput);
        });
    }
    if (diametroInteriorInput) {
        diametroInteriorInput.addEventListener('input', function () {
            syncDiameterFields(diametroInteriorInput);
        });
    }

    setupBlockedGeometryHandlers();
    updateGeometryAvailability();
}

// Bloqueo inteligente de campos relacionados en muelle de compresión
function setupCompressionSpringFieldLocking() {
    const pitchInput = document.getElementById('pitch');
    const numeroEspirasInput = document.getElementById('numero_espiras');
    const longitudLibreInput = document.getElementById('longitud_libre');

    // Salir si no están todos los campos (no es formulario de compresión)
    if (!pitchInput || !numeroEspirasInput || !longitudLibreInput) {
        return;
    }

    const fields = [
        { input: pitchInput, name: 'pitch' },
        { input: numeroEspirasInput, name: 'numero_espiras' },
        { input: longitudLibreInput, name: 'longitud_libre' }
    ];

    let blockNotice = null;
    let blockNoticeTimer = null;

    function showCompressionBlockMessage() {
        if (!blockNotice) {
            blockNotice = document.createElement('div');
            blockNotice.textContent = 'Campo bloqueado: relación entre pitch, espiras y longitud libre';
            blockNotice.style.cssText = [
                'position: fixed',
                'left: 50%',
                'top: 50%',
                'transform: translate(-50%, -50%)',
                'z-index: 9999',
                'padding: 16px 20px',
                'border-radius: 8px',
                'background: #f59e0b',
                'color: #fff',
                'font-size: 14px',
                'box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3)',
                'opacity: 0',
                'transition: opacity 0.2s ease'
            ].join(';');
            document.body.appendChild(blockNotice);
        }

        if (blockNoticeTimer) {
            clearTimeout(blockNoticeTimer);
        }

        blockNotice.style.opacity = '1';
        blockNoticeTimer = setTimeout(() => {
            blockNotice.style.opacity = '0';
        }, 1800);
    }

    function updateFieldLocking() {
        // Contar campos rellenos
        const filledCount = fields.filter(f => f.input.value && f.input.value.trim() !== '').length;

        // Si hay 2 campos rellenos, bloquear el tercero
        if (filledCount === 2) {
            fields.forEach(field => {
                if (!field.input.value || field.input.value.trim() === '') {
                    field.input.disabled = true;
                    field.input.style.opacity = '0.5';
                    field.input.style.cursor = 'not-allowed';
                }
            });
        } else {
            // Si no hay 2 campos rellenos, desbloquear todos
            fields.forEach(field => {
                if (field.input.name != "longitud_inicial" && field.input.name != "longitud_final") {
                    field.input.disabled = false;
                    field.input.style.opacity = '1';
                    field.input.style.cursor = 'auto';
                };
            });

        }
    }

    // Agregar event listeners a los tres campos
    fields.forEach(field => {
        // field.input.addEventListener('input', updateFieldLocking);

        // Prevenir entrada en campos bloqueados
        field.input.addEventListener('pointerdown', function (event) {
            if (field.input.disabled) {
                event.preventDefault();
                event.stopPropagation();
                showCompressionBlockMessage();
            }
        }, true);

        field.input.addEventListener('mousedown', function (event) {
            if (field.input.disabled) {
                event.preventDefault();
                event.stopPropagation();
                showCompressionBlockMessage();
            }
        }, true);

        field.input.addEventListener('keydown', function (event) {
            if (field.input.disabled) {
                event.preventDefault();
                showCompressionBlockMessage();
            }
        });
    });

    // Inicializar estado
    updateFieldLocking();
}

// Inicialización del sistema cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    setupFormatDetection();
    setupMaterialDetection();
    setupFormValidation();
    setupSpringTypeSelector();
    setupSpringEndSelector();
    setupMaterialPropertyDetection();
    setupGeometryFieldControlAndDiameterSync();
    setupCompressionSpringFieldLocking();

    // Mostrar mensaje de carga en consola
    console.log('🔧 Sistema de detección de formato HTML activado');
    console.log('🌀 Calculadora de Muelles initialized');
});
