# Role-Based Access Control (RBAC) in FastAPI

## Duration: 1 hour

## Table of Contents

1. [Introduction to RBAC](#introduction-to-rbac)
2. [Understanding Authorization vs Authentication](#authorization-vs-authentication)
3. [Role-Based Access Control Concepts](#role-based-access-control-concepts)
4. [User Permissions Model](#user-permissions-model)
5. [Implementing RBAC in FastAPI](#implementing-rbac-in-fastapi)
6. [Role Dependency Decorators](#role-dependency-decorators)
7. [Protecting Routes by Role](#protecting-routes-by-role)
8. [Permission Checks](#permission-checks)
9. [Best Practices](#best-practices)
10. [Practice Assignment](#practice-assignment)

---

## Introduction to RBAC

**Role-Based Access Control (RBAC)** is a security model that restricts system access based on user roles. Instead of granting permissions to individual users, permissions are assigned to roles, and users are assigned to roles.

### Why RBAC?

- **Simplified management**: Easier to manage permissions for groups of users
- **Security**: Principle of least privilege - users only get access they need
- **Scalability**: Easy to add new users with predefined roles
- **Compliance**: Helps meet regulatory requirements
- **Maintainability**: Changes to role permissions automatically apply to all users in that role

---

## Authorization vs Authentication

### Authentication

- **What it is**: Verifying WHO the user is
- **Question answered**: "Are you who you claim to be?"
- **Mechanisms**: Username/password, JWT tokens, OAuth2, biometrics
- **Example**: User logs in with email and password

### Authorization

- **What it is**: Verifying WHAT the user can do
- **Question answered**: "Do you have permission to access this resource?"
- **Mechanisms**: Roles, permissions, access control lists
- **Example**: Admin can delete users, regular users cannot

```
Authentication ➜ Authorization ➜ Access Granted/Denied
    (Who?)           (What?)          (Result)
```

---

## Role-Based Access Control Concepts

### 1. Roles

A **role** represents a job function or responsibility within an organization.

Common roles:

- **Admin**: Full system access
- **Manager**: Elevated access, can manage users
- **User**: Standard access
- **Guest**: Limited read-only access
- **Moderator**: Can moderate content

### 2. Permissions

**Permissions** are specific actions that can be performed on resources.

Examples:

- `read:users` - Can view user list
- `create:users` - Can create new users
- `update:users` - Can modify users
- `delete:users` - Can delete users
- `read:reports` - Can view reports
- `export:data` - Can export data

### 3. Role-Permission Mapping

```
┌─────────────┐
│    Admin    │ ➜ All permissions
└─────────────┘

┌─────────────┐
│   Manager   │ ➜ read:*, create:users, update:users, read:reports
└─────────────┘

┌─────────────┐
│    User     │ ➜ read:own_profile, update:own_profile
└─────────────┘

┌─────────────┐
│    Guest    │ ➜ read:public_content
└─────────────┘
```

---

## User Permissions Model

### Database Schema

```sql
-- Users table with role column
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(100),
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Optional: Separate roles table for complex scenarios
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    description TEXT
);

-- Optional: Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description TEXT
);

-- Optional: Role-Permission mapping (many-to-many)
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);
```

### Simple vs Complex Models

#### Simple Model (Used in this guide)

- Role stored as ENUM or String in User table
- Permissions hard-coded in application logic
- Best for: Small to medium applications with fixed roles

#### Complex Model

- Separate tables for roles and permissions
- Many-to-many relationships
- Dynamic permission assignment
- Best for: Large enterprise applications with complex requirements

---

## Implementing RBAC in FastAPI

### Step 1: Define Role Enum

```python
# auth.py or models.py
from enum import Enum

class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"
```

### Step 2: Update User Model

```python
# models.py
from sqlalchemy import Column, String, Enum as SQLEnum

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.USER
    )
    is_active = Column(Boolean, default=True)
```

### Step 3: Update Schemas

```python
# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER  # Default to user role

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
```

---

## Role Dependency Decorators

### Basic Role Checker

```python
# auth.py
from fastapi import Depends, HTTPException, status
from typing import List

def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory that creates a role checker dependency.

    Args:
        allowed_roles: List of roles allowed to access the endpoint

    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user

    return role_checker


# Convenience functions for common role checks
def require_admin(current_user: User = Depends(get_current_active_user)):
    """Dependency that requires admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_manager_or_admin(current_user: User = Depends(get_current_active_user)):
    """Dependency that requires manager or admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    return current_user
```

---

## Protecting Routes by Role

### Example: Admin-Only Route

```python
@app.get("/admin/users", response_model=List[UserResponse])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Admin-only endpoint to list all users.
    Regular users will receive 403 Forbidden.
    """
    users = db.query(User).all()
    return users
```

### Example: Manager or Admin Route

```python
@app.post("/admin/users/{user_id}/activate")
def activate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin)
):
    """
    Managers and Admins can activate user accounts.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()
    return {"message": f"User {user.email} activated successfully"}
```

### Example: Multiple Allowed Roles

```python
@app.get("/reports/sales", response_model=List[SalesReport])
def get_sales_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.USER])
    )
):
    """
    All authenticated users can view sales reports.
    """
    reports = db.query(SalesReport).all()
    return reports
```

### Example: User Can Only Access Own Data

```python
@app.get("/users/{user_id}/profile", response_model=UserResponse)
def get_user_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Users can only view their own profile.
    Admins can view any profile.
    """
    # Admin can view any profile
    if current_user.role == UserRole.ADMIN:
        user = db.query(User).filter(User.id == user_id).first()
    # Regular users can only view their own profile
    elif current_user.id == user_id:
        user = current_user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile"
        )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

---

## Permission Checks

### Fine-Grained Permission System

```python
# auth.py
from enum import Enum

class Permission(str, Enum):
    """System permissions"""
    # User permissions
    READ_USERS = "read:users"
    CREATE_USERS = "create:users"
    UPDATE_USERS = "update:users"
    DELETE_USERS = "delete:users"

    # Product permissions
    READ_PRODUCTS = "read:products"
    CREATE_PRODUCTS = "create:products"
    UPDATE_PRODUCTS = "update:products"
    DELETE_PRODUCTS = "delete:products"

    # Report permissions
    READ_REPORTS = "read:reports"
    EXPORT_DATA = "export:data"


# Role to permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Admins have all permissions
        *[p for p in Permission]
    ],
    UserRole.MANAGER: [
        Permission.READ_USERS,
        Permission.UPDATE_USERS,
        Permission.READ_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.UPDATE_PRODUCTS,
        Permission.READ_REPORTS,
        Permission.EXPORT_DATA,
    ],
    UserRole.USER: [
        Permission.READ_PRODUCTS,
        Permission.READ_REPORTS,
    ],
    UserRole.GUEST: [
        Permission.READ_PRODUCTS,
    ],
}


def has_permission(user: User, required_permission: Permission) -> bool:
    """
    Check if user's role has the required permission.

    Args:
        user: User object
        required_permission: Permission to check

    Returns:
        bool: True if user has permission
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return required_permission in user_permissions


def require_permission(permission: Permission):
    """
    Dependency factory for permission-based access control.

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}"
            )
        return current_user

    return permission_checker
```

### Using Permission-Based Protection

```python
@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DELETE_USERS))
):
    """
    Only users with DELETE_USERS permission can delete users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
```

---

## Best Practices

### 1. Principle of Least Privilege

```python
# ❌ Bad: Giving all users admin access by default
class UserCreate(BaseModel):
    role: UserRole = UserRole.ADMIN  # Too permissive!

# ✅ Good: Default to least privileged role
class UserCreate(BaseModel):
    role: UserRole = UserRole.USER
```

### 2. Separate Admin User Creation

```python
@app.post("/admin/create-admin", status_code=status.HTTP_201_CREATED)
def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Only existing admins can create new admin accounts.
    """
    # Force admin role
    user_data.role = UserRole.ADMIN

    # Create admin user...
    return new_user
```

### 3. Audit Logging

```python
from datetime import datetime

def log_admin_action(user: User, action: str, details: dict):
    """Log administrative actions for audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow(),
        "user_id": user.id,
        "user_email": user.email,
        "action": action,
        "details": details
    }
    # Save to database or logging system
    logger.info(f"Admin action: {log_entry}")

@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log the deletion
    log_admin_action(
        current_user,
        "DELETE_USER",
        {"deleted_user_id": str(user_id), "deleted_email": user.email}
    )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
```

### 4. Role Hierarchy

```python
ROLE_HIERARCHY = {
    UserRole.ADMIN: 4,
    UserRole.MANAGER: 3,
    UserRole.USER: 2,
    UserRole.GUEST: 1,
}

def has_higher_or_equal_role(user: User, required_role: UserRole) -> bool:
    """Check if user's role is higher or equal in hierarchy"""
    return ROLE_HIERARCHY.get(user.role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
```

### 5. Environment-Based Admin Creation

```python
# Create first admin via environment variable or CLI script
# Never expose admin creation endpoint publicly
import os

def create_initial_admin(db: Session):
    """Create initial admin from environment variables"""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        return

    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        return

    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
```

---

## Practice Assignment

### Assignment: Implement Multi-Role Task Management System

**Objective**: Build a task management system with role-based access control where different roles have different permissions.

#### Requirements

##### 1. Database Schema

Create the following models:

```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    priority = Column(String(20), default="medium")  # low, medium, high
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
```

##### 2. Role Definitions

Implement the following roles with specific permissions:

- **Admin**
  - Create, read, update, delete ANY task
  - Assign tasks to any user
  - View all tasks in the system
  - Change task status
  - Delete any task

- **Manager**
  - Create tasks
  - View all tasks
  - Assign tasks to team members
  - Update tasks they created or are assigned to
  - Change status of any task
  - Cannot delete tasks

- **User**
  - Create tasks (assigned to themselves)
  - View tasks assigned to them
  - View tasks they created
  - Update only their own tasks
  - Change status of tasks assigned to them
  - Cannot delete tasks

- **Guest**
  - View public/completed tasks only (read-only)
  - Cannot create, update, or delete tasks

##### 3. Required Endpoints

Implement the following endpoints with proper role protection:

```python
# Task CRUD operations
POST   /tasks                    # Create task (User+)
GET    /tasks                    # List tasks (role-based filtering)
GET    /tasks/{task_id}         # Get task details
PUT    /tasks/{task_id}         # Update task
DELETE /tasks/{task_id}         # Delete task (Admin only)

# Task assignment
PUT    /tasks/{task_id}/assign  # Assign task (Manager+)
PUT    /tasks/{task_id}/status  # Update status

# Statistics
GET    /admin/tasks/stats       # Task statistics (Manager+)
GET    /my-tasks                # Current user's tasks
```

##### 4. Business Rules to Implement

1. **Task Creation**
   - Users can only create tasks assigned to themselves
   - Managers can create tasks assigned to anyone
   - Admins can create tasks assigned to anyone

2. **Task Viewing**
   - Guests see only completed tasks
   - Users see tasks they created or are assigned to
   - Managers and Admins see all tasks

3. **Task Updates**
   - Users can only update their own tasks
   - Managers can update any task
   - Admins can update any task

4. **Task Deletion**
   - Only Admins can delete tasks
   - Must log deletion in audit trail

5. **Status Changes**
   - Users can change status of tasks assigned to them
   - Managers and Admins can change any task status

##### 5. Testing Scenarios

Create test cases for:

1. **Authorization Tests**
   - Guest trying to create task (should fail)
   - User trying to delete task (should fail)
   - Manager trying to view all tasks (should succeed)

2. **Data Isolation Tests**
   - User A cannot see User B's tasks
   - Manager can see all users' tasks

3. **Permission Tests**
   - User trying to assign task to another user (should fail)
   - Manager assigning task to user (should succeed)

##### 6. Deliverables

1. **Code Implementation**
   - Updated models with Task model
   - Role-based dependencies
   - All required endpoints
   - Proper error handling

2. **Documentation**
   - API documentation with role requirements
   - Curl/Postman examples for each endpoint
   - Role permission matrix

3. **Testing**
   - Create 4 test users (one for each role)
   - Test each endpoint with different roles
   - Document test results

##### 7. Bonus Challenges

1. **Task Comments**: Add comments to tasks with role-based access
2. **Task History**: Track all changes to tasks (audit trail)
3. **Bulk Operations**: Allow managers to assign multiple tasks at once
4. **Task Filters**: Filter tasks by status, priority, assignee
5. **Email Notifications**: Send email when task is assigned (use background tasks)
6. **Task Due Dates**: Add due dates and overdue task alerts

### Expected Output

When completed, you should be able to:

```bash
# Admin can do everything
curl -X GET "http://localhost:8000/tasks" \
  -H "Authorization: Bearer <admin_token>"
# Returns all tasks

# User sees only their tasks
curl -X GET "http://localhost:8000/tasks" \
  -H "Authorization: Bearer <user_token>"
# Returns only tasks assigned to or created by user

# Guest trying to create task fails
curl -X POST "http://localhost:8000/tasks" \
  -H "Authorization: Bearer <guest_token>" \
  -d '{"title": "New task"}'
# Returns 403 Forbidden

# Manager assigns task
curl -X PUT "http://localhost:8000/tasks/{task_id}/assign" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{"assigned_to_id": "<user_id>"}'
# Success
```

---

## Key Takeaways

### 1. Authorization is Different from Authentication

- Authentication proves identity
- Authorization controls access
- Both are essential for security

### 2. RBAC Simplifies Access Control

- Roles group related permissions
- Easier to manage than individual permissions
- Scales well as application grows

### 3. Use Dependencies for Protection

- FastAPI's dependency system is perfect for RBAC
- Dependencies can be composed and reused
- Clear, declarative access control

### 4. Implement Multiple Layers

- Role-based access (coarse-grained)
- Permission-based access (fine-grained)
- Resource ownership checks

### 5. Security Best Practices

- Principle of least privilege
- Default deny approach
- Audit logging for sensitive operations
- Separate admin management
- Never trust client input for roles

### 6. Testing is Critical

- Test each role's permissions
- Test permission boundaries
- Test unauthorized access attempts
- Document expected behavior

---

## Additional Resources

### Documentation

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 Scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/14/orm/relationship_api.html)

### Security Standards

- [OWASP Access Control](https://owasp.org/www-project-top-ten/)
- [NIST RBAC Model](https://csrc.nist.gov/projects/role-based-access-control)

### Example Projects

- [FastAPI Full Stack Template](https://github.com/tiangolo/full-stack-fastapi-postgresql)
- [FastAPI Users](https://github.com/fastapi-users/fastapi-users)

---

## Conclusion

Role-Based Access Control is a fundamental security concept that every web application needs. By implementing RBAC in FastAPI using dependencies, you create a clean, maintainable, and secure system. Remember to:

- Start simple and add complexity as needed
- Test thoroughly
- Follow security best practices
- Document your role and permission structure
- Regularly audit access controls

Good luck with the assignment! 🚀
