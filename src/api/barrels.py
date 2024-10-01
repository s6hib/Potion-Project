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
    # calculate total ml and cost for the delivered barrels
    total_ml = sum(b.ml_per_barrel * b.quantity for b in barrels_delivered)
    total_cost = sum(b.price * b.quantity for b in barrels_delivered)

    # update inventory in the database
    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                f"UPDATE global_inventory \
                SET num_green_ml = num_green_ml + {total_ml}, \
                gold = gold - {total_cost}"
            )
        )
    # log the delivery details
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# plan wholesale barrel purchases
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """plan barrel purchases"""
    print(wholesale_catalog)
    # find green barrel in the catalog
    green_barrel = next((b for b in wholesale_catalog if b.sku == "SMALL_GREEN_BARREL"), None)
    if green_barrel:
        # retrieve current inventory data
        with db.engine.begin() as conn:
            res = conn.execute(
                sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")
            )
            inv_data = res.first()
        # if conditions are met, plan to buy one green barrel
        if inv_data.num_green_potions < 10 and inv_data.gold >= green_barrel.price:
            return [{"sku": "SMALL_GREEN_BARREL", "quantity": 1}]
    # return empty if no purchase is needed
    return []