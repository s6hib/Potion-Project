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
        # reset inventory
        connection.execute(sqlalchemy.text("""
            UPDATE inventory
            SET red_ml = 0,
                green_ml = 0,
                blue_ml = 0,
                dark_ml = 0,
                gold = 100
        """))

        # clear all potion inventories
        connection.execute(sqlalchemy.text("""
            UPDATE potion_types
            SET inventory = 0
        """))

        # delete all cart items
        connection.execute(sqlalchemy.text("""
            DELETE FROM cart_items
        """))

        # delete all carts
        connection.execute(sqlalchemy.text("""
            DELETE FROM carts
        """))

    return "OK"
