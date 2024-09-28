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
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()
        num_green_ml = result[0]

        potions_to_make = num_green_ml // 100
        if potions_to_make > 0:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - :used_ml, num_green_potions = num_green_potions + :new_potions"),
                               {"used_ml": potions_to_make * 100, "new_potions": potions_to_make})
            return [{"potion_type": [0, 100, 0, 0], "quantity": potions_to_make}]

    return []

if __name__ == "__main__":
    print(get_bottle_plan())