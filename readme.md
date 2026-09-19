# POS Interface

A small desktop point-of-sale application built with Python and PySide6. The project includes a sales terminal for adding items to a cart and a data-entry window for managing products, coupons, and quick items.

## What this app does

- Lets a cashier add items to a sale from a product list or a quick-item tile grid
- Supports adding custom one-off items that are not saved to the database
- Applies coupon discounts to the current cart total
- Removes purchased real products from the local database after checkout
- Provides a separate admin window for creating and deleting products, coupons, and quick items

## Current implementation details

This project currently uses SQLite rather than PostgreSQL. The database is created automatically as a local file named Data.db when the app starts, and the schema is defined in init_db.py.

The main database tables are:

- products
- cupons
- quickitems

## Tech stack

- Python 3.10+
- PySide6
- SQLite3
- Qt stylesheet file: pos_style.qss

## Requirements

Install the dependencies in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Project structure

```text
POS Interface/
├── data_entry.py      # Product, coupon, and quick-item management UI
├── db_connect.py      # SQLite database access helper
├── init_db.py         # Table creation and DB initialization
├── init.sql           # SQL seed script for schema and sample records
├── pos_main.py        # Checkout interface and cart logic
├── pos_style.qss      # Shared Qt styling
├── requirements.txt   # Python dependencies
├── Data.db            # Local SQLite database created at runtime
├── test.py            # Experimental/test script
├── readme.md          # Project documentation
└── .venv              # Virtual environment (local)
```

## How to run the app

### 1. Open a terminal in the project root

```powershell
cd "C:\Code\Qt-Python\POS Interface"
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If execution policy blocks the script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Launch the checkout window

```powershell
python pos_main.py
```

This opens the POS sales screen.

### 4. Launch the data-entry window

```powershell
python data_entry.py
```

This opens the management screen for coupons and products.

> Do not run both windows in the same terminal session if you want to keep them separate and avoid Qt event-loop conflicts.

## Database setup

The app creates the database automatically, so there is no .env configuration step in the current implementation.

When the app starts, it connects to Data.db and creates the required tables if they do not already exist:

- products(code, product_name, price)
- cupons(cuponcode, discount)
- quickitems(product_name, price)

You can also initialize sample data manually by running the SQL in init.sql.

## Using the checkout screen

### Add products

- Click a quick-item tile to add an item instantly
- Enter a product code and click Add to look up a saved product
- Use Add custom item to create a temporary item not stored in the product catalog

### Manage the cart

- Increase or decrease quantity using the controls in the cart table
- Remove items individually
- Review the subtotal and total as the cart changes

### Apply a discount

- Enter a coupon code such as SAVE10 or WELCOME20
- Click Apply to calculate the discounted total

### Complete a purchase

- Click Purchase when ready
- The app calculates the final amount, removes purchased real products from the database, and clears the cart
- Custom items are not saved to the database and are only included for the current transaction

## Using the data-entry screen

### Add coupons

- Enter a coupon code and percentage discount
- Click Add Coupon
- The coupon appears in the saved coupon table

### Add products in a range

- Enter a starting and ending code range
- Provide a product name and price
- Click Preview Range to confirm the number of rows to insert
- Click Add Products to insert them into the products table

### Delete entries

- Delete individual rows with the delete button in each table
- Select several products and click Delete Selected for bulk removal
- Refresh the tables after making external changes to the database

## Quick items

The quick-item section is populated from the quickitems table. These rows are shown as big clickable tiles in the checkout screen and are useful for frequently sold items.

## Troubleshooting

### Database file is missing

The app creates Data.db automatically when it runs. If it does not exist yet, start the app once and it will be created.

### No items appear in the POS

Check that the tables were created and that the Data.db file contains rows.

### Product lookup fails

Make sure the code you enter matches an existing product in the products table.

### Style is not applied

Keep pos_style.qss in the same folder as the Python files and launch the app from the project directory.

## Notes

- This project does not currently include payment processing or sales history.
- Purchases are not persisted beyond the active checkout flow.
- Quick-item changes are visible after restarting the checkout screen, since it loads the table when it starts.

## Common commands

```powershell
python pos_main.py
python data_entry.py
pip install -r requirements.txt
```
