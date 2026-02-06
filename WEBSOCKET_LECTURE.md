# WebSocket Lecture: Comprehensive Guide to Real-Time Communication

**Duration:** 1 hour  
**Date:** February 3, 2026  
**Level:** Intermediate  
**Prerequisites:** Basic Python, FastAPI fundamentals, HTTP protocol understanding

## 📋 Agenda (60 Minutes)

- **00:00-00:05** | Introduction to Real-Time Communication (5 minutes)
- **00:05-00:15** | WebSocket Protocol Basics (10 minutes)
- **00:15-00:25** | FastAPI WebSocket Support & Setup (10 minutes)
- **00:25-00:35** | Creating WebSocket Endpoints (10 minutes)
- **00:35-00:45** | Accepting Connections & Authentication (10 minutes)
- **00:45-00:55** | Sending/Receiving Messages & Broadcasting (10 minutes)
- **00:55-00:58** | Key Takeaways & Best Practices (3 minutes)
- **00:58-01:00** | Practice Assignment Overview (2 minutes)

---

## 🎯 Introduction to Real-Time Communication (00:00-00:05)

### The Need for Real-Time Communication

Traditional HTTP follows a request-response pattern:

- Client asks → Server responds → Connection closes
- For real-time updates, client must repeatedly ask (polling)
- Inefficient for chat apps, live feeds, gaming, collaborative tools

### Real-Time Communication Solutions

1. **HTTP Polling** - Client repeatedly requests updates (inefficient)
2. **Long Polling** - Server holds request until data available (better, but still overhead)
3. **Server-Sent Events (SSE)** - One-way server → client stream
4. **WebSockets** - Full bidirectional persistent connection ✅

### What We'll Build Today

By the end of this lecture, you'll be able to:

- Understand WebSocket protocol fundamentals
- Create WebSocket endpoints in FastAPI
- Handle multiple concurrent connections
- Build a complete echo server with broadcasting
- Implement authentication for WebSocket connections

---

## 🌐 WebSocket Protocol Basics (00:05-00:15)

### What is WebSocket?

WebSocket (RFC 6455) is a communication protocol providing **full-duplex** communication channels over a **single TCP connection**.

**Key Differences from HTTP:**

| Feature    | HTTP                       | WebSocket             |
| ---------- | -------------------------- | --------------------- |
| Connection | Request-Response           | Persistent            |
| Direction  | One-way                    | Bidirectional         |
| Overhead   | High (headers per request) | Low (after handshake) |
| Real-time  | No (polling needed)        | Yes (native)          |
| Latency    | Higher                     | Lower                 |

### The WebSocket Handshake

WebSocket starts as HTTP, then "upgrades" to WebSocket protocol.

**Client Request:**

```http
GET /ws HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: http://example.com
```

**Server Response:**

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

The status code **101** means "Switching Protocols" - connection upgraded to WebSocket!

### WebSocket Frame Structure

After handshake, data is sent in **frames**:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
```

**Frame Types (Opcodes):**

- `0x0` - Continuation frame
- `0x1` - Text frame (UTF-8)
- `0x2` - Binary frame
- `0x8` - Connection close
- `0x9` - Ping
- `0xA` - Pong

### Message Types

**Text Messages:**

```javascript
// Client-side JavaScript
websocket.send("Hello, Server!");
```

**JSON Messages:**

```javascript
websocket.send(
  JSON.stringify({
    type: "message",
    content: "Hello",
    timestamp: Date.now(),
  }),
);
```

**Binary Messages:**

```javascript
const buffer = new ArrayBuffer(8);
websocket.send(buffer);
```

### Connection Lifecycle

```
1. Client initiates HTTP connection
2. HTTP upgrade request sent
3. Server accepts upgrade (101 response)
4. Connection upgraded to WebSocket
5. Bidirectional message exchange
6. Connection close (either side initiates)
```

### Closing Connections

**Close Frame Codes:**

- `1000` - Normal closure
- `1001` - Going away (e.g., server shutdown)
- `1002` - Protocol error
- `1003` - Unsupported data type
- `1006` - Abnormal closure (no close frame)
- `1008` - Policy violation
- `1009` - Message too big
- `1011` - Server error

### WebSocket URLs

- **Secure:** `wss://example.com/ws` (over TLS, like HTTPS)
- **Insecure:** `ws://example.com/ws` (like HTTP)

