# SQLAlchemy FastAPI Learning Project

This project demonstrates how to use SQLAlchemy with FastAPI with automatic database migrations using Alembic.

## Project Structure

```
sql_app/
├── alembic/              # Alembic migration files
│   ├── versions/         # Migration scripts
│   ├── env.py           # Alembic environment configuration
│   └── script.py.mako   # Migration template
├── alembic.ini          # Alembic configuration
├── database.py          # Database connection and session
├── models.py            # SQLAlchemy models
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── run.sh              # Helper script
└── README.md           # This file
```

## Setup

### 1. Install Dependencies

```bash
cd sql_app
pip install -r requirements.txt
```

Or use the helper script:

```bash
./run.sh install
```

### 2. Configure Database

Update the database URL in:

- `alembic.ini` (line 63): `sqlalchemy.url = postgresql+psycopg2://postgres:postgres@localhost/fastapi-learning`
- `database.py` (line 9): `DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost/fastapi-learning"`

Make sure your PostgreSQL database `fastapi-learning` exists:

```bash
createdb fastapi-learning
```

### 3. Create Initial Migration

```bash
cd sql_app
alembic revision --autogenerate -m "Initial migration"
```

Or use the helper script:

```bash
./run.sh migrate "Initial migration"
```

### 4. Run the Application

The migrations will run automatically when you start the server:

```bash
cd ..  # Go back to fastapilearning directory
uvicorn sql_app.main:app --reload
```

Or use the helper script from the sql_app directory:

```bash
./run.sh run    # Runs on 0.0.0.0:8000
# or
./run.sh dev    # Runs on 127.0.0.1:8000
```

## Helper Script Commands

The `run.sh` script provides convenient commands:

- `./run.sh install` - Install project dependencies
- `./run.sh migrate "message"` - Create a new migration with autogenerate
- `./run.sh upgrade` - Run all pending migrations
- `./run.sh downgrade` - Rollback last migration
- `./run.sh run` - Start FastAPI server (accessible from all network interfaces)
- `./run.sh dev` - Start FastAPI server (localhost only)
- `./run.sh init-db` - Initialize database without Alembic (not recommended)

## How It Works

### Automatic Migrations on Startup

The application is configured to run Alembic migrations automatically when the server starts using FastAPI's `lifespan` context manager in [main.py](sql_app/main.py):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    print("Running database migrations...")
    try:
        run_migrations()
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
    yield
    print("Shutting down...")
```

This means:

1. Every time you start the server, it checks for pending migrations
2. Applies any new migrations automatically
3. Your database schema is always up to date

### Creating New Migrations

When you modify your models:

1. Edit `models.py` with your changes
2. Create a migration: `./run.sh migrate "description of changes"`
3. Review the generated migration in `alembic/versions/`
4. Start the server - migrations run automatically!

Or manually:

```bash
alembic upgrade head
```

## Database Models

The project includes these models:

- **User**: User accounts with email, password, profile info
- **UserProfile**: Additional user profile information
- **Product**: Products with prices, descriptions, and metadata
- **RawMaterial**: Raw materials used in products
- **product_raw_material_association**: Many-to-many relationship table

## API Endpoints

- `GET /` - Hello World
- `GET /items/{item_id}` - Get item by ID (demo data)
- `POST /items/` - Create new item
- `GET /items/` - List all items
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

## Development Workflow

1. Modify models in `models.py`
2. Create migration: `./run.sh migrate "your changes"`
3. Start server: `./run.sh dev`
4. Migrations run automatically on startup
5. Test your API endpoints

## Manual Migration Commands

If you prefer manual control:

```bash
# Create a new migration
alembic revision --autogenerate -m "your message"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration status
alembic current

# View migration history
alembic history
```

## Troubleshooting

### Migration fails to run

- Check database connection in `alembic.ini` and `database.py`
- Ensure database exists: `createdb fastapi-learning`
- Check PostgreSQL is running

### Models not detected in migration

- Make sure models are imported in `alembic/env.py`
- Verify `target_metadata = Base.metadata` is set correctly

### Database connection error

- Verify PostgreSQL credentials
- Check database name exists
- Ensure PostgreSQL service is running

## Best Practices

1. **Always review generated migrations** before applying them
2. **Test migrations** in development before production
3. **Backup your database** before running migrations in production
4. **Use descriptive migration messages** to track changes
5. **Don't edit applied migrations** - create new ones instead

## Production Deployment

For production, you might want to:

1. Remove automatic migrations from startup
2. Run migrations manually or via CI/CD pipeline
3. Use environment variables for database credentials
4. Add proper error handling and logging

Example production startup without auto-migrations:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    # Don't run migrations automatically in production
    # Run them manually: alembic upgrade head
    yield
    print("Shutting down...")
```
