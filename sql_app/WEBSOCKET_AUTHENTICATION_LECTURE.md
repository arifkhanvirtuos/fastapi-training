# 🔐 WebSocket Authentication with JWT

## Complete 1-Hour Lecture

**Duration:** 60 minutes  
**Level:** Intermediate to Advanced  
**Prerequisites:** Basic WebSocket knowledge, JWT basics, FastAPI fundamentals

---

## 📋 Table of Contents

| Time        | Topic                                    | Duration |
| ----------- | ---------------------------------------- | -------- |
| 00:00-00:10 | Introduction to WebSocket Authentication | 10 min   |
| 00:10-00:20 | JWT Basics and Token Flow                | 10 min   |
| 00:20-00:30 | Implementing Token Validation            | 10 min   |
| 00:30-00:40 | Building Authenticated Endpoints         | 10 min   |
| 00:40-00:50 | Security Best Practices                  | 10 min   |
| 00:50-00:58 | Testing Authenticated WebSockets         | 8 min    |
| 00:58-01:00 | Practice Assignment                      | 2 min    |

---

## ⏱️ **00:00-00:10: Introduction to WebSocket Authentication**

### Why Authenticate WebSocket Connections?

Unlike HTTP requests where you can simply add an `Authorization` header to each request, WebSocket connections are **persistent** and **bidirectional**. Once established, the connection stays open, making authentication more challenging.

**Key Challenges:**

1. **Initial Authentication** - How to verify the user before accepting the connection?
2. **Token Expiration** - What happens when the JWT expires during an active connection?
3. **Connection Hijacking** - How to prevent unauthorized access to an existing connection?
4. **Scalability** - Managing authenticated connections across multiple servers

**Why Not Regular HTTP Auth?**

```
Regular HTTP Request:
Client → [Request + Authorization Header] → Server
Client ← [Response] ← Server
(Connection closes)

WebSocket Connection:
Client → [Handshake + Token] → Server
      ← [Accept/Reject] ←
      ↔ [Persistent Connection] ↔
      (Connection stays open for minutes/hours)
```

### Real-World Use Cases

| Use Case                  | Why Authentication Needed                    |
| ------------------------- | -------------------------------------------- |
| **Chat Applications**     | Identify users, prevent spam, enable DMs     |
| **Trading Platforms**     | Secure order updates, account-specific data  |
| **Collaborative Editing** | Track who's editing, permission checks       |
| **IoT Dashboards**        | Device-specific data, user permissions       |
| **Gaming**                | Player identity, anti-cheating, leaderboards |

### The WebSocket Security Problem

**Without Authentication:**

```python
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()  # ❌ ANYONE can connect!
    # No way to know WHO this is
```

**With Authentication:**

```python
@app.websocket("/ws/secure/chat")
async def secure_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token")
    user = await verify_websocket_token(token, db)  # ✅ Verify FIRST
    await websocket.accept()  # Only accept if valid
    # Now we know WHO this is!
```

---

## ⏱️ **00:10-00:20: JWT Basics and Token Flow**

### What is JWT (JSON Web Token)?

A JWT is a **compact, URL-safe means of representing claims** between two parties. It's **self-contained** - the token itself contains all the necessary information.

**Structure:**

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

[Header].[Payload].[Signature]
```

**Decoded Header:**

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Decoded Payload:**

```json
{
  "sub": "1234567890", // Subject (user ID)
  "email": "john@example.com",
  "role": "admin",
  "exp": 1716239022 // Expiration timestamp
}
```

**Signature:**

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  your-256-bit-secret
)
```

### Token Flow for WebSocket Authentication

