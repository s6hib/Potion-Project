from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT num_red_potions, num_green_potions, num_blue_potions,
                   num_red_ml, num_green_ml, num_blue_ml, gold
            FROM global_inventory
        """)).fetchone()
        
        red_potions, green_potions, blue_potions, red_ml, green_ml, blue_ml, gold = result

    total_potions = red_potions + green_potions + blue_potions
    total_ml = red_ml + green_ml + blue_ml

    return {
        "number_of_potions": total_potions,
        "ml_in_barrels": total_ml,
        "gold": gold,
        "red_potions": red_potions,
        "green_potions": green_potions,
        "blue_potions": blue_potions,
        "red_ml": red_ml,
        "green_ml": green_ml,
        "blue_ml": blue_ml
    }

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    return {
        "potion_capacity": 0,
        "ml_capacity": 0
    }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    return "OK"
