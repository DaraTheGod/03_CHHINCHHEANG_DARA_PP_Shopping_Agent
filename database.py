"""SQLite database setup and connection helpers for the product catalog."""

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "shopping.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "db" / "data.sql"


def get_connection() -> sqlite3.Connection:
    """Open a row-aware SQLite connection and ensure the catalog exists."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    initialize_database(connection)
    return connection


def initialize_database(connection: sqlite3.Connection | None = None) -> None:
    """Create the schema and seed only an empty catalog."""
    owns_connection = connection is None
    connection = connection or sqlite3.connect(DATABASE_PATH)
    try:
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        order_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(orders)").fetchall()
        }
        if existing_columns and (
            "category_id" not in existing_columns or "customer_id" in order_columns
        ):
            connection.executescript(
                """
                DROP TABLE IF EXISTS order_items;
                DROP TABLE IF EXISTS orders;
                DROP TABLE IF EXISTS products;
                DROP TABLE IF EXISTS customers;
                DROP TABLE IF EXISTS categories;
                """
            )
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        product_count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0:
            connection.executescript(SEED_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        if owns_connection:
            connection.close()


def product_from_row(row: sqlite3.Row) -> dict:
    """Convert a database row into the public product shape."""
    return dict(row)
