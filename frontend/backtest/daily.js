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
    let allAvailableSymbols = []; // Store all symbols for search
    let selectedSymbolsSet = new Set(); // Track manually selected symbols

    // Color palette for multiple symbols (15 colors for 15 symbols)
    const CHART_COLORS = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe', 
        '#43e97b', '#fa709a', '#30cfd0', '#a8edea',
        '#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731',
        '#5f27cd', '#00d2d3', '#ff9ff3'
    ];

    /**
     * Initialize the page
     */
    async function init() {
        console.log('Initializing daily data page...');
        await loadAvailableSymbols();
        setupSearchHandlers();
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
        
        // Store all symbols for search
        allAvailableSymbols = data.symbols;
        
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
 * Setup search input handlers
 */
function setupSearchHandlers() {
    const searchInput = document.getElementById('symbolSearchInput');
    const suggestionsDiv = document.getElementById('searchSuggestions');
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toUpperCase().trim();
        
        if (query.length === 0) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        
        // Filter symbols that match the query
        const matches = allAvailableSymbols.filter(symbol => 
            symbol.toUpperCase().includes(query)
        ).slice(0, 10); // Limit to 10 suggestions
        
        if (matches.length === 0) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        
        // Display suggestions
        suggestionsDiv.innerHTML = matches.map(symbol => 
            `<div class="suggestion-item" onclick="addSymbol('${symbol}')">${symbol}</div>`
        ).join('');
        suggestionsDiv.style.display = 'block';
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });
    
    // Add symbol on Enter key
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const query = e.target.value.toUpperCase().trim();
            if (allAvailableSymbols.includes(query)) {
                addSymbol(query);
                e.target.value = '';
                suggestionsDiv.style.display = 'none';
            }
        }
    });
}

/**
 * Add a symbol to the selected list
 */
function addSymbol(symbol) {
    if (selectedSymbolsSet.has(symbol)) {
        showStatus('error', `${symbol} is already selected`);
        return;
    }
    
    if (selectedSymbolsSet.size >= 15) {
        showStatus('error', 'Maximum 15 symbols allowed for optimal visualization');
        return;
    }
    
    selectedSymbolsSet.add(symbol);
    updateSelectedSymbolsDisplay();
    
    // Clear search input
    document.getElementById('symbolSearchInput').value = '';
    document.getElementById('searchSuggestions').style.display = 'none';
}

/**
 * Remove a symbol from the selected list
 */
function removeSymbol(symbol) {
    selectedSymbolsSet.delete(symbol);
    updateSelectedSymbolsDisplay();
}

/**
 * Clear all selected symbols
 */
function clearSelectedSymbols() {
    selectedSymbolsSet.clear();
    updateSelectedSymbolsDisplay();
}

/**
 * Update the display of selected symbols
 */
function updateSelectedSymbolsDisplay() {
    const displayDiv = document.getElementById('selectedSymbolsDisplay');
    
    if (selectedSymbolsSet.size === 0) {
        displayDiv.innerHTML = '<span style="color: #999; font-size: 0.9rem;">No symbols selected. Search and add symbols above.</span>';
        return;
    }
    
    displayDiv.innerHTML = Array.from(selectedSymbolsSet).map(symbol => 
        `<span class="symbol-tag">
            ${symbol}
            <span class="remove-btn" onclick="removeSymbol('${symbol}')">✕</span>
        </span>`
    ).join('');
}

/**
 * Load data for selected symbols
 */
