// Editor de JSON interactivo con vista de tabla
class JSONTableEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.data = {};
        this.tableData = [];
        this.selectedRows = new Set();
        this.currentView = 'table';
        this.initializeEvents();
    }

    // Cargar datos JSON
    loadData(jsonText) {
        console.log('Cargando datos JSON:', jsonText);
        try {
            this.data = JSON.parse(jsonText);
            console.log('JSON parseado correctamente:', this.data);
            this.convertToTableData();
            this.renderInterface();
            this.showError('');
        } catch (error) {
            console.error('Error al parsear JSON:', error);
            this.showError('Error al parsear JSON: ' + error.message);
            this.currentView = 'text';

            // Crear interfaz básica para modo texto
            document.getElementById('jsonContainer').innerHTML = `
                <div class="view-tabs">
                    <button class="active" onclick="jsonEditor.switchView('text')">📝 Vista Texto</button>
                </div>
                <div id="textView" class="">
                    <div class="json-controls">
                        <button onclick="jsonEditor.formatJSON()">🎨 Formatear JSON</button>
                        <button onclick="jsonEditor.validateJSON()">✅ Validar JSON</button>
                        <button onclick="jsonEditor.switchView('table')">📊 Ver como Tabla</button>
                    </div>
                    <textarea id="jsonTextArea" class="json-textarea" placeholder="Edita el JSON aquí...">${jsonText}</textarea>
                </div>
                <div id="errorMessage" class="json-error show">${this.showError.message || 'Error al parsear JSON'}</div>
            `;
        }
    }

    // Renderizar vista de texto simple (fallback)
    renderTextView() {
        const interfaceHTML = `
            <div class="view-tabs">
                <button onclick="jsonEditor.switchView('table')">📊 Vista Tabla</button>
                <button class="active" onclick="jsonEditor.switchView('text')">📝 Vista Texto</button>
            </div>
            <div class="json-text-view active">
                <div class="json-controls">
                    <button onclick="jsonEditor.formatJSON()">🎨 Formatear JSON</button>
                    <button onclick="jsonEditor.validateJSON()">✅ Validar JSON</button>
                </div>
                <textarea id="jsonTextArea" class="json-textarea" placeholder="Edita el JSON aquí..."></textarea>
            </div>
            <div id="errorMessage" class="json-error"></div>
        `;
        document.getElementById('jsonContainer').innerHTML = interfaceHTML;
    }

    // Convertir JSON a datos de tabla
    convertToTableData() {
        this.tableData = [];

        // Manejar diferentes estructuras JSON
        if (this.data.links && typeof this.data.links === 'object') {
            // Estructura como la de General.json con links
            Object.entries(this.data.links).forEach(([key, value]) => {
                if (typeof value === 'object' && value !== null) {
                    this.tableData.push({
                        key: key,
                        name: value.name || '',
                        link: value.link || value.LINK || '',
                        type: 'link'
                    });
                }
            });
        } else if (Array.isArray(this.data)) {
            // Array de objetos
            this.data.forEach((item, index) => {
                const row = { _index: index };
                if (typeof item === 'object' && item !== null) {
                    Object.assign(row, item);
                }
                this.tableData.push(row);
            });
        } else if (typeof this.data === 'object') {
            // Objeto plano
            Object.entries(this.data).forEach(([key, value]) => {
                this.tableData.push({
                    key: key,
                    value: typeof value === 'object' ? JSON.stringify(value) : value,
                    type: typeof value
                });
            });
        }
    }

    // Convertir datos de tabla de vuelta a JSON
    convertToJSON() {
        if (this.data.links !== undefined) {
            // Estructura con links
            const newData = { ...this.data };
            newData.links = {};

            this.tableData.forEach(row => {
                if (row.key !== undefined) {
                    newData.links[row.key] = {
                        name: row.name || '',
                        [row.link && row.link.startsWith('http') ? 'link' : 'link']: row.link || ''
                    };
                }
            });

            return newData;
        } else if (this.tableData.length > 0 && this.tableData[0]._index !== undefined) {
            // Array de objetos
            return this.tableData.map(row => {
                const { _index, ...cleanRow } = row;
                return cleanRow;
            });
        } else {
            // Objeto plano
            const newData = {};
            this.tableData.forEach(row => {
                if (row.key !== undefined) {
                    try {
                        newData[row.key] = row.type === 'object' ? JSON.parse(row.value) : row.value;
                    } catch {
                        newData[row.key] = row.value;
                    }
                }
            });
            return newData;
        }
    }

    // Renderizar interfaz principal
    renderInterface() {
        const headers = this.getTableHeaders();

        const interfaceHTML = `
            <div class="view-tabs">
                <button class="${this.currentView === 'table' ? 'active' : ''}" onclick="jsonEditor.switchView('table')">
                    📊 Vista Tabla
                </button>
                <button class="${this.currentView === 'text' ? 'active' : ''}" onclick="jsonEditor.switchView('text')">
                    📝 Vista Texto
                </button>
            </div>
            
            <div id="tableView" class="${this.currentView === 'table' ? '' : 'json-text-view'}">
                <div class="json-controls">
                    <button onclick="jsonEditor.addRow()">➕ Añadir Elemento</button>
                    <button onclick="jsonEditor.deleteSelected()" id="deleteBtn" disabled>🗑️ Eliminar Seleccionados</button>
                    <button onclick="jsonEditor.copySelected()" id="copyBtn" disabled>📋 Copiar Seleccionados</button>
                    <button onclick="jsonEditor.moveUp()" id="moveUpBtn" disabled>⬆️ Mover Arriba</button>
                    <button onclick="jsonEditor.moveDown()" id="moveDownBtn" disabled>⬇️ Mover Abajo</button>
                </div>
                <table class="json-table" id="jsonTable">
                    <thead>
                        <tr>
                            <th><input type="checkbox" id="selectAll" onchange="jsonEditor.toggleSelectAll()"></th>
                            ${headers.map(header => `<th>${this.formatHeader(header)}</th>`).join('')}
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.tableData.map((row, index) => this.renderRow(row, index, headers)).join('')}
                    </tbody>
                </table>
            </div>
            
            <div id="textView" class="${this.currentView === 'text' ? '' : 'json-text-view'}">
                <div class="json-controls">
                    <button onclick="jsonEditor.formatJSON()">🎨 Formatear JSON</button>
                    <button onclick="jsonEditor.validateJSON()">✅ Validar JSON</button>
                    <button onclick="jsonEditor.switchView('table')">📊 Ver como Tabla</button>
                </div>
                <textarea id="jsonTextArea" class="json-textarea" placeholder="Edita el JSON aquí...">${JSON.stringify(this.data, null, 2)}</textarea>
            </div>
            
            <div id="errorMessage" class="json-error"></div>
        `;

        document.getElementById('jsonContainer').innerHTML = interfaceHTML;
        this.updateControlButtons();
    }

    // Obtener headers de la tabla
    getTableHeaders() {
        if (this.tableData.length === 0) return ['key', 'value'];

        const allKeys = new Set();
        this.tableData.forEach(row => {
            Object.keys(row).forEach(key => {
                if (key !== '_index') allKeys.add(key);
            });
        });

        return Array.from(allKeys);
    }

    // Formatear nombre de header
    formatHeader(header) {
        const headerMap = {
            'key': 'Clave',
            'name': 'Nombre',
            'link': 'Enlace',
            'value': 'Valor',
            'type': 'Tipo'
        };
        return headerMap[header] || header.charAt(0).toUpperCase() + header.slice(1);
    }

    // Renderizar una fila
    renderRow(row, index, headers) {
        return `
            <tr data-index="${index}" draggable="true" ondragstart="jsonEditor.dragStart(event)" ondragover="jsonEditor.dragOver(event)" ondrop="jsonEditor.drop(event)">
                <td><input type="checkbox" onchange="jsonEditor.toggleRowSelection(${index})"></td>
                ${headers.map(header => {
            const value = row[header] || '';
            const dataLabel = this.formatHeader(header);
            return `<td data-label="${dataLabel}">
                        <input type="text" value="${value}" onchange="jsonEditor.updateCell(${index}, '${header}', this.value)" placeholder="${header}">
                    </td>`;
        }).join('')}
                <td>
                    <div class="json-row-controls">
                        <button class="copy-btn" onclick="jsonEditor.copyRow(${index})" title="Copiar elemento">📋</button>
                        <button class="delete-btn" onclick="jsonEditor.deleteRow(${index})" title="Eliminar elemento">🗑️</button>
                        <button class="move-btn" title="Arrastrar para mover">⋮⋮</button>
                    </div>
                </td>
            </tr>
        `;
    }

    // Cambiar vista
    switchView(view) {
        this.currentView = view;

        if (view === 'text') {
            // Sincronizar datos de tabla a texto
            try {
                const jsonData = this.convertToJSON();
                document.getElementById('jsonTextArea').value = JSON.stringify(jsonData, null, 2);
            } catch (error) {
                this.showError('Error al convertir tabla a JSON: ' + error.message);
            }
        } else {
            // Sincronizar datos de texto a tabla
            try {
                const textData = document.getElementById('jsonTextArea').value;
                this.data = JSON.parse(textData);
                this.convertToTableData();
            } catch (error) {
                this.showError('Error al parsear JSON desde texto: ' + error.message);
                return;
            }
        }

        this.renderInterface();
    }

    // Añadir nueva fila
    addRow() {
        const headers = this.getTableHeaders();
        const newRow = {};

        headers.forEach(header => {
            newRow[header] = '';
        });

        // Asignar key único si es necesario
        if (headers.includes('key')) {
            newRow.key = String(this.tableData.length);
        }

        this.tableData.push(newRow);
        this.renderInterface();
    }

    // Eliminar fila
    deleteRow(index) {
        if (confirm('¿Estás seguro de que quieres eliminar este elemento?')) {
            this.tableData.splice(index, 1);
            this.selectedRows.clear();
            this.renderInterface();
        }
    }

    // Copiar fila
    copyRow(index) {
        const newRow = { ...this.tableData[index] };

        // Generar nueva key si existe
        if (newRow.key !== undefined) {
            newRow.key = String(this.tableData.length);
        }

        this.tableData.splice(index + 1, 0, newRow);
        this.renderInterface();
    }

    // Actualizar celda
    updateCell(row, col, value) {
        this.tableData[row][col] = value;
    }

    // Selección de filas (similar al CSV)
    toggleRowSelection(index) {
        if (this.selectedRows.has(index)) {
            this.selectedRows.delete(index);
        } else {
            this.selectedRows.add(index);
        }
        this.updateControlButtons();
        this.updateRowHighlight();
    }

    toggleSelectAll() {
        const selectAll = document.getElementById('selectAll');
        const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');

        if (selectAll.checked) {
            this.selectedRows.clear();
            this.tableData.forEach((_, index) => this.selectedRows.add(index));
            checkboxes.forEach(cb => cb.checked = true);
        } else {
            this.selectedRows.clear();
            checkboxes.forEach(cb => cb.checked = false);
        }

        this.updateControlButtons();
        this.updateRowHighlight();
    }

    // Eliminar seleccionados
    deleteSelected() {
        if (this.selectedRows.size === 0) return;

        if (confirm(`¿Estás seguro de que quieres eliminar ${this.selectedRows.size} elemento(s)?`)) {
            const indices = Array.from(this.selectedRows).sort((a, b) => b - a);
            indices.forEach(index => this.tableData.splice(index, 1));
            this.selectedRows.clear();
            this.renderInterface();
        }
    }

    // Copiar seleccionados
    copySelected() {
        if (this.selectedRows.size === 0) return;

        const indices = Array.from(this.selectedRows).sort();
        const rowsToCopy = indices.map(index => ({ ...this.tableData[index] }));

        // Generar nuevas keys si es necesario
        rowsToCopy.forEach((row, i) => {
            if (row.key !== undefined) {
                row.key = String(this.tableData.length + i);
            }
        });

        const lastIndex = Math.max(...indices);
        rowsToCopy.reverse().forEach(row => {
            this.tableData.splice(lastIndex + 1, 0, row);
        });

        this.selectedRows.clear();
        this.renderInterface();
    }

    // Mover hacia arriba/abajo (similar al CSV)
    moveUp() {
        if (this.selectedRows.size === 0) return;

        const indices = Array.from(this.selectedRows).sort();
        if (indices[0] === 0) return;

        indices.forEach(index => {
            [this.tableData[index - 1], this.tableData[index]] = [this.tableData[index], this.tableData[index - 1]];
        });

        this.selectedRows.clear();
        indices.forEach(index => this.selectedRows.add(index - 1));

        this.renderInterface();
        this.restoreSelection();
    }

    moveDown() {
        if (this.selectedRows.size === 0) return;

        const indices = Array.from(this.selectedRows).sort().reverse();
        if (indices[0] === this.tableData.length - 1) return;

        indices.forEach(index => {
            [this.tableData[index], this.tableData[index + 1]] = [this.tableData[index + 1], this.tableData[index]];
        });

        this.selectedRows.clear();
        indices.reverse().forEach(index => this.selectedRows.add(index + 1));

        this.renderInterface();
        this.restoreSelection();
    }

    // Funciones auxiliares (drag & drop, etc.)
    dragStart(event) {
        event.dataTransfer.setData('text/plain', event.target.closest('tr').dataset.index);
        event.target.closest('tr').classList.add('dragging');
    }

    dragOver(event) {
        event.preventDefault();
        const dropTarget = event.target.closest('tr');
        if (dropTarget) {
            dropTarget.classList.add('drop-target');
        }
    }

    drop(event) {
        event.preventDefault();
        const draggedIndex = parseInt(event.dataTransfer.getData('text/plain'));
        const dropTarget = event.target.closest('tr');

        if (dropTarget) {
            const dropIndex = parseInt(dropTarget.dataset.index);

            if (draggedIndex !== dropIndex) {
                const draggedRow = this.tableData.splice(draggedIndex, 1)[0];
                this.tableData.splice(dropIndex, 0, draggedRow);
                this.renderInterface();
            }
        }

        document.querySelectorAll('.dragging, .drop-target').forEach(el => {
            el.classList.remove('dragging', 'drop-target');
        });
    }

    // Funciones de la vista de texto
    formatJSON() {
        try {
            const textArea = document.getElementById('jsonTextArea');
            const jsonData = JSON.parse(textArea.value);
            textArea.value = JSON.stringify(jsonData, null, 2);
            this.showError('');
        } catch (error) {
            this.showError('Error al formatear JSON: ' + error.message);
        }
    }

    validateJSON() {
        try {
            const textArea = document.getElementById('jsonTextArea');
            JSON.parse(textArea.value);
            this.showError('✅ JSON válido');
        } catch (error) {
            this.showError('❌ JSON inválido: ' + error.message);
        }
    }

    // Funciones auxiliares
    restoreSelection() {
        setTimeout(() => {
            const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
            checkboxes.forEach((cb, index) => {
                cb.checked = this.selectedRows.has(index);
            });
            this.updateRowHighlight();
            this.updateControlButtons();
        }, 50);
    }

    updateRowHighlight() {
        const rows = document.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            if (this.selectedRows.has(index)) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        });
    }

    updateControlButtons() {
        const hasSelection = this.selectedRows.size > 0;
        const deleteBtn = document.getElementById('deleteBtn');
        const copyBtn = document.getElementById('copyBtn');
        const moveUpBtn = document.getElementById('moveUpBtn');
        const moveDownBtn = document.getElementById('moveDownBtn');

        if (deleteBtn) deleteBtn.disabled = !hasSelection;
        if (copyBtn) copyBtn.disabled = !hasSelection;
        if (moveUpBtn) moveUpBtn.disabled = !hasSelection;
        if (moveDownBtn) moveDownBtn.disabled = !hasSelection;
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.className = message ? 'json-error show' : 'json-error';
        }
    }

    // Obtener JSON final
    getJSON() {
        if (this.currentView === 'text') {
            return document.getElementById('jsonTextArea').value;
        } else {
            return JSON.stringify(this.convertToJSON(), null, 2);
        }
    }

    // Inicializar eventos
    initializeEvents() {
        document.addEventListener('dragleave', (event) => {
            if (!event.relatedTarget) {
                document.querySelectorAll('.drop-target').forEach(el => {
                    el.classList.remove('drop-target');
                });
            }
        });

        document.addEventListener('dragend', () => {
            document.querySelectorAll('.dragging, .drop-target').forEach(el => {
                el.classList.remove('dragging', 'drop-target');
            });
        });
    }
}

