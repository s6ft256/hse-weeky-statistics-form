/**
 * Airtable Dashboard - JavaScript Application
 * Modular, component-based architecture for scalability
 */

class AirtableDashboard {
  constructor() {
    this.currentTable = null;
    this.allTables = [];
    this.isLoading = false;
    this.cache = new Map();
    
    this.init();
  }

  /**
   * Initialize the application
   */
  async init() {
    this.bindEvents();
    await this.loadInitialData();
    this.setupResponsive();
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', () => this.toggleSidebar());
    }

    // Search functionality
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));

    // Auto-refresh
    setInterval(() => this.refreshCurrentView(), 30000); // Refresh every 30 seconds
  }

  /**
   * Load initial application data
   */
  async loadInitialData() {
    try {
      this.showLoading('Loading tables...');
      await this.loadTables();
      this.hideLoading();
    } catch (error) {
      this.showError('Failed to load initial data', error);
    }
  }

  /**
   * Load tables from API
   */
  async loadTables() {
    try {
      const response = await fetch('/api/tables');
      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      this.allTables = data.tables;
      this.renderSidebar(data);
      this.renderTabs(data);
      this.cache.set('tables', data);

    } catch (error) {
      throw new Error(`Failed to load tables: ${error.message}`);
    }
  }

  /**
   * Render sidebar navigation
   */
  renderSidebar(data) {
    const sidebar = document.getElementById('sidebar-menu');
    const tableCount = document.getElementById('table-count');
    
    if (tableCount) {
      tableCount.textContent = `${data.table_count} tables`;
    }

    if (!sidebar) return;

    // Group tables by category (if you have categories in your data)
    const groupedTables = this.groupTablesByCategory(data.tables);
    
    let html = '';
    
    // Add search
    html += `
      <div class="nav-section">
        <input 
          type="text" 
          id="table-search" 
          placeholder="Search tables..." 
          class="form-input"
          style="margin: 0 var(--space-6) var(--space-4);"
        >
      </div>
    `;

    // Render grouped tables
    for (const [category, tables] of Object.entries(groupedTables)) {
      html += `<div class="nav-section">`;
      if (category !== 'default') {
        html += `<div class="nav-section-title">${category}</div>`;
      }
      
      tables.forEach(table => {
        const editableFields = this.getEditableFieldsCount(table);
        html += `
          <div class="nav-item">
            <button 
              class="nav-link" 
              onclick="dashboard.loadTable('${table.name}', '${table.id}')"
              data-table="${table.name}"
            >
              <span class="nav-icon">📋</span>
              <span>${table.name}</span>
              <span class="nav-badge">${editableFields}/${table.fields.length}</span>
            </button>
          </div>
        `;
      });
      
      html += `</div>`;
    }

    sidebar.innerHTML = html;

    // Re-bind search after rendering
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
    }
  }

  /**
   * Render tab navigation
   */
  renderTabs(data) {
    const tabsContainer = document.getElementById('tabs-container');
    if (!tabsContainer) return;

    let html = '';
    data.tables.forEach(table => {
      html += `
        <button 
          class="tab" 
          onclick="dashboard.loadTable('${table.name}', '${table.id}')"
          data-tab="${table.name}"
        >
          ${table.name}
        </button>
      `;
    });

    tabsContainer.innerHTML = html;
  }

  /**
   * Load specific table data
   */
  async loadTable(tableName, tableId) {
    if (this.isLoading) return;
    
    try {
      this.isLoading = true;
      this.currentTable = tableName;
      
      // Update UI state
      this.updateActiveStates(tableName);
      this.showLoading(`Loading ${tableName}...`);

      // Check cache first
      const cacheKey = `table_${tableName}`;
      let tableData = this.cache.get(cacheKey);
      
      if (!tableData || this.isCacheStale(cacheKey)) {
        const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records?max_records=50`);
        tableData = await response.json();
        
        if (tableData.error) {
          throw new Error(tableData.error);
        }
        
        this.cache.set(cacheKey, { data: tableData, timestamp: Date.now() });
      } else {
        tableData = tableData.data;
      }

      this.renderTableView(tableName, tableData);
      this.hideLoading();

    } catch (error) {
      this.showError(`Failed to load table ${tableName}`, error);
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Render table view with records
   */
  renderTableView(tableName, data) {
    const container = document.getElementById('main-content');
    if (!container) return;

    const table = this.allTables.find(t => t.name === tableName);
    const editableFields = table.fields.filter(f => 
      !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
    );

    let html = `
      <!-- Table Header -->
      <div class="card mb-6">
        <div class="card-header">
          <div class="flex justify-between items-center">
            <div>
              <h2 class="card-title">📋 ${tableName}</h2>
              ${table.description ? `<p class="card-subtitle">${table.description}</p>` : ''}
            </div>
            <div class="flex gap-4">
              <button class="btn btn-primary" onclick="dashboard.showAddRecordForm('${tableName}')">
                <span>➕</span> Add Record
              </button>
              <button class="btn btn-outline" onclick="dashboard.refreshTable('${tableName}')">
                <span>🔄</span> Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Statistics -->
      <div class="stats-grid mb-6">
        <div class="stat-card">
          <div class="stat-number">${data.count}</div>
          <div class="stat-label">Records</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${table.fields.length}</div>
          <div class="stat-label">Total Fields</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${editableFields.length}</div>
          <div class="stat-label">Editable Fields</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${table.views.length}</div>
          <div class="stat-label">Views</div>
        </div>
      </div>

      <!-- Records -->
      <div class="records-grid">
    `;

    if (data.records.length === 0) {
      html += `
        <div class="card">
          <div class="card-content text-center">
            <p style="color: var(--gray-500); font-size: var(--font-size-lg); margin-bottom: var(--space-4);">
              📝 No records found
            </p>
            <p style="color: var(--gray-400); margin-bottom: var(--space-6);">
              Get started by adding your first record to this table.
            </p>
            <button class="btn btn-primary" onclick="dashboard.showAddRecordForm('${tableName}')">
              ➕ Add First Record
            </button>
          </div>
        </div>
      `;
    } else {
      data.records.forEach(record => {
        html += this.renderRecordCard(tableName, record);
      });
    }

    html += '</div>';
    container.innerHTML = html;
  }

  /**
   * Render individual record card
   */
  renderRecordCard(tableName, record) {
    return `
      <div class="record-card">
        <div class="record-header">
          <div class="record-id">${record.id}</div>
          <div class="flex gap-4">
            <button 
              class="btn btn-secondary" 
              onclick="dashboard.showEditRecordForm('${tableName}', '${record.id}', ${JSON.stringify(record.fields).replace(/'/g, "&#39;")})"
            >
              ✏️ Edit
            </button>
            <button 
              class="btn btn-danger" 
              onclick="dashboard.deleteRecord('${tableName}', '${record.id}')"
            >
              🗑️ Delete
            </button>
          </div>
        </div>
        <div class="record-fields">
          ${Object.entries(record.fields).map(([fieldName, fieldValue]) => `
            <div class="field-row">
              <div class="field-name">${fieldName}</div>
              <div class="field-value">${this.formatFieldValue(fieldValue)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Show add record form
   */
  showAddRecordForm(tableName) {
    const table = this.allTables.find(t => t.name === tableName);
    const editableFields = table.fields.filter(f => 
      !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
    );

    const container = document.getElementById('main-content');
    
    let html = `
      <div class="card mb-6">
        <div class="card-header">
          <div class="flex justify-between items-center">
            <h2 class="card-title">➕ Add New Record to ${tableName}</h2>
            <button class="btn btn-outline" onclick="dashboard.loadTable('${tableName}')">
              ← Back to Records
            </button>
          </div>
        </div>
      </div>

      <div class="card">
        <form id="add-record-form" onsubmit="dashboard.addRecord(event, '${tableName}')">
          <div class="card-content">
    `;

    editableFields.forEach(field => {
      html += this.renderFormField(field);
    });

    html += `
          </div>
          <div class="card-actions">
            <button type="submit" class="btn btn-primary">💾 Save Record</button>
            <button type="button" class="btn btn-outline" onclick="dashboard.loadTable('${tableName}')">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    container.innerHTML = html;
  }

  /**
   * Show edit record form
   */
  showEditRecordForm(tableName, recordId, currentFields) {
    const table = this.allTables.find(t => t.name === tableName);
    const editableFields = table.fields.filter(f => 
      !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
    );

    const container = document.getElementById('main-content');
    
    let html = `
      <div class="card mb-6">
        <div class="card-header">
          <div class="flex justify-between items-center">
            <div>
              <h2 class="card-title">✏️ Edit Record in ${tableName}</h2>
              <p class="card-subtitle">Record ID: ${recordId}</p>
            </div>
            <button class="btn btn-outline" onclick="dashboard.loadTable('${tableName}')">
              ← Back to Records
            </button>
          </div>
        </div>
      </div>

      <div class="card">
        <form id="edit-record-form" onsubmit="dashboard.updateRecord(event, '${tableName}', '${recordId}')">
          <div class="card-content">
    `;

    editableFields.forEach(field => {
      const currentValue = currentFields[field.name] || '';
      html += this.renderFormField(field, currentValue);
    });

    html += `
          </div>
          <div class="card-actions">
            <button type="submit" class="btn btn-primary">💾 Update Record</button>
            <button type="button" class="btn btn-outline" onclick="dashboard.loadTable('${tableName}')">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    container.innerHTML = html;
  }

  /**
   * Render form field based on field type
   */
  renderFormField(field, value = '') {
    const fieldId = `field_${field.name.replace(/\s+/g, '_')}`;
    
    let inputHtml = '';
    
    switch (field.type) {
      case 'multilineText':
        inputHtml = `<textarea id="${fieldId}" name="${field.name}" class="form-textarea">${value}</textarea>`;
        break;
      case 'checkbox':
        inputHtml = `<input type="checkbox" id="${fieldId}" name="${field.name}" value="true" ${value ? 'checked' : ''} class="form-input">`;
        break;
      case 'number':
      case 'currency':
      case 'percent':
      case 'rating':
        inputHtml = `<input type="number" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      case 'date':
        inputHtml = `<input type="date" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      case 'dateTime':
        inputHtml = `<input type="datetime-local" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      case 'email':
        inputHtml = `<input type="email" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      case 'url':
        inputHtml = `<input type="url" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      case 'phoneNumber':
        inputHtml = `<input type="tel" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
        break;
      default:
        inputHtml = `<input type="text" id="${fieldId}" name="${field.name}" value="${value}" class="form-input">`;
    }

    return `
      <div class="form-group">
        <label for="${fieldId}" class="form-label">
          ${field.name} 
          <span style="color: var(--gray-500); font-weight: normal;">(${field.type})</span>
        </label>
        ${inputHtml}
        <div class="form-hint">Field type: ${field.type}</div>
      </div>
    `;
  }

  /**
   * Add new record
   */
  async addRecord(event, tableName) {
    event.preventDefault();
    
    try {
      this.showLoading('Saving record...');
      
      const formData = new FormData(event.target);
      const fields = {};
      
      for (const [key, value] of formData.entries()) {
        if (value) {
          fields[key] = value;
        }
      }

      const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      this.showSuccess('✅ Record created successfully!');
      this.invalidateTableCache(tableName);
      await this.loadTable(tableName);

    } catch (error) {
      this.showError('Failed to create record', error);
    } finally {
      this.hideLoading();
    }
  }

  /**
   * Update existing record
   */
  async updateRecord(event, tableName, recordId) {
    event.preventDefault();
    
    try {
      this.showLoading('Updating record...');
      
      const formData = new FormData(event.target);
      const fields = {};
      
      for (const [key, value] of formData.entries()) {
        fields[key] = value;
      }

      const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records/${recordId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields })
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      this.showSuccess('✅ Record updated successfully!');
      this.invalidateTableCache(tableName);
      await this.loadTable(tableName);

    } catch (error) {
      this.showError('Failed to update record', error);
    } finally {
      this.hideLoading();
    }
  }

  /**
   * Delete record
   */
  async deleteRecord(tableName, recordId) {
    if (!confirm('Are you sure you want to delete this record? This cannot be undone.')) {
      return;
    }

    try {
      this.showLoading('Deleting record...');

      const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}/records/${recordId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      this.showSuccess('✅ Record deleted successfully!');
      this.invalidateTableCache(tableName);
      await this.loadTable(tableName);

    } catch (error) {
      this.showError('Failed to delete record', error);
    } finally {
      this.hideLoading();
    }
  }

  /**
   * Utility Methods
   */

  updateActiveStates(tableName) {
    // Update sidebar
    document.querySelectorAll('.nav-link').forEach(btn => {
      btn.classList.remove('active');
    });
    const sidebarBtn = document.querySelector(`.nav-link[data-table="${tableName}"]`);
    if (sidebarBtn) sidebarBtn.classList.add('active');
    
    // Update tabs
    document.querySelectorAll('.tab').forEach(tab => {
      tab.classList.remove('active');
    });
    const activeTab = document.querySelector(`.tab[data-tab="${tableName}"]`);
    if (activeTab) {
      activeTab.classList.add('active');
      activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }

  groupTablesByCategory(tables) {
    // For now, return default grouping
    // You can enhance this to read categories from table metadata
    return { default: tables };
  }

  getEditableFieldsCount(table) {
    return table.fields.filter(f => 
      !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
    ).length;
  }

  formatFieldValue(value) {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    if (typeof value === 'string' && value.length > 100) {
      return value.substring(0, 100) + '...';
    }
    return String(value);
  }

  handleSearch(query) {
    const items = document.querySelectorAll('.nav-link');
    items.forEach(item => {
      const text = item.textContent.toLowerCase();
      const matches = text.includes(query.toLowerCase());
      item.style.display = matches ? 'flex' : 'none';
    });
  }

  handleKeyboard(event) {
    // Keyboard shortcuts
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case 'r':
          event.preventDefault();
          if (this.currentTable) {
            this.refreshTable(this.currentTable);
          }
          break;
        case 'n':
          event.preventDefault();
          if (this.currentTable) {
            this.showAddRecordForm(this.currentTable);
          }
          break;
      }
    }
  }

  async refreshTable(tableName) {
    this.invalidateTableCache(tableName);
    await this.loadTable(tableName);
  }

  async refreshCurrentView() {
    if (this.currentTable && !this.isLoading) {
      this.invalidateTableCache(this.currentTable);
      await this.loadTable(this.currentTable);
    }
  }

  invalidateTableCache(tableName) {
    this.cache.delete(`table_${tableName}`);
  }

  isCacheStale(cacheKey) {
    const cached = this.cache.get(cacheKey);
    if (!cached) return true;
    return Date.now() - cached.timestamp > 60000; // 1 minute
  }

  toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar?.classList.toggle('open');
  }

  setupResponsive() {
    // Handle responsive behavior
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    
    const handleResize = (e) => {
      if (e.matches) {
        // Mobile view
        document.body.classList.add('mobile');
      } else {
        // Desktop view
        document.body.classList.remove('mobile');
        const sidebar = document.querySelector('.sidebar');
        sidebar?.classList.remove('open');
      }
    };

    mediaQuery.addListener(handleResize);
    handleResize(mediaQuery);
  }

  showLoading(message = 'Loading...') {
    const container = document.getElementById('main-content');
    if (container) {
      container.innerHTML = `
        <div class="loading">
          <div class="loading-spinner"></div>
          ${message}
        </div>
      `;
    }
  }

  hideLoading() {
    // Loading will be replaced by content
  }

  showSuccess(message) {
    this.showMessage(message, 'success');
  }

  showError(message, error = null) {
    const fullMessage = error ? `${message}: ${error.message}` : message;
    this.showMessage(fullMessage, 'error');
    console.error('Dashboard Error:', error);
  }

  showMessage(message, type = 'info') {
    const container = document.getElementById('main-content');
    if (container) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message message-${type}`;
      messageDiv.textContent = message;
      
      container.insertBefore(messageDiv, container.firstChild);
      
      setTimeout(() => {
        messageDiv.remove();
      }, 5000);
    }
  }
}

// Initialize the dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
  dashboard = new AirtableDashboard();
});

// Make dashboard available globally for onclick handlers
window.dashboard = dashboard;