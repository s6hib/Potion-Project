from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    print(customers)
    return "OK"

# in-memory cart storage
carts = {}

@router.post("/")
def create_cart(new_cart: Customer):
    cart_id = len(carts) + 1
    carts[cart_id] = {"customer": new_cart, "items": {}}
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT num_red_potions, num_green_potions, num_blue_potions
            FROM global_inventory
        """)).fetchone()
        
        red_potions, green_potions, blue_potions = result

    inventory = {
        "RED_POTION_0": red_potions,
        "GREEN_POTION_0": green_potions,
        "BLUE_POTION_0": blue_potions
    }

    if item_sku not in inventory:
        raise HTTPException(status_code=400, detail="Invalid item SKU")

    if cart_item.quantity > inventory[item_sku]:
        raise HTTPException(status_code=400, detail="Not enough inventory")

    carts[cart_id]["items"][item_sku] = cart_item.quantity
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart = carts[cart_id]
    total_potions = sum(cart["items"].values())
    total_gold = total_potions * 50  # assuming all potions cost 50 gold

    with db.engine.begin() as connection:
        for sku, quantity in cart["items"].items():
            color = "red" if sku == "RED_POTION_0" else "green" if sku == "GREEN_POTION_0" else "blue"
            sql = f"""
            UPDATE global_inventory
            SET num_{color}_potions = num_{color}_potions - :quantity,
                gold = gold + :gold
            WHERE num_{color}_potions >= :quantity
            """
            result = connection.execute(sqlalchemy.text(sql), 
                                        {"quantity": quantity, "gold": quantity * 50})
            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail=f"Not enough {color} potions in inventory")

    # clear the cart after successful checkout
    del carts[cart_id]

    return {"total_potions_bought": total_potions, "total_gold_paid": total_gold}
