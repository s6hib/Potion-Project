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
            SELECT sku, name, quantity, price, red, green, blue, dark
            FROM potion_types
            WHERE quantity > 0
        """))
        
        catalog = []
        for row in result:
            catalog.append({
                "sku": row.sku,
                "name": row.name,
                "quantity": row.quantity,
                "price": row.price,
                "potion_type": [row.red, row.green, row.blue, row.dark],
            })

    return catalog
