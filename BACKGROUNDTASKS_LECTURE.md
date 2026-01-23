# FastAPI BackgroundTasks - 1 Hour Training Session

**Duration:** 1 hour  
**Level:** Intermediate  
**Objective:** Learn to handle long-running operations without blocking API responses

---

## 1. Introduction to BackgroundTasks (10 mins)

### What are Background Tasks?

Background tasks allow you to run operations **after** returning a response to the client. The client doesn't wait for these tasks to complete.

### Why Use Background Tasks?

- **Faster Response Times**: Return responses immediately
- **Better User Experience**: Don't make users wait for non-critical operations
- **Simple Implementation**: No need for complex queue systems for basic tasks

### Common Use Cases

- Sending emails (welcome emails, notifications)
- Generating reports or PDFs
- Logging activities
- Processing uploaded files
- Sending webhooks
- Updating analytics or metrics

---

## 2. BackgroundTasks API Basics (15 mins)

### Simple Example

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

def write_log(message: str):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{message}\n")

@app.post("/send-notification/")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, f"Notification sent to {email}")
    return {"message": "Notification sent in the background"}
```

### Key Components

1. **Import BackgroundTasks**: `from fastapi import BackgroundTasks`
2. **Add as Dependency**: Include `background_tasks: BackgroundTasks` in function parameters
3. **Add Tasks**: Use `background_tasks.add_task(function, *args, **kwargs)`

### Multiple Background Tasks

```python
@app.post("/user/register/")
async def register_user(email: str, background_tasks: BackgroundTasks):
    # Add multiple tasks
    background_tasks.add_task(send_welcome_email, email)
    background_tasks.add_task(update_analytics, "new_user")
    background_tasks.add_task(notify_admin, email)

    return {"message": "User registered successfully"}
```

---

## 3. Async vs Sync Functions (10 mins)

### Sync Background Function

```python
def send_email(email: str, message: str):
    # Synchronous operation
    import time
    time.sleep(2)  # Simulating email sending
    print(f"Email sent to {email}: {message}")

