from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

# handle delivery of barrels
@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """handle barrel delivery"""
    # calculate total ml and cost for the delivered barrels
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_cost = 0

    for b in barrels_delivered:
        ml = b.ml_per_barrel * b.quantity
        cost = b.price * b.quantity
        total_cost += cost

        # determine potion type based on SKU
        if b.sku == "MINI_GREEN_BARREL":
            total_green_ml += ml
        elif b.sku == "MINI_RED_BARREL":
            total_red_ml += ml
        elif b.sku == "MINI_BLUE_BARREL":
            total_blue_ml += ml
        else:
            # handle unknown SKU if necessary
            pass

    # update inventory in the database
    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                f"""
                UPDATE global_inventory
                SET
                    num_green_ml = num_green_ml + {total_green_ml},
                    num_red_ml = num_red_ml + {total_red_ml},
                    num_blue_ml = num_blue_ml + {total_blue_ml},
                    gold = gold - {total_cost}
                """
            )
        )
    # log the delivery details
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# plan wholesale barrel purchases
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """plan barrel purchases"""
    print(wholesale_catalog)
    # find MINI barrels in the catalog
    blue_barrel = next((b for b in wholesale_catalog if b.sku == "MINI_BLUE_BARREL"), None)
    red_barrel = next((b for b in wholesale_catalog if b.sku == "MINI_RED_BARREL"), None)
    green_barrel = next((b for b in wholesale_catalog if b.sku == "MINI_GREEN_BARREL"), None)

    # retrieve current inventory data
    with db.engine.begin() as conn:
        res = conn.execute(
            sqlalchemy.text(
                "SELECT num_green_potions, num_red_potions, num_blue_potions, gold FROM global_inventory"
            )
        )
        inv_data = res.first()

    purchase_plan = []
    available_gold = inv_data.gold

    # plan to buy blue barrel if needed
    if blue_barrel and inv_data.num_blue_potions < 10 and available_gold >= blue_barrel.price:
        purchase_plan.append({"sku": "MINI_BLUE_BARREL", "quantity": 1})
        available_gold -= blue_barrel.price

    # plan to buy red barrel if needed
    if red_barrel and inv_data.num_red_potions < 10 and available_gold >= red_barrel.price:
        purchase_plan.append({"sku": "MINI_RED_BARREL", "quantity": 1})
        available_gold -= red_barrel.price

    # plan to buy green barrel if needed
    if green_barrel and inv_data.num_green_potions < 10 and available_gold >= green_barrel.price:
        purchase_plan.append({"sku": "MINI_GREEN_BARREL", "quantity": 1})
        available_gold -= green_barrel.price

    return purchase_plan