# FastAPI Annotations: Complete One-Hour Lecture

## Table of Contents

1. [Introduction (5 min)](#1-introduction)
2. [Python Type Hints Basics (10 min)](#2-python-type-hints-basics)
3. [Path Parameters (8 min)](#3-path-parameters)
4. [Query Parameters (8 min)](#4-query-parameters)
5. [Request Body & Pydantic Models (10 min)](#5-request-body--pydantic-models)
6. [Response Models & Status Codes (7 min)](#6-response-models--status-codes)
7. [Dependency Injection (7 min)](#7-dependency-injection)
8. [Advanced Annotations (5 min)](#8-advanced-annotations)

---

## 1. Introduction (5 min)

### What are Annotations in FastAPI?

Annotations in FastAPI are Python type hints that serve multiple purposes:

- **Type checking**: Validate data types at runtime
- **Automatic validation**: Convert and validate incoming data
- **Documentation**: Auto-generate OpenAPI/Swagger docs
- **Editor support**: Better autocomplete and type checking

### Why FastAPI Loves Annotations?

FastAPI is built on top of:

- **Pydantic**: Data validation using Python type annotations
- **Starlette**: Web framework foundation
- **Type hints**: Python 3.6+ feature

```python
from fastapi import FastAPI

app = FastAPI()

# Without annotations (bad practice)
@app.get("/old")
def old_way(name, age):
    return {"name": name, "age": age}

# With annotations (FastAPI way)
@app.get("/new")
def new_way(name: str, age: int):
    return {"name": name, "age": age}
```

---

## 2. Python Type Hints Basics (10 min)

### Basic Types

```python
from typing import Optional, List, Dict, Set, Tuple, Union

# Simple types
name: str = "John"
age: int = 30
height: float = 5.9
is_active: bool = True

# Collections
names: List[str] = ["John", "Jane"]
user_data: Dict[str, int] = {"age": 30, "score": 100}
unique_ids: Set[int] = {1, 2, 3}
coordinates: Tuple[float, float] = (10.5, 20.3)

# Optional values (can be None)
middle_name: Optional[str] = None
# Equivalent to:
middle_name: Union[str, None] = None

# Python 3.10+ syntax
middle_name: str | None = None
```

### Generic Types for FastAPI

```python
from typing import Any, Union
from pydantic import BaseModel

# Union types (Python 3.10+)
def process(value: int | str) -> dict:
    return {"value": value}

# Any type (avoid when possible)
def flexible(data: Any) -> Any:
    return data

# Pydantic models (most common in FastAPI)
class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None
```

### Why Types Matter in FastAPI

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/calculate")
def calculate(num1: int, num2: int):
    """
    FastAPI automatically:
    1. Validates num1 and num2 are integers
    2. Converts string inputs to integers
    3. Returns 422 error if conversion fails
    4. Documents parameters in OpenAPI schema
    """
    return {"result": num1 + num2}

# Try: GET /calculate?num1=10&num2=20 → Works
# Try: GET /calculate?num1=abc&num2=20 → 422 Error
```

---

## 3. Path Parameters (8 min)

### Basic Path Parameters

```python
from fastapi import FastAPI, Path

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """user_id is extracted from URL and validated as int"""
    return {"user_id": user_id}

# Multiple path parameters
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id}
```

### Path Parameters with Validation

```python
from fastapi import Path

@app.get("/items/{item_id}")
def get_item(
    item_id: int = Path(
        ...,  # Required (ellipsis means required)
        title="Item ID",
        description="The ID of the item to retrieve",
        ge=1,  # Greater than or equal to 1
        le=1000  # Less than or equal to 1000
    )
):
    return {"item_id": item_id}

# String path parameter with pattern
@app.get("/users/{username}")
def get_user_by_name(
    username: str = Path(
        ...,
        min_length=3,
        max_length=50,
        regex="^[a-zA-Z0-9_]+$"  # Alphanumeric and underscore only
    )
):
    return {"username": username}
```

### Enum Path Parameters

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    """Only accepts: alexnet, resnet, or lenet"""
    if model_name == ModelName.alexnet:
        return {"model": "AlexNet", "message": "Deep Learning FTW!"}

    return {"model": model_name.value}
```

---

## 4. Query Parameters (8 min)

### Basic Query Parameters

```python
from fastapi import Query
from typing import Optional

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    """
    GET /items/?skip=5&limit=20
    skip and limit are query parameters with defaults
    """
    return {"skip": skip, "limit": limit}

# Optional query parameters
@app.get("/search/")
def search(q: Optional[str] = None, page: int = 1):
    """q is optional (can be omitted)"""
    if q:
        return {"query": q, "page": page}
    return {"message": "No query provided"}
```

### Query Parameters with Validation

```python
from typing import List

@app.get("/items/")
def read_items(
    q: Optional[str] = Query(
        None,  # Default value
        min_length=3,
        max_length=50,
        regex="^[a-zA-Z]+$",
        title="Query string",
        description="Search query for filtering items",
        deprecated=False
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of items to return"
    )
):
    return {"q": q, "limit": limit}

# Required query parameter
@app.get("/required/")
def required_query(name: str = Query(..., min_length=1)):
    """name is required (must be provided)"""
    return {"name": name}
```

### Multiple Values & Lists

```python
# List of query parameters
@app.get("/items/")
def read_items(
    tags: List[str] = Query(
        [],  # Default empty list
        title="Tags",
        description="List of tags to filter by"
    )
):
    """
    GET /items/?tags=python&tags=fastapi&tags=web
    tags = ["python", "fastapi", "web"]
    """
    return {"tags": tags}

# Alternative: comma-separated
@app.get("/items/")
def read_items_alt(tags: Optional[str] = Query(None)):
    """Parse comma-separated manually if needed"""
    tag_list = tags.split(",") if tags else []
    return {"tags": tag_list}
```

### Boolean Query Parameters

```python
@app.get("/items/")
def read_items(
    is_active: bool = Query(True),
    include_deleted: bool = False
):
    """
    GET /items/?is_active=false&include_deleted=1
    Accepts: true/false, 1/0, yes/no, on/off
    """
    return {"is_active": is_active, "include_deleted": include_deleted}
```

---

## 5. Request Body & Pydantic Models (10 min)

### Basic Request Body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@app.post("/items/")
def create_item(item: Item):
    """
    POST /items/
    Body: {"name": "Laptop", "price": 999.99}

    FastAPI automatically:
    1. Reads request body as JSON
    2. Validates against Item model
    3. Converts to Item instance
    """
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

### Pydantic Model Validation

```python
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime

class User(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex="^[a-zA-Z0-9_]+$"
    )
    email: EmailStr  # Validates email format
    age: int = Field(..., ge=0, le=150)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    # Custom validator
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum() or '_' in v, 'must be alphanumeric'
        return v

    # Config
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "age": 30
            }
        }

@app.post("/users/")
def create_user(user: User):
    return user
```

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str
    zip_code: Optional[str] = None

class Company(BaseModel):
    name: str
    address: Address

class Employee(BaseModel):
    name: str
    email: EmailStr
    company: Company
    skills: List[str] = []

@app.post("/employees/")
def create_employee(employee: Employee):
    """
    POST /employees/
    Body: {
        "name": "John",
        "email": "john@example.com",
        "company": {
            "name": "TechCorp",
            "address": {
                "street": "123 Main St",
                "city": "NYC",
                "country": "USA"
            }
        },
        "skills": ["Python", "FastAPI"]
    }
    """
    return employee
```

### Multiple Body Parameters

```python
from fastapi import Body

class Item(BaseModel):
    name: str
    price: float

class User(BaseModel):
    username: str
    email: EmailStr

@app.post("/combined/")
def create_combined(
    item: Item,
    user: User,
    importance: int = Body(...)
):
    """
    POST /combined/
    Body: {
        "item": {"name": "Laptop", "price": 999},
        "user": {"username": "john", "email": "john@example.com"},
        "importance": 5
    }
    """
    return {"item": item, "user": user, "importance": importance}

# Single body parameter (not nested)
@app.post("/items/")
def create_item(
    item: Item = Body(..., embed=True)
):
    """
    embed=True requires: {"item": {"name": "...", "price": ...}}
    embed=False allows: {"name": "...", "price": ...}
    """
    return item
```

---

## 6. Response Models & Status Codes (7 min)

### Response Model Annotation

```python
from typing import List

class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserOut(BaseModel):
    username: str
    email: EmailStr
    # Note: password is excluded

@app.post("/users/", response_model=UserOut)
def create_user(user: UserIn):
    """
    Response model filters output:
    - Only returns fields in UserOut
    - Password is automatically excluded
    """
    return user

# List response
@app.get("/users/", response_model=List[UserOut])
def list_users():
    users = [
        {"username": "john", "email": "john@example.com", "password": "secret"},
        {"username": "jane", "email": "jane@example.com", "password": "secret"}
    ]
    return users  # Passwords automatically filtered
```

### Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    """Returns 201 Created instead of default 200 OK"""
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    """Returns 204 No Content (no body)"""
    return None

# Common status codes:
# status.HTTP_200_OK
# status.HTTP_201_CREATED
# status.HTTP_204_NO_CONTENT
# status.HTTP_400_BAD_REQUEST
# status.HTTP_401_UNAUTHORIZED
# status.HTTP_403_FORBIDDEN
# status.HTTP_404_NOT_FOUND
# status.HTTP_422_UNPROCESSABLE_ENTITY
# status.HTTP_500_INTERNAL_SERVER_ERROR
```

### Response Model Config

```python
class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    tax: Optional[float] = None

@app.get("/items/{item_id}", response_model=Item, response_model_exclude_unset=True)
def get_item(item_id: int):
    """
    Only returns fields that were set:
    - If tax is None, it won't appear in response
    """
    return {"name": "Laptop", "price": 999.99}

# Other options:
@app.get("/items/", response_model=Item, response_model_exclude={"tax"})
def list_items():
    """Excludes 'tax' from all responses"""
    pass

@app.get("/items/", response_model=Item, response_model_include={"name", "price"})
def list_items_minimal():
    """Only includes 'name' and 'price'"""
    pass
```

---

## 7. Dependency Injection (7 min)

### Basic Dependencies

```python
from fastapi import Depends

# Dependency function
def common_parameters(q: Optional[str] = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
def read_items(commons: dict = Depends(common_parameters)):
    """
    Automatically calls common_parameters and injects result
    GET /items/?q=search&skip=10&limit=20
    commons = {"q": "search", "skip": 10, "limit": 20}
    """
    return commons

@app.get("/users/")
def read_users(commons: dict = Depends(common_parameters)):
    """Reuses the same dependency"""
    return commons
```

### Class-Based Dependencies

```python
class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
def read_items(commons: CommonQueryParams = Depends(CommonQueryParams)):
    """
    Creates instance of CommonQueryParams
    Access: commons.q, commons.skip, commons.limit
    """
    return {"q": commons.q, "skip": commons.skip, "limit": commons.limit}

# Shorthand (when parameter name matches class name)
@app.get("/items/")
def read_items(commons: CommonQueryParams = Depends()):
    return commons
```

### Dependency with Database

```python
from sqlalchemy.orm import Session

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    """
    db is automatically injected and closed after request
    """
    users = db.query(User).all()
    return users

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Security Dependencies

```python
from fastapi import Header, HTTPException

def verify_token(x_token: str = Header(...)):
    """Header dependency for authentication"""
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="Invalid token")
    return x_token

def verify_key(x_key: str = Header(...)):
    if x_key != "secret-key":
        raise HTTPException(status_code=400, detail="Invalid key")
    return x_key

@app.get("/protected/")
def protected_route(
    token: str = Depends(verify_token),
    key: str = Depends(verify_key)
):
    """
    Requires both headers:
    X-Token: secret-token
    X-Key: secret-key
    """
    return {"message": "Access granted"}
```

### Global Dependencies

```python
# Apply dependency to all routes
app = FastAPI(dependencies=[Depends(verify_token)])

@app.get("/items/")
def read_items():
    """Automatically requires token"""
    return {"items": []}

@app.get("/users/")
def read_users():
    """Also requires token"""
    return {"users": []}
```

---

## 8. Advanced Annotations (5 min)

### Cookie and Header Parameters

```python
from fastapi import Cookie, Header

@app.get("/items/")
def read_items(
    user_agent: Optional[str] = Header(None),
    session_id: Optional[str] = Cookie(None)
):
    """
    Reads from HTTP headers and cookies
    user_agent reads "User-Agent" header
    session_id reads "session_id" cookie
    """
    return {"user_agent": user_agent, "session_id": session_id}
```

### File Upload Annotations

```python
from fastapi import File, UploadFile

@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    """
    POST /upload/
    Content-Type: multipart/form-data
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }

# Multiple files
@app.post("/upload-multiple/")
def upload_multiple(files: List[UploadFile] = File(...)):
    return [{"filename": f.filename} for f in files]
```

### Form Data

```python
from fastapi import Form

@app.post("/login/")
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    """
    POST /login/
    Content-Type: application/x-www-form-urlencoded
    username=john&password=secret
    """
    return {"username": username}
```

### Annotated Type (Python 3.9+)

```python
from typing import Annotated

# Reusable annotations
UserIdPath = Annotated[int, Path(ge=1, le=1000)]
QueryString = Annotated[Optional[str], Query(min_length=3, max_length=50)]

@app.get("/users/{user_id}")
def get_user(user_id: UserIdPath, q: QueryString = None):
    """Cleaner syntax with Annotated"""
    return {"user_id": user_id, "q": q}
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")

@app.post("/send-notification/")
def send_notification(
    email: EmailStr,
    background_tasks: BackgroundTasks
):
    """
    background_tasks annotation allows async processing
    """
    background_tasks.add_task(write_log, f"Notification sent to {email}")
    return {"message": "Notification sent"}
```

### Generic Response Types

```python
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

@app.get("/json/")
def get_json():
    """Default response is JSONResponse"""
    return {"message": "JSON"}

@app.get("/html/", response_class=HTMLResponse)
def get_html():
    """Returns HTML content"""
    return "<h1>Hello World</h1>"

@app.get("/text/", response_class=PlainTextResponse)
def get_text():
    """Returns plain text"""
    return "Hello World"
```

---

## Practice Examples

### Complete CRUD API with All Annotations

```python
from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

# Fake database
fake_users_db: List[UserInDB] = []
user_id_counter = 1

# Dependencies
def get_user_or_404(
    user_id: int = Path(..., ge=1, description="User ID")
) -> UserInDB:
    for user in fake_users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

# Routes
@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    global user_id_counter
    user_dict = user.dict()
    user_dict.pop("password")  # Don't store in fake DB
    db_user = UserInDB(
        id=user_id_counter,
        created_at=datetime.utcnow(),
        **user_dict
    )
    fake_users_db.append(db_user)
    user_id_counter += 1
    return db_user

@app.get("/users/", response_model=List[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None
):
    users = fake_users_db
    if is_active is not None:
        users = [u for u in users if u.is_active == is_active]
    return users[skip : skip + limit]

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user: UserInDB = Depends(get_user_or_404)):
    return user

@app.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_update: UserUpdate,
    user: UserInDB = Depends(get_user_or_404)
):
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    return user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: UserInDB = Depends(get_user_or_404)):
    fake_users_db.remove(user)
    return None
```

---

## Key Takeaways

1. **Type hints are the foundation**: Everything in FastAPI starts with Python type annotations
2. **Automatic validation**: FastAPI validates all annotated parameters automatically
3. **Documentation is free**: OpenAPI/Swagger docs are generated from annotations
4. **Pydantic models**: Use for request/response body validation
5. **Path/Query/Body**: Different annotations for different parameter sources
6. **Dependencies**: Use `Depends()` for reusable logic and injection
7. **response_model**: Controls what data is returned to clients
8. **Validation helpers**: Use `Field()`, `Query()`, `Path()`, `Body()` for advanced validation

## Resources for Further Learning

1. **FastAPI Documentation**: https://fastapi.tiangolo.com/
2. **Pydantic Documentation**: https://docs.pydantic.dev/
3. **Python Type Hints**: https://docs.python.org/3/library/typing.html
4. **OpenAPI Specification**: https://swagger.io/specification/

---

## Homework Assignment

Create a complete Book Library API with the following requirements:

1. **Book Model** with validation for:
   - ISBN (regex pattern)
   - Title (3-200 chars)
   - Author (not empty)
   - Publication year (1000-2026)
   - Price (positive float)

2. **Endpoints**:
   - POST /books/ (create book)
   - GET /books/ (list with pagination and filtering)
   - GET /books/{isbn} (get single book)
   - PATCH /books/{isbn} (update book)
   - DELETE /books/{isbn} (delete book)

3. **Use**:
   - Path parameters with validation
   - Query parameters for search/filter
   - Pydantic models for request/response
   - Dependencies for common parameters
   - Proper status codes
   - Response models

Good luck! 🚀
