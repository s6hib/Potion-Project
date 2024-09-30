# Main purpose of this file seems to be to handle the delivery of barrels (raw materials) to make potions

# import statements. last two lines are new
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

# sets up router for barrel endpoints (nothing changed)
router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

# defines the Barrel class with the specified attributes (nothing changed)
class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int): 
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
# if someone sends a POST request to /plan, this function is called
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]): # it takes in a list of barrels that are available for wholesale purchase
    with db.engine.begin() as connection: # think of this as like opening a door to the database to do the following
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchone() # check to see how many green potions and gold is in the global_inventory table
        num_green_potions, gold = result # now whatever we retrieved from the database, we are storing it in num_green_potions and gold. fetchone() returns a tuple, so it will automatically assign the first value to num_green_potions and the second to gold

        # after we assigned the values to num_green_potions and gold, we can now use it to do the following
        if num_green_potions < 10: # if the number of green potions is less than 10, we want to buy a small green barrel
            for barrel in wholesale_catalog: # we are looping through the entire wholesale catalog
                if barrel.sku == "SMALL_GREEN_BARREL" and gold >= barrel.price: # if the sku is a small green barrel and if we have enough gold to buy it
                    new_gold = gold - barrel.price # if we decide to buy the barrel, this will calculate the amount of gold we have left
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :ml, gold = :new_gold"), # now we have to update the db, add the barrels contents (ml) to our green potion stock and update the gold we have left after possibly buying
                                       {"ml": barrel.ml_per_barrel, "new_gold": new_gold})
                    return [{"sku": "SMALL_GREEN_BARREL", "quantity": 1}] # after all of these checks, we tell the sysem "Hey I want a barrel pls and thankyou"

    return [] # if we're broke we don't get anything ('_')