**Best Practice:** Always use `wss://` in production!

---

## 🚀 FastAPI WebSocket Support & Setup (00:15-00:25)

### FastAPI's WebSocket Foundation

FastAPI is built on **Starlette**, which provides robust WebSocket support. This means:

- Asynchronous WebSocket handling
- Native Python async/await syntax
- Excellent performance
- Clean, intuitive API

### Installation Requirements

```bash
# FastAPI with WebSocket support
pip install fastapi[all]

# Or separately
pip install fastapi uvicorn websockets
```

### Essential Imports

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
import json
```

**Key Classes:**

- `WebSocket` - Represents a WebSocket connection
- `WebSocketDisconnect` - Exception raised when client disconnects
- `HTMLResponse` - For serving test HTML pages

### Basic Application Structure

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# HTTP endpoint (for serving HTML test page)
@app.get("/")
async def get():
    return HTMLResponse(content="<h1>WebSocket Server</h1>", status_code=200)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Handle messages here
```

### Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### WebSocket Connection Manager Pattern

For managing multiple connections, use the **Connection Manager** pattern:

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Global instance
manager = ConnectionManager()
```

**Why Use a Connection Manager?**

- Centralized connection tracking
- Easy broadcasting to all clients
- Simplified cleanup on disconnect
- Room/channel management capability

### Testing WebSocket Connections

**Option 1: Browser JavaScript**

```html
<!DOCTYPE html>
<html>
  <head>
    <title>WebSocket Test</title>
  </head>
  <body>
    <script>
      const ws = new WebSocket("ws://localhost:8000/ws");

      ws.onopen = () => console.log("Connected!");
      ws.onmessage = (event) => console.log("Message:", event.data);
      ws.onerror = (error) => console.error("Error:", error);
      ws.onclose = () => console.log("Disconnected");

      // Send message
      ws.send("Hello, Server!");
    </script>
  </body>
</html>
```

**Option 2: Python Client**

```python
import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello, Server!")
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

**Option 3: Browser DevTools Console**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (e) => console.log(e.data);
ws.send("Test message");
```

---

## 🔌 Creating WebSocket Endpoints (00:25-00:35)

### Basic WebSocket Endpoint

The `@app.websocket()` decorator creates a WebSocket route:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Send response back
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        print("Client disconnected")
```

### Path Parameters

WebSocket endpoints support path parameters:

```python
@app.websocket("/ws/{client_id}")
async def websocket_with_id(websocket: WebSocket, client_id: int):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Client {client_id} says: {data}")

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
```

**Usage:** `ws://localhost:8000/ws/123`

### Query Parameters

Access query parameters via `websocket.query_params`:

```python
@app.websocket("/ws")
async def websocket_with_query(websocket: WebSocket):
    # Get query parameter
    token = websocket.query_params.get("token")
    username = websocket.query_params.get("username", "Anonymous")

    if not token:
        await websocket.close(code=1008)  # Policy violation
        return

    await websocket.accept()
    await websocket.send_text(f"Welcome, {username}!")
```

**Usage:** `ws://localhost:8000/ws?token=abc123&username=John`

### Headers Access

Read request headers for authentication:

```python
@app.websocket("/ws")
async def websocket_with_headers(websocket: WebSocket):
    # Access headers
    auth_header = websocket.headers.get("Authorization")
    user_agent = websocket.headers.get("User-Agent")

    print(f"User-Agent: {user_agent}")

    await websocket.accept()
```

### Multiple WebSocket Endpoints

Organize different functionality into separate endpoints:

```python
# Chat endpoint
@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(f"Chat: {message}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Notification endpoint
@app.websocket("/ws/notifications")
async def notification_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send periodic notifications
            await asyncio.sleep(10)
            await websocket.send_json({
                "type": "notification",
                "message": "You have new updates!"
            })
    except WebSocketDisconnect:
        print("Notification client disconnected")

# Real-time data feed
@app.websocket("/ws/feed")
async def feed_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Stream data
            data = get_real_time_data()  # Your data source
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Feed client disconnected")
```

