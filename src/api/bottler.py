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
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            color = "red" if potion.potion_type == [100, 0, 0, 0] else "green" if potion.potion_type == [0, 100, 0, 0] else "blue"
            sql = f"""
            UPDATE global_inventory
            SET num_{color}_potions = num_{color}_potions + :quantity,
                num_{color}_ml = num_{color}_ml - :ml_used
            """
            connection.execute(sqlalchemy.text(sql), {"quantity": potion.quantity, "ml_used": potion.quantity * 100})
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT num_red_ml, num_green_ml, num_blue_ml
            FROM global_inventory
        """)).fetchone()
        
        red_ml, green_ml, blue_ml = result

    bottle_plan = []
    
    # create red potions
    red_potions = min(red_ml // 100, 5)  # max 5 potions per color
    if red_potions > 0:
        bottle_plan.append({"potion_type": [100, 0, 0, 0], "quantity": red_potions})
    
    # create green potions
    green_potions = min(green_ml // 100, 5)  # max 5 potions per color
    if green_potions > 0:
        bottle_plan.append({"potion_type": [0, 100, 0, 0], "quantity": green_potions})
    
    # create blue potions
    blue_potions = min(blue_ml // 100, 5)  # max 5 potions per color
    if blue_potions > 0:
        bottle_plan.append({"potion_type": [0, 0, 100, 0], "quantity": blue_potions})

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
