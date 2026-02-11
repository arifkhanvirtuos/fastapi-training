"""
OpenAPI Customization - Complete Working Example
=================================================

This is a comprehensive example demonstrating all OpenAPI customization features:
- Application metadata
- Model descriptions and examples
- Endpoint documentation
- Tags and organization
- API versioning
- RESTful best practices

Run: uvicorn openapi_example:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body, status, APIRouter
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Generic, TypeVar
from datetime import datetime, date
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ============================================================================
# PYDANTIC MODELS WITH COMPLETE DOCUMENTATION
# ============================================================================

class UserBase(BaseModel):
    """
    Base user model with common fields
    """
    username: str = Field(
        ...,
        description="Unique username for the user",
        min_length=3,
        max_length=50,
        example="johndoe"
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="john.doe@example.com"
    )
    full_name: Optional[str] = Field(
        None,
        description="User's full name",
        example="John Doe"
    )

class User(UserBase):
    """
    User model representing a system user
    """
    id: int = Field(..., description="Unique user identifier", example=1)
    is_active: bool = Field(
        True,
        description="Whether the user account is active",
        example=True
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="User creation timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00"
            }
        }

class UserCreate(UserBase):
    """
    Model for creating a new user
    """
    password: str = Field(
        ...,
        description="User password (will be hashed)",
        min_length=8,
        example="SecurePass123!"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "username": "janedoe",
                "email": "jane.doe@example.com",
                "full_name": "Jane Doe",
                "password": "SecurePass123!"
            }
        }

class Task(BaseModel):
    """
    Task model representing a todo item
    """
    id: Optional[int] = Field(None, description="Unique task identifier")
    title: str = Field(
        ...,
        description="Task title/summary",
        min_length=1,
        max_length=200,
        example="Complete API documentation"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed task description",
        example="Add comprehensive examples and descriptions to all API endpoints"
    )
    priority: TaskPriority = Field(
        TaskPriority.MEDIUM,
        description="Task priority level"
    )
    status: TaskStatus = Field(
        TaskStatus.TODO,
        description="Current task status"
    )
    due_date: Optional[date] = Field(
        None,
        description="Task due date",
        example="2024-12-31"
    )
    assigned_to: Optional[int] = Field(
        None,
        description="ID of assigned user",
        example=1
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Task creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp"
    )
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": 1,
                    "title": "Complete API documentation",
                    "description": "Add examples to all endpoints",
                    "priority": "high",
                    "status": "in_progress",
                    "due_date": "2024-12-31",
                    "assigned_to": 1,
                    "created_at": "2024-01-15T10:00:00",
                    "updated_at": "2024-01-15T15:30:00"
                },
                {
                    "id": 2,
                    "title": "Review pull requests",
                    "description": None,
                    "priority": "medium",
                    "status": "todo",
                    "due_date": "2024-01-20",
                    "assigned_to": 2,
                    "created_at": "2024-01-15T11:00:00",
                    "updated_at": None
                }
            ]
        }

class TaskCreate(BaseModel):
    """Model for creating a new task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None

class TaskUpdate(BaseModel):
    """Model for updating a task (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None
    assigned_to: Optional[int] = None

# ============================================================================
# GENERIC RESPONSE MODELS
# ============================================================================

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper
    """
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items", example=100)
    page: int = Field(..., description="Current page number", example=1)
    page_size: int = Field(..., description="Items per page", example=20)
    pages: int = Field(..., description="Total number of pages", example=5)
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")

# ============================================================================
# TAGS METADATA
# ============================================================================

tags_metadata = [
    {
        "name": "v2-tasks",
        "description": """
        **Task Management Operations (v2)**
        
        Create, read, update, and delete tasks. Version 2 includes:
        - Enhanced filtering and search
        - Pagination support
        - Priority and status management
        """,
        "externalDocs": {
            "description": "Task Management Guide",
            "url": "https://example.com/docs/tasks",
        },
    },
    {
        "name": "v2-users",
        "description": """
        **User Management Operations (v2)**
        
        Manage system users and their profiles.
        """,
    },
    {
        "name": "v1",
        "description": "**Legacy API v1** (deprecated - use v2 instead)",
    },
    {
        "name": "deprecated",
        "description": "⚠️ **Deprecated Endpoints** - Will be removed in v3.0",
    },
]

# ============================================================================
# FASTAPI APP WITH COMPLETE METADATA
# ============================================================================

