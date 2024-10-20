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
    with db.engine.begin() as connection:
        # Get current inventory and capacity
        result = connection.execute(sqlalchemy.text("""
            SELECT SUM(inventory) as total_potions, 
                   (SELECT potion_capacity FROM shop_capacity) as current_capacity,
                   (SELECT gold FROM inventory) as gold
            FROM potion_types
        """)).fetchone()
        
        total_potions = result.total_potions or 0
        current_capacity = result.current_capacity or 1  # Default to 1 if not set
        gold = result.gold or 0

        # Calculate how many more potion capacities we need
        needed_capacity = max(0, (total_potions // 50) - current_capacity + 1)
        
        # Limit the purchase based on available gold
        affordable_capacity = min(needed_capacity, gold // 1000)

    return {
        "potion_capacity": affordable_capacity,
        "ml_capacity": 0  # We're not handling ml capacity in this example
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
    with db.engine.begin() as connection:
        # Update the shop capacity
        connection.execute(sqlalchemy.text("""
            INSERT INTO shop_capacity (potion_capacity, ml_capacity)
            VALUES (:potion_capacity, :ml_capacity)
            ON CONFLICT (id) DO UPDATE
            SET potion_capacity = shop_capacity.potion_capacity + :potion_capacity,
                ml_capacity = shop_capacity.ml_capacity + :ml_capacity
        """), {
            "potion_capacity": capacity_purchase.potion_capacity,
            "ml_capacity": capacity_purchase.ml_capacity
        })

        # Deduct the cost from gold
        total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
        connection.execute(sqlalchemy.text("""
            UPDATE inventory
            SET gold = gold - :cost
        """), {"cost": total_cost})

    return "OK"
