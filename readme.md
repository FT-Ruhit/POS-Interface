# POS Interface

A desktop point-of-sale (POS) interface built with Python, PySide6, and PostgreSQL. The application provides a product selection screen on the left and a checkout cart on the right.

## Features

- Load products from a PostgreSQL `products` table.
- Search products by name or product code.
- Support barcode-style entry by submitting an exact product code.
- Add products to a cart by clicking product tiles.
- Add custom items with a name, price, and quantity.
- Increase, decrease, or remove cart items.
- Apply percentage coupons loaded from PostgreSQL.
- Display the original total and discounted total.
- Show purchase confirmation and clear the cart after checkout.
- Apply a dark Qt stylesheet from `pos_style.qss`.

## Requirements

- Python 3.10 or newer
- PostgreSQL
- Python dependencies listed in `requirements.txt`

## Installation

1. Create and activate a virtual environment:

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

2. Install the dependencies from `requirements.txt`:

	```powershell
	pip install -r requirements.txt
	```

3. Create a PostgreSQL database for the application.

4. Execute the SQL in `init.sql` against that database. It creates the `products` and `cupons` tables and inserts sample records.

5. Configure the local database connection through a `.env` file before starting the application.

## Running the application

With the virtual environment activated, the database configured, and PostgreSQL running, start the application with:

```powershell
python pos_main.py
```

The window opens maximized. The application connects to PostgreSQL during startup, so the database must be available and the `.env` values must be valid before launching it.

## Using the POS

### Add products

- Click a product tile to add one unit to the cart.
- Type a product name or code in the search field to filter the product grid.
- Enter an exact product code and press Enter to add it directly.
- Use **Add custom item** for products that are not in the database.

### Manage the cart

- Use `+` and `-` to change an item's quantity.
- Use the remove control in the final column to delete an item.
- The total updates after every cart change.

### Apply a coupon

Enter a coupon code such as `SAVE10` or `WELCOME20`, then select **Apply**. Coupon matching is case-insensitive. Invalid codes display a warning and remove the current discount.

### Complete a purchase

Select **Purchase** when the cart is ready. The current implementation displays the amount charged, clears the cart, and does not write an order or payment record to the database.

## Database schema

`init.sql` defines these tables:

| Table | Columns | Purpose |
| --- | --- | --- |
| `products` | `code`, `product_name`, `price` | Product catalog shown in the application |
| `cupons` | `cuponcode`, `discount` | Percentage coupon codes |

The project currently uses the existing table name `cupons` and field name `cuponcode`.

## Project structure

```text
POS Interface/
├── db_connect.py    # PostgreSQL connection and table reads
├── init.sql         # Database schema and sample data
├── pos_main.py      # PySide6 UI and cart behavior
├── pos_style.qss    # Qt stylesheet and color tokens
├── requirements.txt  # Python dependencies
└── readme.md        # Project documentation
```

## How it works

1. `pos_main.py` loads the database connection environment from `.env`.
2. Two `DB_Connection` instances fetch products and coupons at startup.
3. `ProductPanel` filters products and sends selected items to the cart.
4. `CartPanel` renders quantities, subtotals, coupons, and totals.
5. `MainWindow` owns cart state and handles quantity changes, coupon validation, and purchase confirmation.

## Troubleshooting

### PostgreSQL connection errors

Check that PostgreSQL is running, the database exists, and the local `.env` configuration is correct.

### No products or coupons appear

Confirm that `init.sql` was executed against the database configured in `.env`. Verify the table names `products` and `cupons` and check that they contain rows.

### The stylesheet is not applied

Run `pos_main.py` from the project directory or keep `pos_style.qss` beside `pos_main.py`; the stylesheet path is resolved relative to the Python entry point.

## Current limitations

- Purchases are not persisted.
- Inventory is not updated after a purchase.
- Database errors are not presented through a dedicated UI error screen.
- Product and coupon records are loaded once at startup.
- Custom items exist only for the current checkout session.
