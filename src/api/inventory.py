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
        # Get liquid inventory
        liquid_inventory = connection.execute(sqlalchemy.text("""
            SELECT red_ml, green_ml, blue_ml, dark_ml, gold
            FROM inventory
        """)).fetchone()

        # Get potion inventory
        potion_inventory = connection.execute(sqlalchemy.text("""
            SELECT id, name, inventory, red_ml, green_ml, blue_ml, dark_ml
            FROM potion_types
        """)).fetchall()

    total_potions = sum(potion.inventory for potion in potion_inventory)
    total_ml = sum(getattr(liquid_inventory, f"{color}_ml") for color in ['red', 'green', 'blue', 'dark'])

    audit_result = {
        "number_of_potions": total_potions,
        "ml_in_barrels": total_ml,
        "gold": liquid_inventory.gold,
    }

    # Add liquid inventory
    for color in ['red', 'green', 'blue', 'dark']:
        audit_result[f"{color}_ml"] = getattr(liquid_inventory, f"{color}_ml")

    # Add potion inventory
    for potion in potion_inventory:
        audit_result[f"{potion.name}_potions"] = potion.inventory
        audit_result[f"{potion.name}_ml"] = sum(getattr(potion, f"{color}_ml") * potion.inventory for color in ['red', 'green', 'blue', 'dark'])

    return audit_result

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
