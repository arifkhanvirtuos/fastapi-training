# WebSocket Implementation Guide

## 📚 Overview

This implementation adds comprehensive WebSocket support to the FastAPI application, enabling real-time bidirectional communication between clients and the server.

## 🚀 Quick Start

### 1. Start the Server

```bash
cd sql_app
uvicorn main:app --reload
```

### 2. Access the Test Interface

Open your browser to: **http://localhost:8000/websocket-test**

### 3. Test the Echo Server

1. Enter a Client ID (e.g., `1`)
2. Click **Connect**
3. Type a message and click **Send Message**
4. Watch the echo and broadcast features in action!

## 📡 Available WebSocket Endpoints

### 1. Echo Endpoint with Broadcasting

**URL:** `ws://localhost:8000/ws/echo/{client_id}`

**Features:**

- Echoes back all received messages
- Broadcasts messages to all connected clients
- Shows join/leave notifications

**Example Usage:**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/echo/1");

ws.onopen = () => console.log("Connected!");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};
ws.send("Hello, Server!");
```

### 2. Chat Room Endpoint

**URL:** `ws://localhost:8000/ws/chat/{room_id}/{username}`

**Features:**

- Room-based messaging
- User identification
- Join/leave notifications
- Supports both text and JSON messages

**Example Usage:**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat/general/John");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.username}: ${data.content}`);
};

// Send plain text
ws.send("Hello, room!");

// Send JSON
ws.send(
  JSON.stringify({
    type: "chat",
    content: "Hello with JSON!",
  }),
);
```

### 3. Statistics Endpoint

**URL:** `GET http://localhost:8000/ws/stats`

**Returns:** Current WebSocket connection statistics

**Example Response:**

```json
{
  "active_connections": 3,
  "clients": [
    { "client_id": "1", "connected_at": "2026-02-03T10:30:00Z" },
    { "client_id": "2", "connected_at": "2026-02-03T10:31:00Z" }
  ],
  "timestamp": "2026-02-03T10:35:00Z"
}
```

## 🏗️ Architecture

### Connection Manager

The `ConnectionManager` class handles all WebSocket connections:

```python
class ConnectionManager:
    - active_connections: List[WebSocket]  # All active connections
    - client_info: dict                    # Client metadata

    Methods:
    - connect(websocket, client_id)        # Accept new connection
    - disconnect(websocket)                # Remove connection
    - send_personal_message()              # Send to one client
    - send_personal_json()                 # Send JSON to one client
    - broadcast()                          # Send to all clients
    - broadcast_json()                     # Send JSON to all clients
    - get_connection_count()               # Count active connections
```

### Message Flow

```
1. Client connects → Server accepts → Connection added to manager
2. Client sends message → Server receives → Process message
3. Server sends response:
   - Personal message (echo back to sender)
   - Broadcast message (to all other clients)
4. Client disconnects → Server cleans up → Notifies others
```

## 🔧 Implementation Details

### Message Types

The implementation uses JSON messages with type fields:

```json
{
  "type": "echo|broadcast|join|leave|chat|system",
  "message": "Message content",
  "client_id": 1,
  "timestamp": "2026-02-03T10:30:00Z"
}
```

### Error Handling

- Automatic cleanup of disconnected clients
- Exception handling for send failures
- Graceful handling of malformed JSON
- WebSocketDisconnect exception catching

### Features Implemented

✅ **Basic Echo Server** - Echoes back all received messages  
✅ **Broadcasting** - Send messages to all connected clients  
✅ **Connection Manager** - Centralized connection handling  
✅ **Multiple Endpoints** - Echo, chat room, and authenticated endpoints  
✅ **Client Tracking** - Track client IDs and connection times  
✅ **HTML Test Interface** - Beautiful web UI for testing  
✅ **Statistics Endpoint** - Monitor active connections  
✅ **Room-based Chat** - Support for multiple chat rooms  
✅ **Timestamps** - All messages include UTC timestamps  
✅ **Graceful Disconnection** - Proper cleanup on disconnect

## 🎨 HTML Test Interface Features

The test page at `/websocket-test` includes:

- ✅ Connection status indicator
- ✅ Connect/disconnect buttons
- ✅ Message input with Enter key support
- ✅ Real-time message display
- ✅ Message type indicators (sent, received, broadcast)
- ✅ Statistics (sent count, received count, connection time)
- ✅ Beautiful gradient design
- ✅ Animated message additions
- ✅ Auto-scrolling message area

## 📝 Code Examples

### Python Client

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/echo/123"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send("Hello, Server!")

        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Received: {data}")

