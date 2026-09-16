# POS Interface

A desktop point-of-sale (POS) application built with Python, PySide6, and PostgreSQL. It includes a checkout terminal for selling products and a separate data-entry window for managing the product catalog and coupons.

## Features

- Load products from a PostgreSQL `products` table.
- Add products to a cart by clicking quick-item tiles or entering an exact product code.
- Add custom items with a name, price, and quantity.
- Increase, decrease, or remove cart items.
- Apply percentage coupons loaded from PostgreSQL and display the original and discounted totals.
- Remove purchased database products after a successful checkout.
- Show purchase confirmation and clear the cart after checkout.
- Manage products and coupons with the data-entry application.
- Apply the shared Qt stylesheet from `pos_style.qss`.

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

5. Configure the local database connection through a `.env` file before starting either application. The expected keys are:

	```dotenv
	host=localhost
	port=5432
	dbname=your_database
	user=your_user
	password=your_password
	```

## Running the application

The project contains two separate desktop windows:

- `pos_main.py` is the checkout terminal used to create sales.
- `data_entry.py` is the catalog and coupon manager used to prepare the database.

Both programs connect to PostgreSQL when they start. Keep PostgreSQL running, run commands from the project directory, and activate the virtual environment before launching either program.

### Start-up checklist

1. Start the PostgreSQL service and confirm that the configured database is available.
2. Open PowerShell in the project directory:

	```powershell
	cd "C:\Code\Qt-Python\POS Interface"
	```

3. Activate the virtual environment:

	```powershell
	.\.venv\Scripts\Activate.ps1
	```

	If PowerShell blocks the activation script for the current session, run:

	```powershell
	Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
	.\.venv\Scripts\Activate.ps1
	```

4. Check that `.env` is in the project directory and contains the lowercase keys `host`, `port`, `dbname`, `user`, and `password`.
5. Launch the window required for the task. Do not start both scripts in the same terminal because each script owns its own Qt event loop.

### Start the checkout terminal

Run:

```powershell
python pos_main.py
```

The terminal opens maximized with products on the left and the cart on the right. The first six products ordered by `code` are displayed as quick-item tiles. The remaining products can still be added by entering their exact numeric code in **Add by code**.

### Complete a sale

1. Add a product by clicking a quick-item tile, or enter its numeric code and select **Add**. A product code must already exist in the `products` table.
2. Add any one-off items through **Add custom item** by entering a name and price. These items are identified internally with a `CUSTOM-` code and are not added to the catalog.
3. Review the cart. Use `+` and `-` to adjust quantities, or use the remove control to delete a line.
4. Enter a coupon code from the `cupons` table and select **Apply**. The discount is shown below the coupon field and the total is recalculated.
5. Select **Purchase**. The discounted amount is displayed, real database products in the cart are deleted from `products`, and the cart is cleared.

An empty cart cannot be purchased. If the database deletion fails, the purchase is not completed and the cart remains available for retry.

### Start the data-entry window

Run:

```powershell
python data_entry.py
```

The data-entry window opens maximized with coupon controls on the left and product controls on the right. Both saved-data tables are loaded from PostgreSQL when the window starts.

### Add and remove coupons

1. Enter a unique coupon code, such as `SAVE10`, in the **Code** field.
2. Enter a percentage from `1` to `100` in **Discount**.
3. Select **Add Coupon**. The coupon is inserted into `cupons` and appears in **Saved Coupons**.
4. Use the delete control in the table to remove a coupon.
5. Select **Refresh** after making changes through another database tool.

Coupon codes must be unique because `cuponcode` has a unique constraint. A duplicate code is rejected by PostgreSQL and shown as an error dialog.

### Add and remove products

1. Enter the first and last product codes in **Code from** and **Code to**. The range is inclusive.
2. Enter one product name and price for the range.
3. Select **Preview Range**. The window reports how many product rows are queued.
4. Select **Add Products** to insert the queued rows into `products`.
5. Use the delete control beside a saved product to remove one row.
6. To remove several products, check their selection boxes, select **Delete Selected**, and confirm the dialog.
7. Select **Refresh** after making changes through another database tool.