### Dependency Injection with WebSockets

FastAPI's dependency injection works with WebSockets:

```python
from fastapi import Depends
from sqlalchemy.orm import Session

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.websocket("/ws/chat/{room_id}")
async def chat_room(
    websocket: WebSocket,
    room_id: int,
    db: Session = Depends(get_db)
):
    await websocket.accept()

    # Use database
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        await websocket.close(code=1003)
        return

    try:
        while True:
            message = await websocket.receive_text()
            # Save message to database
            save_message(db, room_id, message)
            await websocket.send_text(f"Saved to room {room.name}")

    except WebSocketDisconnect:
        print(f"Client left room {room_id}")
```

### Error Handling

Implement robust error handling:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
    except Exception as e:
        print(f"Failed to accept connection: {e}")
        return

    try:
        while True:
            try:
                data = await websocket.receive_text()
                # Process data
                result = process_message(data)
                await websocket.send_text(result)

            except json.JSONDecodeError:
                await websocket.send_text("Error: Invalid JSON")

            except ValueError as e:
                await websocket.send_text(f"Error: {str(e)}")

    except WebSocketDisconnect:
        print("Connection closed normally")

    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close(code=1011)
```

---

## 🔐 Accepting Connections & Authentication (00:35-00:45)

### Connection Acceptance

Every WebSocket connection **must** be explicitly accepted:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # REQUIRED: Accept the connection
    await websocket.accept()

    # Now connection is established
    await websocket.send_text("Connected!")
```

**Without `accept()`, the client cannot communicate!**

### Subprotocol Negotiation

WebSocket subprotocols allow different message formats:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Client can request subprotocols
    requested_subprotocols = websocket.headers.get("Sec-WebSocket-Protocol", "").split(",")

    # Accept with specific subprotocol
    if "chat" in requested_subprotocols:
        await websocket.accept(subprotocol="chat")
    else:
        await websocket.accept()
```

**Client-side:**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws", ["chat", "json"]);
```

### Authentication Before Accepting

**Method 1: Query Parameter Token**

```python
from jose import jwt, JWTError

async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Get token from query parameter
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    user_data = await verify_token(token)
    if not user_data:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Token valid - accept connection
    await websocket.accept()
    await websocket.send_text(f"Welcome, {user_data['username']}!")
```

**Client-side:**

```javascript
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
```

**Method 2: Cookie-based Authentication**

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Get cookie
    cookies = websocket.cookies
    session_id = cookies.get("session_id")

    if not session_id or not validate_session(session_id):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
```

**Method 3: Header-based Authentication**

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Get Authorization header
    auth_header = websocket.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=1008, reason="Missing authorization")
        return

    token = auth_header.split(" ")[1]
    user = await authenticate_token(token)

    if not user:
        await websocket.close(code=1008, reason="Invalid credentials")
        return

    await websocket.accept()
```

### Connection Limits & Rate Limiting

Prevent resource exhaustion:

```python
class ConnectionManager:
    def __init__(self, max_connections: int = 100):
        self.active_connections: List[WebSocket] = []
        self.max_connections = max_connections

    async def connect(self, websocket: WebSocket) -> bool:
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Server at capacity")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager(max_connections=50)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not await manager.connect(websocket):
        return

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### IP-based Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_connections_per_ip: int = 5):
        self.connections_per_ip = defaultdict(list)
        self.max_per_ip = max_connections_per_ip

    def can_connect(self, client_ip: str) -> bool:
        # Clean old connections
        cutoff = datetime.now() - timedelta(minutes=5)
        self.connections_per_ip[client_ip] = [
            conn for conn in self.connections_per_ip[client_ip]
            if conn > cutoff
        ]

        # Check limit
        if len(self.connections_per_ip[client_ip]) >= self.max_per_ip:
            return False

        self.connections_per_ip[client_ip].append(datetime.now())
        return True

rate_limiter = RateLimiter(max_connections_per_ip=3)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host

    if not rate_limiter.can_connect(client_ip):
        await websocket.close(code=1008, reason="Too many connections")
        return

    await websocket.accept()
```

