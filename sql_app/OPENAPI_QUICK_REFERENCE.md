# OpenAPI Customization - Quick Reference Guide

## 📚 Quick Links

- **Main Lecture**: [OPENAPI_CUSTOMIZATION_LECTURE.md](./OPENAPI_CUSTOMIZATION_LECTURE.md)
- **Practice Assignment**: [OPENAPI_PRACTICE_ASSIGNMENT.md](./OPENAPI_PRACTICE_ASSIGNMENT.md)
- **Working Example**: [openapi_example.py](./openapi_example.py)

---

## ⚡ Quick Reference

### 1. FastAPI App Metadata

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="API description with **markdown**",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "http://example.com/contact",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

---

### 2. Model with Examples

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., description="Item name", example="Widget")
    price: float = Field(..., gt=0, description="Price in USD", example=29.99)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Gaming Mouse",
                "price": 49.99
            }
        }
```

---

### 3. Endpoint Documentation

```python
@app.get(
    "/items/{item_id}",
    summary="Get an item",
    description="Retrieve item by ID",
    response_description="The requested item",
    tags=["items"],
    deprecated=False,
)
async def get_item(item_id: int):
    """
    Detailed docstring:
    - Shows in documentation
    - Supports markdown
    """
    return {"item_id": item_id}
```

---

### 4. Tags

```python
tags_metadata = [
    {
        "name": "items",
        "description": "Operations with items",
        "externalDocs": {
            "description": "Items docs",
            "url": "https://example.com/docs",
        },
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.get("/items/", tags=["items"])
async def list_items():
    return []
```

---

### 5. Response Examples

```python
@app.get(
    "/items/{item_id}",
    responses={
        200: {
            "description": "Success",
            "content": {
                "application/json": {
                    "example": {"id": 1, "name": "Item"}
                }
            }
        },
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found"}
                }
            }
        }
    }
)
async def get_item(item_id: int):
    return {"id": item_id}
```

---

### 6. Query Parameters

```python
from fastapi import Query
from typing import Optional

@app.get("/items/")
async def list_items(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records"),
    search: Optional[str] = Query(None, min_length=2, description="Search term"),
):
    return []
```

---

### 7. Request Body Examples

```python
from fastapi import Body

@app.post("/items/")
async def create_item(
    item: Item = Body(
        ...,
        examples={
            "normal": {
                "summary": "Normal item",
                "value": {"name": "Widget", "price": 9.99}
            },
            "premium": {
                "summary": "Premium item",
                "value": {"name": "Gold Widget", "price": 99.99}
            }
        }
    )
):
    return item
```

---

### 8. API Versioning (Path-based)

```python
from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v2_router = APIRouter(prefix="/v2", tags=["v2"])

@v1_router.get("/items/")
async def get_items_v1():
    return {"version": "1.0"}

@v2_router.get("/items/")
async def get_items_v2():
    return {"version": "2.0", "enhanced": True}

app.include_router(v1_router)
app.include_router(v2_router)
```

---

### 9. Deprecation

```python
@app.get(
    "/old-endpoint/",
    deprecated=True,
    summary="[DEPRECATED] Old Endpoint",
    description="⚠️ Use /v2/new-endpoint/ instead. Sunset: 2024-12-31"
)
async def old_endpoint():
    return {"warning": "deprecated"}
```

---

### 10. Custom OpenAPI Schema

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Custom API",
        version="1.0.0",
        description="Custom schema",
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    openapi_schema["servers"] = [
        {"url": "https://api.example.com", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Development"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

---

## 🎯 RESTful Best Practices Cheatsheet

### HTTP Methods & Status Codes

| Method | Use Case | Success Code | Error Codes |
|--------|----------|--------------|-------------|
| GET | Retrieve resource(s) | 200 | 404, 400 |
| POST | Create new resource | 201 | 400, 422 |
| PUT | Replace entire resource | 200, 204 | 404, 400 |
| PATCH | Partial update | 200 | 404, 400 |
| DELETE | Remove resource | 204, 200 | 404 |

### Naming Conventions

```python
# ✅ GOOD
GET    /users/              # List users
GET    /users/{id}          # Get specific user
POST   /users/              # Create user
PUT    /users/{id}          # Update user
DELETE /users/{id}          # Delete user
GET    /users/{id}/orders/  # Nested resource

# ❌ BAD
GET    /getUsers/
POST   /user/create/
GET    /user/{id}           # Inconsistent (should be plural)
```

### Query Parameters

```python
# Filtering
GET /products?category=electronics&price_min=100

# Sorting
GET /products?sort=price&order=desc

# Pagination
GET /products?page=1&page_size=20

# Search
GET /products?search=laptop

