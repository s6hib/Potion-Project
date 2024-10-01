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
    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:  # Green potion
            with db.engine.begin() as connection:
                # update green potion inventory
                connection.execute(
                    sqlalchemy.text(
                        "UPDATE global_inventory SET num_green_potions = num_green_potions + :quantity"
                    ),
                    {"quantity": potion.quantity}
                )
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        # get current green ml
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        green_ml = result.fetchone().num_green_ml
    
    # calculate how many potions can be made, ensuring at least 100 ml is available
    potions_to_make = green_ml // 100
    if potions_to_make > 0:
        ml_to_use = potions_to_make * 100
        with db.engine.begin() as connection:
            # deduct used green ml
            connection.execute(
                sqlalchemy.text(
                    "UPDATE global_inventory SET num_green_ml = num_green_ml - :used_ml"
                ),
                {"used_ml": ml_to_use}
            )
        return [{"potion_type": [0, 100, 0, 0], "quantity": potions_to_make}]
    return []

if __name__ == "__main__":
    print(get_bottle_plan())