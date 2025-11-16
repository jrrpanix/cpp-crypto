/**
 * Daily Market Data Visualization
 * Displays daily OHLCV data for selected symbols from aggregate data file
 */

// Wrap in IIFE to avoid global namespace pollution
(function() {
    'use strict';
    
    const API_BASE = 'http://localhost:5001/api';

    let priceChart = null;
    let volumeChart = null;
    let rawData = null; // Store raw data for re-rendering with different scales
    let currentSymbols = null;

    // Color palette for multiple symbols
    const CHART_COLORS = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe', 
        '#43e97b', '#fa709a', '#30cfd0', '#a8edea',
        '#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731'
    ];

    /**
     * Initialize the page
     */
    async function init() {
        console.log('Initializing daily data page...');
        await loadAvailableSymbols();
    }

/**
 * Load available symbols from API
 */
async function loadAvailableSymbols() {
    try {
        const response = await fetch(`${API_BASE}/symbols`);
        const data = await response.json();
        
        if (!data.success) {
            showStatus('error', `Failed to load symbols: ${data.error}`);
            return;
        }
        
        const symbolSelect = document.getElementById('symbols');
        symbolSelect.innerHTML = '';
        
        // Add common symbols at top
        const commonSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];
        const availableCommon = commonSymbols.filter(s => data.symbols.includes(s));
        
        if (availableCommon.length > 0) {
            const commonGroup = document.createElement('optgroup');
            commonGroup.label = 'Common Symbols';
            availableCommon.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol;
                option.textContent = symbol;
                commonGroup.appendChild(option);
            });
            symbolSelect.appendChild(commonGroup);
        }
        
        // Add all symbols
        const allGroup = document.createElement('optgroup');
        allGroup.label = 'All Symbols';
        data.symbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol;
            allGroup.appendChild(option);
        });
        symbolSelect.appendChild(allGroup);
        
        console.log(`Loaded ${data.symbols.length} symbols`);
        
    } catch (error) {
        console.error('Error loading symbols:', error);
        showStatus('error', `Error loading symbols: ${error.message}`);
    }
}

/**
 * Load data for selected symbols
 */
