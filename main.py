"""Command-line entry point for the safe shopping agent."""

import json
import sys

from agent import ShoppingAgent
from config import validate_config


RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
DIM = "\033[2m"


def color(text: str, code: str) -> str:
    """Use color interactively while keeping redirected output readable."""
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


def print_banner() -> None:
    print()
    print(color("=" * 64, CYAN))
    print(color("                 SAFE SHOPPING AGENT", CYAN))
    print(color("=" * 64, CYAN))
    print("Local model + permission-controlled tools")
    print()


def print_trace(trace: list[dict]) -> None:
    print(color("AGENT TRACE", BLUE))
    print(color("-" * 64, DIM))
    if not trace:
        print("No tool calls recorded. The model answered without using a tool.")
        print()
        return

    for item in trace:
        arguments = json.dumps(item["arguments"], indent=2)
        result = json.dumps(item["result"], indent=2)
        status = "OK" if item["result"].get("ok") else "BLOCKED"
        status_color = GREEN if status == "OK" else YELLOW
        print(f"[{item['call']}] {color('TOOL CALL', CYAN)}  {item['tool']}")
        print(f"    Arguments: {arguments}")
        print(f"    Result:    {color(status, status_color)}")
        print(f"    Observation: {result}")
        print()


def main() -> None:
    try:
        validate_config()
    except RuntimeError as error:
        print(color(f"Configuration error: {error}", YELLOW))
        return

    print_banner()
    print("Role options: customer, admin")
    while True:
        role = input("Role (customer/admin): ").strip().lower()
        if role in {"customer", "admin"}:
            break
        print("Invalid role. Please enter exactly 'customer' or 'admin'.")

    while True:
        request = input("Request (or 'exit'): ").strip()
        if request.lower() == "exit":
            print("Goodbye.")
            return
        if not request:
            print("Please enter a request or type 'exit'.")
            continue

        agent = ShoppingAgent(role=role)
        print()
        print(color("SESSION", BLUE))
        print(color("-" * 64, DIM))
        print(f"Model:   {agent.model}")
        print(f"Role:    {agent.role}")
        print(f"Request: {request}")
        print()

        answer = agent.run(request)
        print_trace(agent.trace)
        print(color("FINAL ANSWER", GREEN))
        print(color("-" * 64, DIM))
        print(answer)
        print()


if __name__ == "__main__":
    main()