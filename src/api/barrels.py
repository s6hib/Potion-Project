import sqlalchemy
from src import database as db

from fastapi import APIRouter, Depends
from pydantic import BaseModel
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

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        # Get current inventory
        result = connection.execute(sqlalchemy.text(
            "SELECT num_green_ml, gold FROM global_inventory"
        )).fetchone()
        
        current_green_ml, current_gold = result

        # Basic logic: buy a small green barrel if we have less than 1000 ml and enough gold
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL" and current_green_ml < 1000 and current_gold >= barrel.price:
                # Update inventory
                connection.execute(sqlalchemy.text(
                    "UPDATE global_inventory SET num_green_ml = num_green_ml + :ml, gold = gold - :price"
                ), {"ml": barrel.ml_per_barrel, "price": barrel.price})
                
                return [{"sku": "SMALL_GREEN_BARREL", "quantity": 1}]

    return []  # Don't buy anything if conditions aren't met

