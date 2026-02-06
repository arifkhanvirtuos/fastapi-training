# 🚀 WebSocket Quick Start Guide

## ⚡ Get Started in 3 Steps

### Step 1: Start the Server (30 seconds)

```bash
cd sql_app
uvicorn main:app --reload
```

**Expected output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Open Test Interface (10 seconds)

Open your browser to: **http://localhost:8000/websocket-test**

### Step 3: Test WebSocket (1 minute)

1. Enter Client ID: `1`
2. Click **Connect**
3. Type "Hello!" and click **Send Message**
4. See the echo response! 🎉

---

## 🎯 What You Just Accomplished

✅ Started a FastAPI WebSocket server  
✅ Connected a client to the server  
✅ Sent and received real-time messages  
✅ Experienced bidirectional communication

---

## 🔥 Try This Next

### Multi-Client Broadcasting

1. Open **3 browser tabs** to the test page
2. Connect as Client #1, #2, and #3
3. Send a message from Client #1
4. Watch it appear in ALL tabs! 🌐

**You'll see:**

- Tab 1: "Echo: [your message]" + broadcast notification
- Tab 2: "Client #1: [your message]"
- Tab 3: "Client #1: [your message]"

---

## 📚 Learning Path

### 🎓 Complete Tutorial (1 hour)

Read: [`WEBSOCKET_LECTURE.md`](WEBSOCKET_LECTURE.md)

**Covers:**

- WebSocket protocol fundamentals
- FastAPI WebSocket implementation
- Creating endpoints
- Authentication
- Broadcasting
- Best practices
- Complete assignment

### 🔧 Implementation Guide

Read: [`sql_app/WEBSOCKET_README.md`](sql_app/WEBSOCKET_README.md)

**Includes:**

- Architecture overview
- Code examples
- Testing instructions
- Troubleshooting

### 🏗️ Architecture Diagram

Read: [`WEBSOCKET_ARCHITECTURE.md`](WEBSOCKET_ARCHITECTURE.md)

**Shows:**

- Visual flow diagrams
- Message formats
- Connection states
- Technology stack

---

## 💡 Common Use Cases

### 1. Real-Time Chat

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat/general/YourName");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send("Hello, everyone!");
```

### 2. Live Notifications

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/echo/1");
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  showNotification(data.message);
};
```

### 3. Real-Time Data Feed

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/echo/monitor");
ws.onmessage = (e) => {
  updateDashboard(JSON.parse(e.data));
};
```

---

## 🐛 Quick Troubleshooting

### Problem: Can't connect

**Solution:**

```bash
# Check if server is running
curl http://localhost:8000

# Restart server
uvicorn main:app --reload
```

### Problem: Port already in use

**Solution:**

```bash
# Use different port
uvicorn main:app --reload --port 8001
```

### Problem: Messages not appearing

**Solution:**

- Check browser console (F12)
- Verify connection status is "Connected"
- Try disconnecting and reconnecting

---

## 📊 Check Connection Statistics

Visit: **http://localhost:8000/ws/stats**

**Returns:**

```json
{
  "active_connections": 3,
  "clients": [{ "client_id": "1", "connected_at": "2026-02-03T10:30:00Z" }],
  "timestamp": "2026-02-03T10:35:00Z"
}
```

---

## 🎨 Customize the Test Interface

The HTML test page is embedded in `sql_app/main.py`.

**Find this function:**

```python
@app.get("/websocket-test", response_class=HTMLResponse)
async def websocket_test_page():
    html_content = """
    <!-- Customize HTML here -->
    """
```

---

## 🔐 Add Authentication (5 minutes)

### Option 1: Token in URL

```javascript
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws/echo/1?token=${token}`);
```

### Option 2: Check token in endpoint

```python
@app.websocket("/ws/secure/{client_id}")
async def secure_endpoint(websocket: WebSocket, client_id: int):
    token = websocket.query_params.get("token")
    if not validate_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    # ... rest of code
```

---

## 📱 Test from Mobile

