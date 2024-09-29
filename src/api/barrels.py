# import statements. last two lines are new
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

# sets up router for barrel endpoints (nothing changed)
router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

# defines the Barrel class with the specified attributes (nothing changed)
class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

# this endpoint hasn't changed
@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# 
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchone()
        num_green_potions, gold = result

        if num_green_potions < 10:
            for barrel in wholesale_catalog:
                if barrel.sku == "SMALL_GREEN_BARREL" and gold >= barrel.price:
                    new_gold = gold - barrel.price
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :ml, gold = :new_gold"),
                                       {"ml": barrel.ml_per_barrel, "new_gold": new_gold})
                    return [{"sku": "SMALL_GREEN_BARREL", "quantity": 1}]

    return []