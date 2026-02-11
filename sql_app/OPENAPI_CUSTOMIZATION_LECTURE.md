# OpenAPI Customization & API Documentation Best Practices
## Comprehensive 1-Hour FastAPI Lecture

---

## 📋 Table of Contents
1. [Introduction to OpenAPI](#1-introduction-to-openapi) (5 min)
2. [Customizing OpenAPI Schema](#2-customizing-openapi-schema) (15 min)
3. [Adding Descriptions and Examples](#3-adding-descriptions-and-examples) (15 min)
4. [Tagging and Organizing Endpoints](#4-tagging-and-organizing-endpoints) (10 min)
5. [API Versioning Strategies](#5-api-versioning-strategies) (10 min)
6. [RESTful Best Practices](#6-restful-best-practices) (5 min)
7. [Summary & Key Takeaways](#7-summary--key-takeaways) (5 min)

---

## 1. Introduction to OpenAPI
**Duration: 5 minutes**

### What is OpenAPI?

OpenAPI (formerly Swagger) is a specification for describing RESTful APIs. FastAPI automatically generates:
- **Interactive API documentation** (Swagger UI at `/docs`)
- **Alternative documentation** (ReDoc at `/redoc`)
- **OpenAPI schema** (JSON at `/openapi.json`)

### Why Customize OpenAPI?

```python
# Default FastAPI generates basic docs
from fastapi import FastAPI

app = FastAPI()  # Minimal documentation

# vs

app = FastAPI(
    title="Task Management API",
    description="A comprehensive task management system",
    version="2.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    }
)
```

**Benefits:**
- ✅ Professional appearance
- ✅ Better developer experience
- ✅ Clear API contracts
- ✅ Easier onboarding
- ✅ Self-service integration

---

## 2. Customizing OpenAPI Schema
**Duration: 15 minutes**

### 2.1 Application-Level Metadata

```python
from fastapi import FastAPI

app = FastAPI(
    title="E-Commerce API",
    description="""
    ## Features
    
    This API provides comprehensive e-commerce functionality:
    
    * **Products** - Create, read, update, and delete products
    * **Orders** - Order management and tracking
    * **Users** - User authentication and profiles
    * **Payments** - Secure payment processing
    
    ## Authentication
    
    Most endpoints require JWT authentication.
    Use the `/auth/login` endpoint to obtain a token.
    """,
    version="3.1.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support Team",
        "url": "https://example.com/support",
        "email": "api@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=[
        {
            "name": "products",
            "description": "Operations with products. The **Products** endpoint.",
        },
        {
            "name": "orders",
            "description": "Manage orders. So _fancy_ they have their own docs.",
            "externalDocs": {
                "description": "Orders external docs",
                "url": "https://example.com/docs/orders",
            },
        },
    ],
)
```

### 2.2 Custom OpenAPI Schema Function

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Custom API",
        version="2.5.0",
        description="This is a very custom OpenAPI schema",
        routes=app.routes,
    )
    
    # Add custom fields
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {"url": "https://api.example.com", "description": "Production"},
        {"url": "https://staging.example.com", "description": "Staging"},
        {"url": "http://localhost:8000", "description": "Development"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 2.3 Customizing Individual Endpoints

```python
from fastapi import FastAPI, Path, Query
from typing import Optional

app = FastAPI()

@app.get(
    "/items/{item_id}",
    summary="Retrieve an item",
    description="Get a single item by its unique identifier",
    response_description="The requested item",
    deprecated=False,
)
async def get_item(
    item_id: int = Path(..., description="The ID of the item to retrieve", ge=1),
    q: Optional[str] = Query(None, description="Optional search query")
):
    return {"item_id": item_id, "q": q}
```

### 2.4 Excluding Endpoints from Documentation

```python
@app.get("/hidden-endpoint", include_in_schema=False)
async def hidden_endpoint():
    """This endpoint won't appear in the OpenAPI docs"""
    return {"message": "Secret endpoint"}

# Useful for:
# - Internal endpoints
# - Health checks
# - Admin-only routes
# - Deprecated endpoints during migration
```

---

## 3. Adding Descriptions and Examples
**Duration: 15 minutes**

### 3.1 Pydantic Model Descriptions

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Product(BaseModel):
    """
    Product model representing items in the catalog
    """
    id: Optional[int] = Field(None, description="Unique product identifier")
    name: str = Field(
        ..., 
        description="Product name",
        min_length=1,
        max_length=100,
        example="Wireless Mouse"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed product description",
        example="Ergonomic wireless mouse with 6 programmable buttons"
    )
    price: float = Field(
        ...,
        description="Product price in USD",
        gt=0,
        example=29.99
    )
    stock: int = Field(
        default=0,
        description="Available quantity in inventory",
        ge=0,
        example=150
    )
    category: str = Field(
        ...,
        description="Product category",
        example="Electronics"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Wireless Mouse",
                "description": "Ergonomic wireless mouse with 6 programmable buttons",
                "price": 29.99,
                "stock": 150,
                "category": "Electronics"
            }
        }
```

### 3.2 Multiple Examples

```python
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe"
                },
                {
                    "username": "janedoe",
                    "email": "jane@example.com",
                    "full_name": "Jane Doe"
                }
            ]
        }
```

### 3.3 Request Body Examples

```python
from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

@app.post("/items/")
async def create_item(
    item: Item = Body(
        ...,
        example={
            "name": "Premium Coffee",
            "price": 12.99,
            "description": "Freshly roasted arabica beans"
        }
    )
):
    return item

# Multiple examples
@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: Item = Body(
        ...,
        examples={
            "normal": {
                "summary": "A normal example",
                "description": "A **normal** item works correctly.",
                "value": {
                    "name": "Regular Item",
                    "price": 9.99,
                    "description": "A standard item"
                },
            },
            "premium": {
                "summary": "A premium example",
                "description": "Premium items cost more",
                "value": {
                    "name": "Premium Item",
                    "price": 99.99,
                    "description": "A premium quality item"
                },
            },
            "invalid": {
                "summary": "Invalid data example",
                "description": "This will fail validation",
                "value": {
                    "name": "x",
                    "price": -10,
                },
            },
        },
    )
):
    return {"item_id": item_id, **item.dict()}
```

### 3.4 Response Examples

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
    price: float

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Coffee Maker",
                        "price": 79.99
                    }
                }
            }
        },
        404: {
            "description": "Item not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "item_id"],
                                "msg": "value is not a valid integer",
                                "type": "type_error.integer"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_item(item_id: int):
    return {"id": item_id, "name": "Coffee Maker", "price": 79.99}
```

### 3.5 Docstrings for Documentation

```python
@app.post("/users/", response_model=User)
async def create_user(user: User):
    """
    Create a new user with the following information:
    
    - **username**: unique username (required)
    - **email**: valid email address (required)
    - **full_name**: user's full name (optional)
    - **disabled**: account status (optional, defaults to False)
    
    The endpoint will:
    1. Validate the input data
    2. Check for duplicate usernames
    3. Hash the password
    4. Store the user in the database
    5. Return the created user object
    
    **Note**: Passwords are never returned in responses.
    """
    return user
```

---

## 4. Tagging and Organizing Endpoints
**Duration: 10 minutes**

### 4.1 Basic Tagging

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/", tags=["users"])
async def get_users():
    return [{"username": "john"}, {"username": "jane"}]

@app.get("/users/{user_id}", tags=["users"])
async def get_user(user_id: int):
    return {"username": "john", "id": user_id}

@app.get("/products/", tags=["products"])
async def get_products():
    return [{"name": "Widget"}, {"name": "Gadget"}]

@app.get("/products/{product_id}", tags=["products"])
async def get_product(product_id: int):
    return {"name": "Widget", "id": product_id}
```

### 4.2 Tag Metadata

```python
from fastapi import FastAPI

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "products",
        "description": "Manage products. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Product catalog documentation",
            "url": "https://example.com/docs/products",
        },
    },
    {
        "name": "orders",
        "description": "Order management and fulfillment",
    },
    {
        "name": "admin",
        "description": "Administrative operations (requires admin role)",
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.get("/users/", tags=["users"])
async def get_users():
    return []

@app.get("/products/", tags=["products"])
async def get_products():
    return []
```

### 4.3 Multiple Tags

```python
@app.get(
    "/analytics/user-purchases/",
    tags=["analytics", "users", "orders"],
    summary="Get user purchase analytics"
)
async def get_user_purchase_analytics():
    """
    This endpoint appears under multiple tags:
    - Analytics (primary category)
    - Users (related to users)
    - Orders (related to orders)
    """
    return {"total_purchases": 150, "average_value": 45.50}
```

### 4.4 APIRouter with Tags

```python
from fastapi import APIRouter, FastAPI

# Create routers with tags
user_router = APIRouter(prefix="/users", tags=["users"])
product_router = APIRouter(prefix="/products", tags=["products"])
order_router = APIRouter(prefix="/orders", tags=["orders"])

@user_router.get("/")
async def get_users():
    return []

@user_router.post("/")
async def create_user():
    return {}

@product_router.get("/")
async def get_products():
    return []

@product_router.post("/")
async def create_product():
    return {}

@order_router.get("/")
async def get_orders():
    return []

# Main app
app = FastAPI()
app.include_router(user_router)
app.include_router(product_router)
app.include_router(order_router)
```

### 4.5 Organizing a Large API

```python
# Structure for large applications
from fastapi import FastAPI
from .routers import users, products, orders, admin, analytics

app = FastAPI(
    title="Enterprise API",
    version="3.0.0",
    openapi_tags=[
        {"name": "authentication", "description": "Auth operations"},
        {"name": "users", "description": "User management"},
        {"name": "products", "description": "Product catalog"},
        {"name": "orders", "description": "Order processing"},
        {"name": "payments", "description": "Payment handling"},
        {"name": "analytics", "description": "Business analytics"},
        {"name": "admin", "description": "Admin operations"},
    ]
)

# Include routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(analytics.router)
```

---

## 5. API Versioning Strategies
**Duration: 10 minutes**

### 5.1 Version in Path (Recommended)

```python
from fastapi import FastAPI, APIRouter

app = FastAPI(title="Versioned API")

# Version 1 Router
v1_router = APIRouter(prefix="/v1")

@v1_router.get("/users/")
async def get_users_v1():
    return {"version": "1.0", "users": []}

@v1_router.get("/products/")
async def get_products_v1():
    return {"version": "1.0", "products": []}

# Version 2 Router
v2_router = APIRouter(prefix="/v2")

@v2_router.get("/users/")
async def get_users_v2():
    """
    Version 2: Returns enhanced user data with profile pictures
    """
    return {
        "version": "2.0",
        "users": [
            {"id": 1, "name": "John", "avatar_url": "https://..."}
        ]
    }

@v2_router.get("/products/")
async def get_products_v2():
    """
    Version 2: Includes inventory levels and ratings
    """
    return {
        "version": "2.0",
        "products": [
            {"id": 1, "name": "Widget", "stock": 100, "rating": 4.5}
        ]
    }

app.include_router(v1_router, tags=["v1"])
app.include_router(v2_router, tags=["v2"])
```

### 5.2 Version in Headers

```python
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

@app.get("/users/")
async def get_users(api_version: str = Header(default="1.0", alias="X-API-Version")):
    if api_version == "1.0":
        return {"version": "1.0", "users": [{"id": 1, "name": "John"}]}
    elif api_version == "2.0":
        return {
            "version": "2.0",
            "users": [{"id": 1, "name": "John", "avatar": "..."}]
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported API version")
```

### 5.3 Version in Query Parameters

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/users/")
async def get_users(version: str = Query(default="1.0", description="API version")):
    if version == "1.0":
        return {"users": []}
    elif version == "2.0":
        return {"users": [], "metadata": {"total": 0}}
    return {"error": "Unsupported version"}
```

### 5.4 Subdomain Versioning

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/users/")
async def get_users(request: Request):
    host = request.headers.get("host", "")
    
    if host.startswith("v1."):
        return {"version": "1.0", "users": []}
    elif host.startswith("v2."):
        return {"version": "2.0", "users": []}
    
    # Default to latest version
    return {"version": "2.0", "users": []}
```

### 5.5 Multiple FastAPI Apps (Best for Major Versions)

```python
# app_v1.py
from fastapi import FastAPI

app_v1 = FastAPI(title="API v1", version="1.0.0")

@app_v1.get("/users/")
async def get_users_v1():
    return {"users": []}

# app_v2.py
from fastapi import FastAPI

app_v2 = FastAPI(title="API v2", version="2.0.0")

@app_v2.get("/users/")
async def get_users_v2():
    return {"users": [], "total": 0}

# main.py
from fastapi import FastAPI
from .app_v1 import app_v1
from .app_v2 import app_v2

app = FastAPI()
app.mount("/v1", app_v1)
app.mount("/v2", app_v2)
```

### 5.6 Deprecation Strategy

```python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get(
    "/old-endpoint/",
    deprecated=True,
    summary="[DEPRECATED] Old Endpoint",
    description="""
    ⚠️ **This endpoint is deprecated and will be removed on 2024-12-31**
    
    Please migrate to `/v2/new-endpoint/`
    
    Migration guide: https://docs.example.com/migration/v1-to-v2
    """
)
async def old_endpoint():
    return {
        "message": "This endpoint is deprecated",
        "deprecation_date": "2024-01-01",
        "sunset_date": "2024-12-31",
        "migration_url": "https://docs.example.com/migration"
    }

@app.get("/v2/new-endpoint/")
async def new_endpoint():
    return {"message": "Use this endpoint instead"}
```

---

## 6. RESTful Best Practices
**Duration: 5 minutes**

### 6.1 HTTP Methods & Status Codes

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

# GET - Retrieve resources (200, 404)
@app.get("/items/", status_code=status.HTTP_200_OK)
async def list_items() -> List[Item]:
    return []

@app.get("/items/{item_id}", status_code=status.HTTP_200_OK)
async def get_item(item_id: int) -> Item:
    # Return 404 if not found
    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return Item(name="Widget", price=9.99)

# POST - Create new resource (201)
@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item) -> Item:
    return item

# PUT - Update/Replace entire resource (200, 204)
@app.put("/items/{item_id}", status_code=status.HTTP_200_OK)
async def update_item(item_id: int, item: Item) -> Item:
    return item

# PATCH - Partial update (200)
@app.patch("/items/{item_id}", status_code=status.HTTP_200_OK)
async def partial_update_item(item_id: int, name: str = None, price: float = None):
    return {"id": item_id, "updated_fields": ["name", "price"]}

# DELETE - Remove resource (204, 200)
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None  # 204 returns no content
```

### 6.2 Resource Naming Conventions

```python
# ✅ GOOD - Plural nouns for collections
@app.get("/users/")
@app.get("/products/")
@app.get("/orders/")

# ✅ GOOD - Singular resource by ID
@app.get("/users/{user_id}")
@app.get("/products/{product_id}")

# ✅ GOOD - Nested resources
@app.get("/users/{user_id}/orders/")
@app.get("/users/{user_id}/orders/{order_id}")

# ✅ GOOD - Actions as sub-resources
@app.post("/orders/{order_id}/cancel")
@app.post("/users/{user_id}/activate")

# ❌ BAD - Verbs in endpoints
@app.get("/getUsers/")
@app.post("/createProduct/")

# ❌ BAD - Mixed naming
@app.get("/user/")  # Should be /users/
@app.get("/products/{id}")  # Should be /products/{product_id}
```

### 6.3 Query Parameters for Filtering

```python
from fastapi import Query
from typing import Optional

@app.get("/products/")
async def get_products(
    # Filtering
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Only show in-stock items"),
    
    # Sorting
    sort_by: Optional[str] = Query("name", description="Sort field"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Search
    search: Optional[str] = Query(None, min_length=2, description="Search query"),
):
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "filters_applied": {
            "category": category,
            "price_range": [min_price, max_price],
            "in_stock": in_stock,
            "search": search
        }
    }
```

### 6.4 Consistent Response Structure

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response"""
    data: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[dict] = None

class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response"""
    success: bool = True
    data: T
    message: Optional[str] = None

# Usage
@app.get("/items/", response_model=PaginatedResponse[Item])
async def get_items(page: int = 1, page_size: int = 20):
    items = []  # Fetch from database
    total = 0
    
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        has_prev=page > 1
    )
```

### 6.5 HATEOAS (Hypermedia Links)

```python
from pydantic import BaseModel
from typing import Dict

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    _links: Dict[str, str]

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return ItemResponse(
        id=item_id,
        name="Widget",
        price=9.99,
        _links={
            "self": f"/items/{item_id}",
            "collection": "/items/",
            "update": f"/items/{item_id}",
            "delete": f"/items/{item_id}",
            "related_products": f"/items/{item_id}/related"
        }
    )
```

---

## 7. Summary & Key Takeaways
**Duration: 5 minutes**

### 🎯 Key Takeaways

1. **OpenAPI Customization**
   - Use FastAPI metadata for professional docs
   - Customize the schema for branding and additional info
   - Hide internal endpoints with `include_in_schema=False`

2. **Documentation Quality**
   - Add descriptions to all models and endpoints
   - Provide realistic examples
   - Use docstrings for complex logic

3. **Organization**
   - Tag endpoints logically
   - Use tag metadata with descriptions
   - Leverage APIRouter for modular structure

4. **Versioning**
   - Path-based versioning is most explicit (recommended)
   - Plan for deprecation from day one
   - Document breaking changes clearly

5. **RESTful Design**
   - Follow HTTP method semantics
   - Use appropriate status codes
   - Consistent naming (plural nouns, lowercase)
   - Pagination and filtering on collections

### 📚 Documentation Checklist

- [ ] Application metadata (title, description, version)
- [ ] All models have Field descriptions
- [ ] Realistic examples in schemas
- [ ] Endpoints have summaries and descriptions
- [ ] Response models defined
- [ ] Error responses documented
- [ ] Tags organized logically
- [ ] External documentation links
- [ ] Deprecation notices for old endpoints
- [ ] Versioning strategy implemented

### 🎨 Professional API Standards

```python
# Complete example combining all concepts
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional

# Models with examples
class Task(BaseModel):
    """Task model with complete documentation"""
    id: Optional[int] = Field(None, description="Unique task identifier")
    title: str = Field(..., description="Task title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Detailed description")
    completed: bool = Field(False, description="Completion status")
    priority: int = Field(1, ge=1, le=5, description="Priority (1-5)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Complete API documentation",
                "description": "Add examples and descriptions to all endpoints",
                "completed": False,
                "priority": 5
            }
        }

