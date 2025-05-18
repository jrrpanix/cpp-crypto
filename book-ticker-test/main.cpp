#include <ixwebsocket/IXWebSocket.h>
#include <iostream>
#include <chrono>
#include <thread>

int main() {
    ix::WebSocket webSocket;

    // Set the URL for Binance Futures BTCUSDT bookTicker
    webSocket.setUrl("wss://fstream.binance.com/ws/btcusdt@bookTicker");

    // Optional: Enable automatic pong response
    webSocket.setPingInterval(30);  // Send ping every 30 seconds

    webSocket.setOnMessageCallback([](const ix::WebSocketMessagePtr& msg) {
        switch (msg->type) {
            case ix::WebSocketMessageType::Message:
                std::cout << "📩 Received: " << msg->str << std::endl;
                break;

            case ix::WebSocketMessageType::Open:
                std::cout << "✅ Connection opened\n";
                break;

            case ix::WebSocketMessageType::Close:
                std::cout << "❌ Connection closed\n";
                break;

            case ix::WebSocketMessageType::Ping:
                std::cout << "↔️ Ping received\n";
                break;

            case ix::WebSocketMessageType::Pong:
                std::cout << "🏓 Pong received\n";
                break;

            case ix::WebSocketMessageType::Error:
                std::cerr << "❗ Error: " << msg->errorInfo.reason << std::endl;
                break;

            default:
                break;
        }
    });

    webSocket.start();

    // Keep the program alive for testing
    std::this_thread::sleep_for(std::chrono::minutes(5));

    webSocket.stop();
    return 0;
}

