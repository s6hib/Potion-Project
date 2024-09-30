# Main purpose of this file seems to be turing raw materials into bottles

# import statements. last two lines are new
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

# sets up router for barrel endpoints (nothing changed)
router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

# defines the PotionInventory class with the specified attributes (nothing changed)
class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

# this endpoint is designed to handle the delivery of bottles to my shop (nothing changed)
# at this point and time it doesn't do anything aside from printing the order id and the bottles being delivered
@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

# if someone sends a POST request to /plan, this function is called
@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection: # opens a connection to the database
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone() # retrieves the number of green ml from the global inventory table
        num_green_ml = result[0] # stores the number of green ml in the variable num_green_ml. fetchone() still returns a tuple even though we asked for one value, so we access the first element of the tuple using [0]

        potions_to_make = num_green_ml // 100 # calculates the number of potions to make by dividing the number of green ml by 100. // is **integer** division
        if potions_to_make > 0: # if we can make at least one potion, do the following
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - :used_ml, num_green_potions = num_green_potions + :new_potions"), # update the global inventory table. reduce the number of green ml by the number of ml used to make the potion(s), and increase the number of green potion(s) by the number of potions made
                               {"used_ml": potions_to_make * 100, "new_potions": potions_to_make}) # these were the placeholder values we used in the sql query. we are passing in the actual values from the python script in this dictionary
            return [{"potion_type": [0, 100, 0, 0], "quantity": potions_to_make}] # this returns our bottling plan, potion type represents green potions, quantity is the number of potions to make

    return [] # no potions to make ('_')

if __name__ == "__main__":
    print(get_bottle_plan())