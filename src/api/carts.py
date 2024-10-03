from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

# simple in memory cart storage
cart_storage = {}

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class SearchSortOptions(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class SearchSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: SearchSortOptions = SearchSortOptions.timestamp,
    sort_order: SearchSortOrder = SearchSortOrder.desc,
):
    """search for cart line items by customer name and/or potion sku"""
    # placeholder implementation
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
    """log customer visits"""
    print(customers)
    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """create a new cart"""
    cart_id = len(cart_storage) + 1
    cart_storage[cart_id] = {"customer": new_cart, "items": {}}
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """set item quantity in cart"""
    cart_storage[cart_id]["items"][item_sku] = cart_item
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """process cart checkout"""
    cart = cart_storage[cart_id]
    total_red_potions = 0
    total_green_potions = 0
    total_blue_potions = 0
    total_price = 0

    for item_sku, cart_item in cart["items"].items():
        if item_sku.startswith("RED"):
            total_red_potions += cart_item.quantity
        elif item_sku.startswith("GREEN"):
            total_green_potions += cart_item.quantity
        elif item_sku.startswith("BLUE"):
            total_blue_potions += cart_item.quantity
        
        total_price += cart_item.quantity * 50  # Assuming all potions cost 50 gold

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                f"""
                UPDATE global_inventory 
                SET num_red_potions = num_red_potions - :red_potions,
                    num_green_potions = num_green_potions - :green_potions,
                    num_blue_potions = num_blue_potions - :blue_potions,
                    gold = gold + :total_price
                """
            ),
            {
                "red_potions": total_red_potions,
                "green_potions": total_green_potions,
                "blue_potions": total_blue_potions,
                "total_price": total_price
            }
        )

    total_potions = total_red_potions + total_green_potions + total_blue_potions
    return {"total_potions_bought": total_potions, "total_gold_paid": total_price}