asyncio.run(test_websocket())
```

### JavaScript Client (Browser)

```javascript
// Connect
const ws = new WebSocket("ws://localhost:8000/ws/echo/1");

// Handle connection open
ws.onopen = () => {
  console.log("Connected to WebSocket");
  ws.send("Hello!");
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "echo") {
    console.log("Echo:", data.message);
  } else if (data.type === "broadcast") {
    console.log("Broadcast:", data.message);
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// Handle disconnection
ws.onclose = () => {
  console.log("Disconnected from WebSocket");
};
```

### Multiple Clients Demo

Open multiple browser tabs to see broadcasting in action:

1. Tab 1: Connect as Client #1
2. Tab 2: Connect as Client #2
3. Tab 1: Send "Hello from Client 1"
4. Tab 2: See the broadcast message appear!

## 🧪 Testing

### Manual Testing

1. **Single Client Echo:**
   - Connect with client ID `1`
   - Send: "Test message"
   - Expect: Echo response

2. **Multi-Client Broadcasting:**
   - Open 2+ browser tabs
   - Connect each with different client IDs
   - Send message from one client
   - Verify all other clients receive broadcast

3. **Chat Room:**
   - Connect to `/ws/chat/general/Alice`
   - Connect to `/ws/chat/general/Bob`
   - Send messages between Alice and Bob

### Automated Testing

```python
import pytest
from fastapi.testclient import TestClient
from main import app

def test_websocket_echo():
    client = TestClient(app)

    with client.websocket_connect("/ws/echo/1") as websocket:
        websocket.send_text("Hello")
        data = websocket.receive_json()

        assert data["type"] == "echo"
        assert "Hello" in data["message"]
```

## 🔐 Security Considerations

### Current Implementation

- Basic connection tracking
- No authentication required for echo/chat endpoints

### Production Recommendations

1. **Add Authentication:**

   ```python
   @app.websocket("/ws/secure")
   async def secure_endpoint(websocket: WebSocket):
       token = websocket.query_params.get("token")
       if not validate_token(token):
           await websocket.close(code=1008)
           return
       await websocket.accept()
   ```

2. **Rate Limiting:**

   ```python
   # Limit messages per client
   MAX_MESSAGES_PER_MINUTE = 60
   ```

3. **Connection Limits:**

   ```python
   MAX_CONNECTIONS = 100
   if len(active_connections) >= MAX_CONNECTIONS:
       await websocket.close(code=1013)
   ```

4. **Input Validation:**
   - Validate message size
   - Sanitize message content
   - Prevent injection attacks

5. **Use WSS (WebSocket Secure):**
   - Deploy with TLS/SSL
   - Use `wss://` instead of `ws://`

## 📊 Performance Considerations

### Current Setup

- Single server instance
- In-memory connection storage
- No persistence

### Scaling Recommendations

1. **Horizontal Scaling:**
   - Use Redis for pub/sub across servers
   - Share connection state

2. **Load Balancing:**
   - Use sticky sessions
   - Or implement reconnection logic

3. **Message Queue:**
   - Offload message processing
   - Use Celery or similar

## 🐛 Troubleshooting

### Connection Refused

- Ensure server is running on port 8000
- Check firewall settings
- Verify URL is correct (`ws://` not `wss://`)

### Messages Not Broadcasting

- Check all clients are connected
- Verify Connection Manager is working
- Check server logs for errors

### Disconnection Issues

- Check network stability
- Implement reconnection logic in client
- Add heartbeat/ping mechanism

## 📚 Further Learning

### Topics to Explore

1. WebSocket authentication with JWT
2. Room-based messaging with Redis
3. Presence detection (who's online)
4. Typing indicators
5. Read receipts
6. File sharing over WebSockets
7. Video/audio streaming
8. WebRTC integration

### Resources

- [FastAPI WebSocket Docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [RFC 6455 - WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 🎯 Practice Assignments

### Assignment 1: Add Typing Indicator

Implement "User is typing..." functionality

### Assignment 2: Private Messages

Add ability to send messages to specific clients

### Assignment 3: Message History

Store and retrieve chat history from database

### Assignment 4: User Presence

Show list of currently connected users

### Assignment 5: File Upload

Enable file sharing through WebSockets

## 📞 Support

For questions or issues:

1. Check the main WebSocket lecture: `WEBSOCKET_LECTURE.md`
2. Review FastAPI documentation
3. Test with the provided HTML interface
4. Check server logs for errors

---

**Created:** February 3, 2026  
**Version:** 1.0  
**Status:** Production-ready for learning and development
