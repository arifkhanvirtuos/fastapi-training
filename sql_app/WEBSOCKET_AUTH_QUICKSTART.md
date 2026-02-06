# 🚀 Authenticated WebSocket Quick Start Guide

## 5-Minute Setup

### Step 1: Get Access Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Step 2: Connect to WebSocket

```javascript
const token = "YOUR_ACCESS_TOKEN_HERE";
const ws = new WebSocket(
  `ws://localhost:8000/ws/secure/echo/client1?token=${token}`,
);

ws.onopen = () => console.log("✅ Connected");
ws.onmessage = (event) => console.log("📨", JSON.parse(event.data));
ws.send("Hello authenticated world!");
```

### Step 3: Test in Browser

Visit: http://localhost:8000/authenticated-websocket-test

---

## 📚 Available Endpoints

### 1. Secure Echo

**URL:** `ws://localhost:8000/ws/secure/echo/{client_id}?token={jwt}`

**Features:**

- Personal echo with user info
- Broadcasts messages to other users
- User join/leave notifications

**Test:**

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/secure/echo/test123?token=${token}`,
);
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send("Hello!");
```

### 2. Secure Chat Room

**URL:** `ws://localhost:8000/ws/secure/chat/{room_id}?token={jwt}`

**Features:**

- Room-based messaging
- Private messages
- Admin announcements
- Typing indicators
- Online user list

**Message Types:**

```javascript
// Regular chat
ws.send(
  JSON.stringify({
    type: "chat",
    content: "Hello everyone!",
  }),
);

// Private message
ws.send(
  JSON.stringify({
    type: "private",
    content: "Secret message",
    target_user_id: 2,
  }),
);

// Admin announcement
ws.send(
  JSON.stringify({
    type: "announcement",
    content: "Server maintenance in 10 minutes",
  }),
);

// Typing indicator
ws.send(
  JSON.stringify({
    type: "typing",
  }),
);
```

### 3. Personal Notifications

**URL:** `ws://localhost:8000/ws/secure/notifications?token={jwt}`

**Features:**

- Personal notification stream
- Real-time alerts
- System messages

**Test:**

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/secure/notifications?token=${token}`,
);
ws.onmessage = (e) => console.log("Notification:", JSON.parse(e.data));
```

---

## 🔧 Admin Endpoints (HTTP)

### Get Connection Stats

```bash
curl -X GET "http://localhost:8000/ws/secure/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**

```json
{
  "total_connections": 5,
  "unique_users": 3,
  "online_users": [
    {
      "user_id": 1,
      "email": "admin@example.com",
      "full_name": "Admin User",
      "role": "admin",
      "connection_count": 2
    }
  ],
  "your_connections": 2
}
```

### Send Notification to User (Admin Only)

```bash
curl -X POST "http://localhost:8000/ws/secure/send-notification/2" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "alert",
    "message": "Your task has been updated",
    "priority": "high"
  }'
```

### Broadcast to All Users (Admin Only)

```bash
curl -X POST "http://localhost:8000/ws/secure/broadcast" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "system_announcement",
    "message": "Server maintenance in 10 minutes",
    "priority": "high"
  }'
```

---

## 🐍 Python Client Example

```python
import asyncio
import websockets
import json
import requests

async def connect_authenticated():
    # 1. Login
    response = requests.post(
        'http://localhost:8000/token',
        data={'username': 'admin@example.com', 'password': 'admin123'}
    )
    token = response.json()['access_token']

    # 2. Connect to WebSocket
    uri = f"ws://localhost:8000/ws/secure/chat/general?token={token}"

    async with websockets.connect(uri) as ws:
        # 3. Receive welcome
        welcome = await ws.recv()
        print(json.loads(welcome))

        # 4. Send message
        await ws.send(json.dumps({
            "type": "chat",
            "content": "Hello from Python!"
        }))

        # 5. Listen for messages
        async for message in ws:
            print(json.loads(message))

asyncio.run(connect_authenticated())
```

---

## 🌐 JavaScript Client Example

```javascript
class AuthenticatedWebSocketClient {
  constructor(endpoint, token) {
    this.endpoint = endpoint;
    this.token = token;
    this.ws = null;
  }

