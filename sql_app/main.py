from typing import Union, Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response, status, BackgroundTasks, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db, init_db
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy.orm import Session, joinedload
from models import User, UserProfile
from alembic.config import Config
from alembic import command
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import os
import bcrypt
import uuid
import time
import json
import asyncio
import aiofiles
import imghdr
import io
from pathlib import Path
from PIL import Image
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone

# Import Redis client and caching utilities
from redis_client import RedisClient
from cache_utils import CacheMetrics, cache_result, cache_evict, TaggedCache
from session_manager import SessionManager

# Import OAuth2 authentication utilities
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_active_user,
    verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    # RBAC imports
    require_admin,
    require_manager_or_admin,
    require_role,
    require_permission,
    Permission,
    has_permission
)
from models import UserRole
from schemas import (
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
    RefreshTokenRequest,
    MessageResponse,
    ProfilePictureUploadResponse
)

class Item(BaseModel):
    id: Union[int, None] = None
    name: str
    description: Union[str, None] = "Testing description"
    price: float

class UpdateItem(BaseModel):
    id: Union[int, None] 
    name: Union[str, None]
    description: Union[str, None]
    price: Union[float, None]

items_array = [

]




class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"]= "nosniff"
        response.headers["X-Frame-Options"]= "DENY"
        response.headers["X-XSS-PROTECTION"]= "1; mode=block"

        response.headers["Referrer-Policy"]= "strict-origin-when-cross-origin"

        return response
    




def run_migrations():
    """Run Alembic migrations automatically"""
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(current_dir, "alembic.ini")
    
    # Create Alembic config and set the script location
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(current_dir, "alembic"))
    
    command.upgrade(alembic_cfg, "head")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("🚀 Starting up...")
    print("📦 Running database migrations...")
    
    try:
        run_migrations()
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
    
    # Initialize Redis
    print("🔴 Connecting to Redis...")
    app.state.redis = RedisClient()
    try:
        await app.state.redis.connect()
        print("✅ Redis connected successfully!")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("⚠️  Running without Redis caching")
        app.state.redis = None
    
    yield
    
    # Shutdown code
    print("🛑 Shutting down...")
    if app.state.redis:
        await app.state.redis.disconnect()

app = FastAPI(lifespan=lifespan)


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# Redis dependency
async def get_redis() -> Optional[RedisClient]:
    """Get Redis client from app state"""
    redis = getattr(app.state, 'redis', None)
    return redis


app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(GZipMiddleware, minimum_size=1000)


rate_limit_store = {}
MAX_REQUESTS_PER_MINUTE = 5
TIME_WINDOW = 60  # seconds

# @app.middleware("http")
# async def rate_limit_middleware(request, call_next):
#     client_ip = request.client.host
#     current_time = time.time()
#     print("Client IP:", client_ip)

#     request_time= rate_limit_store.get(client_ip, {"count": 0, "start_time": current_time})
#     elapsed_time = current_time - request_time["start_time"]
#     if elapsed_time > TIME_WINDOW:
#         request_time = {"count": 1, "start_time": current_time}
#     else:
#         request_time["count"] += 1

#     rate_limit_store[client_ip] = request_time
#     print("Request count for IP", client_ip, ":", request_time["count"])
#     print("Elapsed time for IP", client_ip, ":", elapsed_time)
#     if request_time["count"] > MAX_REQUESTS_PER_MINUTE:
#         return JSONResponse(status_code=429, content={"error": "Too many requests"})

#     response = await call_next(request)
#     return response



class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time= time.time()
        print(f"Processing request: {request.method} {request.url}")
        response = await call_next(request)
        process_time= time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        print(f"Completed request: {request.method} {request.url} in {process_time} seconds")
        return response
        
    

@app.middleware("http")
async def modify_response_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "CustomValue"
    response.headers["X-Powered-By"] = "FastAPI"

    return response


app.add_middleware(ProcessTimeMiddleware)
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
  #response = await call_next(request)

    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response


@app.get("/")
def read_root():
    print("Root endpoint accessed")
    return {"Hello": "World"}




@app.get("/items/{item_id}")
def get_item_stock(item_id: int):
    item_records = {
        1: {"name": "Item One", "stock": 10},
        2: {"name": "Item Two", "stock": 0},
        3: {"name": "Item Three", "stock": 5},
    }

    item = item_records.get(item_id)
    if item:
        return {"item_id": item_id, "name": item["name"], "stock": item["stock"]}
    else:
        return {"error": "Item not found"}
    return { "item_id": item_id, "name": "Sample Item", "stock": 42 }
  

@app.post("/items/")
def create_item(item: Item):

    item_new_id = len(items_array) + 1
    item.id = item_new_id

    items_array.append(item)
    return len(items_array)


@app.get("/items/")
def read_items():
    return items_array


