// ADV Analysis JavaScript

function showLoading() {
    document.getElementById('loading').classList.add('active');
    document.getElementById('results').classList.remove('active');
    document.getElementById('errorMessage').classList.remove('active');
    document.getElementById('calculateBtn').disabled = true;
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
    document.getElementById('calculateBtn').disabled = false;
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.add('active');
    hideLoading();
}

function formatNumber(num) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatLargeNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(2) + 'B';
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(2) + 'M';
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function displayStats(data) {
    const statsContainer = document.getElementById('statsContainer');
    
    // Calculate statistics
    const totalPeriods = new Set(data.map(row => row.begin_date)).size;
    const totalSymbols = new Set(data.map(row => row.symbol)).size;
    const avgADV = data.reduce((sum, row) => sum + row.adv, 0) / data.length;
    const maxADV = Math.max(...data.map(row => row.adv));
    
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Total Periods</div>
            <div class="stat-value">${totalPeriods}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Unique Symbols</div>
            <div class="stat-value">${totalSymbols}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Average ADV</div>
            <div class="stat-value">$${formatLargeNumber(avgADV)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Max ADV</div>
            <div class="stat-value">$${formatLargeNumber(maxADV)}</div>
        </div>
    `;
}

function displayResults(data) {
    const tableHead = document.getElementById('resultsTableHead');
    const tableBody = document.getElementById('resultsTable');
    
    // Clear existing content
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Group data by period
    const periodMap = new Map();
    
    data.forEach(row => {
        const periodKey = `${row.begin_date}_${row.end_date}`;
        if (!periodMap.has(periodKey)) {
            periodMap.set(periodKey, {
                begin_date: row.begin_date,
                end_date: row.end_date,
                symbols: []
            });
        }
        periodMap.get(periodKey).symbols.push({
            symbol: row.symbol,
            adv: row.adv,
            weight: row.weight
        });
    });
    
    // Sort periods chronologically
    const periods = Array.from(periodMap.entries()).sort((a, b) => 
        new Date(a[1].begin_date) - new Date(b[1].begin_date)
    );
    
    // Sort symbols within each period by ADV (descending) and assign ranks
    periods.forEach(([key, period]) => {
        period.symbols.sort((a, b) => b.adv - a.adv);
        period.symbols.forEach((symbol, index) => {
            symbol.rank = index + 1;
        });
    });
    
    // Build header row with periods as columns
    let headerHTML = '<tr>';
    periods.forEach(([key, period]) => {
        const date = new Date(period.begin_date);
        const monthYear = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        headerHTML += `<th class="period-header">${monthYear}</th>`;
    });
    headerHTML += '</tr>';
    
    tableHead.innerHTML = headerHTML;
    
    // Find the maximum number of rows needed (max symbols in any period)
    const maxRows = Math.max(...periods.map(([key, period]) => period.symbols.length));
    
    // Build table rows
    for (let rowIndex = 0; rowIndex < maxRows; rowIndex++) {
        const tr = document.createElement('tr');
        let rowHTML = '';
        
        periods.forEach(([periodKey, period]) => {
            if (rowIndex < period.symbols.length) {
                const symbolData = period.symbols[rowIndex];
                const rank = symbolData.rank;
                // Strip USDT suffix from symbol
                const symbol = symbolData.symbol.replace(/USDT$/, '');
                const adv = formatLargeNumber(symbolData.adv);
                // Format weight with 5 decimal places for precision
                const weight = symbolData.weight.toFixed(5);
                
                rowHTML += `
                    <td class="rank-${rank}">
                        <div class="cell-content">
                            <span class="cell-rank">${rank}</span>
                            <span class="cell-symbol">${symbol}</span>
                            <span class="cell-adv">$${adv}</span>
                            <span class="cell-weight">${weight}</span>
                        </div>
                    </td>
                `;
            } else {
                rowHTML += `<td class="empty-cell">-</td>`;
            }
        });
        
        tr.innerHTML = rowHTML;
        tableBody.appendChild(tr);
    }
    
    // Show results section
    document.getElementById('results').classList.add('active');
}

async function calculateADV() {
    // Get form values
    const units = document.getElementById('units').value;
    const interval = parseInt(document.getElementById('interval').value);
    const topN = parseInt(document.getElementById('topN').value);
    const dropN = parseInt(document.getElementById('dropN').value) || 0;
    
    // Validate inputs
    if (interval < 1 || interval > 12) {
        showError('Interval must be between 1 and 12');
        return;
    }
    
    if (topN < 1 || topN > 1000) {
        showError('Top N must be between 1 and 1000');
        return;
    }
    
    if (dropN < 0 || dropN >= topN) {
        showError(`Drop N must be between 0 and ${topN - 1}`);
        return;
    }
    
    showLoading();
    
    try {
        // Call API
        const response = await fetch('/api/calculate-adv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                units: units,
                interval: interval,
                top_n: topN,
                drop_n: dropN
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Display results
        hideLoading();
        displayStats(result.data);
        displayResults(result.data);
        
    } catch (error) {
        console.error('Error calculating ADV:', error);
        showError(`Error: ${error.message}`);
    }
}

// Allow Enter key to trigger calculation
document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                calculateADV();
            }
        });
    });
});
