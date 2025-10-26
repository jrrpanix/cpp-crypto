// Wrap in IIFE to avoid global namespace pollution
(function() {
    'use strict';

    // Configuration
    const API_BASE_URL = 'http://localhost:5001';

    // State
    let availableSymbols = [];
    let rowCounter = 0;
    let backtestResults = [];

    // Initialize on page load
    async function init() {
        await loadSymbols();
        addParameterRow(); // Add initial row
    }

    // Run initialization when DOM is ready or immediately if already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM is already ready, run init immediately
        init();
    }

// Load available symbols from API
async function loadSymbols() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/symbols`);
        const data = await response.json();
        
        if (data.symbols && data.symbols.length > 0) {
            availableSymbols = data.symbols;
        } else {
            showError('No symbols available. Make sure parquet data files exist in data/aggregate_parquet/');
        }
    } catch (error) {
        showError(`Failed to load symbols: ${error.message}`);
    }
}

// Add a new parameter row to the table
function addParameterRow() {
    const tbody = document.getElementById('paramsTableBody');
    const rowId = `row_${rowCounter++}`;
    
    const row = document.createElement('tr');
    row.id = rowId;
    row.innerHTML = `
        <td>
            <select class="param-symbol" required>
                <option value="">Select...</option>
                ${availableSymbols.map(s => `<option value="${s}">${s}</option>`).join('')}
            </select>
        </td>
        <td><input type="number" step="0.001" value="0.01" class="param-up-thr" style="width: 70px;"></td>
        <td class="direction-cell">
            <button type="button" class="direction-btn selected" data-value="B" onclick="selectDirection(this)">B</button>
            <button type="button" class="direction-btn" data-value="S" onclick="selectDirection(this)">S</button>
            <input type="hidden" class="param-up-dir" value="B">
        </td>
        <td><input type="number" step="0.001" value="-0.02" class="param-dn-thr" style="width: 70px;"></td>
        <td class="direction-cell">
            <button type="button" class="direction-btn" data-value="B" onclick="selectDirection(this)">B</button>
            <button type="button" class="direction-btn selected" data-value="S" onclick="selectDirection(this)">S</button>
            <input type="hidden" class="param-dn-dir" value="S">
        </td>
        <td><input type="number" min="1" value="30" class="param-det-win" style="width: 70px;"></td>
        <td><input type="number" min="1" value="30" class="param-hold-win" style="width: 70px;"></td>
        <td><input type="number" min="1" value="1000" class="param-pos-size" style="width: 80px;"></td>
        <td><input type="number" min="1" value="1" class="param-pos-limit" style="width: 60px;"></td>
        <td>
            <select class="param-n-accounts" style="width: 60px;">
                <option value="1">1</option>
                <option value="2">2</option>
            </select>
        </td>
        <td><input type="date" class="param-start-date" style="width: 130px;"></td>
        <td><input type="number" step="0.0001" value="0.0003" class="param-fee-rate" style="width: 70px;"></td>
        <td>
            <span class="status-cell status-pending" id="status_${rowId}">Ready</span>
        </td>
        <td class="action-cell">
            <button class="btn-sm btn-run" onclick="runBacktest('${rowId}')">▶ Run</button>
            <button class="btn-sm btn-remove" onclick="removeRow('${rowId}')">✕</button>
        </td>
    `;
    
    tbody.appendChild(row);
}

// Select direction button
function selectDirection(btn) {
    const cell = btn.parentElement;
    const buttons = cell.querySelectorAll('.direction-btn');
    const hiddenInput = cell.querySelector('input[type="hidden"]');
    
    buttons.forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    hiddenInput.value = btn.dataset.value;
}

// Remove a parameter row
function removeRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
        // Also remove associated result if exists
        backtestResults = backtestResults.filter(r => r.rowId !== rowId);
        updateResultsTable();
    }
}

// Get parameters from a row
function getRowParameters(rowId) {
    const row = document.getElementById(rowId);
    if (!row) return null;
    
    const params = {
        symbol: row.querySelector('.param-symbol').value,
        up_threshold: parseFloat(row.querySelector('.param-up-thr').value),
        up_direction: row.querySelector('.param-up-dir').value,
        down_threshold: parseFloat(row.querySelector('.param-dn-thr').value),
        down_direction: row.querySelector('.param-dn-dir').value,
        detection_window: parseInt(row.querySelector('.param-det-win').value),
        hold_window: parseInt(row.querySelector('.param-hold-win').value),
        position_size: parseFloat(row.querySelector('.param-pos-size').value),
        position_limit: parseInt(row.querySelector('.param-pos-limit').value),
        num_accounts: parseInt(row.querySelector('.param-n-accounts').value),
        fee_rate: parseFloat(row.querySelector('.param-fee-rate').value),
        include_plot: true  // Enable plot generation for single-symbol backtests
    };
    
    const startDate = row.querySelector('.param-start-date').value;
    if (startDate) {
        params.start_date = startDate;
    }
    
    // Validation
    if (!params.symbol) {
        throw new Error('Please select a symbol');
    }
    
    return params;
}

// Update row status
function updateRowStatus(rowId, status, message) {
    const statusEl = document.getElementById(`status_${rowId}`);
    if (!statusEl) return;
    
    statusEl.className = `status-cell status-${status}`;
    statusEl.textContent = message;
}

// Enable/disable row buttons
function setRowButtonsEnabled(rowId, enabled) {
    const row = document.getElementById(rowId);
    if (!row) return;
    
    const runBtn = row.querySelector('.btn-run');
    if (runBtn) {
        runBtn.disabled = !enabled;
    }
}

// Run backtest for a specific row
async function runBacktest(rowId) {
    try {
        // Get parameters
        const params = getRowParameters(rowId);
        if (!params) return;
        
        // Update status
        updateRowStatus(rowId, 'running', 'Running...');
        setRowButtonsEnabled(rowId, false);
        
        // Call API
        const response = await fetch(`${API_BASE_URL}/api/backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Backtest failed');
        }
        
        // Update status
        updateRowStatus(rowId, 'complete', '✓ Complete');
        setRowButtonsEnabled(rowId, true);
        
        // Store results
        const result = {
            rowId: rowId,
            params: params,
            summary: data.summary,
            plot: data.plot,
            timestamp: new Date()
        };
        
        // Remove old result for this row if exists
        backtestResults = backtestResults.filter(r => r.rowId !== rowId);
        backtestResults.push(result);
        
        // Update results table
        updateResultsTable();
        
        // Show results section
        document.getElementById('resultsSection').classList.add('active');
        
    } catch (error) {
        updateRowStatus(rowId, 'error', 'Error');
        setRowButtonsEnabled(rowId, true);
        showError(`Row error: ${error.message}`);
    }
}

