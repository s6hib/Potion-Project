from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """Get current inventory status"""
    with db.engine.begin() as conn:
        result = conn.execute(sqlalchemy.text("""
            SELECT 
                num_red_potions + num_green_potions + num_blue_potions AS number_of_potions,
                num_red_ml + num_green_ml + num_blue_ml AS ml_in_barrels,
                gold
            FROM global_inventory
        """))
        inventory = result.first()
    
    return {
        "number_of_potions": inventory.number_of_potions,
        "ml_in_barrels": inventory.ml_in_barrels,
        "gold": inventory.gold
    }

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    # This function remains unchanged as it's not directly related to the potion types
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
    # This function remains unchanged as it's not directly related to the potion types
    return "OK"
