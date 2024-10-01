from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """handle potion delivery"""
    total_bottles = sum(potion.quantity for potion in potions_delivered)  # sum quantities
    total_green_ml = sum(potion.potion_type[1] * potion.quantity for potion in potions_delivered)  # sum green ml
    
    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                f"update global_inventory \
                set num_green_potions = num_green_potions + {total_bottles}, \
                num_green_ml = num_green_ml - {total_green_ml}"
            )
        )
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    return "ok"

@router.post("/plan")
def get_bottle_plan():
    """plan potion bottling"""
    # each bottle needs 100 ml of potion
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text("select num_green_ml from global_inventory")
        )
        green_ml = res.first().num_green_ml  # fetch green ml
    
    mixable_potions = green_ml // 100  # calculate mixable potions
    if mixable_potions > 0:
        return [{
            "potion_type": [0, 100, 0, 0],  # potion details
            "quantity": mixable_potions,  # mixable potion count
        }]
    return []

if __name__ == "__main__":
    print(get_bottle_plan())
