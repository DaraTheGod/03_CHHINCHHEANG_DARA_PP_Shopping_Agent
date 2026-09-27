"""Explicit input schemas for the available tools."""

from dataclasses import dataclass


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog by name or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Product name or category to search for."}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check the current stock for a product ID returned by search_products.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID."}
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get the complete details for a product ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID."}
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy_product",
            "description": "Buy a quantity of a product. Available to customers and admins.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID."},
                    "quantity": {"type": "integer", "description": "Positive quantity to buy."},
                },
                "required": ["product_id", "quantity"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get an order, customer, and item details by order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Positive order ID."}
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List all orders for the default customer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_product",
            "description": "Add a new product to the catalog. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name."},
                    "category": {"type": "string", "description": "Product category."},
                    "price": {"type": "number", "description": "Non-negative price."},
                    "stock": {"type": "integer", "description": "Non-negative stock quantity."},
                },
                "required": ["name", "category", "price", "stock"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_product",
            "description": "Edit an existing product. Admin only. Include at least one field to change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID."},
                    "name": {"type": "string", "description": "New product name."},
                    "category": {"type": "string", "description": "New product category."},
                    "price": {"type": "number", "description": "New non-negative price."},
                    "stock": {"type": "integer", "description": "New non-negative stock quantity."},
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_product",
            "description": "Delete a product from the catalog. Admin only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Positive product ID."}
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
]


@dataclass(frozen=True)
class SearchProductsInput:
    query: str


@dataclass(frozen=True)
class CheckStockInput:
    product_id: int


@dataclass(frozen=True)
class GetProductDetailsInput:
    product_id: int


@dataclass(frozen=True)
class BuyProductInput:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class GetOrderDetailsInput:
    order_id: int


@dataclass(frozen=True)
class ListOrdersInput:
    pass


@dataclass(frozen=True)
class AddProductInput:
    name: str
    category: str
    price: float
    stock: int


@dataclass(frozen=True)
class EditProductInput:
    product_id: int
    name: str | None = None
    category: str | None = None
    price: float | None = None
    stock: int | None = None


@dataclass(frozen=True)
class DeleteProductInput:
    product_id: int