### Graceful Connection Rejection

Always provide clear reasons when rejecting:

```python
@app.websocket("/ws/{room_id}")
async def join_room(websocket: WebSocket, room_id: int, db: Session = Depends(get_db)):
    # Validate room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=1003, reason=f"Room {room_id} not found")
        return

    # Check room capacity
    if room.is_full():
        await websocket.close(code=1013, reason="Room is full")
        return

    # Check permissions
    user_token = websocket.query_params.get("token")
    if not has_room_access(user_token, room_id):
        await websocket.close(code=1008, reason="Access denied")
        return

    # All checks passed - accept connection
    await websocket.accept()
    await websocket.send_json({
        "type": "welcome",
        "room": room.name,
        "members": room.member_count
    })
```

---

## 💬 Sending/Receiving Messages & Broadcasting (00:45-00:55)

### Receiving Messages

**Text Messages:**

```python
# Simple text
data = await websocket.receive_text()
print(f"Received: {data}")
```

**JSON Messages:**

```python
# Automatically parsed as dict
data = await websocket.receive_json()
print(f"Type: {data['type']}, Content: {data['content']}")
```

**Binary Data:**

```python
# Receive bytes
data = await websocket.receive_bytes()
print(f"Received {len(data)} bytes")
```

**Generic Receive (any type):**

```python
message = await websocket.receive()

if message["type"] == "websocket.receive":
    if "text" in message:
        text_data = message["text"]
    elif "bytes" in message:
        binary_data = message["bytes"]
elif message["type"] == "websocket.disconnect":
    print("Client disconnected")
```

### Sending Messages

**Text Messages:**

```python
await websocket.send_text("Hello, client!")
```

**JSON Messages:**

```python
await websocket.send_json({
    "type": "notification",
    "message": "New update available",
    "timestamp": datetime.now().isoformat()
})
```

**Binary Messages:**

```python
binary_data = b"\x00\x01\x02\x03"
await websocket.send_bytes(binary_data)
```

