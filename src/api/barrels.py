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
    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_GREEN_BARREL":
            with db.engine.begin() as connection:
                # update green ml and deduct gold for purchased barrels
                connection.execute(
                    sqlalchemy.text(
                        "UPDATE global_inventory SET num_green_ml = num_green_ml + :ml, gold = gold - :cost"
                    ),
                    {"ml": barrel.ml_per_barrel * barrel.quantity, "cost": barrel.price * barrel.quantity}
                )
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        # get current inventory
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_green_ml, gold FROM global_inventory"))
        inventory = result.fetchone()
    
    # buy a small green barrel if inventory is low and we have enough gold
    if (inventory.num_green_potions < 10 or inventory.num_green_ml < 1000) and inventory.gold >= 50:
        return [{"sku": "SMALL_GREEN_BARREL", "quantity": 1}]
    return []