# Advanced SQLAlchemy CRUD Operations - Teaching Guide

## Duration: 1 Hour

---

## Table of Contents

1. [Joins and Eager Loading](#1-joins-and-eager-loading)
2. [Filtering and Sorting](#2-filtering-and-sorting)
3. [Aggregations](#3-aggregations)
4. [Transaction Management](#4-transaction-management)
5. [Session Lifecycle](#5-session-lifecycle)
6. [Practice Assignment](#practice-assignment)

---

## 1. Joins and Eager Loading

### What are Joins?

**Joins** are SQL operations that combine rows from two or more tables based on a related column between them. In SQLAlchemy, joins allow you to retrieve related data from multiple tables in a single query.

### Types of Joins

#### Inner Join

Returns only the rows where there is a match in both tables.

```python
# Example: Get users with their profiles
users_with_profiles = db.query(User).join(UserProfile).all()

# Example: Get products with their raw materials
products_with_materials = db.query(Product).join(Product.raw_materials).all()
```

#### Left Outer Join

Returns all rows from the left table and matched rows from the right table. If no match, NULL values are returned.

```python
# Example: Get all users, including those without profiles
users = db.query(User).outerjoin(UserProfile).all()
```

### The N+1 Problem

**What is it?** When you fetch a list of objects, then for each object, you make an additional query to fetch related data. This results in 1 query + N queries (one per object).

**Example of N+1 Problem:**

```python
# This causes N+1 queries!
products = db.query(Product).all()  # 1 query
for product in products:
    print(product.raw_materials)  # N additional queries (one per product)
```

### Eager Loading Solutions

#### 1. **Joinedload** (SQL JOIN)

Loads related objects in the same query using a SQL JOIN. Best for one-to-one or small one-to-many relationships.

```python
from sqlalchemy.orm import joinedload

# Single query with JOIN - for one-to-one relationship
users = db.query(User).options(joinedload(User.profile)).all()
```

**When to use:**

- One-to-one relationships
- Small one-to-many relationships
- When you need the related data immediately

#### 2. **Selectinload** (Separate SELECT)

Loads related objects with a separate SELECT query. Best for one-to-many or many-to-many relationships.

```python
from sqlalchemy.orm import selectinload

# Two queries: one for products, one for all related raw materials
products = db.query(Product).options(selectinload(Product.raw_materials)).all()
```

**When to use:**

- Large one-to-many relationships
- Many-to-many relationships
- Avoids duplicate data in result set

#### 3. **Subqueryload** (Subquery)

Similar to selectinload but uses a subquery instead of an IN clause.

```python
from sqlalchemy.orm import subqueryload

products = db.query(Product).options(subqueryload(Product.raw_materials)).all()
```

#### 4. **Lazy Loading** (Default)

Loads related objects only when accessed (causes N+1 problem).

```python
# Default behavior - loads on access
products = db.query(Product).all()
for product in products:
    print(product.raw_materials)  # Separate query for each product
```

### Practical Example with Multiple Relationships

````python
from sqlalchemy.orm import joinedload, selectinload

# Load users with their profile (1-to-1)
users = db.query(User).options(
    joinedload(User.profile)      # Use joinedload for 1-to-1
).all()

# Load products with raw materials (many-to-many)
products = db.query(Product).options(
    selectinload(Product.raw_materials)  # Use selectinload for many-to-many
).all()

# Load raw materials with their products
raw_materials = db.query(RawMaterial).options(
    selectinload(RawMaterial.products)

---

## 2. Filtering and Sorting

### Basic Filtering

#### Using filter()
The `filter()` method allows you to add WHERE conditions to your query.

```python
# Single condition
active_users = db.query(User).filter(User.is_active == True).all()

# Multiple conditions (AND)
users = db.query(User).filter(
    User.is_active == True,
    User.email.endswith('@gmail.com')
).all()
````

#### Using filter_by()

Simpler syntax using keyword arguments (equality only).

```python
# Equivalent to filter(User.email == 'test@example.com')
user = db.query(User).filter_by(email='test@example.com').first()
```

### Advanced Filtering Operators

#### Comparison Operators

```python
# Equal
users = db.query(User).filter(User.age == 25).all()

# Not equal
users = db.query(User).filter(User.age != 25).all()

# Greater than, less than
users = db.query(User).filter(User.age > 18).all()
users = db.query(User).filter(User.age < 65).all()

# Greater/less than or equal
users = db.query(User).filter(User.age >= 18).all()
users = db.query(User).filter(User.age <= 65).all()
```

#### String Operations

```python
# LIKE (case-sensitive pattern matching)
users = db.query(User).filter(User.name.like('%John%')).all()

# ILIKE (case-insensitive pattern matching)
users = db.query(User).filter(User.name.ilike('%john%')).all()

# Starts with
users = db.query(User).filter(User.name.startswith('J')).all()

# Ends with
users = db.query(User).filter(User.email.endswith('@gmail.com')).all()

# Contains
users = db.query(User).filter(User.name.contains('oh')).all()
```

#### IN and NOT IN

```python
# IN - check if value is in a list
users = db.query(User).filter(User.id.in_([1, 2, 3, 4])).all()

# NOT IN
users = db.query(User).filter(~User.id.in_([1, 2, 3])).all()
```

#### NULL Checks

```python
# IS NULL
users = db.query(User).filter(User.phone_number == None).all()
# or
users = db.query(User).filter(User.phone_number.is_(None)).all()

# IS NOT NULL
users = db.query(User).filter(User.phone_number != None).all()
# or
users = db.query(User).filter(User.phone_number.isnot(None)).all()
```

#### AND, OR, NOT

```python
from sqlalchemy import and_, or_, not_

# AND - all conditions must be true
users = db.query(User).filter(
    and_(
        User.is_active == True,
        User.age >= 18
    )
).all()

# OR - at least one condition must be true
users = db.query(User).filter(
    or_(
        User.email.endswith('@gmail.com'),
        User.email.endswith('@yahoo.com')
    )
).all()

# NOT - negates a condition
users = db.query(User).filter(
    not_(User.is_active == False)
).all()

# Complex combinations
users = db.query(User).filter(
    and_(
        User.is_active == True,
        or_(
            User.age >= 18,
            User.has_parental_consent == True
        )
    )
).all()
```

### Sorting

#### order_by() - Ascending

```python
# Sort by single column (ascending)
users = db.query(User).order_by(User.name).all()

# Sort by multiple columns
users = db.query(User).order_by(User.last_name, User.first_name).all()
```

#### order_by() - Descending

```python
from sqlalchemy import desc

# Descending order
users = db.query(User).order_by(desc(User.created_at)).all()

# Mixed ascending and descending
users = db.query(User).order_by(
    User.last_name,           # ascending
    desc(User.created_at)     # descending
).all()
```

#### Sorting with NULL values

```python
from sqlalchemy import nullsfirst, nullslast

# NULLs first
users = db.query(User).order_by(nullsfirst(User.phone_number)).all()

# NULLs last
users = db.query(User).order_by(nullslast(User.phone_number)).all()
```

### Pagination

#### limit() and offset()

```python
# Get first 10 users
users = db.query(User).limit(10).all()

# Skip first 20, get next 10 (page 3 of size 10)
users = db.query(User).offset(20).limit(10).all()

# Pagination function
def get_paginated_users(page: int, page_size: int):
    offset = (page - 1) * page_size
    return db.query(User).offset(offset).limit(page_size).all()
```

---

## 3. Aggregations (count, sum, avg)

### What are Aggregations?

**Aggregations** are operations that perform calculations on a set of values and return a single value. Common aggregations include counting rows, summing values, calculating averages, finding minimums and maximums.

### Count

#### count() - Count all rows

```python
# Count all users
user_count = db.query(User).count()

# Count with filter
active_user_count = db.query(User).filter(User.is_active == True).count()
```

#### func.count() - More flexible counting

```python
from sqlalchemy import func

# Count all
count = db.query(func.count(User.id)).scalar()

# Count distinct values
distinct_emails = db.query(func.count(User.email.distinct())).scalar()

# Count with GROUP BY
user_counts_by_status = db.query(
    User.is_active,
    func.count(User.id).label('count')
).group_by(User.is_active).all()
```

### Sum

```python
from sqlalchemy import func

# Sum of all order totals
total_revenue = db.query(func.sum(Order.total)).scalar()

# Sum with filter
revenue_2024 = db.query(func.sum(Order.total)).filter(
    func.extract('year', Order.created_at) == 2024
).scalar()

# Sum grouped by user
user_spending = db.query(
    User.id,
    User.email,
    func.sum(Order.total).label('total_spent')
).join(Order).group_by(User.id, User.email).all()
```

### Average (AVG)

```python
from sqlalchemy import func

# Average order value
avg_order_value = db.query(func.avg(Order.total)).scalar()

# Average with filter
avg_large_orders = db.query(func.avg(Order.total)).filter(
    Order.total > 100
).scalar()

# Average by category
avg_by_category = db.query(
    Product.category,
    func.avg(Product.price).label('average_price')
).group_by(Product.category).all()
```

### Min and Max

```python
from sqlalchemy import func

# Minimum and maximum prices
min_price = db.query(func.min(Product.price)).scalar()
max_price = db.query(func.max(Product.price)).scalar()

# Both in one query
price_range = db.query(
    func.min(Product.price).label('min_price'),
    func.max(Product.price).label('max_price')
).first()
```

### GROUP BY and HAVING

#### GROUP BY

Groups rows with the same values in specified columns.

```python
from sqlalchemy import func

# Count orders per user
orders_per_user = db.query(
    User.id,
    User.email,
    func.count(Order.id).label('order_count')
).join(Order).group_by(User.id, User.email).all()

# Revenue by month
monthly_revenue = db.query(
    func.extract('year', Order.created_at).label('year'),
    func.extract('month', Order.created_at).label('month'),
    func.sum(Order.total).label('revenue')
).group_by('year', 'month').all()
```

#### HAVING

Filters groups created by GROUP BY (like WHERE but for aggregated data).

```python
from sqlalchemy import func

# Users with more than 5 orders
power_users = db.query(
    User.id,
    User.email,
    func.count(Order.id).label('order_count')
).join(Order).group_by(User.id, User.email).having(
    func.count(Order.id) > 5
).all()

# Categories with average price > $50
expensive_categories = db.query(
    Product.category,
    func.avg(Product.price).label('avg_price')
).group_by(Product.category).having(
    func.avg(Product.price) > 50
).all()
```

### Complex Aggregation Example

```python
from sqlalchemy import func, case

# Comprehensive user statistics
user_stats = db.query(
    User.id,
    User.email,
    func.count(Order.id).label('total_orders'),
    func.sum(Order.total).label('total_spent'),
    func.avg(Order.total).label('avg_order_value'),
    func.max(Order.created_at).label('last_order_date'),
    func.sum(
        case(
            (Order.status == 'completed', 1),
            else_=0
        )
    ).label('completed_orders')
).outerjoin(Order).group_by(User.id, User.email).all()
```

---

## 4. Transaction Management

### What is a Transaction?

A **transaction** is a sequence of database operations that are treated as a single unit of work. Transactions ensure data integrity by following ACID properties.

### ACID Properties

#### **A - Atomicity**

All operations in a transaction succeed or all fail. No partial updates.

```python
# Either both operations succeed or both fail
try:
    user = User(email="test@example.com")
    db.add(user)
    order = Order(user_id=user.id, total=100)
    db.add(order)
    db.commit()  # Both saved
except:
    db.rollback()  # Neither saved
```

#### **C - Consistency**

Database remains in a valid state before and after transaction.

```python
# Ensures constraints are maintained
user = User(email=None)  # If email is required, this will fail
db.add(user)
db.commit()  # Raises error, database stays consistent
```

#### **I - Isolation**

Concurrent transactions don't interfere with each other.

```python
# Two users updating the same account simultaneously
# are isolated from each other
```

#### **D - Durability**

Committed transactions are permanent, even after system failures.

```python
db.commit()  # Once committed, data is saved permanently
```

### Basic Transaction Operations

#### commit()

Saves all pending changes to the database.

```python
user = User(email="test@example.com")
db.add(user)
db.commit()  # Changes are now permanent
```

#### rollback()

Discards all pending changes since the last commit.

```python
user = User(email="test@example.com")
db.add(user)
db.rollback()  # User is not saved, changes discarded
```

#### flush()

Sends pending changes to the database but doesn't commit them. Useful when you need generated IDs.

```python
user = User(email="test@example.com")
db.add(user)
db.flush()  # SQL executed, but not committed
print(user.id)  # ID is now available
db.commit()  # Now it's permanent
```

### Transaction Patterns

#### Manual Transaction Management

```python
from sqlalchemy.orm import Session

def transfer_money(from_account_id, to_account_id, amount, db: Session):
    try:
        # Start transaction (implicit)
        from_account = db.query(Account).filter(Account.id == from_account_id).first()
        to_account = db.query(Account).filter(Account.id == to_account_id).first()

        if from_account.balance < amount:
            raise ValueError("Insufficient funds")

        from_account.balance -= amount
        to_account.balance += amount

        db.commit()  # Both operations succeed
        return {"status": "success"}
    except Exception as e:
        db.rollback()  # Both operations fail
        return {"status": "error", "message": str(e)}
```

#### Context Manager (Recommended)

```python
from contextlib import contextmanager

@contextmanager
def transaction_scope(db: Session):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# Usage
with transaction_scope(db) as session:
    user = User(email="test@example.com")
    session.add(user)
    # Auto-commits on success, auto-rolls back on error
```

#### Nested Transactions (Savepoints)

```python
from sqlalchemy.orm import Session

def complex_operation(db: Session):
    user = User(email="test@example.com")
    db.add(user)

    # Create a savepoint
    savepoint = db.begin_nested()

    try:
        # Risky operation
        order = Order(user_id=user.id, total=1000000)
        db.add(order)
        db.flush()
    except Exception:
        # Rollback to savepoint, user is still added
        savepoint.rollback()

    db.commit()  # User is saved, order might not be
```

### Transaction Isolation Levels

Different levels control how transactions interact:

```python
from sqlalchemy import create_engine

# READ UNCOMMITTED - Can read uncommitted changes (dirty reads)
engine = create_engine(
    "postgresql://...",
    isolation_level="READ UNCOMMITTED"
)

# READ COMMITTED - Only read committed changes (default)
engine = create_engine(
    "postgresql://...",
    isolation_level="READ COMMITTED"
)

# REPEATABLE READ - Same read results within transaction
engine = create_engine(
    "postgresql://...",
    isolation_level="REPEATABLE READ"
)

# SERIALIZABLE - Highest isolation, slowest performance
engine = create_engine(
    "postgresql://...",
    isolation_level="SERIALIZABLE"
)
```

### Best Practices

1. **Keep transactions short** - Long transactions lock resources
2. **Don't commit in loops** - Batch operations when possible
3. **Always handle exceptions** - Use try/except with rollback
4. **Use context managers** - Ensures cleanup
5. **Avoid nested commits** - Use savepoints instead

---

## 5. Session Lifecycle and Commit/Rollback

### What is a Session?

A **Session** is SQLAlchemy's "workspace" for database operations. It manages the connection to the database and tracks changes to objects.

### Session States

Objects in a session can be in different states:

#### 1. Transient

Object exists in Python but not associated with any session or database.

```python
user = User(email="test@example.com")  # Transient
# Not in session, not in database
```

#### 2. Pending

Object is added to session but not yet in database.

```python
user = User(email="test@example.com")
db.add(user)  # Now Pending
# In session, not yet in database
```

#### 3. Persistent

Object is in session and exists in database.

```python
db.commit()  # Now Persistent
# In session, in database, changes are tracked
```

#### 4. Detached

Object was persistent but session was closed.

```python
db.close()
# user is now Detached - exists in database but not tracked
```

### Session Lifecycle

#### Creating a Session

```python
from sqlalchemy.orm import Session
from database import engine

# Create a new session
db = Session(bind=engine)
```

#### Using Dependency Injection (FastAPI)

```python
from database import get_db
from fastapi import Depends

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Session is automatically created and closed
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return db_user
```

### Understanding get_db()

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()  # Create session
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Always close session
```

### Commit vs Flush vs Refresh

#### commit()

- Saves all changes to database permanently
- Ends the current transaction
- Makes changes visible to other sessions

```python
user = User(email="test@example.com")
db.add(user)
db.commit()  # Permanent in database
```

#### flush()

- Sends SQL to database but doesn't commit
- Stays in same transaction
- Useful to get auto-generated IDs

```python
user = User(email="test@example.com")
db.add(user)
db.flush()  # SQL executed
print(user.id)  # ID is available
db.commit()  # Now permanent
```

#### refresh()

- Reloads object from database
- Discards in-memory changes
- Gets latest database values

```python
user = db.query(User).first()
user.email = "new@example.com"  # Change in memory
db.refresh(user)  # Reload from database
print(user.email)  # Original email, change discarded
```

### Common Patterns

#### Pattern 1: Standard CRUD Operation

```python
def create_user(user_data: dict, db: Session):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)  # Get updated fields like created_at
    return user
```

#### Pattern 2: Bulk Operations

```python
def create_multiple_users(users_data: list, db: Session):
    users = [User(**data) for data in users_data]
    db.add_all(users)  # Add multiple objects
    db.commit()
    return users
```

#### Pattern 3: Update with Validation

```python
def update_user(user_id: int, update_data: dict, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
```

#### Pattern 4: Conditional Commit

```python
def toggle_user_status(user_id: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()

    if user:
        user.is_active = not user.is_active
        db.commit()
        return True

    # No commit if user not found
    return False
```

### Session Expiry and Refresh

```python
# After commit, objects are expired by default
user = User(email="test@example.com")
db.add(user)
db.commit()

# Accessing attributes triggers refresh from database
print(user.email)  # Automatically refreshed

# Disable auto-expire
db.commit()
db.expire_on_commit = False
print(user.email)  # No database query
```

### Session Best Practices

1. **One session per request** - Create new session for each API request
2. **Always close sessions** - Use context managers or dependency injection
3. **Don't share sessions** - Each thread/request should have its own session
4. **Commit explicitly** - Don't rely on auto-commit
5. **Handle rollback in exceptions** - Always rollback on errors
6. **Refresh after commit** - Get updated values from database

### Complete Example: Session Lifecycle

```python
from sqlalchemy.orm import Session
from database import SessionLocal

def complete_user_workflow():
    # 1. Create session
    db = SessionLocal()

    try:
        # 2. Create object (Transient)
        user = User(email="test@example.com")
        print(f"State: Transient")

        # 3. Add to session (Pending)
        db.add(user)
        print(f"State: Pending, ID: {user.id}")  # ID is None

        # 4. Flush (still Pending, but ID available)
        db.flush()
        print(f"State: Pending, ID: {user.id}")  # ID is set

        # 5. Commit (Persistent)
        db.commit()
        print(f"State: Persistent, ID: {user.id}")

        # 6. Modify object
        user.email = "updated@example.com"
        db.commit()

        # 7. Refresh to get latest data
        db.refresh(user)

        return user

    except Exception as e:
        # Rollback on error
        db.rollback()
        raise e

    finally:
        # 8. Close session (object becomes Detached)
        db.close()
        print(f"State: Detached")
```

---

## Practice Assignment

### Objective

Create a complete FastAPI application with advanced SQLAlchemy operations demonstrating joins, filtering, aggregations, and transaction management using the existing database schema.

### Current Database Schema

Your `models.py` already contains these models:

```python
# User Model - stores user information
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone_number = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=False)
    address = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # One-to-One relationship with UserProfile
    profile = relationship("UserProfile", back_populates="user", uselist=False)

# UserProfile Model - stores additional user details
class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    address = Column(String(200), nullable=True)
    city = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="profile")

# Product Model - stores product information
class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    tags = Column(ARRAY(String), nullable=True)  # PostgreSQL array
    extra_data = Column(JSONB, nullable=True)    # JSON data

    # Many-to-Many relationship with RawMaterial
    raw_materials = relationship("RawMaterial", secondary=product_raw_material_association,
                                back_populates="products")

# RawMaterial Model - stores raw materials
class RawMaterial(Base):
    __tablename__ = "raw_materials"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)

    # Many-to-Many relationship with Product
    products = relationship("Product", secondary=product_raw_material_association,
                           back_populates="raw_materials")

# Association table for Product-RawMaterial many-to-many relationship
product_raw_material_association = Table(
    'product_raw_material_association',
    Base.metadata,
    Column('product_id', UUID(as_uuid=True), ForeignKey('products.id'), primary_key=True),
    Column('raw_material_id', UUID(as_uuid=True), ForeignKey('raw_materials.id'), primary_key=True)
)
```

### Relationship Summary

- **User ↔ UserProfile**: One-to-One (each user has one profile)
- **Product ↔ RawMaterial**: Many-to-Many (products use many materials, materials used in many products)

### Tasks to Implement

#### Task 1: Joins and Eager Loading (15 minutes)

Create the following endpoints:

1. **GET /users/{user_id}/complete**
   - Fetch user with their profile information
   - Use `joinedload()` for the one-to-one relationship
   - Avoid N+1 queries

2. **GET /products/{product_id}/with-materials**
   - Fetch product with all its raw materials
   - Use `selectinload()` for many-to-many relationship
   - Demonstrate eager loading efficiency

3. **GET /raw-materials/{material_id}/with-products**
   - Fetch raw material with all products that use it
   - Use appropriate eager loading
   - Show bidirectional relationship loading

**Expected Code:**

````python
from sqlalchemy.orm import joinedload, selectinload

@app.get("/users/{user_id}/complete")
def get_user_complete(user_id: str, db: Session = Depends(get_db)):
    # TODO: Implement with joinedload for User.profile
    # user = db.query(User).options(joinedload(User.profile))...
    pass

@app.get("/products/{product_id}/with-materials")
def get_product_with_materials(product_id: str, db: Session = Depends(get_db)):
    # TODO: Implement with selectinload for Product.raw_materials
    # product = db.query(Product).options(selectinload(Product.raw_materials))...
    pass

@app.get("/raw-materialsmin_price`, `max_price`, `search_term`, `tags`, `sort_by`
   - Support filtering by price range, name search, and tags (ARRAY field)
   - Sort by price or name

2. **GET /users/search**
   - Query parameters: `email_domain`, `is_active`, `has_profile`, `city`
   - Filter users by email pattern, activity status, and profile existence
   - Join with UserProfile to filter by city
   - Implement pagination

3. **GET /raw-materials/filter**
   - Query parameters: `min_quantity`, `max_quantity`, `name_pattern`, `used_in_products`
   - Filter by quantity range and name
   - Filter materials that are used in at least one product

**Expected Code:**
```python
from sqlalchemy import and_, or_, desc

@app.get("/products/search")
def search_products(
    min_price: float = None,
    max_price: float = None,
    search_term: str = None,
    tags: list[str] = None,
    sort_by: str = "name",
    db: Session = Depends(get_db)
):
    # TODO: Build query with filters
    # query = db.query(Product)
    # if min_price: query = query.filter(Product.price >= min_price)
    # if search_term: query = query.filter(Product.name.ilike(f"%{search_term}%"))
    # Handle ARRAY filtering for tags
    pass

@app.geUser information (email, full_name)
     - Whether they have a profile
     - Count of users by activity status
   - Group by is_active status

2. **GET /analytics/product-materials**
   - For each product, return:
     - Product name and price
     - Count of raw materials used
     - Total quantity of all raw materials
     - Average quantity per material
   - Only include products with at least 1 raw material

3. **GET /analytics/material-usage**
   - For each raw material, return:
     - Material name and quantity
     - Count of products using this material
     - Average price of products using this material
     - Most expensive product using this material
   - Group by raw material

**Expected Code:**
```python
from sqlalchemy import func

@app.get("/analytics/user-stats")
def get_user_stats(db: Session = Depends(get_db)):
    # TODO: Group users by is_active status
    # results = db.query(
    #     User.is_active,
    #     func.count(User.id).label('user_count'),
    #     func.count(UserProfile.id).label('users_with_profile')
    # ).outerjoin(UserProfile).group_by(User.is_active).all()
    pass

@app.get("/analytics/product-materials")
def get_product_material_stats(db: Session = Depends(get_db)):
    # TODO: Join with RawMaterial through association table
    # TODO: Use func.count(), func.sum(), func.avg()
    # TODO: Use group_by(Product.id) and having()
    pass
products/create-with-materials**
   - Create a product and associate it with multiple raw materials
   - Validate that all raw materials exist
   - All operations must succeed or all fail (atomicity)
   - Rollback if any validation fails

2. **POST /products/{product_id}/add-materials**
   - Add multiple raw materials to an existing product
   - Decrease each raw material's quantity
   - Use transaction to ensure consistency
   - Rollback if insufficient quantity

3. **POST /users/create-with-profile**
   - Create a user and their profile in one transaction
   - Use flush() to get the user ID before creating profile
   - Demonstrate nested object creation

**Expected Code:**
```python
from pydantic import BaseModel

class ProductWithMaterials(BaseModel):
    name: str
    description: str
    price: float
    material_ids: list[str]

class MaterialUpdate(BaseModel):
    material_id: str
    quantity_used: float

@app.post("/products/create-with-materials")
def create_product_with_materials(data: ProductWithMaterials, db: Session = Depends(get_db)):
    try:
        # TODO: Start transaction (implicit)
        # TODO: Validate all materials exist
        # TODO: Create product
        # TODO: Associate materials
        # TODO: Commit transaction
        pass
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
to models and filter deleted records
2. **JSONB queries** - Query the `extra_data` JSONB field in Product model
3. **Array operations** - Filter products by tags using PostgreSQL ARRAY operators
4. **Optimize queries** - Use `query.statement` to print SQL and optimize
5. **Complex aggregations** - Create a report showing which materials are running low based on product demand
6. **Cascade deletes** - Handle deletion of users with their profiles properly
7. **Bulk operations** - Create endpoint to bulk insert products with materials efficiently
    db: Session = Depends(get_db)
):
    try:
        # TODO: Fetch product
        # TODO: For each material, check quantity and decrease
        # TODO: Add to product.raw_materials
        # TODO: Commit or rollback
        pass
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/users/create-with-profile")
def create_user_with_profile(user_data: dict, profile_data: dict, db: Session = Depends(get_db)):
    try:
        # TODO: Create user
        # TODO: Use flush() to get user.id
        # TODO: Create profile with user_id
   All endpoints implemented in `main.py` using existing models
2. Demonstrate proper eager loading (no N+1 queries)
3. Show transaction handling with rollback scenarios
4. Complex aggregation queries working correctly
5. Test file with at least 8 test cases covering all task=400, detail=str(e))DO: Aggregate by product and category
    pass
````

#### Task 4: Transaction Management (15 minutes)

Create the following endpoints that require transaction handling:

1. **POST /orders/create**
   - Create an order with multiple items
   - Decrease product stock for each item
   - Calculate total
   - All operations must succeed or all fail (atomicity)
   - Rollback if insufficient stock

2. **POST /orders/{order_id}/cancel**
   - Cancel order
   - Return items to stock
   - Update order status
   - Use transaction to ensure consistency

3. **POST /products/{product_id}/restock**
   - Add quantity to product stock
   - Create a stock history record
   - Use flush() to get generated IDs

**Expected Code:**

```python
@app.post("/orders/create")
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        # TODO: Start transaction
        # TODO: Validate stock availability
        # TODO: Create order and order items
        # TODO: Update product stock
        # TODO: Commit transaction
        pass
    except Exception as e:
        # TODO: Rollback on error
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    # TODO: Implement with proper transaction handling
    # TODO: Use flush() if needed to get IDs
    pass
```

### Bonus Challenges

1. **Implement soft deletes** - Add `deleted_at` field and filter deleted records
2. **Add caching** - Cache frequently accessed queries
3. **Optimize queries** - Use `query.statement` to print SQL and optimize
4. **Add database indexes** - Identify slow queries and add indexes
5. **Implement full-text search** - Use PostgreSQL full-text search

### Testing Your Implementation

Create test cases for:

1. Verify no N+1 queries (print SQL statements)
2. Test transaction rollback scenarios
3. Validate aggregation results
4. Test complex filtering combinations
5. Verify pagination works correctly

```python
# Enable SQL logging to see queries
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Deliverables

1. Complete `models.py` with all relationships
2. All endpoints implemented in `main.py`
3. Alembic migrations for the schema
4. README with API documentation
5. Test file with at least 10 test cases

### Evaluation Criteria

- **Correctness**: All endpoints work as expected
- **Query Optimization**: No N+1 queries, proper eager loading
- **Transaction Handling**: Proper commit/rollback logic
- **Code Quality**: Clean, readable, well-documented code
- **Error Handling**: Proper exception handling and user feedback

---

## Key Takeaways Summary

### Joins and Eager Loading

- ✅ Use `joinedload()` for one-to-one relationships
- ✅ Use `selectinload()` for one-to-many relationships
- ✅ Always avoid N+1 query problems
- ✅ Print SQL to verify query efficiency

### Filtering and Sorting

- ✅ Use `filter()` for complex conditions
- ✅ Combine `and_()`, `or_()`, `not_()` for logic
- ✅ Use `order_by()` with `desc()` for sorting
- ✅ Implement pagination with `limit()` and `offset()`

### Aggregations

- ✅ Use `func.count()`, `func.sum()`, `func.avg()` for calculations
- ✅ Group results with `group_by()`
- ✅ Filter groups with `having()`
- ✅ Combine multiple aggregations in one query

### Transaction Management

- ✅ Always use try/except with commit/rollback
- ✅ Keep transactions short and focused
- ✅ Use `flush()` to get generated IDs without committing
- ✅ Understand ACID properties

### Session Lifecycle

- ✅ One session per request (use dependency injection)
- ✅ Always close sessions (use `finally` or context managers)
- ✅ Understand object states: Transient → Pending → Persistent → Detached
- ✅ Use `refresh()` to reload data from database

---

## Additional Resources

### Documentation

- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/tutorial.html)
- [SQLAlchemy Relationship Loading](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html)
- [FastAPI SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### Common Pitfalls to Avoid

1. ❌ Not using eager loading (N+1 queries)
2. ❌ Forgetting to commit transactions
3. ❌ Sharing sessions across requests
4. ❌ Not handling rollback on errors
5. ❌ Using lazy loading in production
6. ❌ Not closing database sessions
7. ❌ Committing inside loops
8. ❌ Not validating data before commit

### Performance Tips

- Enable SQL query logging during development
- Use `explain()` to analyze query plans
- Add database indexes on frequently queried columns
- Use `joinedload()` sparingly (can create large result sets)
- Batch operations when possible
- Use connection pooling
- Monitor slow queries

---

## Questions for Discussion

1. What's the difference between `joinedload()` and `selectinload()`?
2. When would you use `flush()` instead of `commit()`?
3. How do you prevent the N+1 query problem?
4. What happens if you don't rollback after an exception?
5. Why is `HAVING` different from `WHERE`?
6. What are the four ACID properties and why are they important?
7. How does SQLAlchemy track changes to objects?
8. What's the difference between `filter()` and `filter_by()`?

---

**Good luck with your teaching session! 🚀**
