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
            color = "red" if barrel.potion_type == [100, 0, 0, 0] else "green" if barrel.potion_type == [0, 100, 0, 0] else "blue"
            sql = f"""
            UPDATE global_inventory
            SET num_{color}_ml = num_{color}_ml + :ml,
                gold = gold - :price
            """
            connection.execute(sqlalchemy.text(sql), {"ml": barrel.ml_per_barrel * barrel.quantity, "price": barrel.price * barrel.quantity})
    
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT gold, num_red_ml, num_green_ml, num_blue_ml
            FROM global_inventory
        """)).fetchone()
        
        gold, red_ml, green_ml, blue_ml = result

    purchase_plan = []
    for barrel in wholesale_catalog:
        color = "red" if barrel.potion_type == [100, 0, 0, 0] else "green" if barrel.potion_type == [0, 100, 0, 0] else "blue"
        current_ml = red_ml if color == "red" else green_ml if color == "green" else blue_ml
        
        if current_ml < 500 and gold >= barrel.price:  # buy if less than 500 ml and we have enough gold
            purchase_plan.append({
                "sku": barrel.sku,
                "quantity": 1
            })
            gold -= barrel.price
    
    return purchase_plan
