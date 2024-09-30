# Main purpose of this file seems to be to provide information about what potions are available for sale

# import statements. last two lines are new
from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    with db.engine.begin() as connection:
        # Get the current number of green potions
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone()
        num_green_potions = result[0]

        # Update the green potion entry in the catalog
        connection.execute(sqlalchemy.text("""
            UPDATE potion_catalog_items 
            SET quantity = GREATEST(0, :quantity)
            WHERE sku = 'GREEN_POTION_0'
        """), {"quantity": num_green_potions})

        # Fetch the updated catalog
        catalog = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog_items")).fetchall()

    return [
        {
            "sku": item.sku,
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price,
            "potion_type": item.potion_type,
        } for item in catalog
    ]