// Trading Table Dashboard
class TradingTableDashboard {
    constructor() {
        this.ws = null;
        this.httpPollingInterval = null;
        this.heartbeatInterval = null;
        this.isConnected = false;
        this.data = new Map(); // Using Map for better performance with symbol lookup
        this.messageCounters = new Map(); // Track message count per symbol
        this.totalMessages = 0;
        this.lastMessageTime = null;
        this.dataSource = 'No Data'; // Track if we're getting live or test data
        
        // Connect directly to FastAPI server on port 8000 (no nginx)
        this.baseUrl = `http://localhost:8000`;
        this.wsUrl = `ws://localhost:8000/ws`;
        
        // Symbol mapping - map ID to symbol name
        this.symbolMap = new Map([
            [50, 'ADAUSDT'],
            [170, 'LTCUSDT'], 
            [258, 'BNBUSDT'],    // Added based on server data
            [290, 'BTCUSDT'],
            [388, 'DOGEUSDT'],
            [469, 'ALGOUSDT'],   // Added based on server data
            [476, 'ETHUSDT'],
            [721, 'AVAXUSDT'],
            [1132, 'SOLUSDT'],
            [1136, 'XRPUSDT'],
            [1178, 'ATOMUSDT'],  // Added based on server data
            [1394, 'INJUSDT']    // Added based on server data
        ]);
        
        console.log('Symbol map initialized:', this.symbolMap);
        
        // Initialize UI elements
        this.tableBody = document.getElementById('tradingTableBody');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectBtn = document.getElementById('connectBtn');
        this.heartbeat = document.getElementById('heartbeat');
        this.heartbeatText = document.getElementById('heartbeatText');
        this.totalMessagesEl = document.getElementById('totalMessages');
        this.dataSourceIndicator = document.getElementById('dataSourceIndicator');
        this.dataSourceText = document.getElementById('dataSourceText');
        
        // Initialize with empty table
        this.updateTable();
        this.updateDataSourceIndicator();
        this.startHeartbeatMonitor();
        

    }
    
    calculateSpread(bid, ask) {
        const spread = ((ask - bid) / bid * 100).toFixed(4);
        return `${spread}%`;
    }
    
