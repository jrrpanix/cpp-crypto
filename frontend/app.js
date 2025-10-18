// Simple JavaScript dashboard for crypto trading system
class CryptoDashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
        this.startTime = Date.now();
        
        // Data storage
        this.metrics = {
            activeSymbols: 0,
            messagesPerSec: 0,
            totalMessages: 0,
            uptime: 0
        };
        
        this.recentTrades = [];
        this.priceUpdates = [];
        this.maxHistoryItems = 50;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Crypto Dashboard...');
        this.setupEventListeners();
        this.startMetricsUpdater();
        this.connectWebSocket();
        this.addLog('System initialized', 'info');
    }
    
    setupEventListeners() {
        // Update uptime every second
        setInterval(() => {
            this.updateUptime();
        }, 1000);
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.addLog('Page hidden - pausing updates', 'warning');
            } else {
                this.addLog('Page visible - resuming updates', 'info');
                if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    this.connectWebSocket();
                }
            }
        });

        // Setup collapsible logs
        const logsCard = document.getElementById('logsCard');
        if (logsCard) {
            const header = logsCard.querySelector('h3');
            header.addEventListener('click', () => {
                logsCard.classList.toggle('collapsed');
            });
            // Start collapsed
            logsCard.classList.add('collapsed');
        }
    }
    
    connectWebSocket() {
        try {
            // Try to connect to the server WebSocket endpoint
            // Since we're in a container, try the Python server port (usually 8000)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//localhost:8000/ws`;
            
            this.addLog(`Connecting to WebSocket: ${wsUrl}`, 'info');
            this.updateConnectionStatus('connecting');
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.addLog('WebSocket connected successfully', 'success');
                this.updateConnectionStatus('connected');
                this.reconnectAttempts = 0;
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                    this.addLog(`Error parsing message: ${error.message}`, 'error');
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('❌ WebSocket closed:', event.code, event.reason);
                this.addLog(`WebSocket closed: ${event.reason || 'Connection lost'}`, 'warning');
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.addLog('WebSocket connection error', 'error');
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.addLog(`Failed to create WebSocket: ${error.message}`, 'error');
            this.updateConnectionStatus('error');
            this.fallbackToHttpPolling();
        }
    }
    
    handleWebSocketMessage(data) {
        // Handle structured messages with type
        if (data.type) {
            switch (data.type) {
                case 'metrics':
                    this.updateMetrics(data.payload);
                    break;
                case 'trade':
                    this.addTrade(data.payload);
                    break;
                case 'price':
                    this.addPriceUpdate(data.payload);
                    break;
                case 'log':
                    this.addLog(data.payload.message, data.payload.level);
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
        }
        // Handle direct Binance bookTicker format
        else if (data.e === 'bookTicker') {
            this.addPriceUpdate({
                symbol: data.s || 'Unknown',
                bid_price: parseFloat(data.b),
                ask_price: parseFloat(data.a),
                timestamp: data.E || Date.now()
            });
        }
        // Handle Python server StatusMessage format
        else if (data.consumer_id && (data.bid_price !== undefined || data.ask_price !== undefined)) {
            this.addPriceUpdate({
                symbol: data.consumer_id,
                bid_price: data.bid_price,
                ask_price: data.ask_price,
                timestamp: data.timestamp_ns ? data.timestamp_ns / 1000000 : Date.now()
            });
        }
        else {
            console.log('Unknown message format:', data);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * this.reconnectAttempts;
            
            this.addLog(`Attempting to reconnect in ${delay/1000}s (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'warning');
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            this.addLog('Max reconnection attempts reached. Falling back to HTTP polling.', 'error');
            this.fallbackToHttpPolling();
        }
    }
    
    fallbackToHttpPolling() {
        this.addLog('Starting HTTP polling fallback', 'info');
        
        // Poll the server for data every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch('http://localhost:8000/status/latest');
                if (response.ok) {
                    const messages = await response.json();
                    
                    // Convert server messages to frontend format
                    messages.forEach(msg => {
                        // Handle both Python server format AND original Binance format
                        let priceUpdate;
                        
                        if (msg.e === 'bookTicker') {
                            // Original Binance WebSocket format
                            priceUpdate = {
                                symbol: msg.s || 'Unknown',
                                bid_price: parseFloat(msg.b),
                                ask_price: parseFloat(msg.a),
                                timestamp: msg.E || Date.now()
                            };
                        } else {
                            // Python server format
                            priceUpdate = {
                                symbol: msg.consumer_id || 'Unknown',
                                bid_price: msg.bid_price,
                                ask_price: msg.ask_price,
                                timestamp: msg.timestamp_ns ? msg.timestamp_ns / 1000000 : Date.now()
                            };
                        }
                        
                        this.addPriceUpdate(priceUpdate);
                    });
                    
                    // Update metrics based on received data
                    this.updateMetrics({
                        activeSymbols: new Set(messages.map(m => m.consumer_id)).size,
                        messagesPerSec: messages.length > 0 ? Math.floor(messages.length / 5) : 0,
                        totalMessages: (this.metrics.totalMessages || 0) + messages.length
                    });
                }
            } catch (error) {
                console.error('HTTP polling error:', error);
                this.addLog(`HTTP polling failed: ${error.message}`, 'error');
            }
        }, 5000);
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        const dotElement = statusElement.querySelector('.status-dot');
        const textElement = statusElement.querySelector('.status-text');
        
        // Remove all status classes
        dotElement.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                dotElement.classList.add('connected');
                textElement.textContent = 'Connected';
                break;
            case 'connecting':
                dotElement.classList.add('connecting');
                textElement.textContent = 'Connecting...';
                break;
            case 'disconnected':
                textElement.textContent = 'Disconnected';
                break;
            case 'error':
                textElement.textContent = 'Connection Error';
                break;
        }
    }
    
    updateMetrics(newMetrics) {
        this.metrics = { ...this.metrics, ...newMetrics };
        
        document.getElementById('activeSymbols').textContent = this.metrics.activeSymbols || '-';
        document.getElementById('messagesPerSec').textContent = this.metrics.messagesPerSec || '-';
        document.getElementById('totalMessages').textContent = this.formatNumber(this.metrics.totalMessages || 0);
    }
    
    updateUptime() {
        const uptimeMs = Date.now() - this.startTime;
        const uptimeText = this.formatUptime(uptimeMs);
        document.getElementById('uptime').textContent = uptimeText;
    }
    
    addTrade(trade) {
        this.recentTrades.unshift(trade);
        if (this.recentTrades.length > this.maxHistoryItems) {
            this.recentTrades = this.recentTrades.slice(0, this.maxHistoryItems);
        }
        this.updateTradesDisplay();
    }
    
    addPriceUpdate(price) {
        this.priceUpdates.unshift(price);
        if (this.priceUpdates.length > this.maxHistoryItems) {
            this.priceUpdates = this.priceUpdates.slice(0, this.maxHistoryItems);
        }
        this.updatePricesDisplay();
    }
    
    updateTradesDisplay() {
        const container = document.getElementById('recentTrades');
        
        if (this.recentTrades.length === 0) {
            container.innerHTML = '<div class="loading">No trades yet...</div>';
            return;
        }
        
        const html = this.recentTrades.map(trade => `
            <div class="trade-item slide-in">
                <div class="symbol">${trade.symbol || 'N/A'}</div>
                <div class="price">$${this.formatPrice(trade.price || 0)}</div>
                <div class="time">${this.formatTime(trade.timestamp || Date.now())}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    updatePricesDisplay() {
        const container = document.getElementById('priceUpdates');
        
        if (this.priceUpdates.length === 0) {
            container.innerHTML = '<div class="loading">No price updates yet...</div>';
            return;
        }
        
        const html = this.priceUpdates.map(price => `
            <div class="price-item slide-in">
                <div class="symbol">${price.symbol || 'N/A'}</div>
                <div class="price-container">
                    ${price.bid_price ? `<div class="bid-price">Bid: $${this.formatPrice(price.bid_price)}</div>` : ''}
                    ${price.ask_price ? `<div class="ask-price">Ask: $${this.formatPrice(price.ask_price)}</div>` : ''}
                    ${(!price.bid_price && !price.ask_price && price.price) ? `<div class="single-price">$${this.formatPrice(price.price)}</div>` : ''}
                </div>
                <div class="time">${this.formatTime(price.timestamp || Date.now())}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    addLog(message, level = 'info') {
        const container = document.getElementById('systemLogs');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level} slide-in`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        container.insertBefore(logEntry, container.firstChild);
        
        // Keep only last 100 log entries
        const logEntries = container.querySelectorAll('.log-entry');
        if (logEntries.length > 100) {
            for (let i = 100; i < logEntries.length; i++) {
                logEntries[i].remove();
            }
        }
        
        console.log(`[${level.toUpperCase()}] ${message}`);
    }
    
    startMetricsUpdater() {
        // Generate some demo data if no real data is coming in
        setTimeout(() => {
            if (this.metrics.totalMessages === 0) {
                this.addLog('No live data detected, generating demo data...', 'warning');
                this.generateDemoData();
            }
        }, 10000);
    }
    
    generateDemoData() {
        // Realistic price ranges for each symbol
        const symbolPrices = {
            'BTCUSDT': { base: 43000, range: 4000 },    // BTC: $43k-47k
            'ETHUSDT': { base: 2200, range: 300 },      // ETH: $2.2k-2.5k
            'ADAUSDT': { base: 0.35, range: 0.1 },      // ADA: $0.35-0.45
            'DOTUSDT': { base: 4.5, range: 1.0 },       // DOT: $4.5-5.5
            'LINKUSDT': { base: 11, range: 2 }          // LINK: $11-13
        };
        
        setInterval(() => {
            // Pick a random symbol
            const symbols = Object.keys(symbolPrices);
            const symbol = symbols[Math.floor(Math.random() * symbols.length)];
            const priceConfig = symbolPrices[symbol];
            
            // Generate realistic price for this symbol
            const basePrice = priceConfig.base + (Math.random() * priceConfig.range);
            const spread = basePrice * 0.001; // 0.1% spread
            
            // Generate fake trade
            const trade = {
                symbol: symbol,
                price: basePrice + (Math.random() - 0.5) * spread * 2,
                timestamp: Date.now()
            };
            this.addTrade(trade);
            
            // Generate fake price update with bid/ask
            const price = {
                symbol: symbol,
                bid_price: basePrice - spread/2,
                ask_price: basePrice + spread/2,
                timestamp: Date.now()
            };
            this.addPriceUpdate(price);
            
            // Update metrics
            this.updateMetrics({
                activeSymbols: symbols.length,
                messagesPerSec: Math.floor(Math.random() * 100) + 10,
                totalMessages: (this.metrics.totalMessages || 0) + Math.floor(Math.random() * 50) + 1
            });
        }, 2000);
    }
    
    // Utility functions
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    formatPrice(price) {
        const num = parseFloat(price);
        if (isNaN(num)) return '0.00';
        
        // Format with appropriate decimal places and commas
        if (num >= 1000) {
            return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        } else if (num >= 1) {
            return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
        } else {
            return num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 6 });
        }
    }
    
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    formatUptime(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days}d ${hours % 24}h`;
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOM loaded, starting dashboard...');
    new CryptoDashboard();
});

// Add some global error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});