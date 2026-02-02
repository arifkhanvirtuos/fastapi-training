from typing import Union, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse
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
from jose import jwt
from datetime import timedelta, datetime, timezone

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
    MessageResponse
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
    print("Starting up...")
    print("Running database migrations...")
    try:
        run_migrations()
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
        # Optionally, you can still start the app or raise the exception
        # raise e
    yield
    # Shutdown code
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])





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




class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Union[str, None] = None
    phone_number: Union[str, None] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Union[str, None] = None
    phone_number: Union[str, None] = None
    is_active: bool

    class Config:
        from_attributes = True  

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