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
    potion_type_id: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            # Get potion type details
            potion_type = connection.execute(sqlalchemy.text("""
                SELECT red_ml, green_ml, blue_ml, dark_ml
                FROM potion_types
                WHERE id = :id
            """), {"id": potion.potion_type_id}).fetchone()

            if potion_type:
                # Update potion inventory
                connection.execute(sqlalchemy.text("""
                    UPDATE potion_types
                    SET inventory = inventory + :quantity
                    WHERE id = :id
                """), {"quantity": potion.quantity, "id": potion.potion_type_id})

                # Update liquid inventory
                connection.execute(sqlalchemy.text("""
                    UPDATE inventory
                    SET red_ml = red_ml - :red_ml,
                        green_ml = green_ml - :green_ml,
                        blue_ml = blue_ml - :blue_ml,
                        dark_ml = dark_ml - :dark_ml
                """), {
                    "red_ml": potion_type.red_ml * potion.quantity,
                    "green_ml": potion_type.green_ml * potion.quantity,
                    "blue_ml": potion_type.blue_ml * potion.quantity,
                    "dark_ml": potion_type.dark_ml * potion.quantity
                })
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        # Get available liquid
        inventory = connection.execute(sqlalchemy.text("""
            SELECT red_ml, green_ml, blue_ml, dark_ml
            FROM inventory
        """)).fetchone()

        # Get all potion types
        potion_types = connection.execute(sqlalchemy.text("""
            SELECT id, red_ml, green_ml, blue_ml, dark_ml
            FROM potion_types
        """)).fetchall()

    bottle_plan = []
    
    for potion_type in potion_types:
        max_potions = min(
            inventory.red_ml // potion_type.red_ml if potion_type.red_ml > 0 else float('inf'),
            inventory.green_ml // potion_type.green_ml if potion_type.green_ml > 0 else float('inf'),
            inventory.blue_ml // potion_type.blue_ml if potion_type.blue_ml > 0 else float('inf'),
            inventory.dark_ml // potion_type.dark_ml if potion_type.dark_ml > 0 else float('inf'),
            5  # max 5 potions per type
        )

        if max_potions > 0:
            bottle_plan.append({"potion_type_id": potion_type.id, "quantity": int(max_potions)})

            # Update inventory
            inventory.red_ml -= potion_type.red_ml * max_potions
            inventory.green_ml -= potion_type.green_ml * max_potions
            inventory.blue_ml -= potion_type.blue_ml * max_potions
            inventory.dark_ml -= potion_type.dark_ml * max_potions

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
