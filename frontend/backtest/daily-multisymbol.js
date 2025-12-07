// Daily Multi-Symbol Backtest JavaScript
// Wrap in IIFE to avoid global namespace pollution
(function() {
    'use strict';

    // Use relative URL to work with any domain/port
    const API_BASE_URL = window.location.origin;

    let availableSymbols = [];
    let currentResults = [];
    let availableUniverses = {};
    let currentUniverse = 'all';

    // Initialize on page load
    async function init() {
        console.log('Initializing daily multi-symbol backtest page...');
        await loadUniverses();
        await fetchSymbols();
        
        const form = document.getElementById('backtestForm');
        const clearBtn = document.getElementById('clearBtn');
        
        if (form) {
            form.removeEventListener('submit', runMultiSymbolBacktest);
            form.addEventListener('submit', runMultiSymbolBacktest);
            console.log('Form submit listener attached');
        }
        
        if (clearBtn) {
            clearBtn.removeEventListener('click', clearResults);
            clearBtn.addEventListener('click', clearResults);
            console.log('Clear button listener attached');
        }
    }

    // Run initialization when DOM is ready or immediately if already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Load universe definitions
    async function loadUniverses() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/universes`);
            const data = await response.json();
            
            if (data.success) {
                availableUniverses = data.universes;
                
                const universeSelect = document.getElementById('universeSelect');
                if (universeSelect) {
                    universeSelect.innerHTML = '<option value="all">All Symbols (No Filter)</option>';
                    
                    for (const [id, config] of Object.entries(availableUniverses)) {
                        if (id === 'all') continue;
                        
                        const option = document.createElement('option');
                        option.value = id;
                        option.textContent = `${config.name} - ${config.description}`;
                        universeSelect.appendChild(option);
                    }
                }
            }
        } catch (error) {
            console.error('Error loading universes:', error);
        }
    }

    // Handle universe selection change
    window.onUniverseChange = async function() {
        const universeSelect = document.getElementById('universeSelect');
        currentUniverse = universeSelect.value;
        
        console.log(`Universe changed to: ${currentUniverse}`);
        
        // Reload symbols for the selected universe
        await fetchSymbols();
        
        // Update the Number of Symbols input to match universe size
        const numSymbolsInput = document.getElementById('numSymbols');
        if (numSymbolsInput) {
            numSymbolsInput.max = availableSymbols.length;
            
            // For defined universes (not "all"), automatically set N to the universe size
            // This makes it easier to test the full universe
            if (currentUniverse !== 'all' && availableSymbols.length <= 200) {
                numSymbolsInput.value = availableSymbols.length;
            } else {
                // For "all" or very large universes, adjust only if current value exceeds available
                if (parseInt(numSymbolsInput.value) > availableSymbols.length) {
                    numSymbolsInput.value = availableSymbols.length;
                }
            }
            
            // Update placeholder to show range
            numSymbolsInput.placeholder = `1-${availableSymbols.length}`;
        }
        
        // Show info message
        if (currentUniverse !== 'all' && availableUniverses[currentUniverse]) {
            const config = availableUniverses[currentUniverse];
            showStatus(`Universe: ${config.name} - Testing all ${availableSymbols.length} symbols (you can adjust Number of Symbols to test fewer)`, 'info');
        } else {
            showStatus(`${availableSymbols.length} symbols available`, 'info');
        }
    };

    // Fetch available symbols on page load (from daily data)
    async function fetchSymbols() {
        try {
            let url = `${API_BASE_URL}/api/daily-symbols`;
            if (currentUniverse && currentUniverse !== 'all') {
                url = `${API_BASE_URL}/api/universe-symbols?universe=${currentUniverse}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.symbols) {
                availableSymbols = data.symbols;
                console.log(`Loaded ${availableSymbols.length} available daily symbols for universe: ${currentUniverse}`);
            } else {
                showStatus('Failed to load available symbols', 'error');
            }
        } catch (error) {
            console.error('Error fetching daily symbols:', error);
            showStatus('Error loading symbols: ' + error.message, 'error');
        }
    }

    // Randomly select N symbols from available symbols
    function selectRandomSymbols(n) {
        if (availableSymbols.length === 0) {
            throw new Error('No symbols available');
        }
        
        const shuffled = [...availableSymbols].sort(() => 0.5 - Math.random());
        return shuffled.slice(0, Math.min(n, shuffled.length));
    }

    // Show status message
    function showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = message;
        statusDiv.className = type;
    }

    // Update progress bar
    function updateProgress(current, total) {
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        
        progressBar.classList.add('show');
        const percentage = Math.round((current / total) * 100);
        progressFill.style.width = `${percentage}%`;
        progressFill.textContent = `${current}/${total} (${percentage}%)`;
        
        if (current === total) {
            setTimeout(() => {
                progressBar.classList.remove('show');
            }, 2000);
        }
    }

    // Run backtest for a single symbol (daily data)
    async function runSingleBacktest(symbol, params) {
        const response = await fetch(`${API_BASE_URL}/api/daily-backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                up_threshold: params.up_threshold,
                up_direction: params.up_direction,
                down_threshold: params.down_threshold,
                down_direction: params.down_direction,
                detection_window: params.detection_window,
                hold_window: params.hold_window,
                position_size: params.position_size,
                position_limit: params.position_limit,
                fee_rate: params.fee_rate,
                num_accounts: params.num_accounts,
                start_date: params.start_date || null
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Backtest failed');
        }
        
        return {
            symbol: symbol,
            summary: data.summary,
            num_trades: data.num_trades,
            cumulative_pnl_series: data.cumulative_pnl_series || []
        };
    }

    // Run multi-symbol backtest
    async function runMultiSymbolBacktest(event) {
        event.preventDefault();
        
        const runBtn = document.getElementById('runBtn');
        runBtn.disabled = true;
        
        try {
            // Get form values
            const numSymbols = parseInt(document.getElementById('numSymbols').value);
            const upThreshold = parseFloat(document.getElementById('upThreshold').value) / 100;
            const upDirection = document.getElementById('upDirection').value;
            const downThreshold = parseFloat(document.getElementById('downThreshold').value) / 100;
            const downDirection = document.getElementById('downDirection').value;
            const detectionWindow = parseInt(document.getElementById('detectionWindow').value);
            const holdWindow = parseInt(document.getElementById('holdWindow').value);
            const positionSize = parseFloat(document.getElementById('positionSize').value);
            const positionLimit = parseInt(document.getElementById('positionLimit').value);
            const feeRate = parseFloat(document.getElementById('feeRate').value) / 100;
            const numAccounts = parseInt(document.getElementById('numAccounts').value);
            const startDate = document.getElementById('startDate').value;
            
            // Validate inputs
            if (upThreshold <= 0) {
                showStatus('Up threshold must be positive', 'error');
                return;
            }
            if (downThreshold >= 0) {
                showStatus('Down threshold must be negative (or use -999 to disable)', 'error');
                return;
            }
            
            // Select random symbols
            showStatus('Selecting random symbols...', 'info');
            
            // Log current universe and available symbols for debugging
            console.log(`Current universe: ${currentUniverse}`);
            console.log(`Available symbols count: ${availableSymbols.length}`);
            console.log(`Available symbols:`, availableSymbols.slice(0, 10)); // First 10 for debug
            
            const selectedSymbols = selectRandomSymbols(numSymbols);
            console.log(`Selected symbols:`, selectedSymbols);
            
            if (selectedSymbols.length === 0) {
                showStatus('No symbols available to test', 'error');
                return;
            }
            
            // Show which universe is being used
            let universeInfo = 'All Symbols';
            if (currentUniverse !== 'all' && availableUniverses[currentUniverse]) {
                universeInfo = availableUniverses[currentUniverse].name;
            }
            
            showStatus(`Running daily backtest on ${selectedSymbols.length} symbols from ${universeInfo}...`, 'info');
            
            // Prepare parameters
            const params = {
                up_threshold: upThreshold,
                up_direction: upDirection,
                down_threshold: downThreshold,
                down_direction: downDirection,
                detection_window: detectionWindow,
                hold_window: holdWindow,
                position_size: positionSize,
                position_limit: positionLimit,
                fee_rate: feeRate,
                num_accounts: numAccounts,
                start_date: startDate || null  // Convert empty string to null
            };
            
            // Use batch API for better performance
            const startTime = performance.now();
            const response = await fetch(`${API_BASE_URL}/api/daily-backtest/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbols: selectedSymbols,
                    params: params
                })
            });
            
            const data = await response.json();
            const endTime = performance.now();
            const duration = ((endTime - startTime) / 1000).toFixed(2);
            
            if (!data.success) {
                throw new Error(data.error || 'Batch backtest failed');
            }
            
            // Process results
            currentResults = data.results
                .filter(r => r.success)
                .map(r => ({
                    symbol: r.symbol,
                    summary: r.summary,
                    num_trades: r.num_trades,
                    cumulative_pnl_series: r.cumulative_pnl_series || []
                }));
            
            // Log any failures
            const failures = data.results.filter(r => !r.success);
            if (failures.length > 0) {
                console.warn('Failed symbols:', failures.map(f => `${f.symbol}: ${f.error}`));
            }
            
            if (currentResults.length === 0) {
                showStatus('No successful backtests completed', 'error');
                return;
            }
            
            // Display results
            displayResults();
            showStatus(`✅ Completed ${currentResults.length} daily backtests in ${duration}s (${failures.length} failed)`, 'success');
            
        } catch (error) {
            console.error('Error running multi-symbol backtest:', error);
            showStatus('Error: ' + error.message, 'error');
        } finally {
            runBtn.disabled = false;
        }
    }

    // Calculate aggregate statistics
    function calculateAggregateStats() {
        const totalTrades = currentResults.reduce((sum, r) => sum + r.num_trades, 0);
        const totalGrossProfit = currentResults.reduce((sum, r) => sum + (r.summary.gross_profit || 0), 0);
        const totalFees = currentResults.reduce((sum, r) => sum + (r.summary.total_fees || 0), 0);
        const totalNetProfit = currentResults.reduce((sum, r) => sum + (r.summary.net_profit || 0), 0);
        const totalWinners = currentResults.reduce((sum, r) => sum + (r.summary.num_winners || 0), 0);
        const totalLosers = currentResults.reduce((sum, r) => sum + (r.summary.num_losers || 0), 0);
        
        const avgNetProfit = totalNetProfit / currentResults.length;
        const avgProfitPerTrade = totalTrades > 0 ? totalNetProfit / totalTrades : 0;
        const overallWinRate = totalWinners + totalLosers > 0 
            ? (totalWinners / (totalWinners + totalLosers)) * 100 
            : 0;
        
        // Calculate portfolio Sharpe (simplified - average of individual Sharpes)
        const avgSharpe = currentResults.reduce((sum, r) => sum + (r.summary.net_sharpe_ratio || 0), 0) / currentResults.length;
        
        // Count profitable symbols
        const profitableSymbols = currentResults.filter(r => (r.summary.net_profit || 0) > 0).length;
        
        return {
            totalSymbols: currentResults.length,
            totalTrades: totalTrades,
            totalGrossProfit: totalGrossProfit,
            totalFees: totalFees,
            totalNetProfit: totalNetProfit,
            avgNetProfit: avgNetProfit,
            avgProfitPerTrade: avgProfitPerTrade,
            totalWinners: totalWinners,
            totalLosers: totalLosers,
            overallWinRate: overallWinRate,
            avgSharpe: avgSharpe,
            profitableSymbols: profitableSymbols,
            unprofitableSymbols: currentResults.length - profitableSymbols
        };
    }

    // Format currency
    function formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    // Format percentage (value already in percentage 0-100)
    function formatPercent(value) {
        return value.toFixed(2) + '%';
    }

    // Display results
    function displayResults() {
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.classList.add('show');
        
        // Calculate aggregate stats
        const aggStats = calculateAggregateStats();
        
        // Display aggregate statistics in table format
        const aggregateStatsDiv = document.getElementById('aggregateStats');
        aggregateStatsDiv.innerHTML = `
            <tr>
                <td>${aggStats.totalSymbols}</td>
                <td>${aggStats.totalTrades}</td>
                <td class="${aggStats.totalGrossProfit >= 0 ? 'positive' : 'negative'}">${formatCurrency(aggStats.totalGrossProfit)}</td>
                <td>${formatCurrency(aggStats.totalFees)}</td>
                <td class="${aggStats.totalNetProfit >= 0 ? 'positive' : 'negative'}">${formatCurrency(aggStats.totalNetProfit)}</td>
                <td class="${aggStats.avgNetProfit >= 0 ? 'positive' : 'negative'}">${formatCurrency(aggStats.avgNetProfit)}</td>
                <td class="${aggStats.avgProfitPerTrade >= 0 ? 'positive' : 'negative'}">${formatCurrency(aggStats.avgProfitPerTrade)}</td>
                <td>${aggStats.overallWinRate.toFixed(2)}%</td>
                <td>${aggStats.avgSharpe.toFixed(3)}</td>
                <td>${aggStats.profitableSymbols} / ${aggStats.totalSymbols}</td>
            </tr>
        `;
        
        // Store sorted results for table sorting
        currentSortedResults = [...currentResults].sort((a, b) => {
            return (b.summary.net_profit || 0) - (a.summary.net_profit || 0);
        });
        
        // Display individual symbol results
        renderSymbolTable(currentSortedResults);
        
        // Add sort functionality
        initializeTableSorting();
        
        // Create cumulative PnL chart
        createCumulativePnlChart();
    }

    // Create cumulative PnL chart
    let cumulativeChart = null;

    function createCumulativePnlChart() {
        // Destroy existing chart if it exists
        if (cumulativeChart) {
            cumulativeChart.destroy();
        }
        
        // Collect all time series from all symbols
        const allTimeSeries = [];
        currentResults.forEach(result => {
            if (result.cumulative_pnl_series && result.cumulative_pnl_series.length > 0) {
                result.cumulative_pnl_series.forEach(point => {
                    allTimeSeries.push({
                        time: new Date(point.time),
                        pnl: point.pnl,
                        symbol: result.symbol
                    });
                });
            }
        });
        
        if (allTimeSeries.length === 0) {
            // No data to plot
            const ctx = document.getElementById('cumulativePnlChart').getContext('2d');
            cumulativeChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['No Data'],
                    datasets: [{
                        label: 'Cumulative Net PnL ($)',
                        data: [0],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'No Trade Data Available',
                            font: { size: 16, weight: 'bold' }
                        }
                    }
                }
            });
            return;
        }
        
        // Sort all points by time
        allTimeSeries.sort((a, b) => a.time - b.time);
        
        // Group by time and sum PnL values at each timestamp
        // Create a map of time -> {total PnL, symbols contributing}
        const timeMap = new Map();
        
        allTimeSeries.forEach(point => {
            const timeKey = point.time.getTime();
            if (!timeMap.has(timeKey)) {
                timeMap.set(timeKey, {
                    time: point.time,
                    totalPnl: 0,
                    symbolPnls: new Map()
                });
            }
            const entry = timeMap.get(timeKey);
            entry.symbolPnls.set(point.symbol, point.pnl);
        });
        
        // Convert to array and calculate portfolio cumulative PnL
        // At each timestamp, sum the latest cumulative PnL from each symbol
        const sortedTimes = Array.from(timeMap.keys()).sort((a, b) => a - b);
        const portfolioData = [];
        const labels = [];
        
        // Track the last known cumulative PnL for each symbol
        const lastKnownPnl = new Map();
        currentResults.forEach(r => lastKnownPnl.set(r.symbol, 0));
        
        sortedTimes.forEach(timeKey => {
            const entry = timeMap.get(timeKey);
            
            // Update last known PnL for symbols that have a value at this time
            entry.symbolPnls.forEach((pnl, symbol) => {
                lastKnownPnl.set(symbol, pnl);
            });
            
            // Sum up all symbols' current cumulative PnL
            let portfolioPnl = 0;
            lastKnownPnl.forEach((pnl, symbol) => {
                portfolioPnl += pnl;
            });
            
            portfolioData.push(portfolioPnl);
            labels.push(entry.time);
        });
        
        // Add starting point at 0
        labels.unshift(new Date(sortedTimes[0] - 86400000)); // 1 day before first trade
        portfolioData.unshift(0);
        
        const finalPnl = portfolioData[portfolioData.length - 1];
        
        const ctx = document.getElementById('cumulativePnlChart').getContext('2d');
        
        cumulativeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Portfolio Cumulative Net PnL ($)',
                    data: portfolioData,
                    borderColor: finalPnl >= 0 ? 'rgb(39, 174, 96)' : 'rgb(231, 76, 60)',
                    backgroundColor: finalPnl >= 0 ? 'rgba(39, 174, 96, 0.1)' : 'rgba(231, 76, 60, 0.1)',
                    tension: 0.1,
                    fill: true,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Portfolio Cumulative Net PnL Over Time (${currentResults.length} Symbols, Daily Bars)`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const date = context[0].label;
                                return new Date(date).toLocaleDateString();
                            },
                            label: function(context) {
                                return 'Portfolio PnL: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Cumulative PnL ($)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM d, yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    // Render symbol table
    function renderSymbolTable(results) {
        const tbody = document.getElementById('symbolTableBody');
        tbody.innerHTML = results.map((result, index) => {
            const summary = result.summary;
            const netProfitClass = (summary.net_profit || 0) >= 0 ? 'positive' : 'negative';
            const roiClass = (summary.net_roi || 0) >= 0 ? 'positive' : 'negative';
            
            return `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${result.symbol}</strong></td>
                    <td>${result.num_trades}</td>
                    <td>${formatCurrency(summary.gross_profit || 0)}</td>
                    <td>${formatCurrency(summary.total_fees || 0)}</td>
                    <td class="${netProfitClass}">${formatCurrency(summary.net_profit || 0)}</td>
                    <td class="${roiClass}">${formatPercent(summary.net_roi || 0)}</td>
                    <td>${formatPercent(summary.win_rate || 0)}</td>
                    <td>${summary.num_winners || 0}</td>
                    <td>${summary.num_losers || 0}</td>
                    <td>${(summary.net_sharpe_ratio || 0).toFixed(3)}</td>
                </tr>
            `;
        }).join('');
    }

    // Initialize table sorting
    let currentSortColumn = 'net_pnl';
    let currentSortDirection = 'desc';
    let currentSortedResults = [];

    function initializeTableSorting() {
        const headers = document.querySelectorAll('.results-table th.sortable');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-column');
                
                // Toggle sort direction if clicking same column
                if (currentSortColumn === column) {
                    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortDirection = 'desc'; // Default to descending for new column
                }
                
                // Update header classes
                headers.forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                });
                header.classList.add(currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                
                // Sort and render
                sortAndRenderTable(column, currentSortDirection);
            });
        });
    }

    function sortAndRenderTable(column, direction) {
        const sorted = [...currentSortedResults].sort((a, b) => {
            let aVal, bVal;
            
            switch(column) {
                case 'rank':
                    // Ranks are assigned after sorting by net_pnl, so we'll just reverse current order
                    return direction === 'asc' ? 1 : -1;
                case 'symbol':
                    aVal = a.symbol;
                    bVal = b.symbol;
                    return direction === 'asc' ? 
                        aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                case 'trades':
                    aVal = a.num_trades || 0;
                    bVal = b.num_trades || 0;
                    break;
                case 'gross_pnl':
                    aVal = a.summary.gross_profit || 0;
                    bVal = b.summary.gross_profit || 0;
                    break;
                case 'fees':
                    aVal = a.summary.total_fees || 0;
                    bVal = b.summary.total_fees || 0;
                    break;
                case 'net_pnl':
                    aVal = a.summary.net_profit || 0;
                    bVal = b.summary.net_profit || 0;
                    break;
                case 'roi':
                    aVal = a.summary.net_roi || 0;
                    bVal = b.summary.net_roi || 0;
                    break;
                case 'win_rate':
                    aVal = a.summary.win_rate || 0;
                    bVal = b.summary.win_rate || 0;
                    break;
                case 'winners':
                    aVal = a.summary.num_winners || 0;
                    bVal = b.summary.num_winners || 0;
                    break;
                case 'losers':
                    aVal = a.summary.num_losers || 0;
                    bVal = b.summary.num_losers || 0;
                    break;
                case 'sharpe':
                    aVal = a.summary.net_sharpe_ratio || 0;
                    bVal = b.summary.net_sharpe_ratio || 0;
                    break;
                default:
                    return 0;
            }
            
            if (direction === 'asc') {
                return aVal - bVal;
            } else {
                return bVal - aVal;
            }
        });
        
        currentSortedResults = sorted;
        renderSymbolTable(sorted);
    }

    // Clear results
    function clearResults() {
        currentResults = [];
        currentSortedResults = [];
        
        // Destroy chart if it exists
        if (cumulativeChart) {
            cumulativeChart.destroy();
            cumulativeChart = null;
        }
        
        document.getElementById('resultsSection').classList.remove('show');
        document.getElementById('status').className = '';
        document.getElementById('progressBar').classList.remove('show');
    }

})(); // End IIFE