app = FastAPI(
    title="Task Management API",
    description="""
    ## Professional Task Management System API
    
    This API provides comprehensive task and user management functionality.
    
    ### Features
    
    * **Task Management** - Create, update, delete, and track tasks
    * **User Management** - Manage user accounts and profiles
    * **Advanced Filtering** - Search and filter by multiple criteria
    * **Pagination** - Efficient handling of large datasets
    * **Priority System** - Organize tasks by priority levels
    * **Status Tracking** - Monitor task progress through multiple states
    
    ### Authentication
    
    Most endpoints require JWT authentication (not implemented in this example).
    In production, use the `/auth/login` endpoint to obtain a token.
    
    ### Rate Limiting
    
    - **Anonymous**: 100 requests/hour
    - **Authenticated**: 1000 requests/hour
    - **Premium**: 10000 requests/hour
    
    ### API Versioning
    
    We use path-based versioning:
    - `/v1/*` - Legacy API (deprecated)
    - `/v2/*` - Current stable API
    
    ### Support
    
    For support, email support@example.com or visit our documentation.
    """,
    version="2.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support Team",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
)

# ============================================================================
# CUSTOM OPENAPI SCHEMA
# ============================================================================

def custom_openapi():
    """
    Customize the OpenAPI schema with additional information
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Task Management API",
        version="2.0.0",
        description="Professional task management system",
        routes=app.routes,
    )
    
    # Add logo
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.example.com",
            "description": "Production server"
        },
        {
            "url": "https://staging.api.example.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
    ]
    
    # Add custom vendor extensions
    openapi_schema["x-api-id"] = "task-management-api"
    openapi_schema["x-audience"] = "public"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================================================================
# API V2 ROUTERS
# ============================================================================

v2_tasks = APIRouter(prefix="/v2/tasks", tags=["v2-tasks"])
v2_users = APIRouter(prefix="/v2/users", tags=["v2-users"])

# ============================================================================
# V2 TASKS ENDPOINTS
# ============================================================================

@v2_tasks.get(
    "/",
    response_model=PaginatedResponse[Task],
    summary="List all tasks",
    description="Retrieve a paginated list of tasks with advanced filtering options",
    response_description="Paginated list of tasks",
)
async def list_tasks_v2(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned user ID"),
    search: Optional[str] = Query(None, min_length=2, description="Search in title and description"),
    sort_by: str = Query("created_at", description="Sort field (created_at, due_date, priority, title)"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
):
    """
    Get a paginated list of tasks with comprehensive filtering.
    
    **Filtering Options:**
    - `status`: Filter by task status (todo, in_progress, completed, cancelled)
    - `priority`: Filter by priority level (low, medium, high, urgent)
    - `assigned_to`: Show only tasks assigned to specific user
    - `search`: Search in task title and description
    
    **Sorting:**
    - `sort_by`: Field to sort by
    - `order`: Sort direction (asc or desc)
    
    **Pagination:**
    - `page`: Current page number (1-based)
    - `page_size`: Items per page (max 100)
    
    **Example:** `/v2/tasks/?status=in_progress&priority=high&page=1&page_size=10`
    """
    # Mock data
    tasks = [
        Task(
            id=1,
            title="Complete API documentation",
            description="Add comprehensive examples",
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            assigned_to=1,
        ),
        Task(
            id=2,
            title="Review pull requests",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.TODO,
            assigned_to=1,
        ),
    ]
    
    total = 2
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )

@v2_tasks.get(
    "/{task_id}",
    response_model=Task,
    summary="Get a specific task",
    description="Retrieve detailed information about a specific task by ID",
    response_description="The requested task",
    responses={
        200: {
            "description": "Task found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Complete API documentation",
                        "description": "Add examples to all endpoints",
                        "priority": "high",
                        "status": "in_progress",
                        "due_date": "2024-12-31",
                        "assigned_to": 1,
                        "created_at": "2024-01-15T10:00:00",
                        "updated_at": "2024-01-15T15:30:00"
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task with ID 999 not found"}
                }
            }
        }
    }
)
async def get_task_v2(
    task_id: int = Path(..., description="Unique task identifier", ge=1, example=1)
):
    """
    Get detailed information about a specific task.
    
    Returns all task fields including:
    - Basic information (title, description)
    - Status and priority
    - Assignment information
    - Timestamps (created, updated)
    - Due date
    
    **Error Cases:**
    - Returns 404 if task doesn't exist
    - Returns 422 if task_id is invalid
    """
    if task_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return Task(
        id=task_id,
        title="Complete API documentation",
        description="Add comprehensive examples and descriptions",
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        assigned_to=1,
    )

@v2_tasks.post(
    "/",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with the provided information",
    response_description="The created task with generated ID",
)
async def create_task_v2(
    task: TaskCreate = Body(
        ...,
        examples={
            "basic": {
                "summary": "Basic task",
                "description": "A simple task with minimal information",
                "value": {
                    "title": "Review documentation",
                    "priority": "medium",
                }
            },
            "detailed": {
                "summary": "Detailed task",
                "description": "A comprehensive task with all fields",
                "value": {
                    "title": "Implement new feature",
                    "description": "Add user authentication to the API",
                    "priority": "high",
                    "due_date": "2024-12-31",
                    "assigned_to": 1
                }
            },
            "urgent": {
                "summary": "Urgent task",
                "description": "High priority urgent task",
                "value": {
                    "title": "Fix production bug",
                    "description": "Critical bug affecting users",
                    "priority": "urgent",
                    "due_date": "2024-01-16",
                    "assigned_to": 2
                }
            }
        }
    )
):
    """
    Create a new task.
    
    **Required Fields:**
    - `title`: Task title (1-200 characters)
    
    **Optional Fields:**
    - `description`: Detailed description
    - `priority`: Priority level (default: medium)
    - `due_date`: Target completion date
    - `assigned_to`: User ID to assign the task to
    
    The task will be created with status "todo" and assigned a unique ID.
    """
    # In production: save to database
    return Task(
        id=1,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.TODO,
        due_date=task.due_date,
        assigned_to=task.assigned_to,
    )

@v2_tasks.put(
    "/{task_id}",
    response_model=Task,
    summary="Update a task",
    description="Replace an existing task with new data",
)
async def update_task_v2(
    task_id: int = Path(..., ge=1),
    task: TaskCreate = Body(...),
):
    """
    Update an existing task (full replacement).
    
    All fields except ID will be replaced with the provided values.
    Use PATCH for partial updates.
    """
    if task_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return Task(
        id=task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.TODO,
        due_date=task.due_date,
        assigned_to=task.assigned_to,
    )

@v2_tasks.patch(
    "/{task_id}",
    response_model=Task,
    summary="Partially update a task",
    description="Update specific fields of a task",
)
async def partial_update_task_v2(
    task_id: int = Path(..., ge=1),
    task: TaskUpdate = Body(...),
):
    """
    Update specific fields of a task without replacing the entire resource.
    
    Only provided fields will be updated. Other fields remain unchanged.
    
    **Example:** To mark a task as completed:
    ```json
    {
        "status": "completed"
    }
    ```
    """
    if task_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # In production: fetch existing task and update only provided fields
    return Task(
        id=task_id,
        title=task.title or "Existing title",
        priority=task.priority or TaskPriority.MEDIUM,
        status=task.status or TaskStatus.TODO,
    )

@v2_tasks.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Permanently delete a task",
    responses={
        204: {"description": "Task successfully deleted"},
        404: {"description": "Task not found"},
    }
)
async def delete_task_v2(
    task_id: int = Path(..., ge=1)
):
    """
    Permanently delete a task.
    
    **Warning:** This action cannot be undone.
    
    Returns 204 No Content on success.
    """
    if task_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return None

# ============================================================================
# V2 USERS ENDPOINTS
# ============================================================================

@v2_users.get(
    "/",
    response_model=List[User],
    summary="List all users",
    tags=["v2-users"],
)
async def list_users_v2(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of users to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List all users with optional filtering"""
    return [
        User(
            id=1,
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            is_active=True,
        )
    ]

