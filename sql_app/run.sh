#!/bin/bash

# SQLAlchemy FastAPI Project Helper Script

case "$1" in
  install)
    echo "Installing dependencies..."
    pip install -r requirements.txt
    ;;
  
  migrate)
    echo "Creating new migration..."
    if [ -z "$2" ]; then
      echo "Error: Please provide a migration message"
      echo "Usage: ./run.sh migrate 'your migration message'"
      exit 1
    fi
    cd "$(dirname "$0")"
    alembic revision --autogenerate -m "$2"
    ;;
  
  upgrade)
    echo "Running migrations..."
    cd "$(dirname "$0")"
    alembic upgrade head
    ;;
  
  downgrade)
    echo "Downgrading migration..."
    cd "$(dirname "$0")"
    alembic downgrade -1
    ;;
  
  run)
    echo "Starting FastAPI server with auto-reload..."
    cd "$(dirname "$0")/.."
    uvicorn sql_app.main:app --reload --host 0.0.0.0 --port 8000
    ;;
  
  dev)
    echo "Starting FastAPI server in development mode..."
    cd "$(dirname "$0")/.."
    uvicorn sql_app.main:app --reload --host 127.0.0.1 --port 8000
    ;;
  
  init-db)
    echo "Initializing database..."
    cd "$(dirname "$0")"
    python -c "from database import init_db; init_db(); print('Database initialized!')"
    ;;
  
  *)
    echo "SQLAlchemy FastAPI Helper Script"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install              Install project dependencies"
    echo "  migrate 'message'    Create a new migration with autogenerate"
    echo "  upgrade              Run all pending migrations"
    echo "  downgrade            Rollback last migration"
    echo "  run                  Start FastAPI server (auto-reload, all interfaces)"
    echo "  dev                  Start FastAPI server (auto-reload, localhost only)"
    echo "  init-db              Initialize database (create tables without Alembic)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh install"
    echo "  ./run.sh migrate 'add user table'"
    echo "  ./run.sh upgrade"
    echo "  ./run.sh run"
    ;;
esac