async function loadData() {
    const symbolSelect = document.getElementById('symbols');
    const selectedSymbols = Array.from(symbolSelect.selectedOptions).map(opt => opt.value);
    
    if (selectedSymbols.length === 0) {
        showStatus('error', 'Please select at least one symbol');
        return;
    }
    
    if (selectedSymbols.length > 10) {
        showStatus('error', 'Please select at most 10 symbols for optimal visualization');
        return;
    }
    
    const dateRange = document.getElementById('dateRange').value;
    const loadBtn = document.getElementById('loadBtn');
    
    try {
        loadBtn.disabled = true;
        showStatus('loading', `Loading data for ${selectedSymbols.length} symbols...`);
        
        // Calculate date range
        let startDate = null;
        let endDate = null;
        
        if (dateRange !== 'all') {
            const now = new Date();
            endDate = now.toISOString().split('T')[0];
            
            const daysBack = {
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365
            }[dateRange];
            
            const startDateTime = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
            startDate = startDateTime.toISOString().split('T')[0];
        }
        
        // Call API
        const response = await fetch(`${API_BASE}/daily-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbols: selectedSymbols,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showStatus('error', `Failed to load data: ${result.error}`);
            return;
        }
        
        // Display info
        showInfo(result, selectedSymbols);
        
        // Display performance table
        showPerformanceTable(result.data, selectedSymbols);
        
        // Store raw data for re-rendering
        rawData = result.data;
        currentSymbols = selectedSymbols;
        
        // Update charts
        updateCharts(result.data, selectedSymbols);
        
        showStatus('success', `Successfully loaded data for ${selectedSymbols.length} symbols`);
        
    } catch (error) {
        console.error('Error loading data:', error);
        showStatus('error', `Error: ${error.message}`);
    } finally {
        loadBtn.disabled = false;
    }
}

/**
 * Update price scale when dropdown changes
 */
function updatePriceScale() {
    if (rawData && currentSymbols) {
        updateCharts(rawData, currentSymbols);
    }
}

/**
 * Normalize price data to start at 100
 */
function normalizePrices(data) {
    if (!data || data.length === 0) return [];
    
    const firstPrice = data[0].y;
    return data.map(point => ({
        x: point.x,
        y: (point.y / firstPrice) * 100
    }));
}

/**
 * Update price and volume charts
 */
function updateCharts(data, symbols) {
    // Destroy existing charts
    if (priceChart) {
        priceChart.destroy();
    }
    if (volumeChart) {
        volumeChart.destroy();
    }
    
    // Prepare datasets for each symbol
    const priceDatasets = [];
    const volumeDatasets = [];
    
    const priceScale = document.getElementById('priceScale').value;
    
    symbols.forEach((symbol, index) => {
        const symbolData = data[symbol] || [];
        
        if (symbolData.length === 0) {
            console.warn(`No data for symbol ${symbol}`);
            return;
        }
        
        const color = CHART_COLORS[index % CHART_COLORS.length];
        
        // Prepare price data
        let priceData = symbolData.map(d => ({
            x: new Date(d.date),
            y: d.close
        }));
        
        // Apply normalization if selected
        if (priceScale === 'normalized') {
            priceData = normalizePrices(priceData);
        }
        
        // Price dataset (closing prices)
        priceDatasets.push({
            label: symbol,
            data: priceData,
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.1
        });
        
        // Volume dataset (use quote_volume for dollar volume)
        volumeDatasets.push({
            label: symbol,
            data: symbolData.map(d => ({
                x: new Date(d.date),
                y: d.quote_volume || d.volume  // Use quote_volume (dollar volume) if available
            })),
            backgroundColor: color + '80',
            borderColor: color,
            borderWidth: 1
        });
    });
    
    // Create price chart (line)
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            datasets: priceDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            if (priceScale === 'normalized') {
                                const percentChange = ((value - 100) / 100 * 100).toFixed(2);
                                return `${context.dataset.label}: ${value.toFixed(2)} (${percentChange > 0 ? '+' : ''}${percentChange}%)`;
                            }
                            return `${context.dataset.label}: $${value.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    type: priceScale === 'log' ? 'logarithmic' : 'linear',
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: priceScale === 'normalized' ? 'Normalized Price (Start = 100)' : 'Price (USD)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (priceScale === 'normalized') {
                                return value.toFixed(2);
                            }
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
    
    // Create volume chart (bar)
    const volumeCtx = document.getElementById('volumeChart').getContext('2d');
    volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            datasets: volumeDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            if (value >= 1e9) {
                                return `${context.dataset.label}: $${(value / 1e9).toFixed(2)}B`;
                            } else if (value >= 1e6) {
                                return `${context.dataset.label}: $${(value / 1e6).toFixed(2)}M`;
                            } else if (value >= 1e3) {
                                return `${context.dataset.label}: $${(value / 1e3).toFixed(2)}K`;
                            }
                            return `${context.dataset.label}: $${value.toFixed(0)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    stacked: false
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Volume (USD)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1e9) {
                                return '$' + (value / 1e9).toFixed(2) + 'B';
                            } else if (value >= 1e6) {
                                return '$' + (value / 1e6).toFixed(1) + 'M';
                            } else if (value >= 1e3) {
                                return '$' + (value / 1e3).toFixed(1) + 'K';
                            }
                            return '$' + value.toFixed(0);
                        }
                    },
                    stacked: false
                }
            }
        }
    });
    
    console.log('Charts updated successfully');
}

/**
 * Show performance table with key metrics
 */
function showPerformanceTable(data, symbols) {
    const tableDiv = document.getElementById('performanceTable');
    const tbody = document.querySelector('#perfTableContent tbody');
    
    tbody.innerHTML = '';
    
    // Calculate metrics for each symbol
    const metrics = symbols.map(symbol => {
        const symbolData = data[symbol] || [];
        
        if (symbolData.length === 0) {
            return null;
        }
        
        const startPrice = symbolData[0].close;
        const endPrice = symbolData[symbolData.length - 1].close;
        const priceChange = endPrice - startPrice;
        const returnPct = (priceChange / startPrice) * 100;
        
        // Calculate average daily volume (quote_volume in USD)
        const totalVolume = symbolData.reduce((sum, d) => sum + (d.quote_volume || d.volume * d.close || 0), 0);
        const avgDailyVolume = totalVolume / symbolData.length;
        
        return {
            symbol,
            startPrice,
            endPrice,
            priceChange,
            returnPct,
            avgDailyVolume
        };
    }).filter(m => m !== null);
    
    // Sort by return percentage (descending)
    metrics.sort((a, b) => b.returnPct - a.returnPct);
    
    // Populate table rows
    metrics.forEach(m => {
        const row = document.createElement('tr');
        
        const returnClass = m.returnPct >= 0 ? 'positive' : 'negative';
        const returnSign = m.returnPct >= 0 ? '+' : '';
        
        row.innerHTML = `
            <td class="symbol-cell">${m.symbol}</td>
            <td class="number-cell">$${m.startPrice.toFixed(2)}</td>
            <td class="number-cell">$${m.endPrice.toFixed(2)}</td>
            <td class="number-cell ${returnClass}">${returnSign}$${m.priceChange.toFixed(2)}</td>
            <td class="number-cell ${returnClass}">${returnSign}${m.returnPct.toFixed(2)}%</td>
            <td class="number-cell">${formatVolume(m.avgDailyVolume)}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    tableDiv.style.display = 'block';
}

/**
 * Format volume for display
 */
function formatVolume(value) {
    if (value >= 1e9) {
        return '$' + (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return '$' + (value / 1e6).toFixed(1) + 'M';
    } else if (value >= 1e3) {
        return '$' + (value / 1e3).toFixed(1) + 'K';
    }
    return '$' + value.toFixed(0);
}

/**
 * Show info bar with data statistics
 */
function showInfo(result, symbols) {
    const infoDiv = document.getElementById('info');
    
    // Calculate total data points
    let totalPoints = 0;
    symbols.forEach(symbol => {
        const symbolData = result.data[symbol] || [];
        totalPoints += symbolData.length;
    });
    
    infoDiv.innerHTML = `
        <div>
            <strong>Symbols:</strong> ${symbols.length} | 
            <strong>Data Points:</strong> ${totalPoints} | 
            <strong>Date Range:</strong> ${result.date_range.start.split('T')[0]} to ${result.date_range.end.split('T')[0]}
        </div>
        <div>
            <strong>Source:</strong> ${result.file}
        </div>
    `;
    infoDiv.style.display = 'flex';
}

/**
 * Show status message
 */
function showStatus(type, message) {
    const statusDiv = document.getElementById('status');
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

// Expose functions to global scope for HTML onclick handlers
window.loadData = loadData;
window.updatePriceScale = updatePriceScale;

// Run initialization when DOM is ready or immediately if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM is already ready, run init immediately
    init();
}

})(); // End IIFE