### Complete Echo Server Example

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Echo</title>
</head>
<body>
    <h1>WebSocket Echo Test</h1>
    <input id="messageInput" type="text" placeholder="Enter message">
    <button onclick="sendMessage()">Send</button>
    <button onclick="connect()">Connect</button>
    <button onclick="disconnect()">Disconnect</button>
    <div id="messages"></div>

    <script>
        let ws = null;

        function connect() {
            ws = new WebSocket("ws://localhost:8000/ws");

            ws.onopen = function() {
                addMessage("✅ Connected to server");
            };

            ws.onmessage = function(event) {
                addMessage("📩 " + event.data);
            };

            ws.onclose = function() {
                addMessage("❌ Disconnected from server");
            };

            ws.onerror = function(error) {
                addMessage("⚠️ Error: " + error);
            };
        }

        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }

        function sendMessage() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert("Not connected!");
                return;
            }

            const input = document.getElementById("messageInput");
            ws.send(input.value);
            addMessage("📤 Sent: " + input.value);
            input.value = "";
        }

        function addMessage(message) {
            const div = document.getElementById("messages");
            div.innerHTML += "<p>" + message + "</p>";
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Echo it back with prefix
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        print("Client disconnected")
```

### Broadcasting to Multiple Clients

**Connection Manager with Broadcasting:**

```python
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        # Send to all connected clients
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)

    # Notify everyone about new connection
    await manager.broadcast(f"Client #{client_id} joined the chat")

    try:
        while True:
            data = await websocket.receive_text()

            # Send personal confirmation
            await manager.send_personal_message(f"You said: {data}", websocket)

            # Broadcast to everyone
            await manager.broadcast(f"Client #{client_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```

### Chat Room Implementation

```python
from typing import Dict, List

class ChatRoomManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def join_room(self, room: str, websocket: WebSocket):
        await websocket.accept()

        if room not in self.rooms:
            self.rooms[room] = []

        self.rooms[room].append(websocket)

    def leave_room(self, room: str, websocket: WebSocket):
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)

            # Clean up empty rooms
            if len(self.rooms[room]) == 0:
                del self.rooms[room]

    async def broadcast_to_room(self, room: str, message: str, exclude: WebSocket = None):
        if room in self.rooms:
            for connection in self.rooms[room]:
                if connection != exclude:  # Don't send to sender
                    await connection.send_text(message)

chat_manager = ChatRoomManager()

@app.websocket("/ws/room/{room_name}/{username}")
async def join_chat_room(websocket: WebSocket, room_name: str, username: str):
    await chat_manager.join_room(room_name, websocket)

    # Welcome message to user
    await websocket.send_text(f"Welcome to {room_name}, {username}!")

    # Notify room about new user
    await chat_manager.broadcast_to_room(
        room_name,
        f"{username} joined the room",
        exclude=websocket
    )

    try:
        while True:
            message = await websocket.receive_text()

            # Broadcast to room
            await chat_manager.broadcast_to_room(
                room_name,
                f"{username}: {message}"
            )

    except WebSocketDisconnect:
        chat_manager.leave_room(room_name, websocket)
        await chat_manager.broadcast_to_room(
            room_name,
            f"{username} left the room"
        )
```

### Handling Message Types

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive JSON message
            data = await websocket.receive_json()

            # Handle different message types
            msg_type = data.get("type")

            if msg_type == "chat":
                await handle_chat_message(websocket, data)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":
                await subscribe_to_channel(websocket, data["channel"])

            elif msg_type == "unsubscribe":
                await unsubscribe_from_channel(websocket, data["channel"])

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        print("Client disconnected")

async def handle_chat_message(websocket: WebSocket, data: dict):
    content = data.get("content", "")
    await manager.broadcast_json({
        "type": "chat",
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
```

### Periodic Messages (Server Push)

```python
import asyncio

@app.websocket("/ws/feed")
async def data_feed(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Send updates every 2 seconds
            data = {
                "type": "update",
                "value": random.randint(0, 100),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(data)

            # Wait before next update
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        print("Feed client disconnected")
```

---

## 🎓 Key Takeaways & Best Practices (00:55-00:58)

### Core Concepts Summary

✅ **WebSockets enable true real-time, bidirectional communication**

- Persistent connection, unlike HTTP request-response
- Lower latency and overhead compared to polling
- Starts with HTTP upgrade, then switches protocols

✅ **FastAPI provides excellent WebSocket support**

- Built on Starlette's async WebSocket implementation
- Easy-to-use decorators and async/await syntax
- Supports dependency injection and middleware

✅ **Always explicitly accept connections**

- Use `await websocket.accept()` before communication
- Validate authentication before accepting
- Provide clear rejection reasons with close codes

✅ **Handle disconnections gracefully**

- Use try/except with `WebSocketDisconnect`
- Clean up resources (remove from connection lists)
- Notify other clients when someone leaves

✅ **Use Connection Managers for multi-client scenarios**

- Track all active connections centrally
- Enable broadcasting to all or specific clients
- Implement room/channel logic

### Best Practices

**🔒 Security:**

- Always authenticate before accepting connections
- Use `wss://` (WebSocket Secure) in production
- Validate all incoming messages
- Implement rate limiting per IP/user
- Sanitize data before broadcasting

**⚡ Performance:**

- Use asynchronous operations everywhere
- Implement connection limits to prevent resource exhaustion
- Consider message size limits
- Use binary frames for large data (more efficient)

**🛠️ Error Handling:**

- Catch `WebSocketDisconnect` for clean disconnections
- Handle JSON parsing errors gracefully
- Provide meaningful error messages to clients
- Log errors for debugging

**📊 Monitoring:**

- Track active connection count
- Monitor message rates
- Log connection/disconnection events
- Alert on abnormal patterns

**🧪 Testing:**

- Test with multiple concurrent clients
- Simulate network interruptions
- Test with various message sizes
- Verify cleanup on disconnection

### Common Pitfalls to Avoid

❌ **Forgetting to accept connections**

```python
# WRONG - will fail
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.send_text("Hello")  # Error! Not accepted yet
```

❌ **Not handling disconnections**

```python
# WRONG - will leak connections
while True:
    data = await websocket.receive_text()  # No exception handling
```

❌ **Blocking operations in message loop**

```python
# WRONG - blocks all other clients
while True:
    data = await websocket.receive_text()
    time.sleep(5)  # DON'T DO THIS! Use await asyncio.sleep(5)
```

❌ **Not cleaning up on disconnect**

```python
# WRONG - connection stays in list forever
manager.active_connections.append(websocket)  # No cleanup
```

---

## 📝 Practice Assignment (00:58-01:00)

### Assignment: Build a Complete Echo WebSocket Server

**Objective:** Create a production-ready WebSocket echo server with the following features:

**Core Requirements:**

1. **Basic Echo Functionality**
   - Accept WebSocket connections at `/ws`
   - Echo back all received text messages with "Echo: " prefix
   - Handle disconnections gracefully

2. **HTML Test Interface**
   - Serve an HTML page at `/` endpoint
   - Include connect/disconnect buttons
   - Input field for messages
   - Display area for sent and received messages
   - Show connection status

3. **Multiple Client Support**
   - Implement a `ConnectionManager` class
   - Track all active connections
   - Broadcast messages to all connected clients
   - Show join/leave notifications

4. **Client Identification**
   - Use path parameter for client ID: `/ws/{client_id}`
   - Display client ID in broadcast messages
   - Notify all clients when someone joins/leaves

**Bonus Features (Optional):**

5. **Authentication**
   - Require token in query parameter
   - Validate token before accepting connection
   - Close connection if token invalid

6. **Message Types**
   - Support JSON messages
   - Handle different message types (chat, ping, etc.)
   - Send pong response to ping messages

7. **Connection Limits**
   - Limit to 10 concurrent connections
   - Reject connections beyond limit with proper close code

**Starter Code Structure:**

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    # TODO: Implement connect, disconnect, broadcast methods

manager = ConnectionManager()

html = """
<!DOCTYPE html>
<html>
<head><title>Echo Server</title></head>
<body>
    <h1>WebSocket Echo Server</h1>
    <!-- TODO: Add UI elements -->
    <script>
        // TODO: Implement WebSocket logic
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    # TODO: Implement WebSocket logic
    pass
```

**Testing Steps:**

1. Start server: `uvicorn main:app --reload`
2. Open browser to `http://localhost:8000`
3. Open multiple browser tabs
4. Connect from each tab
5. Send messages and verify broadcasting
6. Disconnect and verify cleanup

**Expected Output:**

```
Client #1 joined the chat
Client #2 joined the chat
Client #1: Hello!
Client #2: Hi there!
Client #1 left the chat
```

**Time Estimate:** 20-30 minutes

**Deliverables:**

- Working Python file (`websocket_echo.py`)
- Screenshot or video of multiple clients communicating
- Brief explanation of how your implementation works

**Evaluation Criteria:**

- ✅ Core functionality works (echo + HTML interface)
- ✅ Multiple clients can connect simultaneously
- ✅ Messages broadcast to all clients
- ✅ Clean disconnection handling
- ✅ Code is well-structured and commented
- ⭐ Bonus points for authentication and advanced features

---

## 🔗 Additional Resources

**Official Documentation:**

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [RFC 6455 - WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

**Tools for Testing:**

- [Postman WebSocket Client](https://www.postman.com/)
- [websocat](https://github.com/vi/websocat) - CLI WebSocket client
- Browser DevTools Network tab (WebSocket frames)

**Further Learning:**

- Implementing WebSocket authentication with JWT
- Scaling WebSockets with Redis pub/sub
- WebSocket compression and performance optimization
- Deploying WebSocket applications to production

---

**End of Lecture**

**Duration:** 60 minutes  
**Next Session:** Advanced WebSocket Patterns & Production Deployment

For questions, open an issue or reach out during office hours!

---

_Created with ❤️ for FastAPI Learning_  
_Last Updated: February 3, 2026_
