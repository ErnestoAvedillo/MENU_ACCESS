// Editor de tabla CSV interactivo
class CSVTableEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.data = [];
        this.headers = [];
        this.selectedRows = new Set();
        this.currentView = 'table';
        this.initializeEvents();
    }

    // Inicializar datos desde CSV
    loadData(csvText) {
        const lines = csvText.split('\n').filter(line => line.trim());
        if (lines.length === 0) return;

        this.headers = lines[0].split(',').map(h => h.trim());
        this.data = lines.slice(1).map(line => line.split(',').map(cell => cell.trim()));
        this.renderInterface();
    }

    // Renderizar tabla HTML
    renderTable() {
        const tableHTML = `
            <div class="table-controls">
                <button onclick="csvEditor.addRow()">➕ Añadir Fila</button>
                <button onclick="csvEditor.deleteSelected()" id="deleteBtn" disabled>🗑️ Eliminar Seleccionadas</button>
                <button onclick="csvEditor.copySelected()" id="copyBtn" disabled>📋 Copiar Seleccionadas</button>
                <button onclick="csvEditor.moveUp()" id="moveUpBtn" disabled>⬆️ Mover Arriba</button>
                <button onclick="csvEditor.moveDown()" id="moveDownBtn" disabled>⬇️ Mover Abajo</button>
            </div>
            <table class="csv-table" id="csvTable">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="selectAll" onchange="csvEditor.toggleSelectAll()"></th>
                        ${this.headers.map(header => `<th>${header}</th>`).join('')}
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.data.map((row, index) => this.renderRow(row, index)).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('tableContainer').innerHTML = tableHTML;
        this.updateControlButtons();
    }

    // Renderizar interfaz principal con pestañas
    renderInterface() {
        const interfaceHTML = `
            <div class="csv-view-tabs">
                <button class="${this.currentView === 'table' ? 'active' : ''}" onclick="csvEditor.switchView('table')">
                    📊 Vista Tabla
                </button>
                <button class="${this.currentView === 'text' ? 'active' : ''}" onclick="csvEditor.switchView('text')">
                    📝 Vista Texto
                </button>
            </div>
            
            <div id="csvTableView" class="${this.currentView === 'table' ? '' : 'csv-text-view'}">
                <div class="table-controls">
                    <button onclick="csvEditor.addRow()">➕ Añadir Fila</button>
                    <button onclick="csvEditor.deleteSelected()" id="deleteBtn" disabled>🗑️ Eliminar Seleccionadas</button>
                    <button onclick="csvEditor.copySelected()" id="copyBtn" disabled>📋 Copiar Seleccionadas</button>
                    <button onclick="csvEditor.moveUp()" id="moveUpBtn" disabled>⬆️ Mover Arriba</button>
                    <button onclick="csvEditor.moveDown()" id="moveDownBtn" disabled>⬇️ Mover Abajo</button>
                </div>
                <table class="csv-table" id="csvTable">
                    <thead>
                        <tr>
                            <th><input type="checkbox" id="selectAll" onchange="csvEditor.toggleSelectAll()"></th>
                            ${this.headers.map(header => `<th>${header}</th>`).join('')}
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.data.map((row, index) => this.renderRow(row, index)).join('')}
                    </tbody>
                </table>
            </div>
            
            <div id="csvTextView" class="${this.currentView === 'text' ? '' : 'csv-text-view'}">
                <div class="csv-text-controls">
                    <button onclick="csvEditor.formatCSV()">🎨 Formatear CSV</button>
                    <button onclick="csvEditor.validateCSV()">✅ Validar CSV</button>
                    <button onclick="csvEditor.switchView('table')">📊 Ver como Tabla</button>
                </div>
                <textarea id="csvTextArea" class="csv-textarea" placeholder="Edita el CSV aquí...">${this.getCSV()}</textarea>
            </div>
        `;
        
        document.getElementById('tableContainer').innerHTML = interfaceHTML;
        this.updateControlButtons();
    }

    // Cambiar vista
    switchView(view) {
        this.currentView = view;
        
        if (view === 'text') {
            // Sincronizar datos de tabla a texto
            document.getElementById('csvTextArea').value = this.getCSV();
        } else {
            // Sincronizar datos de texto a tabla
            try {
                const textData = document.getElementById('csvTextArea').value;
                this.loadDataFromText(textData);
            } catch (error) {
                console.error('Error al parsear CSV desde texto:', error);
            }
        }
        
        this.renderInterface();
    }

    // Cargar datos desde texto
    loadDataFromText(csvText) {
        const lines = csvText.split('\n').filter(line => line.trim());
        if (lines.length === 0) return;

        this.headers = lines[0].split(',').map(h => h.trim());
        this.data = lines.slice(1).map(line => line.split(',').map(cell => cell.trim()));
    }

    // Formatear CSV
    formatCSV() {
        try {
            const textArea = document.getElementById('csvTextArea');
            const lines = textArea.value.split('\n').filter(line => line.trim());
            
            if (lines.length > 0) {
                const formattedLines = lines.map(line => {
                    return line.split(',').map(cell => cell.trim()).join(', ');
                });
                textArea.value = formattedLines.join('\n');
            }
        } catch (error) {
            alert('Error al formatear CSV: ' + error.message);
        }
    }

    // Validar CSV
    validateCSV() {
        try {
            const textArea = document.getElementById('csvTextArea');
            const lines = textArea.value.split('\n').filter(line => line.trim());
            
            if (lines.length === 0) {
                alert('❌ CSV vacío');
                return;
            }

            const headerCount = lines[0].split(',').length;
            let isValid = true;
            let errorLine = -1;

            for (let i = 1; i < lines.length; i++) {
                const columnCount = lines[i].split(',').length;
                if (columnCount !== headerCount) {
                    isValid = false;
                    errorLine = i + 1;
                    break;
                }
            }

            if (isValid) {
                alert('✅ CSV válido');
            } else {
                alert(`❌ CSV inválido: La línea ${errorLine} tiene un número diferente de columnas`);
            }
        } catch (error) {
            alert('❌ Error al validar CSV: ' + error.message);
        }
    }

    // Renderizar una fila
    renderRow(row, index) {
        return `
            <tr data-index="${index}" draggable="true" ondragstart="csvEditor.dragStart(event)" ondragover="csvEditor.dragOver(event)" ondrop="csvEditor.drop(event)">
                <td><input type="checkbox" onchange="csvEditor.toggleRowSelection(${index})"></td>
                ${row.map((cell, cellIndex) => 
                    `<td data-label="${this.headers[cellIndex]}">
                        <input type="text" value="${cell}" onchange="csvEditor.updateCell(${index}, ${cellIndex}, this.value)">
                    </td>`
                ).join('')}
                <td>
                    <div class="row-controls">
                        <button class="copy-btn" onclick="csvEditor.copyRow(${index})" title="Copiar fila">📋</button>
                        <button class="delete-btn" onclick="csvEditor.deleteRow(${index})" title="Eliminar fila">🗑️</button>
                        <button class="move-btn" title="Arrastrar para mover">⋮⋮</button>
                    </div>
                </td>
            </tr>
        `;
    }

    // Añadir nueva fila
    addRow() {
        const newRow = new Array(this.headers.length).fill('');
        this.data.push(newRow);
        this.renderInterface();
    }

    // Eliminar fila específica
    deleteRow(index) {
        if (confirm('¿Estás seguro de que quieres eliminar esta fila?')) {
            this.data.splice(index, 1);
            this.selectedRows.clear();
            this.renderInterface();
        }
    }

    // Copiar fila
    copyRow(index) {
        const newRow = [...this.data[index]];
        this.data.splice(index + 1, 0, newRow);
        this.renderInterface();
    }

    // Actualizar celda
    updateCell(row, col, value) {
        this.data[row][col] = value;
    }

    // Selección de filas
    toggleRowSelection(index) {
        if (this.selectedRows.has(index)) {
            this.selectedRows.delete(index);
        } else {
            this.selectedRows.add(index);
        }
        this.updateControlButtons();
        this.updateRowHighlight();
    }

    // Seleccionar/deseleccionar todas
    toggleSelectAll() {
        const selectAll = document.getElementById('selectAll');
        const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
        
        if (selectAll.checked) {
            this.selectedRows.clear();
            this.data.forEach((_, index) => this.selectedRows.add(index));
            checkboxes.forEach(cb => cb.checked = true);
        } else {
            this.selectedRows.clear();
            checkboxes.forEach(cb => cb.checked = false);
        }
        
        this.updateControlButtons();
        this.updateRowHighlight();
    }

    // Eliminar filas seleccionadas
    deleteSelected() {
        if (this.selectedRows.size === 0) return;
        
        if (confirm(`¿Estás seguro de que quieres eliminar ${this.selectedRows.size} fila(s)?`)) {
            const indices = Array.from(this.selectedRows).sort((a, b) => b - a);
            indices.forEach(index => this.data.splice(index, 1));
            this.selectedRows.clear();
            this.renderInterface();
        }
    }

    // Copiar filas seleccionadas
    copySelected() {
        if (this.selectedRows.size === 0) return;
        
        const indices = Array.from(this.selectedRows).sort();
        const rowsToCopy = indices.map(index => [...this.data[index]]);
        
        // Insertar las copias después de la última fila seleccionada
        const lastIndex = Math.max(...indices);
        rowsToCopy.reverse().forEach(row => {
            this.data.splice(lastIndex + 1, 0, row);
        });
        
        this.selectedRows.clear();
        this.renderInterface();
    }

    // Mover filas seleccionadas hacia arriba
    moveUp() {
        if (this.selectedRows.size === 0) return;
        
        const indices = Array.from(this.selectedRows).sort();
        if (indices[0] === 0) return; // Ya están en la parte superior
        
        indices.forEach(index => {
            [this.data[index - 1], this.data[index]] = [this.data[index], this.data[index - 1]];
        });
        
        // Actualizar índices seleccionados
        this.selectedRows.clear();
        indices.forEach(index => this.selectedRows.add(index - 1));
        
        this.renderInterface();
        this.restoreSelection();
    }

    // Mover filas seleccionadas hacia abajo
    moveDown() {
        if (this.selectedRows.size === 0) return;
        
        const indices = Array.from(this.selectedRows).sort().reverse();
        if (indices[0] === this.data.length - 1) return; // Ya están en la parte inferior
        
        indices.forEach(index => {
            [this.data[index], this.data[index + 1]] = [this.data[index + 1], this.data[index]];
        });
        
        // Actualizar índices seleccionados
        this.selectedRows.clear();
        indices.reverse().forEach(index => this.selectedRows.add(index + 1));
        
        this.renderInterface();
        this.restoreSelection();
    }

    // Restaurar selección después de mover
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

    // Actualizar resaltado de filas
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

    // Actualizar estado de botones de control
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

    // Funciones de arrastrar y soltar
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
                const draggedRow = this.data.splice(draggedIndex, 1)[0];
                this.data.splice(dropIndex, 0, draggedRow);
                this.renderInterface();
            }
        }
        
        // Limpiar estados de arrastre
        document.querySelectorAll('.dragging, .drop-target').forEach(el => {
            el.classList.remove('dragging', 'drop-target');
        });
    }

    // Obtener datos como CSV
    getCSV() {
        const csvLines = [this.headers.join(',')];
        this.data.forEach(row => {
            csvLines.push(row.join(','));
        });
        return csvLines.join('\n');
    }

    // Inicializar eventos
    initializeEvents() {
        // Limpiar eventos de arrastre cuando se sale del área
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

// Variable global para el editor
let csvEditor;

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    csvEditor = new CSVTableEditor('tableEditor');
    
    // Cargar datos iniciales si existen
    const initialData = document.getElementById('initialData');
    if (initialData && initialData.value) {
        csvEditor.loadData(initialData.value);
    }
});

// Función para guardar (llamada desde el formulario)
function saveTable() {
    if (csvEditor.currentView === 'text') {
        // Si está en vista de texto, usar el contenido del textarea
        const csvData = document.getElementById('csvTextArea').value;
        document.getElementById('csvOutput').value = csvData;
    } else {
        // Si está en vista de tabla, usar getCSV()
        const csvData = csvEditor.getCSV();
        document.getElementById('csvOutput').value = csvData;
    }
    return true; // Permitir envío del formulario
}