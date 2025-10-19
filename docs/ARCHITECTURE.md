# System Architecture Overview

## Complete Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CRYPTO TRADING & RESEARCH PLATFORM                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          LIVE DATA PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐  │
│  │   BINANCE    │      │  CONSUMER    │      │   WEBSOCKET     │  │
│  │   PRODUCER   │─────▶│   (C++)      │─────▶│   FRONTEND      │  │
│  │   (C++)      │ ZMQ  │              │ WS   │   (Browser)     │  │
│  │              │      │  - Aggregates│      │                 │  │
│  │  - Real-time │      │  - Throttles │      │  - Real-time    │  │
│  │  - WebSocket │      │  - Broadcasts│      │  - Charts       │  │
│  └──────────────┘      └──────────────┘      └─────────────────┘  │
│                                                                       │
│  Test Mode: Port 8082 (mock data, unlimited rate)                   │
│  Live Mode: Port 8083 (real Binance, 20 msg/sec throttle)          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       BACKTEST ANALYSIS SYSTEM                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐  │
│  │   PARQUET    │      │   FLASK      │      │   WEB UI        │  │
│  │   DATA       │─────▶│   API        │─────▶│   (Browser)     │  │
│  │   FILES      │ Read │   (Python)   │ REST │                 │  │
│  │              │      │              │      │  - Form inputs  │  │
│  │  - Historical│      │  window_sim  │      │  - Metrics      │  │
│  │  - OHLCV     │      │  - Simulates │      │  - PnL charts   │  │
│  │  - 1-minute  │      │  - Analyzes  │      │  - Trade tables │  │
│  └──────────────┘      └──────────────┘      └─────────────────┘  │
│                                                                       │
│  Port: 8084                                                          │
│  Strategy: Window-based event detection + position management        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          DATA MANAGEMENT                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐  │
│  │   BINANCE    │      │   DOWNLOAD   │      │   PARQUET       │  │
│  │   API        │─────▶│   SCRIPTS    │─────▶│   STORAGE       │  │
│  │              │ HTTP │   (Python)   │ Write│                 │  │
│  │              │      │              │      │  - Efficient    │  │
│  │  - Monthly   │      │  bootstrap   │      │  - Columnar     │  │
│  │  - Klines    │      │  update      │      │  - Compressed   │  │
│  │  - ZIP files │      │  repair      │      │                 │  │
│  └──────────────┘      └──────────────┘      └─────────────────┘  │
│                                                                       │
│  Tools: bootstrap_klines.py, update_klines.py, get_latest_klines.py│
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Live Data Pipeline (C++)

**Purpose**: Real-time market data streaming and visualization

**Components**:
- `binance_main.cpp`: Connects to Binance WebSocket, receives book ticker updates
- `mock_binance_main.cpp`: Simulates realistic market data for testing
- `consumer_ws_main.cpp`: Aggregates ZMQ messages, broadcasts via WebSocket
- `direct.html` + `websocket-direct.js`: Browser-based real-time dashboard

**Features**:
- Lock-free multi-threading
- ZMQ message passing
- IXWebSocket compression
- Rate limiting (--max-rate, --throttle)
- Live vs Test modes

**Use Cases**:
- Real-time monitoring
- Live trading signal generation
- Market data recording

---

### Backtest Analysis System (Python)

**Purpose**: Historical strategy testing and performance analysis

**Components**:
- `window_sim.py`: Core strategy simulator with event detection
- `backtest_api.py`: Flask REST API for web access
- `backtest.html` + `backtest.js`: Interactive web interface

**Features**:
- Window-based event detection
- Position management (1-2 accounts)
- Comprehensive metrics (Sharpe, drawdown, win rate, etc.)
- Cumulative PnL visualization
- Trade-by-trade analysis

**Use Cases**:
- Strategy development
- Parameter optimization
- Performance validation

---

### Data Management (Python)

**Purpose**: Acquire and maintain historical market data

**Components**:
- `bootstrap_klines.py`: Initial bulk download (13 months)
- `get_latest_klines.py`: Incremental monthly updates
- `update_klines.py`: Process ZIPs into Parquet
- `repair_missing.py`: Fix data gaps

**Features**:
- Efficient Parquet format
- Automatic symbol discovery
- Date range management
- Gap detection and repair

