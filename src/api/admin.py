from fastapi import APIRouter, Depends
from src.api import auth
import sqlalchemy
from src import database as db
from src.api.carts import carts  # import the in-memory cart storage

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
        connection.execute(sqlalchemy.text("""
            UPDATE global_inventory
            SET num_red_potions = 0,
                num_green_potions = 0,
                num_blue_potions = 0,
                num_red_ml = 0,
                num_green_ml = 0,
                num_blue_ml = 0,
                gold = 100
        """))

    # clear all carts
    carts.clear()

    return "OK"