@app.post("/notify/")
async def notify(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Hello!")
    return {"message": "Notification queued"}
```

### Async Background Function

```python
async def send_email_async(email: str, message: str):
    # Asynchronous operation
    import asyncio
    await asyncio.sleep(2)  # Simulating async email sending
    print(f"Email sent to {email}: {message}")

@app.post("/notify-async/")
async def notify_async(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_async, email, "Hello!")
    return {"message": "Notification queued"}
```

### When to Use Which?

| Use Sync                           | Use Async                           |
| ---------------------------------- | ----------------------------------- |
| File I/O operations                | HTTP requests with async libraries  |
| Database operations (sync drivers) | Database operations (async drivers) |
| Image processing                   | Async API calls                     |
| Simple logging                     | WebSocket operations                |

**Rule of Thumb**: If your function uses `await`, make it `async`. Otherwise, use regular sync functions.

---

## 4. When to Use Background Tasks (10 mins)

### ✅ Good Use Cases

1. **Email Sending**

   ```python
   background_tasks.add_task(send_welcome_email, user.email)
   ```

2. **File Processing**

   ```python
   background_tasks.add_task(resize_image, uploaded_file)
   ```

3. **Audit Logging**

   ```python
   background_tasks.add_task(log_user_action, user_id, action)
   ```

4. **Notifications**
   ```python
   background_tasks.add_task(send_sms_notification, phone, message)
   ```

### ❌ When NOT to Use Background Tasks

1. **Critical Operations**: Don't use for operations that MUST complete (e.g., payment processing)
2. **Long-Running Tasks** (>30 seconds): Use task queues like Celery instead
3. **Tasks Requiring Retry Logic**: BackgroundTasks don't have built-in retry mechanisms
4. **Tasks Needing Status Tracking**: You can't check if background tasks completed

### Example: Good vs Bad

```python
# ❌ BAD - Critical payment processing
@app.post("/process-payment/")
async def process_payment(payment_data: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(charge_credit_card, payment_data)  # DON'T!
    return {"status": "payment processing"}

# ✅ GOOD - Send receipt after payment
@app.post("/process-payment/")
async def process_payment(payment_data: dict, background_tasks: BackgroundTasks):
    result = charge_credit_card(payment_data)  # Process immediately
    background_tasks.add_task(send_receipt_email, payment_data.email)  # Background
    return {"status": "payment successful", "transaction_id": result.id}
```

---

## 5. Limitations and Alternatives (10 mins)

### BackgroundTasks Limitations

1. **No Persistence**: If the server crashes, background tasks are lost
2. **No Retry Mechanism**: Failed tasks don't automatically retry
3. **No Result Tracking**: You can't check task status or get results
4. **Server-Bound**: Tasks run on the same server that handled the request
5. **Not Scalable**: For high-volume tasks, performance degrades

### When You Need More: Task Queues

#### Celery (Popular Choice)

**Use Celery when you need:**

- Task persistence (tasks survive server restarts)
- Retry mechanisms
- Scheduled/periodic tasks
- Result tracking
- Distributed task processing
- Task prioritization

#### Quick Celery Example

```python
# celery_tasks.py
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def send_email_task(email: str):
    # Email sending logic
    return f"Email sent to {email}"

# main.py
from celery_tasks import send_email_task

@app.post("/send-email/")
async def send_email(email: str):
    # Queue task in Celery
    send_email_task.delay(email)
    return {"message": "Email queued"}
```

### Decision Guide

```
Is the task critical?
  → YES: Don't use BackgroundTasks, process immediately

Is the task < 5 seconds?
  → YES: Use BackgroundTasks
  → NO: Continue...

Do you need retry logic or status tracking?
  → YES: Use Celery/RQ
  → NO: BackgroundTasks might work

Do you have high volume (>100 tasks/minute)?
  → YES: Use Celery/RQ
  → NO: BackgroundTasks is fine
```

---

## 6. Practice Assignment (5 mins explanation)

### Assignment: Email Notification System

**Objective**: Build an endpoint that creates a user and sends a welcome email in the background.

**Requirements**:

1. Create a `POST /users/register` endpoint
2. Accept user data: `email`, `name`, `phone_number`
3. Save user to database (can be simulated)
4. Send welcome email as a background task
5. Log the email activity
6. Return response immediately without waiting for email

**Bonus Challenges**:

- Add multiple background tasks (send email + send SMS + log analytics)
- Simulate email failures and see what happens
- Compare response times with/without background tasks

### Starter Code Template

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, EmailStr
import time

app = FastAPI()

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    phone_number: str

def send_welcome_email(email: str, name: str):
    """Simulate sending email"""
    time.sleep(3)  # Simulate email service delay
    print(f"✅ Welcome email sent to {email} for {name}")

def log_registration(email: str):
    """Log user registration"""
    with open("registrations.log", "a") as f:
        f.write(f"New user registered: {email}\n")

@app.post("/users/register")
async def register_user(user: UserRegister, background_tasks: BackgroundTasks):
    # TODO: Implement your solution here
    pass
```

### Expected Output

```json
// Response (immediate, < 100ms)
{
  "message": "User registered successfully",
  "user_id": "123",
  "email_status": "queued"
}

// Console (after ~3 seconds)
✅ Welcome email sent to user@example.com for John Doe
```

---

## Key Takeaways

1. **BackgroundTasks** are perfect for **simple, non-critical** operations that can run after response
2. Use them for **emails, logging, notifications** - things users don't need to wait for
3. Both **sync and async** functions work - choose based on your operation type
4. **Don't use** for critical operations, long tasks (>30s), or tasks needing retry logic
5. For production-scale applications with complex needs, graduate to **Celery** or **RQ**
6. Background tasks make APIs **faster and more responsive** for end users

---

## Additional Resources

- [FastAPI BackgroundTasks Documentation](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [RQ (Redis Queue) - Simpler Alternative](https://python-rq.org/)

---

## Q&A Session (remaining time)

**Common Questions:**

**Q: Can I pass database sessions to background tasks?**  
A: No! Database sessions are request-scoped. Create a new session inside the background task.

**Q: How many background tasks can I add?**  
A: No hard limit, but keep it reasonable (< 5 per request). Too many affects performance.

**Q: Do background tasks run in parallel?**  
A: No, they run sequentially in the order added.

**Q: What if a background task fails?**  
A: It silently fails. No automatic retry. Use proper task queue for critical tasks.

**Q: Can I use BackgroundTasks with dependencies?**  
A: Yes! BackgroundTasks is injected like any other dependency.

---

**End of Training Session**