```
┌─────────────────────────────────────────────────────────────┐
│              WebSocket JWT Authentication Flow               │
└─────────────────────────────────────────────────────────────┘

Step 1: User Login (HTTP)
┌──────────┐                                        ┌──────────┐
│  Client  │  POST /token                           │  Server  │
│          │  {email, password}                     │          │
│          │ ─────────────────────────────────────→ │          │
│          │                                        │          │
│          │  ←─────────────────────────────────── │          │
│          │  {access_token: "eyJhbG..."}          │          │
└──────────┘                                        └──────────┘

Step 2: Store Token (Client-Side)
┌──────────┐
│  Client  │
│          │  localStorage.setItem('token', token)
│          │  OR store in memory/cookie
└──────────┘

Step 3: WebSocket Connection
┌──────────┐                                        ┌──────────┐
│  Client  │  WebSocket Handshake                   │  Server  │
│          │  ws://host/ws/chat?token=eyJhbG...    │          │
│          │ ─────────────────────────────────────→ │          │
│          │                                        │ Verify   │
│          │                                        │ Token    │
│          │  ←─────────────────────────────────── │          │
│          │  Connection Accepted                   │          │
└──────────┘                                        └──────────┘

Step 4: Persistent Authenticated Connection
┌──────────┐                                        ┌──────────┐
│  Client  │  ↔ Messages with user context ↔       │  Server  │
│          │                                        │          │
│          │  Server knows WHO sent each message    │          │
└──────────┘                                        └──────────┘
```

### Token Passing Methods

**Method 1: Query Parameters (Recommended for WebSockets)**

```javascript
// Client-side
const token = localStorage.getItem("access_token");
const ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);
```

```python
# Server-side
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    token = websocket.query_params.get("token")
```

**Pros:** ✅ Simple, works everywhere  
**Cons:** ⚠️ Token visible in logs, URL history

**Method 2: WebSocket Subprotocol (More Secure)**

```javascript
// Client-side
const ws = new WebSocket(
  "ws://localhost:8000/ws/chat",
  ["access_token", token], // Subprotocol
);
```

```python
# Server-side (requires custom handling)
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    # Extract from Sec-WebSocket-Protocol header
    token = websocket.headers.get("Sec-WebSocket-Protocol")
```

**Pros:** ✅ Not in URL, more secure  
**Cons:** ⚠️ More complex, browser compatibility

**Method 3: Custom Header (During Handshake)**

```javascript
// Not directly supported in browser WebSocket API
// Need to use libraries like Socket.IO
```

### Token Creation and Validation

**Creating a JWT (Server-Side):**

```python
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-secret-key-keep-it-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Usage
token = create_access_token({"sub": str(user.id), "email": user.email})
```

**Validating a JWT:**

```python
from jose import jwt, JWTError

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
```

---

## ⏱️ **00:20-00:30: Implementing Token Validation**

### Step 1: Create Token Verification Function

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from models import User

async def verify_websocket_token(token: str, db: Session) -> User:
    """
    Verify JWT token and return authenticated user.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        User object if valid

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Check if token exists
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )

    try:
        from auth import SECRET_KEY, ALGORITHM

        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )

        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )
```

### Step 2: Create Authenticated Connection Manager

```python
from datetime import datetime, timezone
from typing import List, Dict
from models import User, UserRole

class AuthenticatedConnectionManager:
    """
    Enhanced Connection Manager with authentication support.
    Tracks authenticated users and their associated connections.
    """

    def __init__(self):
        self.active_connections: Dict[WebSocket, dict] = {}  # {websocket: user_info}
        self.user_connections: Dict[int, List[WebSocket]] = {}  # {user_id: [websockets]}

    async def connect(self, websocket: WebSocket, user: User):
        """Accept authenticated WebSocket connection"""
        await websocket.accept()

        # Store user info with connection
        user_info = {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }

        self.active_connections[websocket] = user_info

        # Track user's multiple connections (multiple tabs/devices)
        if user.id not in self.user_connections:
            self.user_connections[user.id] = []
        self.user_connections[user.id].append(websocket)

        print(f"✅ Authenticated WebSocket: {user.email} (ID: {user.id})")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket from active connections"""
        if websocket in self.active_connections:
            user_info = self.active_connections[websocket]
            user_id = user_info["user_id"]

            # Remove from active connections
            del self.active_connections[websocket]

            # Remove from user's connections
            if user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)

                # Clean up if no more connections for this user
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            print(f"❌ Disconnected: {user_info['email']}")

    async def send_to_user(self, user_id: int, data: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            disconnected = []

            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected
            for ws in disconnected:
                self.disconnect(ws)

    async def broadcast_json(self, data: dict, exclude: WebSocket = None):
        """Broadcast JSON message to all authenticated connections"""
        disconnected = []

        for websocket in self.active_connections:
            if websocket == exclude:
                continue

            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Broadcast error: {e}")
                disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_to_role(self, role: UserRole, data: dict):
        """Broadcast message to all users with specific role"""
        disconnected = []

        for websocket, user_info in self.active_connections.items():
            if user_info["role"] == role.value:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"Error broadcasting to role {role.value}: {e}")
                    disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws)

    def get_online_users(self) -> List[dict]:
        """Get list of all online users"""
        online_users = {}

        for user_info in self.active_connections.values():
            user_id = user_info["user_id"]

            if user_id not in online_users:
                online_users[user_id] = {
                    "user_id": user_id,
                    "email": user_info["email"],
                    "full_name": user_info["full_name"],
                    "role": user_info["role"],
                    "connection_count": 0
                }

            online_users[user_id]["connection_count"] += 1

        return list(online_users.values())