@v2_users.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    tags=["v2-users"],
)
async def create_user_v2(user: UserCreate):
    """
    Create a new user account.
    
    **Note:** The password will be hashed before storage and never returned in responses.
    """
    return User(
        id=1,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=True,
    )

# ============================================================================
# V1 DEPRECATED ENDPOINTS
# ============================================================================

v1_router = APIRouter(prefix="/v1", tags=["v1"])

@v1_router.get(
    "/tasks/",
    deprecated=True,
    summary="[DEPRECATED] List tasks (v1)",
    description="""
    ⚠️ **This endpoint is deprecated and will be removed on 2025-01-01**
    
    Please migrate to `/v2/tasks/` which provides:
    - Better pagination
    - Advanced filtering
    - Improved response format
    
    **Migration Guide:** https://example.com/docs/migration/v1-to-v2
    """,
)
async def list_tasks_v1():
    """
    Legacy endpoint for listing tasks.
    
    Returns simple list without pagination or filtering.
    """
    return {
        "warning": "This endpoint is deprecated. Use /v2/tasks/ instead.",
        "sunset_date": "2025-01-01",
        "migration_url": "https://example.com/docs/migration",
        "tasks": []
    }

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(v2_tasks)
app.include_router(v2_users)
app.include_router(v1_router)

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get(
    "/",
    tags=["root"],
    summary="API Root",
    description="Get API information and available endpoints",
)
async def root():
    """
    API root endpoint providing version information and links.
    """
    return {
        "name": "Task Management API",
        "version": "2.0.0",
        "description": "Professional task management system",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "endpoints": {
            "v2_tasks": "/v2/tasks/",
            "v2_users": "/v2/users/",
        },
        "_links": {
            "self": "/",
            "docs": "/docs",
            "tasks": "/v2/tasks/",
            "users": "/v2/users/",
        }
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get(
    "/health",
    tags=["monitoring"],
    include_in_schema=False,  # Hidden from documentation
    summary="Health Check",
)
async def health_check():
    """
    Health check endpoint for monitoring systems.
    Not included in the public API documentation.
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============================================================================
# RUN INSTRUCTIONS
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Task Management API...")
    print("📚 Documentation: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("🔧 OpenAPI Schema: http://localhost:8000/openapi.json")
    uvicorn.run(app, host="0.0.0.0", port=8000)