    formatBinanceTime(binanceTimeMs) {
        if (!binanceTimeMs) {
            return {
                formatted: 'N/A',
                age: 0,
                isStale: false,
                isFresh: false
            };
        }
        
        const date = new Date(binanceTimeMs);
        const now = Date.now();
        const age = now - binanceTimeMs;
        
        // Format as HH:MM:SS.mmm
        const timeString = date.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        }) + '.' + String(date.getMilliseconds()).padStart(3, '0');
        
        return {
            formatted: timeString,
            age: age,
            isStale: age > 5000, // Consider stale if older than 5 seconds
            isFresh: age < 1000  // Consider fresh if less than 1 second
        };
    }

    formatPrice(price) {
        if (typeof price === 'string') {
            price = parseFloat(price);
        }
        return price.toLocaleString('en-US', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 8 
        });
    }
    
    updateTable() {
        console.log('updateTable() called');
        // Get sorted symbols (alphabetically)
        const sortedSymbols = Array.from(this.data.keys()).sort();
        console.log('Sorted symbols:', sortedSymbols);
        
        if (sortedSymbols.length === 0) {
            console.log('No symbols to display, showing empty message');
            this.tableBody.innerHTML = '<tr><td colspan="8" class="no-data">No trading data available. Click Connect to start receiving data.</td></tr>';
            return;
        }
        
        // Clear existing rows
        this.tableBody.innerHTML = '';
        console.log('Creating', sortedSymbols.length, 'table rows...');
        
        // Create rows in alphabetical order
        sortedSymbols.forEach(symbol => {
            const item = this.data.get(symbol);
            const row = document.createElement('tr');
            
            // Determine price color based on recent changes (if available)
            const priceClass = item.priceChange > 0 ? 'positive' : 
                              item.priceChange < 0 ? 'negative' : '';
            
            // Format Binance time
            const binanceTimeInfo = this.formatBinanceTime(item.binanceTime);
            const binanceTimeClass = binanceTimeInfo.isFresh ? 'binance-time fresh' :
                                   binanceTimeInfo.isStale ? 'binance-time stale' :
                                   'binance-time';
            
            const rowHTML = `
                <td class="symbol">${symbol}</td>
                <td class="price ${priceClass}">${this.formatPrice(item.lastPrice)}</td>
                <td class="price">${this.formatPrice(item.bidPrice)}</td>
                <td class="price">${this.formatPrice(item.askPrice)}</td>
                <td class="spread">${item.spread}</td>
                <td class="message-count">${item.messageCount || 0}</td>
                <td class="${binanceTimeClass}">${binanceTimeInfo.formatted}</td>
                <td class="last-update">${item.lastUpdate}</td>
            `;
            
            console.log(`Creating row for ${symbol}:`, {
                lastPrice: this.formatPrice(item.lastPrice),
                bidPrice: this.formatPrice(item.bidPrice), 
                askPrice: this.formatPrice(item.askPrice),
                messageCount: item.messageCount,
                lastUpdate: item.lastUpdate
            });
            
            row.innerHTML = rowHTML;
            
            this.tableBody.appendChild(row);
        });
    }

    updateMessageCounter() {
        if (this.totalMessagesEl) {
            this.totalMessagesEl.textContent = this.totalMessages;
        }
    }

    updateDataSourceIndicator() {
        if (this.dataSourceText && this.dataSourceIndicator) {
            this.dataSourceText.textContent = this.dataSource;
            
            // Update styling based on data source
            this.dataSourceIndicator.className = 'data-source-indicator';
            if (this.dataSource.includes('Live Binance')) {
                this.dataSourceIndicator.classList.add('live');
            } else if (this.dataSource.includes('Demo') || this.dataSource.includes('Test')) {
                this.dataSourceIndicator.classList.add('demo');
            } else if (this.dataSource === 'unknown' || this.dataSource === 'No Data') {
                this.dataSourceIndicator.classList.add('none');
            }
        }
    }

    startHeartbeatMonitor() {
        this.heartbeatInterval = setInterval(() => {
            const now = Date.now();
            const timeSinceLastMessage = this.lastMessageTime ? now - this.lastMessageTime : null;
            
            if (this.isConnected && timeSinceLastMessage !== null) {
                if (timeSinceLastMessage < 5000) { // Active if message within 5 seconds
                    this.heartbeat.className = 'heartbeat active';
                    this.heartbeatText.textContent = 'Live Data';
                } else if (timeSinceLastMessage < 30000) { // Slow if message within 30 seconds
                    this.heartbeat.className = 'heartbeat';
                    this.heartbeatText.textContent = `${Math.round(timeSinceLastMessage / 1000)}s ago`;
                } else { // Stale if older than 30 seconds
                    this.heartbeat.className = 'heartbeat';
                    this.heartbeatText.textContent = 'Stale Data';
                }
            } else if (this.isConnected) {
                this.heartbeat.className = 'heartbeat';
                this.heartbeatText.textContent = 'Waiting...';
            } else {
                this.heartbeat.className = 'heartbeat';
                this.heartbeatText.textContent = 'No Activity';
            }
        }, 1000);
    }

    recordMessage(symbol) {
        this.totalMessages++;
        this.lastMessageTime = Date.now();
        
        // Increment message counter for this symbol
        const currentCount = this.messageCounters.get(symbol) || 0;
        this.messageCounters.set(symbol, currentCount + 1);
        
        this.updateMessageCounter();
    }
    
    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Try to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.fallbackToHttpPolling();
                    }
                }, 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.fallbackToHttpPolling();
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.fallbackToHttpPolling();
        }
    }
    
    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Handle Binance WebSocket format
            if (message.e === 'bookTicker' && message.s && message.b && message.a) {
                const symbol = message.s;
                const bidPrice = parseFloat(message.b);
                const askPrice = parseFloat(message.a);
                const binanceTime = message.T; // Binance transaction time
                const receiveTime = Date.now(); // Our receive time
                
                // Detect if this is live or test data
                const now = Date.now();
                const dataAge = binanceTime ? now - binanceTime : 0;
                
                // If data is very recent (< 30 seconds), it's likely live
                // If it's older, it's likely test/replay data
                if (dataAge < 30000) {
                    this.dataSource = 'Live Binance';
                } else {
                    this.dataSource = 'Test Data Replay';
                }
                
                // Record the message
                this.recordMessage(symbol);
                
                // Calculate price change if we have previous data
                const previousData = this.data.get(symbol);
                const lastPrice = (bidPrice + askPrice) / 2;
                const priceChange = previousData ? lastPrice - previousData.lastPrice : 0;
                
                this.data.set(symbol, {
                    symbol: symbol,
                    lastPrice: lastPrice,
                    bidPrice: bidPrice,
                    askPrice: askPrice,
                    spread: this.calculateSpread(bidPrice, askPrice),
                    lastUpdate: new Date().toLocaleTimeString(),
                    timestamp: Date.now(),
                    priceChange: priceChange,
                    messageCount: this.messageCounters.get(symbol),
                    binanceTime: binanceTime,
                    receiveTime: receiveTime
                });
                
                this.updateTable();
                this.updateConnectionStatus(this.isConnected, 'WebSocket');
            }
            // Handle array of data (Python server format)
            else if (Array.isArray(message)) {
                // Detect data source based on presence of Binance fields
                let hasValidBinanceTime = false;
                const now = Date.now();
                
                message.forEach(item => {
                    if (item.symbol) {
                        const binanceTime = item.T || item.binanceTime;
                        if (binanceTime) {
                            const dataAge = now - binanceTime;
                            if (dataAge < 30000) {
                                hasValidBinanceTime = true;
                            }
                        }
                    }
                });
                
                // Set data source based on analysis
                if (hasValidBinanceTime) {
                    this.dataSource = 'Live Binance';
                } else if (message.some(item => item.T || item.binanceTime)) {
                    this.dataSource = 'Test Data Replay';
                } else {
                    this.dataSource = 'Server Data';
                }
                
                message.forEach(item => {
                    if (item.symbol) {
                        // Record the message
                        this.recordMessage(item.symbol);
                        
                        const previousData = this.data.get(item.symbol);
                        const priceChange = previousData ? item.price - previousData.lastPrice : 0;
                        const receiveTime = Date.now();
                        
                        this.data.set(item.symbol, {
                            symbol: item.symbol,
                            lastPrice: item.price,
                            bidPrice: item.bid || item.price * 0.9999,
                            askPrice: item.ask || item.price * 1.0001,
                            spread: this.calculateSpread(item.bid || item.price * 0.9999, item.ask || item.price * 1.0001),
                            lastUpdate: new Date().toLocaleTimeString(),
                            timestamp: Date.now(),
                            priceChange: priceChange,
                            messageCount: this.messageCounters.get(item.symbol),
                            binanceTime: item.T || item.binanceTime || null, // Try multiple field names
                            receiveTime: receiveTime
                        });
                    }
                });
                this.updateTable();
                this.updateConnectionStatus(this.isConnected, 'WebSocket');
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    fallbackToHttpPolling() {
        console.log('Falling back to HTTP polling...');
        console.log('Base URL:', this.baseUrl);
        
        const pollData = async () => {
            try {
                console.log('Fetching from:', `${this.baseUrl}/status/latest`);
                const response = await fetch(`${this.baseUrl}/status/latest`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                console.log('Received data:', data.length, 'items');
                
                if (Array.isArray(data)) {
                    console.log('Processing array data, setting data source...');
                    
                    // Check if prices are static by comparing with previous data
                    let hasStaticPrices = false;
                    let activeSymbols = new Set();
                    
                    data.forEach(item => {
                        if (item.id && this.symbolMap.has(item.id)) {
                            const symbol = this.symbolMap.get(item.id);
                            activeSymbols.add(symbol);
                            const previousData = this.data.get(symbol);
                            if (previousData && previousData.bidPrice === item.bid_price && previousData.askPrice === item.ask_price) {
                                hasStaticPrices = true;
                            }
                        }
                    });
                    
                    // Set data source - this is test/demo data from our server
                    if (hasStaticPrices && this.totalMessages > 10) {
                        this.dataSource = `Demo Data (Static Prices) - ${activeSymbols.size} symbols`;
                    } else {
                        this.dataSource = `Demo Data (Test Server) - ${activeSymbols.size} symbols`;
                    }
                    this.updateDataSourceIndicator();
                    
                    console.log('Processing', data.length, 'data items...');
                    data.forEach(item => {
                        if (item.id && this.symbolMap.has(item.id)) {
                            const symbol = this.symbolMap.get(item.id);
                            console.log('Processing item:', item.id, '→', symbol, 'bid:', item.bid_price, 'ask:', item.ask_price);
                            
                            // Record the message
                            this.recordMessage(symbol);
                            
                            const previousData = this.data.get(symbol);
                            const bidPrice = item.bid_price;
                            const askPrice = item.ask_price;
                            const lastPrice = (bidPrice + askPrice) / 2;
                            const priceChange = previousData ? lastPrice - previousData.lastPrice : 0;
                            const receiveTime = Date.now();
                            
                            // Convert nanoseconds to milliseconds for Binance time
                            const binanceTime = item.timestamp_ns ? Math.floor(item.timestamp_ns / 1000000) : null;
                            console.log(`${symbol}: timestamp_ns=${item.timestamp_ns}, binanceTime=${binanceTime}, formatted=${new Date(binanceTime).toLocaleTimeString()}`);
                            
                            // Debug price changes
                            if (previousData) {
                                console.log(`${symbol}: Previous bid=${previousData.bidPrice}, ask=${previousData.askPrice} → New bid=${bidPrice}, ask=${askPrice} (lastPrice change: ${priceChange})`);
                                if (previousData.bidPrice === bidPrice && previousData.askPrice === askPrice) {
                                    console.log(`${symbol}: PRICES ARE IDENTICAL - no change detected`);
                                } else {
                                    console.log(`${symbol}: PRICES CHANGED - bid ${previousData.bidPrice}→${bidPrice}, ask ${previousData.askPrice}→${askPrice}`);
                                }
                            } else {
                                console.log(`${symbol}: First time seeing this symbol, bid=${bidPrice}, ask=${askPrice}, lastPrice=${lastPrice}`);
                            }
                            
                            const newData = {
                                symbol: symbol,
                                lastPrice: lastPrice,
                                bidPrice: bidPrice,
                                askPrice: askPrice,
                                spread: this.calculateSpread(bidPrice, askPrice),
                                lastUpdate: new Date().toLocaleTimeString(),
                                timestamp: Date.now(),
                                priceChange: priceChange,
                                messageCount: this.messageCounters.get(symbol),
                                binanceTime: binanceTime,
                                receiveTime: receiveTime
                            };
                            
                            console.log(`Setting ${symbol} data:`, newData);
                            this.data.set(symbol, newData);
                        } else if (item.id) {
                            console.log('Unknown symbol ID:', item.id, '(not in symbol map)');
                        }
                    });
                    console.log('Data processing complete, updating table...');
                    console.log('Current data map has', this.data.size, 'symbols');
                    console.log('Data map contents:', Array.from(this.data.entries()));
                    
                    // Force table update
                    this.updateTable();
                    this.updateConnectionStatus(true, 'HTTP Polling');
                }
            } catch (error) {
                console.error('HTTP polling failed:', error);
                this.updateConnectionStatus(false, 'Connection Failed');
            }
        };
        
        // Poll every 2 seconds
        this.httpPollingInterval = setInterval(pollData, 2000);
        pollData(); // Poll immediately
    }
    
    updateConnectionStatus(connected, method = 'WebSocket') {
        this.isConnected = connected;
        
        if (connected) {
            this.connectionStatus.className = 'connection-status status-connected';
            
            // Determine data source based on method and message patterns
            let statusText = `Connected (${method})`;
            if (this.dataSource !== 'unknown') {
                statusText += ` - ${this.dataSource}`;
            }
            
            this.connectionStatus.textContent = statusText;
            this.connectBtn.textContent = 'Disconnect';
            this.connectBtn.disabled = false;
        } else {
            this.connectionStatus.className = 'connection-status status-disconnected';
            this.connectionStatus.textContent = 'Disconnected';
            this.connectBtn.textContent = 'Connect';
            this.connectBtn.disabled = false;
            this.dataSource = 'No Services';
            this.updateDataSourceIndicator();
        }
    }
    
    toggleConnection() {
        if (this.isConnected) {
            this.disconnect();
        } else {
            this.connect();
        }
    }
    
    connect() {
        this.connectBtn.disabled = true;
        this.connectBtn.textContent = 'Connecting...';
        
        console.log('Attempting to connect to:', this.baseUrl);
        console.log('Dashboard class connecting...');
        
        // Test if we can reach the HTTP endpoint first
        fetch(`${this.baseUrl}/status/latest`)
            .then(response => {
                console.log('HTTP endpoint reachable, status:', response.status);
                if (response.ok) {
                    console.log('HTTP test successful, starting polling...');
                    // If HTTP works, start polling
                    this.fallbackToHttpPolling();
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            })
            .catch(error => {
                console.error('Failed to connect to server:', error);
                this.updateConnectionStatus(false);
                this.connectBtn.textContent = 'Connect';
                this.connectBtn.disabled = false;
            });
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        if (this.httpPollingInterval) {
            clearInterval(this.httpPollingInterval);
            this.httpPollingInterval = null;
        }
        
        this.updateConnectionStatus(false);
    }
    
    clearData() {
        this.data.clear();
        this.messageCounters.clear();
        this.totalMessages = 0;
        this.lastMessageTime = null;
        this.updateTable();
        this.updateMessageCounter();
        console.log('Data cleared');
    }

}

// Initialize the dashboard when the DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Trading Table Dashboard...');
    dashboard = new TradingTableDashboard();
    console.log('Trading Table Dashboard initialized:', dashboard);
    console.log('Dashboard base URL:', dashboard.baseUrl);
    
    // Auto-connect after initialization
    setTimeout(() => {
        console.log('Auto-connecting dashboard...');
        dashboard.connect();
    }, 1000);
});