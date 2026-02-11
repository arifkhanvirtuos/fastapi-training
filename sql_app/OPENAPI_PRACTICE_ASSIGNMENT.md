# OpenAPI Customization - Practice Assignment
## Enhance API Documentation with Examples and Descriptions

---

## 🎯 Assignment Objectives

By completing this assignment, you will:
1. Apply OpenAPI customization to a real FastAPI application
2. Add comprehensive descriptions and examples to all models
3. Organize endpoints with tags and metadata
4. Implement API versioning
5. Follow RESTful best practices

**Estimated Time**: 2-3 hours

---

## 📋 Assignment Tasks

### Task 1: Application-Level Customization (15 points)

Create a new FastAPI application with complete metadata:

```python
# assignment_app.py
from fastapi import FastAPI

# TODO: Create FastAPI app with:
# - Title: "Library Management System API"
# - Description: Multi-line description with markdown
# - Version: "1.0.0"
# - Contact information (name, email, url)
# - License information (MIT)
# - Terms of service URL
```

**Requirements**:
- [ ] Include a detailed description with at least 3 features listed
- [ ] Add contact information with your name and email
- [ ] Include license information
- [ ] Add terms of service URL (can be placeholder)

**Expected Output**: Visit `/docs` and verify all metadata appears correctly

---

### Task 2: Create Comprehensive Models (25 points)

Create three Pydantic models with complete documentation:

#### Model 1: Book
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Book(BaseModel):
    """
    TODO: Add class docstring
    """
    # TODO: Add these fields with Field() descriptions and examples:
    # - id: Optional[int]
    # - title: str (min 1, max 200 chars)
    # - author: str
    # - isbn: str (exactly 13 chars)
    # - published_date: date
    # - pages: int (greater than 0)
    # - available: bool (default True)
    # - genre: str
    # - description: Optional[str]
    
    class Config:
        schema_extra = {
            # TODO: Add complete example
        }
```

#### Model 2: Member
```python
class Member(BaseModel):
    """
    TODO: Add library member model with:
    - id, name, email, phone
    - membership_date, membership_type (Basic/Premium)
    - active status
    """
    pass  # Replace with implementation
```

#### Model 3: Loan
```python
class Loan(BaseModel):
    """
    TODO: Add book loan model with:
    - id, book_id, member_id
    - loan_date, due_date, return_date (optional)
    - status (Active/Returned/Overdue)
    """
    pass  # Replace with implementation
```

**Requirements**:
- [ ] All fields have descriptions
- [ ] All fields have realistic examples
- [ ] Each model has a complete schema_extra example
- [ ] Use appropriate validators (min_length, ge, regex, etc.)

---

### Task 3: Tag Organization (15 points)

Define tag metadata and organize endpoints:

```python
tags_metadata = [
    {
        "name": "books",
        "description": "TODO: Add description",
        # TODO: Add external docs link
    },
    # TODO: Add tags for: members, loans, admin
]

app = FastAPI(
    # ... previous metadata
    openapi_tags=tags_metadata
)
```

**Requirements**:
- [ ] Create 4 tags: books, members, loans, admin
- [ ] Each tag has a detailed description
- [ ] At least 2 tags have external documentation links
- [ ] Use markdown formatting in descriptions

---

### Task 4: Implement RESTful Endpoints (30 points)

Implement CRUD operations for Book resource following REST best practices:

```python
# TODO: Implement these endpoints:

@app.get("/v1/books/", tags=["books"])
async def list_books(
    # Add query parameters for:
    # - genre filtering
    # - availability filtering
    # - search by title/author
    # - sorting (by title, author, published_date)
    # - pagination (page, page_size)
):
    """
    TODO: Add comprehensive docstring
    """
    pass

@app.get("/v1/books/{book_id}", tags=["books"])
async def get_book(book_id: int):
    """
    TODO: Add docstring
    TODO: Return 404 if book not found
    """
    pass

@app.post("/v1/books/", tags=["books"], status_code=201)
async def create_book(book: Book):
    """
    TODO: Add docstring with field descriptions
    TODO: Add multiple request body examples
    """
    pass

