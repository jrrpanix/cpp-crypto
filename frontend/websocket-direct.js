// Direct WebSocket Trading Dashboard
class DirectWebSocketDashboard {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.data = new Map();
        this.messageCounters = new Map();
        this.totalMessages = 0;
        this.lastMessageTime = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Connect directly to consumer WebSocket (no FastAPI!)
        this.wsUrl = 'ws://localhost:9001';
        
        // Initialize UI elements
        this.tableBody = document.getElementById('tradingTableBody');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectBtn = document.getElementById('connectBtn');
        this.heartbeat = document.getElementById('heartbeat');
        this.heartbeatText = document.getElementById('heartbeatText');
        this.totalMessagesEl = document.getElementById('totalMessages');
        this.dataSourceText = document.getElementById('dataSourceText');
        
        this.updateTable();
        this.startHeartbeatMonitor();
        
        // Auto-connect after page load
        setTimeout(() => this.connect(), 1000);
    }
    
    calculateSpread(bid, ask) {
        const spread = ((ask - bid) / bid * 100).toFixed(4);
        return `${spread}%`;
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
        const sortedSymbols = Array.from(this.data.keys()).sort();
        
        if (sortedSymbols.length === 0) {
            this.tableBody.innerHTML = '<tr><td colspan="7" class="no-data">No trading data. Click Connect to start receiving data from consumer.</td></tr>';
            return;
        }
        
        this.tableBody.innerHTML = '';
        
        sortedSymbols.forEach(symbol => {
            const item = this.data.get(symbol);
            const row = document.createElement('tr');
            
            const priceClass = item.priceChange > 0 ? 'positive' : 
                              item.priceChange < 0 ? 'negative' : '';
            
            row.innerHTML = `
                <td class="symbol">${symbol}</td>
                <td class="price ${priceClass}">${this.formatPrice(item.lastPrice)}</td>
                <td class="price">${this.formatPrice(item.bidPrice)}</td>
                <td class="price">${this.formatPrice(item.askPrice)}</td>
                <td class="spread">${item.spread}</td>
                <td class="message-count">${item.messageCount || 0}</td>
                <td class="last-update">${item.lastUpdate}</td>
            `;
            
            this.tableBody.appendChild(row);
        });
    }

    updateMessageCounter() {
        if (this.totalMessagesEl) {
            this.totalMessagesEl.textContent = this.totalMessages;
        }
    }

    startHeartbeatMonitor() {
        setInterval(() => {
            const now = Date.now();
            const timeSinceLastMessage = this.lastMessageTime ? now - this.lastMessageTime : null;
            
            if (this.isConnected && timeSinceLastMessage !== null) {
                if (timeSinceLastMessage < 2000) {
                    this.heartbeat.className = 'heartbeat active';
                    this.heartbeatText.textContent = 'Live Data';
                } else if (timeSinceLastMessage < 10000) {
                    this.heartbeat.className = 'heartbeat';
                    this.heartbeatText.textContent = `${Math.round(timeSinceLastMessage / 1000)}s ago`;
                } else {
                    this.heartbeat.className = 'heartbeat';
                    this.heartbeatText.textContent = 'Stale Data';
                }
            } else if (this.isConnected) {
                this.heartbeat.className = 'heartbeat';
                this.heartbeatText.textContent = 'Waiting...';
            } else {
                this.heartbeat.className = 'heartbeat';
                this.heartbeatText.textContent = 'Disconnected';
            }
        }, 1000);
    }

    recordMessage(symbol) {
        this.totalMessages++;
        this.lastMessageTime = Date.now();
        
        const currentCount = this.messageCounters.get(symbol) || 0;
        this.messageCounters.set(symbol, currentCount + 1);
        
        this.updateMessageCounter();
    }
    
    connect() {
        if (this.isConnected) return;
        
        this.connectBtn.disabled = true;
        this.connectBtn.textContent = 'Connecting...';
        
        console.log('Connecting to consumer WebSocket:', this.wsUrl);
        
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ Connected directly to consumer WebSocket');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onclose = (event) => {
                console.log('❌ WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Auto-reconnect with exponential backoff
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.pow(2, this.reconnectAttempts) * 1000; // 1s, 2s, 4s, 8s, 16s
                    console.log(`🔄 Reconnecting in ${delay/1000}s... (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connect();
                    }, delay);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.isConnected = false;
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Handle welcome message
            if (message.type === 'welcome') {
                console.log('📩 Welcome message:', message.message);
                if (this.dataSourceText) {
                    this.dataSourceText.textContent = 'Direct Consumer Connection';
                }
                return;
            }
            
            // Handle BookTicker data
            if (message.e === 'bookTicker' && message.s) {
                const symbol = message.s;
                const bidPrice = parseFloat(message.b);
                const askPrice = parseFloat(message.a);
                
                console.log(`📊 ${symbol}: Bid ${bidPrice}, Ask ${askPrice}`);
                
                this.recordMessage(symbol);
                
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
                    messageCount: this.messageCounters.get(symbol)
                });
                
                this.updateTable();
            }
        } catch (error) {
            console.error('❌ Error parsing message:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        
        if (connected) {
            this.connectionStatus.className = 'connection-status status-connected';
            this.connectionStatus.textContent = 'Connected (Direct WebSocket to Consumer)';
            this.connectBtn.textContent = 'Disconnect';
            this.connectBtn.disabled = false;
        } else {
            this.connectionStatus.className = 'connection-status status-disconnected';
            this.connectionStatus.textContent = 'Disconnected';
            this.connectBtn.textContent = 'Connect';
            this.connectBtn.disabled = false;
        }
    }
    
    toggleConnection() {
        if (this.isConnected) {
            this.disconnect();
        } else {
            this.connect();
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.updateConnectionStatus(false);
    }
    
    clearData() {
        this.data.clear();
        this.messageCounters.clear();
        this.totalMessages = 0;
        this.lastMessageTime = null;
        this.updateTable();
        this.updateMessageCounter();
        console.log('📊 Data cleared');
    }
}

// Initialize the dashboard
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Direct WebSocket Dashboard...');
    dashboard = new DirectWebSocketDashboard();
    console.log('✅ Dashboard ready for direct consumer connection');
});