1. Find your computer's IP address:

   ```bash
   ipconfig getifaddr en0  # macOS
   ```

2. Update WebSocket URL in the test page:

   ```javascript
   ws = new WebSocket(`ws://YOUR_IP:8000/ws/echo/${clientId}`);
   ```

3. Open on mobile browser:
   ```
   http://YOUR_IP:8000/websocket-test
   ```

---

## 🧪 Python Client Example

```python
import asyncio
import websockets
import json

async def test_echo():
    uri = "ws://localhost:8000/ws/echo/999"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send("Hello from Python!")

        # Receive echo
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Received: {data['message']}")

# Run it
asyncio.run(test_echo())
```

---

## 📈 Scaling Tips

### For 100+ Concurrent Users

- Use Redis for pub/sub
- Implement load balancing
- Add connection limits

### For Production

- Use WSS (secure WebSocket)
- Add authentication
- Implement rate limiting
- Monitor connections
- Set up logging

---

## 🎯 Next Challenges

### Challenge 1: Private Messages

Modify the code to send messages to specific clients only.

### Challenge 2: User List

Display list of all connected users.

### Challenge 3: Message History

Store messages in database and show history on connect.

### Challenge 4: Typing Indicator

Show "User is typing..." when someone is typing.

### Challenge 5: File Sharing

Enable file uploads through WebSocket.

---

## 📞 Get Help

### Resources

- 📚 Main Lecture: [`WEBSOCKET_LECTURE.md`](WEBSOCKET_LECTURE.md)
- 📖 Implementation Guide: [`sql_app/WEBSOCKET_README.md`](sql_app/WEBSOCKET_README.md)
- 🏗️ Architecture: [`WEBSOCKET_ARCHITECTURE.md`](WEBSOCKET_ARCHITECTURE.md)
- 📋 Summary: [`WEBSOCKET_IMPLEMENTATION_SUMMARY.md`](WEBSOCKET_IMPLEMENTATION_SUMMARY.md)

### Official Docs

- [FastAPI WebSocket Docs](https://fastapi.tiangolo.com/advanced/websockets/)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [RFC 6455 (WebSocket Protocol)](https://tools.ietf.org/html/rfc6455)

---

## ✅ Quick Reference

### Start Server

```bash
cd sql_app && uvicorn main:app --reload
```

### Test Page

```
http://localhost:8000/websocket-test
```

### Echo Endpoint

```
ws://localhost:8000/ws/echo/1
```

### Chat Room

```
ws://localhost:8000/ws/chat/general/YourName
```

### Statistics

```
http://localhost:8000/ws/stats
```

### API Docs

```
http://localhost:8000/docs
```

---

## 🎉 Success!

You now have a **fully functional WebSocket server** with:

- ✅ Real-time bidirectional communication
- ✅ Broadcasting to multiple clients
- ✅ Beautiful test interface
- ✅ Chat room functionality
- ✅ Connection statistics
- ✅ Production-ready code

**Time invested:** 3 minutes  
**Knowledge gained:** Real-time web development with WebSockets! 🚀

---

_Happy coding! 🎨_

---

## 📸 Expected Results

### Initial Connection

```
Status: ✅ Connected
Messages:
  ℹ️ Connected as Client #1        10:30:15
```

### After Sending Message

```
Status: ✅ Connected
Messages:
  ℹ️ Connected as Client #1        10:30:15
  📤 You: Hello!                   10:30:20
  🔄 Echo: Hello!                  10:30:20

Statistics:
  Messages Sent: 1
  Messages Received: 1
  Connected Time: 0:05
```

### With Multiple Clients

```
Status: ✅ Connected
Messages:
  ℹ️ Connected as Client #1        10:30:15
  📢 Client #2 joined the chat     10:30:25
  📤 You: Hi everyone!             10:30:30
  🔄 Echo: Hi everyone!            10:30:30
  📢 Client #3 joined the chat     10:30:35
```

---

**Ready? Let's go! 🚀**

```bash
cd sql_app && uvicorn main:app --reload
```

Then open: **http://localhost:8000/websocket-test**