// Update results table
function updateResultsTable() {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    
    if (backtestResults.length === 0) {
        tbody.innerHTML = '<tr><td colspan="13" style="text-align: center; padding: 40px; color: #7f8c8d;">No results yet. Run a backtest to see results here.</td></tr>';
        return;
    }
    
    // Sort by timestamp descending
    const sortedResults = [...backtestResults].sort((a, b) => b.timestamp - a.timestamp);
    
    sortedResults.forEach(result => {
        const { params, summary, plot } = result;
        const row = document.createElement('tr');
        
        // Build parameter summary
        const paramSummary = `
            ↑${params.up_threshold} ${params.up_direction} / 
            ↓${params.down_threshold} ${params.down_direction} | 
            D:${params.detection_window} H:${params.hold_window}
        `;
        
        // Use correct field names from window_sim summary
        const grossProfit = summary.gross_profit || 0;
        const netProfit = summary.net_profit || 0;
        const totalFees = summary.total_fees || 0;
        const netRoi = summary.net_roi || 0;
        const sharpe = summary.net_sharpe_ratio;
        const maxDrawdown = summary.max_drawdown || 0;
        const numTrades = summary.num_trades || 0;
        const winRate = summary.win_rate || 0; // Already in percentage (0-100)
        const avgProfit = summary.avg_net_profit || 0;
        
        row.innerHTML = `
            <td><strong>${params.symbol}</strong></td>
            <td style="font-size: 0.8rem;">${paramSummary}</td>
            <td class="${grossProfit >= 0 ? 'metric-positive' : 'metric-negative'}">
                ${formatCurrency(grossProfit)}
            </td>
            <td class="metric-negative">${formatCurrency(totalFees)}</td>
            <td class="${netProfit >= 0 ? 'metric-positive' : 'metric-negative'}">
                ${formatCurrency(netProfit)}
            </td>
            <td class="${netRoi >= 0 ? 'metric-positive' : 'metric-negative'}">
                ${formatPercentValue(netRoi)}
            </td>
            <td>${sharpe !== undefined && sharpe !== null ? sharpe.toFixed(3) : 'N/A'}</td>
            <td class="metric-negative">${formatPercentValue(maxDrawdown)}</td>
            <td>${numTrades}</td>
            <td>${formatPercentValue(winRate)}</td>
            <td class="${avgProfit >= 0 ? 'metric-positive' : 'metric-negative'}">
                ${formatCurrency(avgProfit)}
            </td>
            <td>
                ${plot ? `<img src="data:image/png;base64,${plot}" class="plot-preview" onclick="showPlotModal('data:image/png;base64,${plot}')" alt="PnL Chart">` : 'N/A'}
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Format currency
function formatCurrency(value) {
    if (value === undefined || value === null) return 'N/A';
    return value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
}

// Format percentage (for decimals like 0.15 -> 15%)
function formatPercent(value) {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
}

// Format percentage value (already in percentage like 15.5 -> 15.5%)
function formatPercentValue(value) {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(2)}%`;
}

// Show plot in modal
function showPlotModal(src) {
    const modal = document.getElementById('plotModal');
    const img = document.getElementById('modalPlotImage');
    img.src = src;
    modal.classList.add('active');
}

// Close plot modal
function closePlotModal() {
    const modal = document.getElementById('plotModal');
    modal.classList.remove('active');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('plotModal');
    if (event.target === modal) {
        closePlotModal();
    }
}

// Show error message
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
    setTimeout(() => {
        document.getElementById('errorSection').style.display = 'none';
    }, 5000);
}

// Expose functions needed by HTML onclick handlers
window.addParameterRow = addParameterRow;
window.closePlotModal = closePlotModal;
window.runBacktest = runBacktest;
window.removeRow = removeRow;
window.selectDirection = selectDirection;
window.showPlotModal = showPlotModal;

})(); // End IIFE