@app.put("/items/{item_id}")
def update_item(item_id: int, item: UpdateItem):
    for index, existing_item in enumerate(items_array):
        if existing_item.id == item_id:
            item.id = item_id
            items_array[index] = item
            return {"message": "Item updated successfully"}
    return {"error": "Item not found"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    for index, existing_item in enumerate(items_array):
        if existing_item.id == item_id:
            del items_array[index]
            return {"message": "Item deleted successfully"}
    return {"error": "Item not found"}



# INSERT INTO USERS (email, hashed_password....) VALUES ('ARIF@GMAIL.COM, "JDSNDS"..)

# user = User(email = "arifwip@gmail.com", hashed_password = "jdsnjddsnj"l, full_name = "Arif", phone_number = "1234567890")
# db.add(user)
# db.commit()




# UserCreate and UserResponse are imported from schemas.py - don't redefine them here


class ErrorResponse(BaseModel):
    error: str


@app.post("/users/", response_model= UserResponse)
def create_user(user: UserCreate, db: Session= Depends(get_db)):
    hashed_password = user.password;


    db_user= User(
        email = user.email,
        hashed_password = hashed_password,
        full_name= user.full_name,
        phone_number = user.phone_number
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print("asjsndjnsd", db_user.id)
    return {"message": "User created successfully", "user_id": str(db_user.id)}



@app.get("/users/", response_model= list[UserResponse])
def get_users(skip: int = 0, limit: int = 10,db:Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    print("Users existing: ", users)
    return users


@app.get("/users/{user_id}", response_model= Union[UserResponse, ErrorResponse])
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return {"error": "User not found"}
    return user


class UserUpdate(BaseModel):
    email: Union[EmailStr, None] = None
    full_name: Union[str, None] = None
    phone_number: Union[str,None] = None

# PUT /users/{user_id} - Update user details
@app.put("/users/{user_id}")
def update_user(user_id: str, user_update:UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return {"error": "User doesn't exist"}
    
    update_data = user_update.dict(exclude_unset=True)
    print("test update data", update_data)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    print("final db user", db_user)
    
    db.commit()
    db.refresh(db_user)

    return db_user

    

# joins and eager loading
# filtering and sorting 
# aggregations
#transaction managment 


class UserProfileCreate(BaseModel):
    address: Union[str, None] = None
    city: Union[str, None] = None
    country: Union[str, None] = None
    postal_code: Union[str, None] = None


@app.post("/users/{user_uuid}/profile")
def create_user_profile(user_uuid: str, profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_uuid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    print("Creating profile for user:", db_user)

    print("Profile data:", profile)

    db_profile = UserProfile(
        user_id = db_user.id,
        address = profile.address,
        city = profile.city,
        country = profile.country,
        postal_code=profile.postal_code
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return {"message": "User profile created successfully", "profile_id": str(db_profile.id)
    }



#inner join
@app.get("/users_with_profiles/")
def get_users_with_profile(db: Session = Depends(get_db)):
    users_with_profiles = db.query(User).join(UserProfile).all()




    print("users with profiles ", users_with_profiles)


#left outer join
@app.get("/users_profiles/left_join/")
def get_users_with_profiles_left_join(db: Session = Depends(get_db)):
    users_with_profiles = db.query(User).outerjoin(UserProfile).all()

    for user in users_with_profiles:
        print("User:", user.email)
        if user.profile:
            print("  Profile Address:", user.profile.address)
        else:
            print("  No profile available")

    print("users with profiles (left join) ", users_with_profiles)



# n+1 problem 

#joined loading 

@app.get("/users_profiles/joined_load/")
def get_users_with_profiles_joined_load(db: Session = Depends(get_db)):
    users_with_profiles = db.query(User).options(joinedload(User.profile)).all()

    for user in users_with_profiles:
        print("User:", user.email)
        if user.profile:
            print("  Profile Address:", user.profile.address)
        else:
            print("  No profile available")

    print("users with profiles (joined load) ", users_with_profiles)
    return users_with_profiles



def my_dependency():
    print("Executing my_dependency")
    return "some_value"



@app.get("/test-dependency/")
def test_dependency(value: str = Depends(my_dependency)):
    print("Value from dependency:", value)
    return {"dependency_value": value}



#Dependency with time 

@lru_cache()
def current_time_dependency():
    from datetime import datetime
    now = datetime.now()
    return now


@app.get("/time/")
def get_current_time(current: str = Depends(current_time_dependency)):
    return {"current_time": current}


#Dependency without return value
def verify_api_key(api_key: str = Header(...)):
    if api_key  != "secret-api-key":
       raise HTTPException(status_code=403, detail="Invalid API Key")




@app.get("/protected/")
def protected_endpoint(verified: None = Depends(verify_api_key)):
    return {"message": "You have access to this protected endpoint."}



@app.get("/exception/")
def raise_exception():
    raise HTTPException(status_code=400, detail="This is a custom exception message", headers={"X-Error": "There goes my error"})


@app.get("/custom-error/")
def custom_error():
    raise HTTPException(status_code= 401, detail = "Unauthorized access", headers={"X-Custom-Error": "Custom error header"})



#custom exception handler 

class UserNotFoundException(Exception):
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.message = f"User with ID {user_id} not found"
        super().__init__(self.message)


@app.exception_handler(UserNotFoundException)
async def user_not_found_exception(request:Request, exc: UserNotFoundException):
    print(f"Handling UserNotFoundException for user ID: {exc.user_id}")

    return JSONResponse(
        status_code= 404,
        content= {
            "error": "User not found",
            "message": exc.message,
            "user_id": exc.user_id,
            "timestamp": time.time()
        }
    )


@app.get("/users/test_exception/{user_id}")
async def get_user_test_exception(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id=user_id)
    return user



class InvalidAPIKeyException(Exception):
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.message = f"API Key {api_key} is invalid"
        super().__init__(self.message)


@app.exception_handler(InvalidAPIKeyException)
async def invalid_api_key_exception_handler(request: Request, exc: InvalidAPIKeyException):
    print(f"Handling InvalidAPIKeyException for API Key: {exc.api_key}")
    return JSONResponse(
        status_code= 403,
        content= {
            "error": "Invalid API Key",
            "message": exc.message,
            "api_key": exc.api_key,
            "timestamp": time.time()
        }
    )


@app.get("/test-invalid-api-key/")
def test_invalid_api_key(api_key: str = Header(...)):
    if api_key != "expected-api-key":
        raise InvalidAPIKeyException(api_key=api_key)
    return {"message": "Valid API Key"}


#global exception handler 

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global exception handler caught an error: {exc}")
    return JSONResponse(
        status_code= 500,
        content= {
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": time.time()
        }
    )


@app.get("/test-global-exception/")
def test_global_exception():
    raise Exception("This is a test exception for the global handler")



@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    print("Handling SQLAlchemyError:", exc)
    return JSONResponse(
        status_code= 500,
        content= {
            "error": "Database Error",
            "message": str(exc),
            "timestamp": time.time()
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type")
        })

    print ("Handling ValidationError:", errors)
    return JSONResponse(
        status_code= 422,
        content= {
            "error": "Validation Error",
            "message": errors,
            "timestamp": time.time()
        }
    )

@app.get("/test-pydantic-validation/")
async def test_pydantic_validation():
    class TestModel(BaseModel):
        name: str
        age: int

    invalid_data = {
        "name": "John Doe",
        "age": "not_an_integer"
    }

    test_model = TestModel(**invalid_data)
    return test_model


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    timestamp: float


def create_error_response_model(error: str, message: str) -> ErrorResponseModel:
    return ErrorResponseModel(
        error= error,
        message= message,
        timestamp= time.time()
    )


@app.get("/test-error-response-model/")
async def test_error_response_model():
    error_response = create_error_response_model("Sample Error",4)
    return error_response


#without type annotation


@app.get("/no-type-annotation/")
def no_type_annotation():
    age = 16
    return {"age": age}


#with type annotation
@app.post("/with-type-annotation/")
def with_type_annotation(age : Optional[int] = 16)-> dict:
    return {"age": age}


@app.get("/calculate/")
def calculate(num1:int, num2:int):
    
    return {"result": num1 + num2}





def write_log(message:str):
    with open("app.log", "a") as log_file:
        log_file.write(f"{time.ctime()}: {message}\n")



@app.post("/background-tasks/")
async def background_tasks_test(email: str, background_tasks:BackgroundTasks):
    background_tasks.add_task(write_log, f"Background task executed for email: {email}")

    return {"message": "Background task scheduled"}



def send_email(email:str, body: str):
    time.sleep(10)


    print(f"Email sent to {email} : {body}")



@app.post("/notify/")
def notify(email:str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Hello")
    return {"message": "Notification queued"}





async def send_email_async(email:str, message: str):
    import asyncio 
    asyncio.sleep(12)
    print(f"Email sent to {email} : {message}")


@app.post("/test-async/")
async def test_async_function(email: str, background_tasks: BackgroundTasks ):
    background_tasks.add_task(send_email_async, email, "hello")
    return {

        "message": "Email enqued successfully"
    }



hashed_password_value = ""


@app.post("/hash-password/")
async def hash_password_function(password: str):
    global hashed_password_value
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password_bytes, salt)
    hashed_password_value = hashed_password

    print("hashed password stored : ", hashed_password_value)
    
    return {
        "hashed_password": hashed_password
    }


@app.post("/check_password/")
async def check_password_hashing(password: str):
    print(f"entered password : {password}")
    entered_password_bytes = password.encode("utf-8")
    if bcrypt.checkpw(entered_password_bytes, hashed_password_value):
        return {"status": "password correct"}
    else:
        return {"status": "password wrong"}




SECRET_KEY = "test-scret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES= 30


# OLD CREATE TOKEN FUNCTIONS - REPLACED BY functions in auth.py
# def create_access_token(data: dict, expires_data: Optional= None):
#     to_encode = data.copy()
#     if expires_data:
#         expire = datetime.now(timezone.utc) +expires_data
#     else: 
#         expire = datetime.now(timezone.utc)+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     to_encode.update({"type": "access"})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
#     return encoded_jwt
#
# def create_refresh_token(data:dict, expires_data: Optional= None):
#     to_encode = data.copy()
#     if expires_data:
#         expire = datetime.utcnow()+ expires_data
#     else: 
#         expire = datetime.utcnow()+ timedelta(days=7)
#     to_encode.update({"exp": expire})
#     to_encode.update({"type": "refresh"})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
#     print("Refresh token created: ", encoded_jwt)
#     return encoded_jwt


# ==================== OAuth2 AUTHENTICATION ENDPOINTS ====================

@app.post("/token", response_model=Token, tags=["OAuth2 Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint.
    
    This endpoint follows the OAuth2 password flow standard.
    - Use 'username' field for email (OAuth2 standard)
    - Use 'password' field for password
    - Returns access_token and refresh_token
    
    The Swagger UI "Authorize" button uses this endpoint automatically.
    """
    # OAuth2 standard uses 'username' field, but we authenticate with email
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access and refresh tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


@app.post("/register", response_model=MessageResponse, tags=["OAuth2 Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - Creates a new user account with hashed password
    - Email must be unique
    - Password is automatically hashed using bcrypt
    """
    # Check if user already exists
    print("user email for registration: ", user.email)
    print("user password for registration: ", user.password)
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create new user
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=user.role,  # Use role from UserCreate schema
        is_active=True  # Activate user immediately (or set to False for email verification)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": f"User registered successfully. User ID: {str(db_user.id)}"}


@app.post("/refresh", response_model=Token, tags=["OAuth2 Authentication"])
def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    
    - Provide a valid refresh token
    - Returns a new access token
    - Refresh token remains valid until expiration
    """
    user = verify_refresh_token(refresh_request.refresh_token, db)
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }



# OLD LOGIN ENDPOINT - REPLACED BY /token (OAuth2 standard)
# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str
#
# @app.post("/login/user/")
# def login_user(user: UserLogin, db: Session = Depends(get_db)):
#     db_user= db.query(User).filter(User.email == user.email).first()
#     if not db_user:
#         raise HTTPException(status_code=400, detail="Invalid credentials")
#     if db_user.hashed_password != user.password:
#         raise HTTPException(status_code=400, detail="Invalid credentials")
#     access_token = create_access_token(data={"sub": str(db_user.id)})
#     refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }


# ==================== PROTECTED ENDPOINTS EXAMPLES ====================

@app.get("/protected/data", tags=["OAuth2 Authentication"])
async def get_protected_data(current_user: User = Depends(get_current_active_user)):
    """
    Example of a protected endpoint that requires authentication.
    
    This demonstrates how to protect any endpoint using OAuth2.
    Simply add 'current_user: User = Depends(get_current_active_user)' as a parameter.
    """
    return {
        "message": "This is protected data",
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "access_granted": True
    }


# ==================== FILE UPLOAD CONFIGURATION ====================

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# File upload settings
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


# ==================== FILE VALIDATION HELPERS ====================

async def validate_image_file(file: UploadFile) -> str:
    """
    Validate image file by reading magic bytes.
    More secure than checking MIME type or extension.
    Returns: image type (jpeg, png, gif, webp)
    """
    # Read first 512 bytes for magic number check
    header = await file.read(512)
    await file.seek(0)
    
    # Detect image type from content
    image_type = imghdr.what(None, h=header)
    
    if image_type not in ['jpeg', 'png', 'gif', 'webp']:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file. Only JPEG, PNG, GIF, and WebP are allowed."
        )
    
    return image_type


async def validate_upload_file(
    file: UploadFile,
    max_size: int = MAX_FILE_SIZE,
    allowed_types: set = ALLOWED_CONTENT_TYPES
):
    """
    Comprehensive file validation:
    - Content type
    - File extension
    - File size
    - Magic bytes (actual file content)
    """
    # Validate content type
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Allowed: {allowed_types}"
        )
    
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
        )
    
    # Validate actual file content (magic bytes)
    await validate_image_file(file)
    
    # Validate size
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(contents)} bytes. Max size: {max_size} bytes ({max_size / (1024*1024):.1f} MB)"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    return True


# ==================== FILE STORAGE HELPERS ====================

def get_upload_path(user_id: str, file_type: str = "profile_pictures") -> Path:
    """
    Organize files by user and date.
    Structure: uploads/{user_id}/{year}/{month}/{file}
    """
    now = datetime.now()
    upload_path = (
        UPLOAD_DIR / 
        str(user_id) / 
        str(now.year) / 
        f"{now.month:02d}"
    )
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


async def process_image(file: UploadFile, max_size: tuple = (1000, 1000)) -> bytes:
    """
    Process image: resize, convert to RGB, optimize.
    Returns: processed image as bytes
    """
    # Read uploaded file
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Convert to RGB (removes alpha channel)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize image (maintain aspect ratio)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    return output.getvalue()


async def create_thumbnail(file: UploadFile, size: tuple = (200, 200)) -> bytes:
    """
    Create square thumbnail from uploaded image.
    Returns: thumbnail as bytes
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Convert to RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Create thumbnail (maintains aspect ratio)
    image.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    return output.getvalue()


async def save_with_thumbnail(file: UploadFile, user_id: str) -> dict:
    """
    Save original processed image and thumbnail.
    Returns: dict with paths to both files
    """
    # Get upload path
    upload_path = get_upload_path(user_id, "profile_pictures")
    
    # Generate unique filenames
    unique_id = uuid.uuid4()
    original_filename = f"{unique_id}.jpg"
    thumbnail_filename = f"{unique_id}_thumb.jpg"
    
    original_path = upload_path / original_filename
    thumbnail_path = upload_path / thumbnail_filename
    
    # Process and save original
    processed_image = await process_image(file, max_size=(1000, 1000))
    async with aiofiles.open(original_path, 'wb') as f:
        await f.write(processed_image)
    
    # Reset file pointer
    await file.seek(0)
    
    # Create and save thumbnail
    thumbnail_image = await create_thumbnail(file, size=(200, 200))
    async with aiofiles.open(thumbnail_path, 'wb') as f:
        await f.write(thumbnail_image)
    
    # Return relative paths for database storage
    return {
        "original": str(original_path.relative_to(UPLOAD_DIR)),
        "thumbnail": str(thumbnail_path.relative_to(UPLOAD_DIR))
    }


async def delete_user_pictures(user: User):
    """
    Delete user's profile pictures from disk.
    """
    if user.profile_picture_url:
        original_path = UPLOAD_DIR / user.profile_picture_url
        if original_path.exists():
            original_path.unlink()
    
    if user.profile_picture_thumbnail_url:
        thumbnail_path = UPLOAD_DIR / user.profile_picture_thumbnail_url
        if thumbnail_path.exists():
            thumbnail_path.unlink()


# ==================== FILE UPLOAD ENDPOINTS ====================

@app.post(
    "/users/me/profile-picture",
    response_model=ProfilePictureUploadResponse,
    tags=["File Upload"],
    summary="Upload Profile Picture",
    description="Upload a profile picture for the authenticated user. Supports JPEG, PNG, GIF, and WebP formats. Max size: 5MB."
)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process profile picture for authenticated user.
    
    Features:
    - Validates file type, size, and content
    - Resizes to max 1000x1000 (maintains aspect ratio)
    - Creates 200x200 thumbnail
    - Converts to JPEG format
    - Optimizes for web (85% quality)
    - Deletes old profile pictures if they exist
    
    **Requirements:**
    - Authentication required (Bearer token)
    - File must be image (JPEG, PNG, GIF, WebP)
    - Max file size: 5MB
    
    **Returns:**
    - Success message
    - URL to full-size profile picture
    - URL to thumbnail
    """
    try:
        # Validate uploaded file
        await validate_upload_file(file)
        
        # Delete old profile pictures if they exist
        await delete_user_pictures(current_user)
        
        # Save new pictures
        paths = await save_with_thumbnail(file, str(current_user.id))
        
        # Update user record in database
        current_user.profile_picture_url = paths["original"]
        current_user.profile_picture_thumbnail_url = paths["thumbnail"]
        db.commit()
        db.refresh(current_user)
        
        return ProfilePictureUploadResponse(
            message="Profile picture uploaded successfully",
            profile_picture_url=paths["original"],
            thumbnail_url=paths["thumbnail"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading profile picture: {str(e)}"
        )


@app.get(
    "/users/{user_id}/profile-picture",
    tags=["File Upload"],
    summary="Get Profile Picture",
    description="Download user's profile picture (full size or thumbnail)"
)
async def get_profile_picture(
    user_id: uuid.UUID,
    size: str = "full",
    db: Session = Depends(get_db)
):
    """
    Get user's profile picture.
    
    **Parameters:**
    - user_id: UUID of the user
    - size: "full" or "thumbnail" (default: "full")
    
    **Returns:**
    - Image file (JPEG format)
    
    **Errors:**
    - 404: User not found or no profile picture
    - 400: Invalid size parameter
    """
    # Validate size parameter
    if size not in ["full", "thumbnail"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid size parameter. Must be 'full' or 'thumbnail'"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Get appropriate file path
    if size == "thumbnail":
        file_url = user.profile_picture_thumbnail_url
    else:
        file_url = user.profile_picture_url
    
    if not file_url:
        raise HTTPException(
            status_code=404,
            detail="No profile picture found for this user"
        )
    
    # Construct file path
    file_path = UPLOAD_DIR / file_url
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Profile picture file not found on server"
        )
    
    # Return file
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )


@app.delete(
    "/users/me/profile-picture",
    response_model=MessageResponse,
    tags=["File Upload"],
    summary="Delete Profile Picture",
    description="Delete the authenticated user's profile picture"
)
async def delete_profile_picture(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete profile picture for authenticated user.
    
    **Requirements:**
    - Authentication required (Bearer token)
    
    **Returns:**
    - Success message
    
    **Errors:**
    - 404: No profile picture to delete
    """
    if not current_user.profile_picture_url:
        raise HTTPException(
            status_code=404,
            detail="No profile picture to delete"
        )
    
    try:
        # Delete files from disk
        await delete_user_pictures(current_user)
        
        # Update database
        current_user.profile_picture_url = None
        current_user.profile_picture_thumbnail_url = None
        db.commit()
        
        return MessageResponse(
            message="Profile picture deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting profile picture: {str(e)}"
        )


# OLD TOKEN VERIFICATION - REPLACED BY OAuth2 functions in auth.py
# def verify_token(token:str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         return {
#             "user_id": user_id,
#             "type": payload.get("type")
#         }
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
#
#
# @app.post("/check-token-example/")
# def check_token_example(token:str):
#     user_id = verify_token(token)
#     return {"user_id": user_id, "message": "Token is valid"}
#
#
# async def get_current_user_data_from_token(token: str= Header(...), db: Session= Depends(get_db)):
# OLD TOKEN VERIFICATION - REPLACED BY OAuth2 functions in auth.py
# async def get_current_user_data_from_token(token: str= Header(...), db: Session= Depends(get_db)):
#     user_id = verify_token(token)
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


@app.get("/users/me", response_model=UserResponse, tags=["OAuth2 Authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    This endpoint requires authentication via OAuth2 Bearer token.
    Click the 'Authorize' button in Swagger UI to login first.
    """
    return current_user


@app.put("/users/me", response_model=UserResponse, tags=["OAuth2 Authentication"])
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user's information.
    
    This endpoint requires authentication via OAuth2 Bearer token.
    """
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


# OLD REFRESH TOKEN ENDPOINT - REPLACED BY /refresh (OAuth2 standard)
# @app.get("/refresh-token/")
# def refresh_access_token_old(refresh_token: str, db: Session = Depends(get_db)):
#     user_id = verify_token(refresh_token)["user_id"]
#     token_type = verify_token(refresh_token)["type"]
#     if token_type != "refresh":
#         raise HTTPException(status_code=401, detail="Invalid token type")
#     user = db.query(User).filter(User.id == user_id).first()


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC) ENDPOINTS
# ============================================================================

@app.get("/admin/users", response_model=list[UserResponse], tags=["RBAC - Admin"])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    **Admin-only endpoint** to list all users in the system.
    
    - Requires: Admin role
    - Returns: List of all users with pagination
    
    Regular users will receive 403 Forbidden error.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.delete("/admin/users/{user_id}", tags=["RBAC - Admin"])
async def delete_user_by_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DELETE_USERS))
):
    """
    **Admin-only endpoint** to delete a user account.
    
    - Requires: DELETE_USERS permission (Admin only)
    - Returns: Success message
    
    This is a destructive action and should be logged for audit purposes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted_email = user.email
    db.delete(user)
    db.commit()
    
    # TODO: Log this action for audit trail
    print(f"Admin {current_user.email} deleted user {deleted_email}")
    
    return {"message": f"User {deleted_email} deleted successfully"}


@app.post("/admin/users/{user_id}/activate", tags=["RBAC - Admin"])
async def activate_user_account(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin)
):
    """
    **Manager/Admin endpoint** to activate a user account.
    
    - Requires: Manager or Admin role
    - Returns: Success message
    
    Managers and Admins can activate user accounts.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_active:
        return {"message": f"User {user.email} is already active"}
    
    user.is_active = True
    db.commit()
    
    print(f"{current_user.role.value} {current_user.email} activated user {user.email}")
    
    return {"message": f"User {user.email} activated successfully"}


@app.post("/admin/users/{user_id}/deactivate", tags=["RBAC - Admin"])
async def deactivate_user_account(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin)
):
    """
    **Manager/Admin endpoint** to deactivate a user account.
    
    - Requires: Manager or Admin role
    - Returns: Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    if not user.is_active:
        return {"message": f"User {user.email} is already inactive"}
    
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.email} deactivated successfully"}


@app.put("/admin/users/{user_id}/role", tags=["RBAC - Admin"])
async def change_user_role(
    user_id: uuid.UUID,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    **Admin-only endpoint** to change a user's role.
    
    - Requires: Admin role
    - Returns: Updated user information
    
    Only admins can promote/demote users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    print(f"Admin {current_user.email} changed {user.email}'s role from {old_role.value} to {new_role.value}")
    
    return {
        "message": f"User role updated from {old_role.value} to {new_role.value}",
        "user": UserResponse.from_orm(user)
    }


@app.get("/reports/user-statistics", tags=["RBAC - Reports"])
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """
    **Manager/Admin endpoint** to view user statistics.
    
    - Requires: Manager or Admin role
    - Returns: Statistics about users in the system
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = total_users - active_users
    
    # Count users by role
    role_counts = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        role_counts[role.value] = count
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "users_by_role": role_counts,
        "requested_by": {
            "email": current_user.email,
            "role": current_user.role.value
        }
    }


@app.get("/my-profile", response_model=UserResponse, tags=["RBAC - User"])
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """
    **Authenticated users** can view their own profile.
    
    - Requires: Any authenticated user
    - Returns: Current user's profile information
    """
    return current_user


@app.get("/users/{user_id}/profile", response_model=UserResponse, tags=["RBAC - User"])
async def get_user_profile_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a user's profile with role-based access control.
    
    - **Regular users**: Can only view their own profile
    - **Managers/Admins**: Can view any user's profile
    
    Returns 403 Forbidden if user tries to access another user's profile.
    """
    # Admin and Manager can view any profile
    if current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
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


@app.get("/permissions/check", tags=["RBAC - Permissions"])
async def check_my_permissions(current_user: User = Depends(get_current_active_user)):
    """
    Check what permissions the current user has.
    
    - Requires: Any authenticated user
    - Returns: List of permissions for the user's role
    """
    from auth import ROLE_PERMISSIONS
    
    user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
    
    return {
        "user": {
            "email": current_user.email,
            "role": current_user.role.value
        },
        "permissions": [perm.value for perm in user_permissions],
        "permission_count": len(user_permissions)
    }


@app.post("/admin/create-admin", response_model=UserResponse, tags=["RBAC - Admin"])
async def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    **Admin-only endpoint** to create a new admin user.
    
    - Requires: Admin role
    - Returns: New admin user information
    
    Only existing admins can create new admin accounts.
    This is a sensitive operation that should be logged.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Force admin role regardless of input
    hashed_password = get_password_hash(user_data.password)
    
    new_admin = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        role=UserRole.ADMIN,  # Force admin role
        is_active=True
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    print(f"Admin {current_user.email} created new admin account: {new_admin.email}")
    
    return new_admin

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     new_access_token = create_access_token(data={"sub": str(user.id)})
#
#     return {
#         "access_token": new_access_token,
#         "token_type": "bearer"
#     }

# ============================================================================
# WEBSOCKET IMPLEMENTATION
# ============================================================================

# WebSocket Connection Manager for handling multiple concurrent connections
class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    Supports broadcasting messages to all connected clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_info: dict = {}  # Store client metadata

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept WebSocket connection and add to active connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if client_id:
            self.client_info[id(websocket)] = {
                "client_id": client_id,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
        
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket from active connections"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            # Clean up client info
            ws_id = id(websocket)
            if ws_id in self.client_info:
                del self.client_info[ws_id]
            
            print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

    async def send_personal_json(self, data: dict, websocket: WebSocket):
        """Send JSON message to specific WebSocket connection"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"Error sending personal JSON: {e}")

    async def broadcast(self, message: str, exclude: WebSocket = None):
        """Broadcast text message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            if connection == exclude:
                continue
                
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_json(self, data: dict, exclude: WebSocket = None):
        """Broadcast JSON message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            if connection == exclude:
                continue
                
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"Error broadcasting JSON to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

# Global connection manager instance
ws_manager = ConnectionManager()


@app.get("/websocket-test", response_class=HTMLResponse, tags=["WebSocket"])
async def websocket_test_page():
    """
    Serves an HTML page for testing WebSocket functionality
    Access at: http://localhost:8000/websocket-test
    """
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>FastAPI WebSocket Demo</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .status {
            text-align: center;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.connected {
            background-color: #d4edda;
            color: #155724;
        }
        .status.disconnected {
            background-color: #f8d7da;
            color: #721c24;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="text"], input[type="number"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn-primary {
            background-color: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background-color: #5568d3;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover {
            background-color: #218838;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        #messages {
            height: 400px;
            overflow-y: auto;
            border: 2px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            background-color: #f8f9fa;
            margin-top: 20px;
        }
        .message {
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        .message.sent {
            background-color: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .message.received {
            background-color: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        .message.broadcast {
            background-color: #e7e7ff;
            color: #383874;
            border-left: 4px solid #667eea;
        }
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .timestamp {
            font-size: 11px;
            color: #999;
            margin-left: 10px;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 FastAPI WebSocket Demo</h1>
        <p class="subtitle">Real-time bidirectional communication</p>
        
        <div id="status" class="status disconnected">⭕ Disconnected</div>
        
        <div class="controls">
            <input type="number" id="clientId" placeholder="Enter Client ID" value="1" min="1">
            <button class="btn-success" onclick="connect()">Connect</button>
            <button class="btn-danger" onclick="disconnect()">Disconnect</button>
        </div>
        
        <div class="controls">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button class="btn-primary" onclick="sendMessage()">Send Message</button>
        </div>
        
        <div id="messages"></div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="sentCount">0</div>
                <div class="stat-label">Messages Sent</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="receivedCount">0</div>
                <div class="stat-label">Messages Received</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="connectionTime">0:00</div>
                <div class="stat-label">Connected Time</div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sentCount = 0;
        let receivedCount = 0;
        let connectionStartTime = null;
        let connectionTimer = null;
        
        function connect() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                addMessage('Already connected!', 'error');
                return;
            }
            
            const clientId = document.getElementById('clientId').value;
            if (!clientId) {
                addMessage('Please enter a client ID', 'error');
                return;
            }
            
            ws = new WebSocket(`ws://localhost:8000/ws/echo/${clientId}`);
            
            ws.onopen = function() {
                document.getElementById('status').className = 'status connected';
                document.getElementById('status').textContent = '✅ Connected';
                addMessage(`Connected as Client #${clientId}`, 'info');
                
                connectionStartTime = Date.now();
                startConnectionTimer();
            };
            
            ws.onmessage = function(event) {
                receivedCount++;
                document.getElementById('receivedCount').textContent = receivedCount;
                
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'broadcast') {
                        addMessage(`📢 ${data.message}`, 'broadcast');
                    } else if (data.type === 'echo') {
                        addMessage(`🔄 ${data.message}`, 'received');
                    } else {
                        addMessage(event.data, 'received');
                    }
                } catch {
                    addMessage(`📩 ${event.data}`, 'received');
                }
            };
            
            ws.onclose = function() {
                document.getElementById('status').className = 'status disconnected';
                document.getElementById('status').textContent = '⭕ Disconnected';
                addMessage('Disconnected from server', 'info');
                
                stopConnectionTimer();
                ws = null;
            };
            
            ws.onerror = function(error) {
                addMessage('WebSocket error occurred', 'error');
                console.error('WebSocket error:', error);
            };
        }
        
        function disconnect() {
            if (!ws) {
                addMessage('Not connected', 'error');
                return;
            }
            
            ws.close();
            ws = null;
        }
        
        function sendMessage() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addMessage('Not connected! Click Connect first.', 'error');
                return;
            }
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) {
                addMessage('Please enter a message', 'error');
                return;
            }
            
            ws.send(message);
            addMessage(`📤 You: ${message}`, 'sent');
            
            sentCount++;
            document.getElementById('sentCount').textContent = sentCount;
            
            input.value = '';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function addMessage(message, type = 'info') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const timestamp = new Date().toLocaleTimeString();
            messageDiv.innerHTML = `${message}<span class="timestamp">${timestamp}</span>`;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function startConnectionTimer() {
            connectionTimer = setInterval(() => {
                if (connectionStartTime) {
                    const elapsed = Math.floor((Date.now() - connectionStartTime) / 1000);
                    const minutes = Math.floor(elapsed / 60);
                    const seconds = elapsed % 60;
                    document.getElementById('connectionTime').textContent = 
                        `${minutes}:${seconds.toString().padStart(2, '0')}`;
                }
            }, 1000);
        }
        
        function stopConnectionTimer() {
            if (connectionTimer) {
                clearInterval(connectionTimer);
                connectionTimer = null;
            }
            document.getElementById('connectionTime').textContent = '0:00';
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.websocket("/ws/echo/{client_id}")
async def websocket_echo_endpoint(websocket: WebSocket, client_id: int):
    """
    WebSocket echo endpoint with broadcasting support.
    Echoes back received messages and broadcasts to all clients.
    """
    await ws_manager.connect(websocket, str(client_id))
    
    # Notify all clients about new connection
    await ws_manager.broadcast_json(
        {
            "type": "broadcast",
            "message": f"Client #{client_id} joined the chat"
        },
        exclude=websocket
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            print(f"📨 Received from Client #{client_id}: {data}")
            
            # Send echo response back to sender
            await ws_manager.send_personal_json(
                {
                    "type": "echo",
                    "message": f"Echo: {data}",
                    "client_id": client_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )
            
            # Broadcast to all other clients
            await ws_manager.broadcast_json(
                {
                    "type": "broadcast",
                    "message": f"Client #{client_id}: {data}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exclude=websocket
            )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        
        # Notify all clients about disconnection
        await ws_manager.broadcast_json(
            {
                "type": "broadcast",
                "message": f"Client #{client_id} left the chat"
            }
        )
        
        print(f"👋 Client #{client_id} disconnected")


@app.websocket("/ws/chat/{room_id}/{username}")
async def websocket_chat_room(websocket: WebSocket, room_id: str, username: str):
    """
    WebSocket chat room endpoint with room-based messaging.
    """
    await ws_manager.connect(websocket, f"{room_id}:{username}")
    
    # Send welcome message to user
    await ws_manager.send_personal_json(
        {
            "type": "system",
            "message": f"Welcome to room '{room_id}', {username}!",
            "room": room_id,
            "connected_users": ws_manager.get_connection_count()
        },
        websocket
    )
    
    # Notify room about new user
    await ws_manager.broadcast_json(
        {
            "type": "join",
            "username": username,
            "room": room_id,
            "message": f"{username} joined the room",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        exclude=websocket
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type", "chat")
                content = message_data.get("content", data)
            except json.JSONDecodeError:
                msg_type = "chat"
                content = data
            
            await ws_manager.broadcast_json(
                {
                    "type": msg_type,
                    "username": username,
                    "room": room_id,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await ws_manager.broadcast_json(
            {
                "type": "leave",
                "username": username,
                "room": room_id,
                "message": f"{username} left the room",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        print(f"👋 {username} left room {room_id}")


@app.get("/ws/stats", tags=["WebSocket"])
async def get_websocket_stats():
    """
    Get current WebSocket connection statistics.
    """
    return {
        "active_connections": ws_manager.get_connection_count(),
        "clients": list(ws_manager.client_info.values()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }



# ============================================================================
# AUTHENTICATED WEBSOCKET ENDPOINTS
# ============================================================================

class AuthenticatedConnectionManager:
    """
    Enhanced Connection Manager with authentication support.
    Tracks authenticated users and their associated connections.
    """
    def __init__(self):
        self.active_connections: dict = {}  # {websocket: user_info}
        self.user_connections: dict = {}     # {user_id: [websockets]}
        
    async def connect(self, websocket: WebSocket, user: User):
        """Accept authenticated WebSocket connection"""
        await websocket.accept()
        
        user_info = {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.active_connections[websocket] = user_info
        
        # Track user's multiple connections
        if user.id not in self.user_connections:
            self.user_connections[user.id] = []
        self.user_connections[user.id].append(websocket)
        
        print(f"✅ Authenticated WebSocket: {user.email} (ID: {user.id})")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket from active connections"""
        if websocket in self.active_connections:
            user_info = self.active_connections[websocket]
            user_id = user_info["user_id"]
            
            # Remove from active connections
            del self.active_connections[websocket]
            
            # Remove from user's connections
            if user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)
                
                # Clean up if no more connections for this user
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            print(f"❌ Authenticated WebSocket disconnected: {user_info['email']}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send text message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def send_personal_json(self, data: dict, websocket: WebSocket):
        """Send JSON message to specific WebSocket"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"Error sending JSON: {e}")
    
    async def send_to_user(self, user_id: int, data: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            disconnected = []
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast(self, message: str, exclude: WebSocket = None):
        """Broadcast text message to all authenticated connections"""
        disconnected = []
        for websocket in self.active_connections:
            if websocket == exclude:
                continue
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Broadcast error: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_json(self, data: dict, exclude: WebSocket = None):
        """Broadcast JSON message to all authenticated connections"""
        disconnected = []
        for websocket in self.active_connections:
            if websocket == exclude:
                continue
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Broadcast JSON error: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_to_role(self, role: UserRole, data: dict):
        """Broadcast message to all users with specific role"""
        disconnected = []
        for websocket, user_info in self.active_connections.items():
            if user_info["role"] == role.value:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"Error broadcasting to role {role.value}: {e}")
                    disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_user_info(self, websocket: WebSocket) -> dict:
        """Get user info for a specific WebSocket"""
        return self.active_connections.get(websocket)
    
    def get_connection_count(self) -> int:
        """Get total number of authenticated connections"""
        return len(self.active_connections)
    
    def get_online_users(self) -> List[dict]:
        """Get list of all online users"""
        online_users = {}
        for user_info in self.active_connections.values():
            user_id = user_info["user_id"]
            if user_id not in online_users:
                online_users[user_id] = {
                    "user_id": user_id,
                    "email": user_info["email"],
                    "full_name": user_info["full_name"],
                    "role": user_info["role"],
                    "connection_count": 0
                }
            online_users[user_id]["connection_count"] += 1
        
        return list(online_users.values())

# Global authenticated connection manager
auth_ws_manager = AuthenticatedConnectionManager()


async def verify_websocket_token(token: str, db: Session) -> User:
    """
    Verify JWT token and return authenticated user.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        from auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        print("user_id from token:", user_id)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = db.query(User).filter(User.id == user_id).first()        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@app.websocket("/ws/secure/echo/{client_id}")
async def authenticated_echo_endpoint(websocket: WebSocket, client_id: str, db: Session = Depends(get_db)):
    """
    Authenticated WebSocket echo endpoint.
    
    **Authentication:**
    - Requires valid JWT token in query parameter 'token'
    - Example: ws://localhost:8000/ws/secure/echo/1?token=YOUR_JWT_TOKEN
    
    **Features:**
    - Token validation before connection
    - User identification
    - Personalized echo responses
    - Broadcast user activity to other authenticated users
    
    **Usage:**
    1. Get access token from /token endpoint
    2. Connect: ws://localhost:8000/ws/secure/echo/{id}?token={your_token}
    3. Send messages
    4. Receive echoes with user context
    """
    # Extract and verify token
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return
    
    # Connect authenticated user
    await auth_ws_manager.connect(websocket, user)
    
    # Send welcome message
    await auth_ws_manager.send_personal_json(
        {
            "type": "welcome",
            "message": f"Welcome {user.full_name}!",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )
    
    # Broadcast user joined
    await auth_ws_manager.broadcast_json(
        {
            "type": "user_joined",
            "message": f"{user.full_name} joined the chat",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        exclude=websocket
    )
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            print(f"📨 {user.full_name} ({user.email}): {data}")
            
            # Send personal echo
            await auth_ws_manager.send_personal_json(
                {
                    "type": "echo",
                    "message": f"Echo: {data}",
                    "original": data,
                    "from": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )
            
            # Broadcast to others
            await auth_ws_manager.broadcast_json(
                {
                    "type": "message",
                    "content": data,
                    "from": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role.value
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                exclude=websocket
            )
    
    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
        
        # Broadcast user left
        await auth_ws_manager.broadcast_json(
            {
                "type": "user_left",
                "message": f"{user.full_name} left the chat",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@app.websocket("/ws/secure/chat/{room_id}")
async def authenticated_chat_room(
    websocket: WebSocket,
    room_id: str,
    db: Session = Depends(get_db)
):
    """
    Authenticated chat room endpoint.
    
    **Authentication:**
    - Requires valid JWT token in query parameter
    - Example: ws://localhost:8000/ws/secure/chat/general?token=YOUR_JWT_TOKEN
    
    **Features:**
    - Secure room-based messaging
    - User identification and verification
    - Role-based features (admin announcements)
    - Private messaging support
    - Online user list
    
    **Message Types:**
    - chat: Regular chat message
    - private: Private message to specific user
    - announcement: Admin-only broadcast (requires admin role)
    - typing: Typing indicator
    """
    # Extract and verify token
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return
    
    # Connect user
    await auth_ws_manager.connect(websocket, user)
    
    # Send welcome with room info
    await auth_ws_manager.send_personal_json(
        {
            "type": "room_joined",
            "message": f"Welcome to {room_id}",
            "room": room_id,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "online_users": auth_ws_manager.get_online_users(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )
    
    # Notify others
    await auth_ws_manager.broadcast_json(
        {
            "type": "user_joined_room",
            "room": room_id,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "message": f"{user.full_name} joined {room_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        exclude=websocket
    )
    
    # rooms = {

    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type", "chat")
                content = message_data.get("content", data)
                target_user_id = message_data.get("target_user_id")
            except json.JSONDecodeError:
                msg_type = "chat"
                content = data
                target_user_id = None
            
            # Handle different message types
            if msg_type == "private" and target_user_id:
                # Private message to specific user
                await auth_ws_manager.send_to_user(
                    target_user_id,
                    {
                        "type": "private_message",
                        "content": content,
                        "from": {
                            "id": user.id,
                            "full_name": user.full_name
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                # Confirm to sender
                await auth_ws_manager.send_personal_json(
                    {
                        "type": "private_sent",
                        "content": content,
                        "to_user_id": target_user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    websocket
                )
            
            elif msg_type == "announcement":
                # Admin-only announcements
                if user.role == UserRole.ADMIN:
                    await auth_ws_manager.broadcast_json(
                        {
                            "type": "announcement",
                            "content": content,
                            "from": {
                                "id": user.id,
                                "full_name": user.full_name,
                                "role": user.role.value
                            },
                            "room": room_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                else:
                    await auth_ws_manager.send_personal_json(
                        {
                            "type": "error",
                            "message": "Only admins can send announcements",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        },
                        websocket
                    )
            
            elif msg_type == "typing":
                # Typing indicator
                await auth_ws_manager.broadcast_json(
                    {
                        "type": "user_typing",
                        "room": room_id,
                        "user": {
                            "id": user.id,
                            "full_name": user.full_name
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    exclude=websocket
                )
            
            else:
                # Regular chat message
                await auth_ws_manager.broadcast_json(
                    {
                        "type": "chat",
                        "content": content,
                        "room": room_id,
                        "from": {
                            "id": user.id,
                            "email": user.email,
                            "full_name": user.full_name,
                            "role": user.role.value
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
    
    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
        
        # Notify others
        await auth_ws_manager.broadcast_json(
            {
                "type": "user_left_room",
                "room": room_id,
                "user": {
                    "id": user.id,
                    "full_name": user.full_name
                },
                "message": f"{user.full_name} left {room_id}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@app.websocket("/ws/secure/notifications")
async def authenticated_notifications(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    Personal notification stream for authenticated users.
    
    **Authentication:**
    - Requires valid JWT token
    - Example: ws://localhost:8000/ws/secure/notifications?token=YOUR_JWT_TOKEN
    
    **Features:**
    - Real-time personal notifications
    - System messages
    - User-specific updates
    - Role-based notifications
    
    **Use Cases:**
    - New message alerts
    - Task assignments
    - System announcements
    - Status updates
    """
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    try:
        user = await verify_websocket_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        return
    
    await auth_ws_manager.connect(websocket, user)
    
    # Send connection confirmation
    await auth_ws_manager.send_personal_json(
        {
            "type": "notification_stream_connected",
            "message": "Connected to notification stream",
            "user_id": user.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        websocket
    )
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Echo acknowledgment
            await auth_ws_manager.send_personal_json(
                {
                    "type": "ack",
                    "message": "Notification stream active",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )
    
    except WebSocketDisconnect:
        auth_ws_manager.disconnect(websocket)
        print(f"Notification stream disconnected: {user.email}")


@app.get("/ws/secure/stats", tags=["Authenticated WebSocket"])
async def get_authenticated_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get authenticated WebSocket connection statistics.
    
    **Authentication Required:** Yes (Bearer token)
    
    **Returns:**
    - Total authenticated connections
    - Online users list
    - User's own connections
    - Connection details
    """
    user_info = auth_ws_manager.get_online_users()
    
    # Find current user's connections
    user_connections = 0
    if current_user.id in auth_ws_manager.user_connections:
        user_connections = len(auth_ws_manager.user_connections[current_user.id])
    
    return {
        "total_connections": auth_ws_manager.get_connection_count(),
        "unique_users": len(auth_ws_manager.user_connections),
        "online_users": user_info,
        "your_connections": user_connections,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/ws/secure/send-notification/{user_id}", tags=["Authenticated WebSocket"])
async def send_notification_to_user(
    user_id: int,
    notification: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Send notification to specific user (Admin only).
    
    **Authentication Required:** Yes (Admin role)
    
    **Parameters:**
    - user_id: Target user ID
    - notification: Notification data (type, message, etc.)
    
    **Example Request:**
    ```json
    {
        "type": "alert",
        "message": "Your task has been updated",
        "priority": "high"
    }
    ```
    """
    # Verify target user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add metadata
    notification_data = {
        **notification,
        "from_admin": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Send to user
    await auth_ws_manager.send_to_user(user_id, notification_data)
    
    return {
        "status": "sent",
        "target_user_id": user_id,
        "notification": notification_data
    }


@app.post("/ws/secure/broadcast", tags=["Authenticated WebSocket"])
async def broadcast_message(
    message: dict,
    current_user: User = Depends(require_admin)
):
    """
    Broadcast message to all authenticated WebSocket connections (Admin only).
    
    **Authentication Required:** Yes (Admin role)
    
    **Example Request:**
    ```json
    {
        "type": "system_announcement",
        "message": "Server maintenance in 10 minutes",
        "priority": "high"
    }
    ```
    """
    broadcast_data = {
        **message,
        "from_admin": {
            "id": current_user.id,
            "full_name": current_user.full_name
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await auth_ws_manager.broadcast_json(broadcast_data)
    
    return {
        "status": "broadcast_sent",
        "recipients": auth_ws_manager.get_connection_count(),
        "message": broadcast_data
    }


# HTML test page for authenticated WebSockets
authenticated_websocket_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Authenticated WebSocket Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 {
            color: #1e3c72;
            margin-bottom: 10px;
        }
        .auth-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
        .status.authenticated { background: #d1ecf1; color: #0c5460; }
        input, button, select {
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        button {
            background: #1e3c72;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background: #2a5298; }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        #messages {
            height: 400px;
            overflow-y: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
            margin: 20px 0;
        }
        .message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .message.welcome { background: #d1ecf1; border-color: #17a2b8; }
        .message.echo { background: #d4edda; border-color: #28a745; }
        .message.user_joined { background: #fff3cd; border-color: #ffc107; }
        .message.user_left { background: #f8d7da; border-color: #dc3545; }
        .message.chat { background: #e7e7ff; border-color: #6c757d; }
        .message.announcement { background: #ffe5e5; border-color: #ff0000; font-weight: bold; }
        .user-info {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Authenticated WebSocket Test</h1>
        <p>Test secure WebSocket connections with JWT authentication</p>
        
        <!-- Authentication Section -->
        <div class="auth-section">
            <h3>Step 1: Authenticate</h3>
            <input type="email" id="email" placeholder="Email" value="admin@example.com">
            <input type="password" id="password" placeholder="Password" value="admin123">
            <button onclick="login()">Login & Get Token</button>
            <div id="authStatus" class="status disconnected">Not authenticated</div>
            <div id="userInfo" class="user-info" style="display:none;"></div>
        </div>
        
        <!-- Connection Section -->
        <div class="auth-section">
            <h3>Step 2: Connect to WebSocket</h3>
            <select id="endpoint">
                <option value="echo">Secure Echo</option>
                <option value="chat">Secure Chat Room</option>
                <option value="notifications">Notification Stream</option>
            </select>
            <input type="text" id="clientId" placeholder="Client ID / Room" value="general">
            <button onclick="connect()" id="connectBtn" disabled>Connect</button>
            <button onclick="disconnect()" id="disconnectBtn" disabled>Disconnect</button>
            <div id="wsStatus" class="status disconnected">Not connected</div>
        </div>
        
        <!-- Messaging Section -->
        <div class="grid">
            <div>
                <h3>Send Message</h3>
                <select id="messageType">
                    <option value="chat">Chat</option>
                    <option value="announcement">Announcement (Admin)</option>
                    <option value="typing">Typing Indicator</option>
                </select>
                <input type="text" id="messageInput" placeholder="Type message..." style="width:80%">
                <button onclick="sendMessage()" id="sendBtn" disabled>Send</button>
            </div>
            <div>
                <h3>Online Users</h3>
                <div id="onlineUsers" style="background:#f8f9fa; padding:10px; border-radius:5px; min-height:50px;">
                    No users online
                </div>
            </div>
        </div>
        
        <!-- Messages Display -->
        <div id="messages"></div>
        
        <!-- Stats -->
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin-top:20px;">
            <div style="background:#f8f9fa; padding:15px; border-radius:8px; text-align:center;">
                <div style="font-size:24px; font-weight:bold; color:#1e3c72;" id="sentCount">0</div>
                <div style="font-size:12px; color:#666;">Sent</div>
            </div>
            <div style="background:#f8f9fa; padding:15px; border-radius:8px; text-align:center;">
                <div style="font-size:24px; font-weight:bold; color:#1e3c72;" id="receivedCount">0</div>
                <div style="font-size:12px; color:#666;">Received</div>
            </div>
            <div style="background:#f8f9fa; padding:15px; border-radius:8px; text-align:center;">
                <div style="font-size:24px; font-weight:bold; color:#1e3c72;" id="connectionTime">0:00</div>
                <div style="font-size:12px; color:#666;">Connected</div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let accessToken = null;
        let currentUser = null;
        let sentCount = 0;
        let receivedCount = 0;
        let connectionStartTime = null;
        let connectionTimer = null;
        
        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);
                
                const response = await fetch('/token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    accessToken = data.access_token;
                    
                    // Get user info
                    const userResponse = await fetch('/users/me', {
                        headers: {'Authorization': `Bearer ${accessToken}`}
                    });
                    currentUser = await userResponse.json();
                    
                    document.getElementById('authStatus').className = 'status authenticated';
                    document.getElementById('authStatus').textContent = '✅ Authenticated';
                    
                    document.getElementById('userInfo').style.display = 'block';
                    document.getElementById('userInfo').innerHTML = `
                        <strong>Logged in as:</strong> ${currentUser.full_name}<br>
                        <strong>Email:</strong> ${currentUser.email}<br>
                        <strong>Role:</strong> ${currentUser.role}
                    `;
                    
                    document.getElementById('connectBtn').disabled = false;
                    addMessage('✅ Authentication successful!', 'welcome');
                } else {
                    addMessage('❌ Login failed. Check credentials.', 'user_left');
                }
            } catch (error) {
                addMessage('❌ Error: ' + error.message, 'user_left');
            }
        }
        
        function connect() {
            if (!accessToken) {
                addMessage('Please login first!', 'user_left');
                return;
            }
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                addMessage('Already connected!', 'user_left');
                return;
            }
            
            const endpoint = document.getElementById('endpoint').value;
            const clientId = document.getElementById('clientId').value;
            
            let wsUrl;
            if (endpoint === 'echo') {
                wsUrl = `ws://localhost:8000/ws/secure/echo/${clientId}?token=${accessToken}`;
            } else if (endpoint === 'chat') {
                wsUrl = `ws://localhost:8000/ws/secure/chat/${clientId}?token=${accessToken}`;
            } else {
                wsUrl = `ws://localhost:8000/ws/secure/notifications?token=${accessToken}`;
            }
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                document.getElementById('wsStatus').className = 'status connected';
                document.getElementById('wsStatus').textContent = '✅ WebSocket Connected';
                document.getElementById('sendBtn').disabled = false;
                document.getElementById('disconnectBtn').disabled = false;
                document.getElementById('connectBtn').disabled = true;
                connectionStartTime = Date.now();
                startConnectionTimer();
            };
            
            ws.onmessage = (event) => {
                receivedCount++;
                document.getElementById('receivedCount').textContent = receivedCount;
                
                const data = JSON.parse(event.data);
                
                let messageClass = data.type || 'chat';
                let messageText = '';
                
                if (data.type === 'welcome' || data.type === 'room_joined') {
                    messageText = `🎉 ${data.message}`;
                    if (data.online_users) {
                        updateOnlineUsers(data.online_users);
                    }
                } else if (data.type === 'echo') {
                    messageText = `🔄 ${data.message}`;
                } else if (data.type === 'user_joined' || data.type === 'user_joined_room') {
                    messageText = `👋 ${data.message}`;
                } else if (data.type === 'user_left' || data.type === 'user_left_room') {
                    messageText = `👋 ${data.message}`;
                } else if (data.type === 'chat' || data.type === 'message') {
                    messageText = `💬 ${data.from?.full_name}: ${data.content}`;
                } else if (data.type === 'announcement') {
                    messageText = `📢 ANNOUNCEMENT: ${data.content}`;
                } else if (data.type === 'user_typing') {
                    messageText = `⌨️  ${data.user.full_name} is typing...`;
                } else {
                    messageText = JSON.stringify(data, null, 2);
                }
                
                addMessage(messageText, messageClass);
            };
            
            ws.onclose = () => {
                document.getElementById('wsStatus').className = 'status disconnected';
                document.getElementById('wsStatus').textContent = '⭕ Disconnected';
                document.getElementById('sendBtn').disabled = true;
                document.getElementById('disconnectBtn').disabled = true;
                document.getElementById('connectBtn').disabled = false;
                stopConnectionTimer();
                ws = null;
            };
            
            ws.onerror = (error) => {
                addMessage('❌ WebSocket error', 'user_left');
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
            }
        }
        
        function sendMessage() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addMessage('Not connected!', 'user_left');
                return;
            }
            
            const messageInput = document.getElementById('messageInput');
            const messageType = document.getElementById('messageType').value;
            const message = messageInput.value.trim();
            
            if (!message && messageType !== 'typing') {
                return;
            }
            
            const data = {
                type: messageType,
                content: message
            };
            
            ws.send(JSON.stringify(data));
            
            if (messageType !== 'typing') {
                addMessage(`📤 You: ${message}`, 'echo');
                sentCount++;
                document.getElementById('sentCount').textContent = sentCount;
                messageInput.value = '';
            }
        }
        
        function addMessage(text, className) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.innerHTML = `${text} <small style="color:#999;">${new Date().toLocaleTimeString()}</small>`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateOnlineUsers(users) {
            const onlineDiv = document.getElementById('onlineUsers');
            if (users && users.length > 0) {
                onlineDiv.innerHTML = users.map(u => 
                    `<div style="padding:5px; border-bottom:1px solid #ddd;">
                        👤 ${u.full_name} (${u.role})
                    </div>`
                ).join('');
            } else {
                onlineDiv.innerHTML = 'No users online';
            }
        }
        
        function startConnectionTimer() {
            connectionTimer = setInterval(() => {
                if (connectionStartTime) {
                    const elapsed = Math.floor((Date.now() - connectionStartTime) / 1000);
                    const minutes = Math.floor(elapsed / 60);
                    const seconds = elapsed % 60;
                    document.getElementById('connectionTime').textContent = 
                        `${minutes}:${seconds.toString().padStart(2, '0')}`;
                }
            }, 1000);
        }
        
        function stopConnectionTimer() {
            if (connectionTimer) {
                clearInterval(connectionTimer);
                connectionTimer = null;
            }
            document.getElementById('connectionTime').textContent = '0:00';
        }
        
        // Allow Enter key to send
        document.getElementById('messageInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""


@app.get("/authenticated-websocket-test", response_class=HTMLResponse, tags=["Authenticated WebSocket"])
async def authenticated_websocket_test_page():
    """
    HTML test page for authenticated WebSocket functionality.
    
    **Features:**
    - Login with credentials
    - Get JWT token automatically
    - Connect to authenticated WebSocket endpoints
    - Test echo, chat, and notification streams
    - See online users
    - Send different message types
    
    **Access:** http://localhost:8000/authenticated-websocket-test
    
    **Default credentials:**
    - Email: admin@example.com
    - Password: admin123
    """
    return HTMLResponse(content=authenticated_websocket_html, status_code=200)


# ============================================================================
# REDIS CACHING ENDPOINTS
# ============================================================================

@app.get("/users-cached", response_model=list[UserResponse], tags=["Caching - Users"])
async def list_users_cached(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
) -> list[UserResponse]:
    """
    List users with Redis caching (Cache-Aside pattern)
    
    - **Cache key:** users:list:{skip}:{limit}
    - **Cache duration:** 30 minutes
    - **First request:** Queries database (~100ms)
    - **Subsequent requests:** Redis cache (~1ms)
    """
    cache_key = f"users:list:{skip}:{limit}"
    
    # Try cache first
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            await CacheMetrics(redis).record_hit(cache_key)
            return [UserResponse(**u) for u in json.loads(cached)]
        await CacheMetrics(redis).record_miss(cache_key)
    
    # Cache miss - query database
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Store in cache
    if redis and users:
        await redis.set(
            cache_key,
            [u.to_dict() for u in users],
            ex=1800  # 30 minutes
        )
    
    return users


@app.get("/users-cached/{user_id}", response_model=UserResponse, tags=["Caching - Users"])
async def get_user_cached(
    user_id: str,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
) -> UserResponse:
    """
    Get single user with Redis caching (Cache-Aside pattern)
    
    - **Cache key:** user:{user_id}
    - **Cache duration:** 1 hour
    - **First request:** Queries database (~100ms)
    - **Subsequent requests:** Redis cache (~1ms)
    """
    cache_key = f"user:{user_id}"
    
    # Try cache first
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            await CacheMetrics(redis).record_hit(cache_key)
            return UserResponse(**json.loads(cached))
        await CacheMetrics(redis).record_miss(cache_key)
    
    # Cache miss - query database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store in cache
    if redis:
        await redis.set(
            cache_key,
            user.to_dict(),
            ex=3600  # 1 hour
        )
    
    return user


@app.put("/users-cached/{user_id}", response_model=UserResponse, tags=["Caching - Users"])
async def update_user_cached(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
) -> UserResponse:
    """
    Update user and invalidate cache (Write-Through pattern)
    
    - Updates database
    - Invalidates all related cache entries
    - Returns fresh data from database
    
    **Cache invalidation:**
    - Deletes: user:{user_id}
    - Deletes: users:list:*
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update database
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Invalidate cache
    if redis:
        await redis.delete(f"user:{user_id}")
        deleted = await redis.delete_pattern("users:list:*")
        print(f"🗑️  Invalidated {deleted} cache entries for user {user_id}")
    
    return user


@app.post("/admin/cache/warm", tags=["Admin - Caching"])
async def warm_cache(
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Warm cache with all active users (Admin only)
    
    Pre-populate Redis with frequently accessed user data
    for better performance on subsequent requests.
    
    **Requirements:**
    - Admin role required
    
    **Behavior:**
    - Caches all active users
    - Sets 1-hour TTL
    - Returns count of users cached
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    # Fetch all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    # Cache each user
    for user in users:
        await redis.set(
            f"user:{user.id}",
            user.to_dict(),
            ex=3600  # 1 hour
        )
    
    return {
        "message": f"✅ Cached {len(users)} active users",
        "count": len(users),
        "ttl_seconds": 3600
    }


@app.get("/admin/cache/stats", tags=["Admin - Caching"])
async def get_cache_stats(
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Get cache performance statistics (Admin only)
    
    Shows cache hit/miss ratios and memory usage
    
    **Returns:**
    - hits: Number of cache hits
    - misses: Number of cache misses
    - total_requests: Total cache requests
    - hit_ratio_percent: Cache hit percentage
    - memory_usage_mb: Current Redis memory usage
    - max_memory_mb: Max allowed Redis memory
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    metrics = CacheMetrics(redis)
    stats = await metrics.get_stats()
    
    # Get Redis memory info
    info = await redis.info("memory")
    
    return {
        **stats,
        "memory_usage_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
        "max_memory_mb": round(info.get("maxmemory", 0) / 1024 / 1024, 2) if info.get("maxmemory") else "unlimited"
    }


@app.post("/admin/cache/clear", tags=["Admin - Caching"])
async def clear_cache_entries(
    pattern: str = "*",
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Clear cache entries matching pattern (Admin only)
    
    Example patterns:
    - "*" - Clear all cache
    - "user:*" - Clear all user caches
    - "users:list:*" - Clear all user list caches
    
    **Caution:** Clearing all cache (*) will impact performance!
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    deleted = await redis.delete_pattern(pattern)
    
    return {
        "message": f"✅ Deleted {deleted} cache entries",
        "pattern": pattern,
        "deleted_count": deleted
    }


@app.post("/admin/cache/metrics/reset", tags=["Admin - Caching"])
async def reset_cache_metrics(
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """Reset cache hit/miss metrics (Admin only)"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    metrics = CacheMetrics(redis)
    await metrics.reset()
    
    return {"message": "✅ Cache metrics reset"}


# ============================================================================
# REDIS SESSION STORAGE ENDPOINTS
# ============================================================================

@app.post("/auth/login-with-session", tags=["Sessions - Redis"])
async def login_with_session(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    request: Request = None
):
    """
    Login and create Redis-based session
    
    Returns a session_id to be used in subsequent requests
    instead of JWT tokens.
    
    **Session Features:**
    - Stored in Redis (fast, in-memory)
    - 24-hour expiration (configurable)
    - IP address and user-agent tracked
    - Support for multiple concurrent sessions
    
    **Returns:**
    - session_id: Use in header for authenticated requests
    - expires_in_seconds: Session TTL
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    # Authenticate user
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    manager = SessionManager(redis)
    
    session_data = {
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None,
    }
    
    session_id = await manager.create_session(str(user.id), session_data)
    
    return {
        "session_id": session_id,
        "user_id": str(user.id),
        "user_email": user.email,
        "expires_in_seconds": 86400,
        "message": "✅ Session created successfully"
    }


@app.get("/auth/session-info", tags=["Sessions - Redis"])
async def get_session_info(
    session_id: str = Header(...),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """
    Get current session information
    
    **Parameters:**
    - session_id: Provide in header
    
    **Returns:**
    - Complete session data including user_id, creation time, last activity
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    session = await manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Update activity (extends TTL)
    await manager.update_activity(session_id)
    
    return session


@app.post("/auth/logout-session", tags=["Sessions - Redis"])
async def logout_session(
    session_id: str = Header(...),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """
    Logout and destroy session
    
    **Parameters:**
    - session_id: Provide in header
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    if await manager.destroy_session(session_id):
        return {"message": "✅ Logged out successfully"}
    
    raise HTTPException(status_code=404, detail="Session not found")


@app.post("/auth/logout-everywhere", tags=["Sessions - Redis"])
async def logout_everywhere(
    current_user: User = Depends(get_current_active_user),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """
    Logout from all devices (destroy all sessions)
    
    Logs out user from every device/session simultaneously.
    Useful for security when password is compromised.
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    destroyed = await manager.destroy_all_user_sessions(str(current_user.id))
    
    return {
        "message": f"✅ Logged out from {destroyed} session(s)",
        "sessions_destroyed": destroyed
    }



# ============================================================================
# END AUTHENTICATED WEBSOCKET IMPLEMENTATION
# ============================================================================