**Use Cases**:
- Building historical database
- Keeping data current
- Data quality assurance

---

## Data Flow

### Real-Time Flow
```
Binance WebSocket → ZMQ Queue → Consumer Aggregation → WebSocket Broadcast → Browser
     (TCP)           (IPC)        (Processing)              (WS)           (Display)
```

### Backtest Flow
```
Parquet Files → Polars DataFrame → Strategy Simulation → Metrics Calculation → JSON Response
   (Storage)      (In-memory)          (window_sim)         (Analysis)        (API)
```

### Data Acquisition Flow
```
Binance API → ZIP Downloads → Extract & Parse → Append to Parquet → Update Date Range
  (HTTP)        (Temp Files)     (Processing)      (Write)           (Metadata)
```

---

## Technology Stack

### C++ Core
- **Language**: C++17
- **Build**: CMake
- **Concurrency**: std::thread, std::mutex
- **Networking**: IXWebSocket, ZMQ (cppzmq)
- **Parsing**: simdjson, fast_float
- **HTTP**: CPR (libcurl wrapper)

### Python Research
- **Language**: Python 3.11+
- **Data**: Polars (primary), Pandas (legacy)
- **Web**: Flask, Flask-CORS
- **Visualization**: Matplotlib
- **Storage**: PyArrow (Parquet)

### Frontend
- **HTML5**: Modern semantic markup
- **CSS3**: Gradients, flexbox, grid
- **JavaScript**: ES6+, Fetch API
- **WebSocket**: Native browser API

### Infrastructure
- **Containers**: Docker, docker-compose
- **Web Server**: Nginx (static files)
- **Build Tool**: Make
- **Version Control**: Git

---

## Port Allocation

| Port | Service | Mode | Description |
|------|---------|------|-------------|
| 8084 | Backtest Webapp | Analysis | Historical backtesting |
| 8082 | WebSocket Frontend | Test | Mock data, unlimited rate |
| 8083 | WebSocket Frontend | Live | Real Binance, throttled |
| 5001 | Flask API | Backend | Backtest computation |
| 9001 | Consumer WebSocket | Internal | Live data broadcast |

---

## Service Architecture

```
Docker Network: realtime-network
├── binance-producer (C++)
├── consumer-websocket (C++)
├── frontend-nginx (static)
└── (ZMQ IPC via volume mount)

Docker Network: backtest-network
├── backtest-api (Python/Flask)
└── backtest-frontend (nginx)

Independent Services:
├── Live WebSocket (8082/8083)
└── Backtest Webapp (8084)
```

---

## Design Principles

### 1. Separation of Concerns
- Real-time processing in C++ (performance)
- Analysis in Python (flexibility)
- UI in browser (accessibility)

### 2. Modularity
- Each component can run independently
- Docker provides isolation
- Clean interfaces (ZMQ, REST, WebSocket)

### 3. Scalability
- Lock-free producer
- Throttled consumer
- Stateless API server

### 4. Developer Experience
- Live code reloading
- Comprehensive documentation
- Simple startup scripts

### 5. Data Efficiency
- Parquet columnar format
- Single file per symbol
- Compressed WebSocket streams

---

## Future Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLANNED ENHANCEMENTS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Strategy Optimization                                               │
│  ├── Grid search across parameters                                  │
│  ├── Walk-forward analysis                                          │
│  └── Monte Carlo simulations                                        │
│                                                                       │
│  Live Trading Integration                                            │
│  ├── Signal generation from backtest strategies                     │
│  ├── Order management system                                        │
│  └── Risk controls and position limits                              │
│                                                                       │
│  Enhanced Analytics                                                  │
│  ├── Multi-symbol portfolio backtests                               │
│  ├── Correlation analysis                                           │
│  └── Advanced visualizations                                        │
│                                                                       │
│  Infrastructure                                                      │
│  ├── Redis for symbol caching                                       │
│  ├── Prometheus metrics                                             │
│  └── Database for trade history                                     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- [Backtest Quick Start](BACKTEST_QUICKSTART.md)
- [Backtest Implementation Details](BACKTEST_WEBAPP_IMPLEMENTATION.md)
- [Python Development Guide](PYTHON_CI_SETUP.md)
- [Code Quality Standards](PYTHON_QUALITY.md)