@app.put("/v1/books/{book_id}", tags=["books"])
async def update_book(book_id: int, book: Book):
    """TODO: Add docstring"""
    pass

@app.patch("/v1/books/{book_id}", tags=["books"])
async def partial_update_book(
    book_id: int,
    # TODO: Make all fields optional for partial update
):
    """TODO: Add docstring explaining partial updates"""
    pass

@app.delete("/v1/books/{book_id}", tags=["books"], status_code=204)
async def delete_book(book_id: int):
    """TODO: Add docstring"""
    pass
```

**Requirements**:
- [ ] All endpoints have proper HTTP methods
- [ ] Correct status codes used
- [ ] Query parameters have descriptions and validators
- [ ] Comprehensive docstrings
- [ ] Response examples documented

---

### Task 5: Add Response Documentation (15 points)

Add response models and examples:

```python
@app.get(
    "/v1/books/{book_id}",
    response_model=Book,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        # TODO: Add complete example
                    }
                }
            }
        },
        404: {
            # TODO: Add 404 response example
        },
        422: {
            # TODO: Add validation error example
        }
    }
)
async def get_book(book_id: int):
    pass
```

**Requirements**:
- [ ] Define responses for 200, 404, 422 status codes
- [ ] Include realistic examples for each response
- [ ] Add descriptions for each response type

---

### Task 6: Implement API Versioning (20 points)

Create V2 endpoints with enhancements:

```python
from fastapi import APIRouter

# V1 Router
v1_router = APIRouter(prefix="/v1", tags=["v1"])

# TODO: Move all previous endpoints to v1_router

# V2 Router with enhancements
v2_router = APIRouter(prefix="/v2", tags=["v2"])

@v2_router.get("/books/", response_model=PaginatedResponse[Book])
async def list_books_v2():
    """
    V2: Returns paginated response with metadata
    
    Enhancements over V1:
    - TODO: List improvements
    """
    pass

# TODO: Add deprecated endpoint example
@app.get("/books/", deprecated=True)
async def old_list_books():
    """
    ⚠️ DEPRECATED: This endpoint will be removed in v3.0.0
    
    Please use /v2/books/ instead
    """
    pass
```

**Requirements**:
- [ ] Implement both v1 and v2 versions
- [ ] V2 includes enhanced features (pagination, better filtering)
- [ ] Add at least one deprecated endpoint
- [ ] Deprecation notice includes sunset date and migration path
- [ ] Document differences between versions

---

### Task 7: Custom OpenAPI Schema (Bonus: 15 points)

Customize the OpenAPI schema:

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Library Management System",
        version="1.0.0",
        description="Custom OpenAPI schema",
        routes=app.routes,
    )
    
    # TODO: Add custom fields
    # - Add logo URL
    # - Add multiple servers (dev, staging, prod)
    # - Add security schemes
    # - Add custom vendor extensions (x-*)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

**Requirements**:
- [ ] Add logo URL
- [ ] Define 3 servers (development, staging, production)
- [ ] Add at least one custom extension field (x-*)
- [ ] Document the customizations in comments

---

## 🧪 Testing Your Implementation

### Manual Testing Checklist

1. **Documentation UI**
   ```bash
   # Start your app
   uvicorn assignment_app:app --reload
   
   # Visit http://localhost:8000/docs
   ```
   - [ ] Application title and description appear
   - [ ] All tags are visible and organized
   - [ ] Endpoints are grouped correctly
   - [ ] Examples appear in request bodies

2. **Test Each Endpoint**
   - [ ] Try the example requests in Swagger UI
   - [ ] Verify response examples match
   - [ ] Check error responses (404, 422)
   - [ ] Test query parameter validation

3. **Version Testing**
   - [ ] Access /v1/books/ and /v2/books/
   - [ ] Verify deprecated endpoint shows warning
   - [ ] Check differences between versions

### Automated Testing (Optional)

```python
# test_assignment.py
from fastapi.testclient import TestClient
from assignment_app import app

client = TestClient(app)

