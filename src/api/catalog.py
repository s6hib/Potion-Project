from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combo must have only one price"""
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    num_red_potions, 
                    num_green_potions, 
                    num_blue_potions 
                FROM global_inventory
            """)
        )
        inventory = res.first()
    
    catalog = []
    
    # add red potions if available
    if inventory.num_red_potions > 0:
        catalog.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": inventory.num_red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        })
    
    # add green potions if available
    if inventory.num_green_potions > 0:
        catalog.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": inventory.num_green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })
    
    # add blue potions if available
    if inventory.num_blue_potions > 0:
        catalog.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": inventory.num_blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        })
    
    return catalog