"""Database-backed catalog, customer, and order tool implementations."""

import sqlite3

from database import get_connection
from schemas import (
    AddProductInput,
    BuyProductInput,
    CheckStockInput,
    DeleteProductInput,
    EditProductInput,
    GetOrderDetailsInput,
    GetProductDetailsInput,
    ListInStockProductsInput,
    ListOrdersInput,
    SearchProductsInput,
)


def _get_product(connection: sqlite3.Connection, product_id: int, include_inactive: bool = False):
    active_filter = "" if include_inactive else "AND p.active = 1"
    return connection.execute(
        f"""
        SELECT p.id, p.name, c.name AS category, p.price, p.stock, p.active
        FROM products p
        JOIN categories c ON c.id = p.category_id
        WHERE p.id = ? {active_filter}
        """,
        (product_id,),
    ).fetchone()


def _get_or_create_category(connection: sqlite3.Connection, name: str) -> int:
    row = connection.execute(
        "SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return row["id"]
    cursor = connection.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return cursor.lastrowid


def search_products(arguments: SearchProductsInput) -> dict:
    """Search active products by name or category."""
    query = arguments.query.strip().lower()
    if not query:
        return {"ok": False, "error": "SEARCH_QUERY_REQUIRED"}
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.name, c.name AS category, p.price
                FROM products p
                JOIN categories c ON c.id = p.category_id
                WHERE p.active = 1 AND (lower(p.name) LIKE ? OR lower(c.name) LIKE ?)
                ORDER BY p.id
                """,
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        return {"ok": True, "products": [dict(row) for row in rows]}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_READ_ERROR"}


def list_in_stock_products(arguments: ListInStockProductsInput) -> dict:
    """Return every active product that currently has stock."""
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.name, c.name AS category, p.price, p.stock
                FROM products p
                JOIN categories c ON c.id = p.category_id
                WHERE p.active = 1 AND p.stock > 0
                ORDER BY p.id
                """
            ).fetchall()
        return {"ok": True, "products": [dict(row) for row in rows]}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_READ_ERROR"}


def check_stock(arguments: CheckStockInput) -> dict:
    """Return current stock for an active product."""
    if arguments.product_id <= 0:
        return {"ok": False, "error": "PRODUCT_ID_MUST_BE_POSITIVE"}
    try:
        with get_connection() as connection:
            product = _get_product(connection, arguments.product_id)
        if product is None:
            return {"ok": False, "error": "PRODUCT_NOT_FOUND"}
        return {
            "ok": True,
            "product_id": product["id"],
            "product_name": product["name"],
            "stock": product["stock"],
            "in_stock": product["stock"] > 0,
        }
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_READ_ERROR"}


def get_product_details(arguments: GetProductDetailsInput) -> dict:
    """Return complete details for an active product."""
    if arguments.product_id <= 0:
        return {"ok": False, "error": "PRODUCT_ID_MUST_BE_POSITIVE"}
    try:
        with get_connection() as connection:
            product = _get_product(connection, arguments.product_id)
        if product is None:
            return {"ok": False, "error": "PRODUCT_NOT_FOUND"}
        return {"ok": True, "product": dict(product)}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_READ_ERROR"}


def buy_product(arguments: BuyProductInput) -> dict:
    """Create an order and order item while reducing stock atomically."""
    if arguments.product_id <= 0:
        return {"ok": False, "error": "PRODUCT_ID_MUST_BE_POSITIVE"}
    if arguments.quantity <= 0:
        return {"ok": False, "error": "QUANTITY_MUST_BE_POSITIVE"}
    try:
        with get_connection() as connection:
            product = _get_product(connection, arguments.product_id)
            if product is None:
                return {"ok": False, "error": "PRODUCT_NOT_FOUND"}
            if arguments.quantity > product["stock"]:
                return {"ok": False, "error": "INSUFFICIENT_STOCK"}

            line_total = round(product["price"] * arguments.quantity, 2)
            cursor = connection.execute(
                "INSERT INTO orders (customer_name, status, total_amount) VALUES ('Default Customer', 'confirmed', ?)",
                (line_total,),
            )
            order_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, arguments.product_id, arguments.quantity, product["price"], line_total),
            )
            connection.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (arguments.quantity, arguments.product_id),
            )
            remaining_stock = product["stock"] - arguments.quantity
        return {
            "ok": True,
            "message": "ORDER_CREATED",
            "order_id": order_id,
            "customer_name": "Default Customer",
            "product_id": arguments.product_id,
            "quantity": arguments.quantity,
            "total_amount": line_total,
            "remaining_stock": remaining_stock,
        }
    except sqlite3.Error:
        return {"ok": False, "error": "ORDER_WRITE_ERROR"}


