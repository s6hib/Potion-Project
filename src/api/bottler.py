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
            sql = """
            UPDATE potion_types
            SET quantity = quantity + :quantity
            WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark
            """
            connection.execute(sqlalchemy.text(sql), {
                "quantity": potion.quantity,
                "red": potion.potion_type[0],
                "green": potion.potion_type[1],
                "blue": potion.potion_type[2],
                "dark": potion.potion_type[3]
            })
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        potion_types = connection.execute(sqlalchemy.text("""
            SELECT red, green, blue, dark, quantity
            FROM potion_types
        """)).fetchall()

    bottle_plan = []
    
    for potion_type in potion_types:
        red, green, blue, dark, quantity = potion_type
        potions_to_create = min(quantity // 100, 5)  # max 5 potions per type
        if potions_to_create > 0:
            bottle_plan.append({
                "potion_type": [red, green, blue, dark],
                "quantity": potions_to_create
            })

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())
