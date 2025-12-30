from pydantic import BaseModel, ConfigDict
from typing import Union, Optional, List, Dict


class RawMaterial(BaseModel):
    id: int
    name: str
    quantity: float




class ProductValidation(BaseModel):
    id: int 
    name: str
    description: Optional[str] = None
    price: float 
    product_raw_materials: List[RawMaterial] = []
    metadata: Optional[Dict[str, Union[str, int, bool] ]] = None
    model_config = ConfigDict(extra="forbid", strict=True)


def vaildate_product(data):
    try:
        product = ProductValidation(**data)
        return product
    except Exception as e:
        print(f"Validation error: {e}")
        return None
    

if __name__ == "__main__":
    sample_data = {
        "id": 1,
        "name": "Sample Product",
        "description": "This is a sample product.",
        "price": 99.99,
        "product_raw_materials": [
            {
                "id": 1,
                "name": "Copper",
                "quantity": 5.0

            },
            {
                "id":2,
                "name": "Plastic",
                "quantity": 2.5
            }
          
        ],
        "metadata":{
            "catefory": "Electronics",
            "warranty_years": 2,
            "is_returnable": True,
            "carbon_neutral": False,
            "tags": ["gadget", "tech"]

        }
    }

    validated_product = vaildate_product(sample_data)
    print(validated_product)