def test_openapi_schema():
    """Verify OpenAPI schema is customized"""
    response = client.get("/openapi.json")
    schema = response.json()
    
    assert schema["info"]["title"] == "Library Management System API"
    assert "contact" in schema["info"]
    assert "license" in schema["info"]
    assert len(schema["tags"]) >= 4

def test_list_books():
    """Test book listing endpoint"""
    response = client.get("/v1/books/")
    assert response.status_code == 200

def test_create_book():
    """Test book creation"""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890123",
        "published_date": "2024-01-01",
        "pages": 300,
        "genre": "Fiction"
    }
    response = client.post("/v1/books/", json=book_data)
    assert response.status_code == 201

# TODO: Add more tests
```

---

## 📊 Grading Rubric

| Task | Points | Criteria |
|------|--------|----------|
| Task 1: App Metadata | 15 | Complete metadata with all fields |
| Task 2: Models | 25 | 3 models with descriptions, examples, validators |
| Task 3: Tags | 15 | 4+ tags with descriptions and external docs |
| Task 4: REST Endpoints | 30 | All CRUD operations with proper HTTP methods |
| Task 5: Response Docs | 15 | Multiple response types documented |
| Task 6: Versioning | 20 | V1/V2 implementation with deprecation |
| Task 7: Custom Schema | 15 | Bonus points for advanced customization |
| **Total** | **135** | **100 + 35 bonus** |

### Grading Scale
- **90-100+**: Excellent - Professional-grade documentation
- **80-89**: Good - Well-documented with minor gaps
- **70-79**: Satisfactory - Basic documentation complete
- **Below 70**: Needs improvement

---

## 💡 Tips for Success

1. **Start with Models**
   - Get the data models right first
   - Use realistic examples from a real library

2. **Be Consistent**
   - Follow naming conventions throughout
   - Use the same date formats, structures, etc.

3. **Think Like a User**
   - What would you want to know about this endpoint?
   - What examples would be helpful?

4. **Use the Swagger UI**
   - Test frequently as you build
   - The UI will show you what's missing

5. **Read the OpenAPI JSON**
   - Visit `/openapi.json` to see the raw schema
   - Helps debug customization issues

---

## 🎁 Bonus Challenges

### Challenge 1: Search Implementation
Implement full-text search across book title, author, and description:
```python
@app.get("/v2/books/search/")
async def search_books(
    q: str = Query(..., min_length=2, description="Search query"),
    # Add search-specific filters
):
    """Advanced search with ranking"""
    pass
```

### Challenge 2: Rate Limiting Documentation
Document rate limiting in OpenAPI:
```python
# Add to custom OpenAPI schema
openapi_schema["x-rate-limit"] = {
    "anonymous": "100/hour",
    "authenticated": "1000/hour",
    "premium": "10000/hour"
}
```

### Challenge 3: Webhook Documentation
Document webhooks for loan events:
```python
# Add webhook documentation to OpenAPI schema
```

---

## 📤 Submission

Submit the following files:
1. `assignment_app.py` - Your complete FastAPI application
2. `test_assignment.py` - Test file (if you wrote tests)
3. `REFLECTION.md` - Brief reflection on what you learned

### Reflection Questions
1. What was the most challenging part of the assignment?
2. How does good documentation improve API usability?
3. Which versioning strategy would you use in production?
4. What RESTful best practices will you apply in future projects?

---

## 🔗 Resources

- [FastAPI OpenAPI Docs](https://fastapi.tiangolo.com/tutorial/metadata/)
- [Pydantic Field Documentation](https://docs.pydantic.dev/latest/usage/fields/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Tutorial](https://restfulapi.net/)

---

## ✅ Completion Checklist

Before submitting, verify:
- [ ] All 6 main tasks completed
- [ ] Swagger UI loads without errors
- [ ] All endpoints have descriptions
- [ ] All models have examples
- [ ] Tags are organized logically
- [ ] Versioning is implemented
- [ ] No validation errors in OpenAPI schema
- [ ] `/openapi.json` is valid JSON
- [ ] Documentation is professional and complete

---

**Good luck! 🚀**

Remember: The goal is to create documentation so good that developers can use your API without asking questions!
