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
    inventory, and all carts are cleared.
    """
    with db.engine.begin() as connection:
        # reset global_inventory
        connection.execute(sqlalchemy.text("""
            UPDATE global_inventory
            SET gold = 100
        """))

        # reset potion_types
        connection.execute(sqlalchemy.text("""
            UPDATE potion_types
            SET quantity = 0
        """))

        # clear all carts and cart items
        connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
        connection.execute(sqlalchemy.text("DELETE FROM carts"))

    return "OK"