# Multiple filters
GET /products?category=electronics&brand=apple&in_stock=true
```

---

## 🔧 Common Patterns

### Paginated Response

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

@app.get("/items/", response_model=PaginatedResponse[Item])
async def list_items(page: int = 1, page_size: int = 20):
    total = 100  # From database
    items = []   # Fetch from database
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
```

### Error Response

```python
from fastapi import HTTPException, status

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {"id": item_id}
```

### HATEOAS Links

```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {
        "id": item_id,
        "name": "Widget",
        "_links": {
            "self": f"/items/{item_id}",
            "collection": "/items/",
            "update": f"/items/{item_id}",
            "delete": f"/items/{item_id}"
        }
    }
```

---

## 📊 Status Codes Reference

### Success Codes
- **200 OK**: Standard success response
- **201 Created**: Resource created successfully
- **204 No Content**: Success with no response body
- **206 Partial Content**: Partial data returned

### Client Error Codes
- **400 Bad Request**: Invalid request syntax
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource conflict (duplicate)
- **422 Unprocessable Entity**: Validation error

### Server Error Codes
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service down

---

## 🎨 Documentation Best Practices

### 1. Always Include
- [ ] Application title, description, version
- [ ] Contact information
- [ ] License information
- [ ] Tags for organization
- [ ] Examples for all models
- [ ] Descriptions for all fields

### 2. Model Documentation
- [ ] Class docstring
- [ ] Field descriptions
- [ ] Field examples
- [ ] Validators with constraints
- [ ] Complete schema_extra example

### 3. Endpoint Documentation
- [ ] Summary (short title)
- [ ] Description (detailed explanation)
- [ ] Response description
- [ ] Tags for organization
- [ ] Query parameter descriptions
- [ ] Response examples (200, 4xx, 5xx)
- [ ] Deprecation warnings if needed

### 4. Response Documentation
- [ ] Define response_model
- [ ] Document error responses
- [ ] Include example responses
- [ ] Specify status codes

---

## 🚀 Quick Start Template

```python
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional

# Tags
tags_metadata = [
    {"name": "items", "description": "Item operations"},
]

# App
app = FastAPI(
    title="My API",
    description="API Description",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Model
class Item(BaseModel):
    """Item model"""
    id: Optional[int] = Field(None, description="Item ID")
    name: str = Field(..., description="Item name", example="Widget")
    price: float = Field(..., gt=0, description="Price", example=9.99)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Widget",
                "price": 9.99
            }
        }

# Endpoints
@app.get("/items/", response_model=List[Item], tags=["items"])
async def list_items(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max items"),
):
    """List all items with pagination"""
    return []

@app.get("/items/{item_id}", response_model=Item, tags=["items"])
async def get_item(item_id: int):
    """Get a specific item by ID"""
    return {"id": item_id, "name": "Widget", "price": 9.99}

@app.post("/items/", response_model=Item, status_code=201, tags=["items"])
async def create_item(item: Item):
    """Create a new item"""
    return item

@app.put("/items/{item_id}", response_model=Item, tags=["items"])
async def update_item(item_id: int, item: Item):
    """Update an existing item"""
    return item

@app.delete("/items/{item_id}", status_code=204, tags=["items"])
async def delete_item(item_id: int):
    """Delete an item"""
    return None
```

---

## 🧪 Testing Commands

```bash
# Start the application
uvicorn your_app:app --reload

# View interactive documentation
# Open browser: http://localhost:8000/docs

# View alternative documentation
# Open browser: http://localhost:8000/redoc

# View OpenAPI schema (JSON)
# Open browser: http://localhost:8000/openapi.json

# Or use curl
curl http://localhost:8000/openapi.json | jq
```

---

## 📱 Tools & Resources

### Documentation Tools
- **Swagger UI**: Built into FastAPI at `/docs`
- **ReDoc**: Built into FastAPI at `/redoc`
- **Postman**: Import OpenAPI schema for testing
- **Insomnia**: Import OpenAPI schema

### Validation Tools
- [Swagger Editor](https://editor.swagger.io/): Validate OpenAPI schema
- [OpenAPI Validator](https://validator.swagger.io/): Online validator

### Learning Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Tutorial](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

## 💡 Pro Tips

1. **Use Examples Everywhere**: They make testing easier
2. **Be Consistent**: Follow naming conventions throughout
3. **Document Errors**: Show what can go wrong
4. **Version Early**: Start with v1 even if it's your first version
5. **Test Frequently**: Use Swagger UI to test as you build
6. **Think Like a User**: What would you need to know?
7. **Keep It Updated**: Documentation drift kills APIs
8. **Use Markdown**: Make descriptions readable
9. **Add Links**: External docs, guides, support
10. **Automate**: CI/CD should validate OpenAPI schema

---

**Last Updated**: 2024
**Maintained By**: FastAPI Learning Project