Product codes must be unique. If an insert conflicts with an existing code, PostgreSQL rejects the insert and the error is shown in a dialog.

### Apply catalog changes to checkout

The checkout terminal loads its quick-item tiles only during startup. After adding, deleting, or changing catalog data in `data_entry.py`, close and restart `pos_main.py` so the terminal reloads the current products. Coupon lookups are performed while applying a coupon, so newly added coupons can be used after the checkout terminal is restarted or after the next lookup.

### Stop the application

Close the Qt window normally. If the program is running in a terminal and the window is unresponsive, press `Ctrl+C` in that terminal after closing the window. The application does not create a separate server process.

## Using the POS

### Add products to a sale

- Click a quick-item tile to add one unit to the cart.
- Enter an exact numeric product code and press Enter or select **Add** to look it up in PostgreSQL.
- Use **Add custom item** for products that are not in the database. Custom items use a `CUSTOM-` code and are not saved to PostgreSQL.

### Manage the cart

- Use `+` and `-` to change an item's quantity.
- Use the remove control in the final column to delete an item.
- The total updates after every cart change.

### Apply a coupon

Enter a coupon code such as `SAVE10` or `WELCOME20`, then select **Apply**. Coupons are read from the `cupons` table.

### Complete a purchase

Select **Purchase** when the cart is ready. The application calculates the discounted total, removes the purchased database products from `products`, displays the amount charged, and clears the cart. Custom items are only part of the current sale and are not removed from the database.

## Managing products and coupons

Run `data_entry.py` to open the management window.

- Add a coupon by entering its code and percentage discount.
- Delete individual coupons with the delete control in the saved-coupons table.
- Enter a product code range, name, and price, then select **Preview Range** before **Add Products** to insert one product for each code in the range.
- Refresh the saved products and coupons tables after external database changes.
- Select one or more products and choose **Delete Selected** to remove them after confirmation.
- Delete an individual product with the delete control in the saved-products table.

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
├── data_entry.py    # Product and coupon management window
├── db_connect.py    # PostgreSQL connection and CRUD helpers
├── init.sql         # Database schema and sample data
├── pos_main.py      # Checkout terminal and cart behavior
├── pos_style.qss    # Shared Qt stylesheet
├── requirements.txt # Python dependencies
├── test.py          # Project test or experimentation script
└── readme.md        # Project documentation
```

## How it works

1. `pos_main.py` and `data_entry.py` load the database connection environment from `.env`.
2. The checkout terminal loads up to six quick items from `products` and looks up entered product codes on demand.
3. `ProductPanel` sends selected database products or custom items to `MainWindow`.
4. `CartPanel` renders quantities, subtotals, coupons, and totals.
5. `MainWindow` owns cart state, handles quantity changes, and removes purchased database products after confirmation.
6. `DataEntryWindow` reads and writes the `products` and `cupons` tables, including range insertion and deletion controls.

## Troubleshooting

### PostgreSQL connection errors

Check that PostgreSQL is running, the database exists, and the local `.env` configuration is correct.

### No products or coupons appear

Confirm that `init.sql` was executed against the database configured in `.env`. Verify the table names `products` and `cupons` and check that they contain rows.

### Data-entry changes are not visible in the terminal

The checkout terminal loads quick items when it starts. Restart `pos_main.py` after adding or deleting products in `data_entry.py`.

### The stylesheet is not applied

Run `pos_main.py` from the project directory or keep `pos_style.qss` beside `pos_main.py`; the stylesheet path is resolved relative to the Python entry point.

## Current limitations

- Purchases are not persisted.
- No order, payment, or sales-history record is stored.
- Database errors are not presented through a dedicated UI error screen.
- Quick products are loaded once at startup; catalog changes require restarting the terminal.
- Custom items exist only for the current checkout session.
