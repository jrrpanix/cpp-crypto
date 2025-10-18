# Simple Frontend

This is a lightweight, vanilla JavaScript frontend for the crypto trading system. No complex frameworks, no build steps - just simple HTML, CSS, and JavaScript.

## Features

- **Real-time Dashboard**: WebSocket connection with fallback to HTTP polling
- **Responsive Design**: Works on desktop and mobile
- **Modern UI**: Clean, dark theme with animations
- **No Dependencies**: Pure vanilla JavaScript, no React complexity
- **Easy to Maintain**: Simple file structure, easy to understand

## File Structure

```
frontend/
├── index.html      # Main HTML file
├── styles.css      # All CSS styles
├── app.js         # JavaScript functionality
└── README.md      # This file
```

## How to Use

1. **Development**: Simply open `index.html` in a browser or serve via the Python server
2. **Production**: Serve the files through any web server

## Features

### Dashboard Metrics
- Active symbols count
- Messages per second
- Total messages processed
- System uptime

### Real-time Data
- Recent trades display
- Price updates
- System logs with different severity levels

### Connection Management
- WebSocket connection with automatic reconnection
- Fallback to HTTP polling if WebSocket fails
- Connection status indicator

## API Integration

The frontend expects the following endpoints:

- `WebSocket: /ws` - Real-time data stream
- `HTTP: /api/status` - Fallback polling endpoint

### WebSocket Message Format

```json
{
  "type": "metrics|trade|price|log",
  "payload": { ... }
}
```

## Customization

The design is easily customizable through CSS variables and the modular JavaScript structure. No complex build process needed - just edit the files directly.

## Why This Approach?

- **Simplicity**: No complex frameworks to learn or debug
- **Performance**: Lightweight, fast loading
- **Maintainability**: Easy to understand and modify
- **Reliability**: Fewer dependencies = fewer things that can break
- **Flexibility**: Easy to add new features or modify existing ones