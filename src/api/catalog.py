from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combo must have only one price"""
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text(
                "SELECT num_green_potions, num_red_potions, num_blue_potions FROM global_inventory"
            )
        )
        inventory = res.first()
        green_stock = inventory.num_green_potions
        red_stock = inventory.num_red_potions
        blue_stock = inventory.num_blue_potions

    catalog = []

    # return green potions if available
    if green_stock > 0:
        catalog.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": green_stock,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })

    # return red potions if available
    if red_stock > 0:
        catalog.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": red_stock,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        })

    # return blue potions if available
    if blue_stock > 0:
        catalog.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": blue_stock,
            "price": 50,
            "potion_type": [0, 0, 0, 100],
        })

    return catalog
