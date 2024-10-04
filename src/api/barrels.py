from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sqlalchemy
from src import database as db
from src.api import auth

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

# handle delivery of barrels
@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """handle barrel delivery"""
    total_red_ml = 0
    total_green_ml = 0
    total_blue_ml = 0
    total_cost = 0

    for barrel in barrels_delivered:
        if "RED" in barrel.sku.upper():
            total_red_ml += barrel.ml_per_barrel * barrel.quantity
        elif "GREEN" in barrel.sku.upper():
            total_green_ml += barrel.ml_per_barrel * barrel.quantity
        elif "BLUE" in barrel.sku.upper():
            total_blue_ml += barrel.ml_per_barrel * barrel.quantity
        total_cost += barrel.price * barrel.quantity

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory 
                SET num_red_ml = num_red_ml + :red_ml,
                    num_green_ml = num_green_ml + :green_ml,
                    num_blue_ml = num_blue_ml + :blue_ml,
                    gold = gold - :total_cost
                """
            ),
            {
                "red_ml": total_red_ml,
                "green_ml": total_green_ml,
                "blue_ml": total_blue_ml,
                "total_cost": total_cost
            }
        )

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# plan wholesale barrel purchases
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """plan barrel purchases"""
    purchase_plan = []
    
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text("""
                SELECT num_red_potions, num_green_potions, num_blue_potions, gold 
                FROM global_inventory
            """)
        )
        inv_data = res.first()

    for barrel in wholesale_catalog:
        if "RED" in barrel.sku.upper() and inv_data.num_red_potions < 10 and inv_data.gold >= barrel.price:
            purchase_plan.append({"sku": barrel.sku, "quantity": 1})
            inv_data.gold -= barrel.price
        elif "GREEN" in barrel.sku.upper() and inv_data.num_green_potions < 10 and inv_data.gold >= barrel.price:
            purchase_plan.append({"sku": barrel.sku, "quantity": 1})
            inv_data.gold -= barrel.price
        elif "BLUE" in barrel.sku.upper() and inv_data.num_blue_potions < 10 and inv_data.gold >= barrel.price:
            purchase_plan.append({"sku": barrel.sku, "quantity": 1})
            inv_data.gold -= barrel.price

    return purchase_plan