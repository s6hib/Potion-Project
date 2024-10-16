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
            sql = """
            UPDATE inventory
            SET red_ml = red_ml + :red_ml,
                green_ml = green_ml + :green_ml,
                blue_ml = blue_ml + :blue_ml,
                dark_ml = dark_ml + :dark_ml,
                gold = gold - :price
            """
            connection.execute(sqlalchemy.text(sql), {
                "red_ml": barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[0],
                "green_ml": barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[1],
                "blue_ml": barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[2],
                "dark_ml": barrel.ml_per_barrel * barrel.quantity * barrel.potion_type[3],
                "price": barrel.price * barrel.quantity
            })
    
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT gold, red_ml, green_ml, blue_ml, dark_ml
            FROM inventory
        """)).fetchone()
        
        gold, red_ml, green_ml, blue_ml, dark_ml = result

    purchase_plan = []
    for barrel in wholesale_catalog:
        current_ml = (
            red_ml * barrel.potion_type[0] +
            green_ml * barrel.potion_type[1] +
            blue_ml * barrel.potion_type[2] +
            dark_ml * barrel.potion_type[3]
        )
        
        if current_ml < 500 and gold >= barrel.price:  # buy if less than 500 ml and we have enough gold
            purchase_plan.append({
                "sku": barrel.sku,
                "quantity": 1
            })
            gold -= barrel.price
            red_ml += barrel.ml_per_barrel * barrel.potion_type[0]
            green_ml += barrel.ml_per_barrel * barrel.potion_type[1]
            blue_ml += barrel.ml_per_barrel * barrel.potion_type[2]
            dark_ml += barrel.ml_per_barrel * barrel.potion_type[3]
    
    return purchase_plan
