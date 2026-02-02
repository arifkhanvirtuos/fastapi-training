from jose import jwt
from datetime import timedelta, datetime, timezone
from typing import Union, Optional

SECRET_KEY = "test-scret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES= 30


def create_access_token(data: dict, expires_data: Optional[timedelta]= None):

    to_encode = data.copy()
    if expires_data:
        expire = datetime.now(timezone.utc)+ expires_data
    else: 
        expire = datetime.now(timezone.utc)+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})


    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


    return encoded_jwt



token_data = {
    "sub": "user123"
}

print(create_access_token(token_data))