# Safe Shopping Agent

## 1. Project Overview

A small Topic 07 agent powered by the local Ollama model `qwen3.5:4b`. The model chooses tools, the application checks permissions, the tools query or update SQLite, and the result returns to the model.

## Quick Start

Open PowerShell in this folder:

```powershell
cd D:\HRD\AI\Agent
.\.venv\Scripts\Activate.ps1
```

Make sure Ollama is running and the model is installed:

```powershell
ollama list
```

The project uses `qwen3.5:4b`. No cloud API key is required.

Initialize or reset the database:

```powershell
Remove-Item shopping.db -ErrorAction SilentlyContinue
python init_database.py
```

Start the agent:

```powershell
python main.py
```

The application accepts multiple requests. Choose a role, enter requests, and type `exit` at the request prompt to stop.

```text
Role (customer/admin): customer
Request (or 'exit'): Find a laptop that is currently in stock
```

If the virtual environment is not activated, use the interpreter directly:

```powershell
.\.venv\Scripts\python.exe init_database.py
.\.venv\Scripts\python.exe main.py
```

## 3. Agent Loop

```text
User request
    -> Ollama chooses a structured tool call
    -> application checks role permission and tool arguments
    -> tool reads or changes SQLite
    -> result returns to Ollama
    -> Ollama chooses another tool or writes the final answer
```

The agent has a maximum of 5 tool calls per request.

## Database

The catalog is not hard-coded in Python. It is stored in `shopping.db` and initialized from SQL files.

```text
categories     6 product categories
products       12 products with price, stock, and active status
orders         2 seed orders for Default Customer
order_items    2 seed order lines
```

A purchase creates an order and an order item, saves the exact purchase price, and reduces product stock in one transaction. Product deletion archives the product with `active = 0` so old order history remains valid.

Database files:

```text
db/schema.sql       table definitions and constraints
db/data.sql         seed categories, products, and historical orders
init_database.py    creates or resets the database
```

## 2. Available Tools

There are **10 tools**:

| Tool                     | Input                                | Purpose                               |
| ------------------------ | ------------------------------------ | ------------------------------------- |
| `search_products`        | `query`                              | Search products by name or category.  |
| `list_in_stock_products` | none                                 | List every active product with stock. |
| `check_stock`            | `product_id`                         | Check current stock for one product.  |
| `get_product_details`    | `product_id`                         | Show complete product information.    |
| `buy_product`            | `product_id`, `quantity`             | Create an order and reduce stock.     |
| `get_order_details`      | `order_id`                           | Show one order and its line items.    |
| `list_orders`            | none                                 | Show all orders for Default Customer. |
| `add_product`            | `name`, `category`, `price`, `stock` | Add a product. Admin only.            |
| `edit_product`           | `product_id` plus fields to change   | Edit a product. Admin only.           |
| `delete_product`         | `product_id`                         | Archive a product. Admin only.        |

Tool schemas are in `schemas.py`. Tool implementations are in `tools.py`. The model registration is in `agent.py`.

## 4. Permission Rule

Permissions are enforced in `harness.py` before a tool runs.

| Role       | Allowed actions                                                          |
| ---------- | ------------------------------------------------------------------------ |
| `customer` | Search, check stock, view details, buy, view order details, list orders. |
| `admin`    | All customer actions, plus add, edit, and archive products.              |

Customers attempting `add_product`, `edit_product`, or `delete_product` receive `PERMISSION_DENIED`.

## 5. Safety

- Tool inputs use explicit structured schemas in `schemas.py`.
- Empty searches, invalid product/order IDs, non-positive quantities, negative prices/stock, duplicate names, and empty updates are rejected.
- Database failures return controlled error results instead of raw exceptions.
- The tool registry is an allowlist, and the permission harness runs before every tool.
- Customers cannot add, edit, or archive products; the rule is enforced in `harness.py`.
- A purchase validates stock, creates an order and order item, saves the price, and reduces stock in one database transaction.
- Product deletion archives the product so historical order items remain valid.
- The model can make at most 5 tool calls for one request.

## 6. Example Run

Input:

```text
Role (customer/admin): customer
Request (or 'exit'): Find a laptop that is currently in stock
```

Model-selected tool calls and observations:

```text
[1] TOOL CALL search_products
    Arguments: {"query": "laptop"}
    Observation: candidates Laptop Pro 14 (id 1) and Laptop Air 13 (id 2)

[2] TOOL CALL check_stock
    Arguments: {"product_id": 1}
    Observation: {"stock": 12, "in_stock": true}

FINAL ANSWER
Laptop Pro 14 is in stock at $999.99 with 12 units available.
```

The complete formatted output is saved in `terminal_output.txt`.

## Recommended Tests

Reset before a clean test:

```powershell
Remove-Item shopping.db -ErrorAction SilentlyContinue
python init_database.py
```

### Test 1: Required agent loop

```text
Role: customer
Request: Find a laptop that is currently in stock
```

Expected trace:

```text
search_products -> check_stock -> final answer
```

### Test 2: Product details

```text
Give me the full details for the laptop
```

Expected trace:

```text
search_products -> get_product_details -> final answer
```

### Test 3: Real purchase and stock update

```text
Buy 2 Laptop Pro 14
```

Expected result:

```text
ORDER_CREATED
order_id: 3
total_amount: 1999.98
remaining_stock: 10
```

Then enter:

```text
Show order 3 details
Show order history
```

Expected tools:

```text
get_order_details
list_orders
```

### Test 4: Admin catalog management

Restart the app with role `admin`:

```text
Add a Demo Keyboard in accessories for 49.99 with 10 units
Edit Demo Keyboard price to 44.99
Delete Demo Keyboard
```

Expected results:

```text
PRODUCT_ADDED
PRODUCT_UPDATED
PRODUCT_ARCHIVED
```

### Test 5: Permission control

Restart with role `customer` and enter:

```text
Add a new keyboard
Delete product 1
```

Expected result for both:

```text
PERMISSION_DENIED
```

### Test 6: Validation

Try:

```text
Find
Buy 0 Laptop Pro 14
Find a spaceship
```

Expected controlled responses for missing search text, invalid quantity, and no matching product.

## Automated Checks

Compile the project using a PowerShell-compatible command:

```powershell
$files = Get-ChildItem -Filter *.py | Select-Object -ExpandProperty Name
python -m py_compile $files
```

The saved `terminal_output.txt` contains a representative agent trace for submission.

## Configuration

`.env` contains the local Ollama settings and is ignored by Git:

```text
OLLAMA_HOST=http://localhost:11434/v1
MODEL_NAME=qwen3.5:4b
MAX_TOOL_CALLS=5
```

`.env.example` is the shareable template. `.venv` is the project virtual environment.

## Project Structure

```text
agent.py             Ollama loop and tool routing
config.py            Ollama and safety configuration
database.py          SQLite connection and initialization
tools.py             Database-backed tool implementations
schemas.py           Structured tool schemas and input dataclasses
harness.py           Permission checks, allowlist, and error boundary
main.py              Terminal user interface
db/schema.sql        Relational database schema
db/data.sql          Seed data
init_database.py     Database initialization command
requirements.txt     Python dependencies
terminal_output.txt  Example run output
```
