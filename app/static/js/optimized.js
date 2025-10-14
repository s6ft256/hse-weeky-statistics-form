/**
 * OPTIMIZED AIRTABLE DASHBOARD - ADVANCED JAVASCRIPT ARCHITECTURE
 * Focus: Efficiency, Scalability, Performance
 */

class OptimizedAirtableDashboard {
  constructor() {
    this.state = {
      currentTable: null,
      currentView: 'grid', // grid, list, kanban
      sidebarCollapsed: false,
      panelVisible: false,
      selectedRecords: new Set(),
      filters: new Map(),
      sortConfig: null,
      searchQuery: '',
    };
    
    this.cache = new Map();
    this.controllers = new Map(); // AbortController instances
    this.debounceTimers = new Map();
    this.observers = new Map(); // IntersectionObserver instances
    
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.setupKeyboardShortcuts();
    this.setupIntersectionObservers();
    this.loadUserPreferences();
    await this.loadInitialData();
    this.startPeriodicSync();
  }

  /* ===================================================================
     EVENT MANAGEMENT & PERFORMANCE
     =================================================================== */

  setupEventListeners() {
    // Sidebar toggle
    document.getElementById('sidebar-toggle')?.addEventListener('click', 
      () => this.toggleSidebar());
    
    // Panel close
    document.getElementById('panel-close')?.addEventListener('click', 
      () => this.closePanel());
    
    // Global search with debounce
    const searchInput = document.getElementById('global-search');
    if (searchInput) {
      searchInput.addEventListener('input', 
        this.debounce((e) => this.handleGlobalSearch(e.target.value), 300));
    }

    // View toggle
    document.querySelectorAll('.view-toggle button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.target.dataset.view;
        this.switchView(view);
      });
    });

    // Record selection (bulk operations)
    document.addEventListener('change', (e) => {
      if (e.target.matches('.record-checkbox')) {
        this.toggleRecordSelection(e.target.dataset.recordId);
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));

    // Window resize optimization
    window.addEventListener('resize', 
      this.debounce(() => this.handleResize(), 150));

    // Visibility API for performance
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.pausePeriodicSync();
      } else {
        this.resumePeriodicSync();
      }
    });
  }

  setupKeyboardShortcuts() {
    const shortcuts = {
      'ctrl+k': () => this.focusGlobalSearch(),
      'ctrl+b': () => this.toggleSidebar(),
      'ctrl+p': () => this.togglePanel(),
      'ctrl+r': (e) => { e.preventDefault(); this.refreshCurrentView(); },
      'ctrl+n': (e) => { e.preventDefault(); this.showAddRecordForm(); },
      'ctrl+f': (e) => { e.preventDefault(); this.showAdvancedFilters(); },
      'escape': () => this.closeModals(),
      'ctrl+a': (e) => { e.preventDefault(); this.selectAllRecords(); },
      'delete': () => this.deleteSelectedRecords(),
    };

    document.addEventListener('keydown', (e) => {
      const key = this.getKeyCombo(e);
      if (shortcuts[key]) {
        shortcuts[key](e);
      }
    });
  }

  setupIntersectionObservers() {
    // Lazy loading for record cards
    this.observers.set('records', new IntersectionObserver(
      (entries) => this.handleRecordVisibility(entries),
      { rootMargin: '50px' }
    ));

    // Performance monitoring
    this.observers.set('performance', new PerformanceObserver(
      (list) => this.handlePerformanceEntries(list.getEntries())
    ));
    this.observers.get('performance').observe({entryTypes: ['measure', 'navigation']});
  }

  /* ===================================================================
     STATE MANAGEMENT & CACHING
     =================================================================== */

  async loadInitialData() {
    try {
      this.showGlobalLoading('Initializing dashboard...');
      
      // Load tables with intelligent caching
      const tables = await this.fetchWithCache('/api/tables', 300000); // 5 min cache
      
      if (tables.error) {
        throw new Error(tables.error);
      }

      this.renderSidebar(tables);
      this.updateDashboardStats(tables);
      
      // Load user's last table or default
      const lastTable = this.getUserPreference('lastTable');
      if (lastTable && tables.tables.find(t => t.name === lastTable)) {
        await this.loadTable(lastTable);
      } else if (tables.tables.length > 0) {
        await this.loadTable(tables.tables[0].name);
      }

    } catch (error) {
      this.showError('Failed to initialize dashboard', error);
    } finally {
      this.hideGlobalLoading();
    }
  }

  async fetchWithCache(url, ttl = 60000) {
    const cacheKey = url;
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.data;
    }

    // Cancel previous request if still pending
    if (this.controllers.has(cacheKey)) {
      this.controllers.get(cacheKey).abort();
    }

    const controller = new AbortController();
    this.controllers.set(cacheKey, controller);

    try {
      const response = await fetch(url, { 
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });
      
      return data;

    } finally {
      this.controllers.delete(cacheKey);
    }
  }

  invalidateCache(pattern) {
    if (typeof pattern === 'string') {
      this.cache.delete(pattern);
    } else if (pattern instanceof RegExp) {
      for (const key of this.cache.keys()) {
        if (pattern.test(key)) {
          this.cache.delete(key);
        }
      }
    }
  }

  /* ===================================================================
     ENHANCED UI RENDERING
     =================================================================== */

  renderSidebar(data) {
    const sidebar = document.getElementById('sidebar-nav');
    if (!sidebar) return;

    // Group tables by category for better organization
    const groupedTables = this.groupTablesByCategory(data.tables);
    
    let html = '';

    // Quick Actions Section
    html += this.renderQuickActions();

    // Tables by Category
    Object.entries(groupedTables).forEach(([category, tables]) => {
      html += this.renderNavGroup(category, tables);
    });

    // Recent Tables Section
    const recentTables = this.getRecentTables(data.tables);
    if (recentTables.length > 0) {
      html += this.renderNavGroup('Recent', recentTables, 'recent');
    }

    sidebar.innerHTML = html;
    this.attachSidebarEvents();
  }

  renderNavGroup(title, items, type = 'tables') {
    const groupId = `group-${title.toLowerCase().replace(/\s+/g, '-')}`;
    const isCollapsed = this.getUserPreference(`sidebar.${groupId}.collapsed`, false);
    
    return `
      <div class="nav-group ${isCollapsed ? 'collapsed' : ''}" data-group="${groupId}">
        <div class="nav-group-header" onclick="dashboard.toggleNavGroup('${groupId}')">
          <span>${title}</span>
          <span class="nav-group-toggle">▼</span>
        </div>
        <div class="nav-group-content">
          ${items.map(item => this.renderNavItem(item, type)).join('')}
        </div>
      </div>
    `;
  }

  renderNavItem(table, type = 'tables') {
    const editableFields = this.getEditableFieldsCount(table);
    const isActive = this.state.currentTable === table.name;
    const recordCount = this.getTableRecordCount(table.name);

    return `
      <div class="nav-item">
        <button 
          class="nav-link ${isActive ? 'active' : ''}" 
          onclick="dashboard.loadTable('${table.name}')"
          data-table="${table.name}"
          title="${table.description || table.name}"
        >
          <span class="nav-icon">${this.getTableIcon(table)}</span>
          <span class="nav-text">${table.name}</span>
          <div class="nav-meta">
            <span class="nav-badge ${editableFields > 0 ? 'primary' : ''}">${editableFields}</span>
            ${recordCount !== null ? `<span class="nav-badge">${recordCount}</span>` : ''}
          </div>
        </button>
      </div>
    `;
  }

  renderQuickActions() {
    return `
      <div class="nav-group">
        <div class="nav-group-header">
          <span>Quick Actions</span>
        </div>
        <div class="nav-group-content">
          <div class="nav-item">
            <button class="nav-link" onclick="dashboard.showAddRecordForm()">
              <span class="nav-icon">➕</span>
              <span class="nav-text">Add Record</span>
            </button>
          </div>
          <div class="nav-item">
            <button class="nav-link" onclick="dashboard.showAdvancedFilters()">
              <span class="nav-icon">🔍</span>
              <span class="nav-text">Advanced Search</span>
            </button>
          </div>
          <div class="nav-item">
            <button class="nav-link" onclick="dashboard.showBulkOperations()">
              <span class="nav-icon">⚡</span>
              <span class="nav-text">Bulk Operations</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  async loadTable(tableName) {
    if (this.state.currentTable === tableName) return;
    
    try {
      performance.mark('table-load-start');
      
      this.state.currentTable = tableName;
      this.updateActiveStates(tableName);
      this.saveUserPreference('lastTable', tableName);
      
      this.showMainLoading(`Loading ${tableName}...`);
      
      // Parallel loading of table data and schema
      const [tableData, tableSchema] = await Promise.all([
        this.fetchWithCache(`/api/tables/${encodeURIComponent(tableName)}/records?max_records=100`, 30000),
        this.fetchWithCache(`/api/tables/${encodeURIComponent(tableName)}/schema`, 300000)
      ]);

      if (tableData.error) throw new Error(tableData.error);
      
      this.renderTableView(tableName, tableData, tableSchema);
      this.updateBreadcrumb(tableName);
      
      performance.mark('table-load-end');
      performance.measure('table-load', 'table-load-start', 'table-load-end');
      
    } catch (error) {
      this.showError(`Failed to load table ${tableName}`, error);
    } finally {
      this.hideMainLoading();
    }
  }

  renderTableView(tableName, data, schema) {
    const main = document.getElementById('main-content');
    if (!main) return;

    const table = schema?.schema || this.getTableFromCache(tableName);
    
    let html = `
      <!-- Table Overview -->
      ${this.renderTableOverview(tableName, table, data)}
      
      <!-- Advanced Filters & Controls -->
      ${this.renderTableControls(tableName, table)}
      
      <!-- Records Display -->
      ${this.renderRecordsContainer(tableName, data, table)}
    `;

    main.innerHTML = html;
    this.attachTableEvents();
    this.initializeVirtualScrolling();
  }

  renderTableOverview(tableName, table, data) {
    const editableFields = table?.fields?.filter(f => 
      !['formula', 'rollup', 'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'].includes(f.type)
    ) || [];

    return `
      <div class="table-overview fade-in">
        <div class="table-header">
          <div class="table-info">
            <div class="table-icon">${this.getTableIcon(table)}</div>
            <div class="table-details">
              <h1>${tableName}</h1>
              <p class="table-description">${table?.description || 'No description available'}</p>
            </div>
          </div>
          <div class="table-actions">
            <button class="btn btn-outline btn-sm" onclick="dashboard.exportTable('${tableName}')">
              📁 Export
            </button>
            <button class="btn btn-outline btn-sm" onclick="dashboard.showTableSettings('${tableName}')">
              ⚙️ Settings
            </button>
            <button class="btn btn-primary" onclick="dashboard.showAddRecordForm('${tableName}')">
              ➕ Add Record
            </button>
          </div>
        </div>
        
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">${data.count || 0}</div>
            <div class="stat-label">Records</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${table?.fields?.length || 0}</div>
            <div class="stat-label">Total Fields</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${editableFields.length}</div>
            <div class="stat-label">Editable Fields</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${table?.views?.length || 0}</div>
            <div class="stat-label">Views</div>
          </div>
        </div>
      </div>
    `;
  }

  renderTableControls(tableName, table) {
    return `
      <div class="table-controls fade-in">
        <div class="controls-left">
          <div class="view-toggle">
            <button class="active" data-view="grid" title="Grid View">⊞</button>
            <button data-view="list" title="List View">☰</button>
            <button data-view="kanban" title="Kanban View">📋</button>
          </div>
          
          <div class="bulk-actions" style="display: none;">
            <span class="selected-count">0 selected</span>
            <button class="btn btn-sm btn-outline" onclick="dashboard.bulkEdit()">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="dashboard.bulkDelete()">Delete</button>
          </div>
        </div>
        
        <div class="controls-right">
          <button class="btn btn-outline btn-sm" onclick="dashboard.showAdvancedFilters()">
            🔍 Filter
          </button>
          <button class="btn btn-outline btn-sm" onclick="dashboard.showSortOptions()">
            ↕️ Sort
          </button>
          <button class="btn btn-outline btn-sm" onclick="dashboard.refreshTable()">
            🔄 Refresh
          </button>
        </div>
      </div>
    `;
  }

  renderRecordsContainer(tableName, data, table) {
    const viewClass = `records-${this.state.currentView}`;
    
    let html = `
      <div class="records-container ${viewClass} fade-in">
        <div class="records-header">
          <h2 class="records-title">Records (${data.count || 0})</h2>
          <div class="records-controls">
            <select class="page-size" onchange="dashboard.changePageSize(this.value)">
              <option value="25">25 per page</option>
              <option value="50" selected>50 per page</option>
              <option value="100">100 per page</option>
            </select>
          </div>
        </div>
        
        <div class="records-content" id="records-content">
    `;

    if (!data.records || data.records.length === 0) {
      html += this.renderEmptyState(tableName);
    } else {
      html += `<div class="records-grid" id="records-grid">`;
      data.records.forEach(record => {
        html += this.renderRecordCard(tableName, record, table);
      });
      html += `</div>`;
    }

    html += `
        </div>
      </div>
    `;

    return html;
  }

  renderRecordCard(tableName, record, table) {
    const fields = table?.fields || [];
    const primaryField = fields[0]; // First field is usually primary
    const primaryValue = record.fields[primaryField?.name] || 'Untitled Record';

    return `
      <div class="record-card slide-up" data-record-id="${record.id}">
        <div class="record-card-header">
          <input type="checkbox" class="record-checkbox" data-record-id="${record.id}">
          <div class="record-id">${record.id}</div>
          <div class="record-actions">
            <button class="btn btn-sm btn-outline" 
                    onclick="dashboard.showRecordDetails('${tableName}', '${record.id}')"
                    title="View Details">👁️</button>
            <button class="btn btn-sm btn-outline" 
                    onclick="dashboard.editRecord('${tableName}', '${record.id}')"
                    title="Edit">✏️</button>
            <button class="btn btn-sm btn-danger" 
                    onclick="dashboard.deleteRecord('${tableName}', '${record.id}')"
                    title="Delete">🗑️</button>
          </div>
        </div>
        
        <div class="record-fields">
          <div class="primary-field">
            <div class="field-value primary">${this.formatFieldValue(primaryValue)}</div>
          </div>
          
          ${Object.entries(record.fields).slice(1, 4).map(([fieldName, fieldValue]) => `
            <div class="field-row">
              <div class="field-label">${fieldName}</div>
              <div class="field-value">${this.formatFieldValue(fieldValue)}</div>
            </div>
          `).join('')}
          
          ${Object.keys(record.fields).length > 4 ? `
            <div class="field-more">
              <button class="btn btn-sm btn-outline" 
                      onclick="dashboard.showRecordDetails('${tableName}', '${record.id}')">
                +${Object.keys(record.fields).length - 4} more fields
              </button>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  renderEmptyState(tableName) {
    return `
      <div class="empty-state">
        <div class="empty-icon">📝</div>
        <h3>No records found</h3>
        <p>Get started by adding your first record to ${tableName}</p>
        <button class="btn btn-primary" onclick="dashboard.showAddRecordForm('${tableName}')">
          ➕ Add First Record
        </button>
      </div>
    `;
  }

  /* ===================================================================
     UTILITY METHODS & HELPERS
     =================================================================== */

  debounce(func, wait) {
    return (...args) => {
      const key = func.toString();
      clearTimeout(this.debounceTimers.get(key));
      this.debounceTimers.set(key, setTimeout(() => func.apply(this, args), wait));
    };
  }

  getKeyCombo(event) {
    const keys = [];
    if (event.ctrlKey) keys.push('ctrl');
    if (event.shiftKey) keys.push('shift');
    if (event.altKey) keys.push('alt');
    keys.push(event.key.toLowerCase());
    return keys.join('+');
  }

  formatFieldValue(value) {
    if (value === null || value === undefined || value === '') {
      return '<span class="field-value empty">—</span>';
    }
    
    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        return value.join(', ');
      }
      return JSON.stringify(value, null, 2);
    }
    
    const str = String(value);
    if (str.length > 50) {
      return str.substring(0, 50) + '...';
    }
    
    return str;
  }

  groupTablesByCategory(tables) {
    // Smart categorization based on table names and metadata
    const categories = {
      'Core Data': [],
      'Configuration': [],
      'Logs & History': [],
      'Other': []
    };

    tables.forEach(table => {
      const name = table.name.toLowerCase();
      
      if (name.includes('config') || name.includes('setting') || name.includes('preference')) {
        categories['Configuration'].push(table);
      } else if (name.includes('log') || name.includes('history') || name.includes('audit')) {
        categories['Logs & History'].push(table);
      } else if (table.fields.length > 5) {
        categories['Core Data'].push(table);
      } else {
        categories['Other'].push(table);
      }
    });

    // Remove empty categories
    Object.keys(categories).forEach(key => {
      if (categories[key].length === 0) {
        delete categories[key];
      }
    });

    return categories;
  }

  getTableIcon(table) {
    if (!table || !table.name) return '📋';
    
    const name = table.name.toLowerCase();
    const iconMap = {
      'user': '👤', 'customer': '👤', 'people': '👥',
      'order': '🛒', 'purchase': '🛒', 'sale': '💰',
      'product': '📦', 'inventory': '📦', 'item': '📦',
      'project': '📊', 'task': '✅', 'todo': '📋',
      'config': '⚙️', 'setting': '⚙️', 'preference': '🔧',
      'log': '📝', 'history': '📚', 'audit': '🔍'
    };

    for (const [keyword, icon] of Object.entries(iconMap)) {
      if (name.includes(keyword)) return icon;
    }
    
    return '📋';
  }

  /* ===================================================================
     USER PREFERENCES & PERSISTENCE
     =================================================================== */

  getUserPreference(key, defaultValue = null) {
    try {
      const prefs = JSON.parse(localStorage.getItem('airtable-dashboard-prefs') || '{}');
      return prefs[key] !== undefined ? prefs[key] : defaultValue;
    } catch {
      return defaultValue;
    }
  }

  saveUserPreference(key, value) {
    try {
      const prefs = JSON.parse(localStorage.getItem('airtable-dashboard-prefs') || '{}');
      prefs[key] = value;
      localStorage.setItem('airtable-dashboard-prefs', JSON.stringify(prefs));
    } catch (error) {
      console.warn('Failed to save user preference:', error);
    }
  }

  loadUserPreferences() {
    const prefs = this.getUserPreference('ui', {});
    
    if (prefs.sidebarCollapsed) {
      this.state.sidebarCollapsed = true;
      document.body.classList.add('sidebar-collapsed');
    }
    
    if (prefs.preferredView) {
      this.state.currentView = prefs.preferredView;
    }
  }

  /* ===================================================================
     PERFORMANCE & MONITORING
     =================================================================== */

  startPeriodicSync() {
    this.syncInterval = setInterval(() => {
      if (!document.hidden && this.state.currentTable) {
        this.softRefreshTable();
      }
    }, 30000); // 30 seconds
  }

  pausePeriodicSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
  }

  resumePeriodicSync() {
    this.pausePeriodicSync();
    this.startPeriodicSync();
  }

  async softRefreshTable() {
    // Refresh without showing loading spinner
    if (this.state.currentTable) {
      try {
        this.invalidateCache(`/api/tables/${encodeURIComponent(this.state.currentTable)}/records`);
        const data = await this.fetchWithCache(`/api/tables/${encodeURIComponent(this.state.currentTable)}/records?max_records=100`);
        this.updateRecordsQuietly(data);
      } catch (error) {
        console.warn('Soft refresh failed:', error);
      }
    }
  }

  handlePerformanceEntries(entries) {
    entries.forEach(entry => {
      if (entry.name === 'table-load' && entry.duration > 1000) {
        console.warn(`Slow table load: ${entry.duration.toFixed(2)}ms`);
      }
    });
  }

  /* ===================================================================
     PUBLIC API METHODS
     =================================================================== */

  toggleSidebar() {
    this.state.sidebarCollapsed = !this.state.sidebarCollapsed;
    document.body.classList.toggle('sidebar-collapsed', this.state.sidebarCollapsed);
    this.saveUserPreference('ui.sidebarCollapsed', this.state.sidebarCollapsed);
  }

  togglePanel() {
    this.state.panelVisible = !this.state.panelVisible;
    document.body.classList.toggle('panel-visible', this.state.panelVisible);
  }

  closePanel() {
    this.state.panelVisible = false;
    document.body.classList.remove('panel-visible');
  }

  switchView(view) {
    this.state.currentView = view;
    this.saveUserPreference('ui.preferredView', view);
    
    // Update UI
    document.querySelectorAll('.view-toggle button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Re-render records with new view
    if (this.state.currentTable) {
      this.refreshCurrentView();
    }
  }

  async refreshCurrentView() {
    if (this.state.currentTable) {
      this.invalidateCache(`/api/tables/${encodeURIComponent(this.state.currentTable)}/records`);
      await this.loadTable(this.state.currentTable);
    }
  }

  showGlobalLoading(message = 'Loading...') {
    document.body.classList.add('loading');
    // Implementation for global loading overlay
  }

  hideGlobalLoading() {
    document.body.classList.remove('loading');
  }

  showMainLoading(message = 'Loading...') {
    const main = document.getElementById('main-content');
    if (main) {
      main.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          ${message}
        </div>
      `;
    }
  }

  hideMainLoading() {
    // Loading will be replaced by content
  }

  showError(message, error = null) {
    console.error('Dashboard Error:', { message, error });
    // Implementation for error display
  }

  // Initialize after DOM ready
  static async initialize() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        window.dashboard = new OptimizedAirtableDashboard();
      });
    } else {
      window.dashboard = new OptimizedAirtableDashboard();
    }
  }
}

// Auto-initialize
OptimizedAirtableDashboard.initialize();