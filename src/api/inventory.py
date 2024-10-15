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
        gold_result = connection.execute(sqlalchemy.text("""
            SELECT gold FROM global_inventory
        """)).fetchone()
        
        potions_result = connection.execute(sqlalchemy.text("""
            SELECT SUM(quantity) as total_potions,
                   SUM(CASE WHEN red > 0 THEN quantity ELSE 0 END) as red_potions,
                   SUM(CASE WHEN green > 0 THEN quantity ELSE 0 END) as green_potions,
                   SUM(CASE WHEN blue > 0 THEN quantity ELSE 0 END) as blue_potions,
                   SUM(CASE WHEN dark > 0 THEN quantity ELSE 0 END) as dark_potions
            FROM potion_types
        """)).fetchone()

    gold = gold_result.gold if gold_result else 0
    total_potions = potions_result.total_potions or 0
    red_potions = potions_result.red_potions or 0
    green_potions = potions_result.green_potions or 0
    blue_potions = potions_result.blue_potions or 0
    dark_potions = potions_result.dark_potions or 0

    return {
        "number_of_potions": total_potions,
        "ml_in_barrels": 0,  # We're not tracking ml separately anymore
        "gold": gold,
        "red_potions": red_potions,
        "green_potions": green_potions,
        "blue_potions": blue_potions,
        "dark_potions": dark_potions
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
