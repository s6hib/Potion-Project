from fastapi import APIRouter, Depends
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        # Reset inventory
        connection.execute(sqlalchemy.text("""
            UPDATE inventory
            SET red_ml = 0,
                green_ml = 0,
                blue_ml = 0,
                dark_ml = 0,
                gold = 100
        """))

        # Clear all potion inventories
        connection.execute(sqlalchemy.text("""
            UPDATE potion_types
            SET inventory = 0
        """))

        # Delete all cart items
        connection.execute(sqlalchemy.text("""
            DELETE FROM cart_items
        """))

        # Delete all carts
        connection.execute(sqlalchemy.text("""
            DELETE FROM carts
        """))

    return "OK"
