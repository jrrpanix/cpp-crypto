// Configuration
const API_BASE_URL = 'http://localhost:5001';

// State
let availableSymbols = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadSymbols();
    setupEventListeners();
});

// Load available symbols from API
async function loadSymbols() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/symbols`);
        const data = await response.json();
        
        if (data.symbols && data.symbols.length > 0) {
            availableSymbols = data.symbols;
            populateSymbolDropdown();
        } else {
            showError('No symbols available. Make sure parquet data files exist in data/aggregate_parquet/');
        }
    } catch (error) {
        showError(`Failed to load symbols: ${error.message}`);
    }
}

// Populate symbol dropdown
function populateSymbolDropdown() {
    const select = document.getElementById('symbol');
    select.innerHTML = '<option value="">Select a symbol...</option>';
    
    availableSymbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        select.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('backtestForm').addEventListener('submit', handleFormSubmit);
    
    // Direction button toggles
    document.querySelectorAll('.direction-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = btn.dataset.target;
            const value = btn.dataset.value;
            
            // Update hidden input
            document.getElementById(target).value = value;
            
            // Update button styles
            const group = btn.parentElement;
            group.querySelectorAll('.direction-btn').forEach(b => {
                b.classList.remove('selected');
            });
            btn.classList.add('selected');
        });
    });
    
    // Symbol change - show info
    document.getElementById('symbol').addEventListener('change', async (e) => {
        const symbol = e.target.value;
        if (symbol) {
            await showSymbolInfo(symbol);
        }
    });
}

// Show symbol info
async function showSymbolInfo(symbol) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/symbol-info/${symbol}`);
        const data = await response.json();
        
        if (data.date_range && data.row_count) {
            const infoBox = document.querySelector('.info-box');
            infoBox.innerHTML = `
                <strong>${symbol} Data Info:</strong><br>
                Date Range: ${data.date_range.min} to ${data.date_range.max}<br>
                Total Bars: ${data.row_count.toLocaleString()}
            `;
        }
    } catch (error) {
        console.error('Failed to load symbol info:', error);
    }
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Hide previous results/errors
    document.getElementById('resultsSection').classList.remove('active');
    document.getElementById('errorSection').style.display = 'none';
    
    // Show loading
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('runBtn').disabled = true;
    
    // Collect form data
    const params = {
        symbol: document.getElementById('symbol').value,
        up_threshold: parseFloat(document.getElementById('upThreshold').value),
        down_threshold: parseFloat(document.getElementById('downThreshold').value),
        up_direction: document.getElementById('upDirection').value,
        down_direction: document.getElementById('downDirection').value,
        detection_window: parseInt(document.getElementById('detectionWindow').value),
        hold_window: parseInt(document.getElementById('holdWindow').value),
        position_size: parseFloat(document.getElementById('positionSize').value),
        position_limit: parseInt(document.getElementById('positionLimit').value),
        fee_rate: parseFloat(document.getElementById('feeRate').value),
        num_accounts: parseInt(document.getElementById('numAccounts').value)
    };
    
    // Optional start date
    const startDate = document.getElementById('startDate').value;
    if (startDate) {
        params.start_date = startDate;
    }
    
    try {
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
        
        // Hide loading
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('runBtn').disabled = false;
        
        // Show results
        displayResults(data);
        
    } catch (error) {
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('runBtn').disabled = false;
        showError(error.message);
    }
}

