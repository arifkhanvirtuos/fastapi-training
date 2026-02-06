# WebSocket Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBSOCKET IMPLEMENTATION                          │
│                        FastAPI Learning Project                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Browser 1  │  │  Browser 2  │  │  Browser 3  │  │  Python     │  │
│  │  Client #1  │  │  Client #2  │  │  Client #3  │  │  Client     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │                │           │
│         │    WebSocket   │    WebSocket   │    WebSocket   │           │
│         │   Connection   │   Connection   │   Connection   │           │
│         ▼                ▼                ▼                ▼           │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                   │
                                   │ ws://localhost:8000/ws/...
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                          SERVER LAYER                                    │
│                         FastAPI Application                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     WebSocket Endpoints                          │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  📡 /ws/echo/{client_id}                                         │   │
│  │     ├─ Accept connection                                         │   │
│  │     ├─ Echo messages back to sender                              │   │
│  │     ├─ Broadcast to all other clients                            │   │
│  │     └─ Handle disconnect                                         │   │
│  │                                                                   │   │
│  │  💬 /ws/chat/{room_id}/{username}                                │   │
│  │     ├─ Accept connection with username                           │   │
│  │     ├─ Send welcome message                                      │   │
│  │     ├─ Broadcast to room members                                 │   │
│  │     └─ Notify on join/leave                                      │   │
│  │                                                                   │   │
│  │  📊 GET /ws/stats                                                 │   │
│  │     └─ Return connection statistics                              │   │
│  │                                                                   │   │
│  │  🌐 GET /websocket-test                                           │   │
│  │     └─ Serve HTML test interface                                 │   │
│  │                                                                   │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  Connection Manager                              │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  State:                                                           │   │
│  │  • active_connections: List[WebSocket]                           │   │
│  │  • client_info: dict {client_id, connected_at}                   │   │
│  │                                                                   │   │
│  │  Methods:                                                         │   │
│  │  • connect(websocket, client_id)                                 │   │
│  │  • disconnect(websocket)                                         │   │
│  │  • send_personal_message(message, websocket)                     │   │
│  │  • send_personal_json(data, websocket)                           │   │
│  │  • broadcast(message, exclude)                                   │   │
│  │  • broadcast_json(data, exclude)                                 │   │
│  │  • get_connection_count()                                        │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘


MESSAGE FLOW DIAGRAMS
═══════════════════════════════════════════════════════════════════════════

1. CONNECTION ESTABLISHMENT
───────────────────────────────────────────────────────────────────────────

Client                          Server                    Connection Manager
  │                               │                               │
  │─────HTTP Upgrade──────────────▶│                               │
  │  GET /ws/echo/1               │                               │
  │  Upgrade: websocket           │                               │
  │                               │                               │
  │◀─────101 Switching────────────│                               │
  │       Protocols               │                               │
  │                               │                               │
  │                               │──connect(websocket, "1")──────▶│
  │                               │                               │
  │                               │◀────websocket.accept()────────│
  │                               │    append to connections      │
  │◀─────Connection Ready─────────│                               │
  │                               │                               │
  │                               │─────broadcast_json────────────▶│
  │                               │   "Client #1 joined"          │
  │                               │                               │


2. MESSAGE ECHO & BROADCAST
───────────────────────────────────────────────────────────────────────────

