from fastapi import APIRouter, Depends
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT 
                id,
                name,
                inventory as quantity,
                price,
                red_ml,
                green_ml,
                blue_ml,
                dark_ml
            FROM potion_types
            WHERE inventory > 0
        """)).fetchall()

    catalog = []

    for potion in result:
        catalog.append({
            "sku": f"POTION_{potion.id}",
            "name": potion.name,
            "quantity": potion.quantity,
            "price": int(potion.price),  # Changed from float to int
            "potion_type": [
                potion.red_ml,
                potion.green_ml,
                potion.blue_ml,
                potion.dark_ml
            ],
        })

    return catalog