def get_order_details(arguments: GetOrderDetailsInput) -> dict:
    """Return an order header and all of its items."""
    if arguments.order_id <= 0:
        return {"ok": False, "error": "ORDER_ID_MUST_BE_POSITIVE"}
    try:
        with get_connection() as connection:
            order = connection.execute(
                """
                  SELECT id, customer_name, status, total_amount, created_at
                  FROM orders WHERE id = ?
                """,
                (arguments.order_id,),
            ).fetchone()
            if order is None:
                return {"ok": False, "error": "ORDER_NOT_FOUND"}
            items = connection.execute(
                """
                SELECT oi.product_id, p.name AS product_name, oi.quantity,
                       oi.unit_price, oi.line_total
                FROM order_items oi JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = ? ORDER BY oi.id
                """,
                (arguments.order_id,),
            ).fetchall()
        return {"ok": True, "order": dict(order), "items": [dict(item) for item in items]}
    except sqlite3.Error:
        return {"ok": False, "error": "ORDER_READ_ERROR"}


def list_orders(arguments: ListOrdersInput) -> dict:
    """List all orders for the default customer."""
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, customer_name, status, total_amount, created_at
                FROM orders ORDER BY id DESC
                """,
            ).fetchall()
        return {"ok": True, "orders": [dict(row) for row in rows]}
    except sqlite3.Error:
        return {"ok": False, "error": "ORDER_READ_ERROR"}


def add_product(arguments: AddProductInput) -> dict:
    """Add a product and connect it to a category."""
    name = arguments.name.strip()
    category = arguments.category.strip()
    if not name or not category:
        return {"ok": False, "error": "NAME_AND_CATEGORY_REQUIRED"}
    if arguments.price < 0:
        return {"ok": False, "error": "PRICE_MUST_NOT_BE_NEGATIVE"}
    if arguments.stock < 0:
        return {"ok": False, "error": "STOCK_MUST_NOT_BE_NEGATIVE"}
    try:
        with get_connection() as connection:
            category_id = _get_or_create_category(connection, category)
            cursor = connection.execute(
                "INSERT INTO products (name, category_id, price, stock) VALUES (?, ?, ?, ?)",
                (name, category_id, arguments.price, arguments.stock),
            )
            product = _get_product(connection, cursor.lastrowid)
        return {"ok": True, "message": "PRODUCT_ADDED", "product": dict(product)}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "PRODUCT_NAME_ALREADY_EXISTS"}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_WRITE_ERROR"}


def edit_product(arguments: EditProductInput) -> dict:
    """Update supplied fields on an existing product."""
    if arguments.product_id <= 0:
        return {"ok": False, "error": "PRODUCT_ID_MUST_BE_POSITIVE"}
    if arguments.price is not None and arguments.price < 0:
        return {"ok": False, "error": "PRICE_MUST_NOT_BE_NEGATIVE"}
    if arguments.stock is not None and arguments.stock < 0:
        return {"ok": False, "error": "STOCK_MUST_NOT_BE_NEGATIVE"}
    if all(value is None for value in (arguments.name, arguments.category, arguments.price, arguments.stock)):
        return {"ok": False, "error": "NO_FIELDS_TO_UPDATE"}
    if arguments.name is not None and not arguments.name.strip():
        return {"ok": False, "error": "NAME_MUST_NOT_BE_EMPTY"}
    if arguments.category is not None and not arguments.category.strip():
        return {"ok": False, "error": "CATEGORY_MUST_NOT_BE_EMPTY"}

    try:
        with get_connection() as connection:
            if _get_product(connection, arguments.product_id) is None:
                return {"ok": False, "error": "PRODUCT_NOT_FOUND"}
            fields = []
            values = []
            if arguments.name is not None:
                fields.append("name = ?")
                values.append(arguments.name.strip())
            if arguments.category is not None:
                fields.append("category_id = ?")
                values.append(_get_or_create_category(connection, arguments.category.strip()))
            if arguments.price is not None:
                fields.append("price = ?")
                values.append(arguments.price)
            if arguments.stock is not None:
                fields.append("stock = ?")
                values.append(arguments.stock)
            values.append(arguments.product_id)
            connection.execute(
                f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values
            )
            product = _get_product(connection, arguments.product_id)
        return {"ok": True, "message": "PRODUCT_UPDATED", "product": dict(product)}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "PRODUCT_NAME_ALREADY_EXISTS"}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_WRITE_ERROR"}


def delete_product(arguments: DeleteProductInput) -> dict:
    """Archive a product while preserving historical order references."""
    if arguments.product_id <= 0:
        return {"ok": False, "error": "PRODUCT_ID_MUST_BE_POSITIVE"}
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "UPDATE products SET active = 0 WHERE id = ? AND active = 1",
                (arguments.product_id,),
            )
        if cursor.rowcount == 0:
            return {"ok": False, "error": "PRODUCT_NOT_FOUND"}
        return {"ok": True, "message": "PRODUCT_ARCHIVED", "product_id": arguments.product_id}
    except sqlite3.Error:
        return {"ok": False, "error": "CATALOG_WRITE_ERROR"}
