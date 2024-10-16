from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            # update potion_types table
            sql = """
            UPDATE potion_types
            SET quantity = quantity + :ml
            WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark
            """
            connection.execute(sqlalchemy.text(sql), {
                "ml": barrel.ml_per_barrel * barrel.quantity,
                "red": barrel.potion_type[0],
                "green": barrel.potion_type[1],
                "blue": barrel.potion_type[2],
                "dark": barrel.potion_type[3]
            })
            
            # update global_inventory
            sql = """
            UPDATE global_inventory
            SET gold = gold - :price
            """
            connection.execute(sqlalchemy.text(sql), {"price": barrel.price * barrel.quantity})
    
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT gold FROM global_inventory
        """)).fetchone()
        
        gold = result[0]
        print(f"Current gold: {gold}")

        potion_types = connection.execute(sqlalchemy.text("""
            SELECT red, green, blue, dark, quantity
            FROM potion_types
        """)).fetchall()
        print(f"Potion types: {potion_types}")

    purchase_plan = []
    for barrel in wholesale_catalog:
        print(f"Checking barrel: {barrel}")
        for potion_type in potion_types:
            if sum(barrel.potion_type) == 1 and any(a == 1 and b == 100 for a, b in zip(barrel.potion_type, potion_type[:4])):
                current_ml = potion_type[4]  # quantity
                print(f"Matching potion type found. Current ml: {current_ml}")
                if current_ml < 500 and gold >= barrel.price:  # buy if less than 500 ml and we have enough gold
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    gold -= barrel.price
                    print(f"Added to purchase plan. Remaining gold: {gold}")
                else:
                    print(f"Not added to plan. Current ml: {current_ml}, Barrel price: {barrel.price}, Available gold: {gold}")
                break
        else:
            print(f"No matching potion type found for barrel: {barrel.sku}")

    print(f"Final purchase plan: {purchase_plan}")
    return purchase_plan