  connect() {
    const url = `${this.endpoint}?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("✅ Connected");
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = (event) => {
      console.log("❌ Disconnected:", event.code, event.reason);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case "welcome":
        console.log("Welcome:", data.message);
        break;
      case "chat":
        console.log(`${data.from.full_name}: ${data.content}`);
        break;
      case "user_joined":
        console.log(`${data.user.full_name} joined`);
        break;
      case "announcement":
        console.log("📢 ANNOUNCEMENT:", data.content);
        break;
      default:
        console.log("Message:", data);
    }
  }

  sendChat(message) {
    this.send({
      type: "chat",
      content: message,
    });
  }

  sendPrivate(userId, message) {
    this.send({
      type: "private",
      content: message,
      target_user_id: userId,
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
async function main() {
  // Get token
  const response = await fetch("/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      username: "admin@example.com",
      password: "admin123",
    }),
  });

  const { access_token } = await response.json();

  // Connect
  const client = new AuthenticatedWebSocketClient(
    "ws://localhost:8000/ws/secure/chat/general",
    access_token,
  );

  client.connect();

  // Send message after 1 second
  setTimeout(() => {
    client.sendChat("Hello from JavaScript!");
  }, 1000);
}

main();
```

---

## 🔐 Security Checklist

- [ ] **Use WSS in production** (wss:// not ws://)
- [ ] **Validate token before accepting connection**
- [ ] **Check user is active**
- [ ] **Implement rate limiting**
- [ ] **Validate all input**
- [ ] **Handle token expiration**
- [ ] **Use environment variables for secrets**
- [ ] **Log authentication failures**
- [ ] **Implement connection timeouts**
- [ ] **Monitor for suspicious activity**

---

## 🐛 Troubleshooting

### Connection Rejected

```
Error: WebSocket connection closed: code=1008, reason="Invalid token"
```

**Solutions:**

1. Check token is valid: `jwt.decode(token, SECRET_KEY)`
2. Verify user exists in database
3. Check user is active
4. Ensure token hasn't expired

### Can't Send Messages

```
Error: WebSocket is not open: readyState 3 (CLOSED)
```

**Solutions:**

1. Check connection is open: `ws.readyState === WebSocket.OPEN`
2. Verify token hasn't expired
3. Check server logs for errors
4. Reconnect with new token

### Messages Not Received

**Solutions:**

1. Check `onmessage` handler is set
2. Verify broadcasting logic
3. Check user is in correct room/channel
4. Test with multiple clients

---

## 📊 Message Types Reference

### Server → Client Messages

| Type              | Description             | Example                                                     |
| ----------------- | ----------------------- | ----------------------------------------------------------- |
| `welcome`         | Connection confirmation | `{type: "welcome", message: "Welcome!", user: {...}}`       |
| `echo`            | Echo response           | `{type: "echo", message: "Echo: hello", original: "hello"}` |
| `chat`            | Chat message            | `{type: "chat", content: "Hi", from: {...}}`                |
| `private_message` | Private DM              | `{type: "private_message", content: "Secret", from: {...}}` |
| `announcement`    | Admin broadcast         | `{type: "announcement", content: "Maintenance soon"}`       |
| `user_joined`     | User joined             | `{type: "user_joined", user: {...}}`                        |
| `user_left`       | User left               | `{type: "user_left", user: {...}}`                          |
| `error`           | Error message           | `{type: "error", message: "Invalid action"}`                |

### Client → Server Messages

| Type           | Description      | Format                                                |
| -------------- | ---------------- | ----------------------------------------------------- |
| `chat`         | Regular message  | `{type: "chat", content: "Hello"}`                    |
| `private`      | Private message  | `{type: "private", content: "Hi", target_user_id: 2}` |
| `announcement` | Admin only       | `{type: "announcement", content: "Notice"}`           |
| `typing`       | Typing indicator | `{type: "typing"}`                                    |

---

## 🎯 Common Use Cases

### 1. Real-time Chat

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/secure/chat/general?token=${token}`,
);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "chat") {
    displayMessage(msg.from.full_name, msg.content);
  }
};

function sendMessage(text) {
  ws.send(JSON.stringify({ type: "chat", content: text }));
}
```

### 2. Personal Notifications

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/secure/notifications?token=${token}`,
);

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  showNotification(notification.message, notification.priority);
};
```

### 3. Admin Broadcast

```javascript
// Admin sends to all users
fetch("/ws/secure/broadcast", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${adminToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    type: "system_announcement",
    message: "Server maintenance in 10 minutes",
    priority: "high",
  }),
});
```

---

## 📖 Further Reading

- [Full 1-Hour Lecture](WEBSOCKET_AUTHENTICATION_LECTURE.md)
- [WebSocket Basics](WEBSOCKET_LECTURE.md)
- [Architecture Guide](WEBSOCKET_ARCHITECTURE.md)
- [Implementation Details](WEBSOCKET_README.md)

---

**Happy coding! 🚀**
