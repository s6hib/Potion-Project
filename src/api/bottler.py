from fastapi import APIRouter, Depends
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
            # get potion type details
            potion_type = connection.execute(sqlalchemy.text("""
                SELECT id
                FROM potion_types
                WHERE red_ml = :red_ml AND green_ml = :green_ml AND blue_ml = :blue_ml AND dark_ml = :dark_ml
            """), {
                "red_ml": potion.potion_type[0],
                "green_ml": potion.potion_type[1],
                "blue_ml": potion.potion_type[2],
                "dark_ml": potion.potion_type[3]
            }).fetchone()

            if potion_type:
                # update potion inventory
                connection.execute(sqlalchemy.text("""
                    UPDATE potion_types
                    SET inventory = inventory + :quantity
                    WHERE id = :id
                """), {"quantity": potion.quantity, "id": potion_type.id})

                # update liquid inventory
                connection.execute(sqlalchemy.text("""
                    UPDATE inventory
                    SET red_ml = red_ml - :red_ml,
                        green_ml = green_ml - :green_ml,
                        blue_ml = blue_ml - :blue_ml,
                        dark_ml = dark_ml - :dark_ml
                """), {
                    "red_ml": potion.potion_type[0] * potion.quantity,
                    "green_ml": potion.potion_type[1] * potion.quantity,
                    "blue_ml": potion.potion_type[2] * potion.quantity,
                    "dark_ml": potion.potion_type[3] * potion.quantity
                })
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        # get available liquid
        inventory = connection.execute(sqlalchemy.text("""
            SELECT red_ml, green_ml, blue_ml, dark_ml
            FROM inventory
        """)).fetchone()

        # get all potion types
        potion_types = connection.execute(sqlalchemy.text("""
            SELECT id, red_ml, green_ml, blue_ml, dark_ml
            FROM potion_types
        """)).fetchall()

    bottle_plan = []
    
    # create variables to track remaining liquid (without modifying the actual inventory)
    remaining_red_ml = inventory.red_ml
    remaining_green_ml = inventory.green_ml
    remaining_blue_ml = inventory.blue_ml
    remaining_dark_ml = inventory.dark_ml
    
    for potion_type in potion_types:
        max_potions = min(
            remaining_red_ml // potion_type.red_ml if potion_type.red_ml > 0 else float('inf'),
            remaining_green_ml // potion_type.green_ml if potion_type.green_ml > 0 else float('inf'),
            remaining_blue_ml // potion_type.blue_ml if potion_type.blue_ml > 0 else float('inf'),
            remaining_dark_ml // potion_type.dark_ml if potion_type.dark_ml > 0 else float('inf'),
            5  # Max 5 potions per type
        )

        if max_potions > 0:
            bottle_plan.append({
                "potion_type": [potion_type.red_ml, potion_type.green_ml, potion_type.blue_ml, potion_type.dark_ml],
                "quantity": int(max_potions)
            })

            # update remaining liquid (without modifying the actual inventory)
            remaining_red_ml -= potion_type.red_ml * max_potions
            remaining_green_ml -= potion_type.green_ml * max_potions
            remaining_blue_ml -= potion_type.blue_ml * max_potions
            remaining_dark_ml -= potion_type.dark_ml * max_potions

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