# Application setup
app = FastAPI(
    title="Task Manager API",
    description="Professional task management with complete documentation",
    version="2.0.0",
    contact={"name": "API Support", "email": "support@tasks.com"},
    openapi_tags=[
        {"name": "tasks", "description": "Task operations"},
        {"name": "users", "description": "User management"},
    ]
)

# Well-documented endpoint
@app.get(
    "/v2/tasks/",
    response_model=List[Task],
    tags=["tasks"],
    summary="List all tasks",
    description="Retrieve a paginated list of tasks with optional filtering",
    response_description="List of tasks matching the criteria",
)
async def list_tasks(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Comprehensive task listing with filtering and pagination.
    
    - **completed**: Filter by completion status
    - **priority**: Filter by priority level (1-5)
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    
    Returns a list of tasks with metadata for pagination.
    """
    return []

@app.post(
    "/v2/tasks/",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
    summary="Create a new task",
)
async def create_task(task: Task):
    """Create a new task with the provided details."""
    return task
```

---

## 🎓 What You've Learned

1. ✅ How to customize OpenAPI schema globally and per-endpoint
2. ✅ Adding comprehensive descriptions and examples to models
3. ✅ Organizing APIs with tags and metadata
4. ✅ Implementing API versioning strategies
5. ✅ Following RESTful best practices
6. ✅ Creating professional, self-documenting APIs

---

## 📝 Practice Assignment

See [OPENAPI_PRACTICE_ASSIGNMENT.md](./OPENAPI_PRACTICE_ASSIGNMENT.md) for hands-on exercises.

---

## 🔗 Additional Resources

- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Design Best Practices](https://restfulapi.net/)
- [API Versioning Strategies](https://www.freecodecamp.org/news/how-to-version-a-rest-api/)

---

**Next Steps**: Practice implementing these concepts in your API project!
