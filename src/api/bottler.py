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
def post_deliver_potions(potions_delivered: list[PotionInventory], order_id: int):
    """handle potion delivery"""
    with db.engine.begin() as conn:
        for potion in potions_delivered:
            if potion.potion_type == [100, 0, 0, 0]:  # Red potion
                conn.execute(sqlalchemy.text(
                    "UPDATE global_inventory SET num_red_potions = num_red_potions + :quantity"
                ), {"quantity": potion.quantity})
            elif potion.potion_type == [0, 100, 0, 0]:  # Green potion
                conn.execute(sqlalchemy.text(
                    "UPDATE global_inventory SET num_green_potions = num_green_potions + :quantity"
                ), {"quantity": potion.quantity})
            elif potion.potion_type == [0, 0, 100, 0]:  # Blue potion
                conn.execute(sqlalchemy.text(
                    "UPDATE global_inventory SET num_blue_potions = num_blue_potions + :quantity"
                ), {"quantity": potion.quantity})

    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """plan potion bottling"""
    with db.engine.begin() as conn:
        res = conn.execute(sqlalchemy.text(
            "SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"
        ))
        inventory = res.first()

    bottle_plan = []

    # Red potions
    red_potions = inventory.num_red_ml // 100
    if red_potions > 0:
        bottle_plan.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": red_potions,
        })

    # Green potions
    green_potions = inventory.num_green_ml // 100
    if green_potions > 0:
        bottle_plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": green_potions,
        })

    # Blue potions
    blue_potions = inventory.num_blue_ml // 100
    if blue_potions > 0:
        bottle_plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": blue_potions,
        })

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