async function loadData() {
    // Get symbols from both search/add and traditional select
    const symbolSelect = document.getElementById('symbols');
    const selectSymbols = Array.from(symbolSelect.selectedOptions).map(opt => opt.value);
    
    // Combine with manually added symbols
    const allSymbols = [...new Set([...selectedSymbolsSet, ...selectSymbols])];
    
    if (allSymbols.length === 0) {
        showStatus('error', 'Please select at least one symbol (search & add, or select from list)');
        return;
    }
    
    if (allSymbols.length > 15) {
        showStatus('error', 'Please select at most 15 symbols for optimal visualization');
        return;
    }
    
    const selectedSymbols = allSymbols;
    
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
        
        // Load correlation matrix (don't wait for it)
        loadCorrelationMatrix().catch(err => console.error('Failed to load correlation:', err));
        
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

    // Expose functions to global scope for onclick handlers
    window.loadData = loadData;
    window.updatePriceScale = updatePriceScale;
    window.loadTopPerformers = loadTopPerformers;
    window.loadBottomPerformers = loadBottomPerformers;
    window.addSymbol = addSymbol;
    window.removeSymbol = removeSymbol;
    window.clearSelectedSymbols = clearSelectedSymbols;

/**
 * Load top performing coins
 */
async function loadTopPerformers() {
    // Get Top N from input field
    const topN = parseInt(document.getElementById('topN').value) || 10;
    
    if (topN < 1 || topN > 50) {
        showStatus('error', 'Please enter a number between 1 and 50 for Top N');
        return;
    }
    
    // Use the currently selected date range
    const period = document.getElementById('dateRange').value;
    
    showStatus('loading', `Loading top ${topN} performers for ${period === 'all' ? 'all time' : period}...`);
    
    try {
        // Calculate exact date range
        let startDate = null;
        let endDate = null;
        let cutoffDate = null;
        
        if (period !== 'all') {
            const now = new Date();
            endDate = now.toISOString().split('T')[0];
            
            const daysBack = {
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365
            }[period];
            
            const startDateTime = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
            startDate = startDateTime.toISOString().split('T')[0];
            cutoffDate = new Date(startDate);
        }
        
        // Fetch all available symbols first
        const symbolsResponse = await fetch(`${API_BASE}/symbols`);
        const symbolsData = await symbolsResponse.json();
        
        if (!symbolsData.success) {
            showStatus('error', `Failed to load symbols: ${symbolsData.error}`);
            return;
        }
        
        const allSymbols = symbolsData.symbols;
        
        // Fetch data for all symbols to calculate performance
        const response = await fetch(`${API_BASE}/daily-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbols: allSymbols,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showStatus('error', `Failed to load data: ${data.error}`);
            return;
        }
        
        // Calculate returns for each symbol
        const performances = [];
        
        for (const symbol in data.data) {
            let symbolData = data.data[symbol];
            if (symbolData.length < 2) continue; // Need at least 2 data points
            
            // Filter data to exact date range if specified
            if (cutoffDate) {
                symbolData = symbolData.filter(d => new Date(d.date) >= cutoffDate);
            }
            
            if (symbolData.length < 2) continue; // Still need at least 2 points after filtering
            
            const startPrice = symbolData[0].close;
            const endPrice = symbolData[symbolData.length - 1].close;
            const returnPct = ((endPrice - startPrice) / startPrice) * 100;
            
            performances.push({
                symbol: symbol,
                returnPct: returnPct,
                startPrice: startPrice,
                endPrice: endPrice,
                startDate: symbolData[0].date,
                endDate: symbolData[symbolData.length - 1].date,
                dataPoints: symbolData.length
            });
        }
        
        // Sort by return percentage (descending)
        performances.sort((a, b) => b.returnPct - a.returnPct);
        
        // Get top N
        const topPerformers = performances.slice(0, topN);
        const topSymbols = topPerformers.map(p => p.symbol);
        
        // Clear previous selections and add top performers to search feature
        clearSelectedSymbols();
        topSymbols.forEach(symbol => selectedSymbolsSet.add(symbol));
        updateSelectedSymbolsDisplay();
        
        // Also clear the traditional select
        const symbolSelect = document.getElementById('symbols');
        Array.from(symbolSelect.options).forEach(option => {
            option.selected = false;
        });
        
        // Set price scale to normalized for better comparison
        document.getElementById('priceScale').value = 'normalized';
        
        // Show info about top performers
        const periodLabel = period === 'all' ? 'all time' : 
                           period === '1m' ? 'last month' :
                           period === '3m' ? 'last 3 months' :
                           period === '6m' ? 'last 6 months' :
                           period === '1y' ? 'last year' : period;
        
        const infoText = `Top ${topN} performers (${periodLabel}): ` + 
            topPerformers.slice(0, 5).map(p => 
                `${p.symbol} (${p.returnPct > 0 ? '+' : ''}${p.returnPct.toFixed(1)}%)`
            ).join(', ') +
            (topN > 5 ? ` and ${topN - 5} more...` : '');
        
        showStatus('success', infoText);
        
        // Automatically load the data
        await loadData();
        
    } catch (error) {
        console.error('Error loading top performers:', error);
        showStatus('error', `Error: ${error.message}`);
    }
}

/**
 * Load bottom performing (worst) coins
 */
async function loadBottomPerformers() {
    // Get Top N from input field (reuse for bottom N)
    const topN = parseInt(document.getElementById('topN').value) || 10;
    
    if (topN < 1 || topN > 50) {
        showStatus('error', 'Please enter a number between 1 and 50 for Top N');
        return;
    }
    
    // Use the currently selected date range
    const period = document.getElementById('dateRange').value;
    
    showStatus('loading', `Loading bottom ${topN} performers for ${period === 'all' ? 'all time' : period}...`);
    
    try {
        // Calculate exact date range
        let startDate = null;
        let endDate = null;
        let cutoffDate = null;
        
        if (period !== 'all') {
            const now = new Date();
            endDate = now.toISOString().split('T')[0];
            
            const daysBack = {
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365
            }[period];
            
            const startDateTime = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
            startDate = startDateTime.toISOString().split('T')[0];
            cutoffDate = new Date(startDate);
        }
        
        // Fetch all available symbols first
        const symbolsResponse = await fetch(`${API_BASE}/symbols`);
        const symbolsData = await symbolsResponse.json();
        
        if (!symbolsData.success) {
            showStatus('error', `Failed to load symbols: ${symbolsData.error}`);
            return;
        }
        
        const allSymbols = symbolsData.symbols;
        
        // Fetch data for all symbols to calculate performance
        const response = await fetch(`${API_BASE}/daily-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbols: allSymbols,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showStatus('error', `Failed to load data: ${data.error}`);
            return;
        }
        
        // Calculate returns for each symbol
        const performances = [];
        
        for (const symbol in data.data) {
            let symbolData = data.data[symbol];
            if (symbolData.length < 2) continue; // Need at least 2 data points
            
            // Filter data to exact date range if specified
            if (cutoffDate) {
                symbolData = symbolData.filter(d => new Date(d.date) >= cutoffDate);
            }
            
            if (symbolData.length < 2) continue; // Still need at least 2 points after filtering
            
            const startPrice = symbolData[0].close;
            const endPrice = symbolData[symbolData.length - 1].close;
            const returnPct = ((endPrice - startPrice) / startPrice) * 100;
            
            performances.push({
                symbol: symbol,
                returnPct: returnPct,
                startPrice: startPrice,
                endPrice: endPrice,
                startDate: symbolData[0].date,
                endDate: symbolData[symbolData.length - 1].date,
                dataPoints: symbolData.length
            });
        }
        
        // Sort by return percentage (ascending for bottom performers)
        performances.sort((a, b) => a.returnPct - b.returnPct);
        
        // Get bottom N
        const bottomPerformers = performances.slice(0, topN);
        const bottomSymbols = bottomPerformers.map(p => p.symbol);
        
        // Clear previous selections and add bottom performers to search feature
        clearSelectedSymbols();
        bottomSymbols.forEach(symbol => selectedSymbolsSet.add(symbol));
        updateSelectedSymbolsDisplay();
        
        // Also clear the traditional select
        const symbolSelect = document.getElementById('symbols');
        Array.from(symbolSelect.options).forEach(option => {
            option.selected = false;
        });
        
        // Set price scale to normalized for better comparison
        document.getElementById('priceScale').value = 'normalized';
        
        // Show info about bottom performers
        const periodLabel = period === 'all' ? 'all time' : 
                           period === '1m' ? 'last month' :
                           period === '3m' ? 'last 3 months' :
                           period === '6m' ? 'last 6 months' :
                           period === '1y' ? 'last year' : period;
        
        const infoText = `Bottom ${topN} performers (${periodLabel}): ` + 
            bottomPerformers.slice(0, 5).map(p => 
                `${p.symbol} (${p.returnPct > 0 ? '+' : ''}${p.returnPct.toFixed(1)}%)`
            ).join(', ') +
            (topN > 5 ? ` and ${topN - 5} more...` : '');
        
        showStatus('success', infoText);
        
        // Automatically load the data
        await loadData();
        
    } catch (error) {
        console.error('Error loading bottom performers:', error);
        showStatus('error', `Error: ${error.message}`);
    }
}

/**
 * Load and display correlation matrix
 */
async function loadCorrelationMatrix() {
    console.log('loadCorrelationMatrix called, currentSymbols:', currentSymbols);
    
    if (!currentSymbols || currentSymbols.length < 2) {
        console.log('Not enough symbols for correlation, need at least 2');
        document.getElementById('correlationContainer').style.display = 'none';
        return;
    }
    
    try {
        const dateRange = document.getElementById('dateRange').value;
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
        
        console.log('Fetching correlation from API...', {
            url: `${API_BASE}/daily-correlation`,
            symbols: currentSymbols,
            startDate,
            endDate
        });
        
        const response = await fetch(`${API_BASE}/daily-correlation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbols: currentSymbols,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const result = await response.json();
        console.log('Correlation API response:', result);
        
        if (!result.success) {
            console.error('Failed to load correlation:', result.error);
            document.getElementById('correlationContainer').style.display = 'none';
            return;
        }
        
        renderCorrelationHeatmap(result.correlation_matrix, result.symbols, result.data_points);
        document.getElementById('correlationContainer').style.display = 'block';
        console.log('Correlation heatmap rendered successfully');
        
    } catch (error) {
        console.error('Error loading correlation:', error);
        document.getElementById('correlationContainer').style.display = 'none';
    }
}

/**
 * Render correlation matrix as HTML heatmap
 */
function renderCorrelationHeatmap(corrMatrix, symbols, dataPoints) {
    const heatmapDiv = document.getElementById('correlationHeatmap');
    
    // Create table
    let html = '<table class="corr-table">';
    
    // Header row
    html += '<tr><th></th>';
    symbols.forEach(sym => {
        html += `<th>${sym}</th>`;
    });
    html += '</tr>';
    
    // Data rows
    symbols.forEach(sym1 => {
        html += '<tr>';
        html += `<td class="symbol-label">${sym1}</td>`;
        
        symbols.forEach(sym2 => {
            const corr = corrMatrix[sym1][sym2];
            const color = getCorrelationColor(corr);
            const textColor = Math.abs(corr) > 0.5 ? '#fff' : '#000';
            html += `<td style="background-color: ${color}; color: ${textColor};">${corr.toFixed(2)}</td>`;
        });
        
        html += '</tr>';
    });
    
    html += '</table>';
    
    heatmapDiv.innerHTML = html;
    document.getElementById('correlationDataPoints').textContent = `${dataPoints} days`;
}

/**
 * Get color for correlation value
 * Green for positive, red for negative, white for neutral
 */
function getCorrelationColor(corr) {
    if (corr > 0) {
        // Positive correlation: white to dark green
        const intensity = Math.floor(corr * 255);
        return `rgb(${255 - intensity}, 255, ${255 - intensity})`;
    } else if (corr < 0) {
        // Negative correlation: white to dark red
        const intensity = Math.floor(Math.abs(corr) * 255);
        return `rgb(255, ${255 - intensity}, ${255 - intensity})`;
    } else {
        // Zero correlation
        return '#ffffff';
    }
}

// Run initialization when DOM is ready or immediately if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM is already ready, run init immediately
    init();
}

})(); // End IIFE
