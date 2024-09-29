import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone()
        num_green_potions = result[0]

        # Update the potion_catalog_items table
        connection.execute(sqlalchemy.text("""
            INSERT INTO potion_catalog_items (sku, name, quantity, price, potion_type)
            VALUES ('GREEN_POTION_0', 'green potion', :quantity, 50, ARRAY[0, 100, 0, 0])
            ON CONFLICT (sku) DO UPDATE
            SET quantity = GREATEST(0, :quantity)
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