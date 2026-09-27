"""Application-level permissions and bounded execution controls."""

from collections.abc import Callable


PERMISSIONS = {
    "customer": {
        "search_products", "check_stock", "get_product_details", "buy_product",
        "list_in_stock_products", "get_order_details", "list_orders",
    },
    "admin": {
        "search_products", "check_stock", "get_product_details", "buy_product",
        "list_in_stock_products", "get_order_details", "list_orders",
        "add_product", "edit_product", "delete_product",
    },
}
MAX_TOOL_CALLS = 5


def can_use_tool(role: str, tool_name: str) -> bool:
    """Check permission in application code before a tool is executed."""
    return tool_name in PERMISSIONS.get(role, set())


def execute_tool(
    role: str,
    tool_name: str,
    arguments: object,
    tool_registry: dict[str, Callable[[object], dict]],
) -> dict:
    """Run an allowlisted, permission-checked tool and return controlled errors."""
    if role not in PERMISSIONS:
        return {"ok": False, "error": "UNKNOWN_ROLE"}
    if tool_name not in tool_registry:
        return {"ok": False, "error": "TOOL_NOT_AVAILABLE"}
    if not can_use_tool(role, tool_name):
        return {"ok": False, "error": "PERMISSION_DENIED"}

    try:
        return tool_registry[tool_name](arguments)
    except (TypeError, ValueError, AttributeError):
        return {"ok": False, "error": "INVALID_TOOL_ARGUMENTS"}