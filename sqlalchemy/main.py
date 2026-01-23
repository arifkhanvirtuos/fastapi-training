from typing import Union
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import get_db, init_db
from pydantic import BaseModel
from alembic.config import Config
from alembic import command
from fastapi.middleware.cors import CORSMiddleware
import os


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

def run_migrations():
    """Run Alembic migrations automatically"""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code
#     print("Starting up...")
#     print("Running database migrations...")
#     try:
#         run_migrations()
#         print("Migrations completed successfully!")
#     except Exception as e:
#         print(f"Migration error: {e}")
#         # Optionally, you can still start the app or raise the exception
#         # raise e
#     yield
#     # Shutdown code
#     print("Shutting down...")

app = FastAPI()






@app.get("/")
def read_root():
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