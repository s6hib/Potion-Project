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
    with db.engine.begin() as connection:
        query = """
        SELECT ci.id as line_item_id, pt.sku as item_sku, c.customer_name, 
               (ci.quantity * pt.price) as line_item_total, c.created_at as timestamp
        FROM cart_items ci
        JOIN carts c ON ci.cart_id = c.id
        JOIN potion_types pt ON ci.potion_type_id = pt.id
        WHERE c.customer_name ILIKE :customer_name
        AND pt.sku ILIKE :potion_sku
        ORDER BY {} {}
        LIMIT 5
        """.format(sort_col.value, sort_order.value)

        results = connection.execute(sqlalchemy.text(query), {
            "customer_name": f"%{customer_name}%",
            "potion_sku": f"%{potion_sku}%"
        }).fetchall()

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": row.line_item_id,
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": row.line_item_total,
                "timestamp": row.timestamp.isoformat(),
            } for row in results
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

@router.post("/")
def create_cart(new_cart: Customer):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
        INSERT INTO carts (customer_name, character_class, level)
        VALUES (:customer_name, :character_class, :level)
        RETURNING id
        """), new_cart.dict())
        cart_id = result.scalar_one()
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        # check if the cart exists
        cart = connection.execute(sqlalchemy.text("""
        SELECT id FROM carts WHERE id = :cart_id
        """), {"cart_id": cart_id}).fetchone()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # get the potion type
        potion_type = connection.execute(sqlalchemy.text("""
        SELECT id, quantity FROM potion_types WHERE sku = :sku
        """), {"sku": item_sku}).fetchone()
        if not potion_type:
            raise HTTPException(status_code=400, detail="Invalid item SKU")

        if cart_item.quantity > potion_type.quantity:
            raise HTTPException(status_code=400, detail="Not enough inventory")

        # update or insert the cart item
        connection.execute(sqlalchemy.text("""
        INSERT INTO cart_items (cart_id, potion_type_id, quantity)
        VALUES (:cart_id, :potion_type_id, :quantity)
        ON CONFLICT (cart_id, potion_type_id) DO UPDATE
        SET quantity = :quantity
        """), {
            "cart_id": cart_id,
            "potion_type_id": potion_type.id,
            "quantity": cart_item.quantity
        })

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        # get the cart items
        cart_items = connection.execute(sqlalchemy.text("""
        SELECT ci.quantity, pt.id as potion_type_id, pt.price
        FROM cart_items ci
        JOIN potion_types pt ON ci.potion_type_id = pt.id
        WHERE ci.cart_id = :cart_id
        """), {"cart_id": cart_id}).fetchall()

        if not cart_items:
            raise HTTPException(status_code=404, detail="Cart not found or empty")

        total_potions = 0
        total_gold = 0

        for item in cart_items:
            # update potion_types inventory
            result = connection.execute(sqlalchemy.text("""
            UPDATE potion_types
            SET quantity = quantity - :quantity
            WHERE id = :potion_type_id AND quantity >= :quantity
            """), {
                "quantity": item.quantity,
                "potion_type_id": item.potion_type_id
            })
            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="Not enough potions in inventory")

            total_potions += item.quantity
            total_gold += item.quantity * item.price

        # update global_inventory
        connection.execute(sqlalchemy.text("""
        UPDATE global_inventory
        SET gold = gold + :gold
        """), {"gold": total_gold})

        # clear the cart
        connection.execute(sqlalchemy.text("""
        DELETE FROM cart_items WHERE cart_id = :cart_id
        """), {"cart_id": cart_id})

    return {"total_potions_bought": total_potions, "total_gold_paid": total_gold}