// Variable global para el editor JSON
let jsonEditor;

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function () {
    console.log('Inicializando editor JSON...');
    jsonEditor = new JSONTableEditor('jsonEditor');

    // Cargar datos iniciales si existen
    const initialData = document.getElementById('initialJsonData');
    console.log('Elemento initialJsonData encontrado:', initialData);

    if (initialData && initialData.value) {
        console.log('Valor de datos iniciales:', initialData.value);
        // Decodificar datos escapados
        let jsonData = initialData.value;
        try {
            // Decodificar caracteres Unicode escapados (\uXXXX)
            jsonData = jsonData.replace(/\\u([0-9a-fA-F]{4})/g, function (match, grp) {
                return String.fromCharCode(parseInt(grp, 16));
            });
            console.log('Datos decodificados:', jsonData);
        } catch (e) {
            console.log('No se pudo decodificar, usando datos originales');
        }
        jsonEditor.loadData(jsonData);
    } else {
        console.log('No se encontraron datos iniciales, creando interfaz vacía');
        // Crear interfaz con datos vacíos
        jsonEditor.data = { "name": "", "links": {} };
        jsonEditor.convertToTableData();
        jsonEditor.renderInterface();
    }
});

// Función para guardar JSON
function saveJSON() {
    try {
        const jsonData = jsonEditor.getJSON();
        // Validar que es JSON válido
        JSON.parse(jsonData);
        document.getElementById('jsonOutput').value = jsonData;
        return true;
    } catch (error) {
        alert('Error al validar JSON: ' + error.message);
        return false;
    }
}