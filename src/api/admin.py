import sqlalchemy
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """Reset the game state."""
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                "UPDATE global_inventory SET num_green_potions = 0, num_red_potions = 0, num_blue_potions = 0, num_green_ml = 0, num_red_ml = 0, num_blue_ml = 0, gold = 100"
            ))
    return "OK"