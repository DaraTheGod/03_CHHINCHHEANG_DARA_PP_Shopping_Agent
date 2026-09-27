"""LLM-driven agent loop with application-controlled tool execution."""

import json
from dataclasses import asdict, is_dataclass

from openai import OpenAI

from config import MAX_TOOL_CALLS, MODEL_NAME, create_client
from harness import execute_tool
from schemas import (
    AddProductInput,
    BuyProductInput,
    CheckStockInput,
    DeleteProductInput,
    EditProductInput,
    GetOrderDetailsInput,
    GetProductDetailsInput,
    ListOrdersInput,
    SearchProductsInput,
    TOOL_SCHEMAS,
)
from tools import (
    add_product, buy_product, check_stock, delete_product, edit_product,
    get_order_details, get_product_details, list_orders, search_products,
)


TOOL_REGISTRY = {
    "search_products": search_products,
    "check_stock": check_stock,
    "get_product_details": get_product_details,
    "buy_product": buy_product,
    "get_order_details": get_order_details,
    "list_orders": list_orders,
    "add_product": add_product,
    "edit_product": edit_product,
    "delete_product": delete_product,
}

SYSTEM_PROMPT = """You are a careful shopping assistant.
Use tools when the user's request needs catalog or stock information.
After observing a tool result, decide whether another tool is needed.
Never invent product data. Explain controlled tool errors clearly.
When reporting prices, quantities, totals, or stock, copy the exact values from the latest tool result.
Do not recalculate or alter monetary values in the final answer.
Finish with a concise answer when the user's request is satisfied.
"""


class ShoppingAgent:
    """Ask the model to choose tools while the application controls execution."""

    def __init__(
        self,
        role: str = "customer",
        client: OpenAI | None = None,
        model: str = MODEL_NAME,
        max_tool_calls: int = MAX_TOOL_CALLS,
    ):
        self.role = role
        self.client = client or create_client()
        self.model = model
        self.max_tool_calls = max_tool_calls
        self.trace: list[dict] = []

    def run(self, request: str) -> str:
        """Run the bounded model -> tool -> observation loop."""
        if not request.strip():
            return "I could not process an empty request."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"User role: {self.role}\nRequest: {request}"},
        ]

        while len(self.trace) < self.max_tool_calls:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0,
            )
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return message.content or "The model returned no final answer."

            for tool_call in message.tool_calls:
                if len(self.trace) >= self.max_tool_calls:
                    return "I stopped because the maximum tool-call limit was reached."

                arguments = self._parse_arguments(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                result = self._call_tool(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        return "I stopped because the maximum tool-call limit was reached."

    def _call_tool(self, tool_name: str, arguments: object) -> dict:
        result = execute_tool(self.role, tool_name, arguments, TOOL_REGISTRY)
        self.trace.append(
            {
                "call": len(self.trace) + 1,
                "tool": tool_name,
                "arguments": asdict(arguments) if is_dataclass(arguments) else arguments,
                "result": result,
            }
        )
        return result

    @staticmethod
    def _parse_arguments(tool_name: str, raw_arguments: str) -> object:
        try:
            arguments = json.loads(raw_arguments)
            if not isinstance(arguments, dict):
                raise ValueError
            if tool_name == "search_products":
                return SearchProductsInput(query=arguments.get("query", ""))
            if tool_name == "check_stock":
                return CheckStockInput(product_id=arguments.get("product_id", 0))
            if tool_name == "get_product_details":
                return GetProductDetailsInput(product_id=arguments.get("product_id", 0))
            if tool_name == "buy_product":
                return BuyProductInput(
                    product_id=arguments.get("product_id", 0),
                    quantity=arguments.get("quantity", 0),
                )
            if tool_name == "get_order_details":
                return GetOrderDetailsInput(order_id=arguments.get("order_id", 0))
            if tool_name == "list_orders":
                return ListOrdersInput()
            if tool_name == "add_product":
                return AddProductInput(
                    name=arguments.get("name", ""),
                    category=arguments.get("category", ""),
                    price=arguments.get("price", -1),
                    stock=arguments.get("stock", -1),
                )
            if tool_name == "edit_product":
                return EditProductInput(
                    product_id=arguments.get("product_id", 0),
                    name=arguments.get("name"),
                    category=arguments.get("category"),
                    price=arguments.get("price"),
                    stock=arguments.get("stock"),
                )
            if tool_name == "delete_product":
                return DeleteProductInput(product_id=arguments.get("product_id", 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        return {"invalid_arguments": raw_arguments}