// Display backtest results
function displayResults(data) {
    const { summary, plot, trades } = data;
    
    // Display metrics
    displayMetrics(summary);
    
    // Display plot
    if (plot) {
        displayPlot(plot);
    }
    
    // Display trades
    if (trades && trades.length > 0) {
        displayTrades(trades);
    }
    
    // Show results section
    document.getElementById('resultsSection').classList.add('active');
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Display performance metrics
function displayMetrics(summary) {
    const container = document.getElementById('metricsContainer');
    container.innerHTML = '';
    
    // Define metric display configuration
    const metrics = [
        { key: 'total_pnl', label: 'Total PnL', format: 'currency', highlight: true },
        { key: 'total_return', label: 'Total Return', format: 'percentage', highlight: true },
        { key: 'annualized_return', label: 'Annualized Return', format: 'percentage' },
        { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: 'decimal' },
        { key: 'max_drawdown', label: 'Max Drawdown', format: 'percentage', negative: true },
        { key: 'num_trades', label: 'Total Trades', format: 'number' },
        { key: 'win_rate', label: 'Win Rate', format: 'percentage' },
        { key: 'avg_profit_per_trade', label: 'Avg Profit/Trade', format: 'currency' },
        { key: 'avg_winning_trade', label: 'Avg Winning Trade', format: 'currency' },
        { key: 'avg_losing_trade', label: 'Avg Losing Trade', format: 'currency' },
        { key: 'total_fees', label: 'Total Fees', format: 'currency', negative: true },
        { key: 'avg_hold_bars', label: 'Avg Hold Time', format: 'number', suffix: ' bars' }
    ];
    
    metrics.forEach(metric => {
        if (summary[metric.key] !== undefined) {
            const card = createMetricCard(
                metric.label,
                summary[metric.key],
                metric.format,
                metric.highlight,
                metric.negative,
                metric.suffix
            );
            container.appendChild(card);
        }
    });
}

// Create metric card element
function createMetricCard(label, value, format, highlight = false, negative = false, suffix = '') {
    const card = document.createElement('div');
    card.className = 'metric-card';
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'metric-label';
    labelDiv.textContent = label;
    
    const valueDiv = document.createElement('div');
    valueDiv.className = 'metric-value';
    
    // Format value
    let formattedValue = formatValue(value, format);
    formattedValue += suffix;
    
    valueDiv.textContent = formattedValue;
    
    // Apply color coding
    if (highlight && !negative) {
        valueDiv.classList.add(value >= 0 ? 'positive' : 'negative');
    } else if (negative) {
        valueDiv.classList.add('negative');
    }
    
    card.appendChild(labelDiv);
    card.appendChild(valueDiv);
    
    return card;
}

// Format value based on type
function formatValue(value, format) {
    switch (format) {
        case 'currency':
            return value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
        case 'percentage':
            return `${(value * 100).toFixed(2)}%`;
        case 'decimal':
            return value.toFixed(3);
        case 'number':
            return Math.round(value).toLocaleString();
        default:
            return value.toString();
    }
}

// Display cumulative PnL plot
function displayPlot(plotBase64) {
    const container = document.getElementById('plotContainer');
    container.innerHTML = `<img src="data:image/png;base64,${plotBase64}" alt="Cumulative PnL Chart">`;
}

// Display trade breakdown
function displayTrades(trades) {
    const container = document.getElementById('breakdownContainer');
    
    const upEvents = trades.filter(t => t.signal_type === 'UP');
    const downEvents = trades.filter(t => t.signal_type === 'DOWN');
    
    const totalUpPnl = upEvents.reduce((sum, t) => sum + t.net_profit_dollars, 0);
    const totalDownPnl = downEvents.reduce((sum, t) => sum + t.net_profit_dollars, 0);
    const avgUpPnl = upEvents.length > 0 ? totalUpPnl / upEvents.length : 0;
    const avgDownPnl = downEvents.length > 0 ? totalDownPnl / downEvents.length : 0;
    
    container.innerHTML = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">UP Events</div>
                <div class="metric-value">${upEvents.length}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">UP Total PnL</div>
                <div class="metric-value ${totalUpPnl >= 0 ? 'positive' : 'negative'}">
                    $${totalUpPnl.toFixed(2)}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">UP Avg PnL</div>
                <div class="metric-value ${avgUpPnl >= 0 ? 'positive' : 'negative'}">
                    $${avgUpPnl.toFixed(2)}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">DOWN Events</div>
                <div class="metric-value">${downEvents.length}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">DOWN Total PnL</div>
                <div class="metric-value ${totalDownPnl >= 0 ? 'positive' : 'negative'}">
                    $${totalDownPnl.toFixed(2)}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">DOWN Avg PnL</div>
                <div class="metric-value ${avgDownPnl >= 0 ? 'positive' : 'negative'}">
                    $${avgDownPnl.toFixed(2)}
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>Recent Trades (First ${Math.min(trades.length, 100)})</h3>
            <div style="overflow-x: auto; margin-top: 10px;">
                ${generateTradesTable(trades.slice(0, 100))}
            </div>
        </div>
    `;
}

// Generate trades table HTML
function generateTradesTable(trades) {
    if (trades.length === 0) {
        return '<p>No trades executed</p>';
    }
    
    let html = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f9fa; text-align: left;">
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Date</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Signal</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Direction</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Entry</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Exit</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">PnL</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Fees</th>
                    <th style="padding: 10px; border-bottom: 2px solid #dee2e6;">Net PnL</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    trades.forEach(trade => {
        const grossPnl = trade.gross_profit_dollars;
        const grossPnlColor = grossPnl >= 0 ? '#27ae60' : '#e74c3c';
        const netPnl = trade.net_profit_dollars;
        const netPnlColor = netPnl >= 0 ? '#27ae60' : '#e74c3c';
        
        html += `
            <tr style="border-bottom: 1px solid #ecf0f1;">
                <td style="padding: 10px;">${new Date(trade.entry_time).toLocaleDateString()}</td>
                <td style="padding: 10px;">${trade.signal_type}</td>
                <td style="padding: 10px;">${trade.direction === 'B' ? '📈 Long' : '📉 Short'}</td>
                <td style="padding: 10px;">$${trade.entry_price.toFixed(2)}</td>
                <td style="padding: 10px;">$${trade.exit_price.toFixed(2)}</td>
                <td style="padding: 10px; color: ${grossPnlColor}; font-weight: 600;">$${grossPnl.toFixed(2)}</td>
                <td style="padding: 10px; color: #e74c3c;">$${trade.fees.toFixed(2)}</td>
                <td style="padding: 10px; color: ${netPnlColor}; font-weight: 600;">$${netPnl.toFixed(2)}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    return html;
}

// Show error message
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
    document.getElementById('errorSection').scrollIntoView({ behavior: 'smooth' });
}