Client #1          Server          Connection Manager          Client #2
  │                  │                     │                      │
  │─"Hello!"─────────▶│                     │                      │
  │                  │                     │                      │
  │                  │──receive_text()─────│                      │
  │                  │                     │                      │
  │◀─Echo: Hello!────│                     │                      │
  │                  │─send_personal_json──▶│                      │
  │                  │  {type:"echo"}      │                      │
  │                  │                     │                      │
  │                  │─broadcast_json──────▶│──────────────────────▶│
  │                  │  "Client #1: Hello" │  "Client #1: Hello"  │
  │                  │  (exclude Client #1)│                      │


3. DISCONNECTION HANDLING
───────────────────────────────────────────────────────────────────────────

Client #1          Server          Connection Manager          Client #2
  │                  │                     │                      │
  │─Close────────────▶│                     │                      │
  │                  │                     │                      │
  │                  │─WebSocketDisconnect─│                      │
  │                  │                     │                      │
  │                  │──disconnect()───────▶│                      │
  │                  │                     │─remove from list     │
  │                  │                     │─cleanup client_info  │
  │                  │                     │                      │
  │                  │─broadcast_json──────▶│──────────────────────▶│
  │                  │  "Client #1 left"   │  "Client #1 left"    │
  │                  │                     │                      │


MESSAGE FORMAT
═══════════════════════════════════════════════════════════════════════════

Echo Message:
┌────────────────────────────────────────────────────┐
│ {                                                  │
│   "type": "echo",                                  │
│   "message": "Echo: Hello",                        │
│   "client_id": 1,                                  │
│   "timestamp": "2026-02-03T10:30:00Z"              │
│ }                                                  │
└────────────────────────────────────────────────────┘

Broadcast Message:
┌────────────────────────────────────────────────────┐
│ {                                                  │
│   "type": "broadcast",                             │
│   "message": "Client #1: Hello",                   │
│   "timestamp": "2026-02-03T10:30:00Z"              │
│ }                                                  │
└────────────────────────────────────────────────────┘

Chat Message:
┌────────────────────────────────────────────────────┐
│ {                                                  │
│   "type": "chat",                                  │
│   "username": "Alice",                             │
│   "room": "general",                               │
│   "content": "Hello everyone!",                    │
│   "timestamp": "2026-02-03T10:30:00Z"              │
│ }                                                  │
└────────────────────────────────────────────────────┘


CONNECTION STATES
═══════════════════════════════════════════════════════════════════════════

┌──────────────┐
│  CONNECTING  │  Initial state, HTTP upgrade in progress
└──────┬───────┘
       │
       ▼ accept()
┌──────────────┐
│     OPEN     │  Connection active, can send/receive messages
└──────┬───────┘
       │
       ▼ disconnect() or close()
┌──────────────┐
│   CLOSING    │  Close frame sent, waiting for acknowledgment
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    CLOSED    │  Connection terminated, cleanup complete
└──────────────┘


FILE STRUCTURE
═══════════════════════════════════════════════════════════════════════════

fastapilearning/
├── WEBSOCKET_LECTURE.md                  ← 📚 1-hour lecture (40KB)
├── WEBSOCKET_IMPLEMENTATION_SUMMARY.md   ← 📋 Summary document
└── sql_app/
    ├── main.py                           ← 🚀 Updated with WebSocket
    │   ├── ConnectionManager class       ← 700+ lines added
    │   ├── /ws/echo/{client_id}          ← Echo endpoint
    │   ├── /ws/chat/{room}/{user}        ← Chat endpoint
    │   ├── /ws/stats                     ← Statistics endpoint
    │   └── /websocket-test               ← HTML interface
    │
    └── WEBSOCKET_README.md               ← 📖 Implementation guide


TECHNOLOGY STACK
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                           Technology Stack                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Backend:                                                                 │
│  • Python 3.8+                                                            │
│  • FastAPI (WebSocket support via Starlette)                             │
│  • Uvicorn (ASGI server)                                                  │
│  • asyncio (async/await)                                                  │
│                                                                           │
│  Frontend:                                                                │
│  • HTML5                                                                  │
│  • CSS3 (Gradients, Animations, Flexbox)                                 │
│  • JavaScript (ES6+)                                                      │
│  • WebSocket API (Browser native)                                        │
│                                                                           │
│  Protocol:                                                                │
│  • WebSocket (RFC 6455)                                                   │
│  • HTTP/1.1 (initial handshake)                                          │
│  • JSON (message format)                                                  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘


DEPLOYMENT ARCHITECTURE (Production)
═══════════════════════════════════════════════════════════════════════════

                    ┌─────────────────┐
                    │   Load Balancer │
                    │  (Sticky Session)│
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐        ┌────▼─────┐        ┌────▼─────┐
   │ FastAPI  │        │ FastAPI  │        │ FastAPI  │
   │ Server 1 │        │ Server 2 │        │ Server 3 │
   └────┬─────┘        └────┬─────┘        └────┬─────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                       ┌─────▼──────┐
                       │   Redis    │
                       │  (Pub/Sub) │
                       └────────────┘


KEY FEATURES MATRIX
═══════════════════════════════════════════════════════════════════════════

Feature                    Status    Complexity    Priority
─────────────────────────────────────────────────────────────────────────
Connection Management      ✅        Medium        High
Echo Server               ✅        Low           High
Broadcasting              ✅        Medium        High
Chat Rooms                ✅        Medium        Medium
HTML Test Interface       ✅        Low           High
Statistics Endpoint       ✅        Low           Medium
Error Handling            ✅        Medium        High
Client Tracking           ✅        Low           Medium
Timestamps                ✅        Low           Low
JSON Messages             ✅        Low           High
Graceful Disconnection    ✅        Medium        High
Authentication            ⏳        High          High (Future)
Rate Limiting             ⏳        Medium        High (Future)
Message Persistence       ⏳        High          Medium (Future)
Redis Integration         ⏳        High          Medium (Future)


PERFORMANCE METRICS (Expected)
═══════════════════════════════════════════════════════════════════════════

Metric                          Value              Notes
─────────────────────────────────────────────────────────────────────────
Concurrent Connections          100-500            Per server instance
Message Latency                 < 10ms             Local network
Broadcast Latency               < 50ms             To all clients
Memory per Connection           ~100KB             Rough estimate
CPU Usage                       Low                Async I/O
Throughput                      1000+ msg/sec      Small messages


TESTING CHECKLIST
═══════════════════════════════════════════════════════════════════════════

□ Single client connection
□ Multiple client connections (3+)
□ Echo functionality
□ Broadcasting to all clients
□ Chat room functionality
□ Join/leave notifications
□ Graceful disconnection
□ Reconnection after disconnect
□ Multiple browser tabs
□ Statistics endpoint
□ HTML test interface
□ Send various message types
□ Long messages (1KB+)
□ Rapid message sending
□ Connection stability test (1+ hour)


TROUBLESHOOTING GUIDE
═══════════════════════════════════════════════════════════════════════════

Issue                           Solution
─────────────────────────────────────────────────────────────────────────
Can't connect                   Check server is running on port 8000
                                Verify URL: ws:// not wss://
                                Check firewall settings

Messages not echoing            Check server logs
                                Verify connection is open
                                Test with /ws/stats endpoint

Broadcasting not working        Ensure multiple clients connected
                                Check Connection Manager
                                Verify exclude parameter

Disconnection errors            Add try/except for WebSocketDisconnect
                                Implement cleanup in finally block
                                Check client timeout settings

HTML page not loading           Verify route /websocket-test exists
                                Check return HTMLResponse
                                Clear browser cache


URLS & ENDPOINTS REFERENCE
═══════════════════════════════════════════════════════════════════════════

Description                     URL/Endpoint
─────────────────────────────────────────────────────────────────────────
HTML Test Interface             http://localhost:8000/websocket-test
Echo WebSocket                  ws://localhost:8000/ws/echo/1
Chat Room                       ws://localhost:8000/ws/chat/general/Alice
Statistics (HTTP)               http://localhost:8000/ws/stats
API Documentation               http://localhost:8000/docs
Alternative Docs                http://localhost:8000/redoc


═══════════════════════════════════════════════════════════════════════════
                            END OF DIAGRAM
═══════════════════════════════════════════════════════════════════════════
```
