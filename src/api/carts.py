from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from datetime import datetime

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
        SELECT 
            ci.id as line_item_id,
            pt.name as item_sku,
            c.customer_name,
            ci.quantity * pt.price as line_item_total,
            c.created_at as timestamp
        FROM cart_items ci
        JOIN carts c ON ci.cart_id = c.id
        JOIN potion_types pt ON ci.potion_type_id = pt.id
        WHERE 1=1
        """
        params = {}

        if customer_name:
            query += " AND LOWER(c.customer_name) LIKE LOWER(:customer_name)"
            params['customer_name'] = f"%{customer_name}%"

        if potion_sku:
            query += " AND LOWER(pt.name) LIKE LOWER(:potion_sku)"
            params['potion_sku'] = f"%{potion_sku}%"

        query += f" ORDER BY {sort_col} {sort_order}"
        query += " LIMIT 6"  # 5 + 1 to check if there's a next page

        if search_page:
            query += " OFFSET :offset"
            params['offset'] = int(search_page)

        results = connection.execute(sqlalchemy.text(query), params).fetchall()

    has_previous = search_page != ""
    has_next = len(results) > 5

    return {
        "previous": str(int(search_page) - 5) if has_previous else "",
        "next": search_page + 5 if has_next else "",
        "results": [
            {
                "line_item_id": row.line_item_id,
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": float(row.line_item_total),
                "timestamp": row.timestamp.isoformat(),
            }
            for row in results[:5]  # Only return the first 5 results
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
        result = connection.execute(
            sqlalchemy.text(
                "INSERT INTO carts (customer_name, character_class, level) VALUES (:name, :class, :level) RETURNING id"
            ),
            {"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}
        )
        cart_id = result.scalar_one()
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        # Check if cart exists
        cart = connection.execute(
            sqlalchemy.text("SELECT id FROM carts WHERE id = :cart_id"),
            {"cart_id": cart_id}
        ).fetchone()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Get potion type id and inventory
        potion = connection.execute(
            sqlalchemy.text("SELECT id, inventory FROM potion_types WHERE name = :sku"),
            {"sku": item_sku}
        ).fetchone()
        if not potion:
            raise HTTPException(status_code=400, detail="Invalid item SKU")

        if cart_item.quantity > potion.inventory:
            raise HTTPException(status_code=400, detail="Not enough inventory")

        # Update or insert cart item
        connection.execute(
            sqlalchemy.text("""
            INSERT INTO cart_items (cart_id, potion_type_id, quantity)
            VALUES (:cart_id, :potion_id, :quantity)
            ON CONFLICT (cart_id, potion_type_id) DO UPDATE
            SET quantity = :quantity
            """),
            {"cart_id": cart_id, "potion_id": potion.id, "quantity": cart_item.quantity}
        )

    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        # Check if cart exists and get items
        cart_items = connection.execute(
            sqlalchemy.text("""
            SELECT ci.potion_type_id, ci.quantity, pt.price, pt.inventory,
                   pt.red_ml, pt.green_ml, pt.blue_ml, pt.dark_ml
            FROM cart_items ci
            JOIN potion_types pt ON ci.potion_type_id = pt.id
            WHERE ci.cart_id = :cart_id
            """),
            {"cart_id": cart_id}
        ).fetchall()

        if not cart_items:
            raise HTTPException(status_code=404, detail="Cart not found or empty")

        total_gold = sum(item.quantity * item.price for item in cart_items)

        # Check inventory and update
        for item in cart_items:
            if item.quantity > item.inventory:
                raise HTTPException(status_code=400, detail=f"Not enough inventory for potion {item.potion_type_id}")

            connection.execute(
                sqlalchemy.text("""
                UPDATE potion_types
                SET inventory = inventory - :quantity
                WHERE id = :potion_id
                """),
                {"quantity": item.quantity, "potion_id": item.potion_type_id}
            )

            connection.execute(
                sqlalchemy.text("""
                UPDATE inventory
                SET gold = gold + :gold,
                    red_ml = red_ml - :red_ml,
                    green_ml = green_ml - :green_ml,
                    blue_ml = blue_ml - :blue_ml,
                    dark_ml = dark_ml - :dark_ml
                """),
                {
                    "gold": item.quantity * item.price,
                    "red_ml": item.quantity * item.red_ml,
                    "green_ml": item.quantity * item.green_ml,
                    "blue_ml": item.quantity * item.blue_ml,
                    "dark_ml": item.quantity * item.dark_ml
                }
            )

        # Clear the cart
        connection.execute(
            sqlalchemy.text("DELETE FROM cart_items WHERE cart_id = :cart_id"),
            {"cart_id": cart_id}
        )

    return {"total_potions_bought": sum(item.quantity for item in cart_items), "total_gold_paid": total_gold}