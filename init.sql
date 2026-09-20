CREATE TABLE IF NOT EXISTS products (
    code INT UNIQUE,
    product_name VARCHAR(100),
    price FLOAT
)

CREATE TABLE IF NOT EXISTS cupons (
    cuponcode VARCHAR(20) UNIQUE,
    discount INT
)

CREATE TABLE IF NOT EXISTS quickitems (
    product_name VARCHAR(100),
    price FLOAT
)
CREATE TABLE IF NOT EXISTS customers(
    name VARCHAR(50),
    phone VARCHAR(20) UNIQUE
)

-- Sample data for products
INSERT INTO products (code, product_name, price) VALUES
    (1001, 'Coffee', 3.50),
    (1002, 'Sandwich', 6.00),
    (1003, 'Croissant', 2.75),
    (1004, 'Orange Juice', 3.00),
    (1005, 'Muffin', 2.50),
    (1006, 'Bottled Water', 1.50),
    (1007, 'Bagel', 2.25),
    (1008, 'Iced Tea', 3.25)

-- Sample data for cupons
INSERT INTO cupons (cuponcode, discount) VALUES
    ('SAVE10', 10),
    ('WELCOME20', 20)

-- Sample data for quickitems
INSERT INTO quickitems (product_name, price) VALUES
    ('Coffee', 3.50),
    ('Orange Juice', 3.00),
    ('Bottled Water', 1.50),
    ('Iced Tea', 3.25)


