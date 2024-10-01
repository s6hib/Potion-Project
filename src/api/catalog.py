from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combo must have only one price"""
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text("SELECT num_green_potions FROM global_inventory")
        )
        green_stock = res.first().num_green_potions
    
    # return green potions if available
    if green_stock > 0:
        return [{
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": green_stock,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        }]
    return []