# Global instance
auth_ws_manager = AuthenticatedConnectionManager()
```

### Step 3: Implement Graceful Error Handling

```python
@app.websocket("/ws/secure/chat")
async def secure_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    """Authenticated WebSocket endpoint with proper error handling"""

    # Extract token from query parameters
    token = websocket.query_params.get("token")

    # Close connection if no token
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    # Verify token and get user
    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        # Close with specific error message
        await websocket.close(code=1008, reason=e.detail)
        return

    # Now connect authenticated user
    await auth_ws_manager.connect(websocket, user)

    try:
        # Main message loop
        while True:
            data = await websocket.receive_text()
            # Handle message with user context

    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"Error: {e}")
        auth_ws_manager.disconnect(websocket)
```

**WebSocket Close Codes:**

| Code      | Meaning            | When to Use            |
| --------- | ------------------ | ---------------------- |
| 1000      | Normal Closure     | Clean disconnect       |
| 1008      | Policy Violation   | Authentication failure |
| 1011      | Internal Error     | Server error           |
| 3000-3999 | Custom Application | Custom auth errors     |

---

## ⏱️ **00:30-00:40: Building Authenticated Endpoints**

### Example 1: Authenticated Echo Endpoint

```python
@app.websocket("/ws/secure/echo/{client_id}")
async def authenticated_echo(
    websocket: WebSocket,
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    Authenticated echo endpoint with user identification.

    URL: ws://localhost:8000/ws/secure/echo/123?token=YOUR_JWT_TOKEN
    """
    # Extract and verify token
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return

    # Connect
    await auth_ws_manager.connect(websocket, user)

    # Send welcome with user info
    await auth_ws_manager.send_personal_json(
        {
            "type": "welcome",
            "message": f"Welcome {user.full_name}!",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )

    try:
        while True:
            data = await websocket.receive_text()

            # Echo with user context
            await auth_ws_manager.send_personal_json(
                {
                    "type": "echo",
                    "message": f"Echo: {data}",
                    "from": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )

            # Broadcast to others
            await auth_ws_manager.broadcast_json(
                {
                    "type": "message",
                    "content": data,
                    "from": {
                        "id": user.id,
                        "full_name": user.full_name,
                        "role": user.role.value
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exclude=websocket
            )

    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
```

### Example 2: Authenticated Chat Room with Role-Based Features

```python
@app.websocket("/ws/secure/chat/{room_id}")
async def authenticated_chat_room(
    websocket: WebSocket,
    room_id: str,
    db: Session = Depends(get_db)
):
    """
    Secure chat room with role-based features.

    Features:
    - Regular messages
    - Private messages
    - Admin announcements
    - Typing indicators
    """
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return

    await auth_ws_manager.connect(websocket, user)

    # Welcome message with online users
    await auth_ws_manager.send_personal_json(
        {
            "type": "room_joined",
            "room": room_id,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "online_users": auth_ws_manager.get_online_users(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type", "chat")
                content = message_data.get("content", data)
                target_user_id = message_data.get("target_user_id")
            except json.JSONDecodeError:
                msg_type = "chat"
                content = data

            # Handle message types
            if msg_type == "private" and target_user_id:
                # Private message
                await auth_ws_manager.send_to_user(
                    target_user_id,
                    {
                        "type": "private_message",
                        "content": content,
                        "from": {
                            "id": user.id,
                            "full_name": user.full_name
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

            elif msg_type == "announcement":
                # Admin-only announcements
                if user.role == UserRole.ADMIN:
                    await auth_ws_manager.broadcast_json(
                        {
                            "type": "announcement",
                            "content": content,
                            "from": {"full_name": user.full_name},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                else:
                    await auth_ws_manager.send_personal_json(
                        {
                            "type": "error",
                            "message": "Only admins can send announcements"
                        },
                        websocket
                    )

            else:
                # Regular chat message
                await auth_ws_manager.broadcast_json(
                    {
                        "type": "chat",
                        "content": content,
                        "room": room_id,
                        "from": {
                            "id": user.id,
                            "full_name": user.full_name,
                            "role": user.role.value
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
```

### Example 3: Personal Notification Stream

```python
@app.websocket("/ws/secure/notifications")
async def notifications_stream(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    Personal notification stream for authenticated users.

    Use cases:
    - Real-time alerts
    - Task updates
    - System messages
    """
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return

    await auth_ws_manager.connect(websocket, user)

    await auth_ws_manager.send_personal_json(
        {
            "type": "notification_stream_connected",
            "user_id": user.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )

    try:
        while True:
            await websocket.receive_text()

            await auth_ws_manager.send_personal_json(
                {
                    "type": "ack",
                    "message": "Stream active",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )

    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
```

### Admin Endpoints for Sending Messages

```python
@app.post("/ws/secure/send-notification/{user_id}")
async def send_notification_to_user(
    user_id: int,
    notification: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Send notification to specific user (Admin only).

    Example request:
    {
        "type": "alert",
        "message": "Your task has been updated",
        "priority": "high"
    }
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    notification_data = {
        **notification,
        "from_admin": {
            "id": current_user.id,
            "full_name": current_user.full_name
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    await auth_ws_manager.send_to_user(user_id, notification_data)

    return {"status": "sent", "target_user_id": user_id}


@app.post("/ws/secure/broadcast")
async def broadcast_message(
    message: dict,
    current_user: User = Depends(require_admin)
):
    """Broadcast to all authenticated connections (Admin only)"""
    broadcast_data = {
        **message,
        "from_admin": {"full_name": current_user.full_name},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    await auth_ws_manager.broadcast_json(broadcast_data)

    return {
        "status": "broadcast_sent",
        "recipients": auth_ws_manager.get_connection_count()
    }
```

---

## ⏱️ **00:40-00:50: Security Best Practices**

### 1. Token Security

**✅ DO:**

- Use HTTPS/WSS in production
- Keep tokens short-lived (15-30 minutes)
- Implement token refresh mechanism
- Store tokens securely (httpOnly cookies for web)
- Use strong secret keys (256-bit minimum)

**❌ DON'T:**

- Store tokens in localStorage (XSS vulnerable)
- Use tokens in URL query params in production (log exposure)
- Share tokens between users
- Store secret keys in code (use environment variables)

```python
# GOOD: Environment variable
SECRET_KEY = os.getenv("SECRET_KEY")

# BAD: Hardcoded
SECRET_KEY = "my-secret-key-123"
```

### 2. Connection Validation

**Always validate before accepting:**

```python
@app.websocket("/ws/secure/chat")
async def chat(websocket: WebSocket, db: Session = Depends(get_db)):
    # STEP 1: Extract token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="No token")
        return

    # STEP 2: Verify token
    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return

    # STEP 3: Check user status
    if not user.is_active:
        await websocket.close(code=1008, reason="Inactive user")
        return

    # STEP 4: Accept connection
    await websocket.accept()
```

### 3. Rate Limiting

**Prevent abuse with rate limiting:**

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
        self.user_messages = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()

        # Remove old messages outside window
        self.user_messages[user_id] = [
            ts for ts in self.user_messages[user_id]
            if now - ts < self.window
        ]

        # Check if under limit
        if len(self.user_messages[user_id]) >= self.max_messages:
            return False

        # Add new message timestamp
        self.user_messages[user_id].append(now)
        return True

rate_limiter = RateLimiter(max_messages=10, window_seconds=60)

# Usage in WebSocket
@app.websocket("/ws/secure/chat")
async def chat(websocket: WebSocket, db: Session = Depends(get_db)):
    # ... authentication ...

    try:
        while True:
            data = await websocket.receive_text()

            # Check rate limit
            if not rate_limiter.is_allowed(user.id):
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded. Slow down!"
                })
                continue

            # Process message
    except WebSocketDisconnect:
        pass
```

### 4. Input Validation

**Always validate and sanitize input:**

```python
from pydantic import BaseModel, validator

class ChatMessage(BaseModel):
    type: str
    content: str
    target_user_id: Optional[int] = None

    @validator('content')
    def validate_content(cls, v):
        if len(v) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

    @validator('type')
    def validate_type(cls, v):
        allowed = ['chat', 'private', 'announcement', 'typing']
        if v not in allowed:
            raise ValueError(f'Invalid message type. Allowed: {allowed}')
        return v

# Usage
@app.websocket("/ws/secure/chat")
async def chat(websocket: WebSocket, db: Session = Depends(get_db)):
    # ... auth ...

    try:
        while True:
            data = await websocket.receive_text()

            try:
                # Validate message
                message = ChatMessage(**json.loads(data))
            except ValidationError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                continue

            # Process validated message
    except WebSocketDisconnect:
        pass
```

### 5. Token Expiration Handling

**Handle token expiration gracefully:**

```python
import time

def is_token_expired(token: str) -> bool:
    """Check if token is expired without raising exception"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")

        if exp is None:
            return True

        return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
    except JWTError:
        return True

@app.websocket("/ws/secure/chat")
async def chat(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token")
    user = await verify_websocket_token(token, db)
    await websocket.accept()

    try:
        while True:
            # Periodically check token expiration
            if is_token_expired(token):
                await websocket.send_json({
                    "type": "token_expired",
                    "message": "Your session has expired. Please refresh.",
                    "action": "reconnect"
                })
                await websocket.close(code=1008, reason="Token expired")
                break

            data = await websocket.receive_text()
            # Process message

    except WebSocketDisconnect:
        pass
```

### 6. Secure WebSocket (WSS) in Production

**Always use WSS (WebSocket over TLS) in production:**

```python
# Development
ws://localhost:8000/ws/chat

# Production
wss://yourdomain.com/ws/chat
```

**nginx configuration:**

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Security Checklist

- [ ] Use WSS (WebSocket Secure) in production
- [ ] Validate tokens before accepting connections
- [ ] Implement rate limiting
- [ ] Validate and sanitize all user input
- [ ] Use short-lived tokens (15-30 minutes)
- [ ] Implement token refresh mechanism
- [ ] Store secrets in environment variables
- [ ] Log authentication failures
- [ ] Implement connection timeouts
- [ ] Handle token expiration gracefully
- [ ] Use CORS with specific origins
- [ ] Monitor for suspicious activity
- [ ] Implement user session limits
- [ ] Use secure token storage (httpOnly cookies)
- [ ] Regular security audits

---

## ⏱️ **00:50-00:58: Testing Authenticated WebSockets**

### 1. Manual Testing with Browser

**HTML Test Interface:**

```html
<!DOCTYPE html>
<html>
  <head>
    <title>WebSocket Auth Test</title>
  </head>
  <body>
    <h1>Authenticated WebSocket Test</h1>

    <!-- Step 1: Login -->
    <div>
      <h3>1. Login</h3>
      <input id="email" type="email" placeholder="Email" />
      <input id="password" type="password" placeholder="Password" />
      <button onclick="login()">Login</button>
      <div id="token"></div>
    </div>

    <!-- Step 2: Connect -->
    <div>
      <h3>2. Connect WebSocket</h3>
      <button onclick="connect()" id="connectBtn" disabled>Connect</button>
      <button onclick="disconnect()" id="disconnectBtn" disabled>
        Disconnect
      </button>
      <div id="status">Disconnected</div>
    </div>

    <!-- Step 3: Send Messages -->
    <div>
      <h3>3. Send Message</h3>
      <input id="message" type="text" placeholder="Message" />
      <button onclick="send()" id="sendBtn" disabled>Send</button>
    </div>

    <!-- Messages -->
    <div
      id="messages"
      style="border:1px solid #ccc; height:300px; overflow:auto;"
    ></div>

    <script>
      let ws = null;
      let token = null;

      async function login() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const response = await fetch("/token", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          token = data.access_token;
          document.getElementById("token").textContent =
            "Token: " + token.substring(0, 20) + "...";
          document.getElementById("connectBtn").disabled = false;
          addMessage("✅ Logged in successfully");
        } else {
          addMessage("❌ Login failed");
        }
      }

      function connect() {
        if (!token) {
          addMessage("Please login first");
          return;
        }

        ws = new WebSocket(
          `ws://localhost:8000/ws/secure/echo/test?token=${token}`,
        );

        ws.onopen = () => {
          document.getElementById("status").textContent = "✅ Connected";
          document.getElementById("status").style.color = "green";
          document.getElementById("sendBtn").disabled = false;
          document.getElementById("disconnectBtn").disabled = false;
          document.getElementById("connectBtn").disabled = true;
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          addMessage("📨 " + JSON.stringify(data, null, 2));
        };

        ws.onclose = () => {
          document.getElementById("status").textContent = "⭕ Disconnected";
          document.getElementById("status").style.color = "red";
          document.getElementById("sendBtn").disabled = true;
          document.getElementById("disconnectBtn").disabled = true;
          document.getElementById("connectBtn").disabled = false;
        };
      }

      function disconnect() {
        if (ws) ws.close();
      }

      function send() {
        const message = document.getElementById("message").value;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(message);
          addMessage("📤 Sent: " + message);
          document.getElementById("message").value = "";
        }
      }

      function addMessage(msg) {
        const div = document.getElementById("messages");
        div.innerHTML += "<div>" + msg + "</div>";
        div.scrollTop = div.scrollHeight;
      }

      document.getElementById("message").addEventListener("keypress", (e) => {
        if (e.key === "Enter") send();
      });
    </script>
  </body>
</html>
```

### 2. Python Client Testing

```python
import asyncio
import websockets
import json
import requests

async def test_authenticated_websocket():
    # Step 1: Login and get token
    response = requests.post(
        'http://localhost:8000/token',
        data={
            'username': 'admin@example.com',
            'password': 'admin123'
        }
    )

    if response.status_code != 200:
        print("❌ Login failed")
        return

    token = response.json()['access_token']
    print(f"✅ Got token: {token[:20]}...")

    # Step 2: Connect to WebSocket
    uri = f"ws://localhost:8000/ws/secure/echo/test?token={token}"

    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket connected")

        # Step 3: Receive welcome message
        welcome = await websocket.recv()
        print(f"📨 Welcome: {json.loads(welcome)}")

        # Step 4: Send messages
        for i in range(5):
            message = f"Test message {i+1}"
            await websocket.send(message)
            print(f"📤 Sent: {message}")

            response = await websocket.recv()
            print(f"📨 Received: {json.loads(response)}")

            await asyncio.sleep(1)

        print("✅ Test completed")

# Run test
if __name__ == "__main__":
    asyncio.run(test_authenticated_websocket())
```

### 3. Testing with curl (WebSocket Handshake)

```bash
# Test WebSocket handshake
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  "http://localhost:8000/ws/secure/echo/test?token=YOUR_TOKEN"
```

### 4. Automated Testing with pytest

```python
# test_websocket_auth.py
import pytest
from fastapi.testclient import TestClient
from main import app
from auth import create_access_token

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def valid_token():
    return create_access_token({"sub": "1", "email": "admin@example.com"})

def test_websocket_without_token(client):
    """Test that connection is rejected without token"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/secure/echo/test"):
            pass

def test_websocket_with_invalid_token(client):
    """Test that connection is rejected with invalid token"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/secure/echo/test?token=invalid"):
            pass

def test_websocket_with_valid_token(client, valid_token):
    """Test successful connection with valid token"""
    with client.websocket_connect(f"/ws/secure/echo/test?token={valid_token}") as websocket:
        # Should receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "welcome"

        # Send message
        websocket.send_text("Hello")

        # Should receive echo
        response = websocket.receive_json()
        assert response["type"] == "echo"
        assert "Hello" in response["message"]

def test_multiple_users_chat(client, valid_token):
    """Test multiple authenticated users in chat"""
    # User 1 connects
    with client.websocket_connect(f"/ws/secure/chat/test?token={valid_token}") as ws1:
        # User 1 receives welcome
        welcome1 = ws1.receive_json()
        assert welcome1["type"] == "room_joined"

        # User 2 connects
        token2 = create_access_token({"sub": "2", "email": "user@example.com"})
        with client.websocket_connect(f"/ws/secure/chat/test?token={token2}") as ws2:
            # User 2 receives welcome
            welcome2 = ws2.receive_json()
            assert welcome2["type"] == "room_joined"

            # User 1 should be notified of User 2 joining
            notification = ws1.receive_json()
            assert notification["type"] == "user_joined_room"

            # User 2 sends message
            ws2.send_text(json.dumps({
                "type": "chat",
                "content": "Hello everyone!"
            }))

            # User 1 should receive the message
            message = ws1.receive_json()
            assert message["type"] == "chat"
            assert message["content"] == "Hello everyone!"
```

**Run tests:**

```bash
pytest test_websocket_auth.py -v
```

### Testing Checklist

- [ ] Test connection without token (should fail)
- [ ] Test connection with invalid token (should fail)
- [ ] Test connection with expired token (should fail)
- [ ] Test connection with valid token (should succeed)
- [ ] Test message sending/receiving
- [ ] Test multiple concurrent users
- [ ] Test role-based features
- [ ] Test rate limiting
- [ ] Test token expiration during connection
- [ ] Test reconnection with new token
- [ ] Load testing with many concurrent connections

---

## ⏱️ **00:58-01:00: Practice Assignment**

### Assignment: Build a Secure Task Notification System

**Requirements:**

1. **Authentication**
   - Users must authenticate with JWT
   - Only active users can connect

2. **WebSocket Endpoints**
   - `/ws/secure/tasks` - Personal task updates stream
   - `/ws/secure/team/{team_id}` - Team task notifications

3. **Features**
   - Real-time task assignment notifications
   - Task status update broadcasts
   - Private task comments
   - Admin can broadcast to all teams

4. **Security**
   - Token validation
   - Rate limiting (max 20 messages/minute)
   - Input validation
   - Graceful error handling

**Starter Code:**

```python
@app.websocket("/ws/secure/tasks")
async def task_notifications(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    TODO:
    1. Extract and validate token
    2. Connect authenticated user
    3. Send personal task notifications
    4. Handle task updates
    """
    pass

@app.websocket("/ws/secure/team/{team_id}")
async def team_notifications(
    websocket: WebSocket,
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    TODO:
    1. Authenticate user
    2. Verify user is member of team
    3. Broadcast team task updates
    4. Handle admin announcements
    """
    pass

@app.post("/tasks/{task_id}/notify")
async def notify_task_update(
    task_id: int,
    notification: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    TODO:
    1. Get task from database
    2. Validate user has access
    3. Send notification via WebSocket to assigned user
    """
    pass
```

**Test Cases:**

1. Connect without token → Should fail
2. Connect with valid token → Should succeed
3. Receive task assignment notification
4. Send task status update
5. Admin broadcast to team
6. Rate limit exceeded → Should receive error

**Deliverables:**

1. Implemented endpoints
2. Authentication and validation
3. Test client (HTML or Python)
4. Documentation of your implementation

---

## 📚 Summary

### Key Takeaways

1. **WebSocket authentication requires token validation BEFORE accepting connection**
2. **JWT tokens can be passed via query parameters or subprotocol**
3. **Always implement graceful error handling with proper close codes**
4. **Track authenticated users separately for user-specific messaging**
5. **Implement security measures: rate limiting, input validation, token expiration handling**
6. **Use WSS in production for encrypted communication**
7. **Test thoroughly with both manual and automated tests**

### Common Patterns

```python
# 1. Token Extraction
token = websocket.query_params.get("token")

# 2. Validation
user = await verify_websocket_token(token, db)

# 3. Connection
await auth_ws_manager.connect(websocket, user)

# 4. Message Loop
try:
    while True:
        data = await websocket.receive_text()
        # Process with user context
except WebSocketDisconnect:
    auth_ws_manager.disconnect(websocket)
```

### Resources

- **FastAPI WebSocket Docs:** https://fastapi.tiangolo.com/advanced/websockets/
- **JWT Spec:** https://jwt.io/
- **WebSocket Protocol:** RFC 6455
- **python-jose Library:** https://github.com/mpdavis/python-jose
- **Security Best Practices:** OWASP WebSocket Security

---

## 🎓 Next Steps

1. **Advanced Topics:**
   - Token refresh for long-lived connections
   - WebSocket connection pooling
   - Load balancing with Redis pub/sub
   - Horizontal scaling with message queues

2. **Integration:**
   - Combine with database change streams
   - Integrate with task queues (Celery)
   - Add monitoring and analytics
   - Implement presence tracking

3. **Production Deployment:**
   - Set up reverse proxy (nginx)
   - Configure SSL/TLS
   - Implement logging and monitoring
   - Set up health checks

---

**🎉 Congratulations! You now understand WebSocket authentication with JWT!**

**Questions? Review the code examples and practice assignment.**
