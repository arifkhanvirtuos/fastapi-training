from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserValidation(BaseModel):
    id: int
    name: str 
    age: int
    height: Optional[float] = None
    model_config = ConfigDict(extra="forbid", strict=True)



    


def validate_user(data):
    try:
        user = UserValidation(**data)
        return user
    except Exception as e:
        print(f"Validation error: {e}")
        return None


if __name__ == "__main__":
    sample_data = {
        "id": 1,
        "height": 8.1,
        
        "name": "John Doe",
        "age": 30,
    }

    validated_user = validate_user(sample_data)
    print(validated_user)