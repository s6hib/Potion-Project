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
    # initialize totals for each potion type
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_green_bottles = 0
    total_red_bottles = 0
    total_blue_bottles = 0

    # process each delivered potion
    for potion in potions_delivered:
        quantity = potion.quantity
        potion_type = potion.potion_type
        # calculate ml used for each potion type
        green_ml = potion_type[1] * quantity
        red_ml = potion_type[2] * quantity
        blue_ml = potion_type[3] * quantity
        # update total ml used
        total_green_ml += green_ml
        total_red_ml += red_ml
        total_blue_ml += blue_ml
        # update total bottles per potion type
        if potion_type[1] > 0:
            total_green_bottles += quantity
        if potion_type[2] > 0:
            total_red_bottles += quantity
        if potion_type[3] > 0:
            total_blue_bottles += quantity

    # update inventory in the database
    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                f"""
                UPDATE global_inventory
                SET
                    num_green_potions = num_green_potions + {total_green_bottles},
                    num_red_potions = num_red_potions + {total_red_bottles},
                    num_blue_potions = num_blue_potions + {total_blue_bottles},
                    num_green_ml = num_green_ml - {total_green_ml},
                    num_red_ml = num_red_ml - {total_red_ml},
                    num_blue_ml = num_blue_ml - {total_blue_ml}
                """
            )
        )
    print(f"Potions delivered: {potions_delivered} Order ID: {order_id}")
    return "ok"

@router.post("/plan")
def get_bottle_plan():
    """plan potion bottling"""
    # each bottle needs 100 ml of potion
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml FROM global_inventory")
        )
        inventory = res.first()
        green_ml = inventory.num_green_ml
        red_ml = inventory.num_red_ml
        blue_ml = inventory.num_blue_ml

    # calculate mixable potions for each type
    mixable_green_potions = green_ml // 100
    mixable_red_potions = red_ml // 100
    mixable_blue_potions = blue_ml // 100

    bottle_plan = []

    # plan bottling for green potions
    if mixable_green_potions > 0:
        bottle_plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": mixable_green_potions,
        })

    # plan bottling for red potions
    if mixable_red_potions > 0:
        bottle_plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": mixable_red_potions,
        })

    # plan bottling for blue potions
    if mixable_blue_potions > 0:
        bottle_plan.append({
            "potion_type": [0, 0, 0, 100],
            "quantity": mixable_blue_potions,
        })

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
